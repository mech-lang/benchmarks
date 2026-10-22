# F# local implementation review

This static review covers seventeen complete local/derived source bundles shared
by twenty-one profiles across nine workloads. Nine unchanged upstream profiles
are protected. No source or timing from those profiles is replaced. The locally
ported and typed-output sources remain separate from their original submissions;
`static-output` means ordinary typed output formatting, not precomputed answers.

| Workload | Source findings and pending native work |
| --- | --- |
| Binary trees | The local typed-output copy materializes an array of every tree checksum before summing it. Streaming and checked-accumulator drafts remove that intermediate vector while retaining all actual leaf/interior nodes, temporary trees, stretch tree and long-lived root. All eight depth jobs and their bound remain. Output, allocation/lifetime and overflow behavior need native validation. |
| Fannkuch | The simple copy uses ordinary arrays and ref-cell swaps. The pointer version assigns uniform `factorial/processor-count` chunks; source arithmetic drops any remainder, and zero-sized tasks still inspect an initial permutation. Global rank parity, small-n pointer bounds, terminal transitions and full factorial coverage require a repair and native witness. No candidate is claimed correct from this inspection. |
| FASTA | The retained design already uses pooled bounded blocks, serial naive LCG generation and parallel lookup. Source lookup uses `>=`; threshold equality, zero-size `(n-1)` formulas, publication of block objects and queue memory need native boundary checks. The ordered fixed ALU block copying is already an optimization, not a naive implementation. |
| K-nucleotide | Four local files use two complete designs: substring dictionaries or seven rolling-key dictionaries/tasks. The parser accepts a THREE prefix, trims data and does not correctly model all comments/missing-record boundaries. Exact header/EOF parsing, byte pre-encoding and the standard byref dictionary-update API are candidates. The rolling key uses ACTG order and explicitly decodes lexical ties. All seven general maps must remain. Original authorship/license gaps stay unresolved rather than inferred from a local header. |
| Mandelbrot | Two-lane generic Vector arithmetic and parallel rows already exist. Both sources index `data.[header-length]` before pinning; N=0 needs separate qualification. Native vector width/lowering, storage overlap and tail masks require inspection. `pcrb[y]+0.5` yields the intended imaginary coordinate; the 49-counter loop alone does not prove missing work. |
| N-body | A scalar record/list design precomputes the ten body pairs; another uses stack-allocated Vector256 spans and explicit lanes. Source API names do not establish ARM SIMD lowering. Stack lifetime, initialization of Sun vectors, generated local-init behavior and the struct-tuple loop pattern need actual compilation/IL inspection before alleging a defect. Neither design is described as naive. |
| Pi digits | General GMP P/Invokes leave the spigot, both digit extractions and output in F#. No mpz-clear binding or call is present. Normal/error-path cleanup, ABI, zero/partial blocks and the fixed counter buffer need review. All authored declarations remain application source. |
| Regex | Ordinary .NET regex controls retain nine counts and five ordered substitutions. Serial and parallel drafts use the standard Regex.Count API rather than Match objects/NextMatch. Byte-preserving input and JIT versus NativeAOT regex lowering remain separate unqualified concerns; the performance drafts do not silently claim to repair them. |
| Spectral norm | The local pointer design already reuses three vectors and performs forty dense products. Its barrier uses ProcessorCount while Async.Parallel caps jobs at eight. A worker-count draft caps parties by positive dimension and eight. This addresses source-derived empty-range and oversubscription paths; no native failure or speedup has been observed here. |

The five [source drafts](../candidates-v1.json) are uncompiled and untimed. They
preserve original contributors/notices and add an explicit local-change license.
Their prospective SDK is pinned to 10.0.401 with target net10.0; restoration,
clean JIT/NativeAOT builds, shared corpus outputs, required-work witnesses, native
source measures and three full-process timing samples remain required. No build
or native subject starts alongside the Janet timing cohort.

F# semicolons separate some statements but also occur in arrays, attributes and
records; wrapping nested literals must not create statement counts. `let`/`and`,
computation expressions, expression-return branches and tuple patterns need
native FSharp.Compiler.Service ownership/formatter checks. Raw physical rows,
bytes, gzip and BPE do not certify normalized logical LOC. Source inspection is
not completion of the performance or most-expressive audit.

Primary API references: [checked arithmetic](https://fsharp.github.io/fsharp-core-docs/reference/fsharp-core-operators-checked.html)
and [Regex.Count](https://learn.microsoft.com/en-us/dotnet/api/system.text.regularexpressions.regex.count?view=net-10.0).
These establish available operations, not acceptance or performance of the drafts.
