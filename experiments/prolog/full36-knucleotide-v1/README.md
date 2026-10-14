# Prolog: 36 unfinished full-workload slots

This continuation retains 54 completed observations and prepares only the four
unfinished workloads: k-nucleotide, binary trees, N-body and fannkuch-redux.
Each workload has two existing Prolog profile labels and one matched Mech
control, with three observations per profile. The remaining schedule therefore
contains 24 Prolog processes and 12 controls. No completed observation is rerun.

The [stopped cohort](../knucleotide-linear-v1/stop-v1/closure.json) contains
40 previously retained observations, 14 completed new observations, and one
deliberately interrupted k-nucleotide attempt. Its report remains
`stopped-unqualified`. The interrupted attempt, partial output, native exit,
sampler cleanup and durable exit remain preserved; its elapsed time is excluded
from the measurements. The original 42 receipt files for the 14 completed
observations are checked against the saved pre-stop checkpoint.

The [controller](../../../tools/qualification/prolog_knucleotide_remaining.py)
reuses the frozen native sampler, process-ownership supervisor, complete-output
validators and generic receipt validators. It independently joins the stopped
prefix to the earlier 40-observation seal. The original plans, controllers,
sources, reports and receipts are unchanged.

## Replacement qualification

The [corrected source](../knucleotide-linear-v1/README.md) converts the parsed
sequence to an atom once before the unchanged seven-map loop. Compilation,
bounded correctness, compiled required-work inspection and canonical source
counts must be completed and independently reviewed before preparation.
There is no successful replacement qualification receipt or runnable plan in
this source-preparation packet.

Preparation requires an explicitly supplied, reviewed SHA-256 for a
`prolog-knucleotide-linear-qualified-v1` receipt. Its status must be
`qualified-source-work-and-canonical-counts-awaiting-full-timing`, with
`bounded_outputs_qualified`, `compiled_inputs_qualified`,
`source_work_qualified` and `canonical_LOC_admitted` all true. Its full-timing
and chart-admission flags remain false.

That receipt supplies exactly two replacement profile rows with the existing
IDs and keys. Only their source, compiler, count and work-review fields, plus
explicit source-alias metadata, may change. Binary identity, runtime
environment, worker count, GC/memory policy and all other profile fields must
match the retained profiles. Both labels represent identical authored source,
without a distinct optimization claim. Separately compiled aliases may retain
their own exact QLF paths.

Each counted bundle contains the main file, `clbg_io.pl` and `clbg_records.pl`.
Every original and compiled source identity, main and helper QLF, loaded-input
inventory, source projection and independent review must be pinned. Per-file
canonical and physical counts must sum to the profile counts; formatted counts
are absent or null. The receipt also contains four exact evidence references
(`compilation`, `bounded`, `source_counts`, `required_work`) and closed native
artifact inventories. Its independent disposition is a prerequisite, not a
claim inferred from successful process exits by the timing controller.

## Preparation and execution

These are future commands. Replace `QUALIFIED_SHA` and `PLAN_SHA` only with
digests of the actually reviewed files. Preparation rejects missing or pending
replacement evidence before replaying the earlier measurement closure.

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/prolog_knucleotide_remaining.py prepare --qualification /private/tmp/mech-benchmark-completion/experiments/prolog/knucleotide-linear-v1/qualification/qualified-v1.json --qualification-sha256 QUALIFIED_SHA --plan /private/tmp/mech-benchmark-completion/experiments/prolog/full36-knucleotide-v1/plan-v1.json --output /private/tmp/mech-benchmark-completion/experiments/prolog/full36-knucleotide-v1/run-v1
```

After independent review of the concrete prepared plan, the existing durable
launcher passes the exact command below, with the original physical checkout
as its working directory. Use the fresh job name `knucleotide-remaining36-v1`:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/experiments/prolog/full90-v1/launch_durable.py --job knucleotide-remaining36-v1 --cwd /private/tmp/mech-benchmark-completion --command-json '["/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12","-I","-S","-B","/private/tmp/mech-benchmark-completion/tools/qualification/prolog_knucleotide_remaining.py","run","--plan","/private/tmp/mech-benchmark-completion/experiments/prolog/full36-knucleotide-v1/plan-v1.json","--plan-sha256","PLAN_SHA"]'
```

Preparation and execution acquire the original three durable leases, the
original suite lease and the common timing mutex. The new durable worker holds
an additional private lease. The common mutex remains inherited by the sampler
and native child through cleanup and terminal creation. Original lease files
are opened without recreation, with their recorded inode identities checked.

Timing includes fresh process startup, runtime and QLF loading, input,
computation, output and shutdown. Hashing, compilation and output validation
remain outside the timer. Limits remain six hours and 10,240 MiB sampled
process-group RSS per native process, with a 22,200-second outer deadline.
There are no retries. An isolated workload failure excludes that profile's
partial aggregate and skips its later slots; ownership, environment or
integrity failures stop the cohort. Signals are masked during sample transfer
and finalization. Exact receipt snapshots, retained and replacement artifact
inventories, serialized report bytes, prerequisite pins and the named mutex
are checked before the terminal is written.

The producer grants no full-timing or chart admission. An independent
closed-cohort reconciliation and publication review are still required after
the actual run; the earlier complete-50 reconciler cannot be used to present
the stopped producer as complete.

## Source validation

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/test_prolog_knucleotide_remaining.py
```

The small suite replays the saved 14 receipt trios and the interrupted native,
wrapper and ownership receipts. It uses a reduced synthetic pin map derived
from their saved fingerprints, without reading full historical plans or
hashing runtime closures. Other tests cover altered ownership and stop
dispositions, missing replacement proof and helper counts, schedule reuse,
subject/control failures, and late file, report and mutex changes. These tests
do not constitute actual preparation, native execution or full physical replay.
