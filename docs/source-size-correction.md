# Application source-size correction

Application LOC now separates reusable hosts, generic library bindings and general libraries from workload code. The correction changes 183 retained profiles; source bytes and every timing observation are unchanged. The ten normalized-LOC baselines are unchanged. The formatted pi baseline changes from 30 to 23 after excluding qualified formatting/support files.

Workload-specific helpers remain counted. In particular, Prolog retains 21 normalized lines for the record module’s declaration and FASTA-specific recognition; 13 generic line/join units are separated. Meaningful compiler and runtime settings retain the existing directive policy. The source inspection panel and Data exports include previous counts and source-specific support sections.

## Fewest application LOC

These are minima within each workload’s currently admitted candidate pool. Fastest and fewest-LOC programs are selected independently. Luau interpreted and JIT share source counts; the faster reverse-complement candidate uses 52 lines while the smaller one uses 50.

| Workload | Luau, both modes | Lean 4 (AOT) | Lua (interpreted) | Gleam | C3 | Elixir |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| N-body | 109 | 59 | 107 | 94 | 91 | 68 |
| Mandelbrot | 32 | 38 | 22 | 64 | 45 | 25 |
| K-nucleotide | 74 | 81 | 57 | 174 | 143 | 47 |
| Spectral norm | 39 | 40 | 33 | 53 | 50 | 28 |
| Reverse complement | 50 | 63 | 34 | 135 | 98 | 28 |
| Fannkuch-redux | 70 | 52 | 40 | 119 | 50 | 43 |
| FASTA | 68 | 51 | 86 | 93 | 81 | 38 |
| Binary trees | 40 | 31 | 38 | 64 | 52 | 24 |
| Regex-redux | 27 | 48 | 38 | 44 | 101 | 39 |
| Pi digits | 24 | 30 | 57 | 36 | 66 | 19 |

| Workload | Clojure | Prolog | Kotlin (JVM) | Nim | Pony |
| --- | ---: | ---: | ---: | ---: | ---: |
| N-body | 109 | 188 | 77 | 97 | 171 |
| Mandelbrot | 53 | 67 | 43 | 26 | 83 |
| K-nucleotide | 79 | 186 | 56 | 37 | 157 |
| Spectral norm | 62 | 96 | 43 | 28 | 106 |
| Reverse complement | 44 | 242 | 70 | 22 | 117 |
| Fannkuch-redux | 95 | 126 | 60 | 35 | 112 |
| FASTA | 73 | 87 | 53 | 62 | 106 |
| Binary trees | 43 | 68 | 26 | 26 | 68 |
| Regex-redux | 34 | 49 | 35 | 28 | 152 |
| Pi digits | 48 | 62 | 36 | 30 | 51 |

## Embedded bindings

The following exact-source partitions replay the existing cohort counters. The listed ranges are generic support; algorithm calls, workload constants and problem-specific helpers remain in the application. Prior source-count rules are preserved. One additional correction removes a six-line Julia block-comment body incorrectly counted by the old scanner.

| Source | Previous LOC | Application LOC | Support LOC |
| --- | ---: | ---: | ---: |
| regexredux-fortran-1.f90 | 237 | 91 | 146 |
| regexredux-ghc-3.hs | 199 | 112 | 87 |
| regexredux-smalltalk-pcre2.st | 143 | 65 | 78 |
| regexredux-python3-2.py | 118 | 102 | 16 |
| pidigits-csharpcore-6-arm64-faithful.cs | 119 | 82 | 37 |
| regexredux-csharpcore-2-arm64-faithful.cs | 140 | 56 | 84 |
| pidigits-rust-3.rs | 175 | 82 | 93 |
| pidigits-gnat-2.adb | 112 | 86 | 26 |
| regexredux-ada-pcre2-heap.adb | 126 | 50 | 76 |
| pidigits-fsharpcore-6-arm64-faithful.fs | 80 | 57 | 23 |
| pidigits-fortran-4.f90 | 121 | 62 | 59 |
| binarytrees-fortran-2.f90 | 124 | 90 | 34 |
| pidigits-racket-2-faithful.rkt | 87 | 43 | 44 |
| pidigits-python3-3.py | 52 | 46 | 6 |
| pidigits-odin-gmp.odin | 67 | 52 | 15 |
| regexredux-odin-jit-pcre2.odin | 101 | 40 | 61 |
| regexredux-pascal-pcre2.pas | 103 | 34 | 69 |
| regexredux-zig-compact-pcre2.zig | 101 | 42 | 59 |
| regexredux-zig-jit-pcre2.zig | 102 | 41 | 61 |
| pidigits-zig-gmp.zig | 66 | 56 | 10 |
| fast.d | 63 | 44 | 19 |
| regexredux-julia-3.jl | 45 | 38 | 7 |
| pidigits-julia-3.jl | 58 | 48 | 4 |
| BenchPidigitsJulia3.jl | 57 | 53 | 4 |
| binarytrees-gnat-4-native.adb | 259 | 219 | 40 |

Julia JIT pi’s 58 → 48 consists of four generic binding lines and six incorrectly counted comment lines. Julia AOT’s corresponding 57 → 53 removes four binding lines; its comment handling was already correct.

## Evidence and preservation

The [partition report](../experiments/source-size-correction/v1/partitions.json) binds reviewed sections to exact source hashes and retained counter implementations. The [transition receipt](../experiments/source-size-correction/v1/receipt.json) records every changed count and all canonical baselines. The [previous catalog](../experiments/source-size-correction/v1/before.json.gz) preserves source counts, endpoint selections, provenance and timings before this policy change. Authored general library code remains distinguishable from third-party dependencies; a complete size is marked unavailable where no qualified support count exists.

Current [program results](../results/current/programs.csv) contain corrected application counts. Per-program JSON manifests and website exports include the `source_accounting` breakdown. The historical audit remains bound to its original catalog snapshot.

```sh
python3 tools/apply_source_accounting.py --check
python3 tools/test_source_accounting.py
python3 tools/audit_source_size.py --check
python3 tools/verify_repository.py
```

The correction does not certify all unreviewed inline helpers or replace historical normalization evidence with a universal language parser. No benchmark was rerun.
