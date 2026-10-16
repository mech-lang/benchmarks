# Julia AOT whole-process results

All seventeen PackageCompiler executable profiles completed three full-workload samples each. Thirty fresh matched Mech AOT controls bring the cohort to 81 independently reconciled process observations. All complete outputs passed validation; no automatic retries or timing aliases were admitted. Fourteen Julia AOT profiles form the fastest and smallest endpoints across all ten workloads.

The elapsed interval includes process and runtime startup, app-image and library loading, regular-file input, the complete workload, full output and shutdown. Offline exhaustive compilation and training, setup, hashing and post-exit output validation are excluded. Scored processes use `--compile=no`, `JULIA_LOAD_CODEGEN_LIB=0` and `JULIA_NUM_THREADS=8,0`.

| Workload | Julia AOT (s) | Fresh Mech AOT (s) | Retained Julia JIT (s) | AOT / Mech | AOT / JIT |
| --- | ---: | ---: | ---: | ---: | ---: |
| regexredux | 1.728645916 | 0.495836750 | 1.764936083 | 3.49× | 0.98× |
| revcomp | 0.250765334 | 0.169255792 | 0.283163375 | 1.48× | 0.89× |
| pidigits | 0.387272000 | 0.305592709 | 0.399957042 | 1.27× | 0.97× |
| spectralnorm | 0.222038542 | 0.091466667 | 0.349881833 | 2.43× | 0.63× |
| mandelbrot | 0.503199375 | 0.450210125 | 0.566924833 | 1.12× | 0.89× |
| fasta | 31.378397375 | 0.606838250 | 4.057375166 | 51.71× | 7.73× |
| knucleotide | 1.232605166 | 0.531682333 | 1.597850708 | 2.32× | 0.77× |
| binarytrees | 1.888815667 | 0.417020250 | 2.085797291 | 4.53× | 0.91× |
| nbody | 1.521336667 | 1.041832875 | 1.642435958 | 1.46× | 0.93× |
| fannkuchredux | 2.841937792 | 1.736396000 | 2.951491500 | 1.64× | 0.96× |

Ratios are runtime divided by the comparison runtime: values above 1 mean longer elapsed time. Across ten equally weighted workloads, the geometric ratios are **2.730618× versus fresh Mech AOT** and **1.085884× versus retained Julia JIT**. The FASTA median is 31.378397375 seconds; all three full outputs were correct. The [static review](fasta-static-performance-review-v1.json) found no demonstrated adapter defect or justified patch, so the slowdown remains in the results and its cause is unresolved.

Mech controls share this rotating three-round cohort. Julia JIT medians are retained from separate historical cohorts; they were not remeasured. The [historical provenance audit](historical-jit-provenance-v1.json) records the Julia executable identity, available version observations, command flags and differences in five thread-pool requests. Standard application entry and runtime-reset adaptations are counted and reviewed in [source-adaptation.json](source-adaptation.json). These differences prevent attributing the comparison solely to AOT versus JIT.

The import preserves every existing Julia JIT and other-language observation, source record, exclusion and baseline. No new global timing minimum was found. Matched controls support this comparison without replacing existing Mech chart observations.

Evidence: [prepared plan](full81-prepared-v1.json), [cohort report](full81-v1/report.json), [terminal receipt](full81-v1/terminal.json), [independent reconciliation](full81-independent-review-v1.json), [comparison](full81-comparison-v1.json), and [actual import receipt](publication/apply-v1/import-receipt.json).
