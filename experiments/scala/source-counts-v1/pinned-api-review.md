# Scala 3.10.0 parser transport API review

This is a source review of `scala/scala3` commit
`25c18aaa21b6be202945e024cd5180d9d62d650f`, selected by
[selection.json](../toolchain-v1/selection.json). [SourceReader.scala](SourceReader.scala) is a
transport draft against those interfaces. It has not been compiled or executed;
no parser fixture, canonical count, formatted count or toolchain closure is
qualified.

## Direct entry and diagnostics

The concrete entry is `new Parsers.Parser(source)(using context).parse()`.
`Parser` constructs its own scanner; `parse()` calls `compilationUnit()` and
accepts EOF. It returns an untyped tree and does not call a compiler `Run`, typer,
backend, macro evaluator or subject main. The parser can recover after an error,
so a returned tree alone does not establish valid input.
[Parsers.scala:199–210](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Parsers.scala#L199),
[Parsers.scala:168–180](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Parsers.scala#L168).

The official parser test uses this entry with the initialized context inherited
from `DottyTest`: `new ContextBase`, `base.initialCtx.fresh`, settings, then
`base.initialize()(using setup)`. Initialization sets up platform and definitions;
it can resolve the configured classpath, so it is not an empty operation. The
draft requires an explicit approved compiler/library dependency classpath that
excludes subject classes. It does not construct `Compiler` or call `newRun`.
[ParserTest.scala:26–32](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/test/dotty/tools/dotc/parsing/ParserTest.scala#L26),
[DottyTest.scala:22–29](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/test/dotty/tools/DottyTest.scala#L22),
[Contexts.scala:990–1001](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/core/Contexts.scala#L990).

`FreshContext.setSetting` is public. The draft explicitly selects source `3.10`,
UTF-8, empty sourcepath/language/Wconf, retained comments, and disabled preview,
experimental, rewrite, warning suppression and magic-offset-header settings.
These are actual typed setting fields at the pinned revision.
[Contexts.scala:807–808](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/core/Contexts.scala#L807),
[ScalaSettings.scala](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/config/ScalaSettings.scala#L52).

The draft overrides public, non-final `StoreReporter.report`, records each
incoming diagnostic, and then calls `super.report`. Thus it retains the original
diagnostics before warning filtering while preserving the compiler's own error
counters and recovery behavior. It separately saves buffered diagnostics and
unreported-warning counts. It does not flush an installed store reporter into
itself. Bootstrap diagnostics are saved separately and cause initialization to
be rejected. Diagnostic position traversal stops at `outer == null`;
`NoSourcePosition` has an absent span and the same null default.
[StoreReporter.scala:20–62](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/reporting/StoreReporter.scala#L20),
[Reporter.scala:178–240](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/reporting/Reporter.scala#L178),
[Reporter.scala:314–319](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/reporting/Reporter.scala#L314),
[SourcePosition.scala:17,108–112](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/util/SourcePosition.scala#L17).

## Bytes, identities and positions

`CompilationUnit(path, text)` calls `SourceFile.virtual`, which stores the text
as UTF-8. `SourceFile.content()` decodes the stored bytes into `Array[Char]`.
Neither appends a newline or scanner sentinel. The draft strictly decodes input
UTF-8, saves original bytes/base64/SHA-256 and decoded text, and checks equality
between parser content and decoded input. It also supplies a UTF-16-to-UTF-8
boundary map; a surrogate-pair interior is explicitly not a byte boundary.
`CharArrayReader` indexes the original character array; its CRLF handling advances
over two source positions even when returning one newline character. Actual
non-BMP, CRLF and comment-span fixtures remain required before offset validation.
[CompilationUnit.scala:182–184](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/CompilationUnit.scala#L182),
[SourceFile.scala:75–80,240–242](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/util/SourceFile.scala#L75),
[CharArrayReader.scala](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/CharArrayReader.scala#L26).

`Positioned` is a `Product`, but its `uniqueId` is normally `-1`. The draft uses
reference-identity IDs and native product field names, preserving repeated
references and multiple structural parents. It explicitly includes definition
modifiers, `FunctionWithMods.mods` and the eager `DerivingTemplate.derived` split,
which are not ordinary child fields in every node. Unknown native containers are
retained as opaque diagnostics rather than forced. The transport never calls
`rhs`, `body`, `forceFields`, `tpe`, tree rewriting or semantic ownership queries.
The definition `endSpan` accessor is restricted to trees with no assigned type:
its internal `srcName` lookup then sees `NoDenotation`, and it is skipped on
unexpected typed data.
[Positioned.scala:20–31](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/ast/Positioned.scala#L20),
[Trees.scala:292–320,934–999](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/ast/Trees.scala#L292),
[untpd.scala:81–84,255–259](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/ast/untpd.scala#L81).

Two ordinary parser representations need explicit transport handling. The exact
shared `EmptyValDef` sentinel sets `myTpe = NoType`; its `hasType` flag is retained
without incorrectly treating that sentinel as typed subject work. Numeric
syntax uses `NumberKind` (including whole-number radix), and generators carry
`GenCheckMode`; these native enum values are preserved distinctly.
[Trees.scala:1091–1103](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/ast/Trees.scala#L1091),
[untpd.scala:144–150,186–194](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/ast/untpd.scala#L144).

Every span retains its raw coordinates and existence flag; existing spans also
retain start/end/point, synthetic/source-derived and zero-extent flags. Accessors
for an absent span assert, so the draft checks existence first. A source-derived
or nonempty span is not proof of authored work: `Positioned.envelope` can assign
missing child positions from neighboring spans, and the parser creates implicit
constructors, empty packages, missing type trees and wildcard parameters.
[Spans.scala:38–102](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/util/Spans.scala#L38),
[Positioned.scala:67–126](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/ast/Positioned.scala#L67),
[Parsers.scala:5311–5315](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Parsers.scala#L5311),
[untpd.scala:92–100,585–589](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/ast/untpd.scala#L92).

## Remaining token and ownership boundary

The parser's own scanner exposes comments with native spans/raw text. These are
retained directly; comments are not rediscovered with a separate lexer. Scanner
`offset` is the current token start, but `lastOffset` is the **previous** token's
end. It is not a current-token range. Parser calls alter indentation regions;
scanner postprocessing combines `case class`/`case object`, can remove a semicolon
before `else` or a trailing comma, and classifies `end` contextually. A standalone
scanner walk is therefore not a proven copy of the parser's consumed stream.
`fetchToken` is protected and final; overriding `nextToken` alone would miss
other mutations. The draft reports `complete_token_coverage: false` and does not
fabricate token ranges.
[Scanners.scala:40–80,249–265](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Scanners.scala#L40),
[Scanners.scala:701–800,880](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Scanners.scala#L701),
[Parsers.scala:701–704](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Parsers.scala#L701).

The exact source also establishes several counting hazards:

- An indented one-expression block can become its last expression directly;
  native `Block` count does not establish written brace count.
  [Parsers.scala:3239–3259](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Parsers.scala#L3239).
- Every class parameter initially receives `ParamAccessor`; explicit `val` is
  consumed without a separate `Mod.Val`. Flags alone cannot distinguish an
  authored constructor field from an ordinary formal.
  [Parsers.scala:3983–3996](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Parsers.scala#L3983).
- Interpolated strings retain expression children in native `Thicket` segments;
  masking their entire envelope would hide executable interpolation.
  [untpd.scala:67–72](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/ast/untpd.scala#L67).
- A written `end` marker extends the previous tree's span. Selected definition
  nodes expose a public `endSpan`, but controls need not retain that attachment.
  A retained definition end-name span is therefore positive evidence, not a
  complete inventory of written end markers.
  [Parsers.scala:1745–1784](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Parsers.scala#L1745),
  [Trees.scala:322–357](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/ast/Trees.scala#L322).

The next concrete check is compilation of this transport against the retained
3.10.0 dependency closure, followed by the 41 existing fixtures and ten exact
sources under bounded supervision. Full lexical coverage still needs a reviewed
native scanner/parser observation strategy. Until those results establish byte
and structural coverage, canonical projection remains unimplemented and all
admission flags remain false. No extra parser dependency has been established as
necessary by this source review.
