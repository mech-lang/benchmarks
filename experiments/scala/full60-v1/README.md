# First full Scala timing cohort

This packet prepares sixty sequential fresh-process samples: one retained Scala
implementation and one matched Mech AOT control for each of ten workloads, with
three observations per profile. Scala has ten real source bundles; no duplicate
source aliases or invented optimization variants are added.

The controller requires the exact saved compilation, 149-case correctness,
canonical source-count and required-work admissions. The latter combines the
ten-source bytecode review with the two actual single-entry tree/pi captures.
The original producer reports retain their separate qualification boundaries.
Canonical LOC is qualified; formatted LOC remains null and unqualified.

Each Scala command invokes the retained JDK directly with `Main` and only the
retained application classes plus the two Scala runtime jars. The policy is
`-XX:ActiveProcessorCount=8 -Xms64m -Xmx8g -XX:+UseG1GC`, default tiered JIT, one
main invocation, and no diagnostics or wrapper warmup. It matches the work
captures' execution settings. The full-size workload has not been assumed to
fit the resource bounds merely because bounded correctness passed.

Elapsed time covers process startup, class loading, JIT, input, all work,
complete output and exit. Source compilation, file-pin checks, environment
waiting and output validation occur outside the timer. The frozen full sampler,
output references and independent process supervisor are reused. The serial
controller lifecycle is adapted from `tools/qualification/kotlin_full.py`;
qualification and schedule handling are Scala-specific.

The rounds alternate subject/control order. Five workloads begin with Scala
and five with Mech, balancing the extra leading position across the suite.
Full inputs are unchanged: regex 5,000,000; reverse complement, FASTA and
k-nucleotide 25,000,000; pi 10,000; spectral norm 5,500; Mandelbrot 16,000;
trees 21; n-body 50,000,000; fannkuch 12. Each attempt has a six-hour native
deadline, a separate cleanup/supervision bound and a 10 GiB sampled group-RSS
limit. Whole-output validation is required. An isolated workload failure
preserves its failed receipt and skips only that profile's remaining slots;
integrity, environment or ownership failures stop the cohort without retry.

The common timing mutex (existing inode `79859134`) stays held from preparation
for execution through every native lifetime, cleanup and final evidence write.
A separate Scala suite lease prevents overlapping cohorts. All source, class,
runtime and prerequisite-artifact hashes are verified under the common mutex;
closed artifact inventories are checked again at the end. The transfer of each
returned attempt into the saved ledger, its validation snapshot and derived
sample state blocks interrupt signals. Final evidence checks and terminal
writes use the same protection. Native execution remains interruptible, with
the frozen supervisor responsible for owned child cleanup. Raw receipts remain
available even when validation or interruption prevents timing admission.

Each attempt's raw, sampler-supervisor and outer-supervisor bytes are decoded
and independently checked before their digests are accepted. Finalization
replays those receipts and the sixty-slot ledger, checks serial intervals and
the exact artifact inventory, and verifies the original digests again after
terminal inventory collection. Changed bytes cannot become newly accepted
terminal hashes. Timed JVM injection
environment variables must be absent. Successful producer completion still
requires independent reconciliation and publication review.

## Preparation and execution

These commands are templates for the retained host. No executable plan or native
run is created by this source packet. Run preparation only when the timing mutex
is free. Use fresh paths and independently review the prepared plan before launch.

```sh
SCALA_FULL_PYTHON=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
"$SCALA_FULL_PYTHON" -I -S -B tools/qualification/scala_full.py draft \
  --plan experiments/scala/full60-v1/draft-v1.json \
  --output experiments/scala/full60-v1/run-v1
"$SCALA_FULL_PYTHON" -I -S -B tools/qualification/scala_full.py prepare \
  --draft experiments/scala/full60-v1/draft-v1.json \
  --draft-sha256 "$SCALA_DRAFT_SHA" \
  --plan experiments/scala/full60-v1/plan-v1.json
```

Set `SCALA_DRAFT_SHA` to the digest from the draft command. The prepare command
verifies all bytes and produces the plan digest. The durable launcher is
`experiments/shared/owned-jobs-v1/launch_durable.py`, with a fresh job name such as
`scala-full60-v1`. Its JSON command must contain the absolute physical paths:

```text
["<retained-python>", "-I", "-S", "-B", "-u",
 "/private/tmp/mech-benchmark-completion/tools/qualification/scala_full.py", "run",
 "--plan", "/private/tmp/mech-benchmark-completion/experiments/scala/full60-v1/plan-v1.json",
 "--plan-sha256", "<independently-reviewed-prepared-plan-sha256>"]
```

No previous sample is reused as a fresh Scala or matched-control observation.
Matched controls are separate cohort evidence and do not overwrite published
Mech observations or chart baselines. A closed report and terminal are evidence
for independent review, not automatic chart admission.

## Pure checks

```sh
"$SCALA_FULL_PYTHON" -I -S -B -m unittest discover \
  -s tools/qualification -p test_scala_full.py
```

Tests inspect small saved metadata and synthetic policy faults only. They do
not create a real timing plan, execute subjects, hash complete runtime closures
or repeat qualification.
