# Scala 3.10 authored-source counting preparation

This packet specifies a parser-backed source-count reader and fixtures for the
ten [Scala source drafts](../source-v1/README.md). The exact Scala 3.10.0 parser
interfaces have now been reviewed in the pinned compiler source, and
[SourceReader.scala](SourceReader.scala) is an uncompiled transport draft. It is
separate from canonical counting. No compiler, JVM, parser, formatter or subject
program has run for this packet. Canonical and formatted LOC remain null.

Scala 3.10.0 was released on October 12, 2026. Its
[release page](https://www.scala-lang.org/download/3.10.0.html) links the
[release tag](https://github.com/scala/scala3/releases/tag/3.10.0), whose commit is
`25c18aaa21b6be202945e024cd5180d9d62d650f`.
[upstream-api-review.json](upstream-api-review.json) records release evidence and
the exact source review. [pinned-api-review.md](pinned-api-review.md) gives source
paths, line references and the remaining native token-coverage limitation. All
reviewed compiler interfaces are tied to that release commit.

## Proposed reader boundary

The preferred frontend is the selected compiler's own parser and scanner,
producing **untyped source trees before typer and post-parse compiler phases**,
with parser-side rewrites retained for review, together
with source tokens/comments and their original offsets. The native compiler
artifact and its dependencies must be retained for this reader. No external
parser dependency has been selected. The direct parse entry, context construction,
diagnostic capture and native tree transport are supported by the reviewed source.
No extra parser dependency has been established as necessary; actual compilation
and dependency sufficiency remain unverified.

A diagnostic reader would compile separately against that exact compiler
dependency closure and then parse retained source as text. Its classpath must
exclude benchmark classes, and its entry point must not invoke a subject main,
compiler backend, macros, build scripts, source evaluation or a TASTy inspector.
The draft calls `new Parsers.Parser(source).parse()` in an initialized compiler
context, without creating a compiler run. Its future CLI accepts an explicit
approved dependency classpath, a fresh output directory, and source paths. It
saves `initialization.json` and one JSON transport record per input. This is an
interface description, not a native launch command or a retained dependency
closure.

Each input must retain original bytes, decoded parser text, encoding/newline
behavior, source hash, diagnostics, native node identity and parent/role links,
source ranges, token/comment ranges, and all synthetic/absent/zero-width span
information. The offset unit and non-BMP behavior must be demonstrated by actual
fixtures, not inferred from the JVM's string representation. Every meaningful
source interval must have a reviewed owner or a retained diagnostic.

Untyped trees can already contain parser-created structure. A default constructor,
empty package, missing result type, object scaffolding or normalized operator
node is not automatically an authored declaration. Preserve these nodes for
inspection but derive units only from proven written syntax. Source ranges may
overlap between a parent and child, so summing AST nodes is invalid. Desugared
`map`/`flatMap` chains, accessors, module classes, bridges and TASTy nodes cannot
stand in for authored source size.

The scanner/parser interaction also matters. Significant-indentation regions
and inferred separators are not written closing tokens. Do not assume a separate
standalone scanner walk reproduces the parser's regions without inspecting the
versioned implementation. The official [relaxed-lambda proposal](https://docs.scala-lang.org/sips/75.html)
describes this interaction and identifies the new syntax as a Scala 3.10 preview;
preview features are outside this packet's initial grammar.

## Canonical owner policy

The existing rule is
`canonical-source-units-20261012-approved-rule-v2`. Its retained
[boundary rules](../../../archive/validation/loc-normalization/20261012/canonical.py)
and [independent-unit accounting](../../../archive/validation/loc-normalization/20261012/normalizer.py)
provide the common semantics. Scala is not an alias of Java or JavaScript.

| Written Scala form | Proposed treatment |
| --- | --- |
| Import, type alias, ordinary independent `val`/`var` declaration | One owner per declaration/binding; authored type syntax remains in the span |
| Tuple/pattern binding | One destructuring operation, not a unit per pattern name |
| Object, class or anonymous class body | One declaration header, each authored member/body unit, one written close |
| Constructor `val`/`var` parameter | One authored field in addition to the class header; ordinary constructor formals add no field units |
| Named method with explicit block | Header 1, opener 0, each body unit, written close 1 |
| Expression-bodied named method | One composed declaration unless its expression contains independently owned control/block work |
| Parenthesized expression lambda | Part of the containing expression; no invented close |
| Explicit braced callback | Header, independent body statements/final value, and written close remain visible |
| `if`/`else`, loops, `try`/`catch`/`finally` | Written control headers and body units; scalar conditional expressions may remain composed values |
| `match` and pattern callbacks | Preserve written case/guard/body ownership; parser-created functions/matches cannot supply extra units; initial projection requires explicit review |
| `+=`, updates and infix calls | Classify from native source ownership and written operators, before possible rewrite into applications |
| Arrays, tuples, ordinary argument groups and literal data | Separators are structural; existing literal/data wrapping remains physical |
| Significant indentation | Real method/control headers and body units remain; a layout exit contributes no written close |
| Written `end` marker | Retain it distinctly from layout exits; admission waits for its exact ownership rule |

All ten bundles need object/method/control boundaries, local declarations,
typed expressions, ordinary calls and imports. The tree bundle additionally
needs constructor fields; tree, fannkuch, Mandelbrot, regex and spectral norm
need anonymous `Callable` classes and callback ownership. K-nucleotide and regex
include pattern callbacks; K-nucleotide also includes a `match`. Numeric programs
use compound updates, while several bundles contain string interpolation and
wrapped literal arrays. These forms must be demonstrated in actual parser output
before counting their application sources.

Compiler-owned literal spans must protect comment-looking text without hiding
executable interpolation. Nested comments, strings, characters, interpolation,
non-BMP text and CRLF have separate fixtures. An unrecognized node, unowned
source interval, ambiguous synthesized span or disputed continuation produces a
diagnostic and null admitted count. Meaningful compiler directives and annotations
cannot disappear as ordinary comments. Unsupported syntax is a review gate, not
a reason to substitute formatted LOC or count generated bytecode.

[fixtures.json](fixtures.json) supplies proposed count contracts for simple
owners and explicit review/rejection cases for more complex forms. Counts are
hand-reviewed expectations, not parser observations. Packed/expanded source
pairs must agree where only executable layout changes. Braced versus indented
bodies intentionally differ when an actual written close is removed; packed
versus wrapped data can also differ under the preserved physical-row policy.

## Deferred qualification

1. Retain the exact Scala 3.10.0 compiler/JAR dependency closure under the common
   timing mutex. Confirm that its classes match the reviewed APIs. The direct
   parser setup, source creation, diagnostics and span interfaces have source
   evidence; actual compatibility and full native token coverage are pending.
2. Compile only the diagnostic reader draft against those interfaces. Pin its
   source, emitted classes, JVM, compiler dependencies and
   complete input inventory before launching it with bounded supervision.
3. Run every fixture and all ten exact application sources serially. Retain
   complete outputs and failure artifacts. Independently check source bytes,
   ranges, synthetic flags, token/source coverage, parser outcomes, descendant
   ownership and process closure.
4. Implement the narrow canonical projection over the retained evidence. Review
   all fixture results and application owner maps before admitting counts.
   Compilation correctness, runtime work, performance and formatter evidence are
   separate gates.

The current draft intentionally reports complete token coverage false. It
retains parser-owned comments, structural graph edges and original bytes, but
does not assume a separate scanner walk reproduces parser-dependent layout or
that native spans alone prove authored ownership. No native plan, dependency
closure hash, compiled reader or source count is claimed by this preparation.
