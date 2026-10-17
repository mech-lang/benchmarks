"""Serial reduced-size diagnostics; never extrapolate or admit these as timings."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess

from lean_run import ROOT, one, sha, energy_output

SIZES = {'nbody': 2000000, 'spectralnorm': 1500, 'mandelbrot': 2000, 'fannkuchredux': 10}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-report', type=Path, required=True)
    parser.add_argument('--bounded-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--benchmarks', nargs='+', default=['nbody', 'spectralnorm', 'mandelbrot'])
    args = parser.parse_args()
    build = json.loads(args.build_report.read_text())
    bounded = json.loads(args.bounded_report.read_text())
    baseline = json.loads((ROOT / 'experiments/lean4/bounded-v2/report.json').read_text())
    assert build['status'] == 'COMPILED_AWAITING_CONFORMANCE'
    assert bounded['status'] == 'PASSED' and len(bounded['cases']) == 149
    assert bounded['sources'] == build['sources']
    assert all(sha(ROOT / name) == digest for name, digest in build['sources'].items())
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, args.output / 'producer.py')
    report = dict(schema='lean-reduced-workload-diagnostic.v1', status='RUNNING',
                  build_report=str(args.build_report), build_report_sha256=sha(args.build_report),
                  bounded_report=str(args.bounded_report), bounded_report_sha256=sha(args.bounded_report),
                  controller_sha256=sha(__file__), process_controller_sha256=sha(Path(__file__).with_name('lean_run.py')),
                  benchmark_samples=0, catalog_admission=False, extrapolation_permitted=False, results={})

    def save():
        (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')

    with open('/tmp/mech-clbg-timing.lock', 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report['common_mutex_inode'] = os.fstat(lock.fileno()).st_ino
        for benchmark in args.benchmarks:
            n = SIZES[benchmark]
            candidate = build['profiles'][benchmark]
            old = ROOT / 'experiments/lean4/.build/native-v1' / benchmark
            assert sha(old) == baseline['binaries'][benchmark]
            assert sha(candidate['binary']) == candidate['binary_sha256'] == bounded['binaries'][benchmark]
            power = subprocess.check_output(['/usr/bin/pmset', '-g', 'batt'], text=True)
            assert 'AC Power' in power
            processes = subprocess.check_output(['/bin/ps', '-axo', 'pid,comm'], text=True).splitlines()
            competing = [line for line in processes if Path(line.split(maxsplit=1)[1]).name in
                         {'cargo', 'rustc', 'rustdoc', 'cc', 'clang', 'lean', 'leanc', 'lake', 'julia', 'hyperfine'}]
            assert not competing, competing
            before = one([str(old), str(n)], Path('/dev/null'), args.output / (benchmark + '-baseline'), 300)
            after = one([candidate['binary'], str(n)], Path('/dev/null'), args.output / (benchmark + '-candidate'), 300)
            assert before['exit_code'] == after['exit_code'] == 0
            assert before['stderr']['bytes'] == after['stderr']['bytes'] == 0
            old_raw = (args.output / (benchmark + '-baseline') / 'stdout.bin').read_bytes()
            new_raw = (args.output / (benchmark + '-candidate') / 'stdout.bin').read_bytes()
            equivalent = energy_output(new_raw, old_raw) if benchmark == 'nbody' else new_raw == old_raw
            report['results'][benchmark] = dict(n=n, baseline=before, candidate=after,
                complete_outputs_equivalent=equivalent,
                observed_reduced_size_ratio=before['elapsed_seconds'] / after['elapsed_seconds'])
            save()
            assert equivalent
            print(benchmark, 'pilot output PASS', f'{before["elapsed_seconds"]:.3f}s -> {after["elapsed_seconds"]:.3f}s', flush=True)
        assert all(sha(ROOT / name) == digest for name, digest in build['sources'].items())
        report['status'] = 'PASSED_REDUCED_DIAGNOSTICS_ONLY'
        save()


if __name__ == '__main__':
    main()
