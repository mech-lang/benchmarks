"""Prepare and run bounded Nim qualification; no pilot, full timing or catalog mode.

Preparation hashes files only. Native execution requires the exact reviewed plan
digest, owns the common lock, preserves every attempt and uses separate untimed
instrumented twins. Existing source proposals and the restored runtime are read-only.
"""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil

from native_process import atom, now, one, sha, success
import instrument_sources as trace
import reference_work as work

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
PROPOSAL = PACKET / 'plan.json'
PROTOCOL = HERE / 'protocol.json'
RESTORATION = ROOT / 'experiments/nim/optimization-v1/runtime-restoration.json'
VERSION = ROOT / 'experiments/nim/optimization-v1/runtime-version.json'
HISTORICAL = ROOT / 'archive/languages/nim/20261012/proposals/private-v4.json'
CORPUS = ROOT / 'experiments/shared/bounded-corpus-v1/cases'
REFERENCE = ROOT / 'archive/languages/c3/20261012/revisions/private-v1/references.py'
REFERENCE_SHA = '6ba2d8d70f23ac04f2bd24e73356f14a1c3a046da35f25e936332b10a7cba1f3'
LOCK = Path('/tmp/mech-clbg-timing.lock')
NAMES = ['parent-compact', 'parent-parallel', 'compact-reverse-guarded',
    'parallel-guarded-copy', 'parallel-reverse-guarded', 'parallel-byte-reverse']
BOUNDED = list(range(1, 9))
WORK = list(range(1, 7))
INVALID = [['0'], ['-1'], ['13'], [], ['not-an-integer']]
INTERVALS = [(0, 1), (1, 2), (3, 7), (5, 9), (23, 25), (119, 121), (359, 361), (719, 720)]
CLANG = '/opt/homebrew/Cellar/llvm@22/22.1.8/bin/clang-22'
EXTERNAL_PREFIXES = ['/Library/Developer/CommandLineTools/SDKs/MacOSX14.4.sdk/',
    '/opt/homebrew/Cellar/llvm@22/22.1.8/', '/opt/homebrew/Cellar/pcre/8.45/',
    '/opt/homebrew/Cellar/gmp/6.3.0/']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), sha256=sha(path))


def check_ref(value):
    path = ROOT / value['path']
    require(path.is_file() and sha(path) == value['sha256'], 'Changed pinned file: ' + value['path'])
    return path


def normal_flags(command):
    result = list(command)
    result[0], result[-1] = '<compiler>', '<application>'
    for index, item in enumerate(result):
        for option in ['--lib:', '--nimcache:', '--out:']:
            if item.startswith(option):
                result[index] = option + '<relocated>'
    return result


def recipes():
    result = {}
    for parent in ['compact', 'parallel']:
        label = 'compact' if parent == 'compact' else 'optimized'
        path = ROOT / ('archive/languages/nim/20261012/qualification/private-v4/builds/'
            'nim-fannkuchredux-' + label + '/build.json')
        row = load(path)
        require(row['exit_status'] == 0 and row['final_exit_status'] == 0, 'Historical build failed')
        result[parent] = dict(receipt=ref(path), command=row['command'])
    require(normal_flags(result['compact']['command']) == normal_flags(result['parallel']['command']),
        'Retained compact and parallel flags differ; prepare an explicit matched policy')
    flags = normal_flags(result['compact']['command'])
    require(all(item in flags for item in ['c', '-d:release', '--mm:orc', '--threads:on',
        '--parallelBuild:1', '--cc:clang', '--skipUserCfg:on', '--skipParentCfg:on', '--skipProjCfg:on',
        '--clang.exe:' + CLANG, '--clang.linkerexe:' + CLANG, '--passC:-ffp-contract=off']),
        'Original backend, safety, memory manager, thread or compiler flags changed')
    require(not any(any(token in item.lower() for token in ['mcpu', 'march', 'mtune', 'danger', 'fast-math'])
        for item in flags), 'No new target/unsafe flags are allowed')
    return result


def source_rows(proposal):
    result = {}
    for name in NAMES:
        if name.startswith('parent-'):
            parent = name.removeprefix('parent-')
            source = proposal['parents'][parent]['snapshot']
            require(source['sha256'] == proposal['parents'][parent]['source']['sha256'], 'Retained snapshot bytes differ')
            check_ref(proposal['parents'][parent]['source'])
        else:
            parent = proposal['candidates'][name]['parent']
            source = proposal['candidates'][name]['source']
        check_ref(source)
        result[name] = dict(source=source, parent=parent, parallel=parent == 'parallel',
            guarded=not name.startswith('parent-'), byte_elements=name == 'parallel-byte-reverse')
    return result


def runtime_pins(restored):
    require(restored['schema'] == 'nim-runtime-restoration.v1'
        and restored['checked_distribution_files'] == 6770
        and len(restored['checked_distribution_pins']) == 6770
        and restored['compiler_source_commit'] == '8e8fbf60693418dc95bb0d762fd660231d08a583'
        and restored['compiler_sha256'] == '5f09b756aaaa46af99ae72e66f54ed5d4e41343e8440df07046712a506857a1f',
        'Exact retained Nim distribution receipt required')
    distribution = Path(restored['distribution'])
    pins = restored['checked_distribution_pins']
    actual = {str(path.relative_to(distribution)) for path in distribution.rglob('*') if path.is_file()}
    require(actual == set(pins), 'Nim distribution file inventory changed')
    for relative, expected in pins.items():
        require(sha(distribution / relative) == expected, 'Changed Nim distribution file: ' + relative)
    require(sha(restored['compiler']) == restored['compiler_sha256'], 'Compiler executable changed')
    return distribution


def make_plan(output):
    require(output.parent == HERE and output.name.startswith('attempt-') and not output.exists(),
        'Use an exclusive qualification-v1/attempt-* output')
    protocol = load(PROTOCOL)
    require(protocol['status'] == 'SOURCE-ONLY-PREPARED-NOT-EXECUTED', 'Protocol status differs')
    for value in protocol['source_pins']:
        check_ref(value)
    proposal = load(PROPOSAL)
    sources = source_rows(proposal)
    restored = load(RESTORATION)
    distribution = runtime_pins(restored)
    historical = load(HISTORICAL)
    external = {path: digest for path, digest in historical['pins'].items()
        if any(path.startswith(prefix) for prefix in EXTERNAL_PREFIXES)}
    require(external.get(CLANG) == '012b35304481c5d5db6b57f20e144fb78f198ca9db14aa0b8db72cd2e493e12d',
        'Retained Clang pin changed')
    for path, digest in external.items():
        require(Path(path).is_file() and sha(path) == digest, 'Changed retained native toolchain file: ' + path)
    original_recipes = recipes()
    require(sha(REFERENCE) == REFERENCE_SHA, 'Shared independent reference changed')
    pins = [ref(path) for path in [PROPOSAL, PROTOCOL, RESTORATION, VERSION, HISTORICAL,
        REFERENCE, CORPUS / 'manifest.json', HERE / 'run_qualification.py',
        HERE / 'instrument_sources.py', HERE / 'reference_work.py', HERE / 'native_process.py']]
    pins += [row['source'] for row in sources.values()]
    pins += [row['receipt'] for row in original_recipes.values()]
    cases = []
    manifest = load(CORPUS / 'manifest.json')
    for row in manifest['cases']:
        if row['benchmark'] == 'fannkuchredux' and row['n'] in BOUNDED:
            require(row['validation'] == 'exact-complete-bytes' and row['expected_exit'] == 0,
                'Shared valid-domain bounded case changed')
            value = ref(CORPUS / row['expected']['path'])
            require(value['sha256'] == row['expected']['sha256'], 'Retained bounded bytes changed')
            pins.append(value)
            cases.append(dict(n=row['n'], expected=value))
    require(sorted(row['n'] for row in cases) == BOUNDED, 'All eight valid-domain cases required')
    library = distribution / 'lib/pure/algorithm.nim'
    require(sha(library) == proposal['library']['pinned_source']['sha256'], 'Pinned general reversal helper changed')
    for value in proposal['candidates'].values():
        pins += [value['source_count_proposal'], value['diff']]
    for value in pins:
        check_ref(value)
    return dict(schema='nim-fannkuch-bounded-plan.v1', status='PREPARED-NOT-EXECUTED',
        output=str(output), controller=ref(__file__), pins=pins, sources=sources,
        runtime_restoration=ref(RESTORATION), runtime_files=restored['checked_distribution_pins'],
        distribution=str(distribution), compiler=restored['compiler'], external_build_pins=external,
        original_recipes=original_recipes, source_proposal=ref(PROPOSAL), cases=cases,
        work_n=WORK, arbitrary_intervals_n6=[list(pair) for pair in INTERVALS],
        invalid_arguments=INVALID, valid_source_domain=[1, 12],
        n0_policy='Expected source rejection, not successful empty-output corpus qualification.',
        private_library_delta='Only lib/pure/algorithm.nim receives trace helpers and a post-swap event; normal builds use the untouched original distribution.',
        environment=dict(PATH='/usr/bin:/bin', LC_ALL='C', LANG='C', TZ='UTC',
            OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1',
            DYLD_LIBRARY_PATH='/opt/homebrew/Cellar/pcre/8.45/lib:/opt/homebrew/Cellar/gmp/6.3.0/lib'),
        common_mutex=str(LOCK), common_mutex_inode=LOCK.stat().st_ino,
        quantitative_benchmark=False, chart_admission=False, application_loc=None,
        required_independent_source_review=True, maximum_trace_n=6,
        required_generated_code_review='Pending separate human review of captured C, standard reversal lowering, array copy/value semantics and byte layout.')


def unchanged(plan, runtime=True):
    for value in plan['pins']:
        check_ref(value)
    if runtime:
        runtime_pins(load(RESTORATION))
        for path, digest in plan['external_build_pins'].items():
            require(sha(path) == digest, 'Pinned native build dependency changed: ' + path)


def command_for(plan, name, source, binary, cache, library):
    recipe = plan['original_recipes'][plan['sources'][name]['parent']]['command']
    command = list(recipe)
    command[0], command[-1] = plan['compiler'], str(source)
    for index, value in enumerate(command):
        for option, replacement in [('--lib:', library), ('--nimcache:', cache), ('--out:', binary)]:
            if value.startswith(option):
                command[index] = option + str(replacement)
    require(normal_flags(command) == normal_flags(recipe), 'Build flag parity failed')
    return command


def run(plan_path, reviewed_sha):
    require(sha(plan_path) == reviewed_sha, 'Reviewed execution plan differs')
    plan = load(plan_path)
    output = Path(plan['output'])
    require(not output.exists(), 'Refuse to overwrite a previous qualification attempt')
    with LOCK.open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(plan == make_plan(output), 'Plan no longer reproduces from exact source/control receipts')
        require(os.fstat(lock.fileno()).st_ino == plan['common_mutex_inode'] == LOCK.stat().st_ino,
            'Common mutex identity changed')
        inherited = fcntl.fcntl(lock.fileno(), fcntl.F_DUPFD, 64)
        output.mkdir()
        report = dict(schema='nim-fannkuch-bounded-execution.v1', status='RUNNING',
            plan=ref(plan_path), controller=ref(__file__), started_utc=now(), active=None,
            common_mutex_inode=plan['common_mutex_inode'], common_mutex_fd=inherited,
            programs={}, outputs=[], rejected_arguments=[], work=[], diagnostic_intervals=[],
            quantitative_benchmark=False, chart_admission=False, application_loc=None,
            independent_source_review='Required separately; no count is approved by this controller.')
        atom(output / 'report.json', report)

        def execute(label, argv, compiler=False, expected_failure=False, timeout=180):
            report['active'] = label
            atom(output / 'report.json', report)
            row = one(argv, output / label, plan['environment'], ROOT, inherited, timeout=timeout)
            if expected_failure:
                require(row.get('exit_code') not in [None, 0] and not row.get('timed_out')
                    and not row.get('remaining_process_group_before_cleanup')
                    and not row.get('remaining_process_group') and 'error' not in row,
                    'Expected invalid-domain rejection did not exit cleanly')
                require(Path(row['stdout']['path']).read_bytes() == b'', 'Rejected arguments produced benchmark output')
            else:
                success(row)
                stderr = Path(row['stderr']['path']).read_bytes()
                if compiler:
                    require(not re.search(rb'\b(?:warning|error):', stderr, re.IGNORECASE),
                        'Unreviewed compilation diagnostic; retain the failed attempt')
                else:
                    require(stderr == b'', 'Unexpected runtime diagnostic')
            return row

        try:
            unchanged(plan)
            # A complete private lib copy changes exactly one module for untimed
            # observation. All normal applications use the untouched original.
            distribution = Path(plan['distribution'])
            stage = PACKET / '.build' / output.name
            require(not stage.exists(), 'Private build attempt already exists')
            stage.mkdir(parents=True)
            witness_lib = stage / 'witness-lib'
            shutil.copytree(distribution / 'lib', witness_lib)
            algorithm = distribution / 'lib/pure/algorithm.nim'
            before = algorithm.read_text()
            after = trace.library_twin(before)
            changed_module = witness_lib / 'pure/algorithm.nim'
            changed_module.write_text(after)
            durable = output / 'witness-library'
            durable.mkdir()
            shutil.copyfile(changed_module, durable / 'algorithm.nim')
            delta = durable / 'algorithm.diff'
            delta.write_text(trace.difference(before, after, str(algorithm), str(changed_module)))
            library_files = {}
            for relative, digest in plan['runtime_files'].items():
                if relative.startswith('lib/'):
                    path = witness_lib / relative.removeprefix('lib/')
                    expected = sha(changed_module) if relative == 'lib/pure/algorithm.nim' else digest
                    require(path.is_file() and sha(path) == expected, 'Private library has an unrelated changed file')
                    library_files[relative] = expected
            require({str(path.relative_to(witness_lib)) for path in witness_lib.rglob('*') if path.is_file()}
                == {path.removeprefix('lib/') for path in library_files}, 'Private library inventory changed')
            report['witness_library'] = dict(original=ref(algorithm), instrumented=ref(durable / 'algorithm.nim'),
                exact_diff=ref(delta), original_runtime_unchanged=True,
                changed_distribution_modules=['lib/pure/algorithm.nim'], files=library_files,
                observer_changes_only=True, compilation_performed=False)
            for label, argv in [('nim-version', [plan['compiler'], '--version']),
                    ('clang-version', [CLANG, '--version'])]:
                row = execute(label, argv)
                text = Path(row['stdout']['path']).read_text()
                if label == 'nim-version':
                    require('Nim Compiler Version 2.2.12 [MacOSX: arm64]' in text
                        and 'git hash: 8e8fbf60693418dc95bb0d762fd660231d08a583' in text,
                        'Actual compiler version differs')
                else:
                    require('22.1.8' in text, 'Actual Clang version differs')
            for name in NAMES:
                descriptor = plan['sources'][name]
                original = check_ref(descriptor['source'])
                report['programs'][name] = dict(**descriptor, builds={})
                for mode in ['normal', 'witness']:
                    folder = stage / mode / name
                    folder.mkdir(parents=True)
                    source, cache, binary = folder / 'fannkuch.nim', folder / 'nimcache', folder / 'fannkuch'
                    saved = output / 'source-snapshots' / mode / name
                    saved.mkdir(parents=True)
                    if mode == 'normal':
                        source.write_bytes(original.read_bytes())
                    else:
                        transformed = trace.source_twin(original.read_text(), descriptor['parallel'])
                        source.write_text(transformed)
                        (saved / 'source.diff').write_text(trace.difference(original.read_text(), transformed,
                            str(original), str(source)))
                    shutil.copyfile(source, saved / 'fannkuch.nim')
                    library = distribution / 'lib' if mode == 'normal' else witness_lib
                    command = command_for(plan, name, source, binary, cache, library)
                    row = execute('compile-' + mode + '-' + name, command, compiler=True)
                    require(binary.is_file(), 'Compiler returned success without an executable')
                    metadata = load(cache / 'fannkuch.json')
                    require(metadata['outputFile'] == str(binary) and metadata['extraCmds'] == [],
                        'Generated build output or extra command changed')
                    require(set(metadata['configFiles']) == {str(distribution / 'config/nim.cfg'),
                        str(distribution / 'config/config.nims')}, 'Unreviewed configuration loaded')
                    generated = output / 'generated-c' / mode / name
                    generated.mkdir(parents=True)
                    copies = []
                    for path in sorted(cache.iterdir()):
                        if path.suffix in ['.c', '.h', '.json']:
                            target = generated / path.name
                            shutil.copyfile(path, target)
                            copies.append(ref(target))
                    require(any(Path(item['path']).name == '@mfannkuch.nim.c' for item in copies),
                        'Missing complete generated application C')
                    generated_commands = [item[1] for item in metadata['compile']] + [metadata['linkcmd']]
                    require(all(not any(flag in item for flag in ['-mcpu', '-march', '-mtune', '-ffast-math'])
                        for item in generated_commands), 'Actual C target/numerical flags changed')
                    require(all('-O3' in item and '-fno-strict-aliasing' in item and '-pthread' in item
                        for item in generated_commands[:-1]), 'Actual C compilation flags differ')
                    linked = execute('linked-' + mode + '-' + name, ['/usr/bin/otool', '-L', str(binary)])
                    machine = (execute('machine-code-' + mode + '-' + name,
                        ['/usr/bin/otool', '-tvV', str(binary)]) if mode == 'normal' else None)
                    report['programs'][name]['builds'][mode] = dict(command=command,
                        source=ref(saved / 'fannkuch.nim'), native_source=ref(source), binary=ref(binary),
                        generated_c=copies, native_build_metadata=ref(cache / 'fannkuch.json'),
                        build_process=ref(output / ('compile-' + mode + '-' + name) / 'process.json'),
                        library='original-pinned' if mode == 'normal' else 'trace-only-private-copy',
                        exact_source_diff=ref(saved / 'source.diff') if mode == 'witness' else None,
                        linked_image_evidence=linked, machine_code_evidence=machine)
                    atom(output / 'report.json', report)
            spec = importlib.util.spec_from_file_location('retained_fannkuch_reference', REFERENCE)
            reference = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(reference)
            for case in plan['cases']:
                n = case['n']
                expected = check_ref(case['expected']).read_bytes()
                require(reference.fannkuchredux(n) == expected, 'Shared independent reference/corpus differ')
                for name in NAMES:
                    binary = check_ref(report['programs'][name]['builds']['normal']['binary'])
                    row = execute(f'bounded-n{n}/{name}', [binary, str(n)], timeout=30)
                    require(Path(row['stdout']['path']).read_bytes() == expected,
                        'Complete bounded output differs: ' + name)
                    report['outputs'].append(dict(name=name, n=n, expected=case['expected'],
                        process=row, exact_complete_output=True))
                if n in WORK:
                    require(work.output(work.expected_work(n), n) == expected, 'Detailed trace oracle/corpus differ')
                    for name in NAMES:
                        descriptor = plan['sources'][name]
                        binary = check_ref(report['programs'][name]['builds']['witness']['binary'])
                        directory = output / f'work-n{n}' / name
                        directory.mkdir(parents=True)
                        row = execute(f'work-process-n{n}/{name}', [binary, str(n), str(directory)], timeout=60)
                        raw = Path(row['stdout']['path']).read_bytes()
                        require(raw == expected, 'Normal/instrumented whole output differs')
                        validation = work.validate(directory, n, descriptor['parallel'], descriptor['guarded'], raw)
                        report['work'].append(dict(name=name, n=n, process=row, validation=validation,
                            trace_files=[ref(path) for path in sorted(directory.iterdir())]))
                atom(output / 'report.json', report)
            for name in NAMES:
                binary = check_ref(report['programs'][name]['builds']['normal']['binary'])
                for number, arguments in enumerate(INVALID):
                    row = execute(f'rejected-{number}/{name}', [binary, *arguments], expected_failure=True, timeout=30)
                    report['rejected_arguments'].append(dict(name=name, arguments=arguments,
                        process=row, valid_domain_extension_claimed=False))
            for name in NAMES:
                descriptor = plan['sources'][name]
                if not descriptor['parallel']:
                    continue
                binary = check_ref(report['programs'][name]['builds']['witness']['binary'])
                for first, last in INTERVALS:
                    directory = output / f'interval-{first}-{last}' / name
                    directory.mkdir(parents=True)
                    row = execute(f'interval-process-{first}-{last}/{name}',
                        [binary, '6', str(directory), str(first), str(last)], timeout=30)
                    validation = work.validate(directory, 6, True, descriptor['guarded'],
                        Path(row['stdout']['path']).read_bytes(), first, last)
                    report['diagnostic_intervals'].append(dict(name=name, process=row, validation=validation,
                        trace_files=[ref(path) for path in sorted(directory.iterdir())]))
            unchanged(plan)
            require(os.fstat(lock.fileno()).st_ino == plan['common_mutex_inode'] == LOCK.stat().st_ino,
                'Common mutex changed during qualification')
            report.update(status='PASSED-BOUNDED-WORK-PENDING-INDEPENDENT-CODE-REVIEW',
                active=None, finished_utc=now(), pins_unchanged=True,
                complete_output_observations=len(report['outputs']),
                detailed_complete_work_observations=len(report['work']),
                native_code_review='Captured; independent review still required.',
                source_counts='Proposals remain null/unapproved until independent native/source review.',
                timing_samples=0, full_processes=0, original_runtime_unchanged=True)
        except BaseException as error:
            report.update(status='FAILED', error=repr(error), finished_utc=now())
            raise
        finally:
            atom(output / 'report.json', report)
            os.close(inherited)
    print(report['status'], len(report['outputs']), len(report['work']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--reviewed-plan-sha256')
    args = parser.parse_args()
    require(args.prepare != args.run, 'Choose exactly one mode')
    if args.prepare:
        require(args.output is not None and not args.plan.exists(), 'Fresh plan and output paths required')
        with LOCK.open('a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            atom(args.plan, make_plan(args.output.resolve()))
        print(sha(args.plan))
    else:
        require(args.reviewed_plan_sha256 is not None, 'Native execution requires a reviewed plan digest')
        run(args.plan.resolve(), args.reviewed_plan_sha256)
