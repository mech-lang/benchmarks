# Serialized nine-reader stage

The [controller](../../../../tools/qualification/prolog_revcomp_loc.py) makes the
source-only command draft executable after the linear candidate's bounded
conformance stage has passed. Its prerequisites are the actual successful
542-process report, terminal and durable-owner terminal. Preparation remains
unperformed; no native reader or candidate count is qualified yet.

Preparation takes an exclusive nonblocking lock on the existing common mutex,
inode 79859134. It verifies the exact bounded plan and inherited physical pins,
all native artifact hashes, the 542-command/PID ledger, each start/active/final
receipt, the old controller's durable PID, exact stdout/stderr, successful and
rejected fixture counts, the copied compiler input, QLF and inspected WAM. The
original 31-test reader receipt and terminal must remain passed and select the
same immutable V5 reader/counter. No prerequisite native command is repeated.

After the bounded stage closes successfully, supply its actual three receipt
hashes to this preparation command:

The bounded run must be launched with the retained interpreter, `-I -S -B`,
and absolute physical controller and plan paths under
`/private/tmp/mech-benchmark-completion`. The prerequisite replay checks those
exact arguments against the durable owner's observed command identity.

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/prolog_revcomp_loc.py prepare \
  --bounded-report <bounded-run>/report.json \
  --bounded-report-sha256 <actual-report-sha256> \
  --bounded-terminal-sha256 <actual-terminal-sha256> \
  --bounded-durable <bounded-owned-job>/terminal.json \
  --bounded-durable-sha256 <actual-durable-sha256> \
  --plan experiments/prolog/revcomp-linear-v1/source-counts-v1/plan-v1.json \
  --output experiments/prolog/revcomp-linear-v1/source-counts-v1/run-v1
```

Preparation verifies closures but starts no native process. Launch the following
command through the retained durable launcher, using the printed plan hash:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/prolog_revcomp_loc.py run \
  --plan experiments/prolog/revcomp-linear-v1/source-counts-v1/plan-v1.json \
  --plan-sha256 <actual-plan-sha256>
```

The run verifies the same closed prerequisite again, holds the mutex throughout
all nine commands, and starts one process at a time. It uses the frozen generic
observer from `prolog_revcomp_bounded.py`, SHA
`642e0f761aa873023eb24e8a66e9a6837d57f1eb9568e80fe1478a263e95bda9`,
with its 30-second deadline, five-second cleanup bound, 2 GiB process-group RSS
ceiling, 8 MiB file limit, inherited mutex, process-birth checks and owned reaping.
The receipt kind remains the observer's frozen `prolog-revcomp-bounded` protocol;
the stage report separately records that every command is a metadata or source
reader. No candidate main, QLF compilation or benchmark sample is run here.

The first command validates ordinary-builtin metadata. The next seven read the
new fixture sources and check exact counts or diagnostic kinds. The ninth reads
the original candidate, requires exact original/compiler-source byte equality,
and compares written predicate definitions with the already inspected WAM.
Complete source-owner expansions are retained for independent review. Native
JSON, stderr, start/active/final receipts, projections and validation records
remain raw artifacts; no warning or error line is filtered.

Success means nine completed readers, seven matched fixture expectations and
an unresolved-diagnostic-free candidate projection. The controller independently
reconciles its registered process ledger, validates final receipts, checks every
validated artifact snapshot, and rehashes all pinned inputs before recording a
terminal. Fresh output is required and there is no automatic retry. Canonical
admission, source-work qualification and chart admission remain false until the
candidate owner review and subsequent stages justify them.

The [pure tests](../../../../tools/qualification/test_prolog_revcomp_loc.py)
exercise historical-parent replay without changing the frozen validator,
incomplete bounded cohorts, native ownership/reaping, closed inventories,
historical reader gates, exact source schedules/projections, missing or extra
receipts, late artifact/input changes and failed inventory retention. They
start no Prolog process and hash no runtime closure.

Independent source review found no remaining blocker in the controller. All
sixteen pure tests passed in 0.265 seconds. The reviewed source digests are
`e135716a6f4f2778e06d222e5351c16944cb34d68dc067041772f86b907d74ef`
for the controller and
`131479411a162f5d09e31deed643613bdd9916342a48b8d0bcdb0a895fcc2984`
for its test suite. This establishes source readiness; it does not establish
the actual runtime metadata, reader output or candidate canonical count.
