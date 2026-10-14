# Read the real empty list without accepting the quoted atom

Additive V5 fixes the actual native reader's empty-list representation. V4
successfully repaired the literal `/var` input argv and ran all31 methods, but
21 failed and10 returned success. Its native JSON represents the real module
export list `[]` at characters13–15 as `kind:unsupported, detail:[]` because
SWI10.0.2 does not classify the empty list as an atom. That baseline diagnostic
also confounds negative fixture passes; none qualifies this corrected scanner.
V3/V4 sources, raw native successes/errors, all projections and closures remain
unchanged. The previously passed six work fixtures are reused, never repeated.

Actual V4 closed review:
`continuation/jobs/prolog-original-reader31-v4-closed-review/receipt.json`
SHA `c41ca6eab3e8a8f43ac5842c566480ece9806e3af9eb557576b7e05775db6229`,
15,057 verified pins, worker23681/target23689, normal exit1. Its report is
`2eb2470a8c4c2c6dc3206843c3b1356a6ee62404653893d1c030103f42dd5239`,
body `f166dc226f070f991a7cc18348792f89b370643d66f6227374ecdc48ce993d2a`,
durable `df4e378d8e7d53fbeddb196c32d17c18bea13a06f3926aa967b404a228ce8d6d`.

The scanner now checks `Term == []` explicitly at a simple original position
and emits the already supported list node with zero children and null tail.
It does not unify or mutate a variable. The quoted atom `'[]'` continues through
`atom(Term)` and remains an atom node with value `[]`. The projector accepts
only real closed list nodes for predicate-indicator lists; the former atom
shortcut is removed. Thus the positive nil fix cannot admit a quoted atom as
module exports or selected imports. Literal-continuation handling likewise
recognizes real list/string data rather than the quoted empty-list atom.
Written spans, owner units/control/meta rules, parser options, complete EOF,
unselected operators/goals and all original process/source gates are unchanged.

The existing `test_formal_and_data_commas_are_structural` method keeps its
original positive assertion and adds a real native read of a quoted-atom export
header. It checks atom identity and requires null count plus the exact closed
predicate-indicator-list diagnostic. All31 method IDs remain unchanged; full31
execution is needed for this corrected scanner and projector fingerprint.

The runner retains all V4 path/owned-service/unittest/terminal machinery and
the original failed-V3 dependency. It additionally binds the exact actual V4
failure/31 IDs/21 failures/0 errors, its root copies, native scanner/projection
artifacts and process identity under the closed V4 private lease. The original
prepared-work-v2 authority stays at the pinned historical host, preserving
cab6/139d and all20/156 source/QLF/WAM/runtime/library records. No earlier
preparation, original subject, passed six work fixtures or old6+11 is rerun.

The maintainer captures a readonly JSON packet with schema
`frozen-prolog-reader31-actual-preparation-v5` and exactly eight pins: five new
V5 files, original old-host `qualified_preparation.py` and its `REVIEW.md`, and
the actual resolved bundled Python3.12 image. Source/new output belongs to the
new repository, exclusive `prolog-proposal-v5/jobs/reader31-v1`. The new durable
job is `prolog-original-reader31-v5`, with cwd the new benchmarks repository.

Run exactly the existing reader fixture command through its durable launcher,
with actual captured packet path/SHA and V5 output. All native readers retain
their20-second owned bound; common inode79859134 spans imports, scanners and
terminal checks. Three historical authority leases and both failed reader
leases remain closed and held shared. Require actual all31 pass and complete
normal0/identity/pin closure before work30 or original22-source LOC replay.
Any further failure remains raw evidence and causes no automatic rerun.
This fixture stage qualifies no source-work, canonical/formatted LOC, timing
or chart point.
