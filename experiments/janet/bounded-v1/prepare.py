#!/usr/bin/env python3
"""Seal or replay Janet's serial bounded-output schedule without native execution."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
JANET = HERE.parent
CORPUS = ROOT / 'experiments/shared/bounded-corpus-v1/cases/manifest.json'
CORPUS_SHA = '92767a167dafd97745361221cd5a9fe04a2388ba6be7f591756f6153ab3895f1'
REFERENCE_CHECKER = ROOT / 'tools/qualification/scala_typescript_outputs.py'
REFERENCE_CHECKER_SHA = '88efb309f9ef6054b4541bd1605d98c323711acf2a62ce7c0080cc3bbcd08d0d'
BENCHES = {'binarytrees', 'fannkuchredux', 'fasta', 'knucleotide', 'mandelbrot',
           'nbody', 'pidigits', 'regexredux', 'revcomp', 'spectralnorm'}
RUNTIME = JANET / '.build/local-runtime-v1/janet'
RUNTIME_SHA = '6732dd0bb37de61676bbdb3a8d3fb14b76b3a39fc9852e2b1f060dd21a9bc765'
CATALOG_SHA = '99db1ecdd4f8a20fc6aabfc13d493728a4a36d94cdc6778235376ebb60983d1c'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contained(base, relative):
    relative = Path(relative)
    require(not relative.is_absolute() and '..' not in relative.parts,
            'Relative contained input required')
    path = base / relative
    require(path.resolve() == path and path.is_file(), 'Missing, escaping or linked input')
    return path


def build():
    """Read and hash files only; intentionally no runtime or benchmark invocation."""
    pins = {}

    def bind(path, expected=None):
        require(path.is_absolute() and path.resolve() == path and path.is_file(),
                'Physical regular input required')
        actual = sha(path)
        require(expected is None or actual == expected, 'Changed pinned input: ' + str(path))
        name = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        require(name not in pins or pins[name]['sha256'] == actual, 'Conflicting file pin')
        pins[name] = dict(sha256=actual, bytes=path.stat().st_size)
        return name

    def document(path, expected=None):
        bind(path, expected)
        return json.loads(path.read_bytes())

    corpus = document(CORPUS, CORPUS_SHA)
    require(corpus['schema'] == 'shared-bounded-workload-corpus-v1'
            and corpus['case_count'] == len(corpus['cases']) == 149
            and corpus['success_cases'] == 142 and corpus['rejection_cases'] == 7,
            'Changed shared corpus policy')
    for name, digest in corpus['reference_pins'].items():
        bind(contained(ROOT, name), digest)
    bind(REFERENCE_CHECKER, REFERENCE_CHECKER_SHA)
    for name in ('prepare.py', 'outputs.py', 'test_preparation.py'):
        bind(HERE / name)
    manifest = document(JANET / 'source-manifest-v1.json')
    require(manifest['preserved_catalog_sha256'] == CATALOG_SHA,
            'Changed canonical preservation prerequisite')
    bind(ROOT / 'data/benchmarks.json', CATALOG_SHA)
    sources = {row['benchmark']: row for row in manifest['sources']}
    require(len(manifest['sources']) == len(sources) == 10 and set(sources) == BENCHES,
            'All ten unique Janet sources required')
    for row in sources.values():
        bind(contained(ROOT, row['path']), row['sha256'])
    built = document(JANET / 'local-runtime-build-result-v1.json')
    require(built['status'] == 'built-and-version-observed' and built['runtime_built_locally'] is True
            and built['binary_sha256'] == RUNTIME_SHA
            and built['observed_version'] == '1.42.1-e1963cd', 'Working local runtime required')
    bind(RUNTIME, RUNTIME_SHA)
    document(JANET / 'runtime-acquisition-v1.json')
    bind(JANET / 'runtime-LICENSE.txt')
    cli = document(JANET / 'dependencies-v1/runtime-cli/snapshot.json')
    for name, pin in cli['files'].items():
        bind(contained(JANET / 'dependencies-v1/runtime-cli', name), pin['sha256'])
    spork = document(JANET / 'dependencies-v1/spork/snapshot.json')
    for name, pin in spork['files'].items():
        bind(contained(JANET / 'dependencies-v1/spork', name), pin['sha256'])
    gmp = manifest['library_boundaries']['pidigits']
    gmp_binary = Path(gmp['binary']).resolve(strict=True)
    bind(gmp_binary, gmp['binary_sha256'])
    environment = dict(PATH='/usr/bin:/bin', LC_ALL='C', LANG='C', TZ='UTC', NO_COLOR='1',
                       JANET_PATH=str(JANET / 'dependencies-v1/spork'),
                       MECH_GMP_LIBRARY=str(gmp_binary))
    schedule = []
    identities = set()
    for index, case in enumerate(corpus['cases'], 1):
        identity = (case['benchmark'], case['case'])
        require(identity not in identities and case['benchmark'] in BENCHES,
                'Duplicate or unknown corpus case')
        identities.add(identity)
        require(case['input_kind'] in ('stdin', 'integer-argument')
                and type(case['n']) is int and case['n'] >= 0, 'Invalid corpus input')
        for field in ('stdin', 'expected'):
            if field in case:
                pin = case[field]
                path = contained(CORPUS.parent, pin['path'])
                bind(path, pin['sha256'])
                require(type(pin['bytes']) is int and path.stat().st_size == pin['bytes'],
                        'Corpus byte length differs')
        require(case['input_kind'] != 'integer-argument' or case['stdin']['bytes'] == 0,
                'Numeric fixture unexpectedly carries stdin')
        rejected = case['expected_exit'] == 'nonzero'
        if rejected:
            require(case['benchmark'] == 'revcomp' and 'expected' not in case
                    and case['validation'] == 'language-specific-invalid-iupac'
                    and type(case['expected_invalid_byte']) is int
                    and 0 <= case['expected_invalid_byte'] <= 255, 'Changed rejection contract')
        else:
            require(type(case['expected_exit']) is int and case['expected_exit'] == 0
                    and case['validation'] in ('exact-complete-bytes',
                                              'finite-two-energy-lines-within-1e-8')
                    and 'expected' in case, 'Changed success contract')
        source = contained(ROOT, sources[case['benchmark']]['path'])
        command = [str(RUNTIME), '-R', '-n', str(source)]
        if case['input_kind'] == 'integer-argument':
            command.append(str(case['n']))
        schedule.append(dict(slot=index, benchmark=case['benchmark'], case=case['case'],
            corpus_index=index - 1, command=command, source_sha256=sha(source),
            stdin=str((CORPUS.parent / case['stdin']['path']).relative_to(ROOT)),
            stdin_sha256=case['stdin']['sha256'],
            check='capture-only-awaiting-Janet-rejection-adapter' if rejected else case['validation'],
            output_contract_qualified=False))
    require(sum(row['check'].startswith('capture-only') for row in schedule) == 7,
            'Rejection cases cannot be silently omitted')
    return dict(schema='janet-bounded-output-preparation.v1',
        status='prepared-not-executed-awaiting-owned-process-controller-and-free-common-mutex',
        native_processes_started=0, benchmark_samples=0, chart_admission=False,
        output_conformance_qualified=False, required_work_qualified=False,
        normalized_loc=None, native_formatted_loc=None,
        root=str(ROOT), corpus=str(CORPUS.relative_to(ROOT)), corpus_sha256=CORPUS_SHA,
        runtime=str(RUNTIME), runtime_sha256=RUNTIME_SHA,
        expected_version_stdout='1.42.1-e1963cd\n', environment=environment,
        gmp_resolution=dict(configured_path=gmp['binary'], native_load_path=str(gmp_binary),
                            sha256=gmp['binary_sha256']),
        common_mutex='/private/tmp/mech-clbg-timing.lock',
        process_policy=dict(serial=True, fresh_process_per_case=True,
            launch_deadline_seconds=30, cleanup_deadline_seconds=5,
            inherited_common_mutex=True, stdout_and_stderr='complete raw bytes',
            required_controller='Register forked child birth identity before exec; verify owned group closure before releasing mutex or launching the next case.',
            native_process_controller_qualified=False),
        limitations=[
            'Preparation hashes files only. No native process, compiler, formatter or benchmark is invoked.',
            'The seven malformed-IUPAC cases require native capture and a Janet-specific adapter review; capture alone cannot pass them.',
            'Working-runtime version observation is retained development evidence, not a fresh locked preflight.',
            'The explicit regex module and GMP binary are pinned; complete native loader closure remains unqualified.',
            'Successful bounded outputs do not establish full-size output, required work, source counts or timing eligibility.'],
        case_count=len(schedule), success_case_count=142, rejection_capture_count=7,
        cases_per_benchmark=dict(sorted(Counter(row['benchmark'] for row in schedule).items())),
        pins=dict(sorted(pins.items())), schedule=schedule)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    plan = build()
    path = HERE / 'plan-v1.json'
    if args.check:
        require(json.loads(path.read_bytes()) == plan, 'Prepared plan differs')
    else:
        with path.open('x') as stream:
            json.dump(plan, stream, indent=2)
            stream.write('\n')
    print(json.dumps(dict(status='checked' if args.check else 'prepared', cases=plan['case_count'],
                          native_processes_started=0, benchmark_samples=0)))
