"""Pure candidate identity, alias and original-measurement preservation tests."""
import copy
import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent


def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


e=load('uiua_retained_export_test','export_uiua_retained.py')
t=load('uiua_retained_export_fixture','test_uiua_retained_reconcile.py')


class Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        values=t.fixture();cls.sources=values['sources']
        cls.review=t.r.reconcile(**values,modules=t.MODULES)
        cls.review.update(status='fifteen-retained-observations-file-verified-awaiting-publication',
            file_integrity_verified=True,common_mutex_held=True,
            report=dict(path=str(t.r.ARCHIVE/'results/timings-uiua.json'),sha256=t.r.REPORT_SHA),
            source_audit=dict(path=str(t.r.ARCHIVE/'source-audit-uiua.json'),sha256=t.r.AUDIT_SHA),
            count_approval=dict(path=str(t.r.COUNT_APPROVAL),sha256=t.r.COUNT_APPROVAL_SHA))

    def test_exact_sources_and_alias_preserve_every_measurement(self):
        before=copy.deepcopy(self.review)
        result=e.build_candidate(self.review,self.sources)
        self.assertEqual(before,self.review)
        self.assertEqual(len(result['program_inventory']),4)
        self.assertEqual(len(result['files']),3)
        self.assertEqual(sum(p['native_observations'] for p in result['program_inventory'].values()),9)
        self.assertEqual(result['retained_control_native_observations'],6)
        self.assertEqual(result['preserved_environmental_exclusion'],self.review['excluded_attempt'])
        for key,row in result['program_inventory'].items():
            original=self.review['profiles'][key]
            self.assertEqual(row['samples'],original['samples_seconds'])
            self.assertEqual(row['seconds'],original['median_seconds'])
            self.assertEqual(row['timing_sd'],original['sample_stdev_seconds'])
            self.assertEqual(row['sample_evidence'],original['sample_evidence'])
            self.assertEqual(row['runtime'],original['original_profile']['runtime'])
            self.assertEqual(row['runtime_arguments'],original['original_profile']['command'])
            self.assertEqual(row['loc'],15 if row['benchmark']=='binarytrees' else 21)
            self.assertIsNone(row['formatted_loc'])
            self.assertFalse(row['eligible_for_chart'])
        alias=result['program_inventory'][t.r.TREE_ALIAS]
        self.assertEqual(alias['timing_alias_of'],t.r.TREE)
        self.assertEqual(alias['native_observations'],0)
        self.assertEqual(len(result['files'][alias['source_sha256']]['source_paths']),2)
        self.assertFalse(result['dataset_files_changed'])
        self.assertEqual(result['native_processes_started'],0)

    def test_unverified_or_changed_native_scope_cannot_export(self):
        for field,value in [('file_integrity_verified',False),('native_processes_started',1),
                            ('subject_native_observations',12),('timing_aliases',0),
                            ('canonical_loc_qualified',False),('source_work_qualified',False)]:
            review=copy.deepcopy(self.review);review[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):e.build_candidate(review,self.sources)

    def test_changed_bytes_count_or_alias_measurement_is_rejected(self):
        for mutation in ('source','count','alias-native','alias-sample'):
            review=copy.deepcopy(self.review);sources=copy.deepcopy(self.sources)
            if mutation=='source':sources[t.r.TREE]+=b'changed'
            elif mutation=='count':review['profiles'][t.r.TREE]['canonical_source_count']['canonical_loc']=14
            elif mutation=='alias-native':review['profiles'][t.r.TREE_ALIAS]['native_observations']=3
            else:review['profiles'][t.r.TREE_ALIAS]['samples_seconds'][0]+=1
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):e.build_candidate(review,sources)

    def test_non_repository_public_evidence_reference_is_rejected(self):
        review=copy.deepcopy(self.review);review['count_approval']['path']='/tmp/unretained-counts.json'
        with self.assertRaises(ValueError):e.build_candidate(review,self.sources)


if __name__=='__main__':unittest.main()
