# Benchmark methodology

These are saved local measurements on an **Apple M3**, using AC power with Low Power Mode disabled. The dataset combines several measurement cohorts; it is not a new run of every language under one compiler release.

## Workloads and admission

| Workload | Full input |
| --- | --- |
| N-body | 50,000,000 steps |
| Mandelbrot | 16,000 × 16,000 image |
| K-nucleotide | FASTA input generated with N = 25,000,000 |
| Spectral norm | N = 5,500 |
| Reverse complement | FASTA input generated with N = 25,000,000 |
| Fannkuch-redux | N = 12; 479,001,600 permutations |
| FASTA | N = 25,000,000; 250,000,000 output bases |
| Binary trees | N = 21, with required node allocation and lifetime checks |
| Regex-redux | FASTA N = 5,000,000; nine counts and five ordered replacements |
| Pi digits | 10,000 digits; unbounded sequential spigot and both required extractions |

Admission requires the prescribed work, complete output validation, and actual full-size samples. Shortened runs, scaled estimates, unfinished sources, and failed work checks supply no plotted timing. General libraries are allowed; application-level benchmark algorithms must remain in the named language. Source corrections and application helpers count toward LOC. The archived reports describe exceptions, input policies, worker counts, allocation checks, and each cohort's validation evidence.

## Timing and source size

A profile's elapsed time is the median of its saved samples, usually three, with five-, seven-, and ten-sample cohorts retained where recorded. Fresh-process measurements include startup, runtime/module loading, execution-time JIT, input, computation, complete output, and shutdown. Ahead-of-time builds, hashing, and output comparisons are outside the timing interval. The cohort protocols retain their worker limits and controls for competing compilation and power changes.

Mech interpreted uses a fresh whole-process cohort, including parsing and preparation, for every sample, median, standard deviation and chart coordinate. Internal preparation and execution measurements are retained as diagnostic phases only. A phase measurement cannot replace a whole-process observation in the language comparison. Historical interpreter optimization studies compare matching phases within their own cohorts; their execution-only figures do not supply the current rankings.

Canonical LOC counts nonblank, noncomment application source, with packed independent statements/assignments expanded and meaningful compiler pragmas counted. This is not compressed source size. Formatting-based LOC is an optional separately supported metric; missing formatter evidence is not replaced by guessed counts. Source roles distinguish application code from general runtime support.

## Chart calculations

For each workload and language variant, the fastest endpoint is the available profile with the lowest median elapsed time, breaking exact ties by LOC. The smallest endpoint has the lowest LOC, breaking ties by time. They may be the same program. Endpoints are winners within the retained measured candidate pool, not claims of universal optimality.

Each workload has saved minimum-LOC and minimum-time baselines. Coordinates are `program LOC / baseline LOC` and `program time / baseline time`; smaller values are better. Filtering the chart does not redefine those baselines. Admitting a newly qualified result below a saved minimum requires an audited rebase of that denominator and its derived program and aggregate coordinates. Raw source counts, timings, samples and retained evidence remain unchanged. For supported canonical-LOC rebases, an ordered history binds the successful admission receipt and its existing before/after snapshots; repository preservation checks validate the complete rebase, then reconstruct historical x coordinates only for the unchanged raw-data checks. A new time minimum requires its own reviewed normalization support. Multi-workload language coordinates are geometric means of the available per-workload ratios, with equal weight per included workload. Coverage is displayed because partial suites can yield different comparisons; use the shared-workload selection for the intersection available to the selected languages.

The **global median** is the coordinate-wise median of the visible language-variant summary points, calculated separately for fastest and smallest profiles. Each execution variant has one vote. This differs from both the median timing of repeated runs and the geometric mean used for a language's multi-workload summary. Its display toggle is independent of the language summary layer.

Spread contours use sample covariance in log2 ratio space across workloads, at one or two standard deviations. They describe workload variation, not confidence intervals or uncertainty in a stopwatch sample. Global contours use the same covariance construction across visible language variants and are translated to the global coordinate median. Recorded-sample and density layers display saved run observations.

## Provenance and reproduction

The current dataset links profiles to sources, saved reports, hashes, and validation evidence. `programs/` provides inspectable source bundles; `archive/` preserves detailed reports and experiments, and `migration/reorganization-paths.tsv` resolves their old repository paths.

A preserved source bundle does not by itself recreate a complete build environment. Historical commands may name local SDKs, compiler builds, dynamic libraries, or files no longer present. Exact historical flags and executable bytes were not captured for every profile. Those gaps remain explicit provenance limitations; they do not erase an otherwise established runtime family such as .NET or JVM. Reproduction on another machine requires checking the recorded dependencies and rerunning the full validation and measurement protocol.
