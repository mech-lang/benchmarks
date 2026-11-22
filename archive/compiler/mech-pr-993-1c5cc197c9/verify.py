#!/usr/bin/env python3
"""Verify and optionally reconstruct a byte-exact compiler benchmark snapshot."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def check(data, record):
    assert len(data) == record['bytes'], record
    assert hashlib.sha256(data).hexdigest() == record['sha256'], record
    if 'git_blob' in record:
        assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == record['git_blob'], record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-dir', type=Path, required=True)
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--restore-dir', type=Path)
    args = parser.parse_args()
    manifest = json.loads((HERE / 'manifest.json').read_text())
    records = manifest['files']
    assert len({r['source_path'] for r in records}) == len(records) == manifest['summary']['files']
    assert sum(r['bytes'] for r in records) == manifest['summary']['source_bytes']
    assets = {a['name']: a for a in manifest['assets']}
    assert len(assets) == len(manifest['assets'])
    args.asset_dir.mkdir(parents=True, exist_ok=True)
    wanted = {}
    destinations = set()

    def restore(record, data):
        if args.restore_dir is not None:
            target = (args.restore_dir / record['source_path']).resolve()
            target.relative_to(args.restore_dir.resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(int(record['mode'], 8) & 0o777)

    for record in records:
        assert record['mode'] in ('100644', '100755')
        assert record['source_path'].startswith(('benchmarks/mech-deflate/', 'benchmarks/related-post-gen/'))
        if 'destination_path' in record:
            path = (ROOT / record['destination_path']).resolve()
            path.relative_to(HERE / 'source')
            assert path not in destinations
            destinations.add(path)
            data = path.read_bytes()
            check(data, record)
            restore(record, data)
        else:
            name, member = record['release_asset'], record['archive_member']
            assert name in assets and member == record['git_blob']
            wanted.setdefault(name, {}).setdefault(member, []).append(record)
    assert destinations == {p.resolve() for p in (HERE / 'source').rglob('*') if p.is_file()}
    assert set(wanted) == set(assets)
    for name, asset in assets.items():
        assert Path(name).name == name
        path = args.asset_dir / name
        if not path.exists() and args.download:
            temporary = path.with_suffix(path.suffix + '.partial')
            subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                            asset['url'], '--output', str(temporary)], check=True)
            temporary.replace(path)
        assert path.stat().st_size == asset['bytes'], name
        with path.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == asset['sha256'], name
        found = set()
        all_members = set()
        with tarfile.open(path, 'r|gz') as archive:
            for entry in archive:
                assert entry.isfile() and re.fullmatch('[0-9a-f]{40}', entry.name), entry.name
                assert entry.name not in all_members
                all_members.add(entry.name)
                data = archive.extractfile(entry).read()
                assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == entry.name
                for record in wanted[name].get(entry.name, []):
                    check(data, record)
                    restore(record, data)
                    found.add(entry.name)
        assert found == set(wanted[name]), name
    print(f"Verified {len(records):,} original files, {manifest['summary']['source_bytes']:,} bytes and {len(assets)} payload bundles.")


if __name__ == '__main__':
    main()
