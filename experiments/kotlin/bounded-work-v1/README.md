# Retained Kotlin bounded-main preparation

This is a new, unexecuted diagnostic stage. It checks the actual retained Kotlin
`MainKt.main(String[])` in 156 fresh JVMs: 78 closed reference cases for each of
the compact and optimized forms. No Kotlin subject is recompiled. One new Java
diagnostic wrapper is compiled once with the original retained JDK `javac`.

The controller is `tools/qualification/kotlin_bounded.py`; the observer is
`BoundedProbe.java`. Both `prepare` and `run` acquire the existing common mutex
`/tmp/mech-clbg-timing.lock`, inode **79859134**, nonblocking. Neither command
should be started while any benchmark timing batch is active. A busy or replaced
mutex aborts. A fresh plan and output directory are mandatory; no retry or
successful-case replay is automatic.

## Bound evidence and case inventory

The compile receipt is
`experiments/kotlin/additive-compile-owners-v1/preparation-result.json`, SHA-256
`2ab7206a97782975827c743453bfdfee1c4a9f4c95c926a55b157fc07200db8a`.
The all-20 helper receipt is `experiments/kotlin/helper-semantics/run-v3/report.json`,
SHA-256 `066592dc37ccf0ca60e5795e02c680a088e8fe9c17448baa049693d77c5679ad`;
its terminal receipt is pinned to
`c8ffede3ba3ff3dd3827237e50d0b40b2f56fae40b02ea1409acc7c0411e1731`.
Preparation verifies the helper's physical input pins, closed evidence resolution,
terminal artifacts, source/owner review, complete retained class inventories,
and the original runtime. This can hash large runtime files; it is deferred
until the timing lane is free.

The reference loader is imported unchanged and hash-pinned from
`tools/qualification/elixir_bounded.py`. It verifies the closed Prolog bounded
corpus, its raw and supervisor receipts, all 20 qualification checks per case,
the retained actual/expected stdout bytes and stream inputs. It preserves the
original case IDs, `workload_n`, hashes and reference provenance. It never starts
Prolog, Elixir or an oracle generator.

| Benchmark | Distinct reference cases | Retained-form executions |
| --- | ---: | ---: |
| N-body | 4 | 8 |
| Mandelbrot | 13 | 26 |
| Spectral norm | 6 | 12 |
| Binary trees | 4 | 8 |
| Fannkuch redux | 8 | 16 |
| Pi digits | 9 | 18 |
| FASTA | 11 | 22 |
| Regex redux | 5 | 10 |
| Reverse complement | 6 | 12 |
| K-nucleotide | 12 | 24 |
| Total | 78 | 156 |

N-body requires two finite nine-decimal energy lines within `1e-8` of the
retained reference. Every other case requires exact complete stdout bytes.
Stderr must be empty and the native process must exit normally. The reference
case inventory rejects an unexpected size, stream substitution, missing case,
duplicate form, or changed case order.

All 40 counted authored source paths remain bound: the main and the complete
`Support.kt` for every form, plus their reviewed archive copies. Preparation
emits ten explicit `alias_pairs`, with both profile IDs, original alias labels,
source hashes and relative class hashes. Every compact/optimized pair must still
have equal source and class bytes. Both forms are executed separately; no
separate optimization is claimed.

## Runtime observation and containment

Each JVM uses the original retained native ARM64 JDK 25.0.4.1+1 and sole original
`kotlin-stdlib.jar`, with `-XX:ActiveProcessorCount=8 -Xms64m -Xmx8g
-XX:+UseG1GC`. Per-case home/tmp directories and class-load/GC diagnostic logs
are explicit additions. Ambient JVM-option injections remain absent, and the
retained sanitized environment is used. The program class directory is selected
as a complete original directory or its verified complete retained copy; mixtures
are rejected and relocation is explicit in the plan.

The application class path contains only the diagnostic wrapper. Its isolated
loader admits exactly the retained subject owner list and Kotlin classes from
the pinned stdlib, delegating platform classes to the platform loader. It checks
all subject resource paths, class origins and the complete `.class` inventory,
rejects an unretained-owner canary, and invokes the declared public static void
`main(String[])` exactly once. Raw stdin/stdout pass directly to the retained
program through OS pipes. The probe records loaded class resources/origins,
main invocation and return counts, runtime identity, flags, collector names,
heap size, main arguments and loader configuration. The controller reconciles
these with independent JVM class-load and GC logs. This is an instrumented
bounded execution, not a full-workload JIT-method or timing qualification.

The native supervisor uses the previously tested Kotlin controller's Darwin
kernel identity and zombie handling. Launch registration, reaping, cleanup and
final process receipt retention mask interrupt/termination/hangup signals;
the child restores the previous signal mask before exec. No `poll()` reaps the
leader before its process group is empty. Its unreaped PID remains reserved
through cleanup, so a stale PGID cannot authorize a signal after reaping.
If kernel group enumeration fails, cleanup records that error and signals the
still-owned unreaped group. No native process monitor is launched.

Bounds are 30 seconds per native command, five seconds for cleanup, and 2 GiB
observed process-group RSS (read through Darwin `PROC_PIDTASKINFO`). Core dumps
are disabled. Native-created stream/log files have an 8 MiB `RLIMIT_FSIZE`.
The stdout pipe fails once captured bytes exceed 8 MiB; at most one 64 KiB read
can cross that threshold. Cleanup capture has a hard 8 MiB + 64 KiB bound. If
that bound prevents further retention, the receipt explicitly fails cleanup;
it does not claim complete output. RSS is sampled at most every 50 ms while
pumping pipes, and before reaping; it is an observed bound, not a peak-RSS proof.

Every native start has exclusive stream artifacts and start/active/final process
receipts. Failed and partial outputs stay in the fresh output directory. Native
launch requests, native starts, diagnostic compiler starts, bounded JVM starts,
observed main invocations/returns, and qualified output cases are separate
counts. Successful completion requires one diagnostic compiler, 156 bounded
JVMs, 156 observed main invocations and returns, 156 qualified cases, all 20
forms, clean ownership receipts, and unchanged pins. The final terminal receipt
hashes all retained artifacts and binds the final report while the mutex is held.

## Ready CLI, deferred until the timing lane is free

From the repository root, after source review:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/kotlin_bounded.py prepare \
  --plan experiments/kotlin/bounded-work-v1/plan-v1.json \
  --output experiments/kotlin/bounded-work-v1/run-v1
```

Preparation prints the exact plan SHA-256. Review the resulting plan and pass
that value explicitly:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/kotlin_bounded.py run \
  --plan experiments/kotlin/bounded-work-v1/plan-v1.json \
  --plan-sha256 PLAN_SHA256_PRINTED_BY_PREPARE
```

A failed output tree remains evidence. Diagnose it before authorizing a new
plan/output revision; successful prior cases are never silently overwritten.

## Source review and checks performed

The Java probe had a separate source review. Independent source review found
two failure-path gaps in the controller, now fixed only in this new
controller: fallback cleanup signaling when kernel enumeration fails, and
retention of final process receipts after an output artifact hash failure.
A final review should cover those changes, complete source/class/runtime binding,
probe/summary and class-log schema agreement, alias identity, closed reference
reuse, native-versus-qualified accounting, and every remaining false gate.

Fourteen tiny pure fixtures pass. They exercise schedule substitution rejection,
launch failure/accounting, identity-read failure after launch, registration failure, partial timeout cleanup,
interrupt delivery after atomic launch/reap, cleanup query failure with owned
fallback signaling, artifact hash failure retention, RSS layout/identity/bound
handling, class-origin rejection and exact/tolerant output validation. They use
fake processes and kernel interfaces; they do not launch subprocesses or hash
the closed corpus/runtime. A metadata-only shape check also confirmed all 20
retained runtime command shapes, compile/reader exit fields, helper summary pin
paths and source-review pin keys. No native/JVM/compiler execution or full
preparation occurred during this source preparation.

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/test_kotlin_bounded.py
```

Even a complete bounded pass leaves `source_work_qualified`,
`subject_JIT_method_evidence_qualified`,
`actual_subject_runtime_dependency_closure_qualified`, `full_timings_qualified`
and `chart_admission` false; canonical/formatted LOC remain null. Small-case
success does not qualify full-size memory feasibility, required-work execution,
JIT method compilation, LOC, or the full timing study.
