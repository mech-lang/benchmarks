# Worker credit with validated input-fragment facts

The retained fragment-fact optimization demonstrates a repeatable complete-process improvement on the qualified worker-credit parent. Both fresh sessions favor the combination in all twelve matched pairs; both paired confidence intervals exclude zero. All correctness, exact-code profile and terminal-receipt checks pass. This is the next qualified performance checkpoint. Rust parity remains incomplete.

## Complete-process timings

| Session | Credit parent | Credit + fragment facts | Exact Rust #7 |
| --- | ---: | ---: | ---: |
| 1 | 0.6230 s · 1.125× | **0.6046 s · 1.092×** | 0.5537 s · 1.000× |
| 2 | 0.6248 s · 1.111× | **0.6083 s · 1.082×** | 0.5622 s · 1.000× |

Session 1: -2.14% paired median change, 95% bootstrap interval [-5.12%, -0.97%], 6/6 matched pairs faster.
Session 2: -2.22% paired median change, 95% bootstrap interval [-3.87%, -1.31%], 6/6 matched pairs faster.

The respective remaining gaps are 50.9 ms and 46.1 ms. Sessions are retained separately, each with its own Rust control. Every session uses all six balanced serial orders of three subjects, reversed in session two. Secured startup through process exit is included. The input has 254,166,745 bytes and 125 million selected bases. There are no excluded full-input warmups or outliers.

Raw observations: [session one](../full-credit-fragment-facts-v1/results.json), [session two](../full-credit-fragment-facts-v2/results.json).

The separate one-million-base prefix cohort has one excluded warmup and three complete measured processes per subject:

| Candidate | Credit parent | Exact Rust |
| ---: | ---: | ---: |
| 0.0919 s · 4.644× | 0.0931 s · 4.707× | 0.0198 s · 1.000× |

This small startup-sensitive cohort is not pooled with full timings and does not establish a startup improvement or prefix parity. The large prefix regression observed in the earlier independent fragment-fact cohort is not reproduced here.

## Implementation and unchanged work

Source `bdb3c511cd552ffc143460d6e1ae7edd04885a7f` applies retained fragment-fact revision `76d17b03f7536132369b7d221f18727a1a045d03` to qualified credit parent `7a715c12a055472247bab992904f43a9962cafd1`. The generic decoder retains exact ASCII and LF facts for the bytes it actually validates. Private fields prevent supplying unchecked certificates; borrowed lifetimes keep them tied to the actual text. Resource delivery and line capture reuse these facts after the original admission and debit. Unicode, incomplete UTF-8, short reads, pending lines, CRLF, input caps, provider failures and deferred consumer errors/panics keep their maintained paths.

The source program, bytecode, resource image, descriptor and **entire generated guest object** match the credit parent byte for byte. Guest SHA-256: `7b1fa85e74cc23a88ce5d9937ad68c7bf003fe5038b4da4e9039171cee3210ea`. All seven complete hash maps, default growth, seven internal workers and **874,999,961 original physical updates** remain. Every full execution uses the original 854,497 funded batches and finite credit protocol. IR81, ABI29 and work policy68 remain; original work prices and finite limits are unchanged. No source primitive, input-specific recognition, query-only scan or replacement workload kernel is introduced.

The earlier fragment-fact result was inconclusive on its older parent. This new controlled comparison establishes usefulness on the current credit baseline; separate historical cohorts do not establish a causal statistical interaction mechanism.

## Correctness, memory and remaining diagnostics

The clean candidate passes **468 checks**: 2 core fragment checks, 9 runtime capture checks, 36 worker-budget checks, 27 line-storage checks, 393 native checks and the catalog check. Three existing manual native checks remain ignored. An initial worker filter selected zero tests; the harness rejected it as qualification. That immutable successful empty receipt is retained and explicitly excluded; the corrected `workers::` suite passes all 36 tests.

| Session | Credit parent RSS, MB | Combination RSS, MB | Rust RSS, MB |
| --- | ---: | ---: | ---: |
| 1 | 162.53 | 163.15 | 140.68 |
| 2 | 162.78 | 162.79 | 140.77 |

No memory improvement is claimed. Fresh exact-whole-text profiles, independent counters and executable sizes are verified. The separately instrumented [phase/per-width diagnostic](../credit-fragment-preparation-workers-v1/) is pending; it will measure the actual candidate and credit parent before attributing the saved time to individual phases. The canonical benchmark dataset is unchanged. All native work runs serially under the existing common lock, with no changes to power, frequency, QoS, affinity or scheduling settings.

## Fresh exact-code diagnostics

The symbol-bearing profile executable matches every byte of the primary executable's **4,326,912-byte text section**, SHA-256 `0508b867d02c3a1aa18a03af9c259b2517af0ada531e9276da7b597c5f843216`. Three pre-armed owned-process captures per language verify exact sampled PIDs and complete outputs. No debugger, process pause or machine setting change is used. These diagnostic observations are excluded from primary timing samples.

Fresh Mech worker locations are 86.62% generated counting, 6.04% active storage helpers, 3.48% active accounting and 0.74% budget waits. These are compositional sampled locations, not recoverable fractions of elapsed time. Main-thread leaves still include the generated source scanner, copying, normalization, offset construction and the new decoder byte-fact reduction. Phase attribution remains pending the separate instrumented comparison.

| Independent counter median | Credit parent | Combination | Rust |
| --- | ---: | ---: | ---: |
| Instructions, billions | 24.979 | 24.522 | 33.149 |
| Summed cycles, billions | 6.031 | 5.862 | 8.205 |
| User CPU, s | 1.700 | 1.650 | 2.420 |
| System CPU, s | 0.030 | 0.030 | 0.030 |
| Involuntary context switches | 4058 | 4342 | 696 |

The candidate retires about 457 million fewer instructions than its parent. Cycles and user CPU are also lower in this diagnostic cohort; primary elapsed measurements establish the performance result. Aggregate counters cannot be converted into a phase-by-phase elapsed decomposition.

The file remains **5,501,200 bytes**, equal to the parent's file size. Executable text grows by 680 bytes from the parent's 4,326,232. Static inspection retains the actual 121-instruction byte-fact function, including 48 vector-register instructions; it does not itself measure speed.

The [verifier](verification.json) checks **84 terminal native process receipts**, all source and executable pins, 36 full primary observations, nine measured prefix observations and the three separately excluded prefix warmups. Every owned native process exits successfully, is reaped, and has a closed group with no signals or cleanup errors. The retained zero-test selection is explicitly excluded from correctness qualification. Source and evidence preserve the entire trial; the canonical benchmark dataset is unchanged.
