# Mech record-runtime catalog admission

The catalog adds four independently measured Mech AOT configurations from the
[seven-round buffer-reuse study](../revcomp-buffer-reuse-v1/RESULTS.md), retaining
**28 fresh observations**. The application source is identical across them.
The selected Mech reverse-complement endpoint is **0.1229 s (1.00× new Mech AOT)**,
versus the fresh original parent at **0.1433 s (1.17×)** and compaction alone at
**0.1293 s (1.05×)**. The eight-partition reused configuration is **0.1233 s
(1.004×)**. Ratios refer to this same cohort; no global optimality is claimed.

All historical program/source records, samples, authorship, source counts and
fixed normalization baselines remain unchanged. The Mech endpoint and aggregate
update from the new measurements. Older cohorts remain separately inspectable;
observations are not overwritten, pooled, aliased or inferred. The unchanged
published Rust control remains in the study's complete 35-observation report.
Admission launches no compiler, runtime or benchmark.

`cohort.json` binds every sample to the original raw process and complete-output
hash receipt. Full stdout was actually written, checked after process closure,
then omitted with size/hash receipts. The five official small outputs remain
complete. All 61 parent/candidate bounded behaviors match at each step, while
**eleven pre-existing broader FASTA source limitations** remain explicit.
Ten runtime tests pass, including 2,736 recycled-buffer parser cases and checks
that live aliases remain untouched. The native compute object is byte-identical.
The final test-only refinement rebuild is identical to the timed executable.

## Source size and attribution

The existing **seven-unit retained source count** is inherited only because the
complete application source hash is unchanged. This is not a new logical-owner
or canonical-format qualification. All four records leave native formatted LOC
unavailable; existing source metrics still provide exact UTF-8 bytes,
deterministic gzip and pinned BPE counts. No compiler/runtime code is represented
as newly removed application source, and no benchmark operation is moved into a
new workload-specific helper.

The unchanged application's original authorship and license gaps remain explicit.
Writing a general runtime optimization does not establish authorship of that
application. The authorship auditor binds only these four exact source identities
to their existing parent. Runtime changes are separately identified by compiler
commits and [PR #910](https://github.com/mech-lang/mech/pull/910).

## Reproduction and guarded application

The Data view's reproduction records include the exact emitter and per-profile
runtime commits, saved emitter build command/features/environment, application
build commands, Rust toolchain, Cranelift version, GMP build dependency pin,
executable hashes, worker policy, stdin identity and generator source/command,
complete output identity, OS/hardware, power/swap scope and all seven samples.
The compact version label preserves both emitter and runtime identities.

The emitter CLI is built at `6de19875e2266f39c93712800c400672a44b98c9`. Preserve
that executable, then restore the runtime checkout for the selected profile
before running its saved application build command. Runtime commits are the base
`6de19875e`, compaction `6634f1f4d`, or compaction plus reuse `fca1ba1f7`.
Saved absolute checkout paths and toolchain/input caches need adapting/restoring
on another machine. Installed library pins from the emitter study are not
misrepresented as fresh reverse-complement loader captures.

`tools/qualification/import_mech_revcomp.py prepare` checks three frozen evidence
seals, raw timings, complete-output receipts, source/object/build identity,
source-bound attribution and process closure. It creates a preview binding both
canonical inputs and outputs. `apply --expected-preview-sha256 DIGEST` reproduces
that preview before installing the two catalogs. Source/evidence drift,
duplicates, changed fixed minima and unexpected concurrent edits are rejected.
Partial writes roll back without overwriting another writer's changes.
`SUCCESS.json` records the final apply.

The first uncommitted preview omitted the full emitter build recipe and hid the
runtime identity in the compact version label. Its canonical inputs were restored
through a drift-protected transaction before correction. That superseded preview
and apply remain in `attempts-v1/`; no benchmark or timing changed. The first
validation wrapper also encountered a nested-lock error in historical replay.
The historical replay and standalone Clojure projection lock conflicts remain
in `validation-attempt-v1/` and `validation-attempt-v2/`; existing verifier checks
were preserved. The corrected wrapper lets pure historical replay acquire its
own lock and holds the common mutex for browser checks.

Exports, source metrics, exact-source projections, reproduction records and
browser assets are rebuilt from the admitted catalog. Local validation receipts
are in `validation/`. Website push and live asset verification are recorded in a
separate deployment packet; this packet alone does not claim a live deployment.
