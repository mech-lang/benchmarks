"""Pre-arm full-input Mech and Rust profiles before loader/input preparation."""
import fcntl
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state, check_native, INPUT_SHA, OUTPUT_SHA, POLICY_SHA
sys.path.insert(0, str(HERE))
from analyze_profile import text_section


def main():
    plan = read(STUDY / 'plan.json')
    before = source_state()
    assert before['commit'] == plan['source_commit'] and not before['status']
    build = read(HERE / 'profile-scalar-cold-origins-build-v1/results.json')
    timing = read(HERE / plan['receipt'] / 'results.json')
    mech = Path(build['binary'])
    rust = HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7'
    assert process.sha(mech) == build['binary_sha256']
    assert process.sha(rust) == 'f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763'
    assert text_section(mech) == text_section(HERE / '.build' / plan['binary'])
    rust_source = HERE.parents[2] / 'archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs'
    assert process.sha(rust_source) == '47548a02d18bbc68734b0ef2145e3bd89523f15fa779682031ddbd462dbf7851'
    inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
    launch = HERE / 'full-disjoint-state-v1/launch.json'
    assert process.sha(inp) == INPUT_SHA and process.sha(launch) == POLICY_SHA
    env = build['environment']
    reports, outputs, binaries = {}, {}, {}
    for language, original in [('mech', mech), ('rust', rust)]:
        out = STUDY / ('early-' + language + '-profile-v1')
        out.mkdir(exist_ok=False)
        binary = HERE / '.build' / (('emcp-' if language == 'mech' else 'ercp-') + secrets.token_hex(4))
        assert not binary.exists()
        shutil.copy2(original, binary)
        assert process.sha(binary) == process.sha(original)
        outputs[language], binaries[language] = out, binary
        reports[language] = dict(status='sampling', language=language, source=before,
            source_commit=before['commit'], source_sha256=process.sha(rust_source) if language == 'rust' else timing['source_sha256'],
            binary_sha256=process.sha(binary), binary_path=str(binary),
            object_sha256=build['object_sha256'] if language == 'mech' else None,
            machine_code_sha256=hashlib.sha256(text_section(binary)).hexdigest(),
            input_sha256=INPUT_SHA, launch_sha256=POLICY_SHA if language == 'mech' else None,
            selected_bases=125000000, expected_table_updates=874999961 if language == 'mech' else None,
            completed_output_verified=False, samples=[], subjects=[], native_counters=None,
            profiling_overhead_included=True, benchmark_samples=0, script_sha256=process.sha(Path(__file__)),
            scope='Three full-input diagnostic captures per language. Sampler is pre-armed with -wait before launch of an exact-byte copy with a random unique name. Every target is an owned direct child and sampled PID must match. No debugger, stop, environment injection or timing observation. Running/waiting stack observations include profiler overhead; startup sampling can alter execution and does not measure phase wall time.')
        process.save(out / 'results.json', reports[language])
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for language in ['mech', 'rust', 'rust', 'mech', 'mech', 'rust']:
            report, out, binary = reports[language], outputs[language], binaries[language]
            index = len(report['subjects'])
            folder = out / f'sample-{index}'
            folder.mkdir()
            launched = []

            def run_subject():
                if launched:
                    return
                launched.append(True)
                native_path = folder / 'native.report.json'
                command = [str(binary)]
                if language == 'mech':
                    command += [str(launch), str(native_path), '--']
                result = process.execute(command, folder / 'subject', env, lock, stdin=inp, deadline=30, quantitative=False)
                assert result['exit_status'] == 0 and process.sha(folder / 'subject/stdout.bin') == OUTPUT_SHA
                if language == 'mech':
                    check_native(native_path)
                    assert read(native_path).get('native_worker_credit_batches', 0) > 0
                    native = read(native_path)
                    report['native_counters'] = {key: value for key, value in native.items() if key.startswith('native_')}
                report['subjects'].append(dict(process=result, stdout_verified=True,
                    native_report_sha256=process.sha(native_path) if language == 'mech' else None))
                process.save(out / 'results.json', report)

            stacks = folder / 'stacks.txt'
            sampler = process.execute(['/usr/bin/sample', binary.name, '2', '1', '-wait', '-mayDie', '-file', str(stacks)],
                folder / 'sampler', env, lock, deadline=12, monitor=run_subject, monitor_interval=0.15, quantitative=False)
            assert sampler['exit_status'] == 0 and len(launched) == 1
            content = stacks.read_text()
            pid = report['subjects'][-1]['process']['birth_identity']['pid']
            assert 'Call graph:\n' in content and f'[{pid}]' in content.split('Call graph:\n', 1)[0]
            assert binary.name in content.split('Call graph:\n', 1)[0]
            report['samples'].append(dict(pid=pid, owned_direct_child=True, stacks=str(stacks),
                stacks_sha256=process.sha(stacks), all_process_threads=True))
            process.save(out / 'results.json', report)
            print(language, index, 'complete output and exact sampled PID verified', flush=True)
    assert source_state() == before
    for language, report in reports.items():
        assert len(report['samples']) == len(report['subjects']) == 3
        report.update(status='profile-captured', completed_output_verified=True, source_after=before)
        process.save(outputs[language] / 'results.json', report)


if __name__ == '__main__':
    main()
