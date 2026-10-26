"""Regressions for unqualified statistics and preserved build evidence."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from analyze import analyze_sessions, analyze
from build_subject import allocate
from campaign import (observation, stages, CONTROLLER, CORRECTNESS, CORRECTNESS_TESTS,
                      PROCESS_TESTS, LINKED_PROCESS_TESTS, TEST_MINIMUMS,
                      check_controllers, required_controller_paths)
from qualify import qualify
import measure
from study import (process, subjects, source_state, STUDY_IDS, STUDY_ID, ROOT,
                   build_receipt_path, runtime_environment, read_plan)

spec = importlib.util.spec_from_file_location('changed_inputs', Path(__file__).with_name('changed-inputs.py'))
changed_inputs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(changed_inputs)


class StudyReviewTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((Path(__file__).parent / 'plan.json').read_text())
        self.reports = [dict(session=session, samples=[
            dict(order=order, position=position, subject=subject,
                 seconds=1.0 if subject == 'F' else 2.0, verified=True)
            for order, subjects in enumerate(self.plan[f'session_{session}'])
            for position, subject in enumerate(subjects)]) for session in [1, 2]]

    def test_study_selection_keeps_data_separate_and_controllers_shared(self):
        code = '''import json,sys,study,campaign,measure,qualify,build_subject
other=next(name for name in study.STUDY_IDS if name!=study.STUDY_ID)
try:campaign.contained('../'+other+'/primary-session-1/results.json')
except AssertionError:isolated=True
else:isolated=False
pins={name:study.process.sha(study.ROOT/name) for name in campaign.required_controller_paths()}
campaign.check_controllers({'controller_pins':pins})
print(json.dumps(dict(study=study.STUDY_ID,plan_study=study.read_plan()['study_id'],
 roots=[str(module.HERE) for module in [study,campaign,measure,qualify,build_subject]],
 code=str(study.CODE_DIR),pins=sorted(pins),remaining=sys.argv[1:],isolated=isolated)))'''
        root = Path(__file__).resolve().parent
        results = []
        for name in STUDY_IDS:
            result = subprocess.run([sys.executable, '-c', code, '--study', name, 'first-report', 'second-report'],
                                    cwd=root, capture_output=True, text=True, timeout=10, check=True)
            selected = json.loads(result.stdout)
            self.assertEqual(selected['study'], name)
            self.assertEqual(selected['plan_study'], name)
            self.assertEqual(set(selected['roots']), {str(root.parent / name)})
            self.assertEqual(selected['remaining'], ['first-report', 'second-report'])
            self.assertEqual(selected['code'], str(root))
            self.assertTrue(selected['isolated'])
            results.append(selected)
        self.assertEqual(results[0]['pins'], results[1]['pins'])

    def test_invalid_or_repeated_study_selection_is_rejected(self):
        root = Path(__file__).resolve().parent
        for selection in [['--study', value] for value in ['unknown', '../another', '/tmp']] + [
            ['--study', STUDY_IDS[0], '--study', STUDY_IDS[1]], ['--study'],
        ]:
            with self.subTest(selection=selection):
                result = subprocess.run([sys.executable, '-c', "import study; print('UNSAFE_SELECTION')", *selection],
                                        cwd=root, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 2)
                self.assertIn('error:', result.stderr)
                self.assertEqual(result.stdout, '')

    def test_controller_pins_must_cover_real_shared_code_and_match_bytes(self):
        pins = {path: process.sha(ROOT / path) for path in required_controller_paths()}
        check_controllers({'controller_pins': pins})
        path = next(path for path in pins if path.endswith('/measure.py'))
        wrong_owner = dict(pins)
        wrong_owner[path.replace(STUDY_IDS[0], STUDY_IDS[1])] = wrong_owner.pop(path)
        for invalid in [wrong_owner, dict(pins, **{path: '0' * 64}), dict(pins, **{'/tmp/elsewhere': '0' * 64})]:
            with self.assertRaises(AssertionError):
                check_controllers({'controller_pins': invalid})

    def test_shared_before_receipt_is_pinned_and_confined_to_named_studies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            architecture, cleanup = (root / name for name in STUDY_IDS)
            architecture.mkdir(); cleanup.mkdir()
            receipt = architecture / 'public-aot.json'
            receipt.write_text(json.dumps({'environment': {'PATH': '/pinned/bin'}}))
            reference = dict(study_id=STUDY_IDS[0], path=receipt.name, sha256=process.sha(receipt))
            with patch('study.CODE_DIR', architecture), patch('study.HERE', cleanup):
                self.assertEqual(build_receipt_path(reference, shared=True), receipt)
                self.assertEqual(runtime_environment({'runtime_environment_receipt': reference}), {'PATH': '/pinned/bin'})
                for invalid in [None, dict(reference, study_id='another-study'),
                                dict(reference, path=str(receipt)), dict(reference, path='../outside.json')]:
                    with self.subTest(reference=invalid), self.assertRaises(ValueError):
                        build_receipt_path(invalid, shared=True)
                with self.assertRaises(ValueError):
                    build_receipt_path(reference)  # A candidate must remain local.
                (cleanup / 'escape.json').symlink_to(receipt)
                with self.assertRaises(ValueError):
                    build_receipt_path('escape.json')
                receipt.write_text(json.dumps({'environment': {'PATH': '/changed/bin'}}))
                with self.assertRaisesRegex(ValueError, 'hash differs'):
                    runtime_environment({'runtime_environment_receipt': reference})

    def test_plan_identity_and_unadopted_runtime_environment_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory, patch('study.HERE', Path(directory)):
            (Path(directory) / 'plan.json').write_text(json.dumps({'study_id': 'another-study'}))
            with self.assertRaisesRegex(ValueError, 'selected study'):
                read_plan()
        with self.assertRaisesRegex(ValueError, 'explicitly adopted'):
            runtime_environment({'runtime_environment_receipt': None})

    def test_cleanup_preserves_protocol_and_an_unfrozen_plan_cannot_start_sampling(self):
        root = Path(__file__).resolve().parent
        cleanup = json.loads((root.parent / STUDY_IDS[1] / 'plan.json').read_text())
        self.assertEqual((root / 'retained-controls.json').read_bytes(),
                         (root.parent / STUDY_IDS[1] / 'retained-controls.json').read_bytes())
        for key in ['session_1', 'session_2', 'primary_observations', 'bootstrap_seed',
                    'bootstrap_resamples', 'acceptance_upper_95_percent', 'warmups',
                    'excluded_outliers', 'source_sha256', 'bytecode_sha256', 'input_sha256',
                    'output_sha256', 'policy_sha256', 'canonical_data_sha256', 'common_mutex']:
            self.assertEqual(cleanup[key], self.plan[key])
        result = subprocess.run([sys.executable, '-c',
                                 "import campaign,study; plan=study.read_plan(); plan['status']='UNFROZEN'; campaign.prerequisites(plan)",
                                 '--study', STUDY_IDS[1]], cwd=root, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('AssertionError', result.stderr)
        self.assertNotIn('FileNotFoundError', result.stderr)

    def test_uncommitted_prerequisites_fail_before_lock_or_sample(self):
        source = dict(commit='candidate', tree='tree', status='')
        pins = dict.fromkeys(['F', 'I', 'W', 'R'], 'binary-pin')
        plan = dict(self.plan, status='frozen-before-first-primary-sample',
                    final_compiler_source='candidate', subject_pins=pins,
                    qualification_sha256='qualification-pin', controller_pins={})
        with patch.object(measure, 'read_plan', return_value=plan), \
             patch.object(measure, 'prerequisites', return_value=(dict.fromkeys(pins), pins, {}, {})), \
             patch.object(measure, 'source_state', return_value=source), \
             patch.object(measure, 'read', return_value=dict(source=source, proceed_to_primary=True)), \
             patch.object(measure.process, 'sha', return_value='qualification-pin'), \
             patch.object(measure.subprocess, 'check_output', side_effect=['evidence-revision', '']), \
             patch.object(measure, 'committed_before_sampling', side_effect=ValueError('missing committed receipt')) as commit_gate, \
             patch.object(measure.fcntl, 'flock') as lock, \
             patch.object(measure.process, 'execute') as execute, \
             patch.object(sys, 'argv', ['measure.py']):
            with self.assertRaisesRegex(ValueError, 'missing committed receipt'):
                measure.main()
            commit_gate.assert_called_once_with('evidence-revision', plan)
            lock.assert_not_called()
            execute.assert_not_called()

    def test_optimized_python_cannot_enter_qualification_or_campaign(self):
        root = Path(__file__).resolve().parent
        message = 'Python optimization disables required campaign evidence and process-supervision checks'
        with tempfile.TemporaryDirectory() as directory:
            commands = {
                'qualification': [str(root / 'qualify.py'), str(Path(directory) / 'missing-session-1.json'),
                                  str(Path(directory) / 'missing-session-2.json')],
                'campaign import': ['-c', "import campaign; print('UNSAFE_CAMPAIGN_IMPORT_REACHED')"],
            }
            for optimization in ('-O', 'PYTHONOPTIMIZE'):
                env = {key: value for key, value in os.environ.items() if key != 'PYTHONOPTIMIZE'}
                flags = ['-O'] if optimization == '-O' else []
                if not flags:
                    env['PYTHONOPTIMIZE'] = '1'
                for entrypoint, command in commands.items():
                    with self.subTest(optimization=optimization, entrypoint=entrypoint):
                        result = subprocess.run([sys.executable, *flags, *command], cwd=root, env=env,
                                                capture_output=True, text=True, timeout=10)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn(message, result.stderr)
                        self.assertEqual(result.stdout, '')
                        self.assertNotIn('FileNotFoundError', result.stderr)

    def test_fabricated_labels_and_timings_never_qualify_performance(self):
        result = analyze_sessions(self.reports, self.plan)
        self.assertTrue(result['statistically_accepted'])
        self.assertFalse(result['performance_qualified'])
        self.assertTrue(all('qualified' not in session for session in result['sessions']))

    def test_duplicate_positions_are_rejected(self):
        report = copy.deepcopy(self.reports[0])
        report['samples'][1]['position'] = 0
        with self.assertRaises(AssertionError):
            analyze(report, self.plan)

    def test_nonfinite_timings_are_rejected(self):
        for value in [float('nan'), float('inf')]:
            report = copy.deepcopy(self.reports[0])
            report['samples'][0]['seconds'] = value
            with self.assertRaises(AssertionError):
                analyze(report, self.plan)

    def test_evidence_qualifier_rejects_unfrozen_campaign(self):
        unfrozen = dict(self.plan, status='unfrozen-test-campaign')
        with self.assertRaises(AssertionError):
            qualify(self.reports, unfrozen)

    def test_multi_package_filter_requires_nonempty_total_not_every_package(self):
        row = dict(stage='native-unit', head='source', exit_code=0,
                   counts=[[426, 0, 2], [0, 0, 0]])
        stages([row], 'source', {'native-unit'})
        row['counts'] = [[0, 0, 0], [0, 0, 0]]
        with self.assertRaises(AssertionError):
            stages([row], 'source', {'native-unit'})

    @staticmethod
    def stage_row(name):
        row = dict(stage=name, head='source', exit_code=0,
                   counts=[[TEST_MINIMUMS[name], 0, 0]] if name in TEST_MINIMUMS else [])
        if name in LINKED_PROCESS_TESTS:
            row['command'] = ['--ignored', '--exact', LINKED_PROCESS_TESTS[name],
                              '--test-threads=1', '--nocapture']
        return row

    def test_required_ci_scopes_cannot_be_omitted_by_an_older_partial_driver(self):
        added_correctness = {
            'resident-factory-attachment', 'native-collection-templates',
            'native-set-conversion', 'native-kind-conversion', 'native-annotation-conversion',
            'source-set-conversion', 'source-kind-conversion', 'source-annotation-conversion',
            'native-semantics', 'iteration-proofs', 'program-runtime-unit',
            'program-prefix-unit', 'program-prefix-window-unit', 'program-prefix-retention-unit',
            'native-source-integration', 'canonical-host-reference', 'canonical-cli-byte-contracts',
            'maintained-hosted-runner',
        }
        added_processes = {
            'canonical-scalar-linked', 'canonical-cast-linked', 'canonical-match-linked',
            'canonical-iteration-linked', 'canonical-program-linked',
            'native-source-host-linked', 'native-source-control-linked',
            'native-source-stdin-linked', 'canonical-resident-cli-linked',
        }
        for required, added, count in [(CORRECTNESS, added_correctness, 51),
                                       (PROCESS_TESTS, added_processes, 16)]:
            self.assertEqual(len(required), count)
            self.assertTrue(added <= required)
            rows = [self.stage_row(name) for name in sorted(required)]
            stages(rows, 'source', required)
            for missing in required:
                with self.subTest(missing=missing), self.assertRaises(AssertionError):
                    stages([row for row in rows if row['stage'] != missing], 'source', required)

    def test_required_test_scopes_reject_missing_ignored_only_or_failed_results(self):
        for name in CORRECTNESS_TESTS | PROCESS_TESTS:
            for counts in [[], [[0, 0, 1]], [[1000, 1, 0]], [[1000, 0, -1]]]:
                with self.subTest(stage=name, counts=counts), self.assertRaises(AssertionError):
                    row = self.stage_row(name)
                    row['counts'] = counts
                    stages([row], 'source', {name})

    def test_empty_companions_cannot_hide_an_unexecuted_integration_suite(self):
        row = self.stage_row('scalar-integration')
        row['counts'] = [[4, 0, 0], [0, 0, 0]]
        with self.assertRaises(AssertionError):
            stages([row], 'source', {'scalar-integration'})
        row['stage'] = 'maintained-hosted-runner'
        stages([row], 'source', {'maintained-hosted-runner'})

    def test_linked_scopes_require_the_exact_ignored_case_to_execute(self):
        for name in LINKED_PROCESS_TESTS:
            row = self.stage_row(name)
            stages([row], 'source', {name})
            for command, counts in [
                (['--ignored', '--exact', 'another_case'], [[1, 0, 0]]),
                ([*row['command'], '--list'], [[1, 0, 0]]),
                ([*row['command'], '--no-run'], [[1, 0, 0]]),
                (['--exact', LINKED_PROCESS_TESTS[name]], [[1, 0, 0]]),
                (row['command'], [[2, 0, 0]]),
                (row['command'], [[1, 0, 1]]),
            ]:
                with self.subTest(stage=name, command=command, counts=counts), self.assertRaises(AssertionError):
                    stages([dict(row, command=command, counts=counts)], 'source', {name})

    def test_public_cli_and_policy_contracts_reject_partial_test_counts(self):
        for name, expected in [('canonical-cli-unit-contracts', 5),
                               ('canonical-cli-public-qualification', 3),
                               ('canonical-policy-kernel', 13), ('benchmark-policy-unit', 13)]:
            row = dict(stage=name, head='source', exit_code=0, counts=[[expected - 1, 0, 0]])
            with self.subTest(stage=name), self.assertRaises(AssertionError):
                stages([row], 'source', {name})
            row['counts'] = [[expected, 0, 0]]
            stages([row], 'source', {name})

    def test_observations_require_matching_owned_receipts_and_cleanup(self):
        with tempfile.TemporaryDirectory() as directory, patch('campaign.HERE', Path(directory)):
            root = Path(directory)
            path = root / 'primary-session-1/00-2-R/process.json'
            path.parent.mkdir(parents=True)
            (path.parent / 'stdout.bin').write_bytes(b'output')
            (path.parent / 'stderr.bin').write_bytes(b'')
            plan = copy.deepcopy(self.plan)
            plan['output_sha256'] = process.sha(path.parent / 'stdout.bin')
            plan['controller_pins'] = {CONTROLLER: 'controller'}
            raw = dict(exit_status=0, quantitative_benchmark=True, inherited_common_mutex=True,
                       deadline_seconds=30, cleanup_errors=[], group_closed=True, reaped=True,
                       signals=[], controller_sha256='controller', elapsed_seconds=2.0,
                       maximum_rss_bytes=1234,
                       birth_identity=dict(pid=123, birth_seconds=456, birth_microseconds=789),
                       command=['/retained/R'])
            sample = dict(order=0, position=2, subject='R', process=str(path.relative_to(root)),
                          seconds=2.0, maximum_rss_bytes=1234,
                          stdout_sha256=plan['output_sha256'], native_sha256=None, native=None,
                          verified=True)

            def validate(record, row, identities):
                path.write_text(json.dumps(record))
                row['process_sha256'] = process.sha(path)
                observation(row, 1, plan, {'R': Path('/retained/R')}, identities, Path('/policy'))

            identities = set()
            validate(raw, sample, identities)
            with self.assertRaises(AssertionError):
                validate(raw, sample, identities)
            for field, value in [('group_closed', False), ('reaped', False),
                                 ('cleanup_errors', ['unreaped child']),
                                 ('quantitative_benchmark', False), ('elapsed_seconds', 1.0),
                                 ('exit_status', 1), ('command', ['/another/R'])]:
                tampered = copy.deepcopy(raw)
                tampered[field] = value
                with self.assertRaises(AssertionError, msg=field):
                    validate(tampered, copy.deepcopy(sample), set())
            wrong_path = copy.deepcopy(sample)
            wrong_path['process'] = '../escaped/process.json'
            with self.assertRaises(AssertionError):
                observation(wrong_path, 1, plan, {'R': Path('/retained/R')}, set(), Path('/policy'))

    def test_rebuilds_preserve_committed_and_previous_receipts(self):
        with tempfile.TemporaryDirectory() as directory, patch('build_subject.HERE', Path(directory)):
            old = Path(directory) / 'baseline/aot-build/process.json'
            old.parent.mkdir(parents=True)
            old.write_text('retained evidence')
            first, binary = allocate('I', 'first')
            receipt = first / 'public-aot.json'
            receipt.write_text('first build')
            second, second_binary = allocate('I', 'second')
            self.assertNotEqual(first, second)
            self.assertNotEqual(binary, second_binary)
            with self.assertRaises(FileExistsError):
                allocate('I', 'first')
            with self.assertRaises(AssertionError):
                allocate('I', '../escape')
            self.assertEqual(old.read_text(), 'retained evidence')
            self.assertEqual(receipt.read_text(), 'first build')

    def test_changed_input_runs_preserve_intermediate_and_final_evidence(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(changed_inputs, 'HERE', Path(directory)):
            retained = Path(directory) / 'changed-inputs-v1'
            retained.mkdir()
            (retained / 'results.json').write_text('intermediate evidence')
            final = changed_inputs.allocate_output('final')
            (final / 'results.json').write_text('final evidence')
            with self.assertRaises(FileExistsError):
                changed_inputs.allocate_output('final')
            changed_inputs.allocate_output('next')
            self.assertEqual((retained / 'results.json').read_text(), 'intermediate evidence')
            self.assertEqual((final / 'results.json').read_text(), 'final evidence')

    def test_adopted_candidate_workspace_controls_all_source_checks(self):
        with tempfile.TemporaryDirectory() as directory, patch('study.HERE', Path(directory)):
            root = Path(directory)
            source = dict(commit='final', tree='tree', status='')
            targets = {}
            pins = {}
            for subject in ['F','I','W','R']:
                targets[subject] = root / subject
                targets[subject].write_text(subject)
                pins[subject] = process.sha(targets[subject])
            plan = dict(study_id=STUDY_ID, candidate_receipt='new-F.json', baseline_receipt='new-I.json', implementation_base='before')
            (root / 'plan.json').write_text(json.dumps(plan))
            (root / 'new-F.json').write_text(json.dumps(dict(source=source, workspace='/alternate-checkout', executable=str(targets['F']), executable_sha256=pins['F'])))
            (root / 'new-I.json').write_text(json.dumps(dict(source=dict(commit='before'), executable=str(targets['I']), executable_sha256=pins['I'])))
            (root / 'retained-controls.json').write_text(json.dumps({s:dict(path=str(targets[s]),sha256=pins[s]) for s in ['W','R']}))

            def git(command, **kwargs):
                self.assertEqual(command[:3], ['git','-C','/alternate-checkout'])
                return {'HEAD': 'final', 'HEAD^{tree}': 'tree', '--porcelain': ''}[command[-1]]

            with patch('study.subprocess.check_output', side_effect=git):
                self.assertEqual(subjects()[:2], (targets, pins))
                self.assertEqual(source_state(), source)


if __name__ == '__main__':
    unittest.main()
