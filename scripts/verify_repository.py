#!/usr/bin/env python3
"""Verify immutable references, actual parser reconstruction and certificate provenance."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from audit_common import (ROOT, METHODS, TABLES, AuditError, require, read_json, rows, sha256,
                          payload_hash, equal, plan, check_job_config, check_record, verify_output)

def verify_manifest() -> int:
    records = rows(ROOT / "repository_manifest.csv")
    expected = {r["path"]:r for r in records}
    require(len(expected) == len(records), "Duplicate file in repository manifest")
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()
              and ".git" not in p.relative_to(ROOT).parts
              and "__pycache__" not in p.relative_to(ROOT).parts
              and p.relative_to(ROOT).parts[0] not in ("outputs", ".venv", "venv")
              and p.name != "repository_manifest.csv"}
    require(actual == expected.keys(), f"Repository file set differs; missing={sorted(expected.keys()-actual)}, extra={sorted(actual-expected.keys())}")
    for name, item in expected.items():
        p = ROOT/name
        require(p.stat().st_size == int(item["bytes"]) and sha256(p) == item["sha256"], f"Repository byte hash mismatch: {name}")
    return len(records)

def verify() -> dict:
    files = verify_manifest()
    jobs = plan(); require(len(jobs) == 140, "Expected 140 formal calls")
    require(len({j["job_id"] for j in jobs}) == 140, "Repeated job ID")
    require(Counter(j["study"] for j in jobs) == {"2d":60,"3d":80}, "Formal call counts differ")
    expected_ids = {"2d":{f"B{b:04d}" for b in range(300,1441,60)}, "3d":{f"R{i:02d}" for i in range(1,21)}}
    jobmap = {j["job_id"]:j for j in jobs}; all_bounds = defaultdict(list); configs = {}
    for j in jobs: configs[j["job_id"]] = check_job_config(j)
    indices = rows(ROOT/"instances/instance_index.csv"); require(len(indices) == 40, "Expected 40 instances")
    require(len({(x['study'],x['instance_id']) for x in indices})==40,"Duplicate instance index")
    manifests = {}
    for r in indices:
        s,i = r["study"],r["instance_id"]; m = read_json(ROOT/r["manifest"]); f = m["family_payload"]
        require("args" not in m, "Canonical instances must separate runtime args")
        require(payload_hash(m) == r["payload_sha256"], "Canonical payload hash differs")
        for column,obj in [("family_payload_sha256",f),("final_requirements_sha256",f["dcap_requirements"]),
                           ("final_task_periods_sha256",f["dcap_task_periods"]),("scenario_capacities_sha256",m["scenario_capacities"])]:
            require(payload_hash(obj)==r[column], "Final component hash differs")
        require(f["dcap_nested_b60_prefix_verified"] and f["dcap_nested_b60_first_stage_verified"] and f["dcap_nested_b60_tail_verified"], "Archived prefix/freeze/tail flag failed")
        if s == "3d":
            require(f["dcap_homogeneous_A0_enabled"] and len(f["dcap_requirements"])==120,"Homogeneous A0 definition differs")
            require(all(equal(x,f["dcap_requirements"][0]) for x in f["dcap_requirements"]),"Final homogeneous requirements differ")
            require(all(equal(x,f["dcap_task_periods"][0]) for x in f["dcap_task_periods"]),"Final homogeneous task periods differ")
        jj=[j for j in jobs if j["study"]==s and j["instance_id"]==i]
        require(len(jj)==(3 if s=="2d" else 4),"Wrong per-instance call count")
        require([x for j in jj for x in j["methods_internal"]].__len__()==4 and
                set(x for j in jj for x in j["methods_internal"])==set(METHODS),"Missing/duplicate method")
        for j in jj:
            require(j["payload_sha256"]==r["payload_sha256"],"Cross-method full payload hash differs")
            a=configs[j["job_id"]]["args"]
            for field,key in [("family_seed","instance_seed"),("candidate_seed","dcap_candidate_seed_override"),
                              ("candidate_index","dcap_candidate_index_label"),("common_pool_seed","dcap_nested_b60_common_pool_seed_override"),
                              ("num_blocks","dcap_num_blocks"),("n_knapsacks","n_knapsacks")]:
                require(int(r[field])==a[key],"Instance index/config identity differs")
        manifests[(s,i)]=m
    for s in expected_ids: require({i for st,i in manifests if st==s}==expected_ids[s],"Instance set differs")
    # Full exact prefix comparisons of serialized final 2D coefficients.
    largest=manifests[("2d","B1440")];large=largest["family_payload"]
    for s,i in manifests:
        if s!='2d':continue
        m=manifests[(s,i)];f=m['family_payload'];b=int(i[1:])
        for k in ['dcap_block_probabilities','dcap_block_profiles','dcap_block_focus_resources','dcap_task_periods','dcap_requirements','dcap_rewards','dcap_profile_meta','dcap_pc1_projected_mild_scores']:
            require(equal(f[k],large[k][:b]),f"2D final prefix mismatch: {i}/{k}")
        for k in ['scenario_probabilities','scenario_capacities']:require(equal(m[k],largest[k][:b]),f"2D scenario prefix mismatch: {i}/{k}")
        for k in ['dcap_budget','dcap_tier_capacities','dcap_tier_costs','dcap_effective_z_ub','dcap_tail_start','dcap_tail_original_z_lb','dcap_tail_original_z_ub']:
            require(equal(f[k],large[k]),f"2D first-stage freeze mismatch: {i}/{k}")
    result_count=0
    fields=rows(ROOT/'provenance/result_field_provenance.csv')
    for study,tablepath in TABLES.items():
        records=rows(ROOT/tablepath);require(len(records)==80,"Expected 80 study result rows")
        require(len({(r['instance_id'],r['method_internal']) for r in records})==80,"Duplicate method result")
        require({r['instance_id'] for r in records}==expected_ids[study],"Result instance set differs")
        for r in records:
            j=jobmap[r['job_id']];method=r['method_internal'];label,stem=METHODS[method]
            require(j['study']==study and j['instance_id']==r['instance_id'] and method in j['methods_internal'],"Result/job binding differs")
            require(r['method']==label and r['source_file']==j['reference_result_dir']+'/'+stem+'.csv',"Method/source mapping differs")
            require(r['config']==j['config'] and r['instance_payload_sha256']==j['payload_sha256'],"Table provenance differs")
            raw=rows(ROOT/r['source_file']);require(len(raw)==1,"Source summary not single-row")
            a=configs[j['job_id']]['args'];nums=check_record(raw[0],method,a,(ROOT/r['source_file']).parent)
            require(r['effective_time_limit_sec']==str(a['baseline_time_limit' if method=='gurobi' else 'outer_time_limit']),"Reported budget differs")
            matches=[f for f in fields if f['table']==tablepath and f['instance_id']==r['instance_id'] and f['method']==label]
            require(len(matches)>=7,"Insufficient per-field provenance")
            for f in matches:
                require(f['source_file']==r['source_file'] and r[f['field']]==raw[0][f['source_column']],"Table cell differs from latest raw source string")
            all_bounds[(study,r['instance_id'])].append((nums['lb'],nums['ub']));result_count+=1
    for key,b in all_bounds.items():require(max(x for x,y in b)<=min(y for x,y in b)+1e-6,f"Cross-method bound conflict: {key}")
    selected=rows(ROOT/'screening/selected_instances.csv');ranks=rows(ROOT/'screening/stage2_300s_ranking.csv')
    require(len(selected)==20 and len(ranks)==60,"Selected/screening count differs")
    for n,(sel,rank) in enumerate(zip(selected,ranks),1):
        require(sel['final_ID']==f'R{n:02d}',"Selected ID order differs")
        require(all(sel[k]==rank[k] for k in ['family_seed','candidate_index','candidate_seed']),"Final top20 selection differs")
        require(payload_hash(manifests[('3d',sel['final_ID'])])==sel['payload_sha256_excluding_args'],"Selected complete instance identity differs")
    require(len(rows(ROOT/'screening/candidate_registry.csv'))==400 and len(rows(ROOT/'screening/stage1_60s_ranking.csv'))==400,"Stage1 candidate counts differ")
    require(len(read_json(ROOT/'screening/archived_candidate_run_configs.json')['runs'])==460,"Archived screening config count differs")
    require(not read_json(ROOT/'provenance/deep_input_audit.json')['errors'],"Recorded input audit has errors")
    return {'immutable_files_checked':files,'formal_calls':140,'instances':40,'method_results':result_count,
            'frozen_source_hashes':'PASS','parser_configuration_roundtrips':'PASS',
            'archived_identity_and_certificates':'PASS','source_table_string_matches':'PASS',
            'optimization_executed':False,'fresh_third_party_end_to_end_reproduction':'NOT_PERFORMED'}

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-output',type=Path,help='Check one completed fresh output directory instead of archived references')
    p.add_argument('--job-id');p.add_argument('--identity-mode',choices=['strict','numerical'],default='strict')
    args=p.parse_args()
    try:
        if args.run_output is not None:
            verify_manifest();require(args.job_id is not None,'--job-id required with --run-output')
            selected=[j for j in plan() if j['job_id']==args.job_id];require(len(selected)==1,'Unknown job ID')
            report=verify_output(selected[0],args.run_output.resolve(),args.identity_mode)
        else:
            require(args.job_id is None,'--job-id only valid with --run-output');report=verify()
        print(json.dumps({'status':'PASS',**report},ensure_ascii=False,indent=2));return 0
    except (AuditError,OSError,ValueError,KeyError,TypeError) as e:
        print(f'VERIFICATION FAILED: {e}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
