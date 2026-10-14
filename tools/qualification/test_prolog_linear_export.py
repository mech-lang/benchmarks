"""Pure export tests: saved source/metadata with an explicitly synthetic future ledger."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


def load(file,name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


e=load('prolog_linear_export.py','tested_prolog_export')
f=load('test_prolog_linear_metadata.py','export_saved_metadata')


class Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f.Metadata.setUpClass();cls.plan=f.Metadata.plan;cls.previous=f.Metadata.previous
        cls.bytes={}
        for manifest in cls.plan['manifests'].values():
            for row in manifest['profiles'][:2]:
                for source in row['source_bundle']:
                    retained=e.retained_source(source,cls.previous['plan'],cls.plan['pins'])
                    raw=Path(retained['path']).read_bytes()
                    assert hashlib.sha256(raw).hexdigest()==retained['sha256']
                    cls.bytes[retained['path']]=raw

    def fixture(self,failure=None,absent_failed_output=False):
        args=f.t.fixture(self.plan,self.previous,failure=failure)
        if absent_failed_output:
            attempt=next(x for x in args['report']['attempts'] if not x['qualified'])
            copies=(attempt,args['raw'][attempt['result_path']],args['supervised'][attempt['supervisor_result_path']],
                    args['report']['programs'][failure]['full_failure'])
            for item in copies:
                item.update(error='synthetic runtime failure before complete output',error_type='RuntimeError')
                for field in ('stdout_bytes','stdout_sha256','seconds','validation'):item.pop(field,None)
        review=e.l.reconcile(**args)
        pins={**self.plan['pins'],**args['terminal']['available_evidence_pins'],
              str(e.METADATA):e.METADATA_SHA}
        for prefix in ('old_raw','old_supervised','old_outer'):
            for name in args[prefix]:pins[name]=self.previous['terminal']['available_evidence_pins'][name]
        review.update(status='full81-plus-retained9-reconciled-awaiting-runtime-and-publication-review',
            file_integrity_verified=True,verified_file_pins=pins,
            plan=e.ref(str(e.l.PLAN),e.l.PLAN_SHA),report=e.ref(self.plan['output']+'/report.json','1'*64),
            terminal=e.ref(self.plan['output']+'/terminal.json','2'*64))
        metadata=copy.deepcopy(f.Metadata.result)
        metadata.update(status='qualified-recorded-runtime-metadata',file_integrity_verified=True,
            runtime_publication_metadata_qualified=True,plan=review['plan'],verified_file_pins=dict(pins))
        metadata['profiles']=[v for v in metadata['profiles'] if review['profiles'][v['key']]['full_workload_qualified']]
        for row in metadata['profiles']:row['timing']=copy.deepcopy(review['profiles'][row['key']])
        raw=dict(self.bytes)
        for prefix in ('raw','supervised','outer','old_raw','old_supervised','old_outer'):
            raw.update({name:json.dumps(value).encode() for name,value in args[prefix].items()})
        return dict(plan=copy.deepcopy(self.plan),previous=copy.deepcopy(self.previous['plan']),
            review=review,metadata=metadata,read_raw=lambda name,digest:raw[name]),raw

    def test_exact20_two_cohorts_and_canonical_only(self):
        values,_=self.fixture();result=e.build_candidate(**values)
        self.assertEqual(len(result['program_inventory']),20)
        self.assertEqual(len(result['matched_mech_controls']),10)
        self.assertFalse(result['chart_admission'])
        self.assertFalse(result['dataset_files_changed'])
        for row in result['program_inventory'].values():
            self.assertIsNone(row['formatted_loc'])
            self.assertFalse(row['formatted_loc_qualified'])
            self.assertEqual(row['loc'],sum(v['normalized_loc'] for v in row['file_roles'].values()))
            for sample in row['sample_execution_metadata']:
                old=row['benchmark']=='regexredux'
                self.assertEqual(sample['attempt_cohort'],'preserved-full90' if old else 'linear-full81')
                self.assertIn('/full90-v1/' if old else '/full81-linear-v1/',sample['producer_report']['path'])
        self.assertEqual(result['program_inventory']['revcomp:prolog-revcomp-linear-optimized']['source_alias_of'],
                         'prolog-revcomp-linear-compact')

    def test_failed_subject_kept_without_median_or_endpoint(self):
        key='pidigits:prolog-pidigits-compact';values,_=self.fixture(key);result=e.build_candidate(**values)
        row=result['program_inventory'][key]
        self.assertIsNone(row['seconds']);self.assertIsNone(row['timing_sd'])
        self.assertEqual(len(row['sample_execution_metadata']),1)
        self.assertIn(row['id'],result['excluded_profiles'])
        self.assertNotIn(key,result['endpoint_proposals']['pidigits']['programs'])

    def test_failed_control_excludes_both_aliases(self):
        values,_=self.fixture('pidigits:prolog-full-study:mech-control');result=e.build_candidate(**values)
        self.assertEqual(result['endpoint_proposals']['pidigits']['programs'],[])
        for row in result['program_inventory'].values():
            if row['benchmark']=='pidigits':
                self.assertTrue(row['full_workload_qualified'])
                self.assertFalse(row['eligible_for_publication_review'])
                self.assertIsNone(row['time_ratio_to_matched_mech'])

    def test_failed_subject_without_complete_output_retains_nulls(self):
        key='pidigits:prolog-pidigits-compact';values,_=self.fixture(key,True)
        row=e.build_candidate(**values)['program_inventory'][key]
        sample=row['sample_execution_metadata'][0]
        self.assertFalse(sample['qualified'])
        for field in ('stdout_bytes','stdout_sha256','seconds','validation'):self.assertIsNone(sample[field])
        self.assertIsNone(row['seconds'])

    def test_failed_control_without_complete_output_retains_nulls(self):
        values,_=self.fixture('pidigits:prolog-full-study:mech-control',True)
        candidate=e.build_candidate(**values)
        sample=candidate['matched_mech_controls']['pidigits']['sample_execution_metadata'][0]
        self.assertFalse(sample['qualified'])
        for field in ('stdout_bytes','stdout_sha256','seconds','validation'):self.assertIsNone(sample[field])
        self.assertEqual(candidate['endpoint_proposals']['pidigits']['programs'],[])

    def test_unqualified_runtime_rejected(self):
        values,_=self.fixture();values['metadata']['runtime_publication_metadata_qualified']=False
        with self.assertRaises((AssertionError,ValueError)):e.build_candidate(**values)

    def test_wrong_cohort_rejected(self):
        values,_=self.fixture();values['review']['profiles']['regexredux:prolog-regexredux-compact']['attempt_cohort']='linear-full81'
        with self.assertRaises((AssertionError,ValueError)):e.build_candidate(**values)

    def test_edited_compiler_source_rejected(self):
        values,raw=self.fixture();name=next(iter(raw));raw[name]+=b'\n'
        with self.assertRaises((AssertionError,ValueError)):e.build_candidate(**values)

    def test_editorial_source_relocation_rejected(self):
        values,_=self.fixture();name=values['plan']['manifests']['pidigits']['profiles'][0]['source_bundle'][0]['path']
        values['previous']['path_reconciliation'][name]['editorial_substitution']='rewrite'
        with self.assertRaises((AssertionError,ValueError)):e.build_candidate(**values)

    def test_source_hash_dedup_retains_per_form_ownership(self):
        values,_=self.fixture();result=e.build_candidate(**values)
        self.assertLess(len(result['files']),sum(len(v['files']) for v in result['program_inventory'].values()))
        for row in result['program_inventory'].values():
            self.assertEqual(set(row['files']),set(row['file_roles']))


if __name__=='__main__':unittest.main()
