# Hash-table-preserving native windows

The [nucleotide workload](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/knucleotide.html)
requires library hash-table lookups and count updates for every window at
lengths 1, 2, 3, 4, 6, 12 and 18. Dense counters and query-only counting cannot
qualify by matching stdout alone.

The compiler candidate is on `codex/native-hashmap-window-lowering`, [PR #911](https://github.com/mech-lang/mech/pull/911), based on
`bbd66acb9b3beacdc95356084df259ca172c8b98`. Its first implementation is
`96ef05bfd`: a Cranelift loop invokes the pinned hashbrown 0.15.5 accumulator
for every overlapping ASCII window. Keys use an injective seven-bit packing
into u128, whose natural maximum width is eighteen bytes. Tables start empty,
grow through the library, and include keys never queried. Each query is read
from the completed table. Small full histograms are materialized only after
the table updates finish. Wider and non-ASCII representations retain the
ordinary canonical CFG; this record does not qualify their physical algorithm.

Every growth reserves the old-plus-replacement peak before fallible library
allocation. The actual allocation size is checked against the conservative
bound. Finite work includes collision and growth envelopes on the existing
invocation account. An allocation or work failure stops native iteration and
prevents result publication. ABI13 and work policy38 reject older objects
whose private five-word loan arguments have different meanings.

`tests-v3` passed four focused tests: generated-loop entry updates, all seven
widths against independent ordered counts, full-width/NUL keys, and denied
memory/work before table mutation. `tests-v4` additionally passed original and
decoded program execution with actual update counters. These are correctness
checks, not benchmark timing samples. `tests-v2` compiled but selected zero
tests and is explicitly not a test qualification. The earlier empty
`tests-v1` directory came from a controller directory-creation error before any
subject was launched.

`a83c2b5ff` adds persistent execution witnesses. `tests-v6` passed all 166
native regression tests (three ignored), including stale ABI/work-policy
rejection, original/decoded images, exact/one-short memory denial and cleanup.
`tests-v5` retained five failures from old counter-only comparison allowances
and hard-coded preceding ABI identities; these were corrected without removing
assertions before the successful rerun.

Full qualification passed in `qualification-v4`: source and decoded builds
produce byte-identical executables, pass twelve bounded cases and two capability
denials, and each produce the exact full 259-byte output. Every full process
reports seven completed library tables and 874,999,961 actual updates.

The first full-input policies were too small: `qualification-v2` rejected
4,166,671 input lines at its element cap, and `qualification-v3` rejected a
636,948,831-byte temporary admission. Both failures precede publication and
remain retained. The successful policy reuses the recorded standard full-input
resource caps from `canonical-knucleotide-owned-string-footprint-v1.json`,
including a 3 GiB shared physical allowance and 1 GiB temporary allowance.
Authority and binaries remain identical; only larger finite compute/comparison
bounds fund the restored collision/growth work. The original static metadata
assertion in `qualification-v1` expected seven definitions; the compiler
correctly emits two shared definitions invoked seven times. Reusing verified
successful preparation avoided rebuilding or retiming other languages.

## Matched full-input timings

`rust-comparison-v2` contains seven shuffled serial rounds, after full correctness
for both subjects. Each duration includes fresh-process startup, all input,
computation, output and shutdown; Mech also includes secured admission and report
publication. Build, integrity hashing and parent validation are excluded. These
are whole-implementation comparisons on the same machine and warm filesystem
cache, not isolated capability overhead.

| Implementation | Median seconds | × canonical secured Mech AOT | Sample SD seconds |
| --- | ---: | ---: | ---: |
| Mech AOT, canonical secured | 9.39939 | 1.00000 | 0.11519 |
| Unchanged Rust #7 | 0.54998 | 0.05851 | 0.01237 |

Mech takes 17.09× Rust's time in this cohort. Mech uses a serial accumulator;
Rust retains its original default Tokio thread pool. Retained process CPU time
divided by elapsed time gives median core equivalents of 1.00 and 4.35,
respectively. This observation does not isolate how much of the gap is caused
by concurrency, key representation, or accounting.

All sixteen cohort full outputs pass. Every measured Mech process attests all
required table updates. The protected Rust source, pinned dependency manifest
and lock remain unchanged. Cargo's JSON artifact identities select the exact
direct dependency versions; the earlier `rust-comparison-v1` correctly refused
ambiguous hashbrown filenames before launching any benchmark subject.

`seal.py` independently recomputes output hashes, process closure, medians,
standard deviations, and multiples. `artifact-index-v1.json` pins the retained
records. The older frozen Mech emitter remains byte-identical. No new profile
is admitted to the canonical dataset or website by this experiment.

Further compiler optimization must preserve every table update. Candidate
areas are native rolling window keys and amortized finite-work accounting;
these are targets for measurement, not claimed improvements.
