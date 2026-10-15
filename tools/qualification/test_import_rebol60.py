"""Focused full60 catalog and transaction checks using invented evidence."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import unittest


def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


HERE=Path(__file__).resolve().parent
m=load('rebol60_import_tests',HERE/'import_rebol60.py')
x=load('rebol60_import_export_fixture',HERE/'test_rebol_export60.py')
templates=load('rebol60_import_transaction_fixtures',HERE/'test_import_rebol.py')
# Reuse only synthetic catalog and transaction fixtures; no old tests execute.
templates.m=m;templates.x=x;templates.e=x.e
fixture=templates.fixture
publish_fixture=templates.publish_fixture


class Import60(unittest.TestCase):
    def test_ten_programs_fifteen_sources_single_endpoints_and_existing_rows(self):
        f=fixture();prepared,audit,links=m.build_publication(f.originals,f.candidate,f.release,f.refs,f.plan)
        data=json.loads(prepared[m.TARGETS[0]])
        rows=[v for v in data['program_inventory'].values() if v['language']=='rebol3']
        self.assertEqual((audit['imported_program_inventory'],len(rows)),(10,10))
        self.assertEqual((audit['planned_rebol_samples'],audit['planned_matched_mech_samples']),(30,30))
        self.assertEqual(len({r['source_path'] for row in rows for r in row['file_roles'].values()}),15)
        self.assertTrue(all(row['source_alias_of'] is row['timing_alias_of'] is None for row in rows))
        for endpoints in audit['endpoints'].values():
            self.assertEqual(endpoints['fast'],endpoints['small'])
            self.assertEqual(endpoints['programs'],[endpoints['fast']])
        for field in ('programs','program_inventory','files','archive_paths'):
            self.assertEqual({k:data[field][k] for k in f.data[field]},f.data[field])
        self.assertFalse(audit['baseline_changed'])
        self.assertTrue(all(row['formatted_x'] is None for row in rows))
        self.assertIn('30 planned subject and 30 matched control',data['protocol']['rebol3'])
        self.assertIn(Path(f.candidate['cohort_policy_file']['path']).relative_to(m.ROOT).as_posix(),links)

    def test_failed_subject_or_control_keeps_raw_and_excludes_only_workload(self):
        for identity in ('rebol-pidigits-compact','pidigits:rebol-full-study:mech-control'):
            f=fixture(identity);prepared,audit,_=m.build_publication(f.originals,f.candidate,f.release,f.refs,f.plan)
            data=json.loads(prepared[m.TARGETS[0]]);row=data['program_inventory']['pidigits:rebol-pidigits-compact']
            self.assertFalse(row['eligible_for_chart']);self.assertIsNone(row['x']);self.assertIsNone(row['y'])
            self.assertIsNone(row['time_ratio_to_matched_mech'])
            self.assertNotIn('pidigits',audit['admitted_workloads']);self.assertEqual(len(audit['admitted_workloads']),9)
            self.assertEqual(row['sample_execution_metadata'],m.public_values(
                f.candidate['program_inventory'][row['key']]['sample_execution_metadata'],{}))
            self.assertEqual(audit['endpoints']['pidigits']['programs'],[])

    def test_two_form_policy_aliases_and_wrong_cohort_reject(self):
        for fault in ('schema','count','samples','subject_policy','cohort','extra','source_alias','timing_alias'):
            f=fixture();candidate=f.candidate
            if fault=='schema':candidate['schema']='rebol-full90-publication-candidate-v1'
            elif fault=='count':candidate['source_forms']=20
            elif fault=='samples':candidate['planned_rebol_samples']=60
            elif fault=='subject_policy':candidate['subject_policy']['publication_forms'].append('optimized')
            elif fault=='cohort':candidate['cohort_policy_file']['sha256']='0'*64
            elif fault=='extra':candidate['program_inventory']['pidigits:rebol-pidigits-optimized']=copy.deepcopy(
                candidate['program_inventory']['pidigits:rebol-pidigits-compact'])
            else:candidate['program_inventory']['pidigits:rebol-pidigits-compact'][fault+'_of']='different-program'
            with self.subTest(fault=fault),self.assertRaises(AssertionError):
                m.build_publication(f.originals,candidate,f.release,f.refs,f.plan)

    def test_new_minimum_rejects_without_rewriting_existing_baselines(self):
        for field in ('baseline_loc','baseline_seconds'):
            f=fixture();changed=copy.deepcopy(f.data);changed['benchmarks'][0][field]=1000
            f.originals[m.TARGETS[0]]=m.encoded(changed)
            with self.assertRaisesRegex(AssertionError,'minimum'):
                m.build_publication(f.originals,f.candidate,f.release,f.refs,f.plan)

    def test_physical_runtime_identity_and_historical_control_paths_preserved(self):
        f=fixture();control=f.candidate['matched_mech_controls']['pidigits']
        control['original_profile']=dict(algorithm=dict(evidence=['../../hosts/gpu/src/control/runtime.rs']))
        public,_,_=m.public_candidate(f.candidate,f.refs)
        self.assertEqual(public['qualified_runtime'],f.candidate['qualified_runtime'])
        self.assertEqual(public['matched_mech_controls']['pidigits']['original_profile'],control['original_profile'])
        self.assertEqual(public['program_inventory']['pidigits:rebol-pidigits-compact']['extension_image'],
            f.candidate['program_inventory']['pidigits:rebol-pidigits-compact']['extension_image'])

    def test_exact_preview_and_apply_with_new_candidate(self):
        for apply in (False,True):
            with publish_fixture(apply=apply) as (f,args,old,events,prepared):
                receipt=m.publish(args);self.assertIs(receipt['applied'],apply)
                self.assertEqual(receipt['imported_program_inventory'],10)
                for name in m.TARGETS:
                    self.assertEqual((args.publication_root/name).read_bytes(),prepared[name] if apply else f.originals[name])
                    self.assertEqual((args.output/name).read_bytes(),prepared[name])
                self.assertEqual(events,['held','released'])

    def test_late_evidence_failure_rolls_back_before_release(self):
        def late(f,args):f.content[f.refs['metadata']['path']]=b'changed source evidence'
        with publish_fixture(late=late) as (f,args,old,events,prepared):
            with self.assertRaises(AssertionError):m.publish(args)
            self.assertEqual(events,['held','cleanup-held','released']);self.assertFalse(args.output.exists())
            for name in m.TARGETS:self.assertEqual((args.publication_root/name).read_bytes(),f.originals[name])

    def test_transaction_and_cleanup_functions_are_unchanged(self):
        def functions(path):
            return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(path.read_text()).body
                    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
        original=functions(HERE/'import_rebol.py');current=functions(Path(m.__file__))
        for name in ('publish','load_transaction','restore_owned','verify_owned','lease_stat','atomic',
                     'destination','write_owned','verify_links','named_leases','release_contract'):
            with self.subTest(function=name):self.assertEqual(current[name],original[name])


if __name__=='__main__':unittest.main()
