# TypeScript publication from a closed full60 cohort

This packet contains publication tooling for ten real typed TypeScript applications, one per workload. It contains no completed full60 timing cohort, candidate, preview or catalog admission. The existing strict compile/AST capture, 149 bounded cases, canonical source-owner decision, 27 required-work contracts, direct tree/pi captures and static runtime review are reused.

The [exporter](../../../../tools/qualification/typescript_export.py) reproduces the [independent reconciliation](../reconciliation/README.md) while the completed durable-job, TypeScript-cohort and common timing leases remain held. Each row binds its authored `.ts` source, exact staged source copy, emitted CommonJS `.js`, source map and native AST. Canonical LOC counts the typed application only; formatted LOC is unavailable. The emitted artifacts remain execution evidence rather than an alternative source count.

The proposed cohort has 30 fresh direct Node subject processes and 30 matched Mech controls. It adds no diagnostic flags, forced optimization, warmup or compiler invocation to timed subjects. Node startup, JavaScript loading, runtime JIT, input, computation, complete output and shutdown are inside the full-process interval. TypeScript compilation is outside it. The recorded `UV_THREADPOOL_SIZE=8` policy is retained; it is not a claim that every workload uses eight workers or that V8 has at most eight threads.

[Runtime metadata](../runtime-metadata-v1.json) records TypeScript 7.0.2, Node 24.19.0 and V8 13.6.233.17-node.51. It binds the exact retained Node/application identity, recorded embedded versions, static declared system dependencies and host OS build. It claims neither a per-timed-process loaded-image inventory nor numeric GC defaults. V8's JIT classification does not imply that every function is optimized. [Release metadata](../release-metadata-v1.json) uses TypeScript's first public release, October 1, 2012, supported by Microsoft's official retrospective.

Every candidate retains actual sample receipts, standard deviation, matched controls, failures and skipped slots. A failed subject has no admitted median. A failed control leaves any completed subject observations intact but excludes that workload's chart endpoint. All ten real source records remain in the inventory; only eligible endpoints enter `programs`. There are no invented compact/optimized variants or source/timing aliases, and matched controls never replace current Mech results.

The [importer](../../../../tools/qualification/import_typescript.py) independently reproduces the pinned candidate, prepares the dataset, language catalog and site metadata module, and optionally applies all three under the same held leases. It preserves existing raw rows, sources, measurements, baselines and aggregate records. A newly winning TypeScript LOC or time minimum stops both preview and apply for a separately reviewed normalization change; this packet does not guess such a change. Canonical-only aggregate coverage explicitly lists the admitted workloads, and no formatted aggregate is added.

## Closed-evidence commands

Run these file phases only after the actual full60 cohort closes and the common timing lane is free. They verify the retained physical closure and do not launch native code. Use actual saved paths and digests from the completed cohort; none is supplied by this source-only packet.

```sh
ts_python=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
ts_plan=experiments/typescript/full60-v1/plan-v1.json
ts_job=experiments/shared/owned-jobs-v1/owned-jobs/typescript-full60-v1
ts_review=experiments/typescript/full60-v1/reconciliation/review-v1.json
ts_candidate=experiments/typescript/full60-v1/publication/candidate-v1.json
```

Set `ts_plan_sha` and `ts_review_sha` to the actual closed plan and independently reviewed reconciliation digests. Export into a fresh retained candidate path:

```sh
"$ts_python" -I -S -B tools/qualification/typescript_export.py \
  --plan "$ts_plan" --plan-sha256 "$ts_plan_sha" \
  --durable-directory "$ts_job" \
  --reconciliation "$ts_review" --reconciliation-sha256 "$ts_review_sha" \
  --output "$ts_candidate"
```

Set `ts_candidate_sha` from the successful export, `ts_importer_sha` from the independently reviewed importer source, and the three input digests from the actual current publication files. Preview into a fresh private directory outside the repository:

```sh
"$ts_python" -I -S -B tools/qualification/import_typescript.py \
  --plan "$ts_plan" --plan-sha256 "$ts_plan_sha" \
  --durable-directory "$ts_job" \
  --reconciliation "$ts_review" --reconciliation-sha256 "$ts_review_sha" \
  --candidate "$ts_candidate" --candidate-sha256 "$ts_candidate_sha" \
  --importer-sha256 "$ts_importer_sha" \
  --benchmarks-sha256 "$ts_benchmarks_sha" \
  --languages-sha256 "$ts_languages_sha" --module-sha256 "$ts_module_sha" \
  --output /private/tmp/typescript-publication-preview-v1
```

Review the prepared files, exact original-byte backups and `import-receipt.json`. The same command with `--apply` and a different fresh private output directory performs the guarded replacement. Repository verification, site tests/build and deployment remain separate steps.

Immutable evidence, publication metadata, lease names, private output inodes/bytes and every written catalog target are rechecked before the leases are released. A failure restores files that still match this import's replacement bytes and removes its owned success receipt. External changes are preserved and reported as restoration conflicts. Success is printed only after context-exit checks complete.

## Source checks

The focused tests use small retained qualification metadata and synthetic future timing ledgers. They cover failures with missing output fields, exact typed/emitted/source-map ownership, static runtime scope, matched-control exclusion, preserved Mech modes and old null fields, canonical-only selection, new-minimum rejection, output replacement and rollback. They do not open the current catalog or replay runtime closure hashes.

```sh
"$ts_python" -I -S -B tools/qualification/test_typescript_export.py
"$ts_python" -I -S -B tools/qualification/test_import_typescript.py
```
