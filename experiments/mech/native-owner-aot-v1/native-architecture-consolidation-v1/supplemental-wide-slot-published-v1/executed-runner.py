#!/usr/bin/env python3
"""Public source/decoded wide-slot artifact comparison; no guest execution."""
if not __debug__:
    raise RuntimeError('Required evidence checks cannot run under optimized Python')
import argparse
import fcntl
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

FILES = ('program.o', 'program.mecb', 'native-descriptor.json',
         'native-descriptor.bin', 'object-identity.bin', 'native-resources.json')


def require(value, message):
    if not value:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def state(workspace):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(workspace), *args],
                                       text=True, timeout=60).strip()
    return dict(commit=git('rev-parse', 'HEAD'), tree=git('rev-parse', 'HEAD^{tree}'),
                status=git('status', '--porcelain'))


def wrapped(workspace, command):
    wrapper = 'import os,sys;os.chdir(sys.argv[1]);os.execve(sys.argv[2],sys.argv[2:],os.environ)'
    return [sys.executable, '-c', wrapper, str(workspace), *command]


def check_process(receipt, deadline, owner):
    require(receipt.get('exit_status') == 0, 'Owned process failed')
    require(not receipt.get('error') and not receipt.get('observer_still_waiting'), 'Process error')
    require(receipt.get('group_closed') is True and receipt.get('reaped') is True, 'Unclosed process group')
    require(receipt.get('cleanup_errors') == [] and receipt.get('signals') == [], 'Cleanup/deadline failure')
    require(receipt.get('deadline_seconds') == deadline, 'Deadline changed')
    require(receipt.get('inherited_common_mutex') is True, 'Missing shared ownership mutex')
    require(receipt.get('quantitative_benchmark') is False, 'Unexpected timing classification')
    require(receipt.get('controller_sha256') == sha(owner), 'Process owner changed')


def descriptor_evidence(project):
    image = read(project / 'native-descriptor.json')
    require(image['format'] == 'mech.build-owned-native-descriptor' and image['version'] == 1,
            'Unexpected descriptor format')
    d = image['descriptor']
    require(d['plan']['inputs'] == [] and d['plan']['resource_requirements'] == [],
            'Closed fixture unexpectedly needs external inputs/resources')
    packed = [r for r in d['closed_tails']['regions'] if r['packed'] is not None]
    require(len(packed) == 1, 'Expected exactly one packed closed-tail body')
    proof = packed[0]['packed']
    require(proof['domain']['bits'] == 4 and proof['domain']['shift'] == 0,
            'Fixture did not select the four-bit source domain')
    constants = [x['constant']['data'].get('U64') for x in d['plan']['constants']]
    require(17 in constants and 42 in constants, 'Width17/input42 constants are absent')
    require(4 * 18 > 64 and 4 * 17 == 68, 'Wide predicate or chosen key width changed')
    return dict(packed=packed[0], packing_bits=4, selected_width=17, selected_key_bits=68,
                maximum_supported_width=18, payload_bytes=24,
                payload_basis='Pinned repr(C) Slot {low:u64,high:u64,value:u64}; pinned narrow(domain) iff bits*18<=64')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, default=Path(__file__).with_name('protocol.json'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    protocol_path = args.protocol.resolve()
    protocol = read(protocol_path)
    require(args.execute, 'Preparation only: execution requires an explicit --execute invocation')
    require(protocol['status'] == 'ready', 'Prospective protocol is not yet fully pinned')
    require(protocol['subjects_order'] == ['I', 'A', 'C'] and protocol['routes'] == ['source', 'decoded'],
            'Changed six-build inventory')
    require(protocol['aot_deadline_seconds'] == 1800 and protocol['clean_deadline_seconds'] == 180,
            'Existing public build/clean deadlines changed')
    source = protocol_path.parent / protocol['fixture']['file']
    require(sha(source) == protocol['fixture']['sha256'], 'Supplemental fixture changed')
    target = Path(protocol['target'])
    require(target == Path('/private/tmp/mech-native-consolidation-perf-target') and target.is_dir(),
            'Unexpected shared public target')
    out = args.out.resolve()
    require(not out.exists() and not out.is_relative_to(target), 'Output must be fresh and outside target')
    root = Path(protocol['benchmark_repository'])
    code = root / protocol['shared_study_directory']
    sys.path.insert(0, str(code))
    old_argv = sys.argv
    sys.argv = [str(Path(__file__).resolve())]
    import study
    sys.argv = old_argv
    process = study.process
    owner = root / 'experiments/janet/knucleotide-bytes-v1/process.py'
    pins = {str(protocol_path): sha(protocol_path), str(source): sha(source),
            str(Path(__file__).resolve()): sha(__file__)}
    for relative, expected in protocol['controller_pins'].items():
        p = root / relative
        require(sha(p) == expected, 'Shared controller differs: ' + relative)
        pins[str(p)] = expected
    require(sha(__file__) == protocol['runner_sha256'], 'Runner differs from reviewed protocol')
    canonical_environment = read(root / protocol['canonical_build_environment'])['environment']
    subjects = []
    for name in protocol['subjects_order']:
        spec = protocol['subjects'][name]
        receipt_path = root / spec['receipt']
        require(spec['receipt_sha256'] and sha(receipt_path) == spec['receipt_sha256'],
                'Public build receipt is missing or changed: ' + name)
        receipt = read(receipt_path)
        workspace = Path(spec['workspace'])
        require(receipt['source']['commit'] == spec['commit'] and receipt['source']['status'] == '',
                'Wrong public receipt source')
        require(state(workspace) == receipt['source'] and receipt['workspace'] == str(workspace),
                'Source checkout is not exact and clean')
        require(not out.is_relative_to(workspace), 'Evidence must be outside frozen source')
        compiler = Path(receipt['executable'] + '-compiler')
        require(sha(compiler) == receipt['compiler_sha256'] == spec['compiler_sha256'],
                'Pinned compiler differs')
        require(sha(receipt['executable']) == receipt['executable_sha256'], 'Pinned public binary changed')
        expected_env = dict(canonical_environment, CARGO_TARGET_DIR=str(target), TMPDIR=str(receipt_path.parent / 'tmp'))
        require(receipt['environment'] == expected_env, 'Public build environment differs')
        for key in ('compiler_process_receipt', 'process_receipt'):
            rp = receipt_path.parents[2] / receipt[key]
            check_process(read(rp), 1800, owner)
            pins[str(rp)] = sha(rp)
        for relative, expected in spec['source_contract_pins'].items():
            p = workspace / relative
            require(sha(p) == expected, 'Wide predicate/fixture/CLI contract differs')
            pins[str(p)] = expected
        for p in [receipt_path, compiler, Path(receipt['executable'])]:
            pins[str(p)] = sha(p)
        subjects.append((name, spec, receipt, workspace, compiler))
    for p, expected in protocol['preserved_workload_pins'].items():
        require(sha(p) == expected, 'Original benchmark workload changed')
        pins[p] = expected

    def unchanged():
        require(all(sha(p) == expected for p, expected in pins.items()), 'Pinned evidence/source changed')
        for _, _, receipt, workspace, _ in subjects:
            require(state(workspace) == receipt['source'], 'Frozen source changed')

    out.mkdir(parents=True)
    shutil.copy2(protocol_path, out / 'prospective-protocol.json')
    shutil.copy2(__file__, out / 'executed-runner.py')
    shutil.copy2(source, out / 'fixture.mec')
    result = dict(schema='mech.wide-slot-public-artifacts.v1', status='running',
                  protocol_sha256=sha(protocol_path), pins=pins, builds=[],
                  benchmark_samples=0, performance_qualified=False)
    save(out / 'result.json', result)
    mutex = Path(protocol['common_mutex'])
    require(mutex.is_file() and mutex.stat().st_ino == protocol['mutex_inode'], 'Mutex changed')
    reference = None
    baseline_bytecode = None
    try:
        with mutex.open('r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            for name, spec, receipt, workspace, compiler in subjects:
                unchanged()
                subject_out = out / name
                subject_out.mkdir()
                tmp = subject_out / 'tmp'
                tmp.mkdir()
                env = dict(receipt['environment'], TMPDIR=str(tmp))
                cargo = ['/Users/cim310/.cargo/bin/cargo', '+nightly-2026-03-03']
                metadata = cargo + ['metadata', '--format-version', '1', '--no-deps', '--locked', '--offline']
                r = process.execute(wrapped(workspace, metadata), subject_out / 'metadata', env, lock,
                                    deadline=180, quantitative=False)
                check_process(r, 180, owner)
                m = read(subject_out / 'metadata/stdout.bin')
                packages = sorted(p['name'] for p in m['packages'] if p['id'] in m['workspace_members'])
                require(packages == protocol['workspace_packages'], 'Workspace package inventory changed')
                clean = cargo + ['clean', '--locked', '--offline', '--target-dir', str(target)]
                for package in packages:
                    clean += ['-p', package]
                r = process.execute(wrapped(workspace, clean), subject_out / 'clean', env, lock,
                                    deadline=180, quantitative=False)
                check_process(r, 180, owner)
                save(subject_out / 'cache-provenance.json', dict(source=receipt['source'], target=str(target),
                     packages=packages, command=clean, process_sha256=sha(subject_out / 'clean/process.json'),
                     purpose='Clean all workspace packages before checkout-path reuse; retain external dependencies only'))
                unchanged()
                for route in protocol['routes']:
                    route_out = subject_out / route
                    route_out.mkdir()
                    binary = route_out / 'native-wide-slot-evidence'
                    input_path = source if route == 'source' else baseline_bytecode
                    require(input_path is not None, 'Decoded route requires pinned baseline source bytecode')
                    command = [str(compiler), '--no-config', 'build', str(input_path), '--backend', 'cranelift',
                               '--profile', 'release', '--keep-project', '--offline', '--workspace-root', str(workspace),
                               '--name', 'native-wide-slot-evidence', '-o', str(binary)]
                    r = process.execute(command, route_out / 'aot-build', env, lock, deadline=1800, quantitative=False)
                    check_process(r, 1800, owner)
                    project = Path(str(binary) + '.project')
                    hashes = {}
                    for f in FILES:
                        p = project / f
                        require(p.is_file() and not p.is_symlink(), 'Missing/nonregular guest artifact: ' + f)
                        hashes[f] = sha(p)
                    evidence = descriptor_evidence(project)
                    if reference is None:
                        require((name, route) == ('I', 'source'), 'Unexpected reference build')
                        reference = hashes
                        baseline_bytecode = project / 'program.mecb'
                    require(hashes == reference, 'Guest Object/bytecode/descriptor/identity/resources differ')
                    for f in FILES:
                        pins[str(project / f)] = hashes[f]
                    pins[str(binary)] = sha(binary)
                    disassemble = [protocol['objdump'], '--disassemble', '--no-show-raw-insn', str(project / 'program.o')]
                    r = process.execute(disassemble, route_out / 'disassembly', env, lock, deadline=180, quantitative=False)
                    check_process(r, 180, owner)
                    require((route_out / 'disassembly/stdout.bin').stat().st_size > 0, 'Empty disassembly')
                    pins[str(route_out / 'disassembly/stdout.bin')] = sha(route_out / 'disassembly/stdout.bin')
                    result['builds'].append(dict(subject=name, route=route, source=receipt['source'], command=command,
                         environment=env, guest_artifacts=hashes, descriptor_evidence=evidence,
                         executable_sha256=sha(binary), aot_process_sha256=sha(route_out / 'aot-build/process.json'),
                         disassembly_sha256=sha(route_out / 'disassembly/stdout.bin')))
                    unchanged()
                    save(out / 'result.json', result)
                    print(name, route, 'six guest artifacts match; four-bit wide layout verified', flush=True)
        require([(r['subject'], r['route']) for r in result['builds']] ==
                [(s, r) for s in protocol['subjects_order'] for r in protocol['routes']], 'Incomplete six-build inventory')
        unchanged()
        result['status'] = 'passed-six-public-builds-wide-guest-artifacts-identical'
    except BaseException as error:
        result.update(status='failed', error=repr(error))
        raise
    finally:
        save(out / 'result.json', result)


if __name__ == '__main__':
    main()
