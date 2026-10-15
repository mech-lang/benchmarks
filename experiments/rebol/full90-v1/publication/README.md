# Rebol publication candidate intake

The additive [importer](../../../../tools/qualification/import_rebol.py) previews
or applies an independently reproduced full90 candidate to a separate checkout.
Its 16 focused test methods passed on 2026-10-15 UTC, recorded in
[the initial pure-validation record](../../../shared/pure-validation-20261015/post-prolog-pure-validation-run-v1/report.json). No actual Rebol qualification,
full timing cohort, reconciliation, export or publication is claimed by this
source packet.

The evidence root remains `/private/tmp/mech-benchmark-completion`. The
publication root is an explicitly supplied, physically disjoint directory.
Only `data/benchmarks.json`, `data/languages.json` and
`site/src/languages.mjs` are publication targets. Neither measurement sources
nor historical receipts are rewritten. Original qualification, full90 and
durable leases stay held through candidate reproduction, target writes and
final checks. The sole named-path exception is the existing common-lock alias
`/tmp/mech-clbg-timing.lock` to `/private/tmp/mech-clbg-timing.lock`; its exact
resolution and inode 79859134 are rechecked. Other evidence paths remain
physical and nonsymlinked.

The new candidate has twenty source-form rows and ten complete authored bundles:
eight contain four files and two contain five, covering fifteen physical files.
Compact and optimized are disclosed source aliases with independent fresh
samples. No timings are copied. The complete general C extension remains part
of every counted bundle. Formatted LOC is unavailable. Successful forms require
three qualified samples and a successful three-sample matched Mech control;
failed forms or controls retain their raw records without chart coordinates.

The transform preserves existing program rows, counted source metadata,
endpoints, aggregates and baselines. Any new canonical-source or time minimum
rejects the operation for a separate normalization review. This append-only
path makes no normalization-history entry and changes no existing history.

## Required actual inputs

The importer requires exact path/SHA pairs for the candidate, saved independent
reconciliation, original full90 plan, runtime publication metadata, historical
release metadata, exporter source review and importer source review. The
original durable job directory is supplied explicitly. Missing or draft
qualification evidence rejects before publication.

Runtime metadata follows the exporter contract
`rebol-publication-runtime-metadata-v1`. The independent record joins the actual
qualification manifest, runtime, selected extension image and retained evidence.
It also supplies reviewed `label`, `family`, `platform`, `runtime`, `style`,
`memory`, `note`, `sources`, `runtime_policy`, `memory_policy` and display `color`.
Interpretation and dynamic typing remain explicit. A source/release association
is not a runtime-source equivalence proof; per-sample image inventories and
numeric GC defaults remain unclaimed.

Release metadata uses `rebol-publication-release-metadata-v1`, status
`independently-reviewed-release-metadata`, `independent_review: true`,
`language: "rebol3"`, the same `family`, and `chart_admission: false`.
It supplies `release_year`, `release_name`, `release_source`, `release_note`,
an ISO `reviewed_on` date and an `evidence` map of retained path/SHA references.
Historical language introduction is distinguished from the selected runtime
release. The importer does not infer a date from the runtime version. The
reviewed date also keeps preview/apply serialization deterministic.

The importer source review uses `rebol-import-source-review-v1`, status
`independent-source-review-complete-actual-import-pending`,
`independent_review: true`, and false `native_execution`/`chart_admission`.
Its `files` map binds exactly this README, `import_rebol.py` and
`test_import_rebol.py`; its `dependencies` map binds `rebol_export.py` and the
unchanged `import_typescript.py` at
`e8b1945e4b6848cff7953e8eb0d543edd2b7f6d89efc766bf850e065d9e38cf9`.
Only the latter's three unchanged transaction functions are selected from its
pinned source: `apply_prepared`, `rollback_publication` and `write_private`.
No TypeScript evidence modules are imported. Nonblocking regular-file readers
guard those functions' reads.

## Public links and original provenance

Copied public links are exact source paths, count/work receipts, sample receipt
trios and the primary plan/report/terminal, reconciliation and review records.
Every such relative path must contain identical bytes in the evidence and
publication roots before writes and at final closure. All fifteen physical
source paths remain represented even when file content is deduplicated.

Runtime images, extension images, declared dependency closures and transitive
physical proof identities stay in their original provenance fields. They are
not relocated into the publication checkout. Historical matched-control
algorithm references keep their original compiler-worktree namespace; they
are not mistaken for current repository links. Candidate bytes remain
unchanged, and the original reconciler still verifies those fingerprints.

## Preview and apply

Use the retained Python with `-I -S -B`. The following placeholders must be
replaced with actual reviewed paths and digests; they are not supplied receipts.

```sh
PYTHON -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/import_rebol.py \
  --candidate CANDIDATE --candidate-sha256 CANDIDATE_SHA \
  --reconciliation RECONCILIATION --reconciliation-sha256 RECONCILIATION_SHA \
  --plan PLAN --plan-sha256 PLAN_SHA --durable-directory DURABLE_JOB \
  --metadata RUNTIME_METADATA --metadata-sha256 RUNTIME_METADATA_SHA \
  --release RELEASE_METADATA --release-sha256 RELEASE_METADATA_SHA \
  --source-review IMPORT_SOURCE_REVIEW --source-review-sha256 IMPORT_SOURCE_REVIEW_SHA \
  --export-source-review EXPORT_SOURCE_REVIEW --export-source-review-sha256 EXPORT_SOURCE_REVIEW_SHA \
  --publication-root PUBLICATION_ROOT \
  --benchmarks-sha256 BEFORE_BENCHMARKS_SHA \
  --languages-sha256 BEFORE_LANGUAGES_SHA --module-sha256 BEFORE_MODULE_SHA \
  --output FRESH_PRIVATE_PREVIEW
```

Preview writes exact prepared targets, `originals/` backups and
`import-receipt.json` into a fresh private directory outside both checkouts.
For apply, repeat the same inputs and three original target digests, use another
fresh private output directory, and add:

```sh
--apply \
--prepared-benchmarks-sha256 REVIEWED_PREVIEW_BENCHMARKS_SHA \
--prepared-languages-sha256 REVIEWED_PREVIEW_LANGUAGES_SHA \
--prepared-module-sha256 REVIEWED_PREVIEW_MODULE_SHA
```

All three reproduced prepared digests must match the reviewed preview before
any target write. A persistent in-memory journal records each replacement
intent before rename. Exclusive private-file ownership is registered before
write completion, including the final receipt. INT, TERM and HUP unwind the
transaction; creation/registration and the borrowed apply/restore operations
are signal-masked so pending stops unwind only after their ownership journals
are consistent. Body or
final-context failures restore only still-owned target bytes and remove only
still-owned private output. External edits or special files are preserved and
reported while restoration of unaffected files continues.

Actual source freeze, tests, full evidence replay, preview, application and
repository/site verification remain pending. None is implied by this draft.
