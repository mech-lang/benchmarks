"""Probe retained Elixir helper BEAMs with real nonempty stdin; never run mains."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
COHORT = ROOT / 'archive/languages/elixir/20261013'
LOCK = Path('/tmp/mech-clbg-timing.lock')
COMPILER_RECEIPT = COHORT / 'revisions/remaining19-compile-owners-v1/jobs/remaining19-compile-owners-v1/preparation-result.json'
COMPILER_SHA = '6a45e7514c68a300b3d3770e713a3c7a9a91744b5ef149f5ec5c626e5ec4fffe'
FIRST_RECEIPT = COHORT / 'jobs/saved-first-compile-owner-writer-v1/preparation-result.json'
FIRST_SHA = 'a5eec9dbf0c93c68ada489fa00aab486306ce5585e1fe0a2af8678c532398206'
SUPPORT_SHA = 'c9fbb60888c46fb50195245761a411716f1256145af367e03a23f70aea270e89'
ELIXIR = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg/elixir-comparison/20261013/.build/retained-otp-toolchain-v1/elixir')
OTP = Path('/opt/homebrew/Cellar/erlang/29.1.1_2')


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def group(pid):
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,pgid='], capture_output=True, text=True, check=True, timeout=5)
    return [int(parts[0]) for line in result.stdout.splitlines()
            if len(parts := line.split()) == 2 and int(parts[1]) == pid]


def no_core():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def observe(command, environment, output, payload, lock):
    record = dict(command=command, environment=environment, cwd=str(output),
                  started_at=datetime.now(timezone.utc).isoformat(), timeout_seconds=30,
                  cleanup_timeout_seconds=5, common_mutex_held=True, benchmark_samples=0,
                  subject_main_executions=0, status='starting', stop_signals=[], cleanup_errors=[],
                  stdin_bytes=len(payload), stdin_sha256=hashlib.sha256(payload).hexdigest(),
                  stdout_path=str(output/'stdout.bin'), stderr_path=str(output/'stderr.txt'))
    process = None
    save(output/'process.json', record)
    try:
        # Direct artifacts retain partial output even if this supervisor dies.
        with (output/'stdout.bin').open('xb') as stdout_file, (output/'stderr.txt').open('xb') as stderr_file:
            process = subprocess.Popen(command, cwd=output, env=environment,
                stdin=subprocess.PIPE, stdout=stdout_file, stderr=stderr_file,
                start_new_session=True, pass_fds=(lock.fileno(),), preexec_fn=no_core)
            record.update(pid=process.pid, pgid=process.pid, status='running')
            save(output/'process.json', record)
            process.communicate(payload, timeout=30)
            record.update(exit_status=process.returncode, remaining_process_group=group(process.pid))
            require(process.returncode == 0, 'Helper process failed; raw output retained')
            require(not record['remaining_process_group'], 'Helper left running descendants')
        stdout, stderr = (output/'stdout.bin').read_bytes(), (output/'stderr.txt').read_bytes()
        require(not stderr and stdout == payload, 'Helper output differs; raw output retained')
        record['status'] = 'passed'
    except BaseException as error:
        record.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
        if isinstance(error, subprocess.TimeoutExpired):
            record['timed_out'] = True
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
                record['stop_signals'].append(int(signal.SIGKILL))
            except ProcessLookupError:
                pass
            except BaseException as cleanup_error:
                record['cleanup_errors'].append(str(cleanup_error) or type(cleanup_error).__name__)
            try:
                deadline = time.monotonic() + 5
                process.communicate(timeout=max(0.001, deadline-time.monotonic()))
                record['exit_status'] = process.returncode
                while remaining := group(process.pid):
                    record['remaining_after_cleanup'] = remaining
                    require(time.monotonic() < deadline, 'Helper process group survived cleanup')
                    time.sleep(0.05)
                record['remaining_after_cleanup'] = []
            except BaseException as cleanup_error:
                record['cleanup_errors'].append(str(cleanup_error) or type(cleanup_error).__name__)
        raise
    finally:
        for name, prefix in (('stdout.bin', 'stdout'), ('stderr.txt', 'stderr')):
            path = output/name
            try:
                require(path.is_file(), ('Missing output artifact', name))
                record[prefix+'_bytes'], record[prefix+'_sha256'] = path.stat().st_size, sha(path)
            except BaseException as artifact_error:
                record.setdefault('artifact_errors', []).append(str(artifact_error) or type(artifact_error).__name__)
                record['status'] = 'failed-artifact-integrity'
        record['complete_output_matches'] = (record.get('stdout_bytes'), record.get('stdout_sha256')) == (
            len(payload), hashlib.sha256(payload).hexdigest())
        record['finished_at'] = datetime.now(timezone.utc).isoformat()
        save(output/'process.json', record)
        require(not record.get('artifact_errors') and not record['cleanup_errors'], 'Helper cleanup/artifact integrity failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.exists(), 'Fresh output required; no overwrite or automatic retry')
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Helper qualification interrupted: ' + str(signum))
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        opened, named = os.fstat(lock.fileno()), LOCK.stat()
        require((opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
                and opened.st_ino == 79859134, 'Shared lock changed')
        pins = {}
        def bind(path, expected):
            path = Path(path)
            require(sha(path) == expected, ('Changed pinned input', str(path)))
            require(str(path) not in pins or pins[str(path)] == expected, 'Conflicting pin')
            pins[str(path)] = expected
            return path
        compiled = json.loads(bind(COMPILER_RECEIPT, COMPILER_SHA).read_bytes())
        first = json.loads(bind(FIRST_RECEIPT, FIRST_SHA).read_bytes())
        require(compiled['total_compiled_profiles'] == len(compiled['profiles']) == 20, 'Incomplete retained cohort')
        require(len({row['id'] for row in compiled['profiles']}) == 20, 'Duplicate profile')
        # This bounded diagnostic depends on exact runtime and source/BEAM bytes;
        # it does not certify or replay historical orchestration closures.
        for path, digest in compiled['pins'].items():
            if Path(path).is_relative_to(ELIXIR) or Path(path).is_relative_to(OTP):
                bind(path, digest)
        require(str(ELIXIR/'bin/elixir') in pins and str(OTP/'erts-17.1/bin/beam.smp') in pins,
                'Missing retained runtime executable pins')
        probe = ROOT/'experiments/elixir/helper-semantics/probe.exs'
        vectors = probe.with_name('format-vectors.tsv')
        generator = probe.with_name('generate_vectors.py')
        for path in (Path(__file__).resolve(), probe, vectors, generator):
            bind(path, sha(path))
        spec = importlib.util.spec_from_file_location('elixir_format_vector_generator', generator)
        vector_module = importlib.util.module_from_spec(spec)
        generator_source = generator.read_bytes()
        require(hashlib.sha256(generator_source).hexdigest() == pins[str(generator)], 'Generator changed before loading')
        exec(compile(generator_source, str(generator), 'exec'), vector_module.__dict__)
        generated = list(vector_module.vectors())
        require(len(generated) == 1536, 'Formatting vector inventory changed')
        expected_vectors = ''.join('\t'.join(row)+'\n' for row in generated).encode()
        require(vectors.read_bytes() == expected_vectors, 'Vectors differ from the independent Python formatter')
        for row in compiled['profiles']:
            for item in row['physical_inputs'] + row['beams']:
                bind(item['path'], item['sha256'])
            helper = next(item for item in row['physical_inputs'] if item['role'] == 'application-helper')
            require(helper['sha256'] == SUPPORT_SHA, 'Unexpected helper source')
        output.mkdir(parents=True)
        payload = bytes(range(256))*1027 + b'\x00\r\n\x1bFINAL-WITHOUT-NEWLINE'
        (output/'input.bin').write_bytes(payload)
        report = dict(status='running', scope='compiled-helper-stdio-and-format-semantics',
                      pins=pins, profile_ids=[], benchmark_samples=0, subject_main_executions=0,
                      source_work_qualified=False, chart_admission=False,
                      payload_sha256=hashlib.sha256(payload).hexdigest(), payload_bytes=len(payload))
        save(output/'report.json', report)
        try:
            for row in compiled['profiles']:
                case = output/row['id']; case.mkdir()
                for name in ('home', 'config', 'tmp'):
                    (case/name).mkdir()
                environment = dict(first['runtime_environment'] if row['reused'] else row['runtime_environment'])
                environment.update(HOME=str(case/'home'), XDG_CONFIG_HOME=str(case/'config'),
                    TMPDIR=str(case/'tmp')+os.sep, ERL_CRASH_DUMP=str(case/'erl-crash.dump'))
                require(environment['ELIXIR_ERL_OPTIONS'] == '+S 8:8 +A 1 +SDcpu 1:1 +SDio 1', 'Scheduler policy changed')
                require(all(not environment.get(k) for k in ('ERL_FLAGS', 'ERL_AFLAGS', 'ERL_ZFLAGS', 'ERL_LIBS', 'ERL_COMPILER_OPTIONS')),
                        'Injected runtime flags')
                beam = next(item for item in row['beams'] if item['path'].endswith('/Elixir.Clbg.Support.beam'))
                ebin = Path(beam['path']).parent
                for path, digest in pins.items():
                    require(sha(path) == digest, ('Pinned input changed before probe', path))
                command = [str(ELIXIR/'bin/elixir'), '-pa', str(ebin), str(probe), str(ebin), str(vectors), str(case/'summary.txt')]
                observe(command, environment, case, payload, lock)
                expected = ('format_vectors=1536\ninput_bytes='+str(len(payload))+
                            '\nnonempty_input=true\nrepeated_eof=true\nmain_loaded=false\n')
                require((case/'summary.txt').read_text() == expected, 'Incomplete helper observation')
                report['profile_ids'].append(row['id'])
                save(output/'report.json', report)
                print('Validated Elixir helper:', row['id'], flush=True)
            report.update(status='compiled-helper-semantics-passed', helper_formatting_and_stdio_qualified=True)
        except BaseException as error:
            report.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
            raise
        finally:
            changed, integrity_errors = [], []
            for path, digest in pins.items():
                try:
                    require(sha(path) == digest, 'Pinned bytes changed')
                except BaseException as error:
                    changed.append(path)
                    integrity_errors.append(dict(path=path, error=str(error) or type(error).__name__))
            report.update(changed_pins=changed, integrity_errors=integrity_errors,
                          finished_at=datetime.now(timezone.utc).isoformat())
            if integrity_errors:
                report['status'] = 'failed-input-integrity'
                report['helper_formatting_and_stdio_qualified'] = False
            save(output/'report.json', report)
            artifacts, artifact_errors = {}, []
            for path in output.rglob('*'):
                if path.is_file():
                    try:
                        artifacts[str(path.relative_to(output))] = dict(sha256=sha(path), bytes=path.stat().st_size)
                    except BaseException as error:
                        artifact_errors.append(dict(path=str(path), error=str(error) or type(error).__name__))
            if artifact_errors:
                report.update(status='failed-artifact-integrity', helper_formatting_and_stdio_qualified=False,
                              artifact_errors=artifact_errors)
                save(output/'report.json', report)
                artifacts['report.json'] = dict(sha256=sha(output/'report.json'), bytes=(output/'report.json').stat().st_size)
            save(output/'terminal.json', dict(status='failed-artifact-integrity' if artifact_errors else report['status'],
                report_sha256=sha(output/'report.json'), pins=pins, available_evidence=artifacts,
                integrity_errors=integrity_errors, artifact_errors=artifact_errors,
                common_mutex_held=True, benchmark_samples=0, subject_main_executions=0,
                source_work_qualified=False, chart_admission=False))
            require(not integrity_errors and not artifact_errors, 'Pinned inputs or output artifacts changed')


if __name__ == '__main__':
    main()
