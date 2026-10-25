"""Retain exact-symbol main-thread observations from early full captures."""
from collections import Counter
import fcntl
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE))
from analyze_profile import stack_threads, text_section
from profile_hotspots import leaves
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read


def main():
    reports = {}
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for language in ('mech', 'rust'):
            folder = STUDY / ('early-' + language + '-profile-v1')
            capture = read(folder / 'results.json')
            binary = Path(capture['binary_path'])
            assert capture['status'] == 'profile-captured' and capture['completed_output_verified']
            assert process.sha(binary) == capture['binary_sha256']
            assert hashlib.sha256(text_section(binary)).hexdigest() == capture['machine_code_sha256']
            raw = subprocess.check_output(['/usr/bin/nm', '-n', str(binary)], text=True)
            pretty = subprocess.check_output(['/usr/bin/nm', '-n', '--demangle', str(binary)], text=True)
            for name, content in [('symbols.txt', raw), ('symbols-demangled.txt', pretty)]:
                (folder / name).write_text(content)
            names = {}
            for line in pretty.splitlines():
                match = re.match(r'^([0-9a-fA-F]+) [tT] (.*)$', line)
                if match:
                    names.setdefault(match[1], []).append(match[2])
            demangled = {}
            for line in raw.splitlines():
                match = re.match(r'^([0-9a-fA-F]+) [tT] (.*)$', line)
                if match and match[1] in names:
                    demangled[match[2].lstrip('_')] = max(names[match[1]], key=len)
            def readable(symbol):
                return demangled.get(symbol.lstrip('_'), symbol)
            main_symbols, main_contexts, samples = Counter(), Counter(), []
            patterns = dict(generated_program_entry=('mech_canonical_program_entry_v1',),
                parallel_worker_entry=('10run_worker', '::run_worker'),
                parallel_dispatch=('12run_parallel', '::run_parallel'),
                counting_task=('knucleotide_rust_74freq', 'knucleotide_rust_74calc'),
                wait=('__psynch_cvwait', '__psynch_mutexwait', '__ulock_wait', 'semaphore_wait_trap', '__semwait_signal', 'mach_msg2_trap'))
            inventory = []
            for index, item in enumerate(capture['samples']):
                path = folder / f'sample-{index}' / 'stacks.txt'
                assert process.sha(path) == item['stacks_sha256']
                content = path.read_text()
                graph = content.split('Call graph:\n', 1)[1].split('Total number in stack', 1)[0]
                has_stacks = bool(re.search(r'\d+ Thread_', graph))
                inventory.append(dict(index=index, has_stacks=has_stacks, stacks_sha256=process.sha(path)))
                if not has_stacks:
                    continue
                threads = stack_threads(content, patterns)
                main_threads = {thread['thread'] for thread in threads if thread['main_thread']}
                total = 0
                local = Counter()
                for thread, symbol, count, context in leaves(content):
                    if thread in main_threads:
                        total += count
                        local[readable(symbol)] += count
                        main_symbols[readable(symbol)] += count
                        main_contexts[tuple(readable(s) for s in context)] += count
                assert total == sum(t['samples'] for t in threads if t['main_thread'])
                for thread in threads:
                    thread['counting_task_samples'] = 0 if thread['main_thread'] else thread['inclusive_samples']['counting_task']
                    thread['waiting_samples'] = thread['inclusive_samples']['wait']
                samples.append(dict(stacks=str(path.relative_to(HERE)), stacks_sha256=process.sha(path),
                    main_observations=total, threads=threads,
                    top_main_symbols=[dict(symbol=s, observations=n) for s, n in local.most_common(30)]))
            assert samples
            result = dict(status='early-main-stack-observations-verified', language=language,
                binary_sha256=capture['binary_sha256'], source=capture['source'],
                machine_code_sha256=capture['machine_code_sha256'],
                main_observations=sum(main_symbols.values()), capture_inventory=inventory, samples=samples,
                top_main_symbols=[dict(symbol=s, observations=n) for s, n in main_symbols.most_common(60)],
                top_main_contexts=[dict(ancestors=s, observations=n) for s, n in main_contexts.most_common(80)],
                raw_symbols_sha256=process.sha(folder / 'symbols.txt'),
                demangled_symbols_sha256=process.sha(folder / 'symbols-demangled.txt'),
                analysis_script_sha256=process.sha(Path(__file__)), benchmark_samples=0,
                scope='Exclusive main-thread stack-location observations, with complete ancestor contexts and exact-binary symbol names. Repeated thread roots are merged by ID. Waits, loader/partial-unwind roots and profiler overhead are retained. These are not wall time, CPU time, utilization or matched phase costs. All raw captures, including any empty graph, remain retained.')
            process.save(folder / 'main-analysis.json', result)
            reports[language] = dict(main_observations=result['main_observations'], top_main_symbols=result['top_main_symbols'][:15])
    # Reuse the established Mech analyzer without recapturing a successful run.
    mech_folder = STUDY / 'early-mech-profile-v1'
    inventory = read(mech_folder / 'main-analysis.json')['capture_inventory']
    arguments = [sys.executable, str(HERE / 'analyze_profile.py'), '--timing', 'packed-domain-validation-timing-v1',
        '--profile-build', 'profile-packed-domain-validation-build-v1', '--samples', str(mech_folder.relative_to(HERE)),
        '--binary', 'counting-packed-domain-validation']
    for row in inventory:
        if row['has_stacks']:
            arguments += ['--sample-index', str(row['index'])]
    with (STUDY / 'early-mech-analysis.controller.stdout').open('xb') as stdout, (STUDY / 'early-mech-analysis.controller.stderr').open('xb') as stderr:
        result = subprocess.run(arguments, stdout=stdout, stderr=stderr, cwd=HERE)
        assert result.returncode == 0
    process.save(STUDY / 'early-main-summary.json', dict(status='early-main-observations-retained',
        analysis_script_sha256=process.sha(Path(__file__)), reports=reports, benchmark_samples=0))
    print(json.dumps(reports, indent=2))


if __name__ == '__main__':
    main()
