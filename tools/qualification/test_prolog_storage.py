"""Small storage integrity regression; no native processes or seal replays."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('prolog_storage', Path(__file__).with_name('prolog_storage.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StorageIntegrity(unittest.TestCase):
    def test_declared_gzip_and_immutable_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = b'{"durable_pid": 241, "exit_status": 0}\n'
            stored = gzip.compress(raw, mtime=0)
            digest = lambda data: hashlib.sha256(data).hexdigest()
            (root / 'receipt.json.gz').write_bytes(stored)
            value = dict(schema='declared-exact-gzip-storage-v1', original_content_unchanged=True,
                historical_receipts_unchanged=True, compression=dict(format='gzip',mtime=0,filename='',compresslevel=9),
                artifacts=[dict(logical_path='receipt.json', stored_path='receipt.json.gz', storage_encoding='gzip',
                    original_sha256=digest(raw), stored_sha256=digest(stored), original_bytes=len(raw), stored_bytes=len(stored))])
            manifest = root / 'storage.json'
            manifest.write_text(json.dumps(value))
            reader = module.Storage(root, manifest, digest(manifest.read_bytes()))
            self.assertEqual(reader.read_bytes(root / 'receipt.json', digest(raw)), raw)
            # A recompressed successful receipt with an altered owner fails.
            (root / 'receipt.json.gz').write_bytes(gzip.compress(raw.replace(b'241', b'242'), mtime=0))
            with self.assertRaises(AssertionError):
                reader.read(root / 'receipt.json', digest(raw))
            # Native archive bytes have no declared added compression.
            archive = root / 'runtime.tar.gz'
            archive.write_bytes(stored)
            self.assertEqual(reader.read_bytes(archive, digest(stored)), stored)


if __name__ == '__main__':
    unittest.main()
