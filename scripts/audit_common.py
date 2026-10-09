"""Repository-only checks. This module never alters or runs an optimization driver."""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
METHODS = {"p1": ("SCP-ALM", "SCP_ALM"), "p2": ("RD-ALM", "RD_ALM"),
           "p1_norho": ("SCP-LR", "SCP_LR"), "gurobi": ("Gurobi", "Gurobi")}
TABLES = {"2d": "results/local_side_scaling_results.csv", "3d": "results/difficult_instance_results.csv"}
# Absolute, not relative, tolerance. No seed/integer/hash/structure field is exempted.
NUMERICAL_ATOL = 1e-13
_FLOAT_PATHS = [
 r"/family_payload/dcap_pc1_projected_mild_(?:beta|centered_energy_match_abs|full_energy_match_abs|explained_fraction)",
 r"/family_payload/dcap_pc1_projected_mild_direction/\d+/\d+",
 r"/family_payload/dcap_pc1_projected_mild_scores/\d+",
 r"/family_payload/dcap_profile_meta/\d+/pc1_projected_mild_score",
 r"/family_payload/dcap_requirements/\d+/\d+/\d+",
 r"/generator_metrics/pc1_projected_mild_(?:beta|centered_energy_match_abs|centered_frobenius_energy|explained_fraction|full_energy_match_abs|score_mean)",
 r"/scenario_capacities/\d+/\d+",
]
FLOAT_PATTERNS = [re.compile(x) for x in _FLOAT_PATHS]

class AuditError(RuntimeError):
    """A reference, configuration or numerical consistency requirement failed."""

def require(ok: bool, message: str) -> None:
    if not ok:
        raise AuditError(message)

def read_json(path: Path) -> Any:
    # Frozen output format uses NaN/Infinity. Python's JSON reader preserves them.
    return json.loads(path.read_text(encoding="utf-8-sig"))

def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def payload(obj: dict) -> dict:
    return {k: v for k, v in obj.items() if k != "args"}

def payload_hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=True).encode("utf-8")).hexdigest()

def equal(a: Any, b: Any) -> bool:
    if type(a) is not type(b):
        return False
    if isinstance(a, float) and math.isnan(a) and math.isnan(b):
        return True
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b

def compare_instance(reference: dict, actual: dict, study: str, mode: str = "strict") -> dict:
    require(mode in ("strict", "numerical"), "Invalid identity mode")
    expected, observed = payload_hash(reference), payload_hash(actual)
    if expected == observed:
        return {"mode": mode, "strict_hash_equal": True, "numerically_different_fields": 0, "max_absolute_difference": 0}
    require(mode == "numerical" and study == "2d", "Strict instance payload hash differs (numerical mode only supports documented 2D PC1 fields)")
    count, maximum = 0, 0.0
    def walk(a: Any, b: Any, path: str = "") -> None:
        nonlocal count, maximum
        require(type(a) is type(b), f"Instance type differs: {path}")
        if isinstance(a, dict):
            require(a.keys() == b.keys(), f"Instance keys differ: {path}")
            for k in a: walk(a[k], b[k], path + "/" + k)
        elif isinstance(a, list):
            require(len(a) == len(b), f"Instance list length differs: {path}")
            for i, (x, y) in enumerate(zip(a, b)): walk(x, y, path + f"/{i}")
        elif equal(a, b):
            return
        else:
            permitted = (isinstance(a, float) and math.isfinite(a) and math.isfinite(b)
                         and any(p.fullmatch(path) for p in FLOAT_PATTERNS))
            require(permitted, f"Non-whitelisted instance field differs: {path}")
            delta = abs(a - b)
            require(delta <= NUMERICAL_ATOL, f"Instance difference {delta:g} exceeds {NUMERICAL_ATOL:g}: {path}")
            count += 1
            maximum = max(maximum, delta)
    walk(reference, actual)
    return {"mode": mode, "strict_hash_equal": False, "reference_payload_sha256": expected,
            "actual_payload_sha256": observed, "numerically_different_fields": count,
            "max_absolute_difference": maximum, "absolute_tolerance": NUMERICAL_ATOL}

@lru_cache(maxsize=2)
def parser_for(driver_name: str) -> argparse.ArgumentParser:
    """Compile only the frozen parser factory and literal constants, not module/main."""
    source = ROOT / driver_name
    tree = ast.parse(source.read_text(encoding="utf-8-sig"))
    namespace: dict[str, Any] = {"argparse": argparse}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            # This exact syntactic form is the frozen tuple(range(300,1441,60)).
            val = node.value
            if (isinstance(val, ast.Call) and isinstance(val.func, ast.Name) and val.func.id == "tuple"
                and len(val.args) == 1 and isinstance(val.args[0], ast.Call)
                and isinstance(val.args[0].func, ast.Name) and val.args[0].func.id == "range"
                and not val.keywords and not val.args[0].keywords):
                try: value = tuple(range(*(ast.literal_eval(x) for x in val.args[0].args)))
                except (ValueError, TypeError): continue
            else: continue
        for target in targets:
            if isinstance(target, ast.Name): namespace[target.id] = value
    factories = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_argparser"]
    require(len(factories) == 1, "Frozen parser factory missing or ambiguous")
    exec(compile(ast.Module(body=factories, type_ignores=[]), str(source), "exec"), namespace)
    return namespace["build_argparser"]()

def plan() -> list[dict]:
    return read_json(ROOT / "configs/run_plan.json")["jobs"]

def check_job_config(job: dict) -> dict:
    require(sha256(ROOT / job["driver"]) == job["driver_sha256"], f"Frozen source SHA mismatch: {job['driver']}")
    require(sha256(ROOT / job["config"]) == job["config_sha256"], f"Config SHA mismatch: {job['job_id']}")
    conf = read_json(ROOT / job["config"])
    got = vars(parser_for(job["driver"]).parse_args(job["argv"]))
    require(equal(got, conf["args"]), f"Actual frozen parser does not reconstruct recorded config: {job['job_id']}")
    a = conf["args"]
    require(a["run_algos"].split(",") == job["methods_internal"], "Method mapping differs")
    require(a["out_dir"] == "outputs/" + job["output_relative_dir"], "Nonportable recorded output path")
    require(a["dcap_nested_b60_enable"] and a["dcap_nested_b60_verify_prefix"] and a["dcap_nested_b60_freeze_first_stage"], "Nested/prefix/freeze flag mismatch")
    require(a["dcap_tail_delta"] == .1 and a["dcap_tail_rnc_weight_scale"] == .001, "Tail settings differ")
    if job["study"] == "2d":
        b = int(job["instance_id"][1:]); budget = 3600 if b >= 1200 else 3000 if b >= 900 else 2400 if b >= 600 else 1800
        expected = {"dcap_num_blocks": b, "n_knapsacks": 2, "instance_seed": 4,
                    "dcap_candidate_index_label": 13, "dcap_candidate_seed_override": 1346405564,
                    "dcap_nested_b60_common_pool_seed_override": 5711692,
                    "outer_time_limit": float(budget), "baseline_time_limit": float(budget)}
    else:
        expected = {"dcap_num_blocks": 120, "n_knapsacks": 3, "dcap_mildz_target_low": 80,
                    "dcap_mildz_target_high": 180, "dcap_mildz_target_mid": 120,
                    "dcap_nested_b60_common_pool_seed_override": 161262537,
                    "dcap_homogeneous_A0_enable": True, "baseline_time_limit": 1800.0,
                    "outer_time_limit": 3600.0 if job["run_group"] == "gurobi" else 1800.0}
    require(all(equal(a[k], v) for k, v in expected.items()), f"Formal instance/budget settings differ: {job['job_id']}")
    return conf

def columns(method: str) -> dict:
    if method == "p2":
        return dict(lb="p2_certified_global_lb", ub="p2_certified_ub", gap="p2_certified_gap",
                    rel="p2_certified_rel_gap", pct="p2_certified_rel_gap_percent",
                    time="p2_certified_total_time_sec", residual="p2_certified_residual", status="stop_reason")
    if method == "gurobi":
        return dict(lb="best_bound", ub="incumbent_obj", gap=None, rel="cert_rel_gap",
                    pct="cert_rel_gap_percent", time="runtime", residual="residual_linf", status="status")
    return dict(lb="global_lb", ub="global_ub", gap="objective_cert_gap", rel="cert_rel_gap",
                pct="cert_rel_gap_percent", time="total_time_sec", residual="returned_primal_residual", status="stop_reason")

def number(value: Any) -> float:
    try: return float(value)
    except (TypeError, ValueError): return math.nan

def check_record(row: dict, method: str, args: dict, directory: Path | None = None) -> dict:
    c = columns(method); n = {k: number(row[v]) for k, v in c.items() if v is not None and k != "status"}
    require(all(math.isfinite(v) for v in n.values()), f"Nonfinite official {method} metric")
    delta = n["ub"] - n["lb"]
    require(delta >= -1e-6, f"{method}: lower bound exceeds upper bound")
    require(n["time"] >= 0 and 0 <= n["residual"] <= args["feas_tol"], f"{method}: time or residual invalid")
    rel = max(0, delta) / max(1, abs(n["ub"]))
    require(math.isclose(n["rel"], rel, rel_tol=1e-12, abs_tol=1e-14), f"{method}: certified relative gap formula mismatch")
    require(math.isclose(n["pct"], 100*n["rel"], rel_tol=1e-12, abs_tol=1e-12), f"{method}: percent gap mismatch")
    if "gap" in n: require(math.isclose(n["gap"], max(0, delta), rel_tol=1e-12, abs_tol=1e-7), "Absolute gap mismatch")
    require(bool(row[c["status"]]), "Missing final status")
    require(number(row["instance_seed"]) == args["instance_seed"], "Summary family/instance seed mismatch")
    require(number(row["n_items"]) == args["n_items"] and number(row["m_knapsacks"]) == args["n_knapsacks"]
            and number(row["n_scenarios"]) == args["dcap_num_blocks"], "Summary dimensions mismatch")
    if method == "p2":
        require(row["p2_certified_has_ub"] == "1" and row["p2_certified_bound_order_ok"] == "1", "RD-ALM audited certificate absent")
    if method == "gurobi": require(row["has_incumbent"] == "1", "Gurobi incumbent absent")
    if directory is None: return n
    if method == "gurobi":
        import decimal
        text = (directory / "gurobi_extensive.log").read_text(encoding="utf-8-sig")
        matches = re.findall(r"Best objective\s+([^,]+), best bound\s+([^,]+), gap\s+([\d.]+)%", text)
        require(len(matches) == 1 and text.count("logging started") == 1, "Native Gurobi log incomplete/concatenated")
        for displayed, field in zip(matches[0], [c["ub"], c["lb"], c["pct"]]):
            d = decimal.Decimal(displayed); q = decimal.Decimal(1).scaleb(d.as_tuple().exponent)
            require(abs(d-decimal.Decimal(row[field])) <= abs(q)/2 + decimal.Decimal("1e-12"), "Native log final bound/objective/gap disagrees")
        if row[c["status"]] == "TIME_LIMIT": require("Time limit reached" in text, "Native termination disagrees")
        require(re.search(r"Explored [^\n]* in [\d.]+ seconds", text) is not None, "Native completion runtime absent")
        nodes = re.findall(r"Explored (\d+) nodes", text)
        require(len(nodes)==1 and int(nodes[0])==number(row["node_count"]), "Native node count differs")
        # Printed runtime and Model.Runtime are kept separate; no false exact equality.
        return n
    trace = rows(directory / {"p1": "p1prime_log.csv", "p2": "p2_theory_log.csv", "p1_norho": "p1_norho_log.csv"}[method])
    require(bool(trace), "Missing/empty iteration trace")
    lbs = [number(r["inner_lb"]) for r in trace if math.isfinite(number(r["inner_lb"]))]
    require(lbs and abs(max(lbs)-n["lb"]) <= 1e-6, f"{method}: LB not supported by trace")
    require(all(not (number(r["inner_lb"]) > number(r["inner_ub"]) + 1e-6) for r in trace), "Inner bound order failed")
    if method == "p2":
        audits = rows(directory / "p2_fixed_z_audit.csv")
        valid = [r for r in audits if r["audit_ok_feasible_ub"] == "1"]
        ubs = [number(r["audit_obj"]) for r in valid]
        require(int(row["p2_certified_audit_count"]) == len(audits), "RD-ALM audit count differs")
        require(all(r["audit_completed_before_global_deadline"] == "1" for r in valid), "RD-ALM late valid audit")
    else:
        audits = rows(directory / ("p1_incumbent_audit.csv" if method == "p1" else "p1_norho_incumbent_audit.csv"))
        ubs = [number(r["verify_obj"]) for r in audits if r["has_incumbent"] == "1" and number(r["verify_residual_l1"]) <= args["feas_tol"]]
        last = directory / "p1_final_stop_audit.csv"
        if method == "p1" and last.exists():
            ubs += [number(r["verify_obj"]) for r in rows(last) if r["verify_has_incumbent"] == "1" and r["residual_ok"] == "1"]
        post = directory / "p1_postrun_lb_filter.json"
        if method == "p1" and args["n_knapsacks"] == 2 and post.exists():
            a = read_json(post)
            require(a["filter_applied"] == 0 and a["rejected_p1_history_lb_count"] == 0 and a["p1_gap_uses_p1_own_ub"] == 1, "SCP-ALM history audit failed")
            require(abs(a["selected_p1_history_lb"]-n["lb"]) <= 1e-7 and abs(a["p1_own_audited_ub"]-n["ub"]) <= 1e-7, "History audit bounds differ")
    require(ubs and abs(min(ubs)-n["ub"]) <= 1e-6, f"{method}: UB lacks fixed-z audit provenance")
    return n

def verify_output(job: dict, directory: Path, mode: str = "strict") -> dict:
    """Validate a fresh run's configuration, identity and certificates, NOT old runtimes/gaps."""
    expected = check_job_config(job)
    conf = read_json(directory / "config.json")
    require(equal({k:v for k,v in conf["args"].items() if k != "out_dir"},
                  {k:v for k,v in expected["args"].items() if k != "out_dir"}), "Fresh output configuration differs")
    require(equal(conf["gurobi_params"], expected["gurobi_params"]), "Fresh output recorded solver defaults differ")
    m = read_json(directory / "instance_manifest.json")
    require(equal(m["args"], conf["args"]), "Fresh manifest/config args differ")
    identity = compare_instance(read_json(ROOT/job["instance_manifest"]), payload(m), job["study"], mode)
    for method in job["methods_internal"]:
        rr = rows(directory / (method + "_summary.csv"))
        require(len(rr) == 1, "Fresh method summary missing/duplicated")
        check_record(rr[0], method, conf["args"], directory)
    if job["study"] == "2d" and "p1" in job["methods_internal"]:
        require((directory/"p1_postrun_lb_filter.json").is_file(), "Joint 2D history audit missing")
    return {"job_id":job["job_id"], "configuration":"PASS", "instance_identity":identity,
            "result_consistency":"PASS", "matches_historical_numbers":"NOT_REQUIRED"}
