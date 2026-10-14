# Retained R, Uiua and APL coverage

Eleven workloads missing from the published chart already have complete sets of three saved samples per distinct source, with three matched Mech control samples per workload. The retained reports contain **60 subject observations and 33 control observations** for these workloads. Publication can use those observations after their existing evidence and source counts are reconciled; no replacement performance runs are required to fill these eleven gaps.

This packet inventories saved report contents. It does not independently replay native receipts, rehash runtime closures, approve source counts, or change the catalog. [report-inventory.json](report-inventory.json) records exact source identities, report paths, sample values, attempt numbers, aliases, available receipt paths and the scope of this inspection. Hashes in that file are values recorded by the existing evidence, not fresh file verification.

| Language | Missing workload | Distinct timed sources | Subject observations | Control observations |
| --- | --- | ---: | ---: | ---: |
| R | n-body | 2 | 6 | 3 |
| R | binary trees | 2 | 6 | 3 |
| R | fannkuch-redux | 2 | 6 | 3 |
| Uiua | n-body | 2 | 6 | 3 |
| Uiua | binary trees | 1 | 3 | 3 |
| Uiua | fannkuch-redux v5 | 2 | 6 | 3 |
| APL | n-body | 1 | 3 | 3 |
| APL | Mandelbrot | 3 | 9 | 3 |
| APL | k-nucleotide | 2 | 6 | 3 |
| APL | fannkuch-redux | 1 | 3 | 3 |
| APL | FASTA | 2 | 6 | 3 |

Uiua binary trees and APL n-body/fannkuch have an additional optimized endpoint that aliases the same source and timings. Those aliases contribute no extra native observations. All three completed APL Mandelbrot sources remain available; choosing endpoints must preserve the other source records.

APL binary trees is a separate, twelfth gap: attempt 75 returned `WS FULL`, produced no expected output and failed validation. Its zero exit status does not make it a valid timing. The alias also has no valid observations, and its control remains unmeasured. This packet does not authorize a replacement run.

## Why the chart is behind

The current `data/benchmarks.json` embeds the earlier `r_apl_uiua_audit` report snapshots: R `ff800831…`, Uiua `004c830d…`, and APL `9ef8f377…`. That snapshot has only two tree samples per R/Uiua source and no n-body/fannkuch samples for them; none of the five completed APL workloads above is admitted there.

The later `archive/comparisons/r-apl-uiua-comparison/20261011/results/summary.json` is also insufficient as a publication input. Its 2026-10-12 13:44 UTC snapshot predates completion of R fannkuch and the APL recovery, and it describes the older, partial Uiua fannkuch v2 cohort. The archived importer `archive/site/explorer/r_apl_uiua_data.py` reads that fixed summary. Replacing a path in that importer would bypass the distinctions between cohorts, source counts and recovery evidence.

The next publication step should be an additive consumer of the exact retained reports. Existing reports, historical paths, source audits and raw published measurements remain unchanged. When a newly qualified source establishes a lower minimum, current chart coordinates must be recomputed against that minimum to preserve the interface's x-best meaning; the previous baseline and exact derived changes remain in an audit.

## Exact retained reports and reusable evidence

Paths below are relative to the repository. `COHORT` means `archive/comparisons/r-apl-uiua-comparison/20261011`.

**R:** `COHORT/results/timings-r.json` is complete, with 93 recorded attempts and an update at 2026-10-12 14:57 UTC. The six source rows above hold all 18 subject samples and nine controls. Their source audit is `COHORT/source-audit-r.json`, recorded digest `d76be20504617addb9efd5915bf7074877e727e3a49ccbd36585b4be5c763af3`. The report retains guard migrations and exclusions; those must remain part of admission replay. Tree rows already bind `COHORT/results/r/semantics-fixtures.tsv`, with 63 distinct node addresses at depth five, including leaves. There is no need to repeat that native fixture merely to repair publication.

**Uiua n-body and trees:** `COHORT/results/timings-uiua.json` remains a partial suite report, but these individual workloads have complete samples and controls. Tree allocation and long-lived-root work already have a pinned-runtime source proof in `COHORT/results/uiua/source-audit.json`, section `binarytrees`. N-body v3 has its own source audit at `COHORT/uiua-nbody-v3/results/source-audit.json`, recorded digest `248f99a5bae5446e904d53a85bafd91fb9a80005df40420234856187ab27c4e9`. Attempt 70 was discarded for compiler contention; its completed replacement is attempt 74. The inventory uses attempts 66, 71 and 74 for the compact source.

**Uiua fannkuch v5:** `COHORT/uiua-fann-compact-v5/full-study/report.json` is complete, with six subject and three control observations. Its report digest is recorded as `f5ab40f30c8add188c4e7a0ac87dc7fd18475ff28c5bba8838dc08b10ff71a6c`; the full-study manifest digest is `d8b6ad100671b3fef5ae46d90dcb36b044733b25ea8d65e3ba7a4589e5b62513`. Existing independent reconciliation is already **passed** in `COHORT/evidence/new-results-review-20261012/independent-study-reconciliation.json`, section `fann`: nine records, 1,245 input pins, and a successful dry import. That receipt did not admit data or write the chart. Its existing 27-case importer fixture proof is also referenced there. The endpoint revision at `COHORT/uiua-fann-compact-v5/controller_rev2/revision/uiua-fann-v5-endpoint-revision.json` permits a separate v5 overlay while preserving prior rows. The v2 partial observations must never be mixed with v5 or used to invent one combined attempt order.

**APL:** `archive/qualification/shared/records/apl-sample84-recovery-v1/full-owner/timings-apl.json` contains the latest 87-attempt report. Its recorded digest is `d8281e04af0cfb460364af540d7cb158074df8dad6238c78cc8d8cd971257bda`. The report remains partial because trees failed; the recovery owner's `status.json` is complete. The source-audit binding is `COHORT/uiua-fann-compact-v5/controller_rev2/apl-argv-v1/full-owner/source-audit-apl-argv.json`, digest `b00de5ce41c3a6322f4ab9a3e194775723c8889d3143573d93a21ced75e22e6b`.

APL fannkuch samples 82, 84 and 87 took approximately 7,919, 7,797 and 7,814 seconds. Sample 84 was recovered from the original kernel-observed exit, not rerun. Preserve `recovery-admission.json`, `recovered-084.supervisor.json`, `original-snapshot/observer-terminal.json`, the original raw receipt and new attempts 85–87. The existing readiness observation and source review under `archive/qualification/site/records/apl-current-publication-v1/` explicitly leave independent native-receipt replay and numeric canonical count approval open.

APL FASTA attempt 58 produced zero output and remains failed. The corrected argv cohort supplies valid optimized samples 59, 60 and 63. Preserve its command revision and both the failed and successful records.

## Remaining admission work

1. **Bind canonical counts to the twenty exact source identities.** Reuse the existing R normalizer in `archive/validation/loc-normalization/20261012/normalizer.py` for six sources, with its existing fixture and owner policy. For the five Uiua identities, review the same binding/data-declaration and physical-line policy already used by the array-source records. For nine APL identities, include explicit written closers and complete authored source bundles. Existing `prior_array_loc.py` covers seventeen exact old public identities; it covers none of these missing Uiua/APL identities. `apl-closer-approval-job07.json` approves six older APL sources only. The fannkuch source review proposes 38 units versus the producer's 37, but that proposal is not a qualified numeric receipt. Do not increment all APL counts blindly or silently use the producer metric.
2. **Reconcile preserved native evidence under the common timing mutex.** Match each report sample to its original source, runtime, command, workload, output validation and applicable execution/guard ancestry. Reuse the existing Uiua v5 independent reconciliation and its consumer checks, rechecking its exact file bindings at import. For the older R/Uiua records, reuse the archived guard-migration and execution-fingerprint logic rather than demanding fields their original record schema never wrote. For APL, close the argv revision and sample-84 recovery chain against the saved raw/supervisor/terminal evidence. No native benchmark rerun is needed for these completed observations.
3. **Prepare and review one additive publication transaction.** It must preserve every existing raw measurement and file, retain failed and discarded attempts, represent aliases explicitly, keep real report statuses, and add only qualified source/sample records. Any newly established minimum must update the affected chart baseline, derived coordinates and aggregate references together, with an exact before/after audit. Preview and independently review the candidate before applying it; then run the ordinary catalog and site checks.

The inventory did not locate a new canonical-count admission receipt for these twenty identities in the reviewed evidence. That is a scoped finding, not a claim that every repository artifact has been exhaustively searched. Source-specific prior approvals can be reused if subsequently located and their exact bindings match.

The shortest isolated admission candidate is Uiua fannkuch v5: its nine native observations already have independent reconciliation, leaving the exact two-source count binding and additive publication review. The larger R/Uiua/APL overlay can follow without invalidating or rerunning that cohort.

Independent source review subsequently confirmed the Uiua v5 counts of 20 and 21. The existing fannkuch LOC baseline is 31, so that admission must rebase only the current canonical LOC axis to 20. Raw counts, all timings and samples, historical reports, time baselines and formatted metrics remain unchanged. Publishing ratios below one against the old 31-line minimum would mislabel the new data as x-best.
