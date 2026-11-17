import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmark_suite import (campaign_lock, comparison, digest, equal, file_digest, invoke,
    load_catalog, measurement_response, summarize, verify_response, worker_provenance)
from benchmark_suite import save, seal_evidence, validate_campaign, archive_evidence, EvidenceReader, signal_group
from suite_oracle import outputs
from run_native import parse_sections, text_size
import export_suite


class Contracts(unittest.TestCase):
    def setUp(self):
        self.case = load_catalog()['cases'][0]
        self.expected = outputs(self.case, len(self.case['measurement']['schedule']))

    def response(self):
        return {'protocol': 1, 'outcome': 'ok', 'output_name': 'result', 'outputs': self.expected,
                'before_execution': self.expected[:-1], 'metrics': {'managed_after_drop_bytes': 0}}

    def test_complete_trajectory_and_negative_control(self):
        self.assertEqual(verify_response(self.response(), self.expected, self.case), ('ok', None))
        broken = self.response()
        broken['before_execution'] = self.expected[1:]
        self.assertEqual(verify_response(broken, self.expected, self.case)[0], 'incorrect')

    def test_noop_and_partial_answers_rejected(self):
        for values in ([self.expected[0]] * len(self.expected), self.expected[:1]):
            response = self.response()
            response['outputs'] = values
            self.assertEqual(verify_response(response, self.expected, self.case)[0], 'incorrect')

    def test_output_identity_and_leaked_ownership_rejected(self):
        for key, value in [('output_name', 'last-node'), ('metrics', {'managed_after_drop_bytes': 1})]:
            response = self.response()
            response[key] = value
            self.assertEqual(verify_response(response, self.expected, self.case)[0], 'incorrect')

    def test_retained_snapshots_checked_after_later_turns(self):
        case = copy.deepcopy(self.case)
        case['measurement']['retain_snapshots'] = True
        response = self.response()
        response['retained_outputs'] = [self.expected[-1]] * len(self.expected)
        self.assertEqual(verify_response(response, self.expected, case)[0], 'incorrect')

    def test_shapes_and_nonfinite_numbers_are_not_tolerated(self):
        task = self.case['task']
        self.assertFalse(equal(float('nan'), 1.0, task))
        self.assertFalse(equal(True, 1, task))
        self.assertFalse(equal({'kind':'matrix','shape':[1,2],'values':[1,2]},
                               {'kind':'matrix','shape':[2,1],'values':[1,2]}, task))

    def test_tolerance_does_not_hide_missing_values(self):
        task = self.case['task']
        self.assertTrue(equal(2.0 + 1e-11, 2.0, task))
        self.assertFalse(equal([2.0], [2.0, 3.0], task))

    def test_measured_endpoint_and_numeric_metrics_required(self):
        response = {'outcome':'ok','iterations':6,'output_name':'result','final_output':self.expected[-1],
                    'metrics':{'resident_turn_seconds':1e-5,'source_to_artifact_seconds':1e-3,
                               'artifact_bytes':100,'managed_after_drop_bytes':0}}
        self.assertEqual(measurement_response(response,self.expected[-1],self.case,6)[0],'ok')
        response['metrics']['resident_turn_seconds'] = float('nan')
        self.assertEqual(measurement_response(response,self.expected[-1],self.case,6)[0],'error')
        response['metrics']['resident_turn_seconds'] = 1e-5
        response['final_output'] = self.expected[0]
        self.assertEqual(measurement_response(response,self.expected[-1],self.case,6)[0],'incorrect')

    def test_every_implemented_case_has_an_independent_oracle(self):
        for case in load_catalog()['cases']:
            if case['progress'] != 'planned' and set(case['backends']) & {'source','bytecode','jit','process-workers'}:
                count = len(case['measurement']['schedule']) * 2
                self.assertEqual(len(outputs(case,count)),count,case['id'])

    def test_planned_coverage_is_separate_from_capability(self):
        for case in load_catalog()['cases']:
            if case['progress'] == 'planned':
                self.assertNotIn('capability',case)
                self.assertEqual(case['backends'],[])


class Comparison(unittest.TestCase):
    def record(self,values):
        return {'task_hash':'task','measurement_hash':'measurement','source_sha256':'source',
                'backend':'source','environment_hash':'host','outcome':'ok',
                'samples':[{'fork':i,'metrics':{'resident_turn_seconds':value}} for i,value in enumerate(values)]}

    def test_boundary_source_environment_and_backend_must_match(self):
        for field in ('task_hash','measurement_hash','source_sha256','environment_hash','backend','feature_profile'):
            a,b=self.record([1]*5),self.record([2]*5)
            b[field]='changed'
            self.assertEqual(comparison(a,b)['status'],'incompatible',field)

    def test_implementation_allocation_changes_do_not_invalidate_task(self):
        a,b=self.record([1]*5),self.record([.5]*5)
        b['implementation']={'allocations':0,'algorithm':'improved'}
        self.assertEqual(comparison(a,b)['status'],'improvement')

    def test_three_forks_do_not_enable_regression_decisions(self):
        result=comparison(self.record([1]*3),self.record([2]*3))
        self.assertEqual(result['status'],'informational')
        self.assertFalse(result['performance_gate'])

    def test_screening_requires_confirmation_and_is_reproducible(self):
        a,b=self.record([1,1.01,.99,1.02,1]),self.record([2,2.01,1.99,2,2.02])
        first=comparison(a,b,seed=10)
        self.assertEqual(first,comparison(a,b,seed=10))
        self.assertEqual(first['status'],'suspected_regression')
        self.assertIn('confirmation',first['reason'])
        self.assertFalse(first['performance_gate'])

    def test_failure_cannot_create_a_ratio(self):
        a,b=self.record([1]*5),self.record([.5]*5)
        b['outcome']='incorrect'
        self.assertNotIn('ratio',comparison(a,b))

    def test_raw_samples_retained(self):
        samples=[{'metrics':{'seconds':n}} for n in [3,1,2]]
        result=summarize(samples)['seconds']
        self.assertEqual(result['median'],2)
        self.assertEqual(result['samples'],[3,1,2])


class Supervision(unittest.TestCase):
    def test_orphaned_zombie_group_permission_race_is_harmless(self):
        with patch('benchmark_suite.os.killpg',side_effect=PermissionError), patch('benchmark_suite.subprocess.check_output',return_value='100 Z+\n'):
            signal_group(100,9)

    def test_permission_failure_for_live_group_is_not_hidden(self):
        with patch('benchmark_suite.os.killpg',side_effect=PermissionError), patch('benchmark_suite.subprocess.check_output',return_value='100 S\n'):
            with self.assertRaises(PermissionError):signal_group(100,9)
    def test_valid_malformed_crash_and_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            tests=[('ok','print(\'{"protocol":1,"outcome":"ok"}\')',1,'ok'),
                   ('bad','print("invalid")',1,'error'),('crash','raise SystemExit(3)',1,'crash'),
                   ('timeout','import time; time.sleep(10)',.1,'timeout')]
            for name,script,timeout,expected in tests:
                result=invoke([sys.executable,'-c',script],{},root/name,timeout)
                self.assertEqual(result['outcome'],expected)
                self.assertTrue((root/name/'request.json').is_file())
                self.assertTrue((root/name/'stdout.json').is_file())

    def test_process_descendants_are_stopped_even_after_leader_exits(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            marker=root/'escaped'
            child=f'import time; from pathlib import Path; time.sleep(.6); Path({str(marker)!r}).write_text("leaked")'
            parent=f'import subprocess,sys; subprocess.Popen([sys.executable,"-c",{child!r}]); print(\'{{"protocol":1,"outcome":"ok"}}\')'
            result=invoke([sys.executable,'-c',parent],{},root/'raw',2)
            self.assertEqual(result['outcome'],'ok')
            time.sleep(.8)
            self.assertFalse(marker.exists())

    def test_locks_prevent_competing_campaigns(self):
        with tempfile.TemporaryDirectory() as directory:
            with campaign_lock(directory):
                with self.assertRaises(ValueError):
                    with campaign_lock(directory): pass
            self.assertFalse((Path(directory)/'campaign.lock').exists())

    def test_worker_hash_is_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            binary=root/'worker'
            binary.write_text('worker')
            (root/'src').mkdir()
            for name in ('src/main.rs','Cargo.toml','Cargo.lock'):(root/name).write_text(name)
            manifest=root/'worker.json'
            manifest.write_text(json.dumps({'protocol':1,'binary':str(binary),'binary_sha256':file_digest(binary),
                'revision':'revision','adapter_sha256':file_digest(root/'src/main.rs'),
                'manifest_sha256':file_digest(root/'Cargo.toml'),'lock_sha256':file_digest(root/'Cargo.lock')}))
            worker_provenance(manifest)
            binary.write_text('changed')
            with self.assertRaises(ValueError):worker_provenance(manifest)

    def test_sealed_evidence_cannot_be_silently_changed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            save(root/'raw/one/supervised.json',{'outcome':'ok','metrics':{'seconds':1}})
            seal_evidence(root)
            campaign={'schema':'mech.benchmark-campaign.v1','complete':True,'environment':{},
                      'environment_hash':digest({}),'results':[]}
            self.assertTrue(validate_campaign(root,campaign))
            (root/'raw/one/supervised.json').write_text('changed')
            with self.assertRaises(ValueError):validate_campaign(root,campaign)

    def test_raw_archive_is_portable_and_detects_tampering(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            save(root/'raw/one/supervised.json',{'outcome':'ok','metrics':{'seconds':1}})
            expected=(root/'raw/one/supervised.json').read_bytes()
            seal_evidence(root)
            archive_evidence(root)
            shutil.rmtree(root/'raw')
            with EvidenceReader(root) as reader:self.assertEqual(reader.read('raw/one/supervised.json'),expected)
            with (root/'raw.tar.gz').open('ab') as stream:stream.write(b'changed')
            with self.assertRaises(ValueError):
                with EvidenceReader(root):pass


class NativeFootprint(unittest.TestCase):
    def test_macho_object_sections_keep_segment_identity(self):
        sections=parse_sections('Segment : 220\n\tSection (__TEXT, __text): 200\n\tSection (__TEXT, __const): 20\n','Darwin')
        self.assertEqual(sections,{'__TEXT/__text':200,'__TEXT/__const':20})
        self.assertEqual(text_size(sections),200)

    def test_linked_const_sections_do_not_overwrite_each_other(self):
        sections=parse_sections('Segment __TEXT: 300\nSection __text: 200\nSection __const: 100\nSegment __DATA_CONST: 80\nSection __const: 80\n','Darwin')
        self.assertEqual(sections['__TEXT/__const'],100)
        self.assertEqual(sections['__DATA_CONST/__const'],80)
        self.assertEqual(text_size(sections),200)

    def test_elf_text_excludes_data_and_debug_sections(self):
        sections=parse_sections('.text 120 0\n.text.entry 20 0\n.data 80 0\n.debug_info 90 0\n','Linux')
        self.assertEqual(text_size(sections),140)
        self.assertIsNone(text_size({'__TEXT/__const':20}))


class RetainedMeasurements(unittest.TestCase):
    def test_compressed_size_is_bound_to_the_actual_worker_bytes(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); parent=root/'raw/program/stdout.json'
            save(parent,{'outcome':'ok','application_results':[{'name':'case','raw_hex':'abcdef','metrics':{'seconds':1}}],'metrics':{'artifact_bytes':12}})
            metrics={'seconds':1,'artifact_bytes':12,'output_bytes':3}
            receipt={'outcome':'ok','metrics':metrics,'derived_metrics':['output_bytes'],
                'final_output':{'sha256':hashlib.sha256(bytes.fromhex('abcdef')).hexdigest()},
                'parent_observation':{'path':'raw/program/stdout.json','sha256':file_digest(parent),'case':'case'}}
            record={'case_id':'case','backend':'program-jit','lane':'candidate','progress':'measured','outcome':'ok',
                'task':{},'task_hash':digest({}),'measurement':{},'measurement_hash':digest({}),
                'source':'test','source_sha256':hashlib.sha256(b'test').hexdigest(),'environment_hash':digest({}),
                'samples':[{'fork':0,'raw':'raw/fork-1','metrics':metrics}]}
            record['summary']=summarize(record['samples'])
            campaign={'schema':'mech.benchmark-campaign.v1','complete':True,'environment':{},'environment_hash':digest({}),'results':[record]}
            save(root/'raw/fork-1/supervised.json',receipt);seal_evidence(root)
            self.assertTrue(validate_campaign(root,campaign))
            metrics['output_bytes']=2;record['summary']=summarize(record['samples'])
            save(root/'raw/fork-1/supervised.json',receipt);seal_evidence(root)
            with self.assertRaisesRegex(ValueError,'actual program worker'):validate_campaign(root,campaign)

    def test_resealed_receipt_cannot_replace_original_retained_timing(self):
        import gzip
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source={'samples':[{'round':0,'variant':'mech-test','exit':0,'exact_output':True,
                                'post_json_seconds':.001,'whole_process_seconds':.03}]}
            parent=root/'raw/report.json.gz';parent.parent.mkdir()
            parent.write_bytes(gzip.compress(json.dumps(source).encode(),mtime=0))
            metrics={'post_json_seconds':.001,'native_process_seconds':.03}
            receipt={'outcome':'ok','metrics':metrics,'retained_observation':{'path':'raw/report.json.gz',
                'sha256':file_digest(parent),'cohort':'confirmation','variant':'mech-test','round':0}}
            record={'case_id':'test','backend':'related-managed','lane':'candidate','progress':'measured','outcome':'ok',
                'task':{},'task_hash':digest({}),'measurement':{},'measurement_hash':digest({}),
                'source':'test','source_sha256':hashlib.sha256(b'test').hexdigest(),'environment_hash':digest({}),
                'samples':[{'fork':0,'raw':'raw/fork-1','metrics':metrics}]}
            record['summary']=summarize(record['samples'])
            campaign={'schema':'mech.benchmark-campaign.v1','complete':True,'environment':{},'environment_hash':digest({}),'results':[record]}
            save(root/'raw/fork-1/supervised.json',receipt);seal_evidence(root)
            self.assertTrue(validate_campaign(root,campaign))
            metrics['post_json_seconds']=.0001
            record['summary']=summarize(record['samples'])
            save(root/'raw/fork-1/supervised.json',receipt);seal_evidence(root)
            with self.assertRaisesRegex(ValueError,'differs from original measurement'):validate_campaign(root,campaign)


class ExportPreservation(unittest.TestCase):
    def test_large_download_is_compressed_without_changing_any_bytes(self):
        import gzip
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); campaign=root/'results/campaigns/compressed'
            campaign.mkdir(parents=True)
            save(campaign/'campaign.json',{'schema':'mech.benchmark-campaign.v1','id':'compressed','complete':True,
                'started_at':'2026-11-17','environment':{},'environment_hash':digest({}),'results':[]})
            raw=campaign/'raw/verify/supervised.json';save(raw,{'outputs':['complete trajectory']*10000})
            original=raw.read_bytes();seal_evidence(campaign);archive_evidence(campaign)
            archive=campaign/'raw.tar.gz'
            pin={'sha256':file_digest(archive),'bytes':archive.stat().st_size}
            save(root/'suite/evidence-hosting.json',{'schema':'mech.benchmark-evidence-hosting.v1','source_commit':'a'*40,'archives':{'compressed':pin}})
            with patch.object(export_suite,'load_catalog',return_value={'cases':[]}):
                bundle=export_suite.export(root/'public',root)
            index=bundle['campaigns'][0]
            self.assertNotIn('compressed_evidence',index)
            record=json.loads((root/'public'/index['context_path']).read_text())['campaign']
            self.assertEqual(record['compressed_evidence']['raw/verify/supervised.json'],'raw/verify/supervised.json.gz')
            self.assertEqual(gzip.decompress((root/'public/campaign-evidence/compressed/raw/verify/supervised.json.gz').read_bytes()),original)
            self.assertFalse((root/'public/campaign-evidence/compressed/raw.tar.gz').exists())
            self.assertEqual(bundle['external_evidence']['campaign-evidence/compressed/raw.tar.gz']['sha256'],pin['sha256'])
            self.assertIn('/'+('a'*40)+'/results/campaigns/compressed/raw.tar.gz',record['raw_archive_url'])
            self.assertEqual(file_digest(archive),pin['sha256'])
            save(root/'suite/evidence-hosting.json',{'schema':'mech.benchmark-evidence-hosting.v1','source_commit':'a'*40,'archives':{'compressed':{**pin,'sha256':'0'*64}}})
            with patch.object(export_suite,'load_catalog',return_value={'cases':[]}):
                with self.assertRaisesRegex(ValueError,'differs from retained bytes'):export_suite.export(root/'public',root)

    def test_summary_defers_sources_schedules_and_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);campaign=root/'results/campaigns/lazy'
            case=copy.deepcopy(load_catalog()['cases'][0]);host=digest({})
            samples=[{'fork':0,'raw':'raw/fork-1','metrics':{'resident_turn_seconds':.00001}}]
            record={'case_id':case['id'],'backend':'source','lane':'candidate','revision':'revision',
                'task':case['task'],'task_hash':digest(case['task']),'measurement':case['measurement'],
                'measurement_hash':digest(case['measurement']),'source':'exact measured source',
                'source_sha256':__import__('hashlib').sha256(b'exact measured source').hexdigest(),
                'environment_hash':host,'outcome':'ok','progress':'measured','samples':samples,'summary':summarize(samples)}
            save(campaign/'campaign.json',{'schema':'mech.benchmark-campaign.v1','id':'lazy','complete':True,
                'started_at':'2026-11-17','environment':{},'environment_hash':host,'results':[record]})
            save(campaign/'raw/fork-1/supervised.json',{'outcome':'ok','metrics':samples[0]['metrics']})
            save(campaign/'raw/fork-1/request.json',{'schedule':case['measurement']['schedule']})
            seal_evidence(campaign)
            with patch.object(export_suite,'load_catalog',return_value={'cases':[case]}):
                bundle=export_suite.export(root/'public',root)
            self.assertEqual(bundle['schema'],'mech.benchmark-dashboard.v2')
            summary=bundle['campaigns'][0]['results'][0]
            for field in ('source','samples','task','verification'):self.assertNotIn(field,summary)
            self.assertNotIn('schedule',summary['measurement'])
            self.assertNotIn('measurement',bundle['catalog']['cases'][0])
            detail=json.loads((root/'public'/summary['detail_path']).read_text())
            self.assertEqual(detail['record'],record)
            self.assertEqual(detail['definition'],case)
            self.assertEqual(summary['summary']['resident_turn_seconds']['median'],record['summary']['resident_turn_seconds']['median'])
            self.assertFalse((root/'public/campaign-evidence/lazy/raw/fork-1/request.json').exists())
            self.assertEqual((root/'public/campaign-evidence/lazy/raw/fork-1/supervised.json').read_bytes(),(campaign/'raw/fork-1/supervised.json').read_bytes())

    def test_independent_c_oracle_source_is_downloadable(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); campaign=root/'results/campaigns/oracle-source'
            campaign.mkdir(parents=True)
            save(campaign/'campaign.json',{'schema':'mech.benchmark-campaign.v1','id':'oracle-source','complete':True,
                'started_at':'2026-11-17','environment':{},'environment_hash':digest({}),'results':[]})
            (campaign/'oracle.c').write_text('int main(void) { return 0; }\n')
            seal_evidence(campaign)
            with patch.object(export_suite,'load_catalog',return_value={'cases':[]}):
                export_suite.export(root/'public',root)
            self.assertEqual((root/'public/campaign-evidence/oracle-source/oracle.c').read_bytes(),(campaign/'oracle.c').read_bytes())

    def test_bad_incoming_evidence_preserves_existing_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            campaign=root/'results/campaigns/broken'
            campaign.mkdir(parents=True)
            save(campaign/'campaign.json',{'schema':'mech.benchmark-campaign.v1','id':'broken','complete':True,
                'environment':{},'environment_hash':digest({}),'results':[]})
            (campaign/'sample.txt').write_text('original')
            seal_evidence(campaign)
            (campaign/'sample.txt').write_text('tampered')
            previous=root/'public/campaign-evidence/saved.txt'
            previous.parent.mkdir(parents=True)
            previous.write_text('previous successful export')
            with patch.object(export_suite,'load_catalog',return_value={'cases':[]}):
                with self.assertRaises(ValueError):export_suite.export(root/'public',root)
            self.assertEqual(previous.read_text(),'previous successful export')


if __name__ == '__main__':
    unittest.main()
