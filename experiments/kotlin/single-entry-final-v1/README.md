# Final Kotlin single-entry capture

This additive capture stage reuses three completed direct-main executions and
starts only `kotlin-pidigits-optimized` at input 10000. The compact and optimized
tree executions and compact pi execution are not repeated. Earlier reports keep
their original failed status and their artifacts remain unchanged.

The first capture stopped because an identified VM warning preceded otherwise
complete benchmark output. The second capture completed two native executions,
then stopped because the observer required a compiled pi `main`. Its complete
HotSpot log instead records an interpreted main and compiled general BigInteger
division methods. The [instruction review](../single-entry-remaining-v1/actual-instruction-review.md)
and [evidence index](../single-entry-remaining-v1/actual-instruction-review-evidence.json)
describe the actual saved allocation, GC-root and division evidence.

The [controller](../../../tools/qualification/kotlin_single_entry_final.py)
imports the exact frozen previous controller and byte-row parser. Preparation
reconciles both failed attempts, their precise failure boundaries, complete
artifact inventories, durable command identity, process birth/parent/reaping,
output bytes, OS diagnostic routing, actual class origins and VM identity. It
inherits all runtime, source, compiler and class bindings. The new plan also pins
the independent review, controller, tests, documentation and retained interpreter.

The final JVM uses the existing compiled optimized classes, retained JDK and
stdlib, one direct launcher entry and the same diagnostic options. The scored
flags remain `-XX:ActiveProcessorCount=8 -Xms64m -Xmx8g -XX:+UseG1GC`.
The existing common mutex, 30-second deadline, five-second cleanup deadline,
10 GiB process-group RSS limit, 8 MiB file limit and owned process supervision
remain in force. There is no warmup wrapper, subject compilation, threshold
change or automatic retry. Preparation and execution each hold the same common
mutex continuously. Preparation requires fresh plan and output paths; execution
consumes the existing pinned plan and requires that its output path is still fresh.

Pi capture accepts either of two observed execution paths:

- If main remains interpreted, the complete compilation log must contain no
  queued task, compiler task, installed nmethod or inline-method reference for
  main. Every compiler task must close successfully and link to its queued and
  installed records. Actual loaded classes, pinned source, current class bytes
  and retained disassembly must agree. A bytecode control-flow check requires
  both ordered general `BigInteger.divide` invokes to dominate every comparison,
  with all loop backedges returning before the two invokes and no exception
  handlers entering the loop.
- If main compiles, every installed main version must retain its complete
  machine-code byte range and OopMaps. A reference from another compiled caller
  requires separate caller evidence and fails this narrow capture.

Both paths require complete bytes for every installed targeted general-division
method. Capture completeness does not establish a numeric runtime division
count or qualify native instructions automatically. Independent semantic review,
full source-work qualification, timing qualification and chart admission remain
false. Finalization checks the exact one-process ledger, output snapshots and
all inherited pins, including a second pin check after the artifact inventory.

No plan or native execution is created by importing the module or running the
[pure tests](../../../tools/qualification/test_kotlin_single_entry_final.py).
Preparation and the one permitted capture must be scheduled through the retained
serialized execution lane and durable launcher. A failed final attempt requires
an explicit new evidence review; it is never retried by this controller.

The physical preparation command is:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/kotlin_single_entry_final.py prepare --plan /private/tmp/mech-benchmark-completion/experiments/kotlin/single-entry-final-v1/plan-v1.json --output /private/tmp/mech-benchmark-completion/experiments/kotlin/single-entry-final-v1/run-v1
```

For execution, the unchanged durable launcher receives this command array with
`<PLAN_SHA>` replaced by the printed preparation digest, the physical checkout
as its working directory and a fresh `single-entry-final-pi-v1` job name:

```json
["/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12", "-I", "-S", "-B", "-u", "/private/tmp/mech-benchmark-completion/tools/qualification/kotlin_single_entry_final.py", "run", "--plan", "/private/tmp/mech-benchmark-completion/experiments/kotlin/single-entry-final-v1/plan-v1.json", "--plan-sha256", "<PLAN_SHA>"]
```
