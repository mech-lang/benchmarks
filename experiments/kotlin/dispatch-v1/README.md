# Kotlin bounded-stage dispatch

This focused dispatcher waits for the existing Prolog durable-job lease and
continuous cohort lease, validates their identities and completed durable,
report and terminal state, then waits for the original common timing mutex
(inode 79859134). A gap between Prolog samples cannot start Kotlin preparation.
Completed Prolog cohorts with explicitly isolated unqualified profiles may
close scheduling ownership; this does not qualify their measurements.

The dispatcher keeps all three leases through final receipt persistence. With
the same open timing-lock descriptor, it loads the exact frozen
`kotlin_bounded.py` definitions, calls `prepare`, then calls `run(args, lock)`.
It does not reopen the mutex through the CLI. Queued checkpoint jobs either
finish before this acquisition or wait until the bounded stage finishes.

Only `bounded-work-v1/plan-v1.json` and `bounded-work-v1/run-v1` are permitted.
Both must be fresh before waiting and immediately before preparation. Existing
failed evidence is never reused. Waiting is interruptible; missing or unexpected
Prolog terminal evidence, changed source, replaced leases, preparation failure,
native failure, or incomplete result receipts stop the dispatcher without retry.

The included `launch_durable.py` is an unchanged copy of the launcher used by
the Prolog full cohort. It supplies durable outer ownership and retains fresh
job requests, process identities, command streams and terminal records under
this stage's `owned-jobs/` directory. After source review, dispatch this exact
command through that launcher with a fresh durable job:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B -u \
  tools/qualification/kotlin_dispatch.py \
  --dispatcher-sha256 REVIEWED_DISPATCHER_SHA256 \
  --receipt experiments/kotlin/dispatch-v1/dispatch-v1.json
```

The receipt binds dispatcher/controller/plan identities, observed Prolog closure,
held lease identities, preparation/run entry, final report/terminal hashes,
native-start accounting from the stage report, and failures. It is persisted
before releasing ownership. A successful dispatch requires the actual 156-case,
157-native-command completed bounded report and matching terminal. It never
sets `qualification_granted`; supplemental outputs, compiled work, LOC and full
timings require their separate subsequent review and commands.

Source-only preparation does not run this dispatcher or the native stage.
Regression tests use temporary synthetic receipts and mocked locks/stages:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/test_kotlin_dispatch.py
```
