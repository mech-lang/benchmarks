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
a=load('combined149_test_adapter',HERE/'rebol_bounded_remaining.py')
e=load('combined149_test_helper',HERE/'rebol_extension.py')
supplemental=load('remaining149_test_primitive',a.PRIMITIVE_ADAPTER)
p=supplemental.load_controller(a.PRIMITIVE_ADAPTER_SHA)
OWN=a.digest(Path(a.__file__).read_bytes());PRIMITIVE=a.digest(a.PRIMITIVE_ADAPTER.read_bytes())


class CombinedTests(unittest.TestCase):
    def approval(self):
        ref=lambda name:dict(path='/evidence/'+name,sha256='a'*64)
        job=a.ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/remaining16'
        r=a.load_controller(OWN,PRIMITIVE)
        return dict(schema='rebol-combined-independent-primitive-review-v1',
            status='exact-eighteen-primitive-contracts-qualified',independent_review=True,
            full_primitive_fixtures_qualified=True,native_attempts=21,primitive_attempts=19,
            diagnostic_compile_attempts=2,successful_captures=19,successful_primitive_contracts=18,
            failed_attempts=2,benchmark_samples=0,
            references={key:ref(key) for key in ('plan','report','terminal','extension_review','source_review')},
            prior_cohorts={key:ref(key) for key in ('first_compile_failure','linker_stage')},
            durable=dict(directory=str(job),artifacts={},lease=dict(path=str(job/'owner.lock'),device=1,inode=2)),
            **{key:False for key in r.GATES})

    def test_original_observation_and_schedule_remain_frozen(self):
        r=a.load_controller(OWN,PRIMITIVE)
        original=load('original149_comparison',a.ORIGINAL)
        self.assertEqual(Path(r.__file__),a.ORIGINAL)
        for name in ('schedule','held','verify_inputs','run','finish','checked_case','native_capture'):
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
        linker=dict(durable=dict(directory='/linker/job',artifacts={}))
        linker_closure=dict(directory='/linker/output',artifacts={})
        plan=dict(prior_fixed19_failure=failure,prior_linker_stage=linker,unavailable_inputs=sorted(['/prior/missing',missing]),prerequisite_artifact_closures=closures+[header,failure_closure,linker_closure],
            diagnostic_header_review=p.HEADER_REVIEW,pins={str(p.HEADER):p.HEADER_SHA},extension_durables=jobs,extension_image=image)
        self.assertEqual(a.check_prerequisites(plan,prior,closures,jobs,image,p,intake,failure,failure_closure,linker,linker_closure),closures+[header,failure_closure,linker_closure])
        for key,value in (('extension_durables',jobs[:1]),('extension_durable',jobs[0]),
                          ('prerequisite_artifact_closures',closures),('unavailable_inputs',['/prior/missing']),
                          ('prior_fixed19_failure',{}),('prior_linker_stage',{}),('diagnostic_header_review',dict(p.HEADER_REVIEW,sha256='0'*64))):
            changed=copy.deepcopy(plan);changed[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(AssertionError,'split jobs or diagnostic header/failure'):
                a.check_prerequisites(changed,prior,closures,jobs,image,p,intake,failure,failure_closure,linker,linker_closure)

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

    def test_combined_approval_preserves_real_attempt_accounting(self):
        r=a.load_controller(OWN,PRIMITIVE);review=self.approval()
        r.check_primitive_review(review)
        for key,value in (('schema','rebol19-independent-primitive-review-v1'),
                          ('native_attempts',19),('primitive_attempts',18),('failed_attempts',0),
                          ('diagnostic_compile_attempts',True),('successful_captures',18),
                          ('benchmark_samples',False),('chart_admission',True),
                          ('full_primitive_fixtures_qualified',False),('prior_cohorts',{})):
            changed=copy.deepcopy(review);changed[key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):r.check_primitive_review(changed)
        for mutation in ('missing-reference','old-reference','foreign-lease'):
            changed=copy.deepcopy(review)
            if mutation=='missing-reference':del changed['references']['source_review']
            elif mutation=='old-reference':changed['references']['original_plan']={}
            else:changed['durable']['lease']['path']='/unrelated/owner.lock'
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):r.check_primitive_review(changed)

    def test_three_preserved_plus_sixteen_new_cover_contracts_once(self):
        r=a.load_controller(OWN,PRIMITIVE)
        transport=load('remaining_transport_order',p.ADAPTER)
        ids=list(transport.CASE_IDS[2:])
        rows=[dict(id=name,started_at=f'2026-10-15T00:00:0{i*2}+00:00',
                   finished_at=f'2026-10-15T00:00:0{i*2+1}+00:00')
              for i,name in enumerate(('compile-io-interposer','arithmetic','formatting'))]
        linker=dict(successful_captures=rows)
        self.assertEqual(a.prior_success_end(r,linker,ids,transport.CASE_IDS),r.stamp(rows[-1]['finished_at']))
        for current in (ids[1:],ids[::-1],ids[:-1]+[ids[0]]):
            with self.assertRaises(AssertionError):a.prior_success_end(r,linker,current,transport.CASE_IDS)
        bad=copy.deepcopy(linker);bad['successful_captures'][1]['started_at']=rows[0]['started_at']
        with self.assertRaisesRegex(AssertionError,'overlap'):a.prior_success_end(r,bad,ids,transport.CASE_IDS)

    def selection_inputs(self):
        original=load('remaining_original_source_selection',a.ORIGINAL)
        spec=json.loads((original.ORIGINAL/'spec.json').read_bytes())
        mapping=json.loads((original.ORIGINAL/'bounded-corpus-map.json').read_bytes())
        cases=[dict(benchmark=row['benchmark'],case=name) for row in mapping['rows'] for name in row['case_ids']]
        pins={str(a.ROOT/name):value for name,value in spec['immutable_source_pins'].items()}
        pins[str(original.FANN)]=a.digest(original.FANN.read_bytes())
        return original,spec,mapping,cases,pins

    def test_only_regex_main_changes_and_original_pin_is_retained(self):
        original,spec,mapping,cases,pins=self.selection_inputs()
        before=original.source_selection(e,spec,mapping,cases,copy.deepcopy(pins),{})
        r=a.load_controller(OWN,PRIMITIVE)
        actual=r.source_selection(e,spec,mapping,cases,pins,{})
        self.assertEqual(set(actual),set(before))
        for bench in before:
            if bench!='regexredux':self.assertEqual(actual[bench],before[bench])
        old=before['regexredux'];corrected=actual['regexredux']
        self.assertEqual({k:corrected[k] for k in ('path','sha256')},a.REGEX_MAIN)
        self.assertEqual(corrected['historical_path'],old['path'])
        self.assertEqual(corrected['historical_sha256'],old['sha256'])
        self.assertEqual(pins[old['path']],old['sha256']);self.assertEqual(pins[a.REGEX_MAIN['path']],a.REGEX_MAIN['sha256'])
        self.assertEqual(corrected['substitution'],'literal-regex-source')

    def test_corrected_source_cannot_bypass_exact_review_or_helpers(self):
        r=a.load_controller(OWN,PRIMITIVE)
        original,spec,mapping,cases,pins=self.selection_inputs()
        review=json.loads(Path(a.REGEX_REVIEW['path']).read_bytes())
        for name in ('old-source','new-source','helper','gate'):
            changed=copy.deepcopy(review)
            if name=='old-source':changed['original_sources']['original_main']['sha256']='0'*64
            elif name=='new-source':changed['files']['main.reb']['sha256']='0'*64
            elif name=='helper':changed['relative_helper_paths']=[x for x in changed['relative_helper_paths'] if x['source']!='main.reb']
            else:changed['canonical_source_count_qualified']=True
            helper=SimpleNamespace(document=lambda *args:copy.deepcopy(changed),pin=e.pin)
            with self.subTest(name=name),self.assertRaises(AssertionError):
                a.select_sources(r,original.source_selection,helper,spec,mapping,cases,copy.deepcopy(pins),{})


if __name__=='__main__':unittest.main()
