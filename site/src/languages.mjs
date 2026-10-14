// Explicit reviewed taxonomy for each measured variant. See data/languages.json for saved-report evidence.
export const languageMetadata = {
  "c": {
    "platform": "native",
    "runtime": "GCC and Clang/LLVM",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative"
    ],
    "memory": [
      "manual"
    ],
    "note": "Manual heap allocation; automatic local storage is not an ownership type system.",
    "sources": [
      "https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf"
    ]
  },
  "cpp": {
    "platform": "native",
    "runtime": "G++ and Clang/LLVM",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "manual",
      "owned",
      "rc"
    ],
    "note": "RAII and standard smart pointers coexist with explicit allocation. Paradigms and memory models describe the language/runtime, not a claim every measured source uses every model.",
    "sources": [
      "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rr-raii"
    ]
  },
  "chapel": {
    "platform": "native",
    "runtime": "Chapel native compiler/runtime",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object",
      "array"
    ],
    "memory": [
      "manual",
      "owned",
      "rc"
    ],
    "note": "Distinct owned, shared (reference counted), and unmanaged class strategies; not one combined manual/ownership model.",
    "sources": [
      "https://chapel-lang.org/docs/language/spec/classes.html"
    ]
  },
  "go": {
    "platform": "native",
    "runtime": "Go native compiler/runtime",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative"
    ],
    "memory": [
      "gc"
    ],
    "note": "Native executable with a tracing-GC runtime; native compilation does not imply manual memory management.",
    "sources": [
      "https://go.dev/doc/gc-guide"
    ]
  },
  "java": {
    "platform": "jvm",
    "runtime": "OpenJDK HotSpot JVM",
    "execution": [
      "jit"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object"
    ],
    "memory": [
      "gc"
    ],
    "note": "All 17 displayed profiles invoke the OpenJDK JVM and explicitly record JIT execution. GraalVM native-image describes the upstream submission only, not these measurements.",
    "sources": [
      "https://docs.oracle.com/en/java/javase/25/vm/java-hotspot-virtual-machine-performance-enhancements.html"
    ]
  },
  "julia": {
    "platform": "runtime",
    "runtime": "Julia / LLVM runtime",
    "execution": [
      "jit"
    ],
    "typing": "dynamic",
    "style": [
      "imperative",
      "functional",
      "array"
    ],
    "memory": [
      "gc"
    ],
    "note": "Saved commands invoke the Julia LLVM runtime with -O3. JIT is the normal measured execution path; exact effective flags were not captured for every historical sample.",
    "sources": [
      "https://docs.julialang.org/en/v1/devdocs/jit/",
      "https://docs.julialang.org/en/v1/devdocs/gc/"
    ]
  },
  "mech": {
    "platform": "native",
    "runtime": "Mech native AOT compiler/runtime",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "array",
      "functional",
      "reactive"
    ],
    "memory": [
      "owned",
      "rc"
    ],
    "note": "Typed array/dataflow language. Native storage ownership and runtime reference-counted values are distinct from user-managed allocation.",
    "sources": [
      "https://github.com/mech-lang/mech"
    ]
  },
  "mech-jit": {
    "platform": "runtime",
    "runtime": "Mech native JIT runtime",
    "execution": [
      "jit"
    ],
    "typing": "static",
    "style": [
      "array",
      "functional",
      "reactive"
    ],
    "memory": [
      "owned",
      "rc"
    ],
    "note": "Native JIT is distinct from the AOT and loaded-interpreter series; runtime values use owned storage and reference counting.",
    "sources": [
      "https://github.com/mech-lang/mech"
    ]
  },
  "mech-resident": {
    "platform": "runtime",
    "runtime": "Mech loaded typed interpreter",
    "execution": [
      "interpreted"
    ],
    "typing": "static",
    "style": [
      "array",
      "functional",
      "reactive"
    ],
    "memory": [
      "owned",
      "rc"
    ],
    "note": "Loaded typed interpreter; its retained timing starts after preparation, unlike fresh-process timings. Runtime values use owned storage and reference counting.",
    "sources": [
      "https://github.com/mech-lang/mech"
    ]
  },
  "rust": {
    "platform": "native",
    "runtime": "rustc / LLVM",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "functional"
    ],
    "memory": [
      "owned",
      "rc"
    ],
    "note": "Ownership/borrowing with deterministic drop; standard Rc/Arc provide reference counting. Unsafe allocator APIs do not make manual allocation the default model.",
    "sources": [
      "https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html",
      "https://doc.rust-lang.org/std/rc/"
    ]
  },
  "python": {
    "platform": "runtime",
    "runtime": "CPython bytecode interpreter",
    "execution": [
      "interpreted"
    ],
    "typing": "dynamic",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "rc",
      "cycles"
    ],
    "note": "CPython bytecode execution in the saved runner; optional CPython JIT was not enabled by the recorded command. Reference counting and a separate cycle collector are both represented.",
    "sources": [
      "https://docs.python.org/3/c-api/memory.html",
      "https://docs.python.org/3/library/gc.html"
    ]
  },
  "ruby": {
    "platform": "runtime",
    "runtime": "CRuby / YJIT",
    "execution": [
      "jit"
    ],
    "typing": "dynamic",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "gc"
    ],
    "note": "All 19 selected saved commands explicitly enable --yjit; the old interpreted language-group membership was stale.",
    "sources": [
      "https://docs.ruby-lang.org/en/master/yjit/yjit_md.html",
      "https://docs.ruby-lang.org/en/master/GC.html"
    ]
  },
  "perl": {
    "platform": "runtime",
    "runtime": "Perl 5 interpreter",
    "execution": [
      "interpreted"
    ],
    "typing": "dynamic",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "rc"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://perldoc.perl.org/perlref"
    ]
  },
  "luajit": {
    "platform": "runtime",
    "runtime": "LuaJIT",
    "execution": [
      "jit"
    ],
    "typing": "dynamic",
    "style": [
      "imperative",
      "functional"
    ],
    "memory": [
      "gc"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://luajit.org/luajit.html"
    ]
  },
  "javascript": {
    "platform": "javascript",
    "runtime": "Node.js / V8",
    "execution": [
      "jit"
    ],
    "typing": "dynamic",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "gc"
    ],
    "note": "Node/V8 is an execution engine, not a JavaScript-only language platform. Elm in this cohort runs on the same engine. Saved commands use normal V8 execution; exact effective flags are incomplete for some historical samples.",
    "sources": [
      "https://nodejs.org/en/learn/getting-started/the-v8-javascript-engine",
      "https://v8.dev/blog/trash-talk"
    ]
  },
  "php": {
    "platform": "runtime",
    "runtime": "PHP / Zend Engine / OPcache",
    "execution": [
      "jit",
      "interpreted"
    ],
    "typing": "dynamic",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "rc",
      "cycles"
    ],
    "note": "Fourteen selected commands request OPcache tracing JIT; one selected binarytrees profile explicitly disables JIT. A later exact-flag runtime audit confirms OPcache JIT is available/enabled; it is corroboration, not per-sample historical state.",
    "sources": [
      "https://www.php.net/manual/en/features.gc.php",
      "https://www.php.net/manual/en/opcache.configuration.php"
    ]
  },
  "lua": {
    "platform": "runtime",
    "runtime": "PUC Lua bytecode interpreter",
    "execution": [
      "interpreted"
    ],
    "typing": "dynamic",
    "style": [
      "imperative",
      "functional"
    ],
    "memory": [
      "gc"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://www.lua.org/manual/5.4/manual.html#2.5"
    ]
  },
  "bqn": {
    "platform": "runtime",
    "runtime": "CBQN interpreter on ARM64",
    "execution": [
      "interpreted"
    ],
    "typing": "dynamic",
    "style": [
      "array",
      "functional"
    ],
    "memory": [
      "rc",
      "gc"
    ],
    "note": "The measured Apple ARM64 CBQN runs its interpreter; CBQN native-code compilation documented for x86 is not assumed on this machine. Reference counting is supplemented by tracing GC.",
    "sources": [
      "https://github.com/dzaima/CBQN/blob/master/src/README.md",
      "https://mlochbaum.github.io/BQN/implementation/vm.html"
    ]
  },
  "k": {
    "platform": "runtime",
    "runtime": "Growler K interpreter",
    "execution": [
      "interpreted"
    ],
    "typing": "dynamic",
    "style": [
      "array",
      "functional",
      "imperative"
    ],
    "memory": [
      "rc"
    ],
    "note": "Growler K array interpreter; its value retain/release memory model is reference counted. This is not K running on JVM or a JavaScript K implementation.",
    "sources": [
      "https://github.com/growler/k"
    ]
  },
  "mojo": {
    "platform": "native",
    "runtime": "Mojo / MLIR / LLVM",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative"
    ],
    "memory": [
      "owned",
      "manual"
    ],
    "note": "Ownership and prompt destructors coexist with explicit unsafe-pointer allocation. The compiled cohort has static types; Python interoperability is not the measured backend.",
    "sources": [
      "https://docs.modular.com/mojo/manual/values/ownership/"
    ]
  },
  "futhark": {
    "platform": "native",
    "runtime": "Futhark CPU C backend",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "array",
      "functional"
    ],
    "memory": [
      "rc"
    ],
    "note": "CPU backend in this cohort, not GPU/OpenCL execution. Array buffers are reference counted; uniqueness checking enables reuse and does not imply tracing GC.",
    "sources": [
      "https://futhark-lang.org/blog/2021-08-02-value-representation.html"
    ]
  },
  "swift": {
    "platform": "native",
    "runtime": "Swift / LLVM",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "rc"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://docs.swift.org/swift-book/documentation/the-swift-programming-language/automaticreferencecounting/"
    ]
  },
  "haskell": {
    "platform": "native",
    "runtime": "GHC native compiler/runtime",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "functional"
    ],
    "memory": [
      "gc"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://www.haskell.org/definition/haskell2010.pdf",
      "https://ghc.gitlab.haskell.org/ghc/doc/users_guide/runtime_control.html"
    ]
  },
  "ocaml": {
    "platform": "native",
    "runtime": "OCaml native compiler/runtime",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "functional",
      "imperative",
      "object"
    ],
    "memory": [
      "gc"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://ocaml.org/about",
      "https://ocaml.org/manual/5.3/intfc.html"
    ]
  },
  "matlab": {
    "platform": "runtime",
    "runtime": "MATLAB native runtime / JIT",
    "execution": [
      "jit"
    ],
    "typing": "dynamic",
    "style": [
      "array",
      "imperative",
      "object"
    ],
    "memory": [
      "rc",
      "cycles"
    ],
    "note": "Saved policy says base MATLAB R2026b with standard JIT. Reference-counted values and cycle handling are distinct from the optional R2026b beta collector; beta use is not assumed.",
    "sources": [
      "https://www.mathworks.com/help/matlab/matlab_oop/object-life-cycle-management.html"
    ]
  },
  "erlang": {
    "platform": "beam",
    "runtime": "Erlang / BEAM JIT",
    "execution": [
      "jit"
    ],
    "typing": "dynamic",
    "style": [
      "functional"
    ],
    "memory": [
      "gc",
      "rc"
    ],
    "note": "BEAM JIT and per-process tracing heaps, plus reference-counted large binaries outside those heaps.",
    "sources": [
      "https://www.erlang.org/doc/system/beamjit.html",
      "https://www.erlang.org/doc/apps/erts/garbagecollection.html",
      "https://www.erlang.org/doc/system/binaryhandling.html"
    ]
  },
  "lisp": {
    "platform": "runtime",
    "runtime": "SBCL precompiled native saved core",
    "execution": [
      "aot"
    ],
    "typing": "dynamic",
    "style": [
      "functional",
      "imperative",
      "object"
    ],
    "memory": [
      "gc"
    ],
    "note": "SBCL compile-file/save-core happened before timing, so this series is AOT despite dynamic typing.",
    "sources": [
      "https://www.sbcl.org/manual/"
    ]
  },
  "racket": {
    "platform": "runtime",
    "runtime": "Racket CS / Chez precompiled native modules",
    "execution": [
      "aot"
    ],
    "typing": "dynamic",
    "style": [
      "functional",
      "imperative",
      "object"
    ],
    "memory": [
      "gc"
    ],
    "note": "Racket CS modules were precompiled by raco make; CS stores native machine code. Dynamic Racket is measured, not Typed Racket.",
    "sources": [
      "https://docs.racket-lang.org/guide/performance.html"
    ]
  },
  "zig": {
    "platform": "native",
    "runtime": "Zig / LLVM",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative"
    ],
    "memory": [
      "manual"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://ziglang.org/documentation/master/#Memory"
    ]
  },
  "odin": {
    "platform": "native",
    "runtime": "Odin / LLVM",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative"
    ],
    "memory": [
      "manual"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://odin-lang.org/docs/overview/#allocators"
    ]
  },
  "roc": {
    "platform": "native",
    "runtime": "Roc LLVM alpha4 compiler/runtime",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "functional"
    ],
    "memory": [
      "rc"
    ],
    "note": "Measured LLVM alpha4 compiler; newer compiler implementations do not replace the historical runtime identity.",
    "sources": [
      "https://www.roc-lang.org/docs/main/langref/lists/",
      "https://github.com/roc-lang/roc/blob/main/Glossary.md"
    ]
  },
  "elm": {
    "platform": "javascript",
    "runtime": "Elm generated JavaScript on Node.js / V8",
    "execution": [
      "jit"
    ],
    "typing": "static",
    "style": [
      "functional"
    ],
    "memory": [
      "gc"
    ],
    "note": "Statically typed functional Elm compiled to JavaScript, then executed by Node/V8. Compile-to-JavaScript is not native AOT execution.",
    "sources": [
      "https://guide.elm-lang.org/",
      "https://nodejs.org/en/learn/getting-started/the-v8-javascript-engine"
    ]
  },
  "csharp": {
    "platform": "dotnet",
    "runtime": ".NET CoreCLR JIT",
    "execution": [
      "jit"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "gc"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://learn.microsoft.com/en-us/dotnet/standard/clr",
      "https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/fundamentals"
    ]
  },
  "csharp-aot": {
    "platform": "dotnet",
    "runtime": ".NET NativeAOT runtime",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "gc"
    ],
    "note": ".NET NativeAOT includes native code and supporting .NET runtime/GC. It remains in the .NET family and has no execution-time JIT.",
    "sources": [
      "https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/"
    ]
  },
  "fsharp": {
    "platform": "dotnet",
    "runtime": ".NET CoreCLR JIT",
    "execution": [
      "jit"
    ],
    "typing": "static",
    "style": [
      "functional",
      "imperative",
      "object"
    ],
    "memory": [
      "gc"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://learn.microsoft.com/en-us/dotnet/fsharp/what-is-fsharp",
      "https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/fundamentals"
    ]
  },
  "fsharp-aot": {
    "platform": "dotnet",
    "runtime": ".NET NativeAOT runtime",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "functional",
      "imperative",
      "object"
    ],
    "memory": [
      "gc"
    ],
    "note": ".NET NativeAOT includes native code and supporting .NET runtime/GC. It remains in the .NET family and has no execution-time JIT.",
    "sources": [
      "https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/"
    ]
  },
  "ada": {
    "platform": "native",
    "runtime": "GNAT / GCC",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object"
    ],
    "memory": [
      "manual",
      "owned"
    ],
    "note": "Explicit access-type deallocation plus controlled finalization/RAII; no default tracing GC.",
    "sources": [
      "https://www.adaic.org/resources/add_content/standards/12rm/html/RM-7-6.html",
      "https://www.adaic.org/resources/add_content/standards/12rm/html/RM-13-11-2.html"
    ]
  },
  "pascal": {
    "platform": "native",
    "runtime": "Free Pascal",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object"
    ],
    "memory": [
      "manual",
      "rc"
    ],
    "note": "Free Pascal managed strings/dynamic arrays use reference counting; ordinary class/pointer allocations have explicit lifetimes.",
    "sources": [
      "https://www.freepascal.org/docs-html/ref/refsu47.html",
      "https://www.freepascal.org/docs-html/ref/refsu14.html"
    ]
  },
  "fortran": {
    "platform": "native",
    "runtime": "GNU Fortran / GCC",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "array",
      "object"
    ],
    "memory": [
      "manual",
      "owned"
    ],
    "note": "Allocatable variables can be automatically deallocated at scope exit; pointer/explicit allocations require separate lifetime management.",
    "sources": [
      "https://j3-fortran.org/doc/year/18/18-007r1.pdf"
    ]
  },
  "dart": {
    "platform": "runtime",
    "runtime": "Dart native AOT runtime",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "gc"
    ],
    "note": "Dart native AOT executable retains the Dart tracing-GC runtime. The separate JIT series shares this runtime family.",
    "sources": [
      "https://dart.dev/overview"
    ]
  },
  "dart-jit": {
    "platform": "runtime",
    "runtime": "Dart VM JIT",
    "execution": [
      "jit"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "gc"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://dart.dev/overview"
    ]
  },
  "smalltalk": {
    "platform": "runtime",
    "runtime": "Pharo Cog/Spur VM",
    "execution": [
      "jit"
    ],
    "typing": "dynamic",
    "style": [
      "object"
    ],
    "memory": [
      "gc"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://github.com/OpenSmalltalk/opensmalltalk-vm"
    ]
  },
  "d": {
    "platform": "native",
    "runtime": "LDC / LLVM / D runtime",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "gc",
      "manual",
      "owned"
    ],
    "note": "D runtime tracing GC coexists with manual allocation and deterministic struct destruction; @nogc is available but not assumed for the whole cohort.",
    "sources": [
      "https://dlang.org/spec/garbage.html",
      "https://dlang.org/spec/struct.html#struct-destructor"
    ]
  },
  "r": {
    "platform": "runtime",
    "runtime": "GNU R bytecode interpreter",
    "execution": [
      "interpreted"
    ],
    "typing": "dynamic",
    "style": [
      "array",
      "functional",
      "imperative",
      "object"
    ],
    "memory": [
      "gc"
    ],
    "note": "GNU R bytecode JIT compiles expressions to bytecode interpreted by the R VM; it is not a native-code JIT like V8 or HotSpot.",
    "sources": [
      "https://cran.r-project.org/doc/manuals/r-release/R-ints.html",
      "https://stat.ethz.ch/R-manual/R-devel/library/compiler/html/compile.html"
    ]
  },
  "apl": {
    "platform": "runtime",
    "runtime": "GNU APL interpreter",
    "execution": [
      "interpreted"
    ],
    "typing": "dynamic",
    "style": [
      "array",
      "imperative"
    ],
    "memory": [
      "rc"
    ],
    "note": "GNU APL interpreter, not Dyalog or another APL runtime. Automatic value ownership/reference counts do not imply a language ownership type system.",
    "sources": [
      "https://www.gnu.org/software/apl/apl.html"
    ]
  },
  "uiua": {
    "platform": "runtime",
    "runtime": "Uiua interpreter",
    "execution": [
      "interpreted"
    ],
    "typing": "dynamic",
    "style": [
      "array",
      "functional"
    ],
    "memory": [
      "rc"
    ],
    "note": "Dynamically typed stack/array interpreter. Its copy-on-write array backing uses reference counting; Rust implementation details do not make Uiua statically typed.",
    "sources": [
      "https://github.com/uiua-lang/uiua/blob/main/src/cowslice.rs",
      "https://www.uiua.org/"
    ]
  },
  "crystal": {
    "platform": "native",
    "runtime": "Crystal / LLVM / Boehm GC",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object"
    ],
    "memory": [
      "gc"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://crystal-lang.org/reference/latest/syntax_and_semantics/memory.html"
    ]
  },
  "c3": {
    "platform": "native",
    "runtime": "C3 / LLVM",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative"
    ],
    "memory": [
      "manual"
    ],
    "note": "Explicit allocator/free model; scoped defer cleanup is not an ownership type system.",
    "sources": [
      "https://c3-lang.org/language-common/memory/"
    ]
  },
  "clojure": {
    "platform": "jvm",
    "runtime": "Clojure on OpenJDK HotSpot JVM",
    "execution": [
      "jit"
    ],
    "typing": "dynamic",
    "style": [
      "functional"
    ],
    "memory": [
      "gc"
    ],
    "note": "Measured implementation identified by the saved build/run reports; language traits describe its standard language/runtime model.",
    "sources": [
      "https://clojure.org/about/features",
      "https://clojure.org/about/jvm_hosted"
    ]
  },
  "nim": {
    "platform": "native",
    "runtime": "Nim C backend / Clang / ORC",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object",
      "functional"
    ],
    "memory": [
      "rc",
      "cycles",
      "owned"
    ],
    "note": "The measured C backend uses ORC: reference counting plus trial-deletion cycle collection and deterministic destructors. ORC is not a global tracing collector.",
    "sources": [
      "https://nim-lang.org/2.0.4/mm.html",
      "https://nim-lang.org/docs/destructors.html"
    ]
  },
  "gleam": {
    "platform": "beam",
    "runtime": "Gleam on Erlang / BEAM JIT",
    "execution": [
      "jit"
    ],
    "typing": "static",
    "style": [
      "functional"
    ],
    "memory": [
      "gc",
      "rc"
    ],
    "note": "Statically typed functional language using the measured Erlang target and BEAM load-time JIT; its available JavaScript target was not measured. BEAM heaps use tracing GC and large binaries use reference counts.",
    "sources": [
      "https://gleam.run/",
      "https://www.erlang.org/doc/apps/erts/garbagecollection.html",
      "https://www.erlang.org/doc/system/binaryhandling.html"
    ]
  },
  "v": {
    "platform": "native",
    "runtime": "V C backend / Clang / Boehm GC",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative"
    ],
    "memory": [
      "gc"
    ],
    "note": "Saved production builds use V C backend with Clang and default Boehm tracing GC. Neither experimental autofree nor -gc none is assumed.",
    "sources": [
      "https://docs.vlang.io/memory-management.html",
      "https://github.com/vlang/v/wiki/FAQ"
    ]
  },
  "pony": {
    "platform": "native",
    "runtime": "Pony native compiler/runtime",
    "execution": [
      "aot"
    ],
    "typing": "static",
    "style": [
      "imperative",
      "object"
    ],
    "memory": [
      "gc",
      "rc",
      "cycles"
    ],
    "note": "Actor-based, statically typed native language with reference capabilities. Actor-local heaps use tracing GC; cross-actor references and actor cycles use runtime collection. Reference capabilities are not manual allocation or RAII ownership.",
    "sources": [
      "https://www.ponylang.io/blog/2017/05/an-early-history-of-pony/",
      "https://www.ponylang.io/media/papers/OGC.pdf",
      "https://www.ponylang.io/media/papers/a_string_of_ponies.pdf",
      "https://www.ponylang.io/use/compiler/runtime-options/"
    ]
  },
  "elixir": {
    "platform": "beam",
    "runtime": "Elixir 1.20.4 on Erlang/OTP 29 / ERTS 17.1 BEAM JIT",
    "execution": [
      "jit"
    ],
    "typing": "dynamic",
    "style": [
      "functional"
    ],
    "memory": [
      "gc",
      "rc"
    ],
    "note": "BEAM JIT with per-process tracing heaps and reference-counted large binaries; identical source aliases remain independently measured.",
    "sources": [
      "https://www.erlang.org/doc/system/beamjit.html",
      "https://www.erlang.org/doc/apps/erts/garbagecollection.html",
      "https://www.erlang.org/doc/system/binaryhandling.html"
    ]
  }
};
