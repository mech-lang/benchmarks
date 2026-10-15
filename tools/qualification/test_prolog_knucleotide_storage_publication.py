"""Pure four-cohort publication faults with synthetic timings, never native data."""
import copy
from contextlib import contextmanager
import hashlib
import gzip
import importlib.util
import json
import os
import signal
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent

def load(name):
    spec=importlib.util.spec_from_file_location('test_'+name,HERE/(name+'.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

i=load('import_prolog_knucleotide_storage');e,m,n=i.e,i.m,i.l
catalog=load('test_import_prolog_linear').catalog
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def fixture():
    """Four actual cohort labels; future measurements are in-memory fixtures only."""
    manifests={};profiles={};raw={};pins={str(e.METADATA):e.METADATA_SHA}
    bins=['original-full90','linear-full81','linear-remaining50','knucleotide-remaining36']
    directories=[n.OLD/'results',n.PRIOR/'run-v1',n.PREVIOUS/'run-v1',n.PACKET/'run-v1']
    cohorts={name:{kind:e.ref(str(directory/(kind+'.json')),'a'*64) for kind in ('plan','report','terminal')}
             for name,directory in zip(bins,directories)}
    for name in bins:cohorts[name]['status']='complete' if name==bins[-1] else 'stopped-unqualified'
    cohorts[bins[2]].update(actual_native_processes=15,preserved_qualified_samples=14,excluded_attempts=[15])
    cohorts[bins[-1]].update(actual_native_processes=36,qualified_samples=36)
    for bench in n.r.BENCHES:
        rows=[]
        for variant in ('compact','optimized','control'):
            identity='mech-aot-control' if variant=='control' else 'prolog-'+bench+('-linear' if bench=='revcomp' else '')+'-'+variant
            key=bench+':prolog-full-study:mech-control' if variant=='control' else bench+':'+identity
            code='fixture '+bench+'\n';digest=sha(code.encode());source=str(n.ROOT/'experiments/prolog/full36-knucleotide-v1/synthetic'/bench/'main.pl')
            raw[source]=code.encode();pins[source]=digest
            row=dict(key=key,id=identity,benchmark=bench,variant=variant,language='mech' if variant=='control' else 'prolog',
                source=source,measured_source=source,source_sha256=digest,binary='/synthetic/runtime',binary_sha256='b'*64,
                source_bundle=[dict(path=source,origin=source,sha256=digest,normalized_loc=100,physical_loc=80)],
                canonical_loc=100,physical_loc=80,source_alias_of=identity.removesuffix('-optimized')+'-compact' if variant=='optimized' else None,
                optimization_claim='explicit source alias' if variant=='optimized' else 'baseline',maximum_workers=1,
                command=['/synthetic/runtime',source],cwd=str(Path(source).parent),runtime_environment={},
                compiler_bound_input_inventory=e.ref(str(n.PACKET/'synthetic-counts.json'),'c'*64))
            rows.append(row);profiles[key]=row
        manifests[bench]=dict(profiles=rows)
    observed={k:dict(**{f:v[f] for f in ('key','id','language','benchmark','source','source_sha256','binary_sha256')},
        full_workload_qualified=True,samples_seconds=[],attempts=[],retained_attempts=[],sample_evidence=[],failed_attempt=None,failed_cohort=None)
        for k,v in profiles.items()}
    slot=0;counts=dict.fromkeys(bins,0)
    for bench in n.r.BENCHES:
        rows=manifests[bench]['profiles']
        for round_ in (1,2,3):
            for row in rows[round_-1:]+rows[:round_-1]:
                cohort=bins[0] if slot<9 else bins[1] if slot<40 else bins[2] if slot<54 else bins[3]
                slot+=1;counts[cohort]+=1;number=counts[cohort]
                paths=n.attempt_paths(directories[bins.index(cohort)],dict(attempt=number,id=row['id']))
                seconds=float(round_)+(1 if row['language']=='prolog' else 0)
                value=dict(attempt=number,key=row['key'],id=row['id'],benchmark=bench,round=round_,qualified=True,
                    seconds=seconds,stdout_bytes=1,stdout_sha256='d'*64,validation={'reference_match':True},started_at='2027-01-01T00:00:00+00:00',finished_at='2027-01-01T00:00:01+00:00')
                for path in paths:
                    raw[str(path)]=json.dumps(value).encode();pins[str(path)]=sha(raw[str(path)])
                origin={k:value[k] for k in ('round','qualified','seconds','stdout_bytes','stdout_sha256','validation')}
                origin.update(cohort=cohort,attempt=number,**dict(zip(('raw','supervisor','outer'),map(str,paths))))
                dest=observed[row['key']];dest['sample_evidence'].append(origin);dest['samples_seconds'].append(seconds)
                if cohort==bins[-1]:dest['attempts'].append(number)
                else:dest['retained_attempts'].append(dict(cohort=cohort,attempt=number,report=cohorts[cohort]['report']['path'],report_sha256=cohorts[cohort]['report']['sha256']))
    for row in observed.values():
        row['median_seconds'],row['sample_stdev_seconds']=n.p.three_statistics(row['samples_seconds'])
    for row in observed.values():
        row['time_x_mech']=row['median_seconds']/observed[row['benchmark']+':prolog-full-study:mech-control']['median_seconds'] if row['language']=='prolog' else 1
    plan=dict(output=str(n.PACKET/'run-v1'),manifests=manifests,pins=pins,linear_qualification={},
        qualification=e.ref(str(n.QUALIFICATION),n.QUALIFICATION_SHA),timing_policy={'scope':'full-process'})
    previous=dict(sealed_source_outcome=e.ref(str(n.PACKET/'original-outcome.json'),'e'*64))
    review=dict(schema=n.SCHEMA,status='full36-plus-retained54-reconciled-awaiting-runtime-and-publication-review',
        file_integrity_verified=True,chart_admission=False,runtime_publication_metadata_qualified=False,
        full_timings_qualified=False,profiles=observed,plan=e.ref(str(n.PLAN),n.PLAN_SHA),verified_file_pins=pins,
        prior_producer_statuses={name:'stopped-unqualified' for name in bins[:-1]},cohorts=cohorts,
        reused_qualified_samples=54,original_regex_samples=9,retained_linear_samples=31,retained_remaining_samples=14,
        excluded_remaining50_attempt=15,failed_profiles=[],skipped_slots=[],actual_full_native_processes=90,
        total_native_processes_including_cancelled=92,new_full_native_processes=36,qualified_samples=90,
        cohort_policy='four actual cohorts',report=cohorts[bins[-1]]['report'],terminal=cohorts[bins[-1]]['terminal'])
    runtime=[]
    for key,row in profiles.items():
        if row['language']=='prolog':runtime.append(dict(row,timing=copy.deepcopy(observed[key])))
    metadata=dict(schema=m.SCHEMA,status='qualified-recorded-runtime-metadata',file_integrity_verified=True,
        runtime_publication_metadata_qualified=True,chart_admission=False,source_forms_reviewed=20,plan=review['plan'],
        linear_qualification={},knucleotide_qualification=plan['qualification'],profiles=runtime,verified_file_pins=pins,
        cohorts=cohorts,memory_policy='default GC',limitations=['Synthetic test fixture'])
    return dict(plan=plan,stopped={},prior={},previous=previous,review=review,metadata=metadata,
                read_raw=lambda path,digest:raw[path]),profiles,raw


class Publication(unittest.TestCase):
    def candidate(self):
        values,profiles,raw=fixture()
        with patch.object(n,'schedule',return_value=([],profiles,{})):
            candidate=e.build_candidate(**values)
        return candidate,values,profiles,raw
    def test_four_cohorts_and_cancelled_evidence(self):
        candidate,values,_,_=self.candidate();i.validate_candidate(candidate)
        self.assertEqual(candidate['actual_full_native_processes'],90)
        self.assertEqual(candidate['total_native_processes_including_cancelled'],92)
        self.assertEqual(candidate['cohorts']['linear-remaining50']['actual_native_processes'],15)
        self.assertEqual(candidate['cohorts']['linear-remaining50']['excluded_attempts'],[15])
        self.assertEqual(candidate['program_inventory']['knucleotide:prolog-knucleotide-compact']['attempt_cohorts'],['knucleotide-remaining36'])
    def test_preserved_and_current_cohort_cannot_be_swapped(self):
        values,profiles,_=fixture();sample=next(v for v in values['review']['profiles'].values() if v['attempts'])['sample_evidence'][0]
        sample['cohort']='linear-remaining50'
        with patch.object(n,'schedule',return_value=([],profiles,{})),self.assertRaises(ValueError):e.build_candidate(**values)
    def test_cancelled_attempt_cannot_be_admitted(self):
        candidate,_,_,_=self.candidate()
        row=next(v for v in candidate['program_inventory'].values() if 'linear-remaining50' in v['attempt_cohorts'])
        next(s for s in row['sample_execution_metadata'] if s['attempt_cohort']=='linear-remaining50')['attempt']=15
        with self.assertRaises(ValueError):i.validate_candidate(candidate)
    def test_stopped_cohort_cannot_be_completed(self):
        candidate,_,_,_=self.candidate();candidate['cohorts']['linear-remaining50']['status']='complete'
        with self.assertRaises(ValueError):i.validate_candidate(candidate)
    def test_changed_supervisor_is_rejected(self):
        values,profiles,raw=fixture();sample=next(v for v in values['review']['profiles'].values() if v['attempts'])['sample_evidence'][0]
        raw[sample['supervisor']]+=b'\n'
        with patch.object(n,'schedule',return_value=([],profiles,{})),self.assertRaises(ValueError):e.build_candidate(**values)
    def test_existing_catalog_unchanged_and_all_sources_retained(self):
        candidate,values,_,_=self.candidate();originals=catalog();before=json.loads(originals[i.TARGETS[0]])
        refs={key:dict(path='experiments/prolog/full36-knucleotide-v1/'+key+'.json',sha256='a'*64)
              for key in ('candidate','metadata','reconciliation','release','import_controller')}
        result,audit=i.build_publication(originals,candidate,json.loads(i.RELEASE.read_bytes()),refs,values['plan'])
        after=json.loads(result[i.TARGETS[0]])
        for pool in ('programs','program_inventory','files','archive_paths'):
            self.assertEqual({k:after[pool][k] for k in before[pool]},before[pool])
        self.assertEqual(audit['reused_qualified_samples'],54);self.assertEqual(audit['admitted_workloads'],list(n.r.BENCHES))
        self.assertEqual(after['formatted_reference_summary'],before['formatted_reference_summary'])
        for old,new in zip(before['benchmarks'],after['benchmarks']):self.assertEqual(old,dict(new,groups=new['groups'][:-1]))
    def failed_candidate(self,key):
        values,profiles,raw=fixture();review=values['review'];row=review['profiles'][key]
        sample=row['sample_evidence'][-1];self.assertEqual(sample['cohort'],'knucleotide-remaining36')
        sample['qualified']=False;sample['validation']={'reference_match':False}
        saved=json.loads(raw[sample['supervisor']]);saved.update(qualified=False,validation=sample['validation'])
        raw[sample['supervisor']]=json.dumps(saved).encode()
        review['verified_file_pins'][sample['supervisor']]=sha(raw[sample['supervisor']])
        row.update(samples_seconds=row['samples_seconds'][:-1],median_seconds=None,sample_stdev_seconds=None,
                   time_x_mech=None,full_workload_qualified=False,failed_attempt=sample['attempt'],failed_cohort=sample['cohort'])
        review['failed_profiles']=[key];review['qualified_samples']=89
        if row['language']=='mech':
            for other in review['profiles'].values():
                if other['benchmark']==row['benchmark']:other['time_x_mech']=None
        values['metadata']['profiles']=[dict(v,timing=copy.deepcopy(review['profiles'][v['key']]))
            for v in values['metadata']['profiles'] if v['key']!=key]
        with patch.object(n,'schedule',return_value=([],profiles,{})):candidate=e.build_candidate(**values)
        i.validate_candidate(candidate);return candidate
    def test_failed_corrected_subject_preserves_partial_samples(self):
        key='knucleotide:prolog-knucleotide-compact';candidate=self.failed_candidate(key);row=candidate['program_inventory'][key]
        self.assertFalse(row['eligible_for_publication_review']);self.assertIsNone(row['seconds']);self.assertEqual(len(row['samples']),2)
        self.assertEqual(len(row['sample_execution_metadata']),3);self.assertEqual(row['failed_cohort'],'knucleotide-remaining36')
    def test_failed_new_control_excludes_both_source_aliases(self):
        candidate=self.failed_candidate('binarytrees:prolog-full-study:mech-control')
        self.assertEqual(candidate['endpoint_proposals']['binarytrees']['programs'],[])
        for row in candidate['program_inventory'].values():
            if row['benchmark']=='binarytrees':
                self.assertTrue(row['full_workload_qualified']);self.assertFalse(row['eligible_for_publication_review'])
                self.assertIsNone(row['time_ratio_to_matched_mech'])
    def test_metadata_routes_sixteen_original_two_linear_two_corrected(self):
        values,profiles,_=fixture();plan=values['plan'];review=values['review']
        pins={str(m.RECONCILER):m.RECONCILER_SHA,str(n.HELPER):n.HELPER_SHA,str(n.r.HELPER):n.r.HELPER_SHA}
        plan['pins'].update(pins);review['verified_file_pins'].update(pins)
        outcome=dict(status='qualified-original-Prolog20-work-and-LOC-awaiting-full90',source_work_qualified=True,
                     canonical_LOC_admitted=True,chart_admission=False,profiles=20)
        context=({'environment':{},'binary':'/synthetic/runtime','binary_sha256':'b'*64,'pcre_version':'10.40'},
                 {'runtime':{}},{'image_pins':{}},set())
        reply=({},[],{'foreign_libraries':[],'runtime':{}})
        with patch.object(n,'schedule',return_value=([],profiles,{})),patch.object(m,'runtime_context',return_value=context),\
             patch.object(m,'original_profile',return_value=reply) as original,patch.object(m,'linear_profile',return_value=reply) as linear,\
             patch.object(m,'knucleotide_profile',return_value=reply) as corrected:
            result=m.inspect(plan,{}, {},values['previous'],review,outcome,lambda *_:None,lambda *_:None)
        self.assertEqual((original.call_count,linear.call_count,corrected.call_count),(16,2,2))
        self.assertEqual(result['source_forms_reviewed'],20);self.assertEqual(result['knucleotide_qualification'],plan['qualification'])
    def test_export_owned_result_is_rechecked_after_context_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory).resolve()/'candidate.json';args=SimpleNamespace(reconciliation=Path('/r'),reconciliation_sha256='a'*64,
                                                                       metadata=Path('/m'),metadata_sha256='b'*64)
            @contextmanager
            def context(*args,**kwargs):
                try:
                    yield {'verified_file_pins':{}}
                    target.write_bytes(b'{')
                    kwargs['final_consumer_check']()
                except BaseException:
                    kwargs['on_exit_failure']();raise
            with patch.object(m,'review_context',context),patch.object(e,'same'),patch.object(e,'checked',return_value=b'{}'),\
                 patch.object(e,'reproduced_candidate',return_value={'status':'fixture'}):
                with self.assertRaises(BaseException):e.save_candidate(args,target)
            self.assertEqual(target.read_bytes(),b'{','Externally altered completed output must survive cleanup')
    def test_owned_complete_output_edit_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory).resolve()/'result.json';owner=m.OwnedResult(path);owner.write({'passed':True});path.write_bytes(b'{')
            with self.assertRaises(ValueError):owner.verify()
            with self.assertRaises(ValueError):owner.remove()
            self.assertEqual(path.read_bytes(),b'{')
    def test_owned_result_late_check_removes_only_original(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory).resolve()/'result.json';args=SimpleNamespace(reconciliation=Path('/fake'),reconciliation_sha256='a'*64)
            @contextmanager
            def review(*args,**kwargs):
                try:yield {'status':'fixture'}
                finally:
                    kwargs['final_consumer_check']();kwargs['on_exit_failure']();raise ValueError('late prerequisite change')
            with patch.object(m,'review_context',review),self.assertRaisesRegex(ValueError,'late prerequisite'):
                m.save_metadata(args,path)
            self.assertFalse(path.exists())
    def test_post_rename_interrupt_restores_all_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();originals={name:('old '+name).encode() for name in i.TARGETS};prepared={name:('new '+name).encode() for name in i.TARGETS}
            for name,raw in originals.items():(root/name).parent.mkdir(parents=True,exist_ok=True);(root/name).write_bytes(raw)
            real=i.replace_bytes;calls=[];journal=[]
            def interrupted(path,raw,suffix):
                real(path,raw,suffix)
                if suffix.endswith('import.tmp'):
                    calls.append(path)
                    if len(calls)==2:raise KeyboardInterrupt('after rename')
            with patch.object(i,'replace_bytes',interrupted),self.assertRaises(KeyboardInterrupt):
                i.apply_prepared(root,prepared,originals,{k:sha(v) for k,v in originals.items()},lambda:None,journal)
            self.assertEqual(journal,[])
            self.assertEqual({name:(root/name).read_bytes() for name in originals},originals)
    def test_fifo_replacement_never_opens_and_other_targets_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();originals={name:b'old' for name in i.TARGETS};prepared={name:b'new' for name in i.TARGETS}
            for name in i.TARGETS:(root/name).parent.mkdir(parents=True,exist_ok=True);(root/name).write_bytes(b'new')
            victim=root/i.TARGETS[-1];victim.unlink();os.mkfifo(victim)
            with patch.object(m.os,'open',side_effect=AssertionError('FIFO must not be opened')):
                with self.assertRaises(ValueError):m.read_regular(victim)
            journal=list(i.TARGETS)
            with self.assertRaises(BaseExceptionGroup):i.restore_prepared(root,prepared,originals,journal)
            self.assertEqual(journal,[i.TARGETS[-1]])
            for name in i.TARGETS[:-1]:self.assertEqual((root/name).read_bytes(),b'old')
            self.assertTrue(victim.exists());victim.unlink()
    def test_owned_output_fifo_conflict_preserves_other_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()/'owned';owned=i.OwnedOutput(root,i.atomic_publication)
            owned.write('first.json',b'first');owned.write('second.json',b'second')
            victim=root/'second.json';victim.unlink();os.mkfifo(victim)
            with self.assertRaises(BaseExceptionGroup):owned.restore()
            self.assertFalse((root/'first.json').exists());self.assertTrue(victim.exists());victim.unlink()
    def test_cli_stop_signals_raise_through_cleanup(self):
        signals=(signal.SIGINT,signal.SIGTERM,signal.SIGHUP)
        original={sig:signal.getsignal(sig) for sig in signals}
        try:
            m.install_stop_handlers()
            for sig in signals:
                with self.assertRaises(KeyboardInterrupt):signal.getsignal(sig)(sig,None)
        finally:
            for sig,handler in original.items():signal.signal(sig,handler)
    def test_actual_corrected_compiler_binding(self):
        qualification=json.loads(n.QUALIFICATION.read_bytes());plan=dict(knucleotide_qualification=qualification,
            qualification=e.ref(str(n.QUALIFICATION),n.QUALIFICATION_SHA),pins=qualification['pins'])
        config=json.loads(Path(m.f.CONFIG).read_bytes());images=json.loads(Path(m.f.IMAGES).read_bytes())
        def read(path,digest=None):
            raw=Path(path).read_bytes();self.assertEqual(sha(raw),digest or plan['pins'][path]);return json.loads(raw)
        for row in qualification['profiles']:
            qlf,_,loaded=m.knucleotide_profile(plan,row,config,images,read,lambda path,digest=None:Path(path).read_bytes())
            self.assertEqual(len(qlf),3);self.assertEqual(loaded['target'],row['compiled_artifact']['path'])
            altered=copy.deepcopy(row);altered['compiled_artifact']['sha256']='f'*64
            with self.assertRaises(ValueError):m.knucleotide_profile(plan,altered,config,images,read,lambda *_:None)



class DeclaredStorage(unittest.TestCase):
    def item(self,root):
        decoded=b'{"retained": true}\n';stored=gzip.compress(decoded,mtime=0)
        item=dict(logical_path='evidence/raw.json',stored_path='evidence/raw.json.gz',storage_encoding='gzip',
                  original_sha256=sha(decoded),stored_sha256=sha(stored),original_bytes=len(decoded),stored_bytes=len(stored))
        return item,decoded,stored
    def test_public_ref_uses_storage_and_retains_logical_identity(self):
        item,_,_=self.item(i.ROOT)
        with patch.object(i,'storage_entries',return_value={item['logical_path']:item}):
            ref=i.public_ref(dict(path=str(i.ROOT/item['logical_path']),sha256=item['original_sha256']))
            self.assertEqual(ref['path'],item['stored_path']);self.assertEqual(ref['sha256'],item['stored_sha256'])
            self.assertEqual(ref['logical_path'],item['logical_path']);self.assertEqual(ref['original_sha256'],item['original_sha256'])
            self.assertEqual(ref['storage_manifest'],dict(path=i.STORAGE_REL,sha256=i.STORAGE_SHA))
            with self.assertRaisesRegex(ValueError,'Logical evidence identity'):
                i.public_ref(dict(path=str(i.ROOT/item['logical_path']),sha256='a'*64))
    def test_recursive_refs_leave_original_unchanged(self):
        item,_,_=self.item(i.ROOT);value={'rows':[dict(path=str(i.ROOT/item['logical_path']),sha256=item['original_sha256'])]}
        before=copy.deepcopy(value)
        with patch.object(i,'storage_entries',return_value={item['logical_path']:item}):result=i.public_refs(value)
        self.assertEqual(value,before);self.assertEqual(result['rows'][0]['path'],item['stored_path'])
    def test_link_collection_uses_stored_artifact_and_manifest(self):
        item,_,_=self.item(i.ROOT)
        candidate=dict(files={},evidence=dict(path=str(i.ROOT/item['logical_path']),sha256=item['original_sha256']))
        with patch.object(i,'storage_entries',return_value={item['logical_path']:item}):result=i.publication_links(candidate,{},i.ROOT)
        self.assertNotIn(item['logical_path'],result);self.assertEqual(result[item['stored_path']],item['stored_sha256'])
        self.assertEqual(result[i.STORAGE_REL],i.STORAGE_SHA)
        self.assertEqual(result[i.ORIGINAL_IMPORTER.relative_to(i.ROOT).as_posix()],i.ORIGINAL_IMPORTER_SHA)
    def test_copy_requires_stored_and_decoded_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();evidence=root/'e';publication=root/'p';item,decoded,stored=self.item(root)
            for target in (evidence,publication):
                path=target/item['stored_path'];path.parent.mkdir(parents=True);path.write_bytes(stored)
            links={item['stored_path']:item['stored_sha256']}
            with patch.object(i,'storage_entries',return_value={item['logical_path']:item}):
                i.verify_public_links(links,evidence,publication)
                wrong=dict(item,original_sha256='a'*64)
                with patch.object(i,'storage_entries',return_value={wrong['logical_path']:wrong}),self.assertRaisesRegex(ValueError,'Decoded evidence identity'):
                    i.verify_public_links(links,evidence,publication)
                (publication/item['stored_path']).write_bytes(stored+b'x')
                with self.assertRaisesRegex(ValueError,'Pinned publication bytes'):
                    i.verify_public_links(links,evidence,publication)
    def test_unsafe_manifest_path_and_duplicate_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();item,_,_=self.item(root)
            path=root/i.STORAGE_REL;path.parent.mkdir(parents=True)
            for artifacts,match in (([dict(item,stored_path='../escape')],'Unsafe'),([item,item],'Duplicate')):
                raw=json.dumps(dict(schema='declared-exact-gzip-storage-v1',historical_receipts_unchanged=True,original_content_unchanged=True,artifacts=artifacts)).encode();path.write_bytes(raw)
                with patch.object(i,'ROOT',root),patch.object(i,'STORAGE_SHA',sha(raw)),self.assertRaisesRegex(ValueError,match):i.storage_entries()

if __name__=='__main__':unittest.main()
