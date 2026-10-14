# Preserve the actual Prolog fixture input argv spelling

Additive repair of the actual failed reader31 v3 run. All 31 methods started
and errored at the owned-scanner exact-argv guard; no scanner or projector
attempt started. The original v3 source packet, failed output and durable
terminal remain unchanged. Its closed review is
`continuation/jobs/prolog-original-reader31-v3-closed-review/receipt.json`,
SHA `d7788b21f43a9a85566c9068f28bf13ca53e52d013e0d2f31f5528579b2a9981`;
report `5ebb6fca37414fcc7032620aa5de43585436f326369af21b00505b2df0b60f16`,
body `6df8de7376d395e1d940f91ceced89b3913bfeb5ffdd1540d8addf40e3571a08`,
durable `2d5922dafe599386eadfdc26296b62e1a664adcd3261efde02d838463abb8760`.
The normal exit1 process identities are worker19041/target19046. All14,641
input/artifact pins were physically verified and copied to the new repository.

The original fixture calls use `tempfile` paths under `/var/folders/...`.
The old wrapper resolved the last argument to `/private/var/folders/...` and
then demanded that different spelling equal the unchanged original argv.
A common-locked metadata check confirmed `/var` links to `private/var` and
the original/resolved test file paths are `samefile=True`; it ran no scanner.

V4 preserves the original absolute input argv and separately verifies its
resolved file identity. The path must be an absolute, existing regular file
and not itself a symlink; native invocation retains the exact original argv.
Input archiving resolves the file and records both invocation and resolved
source paths. Binary, scanner path, flags, goal, owned process policy and
20-second bound are unchanged. No broad executable/path alias is admitted.
`foreign_prolog.py`, `test_prolog.py` and `scan_source.pl` are unchanged v3
bytes: all31 method bodies/IDs, the owner policy, non-evaluating reader and
success halt outside catch remain exact.

This fresh packet lives in the authoritative new repository. Its shared
actual-preparation authority is explicitly the frozen old-host
`prepared-work-v2/qualified_preparation.py`, preserving historical absolute
paths/cwd and successful cab6/139d runtime/compiler/QLF/WAM/156-case pins.
The runner verifies and retains the closed failed-v3 dependency before any
scanner, including exact command/request/start/worker/terminal, actual31 errors,
zero attempts/projections and complete root copy/original pins. Those failed
methods are necessary first executions after repair, not repeated successes.
The already passed six work fixtures and prior6+11 remain reused separately.

The maintainer captures a readonly packet with schema
`frozen-prolog-reader31-actual-preparation-v4` and exactly eight pin paths:
five absolute new v4 files, the two original old-host authority/helper-note
files, and actual resolved bundled Python3.12. The exclusive output is the
new packet's `jobs/reader31-v1`; a fresh durable job must preserve this new argv.
Three original closed authority leases plus the failed-v3 lease and the common
inode79859134 remain held through native scanners and terminal reconciliation.

```text
bundled-python3.12 -I -S -B -u NEW_REPO/benchmarks/clbg/loc-normalization/20261013/prolog-proposal-v4/run_fixtures.py
  --packet ACTUAL_V4_PACKET --packet-sha256 ACTUAL_V4_PACKET_SHA
  --output NEW_REPO/benchmarks/clbg/loc-normalization/20261013/prolog-proposal-v4/jobs/reader31-v1
```

Require actual all31 discovered/started/passed, exact owned scanner receipts,
normal durable0 and full pin/identity closure before original-source replay.
No original subject/QLF/WAM/preparation, passed fixture or benchmark reruns.
Any reader failure remains preserved and prevents automatic dependent launch.
LOC/work/chart admission remains null/false; no numeric count is qualified here.
