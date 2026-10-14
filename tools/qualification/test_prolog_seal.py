"""Focused integrity check: successful-looking altered closures are rejected."""
import importlib.util
import gzip
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('prolog_seal', Path(__file__).with_name('prolog_seal.py'))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ClosureIntegrityTest(unittest.TestCase):
    def test_native_gzip_bytes_and_added_archive_compression_are_distinct(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'migration').mkdir()
            (root/'migration/reorganization-paths.tsv').write_text('original_path\tcurrent_path\n')
            payload = b'{"source_archive_fixture":true}\n'
            native = root/'native.tar.gz'
            archived_json = root/'receipt.json.gz'
            native.write_bytes(gzip.compress(payload))
            archived_json.write_bytes(gzip.compress(payload))
            evidence = MODULE.Evidence(root, {'substitutions': []})
            self.assertEqual(evidence.read_bytes(str(native), MODULE.digest(native.read_bytes())), native.read_bytes())
            self.assertEqual(evidence.read_bytes(str(root/'receipt.json'), MODULE.digest(payload)), payload)

    def test_changed_owner_and_replay_receipts_are_rejected(self):
        spec = json.loads((ROOT/'experiments/prolog/owner-review-spec.json').read_text())
        resolver = MODULE.Evidence(ROOT, {'substitutions': []})
        keys = [MODULE.OWNER+'terminal.json', MODULE.REPLAY.replace('replay.json','terminal.json')]
        for historical in keys:
            with self.subTest(receipt=historical), tempfile.TemporaryDirectory() as folder:
                raw = resolver.path(historical).read_bytes()
                expected = spec['original_replay_closure_pins'][historical]
                self.assertEqual(MODULE.digest(raw), expected)
                value = json.loads(raw)
                # Keep the successful status, but change the evidence it authenticates.
                if 'command_pid' in value:
                    value['command_pid'] += 1
                else:
                    value['replay_sha256'] = '0'*64
                root = Path(folder)
                (root/'migration').mkdir()
                relative = 'benchmarks/clbg/'+historical.split('/benchmarks/clbg/',1)[1]
                (root/'migration/reorganization-paths.tsv').write_text(
                    'original_path\tcurrent_path\n'+relative+'\treceipt.json\n')
                (root/'receipt.json').write_text(json.dumps(value))
                changed = MODULE.Evidence(root, {'substitutions': []})
                with self.assertRaises(AssertionError):
                    changed.read(historical, expected)


if __name__ == '__main__':
    unittest.main()
