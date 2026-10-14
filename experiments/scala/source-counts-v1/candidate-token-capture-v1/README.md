# Scala parser token-capture candidate

This separate candidate adds physical-event observation to the uncompiled
[frozen transport](../SourceReader.scala). It uses the selected Scala 3.10.0
parser and its actual scanner. The upstream commit is
`25c18aaa21b6be202945e024cd5180d9d62d650f`. No JVM, compiler, parser or subject
program has run for this candidate. Native parity, physical coverage, canonical
LOC, formatted LOC and chart admission remain unqualified; counts remain null.

The candidate does not change the frozen transport or compiler source. Its
`SourceReader.scala` is authored separately from this fixture contract. A source
review supports trying the interception route; it does not establish compilation
success or native equivalence.

The entry point is `benchmark.scala310tokencapture.SourceReader`. Its argument
interface is `<approved dependency classpath> <fresh output directory>
<source.scala>...`. The classpath must exclude benchmark classes. The reader
writes `initialization-stock.json` and `initialization-observed.json`, then
numbered `0000.json`, `0001.json`, and subsequent source records containing both
parser transports and the candidate capture. This specifies the source interface,
not a concrete runtime command or a retained native launch plan.

## Observation boundary

The native `getNextToken` has two callers: `nextToken` and `peekAhead`.
`nextToken` reaches `handleNewLine` before layout insertion, or reaches
`postProcessToken` without that handler. Entry observations at those two methods,
plus an observation after `peekAhead`, can retain a fresh lexical result before
the caller fuses or discards it. Freshness must come from the pre-call
`next.token == EMPTY` value, with separate state for each invocation. Buffered
replays and separate speculative `LookaheadScanner` instances must not create
duplicate physical events.

This distinction preserves both keywords of `case class`/`case object`, a
semicolon consumed before `else`, and a discarded trailing comma. Inferred
newlines, indentation and outdents remain layout evidence. Parser-side token
reclassification must not overwrite already retained source events.

For a fresh ordinary lexical result, `lastCharOffset` is the first unconsumed
character boundary. It is not interchangeable with `lastOffset`. An interpolated
`STRINGPART` can also prefetch its following identifier: the fragment ends at
native `next.offset`, and the prefetched token ends at `lastCharOffset`. Keep the
actual `next.token`, including `THIS` for `$this`. For `${...}`, the opening brace
remains separate executable syntax. These are source-supported interval
expectations that still require native fixtures.

`Parser.in` is a concrete overridable `val`, without a scanner factory. The
candidate's discarded base scanner must be limited to an empty interval; its
replacement scanner reads the complete source. The pinned `Parser` uses the
constructor's `startFrom`/`limit` only to create that base scanner. The scanner
constructor itself calls `nextToken`, so the observer sink must exist before
construction and must not depend on initialized subclass fields. The first-token
and constructor-diagnostic fixtures specifically check this boundary.

## Fixture contract

[fixtures.json](fixtures.json) adds focused event and coverage cases. It also
requires every case from the [existing owner fixture contract](../fixtures.json)
and all ten exact [application sources](../../source-v1/README.md) in the later
native review. The added contract supplies no LOC expectations or counts.
Its exact source fragments are coverage anchors, not a substitute for examining
the whole source. Each `native_token_constant` names a constant in the pinned
`Tokens.scala`; the fixture table binds those constants to numeric token IDs.
Compare those IDs with the event's `token` field. The reader's `token_name` is the
compiler's display label from `showTokenDetailed`, not that symbolic constant.

For each source, compare the candidate with an unmodified full-source
`Parsers.Parser` under the same retained compiler, settings and dependency
classpath. Use fresh input contexts, compilation units and reporters; retain the
exact setup. Compare source bytes, diagnostics, untyped graph, modifiers, spans,
native comments and final scanner state. The candidate requires exact equality
of the complete stock and observed transport JSON, including graph IDs; it does
not normalize IDs or other differences. A differing diagnostic must remain a
failure, including diagnostics emitted while constructing the first token.

Successful coverage requires a successful parse and an explanation for every
source character: a retained physical event, retained native comment interval,
or checked whitespace. A surrogate pair cannot be split by an endpoint. Literal
content must remain protected while interpolation expressions remain visible.
EOF has zero physical width. Unexplained gaps, overlaps, unsupported scanner
handoffs and parser/scanner errors reject the coverage claim, while preserving
partial evidence.

A terminal physical U+001A needs its own rejection case. The native scanner can
recognize that source character as EOF without a parse error, but its
`lastCharOffset` remains before the source end. Successful parser parity therefore
does not suffice: the candidate must retain the byte and reject the early EOF
and unexplained source gap.

Native comment spans need a specific CRLF check. `Comment` records
`charOffset - 1`, whereas `nextChar` can consume CR and LF together. A comment
immediately before CRLF can therefore have a native span that includes CR even
though its native raw text does not. Preserve both fields exactly and record
that relationship explicitly. Do not trim spans generally or permit unrelated
whitespace/code overlap.

XML is an explicit rejection: `MarkupParser` advances the main character reader
directly and bypasses these scanner hooks. Retain its diagnostics and partial
events. The same evidence-preservation rule applies to malformed source; scanner
recovery, such as a synthesized semicolon, cannot establish physical coverage.

## Pinned source basis

All links refer to the selected commit:

- [Parsers.scala:199](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Parsers.scala#L199): direct scanner construction; `parse()` consumes a compilation unit and EOF. Direct token changes occur at lines 1735, 1783, 3440 and 5140.
- [Scanners.scala:390](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Scanners.scala#L390): fresh versus buffered reads, `nextToken`, insertion, newline handling, observation methods, lookahead and fusion. Construction calls `nextToken` at lines 1629–1632.
- [Scanners.scala:1254](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Scanners.scala#L1254): string-part scanning and prefetched token offsets; `finishNamedToken` at lines 158–167 applies native keyword conversion.
- [CharArrayReader.scala:25](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/CharArrayReader.scala#L25): character offsets and CRLF handling.
- [Scanners.scala:1054](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Scanners.scala#L1054): native comment span and raw-text retention.
- [MarkupParsers.scala:74](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/xml/MarkupParsers.scala#L74): direct character-reader operations; the Scala 3.10 parser reports XML unsupported at `Parsers.scala:624–629`.

Native fixture execution, exact compiler/dependency retention, source-event
coverage validation and independent review are pending. This packet supplies no
completed native result, admitted source count or timing.
