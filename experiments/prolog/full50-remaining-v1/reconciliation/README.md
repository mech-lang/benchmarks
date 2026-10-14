# Three-cohort Prolog reconciliation

`tools/qualification/prolog_remaining_reconcile.py` independently joins the
remaining fifty schedule slots with forty preserved observations. It imports
only the frozen independent receipt validators; no measurement producer,
sampler, runtime or compiler is imported or executed.

| Cohort | Retained observations | Producer outcome |
| --- | ---: | --- |
| Original full90 | 9 regex observations | Stopped; original attempt 10 excluded |
| Linear full81 continuation | 31 observations | Stopped after a completed sample; no interrupted native attempt |
| Remaining50 continuation | Up to 50 qualified observations | Must close with complete slot accounting |

The original reports keep their actual `stopped-unqualified` statuses. Every
observation retains its own cohort, report, attempt index and three receipt
paths. The Mandelbrot profiles span the latter two cohorts; their provenance
is preserved per sample, including the matched control. No synthetic completed
81-run report is created. The original excluded attempt remains outside every
median and qualified-sample count.

The pure review reproduces both retained boundaries and all raw, supervised
and outer ownership receipts. It checks exact source/runtime metadata,
remaining-slot rotation, elapsed-interval ordering, full-output evidence,
resource limits and process cleanup. It independently computes three-sample
medians, sample standard deviations and matched-control ratios. An isolated
new workload failure preserves earlier observations without a partial median,
and only its later scheduled slots may be skipped.

The file phase requires five existing leases: the new durable job, both older
durable jobs, the Prolog cohort and the common timing mutex. It verifies all
pinned prerequisite bytes, all three native output inventories and the three
durable inventories. Leases remain held through an optional publication
consumer, a final pin/inventory check and any required guarded restoration.
The CLI creates a new review outside the native run directory and announces
success only after that final check passes.

After the remaining50 job closes, run:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/prolog_remaining_reconcile.py \
  --output experiments/prolog/full50-remaining-v1/independent-reconciliation-v1.json
```

The reconciler is bound to plan SHA-256
`fef4341ebee2d6cf8ef2d0fab618abe6be90d24ec180b8d7036f9e8f37fd4195`
and the `linear-remaining50-v1` durable job. It grants neither runtime-publication
approval nor chart admission. Publication uses a separate adapter that retains
all three real cohort references, canonical source counts and equivalent-source
alias labels. Existing Mech timings and fixed chart baselines are unaffected.

Complete stdout is represented by the frozen sampler's byte count, digest and
full-output validation receipt; full stdout files are not retained. Memory
observations are sampled process-group RSS. Original diagnostic logs that were
not prepared-plan inputs are retained as review-time file bindings, without
promoting them to evidence of a different historical timing boundary.

The tests replay the actual preserved forty observations and use synthetic
future fifty-slot receipts for success, failures, mixed-cohort controls,
reordering, changed source/runtime metadata, ownership faults, output errors,
invalid statistics and closure/restoration faults. Tests do not launch native
programs, hash runtime closures, or manufacture a successful future run receipt.
