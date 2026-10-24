"""Instrument only a copied host shell, preserving the exact checked Mech Object."""
import fcntl
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state, check_native, OUTPUT_SHA

HEAD = 'e82ed4d54d4490102ac41192d1fcbf492d467e08'
OUT = HERE / 'host-startup-audit-v1'
PROJECT = HERE / '.build/host-startup-audit-v1.project'
ORIGINAL = HERE / '.build/counting-preparation-combined.project'
PACKAGE = 'owner-counting-preparation-combined'

INSTRUMENTATION = '''
// Diagnostic-only host shell: markers are excluded from primary timings.
struct HostPhases {
    ratio: [u32; 2],
    rows: std::cell::RefCell<Vec<(&'static str, u64)>>,
}
unsafe extern "C" {
    fn mach_absolute_time() -> u64;
    fn mach_timebase_info(info: *mut [u32; 2]) -> i32;
}
impl HostPhases {
    fn new() -> Self {
        let mut ratio = [0; 2];
        assert_eq!(unsafe { mach_timebase_info(&mut ratio) }, 0);
        let this = Self { ratio, rows: std::cell::RefCell::new(Vec::with_capacity(20)) };
        this.mark("run_entry");
        this
    }
    fn mark(&self, name: &'static str) {
        let ticks = unsafe { mach_absolute_time() };
        let ns = (u128::from(ticks) * u128::from(self.ratio[0]) / u128::from(self.ratio[1])) as u64;
        self.rows.borrow_mut().push((name, ns));
    }
}
impl Drop for HostPhases {
    fn drop(&mut self) {
        self.mark("run_scope_drop");
        eprintln!("MECH_HOST_PHASES {}", serde_json::to_string(self.rows.get_mut()).unwrap());
    }
}
'''


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def main():
    before = source_state()
    assert before['commit'] == HEAD and not before['status']
    OUT.mkdir(exist_ok=False)
    shutil.copytree(ORIGINAL, PROJECT)
    text = (PROJECT / 'src/main.rs').read_text()
    text, tests = text.split('#[cfg(test)]', 1)
    text = replace_once(text, 'fn run() -> Result<(), String> {', INSTRUMENTATION + '\nfn run() -> Result<(), String> {\n    let host_phases = HostPhases::new();\n    let first_capture = std::cell::Cell::new(true);')
    for old, label in [
        ('    let catalog = std::thread::Builder::new()', 'launch_and_arguments_done'),
        ('    // SAFETY: build.rs pins the original source/bytecode/Object', 'catalog_done'),
        ('    if !linked.descriptor().plan().inputs().is_empty()', 'descriptor_and_identity_done'),
        ('    let backend = ArgumentSnapshotCliBackend::new(', 'limits_and_carriers_done'),
        ('    // SAFETY: build.rs pins this complete resource image', 'runtime_builder_done'),
        ('    drop(catalog);', 'resource_metadata_done'),
        ('    let execution = resource_metadata.map_err', 'catalog_drop_done'),
        ('            let captured_lines = turn.text_capture().is_some();', 'input_capture_done'),
        ('            let first_effect = candidates.len().checked_sub(effect_count)', 'native_resume_done'),
        ('    // This CLI runtime supplies authority/provider/transaction services only.', 'resource_commit_done'),
        ('    let execution = execution.map_err(diagnostic);', 'shutdown_done'),
    ]:
        text = replace_once(text, old, f'    host_phases.mark("{label}");\n' + old)
    text = replace_once(text,
        '|admission| linked.prepare_hosted(admission, limits, &memory)\n            .and_then(|session| session.with_text_capture(launch.input_text_bytes, 64 * 1024))\n            .map_err(|error| mech_core::MechError::new(error, None)),',
        '|admission| {\n            host_phases.mark("resource_admission_done");\n            let result = linked.prepare_hosted(admission, limits, &memory)\n                .and_then(|session| session.with_text_capture(launch.input_text_bytes, 64 * 1024))\n                .map_err(|error| mech_core::MechError::new(error, None));\n            host_phases.mark("native_prepare_done");\n            result\n        },')
    text = replace_once(text,
        '|session, chunk| session.capture_chunk(chunk)\n            .map_err(|error| mech_core::MechError::new(error, None)),',
        '|session, chunk| {\n            if first_capture.replace(false) { host_phases.mark("first_capture_chunk"); }\n            session.capture_chunk(chunk).map_err(|error| mech_core::MechError::new(error, None))\n        },')
    (PROJECT / 'src/main.rs').write_text(text + '#[cfg(test)]' + tests)
    # Keep build.rs's ordinary exact generated-file pins. Only diagnostic main
    # source and its associated build/manifest pin values change in this copy.
    manifest_path = PROJECT / 'linked-manifest.json'
    manifest = read(manifest_path)
    build = (PROJECT / 'build.rs').read_text()
    match = re.search(r'const EXPECTED: &str = ("(?:[^"\\]|\\.)*");', build)
    assert match
    expected = json.loads(json.loads(match[1]))
    assert expected == {k: v for k, v in manifest['pins'].items() if k != 'build.rs'}
    expected['src/main.rs'] = process.sha(PROJECT / 'src/main.rs')
    encoded = json.dumps(json.dumps(expected, separators=(',', ':')))
    build = build[:match.start(1)] + encoded + build[match.end(1):]
    (PROJECT / 'build.rs').write_text(build)
    manifest['pins'] = dict(expected, **{'build.rs': process.sha(PROJECT / 'build.rs')})
    process.save(manifest_path, manifest)
    for name in ('program.o', 'program.mecb', 'native-descriptor.bin', 'native-resources.json', 'object-identity.bin'):
        assert process.sha(PROJECT / name) == process.sha(ORIGINAL / name)
    compiler = read(HERE / 'compiler-v69/results.json')
    env = {k: v for k, v in compiler['environment'].items() if not ((k.startswith('CARGO_') and k != 'CARGO_HOME') or (k.startswith('RUST') and k != 'RUSTUP_HOME'))}
    report = dict(status='building', source=before, driver_sha256=process.sha(Path(__file__)),
                  object_sha256=process.sha(PROJECT / 'program.o'),
                  original_main_sha256=process.sha(ORIGINAL / 'src/main.rs'),
                  diagnostic_main_sha256=process.sha(PROJECT / 'src/main.rs'),
                  diagnostic_build_sha256=process.sha(PROJECT / 'build.rs'),
                  observations=[], benchmark_samples=0,
                  scope='Diagnostic-only copied generated host with monotonic markers. Same checked native Object, descriptor, resources and capability-secured route. No kernel, policy, validation or factory removal. Host markers change code and optimization; durations are phase diagnostics, not primary timings. Parent-before-call to run-entry is an upper bound including supervisor/fork/exec and pre-main loader work, not isolated loader cost.')
    process.save(OUT / 'results.json', report)
    shutil.copy2(PROJECT / 'src/main.rs', OUT / 'diagnostic-main.rs')
    shutil.copy2(PROJECT / 'build.rs', OUT / 'diagnostic-build.rs')
    target = Path('/private/tmp/mech-native-hashmap-performance/target/mech-native/cargo-target')
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        command = ['/Users/cim310/.cargo/bin/cargo', '+nightly-2026-03-03', 'rustc', '--manifest-path', str(PROJECT / 'Cargo.toml'), '--release', '--offline', '--locked', '--jobs', '1', '--bin', PACKAGE, '--target-dir', str(target), '--', '-C', 'lto=fat', '-C', 'codegen-units=1', '-C', 'strip=symbols']
        built = process.execute(command, OUT / 'build', env, lock, deadline=1800, quantitative=False)
        assert built['exit_status'] == 0
        binary = HERE / '.build/counting-host-startup-diagnostic'
        shutil.copy2(target / 'release' / PACKAGE, binary)
        report.update(status='collecting', binary_sha256=process.sha(binary))
        process.save(OUT / 'results.json', report)
        for index, mode in enumerate(['prefix', 'full', 'full', 'prefix', 'prefix', 'full']):
            inp = HERE / 'rust-span-diagnostic-v2/input.fasta' if mode == 'prefix' else HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
            policy = HERE / 'full-timing-v1/launch.json' if mode == 'prefix' else HERE / 'full-disjoint-state-v1/launch.json'
            native_path = OUT / f'{index}-{mode}.native.json'
            folder = OUT / f'{index}-{mode}'
            parent_start = time.monotonic_ns()
            receipt = process.execute([str(binary), str(policy), str(native_path), '--'], folder, env, lock,
                                      stdin=inp, deadline=30, quantitative=False)
            assert receipt['exit_status'] == 0
            expected = OUTPUT_SHA if mode == 'full' else 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
            assert process.sha(folder / 'stdout.bin') == expected
            if mode == 'full':
                check_native(native_path)
            else:
                native = read(native_path)
                assert native['native_hash_table_updates'] == 6999961 and native['shutdown'] == 'completed'
            rows = re.findall(r'^MECH_HOST_PHASES (.+)$', (folder / 'stderr.bin').read_text(), re.M)
            assert len(rows) == 1
            phases = json.loads(rows[0])
            assert phases[0][0] == 'run_entry' and phases[-1][0] == 'run_scope_drop'
            assert all(a[1] <= b[1] for a, b in zip(phases, phases[1:]))
            report['observations'].append(dict(mode=mode, process=receipt, phases_monotonic_ns=phases,
                parent_start_monotonic_ns=parent_start, pre_run_upper_bound_seconds=(phases[0][1] - parent_start) / 1e9,
                input_sha256=process.sha(inp), policy_sha256=process.sha(policy),
                phase_durations_seconds={b[0]: (b[1] - a[1]) / 1e9 for a, b in zip(phases, phases[1:])}))
            process.save(OUT / 'results.json', report)
            print(index, mode, 'host phases and output verified', flush=True)
    assert source_state() == before
    report['source_after'] = before
    report['status'] = 'all-host-phase-diagnostics-and-complete-outputs-verified'
    process.save(OUT / 'results.json', report)


if __name__ == '__main__':
    main()
