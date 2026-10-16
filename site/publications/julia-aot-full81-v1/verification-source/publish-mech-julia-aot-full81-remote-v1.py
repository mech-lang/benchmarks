#!/usr/bin/env python3
"""Package the reviewed website on its established remote publishing host.

Invocation publishes. This wrapper must run on Macmini.ht.home, after profiling
has stopped and the caller supplies the final committed benchmark-source ID.
It never builds, reads the canonical catalog, or transfers benchmark evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import types

HOSTNAME = 'Macmini.ht.home'
PUBLISHER = Path('/tmp/deploy-mech-julia-aot-full81-pages-v1.py')
ASSETS = Path('/private/tmp/mech-julia-aot-pages-preparation-20261015-v1/source/site/public')
STAGING = '/tmp/mech-julia-aot-full81-pages-20261015'
BARE = '/Users/coreymontella/mech-lang/website-benchmark-pages-publish.git'
# Fill these from the final committed source and validated remote build.
SOURCE = '97bccc03275b2eb07b8829d127f16c2a66e07baf'
VERSION = '1b021c21ca65c531'
MANIFEST_SHA = '8f5e31e8af5da8bcbc4015ec6449120d728ddf5755c5f2ee235ae7f503ffff33'
DATASET_SHA = 'ec3e743dc01ae1508974818155143965b6737596be7400e4c724c5475cdbda5c'
GZIP_SHA = 'd78ae04ce33a057d22e5801ab85e843d2ab414014bbc51a1a34c1cf89df678dc'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--publisher-sha256', required=True)
    args = parser.parse_args()
    # This precedes every asset read/hash/package operation, so accidentally
    # invoking the wrapper on the active timing host cannot perform that work.
    require(platform.node() == HOSTNAME, 'Run only on the verified publishing host')
    require(re.fullmatch('[0-9a-f]{40}', SOURCE) and re.fullmatch('[0-9a-f]{16}', VERSION)
            and all(re.fullmatch('[0-9a-f]{64}', value) for value in (MANIFEST_SHA, DATASET_SHA, GZIP_SHA)),
            'Replace every reviewed build placeholder before publication')
    require(args.source_commit == SOURCE, 'Expected the exact reviewed build source commit')
    require(re.fullmatch('[0-9a-f]{64}', args.publisher_sha256), 'Expected reviewed publisher SHA')
    require(stat.S_ISREG(PUBLISHER.lstat().st_mode), 'Regular publisher source required')
    with PUBLISHER.open('rb') as stream:
        raw = stream.read(65537)
    require(len(raw) <= 65536 and hashlib.sha256(raw).hexdigest() == args.publisher_sha256,
            'Reviewed publisher source changed')
    publisher = types.ModuleType('reviewed_julia_aot_full81_pages_publisher')
    publisher.__file__ = str(PUBLISHER)
    exec(compile(raw, str(PUBLISHER), 'exec'), publisher.__dict__)
    require(publisher.HOST == 'mac-mini-runner' and publisher.STAGING == STAGING
            and publisher.BARE == BARE, 'Publisher destination scope differs')
    require(not Path(STAGING).exists(), 'Publication staging must be fresh; no retry')
    source = ASSETS.resolve(strict=True)
    require(source.is_dir(), 'Reviewed site/public is missing')
    require(publisher.sha(source/'build.json') == MANIFEST_SHA, 'Reviewed manifest differs')
    manifest = json.loads((source/'build.json').read_bytes())
    require(manifest['version'] == VERSION and len(manifest['files']) == 36
            and manifest['files'].get('data.json') == DATASET_SHA
            and manifest['files'].get('data.json.gz') == GZIP_SHA, 'Reviewed build scope differs')
    expected = dict(manifest['files'], **{'build.json': MANIFEST_SHA})

    def verify_assets():
        require({path.name for path in source.iterdir()} == set(expected), 'Asset inventory differs')
        for name, wanted in expected.items():
            path = source/name
            require(re.fullmatch('[A-Za-z0-9_.-]+', name) and name not in ('.', '..')
                    and re.fullmatch('[0-9a-f]{64}', wanted), 'Invalid manifest entry')
            require(stat.S_ISREG(path.lstat().st_mode) and path.resolve().parent == source,
                    'Nonregular or redirected asset: '+name)
            require(publisher.sha(path) == wanted, 'Reviewed asset changed: '+name)

    verify_assets()
    with tempfile.TemporaryDirectory(prefix='mech-julia-aot-full81-remote-assets-') as directory:
        archive = Path(directory)/'site-public.tar'
        with tarfile.open(archive, 'w') as bundle:
            for name in sorted(expected):
                bundle.add(source/name, arcname=name, recursive=False)
        verify_assets()
        command = [sys.executable, '-I', '-S', '-B', '-c', publisher.REMOTE,
                   STAGING, BARE, args.source_commit, MANIFEST_SHA, VERSION,
                   DATASET_SHA, publisher.sha(archive)]
        with archive.open('rb') as incoming:
            result = subprocess.run(command, stdin=incoming, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, check=False)
        if result.returncode:
            raise RuntimeError('Publication stopped; remote staging retained. '+
                               result.stderr.decode(errors='replace'))
        value = json.loads(result.stdout)
        require(value['schema'] == 'benchmark-julia-aot-full81-pages-publication-v1'
                and value['status'] == 'pushed-awaiting-live-pages-verification'
                and value['remote_ref_verified'] is True
                and value['benchmark_source_commit'] == args.source_commit
                and value['build_manifest_sha256'] == MANIFEST_SHA
                and value['dataset_sha256'] == DATASET_SHA
                and value['build_version'] == VERSION and value['asset_count'] == 36,
                'Unexpected actual publication receipt')
        # REMOTE itself has already saved the authoritative receipt in STAGING.
        # Return only that actual result, never a planned or simulated success.
        print(json.dumps(value), flush=True)


if __name__ == '__main__':
    main()
