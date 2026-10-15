"""Pure binding faults; no source counting, native execution or file admission."""
from copy import deepcopy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('reviewed_count_binding', HERE / 'rebol_regex_reviewed_count_ledger.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def fixture():
    sources = {name: dict(path=path, reviewed_source_sha256=None,
                         rows={'S': '1'}, packed={2: (('S', 'value'),)})
               for name, path in b.PATHS.items()}
    sources['regexredux']['path'] = b.ORIGINAL_REGEX_PATH
    bundles = {name: (name, 'io', 'loader', 'extension') +
               (('big',) if name == 'pidigits' else ('regex',) if name == 'regexredux' else ())
               for name in b.WORKLOADS}
    ledger = SimpleNamespace(RULE=b.RULE, SOURCES=sources, BUNDLES=bundles,
                             KINDS={'S': ('statement', 1)}, DECISIONS={'policy': 'retained'},
                             ORIGINAL_C='old.c', CORRECTED_C=b.PATHS['extension'],
                             ORIGINAL_FANN='old.reb', CORRECTED_FANN=b.PATHS['fannkuchredux'])
    reviewed = {name: dict(path=str(b.ROOT / path), sha256=f'{i:064x}',
                          canonical_loc=i + 2, physical_loc=i + 1)
                for i, (name, path) in enumerate(b.PATHS.items(), 1)}
    reviewed['regexredux']['sha256'] = b.CORRECTED_REGEX_SHA
    review = dict(corrected_regex_substitution=deepcopy(b.REGEX_SUBSTITUTION), schema='rebol15-independent-source-count-review-v1',
                  status='qualified-exact-fifteen-source-owner-counts',
                  independent_review=True, canonical_LOC_admitted=True, rule_version=b.RULE,
                  references={
                      'proposal': dict(path=str(b.ROOT / 'experiments/rebol/regex-literals-v1/source-counts-v1/proposal-v1.json'), sha256='1' * 64),
                      'rule': dict(path=str(b.ROOT / 'archive/validation/loc-normalization/20261012/PLAN.md'), sha256='2' * 64)},
                  sources=reviewed,
                  bundles={name: dict(members=list(members),
                                     canonical_loc=sum(reviewed[i]['canonical_loc'] for i in members),
                                     physical_loc=sum(reviewed[i]['physical_loc'] for i in members))
                           for name, members in bundles.items()},
                  **{gate: False for gate in b.FALSE_GATES})
    return ledger, review


class ReviewedLedgerTests(unittest.TestCase):
    def test_binds_only_reviewed_path_and_digests_and_isolates_original_data(self):
        ledger, review = fixture()
        original = deepcopy(vars(ledger)); original_review = deepcopy(review)
        bound = b.bind_ledger(ledger, review)
        for name in b.PATHS:
            self.assertEqual(bound.SOURCES[name]['reviewed_source_sha256'], review['sources'][name]['sha256'])
            restored = deepcopy(bound.SOURCES[name]); restored['reviewed_source_sha256'] = None
            if name == 'regexredux':
                self.assertEqual(restored['path'], b.PATHS[name])
                restored['path'] = b.ORIGINAL_REGEX_PATH
            self.assertEqual(restored, original['SOURCES'][name])
        self.assertEqual(vars(ledger), original)
        self.assertEqual(review, original_review)
        bound.SOURCES['io']['rows']['S'] = '99'
        bound.DECISIONS['policy'] = 'changed'
        self.assertEqual(vars(ledger), original)

    def test_existing_equal_digest_is_allowed_but_different_digest_rejects(self):
        ledger, review = fixture()
        ledger.SOURCES['io']['reviewed_source_sha256'] = review['sources']['io']['sha256']
        b.bind_ledger(ledger, review)
        review['sources']['io']['sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'Existing approved source digest'):
            b.bind_ledger(ledger, review)

    def test_missing_extra_or_renamed_source_identity_rejects(self):
        for which in ('ledger-missing', 'review-missing', 'review-extra', 'review-renamed'):
            ledger, review = fixture()
            if which == 'ledger-missing': ledger.SOURCES.pop('io')
            elif which == 'review-missing': review['sources'].pop('io')
            elif which == 'review-extra': review['sources']['extra'] = deepcopy(review['sources']['io'])
            else: review['sources']['other'] = review['sources'].pop('io')
            with self.subTest(which=which), self.assertRaisesRegex(ValueError, 'fifteen'):
                b.bind_ledger(ledger, review)

    def test_swapped_original_or_reviewed_paths_reject(self):
        for which in ('ledger', 'review', 'original-fann'):
            ledger, review = fixture()
            if which == 'ledger': ledger.SOURCES['io']['path'] = b.PATHS['loader']
            elif which == 'review': review['sources']['io']['path'] = str(b.ROOT / b.PATHS['loader'])
            else: review['sources']['fannkuchredux']['path'] = str(b.ROOT / b.BASE / 'sources/fannkuchredux/main.reb')
            with self.subTest(which=which), self.assertRaises(ValueError): b.bind_ledger(ledger, review)

    def test_invalid_or_missing_sha_rejects_without_partial_original_mutation(self):
        for value in (None, '', 'a' * 63, 'G' * 64, 123, True):
            ledger, review = fixture(); before = deepcopy(vars(ledger))
            review['sources']['extension']['sha256'] = value
            with self.subTest(value=value), self.assertRaises(ValueError): b.bind_ledger(ledger, review)
            self.assertEqual(vars(ledger), before)
        ledger, review = fixture(); del review['sources']['io']['sha256']
        with self.assertRaises(ValueError): b.bind_ledger(ledger, review)

    def test_rule_admission_or_scope_changes_reject(self):
        for key, value in [('rule_version', 'other'), ('independent_review', 1),
                           ('canonical_LOC_admitted', False), ('schema', 'other'),
                           ('status', 'unreviewed')] + [(gate, True) for gate in b.FALSE_GATES]:
            ledger, review = fixture(); review[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): b.bind_ledger(ledger, review)
        ledger, review = fixture(); ledger.RULE = 'other'
        with self.assertRaises(ValueError): b.bind_ledger(ledger, review)

    def test_reference_identity_or_missing_authority_rejects(self):
        for which in ('missing', 'extra', 'path', 'sha'):
            ledger, review = fixture()
            if which == 'missing': review['references'].pop('rule')
            elif which == 'extra': review['references']['other'] = review['references']['rule'].copy()
            elif which == 'path': review['references']['proposal']['path'] += '.other'
            else: review['references']['rule']['sha256'] = 'invalid'
            with self.subTest(which=which), self.assertRaises(ValueError): b.bind_ledger(ledger, review)

    def test_invalid_counts_members_or_bundle_totals_reject(self):
        for which in ('count', 'bool', 'members', 'total', 'missing', 'ledger'):
            ledger, review = fixture()
            if which == 'count': review['sources']['io']['canonical_loc'] = 0
            elif which == 'bool': review['sources']['io']['physical_loc'] = True
            elif which == 'members': review['bundles']['pidigits']['members'].append('big')
            elif which == 'total': review['bundles']['pidigits']['canonical_loc'] += 1
            elif which == 'missing': review['bundles'].pop('fasta')
            else: ledger.BUNDLES['fasta'] += ('regex',)
            with self.subTest(which=which), self.assertRaises(ValueError): b.bind_ledger(ledger, review)


    def test_only_exact_old_regex_approval_can_be_replaced(self):
        ledger, review = fixture()
        ledger.SOURCES['regexredux']['reviewed_source_sha256'] = b.ORIGINAL_REGEX_SHA
        bound = b.bind_ledger(ledger, review)
        self.assertEqual(bound.SOURCES['regexredux']['reviewed_source_sha256'], b.CORRECTED_REGEX_SHA)
        self.assertEqual(ledger.SOURCES['regexredux']['reviewed_source_sha256'], b.ORIGINAL_REGEX_SHA)
        ledger.SOURCES['regexredux']['reviewed_source_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'Original regex'):
            b.bind_ledger(ledger, review)

    def test_corrected_regex_identity_and_substitution_are_exact(self):
        for which in ('old-digest', 'other-digest', 'old-path', 'old-proposal', 'substitution', 'missing'):
            ledger, review = fixture()
            if which == 'old-digest': review['sources']['regexredux']['sha256'] = b.ORIGINAL_REGEX_SHA
            elif which == 'other-digest': review['sources']['regexredux']['sha256'] = 'f' * 64
            elif which == 'old-path': review['sources']['regexredux']['path'] = str(b.ROOT / b.ORIGINAL_REGEX_PATH)
            elif which == 'old-proposal': review['references']['proposal']['path'] = str(b.ROOT / 'experiments/rebol/source-counts-v1/proposal-v1.json')
            elif which == 'substitution': review['corrected_regex_substitution']['count_both_revisions'] = True
            else: review.pop('corrected_regex_substitution')
            with self.subTest(which=which), self.assertRaises(ValueError): b.bind_ledger(ledger, review)


if __name__ == '__main__':
    unittest.main()
