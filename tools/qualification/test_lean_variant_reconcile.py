"""Pure normalized-owner replay checks; no native execution or real data edits."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from lean_variant_reconcile import replay_counts


class Replay(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root/'source';self.source.mkdir()
        self.counts_path = self.root/'qualified-counts.json'
        self.build_path = self.root/'build.json'
        self.build = dict(source_directory=str(self.source),sources={},profiles={})
        self.counts = dict(status='QUALIFIED_FOR_RETAINED_SOURCE_BUNDLES',sources={},units={},profiles={})
        self.records = []
        for i in range(10):
            name = f'case{i}.lean';path=self.source/name
            raw = 'def text := "λ"\ndef value := do let x := 1; pure x\n'.encode()
            path.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest()
            self.build['sources'][str(path)] = digest
            self.build['profiles'][str(i)] = dict(files=[name])
            self.counts['units'][name] = dict(sha256=digest,canonical_loc=3,physical_loc=2)
            self.counts['profiles'][str(i)] = dict(files=[name],canonical_loc=3)
            self.records.append(dict(source=str(path),tokens=[dict(start=0,end=len(raw)-1)],
                do_statements=[dict(start=raw.index(b'let x')),dict(start=raw.index(b'pure x'))]))
        self.counts['sources'] = copy.deepcopy(self.build['sources'])
        self.build_path.write_text(json.dumps(self.build))
        self.counts['build_report_sha256'] = hashlib.sha256(self.build_path.read_bytes()).hexdigest()

    def run_replay(self):
        self.counts_path.write_text(json.dumps(self.counts))
        (self.root/'native-reader.stdout').write_text(''.join(json.dumps(r)+'\n' for r in self.records))
        return replay_counts(self.counts_path,self.build,self.build_path)

    def test_utf8_positions_and_packed_statements(self):
        _,receipt=self.run_replay()
        self.assertEqual(receipt['status'],'PASSED')
        self.assertEqual(len(receipt['native_lean_units_replayed']),10)

    def test_reject_line_packing_discount(self):
        self.counts['units']['case0.lean']['canonical_loc']=2
        with self.assertRaises(AssertionError):self.run_replay()

    def test_reject_invalid_native_offset(self):
        self.records[0]['tokens'][0]['end']=10000
        with self.assertRaises(AssertionError):self.run_replay()

    def test_reject_incomplete_profile_bundle(self):
        self.counts['profiles']['0']['files']=[]
        with self.assertRaises(AssertionError):self.run_replay()


if __name__ == '__main__':
    unittest.main()
