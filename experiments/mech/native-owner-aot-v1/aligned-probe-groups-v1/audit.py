"""Retain exact parent/candidate probe assembly and control-bit address chains."""
import fcntl
from pathlib import Path
import re
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE))
from analyze_profile import text_section
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state


def main():
    plan = read(STUDY / 'plan.json')
    before = source_state()
    assert before['commit'] == plan['source_commit'] and not before['status']
    out = STUDY / 'code-audit'
    out.mkdir(exist_ok=False)
    env = read(HERE / plan['compiler'] / 'results.json')['environment']
    records = {}
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for label, stem in [('parent', 'shared-string-facts'), ('candidate', 'aligned-probe-groups')]:
            build = read(HERE / f'profile-{stem}-build-v1/results.json')
            binary = Path(build['binary'])
            assert process.sha(binary) == build['binary_sha256']
            assert text_section(binary) == text_section(HERE / '.build' / ('counting-' + stem))
            folder = out / (label + '-otool')
            receipt = process.execute(['/usr/bin/otool', '-tvV', str(binary)], folder, env, lock,
                                      deadline=60, quantitative=False)
            assert receipt['exit_status'] == 0
            lines = (folder / 'stdout.bin').read_text().splitlines()
            functions = []
            for header in (173, 284):
                for suffix in ('funded', 'lookup_cache_funded'):
                    symbol = f'_mech_canonical_program_entry_v1_packed_loop_{header}_{suffix}'
                    start = lines.index(symbol + ':')
                    end = next((i for i in range(start + 1, len(lines)) if lines[i].endswith(':')), len(lines))
                    path = out / f'{label}-{header}-{suffix}.s'
                    path.write_text('\n'.join(lines[start:end]) + '\n')
                    instructions = [dict(address=m[1], instruction=m[2]) for line in lines[start + 1:end]
                                    if (m := re.match(r'^([0-9a-fA-F]{16})\s+(.+)$', line))]
                    assert instructions
                    windows = []
                    for index, row in enumerate(instructions):
                        if row['instruction'].split()[0] not in ('rbit', 'ctz'):
                            continue
                        following = instructions[index:index + 12]
                        first_load = next((i for i, item in enumerate(following)
                                           if item['instruction'].split()[0] in ('ldr', 'ldur')), None)
                        windows.append(dict(address=row['address'], through_first_scalar_load=
                                            following[:first_load + 1] if first_load is not None else following))
                    functions.append(dict(symbol=symbol, instructions=len(instructions),
                        retained=str(path.relative_to(HERE)), retained_sha256=process.sha(path),
                        candidate_bit_windows=windows,
                        stack_address_instructions=[row for row in instructions
                            if '[sp' in row['instruction'] or '[x29' in row['instruction']]))
            records[label] = dict(binary_sha256=build['binary_sha256'],
                machine_code_sha256=build['machine_code_sha256'],
                raw_output_sha256=process.sha(folder / 'stdout.bin'), functions=functions)
    assert source_state() == before
    report = dict(status='exact-probe-assembly-retained', source=before, source_after=before,
        script_sha256=process.sha(Path(__file__)), records=records, benchmark_samples=0,
        scope='Exact-code static disassembly. Candidate-bit windows begin at rbit/ctz and retain the following scalar-load address chain. Instruction counts, stack-address lists and static windows do not measure dynamic frequency or elapsed time; raw full disassembly is retained.')
    process.save(out / 'results.json', report)
    print({label: [(f['symbol'], f['instructions'], len(f['candidate_bit_windows']))
                   for f in data['functions']] for label, data in records.items()}, flush=True)


if __name__ == '__main__':
    main()
