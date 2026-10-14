"""Pure controller boundary tests; no imports of the harness or native work."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('prolog_full', Path(__file__).with_name('prolog_full.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
supervisor_spec = importlib.util.spec_from_file_location('prolog_supervisor',Path(__file__).with_name('prolog_supervisor.py'))
supervisor = importlib.util.module_from_spec(supervisor_spec)
supervisor_spec.loader.exec_module(supervisor)


def waiting_guard(harness,row,manifest,report,round_index,lock_fd):
    child=os.fork()
    try:
        while True:os.waitpid(child,os.WNOHANG)
    finally:
        os.kill(child,9)
        os.waitpid(child,0)


class EditorialCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sealer = module.cold(module.ROOT/'tools/qualification/prolog_seal.py',
                                module.SEALER_SHA, 'prolog_full_editorial_fixture')
        module.install_sealed_editorial_reader(cls.sealer)

    def test_archived_python_keeps_exact_raw_and_recorded_ast_fingerprints(self):
        overrides = json.loads((module.ROOT/'experiments/prolog/editorial-substitutions.json').read_bytes())
        selected = [item for item in overrides['substitutions']
                    if item.get('field_rule') == 'python-migration-policy']
        self.assertEqual(len(selected), 3)
        evidence = self.sealer.Evidence(module.ROOT, overrides)
        for item in selected:
            with self.subTest(path=item['current_path']):
                path = module.ROOT/item['current_path']
                raw = evidence.read_bytes(str(path), item['historical_sha256'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item['current_sha256'])
                self.assertEqual(self.sealer.noneditorial_digest(raw, item['field_rule']),
                                 item['noneditorial_sha256'])

    def test_raw_changes_and_noneditorial_changes_are_still_rejected(self):
        original = b"dict(migration_policy='old narrative', samples=3)\n"
        current = original.replace(b'old narrative', b'new narrative')
        frozen_display = ("Module(body=[Expr(value=Call(func=Name(id='dict', ctx=Load()), "
            "keywords=[keyword(arg='migration_policy', value=Constant(value=None)), "
            "keyword(arg='samples', value=Constant(value=3))]))])")
        expected = hashlib.sha256(original).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root/'migration').mkdir()
            (root/'migration/reorganization-paths.tsv').write_text('original_path\tcurrent_path\n')
            path = root/'manifest.py'
            item = dict(current_path='manifest.py', historical_sha256=expected,
                        current_sha256=hashlib.sha256(current).hexdigest(),
                        technical_content_preserved=True, field_rule='python-migration-policy',
                        noneditorial_sha256=hashlib.sha256(frozen_display.encode()).hexdigest())
            path.write_bytes(current)
            evidence = self.sealer.Evidence(root, {'substitutions': [item]})
            self.assertEqual(evidence.read_bytes(str(path), expected), current)
            changed = current.replace(b'samples=3', b'samples=4')
            path.write_bytes(changed)
            with self.assertRaises(AssertionError):
                self.sealer.Evidence(root, {'substitutions': [item]}).read_bytes(str(path), expected)
            item['current_sha256'] = hashlib.sha256(changed).hexdigest()
            with self.assertRaises(AssertionError):
                self.sealer.Evidence(root, {'substitutions': [item]}).read_bytes(str(path), expected)

    def test_other_editorial_rules_still_use_the_frozen_reader(self):
        raw = b'{"next_step":"editorial narrative","qualified":true}'
        expected = hashlib.sha256(b'{"qualified":true}').hexdigest()
        self.assertEqual(self.sealer.noneditorial_digest(raw, 'json-next-step'), expected)
        with self.assertRaises(AssertionError):
            self.sealer.noneditorial_digest(raw, 'unknown-rule')


class SupervisorBoundary(unittest.TestCase):
    def test_owned_sampler_wait_after_kill_is_bounded(self):
        owner=supervisor.Owner(kernel=SimpleNamespace())
        owner.children[31]=dict(identity=None,reaped=False)
        with patch.object(supervisor.os,'waitpid',return_value=(0,0)), \
             patch.object(supervisor.time,'monotonic',side_effect=[0,1,4]), \
             patch.object(supervisor.signal,'pthread_sigmask',return_value=set()), \
             patch.object(supervisor.time,'sleep'):
            with self.assertRaises(supervisor.OwnedCleanupError):owner.waitpid(31,0)
        self.assertFalse(owner.children[31]['reaped'])

    def test_sampler_loop_deadline_keeps_cleanup_receipt(self):
        self.check_deadline(cleanup_errors=[])

    def test_cleanup_failure_keeps_original_deadline_and_registration(self):
        self.check_deadline(cleanup_errors=['owned group still running'])

    def check_deadline(self,cleanup_errors):
        handlers={}
        class FakeOwner:
            def __init__(self):
                self.children={};self.groups={};self.signals=[]
                self.events=[dict(type='native-group-started',pid=41,pgid=41,inherited_common_mutex=True)]
            def identity(self,pid):return dict(pid=pid)
            def fork(self):
                self.children[31]=dict(identity={'pid':31},reaped=False)
                self.groups[31]={'pid':31}
                return 31
            def waitpid(self,pid,options):
                if options:handlers['alarm'](14,None)
                self.children[pid]['reaped']=True
                return pid,9
            def kill(self,pid,signum):self.signals.append(dict(pid=pid,signal=signum))
            def cleanup(self):return cleanup_errors
            WNOHANG=os.WNOHANG
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)
            guard=SimpleNamespace(OUT=output,one_attempt=waiting_guard,sampler=lambda *args:None,
                                  save=module.new_json,sha=module.sha)
            report={'attempts':[]}
            with patch.object(supervisor.signal,'getitimer',return_value=(0.0,0.0)), \
                 patch.object(supervisor.signal,'getsignal',return_value=0), \
                 patch.object(supervisor.signal,'signal',side_effect=lambda sig,handler:handlers.update(alarm=handler)), \
                 patch.object(supervisor.signal,'setitimer'):
                expected=supervisor.OwnedCleanupError if cleanup_errors else supervisor.SupervisorDeadlineError
                with self.assertRaises(expected):
                    supervisor.one_attempt(guard,SimpleNamespace(),{'id':'prolog-pidigits-compact'},
                        {'timeout_seconds':21600,'supervisor_timeout_seconds':22200},report,1,99,FakeOwner)
            receipt_path=output/'outer-supervisor/001-prolog-pidigits-compact.json'
            receipt=json.loads(receipt_path.read_bytes())
            self.assertTrue(receipt['deadline_expired'])
            self.assertEqual(receipt['error_type'],'SupervisorDeadlineError')
            self.assertEqual(receipt['cleanup_errors'],cleanup_errors)
            self.assertTrue(receipt['owned_sampler_children']['31']['reaped'])
            self.assertEqual(receipt['native_registrations'][0]['pid'],41)
            self.assertEqual(receipt['signals'],[dict(pid=31,signal=9)])
            self.assertEqual(report['independent_supervisors'][0]['sha256'],module.sha(receipt_path))


class Full90Boundary(unittest.TestCase):
    def test_bounded_preparation_includes_the_retained_first_receipt(self):
        prep = dict(all20_bounded_outputs_qualified=True, terminal_evidence_complete=True,
                    new_bounded_cases=155, attempts=list(range(155)),
                    reused_attempts=['retained-regexredux-first-case'],
                    total_bounded_cases=156, case_results=list(range(156)))
        module.require_bounded_preparation(prep)
        for field, value in [('reused_attempts', []), ('case_results', list(range(155))),
                             ('attempts', list(range(156))), ('terminal_evidence_complete', False)]:
            with self.subTest(field=field):
                changed = dict(prep, **{field: value})
                with self.assertRaises(AssertionError):
                    module.require_bounded_preparation(changed)

    def test_only_canonical_full_references_are_bound_from_the_control_audit(self):
        audit = json.loads((module.ROOT/'archive/comparisons/r-apl-uiua-comparison/20261011/source-audit-r.json').read_bytes())
        expected = {str(module.CLBG / path): digest for path, digest in {
            'knucleotide/.build/knucleotide-input25000000.txt': '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa',
            'regexredux/.build/input5000000.txt': '97197f5957a12f8a859ba7edff6d97994daa18afacd77db21fa68c6f2e447e38',
            'pidigits/inputs/output-full.txt': 'bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c',
            'regexredux/inputs/output-full.txt': 'a37e6da1d43b332d5c0f4fc25b76090e9095d4c97c25f1a7186385e87706e4af',
        }.items()}
        resolver = SimpleNamespace(logical={'existing-pin': 'a'*64}, active={})
        module.bind_full_reference_pins(resolver, audit)
        self.assertEqual(resolver.logical, {'existing-pin': 'a'*64, **expected})
        self.assertEqual(resolver.active, {})
        resolver.logical[next(iter(expected))] = '0'*64
        with self.assertRaises(AssertionError):
            module.bind_full_reference_pins(resolver, audit)

    def test_launches_receipts_and_samples_are_separate_counts(self):
        registration=dict(pid=17,pgid=17,inherited_common_mutex=True,command=['/swipl','10000'])
        report=dict(programs={'one':dict(samples_seconds=[1.0])},attempts=[
            dict(attempt=1,supervised_native_group=registration),
            dict(attempt=2,wrapper_native_registration=registration,wrapper_supervisor_failure=True),
            dict(attempt=3,wrapper_supervisor_failure=True)])
        module.refresh_attempt_accounting(report)
        self.assertEqual((report['saved_attempts'],report['full_performance_runs'],report['qualified_samples']),(3,2,1))
        self.assertEqual(report['registered_native_attempts'],[1,2])
        self.assertEqual(report['native_launch_unconfirmed_attempts'],[3])

    def test_wrapper_failure_keeps_registration_even_with_broken_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory);(output/'attempts').mkdir()
            raw=output/'attempts/001-prolog-pidigits-compact.json'
            raw.write_bytes(b'{partial')
            guard=SimpleNamespace(OUT=output,REPORT=output/'report.json',save=module.new_json)
            row=dict(id='prolog-pidigits-compact',key='pidigits:compact',benchmark='pidigits',
                     attempts=[],samples_seconds=[])
            native=dict(pid=17,pgid=17,inherited_common_mutex=True,command=['/swipl','10000'])
            report=dict(programs={row['key']:row},attempts=[],active={'native':native})
            module.preserve_wrapper_failure(guard,report,row,1,RuntimeError('cleanup failed'))
            self.assertEqual(raw.read_bytes(),b'{partial')
            receipt=json.loads(raw.with_suffix('.wrapper.json').read_bytes())
            self.assertEqual(receipt['wrapper_error'],'cleanup failed')
            self.assertEqual(receipt['wrapper_native_registration'],native)
            self.assertIn('partial_receipt_error',receipt)
            self.assertEqual(report['full_performance_runs'],1)
            self.assertEqual(report['qualified_samples'],0)
            self.assertIsNone(report['active'])

    def test_exact_execution_cannot_replace_qlf_or_runtime_environment(self):
        row = dict(id='prolog-pidigits-compact', key='pidigits:prolog-pidigits-compact', benchmark='pidigits',
            language='prolog', source='/source.pl', source_sha256='a'*64, binary='/swipl', binary_sha256='b'*64,
            command=['/swipl','-s','/original.qlf','--','{n}'],cwd='/original',runtime_environment={'SWI_HOME_DIR':'/swi'},
            maximum_workers=1)
        module.require_execution(row,copy.deepcopy(row))
        for field,value in [('command',['/swipl','-s','/substituted.qlf','--','{n}']),
                            ('runtime_environment',{'SWI_HOME_DIR':'/other'}),('maximum_workers',2)]:
            altered=copy.deepcopy(row);altered[field]=value
            with self.assertRaises(AssertionError):module.require_execution(altered,row)

    def test_every_slot_is_a_fresh_rotation_and_no_duplicate_rounds(self):
        manifests={}
        for bench in module.BENCHES:
            ids=[f'prolog-{bench}-compact',f'prolog-{bench}-optimized','mech-aot-control']
            manifests[bench]=dict(profiles=[dict(id=i,key=bench+':'+i,language='mech' if i=='mech-aot-control' else 'prolog') for i in ids],
                orders=[dict(round=i+1,profiles=ids[i:]+ids[:i]) for i in range(3)])
        schedule=module.schedule_for(manifests)
        self.assertEqual(len(schedule),90)
        self.assertEqual(len({slot[3] for slot in schedule}),30)
        altered=copy.deepcopy(manifests)
        altered['pidigits']['orders'][2]=copy.deepcopy(altered['pidigits']['orders'][1])
        with self.assertRaises(AssertionError):module.schedule_for(altered)

    def test_success_requires_complete_output_owner_and_literal_gates(self):
        row={'command':['/swipl','{n}']}
        manifest=dict(size=10000,full_output_reference=dict(bytes=3,sha256='a'*64))
        attempt=dict(qualification_checks={key:True for key in module.GATES},qualified=True,
            full_workload=True,workload_n=10000,seconds=1.234,attempt=1,sampler_wait_status=0,exit_status=0,
            stdout_bytes=3,stdout_sha256='a'*64,command=['/swipl','10000'],execution_fingerprint='exact',
            supervised_native_group=dict(pid=17,pgid=17,inherited_common_mutex=True,command=['/swipl','10000']),
            validation=dict(bytes=3,sha256='a'*64,reference_match=True))
        module.qualified_sample(attempt,manifest,row,'exact')
        changes=[('stdout_sha256','b'*64),('seconds',float('nan')),('full_workload',False)]
        for field,value in changes:
            bad=copy.deepcopy(attempt);bad[field]=value
            with self.assertRaises(AssertionError):module.qualified_sample(bad,manifest,row,'exact')
        for key in module.GATES:
            bad=copy.deepcopy(attempt);bad['qualification_checks'][key]=1
            with self.assertRaises(AssertionError):module.qualified_sample(bad,manifest,row,'exact')
        bad=copy.deepcopy(attempt);bad['supervised_native_group']['pgid']=18
        with self.assertRaises(AssertionError):module.qualified_sample(bad,manifest,row,'exact')


if __name__=='__main__':unittest.main()
