# Bounded native qualification result

The [third exclusive attempt](attempt-v3/report.json) passed bounded output and
required-work checks on 2026-10-20. Its SHA-256 is
`b4d6b69563dd4faaa6f68eae30e61aaa389b8ce7bfdd1d6462d1cc9b6ba7db76`;
the [exact execution plan](native-plan-v3.json) has SHA-256
`a37543b7ee0390ea482915c0d94396bead134f0e55d8a8bd223a5ebfa317a4fd`.
The process exited successfully and released the common mutex. No native job
remains active from this packet.

All six normal applications and their six separate witness twins compiled with
the exact pinned Nim 2.2.12 / Clang 22.1.8 flags and no unreviewed diagnostic.
The independent pure-function string/character probe also compiled and passed.
The untouched original runtime and relevant external build pins matched again
at completion. [Earlier failures and their corrections](ATTEMPT-REVIEW.md)
remain preserved; the original controller, helper, protocol and candidate
source proposals were not rewritten.

The completed checks comprise 48 exact complete outputs for `n = 1..8`, 36
exhaustive detailed work observations for `n = 1..6`, 32 arbitrary-rank interval
checks at `n = 6`, and 30 honest invalid-argument rejections. The retained
`1 <= n <= 12` source contract remains unchanged; `n = 0` is not claimed to
pass the shared successful empty-summary extension. Ten offline regression
methods passed before the third attempt.

| Across all detailed `n = 1..6` runs, per source | Each retained parent | Each guarded candidate |
| --- | ---: | ---: |
| Permutations visited | 873 | 873 |
| Scratch-copy source operations | 873 | 719 |
| Zero-first permutations | 154 | 154 |
| Actual prefix reversals | 2,425 | 2,425 |
| Actual endpoint swaps | 4,128 | 4,128 |

Every rank, permutation, rotation counter, reversal bound, post-swap state,
permutation flip count, checksum sign, running checksum and maximum matched
the independent trace oracle. The observed scratch-copy difference is exactly
the zero-first count. Bounded native thread traces recorded 132 successful
creates and 132 joins, no more than eight counting workers per process, exact
interval coverage, and no surviving process group. These checks cover the
actual bounded lifecycle; no injected native worker-failure test is claimed.
All complete and diagnostic trace files together occupy 1,689,617 bytes.

## Emitted-code observations awaiting independent approval

The normal generated C for the guarded byte-array variant declares twelve
`NU8` elements for permutation and scratch state; factorials, rotation counters,
ranks, checksum and result fields remain `NI`. Its guard precedes the separate
scratch array initialization and value copy. The int variants retain twelve
`NI` elements. The generated copy is a fixed-array `nimCopyMem` operation,
with no alias to the generator. Detailed witness state also remains unchanged
after every scratch reversal.

The normal standard-library reversal emits the ordinary two-endpoint load and
stores, then moves both integer endpoints, retaining index/overflow checks.
It contains no permutation generator, checksum, or benchmark-specific kernel.
In generated C it remains an external helper call; helper-call and check costs
are hypotheses for a future pilot, not measured conclusions. No C heap
allocation is introduced by this reversal/copy loop. This observation does not
measure whole-program heap activity or machine-level copy frequency, and the
untimed trace's extra allocations are not normal-program evidence.

Review the full saved application C, compiled library C and disassembly before
approving the emitted-code gate:

- [Byte-array application C](attempt-v3/generated-c/normal/parallel-byte-reverse/@mfannkuch.nim.c),
  SHA-256 `d68c691a4b69414168274c6940f7387ea87d0fabb0c8411aad161d5ee1801615`.
- [Byte-array standard reversal C](attempt-v3/generated-c/normal/parallel-byte-reverse/@palgorithm.nim.c)
  and [normal disassembly](attempt-v3/machine-code-normal-parallel-byte-reverse/stdout.bin).
- [Guard-only application C](attempt-v3/generated-c/normal/parallel-guarded-copy/@mfannkuch.nim.c),
  SHA-256 `5093e3651cb942c1c0ce9e3ed9d29caa37fb933dfb9e6180e871c030712e77a3`.
- [Parallel library-expression C](attempt-v3/generated-c/normal/parallel-reverse-guarded/@mfannkuch.nim.c),
  SHA-256 `fe6127e5a18e35aee10825c670ddd14a4836c39ef4376cc6fc9e8bf72fa750ec`.
- [Compact library-expression C](attempt-v3/generated-c/normal/compact-reverse-guarded/@mfannkuch.nim.c),
  SHA-256 `b4a8681c5d04af4e5ee4d7d4dee5d5d6c4ec6b2ef923ca252f6c412693e8e9d5`.

Independent emitted-code approval and native source-owner/count qualification
remain separate gates. All application LOC proposals remain null/unapproved in
their frozen ledgers. There is no quantitative pilot, full `n = 12` measurement,
new speed ratio, chart point, globally optimal claim or canonical catalog
change from this bounded result.
