"""Focused offline Prolog intake gates and archived relocation; no subject process."""
import copy
import hashlib
import math
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from qualification import import_prolog_spectral as admission


def put(root,path,value):
    p=root/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(admission.encoded(value) if isinstance(value,(dict,list)) else value);return p


def copy_proof(root):
    results=admission.load(admission.ROOT/admission.RESULTS)
    paths={row['path'] for row in results['artifacts']}|set(admission.REFS.values())|{admission.PARENT_SOURCE,admission.SUPPORT,admission.PLAN,admission.RESULTS}
    for path in paths:
        target=root/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(admission.ROOT/path,target)
    return results


class FullExecutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        self.results=copy_proof(self.root);self.report=admission.load(self.root/admission.REFS['full'])
        self.producer=admission.load(self.root/admission.REFS['producer_plan']);self.recorded=admission.recorded_root(self.report)

    def check(self):
        evidence=admission.Evidence(self.root,self.recorded);original=evidence.document
        # Keep immutable pins untouched. Substitute structured report data only
        # at this unit boundary so semantic gates are tested beyond SHA rejection.
        def document(ref):
            return self.report if ref['path']==admission.REFS['full'] else original(ref)
        with mock.patch.object(evidence,'document',side_effect=document):
            return admission.check_full(evidence,dict(path=admission.REFS['full'],sha256=admission.FINAL_FULL_SHA),self.producer)

    def test_all_six_observations_reconcile_from_copied_proof(self):
        report=self.check();self.assertEqual(len(report['cases']),6)
        self.assertEqual(report['medians']['blocks8-specialized'],34.515944833)
        self.assertEqual(report['medians']['parent'],179.483351667)

    def test_running_active_diagnostic_or_wrong_workload_rejected(self):
        original=copy.deepcopy(self.report)
        for field,value in [('status','RUNNING'),('active',{'source':'parent'}),('diagnostic_profile',True),('full_workload',False),('chart_admission',True),('n',700)]:
            self.report=copy.deepcopy(original);self.report[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.check()

    def test_missing_duplicate_or_reordered_observation_rejected(self):
        original=copy.deepcopy(self.report)
        self.report['cases'].pop()
        with self.assertRaisesRegex(ValueError,'observation'):self.check()
        self.report=copy.deepcopy(original);self.report['cases'][0]=copy.deepcopy(self.report['cases'][1])
        with self.assertRaises(ValueError):self.check()
        self.report=original;self.report['cases'][0],self.report['cases'][1]=self.report['cases'][1],self.report['cases'][0]
        with self.assertRaisesRegex(ValueError,'observation'):self.check()

    def test_raw_pid_source_command_and_power_mismatch_rejected(self):
        original=copy.deepcopy(self.report)
        self.report['cases'][0]['pid']+=1
        with self.assertRaisesRegex(ValueError,'Raw'):self.check()
        self.report=copy.deepcopy(original);self.report['cases'][0]['command'][-1]='700'
        with self.assertRaises(ValueError):self.check()
        self.report=copy.deepcopy(original);self.report['cases'][0]['source_sha256']='0'*64
        with self.assertRaises(ValueError):self.check()
        self.report=original;self.report['cases'][0]['power_after']['settings']='lowpowermode 1'
        with self.assertRaisesRegex(ValueError,'power'):self.check()

    def test_stream_corruption_and_mixed_recorded_root_rejected(self):
        row=self.report['cases'][0];path=admission.Evidence(self.root,self.recorded).relative(row['stdout']['path'])
        put(self.root,path,b'wrong bytes\n')
        with self.assertRaisesRegex(ValueError,'Changed evidence'):self.check()
        shutil.copyfile(admission.ROOT/path,self.root/path)
        row['stdout']['path']=str(self.root/path)
        with self.assertRaisesRegex(ValueError,'recorded repository'):self.check()

    def test_stale_aggregation_and_changed_source_snapshot_rejected(self):
        self.report['medians']['blocks8-specialized']=1.0
        with self.assertRaisesRegex(ValueError,'aggregation'):self.check()
        self.report=admission.load(self.root/admission.REFS['full'])
        put(self.root,admission.FULL_DIR+'full-v1/sources/blocks8-specialized.pl',b'changed\n')
        with self.assertRaisesRegex(ValueError,'Changed evidence'):self.check()

    def test_dispersion_accepts_one_ulp_only_and_preserves_saved_value(self):
        value=self.report['sample_sd_seconds']['blocks8-specialized']
        self.report['sample_sd_seconds']['blocks8-specialized']=math.nextafter(value,math.inf)
        self.assertEqual(self.check()['sample_sd_seconds']['blocks8-specialized'],self.report['sample_sd_seconds']['blocks8-specialized'])
        self.report['sample_sd_seconds']['blocks8-specialized']=value*2
        with self.assertRaisesRegex(ValueError,'dispersion'):self.check()

    def test_path_escape_or_wrong_runtime_suffix_rejected(self):
        evidence=admission.Evidence(self.root,self.recorded)
        for path in [self.recorded+'/../outside','../outside','/unrelated/outside']:
            with self.subTest(path=path),self.assertRaises(ValueError):evidence.relative(path)
        self.report['cases'][0]['command'][0]='/other/swipl'
        with self.assertRaisesRegex(ValueError,'SWI'):admission.recorded_root(self.report)


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();copy_proof(self.root)
        self.receipt=admission.load(self.root/admission.REFS['ownership']);self.recorded=admission.recorded_root(admission.load(self.root/admission.REFS['full']))

    def check(self):
        evidence=admission.Evidence(self.root,self.recorded);original=evidence.document
        def document(ref):return self.receipt if ref['path']==admission.REFS['ownership'] else original(ref)
        with mock.patch.object(evidence,'document',side_effect=document):
            return admission.check_ownership(evidence,dict(path=admission.REFS['ownership'],sha256=admission.PINNED['ownership']))

    def test_approved_manual128_87_and_native_null_are_distinct(self):
        result=self.check();self.assertEqual(result['application_loc'],128);self.assertEqual(result['physical_loc'],87)
        self.assertIsNone(result['current_native_v5_normalized_loc']);self.assertFalse(result['native_grammar_qualification_claimed'])

    def test_unapproved_count_source_or_grammar_claim_rejected(self):
        original=copy.deepcopy(self.receipt)
        for field,value in [('independent_review_approved',False),('application_loc',87),('source_sha256','0'*64),('native_grammar_qualification_claimed',True),('current_native_v5_normalized_loc',128)]:
            self.receipt=copy.deepcopy(original);self.receipt[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.check()

    def test_stale_written_line_or_units_rejected(self):
        self.receipt['line_ledger'][2]['source_text']+=' changed'
        with self.assertRaises(ValueError):self.check()
        self.receipt=admission.load(self.root/admission.REFS['ownership']);self.receipt['line_ledger'][2]['retained_rule_units']+=1
        with self.assertRaises(ValueError):self.check()


class CompleteProofAndCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();copy_proof(self.root)
        self.results=admission.reconcile(self.root,local_artifacts=False)
        put(self.root,admission.RESULTS,self.results)
        parent=dict(key=admission.PARENT,id='prolog-spectralnorm-compact',benchmark='spectralnorm',language='prolog',
            files=[admission.PARENT_SHA,admission.SUPPORT_SHA],loc=96,physical_loc=67,seconds=179.423098959,
            samples=[179.1,179.423098959,179.8],timing_sd=.3,x=96/9,y=179.423098959/.08,
            formatted_loc=None,formatted_loc_complete=False,formatted_x=None,
            authorship=dict(kind='local-origin-unverified',origin_status='unresolved',origin_gaps=['Predecessor source unresolved'],retained_sources=[],
                license=dict(status='unverified',licenses=[],unresolved=['Inherited terms unknown'])))
        source=admission.load(self.root/admission.PLAN)
        files={digest:dict(sha256=digest,code=(self.root/path).read_text()) for digest,path in [(admission.PARENT_SHA,admission.PARENT_SOURCE),(admission.SUPPORT_SHA,admission.SUPPORT)]}
        self.before=dict(programs={admission.PARENT:parent},program_inventory={admission.PARENT:copy.deepcopy(parent)},files=files,
            archive_paths={'old':'old'},benchmarks=[dict(key='spectralnorm',baseline_loc=9,baseline_seconds=.08,
                groups=[dict(language='prolog',programs=[admission.PARENT],fast=admission.PARENT,small=admission.PARENT,formatted_fast=None,formatted_small=None)])],
            reference_summary=[dict(lang='prolog',fast={},small={})],formatted_reference_summary=[dict(lang='prolog',fast=None,small=None)],
            unrelated_sentinel={'preserve':[1,2,3]})

    def test_complete_archived_proof_replays_without_ignored_runtime(self):
        self.assertFalse((self.root/admission.RUNTIME).exists())
        self.assertTrue((self.root/admission.qlf_path('blocks8-specialized')).exists())
        self.assertNotEqual(str(self.root),self.results['recorded_execution_root'])
        self.assertEqual(self.results['programs'][0]['samples_seconds'],[34.493370375,34.515944833,37.083872042])
        self.assertEqual(self.results['matched_evidence_observations'],6)
        self.assertEqual(self.results['required_work']['coefficient_calls_per_process'],1210000000)

    def test_addition_preserves_parent96_67_and_all_old_samples(self):
        old=copy.deepcopy(self.before);after=admission.append_catalog(self.before,self.root)
        self.assertEqual(self.before,old)
        for pool in ['programs','program_inventory','files','archive_paths']:
            for key,value in old[pool].items():self.assertEqual(after[pool][key],value)
        self.assertEqual(after['benchmarks'][0]['groups'][0]['fast'],admission.KEY)
        self.assertEqual(after['benchmarks'][0]['groups'][0]['small'],admission.PARENT)
        self.assertEqual(after['programs'][admission.KEY]['loc'],128)
        self.assertEqual(after['programs'][admission.KEY]['physical_loc'],87)
        self.assertEqual(after['programs'][admission.PARENT]['seconds'],179.423098959)
        self.assertEqual(after['formatted_reference_summary'],old['formatted_reference_summary'])
        self.assertEqual(after['unrelated_sentinel'],old['unrelated_sentinel'])

    def test_source_model_license_and_generic_support_boundaries_preserved(self):
        after=admission.append_catalog(self.before,self.root);row=after['programs'][admission.KEY]
        self.assertEqual(row['authorship'],admission.bound_authorship(after,row,self.root))
        self.assertEqual(row['authorship']['license'],self.before['programs'][admission.PARENT]['authorship']['license'])
        self.assertIsNone(row['authorship']['ai']['exact_model']);self.assertEqual(row['authorship']['ai']['models'],[])
        self.assertFalse(row['file_roles'][admission.SUPPORT_SHA]['included_in_application_loc'])
        self.assertEqual(row['file_roles'][admission.SOURCE_SHA]['normalized_loc'],128)
        row['source_provenance_record']['admission']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Unbound'):admission.bound_authorship(after,row,self.root)

    def test_stale_results_changed_parent_and_new_global_minimum_reject(self):
        changed=copy.deepcopy(self.results);changed['programs'][0]['median_seconds']=1.0;put(self.root,admission.RESULTS,changed)
        with self.assertRaisesRegex(ValueError,'Stale'):admission.append_catalog(self.before,self.root)
        put(self.root,admission.RESULTS,self.results);self.before['programs'][admission.PARENT]['loc']=128
        with self.assertRaisesRegex(ValueError,'parent'):admission.append_catalog(self.before,self.root)
        self.before['programs'][admission.PARENT]['loc']=96;self.before['benchmarks'][0]['baseline_seconds']=1000
        with self.assertRaisesRegex(ValueError,'normalization'):admission.append_catalog(self.before,self.root)

    def test_frozen_failed_evidence_is_not_resealed_by_new_admission_plan(self):
        path=admission.QUAL+'build-native-v1/report.json';document=admission.load(self.root/path);document['status']='PASSED';put(self.root,path,document)
        put(self.root,admission.PLAN,admission.make_plan(self.root))
        with self.assertRaises(ValueError):admission.reconcile(self.root,local_artifacts=False)

    def test_pending_final_pin_fails_before_reading_running_report(self):
        with mock.patch.object(admission,'FINAL_FULL_SHA',None):
            with self.assertRaisesRegex(ValueError,'pending final'):admission.make_plan(self.root)


class PrepareCLITests(unittest.TestCase):
    def test_prepare_rejects_concurrent_canonical_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);put(root,'data/benchmarks.json',{'old':'catalog'})
            def changed(before):
                put(root,'data/benchmarks.json',{'changed':'concurrently'});return {'preview':True}
            with mock.patch.object(admission,'ROOT',root),mock.patch.object(admission,'make_plan',return_value={}),mock.patch.object(admission,'reconcile',return_value={}),\
                 mock.patch.object(admission,'append_catalog',side_effect=changed),mock.patch.object(sys,'argv',['import_prolog_spectral.py','--prepare']):
                with self.assertRaisesRegex(ValueError,'Canonical changed'):admission.main()


class AuthorshipCitationTests(unittest.TestCase):
    def test_original_support_citation_is_inherited_exactly_and_independently(self):
        support=dict(source_sha256=admission.SUPPORT_SHA,
            url='https://github.com/mech-lang/benchmarks/blob/c95f-original/support/clbg_io.pl',
            relationship='original retained helper',extra={'original':['citation']})
        parent=dict(authorship=dict(retained_sources=[dict(source_sha256=admission.PARENT_SHA,url='original application'),support],
            license={'status':'unverified'}))
        evidence={name:dict(path=name,sha256='a'*64) for name in ['plan','results','ownership']}
        original=copy.deepcopy(parent)
        record=admission.authorship_record(parent,{},evidence)
        self.assertEqual(record['retained_sources'],[
            dict(source_sha256=admission.SOURCE_SHA,url='https://github.com/mech-lang/benchmarks/blob/'+admission.SOURCE_REVISION+'/'+admission.SOURCE),
            support])
        self.assertEqual(parent,original)
        record['retained_sources'][1]['extra']['original'].append('changed')
        self.assertEqual(parent,original)


if __name__=='__main__':unittest.main()
