# Janet binary-trees results

Seven ordinary Janet workers reduce the full-depth process median from
**102.899 seconds (260.9× Mech AOT)** to **20.715 seconds (52.5×)**, an observed
**4.97× improvement within Janet**. All fifteen full-size samples match the
complete independent 455-byte output. Every form constructs and walks the same
613,766,494 node instances, including equally allocated leaves.

| Implementation | Median seconds | × Mech AOT | Maximum peak RSS across three samples |
|---|---:|---:|---:|
| Historical callable-array parent | 102.899 | 260.9× | 626 MiB |
| Cached direct access | 98.531 | 249.8× | 637 MiB |
| Two-level check | 93.109 | 236.1× | 533 MiB |
| Seven workers, cached check | 20.715 | 52.5× | 1.58 GiB |
| Seven workers, two-level check | 22.437 | 56.9× | 1.45 GiB |

**Allocation policies differ.** The requested denominator is the retained Mech
AOT median of **0.394411208 seconds (1.0×)**, profile
`binarytrees:mech-binarytrees-parallel`, which uses the general core library
pool with distinct 16-byte node slots and per-tree frame release. Janet uses
unchanged default GC and fresh mutable arrays. These ratios do not isolate
language/compiler throughput under the same allocator. Mech was not remeasured.

The fifteen observations are three shuffled sequential rounds across all five
sources at N=21. No valid observation is removed. The worker forms have scheduling
and GC variation; three samples do not establish a precise ordering between
them. The two-level serial form is consistently faster than the parent here,
but its worker form does not improve the observed median over the simpler
worker check. Both alternatives and all raw samples remain available. The
worker speedup costs higher peak memory and greater aggregate CPU time.
No globally fastest or smallest-source claim follows.

## Source measures

| Implementation | Physical rows | UTF-8 bytes | Deterministic gzip bytes | BPE tokens | Janet lexical tokens |
|---|---:|---:|---:|---:|---:|
| Parent | 22 | 946 | 479 | 283 | 197 |
| Cached direct access | 23 | 968 | 488 | 287 | 201 |
| Two-level check | 33 | 1,269 | 559 | 379 | 271 |
| Seven workers, cached check | 57 | 2,413 | 972 | 692 | 540 |
| Seven workers, two-level check | 66 | 2,649 | 1,003 | 772 | 610 |

The fastest observed median uses 540 lexical tokens versus the parent's 197,
about 2.74× the source tokens. All worker orchestration, job validation, error
handling, output and authored helpers are included. The unchanged standard
runtime/GC/thread library remains external. Physical rows and tokens are distinct
from pending normalized logical and canonical formatted LOC. Exact identities,
tokenizer/grammar versions and original author/license lineage are retained in
the source-measure and source-manifest JSON.

## Work, lifecycle and limits

The 66 bounded complete outputs and 66 diagnostic executions cover serial and
parallel forms, six input depths and 1,2,3,7 workers. Diagnostic identity tables
reject shared node instances; actual constructor and node-probe counters match
every main/worker partition. Two-level checks count child probes even when no
recursive function call is needed. The diagnostic tables change lifetime and
memory and are never timed subjects. All production constructors allocate the
complete tree before checking it, and retain the long-lived tree across jobs.
No node-count formula enters an application.

Another native check verifies 2,464 partition bounds against exact integer
arithmetic through full depth 21. An injected owned worker error fails with
only the previous stretch output, never partial depth summaries. The module-level
worker receives only numeric job descriptors and cannot capture main's local
retained tree. Standard runtime source inspection confirms that asynchronous
threaded subroutines keep event-loop references outstanding through worker VM
cleanup; the CLI drains those references. No native helper or runtime change
is introduced.

All fresh-process observations include source parsing, bytecode compilation,
VM/thread startup, complete allocation/traversal/output and process shutdown.
The common mutex prevents competing benchmark/validation runs. The owned
controller observes exit independently and then checks output, closes the group
and reaps the child. Nested `output_contract` records certify output alone;
process ownership and source work have separate evidence.

Power/process/memory snapshots occur before/after and periodically inside live
subject windows. Their ordinary host contention remains inside observed wall
time. Static source inspection and read-only published-source acquisition also
took place during the cohort. AC power and Low Power Mode off are observed;
no swap usage appears in the recorded host snapshots. These observations do not
prove continuous thermal/frequency conditions, a pristine idle host or absence
of activity between snapshots. No GC or power setting was changed. Results remain
exploratory and do not enter the public chart.

`verify.py` replays complete bytes, actual bounded allocation/visit records,
exact partitions, worker failure, full raw/summary observations, resource/power
records, source/runtime identities and closed process ownership. `seal.json`
hashes the study's retained artifacts. No canonical source, timing or count is
changed.
