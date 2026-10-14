# Language classification

The catalog explicitly defines all **55 measured execution variants in 49 language families**. The browser reads declarative metadata for each variant. AOT/JIT variants of one language remain in the same language family.

| Facet | Meaning |
| --- | --- |
| Runtime / toolchain | Measured engine or compiler family: native toolchains, JVM, .NET, BEAM, Node.js/V8, or another identified language runtime |
| Execution | Native AOT, native JIT, or interpretation; mixed cohorts may have more than one mode |
| Typing | The language's primary static or dynamic type-checking model |
| Paradigm | Established language styles, with intentional overlap: imperative, object-oriented, functional, logic, array, reactive/dataflow |
| Memory | Standard models in the measured language/runtime: manual allocation, ownership/RAII, reference counting, tracing GC, cycle collection |

The exact runtime name is retained even when the compact facet groups several implementations under “Other language runtimes.” This is a known category, not missing classification. Native compilation does not imply manual memory management. Paradigms and memory models do not claim that each individual benchmark exercises every supported model; foreign-library allocation and optional alternate collectors are excluded.

Key distinctions:

- **Java, Clojure and Kotlin are JVM/JIT.** All 17 selected Java commands invoke OpenJDK `java` and record JIT execution. GraalVM NativeAOT identifies their upstream source submissions. Kotlin runs retained JVM classes on HotSpot with G1; JVM startup, class loading and runtime compilation are included in every sample.
- **C# and F# include .NET JIT and NativeAOT.** NativeAOT remains part of .NET and retains runtime/GC support.
- **Elm and JavaScript run on Node.js/V8.** Elm remains statically typed and functional. Compiling Elm to JavaScript does not make the measured execution native AOT.
- **Ruby uses YJIT. PHP has both modes:** fourteen selected profiles request tracing JIT and one explicitly disables it. **R's JIT produces interpreted bytecode.** SBCL saved cores and Racket CS native modules were precompiled before timing.
- **Manual allocation and ownership/RAII are independent.** C/C3/Zig/Odin use explicit allocation; Rust uses ownership and standard RC types; Chapel has separate owned/shared/unmanaged strategies.
- **RC, tracing GC, and cycle collection are independent.** CPython/PHP combine RC and cycle collection. Nim's measured ORC uses RC plus trial-deletion cycle collection, not a global tracing collector. BEAM tracing heaps coexist with reference-counted large binaries.

Classification is based on preserved measurement/build records plus primary language/runtime documentation. Exact missing historical flags remain evidence limitations rather than making the runtime family unknown. The machine-readable audit retains report paths, hashes, documentation references, and per-variant notes. Fetches of some Growler/GNU APL/Uiua internal documentation were unavailable during review; their implementation-level RC references are retained without claiming fresh source or binary certification.

| Variant | Measured implementation | Execution | Typing | Memory models |
| --- | --- | --- | --- | --- |
| Ada | GNAT / GCC | AOT | Static | Manual, Ownership/RAII |
| APL (GNU APL) | GNU APL interpreter | Interpreted | Dynamic | RC |
| BQN (CBQN) | CBQN interpreter on ARM64 | Interpreted | Dynamic | RC, Tracing GC |
| C (GCC + LLVM) | GCC and Clang/LLVM | AOT | Static | Manual |
| C# (AOT) | .NET NativeAOT runtime | AOT | Static | Tracing GC |
| C# (JIT) | .NET CoreCLR JIT | JIT | Static | Tracing GC |
| C++ (GCC + LLVM) | G++ and Clang/LLVM | AOT | Static | Manual, Ownership/RAII, RC |
| C3 | C3 / LLVM | AOT | Static | Manual |
| Chapel | Chapel native compiler/runtime | AOT | Static | Manual, Ownership/RAII, RC |
| Clojure | Clojure on OpenJDK HotSpot JVM | JIT | Dynamic | Tracing GC |
| Common Lisp (SBCL) | SBCL precompiled native saved core | AOT | Dynamic | Tracing GC |
| Crystal | Crystal / LLVM / Boehm GC | AOT | Static | Tracing GC |
| D | LDC / LLVM / D runtime | AOT | Static | Tracing GC, Manual, Ownership/RAII |
| Dart (AOT) | Dart native AOT runtime | AOT | Static | Tracing GC |
| Dart (JIT) | Dart VM JIT | JIT | Static | Tracing GC |
| Elixir | Elixir on Erlang / BEAM JIT | JIT | Dynamic | Tracing GC, RC |
| Elm | Elm generated JavaScript on Node.js / V8 | JIT | Static | Tracing GC |
| Erlang | Erlang / BEAM JIT | JIT | Dynamic | Tracing GC, RC |
| F# (AOT) | .NET NativeAOT runtime | AOT | Static | Tracing GC |
| F# (JIT) | .NET CoreCLR JIT | JIT | Static | Tracing GC |
| Fortran | GNU Fortran / GCC | AOT | Static | Manual, Ownership/RAII |
| Futhark | Futhark CPU C backend | AOT | Static | RC |
| Gleam | Gleam on Erlang / BEAM JIT | JIT | Static | Tracing GC, RC |
| Go | Go native compiler/runtime | AOT | Static | Tracing GC |
| Haskell | GHC native compiler/runtime | AOT | Static | Tracing GC |
| Java | OpenJDK HotSpot JVM | JIT | Static | Tracing GC |
| JavaScript (V8) | Node.js / V8 | JIT | Dynamic | Tracing GC |
| Julia | Julia / LLVM runtime | JIT | Dynamic | Tracing GC |
| K (Growler) | Growler K interpreter | Interpreted | Dynamic | RC |
| Kotlin (JVM) | Kotlin 2.4.21 / Eclipse Temurin HotSpot 25.0.4.1+1 | JIT | Static | Tracing GC |
| Lua (interpreted) | PUC Lua bytecode interpreter | Interpreted | Dynamic | Tracing GC |
| LuaJIT | LuaJIT | JIT | Dynamic | Tracing GC |
| MATLAB | MATLAB native runtime / JIT | JIT | Dynamic | RC, Cycles |
| Mech (AOT) | Mech native AOT compiler/runtime | AOT | Static | Ownership/RAII, RC |
| Mech (interpreted) | Mech typed interpreter | Interpreted | Static | Ownership/RAII, RC |
| Mech (JIT) | Mech native JIT runtime | JIT | Static | Ownership/RAII, RC |
| Mojo | Mojo / MLIR / LLVM | AOT | Static | Ownership/RAII, Manual |
| Nim | Nim C backend / Clang / ORC | AOT | Static | RC, Cycles, Ownership/RAII |
| OCaml | OCaml native compiler/runtime | AOT | Static | Tracing GC |
| Odin | Odin / LLVM | AOT | Static | Manual |
| Pascal | Free Pascal | AOT | Static | Manual, RC |
| Perl | Perl 5 interpreter | Interpreted | Dynamic | RC |
| PHP | PHP / Zend Engine / OPcache | JIT, Interpreted | Dynamic | RC, Cycles |
| Pony | ponyc / LLVM / Pony runtime | AOT | Static | Tracing GC, RC, Cycles |
| Python (CPython) | CPython bytecode interpreter | Interpreted | Dynamic | RC, Cycles |
| R | GNU R bytecode interpreter | Interpreted | Dynamic | Tracing GC |
| Racket | Racket CS / Chez precompiled native modules | AOT | Dynamic | Tracing GC |
| Roc | Roc LLVM alpha4 compiler/runtime | AOT | Static | RC |
| Ruby (YJIT) | CRuby / YJIT | JIT | Dynamic | Tracing GC |
| Rust | rustc / LLVM | AOT | Static | Ownership/RAII, RC |
| Smalltalk (Pharo) | Pharo Cog/Spur VM | JIT | Dynamic | Tracing GC |
| Swift | Swift / LLVM | AOT | Static | RC |
| Uiua | Uiua interpreter | Interpreted | Dynamic | RC |
| V | V C backend / Clang / Boehm GC | AOT | Static | Tracing GC |
| Zig | Zig / LLVM | AOT | Static | Manual |
