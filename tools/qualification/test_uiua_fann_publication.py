"""Raw-measurement preservation, x-best normalization and output ownership."""
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


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name,HERE/filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


p = load('uiua_publication_test','uiua_fann_publication.py')
i = load('uiua_import_test','import_uiua_fann.py')
t = load('uiua_reconcile_fixture','test_uiua_fann_reconcile.py')


def candidate():
    values = t.fixture()
    with t.r.helper_modules() as modules:
        review = t.r.reconcile(**values,modules=modules)
    review.update(file_integrity_verified=True,common_mutex_held=True,
        report=dict(path=str(t.r.ARCHIVE/'full-study/report.json'),sha256=t.r.REPORT_SHA),
        manifest=dict(path=str(t.r.ARCHIVE/'full-study/manifest.json'),sha256=t.r.MANIFEST_SHA),
        source_owner_review=dict(path=str(t.r.OWNER_REVIEW),sha256=t.r.OWNER_REVIEW_SHA),
        independent_source_approval=dict(path=str(t.r.SOURCE_APPROVAL),sha256=t.r.SOURCE_APPROVAL_SHA),
        prior_independent_reconciliation=dict(path=str(t.r.PRIOR_REVIEW),sha256=t.r.PRIOR_REVIEW_SHA),
        source_candidate_archive=dict(path=str(t.r.ARCHIVE/'manifest.json'),sha256=t.r.RETAINED_CANDIDATE_SHA,
            original_sealed_sha256=t.r.CANDIDATE_SHA,documentation_only_changed_fields=['migration_policy']))
    return p.build_candidate(review,values['source_bytes'])


def catalog():
    shape=json.loads((p.ROOT/'experiments/uiua/fann-v5-publication-v1/prior-uiua-catalog-shape.json').read_text())
    rows={key:copy.deepcopy(row) for b in shape['benchmarks'] for key,row in b['rows'].items()}
    benches=[{k:copy.deepcopy(v) for k,v in b.items() if k!='rows'} for b in shape['benchmarks']]
    for bench in benches:
        if bench['key'] not in ('nbody','fannkuchredux'):continue
        key=bench['key']+':c-example'
        loc=bench['baseline_loc']
        row=dict(key=key,id='c-example',language='c',benchmark=bench['key'],loc=loc,physical_loc=loc,
            seconds=bench['baseline_seconds']*2,samples=[1.9,2,2.1],x=1,y=2,
            original_receipt={'path':'unchanged','sha256':'original'},files=['old'])
        row['publication_record']=copy.deepcopy(row)
        rows[key]=row
        bench['groups'].append(dict(language='c',label='C',programs=[key],fast=key,small=key))
    data=dict(programs=rows,program_inventory=copy.deepcopy(rows),benchmarks=benches,
        files={'old':{'code':'unchanged','name':'old.c'}},archive_paths={},
        languages=copy.deepcopy(shape['language'])+[dict(key='c',label='C')],
        reference_summary=[dict(lang='c',label='C',fast=dict(x=1,y=2),small=dict(x=1,y=2))],
        formatted_reference_summary=[dict(lang='c',fast=dict(x=1,y=2),small=dict(x=1,y=2))],
        repository=dict(url='https://gitlab.com/example/benchmarks'),
        original_audit={'preserve':True})
    languages=dict(languages={'uiua':dict(displayed_program_count=len(rows)-2,typing='dynamic'),
                              'c':dict(displayed_program_count=2,typing='static')})
    return data,languages


@contextmanager
def driver_fixture():
    """Small catalog and file-phase stand-in; no runtime closure is hashed."""
    c = candidate()
    review = dict(source_counts=c['source_counts'],fixture='closed retained evidence')
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        packet = root/'experiments/uiua/fann-v5-publication-v1'
        packet.mkdir(parents=True)
        tool = root/'tools/qualification/import_uiua_fann.py'
        tool.parent.mkdir(parents=True)
        tool.write_bytes(Path(i.__file__).read_bytes())
        publication = tool.with_name('uiua_fann_publication.py')
        publication.write_bytes(b'pure publication fixture')
        archive = root/'archive'
        (archive/'sources').mkdir(parents=True)
        for variant in ('compact','fast'):
            (archive/'sources'/(variant+'.ua')).write_bytes(t.fixture()['source_bytes'][variant])
        (root/'data').mkdir()
        data,languages=catalog()
        original = {i.TARGETS[0]:i.encoded(data),i.TARGETS[1]:i.encoded(languages)}
        for name,raw in original.items():(root/name).write_bytes(raw)
        state = dict(mutation=None,events=[])
        class Files:
            def verify(self,path,digest):i.checked(path,digest)
            def read(self,path,digest):return i.checked(path,digest)
        @contextmanager
        def review_context(tool_sha256,on_exit_failure=None,final_consumer_check=None):
            try:
                yield copy.deepcopy(review),Files()
                state['events'].append('pin-replay')
                if state['mutation'] is not None:state['mutation']()
                final_consumer_check()
                state['events'].append('closed')
            except BaseException:
                on_exit_failure()
                raise
        reconciler = SimpleNamespace(ARCHIVE=archive,strict_json=t.r.strict_json,same=t.r.same,
                                     review_context=review_context)
        transform = SimpleNamespace(build_candidate=lambda *_:copy.deepcopy(c),build_publication=p.build_publication)
        def execute(mode,output,exported=None,preview=None):
            args = SimpleNamespace(mode=mode,output=output,tool_sha256=i.sha(tool.read_bytes()),
                reconciler_sha256='0'*64,publication_sha256=i.sha(publication.read_bytes()),
                candidate=exported/'candidate.json' if exported else None,
                candidate_sha256=i.sha((exported/'candidate.json').read_bytes()) if exported else None,
                expected_catalog_sha256=preview['originals'][i.TARGETS[0]] if preview else None,
                expected_languages_sha256=preview['originals'][i.TARGETS[1]] if preview else None,
                expected_prepared_catalog_sha256=preview['prepared'][i.TARGETS[0]] if preview else None,
                expected_prepared_languages_sha256=preview['prepared'][i.TARGETS[1]] if preview else None)
            with redirect_stdout(io.StringIO()):return i.run(args)
        with ExitStack() as stack:
            stack.enter_context(patch.object(i,'ROOT',root))
            stack.enter_context(patch.object(i,'PACKET',packet))
            stack.enter_context(patch.object(i,'__file__',str(tool)))
            stack.enter_context(patch.object(i,'module',side_effect=lambda name,*_:reconciler if 'closed' in name else transform))
            yield root,packet,original,state,execute


class Publication(unittest.TestCase):
    def test_rebase_preserves_all_raw_measurements_and_formatted_axes(self):
        before, languages=catalog()
        after, meta, audit=p.build_publication(before,languages,candidate(),{'path':'candidate.json','sha256':'a'*64})
        self.assertEqual(next(b for b in after['benchmarks'] if b['key']=='fannkuchredux')['baseline_loc'],20)
        for pool in ('programs','program_inventory'):
            for key,row in before[pool].items():
                self.assertEqual(p.without_derived_x(row),p.without_derived_x(after[pool][key]))
                if row['benchmark']=='fannkuchredux':
                    self.assertEqual(after[pool][key]['x'],31/20)
                    self.assertEqual(after[pool][key]['publication_record']['x'],31/20)
                else:self.assertEqual(after[pool][key],row)
        self.assertEqual(after['formatted_reference_summary'],before['formatted_reference_summary'])
        self.assertEqual(after['reference_summary'][0]['fast']['y'],2)
        self.assertAlmostEqual(after['reference_summary'][0]['fast']['x'],(31/20)**.5)
        self.assertEqual(after['programs']['fannkuchredux:parallel-study:uiua-compact']['x'],1)
        self.assertEqual(after['programs']['fannkuchredux:parallel-study:uiua-fast']['x'],1.05)
        self.assertEqual(len(next(x for x in after['languages'] if x['key']=='uiua')['timed_benchmarks']),8)
        self.assertFalse(audit['normalization']['raw_source_counts_changed'])
        self.assertFalse(audit['normalization']['timing_samples_changed'])
        self.assertEqual(meta['languages']['c'],languages['languages']['c'])

    def test_unreviewed_baseline_or_existing_endpoint_rejected(self):
        for case in ('baseline','endpoint'):
            data,meta=catalog()
            bench=next(b for b in data['benchmarks'] if b['key']=='fannkuchredux')
            if case=='baseline':bench['baseline_loc']=30
            else:bench['groups'].append({'language':'uiua'})
            with self.assertRaises(ValueError):
                p.build_publication(data,meta,candidate(),{'path':'candidate.json','sha256':'a'*64})

    def test_changed_count_or_source_cannot_publish(self):
        for case in ('source','count'):
            c=candidate();data,meta=catalog()
            if case=='source':next(iter(c['files'].values()))['code']+='changed'
            else:next(iter(c['program_inventory'].values()))['loc']=19
            with self.assertRaises(ValueError):
                p.build_publication(data,meta,c,{'path':'candidate.json','sha256':'a'*64})

    def test_rollback_restores_other_target_despite_external_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'data').mkdir()
            old={name:b'old '+name.encode() for name in i.TARGETS}
            new={name:b'new '+name.encode() for name in i.TARGETS}
            for name in i.TARGETS:(root/name).write_bytes(new[name])
            (root/i.TARGETS[-1]).write_bytes(b'external')
            with self.assertRaisesRegex(ValueError,'externally changed'):
                i.rollback(root,old,new,list(i.TARGETS))
            self.assertEqual((root/i.TARGETS[0]).read_bytes(),old[i.TARGETS[0]])
            self.assertEqual((root/i.TARGETS[-1]).read_bytes(),b'external')

    def test_owned_writer_failure_and_later_external_truncation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'receipt';owner=i.OwnedFiles()
            with patch.object(i.os,'fsync',side_effect=OSError('flush failed')):
                with self.assertRaises(OSError):owner.write(path,b'full receipt')
            owner.remove_all()
            self.assertFalse(path.exists())
            owner.write(path,b'full receipt')
            path.write_bytes(b'full')
            with self.assertRaisesRegex(ValueError,'externally'):
                owner.remove_all()
            self.assertEqual(path.read_bytes(),b'full')

    def test_late_catalog_change_preserves_external_bytes_and_rolls_back_other_file(self):
        with driver_fixture() as (root,packet,original,state,execute):
            exported=packet/'export';execute('export',exported)
            preview=execute('preview',packet/'preview',exported)
            applied=packet/'apply'
            state['mutation']=lambda:(root/i.TARGETS[0]).write_bytes(b'external catalog')
            with self.assertRaisesRegex(ValueError,'externally changed catalog'):
                execute('apply',applied,exported,preview)
            self.assertEqual((root/i.TARGETS[0]).read_bytes(),b'external catalog')
            self.assertEqual((root/i.TARGETS[1]).read_bytes(),original[i.TARGETS[1]])
            self.assertFalse((applied/'SUCCESS.json').exists())
            self.assertTrue((applied/'before'/i.TARGETS[0]).is_file())
            self.assertEqual(state['events'][-1],'pin-replay')

    def test_late_output_change_rolls_back_catalog_and_removes_unchanged_success(self):
        with driver_fixture() as (root,packet,original,state,execute):
            exported=packet/'export';execute('export',exported)
            preview=execute('preview',packet/'preview',exported)
            applied=packet/'apply'
            changed=applied/'after'/i.TARGETS[0]
            state['mutation']=lambda:changed.write_bytes(b'external output')
            with self.assertRaisesRegex(ValueError,'externally'):
                execute('apply',applied,exported,preview)
            for name in i.TARGETS:self.assertEqual((root/name).read_bytes(),original[name])
            self.assertEqual(changed.read_bytes(),b'external output')
            self.assertFalse((applied/'SUCCESS.json').exists())
            self.assertEqual(state['events'][-1],'pin-replay')


if __name__=='__main__':unittest.main()
