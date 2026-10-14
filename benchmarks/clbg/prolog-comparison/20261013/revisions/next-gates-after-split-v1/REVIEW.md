# Prolog next executable gates after the repository split

Source-only review of the complete eight-file `prepared-work-v2` packet and
five-file `loc-normalization/20261013/prolog-proposal-v3` packet. The retained
scored-source/WAM review and original main/helper LOC input paths were also
read. No fixture, scanner, observer, compiler, benchmark, source hash, import,
Git operation or evidence qualification ran during this review. This fresh
note is in the authoritative benchmarks repository; frozen historical workers
and results remain unchanged.

The three existing target commands below are ready for the reviewed source
capture and serialized execution. A post-reader source replay and final
work/LOC admission consumer are still missing; neither pending fixture runner
already performs those stages. Do not rerun preparation, original QLF builds,
original WAM inspection, the six preparation fixtures or eleven owned-service
fixtures.

## Actual reusable authority

The all-20 preparation report is
`qualification/prepare-explicit-goal-rest-v1/report.json`, recorded SHA
`cab6ea7f3bd8a237f8f83833ed9b9cc293bbe1878cc8a894d74fdcf41f7ffbff`.
Its body/durable terminal SHAs are `716ba1503f06629304bba8932569d8418d214794a41d0b0395dab60bff20029d`
and `21d10035fea80c16dd4514f762e8a92f79af806662b2aed19f133c339906842f`.
The maintainer's 14,611-pin receipt is
`continuation/jobs/prolog-remaining155-closed-review-v1/receipt.json`, recorded
SHA `139d9124d3df942bb3170112b3841c33b0191580a002f974835a627651be9bc8`.
These retain 156 actual bounded cases, twenty original compiled profiles and
the qualified runtime `7fa470a9827e60e84eb9c6ad343cc8385e411b400f0ae8a322fbefda488bb448`.

`revisions/scored-work-review-v1/REVIEW.md` already supplies the whole-20
source/original-WAM semantics review, including fresh tree compounds and
retained root lifetime, seven full overlapping-window maps, and two independent
Pi divisions. It reports no unresolved source/WAM mismatch, but cannot replace
the pending thirty actual observer cases. Its actual frozen digest must be
captured by root when a later admission consumer binds it.

## Execution location and fresh captures

Use the historical host checkout for these already authored workers:

```sh
PY=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
HOST=/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech
CLBG=$HOST/benchmarks/clbg
WORK=$CLBG/prolog-comparison/20261013/revisions/prepared-work-v2
READER=$CLBG/loc-normalization/20261013/prolog-proposal-v3
```

All three durable requests must use `cwd=$HOST`. The narrow authority helper
derives paths from its real source file and checks historical absolute argv,
cwd, source, runtime and terminal pins. Executing a relocated new-repository
copy would select different prerequisite paths and fail those exact checks.
The new repository is authoritative for versioned source/history; the old
checkout remains the explicitly retained artifact host for these stages.

The reviewer must first capture two fresh read-only JSON packets, each with exactly
`schema` and `pins`, after confirming these sources are reviewed and read-only:

* Work schema `frozen-prolog-prepared-work-v2`: the eight absolute `$WORK`
  paths `run.py`, `qualified_preparation.py`, `fixture_runner.py`,
  `instrument_sources.py`, `work_proofs.py`, `test_work_proofs.py`, `observer.pl`
  and `REVIEW.md`, plus the actual resolved `$PY` executable: nine pins.
* Reader schema `frozen-prolog-reader31-actual-preparation-v3`: the five
  absolute `$READER` paths `run_fixtures.py`, `foreign_prolog.py`,
  `test_prolog.py`, `scan_source.pl`, `REVIEW.md`, plus
  `$WORK/qualified_preparation.py`, `$WORK/REVIEW.md` and actual resolved `$PY`:
  eight pins.

Packet paths/digests below are mandatory the maintainer captures, not fabricated future
receipts. Use the existing `continuation/launch_durable_v1.py`, a new private
job name for each target, and its exact target argv in `--command-json`.
The target owns common inode 79859134 itself; do not wrap it in a second
common-lock holder. Inspect results only after the private lease closes.

## Ordered commands

1. Execute the six new pure work fixtures once. Suggested fresh durable job:
   `prolog-prepared-work-six-v2`.

```sh
"$PY" -I -S -B -u "$WORK/run.py" \
  --fixtures --packet "$WORK_PACKET" --packet-sha256 "$WORK_PACKET_SHA"
```

The exclusive output is
`prolog-comparison/20261013/work-qualification/prepared-work-v2-fixtures-v1`.
The worker permits no native command on this branch and sets its outer bound
to 600 seconds after common acquisition. Require normal durable exit 0,
request/start/worker/terminal identity closure, report/body status
`six-work-fixtures-passed-awaiting-thirty-probes`, exactly all six discovered
and started IDs, no failure/error/skip/expected-failure/unexpected-success,
complete terminal pins and zero native/probe counters. Capture the actual
report/body/durable digests for step 3; retain the original packet arguments.

2. Execute the unchanged thirty-one reader methods once. Suggested fresh job:
   `prolog-original-reader31-v3`.

```sh
"$PY" -I -S -B -u "$READER/run_fixtures.py" \
  --packet "$READER_PACKET" --packet-sha256 "$READER_PACKET_SHA" \
  --output "$READER/jobs/reader31-v1"
```

This is independent of the work fixture result, but the same serial slot can
run it before the larger observer batch. The output must be absent. Each
scanner invocation is owned and bounded to 20 seconds. Require actual all-31
discovery/start/pass without skips or expected failures, report/body status
`passed-awaiting-original-source-review`, every scanner/projection/input pin,
normal durable exit 0 and full process identity/lease closure. The two parser
error scenarios require actual clean nonzero native status; timeout or cleanup
failure cannot satisfy them. No original subject is consulted or run.

LOC v3 already moves success `halt(0)` after `catch` and replaces the stale
failed runtime-v2 prerequisite with the actual cab6/139d authority. Those
repairs mentioned in the older work/LOC plan must not be implemented again.

3. After the exact six-fixture closure, execute the thirty new observer cases
   once. Suggested fresh job: `prolog-prepared-work-thirty-v2`.

```sh
"$PY" -I -S -B -u "$WORK/run.py" \
  --work-probes --packet "$WORK_PACKET" --packet-sha256 "$WORK_PACKET_SHA" \
  --fixture-owner "$CLOSED_WORK_FIXTURE_OWNER" \
  --fixture-terminal-sha256 "$ACTUAL_WORK_FIXTURE_DURABLE_SHA" \
  --fixture-report-sha256 "$ACTUAL_WORK_FIXTURE_REPORT_SHA" \
  --fixture-body-sha256 "$ACTUAL_WORK_FIXTURE_BODY_SHA"
```

The exclusive output is
`prolog-comparison/20261013/work-qualification/prepared-work-v2-probes-v1`.
This command does not depend on the reader31 receipt. It cold-checks/reuses
step 1 rather than running its fixtures again. It creates only six separately
instrumented input roots: original scored source/QLF/WAM remain unchanged.
Exact insertions must reverse to the original main bytes. There are 26 bounded
compiler/inspection commands and 30 probe processes, 56 new native commands
total; each retains its 120-second bound, with a 7,200-second outer bound after
common acquisition. Cases are tree n=0,4,7,9 per form (8), Pi
n=0,1,9,10,11,27,97 per form (14), and the four literal K payloads per form (8).

Require normal exit 0, exact 30 unique `(profile,case)` pairs, six instrumented
profiles, all raw native ownership/output checks and original output oracles,
all source derivations/compiler inventories/traces/proofs pinned, and report
status `thirty-instrumented-work-probes-passed-awaiting-scored-source-and-WAM-review`.
Review partial artifacts on failure; the fixed output rejects retries. The
map proof explicitly does not trace each window, so the retained original
source-loop/WAM review remains required. Synthetic fixture traces do not count
as actual observations. A successful worker still leaves original scored work
qualification false until a separate admission consumer combines the evidence.

## Minimum source work after these actual gates

No whole-bundle replay/sealer executable exists in the reviewed thirteen-file
packet. Add one narrow guarded replay consumer after reader31 actually closes,
using `qualified_preparation.load`, the original owned-command service and the
unchanged scanner/projector; no new parser or fixture framework is needed.
It must retain reader31 command/lease/outcomes and the shared source packet,
then perform these exact steps:

1. Read native AST receipts for the twenty **original** main paths
   `revisions/prepare-success-halt-v1/sources/<benchmark>/{compact,optimized}.pl`
   and whole `support/clbg_io.pl`, `support/clbg_records.pl`: 22 original paths.
   Select by explicit `language=prolog`, never `.pl` alone. Pass source as data
   with the existing `scan_source.pl` argv; preserve each original byte stream,
   native stdout/stderr/status, reader settings/operator inventory/EOF, AST,
   character-to-byte positions, owner events and diagnostics. No directives,
   goals, QLF or WAM are evaluated as counted input.
2. Build one exact `BundleContext` per profile using that main and its actual
   compiler-bound helpers. Include whole IO in all twenty; whole records in
   both K and both revcomp forms. The compiler `source_bundle` entries already
   bind original paths to measured copies. Reconcile all 44 references and
   copies, including compact regex's old `prepare-success-halt-v1/builds`
   location and the other nineteen `prepare-explicit-goal-rest-v1/builds`
   locations. Verify original source/QLF/WAM/runtime/vendor pins, preserving
   explicit identical-source aliases and every original evidence object.
3. Independently review every canonical event/full-owner span, literal-data
   continuation, executable clause/control/meta close, helper import and
   callback/formal flow. All definitions/imports use actual source paths.
   `clbg_io:run/1` has declared formal meta flow; `run_checked/1` is inferred
   from its written forwarding body. Regex's selected PCRE `re_foldl/6`
   callback binds to written `count_match/3`; vendor kernel source is excluded
   while the entire authored caller and callback remain counted. Unknown
   calls/operators/expansions/hidden goals or invalid spans leave LOC null;
   neither physical lines nor generated code may fill a failed count.
4. Only after an exact source-bound meaning review, derive each of twenty
   whole-bundle totals from its main plus all counted helpers. Preserve the
   actual scanner/projection diagnostics even if an additive semantic review
   is later required. Bind this review and actual thirty-case work closure
   with `scored-work-review-v1/REVIEW.md`, original WAM/factory/library evidence
   and cab6 preparation into a new explicit all-20 work/LOC receipt.

Full-output/timing qualification remains later: this packet authorizes no full
workload, full90, runtime/chart metadata or publication. None of the 156 bounded
cases is a canonical timed sample. Reuse the existing prepared artifacts and
owned sampler only after the actual all-20 work/LOC receipt is independently
accepted; any eventual full90 and chart admission require their separate
source-reviewed controller and actual complete receipts.
