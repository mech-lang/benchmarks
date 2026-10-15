"""Small synthetic publication faults; no runtime or evidence replay is invoked."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


p = load('apl_tree_pure',HERE/'apl_workspace_publication.py')
e = load('apl_tree_export',HERE/'apl_workspace_export.py')
n = load('apl_tree_history',ROOT/'tools/normalization_history_apl_trees.py')
i = load('apl_tree_import',HERE/'import_apl_workspace.py')


def reference(name):
    return dict(path=p.PACKET+'/synthetic-tests/'+name+'.json',sha256='a'*64)


def fixture():
    # Synthetic metadata is confined to this pure test; it is never saved as a
    # qualifying receipt or accepted by the physical reconciler.
    refs = {name:reference(name) for name in ('report','source_counts','source_work','reconciliation')}
    refs.update(runtime_metadata_basis=copy.deepcopy(p.RUNTIME_REF),consumer_sources={},
                native_cohort={name:reference(name) for name in ('plan','report','terminal','durable')})
    source_bytes = {digest:(ROOT/path).read_bytes() for path,digest,_,_ in p.BUNDLE}
    runtime = dict(schema='apl-retained-runtime-publication-scope-review-v1',runtime_publication_metadata_qualified=True,
        runtime=dict(path='/retained/bin/apl',sha256=p.RUNTIME_SHA),required_inherited_pins={})
    counts = dict(schema='apl-binarytrees-workspace-qualified-source-counts-v1',canonical_LOC_admitted=True,
        canonical_loc=41,physical_loc=41,formatted_loc=None,formatted_loc_qualified=False,setup_assignment_included=True,
        source_bundle=[dict(path=path,sha256=digest,canonical_loc=units,physical_loc=units)
                       for path,digest,_,units in p.BUNDLE])
    work = dict(schema='apl-binarytrees-workspace-required-work-v1',source_work_qualified=True,workload_n=21,
        source_sha256=p.SOURCE_SHA,setup_sha256=p.SETUP_SHA,workspace_scale=200,previous_failures_preserved=True,
        source_counts=refs['source_counts'])
    subject = dict(key=p.SUBJECT,language='apl',variant='compact',source_sha256=p.SOURCE_SHA,
        source='/retained/trees.apl',binary='/retained/run-apl.sh',binary_sha256=p.LAUNCHER_SHA,
        command=['/retained/run-apl.sh','--cc','1','-f',p.EVIDENCE_ROOT+'/'+p.SETUP,'-f','/retained/trees.apl','--','{n}'],
        runtime_binary=copy.deepcopy(runtime['runtime']),runtime_environment={'LC_ALL':'C'},maximum_workers=1,
        memory_policy='GNU APL workspace scale 200; unchanged allocator and garbage collection',
        loc=41,canonical_loc=41,physical_loc=41,setup_inside_timer=True,
        source_count_review=refs['source_counts'],required_work_review=refs['source_work'])
    profiles = {}
    for key,row,samples in ((p.SUBJECT,subject,[20.,21.,22.]),(p.CONTROL,dict(key=p.CONTROL,language='mech'),[1.,2.,3.])):
        profiles[key] = dict(original_profile=row,samples_seconds=samples,median_seconds=statistics.median(samples),
            sample_stdev_seconds=statistics.stdev(samples),sample_evidence=[{'attempt':i} for i in (1,2,3)],
            sample_execution_metadata=[{'fixture':i} for i in (1,2,3)],native_observations=3,full_workload_qualified=True)
    review = dict(schema='apl-workspace-independent-full6-reconciliation-v1',
        status='six-full-process-observations-file-verified-awaiting-publication',file_integrity_verified=True,
        common_mutex_held=True,chart_admission=False,profiles=profiles,verified_file_pins={},
        source_work_qualified=True,canonical_loc_qualified=True,actual_full_native_processes=6,
        subject_native_observations=3,control_native_observations=3,
        source_aliases=[dict(key=p.ALIAS,variant='optimized',source_alias_of=p.SUBJECT,timing_alias_of=p.SUBJECT,
                            additional_native_processes=0,optimization_claim=False)],
        preserved_failed_reports=copy.deepcopy(p.FAILED),references=copy.deepcopy(refs['native_cohort']),
        source_counts=refs['source_counts'],source_work=refs['source_work'],
        qualified_source_counts=copy.deepcopy(counts),qualified_source_work=copy.deepcopy(work))
    return review,source_bytes,counts,work,runtime,refs


def candidate():
    return p.build_candidate(*fixture())


def catalog(with_reference=True):
    workloads = ['binarytrees','nbody','fannkuchredux','fasta','knucleotide','mandelbrot','pidigits','regexredux','revcomp','spectralnorm']
    data = dict(repository={'url':'https://github.com/mech-lang/benchmarks'},benchmarks=[],programs={},program_inventory={},
        files={'old-source':{'code':'preserved'}},archive_paths={},formatted_reference_summary=[],
        languages=[dict(key='apl',timed_benchmarks=workloads[1:],source_benchmarks=workloads[1:])],reference_summary=[],
        apl_retained_publication_audit={'preserved':'older failure and source evidence'})
    for bench in workloads:
        groups = []
        for language,loc,seconds in [('other',15,1)]+([] if bench == 'binarytrees' else [('apl',50,10)]):
            key = bench+':old-'+language
            row = dict(key=key,benchmark=bench,language=language,loc=loc,seconds=seconds,
                samples=[seconds]*3,files=['old-source'],x=loc/15,y=seconds,eligible_for_chart=True)
            data['programs'][key] = copy.deepcopy(row)
            data['program_inventory'][key] = copy.deepcopy(row)
            groups.append(dict(language=language,fast=key,small=key,programs=[key]))
        data['benchmarks'].append(dict(key=bench,baseline_loc=15,baseline_seconds=1,groups=groups))
    if with_reference:
        data['reference_summary'].append(dict(lang='apl',label='APL (GNU APL)',measured_benchmarks=workloads[1:],
            fast={'x':50/15,'y':10},small={'x':50/15,'y':10}))
    return data,dict(languages={'apl':{'displayed_program_count':9,'note':'preserved taxonomy'}})


class Publication(unittest.TestCase):
    def test_two_counted_files_and_one_native_source(self):
        value = candidate()
        self.assertEqual(value['source_units'],41)
        self.assertEqual(value['program_inventory'][p.SUBJECT]['files'],[p.SOURCE_SHA,p.SETUP_SHA])
        self.assertEqual([r['native_observations'] for r in value['program_inventory'].values()],[3,0])
        self.assertEqual(value['program_inventory'][p.ALIAS]['timing_alias_of'],p.SUBJECT)

    def test_missing_setup_or_changed_count_rejects(self):
        for change in ('source','count','command'):
            values = list(fixture())
            if change == 'source':values[1].pop(p.SETUP_SHA)
            if change == 'count':values[2]['source_bundle'].pop()
            if change == 'command':values[0]['profiles'][p.SUBJECT]['original_profile']['command'].pop(4)
            with self.assertRaises(ValueError):p.build_candidate(*values)

    def test_alias_cannot_gain_a_sample_or_claim_an_optimization(self):
        for field,value in (('native_observations',3),('samples',[20.,21.,23.]),('distinct_optimization_claimed',True)):
            item = candidate();item['program_inventory'][p.ALIAS][field] = value
            with self.assertRaises(ValueError):p.validate_candidate(item)

    def test_nine_to_ten_preserves_old_rows_sources_evidence_and_baselines(self):
        before,languages = catalog();saved = copy.deepcopy(before);old_languages = copy.deepcopy(languages)
        after,updated,audit = p.build_publication(before,languages,candidate(),reference('candidate'))
        self.assertEqual(before,saved);self.assertEqual(languages,old_languages)
        for pool in ('programs','program_inventory','files'):
            self.assertTrue(all(after[pool][key] == value for key,value in before[pool].items()))
        self.assertEqual(after['apl_retained_publication_audit'],before['apl_retained_publication_audit'])
        self.assertEqual(audit['normalizations'],[])
        self.assertEqual(len(audit['aggregate_change']['before']['measured_benchmarks']),9)
        self.assertEqual(len(audit['aggregate_change']['after']['measured_benchmarks']),10)
        self.assertEqual(updated['languages']['apl']['displayed_program_count'],10)
        self.assertEqual(set(after['programs'])-set(before['programs']),{p.SUBJECT})
        self.assertEqual(set(after['program_inventory'])-set(before['program_inventory']),{p.SUBJECT,p.ALIAS})

    def test_absent_prior_partial_aggregate_is_not_fabricated(self):
        before,languages = catalog(False)
        _,_,audit = p.build_publication(before,languages,candidate(),reference('candidate'))
        self.assertIsNone(audit['aggregate_change']['before'])
        self.assertEqual(len(audit['aggregate_change']['after']['measured_benchmarks']),10)

    def test_new_minimum_or_existing_tree_is_not_silently_rebased(self):
        for change in ('loc','time','existing'):
            before,languages = catalog()
            tree = before['benchmarks'][0]
            if change == 'loc':tree['baseline_loc'] = 42
            if change == 'time':tree['baseline_seconds'] = 22
            if change == 'existing':tree['groups'].append(p.endpoint())
            with self.assertRaises(ValueError):p.build_publication(before,languages,candidate(),reference('candidate'))

    def test_different_runtime_or_unreplayed_dependency_rejects(self):
        for change in ('runtime','dependency'):
            values = list(fixture())
            if change == 'runtime':values[4]['runtime']['sha256'] = 'b'*64
            else:values[4]['required_inherited_pins']['/retained/extra.dylib'] = 'c'*64
            with self.assertRaises(ValueError):p.build_candidate(*values)

    def test_regular_guard_rejects_fifo_without_opening_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()/'fifo';os.mkfifo(path)
            with patch.object(e.os,'open',side_effect=AssertionError('must not open FIFO')):
                with self.assertRaisesRegex(ValueError,'Regular file required'):e.snapshot(path)

    def test_transaction_keeps_its_original_source_identity(self):
        seen = []
        target = SimpleNamespace(publish=lambda args:seen.append(args) or 'delegated')
        args = SimpleNamespace(cohort='apl-trees',adapter_sha256='b'*64)
        with patch.object(i,'dependencies',return_value=(target,e)):
            self.assertEqual(i.publish(args),'delegated')
        self.assertEqual(seen[0].adapter_sha256,i.TARGET_SHA)
        self.assertEqual(args.adapter_sha256,'b'*64)

    def test_control_algorithm_paths_are_not_mistaken_for_public_evidence(self):
        target = e.module(i.TARGET,i.TARGET_SHA)
        item = candidate()
        evidence = [dict(path='binarytrees/binarytrees-parallel.mec',sha256='b'*64),
                    dict(path='../../hosts/gpu/src/control/runtime.rs',sha256='c'*64)]
        item['matched_mech_controls']['binarytrees']['original_profile']['algorithm'] = {'evidence':evidence}
        rows = item['program_inventory']
        for row in rows.values():row['matched_mech_control']['original_profile']['algorithm'] = {'evidence':copy.deepcopy(evidence)}
        original = copy.deepcopy(item)
        links = i.publication_links(target.publication_links,item,reference('candidate'),{},Path(p.EVIDENCE_ROOT))
        self.assertEqual(item,original)
        self.assertIn(p.SOURCE,links);self.assertIn(p.SETUP,links)
        self.assertNotIn('binarytrees/binarytrees-parallel.mec',links)
        item['unrelated_evidence'] = evidence[1]
        with self.assertRaises(ValueError):
            i.publication_links(target.publication_links,item,reference('candidate'),{},Path(p.EVIDENCE_ROOT))

    def test_new_router_dependencies_reach_original_held_context(self):
        class EnteredReview(Exception):pass
        # Only source modules are loaded. The native/evidence context is replaced
        # at its entry; no retained plan, runtime or result file is replayed.
        publication_sha = e.sha(e.PUBLICATION.read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            publication = Path(directory).resolve()
            packet = publication/p.PACKET;packet.mkdir(parents=True)
            args = SimpleNamespace(cohort='apl-trees',evidence_root=ROOT,publication_root=publication,mode='preview',
                candidate=ROOT/p.PACKET/'publication/synthetic-not-read/candidate.json',candidate_sha256='a'*64,
                output=packet/'synthetic-preview',apply_output=packet/'synthetic-apply',
                exporter_sha256=e.sha(i.EXPORTER.read_bytes()),publication_sha256=publication_sha,
                reconciler_sha256=e.sha(e.RECONCILER.read_bytes()),normalization_sha256=e.sha(i.HISTORY.read_bytes()),
                adapter_sha256=e.sha(Path(i.__file__).read_bytes()),producer_sha256='b'*64)
            with patch.object(i,'load_exporter',return_value=e), \
                 patch.object(e,'context',side_effect=EnteredReview('held review entered')):
                with self.assertRaisesRegex(EnteredReview,'held review entered'):i.publish(args)
            self.assertFalse(args.output.exists());self.assertFalse(args.apply_output.exists())

    def test_standalone_history_load_preserves_all_prior_adapters(self):
        prior = e.module(i.PREVIOUS_HISTORY,i.PREVIOUS_HISTORY_SHA)
        original_keys = set(prior.ADAPTERS)
        self.assertNotIn(p.AUDIT,original_keys)
        loaded = n.load()
        self.assertEqual(set(loaded.ADAPTERS),original_keys|{p.AUDIT})
        self.assertEqual(set(prior.ADAPTERS),original_keys)

    def test_standalone_history_load_rejects_changed_publication_identity(self):
        with patch.object(n,'PUBLICATION_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'Reviewed APL tree history dependency changed'):
                n.load()

    def test_owned_write_registers_before_pending_stop_is_delivered(self):
        writer = e.safe_writer()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()/'new-output';owned=writer.OwnedFiles();calls=[]
            def mask(how,signals):
                calls.append(how)
                if how == e.signal.SIG_SETMASK:
                    self.assertIn(path,owned.records)
                    raise KeyboardInterrupt('pending stop after ownership registration')
                return set()
            with patch.object(e.signal,'pthread_sigmask',side_effect=mask):
                with self.assertRaises(KeyboardInterrupt):owned.write(path,b'complete')
            owned.remove_all()
            self.assertFalse(path.exists());self.assertEqual(calls,[e.signal.SIG_BLOCK,e.signal.SIG_SETMASK])

    def test_additive_history_replays_candidate_and_exact_coverage_boundary(self):
        review,sources,counts,work,runtime,refs = fixture()
        item = p.build_candidate(review,sources,counts,work,runtime,refs)
        before,languages = catalog()
        after,_,audit = p.build_publication(before,languages,item,reference('candidate'))
        report = dict(status='complete',active=None,pins_unchanged_at_end=True,attempts=[{}]*6,
            qualified_samples=6,full_performance_runs=6,
            programs={key:dict(samples_seconds=value['samples_seconds'],median_seconds=value['median_seconds'])
                      for key,value in review['profiles'].items()})
        documents = {audit['candidate']['path']:e.encoded(item),refs['reconciliation']['path']:e.encoded(review),
            refs['source_counts']['path']:e.encoded(counts),refs['source_work']['path']:e.encoded(work),
            refs['runtime_metadata_basis']['path']:e.encoded(runtime),refs['report']['path']:e.encoded(report)}
        documents.update({path:sources[digest] for path,digest,_,_ in p.BUNDLE})
        for ref in refs['native_cohort'].values():documents.setdefault(ref['path'],b'{}\n')
        parent = SimpleNamespace(ADAPTERS={},require=p.require,strict_json=json.loads,
                                 checked=lambda root,ref:documents[ref['path']])
        validator = n.attach(parent,p).ADAPTERS[p.AUDIT]
        additions,references = validator(ROOT,audit,before,after)
        self.assertEqual(additions,dict(programs={p.SUBJECT},program_inventory={p.SUBJECT,p.ALIAS}))
        self.assertEqual(references,set())
        altered = copy.deepcopy(after);altered['programs'][p.SUBJECT]['samples'][0] += 1
        with self.assertRaises(ValueError):validator(ROOT,audit,before,altered)

    def test_safe_owned_cleanup_preserves_external_edit_and_restores_other_files(self):
        writer = e.safe_writer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve();first=root/'one';second=root/'two'
            owned = writer.OwnedFiles();owned.write(first,b'one');owned.write(second,b'two')
            first.write_bytes(b'external')
            with self.assertRaises(ValueError):owned.remove_all()
            self.assertEqual(first.read_bytes(),b'external');self.assertFalse(second.exists())

    def test_existing_transaction_rolls_back_all_three_targets(self):
        old = e.module(HERE/'import_retained_catalog.py','d5dd6d091af4cae7dc6dd7dd7e5c6bda402309e2ae7b214ba2b31bed72d54ad4')
        old.snapshot = e.snapshot
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve();(root/'data').mkdir()
            originals = {name:b'old-'+name.encode() for name in old.TARGETS}
            prepared = {name:b'new-'+name.encode() for name in old.TARGETS}
            for name,raw in originals.items():(root/name).write_bytes(raw)
            identities = {name:e.snapshot(root/name)[1] for name in old.TARGETS}
            journal = old.Journal(root,e.safe_writer(),originals,identities,prepared)
            journal.apply();journal.final_check();journal.rollback()
            self.assertEqual({name:(root/name).read_bytes() for name in old.TARGETS},originals)


if __name__ == '__main__':
    unittest.main()
