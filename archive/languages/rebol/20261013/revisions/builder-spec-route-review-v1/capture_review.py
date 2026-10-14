"""Capture only the exact actual intake and reviewed spec-route metadata."""
from contextlib import ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
H = P.parents[1]
C = H.parents[1]/'continuation'
OLD = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
OH = OLD/'benchmarks/clbg/rebol-comparison/20261013'
OC = OLD/'benchmarks/clbg/continuation'
OWNER = OC/'owned-jobs/rebol-builder-intake-v1'
OUT = H/'sdk-qualification/builder-spec-route-review-v1'
ROOT = C/'jobs/rebol-builder-intake-closed-review-v1/receipt.json'
ROOT_SHA = '1f11a2fb754a9329fe524a77e5436c94f39ee9aed186231f634f113e7fc16caa'
PYTHON = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
PACKET = C/'jobs/rebol-builder-intake-release-v1/frozen-inputs.json'
PACKET_SHA = '6f9c2fd02f4140cb10de570feb7ddc1d26447e47cbb322db32d273bc8975c1ba'
PINS = {}


def bind(path, expected):
    path = Path(path)
    with path.open('rb') as stream: actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert actual == expected and (str(path) not in PINS or PINS[str(path)] == expected)
    PINS[str(path)] = expected
    return path


def read(path, expected):
    return json.loads(bind(path, expected).read_bytes())


def digest(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    print('WAIT common mutex: actual Rebol spec-route review metadata only', flush=True)
    with Path('/tmp/mech-clbg-timing.lock').open('r+') as common, ExitStack() as leases:
        fcntl.flock(common, fcntl.LOCK_EX)
        held, named = os.fstat(common.fileno()), Path('/tmp/mech-clbg-timing.lock').stat()
        assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) and held.st_ino == 79859134
        lease = leases.enter_context((OWNER/'owner.lock').open('rb'))
        fcntl.flock(lease, fcntl.LOCK_SH | fcntl.LOCK_NB)
        held, named = os.fstat(lease.fileno()), (OWNER/'owner.lock').stat()
        assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
        root = read(ROOT, ROOT_SHA)
        assert root['status'] == 'closed-qualified-Rebol-official-Builder-intake-and-898-source-copy'
        assert root['verified_pins'] == 2133 and root['source_copy_files'] == 898
        assert (root['worker_pid'], root['command_pid']) == (23888, 23894) and root['durable_owner'] == str(OWNER)
        assert root['common_mutex_held'] is root['original_host_paths_preserved'] is True and root['common_mutex_inode'] == 79859134
        assert all(root[key] is False for key in ('spec_executed', 'header_generation_executed', 'extension_build_executed', 'chart_admission'))
        for path, expected in root['new_repository_copies'].items(): bind(path, expected)
        packet = read(PACKET, PACKET_SHA)
        assert packet['schema'] == 'frozen-rebol-builder-spec-only-v1'
        for path, expected in packet['pins'].items(): bind(path, expected)
        argv = [PYTHON, '-I', '-S', '-B', '-u', str(OH/'revisions/sdk-builder-spec-v1/controller.py'),
            '--intake', '--packet', str(PACKET), '--packet-sha256', PACKET_SHA]
        done = read(OWNER/'terminal.json', root['durable_terminal_sha256'])
        request = read(OWNER/'request.json', root['request_sha256'])
        start, worker = [read(OWNER/name, root['new_repository_copies'][str(C/'owned-jobs/rebol-builder-intake-v1'/name)])
            for name in ('command-started.json', 'worker-started.json')]
        assert all(item['command'] == argv and item['cwd'] == str(OLD) for item in (request, start, worker))
        assert done['status'] == 'command-exited-zero-awaiting-report-review' and type(done['exit_code']) is int and done['exit_code'] == 0
        assert done['actual_command_started'] is True and done['stop_signals'] == [] and done['command_identity_observation_missing'] is False
        assert not any(done.get(key) for key in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure'))
        assert done['command_identity'] == start['command_identity'] and start['command_pid'] == done['command_pid'] == 23894
        assert done['worker_identity'] == worker['worker_identity'] and done['worker_identity']['pid'] == 23888
        listing = done['command_identity']['listing'].split(None, 7)
        assert listing[:2] == ['23894', '23888'] and listing[7].split() == argv
        report = read(root['report_path'], root['report_sha256'])
        body = read(OH/'sdk-qualification/builder-intake-v1/terminal-pin.json', root['body_terminal_sha256'])
        actual = read(root['intake_path'], root['intake_sha256'])
        assert report['status'] == body['status'] == actual['status'] == 'official-Builder-and-source-copy-ready-awaiting-spec-route-review'
        assert report['terminal_evidence_complete'] is True and not any(report.get(key) for key in ('error', 'error_type', 'terminal_artifact_errors'))
        assert body['partial_evidence_pins'] == report['pins'] and body['inherited_common_mutex'] is True
        assert body['report'] == root['report_path'] and body['report_sha256'] == root['report_sha256']
        for path, expected in report['pins'].items(): bind(path, expected)
        assert len(root['native_commands']) == actual['unscored_native_tool_commands'] == 4
        for item in root['native_commands']:
            record = read(item['path'], item['sha256'])
            assert record['command'] == item['command'] and record['pid'] == record['identity']['pid'] == item['pid']
            assert type(record['exit_status']) is type(record['final_exit_status']) is int
            assert record['exit_status'] == record['final_exit_status'] == 0 and record['inherited_common_mutex'] is True
            assert not any(record.get(key) for key in ('error', 'error_type', 'cleanup_errors', 'cleanup_error'))
        assert actual['source_copy_count'] == len(actual['source_copy_files']) == 898
        assert actual['builder_source_commit'] == '5dd9ec60cb96b1ae3cda0ba56ba033d2cf86042e'
        assert actual['builder_source_binary_build_equivalence_proved'] is actual['source_tree_commit_independently_verified'] is False
        assert actual['header_generation_executed'] is actual['extension_build_executed'] is actual['spec_executed'] is actual['chart_admission'] is False
        copy = Path(actual['source_copy']); original = OH/'.build/saved-runtime-source-intake-v1/source-original'
        assert copy == OH/'.build/sdk-builder-spec-v1/source-copy'
        assert {str(path) for path in copy.rglob('*') if path.is_file()} == {item['copy'] for item in actual['source_copy_files']}
        for item in actual['source_copy_files']:
            assert Path(item['copy']).relative_to(copy) == Path(item['original']).relative_to(original)
            bind(item['copy'], item['sha256']); bind(item['original'], item['sha256'])
        source = Path(actual['builder_source'])
        assert source == OH/'.build/sdk-builder-spec-v1/builder-source-original'
        builder_sources = {str(path): report['pins'][str(path)] for path in source.rglob('*') if path.is_file()}
        assert builder_sources and not any(path.is_symlink() for path in source.rglob('*'))
        assert actual['builder_sha256'] == root['builder_sha256'] and actual['builder'] == root['builder']
        bind(actual['builder'], root['builder_sha256'])
        bind(P/'REVIEW.md', digest(P/'REVIEW.md')); bind(Path(__file__).resolve(), digest(__file__))
        assert not OUT.exists() and not OUT.parent.is_symlink()
        OUT.mkdir(parents=True, exist_ok=False)
        review = dict(status='reviewed-actual-builder-intake-and-exact-Rebol-spec-only-route',
            spec_only_execution_authorized=True, generation_execution_authorized=False, unresolved=[], linked_repositories=[],
            selected_target='%rebol3-bulk-macos-arm64', no_force_eval_on_selected_route=True,
            all_selected_actions_are_suppressed_by_test=True, durable_owner=str(OWNER),
            durable_terminal_sha256=root['durable_terminal_sha256'], report_sha256=root['report_sha256'],
            body_terminal_sha256=root['body_terminal_sha256'], intake_sha256=root['intake_sha256'],
            builder_sha256=root['builder_sha256'], reviewed_source_pins=builder_sources,
            selected_recipe_pins={str(copy/'make/rebol3.nest'):'b10fa4bb1301db8d7292be358acdfc143b7d5dd98c488c4cc77e65be3a1483b5',
                str(copy/'make/pre-make.r3'):'fab18619da3c7c0d8689df29e7b17f1f46a3e2c106e57c7f535d81ef0d93a92b'},
            root_review=dict(path=str(ROOT), sha256=ROOT_SHA, verified_pins=2133),
            source_policy_note=dict(path=str(P/'REVIEW.md'), sha256=PINS[str(P/'REVIEW.md')]),
            actual_embedded_banner=root['actual_version_stdout_stderr'], actual_subject_runtime_version='3.22.1',
            source_binary_build_equivalence_proved=False, kernel_post_exec_image_observed=False,
            native_descendant_count_independently_observed=False, native_commands=0, fixture_reexecutions=0,
            compiler_or_generation_execution=False, common_mutex_inode=79859134, source_judgments_are_native_observations=False)
        for path, expected in review['selected_recipe_pins'].items(): bind(path, expected)
        for path, expected in PINS.items(): bind(path, expected)
        save(OUT/'review.json', review); (OUT/'review.json').chmod(0o444)
        review_sha = digest(OUT/'review.json')
        save(OUT/'capture-receipt.json', dict(status='actual-intake-pins-verified-and-source-policy-review-captured',
            review_path=str(OUT/'review.json'), review_sha256=review_sha, input_pins=PINS,
            finished_at=datetime.now(timezone.utc).isoformat(), common_mutex_inode=79859134, native_commands=0))
        print(json.dumps(dict(review_path=str(OUT/'review.json'), review_sha256=review_sha, verified_pin_paths=len(PINS))), flush=True)


if __name__ == '__main__': main()
