# Kotlin full-workload reconciliation

`tools/qualification/kotlin_reconcile.py` independently checks the retained
`full90-v2/plan-v1.json` cohort: twenty Kotlin forms and ten unchanged matched
Mech controls, with three serial observations per form. Compact and optimized
are separately measured retained aliases; their names imply no optimization.

The pure ledger checks the exact durable Python command, process identity and
parent, every rotated slot, raw sampler receipt, supervised receipt and outer
process monitor. It independently recomputes medians, sample standard
deviations and matched-control ratios. A failed full workload retains its
actual attempt and any earlier valid observations, skips only its remaining
slots, and receives neither a partial median nor a ratio. A failed control
prevents ratios for its workload. Timing includes direct JVM startup, class
loading, tiered JIT, input, output and shutdown. No phases are subtracted.

The file phase requires the durable, Kotlin cohort and common timing leases.
It verifies all prepared pins, all closed measurement artifacts, all eight
prerequisite artifact inventories and every retained application classpath.
The failed original diagnostic producers remain unchanged; the separate
required-work qualification binds their usable captures and final continuation.
Only canonical source counts are qualified. Formatted counts remain null and
unqualified.

All leases stay held across a consumer's publication operation and a final
pin/inventory check, including when that operation raises. An optional
`on_exit_failure` callback permits guarded restoration before lease release.
The callback does not replace the consumer's own rollback for body failures.
Neither the reconciler nor its CLI imports a producer, launches a runtime,
changes a dataset, or grants chart admission.
The CLI announces success only after the final check. A failed check removes
its newly created receipt while leases remain held; an independently replaced
or altered output is preserved and reported as a restoration failure.

After the full90 durable job closes, run the file phase once into a new path:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/kotlin_reconcile.py \
  --plan experiments/kotlin/full90-v2/plan-v1.json \
  --plan-sha256 fa50e8f327ac960623be79f99730aa94ba1c8588c9008854830a3b74495550f5 \
  --durable-directory experiments/shared/owned-jobs-v1/owned-jobs/kotlin-full90-v2 \
  --output experiments/kotlin/full90-v2/independent-reconciliation-v1.json
```

The original sampler retains complete-output byte counts and hashes plus its
validation receipt, not full stdout files. Its memory evidence is sampled
process-group RSS, not an unsampled maximum. The reconciliation makes those
limits explicit. Runtime metadata and publication are separate review gates;
matched controls never replace existing Mech dataset rows or fixed baselines.

`test_kotlin_reconcile.py` uses synthetic clocks, processes, outputs and failures
joined to the exact prepared source/class metadata. It exercises successful and
failed cohorts, malformed ownership, altered command policy, unsupported
formatted counts, class and authored-role pins, overlapping intervals,
incomplete output, wrong statistics, and final closure/restoration ordering.
It neither reads a live timing report nor hashes runtime closures.
