#!/usr/bin/env python3
"""Standard-library static and negative tests; no optimization or license request."""
from __future__ import annotations
import contextlib
import copy
import io
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import audit_common as ac
import run_experiments as launcher
import verify_repository as verifier

class RepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jobs=ac.plan();cls.j=next(j for j in cls.jobs if j['job_id']=='2d_B0300_p1p2')
        cls.config=ac.read_json(ac.ROOT/cls.j['config'])
    def test_reference_verifier(self):
        self.assertEqual(verifier.verify()['method_results'],160)
    def test_all_python_syntax_without_importing_drivers(self):
        for p in ac.ROOT.rglob('*.py'):compile(p.read_text(encoding='utf-8-sig'),str(p),'exec')
    def test_actual_parser_roundtrips_all_calls(self):
        for j in self.jobs:ac.check_job_config(j)
    def test_frozen_sha_failure_is_detected(self):
        with patch.object(ac,'sha256',return_value='0'*64):
            with self.assertRaises(ac.AuditError):ac.check_job_config(self.j)
    def test_strict_and_numerical_identity_boundaries(self):
        x={'family_payload':{'dcap_pc1_projected_mild_beta':.1},'seed':4,'missing':math.nan}
        y=copy.deepcopy(x);y['family_payload']['dcap_pc1_projected_mild_beta']+=1e-14
        with self.assertRaises(ac.AuditError):ac.compare_instance(x,y,'2d','strict')
        self.assertFalse(ac.compare_instance(x,y,'2d','numerical')['strict_hash_equal'])
        with self.assertRaises(ac.AuditError):ac.compare_instance(x,y,'3d','numerical')
        y['family_payload']['dcap_pc1_projected_mild_beta']=.1+1e-10
        with self.assertRaises(ac.AuditError):ac.compare_instance(x,y,'2d','numerical')
        for key,value in [('seed',5),('seed',4.0),('missing',0.0)]:
            y=copy.deepcopy(x);y[key]=value
            with self.assertRaises(ac.AuditError):ac.compare_instance(x,y,'2d','numerical')
        y=copy.deepcopy(x);y['unlisted']=1
        with self.assertRaises(ac.AuditError):ac.compare_instance(x,y,'2d','numerical')
    def test_rd_alm_uses_audited_not_raw_infinite_gap(self):
        r=ac.rows(ac.ROOT/self.j['reference_result_dir']/'RD_ALM.csv')[0]
        mutated=dict(r);mutated['final_cert_gap']='inf';mutated['final_obj']='inf'
        self.assertEqual(ac.check_record(r,'p2',self.config['args']),ac.check_record(mutated,'p2',self.config['args']))
    def test_bounds_and_gap_errors_rejected(self):
        r=ac.rows(ac.ROOT/self.j['reference_result_dir']/'SCP_ALM.csv')[0]
        for field,value in [('global_lb',str(float(r['global_ub'])+1)),('cert_rel_gap','0.75'),('returned_primal_residual','0.001')]:
            bad=dict(r);bad[field]=value
            with self.assertRaises(ac.AuditError):ac.check_record(bad,'p1',self.config['args'])
    def test_protected_output_paths(self):
        for d in ['.','code','configs','instances','results','provenance','screening','scripts']:
            with self.assertRaises(ac.AuditError):launcher.output_path(d,self.j)
    def test_nonempty_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/self.j['output_relative_dir'];target.mkdir(parents=True)
            sentinel=target/'sentinel';sentinel.write_text('keep')
            with self.assertRaises(ac.AuditError):launcher.output_path(d,self.j)
            self.assertEqual(sentinel.read_text(),'keep')
    def test_preview_all_calls_and_paths(self):
        for study,count in [('2d',60),('3d',80)]:
            p=subprocess.run([sys.executable,str(ac.ROOT/'scripts/run_experiments.py'),'--study',study],capture_output=True,text=True,check=False)
            self.assertEqual(p.returncode,0,p.stderr);self.assertIn(f'DRY-RUN: {count} recorded calls',p.stdout)
        target=Path('/tmp/path with spaces')/self.j['output_relative_dir'];cmd=launcher.command(self.j,target)
        self.assertEqual(cmd[cmd.index('--out_dir')+1],str(target));self.assertEqual(cmd[1],str(ac.ROOT/self.j['driver']))
        self.assertNotIn('--help',cmd)
    def test_unknown_selection_fails(self):
        p=subprocess.run([sys.executable,str(ac.ROOT/'scripts/run_experiments.py'),'--study','3d','--instance','R99'],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertIn('No matching',p.stderr)
    def test_missing_dependency_preflight_is_explicit(self):
        with patch.object(launcher.importlib.util,'find_spec',return_value=None):
            with self.assertRaisesRegex(ac.AuditError,'Missing runtime dependencies'):
                launcher.environment()
    def test_simulated_process_failure_does_not_claim_success(self):
        # Deliberately simulated; this is not a solver run.
        with tempfile.TemporaryDirectory() as d:
            args=['run_experiments.py','--study','2d','--instance','B0300','--run-group','p1p2','--output-root',d,'--execute']
            out,err=io.StringIO(),io.StringIO()
            with patch.object(sys,'argv',args),patch.object(launcher,'environment',return_value={'test':'SIMULATED'}),patch.object(launcher.subprocess,'run',return_value=subprocess.CompletedProcess([],7)),patch.object(launcher,'verify_output') as verify,contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                self.assertEqual(launcher.main(),2);verify.assert_not_called()
            self.assertIn('exit 7',err.getvalue());self.assertNotIn('All selected calls completed',out.getvalue())
            self.assertFalse((Path(d)/self.j['output_relative_dir']).exists())

if __name__=='__main__':unittest.main(verbosity=2)
