# Kotlin single-entry native work capture

This prepared diagnostic targets the remaining tree-allocation and pi-division
questions in the [actual compiled-work review](../compiled-work-v1/single-entry-review.md).
It starts four fresh JVMs: binary trees at 21 and pi digits at 10,000, separately
for the retained compact and optimized aliases. Each command launches the
original `MainKt` directly once. No subject, helper, or diagnostic compilation
occurs; the twenty-form warmup cohort is not repeated.

The controller is [kotlin_single_entry.py](../../../tools/qualification/kotlin_single_entry.py).
It binds the completed compiled-work report/terminal and their original runtime,
source, class, output-prerequisite, and native-receipt closures. Preparation and
execution both hold the existing timing mutex at inode 79859134. The pinned
`kotlin_bounded_v2.py` supervisor retains atomic native-start registration,
birth/parent/group checks, process-group memory monitoring, bounded cleanup,
reaping and partial output receipts. The explicit
[single-entry observer revision](../../../tools/qualification/kotlin_single_entry_supervisor.py)
loads those immutable lifecycle definitions in a separate module and changes
only the observer RSS ceiling from 2 GiB to 10 GiB. The original prerequisite
validator retains its 2 GiB bound. Other bounds remain 30 seconds per JVM,
8 MiB per native file, and five seconds for cleanup.
There is one live subject process and no retry.

The 10 GiB observer ceiling matches the retained Clojure full-study binary-trees
manifest's `maximum_rss_mib=10240`, with the same retained JDK, 8 GiB heap and G1.
That completed study's six Clojure samples at input 21 recorded 922,256–1,823,696
KiB peak process-group RSS. Those measurements do not establish a 2 GiB bound for
Kotlin's different trees. Ten GiB permits the scored 8 GiB heap plus native
memory without silently changing any JVM option. The cited original evidence is
`clojure-comparison/20261012/studies/full-v1/binarytrees/{manifest,report}.json`
under the retained CLBG root; this is resource-policy context, not transferred
Kotlin work or timing evidence.

## Capture capability and output

The [retained-file capability audit](capture-capability.md) identifies the
diagnostic flags and output machinery present in the exact retained JVM.
The [machine-readable audit](capture-capability.json) records its original pins.
This is a source/file audit, not a successful native capture.

The commands preserve `ActiveProcessorCount=8`, `Xms64m`, `Xmx8g`, G1, tiered
compilation policy, original classpath, and the sanitized retained environment.
They add `LogCompilation`, `LogVMOutput`, `DisplayVMOutput=false`, and targeted
`CompileCommand=print` requests. `CompileCommand=quiet` suppresses command
announcements. Tree captures request main/tree/check; pi captures request main
and the BigInteger/MutableBigInteger divide method families. No compile-only,
forced inlining, threshold, escape-analysis, collector, or heap-policy override
is used.

VM diagnostics must be retained in `hotspot.xml`; subject stdout remains the
exact complete prescribed output and stderr must remain empty. The absence of
hsdis does not imply absence of native instructions: the retained JVM supports
abstract machine-byte output. Readable assembly mnemonics are not assumed.
Every relevant installed nmethod must have its matching `print_nmethod` body
with instruction bytes; subject methods must also have OopMap records. Missing
or truncated XML, missing prints, unsupported actual output structure, JVM
identity mismatch, unexpected stdout/stderr, or a resource failure stops the
attempt with its original receipts. A failed capture is not retried or recast
as successful proof.

The bytecode review and preserved constructor witness already establish graph
shape and authored control flow. Native review must now map the emitted tree
allocation sites and references through safepoints, and the two pi division
paths through each candidate comparison. The capture index records compiler
IDs, C1/C2/OSR identity, native instruction/OopMap availability, and explicit
Node allocation-elimination stacks. An installed Node elimination stops the
stage and retains the counterexample for review of entry reachability; a
compiler record alone is not claimed to be an exact executed-node counter.
An elimination from a failed/uninstalled compilation is recorded separately.
Absence of elimination records does not automatically qualify allocations.

## Commands and status

Source preparation is complete only after review of the controller, tests and
capability audit. No native execution is claimed by this packet. From the
repository root, use the retained interpreter with `-I -S -B`:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/kotlin_single_entry.py prepare --plan experiments/kotlin/single-entry-work-v1/plan-v1.json --output experiments/kotlin/single-entry-work-v1/run-v1
```

Preparation performs full pin/terminal verification under the mutex and emits
the concrete plan SHA without starting a native process. Review that exact plan
before passing its emitted SHA to:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/kotlin_single_entry.py run --plan experiments/kotlin/single-entry-work-v1/plan-v1.json --plan-sha256 PLAN_SHA_FROM_PREPARATION
```

A complete capture receives `all4-native-captures-awaiting-instruction-review`.
That status asserts four closed capture commands and complete output, not
machine-code semantic qualification. Source-work, optimized-main allocation,
runtime pi-division counts, full timings, and chart admission stay false until
the actual instructions and roots are reviewed. Diagnostic wall times are not
benchmark samples. A proven work failure requires a separately qualified source
revision or an explicitly disclosed different runtime cohort; it cannot be
fixed by relabeling the preserved evidence.
