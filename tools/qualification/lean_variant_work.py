"""Retain required-work witnesses for immutable Lean candidate executables."""
import argparse
import fcntl
import json
import math
from pathlib import Path
import re
import shutil
import subprocess

from lean_run import ROOT, CORPUS, sha

TOOLCHAIN = Path('/private/tmp/mech-lean4-toolchain/lean-4.35.0-darwin_aarch64')


def function(text, name):
    match = re.search(r'LEAN_EXPORT lean_object\* ' + re.escape(name) + r'\([^;\n]+\)\{', text)
    assert match, name
    start = match.start()
    depth = 1
    end = match.end()
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return start, end, text[start:end]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-report', type=Path, required=True)
    parser.add_argument('--bounded-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build = json.loads(args.build_report.read_text())
    bounded = json.loads(args.bounded_report.read_text())
    assert build['status'] == 'COMPILED_AWAITING_CONFORMANCE'
    assert bounded['status'] == 'PASSED' and len(bounded['cases']) == 149
    assert bounded['sources'] == build['sources']
    assert all(sha(ROOT / name) == digest for name, digest in build['sources'].items())
    assert all(sha(p['binary']) == p['binary_sha256'] == bounded['binaries'][b]
               for b, p in build['profiles'].items())
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, args.output / 'producer.py')
    native = ROOT / 'experiments/lean4/.build/optimization-v1' / args.output.name
    native.mkdir(parents=True, exist_ok=False)
    sdk = subprocess.check_output(['/usr/bin/xcrun', '--show-sdk-path'], text=True).strip()
    report = dict(schema='lean-required-work-review.v1', status='REVIEWING',
                  sources=build['sources'], build_report=str(args.build_report),
                  build_report_sha256=sha(args.build_report),
                  bounded_report_sha256=sha(args.bounded_report),
                  controller_sha256=sha(__file__), benchmark_measurements=0, commands=[])

    def save():
        (args.output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')

    def diagnostic(benchmark, text, size, expected):
        source = args.output / (benchmark + '-counted.c')
        source.write_text(text)
        binary = native / benchmark
        command = [str(TOOLCHAIN / 'bin/leanc'), '-O3', '-DNDEBUG', '-fno-fast-math',
                   '-ffp-contract=off', '-mmacosx-version-min=14.4', '-isysroot', sdk,
                   '-isystem', sdk + '/usr/include', '-o', str(binary), str(source.resolve())]
        result = subprocess.run(command, capture_output=True, timeout=300)
        report['commands'].append(dict(command=command, exit_code=result.returncode))
        (args.output / (benchmark + '-compile.stdout')).write_bytes(result.stdout)
        (args.output / (benchmark + '-compile.stderr')).write_bytes(result.stderr)
        assert result.returncode == 0, result.stderr.decode(errors='replace')
        result = subprocess.run([str(binary), str(size)], capture_output=True, timeout=180)
        prefix = benchmark + '-' + str(size)
        (args.output / (prefix + '.stdout')).write_bytes(result.stdout)
        (args.output / (prefix + '.stderr')).write_bytes(result.stderr)
        assert result.returncode == 0
        if expected is not None:
            assert result.stdout == expected
        return dict(size=size, diagnostic_source_sha256=sha(source), diagnostic_binary_sha256=sha(binary),
                    production_binary_sha256=build['profiles'][benchmark]['binary_sha256'],
                    stdout_sha256=sha(args.output / (prefix + '.stdout')),
                    stderr_sha256=sha(args.output / (prefix + '.stderr')),
                    complete_output_matches_reference=expected is not None,
                    observed=json.loads(result.stderr), diagnostic_is_timed_binary=False)

    with open('/tmp/mech-clbg-timing.lock', 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        tree = Path(build['profiles']['binarytrees']['generated_c']).read_text()
        start, end, body = function(tree, 'l_makeTree')
        sites = 'lean_alloc_ctor(1, 2, 8)'
        assert body.count(sites) == 2
        (args.output / 'binarytrees-make.generated.c').write_text(body + '\n')
        helper = '''
#include <stdatomic.h>
#include <stdio.h>
static _Atomic unsigned long long bench_nodes;
static lean_object* bench_node(unsigned t, unsigned o, unsigned s) {
  atomic_fetch_add_explicit(&bench_nodes, 1, memory_order_relaxed);
  return lean_alloc_ctor(t, o, s);
}
__attribute__((destructor)) static void bench_node_report(void) {
  fprintf(stderr, "{\\"node_allocations\\":%llu}\\n", atomic_load(&bench_nodes));
}
'''
        counted = tree[:start] + body.replace(sites, 'bench_node(1, 2, 8)') + tree[end:]
        counted = counted.replace('#include <lean/lean.h>', '#include <lean/lean.h>\n' + helper, 1)
        manifest = json.loads((CORPUS / 'manifest.json').read_text())
        case = next(c for c in manifest['cases'] if c['benchmark'] == 'binarytrees' and c['case'] == 'n-9')
        expected = CORPUS / case['expected']['path']
        assert sha(expected) == case['expected']['sha256']
        witness = diagnostic('binarytrees', counted, 9, expected.read_bytes())
        maximum = 9
        expected_nodes = (2 ** (maximum + 2) - 1) + (2 ** (maximum + 1) - 1)
        expected_nodes += sum(2 ** (maximum - d + 4) * (2 ** (d + 1) - 1)
                              for d in range(4, maximum + 1, 2))
        assert witness['observed']['node_allocations'] == expected_nodes == 51550
        witness['expected_node_allocations'] = expected_nodes
        witness['allocation_sites'] = 'Two dynamic node allocations, including every leaf; no shared node or subtree.'
        witness['lifetime_review'] = ('Generated main consumes and decrements the stretch root before creating the long root. '
            'The long root remains live across task creation and ordered joins, then is checked and decremented. '
            'The manyTrees recurrence checks and decrements each temporary root before recurring.')
        _, _, main_body = function(tree, '_lean_main')
        (args.output / 'binarytrees-main.generated.c').write_text(main_body + '\n')
        report['binarytrees'] = witness
        pi = Path(build['profiles']['pidigits']['generated_c']).read_text()
        divisions = [line for line in pi.splitlines() if '= lean_int_ediv(' in line]
        assert len(divisions) == 2
        (args.output / 'pidigits-divisions.generated.txt').write_text('\n'.join(divisions) + '\n')
        report['pidigits'] = dict(independent_extraction_division_calls=divisions,
            review='Separate 3*q+r and 4*q+r runtime divisions precede agreement testing and emission; arbitrary Int spigot state remains in Lean.')
        fann_source = Path(build['source_directory']) / 'fannkuchredux.lean'
        if 'unsafe def chunk' in fann_source.read_text():
            fann = Path(build['profiles']['fannkuchredux']['generated_c']).read_text()
            start, end, body = function(fann, 'l_enumerating')
            header = body.split('{', 1)[0]
            params = re.findall(r'(v_\w+_)', header)
            n, _, p = params[:3]
            lines = [line for line in body.splitlines() if '= l_flipping(' in line]
            assert len(lines) == 1
            body = body.replace(lines[0], f'bench_visit({n}, {p});\n' + lines[0])
            helper = '''
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
static _Atomic unsigned char bench_seen[362880];
static _Atomic unsigned long long bench_visits, bench_duplicates, bench_invalid;
static void bench_visit(size_t n, lean_object* p) {
  if (n > 9 || lean_sarray_size(p) != n) { atomic_fetch_add(&bench_invalid, 1); return; }
  size_t rank = 0; unsigned mask = 0;
  for (size_t i = 0; i < n; i++) {
    unsigned x = lean_byte_array_uget(p, i);
    if (x >= n || (mask & (1u << x))) { atomic_fetch_add(&bench_invalid, 1); return; }
    mask |= 1u << x;
    unsigned smaller = 0;
    for (size_t j = i + 1; j < n; j++) smaller += lean_byte_array_uget(p, j) < x;
    rank = rank * (n - i) + smaller;
  }
  atomic_fetch_add(&bench_visits, 1);
  if (atomic_exchange(&bench_seen[rank], 1)) atomic_fetch_add(&bench_duplicates, 1);
}
__attribute__((destructor)) static void bench_perm_report(void) {
  unsigned long long distinct = 0;
  for (size_t i = 0; i < 362880; i++) distinct += atomic_load(&bench_seen[i]);
  fprintf(stderr, "{\\"visits\\":%llu,\\"duplicates\\":%llu,\\"invalid\\":%llu,\\"distinct\\":%llu}\\n",
      atomic_load(&bench_visits), atomic_load(&bench_duplicates), atomic_load(&bench_invalid), distinct);
}
'''
            counted = fann[:start] + body + fann[end:]
            counted = counted.replace('#include <lean/lean.h>', '#include <lean/lean.h>\n' + helper, 1)
            witnesses = []
            for size in [8, 9]:
                baseline = subprocess.run([str(ROOT / 'experiments/lean4/.build/native-v1/fannkuchredux'), str(size)],
                                          capture_output=True, timeout=180)
                assert baseline.returncode == 0 and baseline.stderr == b''
                witness = diagnostic('fannkuchredux', counted, size, baseline.stdout)
                assert witness['observed'] == dict(visits=math.factorial(size), duplicates=0,
                    invalid=0, distinct=math.factorial(size))
                witnesses.append(witness)
            report['fannkuchredux'] = dict(witnesses=witnesses,
                review='Factoradic starts partition [0,n!) into eight disjoint consecutive ranges; each local counter decreases once per processed permutation. Independent lexicographic ranks witness every n=8/9 permutation exactly once. Flips execute prefix swaps in Lean and contribute signed checksum and maximum.')
        else:
            report['fannkuchredux'] = dict(review='Retained serial carry enumeration visits permutations in benchmark order; each permutation executes prefix flips and contributes checksum and maximum. Bounded n=0..8 outputs match references.')
        report['other_workloads'] = ('All application algorithms remain in Lean. Mandelbrot computes every pixel with up to 50 strict Float iterations; '
            'spectral norm computes 40 matrix-vector products; N-body performs all pair updates and time steps. '
            'FASTA, parsing, nucleotide rolling counts and reverse complement perform complete required input/output work. '
            'C supplies only generic fixed-point formatting and generic PCRE2 compile/next-match leaves, counted in normalized LOC.')
        assert all(sha(p['binary']) == p['binary_sha256'] for p in build['profiles'].values())
        report['production_binaries_unchanged'] = True
        report['status'] = 'PASSED_STATIC_AND_BOUNDED_NATIVE_ALLOCATION_CHECK'
        save()
        print(report['status'], flush=True)


if __name__ == '__main__':
    main()
