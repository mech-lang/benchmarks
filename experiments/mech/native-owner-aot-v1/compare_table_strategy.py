"""Compare the narrow Mech table algorithm compiled by rustc with hashbrown.

This diagnostic library is never linked into Mech. Its absence of Mech's
managed host, source CFG and work accounting is an explicit comparison limit.
"""
import argparse
import fcntl
import json
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compare_rust_strategy as strategy
from compare_rust_strategy import ROOT, WORKSPACE, process, PLAN, git

NAMES = ['rust', 'hashbrown_wide_decode', 'linear', 'quadratic', 'linear_scoped', 'mech']


def prepare(out):
    assert process.sha(strategy.SOURCE) == strategy.SOURCE_SHA
    base = json.loads((HERE / 'strategy-comparison-v3/results.json').read_text())
    assert base['status'] == 'all-108-complete-process-outputs-pass'
    out.mkdir(exist_ok=False)
    sources = out / 'sources'
    sources.mkdir()
    table = HERE / 'diagnostic_packed_table.rs'
    (sources / table.name).write_bytes(table.read_bytes())
    original = strategy.variant_source('wide_decode', strategy.SOURCE.read_text())
    original = strategy.replace_once(original, 'type Map<T> = hashbrown::HashMap<T, u64>;',
        'mod diagnostic_packed_table;\ntype Map<T> = diagnostic_packed_table::Table<T>;')
    variants = {}
    for name in ['linear', 'quadratic', 'linear_scoped']:
        text = original
        if name == 'linear_scoped':
            text = strategy.variant_source('scoped_threads', text)
            lines = text.splitlines(keepends=True)
            starts = [i for i, line in enumerate(lines) if ' = scope.spawn(move || freq(' in line]
            assert len(starts) == 7 and starts == list(range(starts[0], starts[0] + 7))
            lines[starts[0]:starts[-1] + 1] = reversed(lines[starts[0]:starts[-1] + 1])
            text = ''.join(lines)
        assert text.count('freq(&s') == 7 and text.count('*h.entry(a).or_insert(0) += 1;') == 1
        path = sources / (name + '.rs')
        path.write_text(text)
        variants[name] = dict(source=str(path.relative_to(ROOT)), sha256=process.sha(path),
                              cfg=['--cfg', 'quadratic_probe'] if name == 'quadratic' else [])
    rng = random.Random(2026102402)
    orders = []
    for _ in range(3):
        order = NAMES.copy()
        rng.shuffle(order)
        orders += [order, order[::-1]]
    targets = dict(rust=dict(path=str(strategy.RUST),sha256=strategy.RUST_SHA),
                   mech=dict(path=str(strategy.MECH),sha256=strategy.MECH_SHA),
                   hashbrown_wide_decode=base['binaries']['wide_decode'])
    plan = dict(schema='mech.rust-table-strategy-diagnostic.v1', variants=variants,
        table=dict(path=str((sources / table.name).relative_to(ROOT)),sha256=process.sha(table)),
        controls=targets, inputs=strategy.INPUTS, orders=orders, source_tree=strategy.SOURCE_TREE,
        scope='Six complete-process observations per subject/input; three fixed random permutations paired with their reverses. No excluded warmup or outlier. Inputs are independent cohorts. Every subject executes serially under the common lock. Canonical data and both protected executables remain unchanged.',
        algorithm='Diagnostic Rust table uses u64 keys/counts, sixteen-byte positive payloads, eight-byte NEON control groups, seven mirrored controls, the same folded constants and 7/8 load threshold as Mech. Linear probing advances eight controls; quadratic variant advances triangular groups. Every source window updates its actual full table. Input remains ASCII and each worker performs its own bit decoding. Linear/scoped also starts the seven jobs in ascending-width source order.',
        limitations='This Rust diagnostic omits Mech source-state transport, precise source errors, managed memory and finite work accounting, capability startup and runtime publication. It tests whether the storage/probing algorithm alone reproduces the large gap. It cannot measure a compiler gain, replace a Mech program or attribute all residual time to any one omitted component. Growth uses ordinary Rust allocation; deterministic folded constants differ from hashbrown random seeds.',
        canonical_benchmark_samples=0)
    process.save(out / 'plan.json', plan)
    print('Prepared three table diagnostics and six fixed execution orders.', flush=True)


def run(out):
    plan = json.loads((out / 'plan.json').read_text())
    assert not (out / 'results.json').exists()
    assert git('rev-parse','HEAD^{tree}') == strategy.SOURCE_TREE and not git('status','--porcelain')
    assert not git('status','--porcelain',cwd=ROOT)
    assert process.sha(ROOT/'data/benchmarks.json') == strategy.DATA_SHA
    assert process.sha(strategy.SOURCE) == strategy.SOURCE_SHA
    assert process.sha(ROOT/plan['table']['path']) == plan['table']['sha256']
    for data in [*plan['variants'].values(), *plan['controls'].values()]:
        assert process.sha(Path(data.get('source', data.get('path')))) == data['sha256']
    for spec in plan['inputs'].values():
        assert process.sha(ROOT/spec['path']) == spec['sha256']
        assert process.sha(HERE/spec['policy']) == spec['policy_sha256']
    reference = json.loads((HERE.parent/'native-hashmap-work-v1/rust-comparison-v2/results.json').read_text())
    for data in reference['rust_libraries'].values():
        assert process.sha(Path(data['path'])) == data['sha256']
    env = {**reference['environment'],'TMPDIR':str(HERE/'.build/tmp')}
    base_command = reference['rust_compile_command'][:-3]
    report = dict(status='running',plan_sha256=process.sha(out/'plan.json'),
        controller_sha256=process.sha(Path(__file__)), benchmark_commit=git('rev-parse','HEAD',cwd=ROOT),
        mech_source_commit=git('rev-parse','HEAD'),environment=env, binaries=plan['controls'].copy(), samples=[],
        scope=plan['scope'], canonical_benchmark_samples=0)
    process.save(out/'results.json',report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        def execute(command,label,stdin=None,quant=False,deadline=180):
            (out/label).parent.mkdir(parents=True,exist_ok=True)
            receipt = process.execute(command,out/label,env,lock,stdin=stdin,deadline=deadline,quantitative=quant)
            assert receipt['exit_status'] == 0 and receipt['reaped'] and receipt['group_closed'], (
                label,receipt,(out/label/'stderr.bin').read_text()[-2000:])
            assert not receipt['cleanup_errors']
            return receipt
        try:
            for label,command in {
                'rust-version':['/Users/cim310/.cargo/bin/rustc','-Vv'],
                'hardware':['/usr/sbin/sysctl','machdep.cpu.brand_string','hw.model','hw.memsize','hw.ncpu'],
                'power-source':['/usr/bin/pmset','-g','batt'],
                'power-settings':['/usr/bin/pmset','-g','custom'],
            }.items(): execute(command,label,deadline=30)
            for name,data in plan['variants'].items():
                source = ROOT/data['source']
                binary = HERE/'.build'/(out.name+'-'+name)
                tests = HERE/'.build'/(out.name+'-'+name+'-checks')
                assert not binary.exists() and not tests.exists()
                command = [*base_command,*data['cfg'],str(source),'-o',str(binary)]
                execute(command,'build-'+name)
                execute([*base_command,*data['cfg'],'--test',str(source),'-o',str(tests)],'build-checks-'+name)
                execute([str(tests),'--test-threads=1'],'checks-'+name)
                output = (out/('checks-'+name)/'stdout.bin').read_text()
                assert '3 passed; 0 failed' in output
                report['binaries'][name] = dict(path=str(binary),sha256=process.sha(binary),
                    source_sha256=process.sha(source),command=command,checks=3)
                process.save(out/'results.json',report)
                print('Built and checked table diagnostic:',name,flush=True)
            for input_name,spec in plan['inputs'].items():
                for round_id,order in enumerate(plan['orders']):
                    for subject in order:
                        data = report['binaries'][subject]
                        binary = Path(data['path'])
                        assert process.sha(binary) == data['sha256']
                        label = f'{input_name}/{round_id}-{subject}'
                        native_path = out/(label+'.native.json')
                        command = [str(binary)]
                        if subject == 'mech': command += [str(HERE/spec['policy']),str(native_path),'--']
                        receipt = execute(command,label,ROOT/spec['path'],quant=True)
                        assert process.sha(out/label/'stdout.bin') == spec['output']
                        assert not (out/label/'stderr.bin').stat().st_size
                        if subject == 'mech':
                            native = json.loads(native_path.read_text())
                            assert native['native_aot'] and native['policy'] == 'secured' and not native['jit']
                            assert native['shutdown'] == 'completed'
                            assert native['native_hash_table_regions'] == native['native_packed_ssa_regions'] == 7
                            assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == spec['updates']
                            assert native['native_parallel_tasks'] == 7
                            assert 1 <= native['native_parallel_peak_workers'] <= 7
                            if input_name == 'full': assert native['native_parallel_peak_workers'] == 7
                            assert native['native_guarded_loop_regions'] == native['native_guarded_call_regions'] == 7
                            assert native['native_frozen_map_regions'] == 5 and native['native_frozen_map_reads'] == 10
                        report['samples'].append(dict(input=input_name,round=round_id,subject=subject,
                            seconds=receipt['elapsed_seconds'], maximum_rss_bytes=receipt['maximum_rss_bytes'],
                            process=str((out/label/'process.json').relative_to(ROOT))))
                        process.save(out/'results.json',report)
                    print(input_name,'round',round_id+1,'of 6 complete',flush=True)
            stats = {}
            for input_name in plan['inputs']:
                values = {}
                for subject in NAMES:
                    samples = [s for s in report['samples'] if s['input']==input_name and s['subject']==subject]
                    seconds = [s['seconds'] for s in samples]
                    assert len(seconds) == 6
                    values[subject] = dict(median_seconds=statistics.median(seconds),
                        sample_sd_seconds=statistics.stdev(seconds),minimum_seconds=min(seconds),maximum_seconds=max(seconds),
                        median_rss_bytes=statistics.median(s['maximum_rss_bytes'] for s in samples))
                for data in values.values(): data['x_rust'] = data['median_seconds']/values['rust']['median_seconds']
                stats[input_name] = values
            assert process.sha(strategy.SOURCE) == strategy.SOURCE_SHA
            assert process.sha(strategy.RUST) == strategy.RUST_SHA and process.sha(strategy.MECH) == strategy.MECH_SHA
            assert git('rev-parse','HEAD^{tree}') == strategy.SOURCE_TREE and not git('status','--porcelain')
            assert process.sha(ROOT/'data/benchmarks.json') == strategy.DATA_SHA
            report.update(status='all-72-complete-process-outputs-and-nine-storage-checks-pass',statistics=stats)
            process.save(out/'results.json',report)
            print(json.dumps(stats,indent=2),flush=True)
        except BaseException as error:
            report.update(status='failed-preserve-raw-receipts',error=repr(error))
            process.save(out/'results.json',report)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase',choices=['prepare','run'])
    parser.add_argument('--receipt',default='table-strategy-v1')
    args = parser.parse_args()
    (prepare if args.phase == 'prepare' else run)(HERE/args.receipt)
