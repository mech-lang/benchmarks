# BQN spectral-norm native sum results

Measured 2026-10-20. All21 bounded checks and9 full checks pass; chart admission is separate. The exact parent is `archive/comparisons/array-comparison/all-20261009/sources/spectralnorm-faithful.bqn`, SHA-256 `5e6955104b07d3c2fdda9b5ee29c80ced059c064bd386db33d941f6c2b29d380`. Its retained historical median is 2.166914167 seconds and retained application LOC is 13; these historical facts are not observations of this new runtime. The selected parent is a retained faithful local adaptation with unresolved predecessor origin. The separately retained original `spectralnorm.bqn` is untouched.

`sources/parent-faithful.bqn` is a byte-identical control. `sources/row-sum.bqn` changes exactly the two row reductions in `Av` and `Atv` from `+´` to `•math.Sum`. `sources/row-and-dots-sum.bqn` also changes the two final dot-product reductions. The original comment, coefficient expression, function boundaries, vector traversal, application count, output expression and command-line parsing remain exact. The preparation routine reconstructs each candidate from the hash-checked parent and rejects any other source change. Exact candidate hashes and unified diffs are recorded in `plan.json`.

The hypothesis is specific to the pinned runtime: CBQN `src/builtins/fold.c:26` describes `•math.Sum` as faster and more precise SIMD code for i32/f64, and `sum_c1` at lines 181–211 calls `si_sum_f64` for floating-point lists when Singeli is enabled. In contrast, the ordinary f64 fold helper at lines 125–127 accumulates elements in reverse scalar order. The saved release receipt identifies Singeli AARCH64. This is an ordinary language runtime primitive; there is no FFI import, workload helper, rebuilt runtime, new library or direct native benchmark executor. See the [pinned CBQN source](https://github.com/dzaima/CBQN/blob/c893d3e7828899a50150df03ad33c9052fa51d3c/src/builtins/fold.c#L181). Local checked-out source was inspected; the web fetch of that exact GitHub revision was unavailable in this review.

The [current task description](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/spectralnorm.html) requires the same spectral-norm algorithm and four separate functions, and gives 5500 as the performance argument. All variants preserve `A`, `Av`, `Atv`, and `AtAv` as separate functions. `AtAv⍟19` followed by the final `AtAv` performs 20 applications, each containing two matrix-vector products: 40 products and `40*n*n` coefficient evaluations. No matrix is retained or precomputed. Each row still materializes and sums its actual coefficient-weighted vector. The application starts no workers and retains the parent's single-process execution. Summation order can change low bits; exact bounded and full output are prerequisites, not assumptions. This experiment does not establish global optimality, nor select a new small endpoint or source-count claim.

`run_serial.py --prepare` only hashes/reads evidence and writes the plan; it does not launch native processes. The pinned executable is the existing uninstrumented release `experiments/bqn/optimization-v1/.build/CBQN/BQN`, SHA-256 `0d39846db5f4727c59e6cb652328481e5d4c80d1bce28158172bd0c71d7305d5`, CBQN commit `c893d3e7828899a50150df03ad33c9052fa51d3c`. The release receipt and linked libffi are pinned; spectral-norm does not import the k-nucleotide support library or GMP/PCRE bindings. The retained process helper is `tools/qualification/lean_run.py`, SHA-256 `313418c88aae0de3c86a98566c6138bbaeeb697830da99c9cc1ad5c7be0737ec`.

Reproduce serially from the repository root while other benchmarks, compilers and browsers are stopped:

```sh
python3 experiments/bqn/spectral-sum-v1/run_serial.py --mode bounded --output experiments/bqn/spectral-sum-v1/bounded-v1
python3 experiments/bqn/spectral-sum-v1/run_serial.py --mode full --bounded-report experiments/bqn/spectral-sum-v1/bounded-v1/report.json --output experiments/bqn/spectral-sum-v1/full-matched-v1
```

The bounded run executes all three exact sources on the seven shared cases n=1,2,3,5,9,10,100 and compares complete stdout bytes with the pinned independent corpus. The full run requires that exact successful bounded report, executes all three sources in three deterministically shuffled rounds with fresh `[BQN, source, "5500"]` processes, and requires exactly 12 stdout bytes with SHA-256 `f9d5b5e3eb7657cf1bbba4cc856651864df9cd9fd9a6be9b9bc5fcbb67150deb`. Every run uses the common nonblocking timing mutex and checks AC power with low-power mode off before and after each process. Source/runtime/support/reference hashing and validation happen outside the measured process interval. Reports retain all attempts, raw process receipts, stdout, stderr, source snapshots, controller snapshots, sample order, power checks, source/runtime hashes and plan identity. Invalid output stops the cohort without an automatic retry. A fresh directory is required for every cohort. Canonical data, the frozen k-nucleotide controller and approved Nim source ledger are unchanged.

## Repeated full-size result

All three variants have three fresh complete-process samples in
[full-matched-v1/report.json](full-matched-v1/report.json). Exact complete stdout
passes for every run; all seven [bounded cases](bounded-v1/report.json) also pass
for every source.

| Variant | Median seconds |
| --- | ---: |
| parent-faithful | 2.186282 |
| row-sum | 1.513197 |
| row-and-dots-sum | 1.540136 |

Replacing the row reductions yields a matched 1.44× speedup.
The two extra final-dot replacements do not show a benefit exceeding this
small sample's spread, so the simpler two-replacement source is preferred.
This is an ordinary runtime-primitive improvement with all40 coefficient
evaluating products retained. It does not establish a global optimum.

The sealed pre-run review remains in REVIEW.md with the exact digest recorded in the plan. Results and explanatory updates are kept in this separate file.
