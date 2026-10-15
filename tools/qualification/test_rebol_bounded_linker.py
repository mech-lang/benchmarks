"""Focused split-evidence intake regressions; no native workload is launched."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


HERE=Path(__file__).resolve().parent
a=load('combined149_test_adapter',HERE/'rebol_bounded_linker.py')
e=load('combined149_test_helper',HERE/'rebol_extension.py')
p=load('combined149_test_primitive',a.PRIMITIVE_ADAPTER)
OWN=a.digest(Path(a.__file__).read_bytes());PRIMITIVE=a.digest(a.PRIMITIVE_ADAPTER.read_bytes())


class CombinedTests(unittest.TestCase):
    def test_original_observation_and_schedule_remain_frozen(self):
        r=a.load_controller(OWN,PRIMITIVE)
        original=load('original149_comparison',a.ORIGINAL)
        self.assertEqual(Path(r.__file__),a.ORIGINAL)
        for name in ('schedule','held','verify_inputs','run','finish','checked_case','native_capture','check_primitive_review'):
            selected=getattr(r,name); frozen=getattr(original,name)
            selected=getattr(selected,'__wrapped__',selected);frozen=getattr(frozen,'__wrapped__',frozen)
            self.assertEqual(selected.__code__.co_code,frozen.__code__.co_code)
            self.assertEqual(selected.__code__.co_filename,str(a.ORIGINAL))
        for own,primitive in (('0'*64,PRIMITIVE),(OWN,'0'*64)):
            with self.subTest(own=own,primitive=primitive),self.assertRaises(AssertionError):
                a.load_controller(own,primitive)

    def test_all_actual_jobs_and_supplemental_header_are_required(self):
        intake=dict(include_roots=dict(macos_sdk='/selected/SDK'))
        missing='/selected/SDK/usr/include/mach-o/dyld-interposing.h'
        prior=dict(unavailable_inputs=['/prior/missing'])
        closures=[dict(directory='/prior/output',artifacts={})]
        jobs=[dict(stage=stage,directory='/jobs/'+stage) for stage in p.STAGES]
        image=dict(path='/approved/image.rebx',sha256='a'*64)
        header=dict(directory=str(p.HEADER_ROOT),artifacts={
            'mach-o/dyld-interposing.h':dict(bytes=2368,sha256=p.HEADER_SHA)})
        failure=dict(durable=dict(directory='/failed/diagnostic',artifacts={}))
        failure_closure=dict(directory='/failed/output',artifacts={})
        plan=dict(prior_fixed19_failure=failure,unavailable_inputs=sorted(['/prior/missing',missing]),prerequisite_artifact_closures=closures+[header,failure_closure],
            diagnostic_header_review=p.HEADER_REVIEW,pins={str(p.HEADER):p.HEADER_SHA},extension_durables=jobs,extension_image=image)
        self.assertEqual(a.check_prerequisites(plan,prior,closures,jobs,image,p,intake,failure,failure_closure),closures+[header,failure_closure])
        for key,value in (('extension_durables',jobs[:1]),('extension_durable',jobs[0]),
                          ('prerequisite_artifact_closures',closures),('unavailable_inputs',['/prior/missing']),
                          ('prior_fixed19_failure',{}),('diagnostic_header_review',dict(p.HEADER_REVIEW,sha256='0'*64))):
            changed=copy.deepcopy(plan);changed[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(AssertionError,'split jobs or diagnostic header'):
                a.check_prerequisites(changed,prior,closures,jobs,image,p,intake,failure,failure_closure)

    def test_actual_entrypoint_and_birth_identity_are_required(self):
        r=a.load_controller(OWN,PRIMITIVE)
        plan_ref=dict(path='/exact/primitive-plan.json',sha256='a'*64)
        argv=[str(e.PYTHON),'-I','-S','-B',str(a.PRIMITIVE_ADAPTER),'--adapter-sha256',PRIMITIVE,
              'run','--plan',plan_ref['path'],'--plan-sha256',plan_ref['sha256']]
        identity=dict(pid=9182,listing='retained birth identity')
        with tempfile.TemporaryDirectory() as temp:
            job=Path(temp).resolve()
            launch=dict(command=argv,cwd=str(a.ROOT))
            started=dict(launch,command_pid=9182,command_identity=identity,command_identity_observation_missing=False)
            ended=dict(status='command-exited-zero-awaiting-report-review',exit_code=0,actual_command_started=True,
                automatic_retry=False,stop_signals=[],command_pid=9182,command_identity=identity,command_identity_observation_missing=False)
            def write(l,s,t):
                for name,value in (('launch',l),('command-started',s),('terminal',t)):
                    (job/(name+'.json')).write_text(json.dumps(value))
                return dict(durable=dict(directory=str(job),artifacts=e.inventory(job)[0]))
            review=write(launch,started,ended)
            self.assertEqual(r.durable_inputs(e,review,plan_ref,{},{})[0],9182)
            old_argv=argv[:4]+[str(a.PRIMITIVE)]+argv[7:]
            for l,s,t in ((dict(launch,command=old_argv),dict(started,command=old_argv),ended),
                          (launch,started,dict(ended,command_identity=dict(identity,listing='reused PID'))),
                          (launch,started,dict(ended,status='command-succeeded'))):
                review=write(l,s,t)
                with self.assertRaisesRegex(AssertionError,'Primitive durable ownership'):
                    r.durable_inputs(e,review,plan_ref,{},{})


if __name__=='__main__':unittest.main()
