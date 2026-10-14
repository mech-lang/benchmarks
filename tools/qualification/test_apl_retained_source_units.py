"""Pure source identity, written-closer and complete-owner regression checks."""
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('retained_apl_owners',HERE/'apl_retained_source_units.py')
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
INVENTORY=json.loads((ROOT/'experiments/shared/retained-coverage-audit-v1/report-inventory.json').read_bytes())
PATHS={v['recorded_source_sha256']:ROOT/v['source'] for w in INVENTORY['workloads']
       if w['language']=='apl' for v in w['subjects']}


class Owners(unittest.TestCase):
    def test_all_nine_complete_files_and_each_written_closer_are_owned(self):
        self.assertEqual(len(PATHS),len(a.SOURCES))
        for identity,(digest,total,closers) in a.SOURCES.items():
            with self.subTest(identity=identity):
                source=PATHS[digest].read_bytes()
                row=a.count_source(source,identity)
                self.assertEqual(row['canonical_loc'],total)
                self.assertEqual(row['written_function_closers'],closers)
                self.assertEqual(sum(x['kind']=='function-close' for x in row['source_owners']),closers)
                all_rows=[x['line'] for group in ('source_owners','excluded_rows') for x in row[group]]
                self.assertEqual(sorted(all_rows),list(range(1,len(source.decode().splitlines())+1)))
                self.assertIsNone(row['formatted_loc'])
                self.assertFalse(row['generic_language_certificate'])
                self.assertFalse(row['chart_admission'])

    def test_literals_do_not_invent_comments_assignments_or_statement_separators(self):
        self.assertEqual(a.code_without_literals_or_comment("A←'⍝⋄←''x' ⍝ comment"),'A←         ')
        with self.assertRaises(ValueError):a.code_without_literals_or_comment("A←'unfinished")

    def test_changed_source_never_gets_a_physical_count_fallback(self):
        identity='fannkuchredux';source=PATHS[a.SOURCES[identity][0]].read_bytes()
        for changed in (source.replace(b'Max',b'Min'),source+b'Extra\n',source.replace(b'\n',b'\r\n')):
            with self.assertRaises(ValueError):a.count_source(changed,identity)

    def test_wrong_identity_and_nonbytes_rejected(self):
        source=PATHS[a.SOURCES['fannkuchredux'][0]].read_bytes()
        for identity in ('fasta-compact','unknown'):
            with self.assertRaises(ValueError):a.count_source(source,identity)
        with self.assertRaises(ValueError):a.count_source(source.decode(),'fannkuchredux')


if __name__=='__main__':unittest.main()
