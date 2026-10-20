# Expressiveness review beyond the first fifteen languages

This is a source-only coverage inventory and review queue, not a declaration that
the remaining implementations are idiomatic or optimal. It examines the retained
application/support descriptions and selected actual sources. It adds no source
count, formatter result, parser acceptance, correctness qualification, timing, or
change to the generated inventory. Candidate changes below are questions to test
in separately authorized experiments.

The snapshot is the [1,063-profile inventory](inventory.json), bound to
`data/benchmarks.json` SHA-256
`fda00e2cd7e1274edf977a1f14989f6bc9178ab95c9c3f56507e3893bf5b98de`.
The inventory file itself has SHA-256
`703c8006b71b2e380b6d0fdc80c00e293ba425aba09aeafd55e3293d41e7744a`.
Later admissions require a new inventory snapshot; the numbers here do not
automatically cover their sources.

## Coverage and ownership

The [first fifteen language reviews and admitted alternatives](README.md) and
the separate [Mech compiler/source review](mech-review.md) already have detailed
coverage. Ruby ZJIT belongs to the Ruby review, not a sixteenth independent source
design. Those reviews keep proposed alternatives distinct from qualified measured
candidates.

The remaining `not-yet-source-performance-reviewed` queue contains **734 profiles
in 44 execution variants and 38 language families**:

- **407 derived/adapted and 27 suite-authored profiles**, across 30 families, need
  the next application idiom review. Their included source-unit hash/role bundles
  comprise **381 distinct bundles**, not 434 independent designs. A bundle is the
  ordered whole-file hashes and roles of included source units; it is not a claim
  of normalized semantic equivalence or of identical application partitions.
- **300 unchanged upstream profiles** remain protected. They can supply reference
  designs and receive byte-preserving runtime/configuration review. Their presence
  in the queue does not authorize rewriting the originals.
- No profile in this remaining queue has ownership classification `unknown`.
  This does **not** mean every original author is known: 134 of the 434 local or
  derived profiles have `original_lineage_status: unresolved`, 266 have `cited`,
  and 34 have `suite-authored`. These are different evidence fields. The catalog's
  46 ownership-unknown profiles are in the already reviewed scopes.

Counts weight retained profiles, including source-sharing modes. None of these
434 profiles currently declares `timing_alias_of`; source identity alone must not
collapse separate runtime observations. Conversely, a future timing alias must
not become an additional independent sample merely because it has another label.
The inventory's exact per-profile ownership, citations and predecessor evidence
remain authoritative. Missing original lineage never establishes AI authorship,
an AI tool, a model family, or an exact serving model. The recent BQN/Nim model
evidence does not transfer to archived ports or their ancestors. The two corrected
MATLAB regex sources retain their conservative unknown archival tool/model status.

## Complete remaining local/derived pools

“All ten” means binarytrees, fannkuchredux, fasta, knucleotide, mandelbrot, nbody,
pidigits, regexredux, revcomp and spectralnorm. `P / B` gives local/derived profiles
and distinct included source-unit bundles across the listed modes. `U` gives
protected upstream profiles in that family. The last column is an initial review
question, not a confirmed defect. Each row expands to the exact profile keys,
source hashes, runtime modes and workload pools in [the inventory](inventory.json).

| Family / execution variants | P / B | U | Local/derived workloads | First source review question |
| --- | ---: | ---: | --- | --- |
| C3 | 20 / 20 | 0 | All ten | Generic buffer/FFI modules versus in-application traversal and error handling; original lineage unresolved for all 20. |
| Crystal | 20 / 20 | 0 | All ten | Standard collection/regex idioms versus hand-written traversal, packed blocks, and literal layout; preserve cited predecessors. |
| C# / C# AOT | 20 / 10 | 19 | All except binarytrees | Review ten shared sources once, retain mode-specific observations, and compare native arrays/standard library idioms against the adapted design. |
| Dart / Dart JIT | 36 / 18 | 0 | All ten | Isolate orchestration, typed buffers and copied work/results versus simpler sequential or persistent-worker designs. |
| Elm | 11 / 11 | 0 | All ten | Keep the worker/port wrapper visible; distinguish genuine functional collection expressions from physical layout. All original lineage remains unresolved. |
| Erlang | 7 / 7 | 7 | binarytrees, fasta, knucleotide, mandelbrot, regexredux | ETS/process ownership, message/output ordering and clause/guard counting; keep the seven originals protected. |
| Fortran | 16 / 16 | 0 | All ten | Continuation lines, declarations, `end` syntax and true whole-array expressions; distinguish source layout from scalar algorithm changes. |
| F# / F# AOT | 21 / 17 | 9 | All except revcomp | Shared-mode sources, pipeline/tuple ownership, allocation and output adaptation; four profiles have unresolved original lineage. |
| Gleam | 20 / 20 | 0 | All ten | Exact Erlang bridge surface versus Gleam-owned loops, pattern matches and byte assembly; all original lineage unresolved. |
| Haskell | 5 / 5 | 14 | binarytrees, fasta, knucleotide, mandelbrot | Preserve strict allocation/work guards while considering strict folds, unboxed storage and composition; protect the 14 originals. |
| JavaScript | 1 / 1 | 17 | pidigits | Compare the derived two-extraction spigot with its exact predecessor; do not broaden the source rewrite to the other 17 originals. |
| Julia / Julia AOT | 17 / 17 | 17 | All ten, local records in AOT mode | Separate AOT module/entry packaging from an algorithm alternative; native owner-count qualification already exists for these exact sources. |
| Kotlin | 20 / 10 | 0 | All ten | Compact/optimized pairs share included application source; native PSI accounting already addresses many packed statements. Review idioms rather than counting labels as alternatives. |
| Lean 4 | 23 / 23 | 0 | All ten | Native primitive boundary, mutable array/byte paths, proofs/types versus runtime work, and helper/API declaration scope. |
| Common Lisp | 8 / 8 | 10 | binarytrees, fasta, knucleotide, mandelbrot, pidigits, regexredux, revcomp | Reader forms, declarations and `loop` clauses; mutable typed arrays versus avoidable intermediate objects. Protect ten originals. |
| Lua / LuaJIT | 4 / 4 | 24 | pidigits, local records in Lua mode | GMP primitive boundary and extraction/refinement choices in the four derived spigots; protect the remaining 24 mode profiles. |
| Luau / Luau JIT | 22 / 11 | 0 | All ten | One application review per shared source, including host/GMP/regex role boundaries and temporary integer/byte allocations. |
| Mojo | 20 / 20 | 0 | All ten | Standard-library-like local bindings, generic regex operations versus application loops, move/copy behavior, and native map API ownership; 17 unresolved original lineages. |
| OCaml | 6 / 6 | 12 | binarytrees, fannkuchredux, fasta, knucleotide | Sequence separators versus record fields, simultaneous bindings, mutable buffers and task orchestration; protect 12 originals. |
| Odin | 13 / 13 | 2 | All except nbody | Embedded generic I/O/PCRE2 bindings versus workload loops; dynamic arrays and allocator costs. Eleven unresolved original lineages. |
| Pascal | 13 / 13 | 2 | All except revcomp | Declaration/FFI surface, `begin/end`, record/array literals and imperative sequence ownership; two unresolved original lineages. |
| Pony | 20 / 20 | 0 | All ten | Actor/message scaffolding, native binding surface and near-identical candidate structure; original lineage unresolved for 12 profiles. |
| Racket | 4 / 4 | 16 | knucleotide, pidigits, spectralnorm | Reader-level forms and standard `for`/hash abstractions; keep required per-key updates and all 16 original profiles. |
| Roc | 11 / 11 | 0 | All ten | Embedded general regex/big-integer code versus standard library availability, immutable byte/list construction and platform I/O. All original lineage unresolved. |
| Rust | 2 / 2 | 17 | fannkuchredux, fasta | Separate the NEON and floating-CDF adaptations from unchanged upstream sources; preserve permutation coverage, RNG transitions and numeric behavior. |
| Scala | 10 / 10 | 0 | All ten | Existing native source-owner/work reviews are substantial; next examine executor/closure/boxing scaffolding and idiomatic arrays without repeating those audits. |
| Swift | 18 / 18 | 0 | All ten | Generic GMP/PCRE API and resource lifetime surface, arrays/SIMD/COW behavior and duplicated scalar operations. |
| TypeScript | 10 / 10 | 0 | All ten | Existing native accounting/work reviews are substantial; next compare object/type scaffolding and typed-array designs while retaining source-owned loops. |
| V | 20 / 20 | 0 | All ten | Real array literals/coordinate loops, locally authored helpers and native library scope; eleven suite-authored and nine derived records. |
| Zig | 16 / 16 | 0 | All ten | Embedded process/I/O adaptation, genuine SIMD/vector expressions, literal rows and allocator scope; six unresolved original lineages. |

The other eight families have **no local/derived application pool in this
snapshot**: C (18 protected profiles), Chapel (14), C++ (18), Go (20), Java (17),
Perl (14), PHP (15) and Python (18). Together these are 134 of the 300 protected
profiles; another 166 protected profiles sit beside the derived pools above.
They are not omissions from the database-wide inventory. Python's native logical
owner qualification concerns measurement of protected source, not permission to
rewrite it.

## Highest-value next passes and concrete source evidence

### 1. Compare library and host boundaries before ranking concision

Review **Mojo, Gleam, Luau, Lean 4, Elm, Roc and C3** together first. A lower
application count can reflect a legitimately more capable library, a reusable
binding excluded by policy, or an embedded library that another port carries in
its application file. Those are distinct explanations. The current roles are
preserved; this pass proposes neither a new exclusion nor a rule requiring each
language to hand-write the same library operation.

These examples were read directly from the exact catalog `files[sha256].code`;
short hashes identify the full source objects in the inventory/catalog. Some
Gleam original build paths are labels in the catalog, so use the hash-bound code
instead of assuming the old temporary path is present.

| Exact profile / source | Observed source ownership | Next review artifact |
| --- | --- | --- |
| `regexredux:mojo-regexredux-compact`, application `e7bcedb86784…`, lines 1–27; support `regex.mojo` `708ab2b2a0d4…`, `native.c` `e5c39f5ccc45…` | The application owns nine pattern calls and five ordered substitutions. Its excluded generic service exposes count/global replacement; C lines 55–73 own match traversal and invoke PCRE2 global substitution. | Per-export primitive map, case/offset/empty-match contract and application/submitted size comparison. Keep generic regex roles unless exact evidence supports a separate accounting proposal. |
| `regexredux:gleam-regexredux-compact`, `38e1162afbc7…`, lines 5–30; support `clbg_regex_ffi.erl` `9e20cd3bd0c8…`, lines 3–10 | Count/replace/substitution traversal remains in Gleam. The excluded Erlang service compiles a supplied pattern and returns one indexed match. | Compare Gleam `BitArray` slicing/parts accumulation and generic OTP API alternatives, while retaining the full workload loop in the application. |
| `regexredux:lean4-regexredux-native-v1`, `7c459f6bc218…`, lines 3–55 | Extern declarations provide compile/find primitives; Lean owns count, replacement assembly, pattern iteration and the ordered substitutions. | Reconcile declaration owners with runtime expressions; inspect byte-array allocation/uniqueness and reuse against [the required-work review](../../lean4/required-work-v1/review.json). |
| `pidigits:luau-pidigits-v1`, `30d5cfbd368d…`, lines 4–27; `Bigint.cpp` `69dcfe810981…`, lines 10–68 | Both stability extractions, term refinement and output decisions are in Luau. Excluded GMP arithmetic primitives allocate result integers. The shared `Host.cpp` handles loading/JIT/arguments/I/O. | Review integer reuse/temporary allocations and one whole host API ledger, then bind the same source review to VM/JIT modes. See [required work](../../luau/required-work-v2/review.json). |
| `regexredux:regexredux-elm-idiomatic`, `7dbc3044b242…`, lines 1–33; runner `e8775fd5c317…`, lines 1–20 | `Platform.worker`/ports are in application source. The excluded Node runner performs source-independent dispatch and byte I/O; the regex/list pipeline stays in Elm. | Separate worker boilerplate from the actual collection expressions. Confirm byte/string behavior and library regex semantics without moving application updates into the runner. |
| `regexredux:regexredux-roc-idiomatic`, `a1d38589c1f0…`, lines 7–142 and 143–162 | A general pattern parser/matcher/count/replace engine is embedded in the counted application before workload orchestration. A 161 retained-LOC result therefore includes a library that other ports call. | Investigate a legitimate pinned general regex library or a separately reviewed reusable extraction. Keep the existing source/count unchanged until the genericity and policy are reviewed; do not replace the engine with benchmark-pattern shortcuts. |
| `regexredux:c3-regexredux-compact`, `d142eea8a4a5…`, lines 20–101 | PCRE2/buffer declarations are separate support; explicit compile/error/count/replacement loops remain in the application. | Compare the operation boundary with Mojo and Gleam, and check whether standard C3 facilities can express the same generic operations with less authored scaffolding. |

Some original Luau/Gleam helper comments say their source is “counted”; current
application roles exclude those generic units. These historical comments are not
the present partition rule. [Source metrics](../../../docs/source-metrics.md)
shows both submitted and application scopes and binds the actual partition bytes;
it must remain possible to inspect the full submitted burden. The pending
[Ruby embedded-support proposal](../../source-normalization/ruby-support-v1/README.md)
is a useful example of the separate, hash-bound review needed before changing a
boundary, not approval to apply the same exclusion to these languages.

There is also a **case-policy reconciliation question**, separate from the helper
boundary: Elm regex line 29 explicitly uses `caseInsensitive=True`; Roc line 153
passes `Bool.true` to count matching; Odin's retained PCRE2 source
`15107e77101e…` line 75 uses `compile(pattern, true)`. The corrected
[MATLAB intake](../../matlab/optimization-v1/regex-source-intake-review.md) records
a case-sensitive API correction with specific retained counterexamples. The
published Game regex description gives the pattern/action sequence without
explicit case-mode prose. Canonical FASTA agreement can therefore conceal a
mixed-case-fixture difference. The next review must reconcile exact reference
APIs, historical fixtures and the accepted workload contract across these ports.
This document does not transfer MATLAB's qualification, invalidate another
cohort, quarantine a profile, or claim a case-mode sentence exists in that prose.

### 2. Review source-sharing labels and syntax ownership together

The clear source-sharing pools are C# JIT/AOT (**20 local profiles / 10 included
bundles**), Dart AOT/JIT (**36 / 18**), Luau VM/JIT (**22 / 11**) and Kotlin
compact/optimized (**20 / 10**). F# JIT/AOT has **21 / 17**. These numbers describe
source identity, not equal timings or proof that every support file, compiler
input, flag or process path is the same. Compare the complete submitted/support
bundle and execution mode after grouping the application.

Kotlin n-body `kotlin-nbody-compact` uses multiple independent declarations on
line 17, paired mutations on lines 34–36 and three position updates in the loop
on line 41 of `a5280a8cee35…`. These must remain multiple owners after packing.
Its lines 44–49 are one array initializer with five body entries; wrapping those
rows cannot create additional statements. The current 77 retained units for this
56-line file already demonstrate why physical LOC is not the intended logical
measure. The [native PSI closure review](../../kotlin/source-counts-v3/run-v1-closure-review.json)
and [source-count work](../../kotlin/source-counts-v3/README.md) should be reused,
not described as absent merely because an idiom review is still pending.

Julia AOT's 17 derived records are packaging/entry adaptations alongside 17
protected Julia records. Start with the [entry-dispatch review](../../julia-aot/entry-dispatch-v1/README.md)
and [exact native logical-owner qualification](../../source-normalization/v2/README.md).
Do not infer a new algorithm from the AOT profile name or treat those native
counts as a deep performance/idiom review of the whole family.

Scala and TypeScript each have ten local sources, plus substantial existing
[Scala work/source review](../../scala/compiled-applications-v1/README.md),
[Scala native owner qualification](../../scala/source-counts-v1/canonical-owner-review-v1/README.md),
[TypeScript required-work review](../../typescript/required-work-v1/static-review-v1.json)
and [TypeScript source-count review](../../typescript/source-counts-v1/README.md).
The remaining question is the design choice. Scala spectral norm
`4b945cbdfb8c…` lines 13–35 wraps each row partition in a submitted
`Callable[Unit]` and waits on its future; consider simpler reusable scheduling or
standard array idioms as new candidates, retaining all forty products. TypeScript
n-body `e7a4ecb4b50f…` lines 15–32 declares a seven-field class and a seven-argument
copying constructor. A compact typed representation is a concrete source-size
candidate, but requires numerical/work checks and new timing before any speed
claim. Its multi-line constructor calls are expressions, not one logical unit per
argument row.

### 3. Review orchestration and representation before deleting helpers

Pony binary trees `9fe1b9d288f2…` lines 21–39 schedules one tree at a time through
the `Worker._one` behavior; lines 56–63 create a worker partition even when
`_pending = 1`. A synchronous loop within a bounded worker behavior or different
partitioning is worth qualification, with actor fairness, allocation and the
long-lived tree preserved. Actor code expresses actual application scheduling;
it cannot simply be removed from counted source as generic runtime support.
Compact/optimized labels and equal counts in several Pony workloads do not
establish distinct designs; compare the exact bodies and submitted bundles first.

Dart spectral norm `41ae588b3f16…` lines 18–42 creates full-length result buffers
for row slices, and lines 95–99 copy returned slices into the output reference.
The source uses persistent isolate/message machinery. Review copy/allocation and
sequential or persistent-worker alternatives together; source brevity and runtime
speed can favor different candidates. Do not exclude its workload-specific
partitioning, callback bodies or result placement as generic host code.

Swift pi `1900605f666e…` lines 18–43 allocates five GMP objects and explicitly
clears/deallocates each; lines 45–64 implement extraction, emission refinement and
term updates. A reusable integer wrapper may reduce surface syntax, but deciding
whether it is an excluded generic library requires an exact API/source partition
review. It must not swallow the spigot transitions. The same question should
drive the remaining Lua, Crystal, C#, Odin and Pascal pi reviews rather than
assuming every explicit arithmetic call is avoidable verbosity.

### 4. Preserve meaningful concise syntax and retained work guards

Several concrete sources are useful normalization fixtures even before a new
idiomatic candidate exists:

- **Literal layout:** V n-body `ca63bec8caf4…` lines 14–22 returns a nested body
  array; Zig n-body `0d5f3bc93014…` lines 92–98 initializes a `[5][7]f64` table;
  Fortran n-body `ca109da051d6…` lines 22–53 uses continuation lines for body
  constructors. The initializer/constructor remains an expression when wrapped.
  Zig's `@Vector`, `@reduce` and vector arithmetic at lines 25–38 and 60–77 are
  real native vector operations, not hidden independent source statements to
  unroll for counting.
- **Binding versus sequencing:** F# regex `00657dd8b5e7…` lines 25–32 expresses
  the substitution sequence through a list of pairs and `List.fold`. OCaml
  fannkuch `939492655db5…` uses semicolons both inside record fields (lines 14–16)
  and between executed mutations (lines 32–35); its `let … and …` bindings and
  packed loop at line 64 need grammar ownership, not delimiter splitting. F#'s
  `static-output` source name refers here to formatting adaptation: the read,
  regex work and replacements are plainly performed. It is not evidence of a
  precomputed-output shortcut.
- **Reader forms and clauses:** Racket k-nucleotide `c7a12cba5471…` lines 8–16
  owns a per-window hash update inside a `for` form; lines 19–25 wrap one output
  expression across lines. Common Lisp reverse complement `6f2b1f43b579…`
  lines 20–26 uses one `loop` form with several clauses. Counting only top-level
  forms would hide the written work; counting every closing parenthesis or
  continuation line would inflate it. Native reader/parser fixtures must
  distinguish definitions, bindings, body expressions and data without evaluating
  macros or source.
- **Functional work preservation:** Haskell binary trees `980fe0e71100…`
  explicitly uses strict trees and the `NOINLINE make`/`OPAQUE leafNil` guards at
  lines 69–73. A shorter composition must preserve allocation and traversal;
  removing these guards because they occupy lines would change the work question.
  The remaining Erlang, Racket and other k-nucleotide ports also need exact
  record-boundary and per-window map-operation fixtures. For example, derived
  Erlang source `8e4825a9b38a…` lines 16–28 recognizes a short `>TH` prefix and
  then reads to EOF, whereas lines 34–44 plainly perform per-window updates.
  That is a concrete intake/parser policy question, not proof about all Erlang
  sources or permission to alter protected originals.

## Completion criteria for the next review tranche

For each family above, produce a ten-workload coverage sheet where a local pool
exists, or an explicit protected-only/not-present entry otherwise. Bind every
review to application and support hashes, included ranges, citations and source
notices. A same-source mode may share the source analysis but needs its own
runtime/configuration conclusion. Distinct hashes establish distinct retained
bytes, not necessarily different algorithms; equal hashes do not establish equal
execution or independent observations.

Each deep review should name the actual current design, identify concrete
standard-library/array/functional/native alternatives, and state which required
work constrains them. Compare all retained candidates in the workload pool before
calling one the smallest or fastest retained candidate. Keep source expressiveness,
runtime configuration, correctness eligibility and sampling evidence separate.
Only a hash-bound, work-qualified, measured intake may add a timed candidate.

For a new logical-owner measure, reuse accepted native readers where present and
qualify additional languages incrementally with pinned parse-only acceptance.
Pair an actual source-derived semicolon/sequence fixture with its unpacked form,
and an actual literal/constructor fixture with its row-wrapped form. Require equal
counts, token/span ownership coverage and explicit handling of unsupported syntax.
Independent written statements need separate owners; a true tuple/destructuring
binding with one initializer remains one binding. Chained assignments follow the
versioned target-owner rule; a single AST node alone does not establish one owner.
A literal's rows and closing syntax add no owners. Genuine composition,
array/glyph primitives and vector operations remain expressions; no policy should
expand their implicit algorithm into scalar source statements. Macro expansion,
generated code and foreign-library internals need explicit scope, not silent
source evaluation. Existing retained rules and formatter gaps remain visible
until that exact language subset is qualified.

Use [physical/retained/formatted/application/submitted metrics](../../../docs/source-metrics.md)
as complementary observations. Bytes include comments and whitespace; gzip is
compression-dependent; BPE reflects its pinned tokenizer and Unicode/language
bias. None of them proves minimal idiomatic source or makes heterogeneous legacy
LOC rules uniform. This queue closes inventory coverage, while the 434-profile
deep idiom review remains open.
