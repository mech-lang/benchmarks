# Retained measurement publication

This packet documents publication of completed measurements that are absent
from the chart. The original source, timing samples, validation results,
failed attempts and environmental exclusions remain intact. No benchmark is
rerun by these tools.

The guarded importer, pure catalog transform and normalization-history
validator have passed source review and small regression tests. The physical
evidence replay, concrete catalog preview and catalog apply described below
have **not** been performed for this packet. A source-review receipt is not a
successful publication receipt.

## Admission order and scope

Run each export, preview, review and apply to completion before preparing the
next catalog preview:

| Order | Cohort | Completed workloads added | Subject observations | Paired controls |
|---|---|---|---:|---:|
| 1 | `uiua-fann` | Fannkuch-redux, compact v5 and fast | 6 | 3 |
| 2 | `r` | N-body, binary trees, fannkuch-redux | 18 | 9 |
| 3 | `uiua` | N-body and binary trees | 9 | 6 |
| 4 | `apl` | N-body, Mandelbrot, k-nucleotide, fannkuch-redux, fasta | 27 | 15 |

These admissions reuse **93 distinct completed observations**. Uiua's tree
alias and APL's two source aliases add no native observations. Uiua attempt
70 remains an environmental exclusion, with replacement 74 preserved. APL
failures 58 and 75 remain excluded; recovered observation 84 keeps its actual
recovery receipt. APL's original report remains partial, and binary trees are
not admitted.

Uiua fannkuch first establishes the 20-unit canonical minimum and an
eight-workload Uiua aggregate. R then lowers the n-body minimum from 20 to 19
and the binary-trees minimum from 16 to 15. The final Uiua admission expands
its aggregate from eight to ten workloads. APL expands from four to nine
workloads. Every necessary x-best rebase is recorded; timing baselines and raw
measurements are unchanged. Formatted LOC remains unavailable for these new
rows.

## Prerequisites

Run from the benchmark repository root using the retained Python interpreter:

```sh
retained_python=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
retained_driver_sha=f8897e023c2f9b816d488cab2136a5e50a15783361924c706804666ca3bef372
retained_history_sha=614f3ee1a736b6f990ee79d678ef767ff38e48724881009f27d2874115c10fb5
```

The original native evidence paths and pinned runtime files must still exist.
Each exporter and importer acquires the original common timing mutex
`/tmp/mech-clbg-timing.lock` (inode `79859134`), plus any cohort-specific owner
leases, without waiting. Do not replace the lock file or run this physical
file replay while another benchmark owns the lane. A busy lease causes a
failure before publication; it does not authorize concurrent execution.

Every output directory must be fresh and remain inside its cohort packet.
The tool never overwrites an earlier receipt. Existing candidate/export tools
are frozen; the new driver reuses their exact candidate representation.

## Export candidates

The following commands reproduce the saved native evidence and write a fresh
candidate plus its independent reconciliation. They change no catalog.

```sh
"$retained_python" -I -S -B tools/qualification/import_uiua_fann.py \
  --mode export \
  --tool-sha256 f57246c5ffb5d4c32f9dfb661f5e23c1e210c184aeb9145ea2a79f276b7e0a16 \
  --reconciler-sha256 bf08aec948d4db505633e9e3898818f997fdd0738d6126c01fe9c9ac60e341dd \
  --publication-sha256 793d2bce677760cce6b0e2479742aee17e39094950b7486449416a9bc225f8a7 \
  --output experiments/uiua/fann-v5-publication-v1/publication/export-v1

"$retained_python" -I -S -B tools/qualification/r_retained_export.py \
  --tool-sha256 3ba5c93901ad1911d0c9446bbc61a29a58e8f7b7f62d6bc91c1448fffff8996a \
  --output experiments/r/retained-native-v1/publication/export-v1

"$retained_python" -I -S -B tools/qualification/export_uiua_retained.py \
  --tool-sha256 dd2298c2ce98613f3e6aa2b9cfa942647d5af9fb976eaf0a600693eac0a7cfa6 \
  --output experiments/uiua/retained-native-v1/publication/export-v1

"$retained_python" -I -S -B tools/qualification/apl_retained_export.py \
  --tool-sha256 24802484ccaa005d8d638b6d96ed028888c62c2f56ae375fdaed7be504899179 \
  --output experiments/apl/retained-native-v1/publication/export-v1
```

## Preview an admission

Choose the matching cohort and packet from the table. The example begins
with the first admission:

```sh
retained_cohort=uiua-fann
retained_packet=experiments/uiua/fann-v5-publication-v1
```

| Cohort | Packet |
|---|---|
| `uiua-fann` | `experiments/uiua/fann-v5-publication-v1` |
| `r` | `experiments/r/retained-native-v1` |
| `uiua` | `experiments/uiua/retained-native-v1` |
| `apl` | `experiments/apl/retained-native-v1` |

Set `retained_candidate_sha` to the `candidate_sha256` printed by that
successful export. The future apply path is part of the prepared history
digest and must be selected during preview.

```sh
"$retained_python" -I -S -B tools/qualification/import_retained_catalog.py \
  --cohort "$retained_cohort" --mode preview \
  --tool-sha256 "$retained_driver_sha" \
  --normalization-sha256 "$retained_history_sha" \
  --candidate "$retained_packet/publication/export-v1/candidate.json" \
  --candidate-sha256 "$retained_candidate_sha" \
  --output "$retained_packet/publication/preview-v1" \
  --apply-output "$retained_packet/publication/apply-v1"
```

The preview contains before/after copies of both catalogs and the proposed
normalization registry. An initially absent registry is represented by
`before/data/normalization-history.json.absent`; its original digest is the
literal string `absent`. The preview's own `SUCCESS.json` has status
`preview-ready`. Its `proposed_apply` is a path and expected digest, not a
fabricated successful-apply receipt.

Review the actual before/after rows, selected endpoints, normalization audit
and six digests printed in the preview. Existing source and timing fields
must remain equal; only the qualified additions and explicitly recorded
derived coordinates may change. The generic transition validator independently
replays the LOC changes before a preview can succeed.

## Apply reviewed bytes

Copy these six values from the reviewed preview's `SUCCESS.json`:

| Shell variable | Preview field |
|---|---|
| `retained_original_catalog_sha` | `originals["data/benchmarks.json"]` |
| `retained_original_languages_sha` | `originals["data/languages.json"]` |
| `retained_original_history_sha` | `originals["data/normalization-history.json"]` |
| `retained_prepared_catalog_sha` | `prepared["data/benchmarks.json"]` |
| `retained_prepared_languages_sha` | `prepared["data/languages.json"]` |
| `retained_prepared_history_sha` | `prepared["data/normalization-history.json"]` |

```sh
"$retained_python" -I -S -B tools/qualification/import_retained_catalog.py \
  --cohort "$retained_cohort" --mode apply \
  --tool-sha256 "$retained_driver_sha" \
  --normalization-sha256 "$retained_history_sha" \
  --candidate "$retained_packet/publication/export-v1/candidate.json" \
  --candidate-sha256 "$retained_candidate_sha" \
  --output "$retained_packet/publication/apply-v1" \
  --expected-catalog-sha256 "$retained_original_catalog_sha" \
  --expected-languages-sha256 "$retained_original_languages_sha" \
  --expected-history-sha256 "$retained_original_history_sha" \
  --expected-prepared-catalog-sha256 "$retained_prepared_catalog_sha" \
  --expected-prepared-languages-sha256 "$retained_prepared_languages_sha" \
  --expected-prepared-history-sha256 "$retained_prepared_history_sha"
```

Apply independently reproduces the candidate again. Any changed original,
candidate, preparation result or future receipt path rejects the operation.
The two catalogs and registry form one rollback journal. A registry entry
binds the exact successful receipt bytes; the receipt binds the prior registry
digest and both before/after catalog digests. It deliberately excludes the
new registry digest to avoid a circular hash.

Before releasing the evidence leases, the driver repeats the evidence pins,
validates the installed history, and verifies exact catalog and owned-output
bytes and inodes. On failure it restores every still-owned catalog target,
removes an unchanged owned success receipt, and preserves external edits.
Recovery snapshots are retained if an external conflict prevents restoration.
Success is printed only after the held context has closed.

## GNU APL runtime scope

APL additionally requires
[`runtime-publication-scope-review-v1.json`](../../apl/retained-native-v1/runtime-publication-scope-review-v1.json)
at SHA-256
`76a28e0e75497ebc181c95cbaa3a529b69fe8b2cbac3ae04ed011468565a41d6`.
The driver checks its eleven source/runtime/command/environment bindings and
required inherited pins inside the same held physical-evidence context.
The later approval is cited in the publication audit. The frozen candidate's
original `runtime_publication_metadata_qualified: false` fields are preserved.

This approval covers recorded interpreter identity, launcher, declared static
dependencies, configuration and serial numerical primitive policy. It does
not claim a per-process loaded-image inventory, complete transitive operating
system dependency inventory or complete inherited environment.

## Source review and regression checks

The driver fixes the shared transform at
`e8a14b971bd07b041c1a08e7a46821a70bd068c5a931ac33a9f98227626c836f`
and the original output-ownership helper at
`f57246c5ffb5d4c32f9dfb661f5e23c1e210c184aeb9145ea2a79f276b7e0a16`.
Cohort exporter/reconciler digests are explicit in the driver's registry.
The public review receipts bind the exact reviewed source and test bytes.

```sh
"$retained_python" -I -S -B tools/qualification/test_import_retained_catalog.py
"$retained_python" -I -S -B tools/qualification/test_retained_catalog_publication.py
"$retained_python" -I -S -B tools/test_normalization_history.py
```

These checks use saved small metadata, pure transforms and temporary catalogs.
They do not acquire the real timing lane, hash the full native closure, run a
benchmark or modify the repository's datasets. After real apply, repository
validation, chart build, asset checks and deployment remain separate steps.
