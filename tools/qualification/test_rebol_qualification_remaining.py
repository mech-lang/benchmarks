"""Exercise actual count replay and reject mismatched additive producer identities."""
import hashlib
import importlib.util
import json
from pathlib import Path
import types
import unittest

HERE=Path(__file__).resolve().parent


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


a=load(HERE/'rebol_qualification_remaining.py','qualification_remaining_test_target')


class Evidence:
    def physical(self,path):
        path=Path(path);assert path.resolve()==path
        return path
    def read_bytes(self,path):return Path(path).read_bytes()
    def pin(self,pins,resolutions,path,sha):
        path=Path(path);actual=hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual==sha,(path,actual,sha)
        assert str(path) not in pins or pins[str(path)]==sha
        pins[str(path)]=sha;resolutions[str(path)]=str(path)
    def document(self,ref,pins,resolutions):
        self.pin(pins,resolutions,ref['path'],ref['sha256'])
        return json.loads(self.read_bytes(ref['path']))


def references():
    return {key:dict(path=str(path),sha256=digit*64) for key,path,digit in (
        ('qualification',HERE/'rebol_qualification_remaining.py','1'),
        ('work',a.WORK,'2'),('bounded',a.BOUNDED,'3'),('primitive',a.PRIMITIVE,'4'))}


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.refs=references()
        self.q=load(a.ORIGINAL,'qualification_remaining_original_test')
        a.attach(self.q,types.SimpleNamespace(),self.refs)

    def test_exact_actual_commands(self):
        e=types.SimpleNamespace(PYTHON='/runtime/python')
        plan=dict(path='/evidence/plan.json',sha256='5'*64)
        for kind,original,extra in (
            ('bounded','rebol_bounded.py',['--primitive-adapter-sha256','4'*64]),
            ('work','rebol_work_observations.py',['--bounded-adapter-sha256','3'*64,'--primitive-adapter-sha256','4'*64])):
            expected=['/runtime/python','-I','-S','-B',self.refs[kind]['path'],
                '--adapter-sha256',self.refs[kind]['sha256'],*extra,'run','--plan',plan['path'],'--plan-sha256',plan['sha256']]
            self.assertEqual(a.command_for(e,HERE/original,plan,self.refs),expected)
        with self.assertRaisesRegex(AssertionError,'Only bounded and work'):
            a.command_for(e,a.PRIMITIVE,plan,self.refs)

    def test_stage_identity_rejects_old_entrypoint_and_wrong_dependency(self):
        for kind in ('bounded','work'):
            plan=dict(intake_adapter=self.refs[kind],entrypoint=self.refs[kind]['path'],
                primitive_intake_adapter=self.refs['primitive'],bounded_intake_adapter=self.refs['bounded'])
            a.check_stage_adapter(plan,kind,self.refs)
            with self.assertRaises(AssertionError):a.check_stage_adapter(dict(plan,entrypoint=str(a.ORIGINAL)),kind,self.refs)
            with self.assertRaises(AssertionError):a.check_stage_adapter(dict(plan,primitive_intake_adapter=self.refs['work']),kind,self.refs)
            if kind=='work':
                with self.assertRaises(AssertionError):a.check_stage_adapter(dict(plan,bounded_intake_adapter=self.refs['work']),kind,self.refs)

    def count_inputs(self):
        review=json.loads(Path(a.COUNTS['path']).read_text())
        sources={name:item for name,item in review['sources'].items() if name in review['bundles']}
        extension=dict(corrected_source={k:review['sources']['extension'][k] for k in ('path','sha256')},
            unchanged_facades={review['sources'][name]['path']:review['sources'][name]['sha256'] for name in ('io','loader','big','regex')})
        dependencies={str(path.relative_to(a.ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (self.q.COUNTER,self.q.LEDGER)}
        return dict(dependencies=dependencies),sources,extension

    def test_all_fifteen_real_owner_replays_match_corrected_admission(self):
        source,sources,extension=self.count_inputs();pins={};resolutions={}
        before=self.q.LEDGER.read_bytes();loader=self.q.pinned_module
        bundles,identities,review=self.q.counts(Evidence(),a.COUNTS,source,pins,resolutions,sources,extension)
        self.assertEqual(len(identities),15);self.assertEqual(len(bundles),10)
        self.assertEqual(identities['regexredux']['sha256'],'e031f15f60e0b53cd565a87a2993efec9fcecc9ea5dcde35f1a6f13576c7f650')
        self.assertEqual((bundles['regexredux']['canonical_loc'],bundles['regexredux']['physical_loc']),(469,375))
        self.assertEqual(self.q.LEDGER.read_bytes(),before)
        self.assertIs(self.q.pinned_module,loader)
        self.assertEqual(pins[str(a.BINDING)],a.BINDING_SHA)
        self.assertFalse(review['chart_admission'])

    def test_count_replay_restores_loader_on_rejected_input(self):
        source,sources,extension=self.count_inputs();source['dependencies'][str(self.q.LEDGER.relative_to(a.ROOT))]='0'*64
        loader=self.q.pinned_module
        with self.assertRaises(AssertionError):self.q.counts(Evidence(),a.COUNTS,source,{}, {},sources,extension)
        self.assertIs(self.q.pinned_module,loader)

    def test_old_count_approval_is_rejected(self):
        source,sources,extension=self.count_inputs()
        old=dict(path=str(a.ROOT/'experiments/rebol/source-counts-v1/count-review-v1.json'),sha256='e80b7331b96fe6f979cbb51ef0e04b117f276621aa156be3269501b7c7192a0f')
        with self.assertRaisesRegex(AssertionError,'Only the exact corrected'):
            self.q.counts(Evidence(),old,source,{}, {},sources,extension)


if __name__=='__main__':unittest.main()
