# Rebol full90 private export

The additive exporter consumes the exact closed full90 independent
reconciliation. It starts no process and has no catalog apply mode. This source
packet has no actual export; actual timing, publication metadata and source approvals
are required before its file phase can run.

`build_candidate(reconciler, plan, review, metadata, read_raw)` creates a
`rebol-full90-publication-candidate-v1` with twenty inventory forms, ten matched
Mech controls and ten endpoint proposals. Compact and optimized share each
authored bundle but retain separate fresh sample records. There are ten bundles
and fifteen counted physical files: each main, IO, loader and whole corrected C,
plus bigint or regex facade where used. Each row retains file roles and counts;
formatted LOC is null. The source-content map deduplicates identical bytes and
lists exact source-path aliases. It never combines different component hashes.

Only a subject with three qualified samples and a qualified matched control
can propose an endpoint. Failed rows retain their original failure receipt,
any earlier samples and null summary. A successful subject whose control failed
retains its descriptive median but has no comparative ratio or endpoint.
Missing fields in an isolated failed attempt remain null; no complete output
hash or count is invented. Complete stdout was validated and discarded by the
original sampler, so its counts/hashes and validation receipts are the retained
full-output evidence. Sampled RSS is not an unsampled maximum.

The source-review input has schema `rebol-export-source-review-v1`, status
`independent-source-review-complete-actual-export-pending`, independent review,
and false native execution and chart admission. Its `files` map pins this
README, the exporter and focused tests; its sole `dependencies` entry pins the
actual independently reviewed `rebol_reconcile.py`. Both maps use exact
repository-relative paths and SHA256 values. No placeholder review is supplied.

The separate metadata input has schema `rebol-publication-runtime-metadata-v1`,
status `independently-reviewed-runtime-and-publication-metadata`, independent
review and true `runtime_publication_metadata_qualified`. It contains the
reviewed public key `rebol3`, label, family, platform, runtime label, typing,
execution, style, memory, explanatory note and source links. Rebol execution is
interpreted and typing dynamic. Exact `qualification_manifest`,
`qualified_runtime` and `extension_image` equal the actual qualification result.
Its `runtime_evidence_scope` preserves the qualification limitations, and its
nonempty `evidence` map gives exact path/SHA bindings for the reviewed metadata
basis. Runtime-source equivalence, per-timed-process image observations,
observed GC configuration and numeric GC-default claims remain false. This
input cannot promote the bounded layout/load/source association to a runtime
rebuild or per-timed-process observation. Release-year evidence is a separate
publication-import input; this exporter invents no introduction date.

The reader holds the original qualification, full90 suite and durable-job leases
through candidate creation and final checks. Supplementary metadata, source
review and saved reconciliation bytes are checked again before release, as are
the candidate's exact inode and bytes. Any failure removes only the unchanged
owned output; an independently replaced or edited file is preserved. Original
measurement directories and their failed receipts remain untouched.
CLI INT, TERM and HUP unwind these guards. Their delivery is deferred during
exclusive creation, ownership registration and the small candidate write.

After actual evidence and independent approvals exist, use the retained Python:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/rebol_export.py \
  --plan /absolute/full90-plan.json --plan-sha256 ACTUAL_PLAN_SHA256 \
  --durable-directory /absolute/closed-owned-job \
  --reconciliation /absolute/independent-full90-review.json --reconciliation-sha256 ACTUAL_REVIEW_SHA256 \
  --metadata /absolute/reviewed-publication-metadata.json --metadata-sha256 ACTUAL_METADATA_SHA256 \
  --source-review /absolute/export-source-review.json --source-review-sha256 ACTUAL_SOURCE_REVIEW_SHA256 \
  --output /absolute/new-private-candidate.json
```

The 14 pure test methods passed on 2026-10-15 UTC, recorded in
[the initial pure-validation record](../../shared/pure-validation-20261015/post-prolog-pure-validation-run-v1/report.json). They use synthetic plans,
receipts and temporary files and do not constitute actual native, qualification,
runtime or publication evidence. The actual export remains pending.
