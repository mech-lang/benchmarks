"""Focused additive-intake checks; no evidence intake or native child."""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HERE = Path(__file__).resolve().parent
a = load('remaining_work_adapter_tests', HERE/'rebol_work_remaining.py')
OWN = a.digest(Path(a.__file__).read_bytes())
BOUNDED = a.digest(a.BOUNDED_ADAPTER.read_bytes())
PRIMITIVE = a.PRIMITIVE_ADAPTER_SHA


class RemainingWorkTests(unittest.TestCase):
    def controller(self):
        return a.load_controller(OWN, BOUNDED, PRIMITIVE)

    def refs(self):
        return [dict(path=str(path), sha256=sha) for path,sha in (
            (Path(a.__file__).resolve(),OWN),(a.BOUNDED_ADAPTER,BOUNDED),(a.PRIMITIVE_ADAPTER,PRIMITIVE))]

    def source_approval(self):
        original = load('remaining_work_review_original', a.ORIGINAL)
        own, bounded, primitive = self.refs()
        files = original.FILES | {str(path.relative_to(a.ROOT)) for path in (
            Path(own['path']), HERE/'test_rebol_work_remaining.py', a.PACKET/'README.md')}
        pins = {name:'a'*64 for name in files}
        pins[str(a.ORIGINAL.relative_to(a.ROOT))] = a.ORIGINAL_SHA
        pins[str(Path(own['path']).relative_to(a.ROOT))] = OWN
        return dict(schema='rebol-three-work-observations-remaining-source-review-v1',
            status='independent-source-review-complete-native-observations-pending', independent_review=True,
            files=pins, dependencies={str(a.BOUNDED.relative_to(a.ROOT)):a.BOUNDED_SHA,
                str(a.BOUNDED_ADAPTER.relative_to(a.ROOT)):BOUNDED,
                str(a.PRIMITIVE_ADAPTER.relative_to(a.ROOT)):PRIMITIVE},
            **{key:False for key in original.GATES})

    def test_frozen_controller_and_native_functions_are_retained(self):
        w = self.controller()
        original = load('remaining_work_original_comparison', a.ORIGINAL)
        self.assertEqual(Path(w.__file__), a.ORIGINAL)
        self.assertEqual(w.PACKET, a.PACKET.parent)
        self.assertEqual(w.FILES, original.FILES)
        for name in ('held','schedule','run','finish','native_capture','checked_case','main'):
            actual, expected = getattr(w,name), getattr(original,name)
            actual = getattr(actual,'__wrapped__',actual)
            expected = getattr(expected,'__wrapped__',expected)
            self.assertEqual(actual.__code__.co_code, expected.__code__.co_code)
            self.assertEqual(actual.__code__.co_filename, str(a.ORIGINAL))

    def test_exact_three_adapter_hashes_and_original_source_are_required(self):
        for own,bounded,primitive in (('0'*64,BOUNDED,PRIMITIVE),
                                      (OWN,'0'*64,PRIMITIVE),(OWN,BOUNDED,'0'*64)):
            with self.subTest(own=own,bounded=bounded,primitive=primitive), self.assertRaises(AssertionError):
                a.load_controller(own,bounded,primitive)
        with patch.object(a,'read_small',return_value=b'changed frozen controller'):
            with self.assertRaisesRegex(AssertionError,'Frozen work controller changed'):
                self.controller()

    def test_source_review_has_exact_union_and_no_admission(self):
        w = self.controller()
        review = self.source_approval()
        w.source_review(review)
        for mutation in ('old-schema','missing-file','extra-file','old-only-deps','changed-bounded',
                         'changed-primitive','changed-original','changed-own','gate','not-independent'):
            value = copy.deepcopy(review)
            if mutation=='old-schema': value['schema']='rebol-three-work-observations-source-review-v1'
            elif mutation=='missing-file': del value['files'][str((a.PACKET/'README.md').relative_to(a.ROOT))]
            elif mutation=='extra-file': value['files']['other.py']='a'*64
            elif mutation=='old-only-deps': value['dependencies']={str(a.BOUNDED.relative_to(a.ROOT)):a.BOUNDED_SHA}
            elif mutation=='changed-bounded': value['dependencies'][str(a.BOUNDED_ADAPTER.relative_to(a.ROOT))]='0'*64
            elif mutation=='changed-primitive': value['dependencies'][str(a.PRIMITIVE_ADAPTER.relative_to(a.ROOT))]='0'*64
            elif mutation=='changed-original': value['files'][str(a.ORIGINAL.relative_to(a.ROOT))]='0'*64
            elif mutation=='changed-own': value['files'][str(Path(a.__file__).resolve().relative_to(a.ROOT))]='0'*64
            elif mutation=='gate': value['source_work_qualified']=True
            else: value['independent_review']=False
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError): w.source_review(value)

    def test_only_original_helper_load_is_redirected(self):
        w = self.controller()
        r = w.load(a.read_small(a.BOUNDED),a.BOUNDED,'requested_original_bounded')
        self.assertEqual(r.ROOT,a.ROOT)
        self.assertEqual(Path(r.__file__),a.BOUNDED)
        self.assertEqual(r.run.__code__.co_filename,str(a.BOUNDED))
        other_path=a.PACKET/'synthetic_consumer.py'
        other=w.load(b'answer = 42\n',other_path,'independent_consumer')
        self.assertEqual(other.answer,42)
        self.assertEqual(other.__file__,str(other_path))
        with self.assertRaisesRegex(AssertionError,'Original shared149 helper changed'):
            w.load(b'changed helper',a.BOUNDED,'wrong')

    def test_redirect_preserves_hash_arguments_and_original_identity(self):
        original=load('remaining_work_hook_original',a.ORIGINAL)
        calls=[]
        def loader(*args):
            calls.append(args)
            return SimpleNamespace(ROOT=a.ROOT,__file__=str(a.BOUNDED))
        adapter=SimpleNamespace(load_controller=loader)
        w=a.attach(original,adapter,*self.refs())
        w.load(a.read_small(a.BOUNDED),a.BOUNDED,'bounded')
        self.assertEqual(calls,[(BOUNDED,PRIMITIVE)])
        adapter.load_controller=lambda *args:SimpleNamespace(ROOT=a.ROOT,__file__=str(a.BOUNDED_ADAPTER))
        with self.assertRaisesRegex(AssertionError,'Original bounded helper identity'):
            w.load(a.read_small(a.BOUNDED),a.BOUNDED,'bounded')

    def test_plan_adds_only_intake_refs_and_restricts_output_packet(self):
        original=load('remaining_work_plan_original',a.ORIGINAL)
        calls=[]
        frozen=dict(controller=str(a.ORIGINAL),controller_sha256=a.ORIGINAL_SHA,
                    schedule=[{'id':name} for name in original.IDS],native_processes=3,
                    benchmark_samples=0,**{key:False for key in original.GATES})
        def build(*args):
            calls.append(args)
            return copy.deepcopy(frozen)
        original.build_plan=build
        w=a.attach(original,SimpleNamespace(),*self.refs())
        args=[None]*15
        args[6]=a.PACKET/'run-v1'
        actual=w.build_plan(*args)
        own,bounded,primitive=self.refs()
        self.assertEqual(actual,dict(frozen,intake_adapter=own,bounded_intake_adapter=bounded,
                                    primitive_intake_adapter=primitive,entrypoint=own['path']))
        self.assertEqual(calls,[tuple(args)])
        for output in (a.PACKET,a.PACKET.parent/'run-v1',a.ROOT/'elsewhere'):
            args[6]=output
            with self.subTest(output=output), self.assertRaisesRegex(AssertionError,'additive work packet'):
                w.build_plan(*args)
        self.assertEqual(len(calls),1)

    def test_three_original_diagnostic_paths_and_limits_are_retained(self):
        w=self.controller()
        e=SimpleNamespace(RUNTIME=Path('/exact/rebol'),environment=lambda output:{'HOME':str(output/'home')})
        cases=[dict(benchmark=b,case=c,stdin=dict(bytes=n,sha256='a'*64))
               for (b,c),n in zip(w.CASES,(0,0,10299))]
        output=a.PACKET/'run-v1'
        slots=w.schedule(e,cases,dict(path='/exact/image.rebx'),output)
        self.assertEqual([slot['id'] for slot in slots],list(w.IDS))
        self.assertEqual([slot['command'][3] for slot in slots],
                         [str(w.PACKET/name) for name in ('binarytrees.reb','pidigits.reb','knucleotide.reb')])
        self.assertTrue(all(slot['command'][1:3]==['-q','-s'] and slot['timeout_seconds']==180
                            and slot['rss_limit_bytes']==512*1024**2 for slot in slots))
        self.assertEqual([slot['native_file_limit_bytes'] for slot in slots],[1024**2,1024**2,16*1024**2])
        self.assertEqual([slot['expected_observer_stderr_failure'] for slot in slots],[False,False,True])
        self.assertTrue(all(Path(slot['sidecar']).is_relative_to(output) for slot in slots))

    def test_cli_consumes_three_hashes_then_delegates_unchanged_arguments(self):
        observed=[]
        controller=SimpleNamespace(main=lambda:observed.append(list(a.sys.argv)))
        tail=['run','--plan','/exact/plan.json','--plan-sha256','b'*64]
        argv=[str(a.__file__),'--adapter-sha256',OWN,'--bounded-adapter-sha256',BOUNDED,
              '--primitive-adapter-sha256',PRIMITIVE,*tail]
        with patch.object(a,'load_controller',return_value=controller) as loader,patch.object(a.sys,'argv',argv):
            a.main()
        loader.assert_called_once_with(OWN,BOUNDED,PRIMITIVE)
        self.assertEqual(observed,[[str(a.ORIGINAL),*tail]])


if __name__=='__main__':
    unittest.main()
