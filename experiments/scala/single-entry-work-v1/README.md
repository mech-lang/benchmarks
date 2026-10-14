# Scala tree and pi execution capture

This stage records two fresh direct `Main` invocations using the already compiled
Scala classes: binary trees at depth 21 and pi at 10,000 digits. It addresses the
two optimized-runtime questions left by the actual bytecode review. It does not
repeat the 149 bounded cases, recompile sources, invoke a wrapper, or collect
performance samples.

Preparation replays the complete closed Scala compilation and all 149 correctness
receipts, including the seven expected reverse-complement rejections. The exact
source copies, generated classes, original Scala runtime jars, JDK, controllers,
oracles and prior artifact inventories are pinned in the new plan.

The native observer is the unchanged Kotlin single-entry supervisor. Each process
has a 30-second deadline, five-second cleanup deadline, 10 GiB observed process
group RSS ceiling and 8 MiB per-file limit. JVM settings match the retained JVM
full-study policy: eight active processors, 64 MiB initial heap, 8 GiB maximum
heap and G1. This replaces the bounded preparation stage's smaller heap for these
full-input diagnostic invocations. Logging adds no warmup, threshold change,
compiler exclusion or optimizer override.

The controller records full stdout, stderr, class origins, GC observations,
HotSpot compiler XML and machine bytes for the Scala owners and relevant general
division methods. The known missing-hsdis warning is routed to `os.log`; other
warnings are not silently filtered. Actual installed target methods must have
complete retained machine bytes and matching compiler/method identity. A main
that does not compile remains available for an explicit interpreted-path review;
the capture does not manufacture a compiled main or force compilation.

Successful capture still requires independent review of surviving tree allocation
and long-lived-root reachability, and of both pi division calls on the observed
caller path. OopMaps, allocation-elimination entries and complete compiler events
are retained for that review. Neither a complete capture nor correct stdout alone
grants required-work qualification, timings or chart admission.

The existing common mutex must remain inode 79859134 and free before preparation
or execution. All native commands and final closure run under that same mutex.
Output and plan paths must be fresh. There are no automatic retries or resume.

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/scala_single_entry.py prepare --plan /private/tmp/mech-benchmark-completion/experiments/scala/single-entry-work-v1/plan-v1.json --output /private/tmp/mech-benchmark-completion/experiments/scala/single-entry-work-v1/run-v1
```

After independent plan review, run the same controller with `run --plan` and the
printed `--plan-sha256`. The shared durable launcher may own that command; the
controller itself owns the common mutex and every native process group.
