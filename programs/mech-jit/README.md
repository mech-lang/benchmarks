# Mech (JIT)

Recorded source bundles, grouped by workload. Each bundle has exact source hashes, timing samples and a link to its original report in `program.json`.

| Benchmark | Program | Canonical LOC | Median seconds | Samples |
|---|---|---:|---:|---:|
| binarytrees | [mech-binarytrees-parallel:jit](binarytrees/mech-binarytrees-parallel-jit/program.json) | 26 | 0.525069 | 3 |
| fannkuchredux | [mech-fannkuch-default:jit](fannkuchredux/mech-fannkuch-default-jit/program.json) | 39 | 3.01813 | 3 |
| fannkuchredux | [mech-fannkuch-even:jit](fannkuchredux/mech-fannkuch-even-jit/program.json) | 59 | 2.02061 | 3 |
| fasta | [mech-fasta-final-compact-v2:jit](fasta/mech-fasta-final-compact-v2-jit/program.json) | 32 | 1.34834 | 3 |
| fasta | [mech-fasta-final-expanded-v2:jit](fasta/mech-fasta-final-expanded-v2-jit/program.json) | 43 | 0.765849 | 3 |
| knucleotide | [mech-compact-final-std1-simd0-p4:jit](knucleotide/mech-compact-final-std1-simd0-p4-jit/program.json) | 17 | 0.612304 | 3 |
| mandelbrot | [mech-program-compact:jit](mandelbrot/mech-program-compact-jit/program.json) | 20 | 2.34705 | 3 |
| mandelbrot | [mech-program-simd-loop-fma:jit](mandelbrot/mech-program-simd-loop-fma-jit/program.json) | 29 | 0.78331 | 3 |
| nbody | [compact-baseline:jit](nbody/compact-baseline-jit/program.json) | 20 | 1.38046 | 3 |
| pidigits | [mech-pi-final-advance-signed:jit](pidigits/mech-pi-final-advance-signed-jit/program.json) | 38 | 0.447466 | 3 |
| pidigits | [mech-pi-final-compact-signed:jit](pidigits/mech-pi-final-compact-signed-jit/program.json) | 35 | 0.52691 | 3 |
| regexredux | [mech-regex-final-reuse-signed:jit](regexredux/mech-regex-final-reuse-signed-jit/program.json) | 24 | 0.564493 | 3 |
| revcomp | [mech-revcomp-optimized:jit](revcomp/mech-revcomp-optimized-jit/program.json) | 7 | 0.174436 | 3 |
| spectralnorm | [mech-integer-simd1-u4-r4-p8-g8:jit](spectralnorm/mech-integer-simd1-u4-r4-p8-g8-jit/program.json) | 12 | 0.23705 | 3 |
