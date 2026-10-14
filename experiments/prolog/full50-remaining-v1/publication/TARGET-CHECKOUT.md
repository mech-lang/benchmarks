# Publication into a separate checkout

[The target adapter](../../../../tools/qualification/import_prolog_publication_target.py)
uses the original measurement checkout at
`/private/tmp/mech-benchmark-completion` for every evidence review. The original
importer, exporter, metadata reviewer, reconciler and their physical pins remain
unchanged. Their five existing leases stay held through the final publication
check and any required restoration.

A distinct physical checkout supplies only the three current catalog targets:
`data/benchmarks.json`, `data/languages.json` and `site/src/languages.mjs`.
The adapter passes the original root to the importer's evidence-reference
conversion and the publication root to its existing write/restore helpers.
Neither root can contain the other. Symlinked inputs or targets are rejected.

Before publication, the destination must already contain exact copies of every
local source and receipt link included by the candidate, the pinned release
metadata, the original importer and the adapter. The destination's
`site/src/traits.mjs` must also match the original reviewed traits pin. Both sides
are checked by digest and direct byte equality. An edited receipt or source copy
fails the operation; the adapter provides no editorial hash exception.

The candidate, runtime metadata and reconciliation must be fresh, independently
completed records within the original `experiments/prolog/full50-remaining-v1`
packet. The saved metadata and candidate are reproduced inside the original
review context. Stopped producer statuses, commands, runtime paths, sample
indices and historical receipts retain their original values. A new timing or
source-size minimum still requires separate baseline review.

## Operation

Use the retained Python interpreter with `-I -S -B`, after the native cohort and
its owners have closed and all five existing leases are available. Supply exact
SHA-256 values for the reviewed adapter, three evidence records and three
current destination targets. The output must be a fresh private directory
outside both checkouts, with an existing physical parent directory.

```sh
"$PROLOG_PUBLICATION_PYTHON" -I -S -B \
  /private/tmp/mech-benchmark-completion/tools/qualification/import_prolog_publication_target.py \
  --evidence-root /private/tmp/mech-benchmark-completion \
  --publication-root "$PROLOG_PUBLICATION_ROOT" \
  --candidate "$PROLOG_CANDIDATE" --candidate-sha256 "$PROLOG_CANDIDATE_SHA" \
  --metadata "$PROLOG_METADATA" --metadata-sha256 "$PROLOG_METADATA_SHA" \
  --reconciliation "$PROLOG_RECONCILIATION" --reconciliation-sha256 "$PROLOG_RECONCILIATION_SHA" \
  --adapter-sha256 "$PROLOG_TARGET_ADAPTER_SHA" \
  --benchmarks-sha256 "$PROLOG_BENCHMARKS_SHA" \
  --languages-sha256 "$PROLOG_LANGUAGES_SHA" --module-sha256 "$PROLOG_MODULE_SHA" \
  --output "$PROLOG_PRIVATE_PREVIEW"
```

The default produces a private preview, exact original backups and a receipt;
it does not change the destination catalogs. After reviewing that preview, a
separate invocation with `--apply` and another fresh output directory installs
the prepared bytes. Final checks bind destination files, copied links,
supplemental pins and private output identities while the evidence leases remain
held. A failed final check restores every still-owned catalog and removes owned
private outputs. An unrelated modification is preserved and reported. Success
is returned only after the review context closes successfully.

The receipt records both roots, original importer and adapter identities, all
copied-link pins, and target hashes before and after publication. These records
describe a publication transaction; they do not create new benchmark results.

## Source checks

```sh
"$PROLOG_PUBLICATION_PYTHON" -I -S -B \
  tools/qualification/test_import_prolog_publication_target.py
```

The tests use temporary synthetic records and the original replacement helpers.
They cover root and pin mismatches, source/receipt/traits copy changes, target
mutation, symlinks, missing targets, interruption after apply and restoration
before lease release. They do not replay runtime closures, prepare a real
publication, modify a catalog or execute native programs. Actual evidence replay
and publication remain separate operations.
