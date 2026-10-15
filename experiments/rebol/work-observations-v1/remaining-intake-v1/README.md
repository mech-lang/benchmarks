# Three work observations after split primitive completion

The additive [intake adapter](../../../../tools/qualification/rebol_work_remaining.py)
consumes the combined primitive review through the
[shared149 intake adapter](../../../../tools/qualification/rebol_bounded_remaining.py).
It preserves the original work controller and its three diagnostics: tree N4,
Pi N27 and the existing 10,299-byte arbitrary-widths map input. The original
scripts, corpus outputs, schedule, observer, stream/resource limits, capture
checks, lease lifetime and finalizer remain unchanged. It does not require a
shared149 native run before these three observations.

The inherited intake retains the failed original diagnostic compilation, the
linker stage and its successful captures, and the sixteen remaining primitive
captures. The combined review must account for 21 native attempts: 19 primitive
attempts and two diagnostic compile attempts, with 19 successful captures,
18 successful primitive contracts and two failed attempts. Earlier failures
are preserved. No new diagnostic compilation or retry is part of this stage.

The work source review uses schema
`rebol-three-work-observations-remaining-source-review-v1` and status
`independent-source-review-complete-native-observations-pending`, with
`independent_review: true`. Its `files` are exactly the original controller's
16 files plus this adapter, its focused test and this README. Its
`dependencies` are exactly the original `rebol_bounded.py`,
`rebol_bounded_remaining.py` and `rebol_primitive_remaining.py`, each bound to
its reviewed SHA-256. All six original admission gates remain false. The
separate shared149 source review must satisfy that adapter's own exact scope.

The original controller identity remains in `controller` and
`controller_sha256`. The plan additionally records `intake_adapter`,
`bounded_intake_adapter`, `primitive_intake_adapter` and the actual
`entrypoint`. The work adapter checks all three supplied digests before use.
The original held context checks the frozen shared149 helper before the load
hook selects its additive intake, then pins the complete source-review file
and dependency union under the inherited leases. Diagnostic paths still refer
to the original work packet; fresh output must be beneath this additive packet.

After source review and exact digest freezing, preparation can use:

```sh
"$PY" -I -S -B "$E/tools/qualification/rebol_work_remaining.py" \
  --adapter-sha256 "$WORK_ADAPTER_SHA" \
  --bounded-adapter-sha256 "$BOUNDED_ADAPTER_SHA" \
  --primitive-adapter-sha256 "$PRIMITIVE_ADAPTER_SHA" prepare \
  --primitive-review "$PRIMITIVE_REVIEW" --primitive-review-sha256 "$PRIMITIVE_REVIEW_SHA" \
  --bounded-source-review "$BOUNDED_SOURCE_REVIEW" --bounded-source-review-sha256 "$BOUNDED_SOURCE_REVIEW_SHA" \
  --source-review "$WORK_SOURCE_REVIEW" --source-review-sha256 "$WORK_SOURCE_REVIEW_SHA" \
  --plan "$E/experiments/rebol/work-observations-v1/remaining-intake-v1/plan-v1.json" \
  --output "$E/experiments/rebol/work-observations-v1/remaining-intake-v1/run-v1"
```

The eventual durable run uses the same three adapter digest arguments followed
by `run --plan "$PLAN" --plan-sha256 "$PLAN_SHA"`. The original retained
Python `-I -S -B` requirement still applies. A separately reviewed qualification
consumer must recognize this actual entrypoint and combined prerequisite
accounting; this adapter does not grant qualification.

The eight [focused test methods](../../../../tools/qualification/test_rebol_work_remaining.py)
passed on 2026-10-15 UTC (exit zero). They exercise only source
loading and synthetic intake contracts. No prepared plan, native observation
or native success receipt is supplied here. Runtime equivalence, source work,
source counts, full timing and chart admission remain unqualified by this packet.
