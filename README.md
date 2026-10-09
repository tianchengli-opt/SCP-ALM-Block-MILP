# SCP-ALM: audited reproduction package for block-structured MILPs

This repository packages the author's **latest frozen implementations and independent rerun results** for block-structured mixed-integer linear programs with shared-variable coupling. The algorithm combines a sharp ℓ₁-augmented-Lagrangian dual, Kelley cutting planes, In-Out stabilization, certified inner bounds, and fixed-shared-variable feasibility audits. The two studies are DCAP-style constructed instances, not a claim of deployment on measured industrial data.

**Release status:** input, configuration, instance-identity, result-provenance, static launcher and negative tests have been executed. The package is ready for author-controlled source/result publication **with the limitations below**. No fresh third-party optimization reproduction has been completed. No software license has been selected or granted by this packaging exercise. See [中文说明](README_zh.md), [release audit](provenance/RELEASE_AUDIT_zh.md), and [change log](provenance/CHANGELOG_zh.md).

## Methods and studies

| Internal identifier | Paper label | Role |
|---|---|---|
| `p1` | SCP-ALM | Stabilized sharp ℓ₁ augmented-Lagrangian cutting-plane implementation |
| `p2` | RD-ALM | Residual-driven augmented-Lagrangian baseline; report its fixed-z **certified** fields |
| `p1_norho` | SCP-LR | Ordinary Lagrangian-relaxation ablation with ρ fixed to zero |
| `gurobi` | Gurobi | Direct extensive-form MILP baseline |

Study 1 has **20 scales B = 300, 360, …, 1440**, two resources and four methods (80 results). It uses 60 process calls: `p1p2` jointly produces SCP-ALM and RD-ALM, while `p1_norho` and `gurobi` run separately. Study 2 has **R01–R20**, three resources, 120 local blocks and four separate method calls per instance (80 results / 80 calls). Total: **40 instances, 140 calls, 160 method results**. “2D/3D” denotes the resource setting, not the dimension of the tail-lifted shared-variable vector; the latter is recorded in each manifest.

The original internal method identifiers are unchanged. In particular, use `p1p2`, not `p1`, to select the formal two-resource SCP-ALM invocation.

## Layout

```text
code/                  run_2d_scaling.py; run_3d_difficult.py (frozen)
configs/               run_plan.json; 60 two-resource + 80 three-resource configs
instances/             40 full canonical payloads; instance_index.csv
results/               two 80-row formal result tables
  source_summaries/    160 single-method summaries, numerical traces,
                       fixed-z audits, 20 history audits, 40 redacted native logs
scripts/               Python launcher/verifier/tests; two PowerShell wrappers
screening/             verified historical evidence, not an executable hunter
provenance/            input SHA ledger, code/identity/merge/result audits,
                       file mappings, differences, redactions and test evidence
repository_manifest.csv  immutable file-set, byte-size and SHA-256 manifest
```

Configuration and instance JSON files preserve the frozen format's `NaN`/`Infinity` sentinels. They are read with Python's JSON extension, not claimed to be strict RFC JSON for arbitrary third-party parsers.

All latest scientific results are under `results/`. Old values appear **only in explicitly historical audit/screening files**, not in formal result tables. Original bulk run logs, JSONL duplicates, obsolete source copies, virtual environments, caches and the original archives are deliberately not shipped. They are identified by archive-relative paths and SHA-256 in `provenance/input_inventory.csv`.

## Environment

Both frozen drivers import only `numpy` and `gurobipy` beyond Python's standard library. The repository verifier, previews and unit tests use the standard library and do not import the solver or run a driver.

| Evidence source | Two-resource study | Three-resource study |
|---|---|---|
| Author's device assignment | Desktop | Lenovo laptop |
| CPU in all 20 corresponding native logs | Intel Core i7-14700 | Intel Core i7-14650HX |
| Logged physical / logical cores | 20 / 28 | 16 / 24 |
| Baseline threads in native logs | Up to 4 | Up to 4 |
| Gurobi engine | 13.0.1, build v13.0.1rc0 | 13.0.1, build v13.0.1rc0 |
| Logged platform | win64, Windows 11+.0 (26200.2) | win64, Windows 11+.0 (26200.2) |

The original **Python version, NumPy version, package distribution versions, RAM and Windows edition were not independently recorded in the supplied formal environment evidence**. `requirements.txt` is intentionally not represented as an exact historical lock. Use an engine reporting Gurobi 13.0.1 for solver-version comparability and record the actual environment of any new run. Installing unpinned requirements can produce newer packages and is not a bitwise environment reconstruction.

This release's static tests ran on Linux, Python **3.13.5**, with NumPy **2.3.5** available and **no gurobipy installed**. PowerShell was unavailable. Those are audit-environment facts, not the original experimental environment.

### Setup

From the extracted project root, on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\verify_repository.py
```

On a POSIX shell:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/verify_repository.py
```

Obtain and configure a valid Gurobi license separately. Do not put a license file, secret, token or local user profile into this repository. An import/environment check is **not** a license or solve test:

```powershell
.\.venv\Scripts\python.exe scripts\run_experiments.py --study 2d --instance B0300 --run-group p1p2 --check-environment
```

## Preview and run

The launcher defaults to **dry-run**, checks reference hashes/configurations first, passes an explicit complete CLI and launches with `shell=False`. It never edits the frozen sources. Do **not** invoke the frozen files without arguments: legacy default dispatch can start preset workflows. Also do not use the frozen 2D `--help`; its original help text contains an unescaped percent format error. Use the outer launcher's help instead:

```powershell
python scripts\run_experiments.py --help
python scripts\run_experiments.py --study 2d --show-commands
python scripts\run_experiments.py --study 3d --show-commands
```

Previews produce 60 / 80 calls and do not create output directories. To run all formal configurations:

```powershell
python scripts\run_experiments.py --study 2d --output-root C:\SCP_ALM_runs\Study1 --execute
python scripts\run_experiments.py --study 3d --output-root C:\SCP_ALM_runs\Study2 --execute
```

To run only one scale / selected instance:

```powershell
python scripts\run_experiments.py --study 2d --instance B0300 --run-group p1p2 --output-root C:\SCP_ALM_runs\single_2d --execute
python scripts\run_experiments.py --study 3d --instance R17 --run-group p1 --output-root C:\SCP_ALM_runs\single_3d --execute
```

Omit `--run-group` to run all four methods for that scale/instance. Three-resource groups are `p1`, `p2`, `p1_norho`, `gurobi`; two-resource groups are `p1p2`, `p1_norho`, `gurobi`. POSIX users can use the same Python CLI with an absolute POSIX path or the default repo-relative `outputs` directory. The generated output suffix is always `<study>/<instance>/<run_group>`; the `source_output_directory` field records the supplied archive layout, not the new layout.

Equivalent PowerShell wrappers:

```powershell
.\scripts\run_2d_scaling.ps1 -Python .\.venv\Scripts\python.exe -ShowCommands
.\scripts\run_3d_difficult.ps1 -Python .\.venv\Scripts\python.exe -Instance R01 -RunGroup gurobi -OutputRoot C:\SCP_ALM_runs\test -Execute
```

PowerShell wrappers were inspected, **not executed in Windows/PowerShell** during this audit. Prefer an ASCII-only absolute Windows output path for native Gurobi logs; the original inputs demonstrate that local path strings can enter logs. No source path is rewritten inside the algorithm. The launcher only replaces the CLI output-directory value.

**Safety:** nonempty output directories are refused; there is no overwrite/resume option. Inside this project, output roots must be under `outputs/`. An error, interrupt or failed post-run audit stops subsequent calls and returns nonzero. Partial outputs are not called successful; inspect and archive them before selecting a fresh output root. Do not concurrently launch the same job into the same directory: the preflight is a nonempty-directory guard, not a cross-process locking protocol.

## Validate and inspect results

```powershell
python scripts\verify_repository.py
python scripts\test_repository.py
python scripts\verify_repository.py --job-id 3d_R17_p1 --run-output C:\SCP_ALM_runs\single_3d\3d\R17\p1
```

Reference validation checks all 140 parser/config roundtrips, 40 identities, 160 certificate records, exact source-to-table strings, fixed-z UB provenance, inner-trace LB provenance, cross-method bound consistency, native log final values, selected candidate identities and all registered byte hashes. Fresh-output validation compares the **configuration, generated instance and internal certificate consistency**, not equality to archived runtimes or achieved gaps. It requires complete output artifacts and will flag a materially incomplete or inconsistent run.

Open these files without rerunning optimization:

- `results/local_side_scaling_results.csv`
- `results/difficult_instance_results.csv`

Their `source_file` columns point to one-row latest summaries. `provenance/result_field_provenance.csv` identifies each reported numeric field's source column. All numeric strings are retained; the blank Gurobi absolute-gap table cell means that its source CSV has no corresponding independent field. Compute `UB - LB` for analysis, rather than interpreting a blank as zero. Missing/NaN checkpoint times remain missing/NaN; no “first time attaining the final gap” has been invented.

### Gap, feasible upper bounds and time

For the source-defined certified interval, `gap_rel = max(0, UB-LB) / max(1, abs(UB))`, provided `UB-LB >= -1e-6`; otherwise the code treats it as a bound-order failure. `gap_percent = 100 * gap_rel`. The verification tolerances are in `scripts/audit_common.py`; they check numerical consistency and do not change any algorithm tolerance.

| Method | Formal LB / UB fields | Time field |
|---|---|---|
| SCP-ALM / SCP-LR | `global_lb` / `global_ub` | `total_time_sec` |
| RD-ALM | `p2_certified_global_lb` / `p2_certified_ub` | `p2_certified_total_time_sec` |
| Gurobi | `best_bound` / `incumbent_obj` | `runtime` (`Model.Runtime`) |

RD-ALM's raw `final_cert_gap` can be `inf` even with a finite, feasible audited upper bound; it is **not** the formal certification metric. Final feasible bounds are tied to fixed-z audits. A wide SCP-LR interval is not itself a numerical failure. Likewise, a finite certified interval does not assert that the target tolerance or every inner-oracle requested precision was attained. Original `NUMERICAL_CLOSURE_LIMIT`, repair-skip and stop labels are preserved; do not infer the configured threshold from historical label text.

Two-resource nominal budgets are 1800 s for B<600, 2400 s for 600≤B<900, 3000 s for 900≤B<1200 and 3600 s for B≥1200. Three-resource algorithms use `outer_time_limit=1800`; its Gurobi baseline uses `baseline_time_limit=1800` even though that baseline's unused `outer_time_limit` field is 3600. Reported times are never capped to nominal budgets. Terminal audits and other work can overrun the limit; summed parallel solver times need not equal elapsed wall time.

The source audit retained two printed-native versus `Model.Runtime` discrepancies beyond decimal rounding alone: B1020 about 0.008 s and B1440 about 0.019 s. Both original numbers remain; the exact cause was not established. Native objectives, bounds and final statuses match. See `provenance/native_log_audit.csv`.

## Instance identity: exact hashes and explicit numerical equivalence

Each canonical manifest keeps **every original non-`args` field**; algorithm settings are separately in `configs/`. Excluding `args` is not permission to ignore instance data. The complete final payload is identical across methods within every latest instance. Seeds, probabilities, coefficients, tail/freeze/prefix records and final homogeneous requirements are checked, not only filenames.

The merged three-resource folder contains all 80 completed method records and 20 native Gurobi logs, including R17–R20. All four non-argument payloads match exactly per instance and match the selected historical stage-2 payload. Different original output roots are metadata, not different mathematical instances. Public path redactions affect only named path fields/lines; all original source hashes remain in provenance.

**Hash-stage caveat:** the 3D driver's legacy block-matrix prefix hashes are attached after the tail transformation but **before homogeneous A0**. They must not be presented as recomputed hashes of final homogeneous matrices. `instance_index.csv` adds full-final-payload and final serialized-requirement/task-period hashes, with an explicit hash-stage label. Final matrices were not independently regenerated in this environment.

The old draft and latest 2D manifests differ in PC1 projection-derived floating values: 39,642 scalar fields across 20 scales, maximum absolute difference **5.684341886080802e-14**. The source uses NumPy SVD; seeds and discrete settings agree and the executable AST agrees. The exact historical NumPy/BLAS cause cannot be identified from the missing environment record. These are actual numerical differences, not merely JSON formatting.

Default mode is **strict**. For a different environment, a user may explicitly select `--identity-mode numerical` on the launcher or fresh-output verifier. It permits at most **1e-13 absolute difference only on the exact documented 2D PC1-derived float paths** in `audit_common.py`. All other fields, structure, integer types, NaN locations, seed values and stored hash strings must match exactly. It does not relax the repository SHA checks and is not supported for nonexact 3D payloads. Both hashes and the maximum deviation are reported. This threshold covered all observed old/latest differences and was tested to reject changed seeds, non-whitelisted fields and larger deviations; it is not a guarantee of all future platforms' equivalence. This is a transparent numerical acceptance criterion, not a proof that perturbed real coefficients define exactly the same mathematical MILP or preserve every optimal solution.

## Historical screening boundary

The supplied archive contains 400 stage-1 candidate records and 60 stage-2 records. All 460 ranking/configuration/result bindings were checked against raw records. The final selected list is the first 20 entries of the archived stage-2 ranking, with matching triplets in the historical PowerShell selection list and matching latest full 3D payloads. The original stage-2 “next stage” flags select 30 candidates, so they must not be confused with the final 20-instance list.

The hunter/controller Python source is **absent**. The misleadingly named `stage3_1000s` directory contains only one **interrupted** candidate record: both its actual config and summary specify 600 s, its recorded runtime is 61.04700016975403 s, and its status is `INTERRUPTED`. The controller configuration also specifies 600 s. No completed third-stage screening can be inferred from that directory name. A nominal selected-result file is only a 3-byte BOM and cannot support a completed screening claim. The archived stage-2 ZIP is a verified duplicate of 780 expanded files and is not shipped twice. Historical commands also contain algorithm-parameter values that differ from formal reruns; they are evidence of selection, **not** the current run plan. This repository supports rerunning the fixed final instances, not automatic reconstruction of the complete historical screening workflow.

## Validation scope, immutability and rights

The submitted latest sources are byte-identical to the files in `code/`. Their docstring-stripped ASTs match both supplied predecessors; raw ASTs differ because documentation was changed. The 3D legacy parser reads `__doc__`, so its help prose may differ. No scientific executable statement was modified by this packaging task. The original run artifacts do not themselves embed a per-run source-file hash; latest-source attribution rests on the author's supplied version designation plus this static comparison, not an invented execution-time attestation.

Executed tests include archive CRC/extraction checks, input SHA inventory, syntax compilation, parser roundtrips, full archived audits, all-call previews, negative identity/certificate/overwrite checks and explicit missing-dependency failure. A structural-only manifest regeneration attempt did not finish its first case within its 20 s test limit; no complete regenerated instance or optimization result was obtained. It is **not** listed as a pass. No full optimization, solver license test, Windows PowerShell execution or original package-environment reconstruction was completed.

`repository_manifest.csv` hashes every release payload file except itself (self-hashing is not defined). `.gitattributes` disables newline conversion. Any authorized release edit needs a reviewed new manifest; do not regenerate hashes to hide unexpected changes. The outer ZIP checksum is delivered separately. Test execution may create ignored Python caches; these are not release evidence.

No `LICENSE` grant has been chosen. Publication and licensing remain the author's decisions; source visibility alone does not establish permission to reuse. Add the author-approved license only as a deliberate subsequent release change. This package has not been published or pushed to any remote service.
