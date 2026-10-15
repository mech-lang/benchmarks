"""Focused final intake checks; no qualification context or native process."""
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


a=load(HERE/'rebol_qualification_final.py','final_qualification_test_target')
def document(ref):return json.loads(Path(ref['path']).read_bytes())


class Evidence:
    def physical(self,path):
        path=Path(path);assert path.resolve()==path
        return path
    def read_bytes(self,path):return Path(path).read_bytes()
    def pin(self,pins,resolutions,path,sha):
        path=Path(path);assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
        assert str(path) not in pins or pins[str(path)]==sha
        pins[str(path)]=sha;resolutions[str(path)]=str(path)
        return path
    def document(self,ref,pins,resolutions):
        self.pin(pins,resolutions,ref['path'],ref['sha256'])
        return document(ref)


class FinalQualificationTests(unittest.TestCase):
    def setUp(self):
        self.q=load(a.ORIGINAL,'final_qualification_original_test')
        self.original_context=self.q.review_context
        self.m=load(a.WORK,'final_qualification_work_test')
        self.own=a.reference(Path(a.__file__),a.digest(Path(a.__file__).read_bytes()))
        a.attach(self.q,self.m,self.own)

    def fixtures(self):
        review=document(a.OBSERVATIONS);closure=document(a.CLOSURE);prior=closure['prior_work_stage']
        return review,closure,prior,review['references']

    def test_actual_combined_review_and_single_map_shape(self):
        review,closure,prior,refs=self.fixtures()
        w=types.SimpleNamespace(GATES=self.m.GATES)
        a.check_observations(w,review,closure,prior,refs)
        for mutate in (
            lambda x:x.update(accepted_observations=4),
            lambda x:x.update(backing_series_capacity_observed=True),
            lambda x:x['observations'].reverse(),
            lambda x:x['preserved_failed_capture'].update(sidecar_present=True),
            lambda x:x['durable']['lease'].update(inode=0)):
            bad=copy.deepcopy(review);mutate(bad)
            with self.assertRaises(AssertionError):a.check_observations(w,bad,closure,prior,refs)
        bad=copy.deepcopy(closure);bad['successful_captures']=[]
        with self.assertRaises(AssertionError):a.check_observations(w,review,bad,prior,refs)

    def manifest(self):
        bounded=document(a.BOUNDED);work=document(a.OBSERVATIONS)
        refs=dict(source_review=a.reference(a.PACKET/'source-review-v1.json','1'*64),
            primitive_review=work['references']['primitive_review'],bounded_source_review=work['references']['bounded_source_review'],
            work_source_review=a.WORK_SOURCE,count_review=a.COUNTS,work_review=a.reference(a.PACKET/'work-review-v1.json','2'*64),
            bounded_review=a.BOUNDED,observation_review=a.OBSERVATIONS,timing_policy=a.POLICY)
        stages={kind:dict({k:item['references'][k] for k in ('plan','report','terminal')},durable=a.durable_ref(item['durable']))
                for kind,item in (('bounded',bounded),('work',work))}
        return dict(schema='rebol-exact-bounded-source-qualification-v1',status='independently-qualified-exact-inputs-for-full-timing',
            independent_review=True,scope=dict.fromkeys(self.q.TRUE_SCOPE,True)|dict.fromkeys(self.q.FALSE_SCOPE,False),
            references=refs,stages=stages)

    def test_manifest_rejects_old_approvals_and_extra_admission(self):
        value=self.manifest();self.q.manifest_contract(value)
        for key in ('count_review','work_source_review','bounded_review','observation_review','timing_policy'):
            bad=copy.deepcopy(value);bad['references'][key]['sha256']='0'*64
            with self.assertRaises(AssertionError):self.q.manifest_contract(bad)
        bad=copy.deepcopy(value);bad['scope']['full_timing_qualified']=True
        with self.assertRaises(AssertionError):self.q.manifest_contract(bad)
        bad=copy.deepcopy(value);bad['references']['extra']=a.COUNTS
        with self.assertRaises(AssertionError):self.q.manifest_contract(bad)

    def count_inputs(self):
        review=document(a.COUNTS);sources={i:v for i,v in review['sources'].items() if i in review['bundles']}
        extension=dict(corrected_source={k:review['sources']['extension'][k] for k in ('path','sha256')},
            unchanged_facades={review['sources'][i]['path']:review['sources'][i]['sha256'] for i in ('io','loader','big','regex')})
        source=dict(dependencies={str(p.relative_to(a.ROOT)):a.digest(p.read_bytes()) for p in (self.q.COUNTER,self.q.LEDGER)})
        return source,sources,extension

    def test_fifteen_real_counts_bind_both_corrected_mains(self):
        source,sources,extension=self.count_inputs();before=self.q.LEDGER.read_bytes();loader=self.q.pinned_module
        bundles,identities,review=self.q.counts(Evidence(),a.COUNTS,source,{}, {},sources,extension)
        self.assertEqual((len(identities),len(bundles)),(15,10))
        self.assertEqual(identities['binarytrees']['sha256'],'128df2a9e4c9d5d5be798b07d8ff0ab967c5969ee38746de9c7ee635502574ef')
        self.assertEqual(identities['regexredux']['sha256'],'e031f15f60e0b53cd565a87a2993efec9fcecc9ea5dcde35f1a6f13576c7f650')
        self.assertEqual(self.q.LEDGER.read_bytes(),before);self.assertIs(self.q.pinned_module,loader)
        self.assertTrue(all(x['formatted_loc'] is None for x in bundles.values()))

    def test_count_failure_restores_original_loader(self):
        source,sources,extension=self.count_inputs();source['dependencies'][str(self.q.LEDGER.relative_to(a.ROOT))]='0'*64
        loader=self.q.pinned_module
        with self.assertRaises(AssertionError):self.q.counts(Evidence(),a.COUNTS,source,{}, {},sources,extension)
        self.assertIs(self.q.pinned_module,loader)
        with self.assertRaises(AssertionError):self.q.counts(Evidence(),dict(a.COUNTS,sha256='0'*64),source,{}, {},sources,extension)

    def test_one_compact_base_per_actual_source(self):
        bounded=document(a.BOUNDED);sources=bounded['sources'];profiles=json.loads(self.q.PROFILES.read_bytes())
        counts=document(a.COUNTS)
        bundles={i:dict(physical_inputs=[],canonical_loc=v['canonical_loc'],physical_loc=v['physical_loc'],formatted_loc=None)
                 for i,v in counts['bundles'].items()}
        e=types.SimpleNamespace(RUNTIME='/runtime/rebol',environment=lambda out:dict(PATH='/bin',HOME='home',REBOL_HOME='home',TMPDIR='tmp'))
        r=types.SimpleNamespace(BENCHES=list(bundles));before=copy.deepcopy(profiles)
        bases=self.q.make_bases(e,r,profiles,sources,bundles,bounded['extension_image'],{})
        self.assertEqual(len(bases),10);self.assertEqual(profiles,before)
        for row in bases:
            self.assertEqual(row['alias_policy'],dict(authored_source_forms=1,publication_forms=['compact'],distinct_optimization_claim=False,copied_timing_allowed=False))
            self.assertEqual(row['main'],{k:sources[row['benchmark']][k] for k in ('path','sha256')})
            self.assertEqual(row['command_prefix'],['/runtime/rebol','-q','-s',row['main']['path']])

    def work_approval(self):
        manifest=self.manifest();identities=document(a.COUNTS)['sources'];sources=document(a.BOUNDED)['sources']
        runtime=a.reference(a.ROOT/'runtime','3'*64);image=document(a.BOUNDED)['extension_image']
        review=dict(schema='rebol-final-independent-source-work-review-v1',status='qualified-exact-sources-and-bounded-evidence',
            independent_review=True,bounded_output_qualified=True,required_work_qualified=True,
            **dict.fromkeys(self.q.FALSE_SCOPE,False),references=dict(bounded_review=a.BOUNDED,observation_review=a.OBSERVATIONS,count_review=a.COUNTS,timing_policy=a.POLICY),
            runtime=runtime,extension_image=image,sources={i:{k:v[k] for k in ('path','sha256')} for i,v in identities.items()},
            limitations=copy.deepcopy(self.q.LIMITATIONS),source_work={i:dict(main={k:v[k] for k in ('path','sha256')},
                required_work_qualified=True,scope='exact-source-and-bounded-evidence',evidence=[a.BOUNDED]) for i,v in sources.items()},
            map_growth_source_review=a.BOUNDED)
        return manifest,identities,sources,runtime,image,review

    def test_ten_source_dispositions_and_unobserved_limits(self):
        manifest,identities,sources,runtime,image,review=self.work_approval()
        e=types.SimpleNamespace(document=lambda *args:review,pin=lambda *args:None)
        call=lambda:a.source_work(self.q,e,manifest,{}, {},sources,identities,runtime,image)
        call()
        del review['source_work']['nbody']
        with self.assertRaises(AssertionError):call()
        review.update(self.work_approval()[-1]);review['limitations']['maps']['final_backing_capacity_observed']=True
        with self.assertRaises(AssertionError):call()
        review.update(self.work_approval()[-1]);review['source_work']['binarytrees']['main']=sources['regexredux']
        with self.assertRaises(AssertionError):call()

    def test_map_lease_keeps_inherited_stream_open_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            job=Path(tmp);path=job/'owner.lock';path.touch();st=path.stat();outer=open(job/'outer','w+b')
            inherited=[(job/'outer',outer,(1,2))];seen=[]
            @contextmanager
            def regular(p):
                with open(p,'rb') as stream:yield stream
            def check(leases):
                self.assertTrue(all(not stream.closed for _,stream,_ in leases));seen.append(len(leases))
            e=types.SimpleNamespace(regular=regular,check_leases=check)
            try:
                with patch.object(a,'JOB',job):
                    with self.assertRaisesRegex(RuntimeError,'body'):
                        with a.map_lease(e,inherited,dict(directory=str(job),lease=dict(path=str(path),device=st.st_dev,inode=st.st_ino))) as combined:
                            self.assertEqual(len(combined),2);self.assertEqual(len(inherited),1);raise RuntimeError('body')
                self.assertFalse(outer.closed);self.assertEqual(seen,[2,2])
            finally:outer.close()

    def test_current_map_ledger_artifacts_and_durable_command(self):
        review,closure,prior,refs=self.fixtures();item=closure['successful_captures'][0];capture=item['capture']
        output=a.WORK_PACKET/'run-v1';slot=dict(id=item['id'],directory=Path(item['capture_directory']).name)
        original=str(a.ROOT/'tools/qualification/rebol_work_observations.py');pins={original:'a'*64};resolutions={original:original}
        gates=dict.fromkeys(self.m.GATES,False);complete=closure['artifacts']
        artifacts={k:v for k,v in complete.items() if k not in ('report.json','terminal.json')}
        plan=dict(schema='rebol-single-map-work-plan-v1',repository=str(a.ROOT),controller=original,controller_sha256='a'*64,
            map_intake_adapter=a.reference(a.WORK,a.WORK_SHA),entrypoint=str(a.WORK),output=str(output),automatic_retry=False,
            benchmark_samples=0,native_processes=1,preserved_observations=2,preserved_native_processes=3,preserved_failed_observations=1,
            prior_work_stage=prior,pins=dict(pins),input_resolutions=dict(resolutions),schedule=[slot],common_mutex_inode=79859134,**gates)
        report=dict(schema='rebol-single-map-work-results-v1',status=self.m.SUCCESS,plan=a.STAGE['plan']['path'],
            plan_sha256=a.STAGE['plan']['sha256'],pins=dict(pins,**{a.STAGE['plan']['path']:a.STAGE['plan']['sha256']}),
            input_resolutions=dict(resolutions,**{a.STAGE['plan']['path']:a.STAGE['plan']['path']}),active=None,attempts=[slot['id']],
            registered=[dict(id=slot['id'],pid=capture['pid'])],captures=[capture],prior_work_stage=prior,preserved_observations=2,
            integrity_errors=[],artifact_errors=[],benchmark_samples=0,artifacts=artifacts,validated_files=artifacts,**gates)
        terminal=dict(schema='rebol-single-map-work-terminal-v1',status=self.m.SUCCESS,preserved_observations=2,
            integrity_errors=[],artifact_errors=[],report_sha256=a.STAGE['report']['sha256'],expected_report_sha256=a.STAGE['report']['sha256'],
            native_processes_started=1,validated_observations=1,common_mutex_held=True,common_mutex_inode=79859134,benchmark_samples=0,
            available_evidence={k:v for k,v in complete.items() if k!='terminal.json'},**gates)
        docs={a.STAGE['plan']['path']:plan,a.STAGE['report']['path']:report,a.STAGE['terminal']['path']:terminal}
        durable=review['durable'];job=Path(durable['directory'])
        actual={name:json.loads((job/name).read_bytes()) for name in ('launch.json','command-started.json','terminal.json')}
        def inventory(path,excluded=()):
            value=durable['artifacts'] if Path(path)==job else complete
            return {k:v for k,v in value.items() if k not in excluded},None
        e=types.SimpleNamespace(PYTHON=actual['launch.json']['command'][0],physical=lambda p:p,document=lambda ref,*_:docs[ref['path']],
            inventory=inventory,pin=lambda *args:None,read_bytes=lambda p:json.dumps(actual[Path(p).name]).encode())
        def checked(*args):
            self.assertEqual(args[-1],actual['command-started.json']['command_pid']);return capture,item['capture_files']
        w=types.SimpleNamespace(__file__=original,GATES=self.m.GATES,SUCCESS=self.m.SUCCESS,checked_case=checked)
        call=lambda:a.closed_map(self.q,w,None,e,None,None,types.SimpleNamespace(kb=None),review,closure,prior,{},pins,resolutions)
        self.assertEqual(call()[1],dict(directory=str(output),artifacts=complete))
        actual['launch.json']['command'][4]=str(a.ORIGINAL)
        with self.assertRaises(AssertionError):call()
        actual['launch.json']['command']=list(actual['command-started.json']['command'])
        terminal['preserved_observations']=3
        with self.assertRaises(AssertionError):call()

    def test_exact_loader_preserves_original_exit_policy(self):
        q=a.load_controller(self.own['sha256'])
        self.assertEqual(q.__file__,str(a.ORIGINAL));self.assertEqual(q.ROOT,a.ROOT)
        self.assertEqual(q.review_context.__code__.co_code,self.original_context.__code__.co_code)
        self.assertEqual(q.LIMITATIONS['maps']['final_backing_capacity_observed'],False)
        self.assertEqual(q.LIMITATIONS['maps']['backing_series_identity_observed'],False)
        self.assertEqual(q.intake_adapter,self.own)
        with self.assertRaises(AssertionError):a.load_controller('0'*64)


if __name__=='__main__':unittest.main()
