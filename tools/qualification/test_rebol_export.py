"""Synthetic candidate/ownership tests; no actual reconciliation or native work."""
import copy
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import signal
import statistics
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('rebol_export_test_subject',Path(__file__).with_name('rebol_export.py'))
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)


def fixture(failed=None):
    content={};pins={}
    def add(path,raw):
        content[path]=raw;pins[path]=e.digest(raw);return dict(path=path,sha256=pins[path])
    support={name:dict(add(str(e.ROOT/'synthetic'/name),(name+'\n').encode()),role=role,counted=True,
                      canonical_loc=3,physical_loc=2) for name,role in (
        ('clbg_io.reb','application-helper'),('clbg_primitives.reb','application-launcher'),
        ('clbg_primitives.c','general-library-helper'),('clbg_big.reb','application-helper'),
        ('clbg_regex.reb','application-helper'))}
    runtime=add(str(e.ROOT/'synthetic/runtime'),b'synthetic-runtime')
    image=add(str(e.ROOT/'synthetic/extension'),b'synthetic-image')
    metadata_evidence=add(str(e.ROOT/'synthetic/metadata.json'),b'{}\n')
    qualification_ref=add(str(e.ROOT/'synthetic/qualification.json'),b'{}\n')
    count_ref=add(str(e.ROOT/'synthetic/count.json'),b'{}\n')
    bases=[];originals={};manifests={};slots=[]
    for bench in e.BENCHES:
        main=add(str(e.ROOT/'synthetic'/bench/'main.reb'),('Rebol [] ; '+bench+'\n').encode())
        # The explicit list retains the main+IO+loader+whole-C order.
        members=[dict(main,role='application',counted=True,canonical_loc=5,physical_loc=1)]
        members.extend(copy.deepcopy(support[name]) for name in ('clbg_io.reb','clbg_primitives.reb','clbg_primitives.c'))
        if bench in ('pidigits','regexredux'):
            members.append(copy.deepcopy(support['clbg_big.reb' if bench=='pidigits' else 'clbg_regex.reb']))
        base=dict(benchmark=bench,original_profile_id=f'rebol-{bench}-baseline-v1',main=main,physical_inputs=members,
            canonical_loc=sum(item['canonical_loc'] for item in members),physical_loc=sum(item['physical_loc'] for item in members),
            formatted_loc=None,alias_policy=dict(authored_source_forms=1,publication_forms=['compact','optimized'],
                distinct_optimization_claim=False,copied_timing_allowed=False))
        bases.append(base);rows=[]
        for form in e.FORMS:
            identity=f'rebol-{bench}-{form}'
            row=dict(id=identity,key=identity,language='rebol3',benchmark=bench,variant=form,source=main['path'],
                source_sha256=main['sha256'],binary=runtime['path'],binary_sha256=runtime['sha256'],
                physical_inputs=copy.deepcopy(members),canonical_loc=base['canonical_loc'],physical_loc=base['physical_loc'],
                formatted_loc=None,source_work_qualified=True,canonical_loc_qualified=True,formatted_loc_qualified=False,
                original_profile_id=base['original_profile_id'],alias_policy=copy.deepcopy(base['alias_policy']),
                separate_fresh_samples_required=True,optimization_claim=False,command=[runtime['path'],'-q','-s',main['path']],
                runtime_environment={},cwd=str(e.ROOT),corrections={})
            rows.append(row);originals[identity]=row
        control_source=add(str(e.ROOT/'synthetic'/bench/'control.mec'),('control '+bench).encode())
        control=dict(id='mech-aot-control',key=bench+':rebol-full-study:mech-control',language='mech',benchmark=bench,
            source=control_source['path'],source_sha256=control_source['sha256'],binary_sha256='f'*64)
        rows.append(control);originals[control['key']]=control;manifests[bench]=dict(profiles=rows)
        for round_index in range(3):
            for row in rows[round_index:]+rows[:round_index]:
                slots.append((bench,round_index+1,row['id'],row['key']))
    admission=dict(schema='rebol-pre-timing-admission-v1',manifest=qualification_ref,bases=bases,
        runtime=dict(binary=runtime,declared_image_closure=[],runtime_source_equivalence_proven=False),extension_image=image,
        references=dict(count_review=count_ref),scope=dict(limitations=['synthetic scoped evidence']))
    plan=dict(output=str(e.ROOT/'synthetic/run'),qualification=admission,qualification_manifest=qualification_ref,
              manifests=manifests,pins=copy.deepcopy(pins))
    summaries={key:dict(**{field:row[field] for field in ('key','id','language','benchmark','source','source_sha256','binary_sha256')},
        attempts=[],samples_seconds=[],failed_attempt=None,full_workload_qualified=True) for key,row in originals.items()}
    number=0;skipped=[]
    for bench,round_index,identity,key in slots:
        summary=summaries[key]
        if summary['failed_attempt'] is not None:
            skipped.append(dict(benchmark=bench,round=round_index,id=identity,key=key));continue
        number+=1;good=key!=failed
        item=dict(attempt=number,round=round_index,id=identity,key=key,benchmark=bench,qualified=good,
                  started_at='start',finished_at='end')
        if good:
            seconds=round_index+(1 if identity.endswith('-optimized') else 2)
            item.update(seconds=seconds,stdout_bytes=2,stdout_sha256=e.digest(b'x\n'),validation=dict(valid=True))
            summary['samples_seconds'].append(seconds)
        else:
            summary.update(failed_attempt=number,full_workload_qualified=False)
            item.update(error='isolated timeout',error_type='TimeoutError')
        summary['attempts'].append(number);stem=f'{number:03d}-{identity}'
        add(plan['output']+'/attempts/'+stem+'.json',e.encoded(item))
        add(plan['output']+'/attempts/'+stem+'.supervisor.json',e.encoded(item))
        add(plan['output']+'/outer-supervisor/'+stem+'.json',b'{}\n')
    for key,summary in summaries.items():
        samples=summary['samples_seconds'];success=summary['full_workload_qualified']
        summary.update(median_seconds=statistics.median(samples) if success else None,
                       sample_stdev_seconds=statistics.stdev(samples) if success else None)
    for key,summary in summaries.items():
        control=summaries[summary['benchmark']+':rebol-full-study:mech-control']
        eligible=summary['full_workload_qualified'] and control['full_workload_qualified']
        summary.update(matched_control_qualified=control['full_workload_qualified'],endpoint_eligible=eligible,
                       time_x_mech=summary['median_seconds']/control['median_seconds'] if eligible else None)
    plan_ref=add(str(e.ROOT/'synthetic/plan.json'),e.encoded(plan))
    review=dict(schema='rebol-independent-full90-reconciliation-v1',status='full90-reconciled-awaiting-runtime-and-publication-review',
        file_integrity_verified=True,common_mutex_held=True,common_mutex_inode=79859134,
        runtime_publication_metadata_qualified=False,chart_admission=False,qualification=copy.deepcopy(admission),
        plan=plan_ref,report=dict(path='/report',sha256='1'*64),terminal=dict(path='/terminal',sha256='2'*64),
        verified_file_pins=pins,profiles=summaries,source_evidence=dict(counts=count_ref),
        actual_full_native_processes=number,qualified_samples=sum(len(row['samples_seconds']) for row in summaries.values()),
        skipped_slots=skipped,failed_profiles=[] if failed is None else [failed],
        full_output_evidence='counts/hashes',resource_evidence='sampled RSS')
    metadata=dict(schema='rebol-publication-runtime-metadata-v1',status='independently-reviewed-runtime-and-publication-metadata',
        independent_review=True,key='rebol3',runtime_publication_metadata_qualified=True,chart_admission=False,
        qualification_manifest=qualification_ref,qualified_runtime=copy.deepcopy(admission['runtime']),extension_image=image,
        runtime_source_equivalence_proven=False,observed_in_each_timed_process=False,actual_loaded_image_inventory_observed=False,
        runtime_gc_configuration_observed=False,gc_numeric_defaults_claimed=False,runtime_evidence_scope=admission['scope']['limitations'],
        execution=['interpreted'],typing='dynamic',runtime='synthetic reviewed runtime',label='synthetic Rebol',family='rebol',
        platform='native',style=['imperative'],memory=['gc'],note='synthetic',sources=['https://example.invalid/'],
        evidence=dict(basis=metadata_evidence))
    def read_raw(path,sha):
        raw=content[path];e.require(e.digest(raw)==sha,'Synthetic pin mismatch');return raw
    r=SimpleNamespace(schedule=lambda plan:(slots,originals))
    return r,plan,review,metadata,read_raw,content


def candidate(failed=None):
    args=fixture(failed);return e.build_candidate(*args[:5]),args


class ExportTests(unittest.TestCase):
    def test_twenty_independently_timed_rows_and_fifteen_physical_sources(self):
        value,_=candidate()
        self.assertEqual((len(value['program_inventory']),len(value['files']),len(value['matched_mech_controls'])),(20,15,10))
        self.assertEqual((value['planned_rebol_samples'],value['planned_matched_mech_samples']),(60,30))
        rows=value['program_inventory'];a=rows['pidigits:rebol-pidigits-compact'];b=rows['pidigits:rebol-pidigits-optimized']
        self.assertEqual(a['files'],b['files']);self.assertNotEqual(a['samples'],b['samples'])
        self.assertIsNone(b['timing_alias_of']);self.assertEqual(b['source_alias_of'],a['id'])
        self.assertTrue(all(row['formatted_loc'] is None for row in rows.values()))

    def test_full_c_and_special_facade_counts_are_in_each_bundle(self):
        value,_=candidate()
        for row in value['program_inventory'].values():
            self.assertEqual(len(row['files']),5 if row['benchmark'] in ('pidigits','regexredux') else 4)
            roles=row['file_roles'];self.assertEqual(row['loc'],sum(x['normalized_loc'] for x in roles.values()))
            self.assertEqual(sum(x['role']=='general-library-helper' for x in roles.values()),1)

    def test_failed_subject_missing_complete_output_remains_null(self):
        value,_=candidate('rebol-regexredux-compact');row=value['program_inventory']['regexredux:rebol-regexredux-compact']
        self.assertIsNone(row['seconds']);self.assertFalse(row['eligible_for_publication_review'])
        sample=row['sample_execution_metadata'][0]
        for field in ('seconds','stdout_bytes','stdout_sha256','validation'):self.assertIsNone(sample[field])
        self.assertEqual(sample['error_type'],'TimeoutError')
        self.assertEqual(value['endpoint_proposals']['regexredux']['fast'],'regexredux:rebol-regexredux-optimized')

    def test_failed_control_excludes_both_subjects_without_erasing_samples(self):
        value,_=candidate('regexredux:rebol-full-study:mech-control')
        self.assertEqual(value['endpoint_proposals']['regexredux']['programs'],[])
        for form in e.FORMS:
            row=value['program_inventory']['regexredux:rebol-regexredux-'+form]
            self.assertEqual(len(row['samples']),3);self.assertIsNotNone(row['seconds'])
            self.assertIsNone(row['time_ratio_to_matched_mech']);self.assertFalse(row['eligible_for_publication_review'])
        sample=value['matched_mech_controls']['regexredux']['sample_execution_metadata'][0]
        self.assertIsNone(sample['stdout_sha256'])

    def test_qualified_sample_requires_complete_output_fields(self):
        r,plan,review,metadata,read_raw,content=fixture();row=review['profiles']['rebol-regexredux-compact']
        path=plan['output']+'/attempts/'+f'{row["attempts"][0]:03d}-rebol-regexredux-compact.supervisor.json'
        item=json.loads(content[path]);del item['stdout_sha256'];content[path]=e.encoded(item)
        review['verified_file_pins'][path]=e.digest(content[path])
        with self.assertRaises(KeyError):e.build_candidate(r,plan,review,metadata,read_raw)

    def test_wrong_sample_owner_and_missing_receipt_reject(self):
        for fault in ('owner','missing'):
            r,plan,review,metadata,read_raw,content=fixture()
            path=plan['output']+'/attempts/001-rebol-regexredux-compact.supervisor.json'
            if fault=='owner':
                item=json.loads(content[path]);item['key']='rebol-regexredux-optimized';content[path]=e.encoded(item)
                review['verified_file_pins'][path]=e.digest(content[path])
            else:del review['verified_file_pins'][path]
            with self.assertRaises((AssertionError,KeyError)):e.build_candidate(r,plan,review,metadata,read_raw)

    def test_runtime_observation_promotion_and_unreviewed_metadata_reject(self):
        for field,value in (('observed_in_each_timed_process',True),('runtime_source_equivalence_proven',True),
                            ('independent_review',False),('runtime_gc_configuration_observed',True)):
            args=list(fixture());args[3][field]=value
            with self.assertRaises(AssertionError):e.build_candidate(*args[:5])

    def test_unbound_helper_and_formatted_count_promotion_reject(self):
        for fault in ('helper','formatted'):
            r,plan,review,metadata,read_raw,_=fixture()
            if fault=='helper':del plan['pins'][plan['qualification']['bases'][0]['physical_inputs'][3]['path']]
            else:plan['qualification']['bases'][0]['formatted_loc']=10
            with self.assertRaises(AssertionError):e.build_candidate(r,plan,review,metadata,read_raw)

    def test_statistics_and_endpoint_gate_cannot_be_changed(self):
        for field,value in (('median_seconds',999),('endpoint_eligible',False),('time_x_mech',999)):
            args=list(fixture());args[2]['profiles']['rebol-regexredux-compact'][field]=value
            with self.assertRaises(AssertionError):e.build_candidate(*args[:5])

    def test_complete_candidate_cleanup_preserves_external_truncation(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp).resolve()/'candidate.json';owned={};e.write_new(path,dict(a=1),owned)
            path.write_bytes(owned['raw'][:4])
            with self.assertRaises(AssertionError):e.remove_owned(path,owned)
            self.assertEqual(path.read_bytes(),owned['raw'][:4])

    def test_owned_record_precedes_writer_return_and_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp).resolve()/'candidate.json';owned={}
            with self.assertRaises(KeyboardInterrupt):
                with e.preserve_failure_cleanup(lambda:e.remove_owned(path,owned)):
                    e.write_new(path,dict(a=1),owned);raise KeyboardInterrupt('post-write')
            self.assertFalse(path.exists());self.assertEqual(owned,{})

    def test_stop_after_exclusive_open_is_deferred_until_owned_cleanup(self):
        for number in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):
            with self.subTest(signal=number),tempfile.TemporaryDirectory() as temp:
                path=Path(temp).resolve()/'candidate.json';owned={};observed=[]
                original_open=Path.open
                def interrupted_open(target,*args,**kwargs):
                    stream=original_open(target,*args,**kwargs)
                    if target==path and args==('xb',):
                        self.assertEqual(owned,{})
                        os.kill(os.getpid(),number)
                    return stream
                def cleanup():
                    observed.append(owned.get('complete'))
                    e.remove_owned(path,owned)
                with e.stop_handlers(),patch.object(Path,'open',interrupted_open):
                    with self.assertRaises(InterruptedError):
                        with e.preserve_failure_cleanup(cleanup):e.write_new(path,dict(a=1),owned)
                self.assertEqual(observed,[True]);self.assertFalse(path.exists());self.assertEqual(owned,{})

    def test_late_output_change_preserved_and_error_not_hidden(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp).resolve()/'candidate.json';owned={};e.write_new(path,dict(a=1),owned)
            with self.assertRaises(BaseExceptionGroup) as captured:
                with e.preserve_failure_cleanup(lambda:e.remove_owned(path,owned)):
                    path.write_bytes(b'external');e.verify_owned(path,owned)
            self.assertEqual(len(captured.exception.exceptions),2);self.assertEqual(path.read_bytes(),b'external')

    def test_actual_save_candidate_closure_runs_before_fake_lease_release(self):
        for fault in ('metadata','candidate'):
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
                if fault=='metadata':self.assertFalse(output.exists())
                else:self.assertEqual(output.read_bytes(),b'external')


if __name__=='__main__':unittest.main()
