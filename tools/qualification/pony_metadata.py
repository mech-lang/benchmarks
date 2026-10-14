"""Verify Pony publication metadata against retained production receipts.

No compiler, native executable, workload or timing is run. This check requires
the common timing mutex because it rehashes compiler, runtime and binary files.
Full-suite reconciliation and dataset admission are separate operations.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / 'experiments/pony/migration-resume-v1/plan.json'
PLAN_SHA = '710530db6445292bd6506c97a9e6c91fd7aeba4523f077cf72be25cbebf7a3ee'
SUITE = ROOT / 'archive/languages/pony/20261012/full-studies/pony-retained20-full-v1/manifest.json'
LOCK = Path('/tmp/mech-clbg-timing.lock')
COMPILER_SHA = 'e35646fa9e56bc246e7cf3a867783def6374ce5d0192292d38627d768efa575a'
RUNTIME_ARTIFACTS = {
    'libponyrt.a': '49c91374c473e03889951f63e4de64db6e1d8707a9885d9c098c2c0bd825da0b',
    'libponyrt.bc': '95e60711be95591e4b5f5e3b35e7daef1c28de30fb8bb5b46c74d89d2309438a',
}
OVERRIDE_MARKERS = ('runtime_override_defaults', 'RuntimeOptions', '@pony_gc',
                    '@pony_cycle', '@ponyint_', '@pony_exitcode')
VERSION = ('0.74.0-95ad180 [release]\n'
           'Compiled with: LLVM 23.1.2 -- AppleClang-21.0.0.21000101-arm64\n'
           'Defaults: pic=true')
ENVIRONMENT = {
    'DYLD_LIBRARY_PATH': '/opt/homebrew/Cellar/pcre2/10.49/lib:/opt/homebrew/Cellar/gmp/6.3.0/lib',
    'LC_ALL': 'C', 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1',
    'VECLIB_MAXIMUM_THREADS': '1',
}
LIBRARIES = {
    'regexredux': ('libpcre2-8.0.dylib', '/opt/homebrew/Cellar/pcre2/10.49/lib/libpcre2-8.0.dylib',
                  'c3adcd954967b7e92812831fe12c614a9ca2d12221e897a87ee379df2ac004fd'),
    'pidigits': ('libgmp.10.dylib', '/opt/homebrew/Cellar/gmp/6.3.0/lib/libgmp.10.dylib',
                '571ffb9eb5b5110cda32f62197c1f039e5627d66524ba47bb0774eca184532b9'),
}
SOURCES = [
    'https://www.ponylang.io/blog/2017/05/an-early-history-of-pony/',
    'https://www.ponylang.io/media/papers/OGC.pdf',
    'https://www.ponylang.io/media/papers/a_string_of_ponies.pdf',
    'https://www.ponylang.io/use/compiler/runtime-options/',
]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def successful(receipt, command):
    require(receipt['command'] == command, ('Unexpected receipt command', receipt['command']))
    require(receipt['exit_status'] == receipt['final_exit_status'] == 0,
            'Metadata command did not exit normally')
    require(not any(receipt.get(k) for k in ('error', 'timed_out', 'cleanup_errors', 'remaining_group_members')),
            'Metadata receipt records a failure')


def inspect(plan):
    pins = plan['pins']
    verified = {}

    def bind(path, expected=None):
        path = Path(path)
        name = str(path)
        require(name in pins, ('Metadata input absent from frozen plan', name))
        if expected is not None:
            require(pins[name] == expected, ('Metadata pin differs', name))
        if name not in verified:
            require(digest(path) == pins[name], ('Metadata bytes changed', name))
            verified[name] = pins[name]
        return path

    def read(path):
        return json.loads(bind(path).read_bytes())

    suite = read(SUITE)
    profiles = [row for row in suite['profiles'] if row['language'] == 'pony']
    require(len(profiles) == len({r['key'] for r in profiles}) == 20, 'Incomplete Pony cohort')
    require(len({r['benchmark'] for r in profiles}) == 10, 'Incomplete workload coverage')
    require(len({(r['benchmark'], r['variant']) for r in profiles}) == 20
            and {r['variant'] for r in profiles} == {'compact', 'optimized'},
            'Expected one compact and one optimized profile per workload')
    output = []
    for row in profiles:
        binary = bind(row['binary'], row['binary_sha256'])
        require(row['command'] == [str(binary), '{n}', '--ponymaxthreads', '8'],
                'Unexpected runtime arguments')
        require(row['runtime_arguments'] == row['command'][2:], 'Runtime argument metadata differs')
        require(row['runtime_environment'] == ENVIRONMENT, 'Unexpected runtime environment')
        require(row['execution_mode'] == 'native-aot', 'Unexpected execution mode')
        require(type(row['maximum_compute_actors']) is int and 1 <= row['maximum_compute_actors'] <= 8,
                'Invalid recorded compute actor ceiling')
        build_path = Path(row['production_build_receipt'])
        build = read(build_path)
        argv = build['command']
        compiler = bind(argv[0], COMPILER_SHA)
        require(argv[1:5] == ['--strip', '--triple', 'aarch64-apple-macosx14.4.0', '--sysroot'],
                'Unexpected production build flags')
        require(not any(x in argv for x in ('--debug', '--runtimebc', '--library', '--pass', '--pic=false')),
                'Unsupported production build mode')
        require(argv[-3:] == ['--bin-name', row['id'], str(Path(row['source']).parent)],
                'Production build does not bind the source package')
        require(argv[argv.index('--output') + 1] == str(binary.parent), 'Production output differs')
        successful(build, argv)
        version_path = build_path.parents[2] / 'bootstrap/ponyc-version.json'
        successful(read(version_path), [str(compiler), '--version'])
        require(bind(version_path.with_suffix('.stdout')).read_text().strip() == VERSION,
                'Unexpected compiler version')
        require(not bind(version_path.with_suffix('.stderr')).read_bytes(), 'Compiler version stderr')
        runtime = []
        for name, expected in RUNTIME_ARTIFACTS.items():
            path = bind(compiler.parents[1] / 'lib/armv8-a' / name, expected)
            runtime.append({'path': str(path), 'sha256': pins[str(path)]})
        images = build_path.parent / 'images'
        successful(read(images/'architecture.json'), ['/usr/bin/lipo', '-archs', str(binary)])
        require(bind(images/'architecture.stdout').read_text().strip() == 'arm64', 'Non-arm64 executable')
        require(not bind(images/'architecture.stderr').read_bytes(), 'Architecture inspection stderr')
        successful(read(images/'linked-images.json'), ['/usr/bin/otool', '-L', str(binary)])
        require(not bind(images/'linked-images.stderr').read_bytes(), 'Link inspection stderr')
        linked = bind(images/'linked-images.stdout').read_text().splitlines()
        require(linked[0] == str(binary) + ':', 'Link inspection refers to another binary')
        names = [line.strip().split(' (', 1)[0] for line in linked[1:]]
        require(len(names) == len(set(names)), 'Duplicate linked image')
        allowed = {'/usr/lib/libSystem.B.dylib'}
        library = LIBRARIES.get(row['benchmark'])
        support = []
        if library:
            name, resolved, expected = library
            matches = [p for p in names if Path(p).name == name]
            require(len(matches) == 1, 'Missing general-purpose vendor library')
            allowed.add(matches[0])
            bind(resolved, expected)
            support.append({'install_name': matches[0], 'environment_candidate_path': resolved,
                            'sha256': expected, 'loaded_image_observed': False})
        require(set(names) == allowed, ('Unexpected native dependency', names))
        inventory = row['compiler_bound_input_inventory']
        authored = {(item['path'], item['sha256']) for item in row['source_bundle']}
        require(inventory['status'] == 'qualified-exact-authored-compiler-inputs'
                and inventory['source_sha256'] == row['source_sha256']
                and inventory['binary_sha256'] == row['binary_sha256']
                and len(authored) == len(row['source_bundle'])
                and authored == {(item['path'], item['sha256']) for item in inventory['files']}
                and (row['source'], row['source_sha256']) in authored,
                'Authored source bundle differs from the qualified compiler-input inventory')
        sources = []
        for source in row['source_bundle']:
            path = bind(source['path'], source['sha256'])
            text = path.read_text()
            require(not any(token in text for token in OVERRIDE_MARKERS),
                    'Runtime override requires separate semantic review')
            sources.append({'path': str(path), 'sha256': source['sha256'], 'role': source['role']})
        output.append({'key': row['key'], 'id': row['id'], 'benchmark': row['benchmark'],
            'binary': str(binary), 'binary_sha256': row['binary_sha256'],
            'compiler': str(compiler), 'compiler_sha256': COMPILER_SHA,
            'build_receipt': str(build_path), 'build_command': argv, 'native_architecture': 'arm64',
            'runtime_artifacts': runtime, 'linked_install_names': names, 'vendor_libraries': support,
            'sources': sources, 'command': row['command'], 'runtime_arguments': row['runtime_arguments'],
            'runtime_environment': row['runtime_environment'],
            'maximum_compute_actors': row['maximum_compute_actors'],
            'execution_mode': 'native-aot',
            'runtime_override_source_scan': {'method': 'literal marker scan of the complete authored bundle',
                'markers': list(OVERRIDE_MARKERS), 'matches': []}})
    return {
        'schema': 'pony-production-runtime-metadata-v1', 'status': 'qualified-recorded-runtime-metadata',
        'plan': str(PLAN), 'plan_sha256': PLAN_SHA, 'pins': verified, 'profiles': output,
        'runtime_publication_metadata_qualified': True, 'chart_admission': False,
        'compiler_invocations': 0, 'native_probes': 0, 'benchmark_samples': 0,
        'runtime_policy': 'Pony 0.74.0-95ad180 release compiler/runtime, LLVM 23.1.2, native macOS ARM64; --ponymaxthreads 8',
        'memory_policy': 'Pony actor-local tracing GC with distributed reference counting and actor-cycle collection. Recorded commands contain no GC options, and the complete authored source bundle contains none of the checked runtime-override markers.',
        'language': {'key': 'pony', 'label': 'Pony', 'family': 'pony', 'platform': 'native',
            'runtime': 'Pony native compiler/runtime', 'execution': ['aot'], 'typing': 'static',
            'style': ['imperative', 'object'], 'memory': ['gc', 'rc', 'cycles'],
            'note': 'Actor-based, statically typed native language with reference capabilities. Actor-local heaps use tracing GC; cross-actor references and actor cycles use runtime collection. Reference capabilities are not manual allocation or RAII ownership.',
            'sources': SOURCES, 'release_year': 2015,
            'release_note': 'First open-source release in May 2015 according to the creator; the earlier 2014 prototype is excluded.'},
        'evidence_scope': 'Saved successful production builds, pinned native binaries and static runtime artifacts, recorded architecture and linked-image inspections, exact commands/environment and complete authored-source inventory. Recorded DYLD_LIBRARY_PATH and install names identify pinned library candidates; actual loaded-image paths and runtime GC configuration were not observed by this check.',
        'gc_numeric_defaults_claimed': False,
        'runtime_gc_configuration_observed': False,
        'timing_boundary': suite['timing_boundary'],
        'remaining_gate': 'Independent completed full-suite reconciliation and explicit dataset import.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Fresh output required')
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        opened, named = os.fstat(lock.fileno()), LOCK.stat()
        require((opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
                and opened.st_ino == 79859134, 'Common timing mutex changed')
        require(digest(PLAN) == PLAN_SHA, 'Execution plan changed')
        report = inspect(json.loads(PLAN.read_bytes()))
        report['review_tool'] = {'path': str(Path(__file__).resolve()), 'sha256': digest(__file__)}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
        print(json.dumps({'status': report['status'], 'profiles': len(report['profiles']),
                          'output': str(args.output), 'sha256': digest(args.output),
                          'chart_admission': False}))


if __name__ == '__main__':
    main()
