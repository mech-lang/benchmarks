# Lean 4 implementation study

Lean 4 has 23 measured native programs across the ten workloads. The original
ten programs remain available alongside thirteen additional candidates. Each
program has three validated complete-process samples. The fastest and fewest
normalized-LOC endpoints are selected independently from this measured pool.
Neither endpoint is a claim of a globally optimal Lean implementation.

The initial programs were local implementations of the workload contracts.
Binary trees drew on Lean's compiler benchmark; these are not presented as ten
published community submissions. Source provenance and the exact retained
programs are available through the explorer.

## Results

Times are seconds. The fastest and fewest-LOC columns can select different
programs. Small timing differences between historical cohorts do not establish
an optimization effect; no fresh matched Mech controls were run.

| Workload | Initial application LOC | Fewest application LOC | Original median | Fastest median |
| --- | ---: | ---: | ---: | ---: |
| N-body | 72 | 59 | 63.09 | 2.04 |
| Mandelbrot | 41 | 38 | 252.29 | 4.96 |
| K-nucleotide | 81 | 81 | 6.74 | 6.74 |
| Spectral norm | 41 | 40 | 10.20 | 0.185 |
| Reverse complement | 63 | 63 | 6.45 | 6.45 |
| Fannkuch-redux | 52 | 52 | 167.88 | 4.41 |
| FASTA | 51 | 51 | 13.04 | 13.04 |
| Binary trees | 31 | 31 | 1.75 | 1.74 |
| Regex-redux | 48 | 48 | 10.15 | 10.15 |
| Pi digits | 30 | 30 | 1.30 | 1.30 |

For example, the faster N-body program uses 88 normalized application LOC and has a 2.04 s
median. The shorter record/vector implementation uses 59 normalized application LOC and
has a 50.83 s median. Mandelbrot offers 46 LOC at 4.96 s or 38 LOC at 9.89 s.
Parallel fannkuch uses 75 LOC at 4.41 s; its shorter serial counterpart uses
52 LOC at 168.39 s. Both sides of these tradeoffs remain inspectable.

The historical [exact endpoint comparison](../experiments/lean4/optimization-v1/endpoint-comparison.json)
retains unrounded values, previous bundle counts and program identities. The
[current application-LOC correction](source-size-correction.md) provides the
updated source-size endpoints. Original FASTA, k-nucleotide,
regex-redux, reverse-complement and pi programs remain the fastest observed
implementations for their workloads. Their smaller replacement bundles do not
receive a speed win merely because they were entered as optimization candidates.

## Implementation changes

The numerical fast candidates use tail-recursive scalar parameters so Lean's
native output carries loop state in machine floats and integers. This avoids
repeated boxed mutable-loop tuples in the hot kernels. Cached constants and
integer-form float literals also avoid repeated scientific-literal conversions
inside N-body and spectral-norm inner loops. Mandelbrot computes its coordinates
and every pixel in Lean, with up to fifty iterations and the original PBM output.

Fannkuch uses packed permutations, a reusable scratch buffer and native counters.
Eight Lean tasks cover disjoint factoradic ranges. Prefix reversals, enumeration,
checksums and maxima remain Lean code. An instrumented diagnostic independently
ranks permutations and confirms every permutation occurs exactly once for
n=8 and n=9. Its C instrumentation is confined to an untimed diagnostic build.

The concise N-body candidate expresses positions and velocities as three-field
records with vector operations. The concise Mandelbrot candidate retains simpler
outer loops around a tail-recursive escape calculation. All candidates use
standard Lean streams directly and link only the authored helper units they
actually need. Removing unused shared argument/I/O and formatting units reduces the linked
source bundle. The current application-LOC policy separates generic I/O,
formatting and regex bindings in both initial and later profiles; workload
algorithms and their specific helpers remain counted.

## Qualification and timing

Both source families pass all 149 bounded reference cases. Tree diagnostics
observe exactly 51,550 dynamic node allocations at n=9, including leaves; the
stretch, long-lived and temporary-root lifetimes are reviewed in generated code.
Pi retains its two independent extraction divisions. The production binaries
remain unchanged by diagnostic instrumentation.

Normalized LOC uses native lexical ownership and expands independent statements
that share a physical line. Workload source is counted; generic Lean/C support is disclosed separately.
Native reader fixtures and an independent byte-offset replay qualify the counts;
physical-line packing does not supply a statement-count discount. No formatted
LOC result is claimed.

Thirty fast-family and nine concise-family observations were measured serially
under the common benchmark lock. Six concise bundles match fast-family source
bundles byte for byte and were not redundantly timed. The larger concise
spectral-norm candidate was not selected for a second full cohort after reduced
screening. Reduced diagnostics are retained separately and never substituted for
full-workload timings or extrapolated into chart points.

Each admitted sample measures a fresh native process: startup, input, complete
work and output, flush, and shutdown. Compilation and validation are outside the
timer. Complete saved output hashes, process records, sources, generated code
and binary identities are reconciled before admission. Other languages were not
remeasured and historical normalization baselines were preserved.

The [reconciled results](../experiments/lean4/optimization-v1/reconciled-v1/results.json)
and [catalog admission](../experiments/lean4/optimization-v1/catalog-admission-v1/receipt.json)
bind the source counts, full measurements and required-work evidence.
