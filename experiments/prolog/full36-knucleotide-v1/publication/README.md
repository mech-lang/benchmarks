# Four-cohort Prolog publication

This additive consumer preserves 54 completed observations and consumes the
remaining 36 slots after the corrected knucleotide program is qualified. The
original evidence checkout and all producer records remain unchanged. Source
review and focused tests precede actual reconciliation, metadata review,
export, preview and import; none of those file phases is implied by this packet.

The four observation origins are retained separately:

| Cohort | Preserved or scheduled observations | Original disposition |
| --- | ---: | --- |
| Original full90 | 9 | Stopped; cancelled reverse-complement attempt 10 excluded |
| Linear full81 | 31 | Stopped |
| Linear remaining50 | 14 | Stopped; actual attempt 15 cancelled and excluded |
| Corrected knucleotide remaining36 | Up to 36 | Actual final report required |

All three earlier reports keep their stopped status. The third cohort records
15 actual attempts, including the interrupted attempt; it is never represented
as a completed 50-process run. Only qualified observations enter medians.
Failed source forms retain their partial observations without an admitted
median. Failed matched controls exclude both associated source forms.

[Metadata review](../../../../tools/qualification/prolog_knucleotide_metadata.py)
reuses the frozen original-runtime reviewer for sixteen forms and the linear
reverse-complement reviewer for two forms. The two corrected knucleotide
forms bind the actual independent compiler/count/work receipts, all three
counted inputs, their QLF artifacts and the saved loaded-inputs observations.
Each corrected bundle has 238 canonical units and 154 physical lines. The
identical source forms retain their existing explicit alias identity; they
are not presented as different optimizations. Runtime/GC/library observations
remain preparation evidence, not observations from every measured process.

[Export](../../../../tools/qualification/prolog_knucleotide_export.py) independently
reproduces the saved metadata and reconciliation before constructing the
candidate. Every observation retains its actual report, attempt number, raw
receipt, supervisor receipt and outer-owner receipt. No stopped report is
rewritten, and no completed observation is rerun.

[Import](../../../../tools/qualification/import_prolog_knucleotide.py) executes
from the original evidence checkout and writes only a separate publication
checkout. It preserves all previous catalog rows, measurements, sources,
normalized baselines and formatted summaries. A new minimum rejects the
import and requires a separate normalization review. Direct public source and
evidence links must already have exact-byte copies in the publication checkout;
physical prerequisite maps and historical review files are not recursively
copied. Both roots remain distinct throughout all six original leases.

## Commands

Use the retained Python with `-I -S -B`. The evidence root is
`/private/tmp/mech-benchmark-completion`; the publication root is a separate
clean checkout. Run these steps only after the native stage has closed and
the common timing lane is free. Replace every digest below with the exact
saved artifact digest; there are no successful placeholder receipts.

```sh
PY=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
E=/private/tmp/mech-benchmark-completion
P=/private/tmp/mech-benchmark-publication
Q="$E/experiments/prolog/full36-knucleotide-v1"

"$PY" -I -S -B "$E/tools/qualification/prolog_knucleotide_reconcile.py" --output "$Q/reconciliation-v1.json"
"$PY" -I -S -B "$E/tools/qualification/prolog_knucleotide_metadata.py" --reconciliation "$Q/reconciliation-v1.json" --reconciliation-sha256 RECONCILIATION_SHA --output "$Q/runtime-metadata-v1.json"
"$PY" -I -S -B "$E/tools/qualification/prolog_knucleotide_export.py" --reconciliation "$Q/reconciliation-v1.json" --reconciliation-sha256 RECONCILIATION_SHA --metadata "$Q/runtime-metadata-v1.json" --metadata-sha256 METADATA_SHA --output "$Q/publication/candidate-v1.json"
"$PY" -I -S -B "$E/tools/qualification/import_prolog_knucleotide.py" --evidence-root "$E" --publication-root "$P" --reconciliation "$Q/reconciliation-v1.json" --reconciliation-sha256 RECONCILIATION_SHA --metadata "$Q/runtime-metadata-v1.json" --metadata-sha256 METADATA_SHA --candidate "$Q/publication/candidate-v1.json" --candidate-sha256 CANDIDATE_SHA --importer-sha256 IMPORTER_SHA --benchmarks-sha256 CURRENT_BENCHMARKS_SHA --languages-sha256 CURRENT_LANGUAGES_SHA --module-sha256 CURRENT_MODULE_SHA --output /private/tmp/prolog36-publication-preview-v1
```

Review the exact preview and use the same input digests with `--apply` and a
new private output directory. The importer keeps exact before/after bytes and
an import receipt, rechecks owned outputs and destination files after the final
evidence replay, and rolls back still-owned catalog changes if any check fails.
External edits are preserved and reported as conflicts. Success is announced
only after the held review contexts close successfully. Website validation and
deployment remain separate steps.

The focused [pure tests](../../../../tools/qualification/test_prolog_knucleotide_publication.py)
use synthetic timings in memory, small saved compiler observations and temporary
catalogs. They do not create timing evidence or launch native subjects.
