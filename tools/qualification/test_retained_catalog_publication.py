"""Saved measurement and endpoint preservation for retained catalog additions."""
import copy
import importlib.util
from pathlib import Path
import statistics
import unittest


def load(name, filename):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


p = load('retained_publication_test', 'retained_catalog_publication.py')


def candidates():
    r = load('retained_r_fixture', 'test_r_retained_export.py')
    r.Candidate.setUpClass()
    a = load('retained_apl_fixture', 'test_apl_retained_export.py')
    a.Candidate.setUpClass()
    u = load('retained_uiua_fixture', 'test_export_uiua_retained.py')
    u.Candidate.setUpClass()
    lua = load('retained_lua_fixture', 'test_lua_pidigits_retained.py')
    lua.Retained.setUpClass()
    try:
        _, lua_candidate = lua.Retained().candidate()
        # This is a synthetic file-phase input; no runtime pins are replayed.
        lua_candidate['source_counts'] = copy.deepcopy(p.LUA_COUNTS)
        for row in lua_candidate['program_inventory'].values():
            for role in row['file_roles'].values():
                role['source_owner_review'] = copy.deepcopy(p.LUA_COUNTS)
    finally:
        lua.Retained.tearDownClass()
    return dict(r=r.e.build_candidate(r.Candidate.review, r.Candidate.sources, r.t.r),
                apl=a.Candidate().build(), uiua=u.e.build_candidate(u.Candidate.review, u.Candidate.sources),
                lua=lua_candidate)


def catalog(candidate, expanded_reference=False):
    scope, _ = p.validate_candidate(candidate)
    language = scope['language']
    workloads = ('nbody', 'binarytrees', 'fannkuchredux', 'mandelbrot', 'knucleotide',
                 'fasta', 'regexredux', 'revcomp', 'spectralnorm', 'pidigits')
    baselines = dict(nbody=20, binarytrees=16, fannkuchredux=20)
    rows, benches = {}, []
    present = []
    for bench in workloads:
        low = baselines.get(bench, 7)
        key = bench + ':old-c'
        row = dict(key=key, language='c', benchmark=bench, loc=low, physical_loc=low,
                   x=1, y=2, seconds=.002, samples=[.0019, .002, .0021],
                   receipt={'path': 'retained', 'sha256': 'old'}, files=['old-source'])
        row['publication_record'] = copy.deepcopy(row)
        rows[key] = row
        group = dict(language='c', label='C', fast=key, small=key, programs=[key])
        groups = [group]
        if bench not in scope['workloads'] and not (language == 'apl' and bench == 'binarytrees'):
            ownkey = bench + ':old-' + language
            own = copy.deepcopy(row)
            own.update(key=ownkey, language=language, loc=low + 2, x=(low + 2) / low, y=3)
            own['publication_record'] = {k: copy.deepcopy(v) for k, v in own.items() if k != 'publication_record'}
            rows[ownkey] = own
            groups.append(dict(language=language, label=scope['label'], fast=ownkey, small=ownkey, programs=[ownkey]))
            present.append(bench)
        benches.append(dict(key=bench, baseline_loc=low, baseline_seconds=.001,
                            groups=groups, optional_metadata=None))
    data = dict(programs=rows, program_inventory=copy.deepcopy(rows), benchmarks=benches,
                files={'old-source': dict(code='original', name='original.c')}, archive_paths={'retained': 'retained'},
                languages=[dict(key='c', timed_benchmarks=list(workloads), source_benchmarks=list(workloads)),
                           dict(key=language, timed_benchmarks=present, source_benchmarks=present)],
                reference_summary=[dict(lang='c', label='C', fast=dict(x=1, y=2), small=dict(x=1, y=2))],
                formatted_reference_summary=[dict(lang='c', fast=dict(x=1, y=2), small=dict(x=1, y=2))],
                repository={'url': 'https://example.com/repository'}, prior_audit={'unchanged': True})
    if expanded_reference:
        ref = dict(lang=language, label=scope['label'], measured_benchmarks=present)
        for kind in ('fast', 'small'):
            ref[kind] = {axis: p.aggregate(data, ref, kind, axis) for axis in ('x', 'y')}
        data['reference_summary'].append(ref)
    return data, dict(languages={language: {'displayed_program_count': len(present), 'typing': 'dynamic'},
                                 'c': {'displayed_program_count': 10, 'typing': 'static'}})


class Publication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidates = candidates()

    def apply(self, language, data=None, meta=None):
        candidate = self.candidates[language]
        if data is None:
            data, meta = catalog(candidate, expanded_reference=language in ('uiua','lua'))
        return p.build_publication(data, meta, candidate, dict(path='experiments/candidate.json', sha256='a' * 64),
                                   runtime_scope_ref=p.APL_RUNTIME_REVIEW if language == 'apl' else None)

    def test_all_saved_candidates_preserve_raw_rows_and_selected_endpoints(self):
        for language, candidate in self.candidates.items():
            with self.subTest(language=language):
                before, meta = catalog(candidate, expanded_reference=language in ('uiua','lua'))
                snapshot = copy.deepcopy((before, meta, candidate))
                after, newmeta, audit = self.apply(language, before, meta)
                self.assertEqual((before, meta, candidate), snapshot)
                for pool in ('programs', 'program_inventory'):
                    for key, row in before[pool].items():
                        self.assertEqual(p.raw_row(after[pool][key]), p.raw_row(row))
                selected = {key for g in audit['endpoints'].values() for key in g['programs']}
                self.assertEqual(set(after['programs']) - set(before['programs']), selected)
                self.assertEqual(set(after['program_inventory']) - set(before['program_inventory']), set(candidate['program_inventory']))
                for key, row in candidate['program_inventory'].items():
                    self.assertEqual(after['program_inventory'][key]['samples'], row['samples'])
                    self.assertEqual(after['program_inventory'][key]['seconds'], row['seconds'])
                    self.assertEqual(after['program_inventory'][key]['timing_alias_of'], row['timing_alias_of'])
                self.assertEqual(after['formatted_reference_summary'], before['formatted_reference_summary'])
                self.assertEqual(after['prior_audit'], before['prior_audit'])
                self.assertEqual(newmeta['languages']['c'], meta['languages']['c'])
                self.assertEqual(audit['native_runs'], 0)

    def test_r_rebases_only_two_loc_axes(self):
        before, meta = catalog(self.candidates['r'])
        after, _, audit = self.apply('r', before, meta)
        self.assertEqual([(v['benchmark'], v['before'], v['after']) for v in audit['normalizations']],
                         [('nbody', 20, 19), ('binarytrees', 16, 15)])
        self.assertEqual(audit['imported_program_inventory'], 6)
        self.assertEqual(audit['imported_endpoint_programs'], 5)
        for old, new in zip(before['benchmarks'], after['benchmarks']):
            self.assertEqual(old['baseline_seconds'], new['baseline_seconds'])
        c = next(r for r in after['reference_summary'] if r['lang'] == 'c')
        self.assertEqual(c['fast']['y'], 2)
        self.assertAlmostEqual(c['fast']['x'], (20 / 19 * 16 / 15) ** .1)

    def test_uiua_expands_aggregate_and_preserves_alias_ownership(self):
        before, meta = catalog(self.candidates['uiua'], expanded_reference=True)
        after, _, audit = self.apply('uiua', before, meta)
        self.assertEqual(len(audit['aggregate_change']['before']['measured_benchmarks']), 8)
        self.assertEqual(len(audit['aggregate_change']['after']['measured_benchmarks']), 10)
        self.assertEqual(audit['subject_native_observations'], 9)
        self.assertEqual(audit['timing_aliases'], 1)
        alias = next(r for r in self.candidates['uiua']['program_inventory'].values() if r['timing_alias_of'])
        self.assertEqual(after['program_inventory'][alias['key']]['native_observations'], 0)

    def test_existing_smaller_minimum_needs_no_second_rebase(self):
        before, meta = catalog(self.candidates['uiua'])
        for name, base in (('nbody', 19), ('binarytrees', 15)):
            bench = next(b for b in before['benchmarks'] if b['key'] == name)
            bench['baseline_loc'] = base
            key = bench['groups'][0]['fast']
            for pool in ('programs', 'program_inventory'):
                before[pool][key]['loc'] = before[pool][key]['publication_record']['loc'] = base
        _, _, audit = self.apply('uiua', before, meta)
        self.assertEqual(audit['normalizations'], [])

    def test_apl_failed_tree_and_runtime_scope_remain_unpromoted(self):
        after, _, audit = self.apply('apl')
        self.assertNotIn('binarytrees', audit['endpoints'])
        self.assertEqual(audit['normalizations'], [])
        self.assertEqual((audit['subject_native_observations'], audit['control_native_observations']), (27, 15))
        self.assertEqual(len(audit['aggregate_change']['after']['measured_benchmarks']), 9)
        self.assertEqual(audit['runtime_publication_scope_review'], p.APL_RUNTIME_REVIEW)
        for row in self.candidates['apl']['program_inventory'].values():
            self.assertFalse(after['program_inventory'][row['key']]['runtime_publication_metadata_qualified'])

    def test_apl_needs_separate_reviewed_runtime_scope(self):
        candidate = self.candidates['apl']
        before, meta = catalog(candidate)
        for ref in (None, dict(path='unreviewed.json', sha256='a' * 64)):
            with self.assertRaises(ValueError):
                p.build_publication(before, meta, candidate, dict(path='candidate.json', sha256='a' * 64), ref)

    def test_duplicate_admission_existing_endpoint_and_time_rebase_fail(self):
        for fault in ('duplicate', 'endpoint', 'time'):
            before, meta = catalog(self.candidates['r'])
            if fault == 'duplicate':
                before['r_retained_publication_audit'] = {}
            elif fault == 'endpoint':
                before['benchmarks'][0]['groups'].append({'language': 'r'})
            else:
                before['benchmarks'][0]['baseline_seconds'] = 1e99
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                self.apply('r', before, meta)

    def test_source_sample_count_alias_and_unqualified_changes_fail(self):
        for fault in ('source', 'sample', 'count', 'alias', 'qualification'):
            candidate = copy.deepcopy(self.candidates['uiua'])
            row = next(iter(candidate['program_inventory'].values()))
            if fault == 'source':
                candidate['files'][row['source_sha256']]['code'] += 'changed'
            elif fault == 'sample':
                row['samples'][0] += 1
            elif fault == 'count':
                row['canonical_loc'] += 1
            elif fault == 'alias':
                next(r for r in candidate['program_inventory'].values() if r['timing_alias_of'])['native_observations'] = 3
            else:
                row['full_workload_qualified'] = False
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                p.validate_candidate(candidate)

    def test_lua_complete_bundles_both_controls_and_only_nine_to_ten_aggregate(self):
        candidate = self.candidates['lua']
        before, meta = catalog(candidate, expanded_reference=True)
        # Equal-language-family rows must not be confused with Lua interpreted.
        jit = copy.deepcopy(before['programs']['pidigits:old-c'])
        jit.update(key='pidigits:old-luajit', language='luajit')
        jit['publication_record'] = {k:copy.deepcopy(v) for k,v in jit.items() if k != 'publication_record'}
        for pool in ('programs','program_inventory'):
            before[pool][jit['key']] = copy.deepcopy(jit)
        before['benchmarks'][-1]['groups'].append(dict(language='luajit', label='LuaJIT',
            fast=jit['key'], small=jit['key'], programs=[jit['key']]))
        before['reference_summary'].append(dict(lang='luajit',label='LuaJIT',
            measured_benchmarks=['pidigits'],fast=dict(x=1,y=2),small=dict(x=1,y=2)))
        meta['languages']['luajit'] = dict(displayed_program_count=1)
        after, newmeta, audit = self.apply('lua', before, meta)
        self.assertEqual(audit['normalizations'], [])
        self.assertEqual((audit['source_forms'], audit['distinct_subject_sources'],
            audit['counted_physical_files'], audit['counted_files_per_profile']), (4,4,5,2))
        self.assertEqual((audit['subject_native_observations'], audit['control_native_observations']), (12,6))
        self.assertEqual((len(audit['aggregate_change']['before']['measured_benchmarks']),
                          len(audit['aggregate_change']['after']['measured_benchmarks'])), (9,10))
        self.assertEqual((audit['imported_program_inventory'], audit['imported_endpoint_programs']), (4,2))
        for key,row in candidate['program_inventory'].items():
            actual = after['program_inventory'][key]
            self.assertEqual(actual['files'], row['files'])
            self.assertEqual(actual['additional_matched_mech_control'], candidate['matched_mech_controls']['mech-small-control'])
            self.assertEqual(actual['matched_mech_control'], candidate['matched_mech_controls']['mech-fast-control'])
        self.assertEqual(after['programs'][jit['key']], before['programs'][jit['key']])
        self.assertEqual(after['reference_summary'][-1], before['reference_summary'][-1])
        self.assertEqual(newmeta['languages']['luajit'], meta['languages']['luajit'])
        self.assertEqual(audit['source_manifest'], candidate['source_manifest'])
        self.assertNotIn('source_audit', audit)

    def test_lua_missing_helper_controls_changed_roles_or_profile_fail(self):
        for fault in ('helper','role','count','control','row_control','identity','scope','approval'):
            candidate = copy.deepcopy(self.candidates['lua'])
            row = next(iter(candidate['program_inventory'].values()))
            if fault == 'helper': row['files'].pop()
            elif fault == 'role': row['file_roles'][p.LUA_HELPER]['role'] = 'runtime'
            elif fault == 'count': row['file_roles'][p.LUA_HELPER]['normalized_loc'] -= 1
            elif fault == 'control': candidate['matched_mech_controls'].pop('mech-small-control')
            elif fault == 'row_control': row['additional_matched_mech_control'] = row['matched_mech_control']
            elif fault == 'identity': row['id'] = 'luajit-listed-1'
            elif fault == 'scope': candidate['matched_control_samples'] = 3
            else: candidate['source_counts']['sha256'] = '0'*64
            with self.subTest(fault=fault), self.assertRaises((ValueError,KeyError)):
                p.validate_candidate(candidate)

    def test_lua_unreviewed_minimum_and_wrong_prior_coverage_fail(self):
        for fault in ('minimum','coverage'):
            before, meta = catalog(self.candidates['lua'], expanded_reference=True)
            if fault == 'minimum':
                bench = before['benchmarks'][-1]
                bench['baseline_loc'] = 1000
                key = bench['groups'][0]['fast']
                for pool in ('programs','program_inventory'):
                    before[pool][key]['loc'] = before[pool][key]['publication_record']['loc'] = 1000
            else:
                before['reference_summary'][-1]['measured_benchmarks'].pop()
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                self.apply('lua', before, meta)

    def test_existing_languages_still_require_one_application_file(self):
        for language in ('r','apl','uiua'):
            candidate = copy.deepcopy(self.candidates[language])
            row = next(iter(candidate['program_inventory'].values()))
            row['files'].append(row['files'][0])
            with self.subTest(language=language), self.assertRaisesRegex(ValueError, 'source bundle'):
                p.validate_candidate(candidate)


if __name__ == '__main__':
    unittest.main()
