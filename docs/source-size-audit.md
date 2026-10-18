# Source-size accounting audit

The published LOC metric includes reusable support for some languages and excludes comparable support for others. The difference affects source-size comparisons independently of runtime performance.

The audit is bound to catalog commit `27e5d66be348e8fad2111e6e7d67bbe89a3d02bc` and catalog SHA-256 `de23a95e07862ae440d283f6028c9b0e35f56ef79b530680b472b5860c2e2fc6`. It inspects 1,035 profiles across 62 execution variants, 959 source files and 1,418 exported source copies. Every attached non-primary/support unit (49) received a content review; 27 additional primary-source units received targeted binding/direct-use review.

**Status: findings only. Published source counts, chart coordinates, source bytes and timing observations are unchanged.**

## Included reusable support

The following counts come from existing per-file normalization evidence. A range covers different profiles, not measurement uncertainty. These are support-code charges, not newly approved application LOC deductions. Mixed workload helpers and runtime directives are reported separately.

| Execution variant | Profiles charging generic support | Included support LOC per affected profile |
| --- | ---: | ---: |
| c3 | 13 | 10–78 |
| clojure | 20 | 46 |
| elixir | 20 | 62 |
| gleam | 20 | 67–112 |
| kotlin | 20 | 26 |
| lean4 | 15 | 9–76 |
| lua | 4 | 218 |
| luau | 11 | 108–194 |
| luau-jit | 11 | 108–194 |
| nim | 1 | 23 |
| pony | 2 | 5 |
| prolog | 18 | 39 |

Clojure, Kotlin and Elixir charge complete shared support modules, including services a particular workload does not use. Gleam charges its I/O and launcher layer in every profile and additional storage/task/regex bindings as needed. Lua charges an entire 218-line GMP compatibility module to each of four pi-digits profiles. Earlier Lean profiles include `Common.lean` and `Format.c` in every bundle; later profiles remove unused helpers, so only five later profiles retain native helper charges.

For example, one Lua pi profile has 281 published LOC, comprising 63 application lines and 218 binding lines. Clojure compact binary trees has 89, comprising 43 application and 46 shared support lines. These source splits are already recorded; changing the ranking metric still requires a consistent policy.

## Support already excluded elsewhere

Futhark, Mojo, BQN/K, Elm, MATLAB and Swift exclude general helpers, adapters or dependency configuration from application LOC. The audited excluded launchers do not contain the benchmark algorithm. Their current treatment is inconsistent with charging the comparable Luau host or Gleam/Prolog launch layer.

A second distinction matters: Futhark excludes authored bigint, map, formatting and regex implementations, and Mojo excludes an authored integer map as well as native bindings. Those are substantial general library implementations, not just launch glue or preinstalled standard libraries. Their provenance and separate library size should remain visible. General API names alone do not establish that a helper is an external dependency.

Mech built-in and standard-library implementations are also outside its application counts, as are installed runtimes and libraries for other languages. A separate authored-library accounting rule must apply consistently to comparable Mech library additions. Having no attached helper file does not prove that a program has no supporting implementation.

## Embedded bindings

Separate-file accounting alone misses general bindings written inside the application file. Content review found examples in Ada, C#, F#, D, Fortran, Haskell, Julia, Odin, Pascal, Python, Racket, Rust, Smalltalk and Zig. The source ranges below identify evidence, not complete normalized partitions. Direct library use in Swift and a Chapel CTypes import were also reviewed and do not establish an extra handwritten wrapper.

| Source | Languages | Evidence lines | Content |
| --- | --- | --- | --- |
| [pidigits-gnat-2.adb](../programs/ada/pidigits/pidigits-gnat-2/pidigits-gnat-2.adb) | ada | 23–59 | Ada GMP ABI types, primitive declarations and putchar import. Package Print_String before this range is output-format specific; recurrence/extraction after it must stay. |
| [regexredux-ada-pcre2-heap.adb](../programs/ada/regexredux/regexredux-ada-pcre2-heap/regexredux-ada-pcre2-heap.adb) | ada | 15–85 | Ada PCRE2 types/declarations and generic Pattern/Count/Substitute functions. Prescribed variants and replacements begin at line 86 and must stay. |
| [regexredux-fortran-1.f90](../programs/fortran/regexredux/regexredux-fortran-1/regexredux-fortran-1.f90) | fortran | 9–225 | Fortran pcre2_mod contains ABI declarations and a generic growing-string replacement implementation. Benchmark pattern tables and workflow start in the subsequent program; their LOC must stay. |
| [regexredux-odin-jit-pcre2.odin](../programs/odin/regexredux/regexredux-odin-jit-pcre2/regexredux-odin-jit-pcre2.odin) | odin | 4–63 | Odin PCRE2 ABI, compile/find/destroy and generic read/substitute services before main. Prescribed counts/substitution pipeline remains application code. |
| [pidigits-rust-3.rs](../programs/rust/pidigits/pidigits-rust-3/pidigits-rust-3.rs) | rust | 97–199 | Rust Mpz ownership/arithmetic/comparison wrapper and raw GMP ABI. Context recurrence/iterator before this section remains application code. |
| [pidigits-racket-2-faithful.rkt](../programs/racket/pidigits/pidigits-racket-2-faithful/pidigits-racket-2-faithful.rkt) | racket | 14–55 | Racket GMP ABI and generic arithmetic syntax transformer. Spigot-specific compose macros inside digits are application code and must stay. |
| [pidigits-odin-gmp.odin](../programs/odin/pidigits/pidigits-odin-gmp/pidigits-odin-gmp.odin) | odin | 5–18 | Odin GMP foreign ABI and integer representation; main contains digit recurrence. |
| [pidigits-python3-3.py](../programs/python/pidigits/pidigits-python3-3/pidigits-python3-3.py) | python | 17–28 | Python ctypes GMP loading, return type and mpz representation. Allocated state, extract/next/eliminate helpers implement the workload and must stay. |
| [regexredux-csharpcore-2-arm64-faithful.cs](../programs/csharp-aot/regexredux/regexredux-csharpcore-2-arm64-faithful-aot/regexredux-csharpcore-2-arm64-faithful.cs) | csharp, csharp-aot | 75–166 | C# Pcre class implements general compile/match/replace and native declarations. Workload tables and orchestration remain outside the class. |
| [regexredux-zig-compact-pcre2.zig](../programs/zig/regexredux/regexredux-zig-compact-pcre2/regexredux-zig-compact-pcre2.zig) | zig | 3–56 | Zig byte input, PCRE2 ABI/Regex object and generic substitution before main. Workload arrays, count loops and ordered replacements remain application code. |
| [pidigits-fortran-4.f90](../programs/fortran/pidigits/pidigits-fortran-4/pidigits-fortran-4.f90) | fortran | 9–86 | Fortran GMP module holds representation and primitive ABI declarations. Digit extraction/recurrence follows in the application program. |
| [pidigits-fsharpcore-6-arm64-faithful.fs](../programs/fsharp-aot/pidigits/pidigits-fsharpcore-6-arm64-faithful-aot/pidigits-fsharpcore-6-arm64-faithful.fs) | fsharp, fsharp-aot | 9–40 | F# GMP representation and P/Invoke declarations; digit recurrence and custom output counter remain application code. |
| [pidigits-zig-gmp.zig](../programs/zig/pidigits/pidigits-zig-gmp/pidigits-zig-gmp.zig) | zig | 3–12 | Zig GMP representation/declarations. Main owns state lifetime and complete digit recurrence. |
| [regexredux-python3-2.py](../programs/python/regexredux/regexredux-python3-2/regexredux-python3-2.py) | python | 23–57 | Python ctypes PCRE2 result-type setup and generic replace service. Worker tasks and benchmark workflow contain additional interleaved binding operations; listed range is an example, not an exhaustive partition. |
| [regexredux-zig-jit-pcre2.zig](../programs/zig/regexredux/regexredux-zig-jit-pcre2/regexredux-zig-jit-pcre2.zig) | zig | 3–57 | Zig JIT variant of generic I/O/PCRE2/Regex/substitution helpers before main; native JIT call differs. Workload logic remains in main. |
| [regexredux-smalltalk-pcre2.st](../programs/smalltalk/regexredux/regexredux-smalltalk-pcre2/regexredux-smalltalk-pcre2.st) | smalltalk | 2–78 | Smalltalk BenchmarkPCRE class implements general PCRE2 bindings, ownership, counting and replacement. BenchmarksGame owns workload constants and orchestration. |
| [pidigits-csharpcore-6-arm64-faithful.cs](../programs/csharp-aot/pidigits/pidigits-csharpcore-6-arm64-faithful-aot/pidigits-csharpcore-6-arm64-faithful.cs) | csharp, csharp-aot | 137–185 | C# GMP layout and P/Invoke class. ExtractDigit and the recurrence remain application logic despite using GMP. |
| [binarytrees-gnat-4-native.adb](../programs/ada/binarytrees/binarytrees-gnat-4-native/binarytrees-gnat-4-native.adb) | ada | 309–379 | Ada Apache_Runtime and Pools packages declare/wrap general APR operations. Earlier tree construction and node storage code remain application logic. |
| [fast.d](../programs/d/pidigits/d-fast/fast.d) | d | 7–25 | D GMP representation and extern(C) declarations. The local extract helper in main is benchmark-specific and must stay. |
| [regexredux-pascal-pcre2.pas](../programs/pascal/regexredux/regexredux-pascal-pcre2/regexredux-pascal-pcre2.pas) | pascal | 5–51 | Pascal PCRE2 declarations and generic compile/count/substitute services. Meaningful compiler/link directives and workload pattern arrays require separate treatment. |
| [binarytrees-fortran-2.f90](../programs/fortran/binarytrees/binarytrees-fortran-2/binarytrees-fortran-2.f90) | fortran | 10–53 | Fortran APR interface/error callback module. Tree representation, actual node allocation, construction, checks and pool lifetimes in later modules remain application logic. |
| [regexredux-julia-3.jl](../programs/julia/regexredux/regexredux-julia-3/regexredux-julia-3.jl) | julia | 10–16 | Julia replacement of Base.PCRE.exec selects native PCRE2 JIT for a generic match operation; workload patterns and orchestration follow. |
| [BenchPidigitsJulia3.jl](../programs/julia-aot/pidigits/pidigits-julia-3-aot/BenchPidigitsJulia3.jl) | julia-aot | 15–18 | Julia AOT retains the same generic GMP wrapper section inside its module; julia_main and workload logic remain application code. |
| [pidigits-julia-3.jl](../programs/julia/pidigits/pidigits-julia-3/pidigits-julia-3.jl) | julia | 13–16 | Julia adds three generic in-place GMP wrappers. next!, extract! and produce! are spigot-specific and must stay. |
| [regexredux-ghc-3.hs](../programs/haskell/regexredux/regexredux-ghc-3/regexredux-ghc-3.hs) | haskell | 25–158 | Haskell PCRE2 imports/types, growable string and generic replace service precede main. Keep prescribed patterns, workload scheduling and nine-count/five-substitution orchestration in main. |

## Workload logic and configuration

The Prolog `clbg_records.pl` module is mixed: generic line handling and string assembly sit beside FASTA header/comment recognition and literal `>THREE` selection. The FASTA-specific sections must remain application code. Its 34 normalized lines cannot all be subtracted as generic support.

Likewise, pi extraction/recurrence helpers, tree construction/checks, DNA complement tables, workload pattern lists and the prescribed replacement sequence remain application logic even when they call a native library. Racket’s spigot-specific compose macros are distinct from its general arithmetic syntax wrapper.

Two Pony profiles include five legacy test-package compatibility alias lines. Two APL profiles charge a one-line workspace system-limit setting. The former belongs in support; the latter needs a configuration rule consistent with the existing meaningful-pragma policy. No setting is silently removed by this audit.

## Proposed accounting boundary

Record application/workload LOC, reusable support LOC and authored library LOC separately, with total authored LOC available. Track third-party dependencies and configuration separately from authored application source. Apply the same roles to embedded source sections and separate files. Application call sites and workload-specific helpers continue to count; moving benchmark logic to a native helper cannot erase its source cost or establish a pure named-language implementation.

Before changing published coordinates, qualify normalized splits for embedded/mixed sections, agree how authored general libraries enter the main metric, and recompute affected endpoint selection and fixed LOC baselines. This is source-accounting work and does not require rerunning saved timing samples.

## Coverage and reproduction

Existing per-file normalized counts sum exactly to profile LOC for 311 profiles. Another 662 have a single attached source, so their recorded total requires no cross-file partition. The remaining 62 multi-source profiles exclude support without complete per-file normalized counts; their total including excluded support cannot be recovered by subtraction. Missing normalized counts are not replaced with physical-line estimates. Native-binding text screening is a discovery aid, not a semantic proof for every source or installed dependency.

Rebuild or check the hash-bound audit:

```sh
python3 tools/audit_source_size.py
python3 tools/audit_source_size.py --check
```

The [structured report](../experiments/source-size-audit/v1/report.json) contains every profile/file relationship, current charging role, recorded normalized counts, evidence ranges and language-level totals. The [review decisions](../data/source-size-review.json) bind content judgments to exact source hashes.

This audit does not recertify historical compiler/runtime implementations, inspect every installed dependency, or claim that all possible inline reusable helpers have been identified.
