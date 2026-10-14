"""Small in-memory/temporary-file transaction faults; no runtime file phase."""
import copy
from contextlib import contextmanager, ExitStack, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


i = load('retained_import_test', HERE/'import_retained_catalog.py')
w = load('retained_writer_test', HERE/'import_uiua_fann.py')
n = load('retained_history_test', HERE.parent/'normalization_history.py')
t = load('retained_transform_fixture', HERE/'test_retained_catalog_publication.py')
f = load('retained_fann_fixture', HERE/'test_uiua_fann_publication.py')


@contextmanager
def fixture(cohort, candidate, existing_history=False):
    """Use real pure transforms, with a small held-evidence stand-in only."""
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        spec = copy.deepcopy(i.COHORTS[cohort])
        packet = root/spec['packet']; packet.mkdir(parents=True)
        (root/'data').mkdir()
        data, metadata = f.catalog() if cohort == 'uiua-fann' else t.catalog(candidate, expanded_reference=cohort == 'uiua')
        originals = dict(zip(i.CATALOGS, map(i.encoded, (data,metadata))))
        originals[i.HISTORY] = i.encoded(dict(schema='canonical-loc-normalization-history-v1', admissions=[])) if existing_history else None
        for name,raw in originals.items():
            if raw is not None:
                (root/name).write_bytes(raw)
        saved = packet/'candidate.json'; saved.write_bytes(i.encoded(candidate))
        tool = root/'consumer.py'; tool.write_bytes(b'fixed consumer source\n')
        state = dict(mutation=None, history_mutation=None, historical_fault=False, held=False, closed=False, replayed=False)

        class Files:
            def verify(self,path,digest):
                i.checked(path,digest)

        @contextmanager
        def context(*_,on_exit_failure=None,final_consumer_check=None):
            state['held'] = True
            try:
                yield {},Files()
                state['replayed'] = True
                if state['mutation'] is not None:
                    state['mutation']()
                final_consumer_check()
                state['closed'] = True
            except BaseException:
                selfcheck = state['held']
                on_exit_failure()
                assert selfcheck
                raise
            finally:
                state['held'] = False

        def history(root, actual):
            assert state['held']
            if not (root/i.HISTORY).exists():
                return actual
            document = n.validate_registry(n.strict_json((root/i.HISTORY).read_bytes()))
            for entry in document['admissions']:
                raw = i.checked(root/entry['success']['path'],entry['success']['sha256'])
                success = n.strict_json(raw)
                i.require(success['status']=='applied' and success['audit']==actual[entry['audit_key']], 'History fixture differs')
                base = (root/entry['success']['path']).parent
                for phase,field in [('before','originals'),('after','prepared')]:
                    for name in i.CATALOGS:
                        i.checked(base/phase/name,success[field][name])
            if state['historical_fault'] and document['admissions']:
                raise ValueError('Injected final history failure')
            if state['history_mutation'] is not None and document['admissions']:
                state['history_mutation']()
            return actual

        deps = dict(spec=spec, pins={tool:i.sha(tool.read_bytes())}, writer=w,
            reconciler=SimpleNamespace(review_context=context,review_files=context),
            publication=f.p if cohort=='uiua-fann' else t.p,
            normalization=SimpleNamespace(strict_json=n.strict_json, validate_registry=n.validate_registry,
                validate_transition=n.validate_transition,historical_view=history))

        def args(mode='preview', preview=None, output=None):
            result = SimpleNamespace(cohort=cohort,mode=mode,output=output or packet/('preview' if mode=='preview' else 'apply'),
                apply_output=packet/'apply' if mode=='preview' else None,candidate=saved,candidate_sha256=i.sha(saved.read_bytes()))
            for name,suffix in zip(i.TARGETS,('catalog','languages','history')):
                setattr(result,'expected_'+suffix+'_sha256',preview['originals'][name] if preview else None)
                setattr(result,'expected_prepared_'+suffix+'_sha256',preview['prepared'][name] if preview else None)
            return result

        def run(arguments):
            with redirect_stdout(io.StringIO()):
                return i.run(arguments,deps)

        with ExitStack() as stack:
            stack.enter_context(patch.object(i,'ROOT',root))
            stack.enter_context(patch.object(i,'reproduce',return_value=copy.deepcopy(candidate)))
            stack.enter_context(patch.object(i,'validate_apl_runtime',return_value=copy.deepcopy(i.APL_RUNTIME_REVIEW)))
            yield SimpleNamespace(root=root,packet=packet,originals=originals,state=state,deps=deps,args=args,run=run,tool=tool)


class Transaction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidates=t.candidates()
        cls.candidates['uiua-fann']=f.candidate()

    def unchanged(self, value):
        for name,raw in value.originals.items():
            self.assertEqual((value.root/name).read_bytes() if (value.root/name).exists() else None, raw)

    def test_four_cohort_preview_apply_and_exact_registry(self):
        for cohort,candidate in self.candidates.items():
            with self.subTest(cohort=cohort), fixture(cohort,candidate) as value:
                preview=value.run(value.args())
                self.unchanged(value)
                self.assertFalse((value.packet/'apply/SUCCESS.json').exists())
                self.assertEqual(preview['originals'][i.HISTORY],i.ABSENT)
                proposed=json.loads((value.packet/'preview/after'/i.HISTORY).read_bytes())
                self.assertEqual(proposed['admissions'][-1]['success'],preview['proposed_apply'])
                result=value.run(value.args('apply',preview))
                self.assertTrue(value.state['closed'])
                self.assertEqual(result['status'],'applied')
                self.assertNotIn(i.HISTORY,result['prepared'])
                self.assertEqual(i.sha((value.packet/'apply/SUCCESS.json').read_bytes()),preview['proposed_apply']['sha256'])
                self.assertEqual(i.sha((value.root/i.HISTORY).read_bytes()),preview['prepared'][i.HISTORY])

    def test_existing_empty_registry_is_distinct_from_absence(self):
        with fixture('r',self.candidates['r'],existing_history=True) as value:
            preview=value.run(value.args())
            self.assertNotEqual(preview['originals'][i.HISTORY],i.ABSENT)
            value.run(value.args('apply',preview))

    def test_each_reviewed_digest_is_enforced_before_any_install(self):
        for field in ('catalog','languages','history','prepared_catalog','prepared_languages','prepared_history'):
            with self.subTest(field=field), fixture('r',self.candidates['r']) as value:
                preview=value.run(value.args())
                args=value.args('apply',preview)
                setattr(args,'expected_'+field+'_sha256','0'*64)
                with self.assertRaisesRegex(ValueError,'reviewed preview'):
                    value.run(args)
                self.unchanged(value)
                self.assertFalse((value.packet/'apply/SUCCESS.json').exists())

    def test_future_apply_path_is_bound_by_prepared_registry(self):
        with fixture('r',self.candidates['r']) as value:
            preview=value.run(value.args())
            with self.assertRaisesRegex(ValueError,'Prepared bytes'):
                value.run(value.args('apply',preview,output=value.packet/'different-apply'))
            self.unchanged(value)

    def test_late_pin_replay_catalog_mutation_restores_all_other_targets(self):
        with fixture('r',self.candidates['r']) as value:
            preview=value.run(value.args())
            value.state['mutation']=lambda:(value.root/i.CATALOGS[0]).write_bytes(b'external edit')
            with self.assertRaises(ValueError):
                value.run(value.args('apply',preview))
            self.assertEqual((value.root/i.CATALOGS[0]).read_bytes(),b'external edit')
            self.assertEqual((value.root/i.CATALOGS[1]).read_bytes(),value.originals[i.CATALOGS[1]])
            self.assertFalse((value.root/i.HISTORY).exists())
            self.assertFalse((value.packet/'apply/SUCCESS.json').exists())
            self.assertTrue((value.packet/'apply/before'/i.CATALOGS[0]).exists())

    def test_late_owned_success_mutation_preserves_external_bytes_but_rolls_back(self):
        with fixture('r',self.candidates['r']) as value:
            preview=value.run(value.args())
            receipt=value.packet/'apply/SUCCESS.json'
            value.state['mutation']=lambda:receipt.write_bytes(b'external receipt')
            with self.assertRaises(ValueError):
                value.run(value.args('apply',preview))
            self.unchanged(value)
            self.assertEqual(receipt.read_bytes(),b'external receipt')

    def test_late_consumer_source_mutation_rolls_back(self):
        with fixture('r',self.candidates['r']) as value:
            preview=value.run(value.args())
            value.state['mutation']=lambda:value.tool.write_bytes(b'changed source')
            with self.assertRaisesRegex(ValueError,'Pinned input'):
                value.run(value.args('apply',preview))
            self.unchanged(value)
            self.assertFalse((value.packet/'apply/SUCCESS.json').exists())

    def test_final_history_validation_failure_removes_applied_receipt(self):
        with fixture('r',self.candidates['r']) as value:
            preview=value.run(value.args())
            value.state['historical_fault']=True
            with self.assertRaisesRegex(ValueError,'history failure'):
                value.run(value.args('apply',preview))
            self.unchanged(value)
            self.assertFalse((value.packet/'apply/SUCCESS.json').exists())

    def test_source_change_during_final_history_read_is_checked_afterward(self):
        with fixture('r',self.candidates['r']) as value:
            preview=value.run(value.args())
            value.state['history_mutation']=lambda:value.tool.write_bytes(b'changed during final history')
            with self.assertRaisesRegex(ValueError,'Pinned input'):
                value.run(value.args('apply',preview))
            self.unchanged(value)
            self.assertFalse((value.packet/'apply/SUCCESS.json').exists())

    def test_registry_install_failure_rolls_back_first_two_catalogs(self):
        with fixture('r',self.candidates['r']) as value:
            preview=value.run(value.args())
            replace=Path.replace
            def fail_history(path,target):
                if str(path).endswith('normalization-history.json.retained-admission.tmp'):
                    raise OSError('injected registry rename failure')
                return replace(path,target)
            with patch.object(Path,'replace',fail_history),self.assertRaisesRegex(OSError,'rename failure'):
                value.run(value.args('apply',preview))
            self.unchanged(value)
            self.assertFalse((value.packet/'apply/SUCCESS.json').exists())

    def test_interruption_immediately_after_install_rename_is_journaled(self):
        with fixture('r',self.candidates['r']) as value:
            preview=value.run(value.args())
            replace=Path.replace
            def interrupted(path,target):
                result=replace(path,target)
                if str(path).endswith('benchmarks.json.retained-admission.tmp'):
                    raise KeyboardInterrupt('injected after rename')
                return result
            with patch.object(Path,'replace',interrupted),self.assertRaises(KeyboardInterrupt):
                value.run(value.args('apply',preview))
            self.unchanged(value)
            self.assertFalse((value.packet/'apply/SUCCESS.json').exists())

    def test_interrupted_rollback_can_acknowledge_already_restored_inode(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();(root/'data').mkdir()
            originals={name:(None if name==i.HISTORY else b'original') for name in i.TARGETS}
            prepared={name:b'prepared' for name in i.TARGETS};identities={}
            for name,raw in originals.items():
                if raw is not None:(root/name).write_bytes(raw)
                _,identities[name]=i.snapshot(root/name,optional=True)
            journal=i.Journal(root,w,originals,identities,prepared);journal.apply()
            replace=Path.replace;interrupted=False
            def interrupt_once(path,target):
                nonlocal interrupted
                result=replace(path,target)
                if not interrupted and str(path).endswith('.retained-rollback.tmp'):
                    interrupted=True
                    raise KeyboardInterrupt('injected rollback acknowledgement gap')
                return result
            with patch.object(Path,'replace',interrupt_once),self.assertRaises(ValueError):journal.rollback()
            journal.rollback()
            self.assertEqual(journal.installed,{})
            for name,raw in originals.items():
                self.assertEqual((root/name).read_bytes() if (root/name).exists() else None,raw)

    def test_replaced_inode_with_equal_bytes_is_not_overwritten_in_cleanup(self):
        with fixture('r',self.candidates['r']) as value:
            preview=value.run(value.args())
            def replacement():
                path=value.root/i.CATALOGS[0]
                tmp=path.with_name('external.tmp');tmp.write_bytes(path.read_bytes());tmp.replace(path)
            value.state['mutation']=replacement
            with self.assertRaises(ValueError):
                value.run(value.args('apply',preview))
            self.assertEqual(i.sha((value.root/i.CATALOGS[0]).read_bytes()),preview['prepared'][i.CATALOGS[0]])
            self.assertEqual((value.root/i.CATALOGS[1]).read_bytes(),value.originals[i.CATALOGS[1]])
            self.assertFalse((value.root/i.HISTORY).exists())
            self.assertFalse((value.packet/'apply/SUCCESS.json').exists())

    def test_preview_late_change_is_detected_without_overwriting_external_catalog(self):
        with fixture('r',self.candidates['r']) as value:
            value.state['mutation']=lambda:(value.root/i.CATALOGS[0]).write_bytes(b'external')
            with self.assertRaises(ValueError):
                value.run(value.args())
            self.assertFalse((value.packet/'preview/SUCCESS.json').exists())
            self.assertEqual((value.root/i.CATALOGS[0]).read_bytes(),b'external')


class CandidateRouting(unittest.TestCase):
    def test_four_frozen_export_annotation_shapes_and_tamper_rejection(self):
        for cohort,spec in i.COHORTS.items():
            with self.subTest(cohort=cohort),tempfile.TemporaryDirectory() as directory:
                root=Path(directory).resolve();packet=root/spec['packet'];packet.mkdir(parents=True)
                source=b'exact source\n';digest=i.sha(source);source_path=packet/'source';source_path.write_bytes(source)
                review=dict(canonical_counts={'key':dict(source=dict(path=source_path.relative_to(root).as_posix(),sha256=digest))},
                    profiles={'key':dict(original_profile=dict(source=str(source_path)),source_sha256=digest)},
                    source_counts={v:dict(source_sha256=digest) for v in ('compact','fast')})
                for variant in ('compact','fast'):
                    (packet/'sources').mkdir(exist_ok=True);(packet/'sources'/(variant+'.ua')).write_bytes(source)
                review_path=packet/'reconciliation.json';review_path.write_bytes(i.encoded(review))
                source_review=packet/'source-review.json';source_review.write_bytes(b'{}')
                base=dict(schema='fixture-export',original_runtime_flag=False)
                expected=copy.deepcopy(base)
                expected['reconciliation']=dict(path=review_path.relative_to(root).as_posix(),sha256=i.sha(review_path.read_bytes()))
                if cohort in ('r','apl'):
                    expected['exporter']=dict(path='tools/qualification/'+spec['exporter'],sha256=spec['exporter_sha'])
                elif cohort=='uiua':
                    expected['independent_source_review']=dict(path=source_review.relative_to(root).as_posix(),sha256=i.sha(b'{}'))
                    expected['consumer_sources']=dict(exporter=dict(path='tools/qualification/'+spec['exporter'],sha256=spec['exporter_sha']),
                        reconciler=dict(path='tools/qualification/'+spec['reconciler'],sha256=spec['reconciler_sha']))
                else:
                    expected['consumer_sources']=dict(driver=dict(path='tools/qualification/import_uiua_fann.py',sha256=i.WRITER_SHA),
                        reconciler=dict(path='tools/qualification/uiua_fann_reconcile.py',sha256=spec['reconciler_sha']),
                        publication=dict(path='tools/qualification/uiua_fann_publication.py',sha256=i.FANN_PUBLICATION_SHA))
                candidate_path=packet/'candidate.json';candidate_path.write_bytes(i.encoded(expected))
                deps=dict(spec=spec,reconciler=SimpleNamespace(COUNTS=('key',),ARCHIVE=packet,
                    metadata=lambda:({},dict(counts={},report={}),{},{'key':source})),
                    exporter=SimpleNamespace(REVIEW=source_review,REVIEW_SHA=i.sha(b'{}'),build_candidate=lambda *_:copy.deepcopy(base)),
                    publication=SimpleNamespace(build_candidate=lambda *_:copy.deepcopy(base)),normalization=n)
                args=SimpleNamespace(cohort=cohort,candidate=candidate_path,candidate_sha256=i.sha(candidate_path.read_bytes()))
                with patch.object(i,'ROOT',root):
                    self.assertEqual(i.reproduce(args,deps,review,i.checked),expected)
                    altered=copy.deepcopy(expected);altered['original_runtime_flag']=True
                    candidate_path.write_bytes(i.encoded(altered));args.candidate_sha256=i.sha(candidate_path.read_bytes())
                    with self.assertRaisesRegex(ValueError,'frozen export'):
                        i.reproduce(args,deps,review,i.checked)

    def test_apl_later_static_runtime_scope_binds_actual_saved_metadata(self):
        apl=load('retained_runtime_fixture',HERE/'test_apl_retained_export.py')
        apl.Candidate.setUpClass()
        candidate=apl.Candidate().build()
        review=copy.deepcopy(apl.Candidate.review)
        approval=json.loads((i.ROOT/i.APL_RUNTIME_REVIEW['path']).read_bytes())
        review['verified_file_pins']=copy.deepcopy(approval['required_inherited_pins'])
        expected=copy.deepcopy(candidate)
        self.assertEqual(i.validate_apl_runtime(candidate,review,i.checked,n),i.APL_RUNTIME_REVIEW)
        self.assertEqual(candidate,expected)
        for fault in ('command','source','runtime','scope_flag','missing_pin'):
            altered=copy.deepcopy(candidate);closed=copy.deepcopy(review)
            key=next(iter(altered['program_inventory']))
            row=altered['program_inventory'][key]
            if fault=='command':row['runtime_arguments'].append('extra')
            elif fault=='source':row['source_sha256']='0'*64
            elif fault=='runtime':row['runtime']['version']='unqualified runtime'
            elif fault=='scope_flag':row['runtime_publication_metadata_qualified']=True
            else:closed['verified_file_pins'].pop(next(iter(closed['verified_file_pins'])))
            with self.subTest(fault=fault),self.assertRaises(ValueError):
                i.validate_apl_runtime(altered,closed,i.checked,n)


if __name__=='__main__':
    unittest.main()
