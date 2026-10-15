# Rebol shared149 bounded captures

The source-only [controller](../../../tools/qualification/rebol_bounded.py)
proposes 149 serial interpreter processes: the exact 142 successful cases and
seven invalid-IUPAC cases from the retained
[shared corpus](../../shared/bounded-corpus-v1/README.md). It compiles nothing,
runs no matched controls, and records no benchmark timing samples. Its 14
controller test methods and the output checker's 12 methods passed on
2026-10-15 UTC, recorded in [the initial pure-validation record](../../shared/pure-validation-20261015/post-prolog-pure-validation-run-v1/report.json).
No actual plan or successful native evidence is supplied.

The original [source map](../primitive-fixtures-v1/bounded-corpus-map.json),
specification and every old source pin remain unchanged. Nine mains execute
from their retained locations. Only Fannkuch selects the additive
[zero-size revision](../fannkuch-zero-v1/main.reb), which keeps positive-size
enumeration and emits the corpus's zero-size summary. The corrected C helper
is selected through the actual approved extension image, with its source/image
binding retained explicitly. No script wrapper changes application execution.

The direct argv is the retained runtime, `-q -s`, the exact selected main, and
the integer size only for integer-input cases. The environment selects only
the approved extension, fresh isolated HOME/REBOL_HOME/TMPDIR and the existing
C-locale/thread policy. Diagnostic interposer variables are absent. Inputs and
expected outputs are read from the pinned corpus; their existing files and
reference receipts are included in the plan's physical input closure.

## Actual prerequisites

Preparation requires a future independent primitive review with schema
`rebol19-independent-primitive-review-v1`, status
`exact-eighteen-primitive-contracts-qualified`, `independent_review: true`,
`full_primitive_fixtures_qualified: true`, 19 native processes, 18 fixture
processes and zero benchmark samples. All downstream correctness, runtime
source-equivalence, work, source-count, timing and chart gates remain false.
This is an actual-result approval, not the fixed19 controller's source review.

Its `references` map names exact `plan`, `report`, `terminal`,
`extension_review` and `source_review` path/SHA pairs. Its `durable` map contains
the closed primitive job directory, complete artifact inventory excluding its
lease file, and the lease's exact path/device/inode. The controller replays the
fixed19 source/plan, actual capture/stream/lifecycle records, output contracts,
complete inventories and durable parent identities. The original failed SDK
producer and separate output-reuse approval stay in the inherited evidence.

A separate `rebol149-controller-source-review-v1` record, status
`independent-source-review-complete-native-cases-pending`, binds this controller,
its tests, README, the Rebol output checker and its tests, and the new Fannkuch
source under `files`. Its only `dependencies` entry is the exact unchanged
`tools/qualification/rebol_primitive_fixtures.py`. It records independent source
review and leaves all downstream gates false. No digest slot is treated as a
successful approval merely because the corresponding source exists.

The original helper retains its own leases. The new primitive lease is held
through a separate combined list, so shorter-lived handles cannot enter the
outer helper's final checks. The common mutex remains continuously held through
all cases, output validation and final closure.

## Output and lifecycle

The [Rebol checker](../../../tools/qualification/rebol_outputs.py) owns the
complete stream contract. Successful cases use exact bytes except the retained
two finite N-body energy lines with tolerance 1e-8. The seven invalid-IUPAC
cases use the source-derived Rebol error route, not another language's exception
or buffering policy. Actual native confirmation of that route remains pending.

The frozen observer's normal nonzero-exit failure records remain unchanged.
Only the exact `Native command exited unsuccessfully`/`AssertionError` envelope,
the reviewed positive exit status, intact birth/PID/group identity, direct-child
reaping, empty groups, no signals/timeouts/cleanup errors and the exact Rebol
streams can establish an expected rejection. An unrelated assertion or wrong
diagnostic stops the stage without retry. Raw stdout, stderr and all observer
receipts remain available on every outcome.

This proposal reuses the existing Rebol primitive specification's per-process
180-second, 512-MiB and 1-MiB stream limits, plus the observer's five-second
cleanup deadline. The corpus defines no alternate resource policy. Reuse is
a bounded execution proposal, not evidence that every case fits those limits.
The corpus's largest retained input/output is below the stream cap. An initial
owned zombie may have unavailable derived RSS (`null`); it never establishes
a measured zero peak or complete memory observation.

Each successful case snapshot binds raw streams to the exact bytes passed to
the checker. Final closure requires the exact 149-by-five observer artifact
membership, validated snapshots, serialized report, immutable input and prior
SDK/extension/primitive inventories, durable inventories and named leases.
All six downstream gates stay false even when every output contract passes;
independent results review is still required.

## Deferred commands

After both real reviews and their exact digests exist:

```sh
PY=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
E=/private/tmp/mech-benchmark-completion
"$PY" -I -S -B "$E/tools/qualification/rebol_bounded.py" prepare \
  --primitive-review "$PRIMITIVE_REVIEW" --primitive-review-sha256 "$PRIMITIVE_REVIEW_SHA" \
  --source-review "$BOUNDED_SOURCE_REVIEW" --source-review-sha256 "$BOUNDED_SOURCE_REVIEW_SHA" \
  --plan "$E/experiments/rebol/bounded-v1/plan-v1.json" \
  --output "$E/experiments/rebol/bounded-v1/run-v1"
"$PY" -I -S -B "$E/tools/qualification/rebol_bounded.py" run \
  --plan "$E/experiments/rebol/bounded-v1/plan-v1.json" \
  --plan-sha256 "$REVIEWED_BOUNDED_PLAN_SHA"
```

The run argv is suitable for the existing durable launcher with the original
evidence repository as cwd. Actual preparation, independent plan review and
exclusive scheduling must precede execution. The focused synthetic test source is
[test_rebol_bounded.py](../../../tools/qualification/test_rebol_bounded.py);
it launches no interpreter, compiler or benchmark.
