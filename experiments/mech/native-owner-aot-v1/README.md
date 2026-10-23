# Source-map standalone performance

This study measures a Mech state machine that explicitly traverses a String, selects each window, tests map membership, reads the previous count, inserts a caller-produced count and advances its state. The compiler retains general hash storage while compiling those operations from Mech. The current source is [knucleotide-source-map.mec](knucleotide-source-map.mec), SHA-256 `ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da`.

## Current measured improvement

Compiler [`7091f025d`](https://github.com/mech-lang/mech/commit/7091f025d2489ef511c4650b2c5e6d6dfe29102b) binds a proved closed map loop to invocation-owned storage and a pinned String. The generated Mech code still traverses the input, chooses branches, computes counts and updates every window. Private storage calls use the existing hash library. Entry validates the source representation and caller ownership; the same finite work account funds bounded batches of generated iterations and individual storage operations. Unsupported representations retain canonical execution. A suspended parent comprehension does not prevent a closed child map loop from selecting this path. IR36, work policy53 and ABI20 identify the protocol.

Three alternating complete-process measurements on the first **one million bases** of the standard THREE record give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0211 | 1.00× |
| Previous Mech AOT, `32a3a7b44` | 7.336 | 347× |
| Closed map loops, `7091f025d` | 1.985 | 94× |

The new executable is **3.70 times faster**, reducing elapsed time by **72.9%**. All nine timed outputs exactly match the independent reference. Both Mech executables perform seven tables and 6,999,961 updates. Runtime admissions fall from 55,717,707 to 443; individual private storage calls remain. Source and program bytecode are unchanged. Runs are serial, include secured startup/shutdown, and exclude one warmup per executable. [Raw measurements](closed-map-timing-v2/results.json) retain every sample and identity. Ratios use Rust from this cohort; its changing short-run denominator does not establish a change in the unchanged parent. This diagnostic is not full-input qualification, Rust parity or a comparison with interpreted execution.

[Validation](../native-owner-dispatch-v1/closed-map-nested-validation-v1/summary.json) records 217 native checks passing with three pre-existing exclusions. New original/decoded and restored-image tests cover ordinary non-DNA keys and caller-produced increments, finite fuel, admission refusal, repeated nested invocations, protocol rejection and complete cleanup. The 84 counting cases also execute through guarded, native and restored-image paths, including empty strings, Unicode and CRLF. An [IR36 follow-up](../native-owner-dispatch-v1/closed-map-nested-identity-v1/process.json) follows the version-only identity update.

The [matching profiling build](profile-closed-build-v1/results.json) has identical complete machine code to the timed executable: 3,949,076 bytes, SHA-256 `10a1b5d0337d396ccbffcb1449673930d47229dc5835d4c027438cc717c8b33f`. Three two-second samples during the beginning of full-input counting show:

| Path | Inclusive main-thread sample share |
|---|---:|
| Private map/key storage binding | 88–90% |
| Selected range cardinality/shape validation | 43–46% |
| Private map reads | 13–14% |
| Private map insertions | 12–13% |
| Library work debits | 5.5–6.2% |

Categories overlap and must not be added. [Analysis](full-profile-closed-v1/analysis.json) counts unions of matching stacks and uses all main-thread samples, including partial unwinds. The subject was stopped and reaped at its planned 45-second deadline. These are bounded profiles, not completed full-input timings. Repeated range shape/cardinality validation is the largest identified remaining category; reducing it must preserve the maintained range semantics and failure behavior. Packed keys, independent-loop parallelism, full-input qualification and same-binary secured/trusted measurements remain unfinished.

The preceding [`bc6fdbce8` attempt](closed-map-timing-v1/results.json) measured 7.634 seconds against a 7.356-second parent and selected no closed map regions. Its top-level-only admission restriction missed both counting loops inside parent comprehensions. The [selection analysis](closed-map-timing-v1/selection-analysis.json) retains that failed optimization result; it is not counted as a gain. The corrected timing harness requires both closed map regions and an actual reduction in runtime admissions before collecting the reported cohort.

## Native paths and fused helper admission

Compiler [`32a3a7b44`](https://github.com/mech-lang/mech/commit/32a3a7b449f64740ecf137ba3539a08cda2240e2) prepays native paths across scalar branches and joins between runtime boundaries. Every interior has the same entry; headers cut backedges, and helpers cut effects. A native Tail latch retains its original retirement at the following header. The next callback must match a proved frontier, and arithmetic failures retain their original source location. Selected map and key helpers admit their own boundary in the helper callback, eliminating the separate admission round trip. Refused owner entry preserves canonical execution. IR34, work policy52 and ABI19 identify this protocol.

Three alternating complete-process measurements on the first **one million bases** of the standard THREE record give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0222 | 1.00× |
| Previous Mech AOT, `913450a68` | 8.988 | 405× |
| Native paths, `32a3a7b44` | 7.331 | 330× |

Elapsed time falls by **18.4%**. All nine timed outputs match the independent reference; both Mech executables perform seven tables and 6,999,961 updates. Runtime admissions fall from 139,717,328 to 55,717,707. The latter includes admission fused into map/key helper callbacks; it is not a count of standalone admission-function calls. Source and program bytecode are unchanged. Runs are serial, include secured startup/shutdown, and exclude one warmup per executable. [Raw measurements](map-path-timing-v1/results.json) retain every sample, configuration and executable identity. Ratios use Rust from this cohort only. This diagnostic does not qualify the full 125-million-base workload or Rust parity.

[Validation](../native-owner-dispatch-v1/map-path-validation-v2/summary.json) passes 215 native checks with three pre-existing exclusions. Original/decoded and restored build-image tests exercise branches with multiple runtime successors, actual callback reduction, exactly-once fused admission, canonical fallback, helper replay and foreign-frontier rejection, insufficient fuel before state/storage changes, exact interior arithmetic failures and complete cleanup. The existing 84 independently checked counting cases remain correct. The first broad run passed 214 checks and failed only an outdated ABI18 expectation; the ABI19 expectation passes in the complete rerun.

The [profiling build](profile-path-build-v1/results.json) has the identical complete machine-code section as the timed executable: 3,943,088 bytes, SHA-256 `9dab5e6a7d578c5151ad1a931899d3dc380021be8ce854ae27c08fa084d19947`. Three two-second samples during the beginning of full-input counting show:

| Path | Inclusive sample share |
|---|---:|
| Retained map/key helpers | 65–67% |
| Runtime boundary validation, including fused admission | 27–29% |
| Standalone admission callback | 17–18% |
| Native work debits | 11–14% |
| Selected range cardinality/shape validation | 10–11% |

Categories overlap and must not be added. [Analysis](full-profile-path-v1/analysis.json) records symbol patterns and union counting. The subject was stopped and reaped at the planned 45-second deadline; these are bounded samples from the beginning of execution, not a completed full-input timing or a matched before/after profile.

The remaining implementation still admits about eight runtime boundaries per table update and separately validates/project keys and checks map operations. The next targets are reducing repeated work inside these helpers and extending native finite-fuel execution across map boundaries. Packed keys, independent-loop parallelism, practical full-input source/decoded qualification and same-binary secured/trusted measurements remain unfinished. The counting algorithm remains source-written Mech.

## Cached caller inventory

Compiler [`913450a68`](https://github.com/mech-lang/mech/commit/913450a68c609070b2f12f8f5f5bbf742fa11b75) retains the outer caller's fixed node inventory for each proved closed map-loop invocation. The region may contain native scalar/state operations, selected map operations and selected key projections; other managed operations and nested loops decline reuse. Snapshot holdings and call-cache metadata are read afresh, and every operation still includes current private table and key-view nodes and actual memory use. Work policy51 identifies the changed setup/accounting; IR33 and ABI18 are unchanged. Source and generated program bytecode are unchanged.

Three alternating complete-process measurements on the first **one million bases** of the standard THREE record give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0208 | 1.00× |
| Previous Mech AOT, `a3b1ddfcd` | 9.679 | 465× |
| Cached caller inventory, `913450a68` | 8.944 | 430× |

This change reduces elapsed time by 7.6%. All nine timed outputs exactly match the independent reference, and both Mech executables perform seven tables and 6,999,961 updates. Runs are serial, with startup/shutdown included and one excluded warmup per executable. Mech uses secured execution. [Raw measurements and reproduction configuration](caller-census-timing-v1/results.json) retain every sample and artifact identity. Ratios use Rust from this cohort only; its short runtime varies between cohorts. This diagnostic does not qualify the full 125-million-base source-map workload or Rust parity.

[Validation](../native-owner-dispatch-v1/caller-census-validation-v2) passes 215 native checks with three pre-existing exclusions. During actual generated-code tests, every reused inventory is compared with an independent full census, including after cache population, table growth and view retirement. All 84 original/decoded counting cases pass, including Unicode and CRLF. New original/decoded cases also verify that managed key construction and nested scalar control select the full inventory path. The earlier validation record failed only because the new nested-control fixture placed a state-machine invocation inside an unsupported arithmetic position; the corrected fixture uses an ordinary binding, and the complete suite passes.

The [matching profiling build](profile-caller-build-v1/results.json) has the identical complete `__TEXT,__text` section as the timed executable: 3,923,740 bytes, SHA-256 `e0bdc9ec58411a8a5e51c21c1aee2b6646a7942c1e04f3cfbcaa6e80c68c0336`. Three two-second samples during the beginning of the full-input count show:

| Path | Inclusive share across the three sample windows |
|---|---:|
| Retained map/key helpers | 55–56% |
| Generated-block admission | 40–41% |
| Native work debits, across paths | 17–20% |
| Selected range cardinality/shape validation | 8–10% |

Categories overlap and must not be added. [Analysis](full-profile-caller-v1/analysis.json) retains the symbol patterns and union counting. These samples describe only the bounded beginning of the full-input execution, not every window width or a matched before/after profile. The subject was stopped and reaped after 45 seconds; its elapsed time is not a benchmark result. The one-million-base complete process still makes 139,717,328 actual admission callbacks, unchanged from its parent, for 6,999,961 table updates.

The [exact timed Rust binary was also profiled](rust-full-profile-v1/results.json), without rebuilding it, in three serial full-input runs. All three complete outputs match the full reference. [Per-thread analysis](rust-full-profile-v1/analysis.json) finds counting-task stacks on seven worker threads in each capture; the main thread waits for results in 305/307, 307/308 and 305/306 samples. These are stack observations, not CPU-utilization percentages or new timing measurements. The [protected source](../../../archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs) uses rolling two-bit keys and hash-table entry updates inside those native worker loops.

The structural gap is therefore larger than the caller census: Mech still crosses runtime admission boundaries about twenty times per table update and has separately checked range, key and map operations. The next target is an entry-bound closed map loop with native finite fuel and simpler storage calls, retaining source-written traversal and arithmetic. Packed key representation and independent-loop parallelism also differ from Rust. None of these remaining changes is claimed as implemented or measured here.

## Grouped native admission

Compiler [`a3b1ddfcd`](https://github.com/mech-lang/mech/commit/a3b1ddfcdf501f4bc3c6eb81a7e975849295fcc4) admits a straight-line group of native map-owner instructions once before its first instruction. Group interiors have a single predecessor and contain no library helper or loop/ownership boundary. Every source instruction is still emitted, including its original arithmetic failure location. Refused owner entry retains the canonical per-block callbacks. The full original instruction work plus group-proof overhead is prepaid on the same finite ledger. IR33, work policy50 and ABI18 identify this protocol.

This diagnostic comparison uses the first **one million bases** of the standard THREE record. Three alternating complete-process measurements per executable give:

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

- `compiler-v2` through `compiler-v9` pin the retained-map, cache-total, selected-key, admission-group, caller-inventory, native-path and closed-map compiler builds and their environments. Generated standalone binaries and retained Cargo projects are local build artifacts under `.build`; their hashes and build commands are in the receipts.
- `build_and_time.py`, `measure_cache.py`, `measure_scale.py`, `measure_spans.py`, `compare_rust_spans.py`, `measure_admission.py` and `measure_stage.py` retain the exact build/run procedures. Output directories are versioned and guard against overwriting samples. `measure_stage.py` uses the configuration saved in each result and verifies its parent executable against the parent cohort's recorded hash. `measure_cache.py` reuses the candidate build receipt from `cache-timing-v1`; that attempted cohort stopped before quantitative timing because unmodified Rust used a different tie order on the synthetic input. Rust is excluded from that diagnostic, and its full standard-input output passes.
- `profile_full.py`, `build_profile.py` and `analyze_profile.py` retain the sampled process procedure, matching-link settings and code-identity check. Earlier `profile-build-v2`, `full-profile-v2` and `profile-cache-build-v1` used a ThinLTO final link and are explicitly marked as exploratory mismatches. Their percentages are not a matched before/after comparison. `profile-build-v1` and `full-profile-v1` retain failed preparation/monitor diagnostics, not benchmark samples.
- `profile_rust.py` and `analyze_rust_profile.py` capture and summarize the exact timed upstream Rust binary on the complete input; the original program and binary are unchanged. Profiling process durations are excluded from benchmark cohorts.
- `available-timing-v1` records the earlier canonical-map implementation at compiler `f6fb76f5f`: 5.4684 seconds on the 1,000-base diagnostic. `candidate-timing-v1` records the subsequent retained-map change. These historical diagnostic measurements are not full-input results.
- Every build, test, profile and timed process uses the existing common mutex and owned-process cleanup. The canonical benchmark dataset, website data and protected upstream submissions are unchanged.

Full-input source/decoded correctness and table-update qualification, practical full-input runtime, and secured/trusted timings of the same executable remain unfinished. The current source-map implementation has not reached Rust's performance.
