# Retained admissions in a separate publication checkout

[The target adapter](../../../tools/qualification/import_retained_publication_target.py)
publishes the five retained cohorts through the existing reviewed transforms:

| Cohort | Export entrypoint in `tools/qualification/` | Saved observations |
| --- | --- | ---: |
| Uiua fann | `import_uiua_fann.py --mode export` | 9 |
| R | `r_retained_export.py` | 27 |
| Uiua nbody/trees | `export_uiua_retained.py` | 15 |
| GNU APL | `apl_retained_export.py` | 42 |
| Lua pidigits | `lua_pidigits_export.py` | 18 |

These 111 observations are existing subject and matched-control measurements.
The adapter neither runs benchmarks nor substitutes newly measured controls.
All exporters and evidence reviewers continue to run from the original physical
checkout, `/private/tmp/mech-benchmark-completion`, under their original pins and
leases. Export outputs are fresh directories inside their original cohort
packets. Lua also requires its exact qualified five-file source-count receipt.
The separate APL runtime review remains mandatory; the earlier candidate's
runtime-publication flag is preserved as recorded.

## Checkout boundary

The publication root must be a distinct physical checkout, disjoint from the
evidence root. The original driver and consumer modules are loaded by their
actual original paths and exact source digests. Their `ROOT` values and physical
runtime/source evidence are unchanged.

Only the clean checkout supplies the current `data/benchmarks.json`,
`data/languages.json` and optional `data/normalization-history.json`. Publication
uses the supplied current catalog metadata. It does not copy an older catalog's
release descriptions or classifications into those files.

The destination must already contain exact copies of the exported candidate and
its direct source, report, reconciliation, count, review and tool links. The
adapter compares each required copy against its original digest and bytes; it
does not follow physical proof-pin maps or provide editorial digest exceptions.
Symlinks and nonregular inputs, including FIFOs, are rejected before opening.
Current transaction files and earlier successful publication history are a
different category: they belong to the publication checkout and are verified
there. They do not need counterpart files in the measurement checkout.

The common timing mutex must be free before any physical evidence replay. The
original per-cohort review context keeps its leases through copied-link checks,
the catalog transaction, final history replay and any required restoration.
The adapter leaves every frozen helper unchanged.

## Preview and apply

Use Python with `-I -S -B` and assertions enabled. Supply the original candidate
path and SHA-256, the reviewed adapter SHA-256, and both physical checkout paths.
Each preview requires a distinct future apply directory. Both directories must
be fresh children of the corresponding cohort packet in the publication root,
with existing physical parent directories.

```sh
"$RETAINED_PUBLICATION_PYTHON" -I -S -B \
  /private/tmp/mech-benchmark-completion/tools/qualification/import_retained_publication_target.py \
  --evidence-root /private/tmp/mech-benchmark-completion \
  --publication-root "$RETAINED_PUBLICATION_ROOT" \
  --cohort "$RETAINED_COHORT" --mode preview \
  --candidate "$RETAINED_CANDIDATE" --candidate-sha256 "$RETAINED_CANDIDATE_SHA" \
  --adapter-sha256 "$RETAINED_TARGET_ADAPTER_SHA" \
  --output "$RETAINED_PREVIEW" --apply-output "$RETAINED_APPLY"
```

Review the preview before applying it. Apply uses the same arguments with
`--mode apply`, `--output` set to the proposed apply directory and no
`--apply-output`. It additionally requires all six exact preview digests:
`--expected-catalog-sha256`, `--expected-languages-sha256`,
`--expected-history-sha256`, `--expected-prepared-catalog-sha256`,
`--expected-prepared-languages-sha256` and
`--expected-prepared-history-sha256`. The original history value can be `absent`.
Any intervening change requires a new preview.

Each successful apply retains exact before/after snapshots and a `SUCCESS.json`
inside the clean packet. The history registry pins that receipt, and the receipt
binds the previous registry digest without creating a circular hash. Later
admissions replay the existing target-local history before extending it.

Use the order Uiua fann, R, Uiua nbody/trees, APL, Lua. The unchanged Uiua-fann
transform requires no prior Uiua aggregate and a fannkuch canonical baseline of
31; the subsequent Uiua admission expands that aggregate. Existing endpoints,
unexpected minima or already registered admissions fail closed. The previously
reviewed R/Uiua LOC changes keep their explicit normalization history; Lua
requires its nine-to-ten workload expansion without a new minimum.

A final-check failure restores every still-owned target through the existing
inode journal and removes owned success files before leases close. External
modifications are preserved and reported; recovery snapshots remain available
when a restoration conflict occurs. Success is returned only after the original
review context exits successfully.

## Source validation scope

```sh
"$RETAINED_PUBLICATION_PYTHON" -I -S -B \
  tools/qualification/test_import_retained_publication_target.py
```

The tests use synthetic records, temporary directories and the frozen journal
and owned-file writer. They cover original consumer pin drift, target copy
mismatches, all six apply digests, target-only prior history, late receipt/history
changes, absent-registry restoration and interruption after apply. They do not
replay the actual runtime closure, read current catalogs, create native samples
or certify a completed publication.
