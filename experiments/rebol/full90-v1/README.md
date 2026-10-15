# Rebol full90 timing stage

This packet has no actual timing execution. It requires independently reviewed
extension, primitive, bounded-output, source-count and required-work evidence
through `rebol_qualification.review_context`. No prepared plan, successful
approval or timing observation is supplied by this packet.

Ten workloads each receive three rotated rounds of compact Rebol, optimized
Rebol and the unchanged matched Mech AOT control: **60 fresh Rebol processes
and 30 fresh control processes**. The two Rebol forms use the same qualified
source bundle. They make no distinct optimization claim and receive separate
actual samples. The frozen sampler's timing-alias resolver is never called.

The benchmark order is regexredux, revcomp, pidigits, spectralnorm, mandelbrot,
fasta, knucleotide, binarytrees, nbody and fannkuchredux. Each group's orders are
compact/optimized/control, optimized/control/compact and control/compact/optimized.
The original full inputs and output oracles, 21,600-second native deadline,
22,200-second outer deadline and 10,240 MiB memory limit are unchanged.

Each subject invokes the exact retained interpreter directly as
`runtime -q -s main.reb`, adding the full integer argument only for the seven
argument workloads. The original ten bundles, corrected C extension and
fannkuch-zero substitution are supplied by actual qualification. All authored
Rebol and whole C helper files are counted: fifteen unique physical files,
four per ordinary bundle and five for pidigits/regexredux. Formatted counts
remain unavailable. Runtime and library disclosure retain the qualification
packet's exact scope; runtime-source equivalence is not asserted.

The unchanged timer begins immediately before process launch and ends after
the blocking wait. Runtime startup, source/facade evaluation, extension load,
input, required work, complete output and shutdown are included. Offline
extension compilation, harness file setup, prerequisite hashing, environment
waits and post-process output validation are outside that clock. Complete
stdout counts/hashes and validation receipts are retained by the frozen
sampler; the discarded stdout temporary files are not claimed as retained raw
output. Nbody uses the existing full-output numerical validator.

The qualification context owns the original common mutex continuously through
preparation or all timing slots, cleanup and final closure. Its existing closed
prerequisite leases remain held. This stage adds a separate suite lease and
does not mutate the inherited lease list. Exact raw/supervisor/outer receipts,
serial clocks, source/image/input pins, named resolutions, report bytes and
artifact inventory are checked before terminal acceptance. Finalization runs
after the qualification context's exit replay, while its leases remain held.
Late closure failures invalidate only the exact newly owned terminal; external
replacement bytes are preserved.

An isolated frozen workload failure is retained and prevents that form from
receiving a median. Its remaining scheduled slots are explicitly skipped;
other forms continue. A failed matched control leaves all associated ratios
null and must exclude the subjects from independent comparative admission.
Ownership, environment or integrity failures stop the entire cohort. There are
no retries, resumptions, copied samples or repeated completed samples. Producer
full-timing and chart-admission flags remain false even after a complete run.

After the source and qualification reviews exist, preparation uses:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/rebol_full.py prepare \
  --qualification-manifest /absolute/actual-qualification-manifest.json \
  --qualification-manifest-sha256 ACTUAL_REVIEWED_SHA256 \
  --source-review /absolute/independent-full90-source-review.json \
  --source-review-sha256 ACTUAL_REVIEWED_SHA256 \
  --plan /private/tmp/mech-benchmark-completion/experiments/rebol/full90-v1/plan-v1.json \
  --output /private/tmp/mech-benchmark-completion/experiments/rebol/full90-v1/run-v1
```

Preparation performs strict physical prerequisite replay under the mutex; it
does not run a native process. An independent review must inspect the concrete
prepared plan before the existing durable launcher starts exactly:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/rebol_full.py run \
  --plan /private/tmp/mech-benchmark-completion/experiments/rebol/full90-v1/plan-v1.json \
  --plan-sha256 ACTUAL_REVIEWED_PLAN_SHA256
```

The independent source review schema is `rebol-full90-source-review-v1`, with
status `independent-source-review-complete-native-timing-pending`,
`independent_review: true`, exact `files` pins for the controller, tests and
this README, and exact `dependencies` pins for `rebol_qualification.py`,
`elixir_full.py` and `prolog_reconcile.py`. Both `full_timing_qualified` and
`chart_admission` must be false. Paths in those pin maps are repository-relative.
This documents required future evidence; it is not a substitute approval.

The 17 focused pure test methods in `tools/qualification/test_rebol_full.py`
passed on 2026-10-15 UTC, recorded in
[the initial pure-validation record](../../shared/pure-validation-20261015/post-prolog-pure-validation-run-v1/report.json). The recorded command is:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/test_rebol_full.py
```
