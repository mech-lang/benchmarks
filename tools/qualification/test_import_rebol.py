"""Synthetic append-only and held-transaction faults; no actual file phase."""
import copy
from contextlib import contextmanager
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
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


HERE=Path(__file__).resolve().parent
m=load('rebol_import_tests',HERE/'import_rebol.py')
x=load('rebol_import_export_fixture',HERE/'test_rebol_export.py')
e=x.e


def fixture(failed=None):
    r,plan,review,metadata,read_raw,content=x.fixture(failed)
    def add(path,raw):
        content[str(path)]=raw;return dict(path=str(path),sha256=m.digest(raw))
    plan['timing_policy']='Synthetic fresh-process boundary'
    plan['qualification']['lease_identities']=[]
    review['qualification']['lease_identities']=[]
    plan_ref=add(e.ROOT/'synthetic/plan.json',e.encoded(plan))
    review['plan']=plan_ref;review['verified_file_pins']=copy.deepcopy(review['verified_file_pins'])
    review['verified_file_pins'][plan_ref['path']]=plan_ref['sha256']
    review['report']=add(e.ROOT/'synthetic/report.json',b'{}\n')
    review['terminal']=add(e.ROOT/'synthetic/terminal.json',b'{}\n')
    review['source_evidence']['work']=copy.deepcopy(review['source_evidence']['counts'])
    metadata.update(color='#345678',runtime_policy='Synthetic interpreted runtime',memory_policy='Synthetic tracing GC')
    release=dict(schema='rebol-publication-release-metadata-v1',status='independently-reviewed-release-metadata',
        independent_review=True,language='rebol3',family='rebol',chart_admission=False,release_year=1997,
        release_name='Synthetic release evidence',release_source='https://example.invalid/release',
        release_note='Synthetic fixture, not a publication disposition',reviewed_on='2026-01-01',
        evidence=copy.deepcopy(metadata['evidence']))
    references=dict(plan=plan_ref,reconciliation=add(e.ROOT/'synthetic/reconciliation.json',e.encoded(review)),
        metadata=add(e.ROOT/'synthetic/metadata-review.json',e.encoded(metadata)),
        release=add(e.ROOT/'synthetic/release-review.json',m.encoded(release)))
    references['import_source_review']=add(e.ROOT/'synthetic/import-source-review.json',b'import-review')
    references['import_controller']=add(Path(m.__file__),b'synthetic-reviewed-importer')
    export_source=add(e.ROOT/'synthetic/export-source-review.json',b'export-review')
    export_controller=add(Path(e.__file__),b'synthetic-reviewed-exporter')
    add(e.RECONCILER,b'synthetic-reviewed-reconciler')
    candidate=e.build_candidate(r,plan,review,metadata,read_raw)
    candidate.update(reconciliation=references['reconciliation'],metadata_review=references['metadata'],
        export_source_review=export_source,export_controller=export_controller)
    references['candidate']=add(e.ROOT/'synthetic/candidate.json',e.encoded(candidate))
    # Match the exact insertion order of the publication CLI's reference map.
    references={key:references[key] for key in ('candidate','reconciliation','plan','metadata','release',
                                              'import_source_review','import_controller')}
    old_source=dict(code='old\n',sha256='old',path='old.reb',preserved_metadata='keep')
    data=dict(repository=dict(url='https://example.invalid/repository'),languages=[dict(key='old',label='Old')],
        benchmarks=[dict(key=b,baseline_loc=1,baseline_seconds=1,groups=[dict(language='old',fast=b+':old')]) for b in e.BENCHES],
        files={'old':old_source},archive_paths={'old.reb':'old.reb'},programs={},program_inventory={},
        reference_summary=[dict(lang='old',label='Old',measured_benchmarks=[])],formatted_reference_summary=[],
        protocol={'old':'unchanged'},language_groups=[dict(key='interpreted',languages=['old']),dict(key='functional',languages=[])],
        unrelated=dict(exact='value'))
    for b in e.BENCHES:
        row=dict(key=b+':old',id='old',language='old',files=['old'],seconds=1,loc=1,x=1,y=1)
        data['programs'][row['key']]=copy.deepcopy(row);data['program_inventory'][row['key']]=copy.deepcopy(row)
    languages=dict(languages={'old':dict(note='preserve')},audited_on='2025-01-01',scope='prior')
    originals={m.TARGETS[0]:m.encoded(data),m.TARGETS[1]:m.encoded(languages),
        m.TARGETS[2]:b'// Test metadata\nexport const languageMetadata = {"old":{"note":"preserve"}};\n'}
    return SimpleNamespace(r=r,plan=plan,review=review,metadata=metadata,release=release,candidate=candidate,
        refs=references,export_source=export_source,content=content,originals=originals,data=data)


@contextmanager
def publish_fixture(*,apply=True,late=None):
    f=fixture();old=m.load_transaction()
    with tempfile.TemporaryDirectory() as temporary:
        base=Path(temporary).resolve();publication=base/'publication';publication.mkdir()
        for name,raw in f.originals.items():
            path=publication/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        job=base/'job';job.mkdir();(job/'owner.lock').touch();suite=base/'suite.lock';suite.touch()
        common=base/'common.lock';common.touch();f.r.SUITE=suite
        f.review['qualification']['lease_identities']=[]
        # The saved reconciliation must reflect exactly the yielded fixture.
        f.content[f.refs['reconciliation']['path']]=e.encoded(f.review)
        f.refs['reconciliation']['sha256']=m.digest(f.content[f.refs['reconciliation']['path']])
        f.candidate['reconciliation']=copy.deepcopy(f.refs['reconciliation'])
        f.content[f.refs['candidate']['path']]=e.encoded(f.candidate)
        f.refs['candidate']['sha256']=m.digest(f.content[f.refs['candidate']['path']])
        args=SimpleNamespace(publication_root=publication,output=base/'private-output',apply=apply,durable_directory=job,
            source_review=Path(f.refs['import_source_review']['path']),source_review_sha256=f.refs['import_source_review']['sha256'],
            export_source_review=Path(f.export_source['path']),export_source_review_sha256=f.export_source['sha256'])
        for key in ('candidate','reconciliation','plan','metadata','release'):
            setattr(args,key,Path(f.refs[key]['path']));setattr(args,key+'_sha256',f.refs[key]['sha256'])
        prepared,_,_=m.build_publication(f.originals,f.candidate,f.release,f.refs,f.plan)
        for label,name in zip(('benchmarks','languages','module'),m.TARGETS):
            setattr(args,label+'_sha256',m.digest(f.originals[name]))
            setattr(args,'prepared_'+label+'_sha256',m.digest(prepared[name]) if apply else None)
        own_pins={str(Path(m.__file__)):f.refs['import_controller']['sha256'],
            f.refs['import_source_review']['path']:f.refs['import_source_review']['sha256'],
            str(e.EXPORTER) if hasattr(e,'EXPORTER') else str(Path(e.__file__)):f.candidate['export_controller']['sha256']}
        export_pins={str(e.RECONCILER):m.digest(f.content[str(e.RECONCILER)]),
            str(Path(e.__file__)):f.candidate['export_controller']['sha256'],f.export_source['path']:f.export_source['sha256']}
        actual_checked=m.checked;actual_lease_stat=m.lease_stat;events=[]
        def checked(path,sha):
            if str(path) in f.content:
                raw=f.content[str(path)];m.require(m.digest(raw)==sha,'Synthetic pinned bytes differ');return raw
            return actual_checked(path,sha)
        def lease_stat(path):
            return SimpleNamespace(st_dev=1,st_ino=79859134) if Path(path)==m.COMMON else actual_lease_stat(path)
        def export_context(unused,*,final_consumer_check,on_exit_failure):
            @contextmanager
            def held():
                events.append('held')
                try:
                    yield f.review
                    if late:late(f,args)
                    final_consumer_check()
                except BaseException:
                    events.append('cleanup-held');on_exit_failure();raise
                finally:events.append('released')
            return f.r,export_pins,held()
        with patch.object(m,'source_intake',return_value=(e,old,own_pins)),patch.object(m,'checked',side_effect=checked), \
             patch.object(m,'lease_stat',side_effect=lease_stat),patch.object(m,'verify_links'), \
             patch.object(e,'export_context',side_effect=export_context):
            yield f,args,old,events,prepared


class ImportTests(unittest.TestCase):
    def test_append_only_twenty_forms_and_fifteen_physical_paths(self):
        f=fixture();prepared,audit,links=m.build_publication(f.originals,f.candidate,f.release,f.refs,f.plan)
        data=json.loads(prepared[m.TARGETS[0]])
        self.assertEqual(audit['imported_program_inventory'],20)
        self.assertEqual(len(data['program_inventory'])-len(f.data['program_inventory']),20)
        self.assertEqual(data['reference_summary'][0],f.data['reference_summary'][0])
        self.assertEqual(data['files']['old'],f.data['files']['old'])
        self.assertEqual(len({role['source_path'] for row in f.candidate['program_inventory'].values() for role in row['file_roles'].values()}),15)
        self.assertTrue(all(v['formatted_x'] is None for v in data['program_inventory'].values() if v['language']=='rebol3'))
        self.assertFalse(audit['baseline_changed']);self.assertTrue(links)

    def test_failed_subject_and_failed_control_preserve_raw_and_exclude(self):
        for identity in ('rebol-pidigits-compact','pidigits:rebol-full-study:mech-control'):
            f=fixture(identity);prepared,_,_=m.build_publication(f.originals,f.candidate,f.release,f.refs,f.plan)
            data=json.loads(prepared[m.TARGETS[0]])
            row=data['program_inventory']['pidigits:rebol-pidigits-compact']
            self.assertFalse(row['eligible_for_chart']);self.assertIsNone(row['x']);self.assertIsNone(row['y'])
            self.assertIsNone(row['time_ratio_to_matched_mech'])
            self.assertEqual(row['sample_execution_metadata'],m.public_values(f.candidate['program_inventory'][row['key']]['sample_execution_metadata'],{}))
            if identity.endswith('mech-control'):
                self.assertNotIn('pidigits',data['languages'][-1]['timed_benchmarks'])

    def test_new_minimum_rejects_without_rebase(self):
        for field in ('baseline_loc','baseline_seconds'):
            f=fixture();changed=copy.deepcopy(f.data);changed['benchmarks'][0][field]=1000
            f.originals[m.TARGETS[0]]=m.encoded(changed)
            with self.assertRaisesRegex(AssertionError,'minimum'):m.build_publication(f.originals,f.candidate,f.release,f.refs,f.plan)

    def test_public_links_preserve_physical_images_and_historical_control_namespace(self):
        f=fixture();control=f.candidate['matched_mech_controls']['pidigits']
        control['original_profile']=dict(algorithm=dict(evidence=['../../hosts/gpu/src/control/runtime.rs']))
        physical=f.candidate['qualified_runtime'];image=f.candidate['program_inventory']['pidigits:rebol-pidigits-compact']['extension_image']
        public,_,links=m.public_candidate(f.candidate,f.refs)
        self.assertEqual(public['qualified_runtime'],physical)
        self.assertEqual(public['program_inventory']['pidigits:rebol-pidigits-compact']['extension_image'],image)
        self.assertEqual(public['matched_mech_controls']['pidigits']['original_profile'],control['original_profile'])
        self.assertNotIn(Path(image['path']).relative_to(m.ROOT).as_posix(),links)

    def test_release_requires_review_without_guessing_language_year(self):
        f=fixture()
        for change in (dict(independent_review=False),dict(status='draft'),dict(release_year=True),dict(evidence={})):
            with self.assertRaises(AssertionError):m.release_contract(dict(f.release,**change),f.metadata)

    def test_existing_same_digest_source_metadata_is_preserved(self):
        f=fixture();sha,source=next(iter(f.candidate['files'].items()))
        existing=dict(code=source['code'],sha256=sha,path='prior-canonical-path',retained_note='preserve')
        f.data['files'][sha]=existing;f.originals[m.TARGETS[0]]=m.encoded(f.data)
        prepared,_,_=m.build_publication(f.originals,f.candidate,f.release,f.refs,f.plan)
        self.assertEqual(json.loads(prepared[m.TARGETS[0]])['files'][sha],existing)

    def test_actual_publish_preview_then_apply_exact_outputs(self):
        for apply in (False,True):
            with publish_fixture(apply=apply) as (f,args,old,events,prepared):
                receipt=m.publish(args);self.assertIs(receipt['applied'],apply)
                for name in m.TARGETS:
                    self.assertEqual((args.publication_root/name).read_bytes(),prepared[name] if apply else f.originals[name])
                    self.assertEqual((args.output/name).read_bytes(),prepared[name])
                self.assertEqual(events,['held','released'])

    def test_changed_preview_or_target_rejects_before_writes(self):
        for fault in ('preview','target'):
            with publish_fixture() as (f,args,old,events,prepared):
                if fault=='preview':args.prepared_benchmarks_sha256='0'*64
                else:(args.publication_root/m.TARGETS[0]).write_bytes(b'externally changed')
                with self.assertRaises(AssertionError):m.publish(args)
                self.assertFalse(args.output.exists())
                if fault=='target':self.assertEqual((args.publication_root/m.TARGETS[0]).read_bytes(),b'externally changed')

    def test_late_context_pin_failure_restores_before_unlock(self):
        def late(f,args):f.content[f.refs['metadata']['path']]=b'changed source evidence'
        with publish_fixture(late=late) as (f,args,old,events,prepared):
            with self.assertRaises(AssertionError):m.publish(args)
            self.assertEqual(events,['held','cleanup-held','released'])
            self.assertFalse(args.output.exists())
            for name in m.TARGETS:self.assertEqual((args.publication_root/name).read_bytes(),f.originals[name])

    def test_receipt_write_return_gap_does_not_leave_applied_receipt(self):
        with publish_fixture() as (f,args,old,events,prepared):
            write=old.write_private
            def interrupted(path,raw,owned):
                write(path,raw,owned)
                if path.name=='import-receipt.json':raise KeyboardInterrupt('after receipt write')
            with patch.object(old,'write_private',side_effect=interrupted),self.assertRaises(KeyboardInterrupt):m.publish(args)
            self.assertFalse(args.output.exists())
            for name in m.TARGETS:self.assertEqual((args.publication_root/name).read_bytes(),f.originals[name])

    def test_post_rename_interruption_restores_all_targets(self):
        with publish_fixture() as (f,args,old,events,prepared):
            replace=Path.replace;injected=[]
            def interrupted(path,target):
                result=replace(path,target)
                if str(path).endswith('.typescript-import.tmp') and not injected:
                    injected.append(True);raise KeyboardInterrupt('after replacement')
                return result
            with patch.object(Path,'replace',interrupted),self.assertRaises(KeyboardInterrupt):m.publish(args)
            for name in m.TARGETS:self.assertEqual((args.publication_root/name).read_bytes(),f.originals[name])
            self.assertFalse(args.output.exists())

    def test_borrowed_apply_and_restore_intervals_are_masked(self):
        with publish_fixture() as (f,args,old,events,prepared):
            level=[0];apply=old.apply_prepared;restore=old.rollback_publication;seen=[]
            @contextmanager
            def masked():
                level[0]+=1
                try:yield
                finally:level[0]-=1
            def stopped(*values):
                self.assertGreater(level[0],0);apply(*values);seen.append('applied')
                raise KeyboardInterrupt('after borrowed apply returned')
            def restored(*values):
                self.assertGreater(level[0],0);seen.append('restore');return restore(*values)
            with patch.object(m,'atomic',side_effect=masked),patch.object(old,'apply_prepared',side_effect=stopped), \
                 patch.object(old,'rollback_publication',side_effect=restored),self.assertRaises(KeyboardInterrupt):m.publish(args)
            self.assertEqual(seen,['applied','restore'])
            for name in m.TARGETS:self.assertEqual((args.publication_root/name).read_bytes(),f.originals[name])
            self.assertFalse(args.output.exists())

    def test_special_file_rejected_before_open_and_external_output_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();fifo=root/'fifo';os.mkfifo(fifo)
            with patch.object(m.os,'open',side_effect=AssertionError('must not open')):
                with self.assertRaisesRegex(AssertionError,'Regular'):m.read_bytes(fifo)
            safe=root/'safe';safe.write_bytes(b'safe');changed=root/'changed';changed.write_bytes(b'new')
            files={p:dict(identity=(p.stat().st_dev,p.stat().st_ino),raw=raw,complete=True) for p,raw in ((safe,b'safe'),(changed,b'old'))}
            with self.assertRaises(BaseExceptionGroup):m.restore_owned(files,{})
            self.assertFalse(safe.exists());self.assertEqual(changed.read_bytes(),b'new')
            changed.write_bytes(b'prefix')
            record=dict(identity=(changed.stat().st_dev,changed.stat().st_ino),raw=b'prefix-and-rest',complete=True)
            with self.assertRaises(BaseExceptionGroup):m.restore_owned({changed:record},{})
            self.assertEqual(changed.read_bytes(),b'prefix')

    def test_only_retained_common_alias_and_inode_are_accepted(self):
        info=SimpleNamespace(st_mode=0o100600,st_dev=1,st_ino=79859134)
        with patch.object(Path,'resolve',return_value=m.COMMON_RESOLVED),patch.object(Path,'lstat',return_value=info), \
             patch.object(m,'physical',return_value=m.COMMON_RESOLVED):
            self.assertIs(m.lease_stat(m.COMMON),info)
            m.named_leases({m.COMMON:(1,79859134)})
            with self.assertRaises(AssertionError):m.named_leases({m.COMMON:(1,99)})
        with patch.object(Path,'resolve',return_value=Path('/other/lock')),self.assertRaisesRegex(AssertionError,'alias'):
            m.lease_stat(m.COMMON)

    def test_copied_link_mismatch_and_overlapping_roots_reject(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();original=root/'evidence';publication=root/'publication';original.mkdir();publication.mkdir()
            (original/'receipt').write_bytes(b'original');(publication/'receipt').write_bytes(b'changed')
            with patch.object(m,'ROOT',original),self.assertRaises(AssertionError):
                m.verify_links({'receipt':m.digest(b'original')},publication)
        with self.assertRaises(AssertionError):m.destination(m.ROOT)

    def test_frozen_transaction_source_requires_exact_function_inventory(self):
        with patch.object(m,'checked',return_value=b'def apply_prepared(): pass\n'),self.assertRaisesRegex(AssertionError,'inventory'):
            m.load_transaction()


if __name__=='__main__':unittest.main()
