# Native Bins proposal for BQN FASTA

Source-only preparation, 2026-10-20. No BQN, compiler, benchmark, test or executable modification is part of this stage. Exact source/test hashes, parent identity and planned cases are in `plan.json`.

The retained parent is `archive/comparisons/array-comparison/all-20261009/sources/fasta.bqn`, SHA-256 `531d039ae5f9aa34f9db35e4df9efc723dc64098e3b1828c7b4fba972e35085e`. Its historical median is 10.785043417 seconds and retained count is24/24. Those facts do not establish a result for these candidates or the rebuilt runtime. `sources/parent-faithful.bqn` is an exact byte copy; the original is unchanged.

`sources/bins-only.bqn` changes only parent line17:

```bqn
indices ← cumulative ⍋ r÷139968
```

This replaces a fifteen-by-sample or four-by-sample boolean outer-comparison result, transpose and row sum with ordinary Bins. [BQN's definition](https://mlochbaum.github.io/BQN/doc/order.html#bins) counts sorted left cells earlier than or equal to each right cell. Therefore, for these finite numeric vectors, `cumulative ⍋ sample` is exactly the number of cumulative thresholds satisfying `threshold≤sample`, preserving the parent's strict upper-bound selection even at equality. Both cumulative vectors are ascending because their original probabilities are positive. Floating division, cumulative addition order, original probabilities, alphabets and sample values remain exact source expressions.

The [current FASTA task](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/fasta.html) permits linear or binary search against cumulative probabilities, and requires the naive LCG on each random selection. It forbids scaled lookup transformations and cached random sequences. This proposal uses ordinary binary search over the unscaled floating thresholds. It retains `139968|29573+3877×seed`, every scan element, and the division by139968. No integer cutoffs, state-to-letter table, period reuse, skip-ahead seed, parallel random subsequences or new native helper is introduced. All200,000,000 random selections remain at full N=25,000,000; fixed ALU repetition and output wrapping are unchanged.

There is a runtime-specific reason to expect a useful candidate, without a timing claim. In the pinned CBQN commit `c893d3e7828899a50150df03ad33c9052fa51d3c`, `src/builtins/grade.h:587–630` dispatches same-width f64 inputs to Singeli Bins and selects an i8 result for fewer than128 thresholds. `src/singeli/src/bins.singeli:315–342` performs interleaved branchless binary search, comparing the actual values. Lines344–363 restrict the integer-table paths to i8/i16; f64 uses the binary path. Thus this exact floating-point call does not enter a dense integer-state lookup. The application creates no threshold-scaling or workload-specific table. See the [pinned implementation](https://github.com/dzaima/CBQN/blob/c893d3e7828899a50150df03ad33c9052fa51d3c/src/singeli/src/bins.singeli#L315). Source was inspected locally. The existing rebuilt release executable remains SHA-256 `0d39846db5f4727c59e6cb652328481e5d4c80d1bce28158172bd0c71d7305d5`.

Static review also found a zero-size trap in the parent: line15 unconditionally picks the last element of `r`, even when n=0 makes `r` empty. This is an expected bounds failure from the source, not a newly observed execution. `sources/bins-empty-safe.bqn` keeps the Bins change and separately guards that seed update:

```bqn
seed ↩ {0<≠𝕩? ¯1⊑𝕩; seed} r
```

An empty random record leaves the seed unchanged and still passes an empty selection through existing wrapping. Positive records take the original last generated state, preserving the TWO→THREE continuation. This is the proposed complete-domain candidate; the one-change source isolates lookup cost. No source count is claimed for either changed file until an exact-source retained-rule review. The zero-case guard does not generate or cache any random values.

Planned qualification, after root opens a serial execution window:

1. Run `tests/lookup-equivalence.bqn` under the exact release runtime. It compares Bins with the parent's outer-comparison reduction for **all139,968 possible normalized integer states**, separately for both original probability vectors; it also checks duplicates, exact threshold equality, values on either side and empty right input. This is an untimed test domain, never a production random lookup table.
2. Run every one of the16 shared FASTA cases, n=0,1,2,19,20,21,29,30,31,59,60,61,287,574,1000,20000, against their exact independent complete outputs. Keep the parent's observed n0 failure if it occurs; do not silently retime or rewrite its source. Require the empty-safe candidate to pass all16 cases. Preserve all headers, line lengths, final newline and record-boundary seed continuation.
3. Before performance admission, run fresh full N=25,000,000 processes and validate the entire254,166,745-byte output against SHA-256 `3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa`. Use the shared timing mutex, power gates, source/runtime/controller snapshots and three shuffled matched rounds. No timing runner is created or invoked here.

The hypotheses concern native search dispatch, comparison work and allocation. A result could instead be limited by the sequential LCG scan, division, wrapping or output. Keep a compact alternative and inspect measured whole-process behavior before claiming a speedup. The new source is a local adaptation of an origin-unresolved predecessor; an uncited parent is not evidence of original authorship or a specific model.
