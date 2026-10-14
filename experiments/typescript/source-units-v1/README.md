# TypeScript canonical source-unit candidates

[typescript_source_units.py](../../../tools/qualification/typescript_source_units.py)
projects the exact saved TypeScript 7.0.2 native ASTs into the approved
`canonical-source-units-20261012-approved-rule-v2` accounting rule. It runs no
TypeScript parser, compiler, Node process or application source. The
[native compile/reader review](../native-stage-v1/independent-native-review-v1.json)
binds the actual forty source/AST records, source maps, compiler evidence and
closed native lifetimes. This packet produces candidates; it does not qualify
source counts, surviving work, runtime dependencies or timings.

The policy comes from [methodology](../../../docs/methodology.md), the retained
[canonical boundaries](../../../archive/validation/loc-normalization/20261012/canonical.py)
and [owner/physical-row accounting](../../../archive/validation/loc-normalization/20261012/foreign_core.py).
Those archived modules are read as policy evidence, not imported or executed.
No JavaScript language alias, type erasure, emitted-code count, formatter guess
or source-path exception is used.

## Native ownership and source coverage

The counter verifies the frozen reader validator, the retained compiler's exact
`SyntaxKind` definition, source bytes, every UTF-16 boundary and source-slice
hash, parent/child connectivity, role links and nonoverlapping sibling ranges.
UTF-16 offsets map only to complete Unicode characters. LF, CRLF, CR and the
JavaScript Unicode line separators retain their original byte representation.

Native string, regular-expression and individual template-segment ranges
protect their literal text before comments are recognized. The only source
scan for comments recognizes `//` and `/* ... */` outside these protected
ranges and rejects any intersection with a native semantic leaf. It does not
guess whether a slash begins a regular expression. Template interpolations
remain visible. Compiler directives and executable interpolation with
independent work remain explicit review cases.

Native `Block` boundaries must match written balanced braces. Classes, object
data, destructuring and imports own their respective braces separately.
Unknown kinds, unowned executable bodies or braces, overlapping owner events,
or unexplained source characters produce a null canonical candidate. The
output partitions every source character into whitespace, comment, native
literal, canonical event, native expression or structural separator ownership.
This is an accounting coverage check; the semantic AST is not relabeled as a
complete native concrete-token stream.

## Counting decisions

Function, constructor, method, class and explicit control headers count once;
their executable opening brace adds zero and each written executable closing
brace adds one. Unbraced bodies retain their own statement without an invented
close. `else if` is one combined header. `try`, `catch` and `finally` each own
their header and body.

Each native variable declarator counts independently, including uninitialized
typed declarations. One destructuring declaration remains one operation.
Native assignment operators identify additional chained assignments; operators
inside a consumed control header or data owner do not become independent
statements. Ordinary expression and data wrapping retains its noncomment
physical rows. Object property punctuation and constructor arguments do not
inflate the count. Complete imports and supported type aliases remain authored
declarations, including their types.

Constructor parameters carrying `public`, `private`, `protected` or `readonly`
add one authored field each. The constructor header records their aggregate
weight, while a separate parameter-property ledger retains each field's native
identity and source span. This avoids overlapping header and field events.
Ordinary constructor formals add no fields. Explicit class fields are separate
declarations whether or not JavaScript emission erases them.

Expression-bodied arrows stay in their containing expression. A block callback
owns its combined initial expression/header, body and written close. Only
structural suffix punctuation is absorbed; a subsequent call such as
`.collect()` remains a review case. Nested callbacks retain every body unit.
Unsupported interfaces, ambient declarations, mapped/conditional types,
type-literal members and other unknown native syntax fail closed.

## Actual fixtures and replay

The frozen [thirty fixture contracts](../source-counts-v1/fixtures.json) contain
21 proposed counts, seven explicit ownership-review cases and two expected
native parser rejections. All thirty outcomes pass the small saved-AST fixture
checks. Eleven lightweight regression tests also cover parameter fields,
literal/comment ambiguity, callback nesting, Unicode offsets and line endings,
missing ownership, changed source/kind identities and surrogate splitting.
CR-only and Unicode-line-separator variants are synthetic position-preserving
tests; they are not represented as additional native parser executions.

The full saved-data test and retained replay cover all ten authored workload
sources. The replay command acquires the established common mutex, verifies the
exact closed source packet and its artifact hashes, and writes forty projection
files plus a summary to a fresh directory. It does not hash or requalify the
complete compiler/runtime installation. The existing native producer and
independent review supply that packet's provenance.

```text
<retained-python> -I -S -B tools/qualification/typescript_source_units.py count --source <exact-source.ts> --ast <saved-ast.json> --output <fresh-result.json>
<retained-python> -I -S -B tools/qualification/typescript_source_units.py replay --output <physical-checkout>/experiments/typescript/source-units-v1/replay-v1
```

The [manual source expectations](manual-owner-expectations.md) account for every
change from physical rows in the ten retained applications. The complete
ten-source replay and review of its final owner records remain pending. All
canonical qualification flags remain false, formatted LOC remains null, and
no benchmark catalog or source bundle is changed by this tool.
