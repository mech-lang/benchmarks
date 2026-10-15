"""Focused pure checks for the new APL six-process plan and receipt policy."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('apl_full_checks', HERE/'apl_workspace_full.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def rows():
    return [dict(id=a.SUBJECT_ID, key=a.SUBJECT_KEY, language='apl', benchmark='binarytrees', source_sha256='a'*64),
            dict(id='mech-aot-control', key=a.CONTROL_KEY, language='mech', benchmark='binarytrees', source_sha256='b'*64)]


def manifest():
    return dict(benchmark='binarytrees', profiles=rows(), samples=3, size=21, orders=a.orders())


def plan():
    return dict(manifests={'binarytrees': manifest()}, source_aliases=[dict(key=a.ALIAS_KEY,
        source_alias_of=a.SUBJECT_KEY, timing_alias_of=a.SUBJECT_KEY, additional_native_processes=0)])


def qualified_count():
    return dict(schema='apl-binarytrees-workspace-qualified-source-counts-v1', canonical_LOC_admitted=True,
        canonical_loc=41, physical_loc=41, formatted_loc=None, formatted_loc_qualified=False,
        distinct_authored_main_sources=1, source_forms=['compact', 'optimized'], setup_assignment_included=True,
        source_bundle=[dict(path='archive/comparisons/r-apl-uiua-comparison/20261011/sources/apl/binarytrees.compact.apl',
                            sha256=a.SOURCE_SHA, canonical_loc=40, physical_loc=40),
                       dict(path='experiments/apl/binarytrees-workspace-v1/setup.apl',
                            sha256=a.SETUP_SHA, canonical_loc=1, physical_loc=1)])


class Full(unittest.TestCase):
    def test_exact_six_real_processes_and_alternating_rounds(self):
        slots = a.schedule_for(plan()['manifests'])
        self.assertEqual([slot[2] for slot in slots],
                         [a.SUBJECT_ID, 'mech-aot-control', 'mech-aot-control', a.SUBJECT_ID,
                          a.SUBJECT_ID, 'mech-aot-control'])
        self.assertEqual([slot[1] for slot in slots], [1, 1, 2, 2, 3, 3])
        self.assertNotIn(a.ALIAS_KEY, [slot[3] for slot in slots])

    def test_no_alias_process_extra_round_or_noncanonical_input(self):
        for field, value in [('samples', 4), ('size', 20), ('orders', a.orders()+a.orders()[:1])]:
            m = manifest(); m[field] = value
            with self.assertRaises(AssertionError): a.schedule_for({'binarytrees': m})
        m = manifest(); m['profiles'].append(dict(id='optimized', key=a.ALIAS_KEY, language='apl'))
        with self.assertRaises(AssertionError): a.schedule_for({'binarytrees': m})

    def test_setup_is_in_command_fingerprint_support_and_source_count(self):
        specification = dict(subject_runtime_path='/retained/trees.apl', launcher_runtime_path='/retained/run-apl.sh',
            launcher=dict(sha256='a'*64), runtime_binary=dict(path='/retained/bin/apl', sha256='b'*64))
        count = qualified_count(); before = copy.deepcopy(count)
        refs = dict(counts=dict(path='/evidence/count.json', sha256='c'*64), work=dict(path='/evidence/work.json', sha256='d'*64))
        row = a.subject_profile(specification, count, refs, a.PACKET/'test-unexecuted-run')
        self.assertEqual(row['command'], ['/retained/run-apl.sh', '--cc', '1', '-f', str(a.BASE/'setup.apl'),
                                         '-f', '/retained/trees.apl', '--', '{n}'])
        self.assertEqual(row['support_pins'][str(a.BASE/'setup.apl')], a.SETUP_SHA)
        self.assertEqual(row['canonical_loc'], sum(x['canonical_loc'] for x in row['source_bundle']))
        self.assertTrue(row['setup_inside_timer']); self.assertEqual(row['maximum_workers'], 1)
        self.assertEqual(count, before)

    def test_count_cannot_exclude_setup_or_claim_formatted_source(self):
        for change in (dict(canonical_loc=40), dict(setup_assignment_included=False),
                       dict(formatted_loc=41), dict(canonical_LOC_admitted=False),
                       dict(source_bundle=qualified_count()['source_bundle'][:1])):
            count = qualified_count(); count.update(change)
            with self.assertRaises(AssertionError): a.validate_qualification(count, {}, {}, {})

    def test_exact_stderr_kept_no_generic_warning_filter(self):
        a.check_stderr(dict(stderr=a.WARNING), dict(language='apl'))
        a.check_stderr(dict(stderr=''), dict(language='mech'))
        for text in ('', a.WARNING.strip(), a.WARNING+'other warning\n', 'APL ERROR\n'):
            with self.assertRaises(AssertionError): a.check_stderr(dict(stderr=text), dict(language='apl'))
        with self.assertRaises(AssertionError): a.check_stderr(dict(stderr=a.WARNING), dict(language='mech'))

    def test_success_ledger_counts_distinct_samples_and_alias_zero(self):
        q = plan(); result = dict(programs=a.initial_rows(q), attempts=[], active=None,
            source_aliases=q['source_aliases'], full_performance_runs=6, qualified_samples=6,
            native_launch_unconfirmed_attempts=[], completed_benchmarks=['binarytrees'])
        for index, slot in enumerate(a.schedule_for(q['manifests']), 1):
            attempt = dict(zip(('benchmark', 'round', 'id', 'key'), slot), attempt=index,
                           qualified=True, seconds=float(index), validation=dict(reference_match=True))
            result['attempts'].append(attempt)
            a.accept_attempt(result, result['programs'][slot[3]], attempt)
        a.check_success_ledger(q, result)
        self.assertEqual(len(result['programs']), 2)
        bad = copy.deepcopy(result); bad['attempts'].append(copy.deepcopy(bad['attempts'][0]))
        with self.assertRaises(AssertionError): a.check_success_ledger(q, bad)
        bad = copy.deepcopy(result); bad['source_aliases'][0]['additional_native_processes'] = 3
        with self.assertRaises(AssertionError): a.check_success_ledger(q, bad)

    def test_failed_attempt_preserved_without_a_sample_or_summary(self):
        result = dict(programs=a.initial_rows(plan()))
        row = result['programs'][a.SUBJECT_KEY]
        a.accept_attempt(result, row, dict(attempt=1, qualified=False, seconds=14400.0))
        self.assertEqual(row['attempts'], [1]); self.assertEqual(row['samples_seconds'], [])
        self.assertEqual(row['measurement_status'], 'stopped-unqualified')
        self.assertNotIn('median_seconds', row)

    def test_outer_cannot_accept_old_timeouts_or_fd3(self):
        base = dict(status='returned', deadline_seconds=15000, native_timeout_seconds=14400,
                    common_mutex_fd=64)
        for change in (dict(deadline_seconds=22200), dict(native_timeout_seconds=21600), dict(common_mutex_fd=3)):
            with self.assertRaises(AssertionError): a.check_outer(dict(base, **change), {})

    def test_final_report_bytes_are_not_adopted_after_save_or_input_replay(self):
        for when in ('save-return', 'final-input-replay', 'final-report-read', 'lock-during-final-report-read'):
            with self.subTest(when=when), tempfile.TemporaryDirectory() as directory:
                output = Path(directory); report_path = output/'report.json'
                report = dict(status='stopped-unqualified', attempts=[], active=None, source_aliases=[],
                              full_performance_runs=0, registered_native_attempts=[],
                              native_launch_unconfirmed_attempts=[], qualified_samples=0)
                saves, checks, report_reads = [], [], []
                lock_changed = []
                actual_sha = a.sha
                def save(path, value):
                    path.write_text(json.dumps(value, indent=2)+'\n'); saves.append(path)
                    if len(saves) == 1 and when == 'save-return': path.write_text('{"changed": true}\n')
                def check_inputs(*args):
                    checks.append(True)
                    if len(checks) == 2 and when == 'final-input-replay': report_path.write_text('{"changed": true}\n')
                def read_sha(path):
                    if Path(path) == report_path:
                        report_reads.append(True)
                        if len(report_reads) == 3:
                            if when == 'final-report-read': report_path.write_text('{"changed": true}\n')
                            if when == 'lock-during-final-report-read': lock_changed.append(True)
                    return actual_sha(path)
                def verify_lock(*args):
                    if lock_changed: raise AssertionError('Named mutex changed during final report read')
                guard = SimpleNamespace(OUT=output, REPORT=report_path, save=save)
                lock = SimpleNamespace(fileno=lambda: 64)
                with patch.object(a, 'refresh_attempt_accounting'), patch.object(a, 'verify_lock', side_effect=verify_lock), \
                     patch.object(a, 'sha', side_effect=read_sha), \
                     patch.object(a, 'check_execution_inputs', side_effect=check_inputs), \
                     patch.object(a.r, 'inventory', side_effect=lambda path: {str(p) for p in path.rglob('*') if p.is_file()}):
                    with self.assertRaisesRegex(AssertionError, 'Final integrity failed|Named mutex changed'):
                        a.finish(plan(), report, {}, {}, guard, None, lock)
                terminal = json.loads((output/'terminal.json').read_text())
                self.assertEqual(terminal['status'], 'failed-terminal-integrity')
                self.assertTrue(terminal['integrity_errors'])
                self.assertEqual(terminal['available_evidence_pins'], {})
                self.assertFalse(terminal['common_mutex_held'])
                self.assertFalse(terminal['common_mutex_held_continuously'])
                self.assertFalse(terminal['full_timings_qualified'])
                self.assertFalse(terminal['chart_admission'])


if __name__ == '__main__': unittest.main()
