# Uiua fannkuch v5 retained-study publication

This packet admits the completed Uiua fannkuch v5 study without repeating its expensive measurements. It contains two exact source forms, three full-process observations per form, and three matched Mech AOT control observations. The workload is N=12: 479,001,600 permutations, checksum 3,968,050, maximum 65 flips, with at most eight workers. Uiua timing includes process startup, source compilation, workers, computation, output and shutdown.

| Source | Canonical source units | Samples | Median seconds |
| --- | ---: | ---: | ---: |
| Compact | 20 | 3 | 1668.209 |
| Fast | 21 | 3 | 558.227 |
| Matched Mech AOT control | 59 | 3 | 1.722 |

The source counts are independently reviewed in [source-owner-review.md](source-owner-review.md) and [independent-source-review.json](independent-source-review.json). They enumerate every owner in these two exact files; they do not claim a general Uiua parser. Formatted LOC remains unavailable. Source algorithms, output validation, worker limits and original runner qualification are retained from the completed study and its prior independent reconciliation.

The six Uiua samples and three controls come exclusively from [the completed v5 report](../../../../archive/comparisons/r-apl-uiua-comparison/20261011/uiua-fann-compact-v5/full-study/report.json). Earlier partial fannkuch cohorts supply no measurements. No benchmark, compiler, sampler or measurement producer is executed by the publication tools.

## Evidence and normalization

The consumer joins each original sampler receipt to its exact supervisor-report record. It validates the nine-record schedule, source/runtime identity, full workload, output, completion, process cleanup and original qualification checks. It reuses the frozen archived consumer and binds the prior independent nine-record/1,245-pin reconciliation. The file phase verifies the sealed closure again before admitting data.

The original sealed source-candidate manifest has SHA-256 `41462f55b1c1f6c800d08cca9ba9ba46cb5e3c6efd7f0ff3d21cfde514b70b7c`. Its public archive copy has SHA-256 `9d8972f3254500ad14cbbf56e0378a7a47661edaaeb7afba04b50dcad3cc6534`. The only JSON difference is a documentation sentence in `migration_policy`. Both versions are pinned, and the consumer requires equality of every other field. Original source, command, runtime, work, sample and output fields remain unchanged.

The compact source establishes a new canonical fannkuch minimum of **20**, replacing **31**. To keep the chart in units of × best, admission atomically updates the workload LOC baseline, all derived fannkuch x coordinates in the selected and inventory rows, their publication snapshots, and affected aggregate x coordinates. Existing fannkuch coordinates therefore scale by 31/20. Raw source counts, samples, elapsed times, source text, evidence, time baselines, y coordinates and formatted axes remain unchanged. The preparation receipt lists every before/after coordinate and aggregate change.

The importer adds the two Uiua identities and their endpoint group, updates Uiua workload coverage and displayed source count, and adds its aggregate reference. Existing source records and other language metadata are preserved. The paired Mech observations remain controls; they do not replace current Mech chart samples.

## Reproduction

Run from the repository root on the retained measurement host, after the timing lane is free. The file phase requires the sealed inputs at their original manifest paths; it does not download, rebuild or replace a missing dependency. It acquires the original nonblocking `/tmp/mech-clbg-timing.lock` (inode 79859134) and holds it through final closure. A busy lane fails before any runtime closure replay or output creation.

The following sources are frozen for review:

| File | SHA-256 |
| --- | --- |
| `tools/qualification/uiua_fann_reconcile.py` | `bf08aec948d4db505633e9e3898818f997fdd0738d6126c01fe9c9ac60e341dd` |
| `tools/qualification/uiua_fann_publication.py` | `793d2bce677760cce6b0e2479742aee17e39094950b7486449416a9bc225f8a7` |
| `tools/qualification/import_uiua_fann.py` | `f57246c5ffb5d4c32f9dfb661f5e23c1e210c184aeb9145ea2a79f276b7e0a16` |

Set the common invocation arguments:

```sh
uiua_python=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
uiua_driver=tools/qualification/import_uiua_fann.py
uiua_packet=experiments/uiua/fann-v5-publication-v1
uiua_driver_sha=f57246c5ffb5d4c32f9dfb661f5e23c1e210c184aeb9145ea2a79f276b7e0a16
uiua_reconciler_sha=bf08aec948d4db505633e9e3898818f997fdd0738d6126c01fe9c9ac60e341dd
uiua_publication_sha=793d2bce677760cce6b0e2479742aee17e39094950b7486449416a9bc225f8a7
```

Export an independently reproduced candidate into a fresh directory:

```sh
"$uiua_python" -I -S -B "$uiua_driver" --mode export \
  --tool-sha256 "$uiua_driver_sha" --reconciler-sha256 "$uiua_reconciler_sha" \
  --publication-sha256 "$uiua_publication_sha" --output "$uiua_packet/export-v1"
```

After successful final closure, the directory contains `reconciliation.json`, `candidate.json` and `SUCCESS.json`. Copy `candidate_sha256` from that success receipt into `uiua_candidate_sha`, then prepare the concrete catalog diff:

```sh
"$uiua_python" -I -S -B "$uiua_driver" --mode preview \
  --tool-sha256 "$uiua_driver_sha" --reconciler-sha256 "$uiua_reconciler_sha" \
  --publication-sha256 "$uiua_publication_sha" \
  --candidate "$uiua_packet/export-v1/candidate.json" --candidate-sha256 "$uiua_candidate_sha" \
  --output "$uiua_packet/preview-v1"
```

Preview reproduces the same evidence and candidate, then saves exact `before/` and `after/` versions of both catalog files and their digests. It does not change the catalogs. Review its normalization audit, source/timing preservation, new endpoint selection and concrete data diff before applying.

Apply uses the same arguments with `--mode apply`, a fresh `--output "$uiua_packet/apply-v1"`, and all four exact values from the reviewed preview success receipt:

```text
--expected-catalog-sha256              originals["data/benchmarks.json"]
--expected-languages-sha256            originals["data/languages.json"]
--expected-prepared-catalog-sha256     prepared["data/benchmarks.json"]
--expected-prepared-languages-sha256   prepared["data/languages.json"]
```

Every phase rechecks the immutable original pins and consumer-added evidence before its final consumer check. That check verifies the catalog state and every newly owned output's inode and exact bytes while the common lease is still held. Failure removes unchanged owned success artifacts and restores every still-owned catalog target. External changes are preserved; recovery payloads remain if they prevent restoration. Success is printed only after final closure. The importer does not build the site, deploy, commit or push.

## Source validation

The 11 reconciler tests replay only small saved documents and exercise raw/report equality, complete cohort requirements, source/work rejection, strict JSON, the documentation-only archive distinction, immutable original pins and cleanup under the lease. The seven publication tests exercise the 31→20 rebase, raw-data preservation, changed source/count rejection, partial-write cleanup, external-change preservation and catalog/output mutations during the final pin replay. They use a small retained Uiua catalog shape and temporary synthetic catalog files; they do not load the full catalog or hash the runtime closure.

```sh
"$uiua_python" -I -S -B tools/qualification/test_uiua_fann_reconcile.py
"$uiua_python" -I -S -B tools/qualification/test_uiua_fann_publication.py
```

The independent source review and exact source/test digests are recorded in [publication-source-review-v1.json](publication-source-review-v1.json). These source tests do not constitute chart admission. The exported, previewed and applied receipts record the actual file-phase result when that work is performed.
