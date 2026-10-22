# Mech (AOT)

Recorded source bundles, grouped by workload. Each bundle has exact source hashes, timing samples and a link to its original report in `program.json`.

| Benchmark | Program | Canonical LOC | Median seconds | Samples |
|---|---|---:|---:|---:|
| binarytrees | [mech-binarytrees-parallel](binarytrees/mech-binarytrees-parallel/program.json) | 26 | 0.394411 | 3 |
| fannkuchredux | [mech-fannkuch-default](fannkuchredux/mech-fannkuch-default/program.json) | 39 | 2.83044 | 5 |
| fannkuchredux | [mech-fannkuch-even](fannkuchredux/mech-fannkuch-even/program.json) | 59 | 1.70246 | 3 |
| fasta | [mech-fasta-final-compact-v2](fasta/mech-fasta-final-compact-v2/program.json) | 32 | 1.2273 | 5 |
| fasta | [mech-fasta-final-expanded-v2](fasta/mech-fasta-final-expanded-v2/program.json) | 43 | 0.541193 | 5 |
| knucleotide | [mech-compact-final-std1-simd0-p4](knucleotide/mech-compact-final-std1-simd0-p4/program.json) | 17 | 0.513828 | 3 |
| mandelbrot | [array-state:five16-rows-loop-fma](mandelbrot/array-state-five16-rows-loop-fma/program.json) | 16 | 0.442217 | 3 |
| mandelbrot | [array-state:scalar11](mandelbrot/array-state-scalar11/program.json) | 11 | 2.19099 | 3 |
| nbody | [compact-baseline](nbody/compact-baseline/program.json) | 20 | 1.09048 | 7 |
| nbody | [pairwise-mass-tails](nbody/pairwise-mass-tails/program.json) | 25 | 1.03949 | 7 |
| pidigits | [mech-pi-advance-parent-20261022](pidigits/mech-pi-advance-parent-20261022/program.json) | 38 | 0.312764 | 7 |
| pidigits | [mech-pi-compact-shared-20261022](pidigits/mech-pi-compact-shared-20261022/program.json) | 37 | 0.290062 | 7 |
| pidigits | [mech-pi-final-advance-signed](pidigits/mech-pi-final-advance-signed/program.json) | 38 | 0.300272 | 3 |
| pidigits | [mech-pi-final-compact-signed](pidigits/mech-pi-final-compact-signed/program.json) | 35 | 0.396614 | 5 |
| pidigits | [mech-pi-shared-numerator-20261022](pidigits/mech-pi-shared-numerator-20261022/program.json) | 39 | 0.291547 | 7 |
| regexredux | [mech-regex-final-reuse-signed](regexredux/mech-regex-final-reuse-signed/program.json) | 24 | 0.489612 | 3 |
| revcomp | [mech-revcomp-optimized](revcomp/mech-revcomp-optimized/program.json) | 7 | 0.149273 | 3 |
| spectralnorm | [mech-integer-simd1-u4-r4-p8-g8](spectralnorm/mech-integer-simd1-u4-r4-p8-g8/program.json) | 12 | 0.0860753 | 3 |
