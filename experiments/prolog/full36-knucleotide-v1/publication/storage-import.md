# Declared-storage publication import

The additive [storage importer](../../../../tools/qualification/import_prolog_knucleotide_storage.py)
publishes evidence references using the exact gzip files declared in the
[storage manifest](../../qualified-original22-v2/storage-manifest.json).
Each converted reference retains its logical path, original SHA-256 and byte
length, alongside the stored path, compressed SHA-256 and manifest reference.
The importer checks identical compressed bytes in both checkouts and verifies
the decoded content's original digest and length. Historical receipts and the
[original importer](../../../../tools/qualification/import_prolog_knucleotide.py)
remain unchanged; raw evidence trees are not inflated in the publication checkout.

The original evidence checkout's taxonomy implementation remains pinned.
The current publication checkout's `site/src/traits.mjs` has its own explicit
digest, checked before publication and during final verification. This preserves
the current classification controls while binding the exact code being served.

Use the existing publication arguments with these changes:

```text
tools/qualification/import_prolog_knucleotide_storage.py
--importer-sha256 <SHA256 of this storage importer>
--traits-sha256 <SHA256 of the publication checkout's site/src/traits.mjs>
```

The retained Python `-I -S -B` invocation, distinct evidence/publication roots,
candidate and catalog digests, and fresh private output remain required as
documented in the [publication procedure](README.md). Application still requires
explicit `--apply`.
Preview and application each retain their own receipts; this correction does
not change qualification, normalization baselines or transaction rollback.

All 22 focused [publication tests](../../../../tools/qualification/test_prolog_knucleotide_storage_publication.py)
passed. They cover the preserved four-cohort rules and transaction faults,
declared gzip references, unchanged logical identities, compressed-copy and
decoded-content mismatches, and unsafe or duplicate storage paths. This note
records the correction and its tests; actual import status requires a successful
application receipt.
