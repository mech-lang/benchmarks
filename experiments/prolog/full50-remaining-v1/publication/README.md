# Prolog publication from three timing cohorts

The publication tools combine independently checked observations from three real
measurement periods. They preserve each sample's producer report, terminal,
attempt number, round, complete-output validation and measurement interval.

| Cohort | Retained or planned samples | Producer evidence |
| --- | ---: | --- |
| `original-full90` | 9 retained regex samples | [Original results](../../full90-v1/results/report.json), status `stopped-unqualified` |
| `linear-full81` | 31 retained continuation samples | [Stopped continuation](../../full81-linear-v1/run-v1/report.json), status `stopped-unqualified` |
| `linear-remaining50` | Up to 50 new samples | [Remaining-slot plan](../plan-v1.json); completion must pass independent reconciliation |

The cancelled original reverse-complement attempt contributes no timing. No
completed sample is rerun. A program's three observations may span the two linear
cohorts; its aggregate public report is the additive reconciliation, and its
individual observations retain their actual producer links. Neither stopped
report is rewritten as a completed run.

This directory contains publication tooling documentation. It does not certify a
completed remaining cohort or admit any data by itself.

## Source, runtime and measurement scope

The twenty Prolog source forms comprise two explicitly identified source aliases
for each of ten workloads. Each alias retains independent timings. The aliases
make no claim of distinct optimization. Canonical source counts include the main
application and every authored helper; formatted source counts are unavailable.

SWI-Prolog 10.0.2 executes the retained QLF bytecode with `-q -O -f none`, an 8 GiB
stack limit and one compute worker. A timing covers the full fresh process:
startup, QLF loading, input, required work, output and shutdown. Source compilation
is outside the timer. Runtime/library and GC observations come from retained
preparation and probe records. They are not per-sample observations, and numeric
GC defaults are not claimed. Regex uses SWI `library(pcre)` and the bundled PCRE2
10.40 with `jit(false)`.

The [metadata reviewer](../../../../tools/qualification/prolog_remaining_metadata.py)
replays the existing runtime and compiler-input checks for the original eighteen
forms and the two qualified linear reverse-complement forms. The
[exporter](../../../../tools/qualification/prolog_remaining_export.py) binds each
observation to the three-cohort reconciliation. The
[importer](../../../../tools/qualification/import_prolog_remaining.py) prepares all
twenty inventory rows and selects eligible fastest/fewest-line endpoints. Failed
forms remain in the inventory without medians or chart coordinates. A failed
matched Mech control excludes its workload from chart admission.

## Reproduction

Run from the repository root, on the retained host and filesystem layout. The
frozen plan is `experiments/prolog/full50-remaining-v1/plan-v1.json`, SHA-256
`fef4341ebee2d6cf8ef2d0fab618abe6be90d24ec180b8d7036f9e8f37fd4195`.
A new host or changed runtime requires a new plan; rewriting retained receipts is
not a reproduction procedure.

All steps below are read-only evidence review or publication preparation. They
launch no benchmarks, compilers or runtime probes. Run them only after the
remaining native cohort and its durable owner have closed. Actual file review
holds five existing locks: the three durable-job leases, the Prolog suite lease
and `/tmp/mech-clbg-timing.lock` (inode `79859134`). Missing, replaced or busy locks
fail closed. Never recreate a missing lock.

Use the retained interpreter with isolation, site imports and bytecode writes
disabled:

```sh
PROLOG_PUBLICATION_PYTHON=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
"$PROLOG_PUBLICATION_PYTHON" -I -S -B tools/qualification/prolog_remaining_reconcile.py \
  --output experiments/prolog/full50-remaining-v1/reconciliation-v1.json
```

The reconciler verifies all three actual reports and complete native artifact
inventories. It preserves the two stopped statuses and excludes original attempt
10. Set `PROLOG_RECONCILIATION_SHA` to the digest printed by this successful
command, then reproduce runtime metadata:

```sh
"$PROLOG_PUBLICATION_PYTHON" -I -S -B tools/qualification/prolog_remaining_metadata.py \
  --reconciliation experiments/prolog/full50-remaining-v1/reconciliation-v1.json \
  --reconciliation-sha256 "$PROLOG_RECONCILIATION_SHA" \
  --output experiments/prolog/full50-remaining-v1/runtime-metadata-v1.json
```

Set `PROLOG_METADATA_SHA` to its printed digest, then export the private candidate:

```sh
"$PROLOG_PUBLICATION_PYTHON" -I -S -B tools/qualification/prolog_remaining_export.py \
  --reconciliation experiments/prolog/full50-remaining-v1/reconciliation-v1.json \
  --reconciliation-sha256 "$PROLOG_RECONCILIATION_SHA" \
  --metadata experiments/prolog/full50-remaining-v1/runtime-metadata-v1.json \
  --metadata-sha256 "$PROLOG_METADATA_SHA" \
  --output experiments/prolog/full50-remaining-v1/publication/candidate-v1.json
```

Set `PROLOG_CANDIDATE_SHA` to its printed digest. Independently record the current
SHA-256 values of `tools/qualification/import_prolog_remaining.py`,
`data/benchmarks.json`, `data/languages.json` and `site/src/languages.mjs` in
`PROLOG_IMPORTER_SHA`, `PROLOG_BENCHMARKS_SHA`, `PROLOG_LANGUAGES_SHA` and
`PROLOG_MODULE_SHA`. The importer requires these exact current inputs:

```sh
"$PROLOG_PUBLICATION_PYTHON" -I -S -B tools/qualification/import_prolog_remaining.py \
  --candidate experiments/prolog/full50-remaining-v1/publication/candidate-v1.json \
  --candidate-sha256 "$PROLOG_CANDIDATE_SHA" \
  --metadata experiments/prolog/full50-remaining-v1/runtime-metadata-v1.json \
  --metadata-sha256 "$PROLOG_METADATA_SHA" \
  --reconciliation experiments/prolog/full50-remaining-v1/reconciliation-v1.json \
  --reconciliation-sha256 "$PROLOG_RECONCILIATION_SHA" \
  --importer-sha256 "$PROLOG_IMPORTER_SHA" \
  --benchmarks-sha256 "$PROLOG_BENCHMARKS_SHA" \
  --languages-sha256 "$PROLOG_LANGUAGES_SHA" \
  --module-sha256 "$PROLOG_MODULE_SHA" \
  --output /private/tmp/mech-prolog-publication-preview-v1
```

The default creates a fresh private three-file preview with exact input backups
and a receipt. Review and validate that result before using `--apply` with a new
private output directory. Existing program records, observations, baselines and
formatted summaries are preserved. A newly discovered minimum requires separate
baseline review. Site build, validation and deployment follow catalog import.

Every output path must be fresh. Saved reconciliation, metadata and candidate
files are reproduced before use. Supplemental publication pins are rechecked
after the independent reconciler's final file pass, while all five locks remain
held. A body or final-check failure restores each still-owned catalog file and
removes the owned success receipt. An unrelated edit is preserved and reported.

## Pure regression checks

```sh
"$PROLOG_PUBLICATION_PYTHON" -I -S -B -m unittest discover \
  -s tools/qualification -p test_prolog_remaining_publication.py
```

The tests use the actual preserved forty observations and an explicitly synthetic
future ledger. They cover mixed-cohort profiles, stopped producer status,
per-sample provenance, failed forms and controls, canonical-only source counts,
unchanged catalog records/baselines, supplementary final-check ordering and
failure restoration. They launch no native subjects and do not hash the complete
runtime closure.
