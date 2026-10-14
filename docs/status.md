# Benchmark status

The current snapshot contains **52 execution variants across 46 language families**, **10 workloads**, and **834 selected timed program profiles**. The source inventory retains **843 profiles** including nine measured candidates that are not selected endpoints. Forty-seven execution variants cover the complete suite.

| Partial coverage | Measured workloads | Missing workloads |
| --- | ---: | --- |
| Lua interpreter | 9 / 10 | Pi digits |
| Futhark | 9 / 10 | Binary trees: array representation does not meet the per-node allocation contract |
| R | 7 / 10 | N-body, binary trees, fannkuch-redux |
| Uiua | 7 / 10 | N-body, binary trees, fannkuch-redux |
| GNU APL | 4 / 10 | N-body, mandelbrot, k-nucleotide, binary trees, fannkuch-redux, FASTA |

Pending additions are **Pony, Prolog, Julia AOT, Rebol, Elixir, and Kotlin**. Their preparation and validation artifacts remain in the archive; they have no admitted selectable series in this snapshot. The existing Julia series is JIT. Availability of a compiler or an unfinished study does not count as an admitted timing.

Repository navigation:

| Location | Contents |
| --- | --- |
| `site/src/` | Maintained explorer interface and chart logic |
| `data/` | Current dataset and declarative language metadata |
| `programs/<language>/<workload>/<id>/` | Current source bundles and profile metadata |
| `benchmarks/<workload>/` | Workload definitions and indexes |
| `results/current/` | Current result summaries and validation records |
| `archive/` | Historical studies, measurements, qualification records, and previous tools, grouped by subject |
| `migration/reorganization-paths.tsv` | Original-to-current path mapping, with original Git blob identities |

Old receipts retain their original paths; use the migration map to resolve them. The source bundles improve inspection and navigation, but are not fully portable toolchains: historical commands may depend on local runtimes, SDKs, libraries, working directories, or absent binaries. See [methodology](methodology.md) and [language classification](languages.md).
