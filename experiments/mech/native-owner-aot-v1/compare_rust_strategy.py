"""Controlled strategy diagnostics; protected upstream source/data stay unchanged.

Copies vary representation, decoding placement or scheduling while preserving
all seven complete frequency tables. They are not benchmark submissions and
cannot replace the canonical upstream result or establish a Mech compiler gain.
"""
import argparse
import difflib
import fcntl
import json
import random
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORKSPACE = Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

SOURCE = ROOT / 'archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs'
SOURCE_SHA = '47548a02d18bbc68734b0ef2145e3bd89523f15fa779682031ddbd462dbf7851'
RUST = HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7'
RUST_SHA = 'f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763'
MECH = HERE / '.build/counting-escrow-spin'
MECH_SHA = '86f3a407052eb265930aab5a74235dec3ca29abc04a0d277ebfa5f41b8f162c5'
SOURCE_TREE = '90395fc5a8486a5c040c99a9c023b47de10bc968'
VARIANTS = ['rebuild_control', 'wide_keys', 'wide_counts', 'wide_both',
            'decode_each', 'wide_decode', 'scoped_threads']
SUBJECTS = ['rust', *VARIANTS, 'mech']
DATA_SHA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
INPUTS = {
    'full': dict(path='experiments/janet/.build/inputs/fasta-n25000000.stdin',
                 sha256='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa',
                 output='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7',
                 policy='full-launch-order-v1/launch.json',
                 policy_sha256='73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9',
                 updates=874999961),
    'prefix': dict(path='experiments/mech/native-owner-aot-v1/rust-span-diagnostic-v2/input.fasta',
                   sha256='e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb',
                   output='f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa',
                   policy='full-timing-v1/launch.json',
                   policy_sha256='3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec',
                   updates=6999961),
}


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def variant_source(name, original):
    result = original
    if name in ('wide_keys', 'wide_both', 'wide_decode'):
        result = replace_once(result, 'fn print_stat(h: Map<u8>', 'fn print_stat(h: Map<u64>')
        result = replace_once(result, 'match_key(k),', 'match_key(k as u8),')
        result = replace_once(result, 'match_key(k >> 2),', 'match_key((k >> 2) as u8),')
        result = replace_once(result, 'match_key(0b11 & k),', 'match_key((0b11 & k) as u8),')
        for kind in ('u8', 'u16', 'u32'):
            result = result.replace('print::<' + kind + '>', 'print::<u64>')
    if name in ('wide_counts', 'wide_both', 'wide_decode'):
        result = replace_once(result, 'type Map<T> = hashbrown::HashMap<T, u32>;',
                              'type Map<T> = hashbrown::HashMap<T, u64>;')
        result = replace_once(result, 'h.values().sum::<u32>()', 'h.values().sum::<u64>()')
    if name in ('decode_each', 'wide_decode'):
        start = result.index('fn freq<')
        end = result.index('fn get_seq<')
        body = result[start:end]
        body = replace_once(body, 'T::sh(acc, x, mask)', 'T::sh(acc, 0b11 & x >> 1, mask)')
        body = replace_once(body, 'T::sh(a, x, mask)', 'T::sh(a, 0b11 & x >> 1, mask)')
        result = result[:start] + body + result[end:]
        result = replace_once(result, '.iter().map(|&x| 0b11 & x >> 1)),', '.iter().copied()),')
    if name == 'scoped_threads':
        result = replace_once(result, '    let pool = ThreadPool::new();\n', '')
        result = replace_once(result, '    let f7 = pool.spawn_handle', '    std::thread::scope(|scope| {\n    let f7 = pool.spawn_handle')
        for width, capture in ((18, 's1'), (12, 's2'), (6, 's3'), (4, 's4'), (3, 's5'), (2, 's6'), (1, 's7')):
            result = replace_once(result,
                f'pool.spawn_handle(lazy(move || Ok::<_, ()>(freq(&{capture}, {width}))))',
                f'scope.spawn(move || freq(&{capture}, {width}))')
        result = result.replace('.wait().unwrap()', '.join().unwrap()')
        result = replace_once(result, '    print::<u64>(f7.join().unwrap(), "GGTATTTTAATTTATAGT");\n}',
                              '    print::<u64>(f7.join().unwrap(), "GGTATTTTAATTTATAGT");\n    });\n}')
    assert result.count('freq(&s') == 7
    assert result.count('*h.entry(a).or_insert(0) += 1;') == 1
    return result


def git(*args, cwd=WORKSPACE):
    return subprocess.check_output(['git', '-C', str(cwd), *args], text=True).strip()


def prepare(out):
    assert process.sha(SOURCE) == SOURCE_SHA
    out.mkdir(exist_ok=False)
    sources = out / 'sources'
    sources.mkdir()
    original = SOURCE.read_text()
    variants = {}
    for name in VARIANTS:
        text = variant_source(name, original)
        path = sources / (name + '.rs')
        path.write_text(text)
        (sources / (name + '.patch')).write_text(''.join(difflib.unified_diff(
            original.splitlines(keepends=True), text.splitlines(keepends=True),
            fromfile='protected-original', tofile=name)))
        variants[name] = dict(source=str(path.relative_to(ROOT)), sha256=process.sha(path))
    rng = random.Random(20261024)
    orders = []
    for _ in range(3):
        order = SUBJECTS.copy()
        rng.shuffle(order)
        orders.extend([order, order[::-1]])
    plan = dict(schema='mech.rust-strategy-diagnostic.v1',
        source_sha256=SOURCE_SHA, rust_binary_sha256=RUST_SHA, mech_binary_sha256=MECH_SHA,
        source_tree=SOURCE_TREE, canonical_data_sha256=DATA_SHA,
        variants=variants, orders=orders, inputs=INPUTS,
        scope='Diagnostic variants only; six predeclared complete-process observations per subject/input, three random orders paired with their reverses, no excluded warmup or outlier. Inputs are separate cohorts. All subjects run serially under the original common mutex. Exact upstream Rust and retained secured Mech are unchanged controls. Every variant retains seven complete typed tables and all source windows; no new benchmark sample is published.',
        limitations='Changing types can affect hashing monomorphization, arithmetic and layout together. Decoding moves work between input and workers; it is not a pure instruction microbenchmark. Scoped-thread diagnostic preserves reverse-width submission but does not reproduce every Mech runtime scheduling decision. Counterfactuals do not establish an optimization benefit for Mech.',
        interpretation={
            'wide_keys':'Use u64 keys for all seven maps; retain u32 counts.',
            'wide_counts':'Use u64 counts; retain original u8/u16/u32/u64 keys.',
            'wide_both':'Use u64 keys/counts for all maps, matching Mech narrow payload width.',
            'decode_each':'Keep ASCII input; move identical shift/mask into each worker.',
            'wide_decode':'Combine u64 keys/counts and per-worker byte decoding.',
            'scoped_threads':'Replace Tokio pool with seven scoped OS threads; preserve reverse-width spawn and source-order result printing.',
            'rebuild_control':'Unmodified protected Rust source, same pinned dependencies/toolchain/flags; rebuild at separate output path.'})
    process.save(out / 'plan.json', plan)
    print('Prepared seven diagnostic Rust copies and six fixed execution orders.', flush=True)


def run(out, resume=False):
    plan = json.loads((out / 'plan.json').read_text())
    assert (out / 'results.json').exists() == resume
    assert process.sha(SOURCE) == SOURCE_SHA and process.sha(RUST) == RUST_SHA
    assert process.sha(MECH) == MECH_SHA
    assert git('rev-parse', 'HEAD^{tree}') == SOURCE_TREE and not git('status', '--porcelain')
    assert not git('status', '--porcelain', cwd=ROOT), 'Commit the diagnostic plan/source before running'
    assert process.sha(ROOT / 'data/benchmarks.json') == DATA_SHA
    for name, variant in plan['variants'].items():
        assert process.sha(ROOT / variant['source']) == variant['sha256']
        assert (ROOT / variant['source']).read_text() == variant_source(name, SOURCE.read_text())
    for spec in INPUTS.values():
        assert process.sha(ROOT / spec['path']) == spec['sha256']
        assert process.sha(HERE / spec['policy']) == spec['policy_sha256']
    reference = json.loads((HERE.parent / 'native-hashmap-work-v1/rust-comparison-v2/results.json').read_text())
    for library in reference['rust_libraries'].values():
        assert process.sha(Path(library['path'])) == library['sha256']
    env = {**reference['environment'], 'TMPDIR': str(HERE / '.build/tmp')}
    base_command = reference['rust_compile_command'][:-3]
    assert reference['rust_compile_command'][-3] == str(SOURCE)
    assert env['RUSTUP_TOOLCHAIN'] == 'nightly-2026-03-03'
    initial = dict(status='running', plan_sha256=process.sha(out / 'plan.json'),
                  controller_sha256=process.sha(Path(__file__)),
                  benchmark_commit=git('rev-parse', 'HEAD', cwd=ROOT),
                  mech_source_commit=git('rev-parse', 'HEAD'),
                  environment=env, binaries={}, samples=[], scope=plan['scope'],
                  canonical_benchmark_samples=0)
    if resume:
        report = json.loads((out / 'results.json').read_text())
        assert report['status'] == 'failed-preserve-raw-receipts' and report['error'] == 'AssertionError()'
        assert len([s for s in report['samples'] if s['input'] == 'full']) == 54
        assert report['plan_sha256'] == initial['plan_sha256'] and report['environment'] == env
        assert set(report['binaries']) == set(SUBJECTS)
        for data in report['binaries'].values():
            assert process.sha(Path(data['path'])) == data['sha256']
        assert not (out / 'pre-resume-results.json').exists()
        process.save(out / 'pre-resume-results.json', report)
        report.update(status='resuming-all-prior-observations-retained',
            resume_controller_sha256=initial['controller_sha256'],
            resume_benchmark_commit=initial['benchmark_commit'],
            qualification_amendment='Seven source tasks are still mandatory. Short prefix processes may observe 1–7 overlapping active workers; the full input still requires all seven. One prefix execution observed six. Its complete output, process and timing remain retained. No completed process is rerun or discarded. This is a receipt qualification correction, not a program/runtime change.')
    else:
        report = initial
    process.save(out / 'results.json', report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        def execute(command, label, stdin=None, quant=False, deadline=180):
            (out / label).parent.mkdir(parents=True, exist_ok=True)
            receipt = process.execute(command, out / label, env, lock, stdin=stdin,
                                      deadline=deadline, quantitative=quant)
            assert receipt['exit_status'] == 0 and receipt['reaped'] and receipt['group_closed'], (
                label, receipt, (out / label / 'stderr.bin').read_text()[-2000:])
            return receipt
        def retained(command, label, quant=False):
            receipt = json.loads((out / label / 'process.json').read_text())
            assert receipt['command'] == command and receipt['quantitative_benchmark'] == quant
            assert receipt['exit_status'] == 0 and receipt['reaped'] and receipt['group_closed']
            assert not receipt['cleanup_errors'] and receipt['inherited_common_mutex']
            return receipt
        try:
            for name, command in {
                'rust-version':['/Users/cim310/.cargo/bin/rustc', '-Vv'],
                'hardware':['/usr/sbin/sysctl','machdep.cpu.brand_string','hw.model','hw.memsize','hw.ncpu'],
                'os':['/usr/bin/sw_vers'],
                'power-source':['/usr/bin/pmset','-g','batt'],
                'power-settings':['/usr/bin/pmset','-g','custom'],
            }.items():
                if not resume:
                    execute(command, name, deadline=30)
                else:
                    retained(command, name)
            targets = dict(rust=RUST, mech=MECH)
            for name in VARIANTS:
                binary = HERE / '.build' / (out.name + '-' + name)
                source = SOURCE if name == 'rebuild_control' else ROOT / plan['variants'][name]['source']
                command = [*base_command, str(source), '-o', str(binary)]
                if resume:
                    retained(command, 'build-' + name)
                    assert report['binaries'][name]['command'] == command
                else:
                    assert not binary.exists()
                    execute(command, 'build-' + name)
                targets[name] = binary
                report['binaries'][name] = dict(path=str(binary), sha256=process.sha(binary),
                                                source_sha256=process.sha(source), command=command)
                process.save(out / 'results.json', report)
                print('Built diagnostic:', name, flush=True)
            for name in ('rust', 'mech'):
                report['binaries'][name] = dict(path=str(targets[name]),sha256=process.sha(targets[name]))
            for input_name, spec in INPUTS.items():
                for round_id, order in enumerate(plan['orders']):
                    for subject in order:
                        target = targets[subject]
                        assert process.sha(target) == report['binaries'][subject]['sha256']
                        label = f'{input_name}/{round_id}-{subject}'
                        command = [str(target)]
                        native_path = out / (label + '.native.json')
                        if subject == 'mech':
                            command += [str(HERE / spec['policy']), str(native_path), '--']
                        existing = (out / label / 'process.json').exists()
                        receipt = retained(command, label, quant=True) if existing else execute(
                            command, label, ROOT / spec['path'], quant=True)
                        assert process.sha(out / label / 'stdout.bin') == spec['output']
                        assert (out / label / 'stderr.bin').stat().st_size == 0
                        if subject == 'mech':
                            native = json.loads(native_path.read_text())
                            assert native['native_hash_table_updates'] == spec['updates']
                            assert native['native_packed_map_updates'] == spec['updates']
                            assert native['native_hash_table_regions'] == native['native_packed_ssa_regions'] == 7
                            assert native['native_parallel_tasks'] == 7
                            assert 1 <= native['native_parallel_peak_workers'] <= 7
                            if input_name == 'full':
                                assert native['native_parallel_peak_workers'] == 7
                            assert native['native_guarded_loop_regions'] == native['native_guarded_call_regions'] == 7
                            assert native['native_frozen_map_regions'] == 5 and native['native_frozen_map_reads'] == 10
                            assert native['native_aot'] and not native['jit'] and native['policy'] == 'secured'
                            assert native['shutdown'] == 'completed'
                        sample = dict(input=input_name, round=round_id, subject=subject,
                            seconds=receipt['elapsed_seconds'], maximum_rss_bytes=receipt['maximum_rss_bytes'],
                            process=str((out / label / 'process.json').relative_to(ROOT)))
                        recorded = [s for s in report['samples'] if (s['input'], s['round'], s['subject']) == (input_name, round_id, subject)]
                        if recorded:
                            assert recorded == [sample]
                        else:
                            report['samples'].append(sample)
                        process.save(out / 'results.json', report)
                    print(input_name, 'round', round_id + 1, 'of 6 complete', flush=True)
            report['statistics'] = {}
            for input_name in INPUTS:
                stats = {}
                for subject in SUBJECTS:
                    samples = [s for s in report['samples'] if s['input'] == input_name and s['subject'] == subject]
                    values = [s['seconds'] for s in samples]
                    assert len(values) == 6
                    stats[subject] = dict(median_seconds=statistics.median(values),
                        sample_sd_seconds=statistics.stdev(values), minimum_seconds=min(values),maximum_seconds=max(values),
                        median_rss_bytes=statistics.median(s['maximum_rss_bytes'] for s in samples))
                for stat in stats.values():
                    stat['x_rust'] = stat['median_seconds'] / stats['rust']['median_seconds']
                report['statistics'][input_name] = stats
            assert process.sha(SOURCE) == SOURCE_SHA and process.sha(RUST) == RUST_SHA
            assert process.sha(MECH) == MECH_SHA and git('rev-parse', 'HEAD^{tree}') == SOURCE_TREE
            assert not git('status','--porcelain') and process.sha(ROOT/'data/benchmarks.json') == DATA_SHA
            report['status'] = 'all-108-complete-process-outputs-pass'
            process.save(out / 'results.json', report)
            print(json.dumps(report['statistics'], indent=2), flush=True)
        except BaseException as error:
            report.update(status='failed-preserve-raw-receipts', error=repr(error))
            process.save(out / 'results.json', report)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'run', 'resume'])
    parser.add_argument('--receipt', default='strategy-comparison-v1')
    args = parser.parse_args()
    if args.phase == 'prepare':
        prepare(HERE / args.receipt)
    else:
        run(HERE / args.receipt, resume=args.phase == 'resume')
