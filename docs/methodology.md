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

Application LOC counts nonblank, noncomment workload source, using the retained
normalization rules for independent statements/assignments and meaningful
compiler pragmas. Workload algorithms, domain-specific parsing and output
construction count. Reusable process hosts, generic library bindings and general
libraries are excluded, including reviewed sections embedded in an application
file. Authored general libraries remain identified separately from third-party
dependencies; naming a workload executor as a library cannot remove its source
cost. Compiler-generated C, runtime implementations and installed libraries are
outside application LOC for every language, including Mech.

The [source-size correction](source-size-correction.md) applies this boundary to
the cases identified by the [earlier audit](source-size-audit.md). Original source
bytes, historical totals, count evidence and timings remain available. Source
inspection and exports disclose corrected application counts, previous totals
and excluded support. These are winners among measured implementations, not
proofs of minimum possible source size. Remaining unreviewed inline helpers and
historical normalization limitations are not represented as independently
recertified whole-language grammars.

Formatted LOC uses the same application boundary with separately qualified native
formatter counts. Missing formatter evidence is not replaced by guessed counts.

## Chart calculations

For each workload and language variant, the fastest endpoint is the available profile with the lowest median elapsed time, breaking exact ties by LOC. The smallest endpoint has the lowest LOC, breaking ties by time. They may be the same program. Endpoints are winners within the retained measured candidate pool, not claims of universal optimality.

Each workload has saved minimum-LOC and minimum-time baselines. Coordinates are `program LOC / baseline LOC` and `program time / baseline time`; smaller values are better. Filtering the chart does not redefine those baselines. Admitting a newly qualified result below a saved minimum requires an audited rebase of that denominator and its derived program and aggregate coordinates. Raw source counts, timings, samples and retained evidence remain unchanged. For supported canonical-LOC rebases, an ordered history binds the successful admission receipt and its existing before/after snapshots; repository preservation checks validate the complete rebase, then reconstruct historical x coordinates only for the unchanged raw-data checks. A new time minimum requires its own reviewed normalization support. Multi-workload language coordinates are geometric means of the available per-workload ratios, with equal weight per included workload. Coverage is displayed because partial suites can yield different comparisons; use the shared-workload selection for the intersection available to the selected languages.

The **global median** is the coordinate-wise median of the visible language-variant summary points, calculated separately for fastest and smallest profiles. Each execution variant has one vote. This differs from both the median timing of repeated runs and the geometric mean used for a language's multi-workload summary. Its display toggle is independent of the language summary layer.

The one-dimensional **rankings** use the fastest-time coordinate for speed and the fewest-LOC coordinate for source size. Their signed distance is `(log2(coordinate) − log2(reference)) / sample SD`, using the sample SD of the selected variants' log2 coordinates. Global Rankings use the coordinate median as the reference; a language page uses its selected execution variant, which sits at zero in both charts. Negative distances mean faster or smaller, and positive distances mean slower or larger. Recentering preserves the recorded coordinates and population spread. The readout still shows multiples of the fixed best baseline; the separate language-comparison table uses matched workloads and the selected language at 1.0×.

Spread contours use sample covariance in log2 ratio space across workloads, at one or two standard deviations. They describe workload variation, not confidence intervals or uncertainty in a stopwatch sample. Global contours use the same covariance construction across visible language variants and are translated to the global coordinate median. Recorded-sample and density layers display saved run observations.

Some program labels explicitly reuse another program's timings. These timing
aliases remain available for source inspection, but each recorded run appears
once in sample counts, sample dots and density. The original program is preferred
when both labels are visible. Programs measured separately remain distinct even
when their source or elapsed values match.

CSV exports retain one sample entry per program and run, including shared entries.
The `timing_alias_of` column identifies reused timings. Count distinct
`(timing_owner, run)` pairs for recorded executions; the
`unique_recorded_samples_*` fields in `results/current/summary.json` report those
totals. The older `recorded_samples_*` fields count sample entries.

## Provenance and reproduction

The current dataset links profiles to sources, saved reports, hashes, and validation evidence. `programs/` provides inspectable source bundles; `archive/` preserves detailed reports and experiments, and `migration/reorganization-paths.tsv` resolves their old repository paths.

A preserved source bundle does not by itself recreate a complete build environment. Historical commands may name local SDKs, compiler builds, dynamic libraries, or files no longer present. Exact historical flags and executable bytes were not captured for every profile. Those gaps remain explicit provenance limitations; they do not erase an otherwise established runtime family such as .NET or JVM. Reproduction on another machine requires checking the recorded dependencies and rerunning the full validation and measurement protocol.
