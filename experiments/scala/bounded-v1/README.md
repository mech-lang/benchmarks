# Scala bounded output qualification

This source-only controller prepares 149 serial correctness executions using
the exact retained Scala 3.10.0 application classes. It has not executed. A
successful closed [application compilation](../compiled-applications-v1/README.md)
report and terminal are required before any plan can be prepared.

[scala_bounded.py](../../../tools/qualification/scala_bounded.py) independently
checks all ten source/class bindings, twenty compiler and bytecode-reader
lifecycles, direct `Main` entrypoints, generated class inventories, the two Scala
runtime jars and inherited JDK/toolchain pins. Original `.scala` source files,
compiled copies, `.class`/`.tasty` files and complete compiler evidence remain
bound throughout the bounded stage. No compiler, shell, Scala CLI or benchmark
wrapper is invoked by this stage.

The [shared corpus](../../shared/bounded-corpus-v1/README.md) supplies 149 exact
cases: 142 successful outputs and seven invalid reverse-complement inputs.
Original case order, arguments, input bytes and expected outputs are retained.
The frozen [output checker](../../../tools/qualification/scala_typescript_outputs.py)
requires exact successful bytes except N-body's two finite nine-decimal energy
lines, compared within ten integer nanounits. Missing or changed reference
bytes fail the case.

Each application is a fresh direct Java process with `Main` as its entrypoint,
an isolated home and temporary directory, and the exact classpath containing
its retained classes plus `scala3-library_3-3.10.0.jar` and
`scala-library-3.10.0.jar`. JVM options are `-XX:ActiveProcessorCount=8`,
`-Xms64m`, `-Xmx1g` and `-XX:+UseG1GC`. Compilation is excluded. The frozen
observer enforces a 30-second process deadline, five-second cleanup, 2 GiB
observed process-group RSS and an 8 MiB native-file bound. All commands run
sequentially under the existing common timing mutex. There is no automatic
retry or resume.

The observer records normal exit 1 as a failure. For exactly the seven invalid
IUPAC cases, an additive check requires that specific exit-1 assertion, exact
command/input/environment, original birth identity, direct-child reaping,
empty remaining process group and no timeout, signal or cleanup failure. It
then checks empty stdout and the source-defined `IllegalArgumentException`
diagnostic containing the expected invalid byte and direct `Main` stack.
Unexpected diagnostics, unrelated exceptions and abnormal exits remain failures.
Raw observer receipts are never rewritten or relabeled.

Signals enter owned-group cleanup. Finalization blocks interruptions while
retaining report and terminal evidence. Artifact snapshots bracket every case
validation; final inventories must contain those exact accepted bytes, including
nested receipts. Input pins, class inventories, compilation evidence and mutex
identity are rechecked before the terminal can claim success. A failed stage
retains all observed attempts and does not execute the remaining cases.

The commands require retained Python with `-I -S -B` and physical absolute
paths. Plans are prepared only after native compilation and independent review:

```text
scala_bounded.py prepare --compiled-report <closed-report.json> --compiled-report-sha256 <sha256> --compiled-terminal-sha256 <sha256> --plan <fresh-plan.json> --output <fresh-bounded-output>
scala_bounded.py run --plan <reviewed-plan.json> --plan-sha256 <sha256>
```

Success establishes only the 149 bounded output contracts. Required surviving
work, full-size feasibility, runtime performance and chart admission remain
unqualified. This controller does not admit canonical or formatted source
counts; those are separate source-reader results.
