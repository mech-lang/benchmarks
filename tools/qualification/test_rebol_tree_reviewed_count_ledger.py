"""Final main bindings and unchanged exact-owner policy; no native work."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

b=load('final_tree_count_binding',HERE/'rebol_tree_reviewed_count_ledger.py')
previous=load('prior_regex_count_fixture',HERE/'test_rebol_regex_reviewed_count_ledger.py')
c=load('original_rebol_source_counter',HERE/'rebol_source_units.py')

def fixture():
    ledger,review=previous.fixture()
    review['references']['proposal']['path']=str(b.ROOT/'experiments/rebol/tree-leaves-v1/source-counts-v1/proposal-v1.json')
    review['corrected_tree_substitution']=deepcopy(b.TREE_SUBSTITUTION)
    review['sources']['binarytrees'].update(path=str(b.ROOT/b.PATHS['binarytrees']),sha256=b.CORRECTED_TREE_SHA)
    return ledger,review

class FinalMainBindingTests(unittest.TestCase):
    def test_two_substitutions_only_and_original_owners_remain_isolated(self):
        ledger,review=fixture();before=deepcopy(vars(ledger));saved=deepcopy(review)
        bound=b.bind_ledger(ledger,review)
        self.assertEqual(vars(ledger),before);self.assertEqual(review,saved)
        for name in b.PATHS:
            actual=deepcopy(bound.SOURCES[name]);self.assertEqual(actual.pop('reviewed_source_sha256'),review['sources'][name]['sha256'])
            expected=deepcopy(before['SOURCES'][name]);expected.pop('reviewed_source_sha256')
            if name in ('binarytrees','regexredux'):expected['path']=b.PATHS[name]
            self.assertEqual(actual,expected)
        bound.SOURCES['binarytrees']['rows']['S']='99';bound.DECISIONS['policy']='changed'
        self.assertEqual(vars(ledger),before)

    def test_exact_old_tree_digest_may_change_unknown_approval_cannot(self):
        ledger,review=fixture();ledger.SOURCES['binarytrees']['reviewed_source_sha256']=b.ORIGINAL_TREE_SHA
        bound=b.bind_ledger(ledger,review)
        self.assertEqual(bound.SOURCES['binarytrees']['reviewed_source_sha256'],b.CORRECTED_TREE_SHA)
        self.assertEqual(ledger.SOURCES['binarytrees']['reviewed_source_sha256'],b.ORIGINAL_TREE_SHA)
        for wrong in ('f'*64,b.CORRECTED_TREE_SHA):
            ledger.SOURCES['binarytrees']['reviewed_source_sha256']=wrong
            with self.subTest(wrong=wrong),self.assertRaisesRegex(ValueError,'Original tree'):
                b.bind_ledger(ledger,review)

    def test_tree_identity_route_and_double_counting_are_rejected(self):
        for change in ('old-path','old-digest','other-digest','regex-proposal','missing','count-both','modified'):
            ledger,review=fixture()
            if change=='old-path':review['sources']['binarytrees']['path']=str(b.ROOT/b.ORIGINAL_TREE_PATH)
            elif change=='old-digest':review['sources']['binarytrees']['sha256']=b.ORIGINAL_TREE_SHA
            elif change=='other-digest':review['sources']['binarytrees']['sha256']='f'*64
            elif change=='regex-proposal':review['references']['proposal']['path']=str(b.ROOT/'experiments/rebol/regex-literals-v1/source-counts-v1/proposal-v1.json')
            elif change=='missing':review.pop('corrected_tree_substitution')
            elif change=='count-both':review['corrected_tree_substitution']['count_both_revisions']=True
            else:review['corrected_tree_substitution']['original_modified']=True
            with self.subTest(change=change),self.assertRaises(ValueError):b.bind_ledger(ledger,review)

    def test_regex_other_sources_admission_and_bundle_guards_remain(self):
        for change in ('regex','missing-source','unknown-io','false-count','duplicate-member','wrong-total','scope','unreviewed'):
            ledger,review=fixture()
            if change=='regex':review['sources']['regexredux']['sha256']=b.ORIGINAL_REGEX_SHA
            elif change=='missing-source':review['sources'].pop('loader')
            elif change=='unknown-io':ledger.SOURCES['io']['reviewed_source_sha256']='f'*64
            elif change=='false-count':review['sources']['binarytrees']['canonical_loc']=True
            elif change=='duplicate-member':review['bundles']['binarytrees']['members'].append('binarytrees')
            elif change=='wrong-total':review['bundles']['binarytrees']['canonical_loc']+=1
            elif change=='scope':review['full_timing_qualified']=True
            else:review['canonical_LOC_admitted']=False
            with self.subTest(change=change),self.assertRaises(ValueError):b.bind_ledger(ledger,review)

    def test_actual_tree_owner_rows_and_rule_are_unchanged(self):
        ledger=c.load_ledger();spec=deepcopy(ledger.SOURCES['binarytrees'])
        before=c.project(c.regular_source(b.ROOT,spec['path']),spec,ledger.KINDS)
        spec['path']=b.PATHS['binarytrees']
        after=c.project(c.regular_source(b.ROOT,spec['path']),spec,ledger.KINDS)
        self.assertEqual((after['canonical_loc'],after['physical_loc']),(34,32))
        self.assertEqual(after['row_totals'],before['row_totals'])
        self.assertEqual([(x['line'],x['last_line'],x['tag'],x['canonical_units']) for x in after['source_owners']],
                         [(x['line'],x['last_line'],x['tag'],x['canonical_units']) for x in before['source_owners']])
        changed=[new['line'] for old,new in zip(before['source_owners'],after['source_owners']) if old['text']!=new['text']]
        self.assertEqual(changed,[2,5])
        self.assertEqual(after['unowned_significant_characters'],[])
        self.assertFalse(after['canonical_LOC_admitted']);self.assertIsNone(after['formatted_loc'])
        self.assertEqual(ledger.SOURCES['binarytrees']['path'],b.ORIGINAL_TREE_PATH)
        self.assertIsNone(ledger.SOURCES['binarytrees']['reviewed_source_sha256'])

if __name__=='__main__':unittest.main()
