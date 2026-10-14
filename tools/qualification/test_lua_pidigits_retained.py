"""Small saved-document/fault tests. No physical pin replay or native process."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


r=load('lua_reconcile_test','lua_pidigits_reconcile.py')
e=load('lua_export_test','lua_pidigits_export.py')


def fixture(loaded):
    read=lambda p:json.loads(Path(p).read_text())
    manifest=read(r.OLD/r.COHORT/'full-study/manifest.json')
    retained=read(r.ARCHIVE/'full-study/manifest.json')
    index=read(r.PACKET/'input-index.json')
    report=read(r.ARCHIVE/'results/full-study.json')
    sources={};owners=loaded['owners']
    for n in r.VARIANTS:
        raw=(r.PACKET/'sources'/f'pidigits-lua-{n}-normalized.lua').read_bytes()
        c=owners.count_source(raw,n);digest=c['source_sha256'];sources[digest]=raw
    sources[r.HELPER_SHA]=(r.PACKET/'support/gmp.c').read_bytes()
    counts=read(r.PACKET/'qualified-source-counts-v1.json')
    if hashlib.sha256((r.PACKET/'qualified-source-counts-v1.json').read_bytes()).hexdigest()!=r.COUNTS_SHA:
        raise ValueError('Actual reviewed source-count fixture changed')
    return dict(manifest=manifest,retained=retained,report=report,
        validation=read(r.ARCHIVE/'results/validation.json'),
        family=read(r.ROOT/index['retained_evidence']['family-review']['path']),
        launch=read(r.ARCHIVE/'full-study/launch.json'),index=index,
        raw={a['attempt']:read(r.ARCHIVE/'full-study/attempts'/Path(a['result_path']).name) for a in report['attempts']},
        sources=sources,counts=counts)


class Retained(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context=r.modules();cls.loaded=cls.context.__enter__();cls.saved=fixture(cls.loaded)

    @classmethod
    def tearDownClass(cls):cls.context.__exit__(None,None,None)

    def call(self,values):return r.reconcile(**values,loaded=self.loaded)

    def reject(self,change):
        data=copy.deepcopy(self.saved);change(data)
        with self.assertRaises((ValueError,AssertionError,KeyError)):self.call(data)

    def test_original_eighteen_observations_and_distinct_sources(self):
        result=self.call(self.saved)
        self.assertEqual((result['subject_observations'],result['matched_control_observations']),(12,6))
        self.assertEqual(len(result['profiles']),6)
        self.assertFalse(result['physical_file_integrity_verified']);self.assertFalse(result['chart_admission'])
        self.assertEqual(result['profiles']['lua-listed-6']['median_seconds'],.343833083)

    def test_omitted_and_repeated_attempts_fail(self):
        self.reject(lambda d:d['report']['attempts'].pop())
        self.reject(lambda d:d['report']['attempts'].append(copy.deepcopy(d['report']['attempts'][0])))

    def test_failed_or_unowned_native_is_rejected(self):
        for field,value in [('exit_status',1),('exit_status',False),('stderr','unexpected'),
                            ('qualified',False),('remaining_group_members',[{'pid':1}])]:
            self.reject(lambda d,f=field,v=value:d['report']['attempts'][0].__setitem__(f,v))
        self.reject(lambda d:d['report']['attempts'][0]['supervised_native_group'].__setitem__('inherited_common_mutex',False))

    def test_raw_receipt_and_supervisor_identity_cannot_be_relabelled(self):
        self.reject(lambda d:d['raw'][1].__setitem__('seconds',.123))
        self.reject(lambda d:d['launch'].__setitem__('pid',1))
        self.reject(lambda d:d['launch']['identity'].__setitem__('process_listing','other command'))

    def test_interpreter_module_or_closure_changes_fail(self):
        self.reject(lambda d:d['manifest']['profiles'][0]['runtime'].__setitem__('sha256','0'*64))
        self.reject(lambda d:d['manifest']['library']['modules'].__setitem__(str(r.OLD/r.COHORT/'build/bn.so'),'0'*64))
        self.reject(lambda d:d['index']['original_pins'].pop('/opt/homebrew/bin/lua'))

    def test_archive_prose_exception_is_one_field_only(self):
        self.reject(lambda d:d['retained'].__setitem__('timeout_seconds',100))
        self.reject(lambda d:d['retained']['profiles'][0].__setitem__('loc',61))

    def test_source_or_division_work_mutation_fails(self):
        self.reject(lambda d:d['sources'].__setitem__(r.HELPER_SHA,d['sources'][r.HELPER_SHA]+b'\n'))
        self.reject(lambda d:d['validation']['division_checks'][0].__setitem__('actual_divisions',222))
        self.reject(lambda d:d['validation'].__setitem__('generic_primitive_tests',False))

    def test_complete_counted_bundle_is_mandatory(self):
        self.reject(lambda d:d['counts']['files'].pop(r.HELPER_SHA))
        self.reject(lambda d:d['counts']['profiles']['lua-listed-1']['files'].pop())
        self.reject(lambda d:d['counts']['profiles']['lua-listed-1'].__setitem__('canonical_loc',62))
        self.reject(lambda d:d['counts'].__setitem__('status','proposed'))

    def test_source_owner_spans_cover_each_exact_application(self):
        owners=self.loaded['owners']
        for n,count in [(1,62),(5,77),(6,63),(7,57)]:
            raw=self.saved['sources'][owners.SPECS[n]['sha256']];result=owners.count_source(raw,n)
            self.assertEqual(result['canonical_loc'],count)
            self.assertEqual(result['unowned_significant_characters'],[])
            self.assertFalse(result['generic_language_certificate'])
            with self.assertRaises(ValueError):owners.count_source(raw+b' ',n)

    def test_actual_complete_c_owner_review_and_late_row_fault(self):
        review=json.loads((r.ROOT/r.HELPER_REVIEW).read_text())
        r.check_helper_review(review,self.saved['sources'][r.HELPER_SHA])
        review['rows'][14]['canonical_units']-=1
        with self.assertRaises(ValueError):r.check_helper_review(review,self.saved['sources'][r.HELPER_SHA])

    def candidate(self):
        review=self.call(self.saved)
        # Future verified flags are synthetic transformation inputs only.
        review.update(status='eighteen-saved-observations-file-verified-awaiting-publication-review',
            physical_file_integrity_verified=True,common_mutex_held=True,
            source_counts=dict(path='experiments/lua/retained-pidigits-v1/qualified-source-counts-v1.json',sha256='0'*64),
            source_manifest=copy.deepcopy(self.saved['index']['retained_evidence']['full-study/manifest.json']))
        return review,e.build_candidate(review,self.saved['sources'],r)

    def test_candidate_counts_both_files_and_preserves_old_counts(self):
        review,candidate=self.candidate()
        self.assertEqual(len(candidate['files']),5);self.assertEqual(len(candidate['program_inventory']),4)
        for row in candidate['program_inventory'].values():
            self.assertEqual(len(row['files']),2);self.assertEqual(row['loc'],row['original_producer_loc']+218)
            self.assertTrue(row['helper_counted']);self.assertFalse(row['original_helper_counted'])
            self.assertEqual(row['loc'],sum(v['normalized_loc'] for v in row['file_roles'].values()))
            self.assertIsNone(row['formatted_loc']);self.assertIsNone(row['timing_alias_of'])
        self.assertEqual(sum(len(x['samples']) for x in candidate['matched_mech_controls'].values()),6)
        self.assertFalse(candidate['luajit_mutated']);self.assertFalse(candidate['chart_admission'])

    def test_endpoints_choose_measured_fast_and_complete_bundle_small(self):
        _,candidate=self.candidate();g=candidate['endpoints']['pidigits']
        self.assertTrue(g['fast'].endswith('-6'));self.assertTrue(g['small'].endswith('-7'))
        self.assertEqual(len(g['programs']),2)

    def test_candidate_requires_closed_physical_phase_and_exact_sources(self):
        review,_=self.candidate();review['physical_file_integrity_verified']=False
        with self.assertRaises(ValueError):e.build_candidate(review,self.saved['sources'],r)
        review,_=self.candidate();sources=dict(self.saved['sources']);sources[r.HELPER_SHA]+=b'changed'
        with self.assertRaises(ValueError):e.build_candidate(review,sources,r)


if __name__=='__main__':unittest.main()
