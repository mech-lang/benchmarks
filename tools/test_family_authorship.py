"""Reject invented model identities and stale source-bound family evidence."""
import copy
import json
import unittest

from verify_repository import ROOT, check_model_evidence


class FamilyAuthorship(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT/'data/benchmarks.json').read_text())
        cls.models = json.loads((ROOT/'data/source-model-evidence.json').read_text())['files']

    def test_known_family_is_bound_to_exact_application_and_admission(self):
        keys = ['knucleotide:array-bqn-occurrence-frame',
                'knucleotide:nim-knucleotide-preencoded-v1',
                'spectralnorm:array-bqn-native-sum', 'fasta:array-bqn-bins']
        for key in keys:
            row = self.data['programs'][key]
            check_model_evidence(ROOT, self.data, key, row, self.models)
            self.assertEqual(row['authorship']['ai']['models'], [])
            self.assertIsNone(row['authorship']['ai']['exact_model'])
            for field, value in [('models', ['invented-exact-model']),
                                 ('model_family', 'invented-family'),
                                 ('evidence', [])]:
                with self.subTest(key=key, field=field):
                    changed = copy.deepcopy(row)
                    changed['authorship']['ai'][field] = value
                    with self.assertRaisesRegex(ValueError, 'Authorship admission'):
                        check_model_evidence(ROOT, self.data, key, changed, self.models)
            changed = copy.deepcopy(row)
            changed['source_provenance_record']['source_sha256'] = '0'*64
            with self.assertRaises(ValueError):
                check_model_evidence(ROOT, self.data, key, changed, self.models)

    def test_family_cannot_be_transferred_to_an_archived_predecessor(self):
        key = 'knucleotide:array-bqn-faithful'
        row = copy.deepcopy(self.data['programs'][key])
        check_model_evidence(ROOT, self.data, key, row, self.models)
        row['authorship']['ai']['model_family'] = 'Codex GPT-6'
        with self.assertRaisesRegex(ValueError, 'Authorship model'):
            check_model_evidence(ROOT, self.data, key, row, self.models)


if __name__ == '__main__':
    unittest.main()
