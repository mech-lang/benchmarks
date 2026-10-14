"""Read explicitly declared exact gzip representations of immutable JSON."""
import gzip
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Storage:
    def __init__(self, root, manifest, expected):
        self.root = Path(root).resolve()
        self.manifest = Path(manifest).resolve()
        raw = self.manifest.read_bytes()
        assert sha(raw) == expected, 'Storage manifest changed'
        value = json.loads(raw)
        assert value['schema'] == 'declared-exact-gzip-storage-v1'
        assert value['original_content_unchanged'] is value['historical_receipts_unchanged'] is True
        assert value['compression'] == dict(format='gzip', mtime=0, filename='', compresslevel=9)
        self.records, self.pins = {}, {str(self.manifest): expected}
        for row in value['artifacts']:
            logical, stored = (self.root / row[k] for k in ('logical_path', 'stored_path'))
            assert not Path(row['logical_path']).is_absolute() and not Path(row['stored_path']).is_absolute()
            assert logical.resolve().is_relative_to(self.root) and stored.resolve().is_relative_to(self.root)
            assert '..' not in logical.parts and '..' not in stored.parts
            assert row['storage_encoding'] == 'gzip' and str(stored) == str(logical) + '.gz'
            assert str(logical) not in self.records, 'Duplicate logical artifact'
            self.records[str(logical)] = row

    def read_bytes(self, path, expected):
        path = Path(path).resolve()
        record = self.records.get(str(path))
        if record is None:
            # A .gz suffix alone never authorizes decompression. Original
            # runtime archives continue to hash their original stored bytes.
            raw = path.read_bytes()
            assert sha(raw) == expected, ('Artifact changed', str(path))
            self.pins[str(path)] = expected
            return raw
        assert record['original_sha256'] == expected, 'Logical content pin changed'
        stored = self.root / record['stored_path']
        packed = stored.read_bytes()
        assert len(packed) == record['stored_bytes'] and sha(packed) == record['stored_sha256'], 'Stored artifact changed'
        raw = gzip.decompress(packed)
        assert len(raw) == record['original_bytes'] and sha(raw) == expected, 'Decompressed artifact changed'
        if path.exists():
            assert path.read_bytes() == raw, 'Conflicting unpacked artifact'
        self.pins[str(stored)] = record['stored_sha256']
        return raw

    def read(self, path, expected):
        return json.loads(self.read_bytes(path, expected))
