# Rebol full60 candidate export

[`rebol_export60.py`](../../../tools/qualification/rebol_export60.py) consumes the actual held [independent reconciliation](RECONCILE.md) and separately reviewed runtime publication metadata. It has no catalog apply mode. The original full90 exporter and its evidence remain unchanged.

`build_candidate(reconciler, plan, review, metadata, read_raw)` returns a `rebol-full60-publication-candidate-v1`. Its inventory contains ten canonical compact programs, ten matched Mech controls and ten endpoint proposals. The schedule has sixty slots: thirty subject observations and thirty controls. The sole eligible program may supply both fastest and fewest-lines endpoints; the endpoint's `programs` list contains that key once. Each row has explicit null `source_alias_of` and `timing_alias_of` fields for catalog compatibility, without another program or an alias claim. Native attempt identities and receipt paths must be unique across the entire candidate.

The candidate retains the exact [cohort policy](POLICY.md) reference and single-form subject policy. It includes ten authored bundles and fifteen counted physical files: each main, IO helper, extension loader and whole corrected C source, plus bigint or regex facade where used. Canonical and physical counts retain their separately reviewed meanings; formatted LOC remains null. Identical source bytes may share a content entry with all physical source paths retained.

A failed subject keeps its earlier observations and failure, with no median or replacement endpoint. A successful subject whose matched control failed retains descriptive samples and statistics but has no comparative ratio or endpoint. Missing output fields in failed attempts remain null. The exporter reads every raw, supervisor and outer receipt and preserves their exact references. Full stdout was discarded after validation by the sampler; its retained byte counts, hashes and validation records are the output evidence. Sampled RSS is not an unsampled maximum.

The source approval uses schema `rebol-full60-export-source-review-v1`, status `independent-source-review-complete-actual-export-pending`, independent review, and false native execution and chart admission. Its `files` map contains this document, the exporter and focused tests. Its `dependencies` map contains the full60 reader and `POLICY.md`, with exact repository-relative paths and SHA256 values. The reader is fixed to `30610d445574517d6bfdc34127c7d69c2f5a8e655b5d0660dfe45a6cc7f8e531`.

Runtime metadata keeps the existing `rebol-publication-runtime-metadata-v1` contract. Exact qualification, runtime, extension and evidence references are required. Source/runtime equivalence, per-timed-process image observation, observed GC configuration and numeric GC-default claims remain false. Release-year evidence remains a separate import prerequisite.

`export_context(args, *, final_consumer_check=None, on_exit_failure=None)` retains the reader API for importers. `save_candidate(args)` creates only a fresh private candidate outside timing output, data and site paths. Original evidence leases stay held through supplementary pin checks and exact output inode/byte checks. Failures remove only unchanged owned output; replacement or modified evidence is preserved. INT, TERM and HUP delivery is deferred until exclusive output creation has an ownership record, then unwinds the same checks.

Focused synthetic tests cover the ten-program projection, shared endpoints without duplicate samples, failures, runtime/count/policy gates, all three receipt references and owned-output closure. They perform no actual qualification, reconciliation, export or native execution. Actual evidence and independent source approval are required before invoking the CLI.

```sh
python3.12 -I -S -B tools/qualification/test_rebol_export60.py
```
