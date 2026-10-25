# Selected join and emitted String-map composition

Candidate `b8e8032247ba25f25f43911847e87766bd32175a` composes a uniquely consumed selected-line join with the source-derived emitted SIMD String map after successful input completion. It is based on `630921324a65c385cf63e871d3241dbb0847b8d6`. The implementation passes correctness and ownership qualification, but **does not establish a complete-process performance gain**. It remains an independent unpromoted experiment. Rust parity remains incomplete.

## Transformation and boundaries

A complete-use proof requires a branch-free chain from the selected join through copies and collection initialization to the exact String-map generator. The map must already be available as an immutable root; the chain cannot cross an activation boundary or retain another observer of the joined String. The descriptor's serialized association is rederived from its canonical plan.

Runtime selection requires successful EOF, unique contiguous captured ASCII lines, empty separators and at most 128 source map entries. Relevant ASCII keys must map to one ASCII byte. Other sources, maps, separators and ownership patterns keep their ordinary paths. There is no recognition of a benchmark name, record header, input period or fixed nucleotide alphabet.

At the original admitted join visit, a generated loop requests one initialized physical output chunk and applies the **existing emitted SIMD mapper** in place. The old source chunk retires before the map runs. Copying and mapping remain two local passes over a chunk; the new path replaces a separate whole-buffer normalization pass. No Rust nucleotide implementation or replacement counting kernel is introduced.

The source's intermediate join/copy slots stay absent while a private same-account owner follows the proved path. Original join admissions execute first. A missing key is retained as an index without raising an early map error; the complete join still finishes, and the existing selected lookup reports the failure at the original map origin. Original collection/map admissions and full map operation debits still occur at their original boundaries.

No fuel is renewed. Fixed current-slot/generation reads use the already prepaid join envelope and check the original arena/ledger identity. A conservative bound covers descriptor work, table setup, payload work, selected rows and physical chunk transitions. Unfundable optional cases decline before consuming the source. The full map input's retained bytes/nodes are included in composed eligibility. Actual node and buffer ownership remains admitted through retirement and shutdown.

The prototype still finalizes a genuine private canonical String before converting it into owned bytes. This is not installed as the semantic intermediate, but it means physical canonical construction has not been completely eliminated. It also performs a whole-output UTF-8 validation at that handoff, followed by the existing map-finish validation. These remaining costs matter when assessing this experiment; the result must not be described as elimination of all intermediate construction or all full-buffer scans.

## Complete-process timings

Both sessions contain all six balanced orders of parent, candidate and exact upstream Rust. The repeat reverses the order list. Every observation includes fresh-process startup, secured execution and complete shutdown. The input has 125 million selected bases. All **874,999,961 original Mech histogram updates**, seven complete hash tables, default growth and seven-worker cap remain. Every candidate execution reports exactly **125,000,000 fused bytes**. Subjects run serially under the unchanged common lock. There are no excluded full-input warmups or outliers.

| Session | Parent, s | Parent / Rust | Fusion, s | Fusion / Rust | Rust, s |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.6649 | 1.184× | 0.6616 | 1.178× | 0.5616 |
| 2 | 0.6481 | 1.166× | 0.6624 | 1.191× | 0.5561 |

Paired changes are session 1: -0.17% (95% bootstrap interval -1.49% to +5.43%), 4/6 faster pairs; session 2: +1.21% (95% bootstrap interval -0.64% to +3.64%), 1/6 faster pairs. Both intervals include zero. The first session's median is slightly lower; the repeat is higher. This does **not** support promotion over the retained parent. The separate one-million-base prefix cohort contains one excluded warmup plus three measured observations per executable; it is not pooled with full-input results. Each candidate prefix verifies 1,000,000 fused bytes and 6,999,961 original histogram updates.

## Exact-code profile, counters and size

The profiling executable matches every byte of the primary executable's **4,341,608-byte `.text` section**, SHA-256 `557b661d6c64a8196b8bece344e28242cd0548de9aec583ed135f69aa2c9f8e1`. Three pre-armed owned-process captures per language preserve the exact sampled PID, all-thread stacks and correct final output. These diagnostics include profiler overhead and supply no primary timing samples.

Mech worker locations are 74.97% generated counting loops, 15.78% active accounting, 1.11% accounting waits and 4.81% active storage helpers. Loop refill accounts for 521 of 725 active-accounting observations. These are sampled locations, not percentages of elapsed time that can be subtracted from runtime. The separate [per-width study](../worker-completion-v1/README.md) identifies widths 12 and 18 as the long tasks; this experiment does not change their counting strategy or remeasure their individual CPU spans.

The main-thread profile directly observes the generated source scanner, chunk copying and emitted String mapper. It also records six UTF-8-validation leaf observations under the new private-join finalization and six under the existing compiled-map finish, alongside twelve during input capture. Those observations confirm remaining scans, but do not establish a causal millisecond decomposition of the primary result.

Nine independent counter executions retain exact primary files and original output/update checks. Their medians are diagnostic:

| Counter | Parent Mech | Fusion Mech | Rust |
| --- | ---: | ---: | ---: |
| Instructions, billions | 25.111 | 25.110 | 33.182 |
| Summed cycles, billions | 7.017 | 7.140 | 7.956 |
| User CPU, s | 2.010 | 2.040 | 2.350 |
| System CPU, s | 0.040 | 0.040 | 0.030 |

Aggregate instructions are essentially unchanged against the parent. The prototype does not show an aggregate CPU reduction in this cohort. Fewer aggregate instructions than Rust still do not imply a shorter serial prerequisite or faster completion of the longest workers.

| Session | Parent peak RSS, MB | Fusion peak RSS, MB | Rust peak RSS, MB |
| --- | ---: | ---: | ---: |
| 1 | 161.09 | 162.81 | 140.71 |
| 2 | 161.39 | 162.10 | 140.76 |

The fusion file is **5,517,744 bytes**, 33,072 bytes larger than the parent. Instruction bytes grow by 31,088. There is no measured memory reduction. The source, bytecode and resource image remain unchanged. The guest object and descriptor change to encode the new composition and its ownership protocol: IR82, ABI30 and work policy69; original operation prices and finite limits are retained.

## Qualification and retained failures

The clean timed revision passes **400 native checks, 27 engine line-storage checks and the catalog check**. Three existing manual native tests remain ignored. New checks cover original and decoded programs, captured-versus-snapshot output equivalence, lowercase full nucleotide input, CRLF, lone CR, empty and unterminated rows, Unicode/shared-source fallback, nonempty separators, missing-key origin, input/UTF-8 precedence, exact/one-short local limits, global byte/node pressure, replay/foreign-site/missing-owner denial, stale map generations, cleanup and successful reuse after rejection.

Five unsuccessful attempts remain in the raw evidence: an initial projected-action compile error; a stale optional result flag on ordinary fallback; incorrect test API visibility; an extra debit inside an exactly prepaid join scope; and four legacy artifact-format assertions. Each is followed by a clean qualified correction. Raw receipts and logs are unchanged. `verify.py` audits **90 terminal native process receipts**, including failed attempts, compiler/build qualification, prefix/full runs, profiles, symbol extraction and counters. Every owned process is reaped with a closed group and no signals or cleanup errors.

Primary binary SHA-256: `8116d48702168a637c4fb9153b356a39f6bb05214bd575224925abbbbbdfb95c`. Source SHA-256: `ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da`. Bytecode SHA-256: `050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0`. Canonical benchmark data is unchanged.

## Decision and remaining work

Retain the fusion branch and all negative measurements for later interaction tests; use the independently retained parent as the performance checkpoint. The qualified counters and timings do not establish lower total work or elapsed time. Extra validation, chunk handoffs and remaining private canonical construction are identifiable costs, but their individual contributions have not been isolated.

The next substantial experiments are compact scalar scanner execution, finite local worker reservations that retain the existing parent escrow and error/retirement rules, and a two-iteration pipeline in the confirmed long ordinary-hash loops. Their gains remain unmeasured. Thread spawning itself was already measured near 75 microseconds; source preparation and the long counting tail remain the more substantial targets.
