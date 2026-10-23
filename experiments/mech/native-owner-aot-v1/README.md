# Source-map standalone performance

This study measures a Mech state machine that explicitly traverses a String, selects each window, tests map membership, reads the previous count, inserts a caller-produced count and advances its state. The compiler retains general hash storage while compiling those operations from Mech. The current source is [knucleotide-source-map.mec](knucleotide-source-map.mec), SHA-256 `ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da`.

## Current measured improvement

Compiler [`a3b1ddfcd`](https://github.com/mech-lang/mech/commit/a3b1ddfcdf501f4bc3c6eb81a7e975849295fcc4) admits a straight-line group of native map-owner instructions once before its first instruction. Group interiors have a single predecessor and contain no library helper or loop/ownership boundary. Every source instruction is still emitted, including its original arithmetic failure location. Refused owner entry retains the canonical per-block callbacks. The full original instruction work plus group-proof overhead is prepaid on the same finite ledger. IR33, work policy50 and ABI18 identify this protocol.

The current diagnostic comparison uses the first **one million bases** of the standard THREE record. Three alternating complete-process measurements per executable give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0184 | 1.00× |
| Mech AOT before grouping, `7aa1bea1b` | 12.570 | 682× |
| Mech AOT after grouping, `a3b1ddfcd` | 9.600 | 521× |

The compiler change reduces elapsed time by 23.6%. All nine timed outputs exactly match the independent reference; Mech uses secured startup and shutdown, and each executable has one excluded warmup. Source and generated program bytecode are unchanged. Ratios use Rust measured in this same cohort; its short complete-process timings vary between runs. Raw seconds and all samples are in [map-admission-timing-v1](map-admission-timing-v1/results.json).

| Observed work on one million bases | Before | After |
|---|---:|---:|
| Runtime admission callbacks | 321,998,942 | 139,717,328 |
| Hash tables | 7 | 7 |
| Actual hash-table updates | 6,999,961 | 6,999,961 |

[Validation](../native-owner-dispatch-v1/map-admission-validation-v1) passes 213 native checks with three pre-existing exclusions. New original/decoded and restored-image tests observe fewer actual callbacks, retained canonical fallback, refusal with one unit less than the group work requirement, rejection of group replay/interior entry, exact interior arithmetic errors and complete owner cleanup. The existing 84 counting cases remain correct. Rust parity is not reached; this is not a full 125-million-base source-map result.

The [matching profiling build](profile-groups-build-v1/results.json) retains symbols with the public CLI's final-host FatLTO settings. Its entire `__TEXT,__text` section is byte-identical to the timed candidate: 3,919,368 bytes, SHA-256 `bc38c7feb54e6ece3c7dd2f58a3d814549c5e749473f61a223e2b36d7700ebc2`. Three two-second samples on the full input identify the remaining overhead:

| Path | Inclusive share across the three sample windows |
|---|---:|
| Retained map/key helpers | 59–60% |
| Generated-block admission | 35–37% |
| Native work debits, across paths | 20–23% |
| Library work debits, across paths | 18–21% |
| Selected-key projection, within the helpers | 9–10% |
| Selected range cardinality/shape validation | 8–9% |

Categories overlap and must not be added. [Reproducible analysis](full-profile-groups-v1/analysis.json) counts the union of matching stacks within each category. These samples characterize the grouped candidate; they are not a matched before/after profile. The subject was stopped and reaped at the planned 45-second deadline ([receipt](full-profile-groups-v1/results.json)), so this is not a full-input timing. Further work targets the repeated admission, map-binding and accounting checks while retaining general map storage, source-written operations and finite resource accounting.

The attempted 100,000-base Rust comparison was excluded before quantitative timing: the upstream program prints tied `AG` and `GT` frequencies in the opposite order from the required ascending-key tiebreak ([specification](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/knucleotide.html), [failed warmup](rust-span-diagnostic-v1/results.json)). The published Rust program is unchanged. The one-million-base prefix passes exact output comparison for both executables. [rust-span-diagnostic-v2](rust-span-diagnostic-v2/results.json) retains the separate first paired cohort; its Rust median is not used as a denominator for later cohorts.

## Selected String keys

Compiler [`7aa1bea1b`](https://github.com/mech-lang/mech/commit/7aa1bea1b5565113cd07ddeaeea2bed30ed84a54) borrows selected String map keys instead of materializing a range and substring on every window. Selection still uses the maintained String index, including Unicode and CRLF behavior. The compiler selects this representation only when every key use belongs to the same closed map region; an extra observer retains the canonical path. Source control flow, all hash-table updates and caller-produced counts remain unchanged. IR32, work policy49 and ABI17 identify the new representation and checked helper protocol.

Three alternating measurements per executable on the same 100,000-base prefix give:

| Mech AOT compiler | Input | Median seconds | × latest Mech AOT |
|---|---:|---:|---:|
| Parent `f6ee09e63` | 100,000 bases | 4.686 | 3.40× |
| Latest `7aa1bea1b` | 100,000 bases | 1.380 | 1.00× |

This is a 3.40× speedup, or 70.6% less wall time, on the diagnostic input. Every timed process includes secured startup and shutdown, matches the independent reference output, and the candidate reports seven hash tables with 699,961 actual updates. One warmup per executable is excluded. The [raw measurements](key-span-timing-v1/results.json) retain all six samples, source/input/executable hashes and the launch policy. No full-input speedup is inferred from this small-input result.

[Validation](../native-owner-dispatch-v1/key-span-validation-v2) passes 211 native checks with three pre-existing exclusions. The counting fixture now covers 84 original/decoded cases: seven widths and six inputs, including empty strings, Unicode and CRLF. Checks observe both projection visits, require zero canonical range/key calls on the selected path, compare every count to an independent oracle, and exercise admission refusal, bounds errors and failure cleanup.

The [selected-key profiling build](profile-spans-build-v1/results.json) retains symbols with the same public-CLI link settings. Its entire `__TEXT,__text` machine-code section matches the timed candidate: 3,917,028 bytes, SHA-256 `c5a3d39743b09105608a0f0efe9bd84887c05af6f439f6a4a2d6d08e998810c6`. Three two-second samples on the standard 125-million-base input identify the remaining costs:

| Path | Inclusive share across the three sample windows |
|---|---:|
| Generated-block admission | 46–49% |
| Retained map/key helpers | 46–50% |
| Selected-key projection, within those helpers | 23–24% |
| Native work debits, across paths | 21–23% |
| Selected range cardinality/shape validation | 7–8% |
| Ordinary range snapshot / canonical String selection | 0 observed samples |

These categories overlap and must not be added. [Analysis](full-profile-spans-v1/analysis.json) counts each observed stack at most once within a category, including nested generic symbols. [Process receipts and stacks](full-profile-spans-v1/results.json) retain the evidence. The subject was stopped and reaped at the 45-second profiling deadline; profiling overhead is included, and this is not a completed full-input benchmark. Reducing repeated admission/accounting and projection checks is the next target. Full-input correctness, practical full-input runtime and Rust parity remain unqualified for this source-map implementation.

## Previous cache metadata improvement

Compiler [`f6ee09e63`](https://github.com/mech-lang/mech/commit/f6ee09e631048fb831d2032e8013a56d876efc63) maintains library call-cache metadata totals when each cache changes. Previously every retained-map operation rescanned all caches. It preserves the source, generated program image, map operations and security account; work policy 48 identifies the changed accounting protocol. All 209 native checks pass, with three pre-existing exclusions, including independent observation of the maintained totals ([validation](../native-owner-dispatch-v1/cache-census-v1)).

Each row below is the median of three fresh secured processes. The source and input are identical within each paired cohort. Runs are serial, alternate candidate/parent order and include startup and shutdown. Every complete output matches the reference. Build, profiling and reference generation are outside the timed interval.

| Input | Compiler | Seconds | × `f6ee09e63` Mech AOT on this input |
|---|---|---:|---:|
| 1,000 bases, deterministic diagnostic | Parent `9e2d1a29c` | 0.3966 | 1.09× |
| 1,000 bases, deterministic diagnostic | `f6ee09e63` | 0.3651 | 1.00× |
| 100,000 bases, prefix of standard THREE record | Parent `9e2d1a29c` | 8.4683 | 1.81× |
| 100,000 bases, prefix of standard THREE record | `f6ee09e63` | 4.6755 | 1.00× |

The 100,000-base improvement is 44.8% less wall time. It is a diagnostic result, not a completed 125-million-base benchmark. Results, process receipts, complete outputs and launch policies are in [cache-timing-v2](cache-timing-v2/results.json) and [cache-scale-v1](cache-scale-v1/results.json). These cohorts have different inputs and cannot share a timing denominator.

The `9e2d1a29c` source-map executable exceeded the 180-second limit on the full 125-million-base input ([receipt](full-timing-v1/results.json)); it was killed and reaped. The `f6ee09e63` candidate was sampled on that input for a bounded 45 seconds, then killed and reaped. Neither is a completed full-input timing. No full-input candidate-versus-parent speedup is inferred from those stops.

## Historical #909 source and compiler distinction

The [recorded #909 checkpoint](https://github.com/mech-lang/mech/blob/c5b0b3a35/docs/validation/canonical-knucleotide-word-source-checkpoint-v1.json) used compiler `f2268e482` and reports 0.4828 seconds for 125 million bases on the earlier M1, with a 4,806,512-byte executable and 146.1 MB peak RSS. Its executable SHA-256 is `ff781abb8d10b40374ddba318f9386e124a08b645ac2c84d4be7d60c84b2bb1e`. That exact executable has not been rerun in this study. The historical record is not a paired hardware comparison or the denominator for current timings.

The same historical **source**, SHA-256 `12cadfcd00e25605f190e9d360f7f7bb661be8a02754961055ee5b6dfa84b60f`, was also rebuilt with the **current compiler** as a separate regression control. This is not the original #909 compiler/executable. The old compiler selected dense-counter and direct-query lowering; the current production window lowering selects library hash-table updates. The old lowering remains test-only. Those paths perform materially different work even though the source and output agree.

On the current machine, the rebuilt histogram-source control performs seven full hash tables and 874,999,961 updates. Its complete stdout and native execution report are checked on every run. Three paired complete-process measurements on the standard 125-million-base input give:

| Executable | Seconds | × Rust time |
|---|---:|---:|
| Same historical Mech source, compiler `f6ee09e63` | 4.2816 | 7.77× |
| Unmodified upstream Rust #7 | 0.5511 | 1.00× |

These measurements are the `full-preserved-control` cohort in [cache-timing-v2](cache-timing-v2/results.json); “preserved” refers only to source. Rust is 7.77 times faster in this cohort. This control neither measures the new source-map program nor demonstrates a hardware regression from historical #909. It also does not isolate the cache-total optimization: earlier compiler changes already altered the histogram path.

The workload distinction follows the [Game's k-nucleotide specification](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/knucleotide.html): count every window for all seven widths using library hash tables, then query the resulting counts. Encoding keys is allowed; eliminating required table updates changes this prescribed work. The Rust source remains untouched.

## Cache-stage executable profile

[profile-cache-build-v2](profile-cache-build-v2/results.json) relinks the exact generated Mech object with the public CLI's final-host FatLTO and one codegen unit, retaining symbols. [analyze_profile.py](analyze_profile.py) verifies that its entire Mach-O `__TEXT,__text` section is byte-identical to the timed candidate: 3,896,484 bytes, SHA-256 `085fe0295086bdd5cb608db625616b4a9dd8cdb33c474c3e6380a29acd417689`.

Three 2-second stack samples from the full-input counting loop are retained in [full-profile-cache-v1](full-profile-cache-v1/results.json), with [reproducible analysis](full-profile-cache-v1/analysis.json). Ordinary library invocation accounts for 57–59% of inclusive main-entry samples. Within that path, range snapshot construction accounts for about 13%, and canonical String selection about 6–7%. The retained-map helper accounts for 12–13%; the maintained caller-cache metadata total accounts for less than 1%. These inclusive categories overlap and must not be summed. Samples describe the current candidate only; no matched baseline profile is available.

That profile selected per-window range/String materialization and library invocation overhead as the next target; the selected-key change above addresses it. It preserves ordinary range/index error behavior, lifetime and accounting checks, Unicode fallback and caller-produced map values. The counting algorithm remains expressed in Mech.

## Evidence and reproduction scope

- `compiler-v2` through `compiler-v5` pin the retained-map, cache-total, selected-key and admission-group compiler builds and their environments. Generated standalone binaries and retained Cargo projects are local build artifacts under `.build`; their hashes and build commands are in the receipts.
- `build_and_time.py`, `measure_cache.py`, `measure_scale.py`, `measure_spans.py`, `compare_rust_spans.py` and `measure_admission.py` retain the exact build/run procedures. Output directories are versioned and guard against overwriting samples. `measure_cache.py` reuses the candidate build receipt from `cache-timing-v1`; that attempted cohort stopped before quantitative timing because unmodified Rust used a different tie order on the synthetic input. Rust is excluded from that diagnostic, and its full standard-input output passes.
- `profile_full.py`, `build_profile.py` and `analyze_profile.py` retain the sampled process procedure, matching-link settings and code-identity check. Earlier `profile-build-v2`, `full-profile-v2` and `profile-cache-build-v1` used a ThinLTO final link and are explicitly marked as exploratory mismatches. Their percentages are not a matched before/after comparison. `profile-build-v1` and `full-profile-v1` retain failed preparation/monitor diagnostics, not benchmark samples.
- `available-timing-v1` records the earlier canonical-map implementation at compiler `f6fb76f5f`: 5.4684 seconds on the 1,000-base diagnostic. `candidate-timing-v1` records the subsequent retained-map change. These historical diagnostic measurements are not full-input results.
- Every build, test, profile and timed process uses the existing common mutex and owned-process cleanup. The canonical benchmark dataset, website data and protected upstream submissions are unchanged.

Full-input source/decoded correctness and table-update qualification, practical full-input runtime, and secured/trusted timings of the same executable remain unfinished. The current source-map implementation has not reached Rust's performance.
