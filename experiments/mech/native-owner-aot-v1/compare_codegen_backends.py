"""Controlled Rust backend diagnostic; never substitutes for a Mech result.

Both rebuilds use the unchanged upstream program, existing pinned dependencies,
same toolchain, optimization/native-CPU flags and panic=abort. Only the codegen
backend differs. Existing dependency/standard-library native code remains
shared, so this isolates application/generic codegen, not every library byte.
The distributed backend may differ from Mech's pinned Cranelift release.
"""
import argparse
import fcntl
import hashlib
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

TOOLCHAIN = 'nightly-2026-03-03-aarch64-apple-darwin'
RUSTUP = '/Users/cim310/.cargo/bin/rustup'
SOURCE = ROOT / 'archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs'
RUST = HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7'
PINS = {SOURCE: '47548a02d18bbc68734b0ef2145e3bd89523f15fa779682031ddbd462dbf7851',
        RUST: 'f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763',
        ROOT / 'data/benchmarks.json': '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'}
INPUTS = {
    'prefix': dict(path='experiments/mech/native-owner-aot-v1/rust-span-diagnostic-v2/input.fasta',
        sha256='e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb',
        output='f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa',
        policy='full-timing-v1/launch.json',
        policy_sha256='3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec',
        updates=6999961),
    'full': dict(path='experiments/janet/.build/inputs/fasta-n25000000.stdin',
        sha256='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa',
        output='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7',
        policy='full-cold-snapshots-v1/launch.json',
        policy_sha256='73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9',
        updates=874999961),
}


def source_state():
    def git(*arguments):
        return subprocess.check_output(['git', '--no-optional-locks', '-C', str(WORKSPACE), *arguments], text=True).strip()
    return dict(commit=git('rev-parse','HEAD'), tree=git('rev-parse','HEAD^{tree}'),
                clean=not git('status','--porcelain'))


parser = argparse.ArgumentParser()
parser.add_argument('--receipt', required=True)
parser.add_argument('--toolchain', default=TOOLCHAIN)
parser.add_argument('--rebuild-dependencies', action='store_true')
parser.add_argument('--reuse-dependencies-receipt')
parser.add_argument('--install-component', action='store_true')
parser.add_argument('--no-unwind-tables', action='store_true', help='Matched diagnostic flag for both rebuilds; never changes protected Rust or Mech')
parser.add_argument('--mech-timing', default='direct-entry-timing-v1')
parser.add_argument('--mech-binary', default='counting-direct-entry')
args = parser.parse_args()
TOOLCHAIN = args.toolchain
assert not (args.rebuild_dependencies and args.reuse_dependencies_receipt)
out = HERE / args.receipt
out.mkdir(exist_ok=False)
reference = json.loads((HERE.parent / 'native-hashmap-work-v1/rust-comparison-v2/results.json').read_text())
env = {**reference['environment'], 'RUSTUP_TOOLCHAIN': TOOLCHAIN,
       'TMPDIR': str(HERE / '.build/tmp')}
report = dict(status='running', configuration=vars(args), toolchain=TOOLCHAIN,
    driver_sha256=process.sha(Path(__file__)), canonical_benchmark_samples=0,
    scope='Separate complete-process diagnostics. No excluded warmups or outliers. Application/generic codegen differs; existing dependency and standard-library native code is shared. This is not a Mech compiler improvement or a same-version Cranelift ceiling.')
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
    before = source_state()
    assert before['clean']
    report['source_state_before'] = before

    def execute(command, label, stdin=None, quantitative=False, deadline=180, environment=None):
        (out / label).parent.mkdir(parents=True, exist_ok=True)
        result = process.execute(command, out / label, environment or env, lock, stdin=stdin,
                                 quantitative=quantitative, deadline=deadline)
        assert result['reaped'] and result['group_closed'] and not result['cleanup_errors']
        assert result['exit_status'] == 0, (label, result['exit_status'],
            (out / label / 'stderr.bin').read_text()[-2000:])
        return result

    def validate_pins():
        for path, expected in PINS.items(): assert process.sha(path) == expected
        for data in reference['rust_libraries'].values():
            assert process.sha(Path(data['path'])) == data['sha256']
        for data in INPUTS.values():
            assert process.sha(ROOT / data['path']) == data['sha256']
            assert process.sha(HERE / data['policy']) == data['policy_sha256']

    try:
        validate_pins()
        execute([reference['rust_compile_command'][0], '-Vv'], 'rust-version')
        report['rust_version'] = (out / 'rust-version/stdout.bin').read_text()
        if args.install_component:
            execute([RUSTUP, 'component', 'add', 'rustc-codegen-cranelift-preview',
                     '--toolchain', TOOLCHAIN], 'install-component', deadline=300)
        execute([reference['rust_compile_command'][0], '--print', 'sysroot'], 'sysroot')
        sysroot = Path((out / 'sysroot/stdout.bin').read_text().strip())
        components = [p for p in (sysroot / 'lib').rglob('*cranelift*.dylib') if p.is_file()]
        assert len(components) == 1, components
        report['component'] = dict(path=str(components[0]), sha256=process.sha(components[0]))
        if args.install_component:
            report['status'] = 'official-component-installed-without-default-toolchain-change'
        else:
            timing = json.loads((HERE / args.mech_timing / 'results.json').read_text())
            mech = HERE / '.build' / args.mech_binary
            assert process.sha(mech) == timing['candidate_sha256']
            binaries = dict(rust=dict(path=str(RUST),sha256=PINS[RUST]),
                            mech=dict(path=str(mech),sha256=timing['candidate_sha256']))
            report.update(mech_source_commit=timing['source_commit'], inputs=INPUTS,
                          binaries=binaries, samples=[])
            base = reference['rust_compile_command'][:-3]
            if args.rebuild_dependencies:
                manifest = ROOT / 'archive/workloads/knucleotide/rust-deps/Cargo.toml'
                lockfile = manifest.with_name('Cargo.lock')
                assert process.sha(manifest) == reference['rust_library_manifest_sha256']
                assert process.sha(lockfile) == reference['rust_library_lock_sha256']
                import shutil, tomllib
                for path in (manifest,lockfile): shutil.copyfile(path,out / path.name)
                target = HERE / '.build' / (args.receipt + '-deps')
                assert not target.exists()
                depenv = {**env,'RUSTFLAGS':env.get('RUSTFLAGS','') + ' -C target-cpu=native'}
                execute(['/Users/cim310/.cargo/bin/cargo','build','--release','--locked','--offline',
                    '--manifest-path',str(manifest),'--target-dir',str(target),'--message-format=json'],
                    'build-matched-dependencies',deadline=1200,environment=depenv)
                artifacts = [json.loads(line) for line in (out / 'build-matched-dependencies/stdout.bin').read_text().splitlines()]
                direct = tomllib.loads(manifest.read_text())['dependencies']
                libraries = {}
                for name in reference['rust_libraries']:
                    package = name.replace('_','-'); version = direct[package].removeprefix('=')
                    selected = [a for a in artifacts if a.get('reason') == 'compiler-artifact'
                        and a['target']['name'] == name and a['package_id'].endswith('#'+package+'@'+version)]
                    assert len(selected) == 1, (name,version)
                    files = [Path(f) for f in selected[0]['filenames'] if f.endswith('.rlib')]
                    assert len(files) == 1
                    libraries[name] = dict(path=str(files[0]),sha256=process.sha(files[0]),version=version)
                base = [base[0],'--edition=2021','-Copt-level=3','-Ctarget-cpu=native','-Ccodegen-units=1',
                        '-Ldependency='+str(target / 'release/deps')]
                for name,data in libraries.items(): base.extend(['--extern',name+'='+data['path']])
                report['matched_dependencies'] = libraries
                report['matched_dependency_manifest_sha256'] = process.sha(manifest)
                report['matched_dependency_lock_sha256'] = process.sha(lockfile)
            if args.reuse_dependencies_receipt or args.rebuild_dependencies:
                receipt = HERE / args.reuse_dependencies_receipt if args.reuse_dependencies_receipt else out
                if args.reuse_dependencies_receipt:
                    prior = json.loads((receipt / 'results.json').read_text())
                    assert prior['toolchain'] == TOOLCHAIN
                    assert prior['matched_dependency_manifest_sha256'] == reference['rust_library_manifest_sha256']
                    assert prior['matched_dependency_lock_sha256'] == reference['rust_library_lock_sha256']
                    libraries = prior['matched_dependencies']
                    for data in libraries.values(): assert process.sha(Path(data['path'])) == data['sha256']
                    report['matched_dependencies'] = libraries
                    report['matched_dependency_manifest_sha256'] = prior['matched_dependency_manifest_sha256']
                    report['matched_dependency_lock_sha256'] = prior['matched_dependency_lock_sha256']
                    artifacts = [json.loads(line) for line in (receipt / 'build-matched-dependencies/stdout.bin').read_text().splitlines()]
                files = sorted({Path(f) for a in artifacts if a.get('reason') == 'compiler-artifact'
                    for f in a.get('filenames',[]) if f.endswith(('.rlib','.rmeta'))})
                assert files and all(path.is_file() for path in files)
                report['matched_all_library_files'] = [dict(path=str(path),sha256=process.sha(path)) for path in files]
                # Newer Cargo versions put each package's artifacts in its own
                # directory. Derive search paths from actual compiler output.
                directories = sorted({path.parent for path in files})
                base = [reference['rust_compile_command'][0],'--edition=2021','-Copt-level=3',
                        '-Ctarget-cpu=native','-Ccodegen-units=1']
                base.extend('-Ldependency='+str(path) for path in directories)
                for name,data in libraries.items(): base.extend(['--extern',name+'='+data['path']])
            for name, extra in [('llvm_abort', []), ('cranelift_abort', ['-Zcodegen-backend=cranelift'])]:
                binary = HERE / '.build' / (args.receipt + '-' + name)
                assert not binary.exists()
                common = ['-Cpanic=abort'] + (['-Cforce-unwind-tables=no'] if args.no_unwind_tables else [])
                command = [*base, *common, *extra, str(SOURCE), '-o', str(binary)]
                execute(command, 'build-' + name)
                binaries[name] = dict(path=str(binary),sha256=process.sha(binary),command=command)
                print('Built',name,flush=True)
            names = ['rust','llvm_abort','cranelift_abort','mech']
            orders = []
            rng = random.Random(2026102403)
            for _ in range(3):
                order = names.copy(); rng.shuffle(order)
                orders.extend([order,order[::-1]])
            report['orders'] = orders
            process.save(out / 'results.json', report)
            for input_name, spec in INPUTS.items():
                for round_id, order in enumerate(orders):
                    for subject in order:
                        data = binaries[subject]
                        assert process.sha(Path(data['path'])) == data['sha256']
                        label = f'{input_name}/{round_id}-{subject}'
                        native_path = out / (label + '.native.json')
                        command = [data['path']]
                        if subject == 'mech': command += [str(HERE / spec['policy']),str(native_path),'--']
                        result = execute(command,label,ROOT / spec['path'],quantitative=True)
                        assert process.sha(out / label / 'stdout.bin') == spec['output']
                        assert not (out / label / 'stderr.bin').stat().st_size
                        if subject == 'mech':
                            native = json.loads(native_path.read_text())
                            assert native['native_aot'] and not native['jit']
                            assert native['policy'] == 'secured' and native['shutdown'] == 'completed'
                            assert native['native_hash_table_regions'] == native['native_packed_ssa_regions'] == 7
                            assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == spec['updates']
                            assert native['native_parallel_tasks'] == 7
                            assert 1 <= native['native_parallel_peak_workers'] <= 7
                            if input_name == 'full': assert native['native_parallel_peak_workers'] == 7
                        report['samples'].append(dict(input=input_name,round=round_id,subject=subject,
                            seconds=result['elapsed_seconds'],maximum_rss_bytes=result['maximum_rss_bytes'],
                            process=str((out / label / 'process.json').relative_to(ROOT))))
                        process.save(out / 'results.json',report)
                    print(input_name,'round',round_id+1,'of 6 complete',flush=True)
            stats = {}
            for input_name in INPUTS:
                stats[input_name] = {}
                for name in names:
                    values = [s['seconds'] for s in report['samples'] if s['input'] == input_name and s['subject'] == name]
                    assert len(values) == 6
                    stats[input_name][name] = dict(median_seconds=statistics.median(values),
                        stdev_seconds=statistics.stdev(values),samples_seconds=values)
                denominator = stats[input_name]['rust']['median_seconds']
                for value in stats[input_name].values(): value['x_rust'] = value['median_seconds'] / denominator
            report.update(status='all-backend-diagnostic-outputs-verified', statistics=stats)
        validate_pins()
    except BaseException as error:
        report.update(status='failed-attempt-retained',error=repr(error))
        raise
    finally:
        report['source_state_after'] = source_state()
        report['source_unchanged'] = before == report['source_state_after']
        process.save(out / 'results.json',report)
    assert report['source_unchanged']
print(json.dumps({k:report[k] for k in ('status','statistics') if k in report}))
