# Retained Kotlin helper qualification

This diagnostic checks the independently retained `clbg.Support` class for each of the twenty Kotlin source profiles. It compiles one dedicated Java reflection probe against the retained JDK and runs it once per profile. It does not recompile a Kotlin subject, execute a benchmark main, collect benchmark timings, or qualify LOC.

The controller verifies the closed generic JVM receipt, the successful twenty-profile compile and class-owner evidence, and the source-owner review before execution. Original source, class, runtime, and receipt hashes remain authoritative. An archived class directory can be selected only through an explicit storage mapping whose complete artifact inventory matches the original compiler receipt. All inputs are checked again after the batch.

The probe system classpath contains only its two diagnostic classes. A separate loader admits `clbg.Support` and the pinned Kotlin standard library; every other `clbg` owner is rejected. Negative loader canaries, exact `Support` CodeSource and resource URLs, full class-load logs, VM identity and options, and G1 diagnostics accompany each result.

Each helper receives a real stdin pipe containing every byte value, repeated beyond two 65,536-byte blocks, with embedded NUL/CRLF and a suffix without a newline. Both `write` overloads emit to a real stdout pipe, drained to an exclusive artifact and compared byte for byte outside the JVM. Other checks cover repeated EOF, ISO-8859-1 conversion, eight integer acceptance cases, seven native exception cases, eight exact line-normalization cases, and 1,536 independently generated binary64 format vectors plus five invalid-input cases. The shared formatter vectors are regenerated from their pinned Python generator before use.

Every native command inherits the common timing mutex, runs in a new owned process group, and has a thirty-second deadline plus five seconds for cleanup. The leader remains unreaped until its group is empty, preventing PID reuse during cleanup. Start, active, final, partial-stream, compiler, runtime, class, and terminal receipts survive failures. The batch stops at the first failure; an existing output directory is never reused automatically.

Run with the pinned Python after the timing lane is free:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B -u tools/qualification/kotlin_helpers.py --output experiments/kotlin/helper-semantics/run-v1
```

Pure controller fixtures, without any compiler or JVM execution:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B experiments/kotlin/helper-semantics/test_kotlin_helpers.py
```

Success qualifies only the retained helper's formatting, argument/line handling, and raw I/O behavior. Actual benchmark dependency closure, workload output/work, JIT evidence, LOC, full timings, and chart admission remain separate open gates.

`run-v3/report.json` records successful checks for all twenty helpers, with one
diagnostic Java compilation and twenty fresh JVM probes. Its terminal receipt
retains the complete native outputs and input-integrity checks. No Kotlin
benchmark main executed. Earlier `run-v1` and `run-v2` retain supervisor and
class-log validation failures, their exact controller sources, and the separate
failure reviews; neither attempt is counted as a completed qualification batch.
