"""Retain exact refill assembly and qualify the smaller private quote layout."""
import fcntl
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state
sys.path.insert(0, str(HERE))
from analyze_profile import text_section


def main():
    before = source_state()
    plan = read(STUDY / 'plan.json')
    assert before['commit'] == plan['source_commit'] and not before['status']
    out = STUDY / 'code-audit'
    out.mkdir(exist_ok=False)
    env = read(HERE / plan['compiler'] / 'results.json')['environment']
    records = {}
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for label, stem in [('parent', 'packed-domain-validation'), ('candidate', 'prepared-refill')]:
            build = read(HERE / f'profile-{stem}-build-v1/results.json')
            binary = Path(build['binary'])
            assert process.sha(binary) == build['binary_sha256'] and build['whole_machine_code_matches_timed']
            assert text_section(binary) == text_section(HERE / '.build' / ('counting-' + stem))
            nm_folder = out / (label + '-symbols')
            nm = process.execute(['/usr/bin/nm', str(binary)], nm_folder, env, lock, deadline=10, quantitative=False)
            assert nm['exit_status'] == 0
            names = (nm_folder / 'stdout.bin').read_text()
            symbols = [line.split()[-1] for line in names.splitlines()
                if 'program_packed_map' in line and ('6refill' in line or '4fuel' in line)
                and 'drop_in_place' not in line]
            assert 1 <= len(symbols) <= 12, symbols
            functions = []
            for index, symbol in enumerate(symbols):
                folder = out / f'{label}-assembly-{index}'
                command = ['/usr/bin/otool', '-tvV', '-p', symbol, str(binary)]
                receipt = process.execute(command, folder, env, lock, deadline=30, quantitative=False)
                assert receipt['exit_status'] == 0
                lines = (folder / 'stdout.bin').read_text().splitlines()
                start = lines.index(symbol + ':')
                end = next((i for i in range(start + 1, len(lines)) if lines[i].endswith(':')), len(lines))
                retained = '\n'.join(lines[start:end]) + '\n'
                path = out / f'{label}-refill-{index}.s'
                path.write_text(retained)
                instructions = [(m[1], m[2]) for line in lines[start + 1:end]
                    if (m := re.match(r'^([0-9a-fA-F]{16})\s+(.+)$', line))]
                assert instructions
                functions.append(dict(symbol=symbol, retained=str(path.relative_to(HERE)), retained_sha256=process.sha(path),
                    raw_output_sha256=process.sha(folder / 'stdout.bin'), instructions=len(instructions),
                    divisions=[dict(address=at, instruction=text) for at, text in instructions if text.startswith('udiv')]))
            records[label] = dict(binary_sha256=build['binary_sha256'], machine_code_sha256=build['machine_code_sha256'], functions=functions)

        # Include the actual new private module. The two old field declarations
        # are extracted verbatim from the retained candidate, rather than
        # inferred from disassembly. Error is not a field of either quote.
        source_root = Path('/private/tmp/mech-native-hashmap-performance')
        current = source_root / 'hosts/gpu/src/native_artifact/program_packed_fuel.rs'
        old_source = subprocess.check_output(['git', '-C', str(source_root), 'show',
            '36a0d26e05b92f0f3fb21bdbd3605af2108ec882:hosts/gpu/src/native_artifact/program_packed_map.rs'], text=True)
        old_structs = '\n'.join(re.search(r'struct ' + name + r' \{.*?\n\}', old_source, re.S)[0]
            for name in ['FullRefill', 'RefillPlan'])
        harness = '''#![allow(dead_code)]
mod probe {
    #[derive(Clone, Copy)]
    struct Price { compute: u64, comparison: u64 }
    #[derive(Debug)]
    enum Error { Overflow }
    const BATCH: u64 = 1024;
    fn add(a: u64, b: u64) -> Result<u64, Error> { a.checked_add(b).ok_or(Error::Overflow) }
    fn mul(a: u64, b: u64) -> Result<u64, Error> { a.checked_mul(b).ok_or(Error::Overflow) }
    #[path = @PATH@]
    mod actual_new_quote;
    @OLD_STRUCTS@
    pub fn sizes() -> [usize; 2] {
        [size_of::<actual_new_quote::Prepared>(), size_of::<RefillPlan>()]
    }
}
fn main() { let [new, old] = probe::sizes(); println!("{new} {old}"); }
'''.replace('@PATH@', json.dumps(str(current))).replace('@OLD_STRUCTS@', old_structs)
        source_path = out / 'type-layout.rs'
        source_path.write_text(harness)
        executable = HERE / '.build/prepared-refill-type-layout'
        compiled = process.execute(['/Users/cim310/.cargo/bin/rustc', '+nightly-2026-03-03',
            '--edition=2024', '-O', str(source_path), '-o', str(executable)], out / 'type-layout-build', env, lock, deadline=30, quantitative=False)
        assert compiled['exit_status'] == 0
        ran = process.execute([str(executable)], out / 'type-layout-run', env, lock, deadline=5, quantitative=False)
        assert ran['exit_status'] == 0
        sizes = list(map(int, (out / 'type-layout-run/stdout.bin').read_text().split()))
        assert sizes == [40, 72]
    assert source_state() == before
    result = dict(status='exact-refill-code-and-quote-layout-verified', source=before, source_after=before,
        driver_sha256=process.sha(Path(__file__)), records=records,
        quote_layout=dict(new_bytes=sizes[0], old_bytes=sizes[1], harness_sha256=process.sha(source_path),
            actual_new_source_sha256=process.sha(current), retained_old_source_sha256=hashlib.sha256(old_source.encode()).hexdigest()),
        benchmark_samples=0,
        scope='Static exact-code runtime disassembly and a structural layout diagnostic using the actual new private module plus retained old field declarations. The quotes are stack values and LLVM may scalar-replace them; their Rust type sizes do not measure actual stack traffic or heap allocation. Division presence does not establish dynamic frequency or elapsed-time savings. All native tools are serial, bounded and supervised.')
    process.save(out / 'results.json', result)
    print(json.dumps(dict(status=result['status'], quote_bytes=sizes,
        functions={k: [dict(instructions=f['instructions'], divisions=len(f['divisions'])) for f in v['functions']] for k, v in records.items()})))


if __name__ == '__main__':
    main()
