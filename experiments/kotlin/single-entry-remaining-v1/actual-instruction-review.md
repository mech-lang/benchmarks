# Retained optimized-tree and compact-pi execution paths

The remaining-three capture stopped after two native processes. The optimized
tree completed its capture gate; compact pi completed its prescribed execution
but failed the gate requiring an installed JIT version of `main`. Optimized pi
was never started. The original report and terminal remain failed. These saved
executions are diagnostic evidence, not timing samples.

The [evidence index](actual-instruction-review-evidence.json) records the exact
artifact, source and class hashes, complete native-code coverage, and observed
compilation identities used below. This review is additive to the
[first compact-tree review](first-capture-reconciliation.md). It does not grant
source-work qualification, full measurement eligibility or chart admission.

## Process ownership and output

The [plan](plan-v1.json) SHA is
`c56c0e576b4dca9c7867ae2ef66eeddd2a822d43eb130a188d01c2602a4fdf0f`.
The [report](run-v1/report.json) SHA is
`6602c54ba432d58dc9eca543c1984f3632f3ae02f9659c12d388daf02e951a96`;
the [terminal](run-v1/terminal.json) SHA is
`27d43373ff5a30a96ba6682edd1e68daf88170614b110546cbac600d700bb2c9`.
The [durable terminal](../dispatch-v1/owned-jobs/single-entry-remaining-three-v1/terminal.json)
SHA is `0866dfe66db63fca769a2a3a422116cb017121685936d3c8fae6c1500d0c22d7`.

The durable worker was PID 57899 and the controller was PID 57903. The two JVMs
were PID/PGID 57905 and 57906. Both receipts record exit zero, direct-child
reaping, matching birth/parent/group identities before reaping, an inherited
timing mutex with inode 79859134, and no stop signal, cleanup error or remaining
process group. The controller exited one without retry after the capture
assertion. Its terminal reports no integrity, receipt, remaining-receipt or
artifact errors.

Both commands used `-XX:ActiveProcessorCount=8 -Xms64m -Xmx8g -XX:+UseG1GC`,
direct launcher entry, the retained classes and Kotlin library, and the planned
diagnostic options. The saved VM properties and class origins agree with those
commands. The observer bounds were 30 seconds, 10 GiB process-group RSS, 8 MiB
per native file and a five-second cleanup timeout. Observed peak RSS was
1,325,645,824 bytes for tree and 156,237,824 bytes for pi.

Tree stdout is exactly the prescribed 455 bytes, SHA
`341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1`.
Pi stdout is exactly the prescribed 16,893 bytes for 10,000 digits, SHA
`bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c`.
Both stderr streams are empty. Each `os.log` contains only the known optional
hsdis warning, at 0.053 seconds for tree and 0.031 seconds for pi; neither warning
appears in subject stdout. Both GC logs identify G1. The saved receipt, VM,
class-origin, output and OS-log validators pass when replayed with the retained
controller PID. The tree capture index and validated artifact snapshot also
replay exactly. This review reads saved evidence and small subject files; it
does not repeat the producer's full runtime-closure verification.

## Optimized-tree allocation and lifetime

The actual tree [HotSpot XML](run-v1/kotlin-binarytrees-optimized/hotspot.xml)
SHA is `d39da1d75f6768d5d4ef49c6018b48afe3c0eab19c942e1a4e5d4d2bb08d2862`.
Its installed subject captures are:

| Compile ID | Method and entry | Complete main-code bytes |
| --- | --- | ---: |
| 81 | tree, C1 normal | 1096 |
| 83 | tree, C2 normal | 2280 |
| 87 | check, C1 normal | 808 |
| 90 | check, C2 normal | 448 |
| 122 | main, C1 OSR at BCI 81 | 13264 |
| 123 | main, C1 normal | 12992 |
| 124 | main, C2 OSR at BCI 81 | 3480 |
| 153 | main, C1 OSR at BCI 81 | 18832 |
| 154 | main, C2 OSR at BCI 81 | 3848 |

Every advertised native main-code byte is retained, with OopMaps. There is no
C2 normal-entry `main` and no `Node` elimination record. The following evidence
comes from this invocation's instructions, not from the identically authored
compact form or the earlier repeatedly warmed witness.

* C2 tree 83 at `0x1181502ec` loads the thread's allocation top, computes top
  plus 24, compares against the allocation end, advances the top and initializes
  the `Node`. For example, `0x1181502f4` contains `add x12, x0, #24` and
  `0x118150304` stores the new top. The zero-depth path has its own allocation
  at `0x11815062c`. Capacity failures branch to the annotated `new_instance`
  runtime calls, including `0x118150688` and `0x1181506ac`.
* Recursive calls at `0x11815037c` and `0x118150394` branch to tree entry
  `0x1181502c0`. The OopMaps retain the outer root, in-progress child and
  completed subtree in `[0]`, `[16]` and then `[24]`. The corresponding
  right-subtree calls at `0x118150470` and `0x118150488` additionally retain
  `rfp`. Child-pointer stores and G1 barriers follow; the leaf path initializes
  the child fields to zero. Recursion and object construction survive together.
* C1 main 122's OSR entry imports the existing long-lived tree from migration
  slot 72 at `0x1106949c4`, preserves it through the migration call and stores
  it in stack slot `[456]` at `0x110694a58`. Its emitted pre-loop body also
  stores the result of `tree@52` in that slot at `0x110693164`; the OSR path
  does not need to repeat that earlier construction. The slot is an Oop at the temporary-tree
  constructor `0x1106931a4`, checker `0x1106931d0`, inner poll
  `0x110693210`, output calls and outer poll `0x1106933e4`. The terminal path
  reloads it at `0x110693404`, moves it to the checker argument and calls
  `check@140` at `0x110693458`.
* C2 OSR main 124 imports the existing long-lived tree in `x24` at
  `0x118153cf4`, checks its `Node` class at `0x118153d58`, and retains it as
  `rlocals` in the loop-poll maps at `0x118153d88` and `0x118153ee0`.
  Call spills retain it in stack slot `[16]`. Its temporary-tree fast paths
  explicitly allocate and initialize Nodes; fallback allocation and recursive
  paths carry corresponding OopMaps. Its loop-exit uncommon trap retains the
  long-lived root in `[16]` for interpreter continuation.
* C2 OSR main 154 imports that tree in `x25` at `0x118155ef4`, checks its
  class at `0x118155f5c`, and moves it to `x13` at `0x118155f6c`. The inner
  poll `0x1181560c4` maps `r13`. Across checker calls the root is spilled in
  `[16]`; across recursive tree calls it is in `[32]`, with matching OopMaps.
  Output construction retains it in `[8]`, including `0x11815668c`,
  `0x1181567b0` and the outer poll `0x1181567c8`. At `0x118156804` it is
  reloaded into the checker argument for the final `check@140` call at
  `0x118156808`. It can cease to be live after that final use.

Both C2 OSR versions were entered: compile 124 reports a runtime
`unstable_if` trap at BCI 86 at 0.389 seconds; compile 154 reports an
`uninitialized` trap at BCI 143 at 1.695 seconds, after the final check. Main's
recorded invocation count is one. These observations support surviving tree
construction and long-lived-root retention for this fresh invocation. The
earlier warmed normal-entry C2 allocation eliminations are a different
execution path and are not attributed to this capture.

## Compact-pi interpreted caller and compiled divisions

The actual pi [HotSpot XML](run-v1/kotlin-pidigits-compact/hotspot.xml) SHA is
`312494cdf55a369307a30eb137d43ec02312817512d18f25d668fac13c6b2bf8`.
It is a closed, well-formed log with `hotspot_log_done` at 3.777 seconds. It
contains 220 queued compilations, 220 compilation tasks and 252 installed
nmethod records. There is no queued task, compilation task, installed normal
or OSR nmethod, or compiler method reference for `clbg.pidigits.MainKt.main`.
The only subject method compiled or referenced by compiler tasks is `big`, in
C1 compile 137 and C2 compile 209. No `failure`, `code_cache_full` or
`make_not_compilable` event appears. Thus this invocation supplies an interpreted
caller path, not a compiled `main` whose instructions were lost.

The actual loaded `MainKt` origin is the pinned compact class directory.
Its class SHA is
`e9053276207d5211a8ea166af93f8e77a66ec395467eebf879b4da171f2c7456`;
the retained [javap record](../additive-compile-owners-v1/kotlin-pidigits-compact/owners/javap.stdout)
includes that same class checksum and has SHA
`a787ea2b45d9fef3c89e0aa64e82bd4b45587b882982178801a57b326db33fd7`.
The actual source copy SHA is
`19685b96cc0e7ec10bbab086f55d1b3d8bfb06268e1c9685d1772dcd9d65b9a6`.

The retained main bytecode establishes the loop path:

| BCI | Required operation |
| ---: | --- |
| 48–51 | Check emitted digits against the runtime request; exit at 542 |
| 54–122 | Construct `3*q+r`, then invoke general `BigInteger.divide(t)` at 122 |
| 133–201 | Construct `4*q+r`, then independently invoke `BigInteger.divide(t)` at 201 |
| 212–219 | Load both results and compare with `Intrinsics.areEqual` at 216 |
| 381 / 388 | Accepted-digit branch returns to loop head 48 |
| 539 | Refine-state branch returns to loop head 48 |
| 542–559 | Write the complete accumulated result and return |

Both divide instructions dominate the comparison; there is no branch or
exception handler bypassing either divide into the comparison. With no
compiled or inlined caller, the interpreter executes those two separate calls
on every reached comparison. A compiled callee does not eliminate a second
invocation across an interpreted caller. This establishes the required paired
general-division path without forcing artificial repeated-main warmup. It does
not claim an observed numeric total of loop iterations or divisions.

`BigInteger` was loaded from the retained runtime's shared objects and
`MutableBigInteger` from `jrt:/java.base`. All eight installed division captures
have complete machine bytes:

| Compile ID | Compiler | Method | Main-code bytes |
| --- | --- | --- | ---: |
| 146 | C1 | MutableBigInteger.divideMagnitude | 7744 |
| 153 | C1 | BigInteger.divide | 648 |
| 154 | C1 | BigInteger.divideKnuth | 2000 |
| 156 | C1 | MutableBigInteger.divideKnuth | 4832 |
| 172 | C2 | MutableBigInteger.divideMagnitude | 6256 |
| 216 | C2 | BigInteger.divide | 3360 |
| 221 | C2 | BigInteger.divideKnuth | 3176 |
| 222 | C2 | MutableBigInteger.divideKnuth | 1528 |

The frozen capture gate required an installed `main` nmethod before emitting a
capture index. That expectation explains its failure here; neither the missing
index nor the failed status is rewritten. An additive continuation can retain
this interpreted-caller proof and capture only the unstarted optimized pi.
Qualification of all retained profiles remains a separate review of the closed
evidence, including the future optimized-pi execution. No result is inferred
for that unobserved form.
