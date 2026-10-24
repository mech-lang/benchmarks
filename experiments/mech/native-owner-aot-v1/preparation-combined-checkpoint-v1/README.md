# Preparation interactions, memory and binary size

A later [compact host-metadata trial](../host-metadata-trim-v1/README.md) builds
on this combination without removing either factor. This report preserves the
original four-configuration interaction study and memory audit.

The two preparation changes are retained together on
`codex/native-preparation-interactions` at `e82ed4d54d4490102ac41192d1fcbf492d467e08`.
The combined configuration has lower medians than either change alone in both
independent sessions. A reliable improvement over the accepted baseline is
not established: its median changes by −2.07% initially and −0.08% in the repeat,
and both paired baseline confidence intervals include zero. The accepted PR
branch remains at `abfce6636282cc08d302579614196e1258229941`; no variant is discarded
because its individual effect falls below a promotion threshold.

## Complete-process timings

Each session contains twenty balanced orders of five sequential processes,
including secured Mech startup and shutdown. The input contains 125 million
selected bases. Every observation remains included, without full-input warmups
or outlier exclusions. Sessions are reported separately.

| Configuration | Session 1 seconds | × Rust | Session 2 seconds | × Rust |
|---|---:|---:|---:|---:|
| Exact upstream Rust #7 | 0.5568 | 1.000× | 0.5631 | 1.000× |
| Accepted baseline | 0.7138 | 1.282× | 0.7037 | 1.250× |
| CRLF/offset scan fusion | 0.7082 | 1.272× | 0.7080 | 1.257× |
| Disjoint private metadata | 0.7084 | 1.272× | 0.7098 | 1.260× |
| Both changes | 0.6990 | 1.255× | 0.7031 | 1.248× |

The [predeclared plan](../preparation-interactions-v1/plan.json) was committed
before execution at `a3c44503bec0b358181808528b93ae672474b3fe`. It pins an eleven-file
two-factor source matrix, both individual executables, the unchanged workload,
finite launch limits, balanced orders and paired analysis. The second session
uses an independent deterministic reshuffle of the same balanced design.

Paired effects use median matched log ratios and 20,000 bootstrap resamples of
whole five-subject orders. They differ from ratios of the marginal medians above.
Intervals are descriptive 95% intervals, without multiple-comparison adjustment.

| Paired comparison | Session 1 change [95% interval] | Session 2 change [95% interval] |
|---|---:|---:|
| Combined / baseline | −1.84% [−3.45%, +0.40%] | −0.61% [−0.89%, +0.05%] |
| Combined / scan alone | −1.43% [−2.37%, −0.49%] | −0.65% [−1.47%, −0.11%] |
| Combined / metadata alone | −1.08% [−1.62%, +0.05%] | −1.09% [−2.29%, +0.01%] |
| Interaction, C×B/(S×A) | −0.64% [−2.41%, +0.48%] | −1.56% [−2.48%, −0.41%] |

Both point estimates favor an interaction; only the second interaction interval
excludes zero. The combination beats scan fusion in fifteen of twenty matched
orders in each session and metadata alone in fourteen. This is sufficient to
keep the combined candidate available for further optimization, without claiming
Rust parity or a repeatable 2% baseline improvement.

[Session 1](../full-preparation-interactions-v1/results.json),
[session 2](../full-preparation-interactions-v2/results.json),
[paired analysis](../preparation-interactions-v1/analysis.json) and
[retention decision](../preparation-interactions-v1/decision.json) preserve every
observation. The separate prefix compares the combination with metadata alone,
not with the accepted baseline, and is not pooled with these full-input sessions.

## Peak memory and executable size

Peak resident memory comes from macOS `wait4` in the same 200 original timing
processes: twenty per configuration per session. MB denotes 1,000,000 bytes.
These are medians of per-process high-water marks, not sampled live heaps.

| Configuration | Session 1 peak RSS MB | Session 2 peak RSS MB | Executable MB | Machine code MB |
|---|---:|---:|---:|---:|
| Rust | 140.48 | 140.44 | 0.756 | 0.347 |
| Baseline | 162.78 | 162.87 | 5.501 | 4.334 |
| Scan fusion | 162.48 | 162.61 | 5.501 | 4.334 |
| Private metadata | 162.62 | 162.18 | 5.501 | 4.334 |
| Combined | 162.66 | 162.96 | 5.501 | 4.334 |

The combination uses about 22.5 MB / 16% more peak RSS than Rust in session 2.
Its actual executable is 7.28 times larger and its machine-code section 12.49
times larger. The four Mech configurations have effectively the same size and
memory profile. No memory saving from their interaction is established.

The combined executable's file bytes are 5,501,312. Its `__text` contains
4,334,052 bytes; exception tables, unwind indexes and exception frames occupy
758,420 bytes. This is runtime code and metadata, rather than a large debug file:
the actual stripped timed executable is measured. Rust retains more link-edit
bytes, so total-file ratios should not be confused with executable-code ratios.
`__PAGEZERO`, zero-filled BSS and reserved stack address space are not disk size
or physical RAM consumption.

Exact-code symbol attribution estimates only 112,172 bytes in generated Mech
entry/loop function extents, around 2.6% of all Mech machine code. The emitted
object file is 114,672 bytes. Other leading symbol groups are `core` 923,512,
`mech_core` 806,652, `mech_engine` 744,432, `mech_runtime` 434,636,
`mech_gpu` 393,848 and `alloc` 351,828 bytes. Groups are inferred from demangled
symbol names; generic code may serve other groups. Function extents include
alignment padding and do not establish runtime hotness. Only the code section
of the symbol-preserving profile build is used for attribution; its larger file
size is not substituted for the shipped binary.

[Raw binary sections and function sizes](../preparation-interactions-binary-size-v1/results.json)
and [primary memory accounting](../preparation-interactions-memory-analysis-v1/results.json)
retain byte counts, hashes, distributions, ranges and the analysis scripts.

## Separate memory diagnostics

Fifteen separate full-input processes, three per configuration, collect
birth-verified `libproc` RSS, physical-footprint and thread-count timelines.
The median observed lifetime peak physical footprints are baseline **158.76 MB**,
scan **157.66 MB**, metadata **157.30 MB**, combined **156.88 MB** and Rust
**139.89 MB**. Physical footprint and RSS are different OS accounting measures.
These diagnostics perturb execution and are not added to primary timing or
memory samples; polled maxima are lower bounds.

Five further executions stop only the owned process after seven workers first
become visible, capture content-free `vmmap` and `heap` size summaries, then
resume and verify complete output. Their sampled live allocations are:

| Configuration | Live blocks | Live allocated MB |
|---|---:|---:|
| Baseline | 8,750 | 127.26 |
| Scan fusion | 9,705 | 127.35 |
| Private metadata | 9,704 | 127.75 |
| Combined | 9,718 | 128.42 |
| Rust | 456 | 136.43 |

These snapshots occur at worker appearance, not at an identical count of kernel
operations or the RSS peak. The large live byte count is predominantly the
selected sequence. Rust's vector has spare capacity, so it can have a larger
allocated heap and a lower resident footprint simultaneously. The combined
snapshot has **8,144 KiB of dirty resident empty small-allocation regions**,
versus none reported for Rust at that point, and more resident small-allocation
and code pages. Allocator retention and binary size therefore explain plausible
parts of the RSS gap; live payload size alone does not.

Two final diagnostic executions enable `MallocStackLogging=1`, pause roughly
100 ms after workers first appear, and retain live allocation caller trees.
The exact timed binaries are unchanged, but instrumentation alters execution
and allocation layout. Mech has 9,720 live blocks in this later heap snapshot,
versus Rust's 457. Symbolication maps 12,697 Mech stack frames back to an identical
machine-code image. The OS reports missing stacks for some earlier allocations;
full historical coverage and allocation-churn counts are not claimed.

A disjoint partition of the 9,540 stack-attributed live blocks identifies
1,906 under program-image library-template restoration, 900 under schema
restoration, 346 under canonical string decoding and 324 under resolved-contract
decoding. Further allocations include snapshot-memory imports, cloned types,
schemas and bound calls, plus per-worker native storage. The selected-join
allocation supplies the approximately 125 MB sequence; packed-map slots and
controls supply the later worker tables. Ancestor totals in the inverted caller
tree are not added together.

[Timelines](../preparation-interactions-memory-timeline-v1/results.json),
[worker-entry snapshots](../preparation-interactions-memory-snapshot-v1/results.json),
[instrumented allocation captures](../preparation-interactions-allocation-callers-v1/results.json)
and [symbolicated callers](../preparation-interactions-memory-analysis-v1/combined-live-callers-symbolicated.txt)
remain separate from primary results. No security settings change, administrator
debugger or other-process memory inspection is involved.

## CPU profile and next hypotheses

Three new profiles complete successfully and match the timed combination's
entire machine-code section. The main-thread partition retains 1,775 observations:
1,190 joining workers, 193 input capture/source selection, 64 selected-line
joining, 31 generated byte mapping, 18 input reads, 11 string geometry, six
mapped UTF-8 validation, 40 other locations and 222 unresolved root-only stacks.
These locations include waits and are not elapsed-time or CPU-time shares.

Separate read-only thread observations bracket substantial combined workers at
**0.215–0.231 s**, versus baseline **0.228–0.246 s** and Rust **0.135–0.154 s**.
Main-thread CPU lower bounds are combined **0.207–0.208 s**, baseline
**0.217–0.218 s** and Rust **0.134–0.134 s**. Polling affects execution and the
bounds do not prove a precise causal reduction in startup. Worker activity is
uneven; five Mech workers finish much earlier than two, while Rust's work is
more evenly spread.

Fifteen separate counter executions give these medians:

| Configuration | Instructions billions | Cycles billions | User CPU s | Kernel CPU s | Involuntary switches |
|---|---:|---:|---:|---:|---:|
| Rust | 33.139 | 7.877 | 2.33 | 0.03 | 608 |
| Baseline | 26.577 | 7.260 | 2.07 | 0.04 | 6,540 |
| Scan fusion | 26.384 | 7.331 | 2.09 | 0.04 | 5,021 |
| Private metadata | 26.568 | 7.237 | 2.06 | 0.04 | 5,793 |
| Combined | 26.379 | 7.326 | 2.08 | 0.03 | 5,074 |

Memory and binary evidence identify concrete next hypotheses: share immutable
program metadata instead of reconstructing or cloning it, avoid unnecessary
loading/validation machinery in specialized standalone hosts while preserving
admission and capability checks, and reduce temporary input-preparation storage.
The generated scalar scanner and scheduling of unequal worker costs remain
other candidates. None is implemented or credited with a speedup in this report.
Reducing memory or static bytes does not by itself establish a reduction in the
approximately 0.14-second complete-process gap.

[Main preparation evidence](preparation.json),
[worker profiles](../preparation-combined-remaining-profile-v1/results.json) and
[whole-process counters](../preparation-interactions-hardware-v1/results.json)
retain the raw accounting and its limitations. The Rust stack profile used for
comparison is the earlier unchanged-binary reference, not a new capture.

## Qualification and reproduction

The combined revision passes **45 line-storage, 26 worker-budget, 379 native and
one catalog integration checks**, with three existing manually excluded native
tests. Every full-input Mech process verifies secured completion, seven complete
maps, seven peak workers, five admitted caches and **874,999,961 physical updates**.
Source, bytecode, input, launch-policy and canonical-data hashes are unchanged.
All native jobs run sequentially under the retained shared mutex. All owned
processes are reaped and process groups closed.

[Verification](../preparation-interactions-v1/verification.json) recomputes the
source matrix, both 100-process primary sessions, paired bootstrap estimates,
451 validation checks, exact-code profiles, counters, memory captures and binary
accounting. It checks **287 terminal process receipts**, including diagnostic
helpers. Run `python3 preparation-interactions-v1/verify.py` from this study
directory in the qualified local checkout to recompute the evidence. Build and
measurement drivers and the immutable plan are in
[`preparation-interactions-v1`](../preparation-interactions-v1/).

The earlier [scan-only](../line-offset-crlf-checkpoint-v1/README.md) and
[metadata-only](../disjoint-state-checkpoint-v1/README.md) outcomes remain retained.
Their standalone promotion decisions do not rule out useful combinations.
Canonical website benchmark data is unchanged. Rust parity, decoded-source
standalone qualification and secured/trusted startup comparison remain incomplete.
