"""Measure the cache-census optimization and recheck the preserved histogram program."""
import fcntl, json, statistics, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORKSPACE = Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

out = HERE / 'cache-timing-v2'
out.mkdir(exist_ok=True)
assert not any(path.name != 'results.json' for path in out.iterdir())
prepared = json.loads((HERE / 'compiler-v3/results.json').read_bytes())
assert prepared['status'] == 'compiler-built'
assert subprocess.check_output(['git', '-C', str(WORKSPACE), 'rev-parse', 'HEAD'], text=True).strip() == prepared['source_commit']
assert not subprocess.check_output(['git', '-C', str(WORKSPACE), 'status', '--porcelain'])
env = prepared['environment']
cli = HERE / '.build/mech-canonical'
assert process.sha(cli) == prepared['compiler_sha256']
source = HERE / 'knucleotide-source-map.mec'
candidate = HERE / '.build/counting-cache'
baseline = HERE / '.build/counting-candidate'
assert process.sha(baseline) == '97398e53213992cfd07a4ca8fa0cc732d4ba5695ac20cc655d78a46a6a408c1c'
rust = HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7'
assert process.sha(rust) == 'f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763'
small = HERE / 'available-timing-v1/input.fasta'
small_policy = HERE / 'available-timing-v1/launch.json'
expected_small = (HERE / 'available-timing-v1/run-0/stdout.bin').read_bytes()
full = ROOT / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
assert process.sha(full) == '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
full_policy = HERE / 'full-timing-v1/launch.json'
report = dict(status='building', source_commit=prepared['source_commit'], source_sha256=process.sha(source),
              rust_sha256=process.sha(rust), baseline_sha256=process.sha(baseline),
              small_input_sha256=process.sha(small), full_input_sha256=process.sha(full), samples=[])
process.save(out / 'results.json', report)

with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def build(src, binary, name):
        cmd = [str(cli), '--no-config', 'build', str(src), '--backend', 'cranelift', '--profile', 'release', '--keep-project', '--offline', '--workspace-root', str(WORKSPACE), '--name', name, '-o', str(binary)]
        r = process.execute(cmd, out / ('build-' + name), env, lock, deadline=1800)
        assert r['exit_status'] == 0, (out / ('build-' + name) / 'stderr.bin').read_text()[-6000:]

    def run(binary, label, cohort, round_number, inp, policy, timed=True):
        name = f'{cohort}-{round_number}-{label}'
        cmd = [str(binary), '0'] if label == 'rust' else [str(binary), str(policy), str(out / (name + '.report.json')), '--']
        r = process.execute(cmd, out / name, env, lock, stdin=inp, deadline=120, quantitative=timed)
        assert r['exit_status'] == 0, (out / name / 'stderr.bin').read_text()[-3000:]
        if cohort == 'diagnostic':
            assert (out / name / 'stdout.bin').read_bytes() == expected_small, name
        else:
            assert process.sha(out / name / 'stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7', name
        if label != 'rust':
            native = json.loads((out / (name + '.report.json')).read_bytes())
            assert native['native_aot'] and not native['jit'] and not native['resident_body_evaluation'] and native['shutdown'] == 'completed'
            if label == 'preserved':
                assert native['native_hash_table_regions'] == 7 and native['native_hash_table_updates'] == 874999961
        if timed:
            row = dict(cohort=cohort, label=label, round=round_number, seconds=r['elapsed_seconds'], maximum_rss_bytes=r['maximum_rss_bytes'])
            report['samples'].append(row)
            process.save(out / 'results.json', report)
            print(json.dumps(row), flush=True)

    prior_build = HERE / 'cache-timing-v1/build-owner-cache/process.json'
    assert json.loads(prior_build.read_bytes())['exit_status'] == 0
    assert process.sha(source) == json.loads((HERE / 'cache-timing-v1/results.json').read_bytes())['source_sha256']
    # Generated application.mec is a canonical provenance rendering.
    assert process.sha(Path(str(candidate) + '.project/program.mecb')) == process.sha(Path(str(baseline) + '.project/program.mecb'))
    manifest = json.loads(Path(str(candidate) + '.project/linked-manifest.json').read_bytes())
    assert manifest['object']['work_policy_version'] == 48
    report['candidate_build_receipt'] = str(prior_build)
    report['candidate_sha256'] = process.sha(candidate)
    for label, binary in [('candidate', candidate), ('baseline', baseline)]:
        run(binary, label, 'diagnostic', 'warmup', small, small_policy, False)
    for i, order in enumerate([['candidate', 'baseline'], ['baseline', 'candidate'], ['candidate', 'baseline']]):
        for label in order:
            run(dict(candidate=candidate, baseline=baseline, rust=rust)[label], label, 'diagnostic', i, small, small_policy)

    # This keeps the previously optimized source as a separate regression
    # control. It is not the replacement source-map implementation.
    preserved_source = HERE.parent / 'native-hashmap-batch-v1/qualification-v1/knucleotide.mec'
    preserved = HERE / '.build/histogram-preserved'
    build(preserved_source, preserved, 'histogram-preserved')
    report['preserved_source_sha256'] = process.sha(preserved_source)
    report['preserved_binary_sha256'] = process.sha(preserved)
    for label, binary in [('preserved', preserved), ('rust', rust)]:
        run(binary, label, 'full-preserved-control', 'warmup', full, full_policy, False)
    for i, order in enumerate([['preserved', 'rust'], ['rust', 'preserved'], ['preserved', 'rust']]):
        for label in order:
            run(preserved if label == 'preserved' else rust, label, 'full-preserved-control', i, full, full_policy)

for cohort, denominator in [('diagnostic', 'candidate'), ('full-preserved-control', 'preserved')]:
    samples = [s for s in report['samples'] if s['cohort'] == cohort]
    medians = {label: statistics.median(s['seconds'] for s in samples if s['label'] == label) for label in {s['label'] for s in samples}}
    report[cohort] = dict(median_seconds=medians, x_mech_aot={label: seconds / medians[denominator] for label, seconds in medians.items()}, denominator=denominator)
report['status'] = 'all-outputs-verified'
process.save(out / 'results.json', report)
print(json.dumps({c: report[c] for c in ['diagnostic', 'full-preserved-control']}), flush=True)
