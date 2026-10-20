# Clojure native-reader source owners, v1

The exact-source subset is **qualified** under
`logical-source-owners.clojure-v1`, with [independent review](independent-review.json),
[saved native capture](native-capture.json.gz) and [qualification results](qualification.json).
The initial retained projection covers twenty compact/optimized application
sources and one shared excluded `clbg.support` source. The current catalog
projection also includes the already captured primitive n-body candidate, for
**21 qualified profiles** and **22 retained source units**, without a new native
capture. The proof contains **69 reader jobs**, **22 source units**,
**44 positive/negative fixtures**, nine equivalent fixture pairs and three variants
of an actual retained source. All expected counts/equivalences pass, with zero
unowned significant source tokens. Nine offline regression checks pass.

This separate packet does not replace the [Python/Julia v2 qualification](../v2/README.md)
or change canonical LOC, source roles, correctness eligibility or timings. It is
an exact, versioned source-owner convention, not a whole-language certificate or
proof of universally equal cross-language semantics.

[The separate tool](../../../tools/clojure_logical_source_units.py) has four modes:
`prepare` binds current catalog source/roles; `capture` runs the pinned read-only
helper; `replay` applies the owner policy offline; `review` binds the completed
independent source review. A saved native proof can serve a later catalog
projection only when source jobs, native helper/runtime, policy/tool and per-source
outcomes remain identical. A new source or policy needs separate qualification.

Capture takes the existing `/tmp/mech-clbg-timing.lock` exclusively and without
waiting, before preparing/hash-checking inputs. Run it serially outside timed
workloads. Offline replay needs no JVM. The compact per-profile count and policy
references can be published separately from these full native/source trees.

## Reader evidence and scope

The [official Clojure reader reference](https://clojure.org/reference/reader)
describes forms, comments and reader macros. In particular, a semicolon introduces
a comment: it is not Clojure's equivalent of a Python/Julia statement separator.
Two complete forms can share one physical line without a delimiter between them.
An equivalence fixture must therefore pack complete forms or move whitespace;
replacing a newline with a semicolon can delete the following source.

The [official tools.reader project](https://github.com/clojure/tools.reader)
documents read-eval control and source metadata. We select the pinned official
`org.clojure/tools.reader` **1.6.0** release, whose
[changelog](https://github.com/clojure/tools.reader/blob/v1.6.0/CHANGELOG.md)
and [POM](https://repo.maven.apache.org/maven2/org/clojure/tools.reader/1.6.0/tools.reader-1.6.0.pom)
identify the release and `v1.6.0` source tag. The POM declares EPL-1.0. Its runtime
JAR is SHA-256 `036dc155f3b62548df3da934791aa9d8ec36572a9c664ce2cc7f6551856436be`;
[the download receipt](reader-download.json) pins JAR, POM and source JAR bytes.
Downloads stay in ignored `.build/vendor`; they are not application source or
runtime dependencies of a measured candidate.

The Clojure/JDK restore is separate, using the exact
[runtime restoration plan](../../clojure/optimization-v1/runtime-restoration.json)
and [verified build receipt](../../clojure/optimization-v1/runtime-build.json):
Clojure **1.12.6**, spec.alpha **0.5.238**, core.specs.alpha **0.4.74**, and the
Temurin **25.0.4.1+1** ARM64 Java launcher. The capture pins each JAR and the
launcher. The build receipt supplies the full JDK tree verification; this packet does not
rehash that whole tree on every offline replay.

The helper binds both core and tools.reader `*read-eval*` false, removes custom
and default tag readers, supplies no application source on the classpath, and
never calls input `eval`, `load`, `require`, compiler analysis or `macroexpand`.
Its namespace loads only trusted pinned reader/tooling code. Regex literals
undergo the reader's normal pattern construction; anonymous-function reader
shorthand undergoes normal reader data transformation. Neither is execution of
the benchmark program. Unsupported dispatch, constructors and tags remain
negative fixtures, not a promise that all reader features are qualified.

## Two trees, with an explicit boundary

Tools.reader produces values, not a lossless concrete syntax tree. Quoting,
metadata and `#(...)` may transform the resulting data, and primitive values do
not all carry source metadata. Therefore the packet must retain both:

1. A native `read*` invocation trace with parent IDs, value kinds and original
   UTF-16 start/end positions, including the reader's nested calls. This wraps the
   pinned reader Var, does not replace its grammar functions, and does not expand
   application macros. Arity wrappers can yield duplicate spans; delimiter/EOF
   events are explicit.
2. An independently segmented, lossless source-form tree with UTF-8 spans,
   collection/prefix nodes and all whitespace/comment/string/character tokens.
   This is a **restricted source scanner, not a native lexer and not a lexical
   token-count metric**. Each source-form node must match an exact native read
   event span after leading trivia is removed. Every significant source token
   must have an owner, and concatenating all token bytes must recover the exact
   input. UTF-16-to-UTF-8 conversion must not split a surrogate pair.

The native trace also records the reader's inner list for `#(...)` and numeric
subreads for `%1`/`%2` argument indices. Those exact spans are explicit
reader-internal fragments of the anonymous-function prefix/argument tokens;
they are not additional written statements or new token-count units.

Native read acceptance alone does not establish macro expansion, valid binding
syntax, resolvable class/method names, compilation, type checking, behavior or
required-work correctness. The source walker consequently validates the explicit
supported form shapes and rejects unknown forms/macros, source drift, unsafe
reader settings, unmatched native ranges and contradictory role metadata.
Quoted data is data rather than executable macro input. No whole-language grammar
certificate or semantic-equivalence claim is intended.

## Reviewed ownership rules

The policy ID is `logical-source-owners.clojure-v1`. It follows the v2 idea of
counting written definitions, independent bindings, controls and form statements
rather than physical rows or implicit scalar work. The reviewed decisions are:

| Written source | Owners |
| --- | --- |
| `ns`, `def`, `defn` | One definition/header each. Namespace import/require data and parameter/type annotations add none. |
| A single `defn` body expression | Belongs to the definition owner; a short function, reduction, composition or array primitive is not expanded into hidden operations. “Expression” here is syntactic, not a semantic purity proof; a single side-effecting call can also belong to the definition owner. |
| Multiple written function-body forms | Definition header plus each form statement. Explicit `do` has zero syntax cost and exposes its body forms. A one-expression wrapper cannot hide a written multi-form block. |
| `fn`/`#(...)` inside an expression | A single-expression callback remains an expression, regardless of whether its call has effects. Its explicit blocks, bindings and controls remain visible. The subset supports single-arity `fn`; unsupported arity/metadata forms fail. |
| `let` | One block header, one owner for every target/initializer pair, plus its body statements. True vector/map destructuring with one initializer remains one binding. Destructuring defaults are checked for nested executable syntax. |
| `loop`, `doseq`, `dotimes`, `for` | One loop header, whose iterator/state binding vector is structural, plus body statements. Every written initializer/range expression is still traversed for nested controls or unsupported macros. No implicit iteration or reduction work is invented. |
| `if` / `if-let`, `cond`, `case` | Conditional expressions, including in statement position. A definition/initializer/argument absorbs the expression; a standalone or loop-body conditional has one form owner, not a header plus every branch. Predicates/results are checked recursively, so an explicit `do`/`let`/loop block in a branch remains visible. `if-let`'s structural binding adds none, and `case` constants/literal rows add none. No implicit tests, dispatch table or scalar work is expanded. |
| `when` / `when-not` | One block-control header plus each written body form. These forms permit a multi-form body; they do not have `if`'s fixed one-expression-per-branch shape. |
| `try` | One header plus body statements. `catch`/`finally` separators add zero and expose their bodies. |
| `reify` | One anonymous class definition plus each method definition; a single method expression belongs to its method. Interface names and parameter lists add none. Initially needed only in the excluded generic worker helper. |
| Other supported executable forms | One owner in statement position. Ordinary nested expression calls do not each become a statement. `and`/`or`/`assert` are explicit allowed expression macros, with nested blocks still checked. |
| Comments, commas/whitespace, closing delimiters, literal vector/matrix rows | Zero. They remain in the lossless stream. Source bytes and other measures continue to observe layout/comments. |

The **loop binding decision** deliberately treats the complete written iterator
or recurrence initialization as the loop header, consistent with v2's loop-header
scope. It differs from `let`'s independent block-local bindings. This is an
explicit review point, not a consequence claimed to follow automatically from
the reader tree. A later reviewed change needs a new policy/version and fixture
expectations, not silent count drift.

The **conditional-expression decision** avoids turning native expression syntax
into several statements merely because it occurs in a loop body or at top level.
`(defn f [x] (if x 1 2))` and `(def f (fn [x] (if x 1 2)))` each have one definition
owner, analogous to an expression function using a Python/Julia conditional
expression. `(if c a b)` by itself has one form owner. A loop plus one such body
form has two. The actual written `do`/`let`/other blocks inside branches still
contribute their independent owners, and multiple function-body forms remain
separate. The same expression treatment applies to `cond`/`case` and conditional
binding `if-let`, while `when`'s multi-form body stays a block. This is a stated
syntax-owner convention, not proof of semantic equivalence across all languages
or a new claim that the existing v2 implementation handles every equivalent
conditional spelling identically.

Syntax quote/unquote, reader discard `#_`, reader conditionals, auto-resolved
keywords/namespaced maps, arbitrary tagged literals, multi-arity functions and
non-scalar metadata are outside the initial subset. Non-ASCII syntax whitespace
also fails rather than borrowing Python's whitespace definition; Unicode symbols
and string data have a native UTF-16/UTF-8 fixture. Unsupported forms remain
explicit gaps even when the native reader could accept them.

No arbitrary external function is assumed to be a safe expression macro. The
subset names known core expression functions, exact `clbg.support`/string API
exports, source-defined functions, local function bindings and the retained Java
interop call shapes. Core macro metadata comes from the pinned loaded core, but
only the explicit syntax allowlist is handled. Unknown core macros and unknown
qualified/unqualified heads fail. Required namespace aliases are checked instead
of inferred from a profile label. This does not attempt to resolve or run input
namespaces. Negative tests check unsupported macros and hidden executable defaults. Reify
method parameters are restricted to scalar symbols: an offline source-tree
mutation checks that destructuring is rejected, without pretending to supply
native acceptance evidence for an unseen method form.

## Scope, fixtures and results

The input manifest binds the catalog hash, every profile key, each complete source
hash and role, and whole-file application/excluded partitions. Initial Clojure
application files contain the application; `clbg.support` is the complete excluded
runtime-support unit. Count the helper in submitted/excluded scopes, never in the
application axis. Partial embedded-support ranges currently fail rather than
silently reparse a different selected text. Future partial partitions need their
own masked/native-span qualification.

Synthetic fixture pairs cover packed complete definitions, semicolon comments,
multi-binding vectors, matrix wrapping, a pure definition versus explicit body
forms, transparent `do` blocks, destructuring, and packed/wrapped loops. Pure
reductions remain expressions. Negative fixtures include an unknown macro, an
unsupported core macro, an unknown macro hidden in a destructuring default,
read-eval, a custom tag reader, reader construction and malformed source.
Additional conditional fixtures cover `defn`, a `def` of `fn`, `cond`, `case`,
`if-let`, initializer/argument context, top-level and loop-body context, explicit
`do`/`let` branches, multiple function-body forms, and a `when` multi-form body.
The expected counts distinguish expression syntax from written blocks directly;
they do not rely on equality alone.

Three additional fixtures alter the actual retained compact n-body source by
exact replacement: wrapping a real body-vector literal, packing its two scalar
definitions, and wrapping its existing two-binding `let`. The manifest records
both original/variant source hashes and the exact replacements. Native acceptance
and owner equality must be recorded for these actual source-derived variants,
not merely assumed from whitespace intuition. Synthetic examples alone are not
source qualification.

The saved proof binds every initial retained source scope and the supplemental
primitive source to native acceptance. All significant-token ownership gaps are
zero; all positive expected counts and equivalent pairs match; negative reader
and policy fixtures fail at their intended stage. Independent review covers the
conditional, loop, binding, function-body and support decisions and pins the
policy, code, helper, capture and report. Unknown syntax and incomplete proofs
remain unavailable rather than borrowing retained LOC.

| Workload | Compact logical units (retained LOC) | Optimized logical units (retained LOC) |
| --- | ---: | ---: |
| binarytrees | 23 (43) | 25 (52) |
| fannkuchredux | 46 (95) | 66 (120) |
| fasta | 46 (73) | 48 (79) |
| knucleotide | 31 (79) | 46 (120) |
| mandelbrot | 25 (53) | 33 (69) |
| nbody | 63 (109) | 76 (121) |
| pidigits | 22 (48) | 31 (54) |
| regexredux | 17 (34) | 19 (40) |
| revcomp | 17 (44) | 28 (58) |
| spectralnorm | 27 (62) | 34 (77) |

The generic support unit contributes **18** logical units to submitted/excluded
support scope and zero to the application total. The supplemental primitive
n-body source `12d61dd8…` has **66** logical units; its separately approved retained
111 LOC / 52 physical LOC remain unchanged. Supplemental native acceptance and
source counting do not themselves admit a timed profile. Current profile keys and
catalog binding are in `inputs.json` and `qualification.json`; the table records
the initial twenty-profile projection.

The retained `loc` and physical count remain side by side with the new
application/submitted/excluded logical units. This packet does not call the
retained Clojure counter uniformly normalized and does not copy its values into
the proposed logical measure. See [Clojure's source/idiom review](../../implementation-audit/v1/clojure-review.md)
and [the broader normalization coverage limits](../../../docs/source-metrics.md).
