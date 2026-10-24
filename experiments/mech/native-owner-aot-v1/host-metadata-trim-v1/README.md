# Compact native library metadata

Candidate `e939c8002793c03cf63a31eeb13dd78fb8855064` on
`codex/native-host-startup-trimming` removes duplicate selected-call metadata and
redundant owned decoding during application startup. It builds on the retained
preparation combination `e82ed4d54d4490102ac41192d1fcbf492d467e08`; both preparation
factors and the accepted PR baseline remain available separately.

The candidate is retained. Complete-process medians improve **1.86% initially
and 1.06% in a separate repeat**. The repeat paired interval includes zero, so
a precise repeatable gain is not established. Descriptor loading falls about
**0.8 ms**; the host is a small part of the remaining Rust performance gap.
No validation or capability check is removed, and canonical benchmark data is
unchanged. Rust parity remains incomplete.

## Implementation and preserved behavior

`NativeProgramLibraryTemplate` previously retained a second deep copy of the
schemas, contract, operation key, revision and origin already owned by its
selected root/lexical leaf. Native-enabled builds now read those properties
from the selected owner. Featureless builds retain their previous representation.
The custom serializer preserves every existing wire field and its order.

The build-image reader borrows redundant outer JSON fields for equality checks
instead of decoding another owned selection tree and contract. Exact field and
tag inventories, origin checks, canonical schema finalizers, contract validation
and actual linked-factory witnesses remain. Execution still performs fresh
capability/resource admission, finite work and memory accounting, current-site
checks and secured shutdown.

The application build verifies that **native Object, Object identity, bytecode,
descriptor JSON, compressed descriptor and resource metadata are byte-identical**
to the parent. IR79, ABI28 and work policy66 remain unchanged. No workload name,
input-specific implementation, worker-count, power, affinity or QoS change is
introduced. The Mech performance source is unchanged.

## Complete-process results

The [plan](plan.json) was committed before validation/timing at
`de48812c9563b7c0843d8ff5a7194623ffe15ea7`. Each session uses all six balanced
sequential orders of exact upstream Rust #7, the combined parent and the compact
candidate, with fresh secured startup through process exit. All 36 full-input
observations are included, without excluded warmups or outliers. The input has
125 million selected bases. Sessions are reported separately.

| Configuration | Session 1 seconds | × Rust | Session 2 seconds | × Rust |
|---|---:|---:|---:|---:|
| Rust | 0.5507 | 1.000× | 0.5503 | 1.000× |
| Combined parent | 0.7039 | 1.278× | 0.7068 | 1.284× |
| Compact metadata | 0.6908 | 1.254× | 0.6993 | 1.271× |

All six matched pairs favor the candidate initially, versus four of six in the
repeat. Median paired log-ratio changes are **−1.86% [−3.30%, −0.69%]** and
**−1.40% [−3.73%, +1.11%]**, respectively. These descriptive 95% bootstrap
intervals resample whole matched orders, 20,000 times with fixed seeds. They are
not the ratios of marginal medians and do not remove any observations.

The separate one-million-base prefix has one excluded warmup and three measured
complete processes per executable: Rust **0.01179 s / 1.000×**, parent
**0.09758 s / 8.278×** and candidate **0.08451 s / 7.169×**. This single small
batch is not a repeatable-prefix claim and is not pooled with full-input results.

[Session 1](../full-host-metadata-trim-v1/results.json),
[session 2](../full-host-metadata-trim-v2/results.json) and
[prefix/build qualification](../host-metadata-trim-timing-v1/results.json)
retain the observations, hashes, standard deviations and native reports.

## Host startup phases

A diagnostic-only copy of the generated host records monotonic markers, keeping
the same checked Object and all startup/validation paths. Markers alter host
machine code and therefore are excluded from primary timings. Each revision
has three full-input and three prefix diagnostic processes. No timings from
instrumented hosts replace primary observations.

Full-input diagnostic phase medians are:

| Host phase | Parent milliseconds | Candidate milliseconds |
|---|---:|---:|
| Catalog construction | 0.068 | 0.070 |
| Descriptor restoration and identity | 7.801 | 7.042 |
| CLI runtime construction | 0.074 | 0.075 |
| Native session preparation | 0.212 | 0.210 |
| Input capture | 151.511 | 151.070 |
| Native resume, including computation | 539.726 | 523.251 |

Descriptor restoration drops about 9.7%, only 0.76 ms in absolute terms. Catalog,
provider and capability runtime construction are already sub-millisecond.
Input capture and native resume dominate these instrumented executions; resume
includes preparation, counting workers and publication rather than only host
startup. Separate captures have different scheduling and cannot establish which
phase caused the complete-process gain. Prefix resume direction reverses in
these instrumented captures, reinforcing that limitation.

The original phase audit also records about 15 ms before the host's run routine
in full-input diagnostics. This upper bound includes supervisor/fork/exec and
loader work, not an isolated cost attributable to support-code size.

[Parent phase audit](../host-startup-audit-v1/results.json),
[candidate phase audit](../host-startup-audit-v2/results.json) and their copied
diagnostic source preserve the exact markers, raw timestamps and build pins.
The initial diagnostic setup attempt failed before starting any native process
because an edit anchor also matched test code; its script/output remain retained
in `host-startup-audit-v1-setup-attempt1`.

## Memory and binary size

MB denotes 1,000,000 bytes. Memory values below are medians of each original
timing process's macOS `wait4` peak RSS, six observations per configuration in
each separately reported session.

| Configuration | Session 1 peak RSS MB | Session 2 peak RSS MB | File MB | Machine-code MB |
|---|---:|---:|---:|---:|
| Rust | 141.04 | 140.44 | 0.756 | 0.347 |
| Combined parent | 161.72 | 161.93 | 5.501 | 4.334 |
| Compact metadata | 161.16 | 161.54 | 5.468 | 4.304 |

The candidate saves **33,152 file bytes / 0.60%** and **30,068 machine-code
bytes / 0.69%**. The emitted 114,672-byte Mech Object is unchanged. These are
the actual timed executables; a symbol-preserving profile binary's larger
on-disk file is not used as shipped size. Reserved address space and zero-fill
are not counted as disk bytes or resident memory.

Peak RSS falls only **0.56 MB initially and 0.39 MB in the repeat**. A separate
content-free worker-entry snapshot finds parent **8,923 live blocks / 127.08 MB**,
candidate **7,808 / 127.47 MB**, and Rust **455 / 141.23 MB**. Each owned process
is stopped only for `vmmap`/`heap` summaries, resumed, and checked for complete
output. These sampled heaps have unequal worker progress, are not RSS peaks or
allocation-churn counts, and do not isolate exactly how many blocks the source
change removes. Allocator retention limits the RSS benefit from fewer owners.

[Diagnostic size and memory accounting](../host-metadata-trim-diagnostics-v1/results.json)
contains raw byte sizes, sections, identical-code symbol attribution and heap
receipts. The broader [memory/binary audit](../preparation-combined-checkpoint-v1/README.md)
retains all four earlier configurations and instrumented allocation callers.

## Fresh profiles and counters

Three completed profiles match the timed candidate's entire machine-code
section. Across 4,708 worker stack observations, 70.58% are generated counting
loops, 16.50% active work accounting, 0.81% budget waits, 7.94% storage helpers,
2.10% generated/helper bridges and 2.06% other locations. These include waits;
they are stack-location shares, not elapsed-time or CPU-time shares. The earlier
unchanged Rust profile remains a reference, not a new capture.

Nine separate counter processes, three per executable, give:

| Configuration | Instructions billions | Cycles billions | User CPU s | Kernel CPU s | Involuntary switches |
|---|---:|---:|---:|---:|---:|
| Rust | 33.155 | 8.022 | 2.38 | 0.03 | 571 |
| Combined parent | 26.403 | 7.516 | 2.17 | 0.04 | 6,277 |
| Compact metadata | 26.378 | 7.243 | 2.06 | 0.04 | 6,598 |

Instructions fall about 0.09% and cycles about 3.62% in this small diagnostic
batch. Kernel CPU does not improve, and involuntary switches increase. Counters
sum across threads; centisecond-rounded diagnostic elapsed times are not
substituted for primary measurements.

[Fresh worker profile](../host-metadata-trim-remaining-profile-v1/results.json)
and [counter observations](../host-metadata-trim-diagnostics-v1/results.json)
retain raw evidence. The remaining approximately 0.15-second elapsed gap calls
for larger input-preparation and worker-execution improvements. Removing all
measured descriptor-startup cost would not close it.

## Verification and retained state

The exact source revision passes **82 engine native-artifact checks, 379 native
host/stdlib checks, one catalog integration check and two template-image
compatibility/rejection checks: 464 total**, with three existing manual native
exclusions. The no-default-feature engine build also passes. Tests preserve
malformed/forged metadata rejection, canonical wire shape, source continuations,
exact finite-accounting behavior and changed inputs.

Every full Mech execution verifies complete output, seven complete maps, seven
peak workers, five admitted caches and **874,999,961 physical updates**. All
native jobs run serially under the retained shared lock with clean unchanged
compiler source. [Verification](verification.json) recomputes both timing
sessions, paired estimates, exact build-input equality, phase records, binary
sizes and **97 terminal, reaped, closed-group process receipts**, including the
parent phase reference and all diagnostic helpers.

Run `python3 host-metadata-trim-v1/verify.py` from this study directory in the
qualified local checkout to recompute the retained evidence. Build and native
test toolchain settings are in the compiler/build receipts; source, input,
policy, binary and dependency pins accompany each run. The immutable plan and
all validation, measurement, profile and analysis drivers are retained here.

The candidate stays on its separate pushed branch. The earlier combined
configuration and accepted baseline are preserved. No website timing entries
or other-language measurements are replaced by this experiment.
