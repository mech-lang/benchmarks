"""Focused single-process continuation checks; no native process or full intake."""
from contextlib import contextmanager, nullcontext
import copy
import importlib.util
import json
import os
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
a=load('single_map_tests',HERE/'rebol_work_map.py')
old=load('original_work_fixture_helpers',HERE/'test_rebol_work_observations.py')
OWN=a.digest(Path(a.__file__).read_bytes())


class SingleMapTests(unittest.TestCase):
    def controller(self):return a.load_controller(OWN)

    def test_real_source_review_and_unchanged_native_check_functions(self):
        w=self.controller()
        self.assertEqual(w.__file__,old.w.__file__)
        self.assertEqual(w.PACKET,old.w.PACKET)
        for name in ('native_capture','checked_case','main'):
            self.assertEqual(getattr(w,name).__code__.co_code,getattr(old.w,name).__code__.co_code)
            self.assertEqual(getattr(w,name).__code__.co_filename,old.w.__file__)
        base=json.loads(a.read_small(a.BASE_REVIEW['path']));maps=json.loads(a.read_small(a.MAP_REVIEW['path']))
        files=dict(base['files'],**maps['files'])
        files.update({str(p.relative_to(a.ROOT)):'a'*64 for p in (
            Path(a.__file__),HERE/'test_rebol_work_map.py',a.PACKET/'README.md')})
        files[str(Path(a.__file__).relative_to(a.ROOT))]=OWN
        review=dict(schema='rebol-single-map-work-source-review-v1',
            status='independent-source-review-complete-native-observation-pending',independent_review=True,
            files=files,dependencies=base['dependencies'],base_source_review=a.BASE_REVIEW,
            map_source_review=a.MAP_REVIEW,prior_stage_review=a.PRIOR,**{k:False for k in a.GATES})
        w.source_review(review)
        for change in ({'source_work_qualified':True},{'prior_stage_review':{}},{'files':{}}):
            with self.assertRaises(AssertionError):w.source_review(dict(review,**change))
        with self.assertRaisesRegex(AssertionError,'Single-map adapter changed'):a.load_controller('0'*64)

    def test_exact_one_slot_delta_does_not_repeat_tree_or_pi(self):
        original=old.plan(Path('/fresh'))['schedule'];before=copy.deepcopy(original)
        actual=a.map_schedule(original)
        expected=copy.deepcopy(original[2]);expected['command'][3]=a.MAP_SOURCE['path'];expected['expected_observer_stderr_failure']=False
        self.assertEqual(actual,[expected]);self.assertEqual(original,before)
        self.assertEqual(actual[0]['rss_limit_bytes'],512*1024**2)
        self.assertEqual(actual[0]['timeout_seconds'],180)
        for bad in (original[:1],original[::-1],dict(original[2],expected_observer_stderr_failure=False)):
            with self.assertRaises((AssertionError,TypeError)):
                a.map_schedule(bad if isinstance(bad,list) else [*original[:2],bad])

    def test_actual_mixed_json_markdown_review_references_are_pinned_as_bytes(self):
        review=json.loads(a.read_small(a.MAP_REVIEW['path']))
        pins,resolutions={},{}
        a.pin_review_references(old.e,review['references'],pins,resolutions)
        self.assertEqual(set(pins),{x['path'] for x in review['references'].values()})
        self.assertTrue(review['references']['diagnosis']['path'].endswith('.md'))
        for field in ('bytes','sha256'):
            refs=copy.deepcopy(review['references'])
            refs['diagnosis'][field]=refs['diagnosis'][field]+1 if field=='bytes' else '0'*64
            with self.subTest(field=field),self.assertRaises(AssertionError):
                a.pin_review_references(old.e,refs,{}, {})

    def test_actual_failure_disposition_and_two_retained_capture_join(self):
        review=json.loads(a.read_small(a.PRIOR['path']))
        primitive=review['references']['primitive_review'];bounded=review['references']['bounded_source_review']
        captures=[x['capture'] for x in review['successful_captures']]
        ids=['binarytrees-n4','pidigits-n27','knucleotide-arbitrary-widths']
        plan=dict(schema='rebol-three-work-observations-plan-v1',repository=str(a.ROOT),
            final_intake_adapter=dict(path=str(a.BASE),sha256=a.BASE_SHA),entrypoint=str(a.BASE),
            source_review=a.BASE_REVIEW,primitive_review=primitive,bounded_source_review=bounded,
            output=str(a.PRIOR_PACKET/'run-v1'),schedule=[dict(id=x) for x in ids],pins={},input_resolutions={},
            **{k:False for k in a.GATES})
        report=dict(schema='rebol-three-work-observations-results-v1',status='stopped-unqualified',
            error='Bounded process group exceeded RSS limit',error_type='AssertionError',plan=a.REFS['plan']['path'],
            plan_sha256=a.REFS['plan']['sha256'],active=None,attempts=ids,
            registered=[dict(id=x,pid=p) for x,p in zip(ids,[captures[0]['pid'],captures[1]['pid'],18005])],
            captures=captures,integrity_errors=[],artifact_errors=[],pins={a.REFS['plan']['path']:a.REFS['plan']['sha256']},
            input_resolutions={a.REFS['plan']['path']:a.REFS['plan']['path']},**{k:False for k in a.GATES})
        terminal=dict(schema='rebol-three-work-observations-terminal-v1',status='stopped-unqualified',
            integrity_errors=[],artifact_errors=[],report_sha256=a.REFS['report']['sha256'],
            expected_report_sha256=a.REFS['report']['sha256'],common_mutex_held=True,native_processes_started=3,
            validated_observations=2,**{k:False for k in a.GATES})
        a.prior_ledger(review,plan,report,terminal,primitive,bounded)
        for mutation in ('promoted','one-retained','pid','wrong-error','wrong-source','lost-failure'):
            v,p,r,t=map(copy.deepcopy,(review,plan,report,terminal))
            if mutation=='promoted':r['status']=t['status']=a.SUCCESS
            elif mutation=='one-retained':v['successful_captures'].pop()
            elif mutation=='pid':r['registered'][1]['pid']=r['registered'][0]['pid']
            elif mutation=='wrong-error':r['error']='Unexpected stderr; raw bytes retained'
            elif mutation=='wrong-source':p['final_intake_adapter']['sha256']='0'*64
            else:v['failed_observations']=0
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):
                a.prior_ledger(v,p,r,t,primitive,bounded)

    def test_prior_lease_keeps_inherited_stream_alive(self):
        with tempfile.TemporaryDirectory() as temp:
            job=Path(temp).resolve();lease=job/'owner.lock';lease.write_bytes(b'');st=lease.stat()
            @contextmanager
            def regular(path):
                with path.open('rb') as f:yield f
            def check(rows):self.assertTrue(all(not row[1].closed for row in rows))
            e=SimpleNamespace(regular=regular,check_leases=check)
            review=dict(durable=dict(directory=str(job),lease=dict(path=str(lease),device=st.st_dev,inode=st.st_ino)))
            with (job/'outer').open('w+b') as outer:
                inherited=[(job/'outer',outer,(0,0))]
                with patch.object(a,'JOB',job):
                    with a.prior_lease(e,inherited,review) as combined:
                        self.assertEqual(len(inherited),1);self.assertEqual(len(combined),2);added=combined[-1][1]
                    self.assertTrue(added.closed);self.assertFalse(outer.closed)

    def synthetic_run(self,base,fail=False,alter_preserved=False):
        output=base/'run';corpus=base/'corpus';corpus.mkdir();(corpus/'2.stdin').write_bytes(b'')
        (corpus/'2.expected').write_bytes(b'map')
        document=old.plan(output);document['schedule']=a.map_schedule(document['schedule'])
        document.update(prior_work_stage={'review':a.PRIOR},preserved_observations=2)
        calls=[]
        def observe(command,environment,directory,payload,common,launched,**kwargs):
            calls.append(command);launched(9202);slot=document['schedule'][0]
            _,_,record=old.native_files(directory,slot,2)
            record.update(status='native-passed',stderr_bytes=0,stderr_sha256=a.digest(b''))
            record.pop('error');record.pop('error_type');(directory/'stderr.bin').write_bytes(b'')
            old.save(directory/'process.json',record)
            if fail:raise AssertionError('Unexpected stderr; raw bytes retained')
        def save(path,value):
            if alter_preserved and path.name=='report.json' and value['status']=='running' and value['captures']:
                value['preserved_observations']=3
            old.save(path,value)
        kb=SimpleNamespace(PIPE_CHUNK=65536,atomic=nullcontext,save=save,observe=observe)
        with patch.object(old.r,'CORPUS',corpus/'manifest.json'),patch.object(old.r,'verify_inputs'), \
             patch.object(old.e,'pin'),patch.object(old.e,'check_leases'):
            a.run(old.w,old.r,old.e,None,old.consumers(),kb,document,base/'plan','a'*64,{},{},None,[])
        return calls,json.loads((output/'report.json').read_bytes()),json.loads((output/'terminal.json').read_bytes())

    def test_single_map_run_has_one_new_capture_and_two_separate_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            calls,report,terminal=self.synthetic_run(Path(temp).resolve())
            self.assertEqual(len(calls),1)
            self.assertEqual(report['schema'],'rebol-single-map-work-results-v1')
            self.assertEqual(terminal['schema'],'rebol-single-map-work-terminal-v1')
            self.assertEqual(report['attempts'],list(a.IDS));self.assertEqual(len(report['captures']),1)
            self.assertEqual(terminal['native_processes_started'],1);self.assertEqual(terminal['validated_observations'],1)
            self.assertEqual(report['preserved_observations'],2);self.assertEqual(terminal['preserved_observations'],2)
            self.assertEqual(terminal['status'],a.SUCCESS)
            self.assertTrue(all(terminal[k] is False for k in a.GATES))

    def test_old_stderr_exception_is_not_accepted_or_retried(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve()
            with self.assertRaisesRegex(AssertionError,'Unexpected stderr'):
                self.synthetic_run(base,fail=True)
            report=json.loads((base/'run/report.json').read_bytes());terminal=json.loads((base/'run/terminal.json').read_bytes())
            self.assertEqual(report['attempts'],list(a.IDS));self.assertEqual(report['captures'],[])
            self.assertEqual(terminal['status'],'stopped-unqualified');self.assertEqual(terminal['native_processes_started'],1)

    def test_finalizer_rejects_fabricated_preserved_count(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve()
            with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                self.synthetic_run(base,alter_preserved=True)
            terminal=json.loads((base/'run/terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-integrity')
            self.assertIn('Preserved work disposition changed',terminal['integrity_errors'])


if __name__=='__main__':unittest.main()
