"""Synthetic fresh receipts paired with immutable historical source metadata."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import statistics
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('import_mech_interpreted_rerun', ROOT/'tools/import_mech_interpreted_rerun.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
spec = importlib.util.spec_from_file_location('synthetic_interpreted_producer', ROOT/'tools/rerun_mech_interpreted.py')
producer = importlib.util.module_from_spec(spec); spec.loader.exec_module(producer)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = m.report_bytes(value); path.write_bytes(raw)
    return dict(sha256=m.digest(raw), bytes=len(raw))


def fake_report(root, samples=None):
    historical, old = m.retained()
    recorded = ROOT / Path(m.REPORT).parent
    plan = producer.make_plan(historical, recorded)
    pins = {str(ROOT/m.OLD_PATH):m.OLD_SHA,
            str(ROOT/'tools/rerun_mech_interpreted.py'):m.digest((ROOT/'tools/rerun_mech_interpreted.py').read_bytes()),
            str(producer.HELPER):producer.HELPER_SHA256, m.PYTHON:m.PYTHON_SHA}
    for row in plan['programs'].values():
        for kind in ('source','binary'): pins[row[kind]] = row[kind+'_sha256']
        if row['stdin']: pins[row['stdin']['path']] = row['stdin']['sha256']
    plan['pins'] = deepcopy(pins)
    directory = root / Path(m.REPORT).parent
    plan_meta = write(directory/'plan.json', plan)
    pins[str(recorded/'plan.json')] = plan_meta['sha256']
    report = deepcopy(plan)
    report.update(status='complete', completed_samples=45, native_processes=45,
        attempts=[], pins=pins, controller=str(ROOT/'tools/rerun_mech_interpreted.py'),
        controller_sha256=pins[str(ROOT/'tools/rerun_mech_interpreted.py')], integrity_errors=[],
        artifacts={'plan.json':plan_meta}, plan_sha256=plan_meta['sha256'])
    for row in report['programs'].values():
        row.update(samples_seconds=[], sample_details=[], sample_validation=[], sample_receipts=[])
    clock = 100
    for slot in plan['schedule']:
        row = report['programs'][slot['key']]; ordinal = slot['ordinal']
        supplied = (samples or {}).get(slot['key'], [10.,11.,12.])
        sample = supplied[slot['round']-1]
        detail = dict(seconds=sample, wall_seconds=sample, prepare_seconds=0.01, kernel_seconds=0.02)
        validation = {**{k:row['expected_output'][k] for k in ('bytes','sha256')},'reference_match':True,
                      'validation':'Synthetic complete-output expectation'}
        relative = f'samples/{ordinal:03d}'
        command_dir = recorded / relative
        receipt = dict(status='passed', qualified=True, native_process_started=True, exit_code=0,
            command=row['command'], cwd=row['cwd'], environment=row['runtime_environment'], stdin=row['stdin'],
            common_mutex_inode=79859134, native_inherits_common_mutex=True, timing_measurement='full-process-wall',
            seconds=sample, wall_seconds=sample, sample_details=detail, validation=validation,
            pid=10000+ordinal, process_group_id=10000+ordinal, clock_start_ns=clock,
            clock_stop_ns=clock+int(sample*1e9), monitor_errors=[],
            monitor_observations=[{'power':{'source':'AC Power','low_power_mode':0},'competing_compilers':[]}],
            stdout=str(command_dir/'stdout.bin'), stderr=str(command_dir/'stderr.txt'),
            stderr_sha256='d'*64, stderr_bytes=77)
        clock = receipt['clock_stop_ns']+100
        meta = write(directory/relative/'process.json', receipt)
        report['artifacts'].update({relative+'/process.json':meta,
            relative+'/stdout.bin':{k:validation[k] for k in ('bytes','sha256')},
            relative+'/stderr.txt':dict(bytes=77,sha256='d'*64)})
        path = str(command_dir/'process.json')
        report['attempts'].append({**slot,'receipt':path,'qualified':True})
        row['samples_seconds'].append(sample); row['sample_details'].append(detail)
        row['sample_validation'].append(validation); row['sample_receipts'].append(path)
        row.update(median_seconds=statistics.median(row['samples_seconds']),
                   sample_stdev_seconds=statistics.stdev(row['samples_seconds']) if len(row['samples_seconds'])>1 else None,
                   full_validation=validation)
    meta = write(directory/'report.json', report)
    write(directory/'terminal.json', dict(status='complete', report_sha256=meta['sha256'],completed_samples=45,
        native_processes=45, integrity_errors=[], common_mutex_inode=79859134, common_mutex_held=True,
        artifacts=report['artifacts']))
    (root/m.OLD_PATH).parent.mkdir(parents=True,exist_ok=True)
    (root/m.OLD_PATH).write_bytes((ROOT/m.OLD_PATH).read_bytes())
    return report


class ImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads((ROOT/'archive/site/explorer/dist/data.json').read_text())
        historical, old = m.retained()
        selected = {k:r for k,r in data['programs'].items() if r['language'] == m.LANGUAGE}
        cls.other = 'fannkuchredux:mech-fannkuch-even'
        selected[cls.other] = data['programs'][cls.other]
        files = {r['source_sha256'] for r in old.values()}
        cls.before = dict(programs=selected, program_inventory={}, files={k:data['files'][k] for k in files},
            benchmarks=data['benchmarks'], reference_summary=data['reference_summary'],
            formatted_reference_summary=data['formatted_reference_summary'],
            interpreter_integration_audit=data['interpreter_integration_audit'], untouched={'opaque':[1,2,3]})
        cls.key = 'revcomp:mech-revcomp-optimized:resident'

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.report = fake_report(self.root)

    def imported(self):
        return m.import_dataset(self.before,self.report)

    def test_all15_inventory_history_and_portable_saved_verification(self):
        before = deepcopy(self.before); report = deepcopy(self.report)
        data,review = self.imported()
        self.assertEqual(len(data['program_inventory']),15)
        self.assertEqual(len(m.verify_saved_publication(self.root,data,self.before)),14)
        for key,row in self.before['programs'].items():
            if row['language'] == m.LANGUAGE:
                self.assertEqual(data['program_inventory'][key]['previous_measurement'],row)
            else:self.assertEqual(data['programs'][key],row)
        self.assertEqual(self.before,before); self.assertEqual(self.report,report)
        self.assertEqual(data['untouched'],before['untouched'])
        self.assertEqual(review['fresh_samples'],45)

    def test_phase_sum_and_kernel_selection_rejected(self):
        bad = deepcopy(self.report); row = bad['programs'][self.key]
        row['samples_seconds'] = [d['kernel_seconds']+d['prepare_seconds'] for d in row['sample_details']]
        row['median_seconds'] = statistics.median(row['samples_seconds']); row['sample_stdev_seconds'] = 0.
        with self.assertRaises(ValueError):m.import_dataset(self.before,bad)

    def test_outlier_is_retained_and_endpoint_can_change(self):
        even = 'fannkuchredux:mech-fannkuch-even:resident'
        self.report = fake_report(self.root,{self.key:[1.,2.,100000.],even:[1.,2.,3.]})
        data,review = self.imported()
        self.assertEqual(data['program_inventory'][self.key]['samples'],[1.,2.,100000.])
        self.assertEqual(data['program_inventory'][self.key]['seconds'],2.)
        self.assertEqual(review['endpoints']['fannkuchredux']['fast'],even)
        self.assertIn(even,data['programs'])
        m.verify_saved_publication(self.root,data,self.before)

    def test_failed_missing_extra_and_duplicate_runs_rejected(self):
        changes=[lambda x:x.update(status='failed'),lambda x:x.update(native_processes=44),
                 lambda x:x['programs'].pop(self.key),lambda x:x['attempts'].pop(),
                 lambda x:x['attempts'].__setitem__(1,deepcopy(x['attempts'][0])),
                 lambda x:x['attempts'][0].update(qualified=False),
                 lambda x:x['artifacts'].pop('samples/001/process.json')]
        for change in changes:
            with self.subTest(change=change):
                bad=deepcopy(self.report);change(bad)
                with self.assertRaises((ValueError,KeyError)):m.import_dataset(self.before,bad)

    def test_nonfinite_and_boolean_times_rejected(self):
        for invalid in (float('nan'),float('inf'),-1.,0.,True):
            bad=deepcopy(self.report);bad['programs'][self.key]['samples_seconds'][0]=invalid
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):m.import_dataset(self.before,bad)

    def test_changed_command_source_environment_output_and_pins_rejected(self):
        changes=[lambda x:x['programs'][self.key]['command'].append('--different'),
                 lambda x:x['programs'][self.key].update(source_sha256='a'*64),
                 lambda x:x['programs'][self.key]['runtime_environment'].update(OMP_NUM_THREADS='64'),
                 lambda x:x['programs'][self.key]['sample_validation'][0].update(sha256='a'*64),
                 lambda x:x['pins'].pop(x['programs'][self.key]['binary']),
                 lambda x:x['pins'].pop(m.PYTHON),
                 lambda x:x['pins'].pop(str(producer.HELPER)),
                 lambda x:x.update(controller_sha256='a'*64)]
        for change in changes:
            bad=deepcopy(self.report);change(bad)
            with self.subTest(change=change),self.assertRaises(ValueError):m.import_dataset(self.before,bad)

    def test_other_rows_source_baselines_and_history_are_preserved(self):
        data,_=self.imported()
        changes=[lambda x:x['programs'][self.other].update(seconds=123.),
                 lambda x:x['benchmarks'][0].update(baseline_seconds=123.),
                 lambda x:x['files'][next(iter(x['files']))].update(code='changed'),
                 lambda x:x['program_inventory'][self.key]['previous_measurement'].update(seconds=123.),
                 lambda x:x['interpreter_integration_audit'].update(status='changed')]
        for change in changes:
            bad=deepcopy(data);change(bad)
            with self.subTest(change=change),self.assertRaises(ValueError):m.verify_saved_publication(self.root,bad,self.before)

    def test_altered_receipt_clock_is_rejected_even_with_refreshed_artifact_metadata(self):
        path=self.root/Path(m.REPORT).parent/'samples/001/process.json'
        receipt=json.loads(path.read_text());receipt['clock_stop_ns']+=1
        meta=write(path,receipt);self.report['artifacts']['samples/001/process.json']=meta
        directory=self.root/Path(m.REPORT).parent
        report_meta=write(directory/'report.json',self.report)
        terminal=json.loads((directory/'terminal.json').read_text())
        terminal.update(artifacts=self.report['artifacts'],report_sha256=report_meta['sha256']);write(directory/'terminal.json',terminal)
        data,_=self.imported()
        with self.assertRaises(ValueError):m.verify_saved_publication(self.root,data,self.before)

    def test_missing_or_failed_terminal_rejected(self):
        data,_=self.imported();path=self.root/Path(m.REPORT).parent/'terminal.json'
        terminal=json.loads(path.read_text());terminal['status']='failed';write(path,terminal)
        with self.assertRaises(ValueError):m.verify_saved_publication(self.root,data,self.before)
        path.unlink()
        with self.assertRaises(FileNotFoundError):m.verify_saved_publication(self.root,data,self.before)

    def test_later_metadata_survives_archived_preservation_replay(self):
        immediate = deepcopy(self.before)
        immediate['programs'][self.key]['later_metadata'] = {'null_field':None,'label':'retained'}
        immediate['programs'][self.other]['later_metadata'] = {'null_field':None}
        data,_ = m.import_dataset(immediate,self.report)
        m.verify_saved_publication(self.root,data,self.before)
        del data['program_inventory'][self.key]['previous_measurement']['later_metadata']['null_field']
        with self.assertRaises(ValueError):m.verify_saved_publication(self.root,data,self.before)

    def test_missing_null_legacy_field_rejected(self):
        data,_=self.imported()
        self.assertIsNone(self.before['programs'][self.other]['formatted_loc'])
        del data['programs'][self.other]['formatted_loc']
        with self.assertRaises(ValueError):m.verify_saved_publication(self.root,data,self.before)

    def test_later_additive_catalog_records_and_fields_are_allowed(self):
        data,_=self.imported()
        extra=deepcopy(data['programs'][self.other]);extra.update(key='fannkuchredux:additional',id='additional')
        data['programs'][extra['key']]=extra
        data['programs'][self.other]['later_additive_field']={'value':None}
        m.verify_saved_publication(self.root,data,self.before)

    def test_overlapping_native_intervals_rejected(self):
        directory=self.root/Path(m.REPORT).parent
        first=json.loads((directory/'samples/001/process.json').read_text())
        path=directory/'samples/002/process.json';receipt=json.loads(path.read_text())
        duration=receipt['clock_stop_ns']-receipt['clock_start_ns']
        receipt.update(clock_start_ns=first['clock_start_ns'],clock_stop_ns=first['clock_start_ns']+duration)
        self.report['artifacts']['samples/002/process.json']=write(path,receipt)
        report_meta=write(directory/'report.json',self.report)
        terminal=json.loads((directory/'terminal.json').read_text())
        terminal.update(artifacts=self.report['artifacts'],report_sha256=report_meta['sha256'])
        write(directory/'terminal.json',terminal)
        data,_=self.imported()
        with self.assertRaises(ValueError):m.verify_saved_publication(self.root,data,self.before)


if __name__ == '__main__':unittest.main()
