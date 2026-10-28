#!/usr/bin/env python3
"""Losslessly retain idle task executables before reclaiming their disk space."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil

TARGET = Path('/private/tmp/native-935-current-head-target-v1/debug')
OUT = Path('/private/tmp/native-935-current-correctness-v1/retained-executables-v1')
assert TARGET.resolve() == TARGET and not TARGET.is_symlink()
OUT.mkdir(exist_ok=False)
groups = {}
for path in TARGET.rglob('*'):
    if path.is_symlink() or not path.is_file() or path.suffix:
        continue
    stat = path.stat()
    if stat.st_size < 10 * 2**20:
        continue
    with path.open('rb') as source:
        magic = source.read(4)
    if magic not in [bytes.fromhex(v) for v in ['cffaedfe', 'cefaedfe', 'feedfacf', '7f454c46']]:
        continue
    key = (stat.st_dev, stat.st_ino)
    groups.setdefault(key, []).append(path)

manifest = {'source_head': '36bcb9292ed40676a4547c91588c96735785b139',
            'source_target': str(TARGET.parent), 'primary_timing_samples': 0,
            'scope': 'Only idle task test/generated executables; frozen timing controls and source trees are untouched',
            'free_bytes_before': shutil.disk_usage(OUT).free, 'status': 'running', 'files': []}


def save():
    tmp = OUT / 'manifest.json.tmp'
    tmp.write_text(json.dumps(manifest, indent=2) + '\n')
    tmp.replace(OUT / 'manifest.json')


save()
for index, paths in enumerate(sorted(groups.values(), key=lambda paths: -paths[0].stat().st_size)):
    assert shutil.disk_usage(OUT).free >= 50_000_000_000
    source = paths[0]
    stat = source.stat()
    destination = OUT / f'{index:03d}-{source.name}.gz'
    digest = hashlib.sha256()
    with source.open('rb') as incoming, destination.open('xb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', compresslevel=1, mtime=0) as outgoing:
            while data := incoming.read(1024 * 1024):
                digest.update(data)
                outgoing.write(data)
    check = hashlib.sha256()
    with gzip.open(destination, 'rb') as incoming:
        while data := incoming.read(1024 * 1024):
            check.update(data)
    assert check.digest() == digest.digest()
    assert source.stat().st_size == stat.st_size and source.stat().st_mtime_ns == stat.st_mtime_ns
    row = {'original_paths': [str(p) for p in paths], 'archive': destination.name,
           'raw_sha256': digest.hexdigest(), 'raw_bytes': stat.st_size,
           'archive_bytes': destination.stat().st_size, 'status': 'losslessly-verified'}
    manifest['files'].append(row)
    save()
    for path in paths:
        assert path.is_relative_to(TARGET) and not path.is_symlink()
        path.unlink()
    row['status'] = 'compressed-originals-retired'
    save()
    print(index + 1, '/', len(groups), source.name, 'retained and reclaimed', flush=True)
manifest.update(status='complete', free_bytes_after=shutil.disk_usage(OUT).free)
save()
print('Verified disk reclamation GiB:', (manifest['free_bytes_after'] - manifest['free_bytes_before']) / 2**30, flush=True)
