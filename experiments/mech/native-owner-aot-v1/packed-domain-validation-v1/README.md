# Complete packed-decoder validation

Candidate `1b7c79b3e1d6713f0648cbe59794fab8b091d245` on
`codex/native-packed-domain-validation` establishes once whether the actual
immutable key decoder contains every possible packed code. A complete decoder
makes subsequent per-symbol validity walks redundant after the mandatory key
width check. Sparse encodings retain their original walk.

The candidate is retained. Complete-process medians improve **2.18% initially
and 1.76% in a separate repeat**, but both paired intervals include zero; a
precise repeatable elapsed-time gain is not established. Separate counters show
about **290 million fewer full-input instructions / 1.10%**, and **274 million
fewer prefix instructions / 18.00%**. Rust parity remains incomplete.

## Implementation and unchanged behavior

`PackedMap` derives its private immutable `all_codes_valid` proof from the
actual decoder entries, rather than assuming alphabet cardinality implies
complete coverage. Every key still passes the original high/low-word width
check. Singleton/nonzero codes and sparse alphabets keep their existing
code-by-code checks. Frame validation, current missing-key proof, complete-key
hash comparisons, finite work/memory/node admission, source failure precedence,
publication and cleanup remain.

The cached boolean is included in the existing `size_of::<Self>()` private
metadata reservation and setup charge. No storage or charge is hidden; no
resource limit or per-operation price formula changes. This is a generic
decoder property, with no workload, query, alphabet-name or observed-input
special case. Seven original generated workers still construct seven complete
maps using caller-computed replacement values and every physical update.

The parent is retained scheduling revision
`b8da46b50fd78e59dc610b4dda0b4b5adc93de81`. The Mech performance source,
bytecode, native Object, complete Object identity, descriptor JSON/compressed
image and resource metadata are byte-identical to that parent. The Object hash
remains `f25ada28ff389713076fcb342b3b13f807741bfda91ca2274e6eb4d8ebc36335`;
IR79, ABI28 and work policy66 are unchanged. The earlier preparation,
host-metadata and scheduling factors remain available independently.

## Complete-process results

The [plan](plan.json) was committed at
`47ebb1ce1de576d8e72c04784bad094dcf644047` before validation or timing. Each
session uses all six balanced sequential orders of exact upstream Rust #7,
parent and candidate. All **36 full-input observations** are included, without
excluded warmups or outliers. Input contains 125 million selected bases, with
fresh secured startup and process exit included. No subjects run concurrently.

| Configuration | Session 1 seconds | × Rust | Session 2 seconds | × Rust |
|---|---:|---:|---:|---:|
| Rust | 0.5506 | 1.000× | 0.5664 | 1.000× |
| Size-first parent | 0.7044 | 1.279× | 0.7039 | 1.243× |
| Decoder proof | 0.6890 | 1.251× | 0.6915 | 1.221× |

Median paired log-ratio changes are **−2.65% [−5.12%, +1.53%]** and
**−0.71% [−5.77%, +1.21%]**. Five of six and three of six matched orders favor
the candidate. Descriptive 95% intervals resample whole matched orders 20,000
times with fixed seeds; paired estimates differ from ratios of marginal
medians. Both sessions and every observation remain separately reported.

The separate one-million-base prefix has one excluded warmup and three measured
complete processes per subject: Rust **0.01938 s / 1.000×**, parent
**0.10541 s / 5.440×**, candidate **0.08910 s / 4.599×**. This single small
batch is not a repeated prefix result and is not pooled with full-input runs.

[Session 1](../full-packed-domain-validation-v1/results.json),
[session 2](../full-packed-domain-validation-v2/results.json) and
[prefix/build qualification](../packed-domain-validation-timing-v1/results.json)
retain observations, deviations, source/input/policy/binary pins and native
reports. Every full Mech process verifies complete output, seven complete maps,
five admitted caches, seven peak workers and **874,999,961 physical updates**;
prefix processes verify complete output and **6,999,961 updates**.

## Counters, memory and size

Nine separate full-input counter processes, three per executable, give:

| Configuration | Instructions billions | Cycles billions | User CPU s | Kernel CPU s | Involuntary switches |
|---|---:|---:|---:|---:|---:|
| Rust | 33.132 | 8.091 | 2.39 | 0.03 | 591 |
| Parent | 26.390 | 7.429 | 2.12 | 0.04 | 6,093 |
| Decoder proof | 26.099 | 7.078 | 2.01 | 0.04 | 6,820 |

The separate prefix diagnostic medians are:

| Configuration | Instructions billions | Cycles billions | User CPU s | Kernel CPU s |
|---|---:|---:|---:|---:|
| Rust | 0.308 | 0.082 | 0.02 | 0.00 |
| Parent | 1.522 | 0.648 | 0.16 | 0.00 |
| Decoder proof | 1.248 | 0.536 | 0.13 | 0.00 |

Counters sum across threads. Their rounded diagnostic elapsed values do not
replace the primary timings, and cycles/CPU/switches include scheduling
variation. The instruction reduction is much larger proportionally on the
short input, consistent with avoiding distinct-key validation work; these
totals do not isolate an exact per-function elapsed cost.

MB means 1,000,000 bytes. RSS below is each original timing process's macOS
`wait4` peak, summarized separately by session.

| Configuration | Session 1 RSS MB | Session 2 RSS MB | File MB | Machine-code MB |
|---|---:|---:|---:|---:|
| Rust | 141.07 | 141.12 | 0.756 | 0.347 |
| Parent | 160.94 | 161.35 | 5.468 | 4.304 |
| Decoder proof | 161.29 | 161.28 | 5.468 | 4.304 |

Parent and candidate both occupy 5,468,144 file bytes and 4,304,368 code bytes;
their host code hashes differ. The unchanged checked Mech Object is linked
into each. No meaningful RSS or size improvement is established. No further
paused heap captures are needed for the cached scalar; earlier complete
[heap and host support accounting](../host-metadata-trim-v1/README.md) remains
available. [Full diagnostics](../packed-domain-validation-diagnostics-v1/results.json)
and [prefix counters](../packed-domain-validation-prefix-counters-v1/results.json)
retain all raw observations and exact size evidence.

## Profiles and validation

Three fresh full-input profiles match the candidate's entire timed machine-code
section. Across 4,728 observed worker stacks, 75.04% are generated counting
loops, 15.06% active work accounting, 1.04% accounting waits, 4.99% storage
helpers, 1.78% helper bridges and 2.09% other locations. These are sampled
stack-location shares including waits, not elapsed/CPU time shares. The earlier
unchanged Rust full profile remains a reference rather than a new capture.
[Profile partition](../packed-domain-validation-full-remaining-profile-v1/results.json)
preserves the raw contexts and classification rules.

The exact clean revision passes **383 native checks, two focused checks and
one catalog check: 386 checks**, with focused-suite overlap and three existing
manual native exclusions. New checks compare against the original validation
predicate at every width from zero through 18, using full ASCII, complete
compact, sparse compact, singleton/nonzero and fallback domains. They exercise
every symbol in every position, both sides of the word boundary, arbitrary
words, forbidden codes and excess high bits. Invalid insertions preserve the
table, accounting and update count; all owned memory/nodes are released.

[Verification](verification.json) recomputes the immutable plan, both balanced
timing sessions and bootstrap intervals, exact build-input equality, native
outputs/updates, profiles, raw counters, binary sizes and **81 terminal,
reaped, closed-group process receipts**. Compiler source remains clean and
unchanged throughout. Canonical benchmark data is unchanged. Run `python3
packed-domain-validation-v1/verify.py` from this study directory in the qualified
checkout to recompute the retained evidence.

The [separate host metadata trial](../host-metadata-trim-v1/README.md) reduced
descriptor restoration from about 7.80 to 7.04 ms. This decoder proof affects
map execution rather than descriptor startup. Input capture and worker
execution remain the larger optimization targets.
