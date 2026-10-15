"""Focused final bounded-intake checks; no runtime closure or native execution."""
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


HERE=Path(__file__).resolve().parent
a=load('final_work_tests',HERE/'rebol_work_final.py')
OWN=a.digest(Path(a.__file__).read_bytes())
BASE_REVIEW=json.loads(a.read_small(a.BASE_REVIEW['path']))


class FinalWorkTests(unittest.TestCase):
    def controller(self):return a.load_controller(OWN)

    def source_approval(self,w):
        files=dict(BASE_REVIEW['files'])
        files.update({str(p.relative_to(a.ROOT)):'a'*64 for p in (
            Path(a.__file__),HERE/'test_rebol_work_final.py',a.PACKET/'README.md')})
        files[str(Path(a.__file__).relative_to(a.ROOT))]=OWN
        files[str(Path(a.TREE['path']).relative_to(a.ROOT))]=a.TREE['sha256']
        return dict(schema='rebol-three-work-observations-final-source-review-v1',
            status='independent-source-review-complete-native-observations-pending',independent_review=True,
            files=files,dependencies=dict(BASE_REVIEW['dependencies'],**{
                str(a.FINAL.relative_to(a.ROOT)):a.FINAL_SHA,
                'tools/qualification/rebol_outputs_quoted.py':'68a0e0d9d5f1fd1a99253f495574568e98c6eabc1d084f633f7a6c225dcbddab'}),
            base_source_review=a.BASE_REVIEW,bounded_review=a.BOUNDED_REVIEW,tree_source_review=a.TREE_REVIEW,
            **{k:False for k in w.GATES})

    def test_native_observer_consumers_and_finalizer_are_frozen(self):
        w=self.controller();original=load('final_work_original',HERE/'rebol_work_observations.py')
        self.assertEqual(w.__file__,original.__file__)
        self.assertEqual(w.PACKET,original.PACKET)
        self.assertEqual(w.FILES,original.FILES)
        for name in ('run','finish','native_capture','checked_case','main'):
            self.assertEqual(getattr(w,name).__code__.co_code,getattr(original,name).__code__.co_code)
            self.assertEqual(getattr(w,name).__code__.co_filename,original.__file__)

    def test_loader_preserves_final8_identity_and_exact_source_hashes(self):
        w=self.controller();r=w.load(a.read_small(w.HELPER),w.HELPER,'bounded')
        self.assertEqual(r.__file__,str(w.HELPER))
        self.assertEqual(r.final_adapter,dict(path=str(a.FINAL),sha256=a.FINAL_SHA))
        self.assertEqual(r.SUCCESS,'final8-output-contracts-retained-awaiting-independent-review')
        self.assertEqual(w.load(b'answer=42\n',a.PACKET/'consumer.py','other').answer,42)
        with self.assertRaisesRegex(AssertionError,'Final work intake adapter changed'):a.load_controller('0'*64)
        with patch.object(a,'FINAL_SHA','0'*64),self.assertRaisesRegex(AssertionError,'Final8 intake adapter changed'):
            self.controller()
        with self.assertRaisesRegex(AssertionError,'Original bounded helper changed'):
            w.load(b'changed',w.HELPER,'bad')

    def test_source_union_retains_old_bytes_and_rejects_gate_or_adapter_changes(self):
        w=self.controller();review=self.source_approval(w);w.source_review(review)
        for mutation in ('old-file','missing-tree','dependency','approval','gate','own'):
            value=copy.deepcopy(review)
            if mutation=='old-file':value['files']['tools/qualification/rebol_work_remaining.py']='0'*64
            elif mutation=='missing-tree':del value['files'][str(Path(a.TREE['path']).relative_to(a.ROOT))]
            elif mutation=='dependency':value['dependencies'][str(a.FINAL.relative_to(a.ROOT))]='0'*64
            elif mutation=='approval':value['bounded_review']['sha256']='0'*64
            elif mutation=='gate':value['source_work_qualified']=True
            else:value['files'][str(Path(a.__file__).relative_to(a.ROOT))]='0'*64
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):w.source_review(value)

    def test_schedule_changes_only_corrected_tree_path(self):
        w=self.controller();original=load('final_work_schedule_original',HERE/'rebol_work_observations.py')
        e=SimpleNamespace(RUNTIME=Path('/exact/rebol'),environment=lambda output:{'HOME':str(output/'home')})
        cases=[dict(benchmark=b,case=c,stdin=dict(bytes=n,sha256='a'*64))
               for (b,c),n in zip(w.CASES,(0,0,10299))]
        args=e,cases,dict(path='/exact/image.rebx'),a.PACKET/'run-v1'
        expected=original.schedule(*args);expected[0]['command'][3]=a.TREE['path']
        self.assertEqual(w.schedule(*args),expected)
        self.assertEqual([x['timeout_seconds'] for x in expected],[180]*3)
        self.assertEqual([x['native_file_limit_bytes'] for x in expected],[1024**2,1024**2,16*1024**2])

    def test_actual_small_approval_joins_and_false_work_gates(self):
        w=self.controller()
        approval=json.loads(a.read_small(a.BOUNDED_REVIEW['path']))
        closure=json.loads(a.read_small(a.CLOSURE['path']))
        primitive=approval['references']['primitive_review']
        a.check_approval(w,approval,closure,primitive)
        for mutation in ('count','native-count','work-gate','closure-ref','durable','primitive'):
            left,right=copy.deepcopy(approval),copy.deepcopy(closure)
            if mutation=='count':left['successful_output_contracts']=148
            elif mutation=='native-count':left['native_attempts']=149
            elif mutation=='work-gate':left['source_work_qualified']=True
            elif mutation=='closure-ref':left['current_closure']['sha256']='0'*64
            elif mutation=='durable':right['durable']['lease']['inode']+=1
            else:left['references']['primitive_review']['sha256']='0'*64
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):
                a.check_approval(w,left,right,primitive)

    def test_final_lease_is_owned_without_mutating_outer_lifetime(self):
        with tempfile.TemporaryDirectory() as temporary:
            job=Path(temporary).resolve();path=job/'owner.lock';path.write_bytes(b'')
            identity=path.stat();seen=[]
            @contextmanager
            def regular(p):
                with p.open('rb') as stream:yield stream
            def check(leases):
                self.assertTrue(all(not row[1].closed for row in leases));seen.append(len(leases))
            e=SimpleNamespace(regular=regular,check_leases=check)
            durable=dict(directory=str(job),lease=dict(path=str(path),device=identity.st_dev,inode=identity.st_ino))
            with (job/'outer.lock').open('w+b') as outer:
                inherited=[(job/'outer.lock',outer,(1,2))]
                with patch.object(a,'JOB',job):
                    with a.final_lease(e,inherited,durable) as combined:
                        self.assertEqual(len(combined),2);self.assertEqual(len(inherited),1)
                        added=combined[-1][1]
                    self.assertTrue(added.closed);self.assertFalse(outer.closed)
                    with self.assertRaises(AssertionError):
                        with a.final_lease(e,combined,durable):pass
            self.assertEqual(seen,[2,2])

    def test_build_retains_original_policy_and_adds_real_bounded_closure(self):
        base=load('final_work_plan_base',a.BASE)
        w=base.load_controller(a.BASE_SHA,a.BOUNDED_SHA,a.PRIMITIVE_SHA)
        final=w.load(a.read_small(a.FINAL),a.FINAL,'final_bound')
        frozen=dict(schema='rebol-three-work-observations-plan-v1',controller=w.__file__,
            schedule=[{'id':x} for x in w.IDS],native_processes=3,benchmark_samples=0,
            extension_image={'path':'image'},corrected_source={'path':'source'},unavailable_inputs=['absent'],
            prerequisite_artifact_closures=[{'directory':'old','artifacts':{}}],
            prior_durable_jobs=[{'directory':'oldjob','artifacts':{}}],**{k:False for k in w.GATES})
        calls=[]
        w.build_plan=lambda *args:(calls.append(args) or copy.deepcopy(frozen))
        own=dict(path=str(Path(a.__file__).resolve()),sha256=OWN)
        w=a.attach(w,base,final,BASE_REVIEW,own)
        prior=copy.deepcopy(frozen);closures=prior['prerequisite_artifact_closures']+[{'directory':'final8','artifacts':{}}]
        jobs=prior['prior_durable_jobs']+[{'directory':'finaljob','artifacts':{}}]
        record={'review':a.BOUNDED_REVIEW}
        args=[None]*15;args[5]=SimpleNamespace(kb=object());args[6]=a.PACKET/'run-v1';args[13]={};args[14]={}
        with patch.object(a,'bounded_inputs',return_value=(prior,closures,jobs,record)):
            result=w.build_plan(*args)
            self.assertEqual(result['schedule'],frozen['schedule'])
            self.assertEqual(result['native_processes'],3)
            self.assertTrue(all(result[k] is False for k in w.GATES))
            self.assertEqual(result['entrypoint'],own['path'])
            self.assertEqual(result['bounded_correctness'],record)
            self.assertEqual(result['prerequisite_artifact_closures'],closures)
            self.assertEqual(result['prior_durable_jobs'],jobs)
            args[6]=a.PACKET.parent/'wrong-run'
            with self.assertRaisesRegex(AssertionError,'Fresh final work packet'):w.build_plan(*args)
        self.assertEqual(len(calls),1)

    def test_cli_delegates_original_arguments_and_restores_argv(self):
        seen=[];controller=SimpleNamespace(main=lambda:seen.append(list(a.sys.argv)))
        argv=['entry','--adapter-sha256',OWN,'run','--plan','/plan','--plan-sha256','a'*64]
        with patch.object(a,'load_controller',return_value=controller) as loader,patch.object(a.sys,'argv',argv):
            a.main();self.assertIs(a.sys.argv,argv)
        loader.assert_called_once_with(OWN)
        self.assertEqual(seen,[['entry','run','--plan','/plan','--plan-sha256','a'*64]])


if __name__=='__main__':unittest.main()
