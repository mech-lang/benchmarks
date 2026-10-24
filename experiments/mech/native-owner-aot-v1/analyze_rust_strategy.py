"""Recompute strategy diagnostics and audit every retained process/observation."""
import fcntl
import json
import statistics
import subprocess
from pathlib import Path
import compare_rust_strategy as strategy

HERE = Path(__file__).resolve().parent
ROOT = strategy.ROOT
process = strategy.process


def read(path):
    return json.loads(path.read_text())


def audit():
    summaries = {}
    quantitative = set()
    all_samples = []
    peak_workers = {}
    for dirname, count, success in [
        ('strategy-comparison-v3',108,'all-108-complete-process-outputs-pass'),
        ('table-strategy-v1',72,'all-72-complete-process-outputs-and-nine-storage-checks-pass'),
    ]:
        out = HERE/dirname
        data = read(out/'results.json')
        plan = read(out/'plan.json')
        assert data['status'] == success and len(data['samples']) == count
        assert process.sha(out/'plan.json') == data['plan_sha256']
        assert data['canonical_benchmark_samples'] == 0
        assert len({(s['input'],s['round'],s['subject']) for s in data['samples']}) == count
        for name,binary in data['binaries'].items():
            assert process.sha(Path(binary['path'])) == binary['sha256']
        for input_name,spec in plan['inputs'].items():
            assert process.sha(ROOT/spec['path']) == spec['sha256']
            assert process.sha(HERE/spec['policy']) == spec['policy_sha256']
            for subject,stat in data['statistics'][input_name].items():
                samples = [s for s in data['samples'] if s['input']==input_name and s['subject']==subject]
                assert len(samples) == 6
                seconds = [s['seconds'] for s in samples]
                assert statistics.median(seconds) == stat['median_seconds']
                assert statistics.stdev(seconds) == stat['sample_sd_seconds']
                assert min(seconds) == stat['minimum_seconds'] and max(seconds) == stat['maximum_seconds']
                assert statistics.median(s['maximum_rss_bytes'] for s in samples) == stat['median_rss_bytes']
                assert stat['x_rust'] == stat['median_seconds']/data['statistics'][input_name]['rust']['median_seconds']
            for round_id,order in enumerate(plan['orders']):
                assert len(order) == len(set(order)) == len(data['binaries'])
                expected = [(s['subject']) for s in data['samples'] if s['input']==input_name and s['round']==round_id]
                assert expected == order, (dirname,input_name,round_id,expected,order)
                elapsed = []
                for subject in order:
                    label = f'{input_name}/{round_id}-{subject}'
                    receipt_path = out/label/'process.json'
                    receipt = read(receipt_path)
                    sample = next(s for s in data['samples'] if (s['input'],s['round'],s['subject'])==(input_name,round_id,subject))
                    assert ROOT/sample['process'] == receipt_path
                    assert receipt['quantitative_benchmark'] and receipt['inherited_common_mutex']
                    assert sample['seconds'] == receipt['elapsed_seconds']
                    assert sample['maximum_rss_bytes'] == receipt['maximum_rss_bytes']
                    assert receipt['command'][0] == data['binaries'][subject]['path']
                    assert process.sha(out/label/'stdout.bin') == spec['output']
                    assert not (out/label/'stderr.bin').stat().st_size
                    quantitative.add(receipt_path)
                    elapsed.append((receipt['birth_identity']['birth_seconds'],receipt['birth_identity']['birth_microseconds']))
                    if subject == 'mech':
                        native = read(out/(label+'.native.json'))
                        assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == spec['updates']
                        assert native['native_hash_table_regions'] == native['native_packed_ssa_regions'] == 7
                        assert native['native_parallel_tasks'] == 7
                        assert 1 <= native['native_parallel_peak_workers'] <= 7
                        if input_name == 'full': assert native['native_parallel_peak_workers'] == 7
                        peak_workers.setdefault(input_name,[]).append(native['native_parallel_peak_workers'])
                assert elapsed == sorted(elapsed)
        all_samples.extend(data['samples'])
        summaries[dirname] = data['statistics']
    previous = read(HERE/'strategy-comparison-v3/pre-resume-results.json')
    final = read(HERE/'strategy-comparison-v3/results.json')
    assert previous['status'] == 'failed-preserve-raw-receipts' and previous['error'] == 'AssertionError()'
    assert all(sample in final['samples'] for sample in previous['samples'])
    assert len(previous['samples']) == 81
    assert process.sha(HERE/'strategy-comparison-v3/initial-controller.py') == final['controller_sha256']
    resume_controller = subprocess.check_output(['git','-C',str(ROOT),'show',
        final['resume_benchmark_commit']+':'+str(Path(__file__).relative_to(ROOT).with_name('compare_rust_strategy.py'))])
    import hashlib
    assert hashlib.sha256(resume_controller).hexdigest() == final['resume_controller_sha256']
    assert len({process.sha(HERE/f'strategy-comparison-v{i}/plan.json') for i in [1,2,3]}) == 1
    owned = []
    timed = set()
    failures = []
    parsed = 0
    for dirname in ['strategy-comparison-v1','strategy-comparison-v2','strategy-comparison-v3','table-strategy-v1']:
        for path in (HERE/dirname).rglob('*.json'):
            data = read(path)
            parsed += 1
            if path.name != 'process.json' or 'birth_identity' not in data: continue
            assert data['reaped'] and data['group_closed'] and not data['cleanup_errors'], str(path)
            assert data['inherited_common_mutex']
            if data['exit_status'] != 0:
                assert path == HERE/'strategy-comparison-v1/hardware/process.json' and data['exit_status'] == 1
                failures.append(str(path.relative_to(ROOT)))
            if data['quantitative_benchmark']: timed.add(path)
            owned.append(path)
    assert failures == [str((HERE/'strategy-comparison-v1/hardware/process.json').relative_to(ROOT))]
    assert timed == quantitative and len(timed) == 180
    for name in ['linear','quadratic','linear_scoped']:
        assert '3 passed; 0 failed' in (HERE/'table-strategy-v1'/('checks-'+name)/'stdout.bin').read_text()
    assert process.sha(HERE/'diagnostic_packed_table.rs') == read(HERE/'table-strategy-v1/plan.json')['table']['sha256']
    assert process.sha(ROOT/'data/benchmarks.json') == strategy.DATA_SHA
    assert process.sha(strategy.SOURCE) == strategy.SOURCE_SHA
    assert process.sha(strategy.RUST) == strategy.RUST_SHA and process.sha(strategy.MECH) == strategy.MECH_SHA
    assert strategy.git('rev-parse','HEAD^{tree}') == strategy.SOURCE_TREE and not strategy.git('status','--porcelain')
    assert Path(strategy.PLAN['common_mutex']).stat().st_ino == 83858837
    result = dict(status='all-strategy-observations-and-terminal-processes-verified',
        controller_sha256=process.sha(Path(__file__)),json_parsed=parsed,terminal_owned_processes=len(owned),
        expected_nonzero_processes=failures,complete_process_observations=180,
        resumed_prior_samples_preserved=81,diagnostic_storage_checks=9,
        peak_workers=peak_workers,canonical_benchmark_samples=0,
        retained_source_tree=strategy.SOURCE_TREE,statistics=summaries,
        inference='Wider payloads, per-worker byte decoding, scoped threads and the Mech narrow table algorithm do not reproduce the large Mech runtime gap in these full-input diagnostics. Small median differences overlap and are not established gains. The table diagnostic omits Mech source-state transport, finite work/resource handling and managed host/publication; residual time is not attributed to one component.',
        next_experiment='Separate the source-derived funded counting loop from rare refill/growth/cap/error continuations, reducing live source/frame state. Retain every original window, update, finite debit and source continuation. This is a compiler design target, not an implemented or measured gain.')
    out = HERE/'strategy-diagnosis-v1'
    out.mkdir(exist_ok=True)
    process.save(out/'results.json',result)
    print(json.dumps({k:result[k] for k in ['status','json_parsed','terminal_owned_processes','complete_process_observations','diagnostic_storage_checks','canonical_benchmark_samples']},indent=2))


if __name__ == '__main__':
    with Path(strategy.PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        audit()
