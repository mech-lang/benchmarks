# Janet binary-trees workers and traversal study

This packet measures five local Janet implementations of the complete depth-21
binary-trees workload. Every implementation uses ordinary fresh mutable
2-reference arrays for leaves and interior nodes, with unchanged default GC.
There is no custom pool, free list, shared leaf, recycled subtree, node-count
formula or GC tuning in the application. The complete tree is built before its
check starts. The long-lived tree remains in the main function until the final
check after all short-lived work.

- `parent`: the historical v2 callable-array check and recursive constructor.
- `cached`: direct access with the left child retained across its branch/check.
- `unrolled`: the same check expanded over two levels. It reads every visited
  node's left field; nonleaf right fields supply the recursive descendants.
  Counting the three actually visited nodes is not a depth-based substitute for
  allocating or walking a tree. It supports mixed leaf depths in full binary
  trees, although the benchmark requires perfect trees.
- `threaded-cached` and `threaded-unrolled`: seven standard Janet workers divide
  the required tree iterations for every depth. The main thread retains the
  long-lived tree. Including main, there are at most eight application threads.
  Workers return integer checksums and completed-iteration counts. All worker
  IDs, depth order and completed counts are validated before printing summaries.

The module-level worker receives only `[depth workers id]`. It is not a closure
created inside main, so it cannot capture and serialize main's retained tree.
Each worker constructs, checks and releases its own trees using default GC.
The runtime/event-loop boundary is reviewed separately; no VM code is modified.

## Work and native qualification

At N=21, every form constructs and walks **613,766,494 distinct node instances**:
stretch and retained trees plus the exact prescribed short-lived trees at each
depth. Each tree's leaf nodes use the same allocator and memory shape as its
interior nodes. Reference formulas are confined to the independent checker.
Application checks always walk actual node references.

`qualify.py` checks the parent, cached and threaded/cached forms. The unrolled
follow-up uses `qualify_unrolled.py`. Across both packets, 66 complete outputs
and 66 diagnostic allocation/traversal executions pass at N=0,4,7,9,10,12.
Parallel forms use 1,2,3,7 workers, including nondivisible partitions. Each
projected execution counts actual constructor calls and actual visited nodes,
while a per-VM identity table rejects a shared node. The unrolled diagnostic
counts child probes as visits even when they do not enter a recursive function.
Main and every worker report separately; totals and individual partitions must
match the independent reference.

Diagnostic identity tables retain all bounded nodes and change their lifetime
and memory costs. They are never timing subjects. Worker diagnostic state is
reset in its own VM before building any job trees. The production sources have
none of these tables or counters. The shared constructor and both check forms
are pinned exactly in each projection.

`check_partitions.py` independently verifies 2,464 native division/floor bounds
for every depth from 6 through 21 and worker count from 1 through 7 against exact
integer arithmetic. Every required iteration has exactly one owner, including
remainders. `check_failure.py` injects an owned worker error and requires exit 1,
the explicit error and only the previously written stretch line. No depth
summary can appear on a worker failure.

## Measurement and comparison limits

`full.py` performs three shuffled sequential rounds across all five sources,
always N=21, under the common benchmark mutex. Source parsing, bytecode
compilation, VM/worker startup, all allocations/traversals, output and process
shutdown are inside each fresh-process interval. The inherited owner establishes
birth identity before exec, observes exit independently, captures macOS `wait4`
resources, closes the group and reaps the child. Output checking and group
cleanup follow exit. Complete small stdout/stderr captures are retained.

Read-only power/process/memory snapshots run before/after subjects and periodically
while subjects live. Their ordinary scheduling/I/O contention is inside observed
wall time; a later callback cannot directly extend the independent exit timestamp.
Read-only source/provenance inspection also took place during this cohort.
No other benchmark, language compilation or native validation ran concurrently.
Continuous temperature/frequency and a pristine idle host are not established.
No power setting or GC setting is changed and CPU throttling is not disabled.
Memory/swap snapshots are host observations, not per-process allocation traces.

The requested ×Mech AOT ratios use the retained same-input median of
`binarytrees:mech-binarytrees-parallel`. That Mech program uses a **general core
library pool**, distinct 16-byte node slots and per-tree frame release. Janet
uses **default GC**. This is not a matched allocation-policy comparison, and the
ratios must not be described as isolating language/compiler throughput. Mech is
not freshly remeasured in this cohort. No Janet chart admission is made.

## Source measures and reproducibility

All authored orchestration, validation and helpers are application source.
Unmodified standard VM/GC/thread libraries remain external. `measure.py` records
physical rows, UTF-8 bytes, deterministic gzip, pinned BPE and native grammar
lexical tokens. These remain separate from pending normalized logical and
canonical formatted LOC. Both threading variants and serial tradeoffs are
retained; no globally fastest or smallest program claim follows.

The source manifest preserves parent authors, original consulted programs,
Apache-2.0/BSD notices and exact files. Local authoring identifies Codex GPT-6
family; the exact serving model is unknown. Reproduce in a clean output directory
with the pinned runtime present and no competing native jobs:

```sh
python3 experiments/janet/binarytrees-workers-v1/qualify.py
python3 experiments/janet/binarytrees-workers-v1/qualify_unrolled.py
python3 experiments/janet/binarytrees-workers-v1/check_partitions.py
python3 experiments/janet/binarytrees-workers-v1/check_failure.py
python3 experiments/janet/binarytrees-workers-v1/full.py
experiments/source-metrics/.build/venv39/bin/python experiments/janet/binarytrees-workers-v1/measure.py --run
python3 experiments/janet/binarytrees-workers-v1/verify.py
```

Workload: https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/binarytrees.html
