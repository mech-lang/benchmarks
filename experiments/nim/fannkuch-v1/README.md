# Nim fannkuch: in-place library reversal and bounded array state

This is an unexecuted source proposal. No Nim process, compilation, test,
benchmark, catalog edit or retained-source edit was performed. The four new
applications preserve the retained permutation generator and all nonzero flip
work. Their syntax, emitted code, correctness, source counts and performance
still require qualification. [The plan](plan.json) binds the exact parents,
candidate sources, proposed owner ledgers, library and retained build receipts.

The retained compact and threaded sources already use `array[12, int]` for
permutations and scratch state. There is no sequence allocation to remove.
Their saved medians are 20.779141792 and 3.5549 seconds respectively, from the
historical cohort. These numbers provide context for choosing experiments;
they are not fresh controls or evidence of a new speedup.

| Candidate | Change relative to its retained parent | Proposed retained / physical LOC |
| --- | --- | ---: |
| `compact-reverse-guarded` | Serial parent; guard scratch copy; use existing in-place `reverse` | 31 / 31 |
| `parallel-guarded-copy` | Threaded parent; guard scratch copy; keep written swap loop | 72 / 65 |
| `parallel-reverse-guarded` | Threaded parent; guard scratch copy; use existing in-place `reverse` | 67 / 60 |
| `parallel-byte-reverse` | Previous variant; change permutation and scratch elements to `uint8` | 67 / 60 |

The first candidate tests a smaller ordinary Nim expression. The three parallel
variants isolate copy avoidance, library expression and representation changes.
No candidate is described as faster before it is measured. The original
compact and parallel applications are also copied byte for byte into `sources/`
as future controls. Their original locations remain unchanged.

## Required work and the copy guard

Every variant visits the same global permutation ranks in the same order within
its assigned interval, performs the same canonical prefix rotations, computes
the same parity-signed checksum contribution, and includes each permutation in
the maximum. The threaded variants retain the same factoradic interval seeds,
eight contiguous worker ranges, creation/join operations and result reduction.
This follows the [Game task's algorithm and checksum requirement](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/fannkuchredux.html).

When a permutation starts with zero, the retained flip loop executes zero
iterations. The new guard leaves `flips` equal to zero and skips only the unused
scratch copy and that zero-iteration loop. It still updates the checksum and
maximum and advances the permutation generator. For `n = 12`, there are
479,001,600 permutations, of which 39,916,800 start with zero. Thus the proposed
scratch-copy count is 439,084,800. These are mathematical expectations, not
dynamic work-witness results. No flip count is cached or reused, and no nonzero
flip sequence is skipped. At `n = 1`, the only permutation has zero flips and no
scratch copy is needed.

The exact restored Nim 2.2.12 `std/algorithm.reverse` implementation at lines
101–121 reverses an inclusive range by swapping its two endpoints until they
meet. It is an existing general-purpose helper. It does not implement the
permutation generator, checksum, flip-until-zero loop or any other whole
benchmark operation. The candidate calls `reverse`, whose array is passed by
`var`; it does not call `reversed`, which returns a newly allocated sequence.
The standard [API documentation](https://nim-lang.org/docs/algorithm.html#reverse%2CopenArray%5BT%5D%2CNatural%2CNatural)
and the [exact pinned source](https://github.com/nim-lang/Nim/blob/8e8fbf60693418dc95bb0d762fd660231d08a583/lib/pure/algorithm.nim#L101-L121)
support this distinction. An unchanged copy of the module and its MIT license
are retained under `vendor/nim-2.2.12/` for review; future builds must load the
actual pinned distribution rather than treating this review snapshot as an
application helper.

The byte-array variant stores only values from zero through eleven in
`uint8`. Factorials, rotation counters, ranks, checksum and result types remain
machine integers. Initialization converts each value explicitly, and the
reversal bound converts the selected element back to `int`. This keeps index
intent clear and avoids changing checksum arithmetic. On the retained 64-bit
target, the source types describe 12 bytes of element storage rather than 96;
generated C and machine code must establish the actual copy and access behavior.
There is no claim yet about native allocation, vectorization or instruction
count. Range and bounds checks remain enabled under the same retained settings.

## Source ownership and provenance

Each candidate's entire single source file is application code, including input,
thread orchestration, factoradic seeding, generator, flips, reductions and
output. The existing general standard-library reversal remains vendor support.
No authored workload helper or native benchmark kernel is excluded from a
source count. [The owner ledgers](source-ownership-v1/README.md) assign every
written row under an exact-source extension of the retained Nim convention.
The proposed values in the table are unapproved; `application_loc` is null and
`independent_review_approved` is false. This is not a new uniform logical-source
metric or evidence of native frontend acceptance.

The inherited sources remain `local-origin-unverified`. References to community
collections do not prove an unchanged submission match, establish per-line
original authorship, or resolve all inherited terms. The new changes are
suite-authored in this audit by the current Codex GPT-6 family agent; the exact
model version is unknown. No original model or author is inferred from missing
citations. All old source bytes, citations and measured results are preserved.

## Qualification gates before timing

1. Build both parents and all four candidates with the exact restored Nim
   2.2.12 compiler and retained C backend, release, ORC, thread, SDK and numerical
   flags. Record actual versions, all commands/environment, compiler-loaded
   sources, warnings, generated C, executables and linked dependencies. Retain
   each failed attempt. Do not change CPU targeting or disable checks while
   comparing these source edits.
2. Check exact argument/output behavior for `n = 1` through `8` against the
   independent shared reference and both freshly built parents. Do not use an
   experiment's implementation as the independent oracle.
3. In untimed source-bound twins, compare the rank, full permutation, every
   prefix-reversal bound and post-reversal state, per-permutation flips,
   checksum sign, rotation counters and maximum. Cover all small permutations,
   arbitrary single-rank intervals, odd starts, factorial boundaries and each
   actual worker interval. Verify every rank occurs once with no gaps/overlap,
   and that the guard's scratch-copy count has exactly the expected difference.
   A candidate's final checksum alone does not certify the required work.
4. Inspect generated C and representative machine code for array value-copy
   semantics, byte element storage, real in-place reversals and bounds handling.
   Confirm the scratch array cannot alias the generator and result pointers
   remain live through all joins. Count performed flips or swaps only from
   actual evidence, not from a shortcut recurrence or an output match.
5. After root grants a quiet window, use a separately sealed `n = 10` pilot
   before selecting full `n = 12` comparisons. Full admission needs three
   shuffled whole-process observations per selected source, exact full outputs,
   the required-work evidence, independently approved source counts, and an
   additive importer preserving every historical profile and raw observation.

The eight static chunks may still be imbalanced. Testing more bounded jobs over
eight persistent workers is a separate scheduling experiment. Narrowing rotation
counters, rewriting the frequent first-two rotation, changing task boundaries,
removing checks, changing compiler flags and adding unsafe code are deliberately
outside this source proposal. No globally fastest or smallest claim follows
from these candidates.
