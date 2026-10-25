# Finite local worker credit

Candidate `7a715c12a055472247bab992904f43a9962cafd1` reduces shared work-accounting ownership transfers in the unchanged generated hash-map loops. Two balanced complete-process sessions establish a repeatable improvement over `630921324a65c385cf63e871d3241dbb0847b8d6`: every one of twelve matched candidate/parent pairs is faster, and both paired intervals exclude zero. **Rust parity remains incomplete.** This is the next retained performance checkpoint; the independent join/map-fusion experiment remains unpromoted.

## Complete-process timings

Each session contains all six balanced orders of parent, credit candidate and exact upstream Rust, six observations per executable. Session two reverses the order list. Every observation includes fresh-process startup, secured execution and complete shutdown. The full input contains 125 million selected bases. Subjects execute sequentially under the unchanged shared lock, with seven internal workers. No full-input warmup or outlier is excluded.

| Session | Parent, s | Parent / Rust | Credits, s | Credits / Rust | Rust, s |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.6557 | 1.186× | 0.6166 | 1.115× | 0.5528 |
| 2 | 0.6466 | 1.171× | 0.6218 | 1.126× | 0.5524 |

Median paired changes are session 1: -5.97% (95% bootstrap interval -8.52% to -2.35%); session 2: -4.12% (95% bootstrap interval -5.71% to -2.40%). The candidate saves about 39 ms in the first median comparison and 25 ms in the repeat. Sessions remain separate rather than selecting or pooling favorable observations. The remaining full-input gap is about 64–69 ms against the respective Rust controls.

The separate one-million-base prefix cohort has one excluded warmup plus three measured processes per executable: candidate 0.0919 s / 4.768× Rust, parent 0.1037 s / 5.377×, Rust 0.0193 s. These diagnostic-scale results are not pooled with full-input sessions; short-input parity is not established.

## Actual selection and unchanged work

Every full candidate execution reports exactly **854,497 full batches** charged through local credit. Each batch retains the original 1,024-visit funding size, including the original spent terminal surplus. Across the two sessions, credit claims range from 14,342 to 14,355; median batches per claim are 59.54 and 59.54. This demonstrates roughly sixty full-batch debits per shared reservation. It is not a count of every escrow lock: growth, checked calls, exact queries and publication retain other synchronized accounting.

All candidate and parent full processes verify **874,999,961 original physical hash-table updates**, seven complete maps, default growth, seven peak workers, five admitted complete-key caches and ten original frozen-map reads. The source SHA-256 is `ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da`. Source, bytecode, descriptor, resource image and the **entire generated guest object** match the retained parent byte for byte. IR81, ABI29 and work policy68 remain; no new source primitive, replacement Rust workload kernel, query-only scan, dense histogram or input-specific storage reservation is used.

The original source/body prices and all finite invocation and library limits remain. Setup metadata grows to hold the real registry, aligned pool and effectivity counters. Whole-invocation work/compare receipts retain small pre-existing run variation and the explicit setup change; the optimization does not reduce original full-batch prices or renew the root allowance.

## Protocol

The packed-map refill derives its actual paired compute/comparison price from current source width, table capacity and length. Up to 64 identical full prices are reserved from the existing parent-group escrow. One atomic repetition count commits both u64 dimensions before emitted code resumes. The large prices themselves are not narrowed to atomic bit fields.

A debit requires four unspent repetitions in its exclusive credit, plus the original worker-local headroom. This proves the existing full-batch selection condition. Tight or uncertain cases, changed/unsupported prices, overflow and active scopes keep the original synchronized selector; private credit never causes a smaller batch.

A worker's atomic slot occupies a separate 128-byte-aligned cell. Shared synchronization occurs when acquiring, replacing, reclaiming or retiring credit. Before an authoritative denial, held unused credit can be sealed and recovered from peers. Settlement folds all successfully paid repetitions into the same group ledger and releases only unspent reservation. Group closure seals every slot before parent reconciliation, retaining spent work through errors, cancellation and panic. Root/local caps and checked failure ordering remain enforced. The [protocol design](design.md) states the accounting invariants and ownership rules.

All registry, aligned Arc padding, pool and worker-account backing is admitted. Constructor feasibility includes those simultaneous claims and the fixed child setup inventory. The additional pool owner is included in scheduler node admission. No CPU frequency, QoS, affinity, priority, worker-count or power setting changes are made.

## Exact-code profile and independent counters

The profiling executable matches every byte of the primary executable's **4,326,232-byte `.text` section**, SHA-256 `cd6c7f86b59c36b69335ea379c561a36b0ac433e65a8e7ce14cc2c2935f14c26`. Three pre-armed owned-process captures per language preserve exact sampled PIDs, all-thread stacks and correct final output. No debugger or process pause is used. Profiling overhead is included in diagnostics, which supply no primary timing samples.

Fresh candidate worker observations are 87.42% generated counting loops, 3.01% active accounting, 0.67% accounting waits and 6.08% active storage helpers. The earlier [parent profile](../line-join-copy-v1/README.md) recorded 18.33% active accounting and 73.93% generated counting. These are independent sampling cohorts and compositional location shares, not elapsed-time percentages that can be subtracted from runtime. The new source-aware classifier also recognizes credit-specific symbols if they survive inlining; this build mostly exposes them beneath the existing refill function.

Nine separate counter executions retain the exact primary files and verify all original output/update counts. Their medians are diagnostic:

| Counter | Parent Mech | Credit Mech | Rust |
| --- | ---: | ---: | ---: |
| Instructions, billions | 25.103 | 24.979 | 33.190 |
| Summed cycles, billions | 6.875 | 5.925 | 8.011 |
| User CPU, s | 1.960 | 1.670 | 2.370 |
| System CPU, s | 0.040 | 0.030 | 0.030 |
| Involuntary context switches | 6132.000 | 3855.000 | 596.000 |

Instructions fall only about 0.5%, while summed cycles fall about 13.8% and user CPU about 14.8%. Together with actual credit selection and the reduced accounting locations, this supports lower synchronization cost rather than a changed counting algorithm. The remaining elapsed gap cannot be inferred from aggregate instruction counts: serial preparation and the workers that finish last still determine completion.

| Session | Parent peak RSS, MB | Credit peak RSS, MB | Rust peak RSS, MB |
| --- | ---: | ---: | ---: |
| 1 | 161.09 | 162.50 | 140.41 |
| 2 | 161.98 | 163.46 | 140.72 |

There is no memory improvement: candidate peak RSS is about 1.4–1.5 MB higher in these cohorts. The candidate file is **5,501,200 bytes**, 16,528 bytes larger than the parent; executable instruction bytes grow by 15,712. These costs remain part of the measured standalone executable.

## Qualification and evidence

The clean timed revision passes **393 native checks, 36 engine credit checks, 26 engine line-storage checks and the catalog check**. Three existing manual native checks remain ignored. The credit suite covers large paired prices, local execution without repeated shared locking, idle-peer and direct-debit reclamation, independent comparison denial, exact remaining queries, changed prices, local/call/foreign scopes, close races, concurrent exhaustion, worker unwind, excess-slot fallback and complete metadata retirement. The compiled-source test checks original and decoded artifacts, serial/seven-worker equivalence, changed inputs and all seven counting widths, requiring actual credit counters.

The first full attempt passed 392 checks and failed an old fixture whose 4 KB child view could not fit the correctly admitted new metadata. The correction uses the exact account claim, verifies a one-byte-short rejection with no leak, retains a child ceiling below the parent and preserves the original work allowance. The failed receipt is unchanged. An initial admission filter selected zero tests and is explicitly excluded from qualification; its corrected focused run and full final suite pass. Earlier foundation and integrated checks retain their own immutable revisions.

`verify.py` audits **87 terminal native process receipts**, including the retained failure, compiler/build qualification, all prefix/full processes, exact-code profiles, symbol extraction and counter runs. Every owned process is reaped with a closed group and no signals or cleanup errors. Canonical benchmark data is unchanged. Primary binary SHA-256: `50948088737a8e6ddcf21b23536dd483a5bbea2e0e1cd4a1029aca359d78ff4c`. Unchanged guest object: `7b1fa85e74cc23a88ce5d9937ad68c7bf003fe5038b4da4e9039171cee3210ea`.

## Remaining target

The full-input candidate remains 1.115–1.126× Rust in these sessions. Active accounting is substantially smaller; generated counting and serial input preparation remain. The [per-width diagnostic](../worker-completion-v1/README.md) established widths 12 and 18 as the long tasks, but their current individual CPU spans have not yet been remeasured. Earlier phase measurements put substantial time in the scalar source scanner. Updated phase/per-width evidence, compact scanner execution, the retained UTF-8 fragment-fact interaction and ordinary-loop pipelining are the next avenues; their gains are not claimed here.
