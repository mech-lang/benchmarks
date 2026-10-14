# Kotlin retained compiled-work witnesses

The completed [second attempt](run-v2/report.json) recorded compiled-work,
JIT-method and runtime-dependency evidence for all twenty retained Kotlin forms.
It follows 156 original bounded output checks and thirty supplemental checks.
The [terminal receipt](run-v2/terminal.json) records twenty JVMs and one diagnostic
compile. Bounded work witnesses, required-method JIT evidence and observed
runtime dependency closure passed for every form. Actual optimized-main
allocation/lifetime and final compiled-work review remain separate gates.

`tools/qualification/kotlin_work_v2.py` imports `kotlin_bounded_v2.py` at
SHA-256 `c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc`.
It reuses that controller's tested atomic process supervisor, zombie-aware
ownership, inherited timing mutex, RSS/file limits and retained-class checks.
The required bounded report is the completed `bounded-work-v1/run-v2`.
The preserved `run-v1` stopped on an RSS-monitor teardown race, an observation
infrastructure failure that established no subject-source fault. The v2
observer retries that race briefly within unchanged process/resource bounds.
The original controller and all earlier execution evidence remain unchanged.

The first compiled-work attempt exited its JVM normally but its class-origin
validator rejected JDK-generated dynamic proxies. The revised validator accepts
only the JDK proxy naming pattern and exact `__dynamic_proxy__` origin marker,
with preceding trusted Java-base proxy-factory records. It preserves those
origins and applies the original strict validator to every other class.
Twenty-five pure tests pass; the second native attempt completed the full cohort.

## Exact inputs and sequence

Preparation validates the completed bounded report's real schema, all 156
qualified cases, 157 native starts including its single diagnostic compiler,
156 observed main invocations and returns, empty active state, clean integrity
and process receipts, all twenty profile IDs and ten explicit alias pairs. It
rehashes its pinned inputs and terminal artifact inventory, then binds this
stage's source, specification, existing source-owner review and retained
`javap` files. Every requested JIT target descriptor must occur in the exact
retained bytecode capture. The target shapes were checked against all twenty
small disassembly captures during source preparation.

The separate [specified-case supplement](../specified-cases-v1/README.md) closes
the output-case gaps in the original Kotlin specification. Preparation requires
its explicit completed report and terminal hashes, 30 qualified cases, 31 clean
native starts and 30 observed main invocations/returns, all linked to the same
156-case report. It validates the exact supplemental case schedule, all retained
source/class/runtime bindings and each case's output validation and native
receipt. Its terminal artifacts and inputs are pinned along with the original
bounded corpus. A missing or incomplete supplement blocks this stage.
The reader also reconciles all original 156 saved output proofs with their
terminal artifacts, and requires each supplemental validation/process file
and command snapshot to occur identically in the supplemental terminal
inventory. This is saved-output evidence binding, not new runtime-work proof.

Run compiles only `WorkProbe.java` plus an exact copy of the prior diagnostic
`BoundedProbe.java`, using the original retained JDK `javac` with release 17.
The three expected diagnostic classes are retained and pinned. No Kotlin
subject, counted helper or original generated class is recompiled.

Twenty fresh JVMs then use each independently retained form, its complete
original class directory or declared verified copy, and the sole original
Kotlin stdlib. The immutable isolated subject loader rejects foreign owners
and checks class-resource and code-source origins. Main/helper sources and
all retained class files remain pinned. Compact and optimized aliases stay
separate runtime observations.

Every command requires the existing timing mutex, inode 79859134. Preparation
also takes that mutex because it rehashes large runtime inputs. Do not overlap
this stage with benchmark timing. Each native command has a 30-second deadline
and five seconds for cleanup. The inherited supervisor enforces 2 GiB observed
process-group RSS, an 8 MiB native file limit and bounded pipe capture. The
original `-XX:ActiveProcessorCount=8 -Xms64m -Xmx8g -XX:+UseG1GC` and sanitized
runtime environment remain in place.

## Required-work observations

The new probe follows the existing source-owner review's work-stage scope:

- Binary trees: invoke the exact scored constructor twice at depths 0, 1, 4, 6
  and 8. Identity traversal proves complete shapes, expected node totals and
  disjoint graphs across calls. The scored check must match every total. A
  separate depth-8 root survives bounded pressure with only weak descendant
  references retained by the diagnostic. The post-pressure graph must contain
  the same 511 objects and have the same scored check. Pressure allocates at
  most 256 MiB, retains at most 32 MiB at once, and starts no more allocations
  after five seconds or an observed G1 collection. No explicit GC occurs. If
  no collection occurs within that bound, GC survival remains unqualified.
- K-nucleotide: invoke the exact scored table routine for all seven lengths
  on sequences of lengths 0, 1, 2, 17, 18, 19 and one specified longer mixed
  sequence. Seven distinct full maps remain simultaneously reachable. Every
  entry and window total is checked with an independent overlapping-match
  oracle; Python independently reconciles the reported entries. Repeating
  length 3 must produce a fresh map without changing any earlier map.
- Fannkuch: call the scored flips method on five explicit permutations. Its
  result must match an independent prefix-reversal calculation, and the
  caller's original array must remain unchanged.

The source and exact disassembly bindings retain the other authored algorithm
requirements, including both general BigInteger divisions in pi digits, all
spectral matrix loops, FASTA RNG continuity and the original tree/map main
lifetimes. The completed 156-case stage and 30-case supplement supply the
independent bounded output evidence. This stage does not regenerate their
oracles.

## JIT and actual dependencies

Each JVM repeats one already-qualified small main case, selected explicitly in
`work-spec.json`. It starts at most 10,000 calls and starts no further call after
20 seconds. A call already in progress remains covered by the outer 30-second
native deadline. The diagnostic resets in-memory stdin/stdout for each call,
checks complete output every time, retains the first and last output and a
SHA-256 transcript over all outputs, and records invocation, return and output
check counts. Raw OS-pipe helper/main I/O was covered by the prerequisite
stages; these instrumented repetitions are not benchmark timing samples.

`-XX:+UnlockDiagnosticVMOptions -XX:+LogCompilation` and explicit log files are
diagnostic additions. Compilation thresholds, compiler policy, heap and GC
policy are unchanged. A complete HotSpot XML log must contain actual `nmethod`
records for each listed workload method, with the exact owner and descriptor.
C1/C2 levels, addresses, compilation IDs and OSR markers are retained. Platform
library compilation cannot satisfy a subject method target. Missing target
records leave the JIT gate open; there is no automatic retry or larger run.

Class-load logs are reconciled with the strict loader's independently recorded
subject and stdlib origins. The original JVM module/CDS images stay pinned.
The probe obtains actual mapped native images from `DiagnosticCommand.vmDynlibs`
and retains its raw output. OpenJDK exposes that diagnostic through its MBean
interface and its macOS implementation enumerates dyld image names; see the
[diagnostic command source](https://github.com/openjdk/jdk25u/blob/master/src/hotspot/share/services/diagnosticCommand.cpp)
and [macOS image inventory implementation](https://github.com/openjdk/jdk25u/blob/master/src/hotspot/os/bsd/os_bsd.cpp).

Every non-platform native image must resolve to an already pinned image inside
the original JDK before the runtime dependency gate can pass. An unresolved
image is retained explicitly and leaves that gate open. OS install names are
recorded under the existing dependency review's operating-system-image boundary;
they are not represented as newly hashed standalone files. No new generic
runtime probe, vendor recertification or subject compilation occurs.

## Evidence and remaining gates

Native starts, observed main invocations/returns and qualified profile
observations remain separate. Missing main summaries after a failed native run
are listed explicitly. A failed native command or incorrect witness stops the
batch and retains partial streams, artifacts and receipts. Missing JIT records,
missing natural GC or unresolved native origins remain explicit open gates in
otherwise completed observations. All available evidence is hashed into a
terminal receipt while the mutex is held; post-run integrity failures clear
qualification flags.

Finalization reconciles the exact 21 native command identities, kinds, PIDs
and process groups with the registered starts. Successful receipts must retain
clean ownership/exit/cleanup state, observed resource bounds and exact empty
native stdout/stderr. All twenty summaries must agree with their validated
profile invocation/return counts and aggregate qualification flags. Each
validated command has a required artifact snapshot; missing or changed bytes
at finalization invalidate the report and terminal gates together.

`required_work_witnesses_qualified` covers the specified constructor, container
and copied-input witnesses. `subject_JIT_method_evidence_qualified` covers the
listed actual nmethod records. Runtime dependency qualification applies to the
exact observed subject/stdlib/JVM images and the stated OS-image boundary.
These are separate from the overall `source_work_qualified` gate.

The unchanged scored binary-trees main still needs an allocation/lifetime proof
appropriate to its optimized native execution. Reflectively inspecting fresh
scored trees and their survival through GC does not prove every allocation in
an optimized main. Similarly, matching pi output is not a dynamic division
counter, and small full k-mer maps do not prove prescribed-size memory
feasibility. The packet preserves those limits from the existing specification;
it does not invent a new counting or timing requirement. Overall source-work,
optimized-main allocation/lifetime, LOC, full timings and chart admission remain
false or null in this stage's results.

## Deferred CLI

After both actual output stages complete and their receipts have been reviewed:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/kotlin_work.py prepare \
  --bounded-report experiments/kotlin/bounded-work-v1/run-v2/report.json \
  --bounded-report-sha256 ACTUAL_COMPLETED_BOUNDED_REPORT_SHA256 \
  --bounded-terminal-sha256 ACTUAL_COMPLETED_BOUNDED_TERMINAL_SHA256 \
  --supplement-report experiments/kotlin/specified-cases-v1/run-v1/report.json \
  --supplement-report-sha256 ACTUAL_COMPLETED_SUPPLEMENT_REPORT_SHA256 \
  --supplement-terminal-sha256 ACTUAL_COMPLETED_SUPPLEMENT_TERMINAL_SHA256 \
  --plan experiments/kotlin/compiled-work-v1/plan-v1.json \
  --output experiments/kotlin/compiled-work-v1/run-v1
```

Use the actual preparation output's plan hash:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/kotlin_work.py run \
  --plan experiments/kotlin/compiled-work-v1/plan-v1.json \
  --plan-sha256 ACTUAL_PREPARED_PLAN_SHA256
```

Fifteen small pure evidence fixtures pass, covering prerequisite counts, required
supplemental completion and matching bounded run, subject
versus library JIT evidence, incomplete compilation XML, native image binding,
strict probe class origin, absent natural GC and complete non-query map entries.
They also cover exact native-ledger reconciliation, missing summaries,
resource receipts, changed/missing artifacts, aggregate discrepancies and
supplement reference/terminal mismatches. They use small synthetic artifacts
and do not launch native processes or hash
the retained corpus/runtime. Python syntax and all twenty retained target method
descriptors were checked. Java compilation, preparation and native validation
remain deferred until the timing lane is free.
