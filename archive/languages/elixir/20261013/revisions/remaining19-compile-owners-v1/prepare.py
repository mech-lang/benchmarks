"""Compile nineteen retained Elixir forms; reuse the first compile and probe."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sys
import traceback
import types

P = Path(__file__).resolve().parent
HERE = P.parents[1]
CLBG = HERE.parents[1]
OLD_CLBG = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
OLD = OLD_CLBG/'elixir-comparison/20261013'
RESUME = OLD/'revisions/saved-first-compile-probe-v1'
RESUME_SHA = 'fc350e965282314456d858bb358faac720a6b7739ac30816385ad800b8076c50'
RESUME_NOTE_SHA = '8f68d56b28021db2f2681d2dd3868d824a8cd5daf5198c5eb443c4f3a87e318f'
FIRST = OLD/'jobs/saved-first-compile-owner-writer-v1'
FIRST_OWNER = CLBG/'continuation/owned-jobs/elixir-saved-first-compile-owner-writer-v1'
FIRST_ROOT = CLBG/'continuation/jobs/elixir-saved-first-probe-closed-review-v1/receipt.json'
FIRST_ROOT_SHA = '497204e26b73b1c9125dcb99ba5d28d19d9824d24afa864c917a25be4890db50'
FIRST_RESULT_SHA = 'a5eec9dbf0c93c68ada489fa00aab486306ce5585e1fe0a2af8678c532398206'
FIRST_OUTCOME_SHA = '963e87a402b82b817445c3e581416a4b654101c980eb6823737ecb38332dd165'
FIRST_TERMINAL_SHA = 'ec770c4248d3cdb3f9434818b67de33f8c7cbf728952c30113d368c2ffb8358c'
FIRST_REQUEST_SHA = '4c4965ffbb4a4d24f11c2718e74c355327dda9a57773df1f3d7b0227115e5ee2'
FIRST_NATIVE_SHA = '2a44f16bc31bbbd3bf99b8416f26e9968d3505a7ec13edc507aacfaf628baa62'
SUPPORT_SHA = 'c9fbb60888c46fb50195245761a411716f1256145af367e03a23f70aea270e89'
RUNNER_SHA = 'bdad2389d437fd4c69122e5d25b3065412b4bca0c272631667283273392ba8ff'
LOCK = Path('/tmp/mech-clbg-timing.lock')
PYTHON = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
FIRST_ID = 'elixir-nbody-compact'
STATUS = 'saved-Elixir-first-compile-owner-and-writer-observation-completed'


def load_resume(pins):
    raw = (RESUME/'resume.py').read_bytes()
    assert not (RESUME/'resume.py').stat().st_mode & 0o222
    assert hashlib.sha256(raw).hexdigest() == RESUME_SHA
    name = 'elixir_remaining19_saved_compile_helpers'
    assert name not in sys.modules
    resume = types.ModuleType(name); resume.__file__ = str(RESUME/'resume.py')
    sys.modules[name] = resume
    exec(compile(raw, resume.__file__, 'exec'), resume.__dict__)
    base = resume.load_base(pins)
    base.bind(RESUME/'resume.py', RESUME_SHA, pins)
    base.bind(RESUME/'REVIEW.md', RESUME_NOTE_SHA, pins)
    assert not (RESUME/'REVIEW.md').stat().st_mode & 0o222
    return base, resume


def first_closure(base, resume, pins):
    previous, compiler, saved, contract, beams, main, support = resume.saved_compile(base, pins)
    expected = [PYTHON, '-I', '-S', '-B', '-u', str(RESUME/'resume.py'), '--revision',
        'saved-first-compile-owner-writer-v1', '--worker-sha256', RESUME_SHA,
        '--review-sha256', RESUME_NOTE_SHA]
    request = base.read(FIRST_OWNER/'request.json', FIRST_REQUEST_SHA, pins)
    ended = base.read(FIRST_OWNER/'terminal.json', FIRST_TERMINAL_SHA, pins)
    started, worker, launch = [base.read(FIRST_OWNER/name, base.sha(FIRST_OWNER/name), pins)
        for name in ('command-started.json', 'worker-started.json', 'launch.json')]
    assert all(record['command'] == expected and record['cwd'] == str(OLD_CLBG.parent.parent)
        for record in (request, started, worker, launch))
    assert ended['status'] == 'command-exited-zero-awaiting-report-review'
    assert type(ended['exit_code']) is int and ended['exit_code'] == 0
    assert ended['actual_command_started'] is True and ended['stop_signals'] == []
    assert ended['qualification_granted'] is ended['automatic_retry'] is request['qualification_granted'] is request['automatic_retry'] is False
    assert request['common_mutex_owned_by_target_command'] is worker['common_mutex_owned_by_target_command'] is True
    assert worker['inherited_private_lease'] is worker['detached_session'] is True
    assert worker['worker_identity'] == ended['worker_identity'] and ended['worker_identity']['pid'] == 13072
    assert launch['worker_identity']['pid'] == 13072
    assert started['command_identity_observation_missing'] is ended['command_identity_observation_missing'] is False
    assert started['command_identity'] == ended['command_identity'] and started['command_pid'] == ended['command_pid'] == 13076
    actual = ended['command_identity']['listing'].split(None, 7)
    assert actual[:2] == [str(ended['command_pid']), '13072'] and actual[7].split() == expected
    assert not any(ended.get(key) for key in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure'))
    outcome = base.read(FIRST/'outcome.json', FIRST_OUTCOME_SHA, pins)
    result = base.read(FIRST/'preparation-result.json', FIRST_RESULT_SHA, pins)
    assert outcome['status'] == result['status'] == STATUS
    assert outcome['exclusive_common_mutex_held'] is True and outcome['common_mutex_inode'] == 79859134
    assert not any(outcome.get(key) for key in ('error', 'error_type', 'integrity_errors', 'available_bytes_not_fully_pinned'))
    for mapping in (outcome['prerequisite_pins'], outcome['available_evidence_pins'], result['pins']):
        for path, digest in mapping.items(): base.bind(path, digest, pins)
    assert result['selected_profile'] == FIRST_ID and result['beams'] == beams
    assert result['retained_successful_compilation'] == dict(path=str(resume.OLD_OUT/'compile/first-nbody-compact-compile.json'), sha256=resume.COMPILE_SHA)
    assert result['whole20_inventory'] == saved['retained_source_inventory']
    assert result['compiled_source_debug_bindings'] == 2 and result['writer_output_bytes'] == 131328
    assert result['writer_exact_all256_bytes_multiple_chunks'] is result['input_EOF_observed'] is True
    assert result['subject_compiler_commands'] == result['successful_compiler_reexecutions'] == 0
    assert result['owner_stdio_commands'] == 1 and result['subject_main_executions'] == result['fixture_reexecutions'] == result['actual_benchmark_runs'] == 0
    assert all(result[key] is False for key in ('nonempty_input_qualified', 'full_stdio_qualified',
        'remaining19_profiles_compiled', 'source_work_qualified', 'chart_admission'))
    assert result['canonical_loc'] is result['formatted_loc'] is None
    assert result['original_sources_beams_and_old_ebins_preserved'] is True
    probe_path = FIRST/'probe/compiled-source-owner-and-raw-writer.json'
    assert str(probe_path) in outcome['available_evidence_pins']
    assert outcome['available_evidence_pins'][str(probe_path)] == FIRST_NATIVE_SHA
    probe = base.read(probe_path, FIRST_NATIVE_SHA, pins)
    argv = [str(compiler/'bin/elixir'), '-pa', str(resume.OLD_BUILD/'ebin'), str(resume.PRIOR/'probe.exs'),
        str(FIRST/'owners'), str(resume.OLD_BUILD/'ebin'), str(main), str(support)]
    assert probe['command'] == argv and probe['pid'] == 13085
    assert type(probe['exit_status']) is type(probe['final_exit_status']) is int
    assert probe['exit_status'] == probe['final_exit_status'] == 0
    assert probe['inherited_common_mutex'] is probe['preparation_only'] is probe['never_chart_eligible'] is True
    assert not any(probe.get(key) for key in ('error', 'error_type', 'cleanup_errors'))
    for suffix, data in (('stdout', bytes(range(256))*513), ('stderr', b'')):
        path = probe_path.with_suffix('.'+suffix)
        assert str(path) in outcome['available_evidence_pins']
        assert base.bind(path, outcome['available_evidence_pins'][str(path)], pins).read_bytes() == data
    assert (FIRST/'owners/summary.txt').read_text() == previous.EXPECTED_SUMMARY
    review = base.read(FIRST_ROOT, FIRST_ROOT_SHA, pins)
    assert review['status'] == 'closed-qualified-saved-Elixir-first-compile-owner-and-writer'
    assert (review['worker_pid'], review['command_pid'], review['native_command_pid']) == (13072, 13076, 13085)
    assert type(review['verified_pins']) is int and review['verified_pins'] == 7793
    for stem, path, digest in (('preparation_result', FIRST/'preparation-result.json', FIRST_RESULT_SHA),
        ('outcome', FIRST/'outcome.json', FIRST_OUTCOME_SHA), ('durable_terminal', FIRST_OWNER/'terminal.json', FIRST_TERMINAL_SHA),
        ('request', FIRST_OWNER/'request.json', FIRST_REQUEST_SHA), ('native_command', probe_path, FIRST_NATIVE_SHA)):
        assert review[stem+'_path'] == str(path) and review[stem+'_sha256'] == digest
    assert review['chart_admission'] is False and review['common_mutex_held'] is True
    assert review['common_mutex_inode'] == 79859134 and review['original_host_paths_preserved'] is True
    assert len(review['new_repository_copies']) == 10
    for path, digest in review['new_repository_copies'].items():
        copy = Path(path); assert copy.is_relative_to(HERE/'jobs/saved-first-compile-owner-writer-v1')
        original = FIRST/copy.relative_to(HERE/'jobs/saved-first-compile-owner-writer-v1')
        expected = FIRST_OUTCOME_SHA if original.name == 'outcome.json' else outcome['available_evidence_pins'][str(original)]
        assert digest == expected; base.bind(copy, digest, pins)
    return previous, compiler, saved, result, beams, support


def inventory(base, saved, resume, pins):
    ref = saved['retained_source_inventory']
    value = base.read(ref['path'], ref['sha256'], pins)
    assert value['status'] == 'exact20-inputs-materialized-not-compiled'
    assert value['runner_counted'] is True and value['distinct_optimizer_claim'] is False
    rows = value['forms']
    assert len(rows) == len({row['id'] for row in rows}) == 20
    assert {(row['benchmark'], row['variant']) for row in rows} == {(b, v) for b in base.BENCHES for v in ('compact', 'optimized')}
    for row in rows:
        folder = OLD/'.build/retained-otp-toolchain-v1/forms'/row['id']
        assert row['id'] == 'elixir-'+row['benchmark']+'-'+row['variant']
        assert row['source_input_materialized'] is True and row['subject_compiler_executed'] is row['work_qualified'] is row['chart_admission'] is False
        assert row['canonical_loc'] is row['formatted_loc'] is None
        files = row['physical_inputs']
        assert len(files) == 3 and [item['role'] for item in files] == ['application', 'application-helper', 'application-launcher']
        for item, name in zip(files, ('main.ex', 'support.ex', 'runner.exs')):
            path = folder/name
            assert item['path'] == str(path) and item['counted'] is True
            assert not path.is_symlink() and not path.stat().st_mode & 0o222
            base.bind(path, item['sha256'], pins); base.bind(item['origin'], item['sha256'], pins)
        assert files[1]['sha256'] == SUPPORT_SHA and files[2]['sha256'] == RUNNER_SHA
        assert row['alias_of'] == 'elixir-'+row['benchmark']+'-baseline-v1'
        assert row['compile_command_proposed'] == [str(Path(saved['compiler'])), '-o', str(folder/'ebin'), str(folder/'support.ex'), str(folder/'main.ex')]
        assert row['runtime_command_proposed'] == [str(Path(saved['compiler']).with_name('elixir')), '-pa', str(folder/'ebin'), str(folder/'runner.exs'), '{n}']
        assert (folder/'ebin').is_dir() and not any((folder/'ebin').iterdir())
    return rows


def beam_records(base, ebin, pins):
    assert {p.name for p in ebin.iterdir()} == {'Elixir.Clbg.Main.beam', 'Elixir.Clbg.Support.beam'}
    result = []
    for path in sorted(ebin.iterdir()):
        assert path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= 16*1024*1024
        with path.open('rb') as stream: header = stream.read(12)
        assert header[:4] == b'FOR1' and header[8:12] == b'BEAM' and int.from_bytes(header[4:8], 'big')+8 == path.stat().st_size
        digest = base.sha(path); base.bind(path, digest, pins)
        result.append(dict(path=str(path), sha256=digest, bytes=path.stat().st_size))
    return result


def run(args, output, build, pins, common_fd, base, resume, progress):
    for name, digest in (('prepare.py', args.worker_sha256), ('REVIEW.md', args.review_sha256)):
        assert not (P/name).stat().st_mode & 0o222; base.bind(P/name, digest, pins)
    previous, compiler, saved, first, first_beams, first_support = first_closure(base, resume, pins)
    rows = inventory(base, saved, resume, pins)
    base.verify(pins); progress['prerequisites_verified'] = True
    remaining = [row for row in rows if row['id'] != FIRST_ID]
    assert len(remaining) == 19
    warning = base.bind(resume.OLD_OUT/'compile/first-nbody-compact-compile.stderr', resume.STDERR_SHA, pins).read_bytes()
    assert warning.count(str(first_support).encode()) == 1
    service = base.cold(base.SERVICE, base.SERVICE_SHA, 'elixir_remaining19_original_owned_service', pins)
    guard = service.load_guard(); harness = guard.load_harness()
    assert not list(service.HERE.glob('*.beam')) and not (service.HERE/'start.boot').exists() and not (service.HERE/'.erlang').exists()
    base.save(output/'contract.json', dict(status='remaining19-independent-compiles-and-original-owner-writer-probes',
        first_result=dict(path=str(FIRST/'preparation-result.json'), sha256=FIRST_RESULT_SHA),
        whole20_inventory=saved['retained_source_inventory'], remaining_ids=[row['id'] for row in remaining],
        compilation_commands=19, owner_writer_commands=19, counted_roles=['application', 'application-helper', 'application-launcher'],
        first_compile_or_probe_reexecutions=0, original_ownership_fixtures_reused=11, fixture_reexecutions=0,
        native_stdin='existing-service-DEVNULL', subject_main_executions=0, chart_admission=False))
    completed = [dict(id=FIRST_ID, reused=True, beams=first_beams, physical_inputs=next(row['physical_inputs'] for row in rows if row['id'] == FIRST_ID),
        evidence=dict(path=str(FIRST/'preparation-result.json'), sha256=FIRST_RESULT_SHA))]
    for row in remaining:
        case = output/row['id']; case.mkdir()
        folder = build/row['id']; folder.mkdir()
        ebin, home, config, temporary = [folder/name for name in ('ebin', 'home', 'config', 'tmp')]
        owners = case/'owners'
        for path in (ebin, home, config, temporary, owners): path.mkdir()
        environment = dict(first['runtime_environment'])
        assert 'ERL_COMPILER_OPTIONS' not in environment
        environment.update(HOME=str(home), XDG_CONFIG_HOME=str(config), TMPDIR=str(temporary)+os.sep, ERL_CRASH_DUMP=str(case/'erl-crash.dump'))
        assert environment['PATH'] == saved['runtime_environment']['PATH'] and environment['ELIXIR_ERL_OPTIONS'] == ' '.join(base.FLAGS)
        assert shutil.which('erl', path=environment['PATH']) == str(base.OTP/'bin/erl')
        main, support, runner = [Path(item['path']) for item in row['physical_inputs']]
        assert all('@on_load' not in path.read_text() for path in (main, support))
        base.verify(pins)
        compilation = service.owned_command(guard, harness, [str(compiler/'bin/elixirc'), '-o', str(ebin), str(support), str(main)],
            environment, case/'compile', common_fd, 180, 'compile')
        progress['subject_compiler_commands'] += 1
        assert compilation['stdout'] == b''
        assert compilation['stderr'] == warning.replace(str(first_support).encode(), str(support).encode())
        beams = beam_records(base, ebin, pins)
        base.verify(pins)
        probe = service.owned_command(guard, harness, [str(compiler/'bin/elixir'), '-pa', str(ebin), str(resume.PRIOR/'probe.exs'),
            str(owners), str(ebin), str(main), str(support)], environment, case/'probe', common_fd, 90, 'owner-writer')
        progress['owner_stdio_commands'] += 1
        assert probe['stderr'] == b'' and probe['stdout'] == bytes(range(256))*513
        assert {path.name for path in owners.iterdir()} == {'Elixir.Clbg.Main.ownership.etf', 'Elixir.Clbg.Support.ownership.etf', 'summary.txt'}
        assert (owners/'summary.txt').read_text() == previous.EXPECTED_SUMMARY
        terms = []
        for path in sorted(owners.glob('*.etf')):
            assert path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= 16*1024*1024
            with path.open('rb') as stream: assert stream.read(1) == b'\x83'
            digest = base.sha(path); base.bind(path, digest, pins)
            terms.append(dict(path=str(path), sha256=digest, bytes=path.stat().st_size))
        base.bind(owners/'summary.txt', base.sha(owners/'summary.txt'), pins)
        record = dict(id=row['id'], benchmark=row['benchmark'], variant=row['variant'], alias_of=row['alias_of'],
            reused=False, physical_inputs=row['physical_inputs'], compiler_command=compilation['detail'], beams=beams,
            owner_writer_command=probe['detail'], original_owner_terms=terms, source_debug_bindings=2,
            runtime_command=[str(compiler/'bin/elixir'), '-pa', str(ebin), str(runner), '{n}'],
            runtime_environment=environment, nonempty_input_qualified=False, source_work_qualified=False,
            canonical_loc=None, formatted_loc=None, chart_admission=False)
        base.save(case/'result.json', record); completed.append(record)
        progress['completed_profile_ids'].append(row['id'])
        print('COMPLETED compile+owners:', row['id'], flush=True)
    assert len(completed) == len({row['id'] for row in completed}) == 20
    assert progress['subject_compiler_commands'] == progress['owner_stdio_commands'] == 19
    for row in rows:
        assert not any((OLD/'.build/retained-otp-toolchain-v1/forms'/row['id']/'ebin').iterdir())
    base.verify(pins)
    base.save(output/'preparation-result.json', dict(status='remaining19-Elixir-compile-source-owner-writer-completed', profiles=completed,
        first_result=dict(path=str(FIRST/'preparation-result.json'), sha256=FIRST_RESULT_SHA),
        whole20_inventory=saved['retained_source_inventory'], total_compiled_profiles=20,
        subject_compiler_commands=19, owner_stdio_commands=19, first_compile_or_probe_reexecutions=0,
        subject_main_executions=0, fixture_reexecutions=0, actual_benchmark_runs=0,
        original_ownership_fixtures_reused=11, nonempty_input_qualified=False, full_stdio_qualified=False,
        helper_semantics_qualified=False, source_work_qualified=False, subject_execution_mode_qualified=False,
        canonical_loc=None, formatted_loc=None, chart_admission=False, pins=dict(pins)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('revision', 'worker-sha256', 'review-sha256'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    assert args.revision == 'remaining19-compile-owners-v1'
    assert sys.dont_write_bytecode and Path(sys.executable).resolve() == Path(PYTHON).resolve()
    assert all(re.fullmatch('[a-f0-9]{64}', value) for key, value in vars(args).items() if key.endswith('_sha256'))
    def interrupted(signum, frame): raise KeyboardInterrupt('Elixir remaining19 interrupted: '+str(signum))
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM): signal.signal(sig, interrupted)
    with ExitStack() as leases:
        for path in (FIRST_OWNER/'owner.lock', OLD_CLBG/'continuation/owned-jobs/elixir-first-compiler-stdio-owner-v1/owner.lock',
            OLD_CLBG/'continuation/owned-jobs/elixir-saved-toolchain-probes-v1/owner.lock',
            OLD_CLBG/'continuation/owned-jobs/elixir-retained-otp-toolchain-v1/owner.lock',
            OLD_CLBG/'continuation/owned-jobs/gleam-publication-metadata-v1/owner.lock'):
            held = leases.enter_context(path.open('rb')); fcntl.flock(held, fcntl.LOCK_SH|fcntl.LOCK_NB)
            actual, named = os.fstat(held.fileno()), path.stat(); assert (actual.st_dev, actual.st_ino) == (named.st_dev, named.st_ino)
        owner = leases.enter_context((P/'owner.lock').open('a+')); fcntl.flock(owner, fcntl.LOCK_EX|fcntl.LOCK_NB)
        print('WAIT common mutex: nineteen Elixir compiles + original owner/writer probes', flush=True)
        with LOCK.open('r+') as common:
            fcntl.flock(common, fcntl.LOCK_EX)
            actual, named = os.fstat(common.fileno()), LOCK.stat()
            assert (actual.st_dev, actual.st_ino) == (named.st_dev, named.st_ino) and actual.st_ino == 79859134
            output, build = P/'jobs'/args.revision, HERE/'.build'/args.revision
            assert not output.exists() and not build.exists()
            assert not any(path.is_symlink() for path in (P, HERE, output.parent, build.parent))
            output.mkdir(parents=True); build.mkdir(parents=True)
            pins, failures, base = {}, [], None
            progress = dict(status='failed-Elixir-remaining19-compile-owners', subject_compiler_commands=0,
                owner_stdio_commands=0, completed_profile_ids=[], first_compile_or_probe_reexecutions=0,
                subject_main_executions=0, fixture_reexecutions=0, actual_benchmark_runs=0,
                prerequisites_verified=False, chart_admission=False)
            signal.alarm(6000)
            try:
                for path, expected in ((P/'prepare.py', args.worker_sha256), (P/'REVIEW.md', args.review_sha256),
                    (Path(sys.executable).resolve(), PYTHON_SHA)):
                    if path.suffix in ('.py', '.md'): assert not path.stat().st_mode & 0o222
                    with path.open('rb') as stream: assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected
                    pins[str(path)] = expected
                base, resume = load_resume(pins); base.bind(Path(sys.executable).resolve(), PYTHON_SHA, pins)
                run(args, output, build, pins, common.fileno(), base, resume, progress)
                progress['status'] = 'remaining19-Elixir-compile-source-owner-writer-completed'
            except BaseException as error:
                progress.update(error=str(error) or type(error).__name__, error_type=type(error).__name__)
                with (output/'error.log').open('x') as stream: stream.write(traceback.format_exc())
                raise
            finally:
                signal.alarm(0); available = {}
                def digest(path):
                    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
                for path, expected in pins.items():
                    try: assert digest(Path(path)) == expected
                    except BaseException as error: failures.append(dict(path=path, error=str(error) or type(error).__name__))
                evidence = [path for path in output.rglob('*') if path.is_file()]
                evidence += [path for path in build.rglob('*.beam') if path.parent.name == 'ebin' and path.is_file()]
                # Preserve actual started counts even if the owned service raised.
                for key, relative in (('subject_compiler_commands', 'compile/compile.json'), ('owner_stdio_commands', 'probe/owner-writer.json')):
                    observed = 0
                    for case in output.iterdir():
                        path = case/relative
                        if path.is_file():
                            try:
                                record = json.loads(path.read_text())
                                if type(record.get('pid')) is int and record['pid'] > 0: observed += 1
                            except BaseException as error:
                                failures.append(dict(path=str(path), error=str(error) or type(error).__name__))
                    progress[key] = observed
                for path in evidence:
                    try: available[str(path)] = digest(path)
                    except BaseException as error: failures.append(dict(path=str(path), error=str(error) or type(error).__name__))
                if failures: progress.update(status='failed-terminal-integrity', integrity_errors=failures)
                progress.update(finished_at=datetime.now(timezone.utc).isoformat(), prerequisite_pins=pins, available_evidence_pins=available,
                    exclusive_common_mutex_held=True, common_mutex_inode=79859134,
                    original_sources_and_first_beams_preserved=progress['prerequisites_verified'] and not failures,
                    private_startup_directories_not_evidence_artifacts=True)
                with (output/'outcome.json').open('x') as stream: json.dump(progress, stream, indent=2); stream.write('\n')
                if failures: raise RuntimeError('Elixir remaining19 terminal integrity failed; partial records retained')


if __name__ == '__main__': main()
