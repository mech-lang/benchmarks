"""Small saved-record reconciliation faults; no runtime closure or native work."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('uiua_retained_test',HERE/'uiua_retained_reconcile.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
MODULES=r.load_modules()


def fixture():
    def read(name):return json.loads((r.ARCHIVE/name).read_bytes())
    report=read('results/timings-uiua.json')
    sources={key:(r.ROOT/'archive/comparisons'/Path(report['programs'][key]['source']).relative_to(r.HISTORICAL)).read_bytes()
             for key in r.COUNTS}
    return dict(report=report,audit=read('source-audit-uiua.json'),tree_work=read('results/uiua/source-audit.json'),
        nbody_work=read('uiua-nbody-v3/results/source-audit.json'),
        count_approval=json.loads(r.COUNT_APPROVAL.read_bytes()),sources=sources)


class RetainedUiua(unittest.TestCase):
    def check(self,values):return r.reconcile(**values,modules=MODULES)

    def test_actual_saved_scope_and_alias_have_fifteen_distinct_observations(self):
        values=fixture();before=copy.deepcopy(values)
        result=self.check(values)
        self.assertEqual(values,before)
        self.assertEqual(result['accepted_native_observations'],15)
        self.assertEqual(result['subject_native_observations'],9)
        self.assertEqual(result['control_native_observations'],6)
        self.assertEqual(result['profiles'][r.TREE_ALIAS]['native_observations'],0)
        self.assertEqual(result['profiles'][r.TREE_ALIAS]['timing_alias_of'],r.TREE)
        self.assertEqual(result['excluded_attempt']['attempt_number'],70)
        self.assertFalse(result['file_integrity_verified'])
        self.assertFalse(result['chart_admission'])
        self.assertEqual(result['native_processes_started'],0)

    def test_dropped_compiler_overlap_cannot_be_admitted_or_hidden(self):
        for mutation in ('admit','hide','replace'):
            values=fixture()
            if mutation=='admit':values['report']['attempts'][69]['valid_environment']=True
            elif mutation=='hide':values['report']['discarded']=[]
            else:
                row=values['report']['programs'][r.NBODY_COMPACT]
                row['samples_seconds'][1]=values['report']['attempts'][69]['seconds']
            with self.assertRaises((ValueError,AssertionError)):self.check(values)

    def test_alias_cannot_claim_own_trials_or_changed_source(self):
        for mutation in ('attempts','source'):
            values=fixture()
            if mutation=='attempts':values['report']['programs'][r.TREE_ALIAS]['attempts']=[59,61,63]
            else:values['sources'][r.TREE_ALIAS]+=b'changed'
            with self.assertRaises((ValueError,AssertionError)):self.check(values)

    def test_unrecorded_environment_or_legacy_migration_is_rejected(self):
        for mutation in ('environment','lineage'):
            values=fixture()
            if mutation=='environment':values['report']['attempts'][58].pop('runtime_environment')
            else:values['report']['attempts'][58]['prior_guard_revision_attempt_number']=1
            with self.assertRaisesRegex(ValueError,'original repaired-guard'):self.check(values)

    def test_source_work_and_canonical_count_changes_fail(self):
        for mutation in ('tree','nbody','count','bytes'):
            values=fixture()
            if mutation=='tree':values['tree_work']['binarytrees']['fresh_leaf_allocation']=False
            elif mutation=='nbody':values['nbody_work']['host_helpers']=True
            elif mutation=='count':values['count_approval']['profiles'][0]['canonical_loc']=20
            else:values['sources'][r.NBODY_COMPACT]+=b'changed'
            with self.assertRaises((ValueError,AssertionError)):self.check(values)

    def test_bad_output_live_group_or_overlap_is_rejected(self):
        for mutation in ('output','group','overlap'):
            values=fixture();attempt=values['report']['attempts'][60]
            if mutation=='output':attempt['validation']['sha256']='0'*64
            elif mutation=='group':attempt['remaining_group_members']=[{'pid':123}]
            else:attempt['started_at']=values['report']['attempts'][59]['started_at']
            with self.assertRaises(ValueError):self.check(values)

    def test_synthetic_missing_replacement_or_shortened_work_is_rejected(self):
        for mutation in ('replacement','work','order'):
            values=fixture()
            if mutation=='replacement':values['report']['attempts'][73]['sample']=2
            elif mutation=='work':values['report']['attempts'][73]['workload_n']=1000
            else:values['report']['orders']['nbody'][2].reverse()
            with self.assertRaises((ValueError,AssertionError)):self.check(values)

    def test_file_context_freezes_original_pins_and_checks_consumer_after_replay(self):
        calls=[]
        class Files:
            def __init__(self):self.pins={}
            def verify(self,path,digest):self.pins[str(path)]=digest
            def read(self,path,digest):self.verify(path,digest);return Path(path).read_bytes()
            def final_check(self,original_pins=()):
                calls.append('pins')
                if not original_pins:raise AssertionError('Missing immutable pin snapshot')
                if self.pins:raise AssertionError('Test consumer failed to clear mutable pins')
        with tempfile.TemporaryDirectory() as directory:
            lock=Path(directory)/'lock';lock.touch()
            core=SimpleNamespace(**MODULES['core'].__dict__)
            core.LOCK=lock;core.LOCK_INODE=lock.stat().st_ino;core.Files=Files
            # Recorded historical mutex identity remains the real pathname;
            # only this context's lease is substituted for the pure fixture.
            real_reconcile=r.reconcile
            def reconcile_without_lock_substitution(*args,**kwargs):
                modules=dict(args[-1],core=MODULES['core'])
                return real_reconcile(*args[:-1],modules)
            def final_check():
                with lock.open('r+') as other:
                    with self.assertRaises(BlockingIOError):r.fcntl.flock(other,r.fcntl.LOCK_EX|r.fcntl.LOCK_NB)
                calls.append('consumer')
                raise ValueError('late consumer change')
            def cleanup():
                with lock.open('r+') as other:
                    with self.assertRaises(BlockingIOError):r.fcntl.flock(other,r.fcntl.LOCK_EX|r.fcntl.LOCK_NB)
                calls.append('cleanup')
            with patch.object(r,'load_modules',return_value=dict(MODULES,core=core)),patch.object(r,'reconcile',side_effect=reconcile_without_lock_substitution):
                with self.assertRaisesRegex(ValueError,'late consumer change'):
                    with r.review_context('0'*64,on_exit_failure=cleanup,final_consumer_check=final_check) as (_,files):
                        calls.append('body');files.pins.clear()
            self.assertEqual(calls,['body','pins','consumer','cleanup'])

    def test_mutex_path_replaced_during_pin_replay_fails_before_consumer_check(self):
        calls=[]
        with tempfile.TemporaryDirectory() as directory:
            lock=Path(directory)/'lock';lock.touch();retained=Path(directory)/'original-lock'
            class Files:
                def __init__(self):self.pins={}
                def verify(self,path,digest):self.pins[str(path)]=digest
                def read(self,path,digest):self.verify(path,digest);return Path(path).read_bytes()
                def final_check(self,original_pins=()):
                    if not original_pins:raise AssertionError('Missing immutable original pins')
                    calls.append('pins');lock.rename(retained);lock.touch()
            core=SimpleNamespace(**MODULES['core'].__dict__)
            core.LOCK=lock;core.LOCK_INODE=lock.stat().st_ino;core.Files=Files
            real_reconcile=r.reconcile
            def reconcile_without_lock_substitution(*args,**kwargs):
                return real_reconcile(*args[:-1],dict(args[-1],core=MODULES['core']))
            def cleanup():
                with retained.open('r+') as other:
                    with self.assertRaises(BlockingIOError):r.fcntl.flock(other,r.fcntl.LOCK_EX|r.fcntl.LOCK_NB)
                calls.append('cleanup')
            with patch.object(r,'load_modules',return_value=dict(MODULES,core=core)),patch.object(r,'reconcile',side_effect=reconcile_without_lock_substitution):
                with self.assertRaisesRegex(ValueError,'mutex pathname replaced'):
                    with r.review_context('0'*64,on_exit_failure=cleanup,final_consumer_check=lambda:calls.append('consumer')):
                        calls.append('body')
            self.assertEqual(calls,['body','pins','cleanup'])


if __name__=='__main__':unittest.main()
