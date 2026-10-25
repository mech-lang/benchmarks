"""Retain the exact fused byte-fact function and its vector reduction assembly."""
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
    build = read(HERE / 'profile-credit-fragment-facts-build-v1/results.json')
    binary = Path(build['binary'])
    assert process.sha(binary) == build['binary_sha256']
    assert text_section(binary) == text_section(HERE / '.build' / plan['binary'])
    symbols = STUDY / 'early-mech-profile-v1'
    names = {}
    for line in (symbols / 'nm-pretty/stdout.bin').read_text().splitlines():
        match = re.match(r'^([0-9a-fA-F]+) [tT] (.*)$', line)
        if match and 'mech_core::text_fragment::byte_facts' in match[2]:
            names[match[1]] = match[2]
    raw = []
    for line in (symbols / 'nm-raw/stdout.bin').read_text().splitlines():
        match = re.match(r'^([0-9a-fA-F]+) [tT] (.*)$', line)
        if match and match[1] in names:
            raw.append(match[2])
    assert len(raw) == 1, raw
    env = read(HERE / plan['compiler'] / 'results.json')['environment']
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        receipt = process.execute(['/usr/bin/otool', '-tvV', str(binary)], out / 'candidate-otool',
                                  env, lock, deadline=60, quantitative=False)
        assert receipt['exit_status'] == 0
    lines = (out / 'candidate-otool/stdout.bin').read_text().splitlines()
    start = lines.index(raw[0] + ':')
    end = next((i for i in range(start + 1, len(lines)) if lines[i].endswith(':')), len(lines))
    retained = out / 'byte-facts.s'
    retained.write_text('\n'.join(lines[start:end]) + '\n')
    instructions = [m[2] for line in lines[start + 1:end]
                    if (m := re.match(r'^([0-9a-fA-F]{16})\s+(.+)$', line))]
    assert instructions
    vector = [line for line in instructions if re.search(r'\bv[0-9]+\b', line)]
    assert vector and any(line.startswith('udot.4s') for line in vector)
    candidate = read(HERE / plan['receipt'] / 'results.json')
    parent = read(HERE / plan['parent_receipt'] / 'results.json')
    assert source_state() == before
    process.save(out / 'results.json', dict(status='exact-fragment-fact-assembly-retained',
        source=before, source_after=before, script_sha256=process.sha(Path(__file__)),
        symbol=raw[0], readable=list(names.values())[0], instructions=len(instructions),
        vector_instructions=vector, binary_sha256=build['binary_sha256'],
        machine_code_sha256=build['machine_code_sha256'], retained_sha256=process.sha(retained),
        raw_output_sha256=process.sha(out / 'candidate-otool/stdout.bin'),
        guest_object_unchanged=candidate['object_sha256'] == parent['object_sha256'],
        benchmark_samples=0,
        scope='Static disassembly of the exact timed executable. Vector instruction presence and static counts do not measure speed, dynamic frequency or phase elapsed time. Guest object equality compares the independently built raw object bytes.'))
    print('Retained byte-fact instructions:', len(instructions), 'vector instructions:', len(vector), flush=True)


if __name__ == '__main__':
    main()
