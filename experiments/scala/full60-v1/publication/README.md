# Scala publication from a closed full60 cohort

This packet prepares publication tooling for ten retained Scala implementations, one per workload. It contains no completed full60 measurements, publication candidate or dataset admission. The existing work and canonical source-count decisions are reused; the full-size measurements must finish and pass independent reconciliation before these tools can produce a candidate.

The [exporter](../../../../tools/qualification/scala_export.py) reproduces the [independent reconciliation](../reconciliation/README.md) while the completed durable job, Scala cohort and common timing leases remain held. It binds the exact source and compiled copy, class artifacts, canonical source projection, runtime jars, JVM flags, compiler version and retained JDK release. The [runtime metadata](../runtime-metadata-v1.json) distinguishes HotSpot execution mode from individual methods that may remain interpreted, and records the scope of retained toolchain evidence. It claims no diagnostic probe inside timed processes or numeric garbage-collector defaults.

Each candidate implementation retains its actual three observations, receipt references, sample standard deviation, matched-control observations and failure evidence. A failed subject has no median. A failed control leaves the subject's completed observations intact but excludes its chart endpoint. There are ten real source records, with no compact/optimized aliases. Canonical LOC counts the authored application; formatted LOC remains unavailable. Matched Mech controls remain comparison evidence and do not replace any existing Mech result.

The [importer](../../../../tools/qualification/import_scala.py) accepts only an explicitly pinned candidate that it independently reproduces from the closed evidence. It prepares all ten inventory records and selects the eligible implementation as both the fastest and smallest endpoint for its workload. It appends canonical reference aggregates over the explicitly listed admitted workloads and adds no formatted aggregate. Existing program records, historical measurements, sources, language records and reference summaries are preserved. Existing benchmark baselines are fixed: a new minimum causes the import to stop for a separately reviewed baseline update.

[Release metadata](../release-metadata-v1.json) uses the first public Scala release, January 20, 2004, for the language-history controls. Runtime and language classification metadata are added consistently to the dataset, language catalog and site taxonomy module.

The importer runs from the original measurement checkout and requires an explicit
`--publication-root` naming a separate physical checkout. Its `ROOT`, exporter,
reconciler, original runtime pins and three evidence leases remain unchanged.
Only `data/benchmarks.json`, `data/languages.json` and `site/src/languages.mjs` in
the publication checkout are eligible for replacement. The three caller-supplied
catalog digests describe those destination files. Existing catalog metadata is
preserved from their current bytes.

Before preview or apply, copy the exact authored sources and directly linked
receipts, projections, metadata and publication tools to the same relative paths
in the publication checkout. The importer checks every converted local link
against the original bytes before writing and again during final held closure.
It does not traverse referenced documents to copy their physical pin maps or
relocate runtime files, commands or original evidence paths. A missing or edited
linked copy stops publication. Source proof pins remain checked only in the
original evidence checkout. The preview directory must be fresh and outside
both checkouts; its receipt records both roots and the copied-link digests.

## Closed-evidence procedure

1. Complete the reviewed 60-slot cohort and independently reconcile its actual plan, report, terminal and durable receipts. Retain any workload failures; do not repeat completed observations.
2. Run `tools/qualification/scala_export.py` with the actual `--plan`, `--plan-sha256`, `--durable-directory`, `--reconciliation`, `--reconciliation-sha256` and a fresh `--output` candidate path outside the original timing directory and publication inputs.
3. Review the candidate and run `tools/qualification/import_scala.py` with those actual references plus `--candidate`, `--candidate-sha256`, the reviewed `--importer-sha256`, an explicit `--publication-root`, and exact current `--benchmarks-sha256`, `--languages-sha256` and `--module-sha256` values. Choose a fresh private `--output` directory outside both checkouts. The default produces a preview and exact original-byte backups.
4. Review the preview and preservation receipt. The same importer with `--apply` performs the guarded three-file replacement. Recheck the catalog, site build and published assets separately.

Use the retained Python interpreter with `-I -S -B`. These file phases hash the retained closure and take the common timing mutex nonblockingly; schedule them only while the timing lane is free. Neither tool launches a compiler, runtime, benchmark or measurement producer.

Publication-only metadata, source hashes, lease identities and catalog bytes are checked again after the independent physical closure, before any lease is released. A failure restores every catalog file that still matches this import's replacement bytes and removes only its owned success receipt. Independently changed files are preserved and identified as restoration errors. Partial temporary writes are removed only when their inode and contents still belong to the invocation. Success is printed only after all context-exit checks pass.

The [export tests](../../../../tools/qualification/test_scala_export.py) and [import tests](../../../../tools/qualification/test_import_scala.py) use synthetic timing ledgers and small retained source metadata. They check failed subjects and controls, exact single-source counts, runtime identity, unchanged existing Mech execution modes and historical records, fixed baselines, endpoint selection and guarded rollback. These tests establish source behavior, not completion of the future native timing cohort.
