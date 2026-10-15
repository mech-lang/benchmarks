# Full-size APL binary trees with workspace scale 200

This source draft schedules six fresh processes at N=21: three executions of the
unchanged APL tree program and three matched Mech AOT controls. Rounds alternate
APL/Mech, Mech/APL, APL/Mech. The optimized label is an explicit source and timing
alias of the compact implementation; it adds no native execution.

Each APL command runs the counted workspace assignment before the tree source
inside the original full-process timer. Interpreter startup, parsing, setup,
construction and traversal, output, and shutdown are included. The measured
bundle is 40 canonical tree units plus one setup unit. Compilation, pin checks,
environment waits and output validation remain outside the timer. The runtime,
one-worker argument, allocator and garbage collection remain unchanged.

Every actual process is supervised with a 14,400-second native deadline, a
15,000-second outer deadline and the existing 10 GiB sampled process-group RSS
guard. One common mutex descriptor numbered at least 64 stays held through all
six slots and final cleanup; APL retains descriptor 3 for output. The completed
configuration, diagnostic and small-subject ownership leases also remain held.
The first unqualified attempt stops the cohort. There is no retry, skip, resume,
warmup, new diagnostic or repeated completed sample.

The frozen sampler retains full stdout byte counts and hashes and validates the
455-byte N=21 oracle. It retains the exact 54-byte shutdown diagnostic in each
APL sample. Any missing, extra or different stderr rejects the sample. The Mech
control requires empty stderr. Original workspace failures, the earlier failed
allocation witness and all later successful bounded captures stay unchanged.

The prerequisites are the completed scoped ownership and N=4/N=10 work reviews,
an independently qualified exact 41-unit source-count receipt, and a separate
source-work disposition. The latter must bind the unchanged Make/Check and Run
definitions, the setup assignment and bounded evidence. The source constructs
the stretch tree, retains the long-lived root across all repeated-tree depths,
and constructs and traverses a fresh tree for every iteration. At N=21 the
specified loops require 613,766,494 node constructions, including stretch and
long-lived trees. This arithmetic is a source obligation, not an observed
full-size allocation count or proof of resource feasibility.

`Make D` constructs one root and, for positive `D`, recursively constructs both
children. Its node count is therefore `T(0) = 1` and
`T(D) = 1 + 2 T(D-1) = 2^(D+1) - 1`. `Check` visits the root and both children;
the timed source does not substitute this formula for construction or traversal.
For N=21, the stretch tree at depth 22 requires 8,388,607 nodes and the long-lived
tree at depth 21 requires 4,194,303. The nine repeated depths 4, 6, …, 20 each
run `2^(25-D)` iterations. Their total is
`Σ[2^(25-D) × (2^(D+1)-1)] = 601,183,584` nodes. The sum of all three parts is
613,766,494. The source drops the stretch root before constructing `Long`, keeps
`Long` until the final check, and invokes `Make` and `Check` inside every repeated
iteration. The retained scoped diagnostic supports bounded ownership and
release, while the N=4/N=10 captures support the complete program's small-input
behavior. Neither establishes full-size completion.

The count and source-work dispositions are not yet written. Preparation and
native execution are unstarted, and timing/chart admission remains false. The
controller requires exact paths and SHA-256 values for both future approved
receipts. It replays their small owner metadata and the retained native evidence
under the original leases before creating an executable plan. A successful
measurement still requires independent reconciliation and publication review.

The 9 focused pure test methods passed on 2026-10-15 UTC, recorded in
[the initial pure-validation record](../../../shared/pure-validation-20261015/post-prolog-pure-validation-run-v1/report.json). Once the required source
reviews are complete, prepare from the original evidence checkout while the
timing lane is free:

```sh
python3 -I -S -B tools/qualification/apl_workspace_full.py prepare \
  --counts /absolute/path/to/qualified-source-counts-v1.json \
  --counts-sha256 APPROVED_COUNT_SHA256 \
  --work /absolute/path/to/required-work-review-v1.json \
  --work-sha256 APPROVED_WORK_SHA256 \
  --plan /absolute/path/to/full6-v1/plan-v1.json \
  --output /absolute/path/to/full6-v1/run-v1
```

After reviewing the concrete prepared plan, invoke its `run --plan ...
--plan-sha256 ...` command through the existing durable owner using the retained
Python with `-I -S -B`. No plan or qualification digest is supplied by this draft.
