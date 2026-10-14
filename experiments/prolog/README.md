# Prolog qualification evidence

`qualified-original22-v2/outcome.json` records the completed metadata seal of
22 original authored sources, 44 compiler-copy reconciliations, and 20 work/LOC
profiles. Its original JSON content hashes remain authoritative. The seal ran
zero native commands and zero benchmark executions; full timing and chart
admission are separate gates. `qualified-original22-v1` retains the actual
earlier failed metadata attempt.

JSON artifacts larger than 1 MiB are stored as deterministic gzip: compression
level 9, zero modification time, and an empty original filename. The v2
`storage-manifest.json` maps each logical JSON path to its stored path and records
both original-content and stored-byte SHA-256 hashes and lengths. Decompression
was compared byte for byte with each original. Neither the historical receipts
nor the migration TSV were rewritten. `tools/qualification/prolog_storage.py`
decompresses only artifacts explicitly declared by this manifest; ordinary
runtime `.tar.gz` files keep their original byte-hash meaning.

`prolog_seal.py` performs the retained source/AST/WAM, owner span, compiler-copy,
work-witness, receipt-owner, and dependency checks. Editorial substitutions are
limited to the explicit entries in `editorial-substitutions.json`; source,
runtime, original replay, raw native receipts, and observed timings retain
their original bytes and hashes.

The full timing controller consumes this exact v2 seal and the retained bounded
preparation. It requires a separate immutable execution plan, preserves the
qualified native commands and runtime environment, and uses the existing
common timing lock and frozen sampler. It neither rebuilds Prolog QLF files
nor converts bounded checks into timing samples.
