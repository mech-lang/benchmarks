"""Fault tests for bounded Prolog conformance; no native or runtime hashes.

Receipt files and preparation outputs are small synthetic artifacts. The two
controller tests stop during inspection, before any candidate fixture runs.
"""
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


PATH = Path(__file__).with_name('prolog_revcomp_bounded.py')
SPEC = importlib.util.spec_from_file_location('tested_prolog_revcomp_bounded', PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value))


class PrologBoundedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The fixture oracle is definition-only and uses a different algorithm
        # from the candidate; materialize its manifest in memory, not a JVM/VM.
        oracle = m.module(m.PACKET/'fixtures.py', m.FIXTURES_SHA, 'test_revcomp_oracle')
        oracle.self_check()
        cases = []
        for identity, raw in oracle.cases():
            case = dict(id=identity, stdin=identity+'/stdin.bin', input_bytes=len(raw), input_sha256=digest(raw))
            try:
                expected = oracle.reference(raw)
            except oracle.InvalidNucleotide as error:
                case.update(expected_status='invalid-iupac', expected_invalid_code=error.code)
            else:
                case.update(expected_status='success', stdout=identity+'/expected.stdout',
                            output_bytes=len(expected), output_sha256=digest(expected))
            cases.append(case)
        cls.manifest = dict(schema='prolog-revcomp-linear-fixtures-v1', generator_sha256=m.FIXTURES_SHA,
                            diagnostic_chunk_sizes=list(oracle.CHUNK_SIZES), cases=cases)

    def receipt(self, directory, *, failure=False, compiler_warning=False, stdout=b'>r\nACGT\n', stderr=b'', command=None,
                environment=None, payload=b'>r\nACGT\n', pid=99123):
        command = ['retained-swipl', '-g', 'main'] if command is None else command
        environment = {'SWI_HOME_DIR':'/retained/swipl'} if environment is None else environment
        common = dict(kind='prolog-revcomp-bounded', command=command, environment=environment,
            cwd=str(directory), stdin_bytes=len(payload), stdin_sha256=digest(payload),
            started_at='2026-10-14T12:00:00+00:00', inherited_common_mutex=True,
            common_mutex_inode=m.kb.LOCK_INODE, process_timeout_seconds=m.kb.TIMEOUT,
            cleanup_timeout_seconds=m.kb.CLEANUP_TIMEOUT, maximum_process_group_rss_bytes=m.kb.RSS_LIMIT,
            native_file_limit_bytes=m.kb.FILE_LIMIT, stdout_capture_limit_bytes=m.kb.FILE_LIMIT+m.kb.PIPE_CHUNK)
        start = dict(common, status='starting', native_process_started=False)
        identity = dict(pid=pid, pgid=pid, ppid=os.getpid(), birth_seconds=1000, birth_microseconds=111, status=2)
        active = dict(common, status='running', native_process_started=True, pid=pid, pgid=pid, identity=identity)
        final = dict(active, status='failed' if failure or compiler_warning else 'native-passed', exit_status=1 if failure else 0,
            direct_child_reaped=True, remaining_process_group=[], stop_signals=[], cleanup_errors=[],
            kernel_monitor_samples=3, observed_peak_process_group_rss_bytes=1024,
            leader_identity_before_reap=dict(identity, status=5), stdout_bytes=len(stdout),
            stdout_sha256=digest(stdout), stderr_bytes=len(stderr), stderr_sha256=digest(stderr))
        if failure:
            final.update(error_type='AssertionError', error='Native command exited unsuccessfully', timed_out=False)
        elif compiler_warning:
            final.update(error_type='AssertionError', error='Unexpected stderr; raw bytes retained', timed_out=False)
        for name, value in [('start',start), ('active',active), ('process',final)]:
            dump(directory/(name+'.json'), value)
        (directory/'stdout.bin').write_bytes(stdout)
        (directory/'stderr.bin').write_bytes(stderr)
        return dict(directory=directory, command=command, environment=environment, payload=payload,
                    pid=pid, expected_failure=failure, compiler_warning=compiler_warning)

    def mutate(self, directory, name, change):
        path = directory/(name+'.json')
        row = json.loads(path.read_bytes())
        change(row)
        dump(path, row)

    def test_complete_schedule_covers_each_fixture_and_capacity(self):
        rows = m.schedule(self.manifest)
        self.assertEqual(len(rows), 540)
        self.assertEqual(len({row['id'] for row in rows}), 540)
        self.assertEqual(sum(row['case']['expected_status'] == 'success' for row in rows), 470)
        self.assertEqual(sum(row['case']['expected_status'] == 'invalid-iupac' for row in rows), 70)
        for case in self.manifest['cases']:
            self.assertEqual([row['capacity'] for row in rows if row['case']['id'] == case['id']],
                             [None,1,2,3,7,59,60,61,64,127])

    def test_corrupt_fixture_schedule_rejected(self):
        changes = [lambda x:x['cases'].pop(),
                   lambda x:x['cases'].__setitem__(0, copy.deepcopy(x['cases'][1])),
                   lambda x:x['cases'][0].update(expected_status='invalid-iupac', expected_invalid_code=33),
                   lambda x:x['cases'][0].update(id='../escape'),
                   lambda x:x.update(generator_sha256='0'*64),
                   lambda x:x['diagnostic_chunk_sizes'].reverse()]
        for change in changes:
            manifest = copy.deepcopy(self.manifest); change(manifest)
            with self.subTest(manifest=manifest['cases'][0]['id']), self.assertRaises((AssertionError, KeyError)):
                m.schedule(manifest)

    def test_unplanned_capacity_cannot_reach_command(self):
        for capacity in (True, False, 0, -1, 5, '1', 1.0):
            with self.subTest(capacity=capacity), self.assertRaises(AssertionError):
                m.candidate_command('retained-swipl', Path('/retained/candidate.qlf'), capacity)

    def test_clean_success_and_exact_expected_native_failure_receipts(self):
        for failure in (False, True):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                args = self.receipt(Path(temporary), failure=failure)
                result = m.check_receipt(**args)
                self.assertEqual(result['exit_status'], int(failure))

    def test_missing_active_or_final_receipt_fails(self):
        for name in ('active', 'process'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary); args = self.receipt(directory)
                (directory/(name+'.json')).unlink()
                with self.assertRaises(FileNotFoundError): m.check_receipt(**args)

    def test_unrelated_parent_is_not_owned_even_when_receipts_agree(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary); args = self.receipt(directory)
            self.mutate(directory, 'active', lambda r:r['identity'].update(ppid=os.getpid()+99999))
            self.mutate(directory, 'process', lambda r:(r['identity'].update(ppid=os.getpid()+99999),
                r['leader_identity_before_reap'].update(ppid=os.getpid()+99999)))
            with self.assertRaises(AssertionError): m.check_receipt(**args)

    def test_changed_birth_unreaped_child_and_remaining_group_fail(self):
        changes = [lambda r:r['leader_identity_before_reap'].update(birth_microseconds=112),
                   lambda r:r.update(direct_child_reaped=False),
                   lambda r:r.update(remaining_process_group=[{'pid':99124}]),
                   lambda r:r.update(stop_signals=[9]),
                   lambda r:r.update(native_process_started=False),
                   lambda r:r.update(kernel_monitor_samples=0)]
        for change in changes:
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary); args = self.receipt(directory)
                self.mutate(directory, 'process', change)
                with self.assertRaises(AssertionError): m.check_receipt(**args)

    def test_wrong_registered_pid_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.receipt(Path(temporary)); args['pid'] += 1
            with self.assertRaises(AssertionError): m.check_receipt(**args)

    def test_modified_kind_policy_and_lock_fail(self):
        changes = [('kind','other-stage'), ('common_mutex_inode',m.kb.LOCK_INODE+1),
                   ('process_timeout_seconds',m.kb.TIMEOUT+1), ('cleanup_timeout_seconds',m.kb.CLEANUP_TIMEOUT+1),
                   ('maximum_process_group_rss_bytes',m.kb.RSS_LIMIT+1),
                   ('native_file_limit_bytes',m.kb.FILE_LIMIT+1),
                   ('stdout_capture_limit_bytes',m.kb.FILE_LIMIT+m.kb.PIPE_CHUNK+1)]
        for key, value in changes:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary); args = self.receipt(directory)
                for name in ('start','active','process'):
                    self.mutate(directory, name, lambda r:r.update({key:value}))
                with self.assertRaises(AssertionError): m.check_receipt(**args)

    def test_exit_one_is_not_a_generic_failure_escape(self):
        changes = [lambda r:r.update(exit_status=2), lambda r:r.update(exit_status=-9),
                   lambda r:r.update(error='Unexpected stderr; raw bytes retained'),
                   lambda r:r.update(error_type='TimeoutExpired'),
                   lambda r:r.update(status='native-passed'), lambda r:r.update(timed_out=True)]
        for change in changes:
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary); args = self.receipt(directory, failure=True)
                self.mutate(directory, 'process', change)
                with self.assertRaises(AssertionError): m.check_receipt(**args)

    def test_known_compiler_warning_reconciles_only_exit_zero_stderr_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            args=self.receipt(directory,compiler_warning=True,stdout=b'',stderr=m.COMPILE_WARNING)
            self.assertEqual(m.check_receipt(**args)['exit_status'],0)
            self.mutate(directory,'process',lambda r:r.update(error='Native command exited unsuccessfully'))
            with self.assertRaises(AssertionError):m.check_receipt(**args)
        with tempfile.TemporaryDirectory() as temporary:
            args=self.receipt(Path(temporary),compiler_warning=True,stdout=b'',stderr=m.COMPILE_WARNING)
            args['expected_failure']=True
            with self.assertRaises(AssertionError):m.check_receipt(**args)

    def test_modified_input_or_retained_output_fails(self):
        for name in ('stdout','stderr'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary); args = self.receipt(directory)
                with (directory/(name+'.bin')).open('ab') as stream: stream.write(b'added')
                with self.assertRaises(AssertionError): m.check_receipt(**args)
        with tempfile.TemporaryDirectory() as temporary:
            args = self.receipt(Path(temporary)); args['payload'] += b'changed'
            with self.assertRaises(AssertionError): m.check_receipt(**args)

    def test_success_requires_complete_bytes_and_empty_stderr(self):
        expected = b'>r\nACGT\n'
        case = dict(expected_status='success', output_bytes=len(expected), output_sha256=digest(expected))
        self.assertEqual(m.check_case(case,expected,b''), 'exact-output')
        for stdout, stderr in [(expected[:-1],b''), (expected+b'\n',b''),
                               (expected.replace(b'ACGT',b'AGCT'),b''), (expected,b'warning\n')]:
            with self.subTest(stdout=stdout,stderr=stderr), self.assertRaises(AssertionError):
                m.check_case(case,stdout,stderr)

    def invalid_case(self):
        return copy.deepcopy(next(case for case in self.manifest['cases'] if case['id']=='invalid-space'))

    def test_invalid_iupac_rejects_wrong_code_diagnostic_and_extra_output(self):
        case = self.invalid_case()
        stderr = b"ERROR: [Thread main] Domain error: `iupac_nucleotide' expected, found `32'\n"
        self.assertEqual(m.check_case(case,b'>r\n',stderr), 'expected-invalid-iupac')
        for stdout, bad_stderr in [(b'>r\n',stderr.replace(b'32',b'33')),
                                  (b'>r\n',stderr+b'extra\n'), (b'>r\n',b'failure\n'),
                                  (b'wrong header\n',stderr), (b'>r\nextra\n',stderr)]:
            with self.subTest(stdout=stdout,stderr=bad_stderr), self.assertRaises(AssertionError):
                m.check_case(case,stdout,bad_stderr)

    def compiler_metadata(self, directory, mode='compile', authored=None):
        authored = directory/'authored' if authored is None else authored
        target = authored/('candidate.pl' if mode=='compile' else 'candidate.qlf')
        plan = dict(environment={'SWI_HOME_DIR':'/retained/swipl'},
                    pins={'/retained/json.pl':'a'*64,'/retained/json.dylib':'b'*64})
        data = dict(mode=mode,target=str(target),wam=str(directory/'candidate.wam'),
            runtime=dict(version_components=[10,0,2],version_data='swi(10,0,2,[])', architecture='arm64-darwin',
                         bounded=False,gc=True,stack_limit=8*1024**3,home='/retained/swipl'),
            loaded_sources=[str(authored/'candidate.pl'),'/retained/json.pl'],
            foreign_libraries=[dict(file='foreign(json)',public='[]',resolved_path='/retained/json.dylib')])
        dump(directory/'loaded-inputs.json',data)
        (directory/'candidate.wam').write_text('clbg_revcomp_linear:read_blocks/2\nclbg_revcomp_linear:emit_codes/5\n')
        return dict(directory=directory,mode=mode,target=target,authored=authored,plan=plan)

    def test_compile_and_inspection_require_actual_emitter_arity(self):
        for mode in ('compile','inspect'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                args = self.compiler_metadata(Path(temporary),mode)
                self.assertEqual(m.check_compiler_metadata(**args)['mode'], mode)

    def test_wrong_runtime_policy_or_compiler_target_fails(self):
        changes = [lambda r:r['runtime'].update(version_components=[10,0,1]),
                   lambda r:r['runtime'].update(version_data='swi(10,0,2,[modified])'),
                   lambda r:r['runtime'].update(architecture='x86_64-linux'),
                   lambda r:r['runtime'].update(bounded=True), lambda r:r['runtime'].update(gc=False),
                   lambda r:r['runtime'].update(stack_limit=1024),lambda r:r['runtime'].update(home='/different'),
                   lambda r:r.update(target='/different/candidate.pl'),lambda r:r.update(mode='runtime'),
                   lambda r:r.update(wam='/different/candidate.wam')]
        for change in changes:
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary); args = self.compiler_metadata(directory)
                self.mutate(directory,'loaded-inputs',change)
                with self.assertRaises(AssertionError): m.check_compiler_metadata(**args)

    def test_unpinned_source_or_foreign_dependency_fails(self):
        changes = [lambda r:r['loaded_sources'].append('/unretained/injected.pl'),
                   lambda r:r['foreign_libraries'].append(dict(resolved_path='/unretained/injected.dylib')),
                   lambda r:r.update(loaded_sources=['/retained/json.pl'])]
        for change in changes:
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary); args = self.compiler_metadata(directory)
                self.mutate(directory,'loaded-inputs',change)
                with self.assertRaises(AssertionError): m.check_compiler_metadata(**args)

    def test_missing_vm_parser_or_emitter_fails(self):
        for text in ('clbg_revcomp_linear:read_blocks/2\n','clbg_revcomp_linear:emit_codes/5\n',
                     'clbg_revcomp_linear:read_blocks/2\nclbg_revcomp_linear:emit_codes/6\n'):
            with tempfile.TemporaryDirectory() as temporary:
                directory=Path(temporary); args=self.compiler_metadata(directory)
                (directory/'candidate.wam').write_text(text)
                with self.assertRaises(AssertionError): m.check_compiler_metadata(**args)

    def test_inventory_rejects_symlink_and_detects_late_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary); (directory/'raw.bin').write_bytes(b'original')
            before=m.inventory(directory)
            (directory/'raw.bin').write_bytes(b'changed!')
            self.assertNotEqual(m.inventory(directory),before)
            (directory/'alias').symlink_to(directory/'raw.bin')
            with self.assertRaises(AssertionError): m.inventory(directory)

    def test_inventory_retains_terminal_named_native_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary); (directory/'case').mkdir()
            (directory/'terminal.json').write_text('{}')
            (directory/'case/terminal.json').write_text('{"native":"evidence"}')
            evidence=m.inventory(directory)
            self.assertIn('terminal.json',evidence)
            self.assertIn('case/terminal.json',evidence)

    def plan(self, directory):
        fixtures=directory/'fixtures'; fixtures.mkdir()
        dump(fixtures/'manifest.json',self.manifest)
        pins={'/retained/json.pl':'a'*64,'/retained/json.dylib':'b'*64}
        pins.update(m.required_pins())
        pins[str(fixtures/'manifest.json')]=m.sha(fixtures/'manifest.json')
        for case in self.manifest['cases']:
            for field,hashfield in [('stdin','input_sha256'),('stdout','output_sha256')]:
                if field in case:pins[str(fixtures/case[field])]=case[hashfield]
        plan=dict(schema='prolog-revcomp-linear-bounded-plan-v1',status='prepared-awaiting-native-execution',
            controller=str(PATH.resolve()),
            controller_sha256=m.sha(PATH),candidate_sha256=m.CANDIDATE_SHA,
            candidate_source=str(m.PACKET/'candidate.pl'),retained_plan_sha256=m.RETAINED_PLAN_SHA,
            output=str(directory/'run'),fixtures=str(fixtures),binary='/retained/swipl',
            environment={'SWI_HOME_DIR':'/retained/swipl'},
            pins=pins,schedule=m.schedule(self.manifest),
            planned_compiler_processes=1,planned_inspection_processes=1,planned_candidate_processes=540,
            expected_success_cases=470,expected_rejection_cases=70,process_timeout_seconds=m.kb.TIMEOUT,
            cleanup_timeout_seconds=m.kb.CLEANUP_TIMEOUT,maximum_process_group_rss_bytes=m.kb.RSS_LIMIT,
            native_file_limit_bytes=m.kb.FILE_LIMIT,maximum_live_subject_processes=1,automatic_retries=0,
            benchmark_samples=0,source_work_qualified=False,canonical_loc=None,formatted_loc=None,
            full_timings_qualified=False,chart_admission=False)
        path=directory/'plan.json'; dump(path,plan)
        return plan,path

    @contextmanager
    def synthetic_plan(self, directory):
        # Supply synthetic runtime metadata and expected digests without ever
        # inspecting or hashing the physical retained interpreter/runtime.
        directory=directory.resolve()
        (directory/'candidate.pl').write_bytes((m.PACKET/'candidate.pl').read_bytes())
        retained=directory/'retained-plan.json'
        dump(retained,dict(pins={'/retained/json.pl':'a'*64,'/retained/json.dylib':'b'*64},
            manifests={'revcomp':{'profiles':[dict(binary='/retained/swipl',
                         runtime_environment={'SWI_HOME_DIR':'/retained/swipl'})]}}))
        with patch.object(m,'PACKET',directory),patch.object(m,'RETAINED_PLAN',retained), \
             patch.object(m,'RETAINED_PLAN_SHA',m.sha(retained)):
            plan,path=self.plan(directory)
            m.validate_plan(plan)
            yield plan,path

    def test_corrupt_plan_policy_fails_before_observer(self):
        changes=[('process_timeout_seconds',m.kb.TIMEOUT+1),('cleanup_timeout_seconds',m.kb.CLEANUP_TIMEOUT+1),
                 ('maximum_process_group_rss_bytes',m.kb.RSS_LIMIT+1),('native_file_limit_bytes',m.kb.FILE_LIMIT+1),
                 ('maximum_live_subject_processes',2),('planned_candidate_processes',539),('automatic_retries',1),
                 ('benchmark_samples',1),('source_work_qualified',True),('chart_admission',True)]
        for key,value in changes:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                with self.synthetic_plan(Path(temporary)) as (plan,path):
                    plan[key]=value;dump(path,plan)
                    args=SimpleNamespace(plan=path,plan_sha256=m.sha(path))
                    with patch.object(m,'verify_pins',return_value=[]),patch.object(m.kb.kh,'verify_lock'), \
                         patch.object(m.kb,'observe',side_effect=RuntimeError('native must not start')) as observe:
                        with self.assertRaisesRegex(AssertionError,'Plan policy differs: '+key): m.run(args,None)
                    observe.assert_not_called()

    def test_prepared_plan_rejects_runtime_substitution_and_missing_pin(self):
        changes=[lambda p:p.update(binary='/other/swipl'),
                 lambda p:p['environment'].update(SWI_HOME_DIR='/other/runtime'),
                 lambda p:p['pins'].pop('/retained/json.pl'),
                 lambda p:p['pins'].update({'/retained/json.dylib':'c'*64}),
                 lambda p:p.update(output='/outside/packet/run'),
                 lambda p:p.update(fixtures='/outside/packet/fixtures')]
        for change in changes:
            with tempfile.TemporaryDirectory() as temporary:
                with self.synthetic_plan(Path(temporary)) as (plan,path):
                    change(plan)
                    with self.assertRaises(AssertionError):m.validate_plan(plan)

    def test_each_new_protocol_input_requires_its_exact_pin(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.synthetic_plan(Path(temporary)) as (plan,path):
                for pin in m.required_pins():
                    for replacement in (None,'0'*64):
                        changed=copy.deepcopy(plan)
                        if replacement is None:changed['pins'].pop(pin)
                        else:changed['pins'][pin]=replacement
                        with self.subTest(pin=pin,replacement=replacement), \
                             self.assertRaisesRegex(AssertionError,'Candidate, oracle, controller or protocol pin'):
                            m.validate_plan(changed)

    def test_fixture_input_and_reference_output_require_exact_pins(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.synthetic_plan(Path(temporary)) as (plan,path):
                fixtures=Path(plan['fixtures'])
                sample=next(case for case in self.manifest['cases'] if case['id']=='all-iupac')
                for field in ('stdin','stdout'):
                    pin=str(fixtures/sample[field])
                    for replacement in (None,'0'*64):
                        changed=copy.deepcopy(plan)
                        if replacement is None:changed['pins'].pop(pin)
                        else:changed['pins'][pin]=replacement
                        with self.subTest(field=field,replacement=replacement), \
                             self.assertRaisesRegex(AssertionError,'Fixture byte pin omitted or substituted'):
                            m.validate_plan(changed)

    def test_fixture_manifest_bytes_and_its_pin_must_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.synthetic_plan(Path(temporary)) as (plan,path):
                manifest=Path(plan['fixtures'])/'manifest.json'
                for replacement in (None,'0'*64):
                    changed=copy.deepcopy(plan)
                    if replacement is None:changed['pins'].pop(str(manifest))
                    else:changed['pins'][str(manifest)]=replacement
                    with self.subTest(replacement=replacement), \
                         self.assertRaisesRegex(AssertionError,'Fixture manifest is not pinned'):
                        m.validate_plan(changed)
                manifest.write_bytes(manifest.read_bytes()+b'\n')
                with self.assertRaisesRegex(AssertionError,'Fixture manifest is not pinned'):m.validate_plan(plan)

    def test_fixture_pin_cannot_escape_its_fixture_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.synthetic_plan(Path(temporary)) as (plan,path):
                fixtures=Path(plan['fixtures']);manifest_path=fixtures/'manifest.json'
                manifest=json.loads(manifest_path.read_bytes())
                manifest['cases'][0]['stdin']='../escaped.bin'
                plan['pins'][str(fixtures/'../escaped.bin')]=manifest['cases'][0]['input_sha256']
                dump(manifest_path,manifest)
                plan['pins'][str(manifest_path)]=m.sha(manifest_path)
                plan['schedule']=m.schedule(manifest)
                with self.assertRaisesRegex(AssertionError,'Fixture byte pin omitted or substituted'):
                    m.validate_plan(plan)

    def test_prepared_schedule_mutation_fails_before_observer(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.synthetic_plan(Path(temporary)) as (plan,path):
                plan['schedule'][0]['capacity']=127;dump(path,plan)
                args=SimpleNamespace(plan=path,plan_sha256=m.sha(path))
                with patch.object(m,'verify_pins',return_value=[]),patch.object(m.kb,'observe') as observe:
                    with self.assertRaisesRegex(AssertionError,'Schedule changed'):m.run(args,None)
                observe.assert_not_called()

    def test_late_validated_artifact_change_overrides_ordinary_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.synthetic_plan(Path(temporary)) as (plan,path):
                args=SimpleNamespace(plan=path,plan_sha256=m.sha(path))
                def fake_observe(command, environment, directory, payload, lock, launched, **_):
                    if directory.name=='inspect':
                        (directory.parent/'compile/stdout.bin').write_bytes(b'late mutation')
                        raise RuntimeError('synthetic inspection stops before launch')
                    launched(99123)
                    self.receipt(directory,command=command,environment=environment,payload=payload,
                                 compiler_warning=True,stdout=b'',stderr=m.COMPILE_WARNING)
                    authored=directory.parent/'authored'
                    self.compiler_metadata(directory,authored=authored)
                    (authored/'candidate.qlf').write_bytes(b'synthetic bounded test QLF')
                    raise AssertionError('Unexpected stderr; raw bytes retained')
                with patch.object(m,'verify_pins',return_value=[]),patch.object(m.kb.kh,'verify_lock'), \
                     patch.object(m.kb,'observe',side_effect=fake_observe):
                    with self.assertRaisesRegex(AssertionError,'Closure integrity failed'):m.run(args,None)
                terminal=json.loads((Path(plan['output'])/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity')
                self.assertIs(terminal['bounded_conformance_qualified'],False)
                self.assertTrue(any('Validated command artifacts changed' in row['error']
                                    for row in terminal['artifact_errors']))

    def test_unfamiliar_compiler_warning_stays_failed(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.synthetic_plan(Path(temporary)) as (plan,path):
                args=SimpleNamespace(plan=path,plan_sha256=m.sha(path))
                def fake_observe(command,environment,directory,payload,lock,launched,**_):
                    launched(99123)
                    self.receipt(directory,command=command,environment=environment,payload=payload,
                                 compiler_warning=True,stdout=b'',stderr=m.COMPILE_WARNING+b'extra warning\n')
                    raise AssertionError('Unexpected stderr; raw bytes retained')
                with patch.object(m,'verify_pins',return_value=[]),patch.object(m.kb.kh,'verify_lock'), \
                     patch.object(m.kb,'observe',side_effect=fake_observe):
                    with self.assertRaisesRegex(AssertionError,'Unfamiliar compiler diagnostic'):m.run(args,None)
                terminal=json.loads((Path(plan['output'])/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed')
                self.assertIs(terminal['bounded_conformance_qualified'],False)

    def test_plan_mutation_during_observation_is_caught_at_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.synthetic_plan(Path(temporary)) as (plan,path):
                args=SimpleNamespace(plan=path,plan_sha256=m.sha(path))
                original_verify=m.verify_pins
                def verify_only_synthetic_plan(pins):
                    # Exercise the production verifier on this small plan;
                    # all runtime dependencies are synthetic and not touched.
                    return original_verify({str(path):pins[str(path)]} if str(path) in pins else {})
                def fake_observe(*_,**__):
                    path.write_bytes(path.read_bytes()+b'\n')
                    raise RuntimeError('synthetic observation stops before launch')
                with patch.object(m,'verify_pins',side_effect=verify_only_synthetic_plan), \
                     patch.object(m.kb.kh,'verify_lock'),patch.object(m.kb,'observe',side_effect=fake_observe):
                    with self.assertRaisesRegex(AssertionError,'Closure integrity failed'):m.run(args,None)
                terminal=json.loads((Path(plan['output'])/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity')
                self.assertIs(terminal['bounded_conformance_qualified'],False)
                self.assertEqual([row['path'] for row in terminal['integrity_errors']],[str(path)])


if __name__=='__main__':unittest.main()
