#!/usr/bin/env python3
"""Losslessly compress saved qualification binaries; primary subjects are untouched."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil

CODE = Path('/private/tmp/benchmarks-native-consolidation/experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1')
ARCHIVE = CODE / 'published-processes-7543-v1'
SAVED = CODE / '.build/qualified-processes-7543c56'
MAP = ARCHIVE / 'local-binary-preservation.json'


def digest(path, compressed=False):
    h = hashlib.sha256()
    with (gzip.open(path, 'rb') if compressed else path.open('rb')) as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


original = json.loads(MAP.read_text())
backup = ARCHIVE / 'original-local-binary-preservation.json'
assert not backup.exists()
shutil.copyfile(MAP, backup)
rows = []
for row in original['binaries']:
    path = Path(row['path'])
    assert path.parent == SAVED and path.name == row['sha256']
    assert path.is_file() and not path.is_symlink() and digest(path) == row['sha256']
    archive = path.with_suffix('.gz')
    assert not archive.exists()
    with path.open('rb') as source, archive.open('xb') as target:
        with gzip.GzipFile(filename='', fileobj=target, mode='wb', compresslevel=1, mtime=0) as output:
            shutil.copyfileobj(source, output, length=1024 * 1024)
    assert digest(archive, compressed=True) == row['sha256']
    rows.append(dict(path=str(archive), encoding='gzip', raw_sha256=row['sha256'],
                     raw_bytes=row['bytes'], archive_sha256=digest(archive), archive_bytes=archive.stat().st_size,
                     originals=row['originals']))
    path.unlink()
    print('Preserved exact binary',row['sha256'][:12],row['bytes'],'->',archive.stat().st_size,flush=True)
MAP.write_text(json.dumps(dict(schema='mech.qualified-binary-preservation.v2',
    scope='Lossless archives of the exact qualification harnesses/generated binaries, outside rebuildable Cargo caches; these are not primary timing subjects.',
    binaries=rows, compression_driver_sha256=digest(Path(__file__)),
    raw_binary_bytes=sum(r['raw_bytes'] for r in rows), archive_bytes=sum(r['archive_bytes'] for r in rows)),indent=2)+'\n')
shutil.copyfile(__file__,ARCHIVE/'binary-compression-driver.py')
print('All saved qualification binaries round-trip to their original hashes; public and retained subjects untouched.',flush=True)
