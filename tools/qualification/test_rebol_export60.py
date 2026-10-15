"""Focused synthetic full60 export and owned-output faults; no actual export."""
import copy
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import signal
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


HERE=Path(__file__).parent
e=load('rebol60_export_test_subject',HERE/'rebol_export60.py')
old=load('rebol60_export_synthetic_shapes',HERE/'test_rebol_export.py')


def fixture(failed=None):
    # Reuse only invented source/receipt shapes, with exactly one generated form.
    with patch.object(old.e,'FORMS',('compact',)):
        r,plan,review,metadata,read_raw,content=old.fixture(failed)
    pins=review['verified_file_pins']
    policy_raw=b'synthetic single canonical subject policy\n'
    policy=e.ref(e.POLICY,e.digest(policy_raw));content[policy['path']]=policy_raw
    pins[policy['path']]=policy['sha256'];plan['pins'][policy['path']]=policy['sha256']
    plan.update(cohort_policy_file=policy,subject_policy=dict(authored_source_forms_per_workload=1,
        publication_forms=['compact'],duplicate_program_records=0,distinct_optimization_claim=False))
    for admission in (plan['qualification'],review['qualification']):
        for base in admission['bases']:base['alias_policy']['publication_forms']=['compact']
    for row in r.schedule(plan)[1].values():
        if row['language']=='rebol3':row['alias_policy']['publication_forms']=['compact']
    review.update(schema='rebol-independent-full60-reconciliation-v1',
        status='full60-reconciled-awaiting-runtime-and-publication-review',
        actual_rebol_processes=sum(len(row['attempts']) for row in review['profiles'].values() if row['language']=='rebol3'),
        actual_matched_mech_processes=sum(len(row['attempts']) for row in review['profiles'].values() if row['language']=='mech'))
    plan_path=review['plan']['path'];content[plan_path]=e.encoded(plan)
    pins[plan_path]=e.digest(content[plan_path]);review['plan']['sha256']=pins[plan_path]
    return r,plan,review,metadata,read_raw,content


def candidate(failed=None):
    args=fixture(failed);return e.build_candidate(*args[:5]),args


class Export60Tests(unittest.TestCase):
    def test_ten_canonical_programs_sixty_unique_observations_and_shared_endpoints(self):
        value,args=candidate()
        self.assertEqual(value['schema'],'rebol-full60-publication-candidate-v1')
        self.assertEqual((len(value['program_inventory']),len(value['files']),len(value['matched_mech_controls'])),(10,15,10))
        self.assertEqual((value['planned_rebol_samples'],value['planned_matched_mech_samples'],value['planned_full_processes']),
                         (30,30,60))
        self.assertEqual((value['planned_profile_rows'],value['source_forms'],value['timing_aliases']),(20,10,0))
        self.assertEqual((value['actual_rebol_processes'],value['actual_matched_mech_processes']),(30,30))
        self.assertEqual(value['cohort_policy_file'],args[1]['cohort_policy_file'])
        attempts=[]
        for key,row in value['program_inventory'].items():
            self.assertTrue(key.endswith('-compact'));self.assertEqual(row['variant'],'compact')
            self.assertIsNone(row['source_alias_of']);self.assertIsNone(row['timing_alias_of'])
            self.assertNotIn('source_alias_group',row);self.assertNotIn('source_alias_note',row)
            endpoint=value['endpoint_proposals'][row['benchmark']]
            self.assertEqual((endpoint['fast'],endpoint['small'],endpoint['programs']),(key,key,[key]))
            self.assertEqual(len(row['files']),5 if row['benchmark'] in ('pidigits','regexredux') else 4)
            self.assertEqual(row['loc'],sum(role['normalized_loc'] for role in row['file_roles'].values()))
            self.assertTrue(row['loc']>row['physical_loc']);self.assertIsNone(row['formatted_loc'])
            self.assertEqual(sum(role['role']=='general-library-helper' for role in row['file_roles'].values()),1)
            attempts.extend(sample['attempt'] for sample in row['sample_execution_metadata'])
        attempts.extend(sample['attempt'] for row in value['matched_mech_controls'].values() for sample in row['sample_execution_metadata'])
        self.assertEqual(sorted(attempts),list(range(1,61)))
        self.assertFalse(value['chart_admission']);self.assertFalse(value['dataset_files_changed'])
        self.assertEqual(value['native_processes_started'],0)

    def test_failed_subject_has_no_replacement_endpoint_or_invented_output(self):
        value,_=candidate('rebol-regexredux-compact');row=value['program_inventory']['regexredux:rebol-regexredux-compact']
        self.assertIsNone(row['seconds']);self.assertFalse(row['eligible_for_publication_review'])
        self.assertEqual(value['endpoint_proposals']['regexredux'],dict(fast=None,small=None,programs=[],chart_admission=False))
        sample=row['sample_execution_metadata'][0]
        for field in ('seconds','stdout_bytes','stdout_sha256','validation'):self.assertIsNone(sample[field])
        self.assertEqual(sample['error_type'],'TimeoutError')
        self.assertEqual((value['actual_rebol_processes'],value['actual_full_native_processes']),(28,58))

    def test_failed_control_retains_subject_samples_without_comparative_endpoint(self):
        value,_=candidate('regexredux:rebol-full-study:mech-control')
        row=value['program_inventory']['regexredux:rebol-regexredux-compact']
        self.assertEqual(len(row['samples']),3);self.assertIsNotNone(row['seconds'])
        self.assertFalse(row['eligible_for_publication_review']);self.assertIsNone(row['time_ratio_to_matched_mech'])
        self.assertEqual(value['endpoint_proposals']['regexredux']['programs'],[])
        self.assertIsNone(value['matched_mech_controls']['regexredux']['sample_execution_metadata'][0]['stdout_sha256'])

    def test_wrong_policy_inventory_and_counted_source_scope_reject(self):
        for fault in ('policy','policy_path','extra_form','source','formatted','alias'):
            r,plan,review,metadata,read_raw,_=fixture()
            if fault=='policy':plan['subject_policy']['publication_forms'].append('optimized')
            elif fault=='policy_path':plan['cohort_policy_file']['path']=str(e.PACKET/'README.md')
            elif fault=='extra_form':
                slots,rows=r.schedule(plan);rows['rebol-regexredux-optimized']=copy.deepcopy(rows['rebol-regexredux-compact'])
            elif fault=='source':del plan['pins'][plan['qualification']['bases'][0]['physical_inputs'][3]['path']]
            elif fault=='formatted':plan['qualification']['bases'][0]['formatted_loc']=1
            else:r.schedule(plan)[1]['rebol-regexredux-compact']['timing_alias_of']='invented'
            with self.subTest(fault=fault),self.assertRaises((AssertionError,KeyError)):
                e.build_candidate(r,plan,review,metadata,read_raw)

    def test_runtime_and_statistics_cannot_be_promoted(self):
        for field in ('runtime_source_equivalence_proven','observed_in_each_timed_process',
                      'runtime_gc_configuration_observed','gc_numeric_defaults_claimed'):
            args=list(fixture());args[3][field]=True
            with self.subTest(field=field),self.assertRaises(AssertionError):e.build_candidate(*args[:5])
        for field,value in (('median_seconds',999),('endpoint_eligible',False),('time_x_mech',999)):
            args=list(fixture());args[2]['profiles']['rebol-regexredux-compact'][field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):e.build_candidate(*args[:5])

    def test_all_three_receipt_bytes_and_success_output_fields_are_required(self):
        for fault in ('raw','supervisor','outer','output','owner'):
            r,plan,review,metadata,read_raw,content=fixture()
            stem='001-rebol-regexredux-compact'
            path=plan['output']+('/outer-supervisor/'+stem+'.json' if fault=='outer' else '/attempts/'+stem+
                ('.json' if fault=='raw' else '.supervisor.json'))
            if fault in ('raw','supervisor','outer'):content[path]+=b'changed'
            else:
                item=json.loads(content[path])
                if fault=='output':del item['stdout_sha256']
                else:item['key']='rebol-regexredux-optimized'
                content[path]=e.encoded(item);review['verified_file_pins'][path]=e.digest(content[path])
            with self.subTest(fault=fault),self.assertRaises((AssertionError,KeyError)):
                e.build_candidate(r,plan,review,metadata,read_raw)

    def test_cross_program_observation_duplication_and_totals_reject(self):
        for fault in ('duplicate','count'):
            r,plan,review,metadata,read_raw,content=fixture()
            if fault=='count':review['actual_rebol_processes']+=1
            else:
                row=review['profiles']['rebol-revcomp-compact'];previous=row['attempts'][0];row['attempts'][0]=1
                for suffix,directory in (('.json','attempts'),('.supervisor.json','attempts'),('.json','outer-supervisor')):
                    old_path=plan['output']+'/'+directory+f'/{previous:03d}-rebol-revcomp-compact'+suffix
                    path=plan['output']+'/'+directory+'/001-rebol-revcomp-compact'+suffix
                    item=json.loads(content[old_path])
                    if directory=='attempts':item['attempt']=1
                    content[path]=e.encoded(item);review['verified_file_pins'][path]=e.digest(content[path])
            with self.subTest(fault=fault),self.assertRaisesRegex(AssertionError,
                    'duplicated across programs|Native sample accounting differs'):
                e.build_candidate(r,plan,review,metadata,read_raw)

    def test_source_review_binds_exact_reader_and_policy(self):
        review=dict(schema='rebol-full60-export-source-review-v1',
            status='independent-source-review-complete-actual-export-pending',independent_review=True,
            native_execution=False,chart_admission=False,files={str(path.relative_to(e.ROOT)):'1'*64 for path in e.FILES},
            dependencies={str(e.RECONCILER.relative_to(e.ROOT)):e.RECONCILER_SHA,
                          str(e.POLICY.relative_to(e.ROOT)):'2'*64})
        binding=e.ref(e.PACKET/'synthetic-source-review.json','3'*64)
        def checked(path,expected):return e.encoded(review) if str(path)==binding['path'] else b'synthetic reviewed source'
        with patch.object(e,'checked',side_effect=checked),patch.object(e,'load_reconciler',return_value='reader') as loader:
            reader,pins=e.source_intake(binding);self.assertEqual(reader,'reader')
            loader.assert_called_once_with(e.RECONCILER_SHA);self.assertEqual(pins[str(e.POLICY)],'2'*64)
            del review['dependencies'][str(e.POLICY.relative_to(e.ROOT))]
            with self.assertRaisesRegex(AssertionError,'Actual export source review required'):e.source_intake(binding)
        with patch.object(e,'checked') as read:
            with self.assertRaisesRegex(AssertionError,'reader identity differs'):e.load_reconciler('0'*64)
            read.assert_not_called()

    def test_stop_after_creation_is_deferred_until_owned_registration(self):
        for number in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):
            with self.subTest(signal=number),tempfile.TemporaryDirectory() as temp:
                path=Path(temp).resolve()/'candidate.json';owned={};observed=[];original_open=Path.open
                def interrupted_open(target,*args,**kwargs):
                    stream=original_open(target,*args,**kwargs)
                    if target==path and args==('xb',):os.kill(os.getpid(),number)
                    return stream
                def cleanup():
                    observed.append(owned.get('complete'));e.remove_owned(path,owned)
                with e.stop_handlers(),patch.object(Path,'open',interrupted_open):
                    with self.assertRaises(InterruptedError):
                        with e.preserve_failure_cleanup(cleanup):e.write_new(path,dict(a=1),owned)
                self.assertEqual(observed,[True]);self.assertFalse(path.exists());self.assertEqual(owned,{})

    def test_completed_candidate_truncation_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp).resolve()/'candidate.json';owned={};e.write_new(path,dict(a=1),owned)
            truncated=owned['raw'][:4];path.write_bytes(truncated)
            with self.assertRaises(AssertionError):e.remove_owned(path,owned)
            self.assertEqual(path.read_bytes(),truncated)

    def test_save_closure_checks_and_cleanup_precede_lease_release(self):
        for fault in ('metadata','candidate','late_helper'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temp:
                root=Path(temp).resolve();output=root/'candidate.json';review=dict(synthetic='review')
                documents=dict(plan=dict(output=str(root/'run')),reconciliation=review,metadata=dict(evidence={}),source_review={})
                args=SimpleNamespace(output=output,durable_directory=root/'job')
                for name,value in documents.items():
                    path=root/(name+'.json');raw=e.encoded(value);path.write_bytes(raw)
                    setattr(args,name,path);setattr(args,name+'_sha256',e.digest(raw))
                events=[];source_pins={str(Path(e.__file__).resolve()):e.digest(Path(e.__file__).read_bytes())}
                def context_factory(args,*,final_consumer_check,on_exit_failure):
                    @contextmanager
                    def held():
                        events.append('held')
                        try:
                            yield review
                            if fault=='late_helper':raise ValueError('synthetic late helper failure')
                            (args.metadata if fault=='metadata' else output).write_bytes(b'external')
                            final_consumer_check()
                        except BaseException:
                            events.append('cleanup-held');on_exit_failure();raise
                        finally:events.append('released')
                    return object(),source_pins,held()
                with patch.object(e,'export_context',side_effect=context_factory), \
                     patch.object(e,'build_candidate',return_value=dict(synthetic='candidate')):
                    with self.assertRaises(BaseException):e.save_candidate(args)
                self.assertEqual(events,['held','cleanup-held','released'])
                if fault=='candidate':self.assertEqual(output.read_bytes(),b'external')
                else:self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
