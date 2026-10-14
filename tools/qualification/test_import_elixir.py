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


imp = load('tested_elixir_import', HERE/'import_elixir.py')
fixture = load('import_export_fixture', HERE/'test_elixir_export.py')


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
            result[name]['path'] = str(imp.ROOT/'experiments/elixir/full90-v1/synthetic'/f'{name}.json')
        return result, values['plan']

    def build(self, **kwargs):
        candidate, plan = self.candidate(**kwargs)
        refs = {key:dict(path='experiments/elixir/full90-v1/'+key+'.json', sha256='a'*64)
                for key in ('candidate', 'reconciliation', 'release')}
        encoded, audit = imp.build_publication(self.originals, candidate, self.release, refs, plan)
        return json.loads(encoded[imp.TARGETS[0]]), audit, candidate, encoded

    def test_all_twenty_forms_retained_and_only_selected_endpoints_are_chart_rows(self):
        data, audit, candidate, encoded = self.build()
        self.assertEqual(len(data['program_inventory']), 20)
        self.assertEqual(audit['imported_program_inventory'], 20)
        self.assertEqual(len(audit['admitted_workloads']), 10)
        for bench in data['benchmarks']:
            group = next(g for g in bench['groups'] if g['language'] == 'elixir')
            for key in group['programs']:
                self.assertEqual(data['programs'][key], data['program_inventory'][key])
                self.assertTrue(data['programs'][key]['eligible_for_chart'])
            for field in ('fast', 'small', 'formatted_fast', 'formatted_small'):
                self.assertIn(group[field], group['programs'])
        self.assertFalse(candidate['chart_admission'])
        self.assertFalse(candidate['language_metadata']['chart_admission'])

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

    def test_three_roles_aliases_counts_and_portable_public_receipts(self):
        data, _, _, _ = self.build()
        for row in data['program_inventory'].values():
            self.assertEqual({v['role'] for v in row['file_roles'].values()}, set(imp.e.ROLES))
            self.assertEqual(row['loc'], sum(v['normalized_loc'] for v in row['file_roles'].values()))
            self.assertEqual(row['formatted_loc'], sum(v['formatted_loc'] for v in row['file_roles'].values()))
            self.assertEqual(row['physical_loc'], sum(v['physical_loc'] for v in row['file_roles'].values()))
            self.assertEqual(row['formatted_loc_status'], 'qualified')
            self.assertTrue(row['formatted_loc_complete'])
            self.assertEqual(row['formatted_x'], row['formatted_loc']/20)
            self.assertEqual(row['publication_record'], {k:v for k,v in row.items() if k != 'publication_record'})
            for role in row['file_roles'].values():
                self.assertFalse(Path(role['retained_source']['path']).is_absolute())
                self.assertFalse(Path(role['formatted_ast']['path']).is_absolute())
                self.assertTrue(Path(role['original_source']['path']).is_absolute())
            for digest in row['files']:
                self.assertEqual(data['files'][digest]['path'], data['files'][digest]['archive_path'])
        for bench in imp.r.BENCHES:
            a = data['program_inventory'][bench+':elixir-'+bench+'-compact']
            b = data['program_inventory'][bench+':elixir-'+bench+'-optimized']
            self.assertEqual(a['files'], b['files'])
            self.assertNotEqual(a['sample_execution_metadata'], b['sample_execution_metadata'])
            self.assertFalse(a['distinct_optimization_claimed'])
            self.assertIsNone(a['timing_alias_of'])

    def test_full_suite_canonical_and_formatted_aggregates_use_their_own_coordinates(self):
        data, _, candidate, _ = self.build()
        original = json.loads(self.originals[imp.TARGETS[0]])
        canonical = data['reference_summary'][-1]
        formatted = data['formatted_reference_summary'][-1]
        self.assertEqual(data['reference_summary'][:-1], original['reference_summary'])
        self.assertEqual(data['formatted_reference_summary'][:-1], original['formatted_reference_summary'])
        self.assertEqual(set(formatted), {'lang', 'label', 'fast', 'small'})
        self.assertEqual((formatted['lang'], formatted['label']), ('elixir', 'Elixir'))
        self.assertEqual(set(canonical['measured_benchmarks']), set(imp.r.BENCHES))
        for kind in ('fast', 'small'):
            expected = {'canonical_x':[], 'canonical_y':[], 'formatted_x':[], 'formatted_y':[]}
            for bench in data['benchmarks']:
                group = next(g for g in bench['groups'] if g['language']=='elixir')
                plain = candidate['program_inventory'][group[kind]]
                expanded = candidate['program_inventory'][group['formatted_'+kind]]
                expected['canonical_x'].append(plain['loc']/bench['baseline_loc'])
                expected['canonical_y'].append(plain['seconds']/bench['baseline_seconds'])
                expected['formatted_x'].append(expanded['formatted_loc']/bench['baseline_formatted_loc'])
                expected['formatted_y'].append(expanded['seconds']/bench['baseline_seconds'])
            self.assertTrue(all(len(values)==10 for values in expected.values()))
            for label, summary in [('canonical', canonical), ('formatted', formatted)]:
                for axis in ('x','y'):
                    self.assertAlmostEqual(summary[kind][axis], math.prod(expected[label+'_'+axis])**0.1)
            self.assertNotAlmostEqual(formatted[kind]['x'], canonical[kind]['x'])

    def test_missing_formatted_baseline_omits_only_full_suite_formatted_summary(self):
        candidate, plan = self.candidate()
        refs = {k:dict(path='review/'+k+'.json', sha256='a'*64) for k in ('candidate','reconciliation','release')}
        for baseline in (None, 0):
            originals = copy.deepcopy(self.originals)
            before = json.loads(originals[imp.TARGETS[0]])
            next(b for b in before['benchmarks'] if b['key']=='nbody')['baseline_formatted_loc'] = baseline
            originals[imp.TARGETS[0]] = json.dumps(before).encode()
            with self.subTest(baseline=baseline):
                encoded, _ = imp.build_publication(originals, candidate, self.release, refs, plan)
                data = json.loads(encoded[imp.TARGETS[0]])
                self.assertEqual(data['formatted_reference_summary'], before['formatted_reference_summary'])
                self.assertEqual(len(data['reference_summary'][-1]['measured_benchmarks']), 10)
                self.assertEqual(len(data['languages'][-1]['formatted_timed_benchmarks']), 9)
                group = next(b for b in data['benchmarks'] if b['key']=='nbody')['groups'][-1]
                self.assertIsNotNone(group['fast']); self.assertIsNone(group['formatted_fast'])
                self.assertIsNone(group['formatted_small'])

    def test_subject_failure_retains_partials_and_skips_without_summary_or_chart(self):
        identity = 'elixir-revcomp-compact'
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
        group = next(b for b in data['benchmarks'] if b['key'] == 'revcomp')['groups'][-1]
        self.assertTrue(all('optimized' in k for k in group['programs']))

    def test_matched_control_failure_keeps_successful_subject_times_but_excludes_both(self):
        data, audit, candidate, _ = self.build(failure='revcomp:elixir-full-study:mech-control', failure_round=2)
        for variant in ('compact', 'optimized'):
            key = 'revcomp:elixir-revcomp-'+variant
            row = data['program_inventory'][key]
            self.assertTrue(row['full_workload_qualified'])
            self.assertEqual(len(row['samples']), 3)
            self.assertGreater(row['seconds'], 0)
            self.assertFalse(row['matched_control_qualified'])
            self.assertFalse(row['eligible_for_chart'])
            self.assertIsNone(row['y'])
            self.assertIsNone(row['time_ratio_to_matched_mech'])
            self.assertNotIn(key, data['programs'])
            self.assertEqual(row['exclusion_reason'], 'matched-Mech-control-failed')
        self.assertNotIn('revcomp', audit['admitted_workloads'])
        self.assertEqual(len(data['reference_summary'][-1]['measured_benchmarks']), 9)
        self.assertEqual(data['formatted_reference_summary'],
                         json.loads(self.originals[imp.TARGETS[0]])['formatted_reference_summary'])
        language = data['languages'][-1]
        self.assertEqual(len(language['timed_benchmarks']), 9)
        self.assertEqual(len(language['formatted_timed_benchmarks']), 9)
        self.assertEqual(set(language['source_benchmarks']), set(imp.r.BENCHES))
        self.assertEqual(set(language['formatted_source_benchmarks']), set(imp.r.BENCHES))
        bench = next(b for b in data['benchmarks'] if b['key'] == 'revcomp')
        self.assertFalse(any(g['language'] == 'elixir' for g in bench['groups']))
        self.assertEqual(len(data['program_inventory']), 20)

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
        plan = fixture.synthetic.SAVED_PLAN
        with self.assertRaisesRegex(ValueError, 'already admitted'):
            imp.build_publication(encoded, candidate, self.release, refs, plan)
        candidate['endpoint_proposals']['nbody']['fast'] = 'unrelated'
        with self.assertRaisesRegex(ValueError, 'Endpoint proposal'):
            imp.build_publication(self.originals, candidate, self.release, refs, plan)

    def test_release_metadata_is_pinned_and_distinguishes_earlier_predecessor(self):
        self.assertEqual(imp.sha(imp.RELEASE.read_bytes()), imp.RELEASE_SHA)
        self.assertEqual(self.release['release_year'], 2012)
        self.assertIn('2011', self.release['release_note'])
        self.assertTrue(self.release['release_source'].startswith('https://elixir-lang.org/'))

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
            self.assertEqual(list(root.rglob('*.elixir-import.tmp')), [])
            imp.apply_prepared(root, prepared, originals, pins, lambda:None)
            self.assertEqual({name:(root/name).read_bytes() for name in prepared}, prepared)

    def test_apply_pin_failure_never_replaces_first_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            name = 'data/benchmarks.json'
            (root/name).parent.mkdir()
            (root/name).write_bytes(b'unreviewed')
            with self.assertRaisesRegex(ValueError, 'Pinned bytes changed'):
                imp.apply_prepared(root, {name:b'new'}, {name:b'old'}, {name:imp.sha(b'old')}, lambda:None)
            self.assertEqual((root/name).read_bytes(), b'unreviewed')

    def test_new_time_canonical_or_formatted_minimum_requires_separate_baseline_review(self):
        candidate, plan = self.candidate()
        refs = {k:dict(path='review/'+k+'.json', sha256='a'*64) for k in ('candidate','reconciliation','release')}
        row = candidate['program_inventory']['nbody:elixir-nbody-compact']
        for baseline, value in (('baseline_seconds', row['seconds']+1),
                                ('baseline_loc', row['loc']+1),
                                ('baseline_formatted_loc', row['formatted_loc']+1)):
            originals = copy.deepcopy(self.originals)
            data = json.loads(originals[imp.TARGETS[0]])
            next(b for b in data['benchmarks'] if b['key'] == 'nbody')[baseline] = value
            originals[imp.TARGETS[0]] = json.dumps(data).encode()
            with self.subTest(baseline=baseline), self.assertRaisesRegex(ValueError, 'separately reviewed baseline update'):
                imp.build_publication(originals, candidate, self.release, refs, plan)

    def test_missing_or_wrong_reviewed_importer_pin_stops_before_file_phase_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'must-not-exist'
            argv = ['import_elixir.py', '--durable-directory', '/synthetic/job', '--output', str(output)]
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


if __name__ == '__main__':
    unittest.main()
