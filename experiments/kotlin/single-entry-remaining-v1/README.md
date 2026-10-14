# Three additional Kotlin single-entry captures

This additive stage reuses the closed compact binary-trees capture and requests
only the three processes that the first observer never started:

| Retained form | Main argument |
| --- | --- |
| kotlin-binarytrees-optimized | 21 |
| kotlin-pidigits-compact | 10000 |
| kotlin-pidigits-optimized | 10000 |

The [first-capture reconciliation](first-capture-reconciliation.md) preserves
the original failed report, raw output and process receipts. Its compact tree
is excluded from the new process inventory. Preparation and execution have not
been performed for this stage. Pure tests and replay of saved capture text do
not qualify its prerequisite artifact closure or predict future native results.

The [controller](../../../tools/qualification/kotlin_single_entry_remaining.py)
imports the exact frozen first controller through the narrowly repaired
[byte-row replay](../../../tools/qualification/kotlin_single_entry_capture.py).
The original controller and old receipts remain unchanged. Preparation checks
the exact first plan, report, terminal and durable terminal; all inherited
runtime/source pins; the complete closed artifact inventory; and first-process
ownership, output, VM identity, loaded classes and native code. It retains this
proof in the new plan and replays it again before any new process starts.

Each remaining form uses the original compiled classes, Kotlin standard library,
JDK and direct main entry, with no wrapper invocation, subject recompilation,
warmup calls, threshold change or optimizer change. The retained scored flags
remain `-XX:ActiveProcessorCount=8 -Xms64m -Xmx8g -XX:+UseG1GC`.
The existing isolated observer keeps its 10 GiB process-group RSS bound,
30-second process deadline, five-second cleanup bound and 8 MiB file limit.
The continuously held common mutex must have inode 79859134. Atomic registration,
exact process birth/parent/group checks, owned cleanup and no retries are inherited
from the reviewed supervisor. The exact Python interpreter and SHA are checked
under the mutex before closure hashing or native work.

Two added diagnostic options route the known VM warning without changing
compilation or GC policy:

```text
-Xlog:all=warning,os=off:stdout:uptime,level,tags
-Xlog:os=warning:file=<case>/os.log:uptime,level,tags
```

The default warning selection belongs to stdout; configuration for another
output does not replace it. The explicit stdout selection preserves other
warnings while excluding the exact `os` tag, whose warnings and errors go to
`os.log`. This follows the documented output and selection semantics in the
[JDK 25 launcher reference](https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html#enable-logging-with-the-jvm-unified-logging-framework).
Actual routing still requires the new native receipt. The controller admits only
an empty OS log or one missing-hsdis warning with its uptime decoration; any
other OS diagnostic fails validation and remains retained. It requires exact
complete benchmark stdout and empty stderr.

Every installed targeted nmethod must have complete main-code bytes and the
subject methods must retain OopMaps. Installed `Node` elimination fails the
capture stage for entry/reachability review. Three successful captures remain
`all3-additional-native-captures-awaiting-instruction-review`: allocation/lifetime,
pi division execution, full source work, benchmark timing and chart admission
are not granted by capture completeness. The finalizer reconciles the exact
three-process ledger, saved validated records, first-capture proof, source pins
and all retained output artifacts before recording a terminal.

Run after the serialized lane is available, with a fresh plan and output:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/kotlin_single_entry_remaining.py prepare --plan experiments/kotlin/single-entry-remaining-v1/plan-v1.json --output experiments/kotlin/single-entry-remaining-v1/run-v1
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/kotlin_single_entry_remaining.py run --plan experiments/kotlin/single-entry-remaining-v1/plan-v1.json --plan-sha256 <printed-plan-SHA>
```

Preparation performs no native work but verifies the complete prerequisite closure
under the same mutex. The run should use the retained durable launcher so its
outer command identity, terminal and exit status are also preserved.

The [replay tests](../../../tools/qualification/test_kotlin_single_entry_capture.py)
cover byte-row completeness, overlap, malformed groups, XML comments and the
actual nine-method capture. The
[remaining-stage tests](../../../tools/qualification/test_kotlin_single_entry_remaining.py)
cover exact cohort/routing, the fixed first-output split, unknown diagnostics,
recorded process identity, saved metadata replay without pin verification, and
successful/incomplete/altered/unregistered receipt finalization. They start no
JVM or compiler and perform no runtime closure hash.
