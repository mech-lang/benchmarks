# Rebol full-size cohort outcome

All ten Rebol workloads completed and were admitted to the public benchmark catalog. The cohort finished on **2026-10-15 at 19:55 UTC**, with **60 qualified observations**: 30 Rebol subject processes and 30 fresh matched Mech AOT controls, three of each per workload. Complete output matched the reference contracts for every observation. No profiles failed and no slots were skipped. The [independent reconciliation](independent-reconciliation-v1.json) retains the observation and integrity evidence; the [applied import receipt](publication/apply-receipt-v1.json) records admission of all ten workloads.

## Results

Each median and sample standard deviation uses all three fresh observations. Time × Mech is the Rebol median divided by the median of that workload's fresh matched Mech controls; a larger value means a longer elapsed time. Values below are rounded to three significant figures. Canonical LOC is the admitted statement-normalized count for the complete authored source bundle.

| Workload | Rebol median (s) | Rebol sample SD (s) | Mech median (s) | Time × Mech | Canonical LOC |
|---|---:|---:|---:|---:|---:|
| regexredux | 18.0 | 0.267 | 0.502 | 35.9 | 469 |
| revcomp | 276 | 0.218 | 0.186 | 1,480 | 455 |
| pidigits | 847 | 0.414 | 0.314 | 2,700 | 478 |
| spectralnorm | 567 | 0.360 | 0.110 | 5,180 | 449 |
| mandelbrot | 2,130 | 0.130 | 0.464 | 4,580 | 445 |
| fasta | 191 | 0.669 | 0.620 | 308 | 468 |
| knucleotide | 2,310 | 3.59 | 0.545 | 4,240 | 501 |
| binarytrees | 1,010 | 5.66 | 0.456 | 2,220 | 436 |
| nbody | 2,180 | 3.52 | 1.06 | 2,060 | 486 |
| fannkuchredux | 4,920 | 0.978 | 1.83 | 2,690 | 463 |

Exact samples, statistics, matched controls and source counts are retained in the [publication candidate](publication/candidate-v1.json) and the admitted [program inventory](../../../data/benchmarks.json).

## Measurement and source scope

The runtime was Oldes Rebol/Bulk 3.22.1 on macOS. Each subject observation measured a fresh, single-worker Rebol process from startup through shutdown, including authored source and helper evaluation, extension loading, input, all required computation and complete output. Compilation, harness file setup, input hashing, environment waits and output validation were outside the timer. Subjects and controls ran serially, with their order alternating across the three rounds.

Each workload has one canonical Rebol program. The same program supplies its fastest and fewest-lines catalog endpoints without duplicate program records, copied timings or a separate optimization claim. The ten authored bundles contain **15 distinct physical authored source files**: ten Rebol main files, four shared Rebol helper or loader files, and one corrected C extension source. Every bundle counts its main, I/O helper, extension loader and the entire C extension source; the bigint or regex facade is also counted where used. Shared files remain part of each applicable program's count. Formatted LOC is unavailable.

Runtime-source equivalence is not claimed. Complete stdout was discarded after validation; retained output evidence consists of byte counts, hashes and validation receipts. Resource evidence is sampled process-group RSS.

## Publication record

The [applied import](publication/apply-receipt-v1.json) added ten canonical program records and admitted all ten workload endpoints. Existing program rows and Mech baselines were unchanged. The false admission flags in the retained producer report, independent reconciliation and export candidate describe their earlier stages and remain preserved as historical evidence; public catalog admission is established by the actual import receipt.

The subsequent [platform normalization receipt](publication/platform-normalization-v1.json) records a metadata-only correction: the dataset's `runtime_family` platform facet is `runtime`, matching the reviewed platform classification. The language family remains `rebol`. Timings, sources and baselines were unchanged by that correction.
