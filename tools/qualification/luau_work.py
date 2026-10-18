"""Retain static work review and bounded allocation/permutation witnesses."""
import argparse
import fcntl
import json
from pathlib import Path

from lean_run import one, sha
from luau_run import SOURCE, BUILD, ROOT, source_pins


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output=args.output.resolve()
    args.output.mkdir(parents=True,exist_ok=False)
    pins=source_pins()
    tree=(SOURCE/'binarytrees.luau').read_text().split('local N =')[0]
    fann=(SOURCE/'fannkuchredux.luau').read_text().split('local n = assert')[0]
    assert 'return { }' in tree and 'local left, right = BottomUpTree(depth), BottomUpTree(depth)' in tree
    tree+='''
local original = BottomUpTree
local seen = {}
local allocations = 0
BottomUpTree = function(depth)
    local node = original(depth)
    assert(not seen[node], "reused tree node")
    seen[node] = true
    allocations += 1
    return node
end
local left = BottomUpTree(12)
local right = BottomUpTree(12)
assert(left ~= right)
assert(ItemCheck(left) == 8191 and ItemCheck(right) == 8191)
assert(allocations == 16382)
local a, b = BottomUpTree(0), BottomUpTree(0)
assert(a ~= b and allocations == 16384)
assert(ItemCheck(left) == 8191)
io.write("16384 distinct allocated nodes; both retained roots and distinct leaves verified\\n")
'''
    # Instrument the outer permutation loop, preserving the measured body.
    assert fann.count('  repeat\n')>=1
    fann='local visited = 0\n'+fann.replace('  repeat\n','  repeat\n    visited += 1\n',1)
    fann+='''
local checksum, flips = fannkuch(8)
assert(checksum == 1616 and flips == 22)
assert(visited == 40320)
io.write("40320 permutations visited; checksum 1616 and maximum 22 verified\\n")
'''
    witnesses={'binarytrees':tree,'fannkuchredux':fann}
    results=[]
    with open('/tmp/mech-clbg-timing.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for benchmark,text in witnesses.items():
            path=args.output/(benchmark+'-witness.luau')
            path.write_text(text)
            for mode in ('vm','jit'):
                directory=args.output/(benchmark+'-'+mode)
                r=one([str(BUILD/'luau-host'),'--'+mode,str(path.resolve())],Path('/dev/null'),directory,60)
                assert r['exit_code']==0 and r['stderr']['bytes']==0 and not r['timed_out'],r
                results.append(dict(benchmark=benchmark,execution_mode=mode,witness=str(path.relative_to(ROOT)),
                                    witness_sha256=sha(path),process=str((directory/'process.json').relative_to(ROOT)),
                                    process_sha256=sha(directory/'process.json'),output=(directory/'stdout.bin').read_text()))
    checks={
        'binarytrees':'Each recursive invocation returns a fresh Luau table, including leaves. Stretch tree is scoped and discarded; long-lived root stays live until final recursive check. Bounded identity witness verifies 16,384 distinct real nodes in each mode.',
        'fannkuchredux':'Mike Pall permutation generation and prefix flipping compute both alternating checksum and maximum. Small N=0,1,2 guards are outside the measured N=12 path. The outer-loop witness visits all 40,320 N=8 permutations in each mode.',
        'fasta':'All required 2N/3N/5N bases are generated. The random generator advances once per base with seed carried between random records; lookup tables implement the prescribed probabilities. Header, newline and remainder behavior passed the shared cases.',
        'knucleotide':'Exact THREE token, stopping at next record, comments and CR/LF handling are retained. Histograms traverse all width-1/2 windows; each query traverses all overlapping windows with exact base-4 keys up to 36 bits, below double integer precision.',
        'mandelbrot':'Every prescribed pixel iterates the escape recurrence up to 50 times; PBM row padding and tail widths passed exact bounded outputs. No image/result lookup is present.',
        'nbody':'Five prescribed bodies, momentum offset, all ten pair interactions per step, position updates and two energy computations remain in Luau with 64-bit numeric arithmetic.',
        'pidigits':'Unbounded sequential spigot computes independent floor extractions at 3 and 4 before emission. GMP bindings expose only general integer construction/arithmetic/conversion; there is no native digit or spigot operation.',
        'regexredux':'Luau orchestrates input cleaning, all nine nonoverlapping counts and the five ordered replacements. PCRE2 bindings expose only general compile/find/replace operations, with compilation inside each fresh process.',
        'revcomp':'Luau handles records, comments, case-insensitive IUPAC mapping, reverse traversal, output wrapping and invalid-byte rejection. No host reverse-complement or table translation operation is present.',
        'spectralnorm':'Luau evaluates the coefficient function and all matrix/vector products for ten AtAv pairs, with independent result arrays and the prescribed final quotient and square root.'}
    report=dict(schema='luau-required-work-review.v1',status='PASSED',sources=pins,checks=checks,
                witnesses=results,shared_bounded_report='experiments/luau/bounded-v1/report.json',
                scope='Static source review plus bounded native/VM witnesses; diagnostic elapsed times are not benchmark samples.',
                benchmark_samples=0,chart_admission=False)
    (args.output/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],workloads=len(checks),witnesses=len(results))))


if __name__=='__main__':
    main()
