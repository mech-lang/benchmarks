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

Full standalone source/decoded output, capability denial, lifecycle and work
witness qualification remain required before admitting any new timing or
comparison. The canonical dataset and website are unchanged.
