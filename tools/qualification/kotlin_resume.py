"""Add the missing Kotlin compiles and class-owner dumps to retained evidence.

This stage executes compilers and javap only. It never executes benchmark mains,
admits timing/LOC results, reruns successful commands, or changes retained files.
"""
import argparse
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import traceback


OLD = Path('/Users/cim310/mech-lang/benchmarks')
COHORT = OLD/'benchmarks/clbg/kotlin-comparison/20261013'
REVISION = COHORT/'revisions/subject20-compile-owners-v1'
RETAINED = REVISION/'jobs/subject20-compile-owners-v1'
OUTCOME_SHA = '0fc1bb0cbb31839e6de511203c40f8c944a87b8a8bcfd9cabf89df7a89193db4'
CLOSED = OLD/'benchmarks/clbg/continuation/jobs/kotlin-saved-probe-closed-review-v1/receipt.json'
CLOSED_SHA = '0d0c8d6ac6bc18577f5b71979408e86ce3c557b63387f2c7ddd0598cdac0260b'
FLAGS = ['-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx8g', '-XX:+UseG1GC']
LOCK = Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE = 79859134
COMPILED = ['kotlin-binarytrees-compact', 'kotlin-binarytrees-optimized', 'kotlin-fannkuchredux-compact']
DECODED = COMPILED[:2]
EDITORIAL_PATHS = {
    'archive/languages/kotlin/20261013/revisions/subject20-compile-owners-v1/REVIEW.md',
    'archive/languages/kotlin/20261013/revisions/saved-runtime-probe-v1/REVIEW.md',
    'archive/qualification/shared/records/launch_durable_v1.py',
}
QUALIFICATION_GATES = {
    'bytecode_semantic_owner_review_qualified': False,
    'actual_subject_runtime_dependency_closure_qualified': False,
    'raw_stdio_qualified': False,
    'source_work_qualified': False,
    'subject_JIT_method_evidence_qualified': False,
    'canonical_loc': None, 'formatted_loc': None, 'chart_admission': False,
}


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


class Evidence:
    """Relocate archived receipts; retain exact original host execution paths."""
    def __init__(self, root, overrides):
        self.root = Path(root).resolve()
        with (self.root/'migration/reorganization-paths.tsv').open() as stream:
            rows = list(csv.DictReader(stream, delimiter='\t'))
        self.mapping = {row['original_path']: row['current_path'] for row in rows}
        require(len(rows) == len(self.mapping), 'Duplicate migration entries')
        require(overrides['schema'] == 'kotlin-retired-orchestration-substitutions-v1', 'Wrong editorial schema')
        require(all(r['current_path'] in EDITORIAL_PATHS for r in overrides['substitutions']), 'Unexpected editorial substitution')
        self.overrides = {(r['current_path'], r['historical_sha256']): r for r in overrides['substitutions']}
        require(len(self.overrides) == len(overrides['substitutions']), 'Duplicate editorial substitution')
        self.records, self.pins = {}, {}

    def path(self, logical):
        p = Path(logical)
        require(p.is_absolute() and '..' not in p.parts, ('Invalid receipt path', str(p)))
        if p.is_relative_to(OLD):
            relative = str(p.relative_to(OLD))
            if relative in self.mapping:
                target = (self.root/self.mapping[relative]).resolve()
                require(target.is_relative_to(self.root), 'Migration escape')
                return target
            # Untracked generated classes remain at their original execution path.
            require(p.is_relative_to(COHORT/'.build'), ('Unmapped old repository path', str(p)))
        return p

    def bind(self, logical, expected):
        logical = str(logical)
        require(re.fullmatch('[a-f0-9]{64}', expected), 'Invalid pin')
        require(logical not in self.pins or self.pins[logical] == expected, ('Conflicting pin', logical))
        path = self.path(logical)
        require(path.is_file(), ('Missing file evidence', str(path)))
        actual = sha(path)
        replacement = None
        if actual != expected:
            relative = str(path.relative_to(self.root)) if path.is_relative_to(self.root) else str(path)
            replacement = self.overrides.get((relative, expected))
            require(replacement and replacement['current_sha256'] == actual and
                    replacement['technical_content_preserved'] is True and
                    replacement['executed'] is False and path.suffix in ('.md', '.py'),
                    ('Changed pinned bytes', logical, str(path), expected, actual))
        self.pins[logical] = expected
        self.records[logical] = dict(historical_path=logical, resolved_path=str(path),
            physical_target=str(path.resolve()), historical_sha256=expected,
            active_sha256=actual, editorial_substitution=replacement)
        return path

    def read(self, logical, expected=None):
        path = self.bind(logical, expected or self.pins[str(logical)])
        require(self.records[str(logical)]['editorial_substitution'] is None, 'JSON evidence cannot be substituted')
        return json.loads(path.read_text())

    def absorb(self, mapping):
        for path, digest in mapping.items():
            if path not in self.pins:
                self.bind(path, digest)
            else:
                require(self.pins[path] == digest, ('Conflicting pin', path))

    def unchanged(self):
        for record in self.records.values():
            require(sha(record['resolved_path']) == record['active_sha256'],
                    ('Changed during qualification', record['resolved_path']))


def successful(detail):
    require(type(detail.get('exit_status')) is int and detail['exit_status'] == 0 and
            type(detail.get('final_exit_status')) is int and detail['final_exit_status'] == 0,
            'Native command did not exit successfully')
    require(detail.get('inherited_common_mutex') is True, 'Command lacked the common mutex')
    require(detail.get('preparation_only') is True and detail.get('never_chart_eligible') is True,
            'Unexpected command qualification scope')
    require(detail.get('identity') and detail.get('pid'), 'Missing native process identity')
    require(not any(detail.get(k) for k in ('timeout', 'timed_out', 'error', 'stop_signals')), 'Interrupted native command')


def pin_command(e, directory):
    """Pin full streams and both process receipts before continuing."""
    for path in sorted(directory.iterdir()):
        require(path.is_file() and not path.is_symlink(), 'Unexpected command evidence')
        e.bind(str(path), sha(path))


def class_artifacts(classes, benchmark, pins=None):
    artifacts, owners = [], []
    require(classes.is_dir() and not classes.is_symlink(), 'Missing class directory')
    for path in sorted(classes.rglob('*')):
        require(not path.is_symlink(), ('Symlink in classes', str(path)))
        if not path.is_file():
            continue
        relative = path.relative_to(classes)
        require(path.suffix == '.class' or str(relative) == 'META-INF/main.kotlin_module', 'Unexpected compiler artifact')
        if path.suffix == '.class':
            raw = path.read_bytes()
            require(raw[:4] == b'\xca\xfe\xba\xbe' and int.from_bytes(raw[6:8], 'big') == 61, 'Wrong class target')
            require(relative.parts[0] == 'clbg' and
                    (relative.parts[1] == benchmark or str(relative).startswith('clbg/Support')), 'Unexpected class owner')
            owners.append(relative.with_suffix('').as_posix().replace('/', '.'))
        digest = sha(path)
        if pins is not None:
            require(pins.get(str(path)) == digest, ('Unpinned retained class', str(path)))
        artifacts.append(dict(path=str(path), sha256=digest, bytes=path.stat().st_size))
    require('clbg.Support' in owners and 'clbg.'+benchmark+'.MainKt' in owners, 'Missing application/helper owner')
    if pins is not None:
        expected = {p for p in pins if Path(p).is_relative_to(classes)}
        require(expected == {a['path'] for a in artifacts}, 'Retained class set changed')
    return artifacts, owners


def validate_inventory(inventory, compiler):
    rows = inventory['forms']
    require(len(rows) == len({r['id'] for r in rows}) == 20, 'Expected twenty source forms')
    require([r['id'] for r in rows[:3]] == COMPILED, 'Retained prefix changed')
    require(len({r['benchmark'] for r in rows}) == 10, 'Expected ten workloads')
    for row in rows:
        require(re.fullmatch(r'kotlin-[a-z]+-(compact|optimized)', row['id']), 'Unsafe profile id')
        inputs = row['authored_inputs']
        require(len(inputs) == 2 and [i['role'] for i in inputs] == ['application', 'application-helper'] and
                all(i['counted'] is True for i in inputs), 'Incomplete counted source bundle')
        main, support = [i['path'] for i in inputs]
        require(row['compile_command_proposed'] == [compiler, support, main, '-jvm-target', '17', '-no-reflect', '-d', str(Path(main).parent/'classes')],
                'Compilation flags or source binding changed')
    return rows


def preflight(e):
    outcome = e.read(RETAINED/'outcome.json', OUTCOME_SHA)
    require(outcome['status'] == 'failed-terminal-integrity' and outcome['error_type'] == 'FileNotFoundError', 'Unexpected stop reason')
    require((outcome['compiler_commands_requested'], outcome['compiler_commands_completed'],
             outcome['reader_commands_requested'], outcome['reader_commands_completed']) == (3, 3, 2, 2), 'Changed native command prefix')
    require(outcome['completed_profile_ids'] == DECODED and outcome['subject_main_executions'] == 0, 'Changed completed profile prefix')
    require(len(outcome['integrity_errors']) == 22 and all('No such file or directory' in r['error'] for r in outcome['integrity_errors']),
            'Failure included more than relocation errors')
    for item in outcome['integrity_errors']:
        require(item['path'] in outcome['prerequisite_pins'] and e.path(item['path']).is_file(), 'Unresolved relocation')
    e.absorb(outcome['prerequisite_pins'])
    e.absorb(outcome['available_evidence_pins'])
    closed = e.read(CLOSED, CLOSED_SHA)
    require(closed['status'] == 'closed-Kotlin-saved-generic-runtime-probe-passed-no-subject-execution' and
            closed['verified_pins'] == 5460 and closed['common_mutex_held'] is True and closed['common_mutex_inode'] == LOCK_INODE,
            'Generic runtime probe not closed')
    require(closed['subject_compiler_commands'] == closed['native_benchmarks'] == closed['old_tool_fixture_reexecutions'] == 0,
            'Unexpected generic probe scope')
    require(closed['source_forms'] == 20 and closed['counted_main_and_helper_inputs'] == 40 and closed['chart_admission'] is False,
            'Wrong saved source/runtime cohort')
    e.absorb(closed['pins'])
    terminal = e.read(closed['durable_terminal_path'], closed['durable_terminal_sha256'])
    require(terminal['status'] == 'command-exited-zero-awaiting-report-review' and
            type(terminal['exit_code']) is int and terminal['exit_code'] == 0 and terminal['stop_signals'] == [] and
            terminal['actual_command_started'] is True and terminal['command_identity_observation_missing'] is False,
            'Generic probe durable terminal failed')
    saved = e.read(closed['preparation_result_path'], closed['preparation_result_sha256'])
    e.absorb(saved['pins'])
    require(saved['actual_generic_runtime_probe'] == closed['actual_generic_runtime_probe'] and
            saved['actual_jvm_flags'] == closed['actual_jvm_flags'] and saved['actual_jvm_flags'][:4] == FLAGS and
            saved['actual_collectors'] == closed['actual_collectors'], 'Runtime probe mismatch')
    require(saved['runtime_environment']['JAVA_HOME'] == saved['actual_generic_runtime_probe']['JAVA_HOME'] and
            saved['actual_generic_runtime_probe']['OS_ARCH'] == 'aarch64' and
            saved['actual_generic_runtime_probe']['PROCESSORS'] == '8' and
            saved['actual_generic_runtime_probe']['MAX_HEAP'] == '8589934592', 'Saved runtime configuration changed')
    require(saved['subject_compiler_commands'] == saved['native_benchmarks'] == saved['fixture_reexecutions'] == 0,
            'Saved generic probe executed a subject')
    inventory_ref = saved['retained_source_inventory']
    inventory = e.read(inventory_ref['path'], inventory_ref['sha256'])
    rows = validate_inventory(inventory, saved['compiler'])
    for row in rows:
        for source in row['authored_inputs']:
            # Compiler-bound physical inputs always keep their exact historical bytes.
            e.bind(source['path'], source['sha256'])
            require(e.records[source['path']]['editorial_substitution'] is None, 'Source substitution forbidden')
    old_pins = dict(e.pins)
    retained = {}
    for row in rows[:3]:
        identifier = row['id']; case = RETAINED/identifier
        detail = e.read(case/'compile/compile.json')
        successful(detail)
        command = detail['command']
        require(command[:-1] == row['compile_command_proposed'][:-1] and
                command[-1] == str(COHORT/'.build/subject20-compile-owners-v1'/identifier/'classes'), 'Wrong retained compile command')
        for name in ('stdout', 'stderr'):
            require(e.path(case/('compile/compile.'+name)).read_bytes() == b'', 'Retained compiler diagnostic')
        artifacts, owners = class_artifacts(Path(command[-1]), row['benchmark'], old_pins)
        record = None
        if identifier in DECODED:
            record = e.read(case/'result.json')
            require(record['compile_command'] == detail and record['generated_artifacts'] == artifacts and
                    record['class_owner_names'] == owners and record['physical_inputs'] == row['authored_inputs'], 'Retained record mismatch')
            successful(record['bytecode_reader'])
            decoded = e.read(case/'owners/javap.json')
            require(decoded == record['bytecode_reader'], 'Owner command mismatch')
            require(decoded['command'][-len(owners):] == owners and
                    e.path(case/'owners/javap.stderr').read_bytes() == b'' and
                    e.path(case/'owners/javap.stdout').stat().st_size > 0, 'Invalid retained owner dump')
            require(all(record[k] == value for k, value in QUALIFICATION_GATES.items()), 'Retained artifact stage unexpectedly claims qualification')
        retained[identifier] = dict(detail=detail, artifacts=artifacts, owners=owners, record=record)
    return saved, rows, retained


def verify_lock(lock):
    a, b = os.fstat(lock.fileno()), LOCK.stat()
    require((a.st_dev, a.st_ino) == (b.st_dev, b.st_ino) and a.st_ino == LOCK_INODE, 'Common mutex replaced')


def owned(command, environment, directory, name, timeout, lock):
    directory.mkdir(parents=True, exist_ok=False)
    verify_lock(lock)
    record = dict(command=command, environment=environment, started_at=datetime.now(timezone.utc).isoformat(),
        inherited_common_mutex=True, common_mutex_inode=LOCK_INODE, preparation_only=True,
        never_chart_eligible=True, timeout_seconds=timeout, stop_signals=[])
    process = None
    try:
        with (directory/(name+'.stdout')).open('xb') as out, (directory/(name+'.stderr')).open('xb') as err:
            process = subprocess.Popen(command, env=environment, cwd=directory, stdin=subprocess.DEVNULL,
                stdout=out, stderr=err, start_new_session=True, pass_fds=(lock.fileno(),))
            record['pid'] = process.pid
            listing = subprocess.check_output(['/bin/ps', '-p', str(process.pid), '-o', 'pid=,ppid=,pgid=,lstart=,command='], text=True).strip()
            require(listing and int(listing.split()[0]) == process.pid and int(listing.split()[2]) == process.pid, 'Missing owned process group identity')
            record['identity'] = dict(pid=process.pid, process_listing=listing)
            save(directory/(name+'.active.json'), record)
            record['exit_status'] = process.wait(timeout=timeout)
            record['final_exit_status'] = process.returncode
            listing = subprocess.check_output(['/bin/ps', '-axo', 'pid=,pgid=,stat=,command='], text=True)
            remaining = [line.strip() for line in listing.splitlines()
                         if len(line.split()) >= 3 and line.split()[1] == str(process.pid)]
            record['remaining_process_group'] = remaining
            require(not remaining, 'Compiler/reader left running children')
            successful(record)
    except BaseException as error:
        record.update(error=str(error), error_type=type(error).__name__)
        if process is not None:
            # A child can retain the group after its immediate compiler exits.
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(process.pid, sig); record['stop_signals'].append(int(sig))
                except ProcessLookupError:
                    break
            record['final_exit_status'] = process.wait()
        raise
    finally:
        record['finished_at'] = datetime.now(timezone.utc).isoformat()
        save(directory/(name+'.json'), record)
        verify_lock(lock)
    return record


def execute(e, saved, rows, retained, output, build, lock, progress):
    compiler = saved['compiler']; java = saved['runtime_environment']['JAVACMD']
    javap = str(Path(java).with_name('javap')); stdlib = str(Path(compiler).parent.parent/'lib/kotlin-stdlib.jar')
    for p in (compiler, java, javap, stdlib):
        require(p in e.pins, ('Unpinned executable/runtime', p))
        require(e.records[p]['editorial_substitution'] is None, 'Executable substitution forbidden')
    profiles = []
    for row in rows:
        identifier = row['id']; case = output/identifier
        previous = retained.get(identifier)
        if identifier in DECODED:
            profiles.append(previous['record'])
            progress['reused_profile_ids'].append(identifier)
            continue
        folder = build/identifier
        folder.mkdir()
        for name in ('home', 'config', 'tmp'):
            (folder/name).mkdir()
        flags = FLAGS+['-Duser.home='+str(folder/'home'), '-Djava.io.tmpdir='+str(folder/'tmp')]
        environment = dict(saved['runtime_environment'])
        require(not any(k in environment for k in ('JDK_JAVA_OPTIONS', 'JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS')), 'Injected JVM options')
        environment.update(HOME=str(folder/'home'), XDG_CONFIG_HOME=str(folder/'config'), TMPDIR=str(folder/'tmp')+os.sep,
                           JAVA_OPTS=' '.join(flags))
        if previous:
            compiled, artifacts, owners = previous['detail'], previous['artifacts'], previous['owners']
            classes = Path(compiled['command'][-1])
        else:
            classes = folder/'classes'; classes.mkdir()
            command = row['compile_command_proposed'][:-1]+[str(classes)]
            e.unchanged()
            progress['new_compile_requests'] += 1
            compiled = owned(command, environment, case/'compile', 'compile', 180, lock)
            progress['new_compiles_completed'] += 1
            pin_command(e, case/'compile')
            require((case/'compile/compile.stdout').read_bytes() == (case/'compile/compile.stderr').read_bytes() == b'',
                    'Compiler diagnostics retained; no automatic retry')
            artifacts, owners = class_artifacts(classes, row['benchmark'])
            for artifact in artifacts:
                p = Path(artifact['path']); p.chmod(p.stat().st_mode & ~0o222)
                e.bind(str(p), artifact['sha256'])
        classpath = str(classes)+os.pathsep+stdlib
        command = [javap, *['-J'+f for f in flags], '-classpath', classpath, '-p', '-c', '-s', '-v', *owners]
        e.unchanged()
        progress['new_reader_requests'] += 1
        decoded = owned(command, environment, case/'owners', 'javap', 120, lock)
        progress['new_readers_completed'] += 1
        pin_command(e, case/'owners')
        require((case/'owners/javap.stderr').read_bytes() == b'' and (case/'owners/javap.stdout').stat().st_size > 0,
                'Invalid javap output')
        record = dict(id=identifier, benchmark=row['benchmark'], variant=row['variant'], alias_of=row['alias_of'],
            physical_inputs=row['authored_inputs'], compile_command=compiled, generated_artifacts=artifacts,
            class_owner_names=owners, classfile_target_major=61, bytecode_reader=decoded,
            runtime_command=[java, *flags, '-cp', classpath, 'clbg.'+row['benchmark']+'.MainKt', '{n}'],
            runtime_environment=environment, runtime_classpath_candidates=[dict(path=stdlib, sha256=e.pins[stdlib])],
            source_to_compile_command_binding=True, **QUALIFICATION_GATES)
        save(case/'result.json', record)
        e.bind(str(case/'result.json'), sha(case/'result.json'))
        profiles.append(record)
        progress['completed_profile_ids'].append(identifier)
        print('Captured Kotlin classes and owners:', identifier, flush=True)
    require(len(profiles) == 20 and progress['new_compiles_completed'] == 17 and progress['new_readers_completed'] == 18,
            'Additive command totals differ from plan')
    e.unchanged()
    save(output/'preparation-result.json', dict(status='Kotlin20-classes-and-bytecode-captured-awaiting-scored-owner-and-runtime-review',
        profiles=profiles, source_inventory=saved['retained_source_inventory'], total_compiled_profiles=20,
        retained_compiler_commands=3, retained_bytecode_reader_commands=2, new_compiler_commands=17,
        new_bytecode_reader_commands=18, passed_tool_fixture_reexecutions=0, subject_main_executions=0,
        pins=e.pins, portable_pin_resolution='evidence-resolution.json', **QUALIFICATION_GATES))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--execute', action='store_true', help='Run only the 17 missing compiles and 18 missing javap commands')
    args = parser.parse_args()
    require(sys.dont_write_bytecode, 'Run with -B; qualification must not create bytecode caches')
    args.output, args.build = args.output.resolve(), args.build.resolve()
    require(args.output != args.build and not args.output.is_relative_to(args.build) and not args.build.is_relative_to(args.output),
            'Output and build trees must be separate')
    require(not args.output.exists() and not args.build.exists(), 'Fresh output/build paths required; no retry or overwrite')
    config = args.root/'experiments/kotlin/editorial-substitutions.json'
    e = Evidence(args.root, json.loads(config.read_text()))
    progress = dict(status='failed', new_compile_requests=0, new_compiles_completed=0,
        new_reader_requests=0, new_readers_completed=0, reused_profile_ids=[], completed_profile_ids=[],
        subject_main_executions=0, passed_tool_fixture_reexecutions=0, chart_admission=False)
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Qualification interrupted: '+str(signum))
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_lock(lock)
        args.output.mkdir(parents=True); args.build.mkdir(parents=True)
        try:
            e.bind(str(Path(__file__).resolve()), sha(__file__))
            e.bind(str(config.resolve()), sha(config))
            saved, rows, retained = preflight(e)
            require(str(Path(sys.executable).resolve()) in e.pins, 'Qualification interpreter is outside the retained closure')
            save(args.output/'plan.json', dict(retained_compiles=COMPILED, retained_owner_dumps=DECODED,
                compile=[r['id'] for r in rows if r['id'] not in COMPILED],
                javap=[r['id'] for r in rows if r['id'] not in DECODED], subject_main_executions=0,
                generic_runtime_probe_reexecutions=0, source_forms=20, counted_main_and_helper_inputs=40,
                generic_runtime_receipt=dict(path=str(CLOSED), sha256=CLOSED_SHA), chart_admission=False))
            e.bind(str(args.output/'plan.json'), sha(args.output/'plan.json'))
            if args.execute:
                execute(e, saved, rows, retained, args.output, args.build, lock, progress)
            e.unchanged()
            progress['status'] = 'Kotlin20-class-owner-capture-complete-awaiting-semantic-review' if args.execute else 'Kotlin-additive-plan-pinned-no-native-commands'
        except BaseException as error:
            progress.update(error=str(error), error_type=type(error).__name__)
            (args.output/'error.log').write_text(traceback.format_exc())
            raise
        finally:
            integrity_errors = []
            for check in (e.unchanged, lambda: verify_lock(lock)):
                try:
                    check()
                except BaseException as error:
                    integrity_errors.append(dict(error=str(error), error_type=type(error).__name__))
            if integrity_errors:
                progress.update(status='failed-terminal-integrity', integrity_errors=integrity_errors)
            save(args.output/'evidence-resolution.json', dict(schema='kotlin-portable-evidence-resolution-v1', records=list(e.records.values()),
                historical_receipts_unchanged=True, retired_orchestration_executed=False))
            progress['finished_at'] = datetime.now(timezone.utc).isoformat()
            progress['available_evidence_pins'] = {str(p): sha(p) for p in args.output.rglob('*') if p.is_file()}
            progress['generated_artifact_pins'] = {str(p): sha(p) for p in args.build.rglob('*') if p.is_file()
                and not any(part in ('home', 'config', 'tmp') for part in p.relative_to(args.build).parts)}
            save(args.output/'outcome.json', progress)
            print(json.dumps({k: v for k, v in progress.items() if not k.endswith('_pins')}), flush=True)
            if integrity_errors:
                raise RuntimeError('Kotlin terminal integrity failed; partial evidence retained')


if __name__ == '__main__':
    main()
