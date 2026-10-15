"""Small synthetic full90 contracts; no runtime, qualification or native intake."""
import copy
from contextlib import nullcontext
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('rebol_full.py')
spec = importlib.util.spec_from_file_location('test_rebol_full_source',SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    manifests = {}
    for bench in m.BENCHES:
        rows = [dict(id=f'rebol-{bench}-{form}',key=f'rebol-{bench}-{form}',benchmark=bench,
            language='rebol3',variant=form,source_sha256='a'*64) for form in m.FORMS]
        rows.append(dict(id='mech-aot-control',key=bench+':rebol-full-study:mech-control',benchmark=bench,
                         language='mech',source_sha256='b'*64))
        manifests[bench] = dict(benchmark=bench,profiles=rows,samples=3,orders=m.orders_for(bench))
    return dict(manifests=manifests)


def completed(plan, failed_key=None):
    rows = m.initial_rows(plan)
    report = dict(programs=rows,attempts=[],active=None,completed_benchmarks=list(m.BENCHES),
                  skipped_failed_profile_slots=[],isolated_failed_profiles=[],native_launch_unconfirmed_attempts=[])
    for bench,round_index,identity,key in m.schedule_for(plan['manifests']):
        row = rows[key]
        if row.get('full_failure'):
            report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_index,id=identity,key=key))
            continue
        index = len(report['attempts'])+1
        attempt = dict(attempt=index,benchmark=bench,round=round_index,id=identity,key=key,
                       qualified=key!=failed_key,seconds=1+index/1000,validation=dict(valid=True))
        report['attempts'].append(attempt);row['attempts'].append(index)
        if attempt['qualified']:
            row['samples_seconds'].append(attempt['seconds']);row['sample_validation'].append(attempt['validation'])
            row['measurement_status'] = 'measured' if len(row['samples_seconds'])==3 else 'partial'
        else:
            row.update(full_failure=attempt,measurement_status='failed-full-workload')
            report['isolated_failed_profiles'].append(key)
    for manifest in plan['manifests'].values():m.summarize(rows,manifest)
    report.update(full_performance_runs=len(report['attempts']),
                  qualified_samples=sum(len(row['samples_seconds']) for row in rows.values()))
    return report


def base_fixture(bench='pidigits'):
    environment = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin',LC_ALL='C',LANG='C',
        OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',
        HOME='/out/home',REBOL_HOME='/out/home',TMPDIR='/out/tmp',MECH_CLBG_REBOL_PRIMITIVES='/image')
    files = [('main.reb','application'),('clbg_io.reb','application-helper'),
             ('clbg_primitives.reb','application-launcher'),('clbg_primitives.c','general-library-helper')]
    if bench in ('pidigits','regexredux'):
        files.append(('clbg_big.reb' if bench=='pidigits' else 'clbg_regex.reb','application-helper'))
    inputs = [dict(path='/source/'+name,sha256='a'*64,role=role,counted=True,canonical_loc=2,physical_loc=3)
              for name,role in files]
    runtime,image = dict(path='/runtime',sha256='b'*64),dict(path='/image',sha256='c'*64)
    base = dict(benchmark=bench,language='rebol3',original_profile_id=f'rebol-{bench}-baseline-v1',
        main=dict(path='/source/main.reb',sha256='a'*64),command_prefix=['/runtime','-q','-s','/source/main.reb'],
        input_kind='stdin' if bench in m.STDIN_BENCHES else 'integer-argument',cwd=str(m.ROOT),maximum_workers=1,
        physical_inputs=inputs,canonical_loc=len(inputs)*2,physical_loc=len(inputs)*3,formatted_loc=None,corrections={},
        alias_policy=dict(authored_source_forms=1,publication_forms=['compact','optimized'],
                          distinct_optimization_claim=False,copied_timing_allowed=False),
        runtime_environment_policy=dict(fixed={key:environment[key] for key in
            ('PATH','LC_ALL','LANG','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS')},
            fresh_directories=dict(HOME='home',REBOL_HOME='home',TMPDIR='tmp'),
            extension_variable='MECH_CLBG_REBOL_PRIMITIVES',ambient_loader_overrides=False,diagnostic_flags=[]))
    pins = {item['path']:item['sha256'] for item in inputs+[runtime,image]}
    return base,dict(runtime=dict(binary=runtime),extension_image=image),environment,pins


class Full90(unittest.TestCase):
    def test_exact_ninety_rotated_fresh_slots(self):
        plan=fixture();slots=m.schedule_for(plan['manifests'])
        self.assertEqual(len(slots),90)
        self.assertEqual(sum(slot[2]=='mech-aot-control' for slot in slots),30)
        self.assertEqual(sum(slot[2].endswith('-compact') for slot in slots),30)
        self.assertEqual(sum(slot[2].endswith('-optimized') for slot in slots),30)
        self.assertEqual([s[2] for s in slots[:9]],[
            'rebol-regexredux-compact','rebol-regexredux-optimized','mech-aot-control',
            'rebol-regexredux-optimized','mech-aot-control','rebol-regexredux-compact',
            'mech-aot-control','rebol-regexredux-compact','rebol-regexredux-optimized'])

    def test_missing_form_or_copied_timing_rejected(self):
        for change in ('missing','alias','rotation'):
            plan=fixture();manifest=plan['manifests'][m.BENCHES[0]]
            if change=='missing':manifest['profiles'].pop(1)
            elif change=='alias':manifest['profiles'][1]['timing_alias_of']=manifest['profiles'][0]['key']
            else:manifest['orders'][1]['profiles'].reverse()
            with self.assertRaises(AssertionError):m.schedule_for(plan['manifests'])

    def test_independent_form_samples_and_ledger(self):
        plan=fixture();report=completed(plan);m.check_success_ledger(plan,report)
        a,b=plan['manifests']['pidigits']['profiles'][:2]
        self.assertNotEqual(report['programs'][a['key']]['samples_seconds'],report['programs'][b['key']]['samples_seconds'])
        bad=copy.deepcopy(report);bad['programs'][b['key']]['samples_seconds']=bad['programs'][a['key']]['samples_seconds']
        with self.assertRaises(AssertionError):m.check_success_ledger(plan,bad)

    def test_failed_subject_retains_no_partial_median_and_exact_skips(self):
        plan=fixture();key='rebol-regexredux-compact';report=completed(plan,key)
        m.check_success_ledger(plan,report)
        self.assertEqual(len(report['skipped_failed_profile_slots']),2)
        self.assertNotIn('median_seconds',report['programs'][key])
        self.assertIsNone(report['programs'][key]['time_x_mech'])
        report['skipped_failed_profile_slots'].pop()
        with self.assertRaises(AssertionError):m.check_success_ledger(plan,report)

    def test_failed_control_has_no_subject_comparison(self):
        plan=fixture();key='regexredux:rebol-full-study:mech-control';report=completed(plan,key)
        m.check_success_ledger(plan,report)
        for row in plan['manifests']['regexredux']['profiles']:
            self.assertIsNone(report['programs'][row['key']]['time_x_mech'])
        self.assertIn('median_seconds',report['programs']['rebol-regexredux-compact'])

    def test_repeated_missing_and_reordered_attempts_reject(self):
        for change in ('repeat','missing','reorder'):
            plan=fixture();report=completed(plan)
            if change=='repeat':report['attempts'][1]=copy.deepcopy(report['attempts'][0])
            elif change=='missing':report['attempts'].pop()
            else:report['attempts'][0],report['attempts'][1]=report['attempts'][1],report['attempts'][0]
            with self.assertRaises(AssertionError):m.check_success_ledger(plan,report)

    def test_whole_c_and_facade_bundle_required(self):
        base,admission,environment,pins=base_fixture()
        m.subject(base,'compact',admission,environment,pins)
        for field,value in [('counted',False),('canonical_loc',0),('sha256','d'*64)]:
            bad=copy.deepcopy(base);bad['physical_inputs'][3][field]=value
            with self.assertRaises(AssertionError):m.subject(bad,'compact',admission,environment,pins)
        bad=copy.deepcopy(base);bad['physical_inputs'].pop()
        with self.assertRaises(AssertionError):m.subject(bad,'compact',admission,environment,pins)

    def test_direct_runtime_and_environment_no_diagnostic_flags(self):
        base,admission,environment,pins=base_fixture()
        first=m.subject(base,'compact',admission,environment,pins)
        second=m.subject(base,'optimized',admission,environment,pins)
        self.assertEqual(first['command'],['/runtime','-q','-s','/source/main.reb','{n}'])
        self.assertEqual(first['command'],second['command']);self.assertNotEqual(first['key'],second['key'])
        self.assertNotIn('timing_alias_of',second)
        for change in ('flags','environment','image'):
            b,a=copy.deepcopy(base),copy.deepcopy(admission)
            if change=='flags':b['command_prefix'].append('--trace')
            elif change=='environment':b['runtime_environment_policy']['diagnostic_flags']=['trace']
            else:a['extension_image']['sha256']='d'*64
            with self.assertRaises(AssertionError):m.subject(b,'compact',a,environment,pins)

    def test_stdin_has_no_invented_numeric_argument(self):
        base,admission,environment,pins=base_fixture('knucleotide')
        row=m.subject(base,'optimized',admission,environment,pins)
        self.assertEqual(row['command'],base['command_prefix'])
        base['input_kind']='integer-argument'
        with self.assertRaises(AssertionError):m.subject(base,'compact',admission,environment,pins)

    def test_run_output_must_be_fresh_and_disjoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            with patch.object(m,'PACKET',root):
                m.check_output_paths(root/'plan.json',root/'run')
                (root/'run').mkdir()
                with self.assertRaises(AssertionError):m.check_output_paths(root/'plan.json',root/'run')

    def test_special_artifact_and_changed_owned_metadata_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();path=root/'file.json'
            raw,identity=m.write_new(path,dict(a=1));m.verify_written(path,raw,identity)
            path.write_bytes(raw+b' ')
            with self.assertRaises(AssertionError):m.verify_written(path,raw,identity)
            (root/'linked').symlink_to(path)
            with self.assertRaises(AssertionError):m.artifact_inventory(root)

    def test_finalization_only_once_and_no_native_before_started(self):
        supervisor=types.SimpleNamespace(lifecycle_atomic=nullcontext)
        state=dict(supervisor=supervisor)
        with patch.object(m,'finish') as finish:
            m.finalize_once(state);finish.assert_not_called()
            state['started']=True;m.finalize_once(state);m.finalize_once(state)
            finish.assert_called_once_with(state,None)

    def test_late_context_failure_downgrades_owned_success_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory).resolve()/'terminal.json';owned={}
            m.write_new(path,dict(status='complete',integrity_errors=[],common_mutex_held=True),owned)
            state=dict(terminal_owned=owned,supervisor=types.SimpleNamespace(lifecycle_atomic=nullcontext))
            with self.assertRaisesRegex(RuntimeError,'late lease'):
                with m.final_failure_guard(state):raise RuntimeError('late lease')
            terminal=json.loads(path.read_bytes())
            self.assertEqual(terminal['status'],'failed-terminal-integrity')
            self.assertIs(terminal['common_mutex_held'],False)
            self.assertIs(terminal['common_mutex_held_continuously'],False)
            self.assertIs(terminal['chart_admission'],False)

    def test_downgrade_preserves_external_terminal_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory).resolve()/'terminal.json';owned={}
            m.write_new(path,dict(status='complete',integrity_errors=[]),owned)
            path.unlink();path.write_bytes(b'external')
            with self.assertRaises(AssertionError):m.downgrade_terminal(dict(terminal_owned=owned),RuntimeError('late'))
            self.assertEqual(path.read_bytes(),b'external')

    def test_changed_report_at_initial_inventory_cannot_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory).resolve();report_path=output/'report.json'
            report=dict(status='stopped-unqualified',active=None,attempts=[],programs={},full_performance_runs=0,
                        registered_native_attempts=[],native_launch_unconfirmed_attempts=[],qualified_samples=0,
                        skipped_failed_profile_slots=[])
            guard=types.SimpleNamespace(OUT=output,REPORT=report_path,
                save=lambda path,value:Path(path).write_bytes(m.encoded(value)))
            helpers=types.SimpleNamespace(refresh_attempt_accounting=lambda report:None,verify_lock=lambda lock:None)
            state=dict(plan=dict(manifests={}),report=report,held=types.SimpleNamespace(pins={},resolutions={},common=None),
                helpers=helpers,receipts=None,guard=guard,harness=None,snapshots={},check_lease=lambda:None)
            inventory=m.artifact_inventory
            def changed(root):
                report_path.write_bytes(b'{"external":true}\n')
                return inventory(root)
            with patch.object(m,'check_inputs'),patch.object(m,'artifact_inventory',side_effect=changed):
                with self.assertRaises(AssertionError):m.finish(state)
            self.assertEqual(json.loads((output/'terminal.json').read_bytes())['status'],'failed-terminal-integrity')
            self.assertEqual(report_path.read_bytes(),b'{"external":true}\n')

    def test_qualification_pin_failure_prevents_success_terminal(self):
        state=dict(started=True,supervisor=types.SimpleNamespace(lifecycle_atomic=nullcontext))
        error=AssertionError('qualification pin changed')
        with patch.object(m,'finish') as finish:
            m.finalize_once(state,error)
            finish.assert_called_once_with(state,error)
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory).resolve();report_path=output/'report.json'
            report=dict(status='stopped-unqualified',active=None,attempts=[],programs={},full_performance_runs=0,
                        registered_native_attempts=[],native_launch_unconfirmed_attempts=[],qualified_samples=0,
                        skipped_failed_profile_slots=[])
            guard=types.SimpleNamespace(OUT=output,REPORT=report_path,
                save=lambda path,value:Path(path).write_bytes(m.encoded(value)))
            helpers=types.SimpleNamespace(refresh_attempt_accounting=lambda report:None,verify_lock=lambda lock:None)
            state=dict(plan=dict(manifests={}),report=report,held=types.SimpleNamespace(pins={},resolutions={},common=None),
                helpers=helpers,receipts=None,guard=guard,harness=None,snapshots={},check_lease=lambda:None)
            with patch.object(m,'check_inputs'):
                with self.assertRaises(AssertionError):m.finish(state,error)
            terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertIs(terminal['common_mutex_held'],False)
            self.assertIs(terminal['common_mutex_held_continuously'],False)

    def test_final_report_read_is_compared_not_adopted(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory).resolve();report_path=output/'report.json'
            report=dict(status='stopped-unqualified',active=None,attempts=[],programs={},full_performance_runs=0,
                        registered_native_attempts=[],native_launch_unconfirmed_attempts=[],qualified_samples=0,
                        skipped_failed_profile_slots=[])
            guard=types.SimpleNamespace(OUT=output,REPORT=report_path,
                save=lambda path,value:Path(path).write_bytes(m.encoded(value)))
            helpers=types.SimpleNamespace(refresh_attempt_accounting=lambda report:None,verify_lock=lambda lock:None)
            state=dict(plan=dict(manifests={}),report=report,held=types.SimpleNamespace(pins={},resolutions={},common=None),
                helpers=helpers,receipts=None,guard=guard,harness=None,snapshots={},check_lease=lambda:None)
            original_read=m.read_bytes
            def changed_read(path):
                if Path(path)==report_path:report_path.write_bytes(b'{"external-final":true}\n')
                return original_read(path)
            with patch.object(m,'check_inputs'),patch.object(m,'read_bytes',side_effect=changed_read):
                with self.assertRaises(AssertionError):m.finish(state)
            terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-terminal-integrity')
            self.assertIs(terminal['common_mutex_held_continuously'],False)
            self.assertEqual(report_path.read_bytes(),b'{"external-final":true}\n')


if __name__=='__main__':unittest.main()
