#!/usr/bin/env python3
"""Portable outer launcher. Preview is default; frozen algorithm files are never edited."""
from __future__ import annotations
import argparse
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from audit_common import ROOT,AuditError,require,plan,check_job_config,verify_output

PROTECTED=('code','configs','instances','results','provenance','screening','scripts')

def output_path(root: str, job: dict) -> Path:
    base=Path(root).expanduser()
    if not base.is_absolute():base=ROOT/base
    base=base.resolve();target=(base/job['output_relative_dir']).resolve()
    require(base!=ROOT,'Output root cannot be the repository root')
    if base.is_relative_to(ROOT):
        require(base.relative_to(ROOT).parts[0]=='outputs','Inside the repository, outputs must be under outputs/')
    require(not ROOT.is_relative_to(target),'Output target cannot contain the repository')
    if target.is_relative_to(ROOT):
        require(target.relative_to(ROOT).parts[0]=='outputs','Resolved output target is inside a protected repository directory')
    require(not target.exists() or (target.is_dir() and not any(target.iterdir())),f'Refusing to overwrite nonempty output: {target}')
    return target

def environment() -> dict:
    result={'python':sys.version.split()[0],'python_executable':sys.executable}
    missing=[]
    for name in ['numpy','gurobipy']:
        if importlib.util.find_spec(name) is None:missing.append(name)
        else:
            try: result[name]=importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:result[name]='importable; package version not recorded'
    require(not missing,'Missing runtime dependencies: '+', '.join(missing)+'. Install requirements.txt and provide a valid Gurobi environment. No optimization was started.')
    # Loading the extension detects binary/OS linkage errors but does not assert license availability.
    import numpy  # noqa: F401
    import gurobipy  # noqa: F401
    result['gurobi_engine']='.'.join(map(str,gurobipy.gurobi.version()))
    result['reference_engine_matches']=(result['gurobi_engine']=='13.0.1')
    if not result['reference_engine_matches']:
        print('WARNING: Gurobi engine differs from the archived 13.0.1 environment; this is not an exact environment reproduction.',file=sys.stderr)
    result['license']='NOT_TESTED_BY_IMPORT';return result

def command(job:dict,target:Path) -> list[str]:
    args=list(job['argv']);require(args.count('--out_dir')==1,'Ambiguous output flag')
    args[args.index('--out_dir')+1]=str(target)
    return [sys.executable,str(ROOT/job['driver']),*args]

def display(cmd:list[str]) -> str:
    return subprocess.list2cmdline(cmd) if os.name=='nt' else shlex.join(cmd)

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study',required=True,choices=['2d','3d'])
    p.add_argument('--instance',default='all',help='all, B0300/B0360/.../B1440 for 2d, or R01/.../R20 for 3d')
    p.add_argument('--run-group',default='all',choices=['all','p1p2','p1','p2','p1_norho','gurobi'])
    p.add_argument('--output-root',default='outputs',help='Repo-relative directory or absolute output root; ASCII paths recommended on Windows')
    p.add_argument('--execute',action='store_true',help='Actually execute; without this flag only preview')
    p.add_argument('--show-commands',action='store_true')
    p.add_argument('--check-environment',action='store_true')
    p.add_argument('--identity-mode',choices=['strict','numerical'],default='strict')
    a=p.parse_args()
    try:
        from verify_repository import verify_manifest
        verify_manifest()
        jobs=[j for j in plan() if j['study']==a.study and (a.instance=='all' or j['instance_id']==a.instance)
              and (a.run_group=='all' or j['run_group']==a.run_group)]
        require(bool(jobs),'No matching formal calls. 2D SCP-ALM and RD-ALM use joint run-group p1p2; 3D uses p1 and p2 separately.')
        targets=[]
        for j in jobs:
            check_job_config(j);targets.append(output_path(a.output_root,j))
        if a.check_environment or a.execute:print(json.dumps(environment(),ensure_ascii=False))
        print(f"{'EXECUTE' if a.execute else 'DRY-RUN'}: {len(jobs)} recorded calls; identity mode={a.identity_mode}")
        for j,target in zip(jobs,targets):
            cmd=command(j,target)
            print(f"{j['job_id']} -> {target}")
            if a.show_commands:print(display(cmd))
            if not a.execute:continue
            # Recheck immediately before dispatch. There is no resume/overwrite flag.
            output_path(a.output_root,j)
            completed=subprocess.run(cmd,cwd=ROOT,shell=False,check=False)
            require(completed.returncode==0,f"Driver failed for {j['job_id']} (exit {completed.returncode}); subsequent jobs were not started. Partial output, if any, remains for inspection.")
            verified=verify_output(j,target,a.identity_mode)
            print(json.dumps(verified,ensure_ascii=False))
        print('All selected calls completed and passed output checks.' if a.execute else 'Preview complete. No driver executed and no output directory created.')
        return 0
    except (AuditError,OSError,ValueError,KeyError,TypeError,ImportError) as e:
        print(f'LAUNCH FAILED: {e}',file=sys.stderr);return 2
    except KeyboardInterrupt:
        print('Interrupted; no success is claimed. Inspect partial outputs before rerunning.',file=sys.stderr);return 130
if __name__=='__main__':raise SystemExit(main())
