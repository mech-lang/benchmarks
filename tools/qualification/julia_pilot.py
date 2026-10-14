#!/usr/bin/env python3
"""Validate the retained trimmed Julia N-body executable and record loaded images.

This is a bounded correctness/loader observation, not a timing sample or an AOT
closure proof. It preserves the scored executable and runs under the shared lock.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
LOCK = Path('/tmp/mech-clbg-timing.lock')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def no_core():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    receipt = ROOT / 'archive/languages/julia-aot/20261012/jobs/official-static-io-safe-link-v3/link-result.json'
    reference = ROOT / 'archive/workloads/nbody/results/apple-m3-v04-cranelift-aot-50m.json'
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        assert (os.fstat(lock.fileno()).st_dev, os.fstat(lock.fileno()).st_ino) == (LOCK.stat().st_dev, LOCK.stat().st_ino)
        record = json.loads(receipt.read_text())
        binary = Path(record['binary']['path'])
        assert sha(binary) == record['binary']['sha256']
        references = json.loads(reference.read_text())
        def candidates(value):
            if isinstance(value, dict):
                if 'correctness_1000_stdout' in value:
                    yield value['correctness_1000_stdout']
                for child in value.values():
                    yield from candidates(child)
            elif isinstance(value, list):
                for child in value:
                    yield from candidates(child)
        expected_outputs = set(candidates(references))
        assert expected_outputs == {'-0.169075164\n-0.169087605\n'}
        expected = next(iter(expected_outputs))
        assert not args.output.exists(), 'Output must be fresh'
        args.output.mkdir(parents=True)
        environment = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C',
                       'JULIA_NUM_THREADS': '8', 'OMP_NUM_THREADS': '1',
                       'OPENBLAS_NUM_THREADS': '1', 'VECLIB_MAXIMUM_THREADS': '1',
                       'DYLD_PRINT_LIBRARIES': '1'}
        command = [str(binary), '1000']
        report = {'status': 'running', 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'command': command, 'cwd': str(binary.parent), 'environment': environment,
                  'binary_sha256': sha(binary), 'link_receipt_sha256': sha(receipt),
                  'reference': str(reference.relative_to(ROOT)), 'reference_sha256': sha(reference),
                  'expected_stdout': expected, 'shared_lock': str(LOCK),
                  'common_mutex_inode': os.fstat(lock.fileno()).st_ino,
                  'benchmark_samples': 0, 'runtime_aot_proven': False, 'chart_admission': False,
                  'observer': 'DYLD_PRINT_LIBRARIES; loaded-image observation only'}
        save(args.output/'report.json', report)
        started = time.monotonic()
        process = subprocess.Popen(command, cwd=binary.parent, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
                                   pass_fds=(lock.fileno(),), preexec_fn=no_core)
        report['pid'] = process.pid
        save(args.output/'report.json', report)
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        (args.output/'stdout.txt').write_bytes(stdout)
        (args.output/'stderr.txt').write_bytes(stderr)
        listing = subprocess.run(['/bin/ps', '-axo', 'pid=,pgid='], capture_output=True, text=True, check=True)
        remaining = [int(row.split()[0]) for row in listing.stdout.splitlines() if len(row.split()) == 2 and int(row.split()[1]) == process.pid]
        if remaining:
            os.killpg(process.pid, signal.SIGKILL)
        images = []
        for line in stderr.decode('utf-8', errors='replace').splitlines():
            if line.startswith('dyld['):
                match = re.search(r'\s(/.*)$', line)
                if match and match[1] not in images:
                    images.append(match[1])
        image_files = {path: sha(path) for path in images if Path(path).is_file()}
        unchanged = sha(binary) == report['binary_sha256']
        passed = process.returncode == 0 and stdout.decode('utf-8', errors='replace') == expected and not timed_out and not remaining and unchanged
        report.update(status='bounded-output-validated' if passed else 'bounded-output-failed',
                      exit_status=process.returncode, timeout=timed_out,
                      diagnostic_elapsed_seconds=time.monotonic()-started,
                      stdout_sha256=hashlib.sha256(stdout).hexdigest(), stderr_sha256=hashlib.sha256(stderr).hexdigest(),
                      output_matches_reference=stdout.decode('utf-8', errors='replace') == expected,
                      binary_unchanged=unchanged, remaining_process_group=remaining,
                      loaded_images=images, loaded_image_file_hashes=image_files,
                      codegen_image_observed=any('libjulia-codegen' in path for path in images),
                      actual_workload_executions=1)
        save(args.output/'report.json', report)
        print(json.dumps({key: report[key] for key in ['status', 'exit_status', 'output_matches_reference', 'codegen_image_observed', 'runtime_aot_proven', 'benchmark_samples']}))
        return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
