"""Pure publication transforms with synthetic timings; never run the file phase.

The saved small source/count metadata fixture is reused from the exporter test.
No live timing report, lock acquisition, runtime image hash or program is read.
"""
import copy
import contextlib
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


imp = load('tested_scala_import', HERE/'import_scala.py')
fixture = load('import_export_fixture', HERE/'test_scala_export.py')


def original_catalog():
    source = 'old program\n'
    digest = hashlib.sha256(source.encode()).hexdigest()
    language = dict(key='mech', label='Mech', family='mech')
    benches, programs = [], {}
    for name in imp.r.BENCHES:
        key = name+':old-mech'
        row = dict(key=key, id='old-mech', language='mech', benchmark=name,
                   loc=10, seconds=2, samples=[1, 2, 3], files=[digest], x=1, y=20)
        programs[key] = row
        benches.append(dict(key=name, title=name, workload='saved', baseline_loc=10,
            baseline_formatted_loc=20, baseline_seconds=0.1,
            groups=[dict(language='mech', label='Mech', programs=[key], fast=key, small=key)]))
    data = dict(repository=dict(url='https://example.test/repo'), languages=[language], benchmarks=benches,
        programs=programs, program_inventory={}, files={digest:dict(sha256=digest, code=source, name='old.mech',
            path='old/main.mech', archive_path='archive/old/main.mech')},
        archive_paths={'old/main.mech':'archive/old/main.mech'}, reference_summary=[dict(lang='mech', label='Mech')],
        formatted_reference_summary=[dict(lang='mech', label='Mech', fast=dict(x=2,y=20), small=dict(x=2,y=20))],
        protocol={'old':'preserve'}, language_groups=[dict(key=k, languages=['mech'] if k == 'aot' else [])
            for k in ('aot', 'jit', 'functional', 'dynamic')], untouched={'nested':[1, None, False]})
    metadata = dict(platform='native', runtime='Mech', execution=['aot'], typing='static',
                    style=['functional'], memory=['rc'], note='existing', sources=['https://example.test'])
    values = (data, dict(languages={'mech':metadata}, scope='old scope', audited_on='2026-01-01'))
    originals = {name:(json.dumps(value)+'\n').encode() for name,value in zip(imp.TARGETS, values)}
    originals[imp.TARGETS[2]] = ('// Preserved taxonomy\nexport const languageMetadata = '+
                               json.dumps({'mech':metadata})+';\n').encode()
    return originals


class Import(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.Candidate.setUpClass()
        cls.originals = original_catalog()
        cls.release = json.loads(imp.RELEASE.read_bytes())


    def candidate(self, **kwargs):
        helper = fixture.Candidate()
        values = helper.fixture(**kwargs)
        result = fixture.export.build_candidate(**values)
        # Every timing/receipt identity remains synthetic; only portable path
        # placement differs from the export fixture for this pure transform.
        for name in ('report', 'terminal'):
            result[name]['path'] = str(imp.ROOT/'experiments/scala/full60-v1/synthetic'/f'{name}.json')
        return result, values['plan']


    def build(self, **kwargs):
        candidate, plan = self.candidate(**kwargs)
        refs = {key:dict(path='experiments/scala/full60-v1/'+key+'.json', sha256='a'*64)
                for key in ('candidate', 'reconciliation', 'release')}
        encoded, audit = imp.build_publication(self.originals, candidate, self.release, refs, plan)
        return json.loads(encoded[imp.TARGETS[0]]), audit, candidate, encoded


    def test_original_rows_baselines_taxonomy_and_input_objects_unchanged(self):
        candidate, plan = self.candidate()
        old_candidate, old_plan = copy.deepcopy(candidate), copy.deepcopy(plan)
        refs = {k:dict(path='review/'+k+'.json', sha256='a'*64) for k in ('candidate','reconciliation','release')}
        encoded, _ = imp.build_publication(self.originals, candidate, self.release, refs, plan)
        self.assertEqual(candidate, old_candidate)
        self.assertEqual(plan, old_plan)
        old, data = json.loads(self.originals[imp.TARGETS[0]]), json.loads(encoded[imp.TARGETS[0]])
        for field in ('programs', 'files', 'archive_paths'):
            self.assertEqual({k:data[field][k] for k in old[field]}, old[field])
        self.assertEqual(data['untouched'], old['untouched'])
        for a,b in zip(old['benchmarks'], data['benchmarks']):
            self.assertEqual(a, dict(b, groups=b['groups'][:-1]))
        self.assertEqual(data['protocol']['old'], 'preserve')
        self.assertEqual(json.loads(encoded[imp.TARGETS[1]])['languages']['mech'],
                         json.loads(self.originals[imp.TARGETS[1]])['languages']['mech'])

    def test_nested_legacy_inventory_all_mech_modes_and_null_fields_preserved(self):
        originals=copy.deepcopy(self.originals);data=json.loads(originals[imp.TARGETS[0]])
        for mode in ('aot','jit','interpreted'):
            key='nbody:legacy-'+mode
            row=dict(key=key,id='legacy-'+mode,language='mech',benchmark='nbody',execution_mode=mode,
                files=[],samples=[2.0,3.0,4.0],source_history=[{'retained':True,'optional':None}],
                previous_measurement={'samples':[1.0,1.1,1.2],'timing_boundary':'preserved'},
                publication_record={'independent':True,'nested':{'value':None}})
            data['programs'][key]=copy.deepcopy(row);data['program_inventory'][key]=copy.deepcopy(row)
        data['mech_interpreted_audit']={'historical_records':[{'samples':[1.0],'nullable':None}]}
        originals[imp.TARGETS[0]]=json.dumps(data).encode()
        candidate,plan=self.candidate();refs={k:dict(path='review/'+k+'.json',sha256='a'*64)
                                              for k in ('candidate','reconciliation','release')}
        encoded,_=imp.build_publication(originals,candidate,self.release,refs,plan)
        after=json.loads(encoded[imp.TARGETS[0]])
        for field in ('programs','program_inventory','files','archive_paths'):
            self.assertEqual({key:after[field][key] for key in data[field]},data[field])
        self.assertEqual(after['mech_interpreted_audit'],data['mech_interpreted_audit'])


    def test_subject_failure_retains_partials_and_skips_without_summary_or_chart(self):
        identity = 'scala-revcomp-jvm-v1'
        data, audit, candidate, _ = self.build(failure=identity, failure_round=3)
        key = 'revcomp:'+identity
        row = data['program_inventory'][key]
        self.assertFalse(row['eligible_for_chart'])
        self.assertFalse(row['chart_admission'])
        self.assertIsNone(row['seconds'])
        self.assertIsNone(row['timing_sd'])
        self.assertIsNone(row['x']); self.assertIsNone(row['y']); self.assertIsNone(row['formatted_x'])
        self.assertEqual(len(row['samples']), 2)
        self.assertEqual(len(row['sample_execution_metadata']), 3)
        self.assertEqual(row['sample_execution_metadata'][-1]['attempt'], row['failed_attempt'])
        self.assertNotIn(key, data['programs'])
        self.assertIn(identity, audit['excluded_profiles'])
        self.assertEqual(audit['skipped_slots'], candidate['skipped_slots'])
        groups = next(b for b in data['benchmarks'] if b['key'] == 'revcomp')['groups']
        self.assertFalse(any(g['language']=='scala' for g in groups))


    def test_matched_controls_never_become_language_programs_or_change_fixed_baselines(self):
        data, _, candidate, _ = self.build()
        self.assertFalse(any(':mech-control' in key for key in data['program_inventory']))
        old = json.loads(self.originals[imp.TARGETS[0]])
        for a,b in zip(old['benchmarks'], data['benchmarks']):
            self.assertEqual(a['baseline_seconds'], b['baseline_seconds'])
            for row in data['program_inventory'].values():
                if row['benchmark'] == b['key']:
                    self.assertEqual(row['y'], row['seconds']/b['baseline_seconds'])
                    self.assertEqual(row['time_ratio_to_matched_mech'],
                        row['seconds']/candidate['matched_mech_controls'][b['key']]['median_seconds'])


    def test_rejects_changed_admission_alias_counts_timing_or_sources(self):
        original, _ = self.candidate()
        key = next(iter(original['program_inventory']))
        mutations = [lambda c:c.update(chart_admission=True),
            lambda c:c['program_inventory'][key].update(eligible_for_publication_review=False),
            lambda c:c['program_inventory'][key].update(timing_alias_of='other'),
            lambda c:c['program_inventory'][key].update(loc=1),
            lambda c:c['program_inventory'][key].update(seconds=999),
            lambda c:c['program_inventory'][key].update(samples=[float('nan')]*3),
            lambda c:c['language_metadata'].update(platform='native'),
            lambda c:c['files'][next(iter(c['files']))].update(code='changed')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                candidate = copy.deepcopy(original)
                mutation(candidate)
                with self.assertRaises(ValueError):
                    imp.validate_candidate(candidate)


    def test_rejects_duplicate_existing_language_and_bad_endpoint_proposal(self):
        data, _, candidate, encoded = self.build()
        refs = {k:dict(path='review/'+k+'.json', sha256='a'*64) for k in ('candidate','reconciliation','release')}
        plan = fixture.synthetic.TEMPLATE_PLAN
        with self.assertRaisesRegex(ValueError, 'already admitted'):
            imp.build_publication(encoded, candidate, self.release, refs, plan)
        candidate['endpoint_proposals']['nbody']['fast'] = 'unrelated'
        with self.assertRaisesRegex(ValueError, 'Endpoint proposal'):
            imp.build_publication(self.originals, candidate, self.release, refs, plan)


    def test_named_lease_replacement_is_rejected_even_while_old_handle_lives(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'lease'
            path.write_bytes(b'')
            with path.open('rb'):
                expected = imp.lease_identities([path])
                imp.verify_named_leases(expected)
                path.unlink(); path.write_bytes(b'new')
                with self.assertRaisesRegex(ValueError, 'lease pathname changed'):
                    imp.verify_named_leases(expected)


    def test_private_links_cannot_escape_repo_or_become_implicit_archive_guesses(self):
        with self.assertRaisesRegex(ValueError, 'retained in the repository'):
            imp.public_ref(dict(path='/external/report.json', sha256='a'*64))
        with self.assertRaisesRegex(ValueError, 'Malformed'):
            imp.public_ref(dict(path=str(imp.ROOT/'../report.json'), sha256='a'*64))


    def test_apply_rollback_restores_exact_three_original_files_after_late_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            originals = {name:('original '+name+'\n').encode() for name in imp.TARGETS}
            prepared = {name:b'new\n' for name in imp.TARGETS}
            pins = {name:imp.sha(raw) for name,raw in originals.items()}
            for name,raw in originals.items():
                (root/name).parent.mkdir(parents=True, exist_ok=True)
                (root/name).write_bytes(raw)
            calls = []
            def verify():
                calls.append(True)
                if len(calls) == 3:
                    raise ValueError('injected lease replacement after two writes')
            with self.assertRaisesRegex(ValueError, 'injected lease'):
                imp.apply_prepared(root, prepared, originals, pins, verify)
            self.assertEqual({name:(root/name).read_bytes() for name in originals}, originals)
            self.assertEqual(list(root.rglob('*.scala-import.tmp')), [])
            imp.apply_prepared(root, prepared, originals, pins, lambda:None)
            self.assertEqual({name:(root/name).read_bytes() for name in prepared}, prepared)


    def test_post_rename_interrupt_is_journaled_before_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);old={'a':b'old-a','b':b'old-b'};new={name:b'new-'+name.encode() for name in old}
            for name,raw in old.items():(root/name).write_bytes(raw)
            actual=Path.replace;journal=[]
            def interrupted(path,target):
                actual(path,target)
                raise KeyboardInterrupt('immediately after rename')
            with patch.object(Path,'replace',interrupted),self.assertRaises(KeyboardInterrupt):
                imp.apply_prepared(root,new,old,{name:imp.sha(raw) for name,raw in old.items()},lambda:None,journal)
            self.assertEqual(journal,['a'])
            self.assertEqual({name:(root/name).read_bytes() for name in old},old)

    def test_caller_journal_survives_apply_return_interruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);old={'a':b'old-a','b':b'old-b'};new={name:b'new-'+name.encode() for name in old}
            for name,raw in old.items():(root/name).write_bytes(raw)
            journal=[]
            def interrupted_return():
                imp.apply_prepared(root,new,old,{name:imp.sha(raw) for name,raw in old.items()},lambda:None,journal)
                raise KeyboardInterrupt('before caller sets applied flag')
            with self.assertRaises(KeyboardInterrupt):interrupted_return()
            self.assertEqual(journal,list(old))
            imp.rollback_publication(root,{name:new[name] for name in journal},old)
            self.assertEqual({name:(root/name).read_bytes() for name in old},old)

    def test_missing_target_does_not_prevent_other_restorations(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);old={'a':b'old-a','b':b'old-b','c':b'old-c'}
            new={name:b'new-'+name.encode() for name in old}
            for name,raw in new.items():(root/name).write_bytes(raw)
            (root/'b').unlink()
            with self.assertRaisesRegex(ValueError,'restoration conflicts'):
                imp.rollback_publication(root,new,old)
            self.assertEqual((root/'a').read_bytes(),old['a'])
            self.assertEqual((root/'c').read_bytes(),old['c'])
            self.assertFalse((root/'b').exists())

    def test_apply_pin_failure_never_replaces_first_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            name = 'data/benchmarks.json'
            (root/name).parent.mkdir()
            (root/name).write_bytes(b'unreviewed')
            with self.assertRaisesRegex(ValueError, 'Pinned bytes changed'):
                imp.apply_prepared(root, {name:b'new'}, {name:b'old'}, {name:imp.sha(b'old')}, lambda:None)
            self.assertEqual((root/name).read_bytes(), b'unreviewed')

    def test_apply_failure_restores_owned_targets_and_preserves_external_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);old={'a':b'old-a','b':b'old-b','c':b'old-c'}
            new={name:b'new-'+name.encode() for name in old}
            for name,raw in old.items():(root/name).write_bytes(raw)
            calls=[]
            def verify():
                calls.append(True)
                if len(calls)==3:
                    (root/'b').write_bytes(b'external change')
                    raise ValueError('lease changed')
            with self.assertRaises(BaseExceptionGroup):
                imp.apply_prepared(root,new,old,{name:imp.sha(raw) for name,raw in old.items()},verify)
            self.assertEqual((root/'a').read_bytes(),old['a'])
            self.assertEqual((root/'b').read_bytes(),b'external change')
            self.assertEqual((root/'c').read_bytes(),old['c'])

    def test_temporary_writer_failure_preserves_replaced_temporary(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'a').write_bytes(b'old');temporary=root/'a.scala-import.tmp'
            def fail(_):
                temporary.write_bytes(b'external temporary')
                raise OSError('fsync failed')
            with patch.object(imp.os,'fsync',fail),self.assertRaises(BaseExceptionGroup):
                imp.apply_prepared(root,{'a':b'new'},{'a':b'old'},{'a':imp.sha(b'old')},lambda:None)
            self.assertEqual((root/'a').read_bytes(),b'old')
            self.assertEqual(temporary.read_bytes(),b'external temporary')


    def test_missing_or_wrong_reviewed_importer_pin_stops_before_file_phase_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'must-not-exist'
            argv = ['import_scala.py', '--durable-directory', '/synthetic/job', '--output', str(output)]
            for name in ('candidate', 'reconciliation', 'plan'):
                argv += ['--'+name, '/synthetic/'+name+'.json', '--'+name+'-sha256', 'a'*64]
            for name in ('benchmarks', 'languages', 'module'):
                argv += ['--'+name+'-sha256', 'a'*64]
            with patch.object(imp.r, 'review_files', side_effect=AssertionError('must not enter file phase')):
                with patch.object(sys, 'argv', argv), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        imp.main()
                with patch.object(sys, 'argv', argv+['--importer-sha256', '0'*64]):
                    with self.assertRaisesRegex(ValueError, 'Pinned bytes changed'):
                        imp.main()
            self.assertFalse(output.exists())


    def test_canonical_only_endpoints_and_no_formatted_aggregate(self):
        data,audit,candidate,encoded=self.build()
        original=json.loads(self.originals[imp.TARGETS[0]])
        self.assertEqual(len(data['program_inventory']),10)
        self.assertEqual(data['formatted_reference_summary'],original['formatted_reference_summary'])
        self.assertEqual(data['languages'][-1]['formatted_timed_benchmarks'],[])
        self.assertEqual(data['languages'][-1]['formatted_source_benchmarks'],[])
        self.assertEqual(data['languages'][-1]['runtime_family'],'jvm')
        for bench in data['benchmarks']:
            group=bench['groups'][-1]
            self.assertIsNone(group['formatted_fast']);self.assertIsNone(group['formatted_small'])
            for key in group['programs']:self.assertEqual(data['programs'][key],data['program_inventory'][key])
        for row in data['program_inventory'].values():
            self.assertEqual(row['formatted_loc_status'],'unavailable')
            self.assertFalse(row['formatted_loc_complete']);self.assertIsNone(row['formatted_x'])
            self.assertEqual(len(row['files']),1);self.assertFalse(row['distinct_optimization_claimed'])
            self.assertEqual(row['publication_record'],{k:v for k,v in row.items() if k!='publication_record'})
            self.assertFalse(Path(row['source_provenance_record']['source_evidence']['path']).is_absolute())

    def test_control_failure_retains_subject_samples_without_chart_or_complete_aggregate(self):
        data,audit,candidate,_=self.build(failure='revcomp:scala-full-study:mech-control',failure_round=2)
        for variant in ('jvm-v1',):
            key='revcomp:scala-revcomp-'+variant;row=data['program_inventory'][key]
            self.assertEqual(len(row['samples']),3);self.assertFalse(row['eligible_for_chart'])
            self.assertIsNone(row['time_ratio_to_matched_mech']);self.assertNotIn(key,data['programs'])
        self.assertNotIn('revcomp',audit['admitted_workloads'])
        self.assertEqual(len(data['reference_summary'][-1]['measured_benchmarks']),9)

    def test_time_and_canonical_minima_cannot_silently_change_fixed_baselines(self):
        candidate,plan=self.candidate();row=candidate['program_inventory']['nbody:scala-nbody-jvm-v1']
        refs={k:dict(path='review/'+k+'.json',sha256='a'*64) for k in ('candidate','reconciliation','release')}
        for key,value in (('baseline_seconds',row['seconds']+1),('baseline_loc',row['loc']+1)):
            originals=copy.deepcopy(self.originals);data=json.loads(originals[imp.TARGETS[0]])
            next(b for b in data['benchmarks'] if b['key']=='nbody')[key]=value
            originals[imp.TARGETS[0]]=json.dumps(data).encode()
            with self.assertRaisesRegex(ValueError,'separately reviewed baseline update'):
                imp.build_publication(originals,candidate,self.release,refs,plan)

    def test_post_apply_closure_failure_restores_catalog_without_overwriting_external_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);old={'a':b'old-a','b':b'old-b'};new={'a':b'new-a','b':b'new-b'}
            for name,raw in new.items():(root/name).write_bytes(raw)
            imp.rollback_publication(root,new,old)
            self.assertEqual({name:(root/name).read_bytes() for name in old},old)
            for name,raw in new.items():(root/name).write_bytes(raw)
            (root/'b').write_bytes(b'external')
            with self.assertRaises(ValueError):imp.rollback_publication(root,new,old)
            self.assertEqual((root/'b').read_bytes(),b'external')
            self.assertEqual((root/'a').read_bytes(),old['a'])

    def test_release_metadata_uses_2004_first_public_release(self):
        self.assertEqual(imp.sha(imp.RELEASE.read_bytes()),imp.RELEASE_SHA)
        self.assertEqual(self.release['release_year'],2004)
        self.assertEqual(self.release['release_date'],'2004-01-20')

if __name__=='__main__':unittest.main()
