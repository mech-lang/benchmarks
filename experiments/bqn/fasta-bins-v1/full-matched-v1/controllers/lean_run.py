"""Serial Lean conformance and complete-process measurements with saved streams."""
import argparse
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import threading
import time
import re

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / 'experiments/shared/bounded-corpus-v1/cases'
BUILD = ROOT / 'experiments/lean4/.build/native-v1'
SOURCE = ROOT / 'experiments/lean4/source-v1'
STDIN_BENCHES = {'regexredux', 'knucleotide', 'revcomp'}
FULL = {
    'regexredux': (5000000, 298, 'a37e6da1d43b332d5c0f4fc25b76090e9095d4c97c25f1a7186385e87706e4af'),
    'revcomp': (25000000, 254166745, 'e5730d4fd55c464f276e5c6062c80f46e0a735281de15d8c957e2731a9baf70e'),
    'pidigits': (10000, 16893, 'bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c'),
    'spectralnorm': (5500, 12, 'f9d5b5e3eb7657cf1bbba4cc856651864df9cd9fd9a6be9b9bc5fcbb67150deb'),
    'mandelbrot': (16000, 32000015, '609262469ee6a0262ccd03932e557f745c9e7b997ad17835a02a0232a64807be'),
    'fasta': (25000000, 254166745, '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'),
    'knucleotide': (25000000, 259, 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'),
    'binarytrees': (21, 455, '341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1'),
    'nbody': (50000000, None, None),
    'fannkuchredux': (12, 29, '4265a65135c506a68d90d6474003fb9030b7ee244a06c046bd89b3932a28ce20'),
}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def atom(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)


def energy_output(raw, expected):
    try:
        lines = raw.decode('ascii').splitlines()
        refs = expected.decode('ascii').splitlines()
        return len(lines) == len(refs) == 2 and all(math.isfinite(float(a)) and abs(float(a) - float(b)) <= 1e-8 for a, b in zip(lines, refs))
    except (ValueError, UnicodeError):
        return False


def one(command, stdin, directory, timeout):
    directory.mkdir(parents=True, exist_ok=False)
    record = dict(command=[str(x) for x in command], started_utc=now(), stdin=str(stdin))
    event = threading.Event()
    child = [None]
    timed_out = [False]

    def watchdog():
        if not event.wait(timeout):
            timed_out[0] = True
            if child[0] is not None:
                try:
                    os.killpg(child[0], signal.SIGKILL)
                except ProcessLookupError:
                    pass

    watcher = threading.Thread(target=watchdog, daemon=True)
    watcher.start()
    try:
        with open(stdin, 'rb') as inp, (directory / 'stdout.bin').open('wb') as out, (directory / 'stderr.bin').open('wb') as err:
            started = time.perf_counter_ns()
            proc = subprocess.Popen(command, stdin=inp, stdout=out, stderr=err, cwd=ROOT,
                                    env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'LANG': 'C', 'TZ': 'UTC'}, start_new_session=True)
            child[0] = proc.pid
            pid, status, usage = os.wait4(proc.pid, 0)
            ended = time.perf_counter_ns()
            proc.returncode = os.waitstatus_to_exitcode(status)
        assert pid == proc.pid
        record.update(pid=pid, exit_code=proc.returncode, elapsed_seconds=(ended - started) / 1e9,
                      user_seconds=usage.ru_utime, system_seconds=usage.ru_stime,
                      maximum_rss_bytes=usage.ru_maxrss, timed_out=timed_out[0])
    finally:
        event.set()
        watcher.join()
    record['finished_utc'] = now()
    for stream in ['stdout', 'stderr']:
        p = directory / (stream + '.bin')
        record[stream] = dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p))
    atom(directory / 'process.json', record)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['bounded', 'full'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bounded-report', type=Path)
    parser.add_argument('--work-review', type=Path)
    parser.add_argument('--benchmarks', nargs='*')
    parser.add_argument('--samples', type=int, default=3)
    parser.add_argument('--input-large', type=Path)
    parser.add_argument('--input-regex', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    benches = args.benchmarks or list(FULL)
    source_pins = {str(p.relative_to(ROOT)): sha(p) for p in SOURCE.iterdir() if p.is_file()}
    binary_pins = {b: sha(BUILD / b) for b in benches}
    report = dict(schema='lean-serial-execution.v1', mode=args.mode, status='RUNNING',
                  started_utc=now(), sources=source_pins, binaries=binary_pins,
                  controller_sha256=sha(__file__), cases=[], active=None,
                  benchmark_samples=0, chart_admission=False)
    manifest = json.loads((CORPUS / 'manifest.json').read_text())
    report['corpus_sha256'] = sha(CORPUS / 'manifest.json')
    if args.mode == 'full':
        bounded = json.loads(args.bounded_report.read_text())
        assert bounded['status'] == 'PASSED' and len(bounded['cases']) == 149
        assert bounded['sources'] == source_pins and all(bounded['binaries'][b] == binary_pins[b] for b in benches)
        report['bounded_prerequisite'] = dict(path=str(args.bounded_report), sha256=sha(args.bounded_report))
        work = json.loads(args.work_review.read_text())
        assert work['status'] == 'PASSED_STATIC_AND_BOUNDED_NATIVE_ALLOCATION_CHECK' and work['sources'] == source_pins
        report['required_work'] = dict(path=str(args.work_review), sha256=sha(args.work_review))
        report['input_pins'] = {str(p): dict(bytes=p.stat().st_size, sha256=sha(p), mtime_ns=p.stat().st_mtime_ns)
                                for p in [args.input_large, args.input_regex] if p is not None}
        cases = [dict(benchmark=b, case=f'full-{i}', n=FULL[b][0], expected_exit=0) for b in benches for i in range(1, args.samples + 1)]
    else:
        cases = [c for c in manifest['cases'] if c['benchmark'] in benches]

    def save():
        atom(args.output / 'report.json', report)

    with open('/tmp/mech-clbg-timing.lock', 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report['common_mutex_inode'] = os.fstat(lock.fileno()).st_ino
        save()
        for i, case in enumerate(cases):
            b = case['benchmark']
            assert sha(BUILD / b) == binary_pins[b]
            assert all(sha(ROOT / p) == digest for p, digest in source_pins.items())
            command = [str(BUILD / b)] + ([] if b in STDIN_BENCHES else [str(case['n'])])
            if args.mode == 'bounded':
                stdin = CORPUS / case['stdin']['path']
                assert sha(stdin) == case['stdin']['sha256']
            elif b in STDIN_BENCHES:
                stdin = args.input_regex if b == 'regexredux' else args.input_large
                assert stdin is not None and stdin.is_file()
                pin = report['input_pins'][str(stdin)]
                assert stdin.stat().st_size == pin['bytes'] and stdin.stat().st_mtime_ns == pin['mtime_ns'] and sha(stdin) == pin['sha256']
            else:
                stdin = Path('/dev/null')
            report['active'] = dict(benchmark=b, case=case['case'])
            if args.mode == 'full':
                power = subprocess.check_output(['/usr/bin/pmset', '-g', 'batt'], text=True)
                settings = subprocess.check_output(['/usr/bin/pmset', '-g', 'custom'], text=True)
                assert "AC Power" in power and re.search(r'lowpowermode\s+0', settings)
                processes = subprocess.check_output(['/bin/ps', '-axo', 'pid,comm'], text=True).splitlines()
                competing = [p for p in processes if Path(p.split(maxsplit=1)[1]).name in
                             {'cargo', 'rustc', 'rustdoc', 'cc', 'clang', 'lean', 'leanc', 'lake', 'julia', 'hyperfine'}]
                assert not competing, competing
                report['active']['power_before'] = power.strip()
                report['active']['competing_compilers_before'] = competing
            save()
            directory = args.output / f'{i + 1:03d}-{b}-{case["case"]}'
            record = one(command, stdin, directory, 180 if args.mode == 'bounded' else 21600)
            raw = (directory / 'stdout.bin').read_bytes() if args.mode == 'bounded' or b == 'nbody' else None
            if case['expected_exit'] == 'nonzero':
                stderr = (directory / 'stderr.bin').read_bytes()
                valid = record['exit_code'] == 1 and f'Invalid IUPAC byte: {case["expected_invalid_byte"]}'.encode() in stderr and raw == b'>r\n'
            elif args.mode == 'bounded':
                expected = CORPUS / case['expected']['path']
                assert sha(expected) == case['expected']['sha256']
                valid = record['exit_code'] == 0 and record['stderr']['bytes'] == 0 and (
                    energy_output(raw, expected.read_bytes()) if b == 'nbody' else raw == expected.read_bytes())
            elif b == 'nbody':
                valid = record['exit_code'] == 0 and record['stderr']['bytes'] == 0 and energy_output(raw, b'-0.169075164\n-0.169059907\n')
            else:
                valid = record['exit_code'] == 0 and record['stderr']['bytes'] == 0 and record['stdout']['bytes'] == FULL[b][1] and record['stdout']['sha256'] == FULL[b][2]
            record.update(benchmark=b, case=case['case'], valid=valid)
            if args.mode == 'full':
                record['power_before'] = report['active']['power_before']
                record['competing_compilers_before'] = report['active']['competing_compilers_before']
                record['power_after'] = subprocess.check_output(['/usr/bin/pmset', '-g', 'batt'], text=True).strip()
                valid = valid and 'AC Power' in record['power_after']
                record['valid'] = valid
            report['cases'].append(record)
            report['active'] = None
            if valid and args.mode == 'full':
                report['benchmark_samples'] += 1
            save()
            print(f'{i + 1}/{len(cases)} {b} {case["case"]}: {"PASS" if valid else "FAIL"} ({record["elapsed_seconds"]:.3f}s)', flush=True)
            if not valid:
                report['status'] = 'FAILED'
                save()
                raise SystemExit(1)
        report['status'] = 'PASSED'
        report['finished_utc'] = now()
        report['sources_unchanged'] = all(sha(ROOT / p) == digest for p, digest in source_pins.items())
        save()


if __name__ == '__main__':
    main()
