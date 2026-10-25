"""Compare probe policies on two backends; never link this diagnostic into Mech."""
import fcntl
import json
from pathlib import Path
import statistics
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state, DATA_SHA


def main():
    plan = read(STUDY / 'execution-plan.json')
    before = source_state()
    assert before['commit'] == plan['source_commit'] and not before['status']
    source = STUDY / 'sources/subject.rs'
    assert process.sha(source) == plan['source_sha256']
    assert process.sha(STUDY / 'sources/diagnostic_packed_table.rs') == plan['table_sha256']
    assert process.sha(Path(plan['component']['path'])) == plan['component']['sha256']
    for row in plan['libraries']:
        assert process.sha(Path(row['path'])) == row['sha256']
    timing = read(HERE / plan['mech_receipt'] / 'results.json')
    targets = dict(mech=HERE / '.build' / plan['mech_binary'],
                   rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
    pins = dict(mech=timing['candidate_sha256'], rust='f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763')
    for name, binary in targets.items():
        assert process.sha(binary) == pins[name]
    env = dict(read(HERE / 'compiler-v74/results.json')['environment'], RUSTUP_TOOLCHAIN=plan['toolchain'])
    report = dict(status='running', source=before, script_sha256=process.sha(Path(__file__)),
                  plan_sha256=process.sha(STUDY / 'execution-plan.json'), binaries={}, samples=[],
                  environment=env, benchmark_samples=0, scope=plan['scope'])
    for name, binary in targets.items():
        report['binaries'][name] = dict(path=str(binary), sha256=pins[name])
    process.save(STUDY / 'timing-results.json', report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        def execute(command, label, stdin=None, quantitative=False):
            receipt = process.execute(command, STUDY / label, env, lock,
                                      stdin=stdin, deadline=180, quantitative=quantitative)
            assert receipt['exit_status'] == 0 and receipt['group_closed'] and receipt['reaped'], label
            assert not receipt['cleanup_errors']
            return receipt
        built = read(STUDY / 'resumed-results.json')
        assert built['samples'] == []
        for name in ('llvm_normal', 'llvm_aligned', 'clif_normal', 'clif_aligned'):
            data = built['binaries'][name]
            targets[name] = Path(data['path'])
            pins[name] = data['sha256']
            assert process.sha(targets[name]) == pins[name]
            report['binaries'][name] = data
        report['reused_completed_builds_sha256'] = process.sha(STUDY / 'resumed-results.json')
        for input_name in plan['input_order']:
            (STUDY / input_name).mkdir(exist_ok=False)
            spec = plan['inputs'][input_name]
            inp = HERE.parents[2] / spec['path']
            policy = HERE / spec['policy']
            assert process.sha(inp) == spec['sha256'] and process.sha(policy) == spec['policy_sha256']
            for index, order in enumerate(plan['orders']):
                for name in order:
                    binary = targets[name]
                    assert process.sha(binary) == pins[name]
                    label = f'{input_name}/{index}-{name}'
                    native = STUDY / (label + '.native.json')
                    command = [str(binary)]
                    if name == 'mech':
                        command += [str(policy), str(native), '--']
                    receipt = execute(command, label, inp, True)
                    assert process.sha(STUDY / label / 'stdout.bin') == spec['output']
                    if name == 'mech':
                        data = read(native)
                        assert data['native_hash_table_updates'] == data['native_packed_map_updates'] == spec['updates']
                        assert data['policy'] == 'secured' and data['native_parallel_tasks'] == 7
                        assert data['native_direct_lookup_regions'] == 5 and data['shutdown'] == 'completed'
                        if input_name == 'full':
                            assert data['native_parallel_peak_workers'] == 7
                    report['samples'].append(dict(input=input_name, order=index, subject=name,
                        seconds=receipt['elapsed_seconds'], maximum_rss_bytes=receipt['maximum_rss_bytes'],
                        process=str((STUDY / label / 'process.json').relative_to(HERE))))
                    process.save(STUDY / 'timing-results.json', report)
                print(input_name, index + 1, 'of 6 verified', flush=True)
        report['statistics'] = {}
        for input_name in plan['input_order']:
            data = {}
            for name in plan['subjects']:
                values = [r['seconds'] for r in report['samples'] if r['subject'] == name and r['input'] == input_name]
                assert len(values) == 6
                data[name] = dict(median_seconds=statistics.median(values), stdev_seconds=statistics.stdev(values))
            for row in data.values():
                row['x_rust'] = row['median_seconds'] / data['rust']['median_seconds']
            report['statistics'][input_name] = data
        assert source_state() == before
        assert process.sha(HERE.parents[2] / 'data/benchmarks.json') == DATA_SHA
        report.update(status='all-probe-pilot-outputs-and-six-oracle-cases-verified', source_after=before)
        process.save(STUDY / 'timing-results.json', report)
        print(json.dumps(report['statistics'], indent=2), flush=True)


if __name__ == '__main__':
    main()
