# Runtime metadata for the linear continuation

[`prolog_linear_metadata.py`](../../../tools/qualification/prolog_linear_metadata.py)
is the additive runtime and publication-metadata reviewer for the 81 new slots
and nine preserved regex samples. It consumes a successful, file-verified
[independent reconciliation](reconciliation.md). It does not execute a runtime,
compile a program, sample performance, edit native evidence or publish a dataset.

The runtime checks retain the original reviewed SWI-Prolog 10.0.2 version,
arm64 architecture, unbounded integers, garbage collection, 8 GiB stack limit,
single compute worker and private native-image closure. Compiler and runtime
metadata are from separately retained probe and preparation processes. They do
not establish a per-sample loaded-image inventory or infer unspecified numeric
garbage-collection settings. QLF is application bytecode, not native application
AOT compilation.

The eighteen unchanged profiles retain their original compiler-bound source
bundles, helper ownership, QLF artifacts and compilation/inspection receipts.
The two replacement reverse-complement profiles use the same qualified source
and QLF. Their separate branch validates the actual closed compile/inspection
lifetimes, exact weak-import warning, inspected QLF target and runtime flags,
the [compiled-work review](../revcomp-linear-v1/compiled-work-review.md), and the
[canonical owner review](../revcomp-linear-v1/source-counts-v1/source-count-review.md)
with its exact projection and evidence pins: 242 canonical units and 146 physical
lines. Formatted counts remain unavailable. Source-linear traversal does not
establish an empirical scaling measurement.

The compiler observer's original warning-bearing `failed` records remain
unchanged. The additive validator requires exit zero, full owned-process cleanup
and exactly the previously reviewed warning bytes. It cannot accept another
warning, an unrelated observer failure or a nonzero compiler exit.

The CLI acquires the continuation durable lease, original durable lease, Prolog
study lease and unchanged common mutex. It rechecks all files bound by the saved
reconciliation, independently replays its complete ledger, and verifies both
native artifact inventories and the continuation durable inventory. Original
identity relocations and lossless compressed storage retain their original
rules. It rechecks the files, inventories and lease identities after metadata
review. All file-mode operations must wait for the native cohort to close.

Publication callers may keep the same four leases through candidate creation
and guarded file replacement using `review_context`. The context repeats its
immutable verified-pin and inventory checks before releasing the leases. If
this final check fails, an optional restoration callback runs while the leases
are still held. An optional final consumer check runs after the evidence
recheck, allowing publication callers to verify supplemental pins and the exact
prepared target bytes under those same leases. Its failure invokes the same
restoration path. Read-only callers install neither callback.

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/prolog_linear_metadata.py --reconciliation /private/tmp/mech-benchmark-completion/experiments/prolog/full81-linear-v1/reconciliation-v1.json --reconciliation-sha256 RECONCILIATION_SHA256 --output /private/tmp/mech-benchmark-completion/experiments/prolog/full81-linear-v1/runtime-metadata-v1.json
```

Use the digest of the actual closed reconciliation. The output must be new and
outside `run-v1`. A successful review qualifies runtime publication metadata;
chart admission remains false until an explicit dataset import and validation.
Failed workload profiles remain excluded. Regex samples preserve their original
matched Mech control and receipt paths; the other nine workloads use the new
cohort's controls. The cancelled original reverse-complement attempt contributes
no admitted timing or timeout result.

The [twenty pure tests](../../../tools/qualification/test_prolog_linear_metadata.py)
combine actual saved metadata with an explicitly synthetic future timing ledger.
They validate profile routing, source aliases, original compiler binding,
warning bytes, process birth/reap/cleanup, QLF identity, canonical ownership and
failure exclusion. They do not perform file-mode closure verification, runtime
hashing or native execution, and they do not establish a completed timing study.
The exit-path tests additionally check that restoration precedes lease release
and that simultaneous closure/restoration errors remain available.
