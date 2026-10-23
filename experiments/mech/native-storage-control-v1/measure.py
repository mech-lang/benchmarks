"""Serial direct-storage diagnostic; never publishes a Mech benchmark result."""
import fcntl
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AOT = HERE.parent / 'native-owner-aot-v1'
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

out = HERE / 'timing-v1'
out.mkdir(exist_ok=False)
build = HERE / '.build'
build.mkdir(exist_ok=True)
compiler = json.loads((AOT / 'compiler-v7/results.json').read_text())
parent = json.loads((AOT / 'map-path-timing-v1/results.json').read_text())
rust_build = json.loads((HERE.parent / 'native-hashmap-work-v1/rust-comparison-v2/results.json').read_text())
env = {**compiler['environment'], 'RUSTUP_TOOLCHAIN': 'nightly-2026-03-03'}
library = Path(rust_build['rust_libraries']['hashbrown']['path'])
assert process.sha(library) == rust_build['rust_libraries']['hashbrown']['sha256']
source = HERE / 'string_maps.rs'
targets = dict(control=build / 'string-maps', mech=AOT / '.build/counting-path',
               rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
assert process.sha(targets['mech']) == parent['candidate_sha256']
assert process.sha(targets['rust']) == parent['rust_sha256']
inp = AOT / 'rust-span-diagnostic-v2/input.fasta'
assert process.sha(inp) == parent['input_sha256']
policy = AOT / 'full-timing-v1/launch.json'
assert process.sha(policy) == parent['launch_sha256']
expected = (AOT / 'rust-span-diagnostic-v2/expected.txt').read_bytes()
report = dict(status='building', scope='Diagnostic native String/U64 storage control, not Mech generated code; runtime admission/accounting and canonical map publication are absent; all seven tables and updates retained; one-million-base THREE prefix',
              source_sha256=process.sha(source), mech_compiler_commit=compiler['source_commit'],
              mech_sha256=parent['candidate_sha256'], rust_sha256=parent['rust_sha256'],
              hashbrown=rust_build['rust_libraries']['hashbrown'], input_sha256=process.sha(inp),
              input_bases=1000000, expected_updates=6999961, samples=[], environment=env)
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    command = ['/Users/cim310/.cargo/bin/rustc', '--edition=2021', '-Copt-level=3',
               '-Ctarget-cpu=native', '-Ccodegen-units=1', '-Ldependency=' + str(library.parent),
               '--extern', 'hashbrown=' + str(library), str(source), '-o', str(targets['control'])]
    r = process.execute(command, out / 'build', env, lock, deadline=120)
    assert r['exit_status'] == 0, (out / 'build/stderr.bin').read_text()
    report['control_sha256'] = process.sha(targets['control'])
    report['compile_command'] = command
    process.save(out / 'results.json', report)

    def run(label, number, timed):
        name = f'{number}-{label}'
        command = [str(targets[label])]
        if label == 'mech':
            command += [str(policy), str(out / (name + '.report.json')), '--']
        r = process.execute(command, out / name, env, lock, stdin=inp, deadline=120, quantitative=timed)
        assert r['exit_status'] == 0, (out / name / 'stderr.bin').read_text()
        assert (out / name / 'stdout.bin').read_bytes() == expected
        if label == 'control':
            proof = json.loads((out / name / 'stderr.bin').read_text())
            assert proof == dict(tables=7, updates=6999961, bases=1000000)
        elif label == 'mech':
            proof = json.loads((out / (name + '.report.json')).read_text())
            assert proof['native_aot'] and not proof['jit'] and not proof['resident_body_evaluation']
            assert proof['native_hash_table_regions'] == 7 and proof['native_hash_table_updates'] == 6999961
            assert proof['shutdown'] == 'completed'
        if timed:
            row = dict(label=label, seconds=r['elapsed_seconds'], maximum_rss_bytes=r['maximum_rss_bytes'])
            report['samples'].append(row)
            process.save(out / 'results.json', report)
            print(json.dumps(row), flush=True)

    for label in targets:
        run(label, 'warmup', False)
    for number, order in enumerate([['control', 'mech', 'rust'], ['rust', 'mech', 'control'], ['mech', 'control', 'rust']]):
        for label in order:
            run(label, number, True)
report['median_seconds'] = {label: statistics.median(s['seconds'] for s in report['samples'] if s['label'] == label) for label in targets}
report['x_rust'] = {label: value / report['median_seconds']['rust'] for label, value in report['median_seconds'].items()}
report['status'] = 'all-outputs-and-table-updates-verified'
report['interpretation'] = 'A direct native storage cost control, not a Mech speedup or a prediction. LLVM, canonical publication and runtime accounting differ. Source traversal, serial execution, String keys, separate lookup/update calls and complete table work are retained.'
process.save(out / 'results.json', report)
print(json.dumps(report), flush=True)
