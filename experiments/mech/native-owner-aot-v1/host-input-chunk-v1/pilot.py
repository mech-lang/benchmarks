"""Build two host-only buffer variants and run balanced sequential comparisons."""
import fcntl
import hashlib
import json
import math
import random
import re
import shutil
import statistics
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state, check_native, INPUT_SHA, OUTPUT_SHA, POLICY_SHA, DATA_SHA
sys.path.insert(0, str(HERE))
from analyze_profile import text_section

PREFIX_INPUT = 'e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb'
PREFIX_OUTPUT = 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
PREFIX_POLICY = '3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec'


def main():
    plan = read(STUDY / 'plan.json')
    before = source_state()
    assert before['commit'] == plan['source_commit'] and not before['status']
    baseline = read(HERE / plan['baseline_receipt'] / 'results.json')
    original = HERE / '.build' / (plan['baseline_binary'] + '.project')
    assert process.sha(original / 'program.o') == baseline['object_sha256']
    prepared = read(HERE / plan['compiler'] / 'results.json')
    assert prepared['source_commit'] == before['commit']
    env = {k: v for k, v in prepared['environment'].items()
           if not ((k.startswith('CARGO_') and k != 'CARGO_HOME') or (k.startswith('RUST') and k != 'RUSTUP_HOME'))}
    report = dict(status='building', source=before, plan_sha256=process.sha(STUDY / 'plan.json'),
        driver_sha256=process.sha(Path(__file__)), object_sha256=baseline['object_sha256'],
        baseline_binary_sha256=baseline['candidate_sha256'], builds={}, sessions=[], environment=env)
    assert not (STUDY / 'results.json').exists()
    process.save(STUDY / 'results.json', report)
    targets = dict(baseline=HERE / '.build' / plan['baseline_binary'],
        rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
    pins = dict(baseline=baseline['candidate_sha256'],
        rust='f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763')
    target = Path('/private/tmp/mech-native-hashmap-performance/target/mech-native/cargo-target')
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for label, chunk in plan['variants'].items():
            project = HERE / '.build' / ('host-input-' + label + '.project')
            shutil.copytree(original, project)
            text = (project / 'src/main.rs').read_text()
            old = '.with_text_capture(launch.input_text_bytes, 64 * 1024)'
            assert text.count(old) == 1
            text = text.replace(old, f'.with_text_capture(launch.input_text_bytes, {chunk})')
            (project / 'src/main.rs').write_text(text)
            manifest = read(project / 'linked-manifest.json')
            build = (project / 'build.rs').read_text()
            match = re.search(r'const EXPECTED: &str = ("(?:[^"\\]|\\.)*");', build)
            assert match
            expected = json.loads(json.loads(match[1]))
            assert expected == {k: v for k, v in manifest['pins'].items() if k != 'build.rs'}
            expected['src/main.rs'] = process.sha(project / 'src/main.rs')
            encoded = json.dumps(json.dumps(expected, separators=(',', ':')))
            build = build[:match.start(1)] + encoded + build[match.end(1):]
            (project / 'build.rs').write_text(build)
            manifest['pins'] = dict(expected, **{'build.rs': process.sha(project / 'build.rs')})
            process.save(project / 'linked-manifest.json', manifest)
            unchanged = {}
            for name in ('program.o', 'program.mecb', 'native-descriptor.bin', 'native-descriptor.json', 'native-resources.json', 'object-identity.bin', 'Cargo.toml', 'Cargo.lock'):
                assert process.sha(project / name) == process.sha(original / name), name
                unchanged[name] = process.sha(project / name)
            folder = STUDY / ('build-' + label)
            command = ['/Users/cim310/.cargo/bin/cargo', '+nightly-2026-03-03', 'rustc',
                '--manifest-path', str(project / 'Cargo.toml'), '--release', '--offline', '--locked',
                '--jobs', '1', '--bin', plan['package'], '--target-dir', str(target), '--',
                '-C', 'lto=fat', '-C', 'codegen-units=1', '-C', 'strip=symbols']
            receipt = process.execute(command, folder, env, lock, deadline=1800, quantitative=False)
            assert receipt['exit_status'] == 0
            for name in ('src/main.rs', 'build.rs', 'linked-manifest.json'):
                shutil.copy2(project / name, folder / name.replace('/', '-'))
            binary = HERE / '.build' / ('counting-host-input-' + label)
            shutil.copy2(target / 'release' / plan['package'], binary)
            targets[label], pins[label] = binary, process.sha(binary)
            code = text_section(binary)
            report['builds'][label] = dict(chunk_bytes=chunk, binary=str(binary), binary_sha256=pins[label],
                machine_code_bytes=len(code), machine_code_sha256=hashlib.sha256(code).hexdigest(),
                project=str(project), unchanged_inputs=unchanged, main_sha256=process.sha(project / 'src/main.rs'),
                build_sha256=process.sha(project / 'build.rs'), manifest_sha256=process.sha(project / 'linked-manifest.json'), process=receipt)
            process.save(STUDY / 'results.json', report)
            print('built', label, 'same Object and all non-host inputs verified', flush=True)
        assert source_state() == before
        for mode, session in [('full', 1), ('full', 2), ('prefix', 1)]:
            inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin' if mode == 'full' else HERE / 'rust-span-diagnostic-v2/input.fasta'
            policy = HERE / ('full-disjoint-state-v1/launch.json' if mode == 'full' else 'full-timing-v1/launch.json')
            input_sha, policy_sha = (INPUT_SHA, POLICY_SHA) if mode == 'full' else (PREFIX_INPUT, PREFIX_POLICY)
            assert process.sha(inp) == input_sha and process.sha(policy) == policy_sha
            assert process.sha(HERE.parents[2] / 'data/benchmarks.json') == DATA_SHA
            orders = plan['orders'] if session == 1 else list(reversed(plan['orders']))
            out = STUDY / f'{mode}-v{session}'
            out.mkdir(exist_ok=False)
            batch = dict(status='collecting', mode=mode, session=session, source=before, orders=orders, pins=pins,
                input_sha256=input_sha, policy_sha256=policy_sha, canonical_data_sha256=DATA_SHA,
                samples=[], excluded_warmups=0, excluded_outliers=0, plan_sha256=report['plan_sha256'],
                driver_sha256=report['driver_sha256'], scope=plan['scope'])
            process.save(out / 'results.json', batch)
            for index, order in enumerate(orders):
                for position, subject in enumerate(order):
                    assert process.sha(targets[subject]) == pins[subject]
                    folder = out / f'{index}-{position}-{subject}'
                    native = out / (folder.name + '.native.json')
                    command = [str(targets[subject])]
                    if subject != 'rust':
                        command += [str(policy), str(native), '--']
                    receipt = process.execute(command, folder, env, lock, stdin=inp, deadline=30, quantitative=True)
                    assert receipt['exit_status'] == 0
                    assert process.sha(folder / 'stdout.bin') == (OUTPUT_SHA if mode == 'full' else PREFIX_OUTPUT)
                    if subject != 'rust':
                        if mode == 'full':
                            check_native(native)
                        else:
                            n = read(native)
                            assert n['native_hash_table_updates'] == n['native_packed_map_updates'] == 6999961
                            assert n['policy'] == 'secured' and n['shutdown'] == 'completed'
                            assert n['native_parallel_tasks'] == 7 and 1 <= n['native_parallel_peak_workers'] <= 7
                    batch['samples'].append(dict(subject=subject, order=index, position=position,
                        seconds=receipt['elapsed_seconds'], maximum_rss_bytes=receipt['maximum_rss_bytes'],
                        process=str((folder / 'process.json').relative_to(HERE)), process_sha256=process.sha(folder / 'process.json'),
                        native_sha256=process.sha(native) if subject != 'rust' else None))
                    process.save(out / 'results.json', batch)
                print(mode, session, 'order', index + 1, 'verified', flush=True)
            values = {s: [r for r in batch['samples'] if r['subject'] == s] for s in targets}
            batch['median_seconds'] = {s: statistics.median(r['seconds'] for r in rows) for s, rows in values.items()}
            batch['x_rust'] = {s: v / batch['median_seconds']['rust'] for s, v in batch['median_seconds'].items()}
            batch['median_peak_rss_bytes'] = {s: statistics.median(r['maximum_rss_bytes'] for r in rows) for s, rows in values.items()}
            batch['standard_deviation_seconds'] = {s: statistics.stdev(r['seconds'] for r in rows) for s, rows in values.items()}
            batch['paired_changes'] = {}
            for variant_index, label in enumerate(sorted(plan['variants'])):
                logs = [math.log(c['seconds'] / p['seconds']) for c, p in zip(values[label], values['baseline'])]
                rng = random.Random(2026102505 + 10 * session + variant_index)
                boot = sorted(statistics.median(rng.choices(logs, k=len(logs))) for _ in range(20000))
                batch['paired_changes'][label] = dict(change_percent=100 * math.expm1(statistics.median(logs)),
                    interval_95=[100 * math.expm1(boot[i]) for i in (499, 19499)], faster_pairs=sum(x < 0 for x in logs),
                    median_change_percent=100 * (batch['median_seconds'][label] / batch['median_seconds']['baseline'] - 1))
            assert source_state() == before
            batch.update(status='all-host-chunk-outputs-updates-and-pins-verified', source_after=before)
            process.save(out / 'results.json', batch)
            report['sessions'].append(str((out / 'results.json').relative_to(HERE)))
            process.save(STUDY / 'results.json', report)
            print(json.dumps({k: batch[k] for k in ['mode', 'session', 'median_seconds', 'x_rust', 'paired_changes']}), flush=True)
    assert source_state() == before
    report.update(status='all-host-input-chunk-pilot-stages-verified', source_after=before)
    process.save(STUDY / 'results.json', report)


if __name__ == '__main__':
    main()
