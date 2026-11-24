Continue Mechdeflate optimization from this handoff. The objective is **1× libdeflate runtime across all 81 benchmark cases**, while preserving every current named **81/81 Roc win and 63/81 libdeflate win**. The strategy is now to **reduce the average losing margin across the fixed 18 cases below**. Improvements across a family of inputs count as progress even before another case crosses parity.

**Source and evidence to use**

- Compiler source: [`09d4ea14c9a560d91d5e6ff9404dcde4655408f6`](https://github.com/mech-lang/mech/commit/09d4ea14c9a560d91d5e6ff9404dcde4655408f6), in [Mech PR #995](https://github.com/mech-lang/mech/pull/995). This is source another agent can rebase on. Check the current PR head before changing a shared branch.
- Measured evidence: [`98ebf05a58c0bbadde221336d93bae33b7e2df23`](https://github.com/mech-lang/benchmarks/commit/98ebf05a58c0bbadde221336d93bae33b7e2df23), in [benchmarks PR #11](https://github.com/mech-lang/benchmarks/pull/11). The sibling [masked-field packet](../mechdeflate-masked-fields-v1/README.md) contains source build/probe scripts, exact recipes, all timings and raw observations.
- **Use recipe `control` as the starting primary.** It is the previous `keep-pairs2` recipe, reproduced exactly by the current compiler source. The new `tied-*` field-insert recipes are retained alternatives with mixed runtime, not the selected primary.
- The stack is #973 → #975 → #994 → #993 → #995. Another agent has worked on compilation speed in #973; preserve that work and avoid overwriting unrelated changes. Benchmark records belong in `mech-lang/benchmarks`; do not restore the moved `mech/benchmarks` tree.

**Primary progress metric**

Use the exact 18 names in [baseline.json](baseline.json), with equal weight per named case. For case `i`, let `r_i` be Mech time divided by libdeflate time, computed as the geometric mean of its balanced forward and reverse paired ratios. Lower is better.

```text
average loss margin (%) = (100 / 18) × Σ max(0, r_i − 1)
```

The current baseline is **13.923364% average positive slowdown**. Because all 18 cases currently lose, their arithmetic mean time ratio is **1.139234× C**. Their geometric mean is **1.136666× C**; the companion average using each case's worse order is **14.416442%**.

Keep the cohort and denominator fixed. A newly won case stays in the cohort and contributes zero. Further gains on that winner do not offset unresolved losses elsewhere. Do not drop difficult cases, silently deduplicate named aliases, change weights, or replace this metric with the whole-suite geometric mean. Report the per-order results and maximum remaining gap alongside the average. All 81 cases remain the final qualification scope.

Use a freshly measured matched control and candidate on the same host with the same pinned peers. Compare their average loss margins in **percentage points**. The M1 numbers above are a reference, not a substitute for a fresh baseline on another machine. A 10-percentage-point reduction in one case lowers this average by 0.556 points, even if it remains a loss.

**Where to look first**

The six largest gaps account for **56.35% of the total current loss margin**:

| Case | Paired Mech/C | Slower |
|---|---:|---:|
| `prefix-random-4096` |1.327780×|32.78%|
| `prefix-random-8192` |1.276152×|27.62%|
| `prefix-natural-1024` |1.208397×|20.84%|
| `reymont-prefix-1024` |1.207418×|20.74%|
| `prefix-random-16384` |1.206008×|20.60%|
| `16384-distribution-change` |1.186582×|18.66%|

The two natural/reymont 1 KiB names are distinct scored cases; inspect their input hashes and share profiling work where inputs coincide. The 32 KiB boundary group is another useful family. The closest case, random 1 MiB at 1.029984× C, remains relevant, but a 64th win is an intermediate milestone rather than the experiment-selection rule. Prefer the change expected to remove the most total positive margin across the cohort.

Profile complete invocations across all 18 losses before choosing another narrow optimization. Separate setup/admission, scratch allocation or clearing, literal/histogram work, matching, Huffman/scorer work, output and cleanup. Compare several input sizes to identify fixed per-call overhead versus work that scales with bytes. Use actual phase counts and sampling to locate shared costs. Hoisting validation, initialization reuse, bounds proofs, data layout and instruction selection are hypotheses to test; preserve their admission, alias and error guarantees.

**Lessons and retained work**

- Recent masked-field lowering removed **2,088,774 matcher instructions** on random 1 MiB. Target runtime was effectively flat; distribution-change 16 KiB became **4.9–5.2% slower**. Its average loss margin is **14.391431%**, worse than the matched primary's **13.923364%**, despite preserving all named wins. Smaller code or fewer instructions alone is insufficient under this strategy.
- The masked, widened-copy, tied and square-root profile variants are retained with exact source recipes and evidence. Do not discard a promising candidate because one case regresses: isolate the cause, repair it, and combine it with other advances. Keep the qualified primary until promotion gates pass.
- BFI latency or tied-allocation/frame effects are possible causes, not established facts. A bounded shifted-ORR form is worth a controlled native-loop comparison if the new profiles justify it. Do not spend another round on it merely because it emits fewer instructions.
- Earlier FP spill caching split a hot LDP and added about a million instructions. Pair-preserving mirrored cells repaired that. Keep the actual paired reloads and prefetches when combining changes. Repeatedly changing FP slot counts without new evidence is not the next strategy.
- Read the history and saved partials before rejecting an approach already tried. The hot `0xffff` masks require tracing every SSA incoming definition; physical register reuse is not a proof. Inspect constant-retention/rematerialization history before changing the repeated multiplier setup.

Relevant source includes `hosts/gpu/src/native_artifact/program/codegen/`, its `cfg_cleanup` passes, and `vendor/cranelift-codegen/src/isa/aarch64/` (`lower/isle/bit_fields.rs`, narrow/word extension rules and `fp_spill_cache.rs`). Start from measured costs rather than assuming these particular files are the bottleneck.

**Reproduce and score**

From the sibling masked-field packet:

```sh
python3 reproduce.py --mech-root /path/to/mech --output /tmp/mech-primary --role control
python3 probe.py --mech-root /path/to/mech --output /tmp/mech-native-proof
python3 verify.py
```

The source compiler is built from the supplied Mech checkout. The archive is in three parts; `verify.py` reconstructs it and checks every part. The raw manifest maps archived timing controllers, fixtures, source bindings, counters and outcomes to content hashes. Use the published source and fixtures on another machine; private `/private/tmp` directories are not prerequisites.

From this handoff directory:

```sh
python3 score.py
python3 score.py --results /path/to/full81-results.json --actor mech-control
python3 score.py --results /path/to/full81-results.json --actor mech-experiment
python3 score.py --forward /path/to/forward/summary.json --reverse /path/to/reverse/summary.json
```

`score.py` accepts the combined controller format with two `runs`, or two saved summary arrays. It reports the fixed-cohort metric, each case's contribution, matched-control improvement and protected named wins. For discovery, add `--discovery`; all 18 cohort cases are still required, and the output cannot claim full qualification. Expand discovery panels to all 18 losses plus fragile existing wins. The older six-case screen is insufficient for this strategy. The scorer was checked against actual saved full-suite results; it does not replace correctness gates or independently validate a timer's sampling protocol.

**Promotion and constraints**

- Require a reproducible reduction in the matched average loss margin. Small slowdowns in individual cases are allowed. Do not require every case to match its previous nanosecond timing.
- Preserve every protected named Roc and C win in both full **81-case /96-block** orders. Lists are in `baseline.json`. A gain elsewhere does not excuse losing an existing protected win. After adding a qualified win, add it to the protected floor; keep the original 18-case optimization cohort.
- Preserve the original idiomatic **2,719-line codec** at `hosts/gpu/tests/fixtures/native/compact-compiler-regression.mec` and its canonical bytecode. No codec rewrite, new LLVM dependency, shipped native-byte patch, runtime dispatch by benchmark identity, interpreter substitution or weaker finite admission.
- Read `hosts/gpu/src/native_artifact/AGENTS.md`. Maintain direct efficient Bool/U64/I64/F64 execution, checked errors and private witness construction. Do not retire the efficient scalar entry without its required replacement and latency/allocation proof.
- Check independent output inflation, exact Mech/Roc bytes, input/output aliases, six named errors, recovery and cleanup. Established native gates record 162 success observations and 12 recovery pairs per image. Keep the **5,280 B stack cap**. Run the appropriate native/checker tests for changed code; full GPU/CI is not implied by those checks.
- Freeze Rust during any live source producer. Keep builds, tests, counters, profiles, Git and archiving out of primary runtime and complete-build clocks. Counters instrument diagnostic images; time the original images. Refresh allocation/layout profiles when lowered VCode changes rather than reusing a stale profile identity.
- Track encoder text, lookup data, the whole const section, stripped executable and peak stack. Measure fresh original-source-through-final-executable-link builds with compilers and fixed support equally prebuilt for Mech, Roc and C. Keep compiler construction and stripping separate. Do not compare an executable build to an archive-only or object-only build.
- Publish compiler source in a reviewable PR and data/commands in the benchmark PR. Provide source and evidence commit links, exact roles, all margins and both order results. Preserve partials with their actual failures and planned repairs. Do not leave the only usable result in a local directory. Do not spawn subagents without explicit authorization.

The current primary has **63,720 B encoder text**, **3,200 B lookup data**, **17,728 B whole const**, **210,024 B stripped executable**, and **4,832 B stack**. Current matched complete builds are **2.195 s Mech /2.987 s Roc /0.483 s C** on **Apple M1 / macOS 15.6.1 / arm64**. New smaller qualified alternatives reach 63,672 B but have mixed runtime and 4,848 B stack. Track these dimensions while pursuing the runtime metric; they are not replacements for it.

At each checkpoint report: average margin before/after and percentage-point reduction; all 18 paired ratios/timings and changed contributions; Roc/C score and protected-win status in both orders; matched build time, sizes and stack; source/evidence links. A lower average with the same 63 wins is valid progress. Completion still requires parity across **all 81 cases**, with the full correctness, source and admission guarantees maintained.
