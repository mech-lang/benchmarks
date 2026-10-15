"""Pure intake-boundary checks; no qualification context, preparation or native work."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).with_name('rebol_full_remaining.py')
spec=importlib.util.spec_from_file_location('test_rebol_full_remaining_source',SOURCE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def original():
    raw=m.ORIGINAL.read_bytes()
    if m.digest(raw)!=m.ORIGINAL_SHA:raise AssertionError('Frozen producer changed')
    module=types.ModuleType('full_remaining_test_original');module.__file__=str(m.ORIGINAL)
    exec(compile(raw,str(m.ORIGINAL),'exec'),module.__dict__)
    return module


def loaded():
    return m.load_controller(m.digest(SOURCE.read_bytes()),
        *(m.ADAPTERS[key]['sha256'] for key in ('qualification','work','bounded','primitive')))


def review_document(f):
    files=(*f.SOURCE_FILES,SOURCE,Path(__file__).resolve(),m.PACKET/'README.md')
    dependencies=(f.QUALIFIER,f.HELPERS,f.RECEIPTS,*(Path(ref['path']) for ref in m.ADAPTERS.values()))
    return dict(schema='rebol-full90-remaining-source-review-v1',
        status='independent-source-review-complete-native-timing-pending',independent_review=True,
        files={str(path.relative_to(m.ROOT)):m.digest(path.read_bytes()) for path in files},
        dependencies={str(path.relative_to(m.ROOT)):m.digest(path.read_bytes()) for path in dependencies},
        full_timing_qualified=False,chart_admission=False)


class FullRemaining(unittest.TestCase):
    def tearDown(self):
        for name in ('rebol_full90_qualification','rebol_full90_qualification_intake'):
            sys.modules.pop(name,None)

    def source_ref(self,directory,document):
        path=Path(directory).resolve()/'source-review.json'
        raw=json.dumps(document,sort_keys=True).encode();path.write_bytes(raw)
        return dict(path=str(path),sha256=m.digest(raw))

    def test_original_execution_identity_and_ninety_slots_unchanged(self):
        f,before=loaded(),original()
        self.assertEqual((f.__file__,f.ROOT,f.PACKET,f.SUITE_LEASE),
            (before.__file__,before.ROOT,before.PACKET,before.SUITE_LEASE))
        for name,value in vars(before).items():
            if isinstance(value,types.FunctionType) and name not in ('source_intake','build_plan'):
                self.assertEqual(getattr(f,name).__code__,value.__code__,name)
        manifests={}
        for bench in f.BENCHES:
            rows=[dict(id=f'rebol-{bench}-{form}',key=f'rebol-{bench}-{form}',benchmark=bench,
                language='rebol3',variant=form,source_sha256='a'*64) for form in f.FORMS]
            rows.append(dict(id='mech-aot-control',key=bench+':rebol-full-study:mech-control',
                benchmark=bench,language='mech',source_sha256='b'*64))
            manifests[bench]=dict(benchmark=bench,profiles=rows,samples=3,orders=f.orders_for(bench))
        slots=f.schedule_for(manifests)
        self.assertEqual(slots,before.schedule_for(manifests));self.assertEqual(len(slots),90)
        self.assertEqual(sum(slot[2]=='mech-aot-control' for slot in slots),30)
        self.assertEqual(sum(slot[2].endswith('-compact') for slot in slots),30)
        self.assertEqual(sum(slot[2].endswith('-optimized') for slot in slots),30)

    def test_actual_source_chain_loads_without_entering_qualification(self):
        f=loaded();document=review_document(f)
        with tempfile.TemporaryDirectory() as directory:
            source=self.source_ref(directory,document);q,pins=f.source_intake(source)
        self.assertEqual((q.ROOT,Path(q.__file__)),(m.ROOT,f.QUALIFIER))
        self.assertEqual(q.intake_adapters,m.ADAPTERS)
        self.assertEqual(len(document['files']),6);self.assertEqual(len(document['dependencies']),7)
        self.assertEqual(pins,{**{str(m.ROOT/name):sha for group in ('files','dependencies')
            for name,sha in document[group].items()},source['path']:source['sha256']})
        self.assertEqual(pins[str(f.QUALIFIER)],m.QUALIFIER_SHA)

    def test_source_review_rejects_missing_and_changed_sources_or_gates(self):
        f=loaded();document=review_document(f)
        with tempfile.TemporaryDirectory() as directory:
            for fault in ('missing-source','missing-dependency','helper','adapter','producer','gate','review-bytes'):
                with self.subTest(fault=fault):
                    bad=copy.deepcopy(document)
                    if fault=='missing-source':bad['files'].pop(str(SOURCE.relative_to(m.ROOT)))
                    elif fault=='missing-dependency':bad['dependencies'].pop(str(f.QUALIFIER.relative_to(m.ROOT)))
                    elif fault=='helper':bad['dependencies'][str(f.HELPERS.relative_to(m.ROOT))]='0'*64
                    elif fault=='adapter':bad['dependencies'][str(Path(m.ADAPTERS['work']['path']).relative_to(m.ROOT))]='0'*64
                    elif fault=='producer':bad['files'][str(m.ORIGINAL.relative_to(m.ROOT))]='0'*64
                    elif fault=='gate':bad['full_timing_qualified']=True
                    source=self.source_ref(directory,bad)
                    if fault=='review-bytes':Path(source['path']).write_bytes(b'{}')
                    with self.assertRaises(AssertionError):f.source_intake(source)

    def test_loader_rejects_wrong_chain_or_own_digest(self):
        shas=[m.digest(SOURCE.read_bytes()),*(m.ADAPTERS[key]['sha256']
            for key in ('qualification','work','bounded','primitive'))]
        for index in range(5):
            with self.subTest(index=index):
                bad=list(shas);bad[index]='0'*64
                with self.assertRaises(AssertionError):m.load_controller(*bad)

    def test_adapted_qualification_cannot_change_proof_identity(self):
        for fault in ('root','file','chain'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as directory:
                f=loaded();document=review_document(f)
                q=types.SimpleNamespace(ROOT=m.ROOT,__file__=str(f.QUALIFIER),intake_adapters=copy.deepcopy(m.ADAPTERS))
                if fault=='root':q.ROOT=Path(directory)
                elif fault=='file':q.__file__=str(SOURCE)
                else:q.intake_adapters['work']['sha256']='0'*64
                original_q=types.SimpleNamespace(ROOT=m.ROOT,__file__=str(f.QUALIFIER))
                adapter=types.SimpleNamespace(load_controller=lambda *args:q)
                with patch.object(f,'load',side_effect=[original_q,adapter]):
                    with self.assertRaisesRegex(AssertionError,'qualification identity'):
                        f.source_intake(self.source_ref(directory,document))

    def test_build_wrapper_only_adds_metadata_and_confines_fresh_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();packet=root/'packet';packet.mkdir()
            f=original();calls=[]
            baseline=dict(schema='unchanged',schedule=[['immutable']],full_processes=90,
                rebol_samples=60,matched_mech_samples=30,chart_admission=False)
            def build(*args):calls.append(args);return copy.deepcopy(baseline)
            f.build_plan=build
            adapter_ref=dict(path=str(SOURCE),sha256=m.digest(SOURCE.read_bytes()))
            # Attach under the real root for source membership; only the dynamic output root is synthetic.
            f=m.attach(f,adapter_ref,copy.deepcopy(m.ADAPTERS))
            args=(object(),object(),object(),object(),packet/'run',object(),object(),object())
            with patch.object(m,'PACKET',packet):
                result=f.build_plan(*args)
                metadata=dict(intake_adapter=adapter_ref,entrypoint=str(SOURCE),
                    **{key+'_intake_adapter':value for key,value in m.ADAPTERS.items()})
                self.assertEqual(result,{**baseline,**metadata});self.assertEqual(calls,[args])
                (packet/'existing').mkdir();(root/'linked').symlink_to(packet,target_is_directory=True)
                for output in (packet,root/'outside',packet/'existing',root/'linked'/'run',Path('relative')):
                    bad=(*args[:4],output,*args[5:])
                    with self.subTest(output=str(output)),self.assertRaises(AssertionError):f.build_plan(*bad)
                (packet/'link').symlink_to(root,target_is_directory=True)
                with self.assertRaises(AssertionError):f.build_plan(*args[:4],packet/'link'/'run',*args[5:])
                self.assertEqual(calls,[args])

    def test_cli_passes_exact_chain_and_restores_argv_on_failure(self):
        flags=('adapter','qualification-adapter','work-adapter','bounded-adapter','primitive-adapter')
        values=[str(index)*64 for index in range(1,6)]
        argv=[str(SOURCE),*(item for name,value in zip(flags,values)
            for item in ('--'+name+'-sha256',value)),'prepare','--plan','/future/plan.json']
        seen=[]
        def run():seen.append(list(sys.argv));raise RuntimeError('synthetic dispatch stop')
        with patch.object(sys,'argv',argv),patch.object(m,'load_controller',return_value=types.SimpleNamespace(main=run)) as load:
            with self.assertRaisesRegex(RuntimeError,'synthetic dispatch'):m.main()
            self.assertIs(sys.argv,argv);load.assert_called_once_with(*values)
        self.assertEqual(seen,[[str(m.ORIGINAL),'prepare','--plan','/future/plan.json']])


if __name__=='__main__':unittest.main()
