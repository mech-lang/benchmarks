"""Independently close the single actual Builder spec attempt and mirror its bytes."""
from contextlib import ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil

P = Path(__file__).resolve().parent
H = P.parents[1]
C = H.parents[1]/'continuation'
OLD = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
OH = OLD/'benchmarks/clbg/rebol-comparison/20261013'
OWNER = OLD/'benchmarks/clbg/continuation/owned-jobs/rebol-builder-spec-only-v1'
OUTPUT = OH/'sdk-qualification/builder-spec-only-v1'
REVIEW = H/'sdk-qualification/builder-spec-route-review-v1/review.json'
REVIEW_SHA = 'b2a97d7b8ea6dd517b52392c0090430389466bafd72bc78f9496e55d1984d1af'
PACKET = C/'jobs/rebol-builder-intake-release-v1/frozen-inputs.json'
PACKET_SHA = '6f9c2fd02f4140cb10de570feb7ddc1d26447e47cbb322db32d273bc8975c1ba'
ROOT = C/'jobs/rebol-builder-intake-closed-review-v1/receipt.json'
ROOT_SHA = '1f11a2fb754a9329fe524a77e5436c94f39ee9aed186231f634f113e7fc16caa'
OUT = C/'jobs/rebol-builder-spec-only-closed-review-v1'
PINS = {}


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def bind(path, expected):
    path = Path(path)
    assert sha(path) == expected and (str(path) not in PINS or PINS[str(path)] == expected)
    PINS[str(path)] = expected
    return path


def read(path, expected=None):
    return json.loads(bind(path, expected or sha(path)).read_bytes())


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    print('WAIT common mutex: closed actual Rebol spec bytes and pin review only', flush=True)
    with Path('/tmp/mech-clbg-timing.lock').open('r+') as common, ExitStack() as leases:
        fcntl.flock(common, fcntl.LOCK_EX)
        held, named = os.fstat(common.fileno()), Path('/tmp/mech-clbg-timing.lock').stat()
        assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) and held.st_ino == 79859134
        lease = leases.enter_context((OWNER/'owner.lock').open('rb'))
        fcntl.flock(lease, fcntl.LOCK_SH | fcntl.LOCK_NB)
        held, named = os.fstat(lease.fileno()), (OWNER/'owner.lock').stat()
        assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
        root = read(ROOT, ROOT_SHA); review = read(REVIEW, REVIEW_SHA)
        assert root['status'] == 'closed-qualified-Rebol-official-Builder-intake-and-898-source-copy'
        assert review['root_review'] == dict(path=str(ROOT), sha256=ROOT_SHA, verified_pins=2133)
        packet = read(PACKET, PACKET_SHA)
        for path, expected in packet['pins'].items(): bind(path, expected)
        argv = ['/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12',
            '-I', '-S', '-B', '-u', str(OH/'revisions/sdk-builder-spec-v1/controller.py'), '--spec-only',
            '--packet', str(PACKET), '--packet-sha256', PACKET_SHA, '--intake-review', str(REVIEW), '--intake-review-sha256', REVIEW_SHA]
        done = read(OWNER/'terminal.json')
        request, start, worker = [read(OWNER/name) for name in ('request.json', 'command-started.json', 'worker-started.json')]
        assert all(item['command'] == argv and item['cwd'] == str(OLD) for item in (request, start, worker))
        assert request['common_mutex_owned_by_target_command'] is worker['common_mutex_owned_by_target_command'] is True
        assert done['actual_command_started'] is True and done['stop_signals'] == [] and done['command_identity_observation_missing'] is False
        assert not any(done.get(key) for key in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure'))
        assert done['command_identity'] == start['command_identity'] and done['command_pid'] == start['command_pid']
        assert done['worker_identity'] == worker['worker_identity'] and done['worker_identity']['pid'] == 35498
        listing = done['command_identity']['listing'].split(None, 7)
        assert listing[:2] == [str(done['command_pid']), '35498'] and listing[7].split() == argv
        assert request['qualification_granted'] is request['automatic_retry'] is done['qualification_granted'] is done['automatic_retry'] is False
        report = read(OUTPUT/'report.json'); body = read(OUTPUT/'terminal-pin.json')
        assert report['terminal_evidence_complete'] is True and not report.get('terminal_artifact_errors')
        assert body['report'] == str(OUTPUT/'report.json') and body['report_sha256'] == PINS[str(OUTPUT/'report.json')]
        assert body['partial_evidence_pins'] == report['pins'] and body['status'] == report['status'] and body['inherited_common_mutex'] is True
        for path, expected in report['pins'].items(): bind(path, expected)
        copies = {}
        assert not OUT.exists(); OUT.mkdir(parents=True, exist_ok=False)
        def mirror(source, target):
            assert source.is_file() and not source.is_symlink()
            expected = PINS.get(str(source), sha(source)); bind(source, expected)
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open('rb') as origin, target.open('xb') as destination: shutil.copyfileobj(origin, destination)
            target.chmod(0o444)
            bind(target, expected); copies[str(source)] = dict(path=str(target), sha256=expected)
        for path in sorted(OUTPUT.rglob('*')):
            if path.is_file(): mirror(path, OUT/'evidence'/path.relative_to(OUTPUT))
        for path in sorted(OWNER.iterdir()):
            if path.is_file() and path.name != 'owner.lock': mirror(path, OUT/'durable'/path.name)
        success = done['status'] == 'command-exited-zero-awaiting-report-review' and type(done['exit_code']) is int and done['exit_code'] == 0
        success = success and report['status'] == 'actual-resolved-spec-captured-awaiting-full-root-spec-review'
        receipt = dict(status='failed-Rebol-spec-only-attempt-preserved', durable_owner=str(OWNER),
            worker_pid=35498, command_pid=done['command_pid'], durable_exit_code=done['exit_code'],
            durable_terminal_sha256=PINS[str(OWNER/'terminal.json')], request_sha256=PINS[str(OWNER/'request.json')],
            report_sha256=PINS[str(OUTPUT/'report.json')], body_terminal_sha256=PINS[str(OUTPUT/'terminal-pin.json')],
            source_policy_review_sha256=REVIEW_SHA, prior_intake_root_sha256=ROOT_SHA, original_host_paths_preserved=True,
            common_mutex_held=True, common_mutex_inode=79859134, copies=copies, header_generation_executed=False,
            extension_build_executed=False, runtime_configuration_admitted=False, source_work_qualified=False,
            resolved_spec_semantics_qualified=False, chart_admission=False, automatic_retry=False)
        if success:
            assert not any(report.get(key) for key in ('error', 'error_type', 'private_root_pin_errors'))
            actual = read(OUTPUT/'spec-result.json')
            native = read(OUTPUT/'spec-only.json'); startup = read(OUTPUT/'spec-only-startup.json')
            plan = read(OUTPUT/'spec-only-launch-plan.json')
            assert actual['status'] == 'actual-resolved-spec-captured-awaiting-full-root-spec-review'
            assert type(native['exit_status']) is type(native['final_exit_status']) is int and native['exit_status'] == native['final_exit_status'] == 0
            assert not any(native.get(key) for key in ('error', 'error_type', 'cleanup_error', 'cleanup_errors'))
            assert native['inherited_common_mutex'] is True and native['timeout_seconds'] == 120
            assert native['command'] == [argv[0], '-I', '-S', '-B', '-u', str(OH/'revisions/sdk-builder-spec-v1/launch.py'),
                '--plan', str(OUTPUT/'spec-only-launch-plan.json'), '--plan-sha256', PINS[str(OUTPUT/'spec-only-launch-plan.json')]]
            assert native['pid'] == native['identity']['pid']
            assert startup['pid'] == native['pid'] and startup['command'] == plan['command'] and startup['actual_cwd'] == plan['cwd']
            assert plan['phase'] == 'spec-only' and startup['inherited_common_mutex'] is True and startup['common_mutex_inode'] == 79859134
            assert plan['command'] == [root['builder'], str(OH/'.build/sdk-builder-spec-v1/source-copy/make/rebol3.nest'), '--test', '%rebol3-bulk-macos-arm64']
            assert (OUTPUT/'spec-only.stderr').read_bytes() == b''
            assert actual['immutable_source_files_preserved'] == 898 and actual['owned_spec_commands'] == 1
            assert actual['header_generation_executed'] is actual['extension_build_executed'] is actual['resolved_spec_semantics_qualified'] is actual['chart_admission'] is False
            assert actual['original_runtime_commands_reexecuted'] == actual['old_fixture_reexecutions'] == actual['builder_intake_reexecutions'] == 0
            intake = read(root['intake_path'], root['intake_sha256'])
            assert len(intake['source_copy_files']) == 898
            for item in intake['source_copy_files']:
                bind(item['original'], item['sha256']); bind(item['copy'], item['sha256'])
            for item in actual['new_files']:
                path = bind(item['path'], item['sha256'])
                assert path.name in ('spec.reb', 'objects.txt') and path.parent == Path(actual['resolved_spec']).parent
                mirror(path, OUT/'raw-spec'/path.name)
            spec = bind(actual['resolved_spec'], actual['resolved_spec_sha256'])
            assert spec.stat().st_size > 0 and str(spec) in copies
            receipt.update(status='closed-actual-Rebol-spec-only-native0-and-898-preserved',
                spec_result_sha256=PINS[str(OUTPUT/'spec-result.json')], native_command_receipt_sha256=PINS[str(OUTPUT/'spec-only.json')],
                owned_native_pid=native['pid'], owned_native_exit=0, owned_spec_commands=1, original898_files_preserved=True,
                actual_resolved_spec=str(spec), actual_resolved_spec_sha256=actual['resolved_spec_sha256'],
                raw_spec_copy=copies[str(spec)], native_child_count_independently_observed=False,
                original_runtime_commands_reexecuted=0, old_fixture_reexecutions=0, builder_intake_reexecutions=0)
        for path, expected in PINS.items(): bind(path, expected)
        receipt.update(verified_pins=len(PINS), input_pins=PINS, finished_at=datetime.now(timezone.utc).isoformat())
        save(OUT/'receipt.json', receipt)
        print(json.dumps(dict(status=receipt['status'], receipt_path=str(OUT/'receipt.json'), receipt_sha256=sha(OUT/'receipt.json'),
            durable_exit=done['exit_code'], verified_pins=len(PINS), raw_spec_copy=receipt.get('raw_spec_copy'))), flush=True)


if __name__ == '__main__': main()
