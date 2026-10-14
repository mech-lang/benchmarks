# Scala canonical source-unit projection

This additive packet projects authored source units from the retained Scala
3.10.0 native parser trees and physical token streams. It uses
`canonical-source-units-20261012-approved-rule-v2`. It does not launch Scala,
compile a program, evaluate source, or admit benchmark/chart results.

The [pure projector](../../../../tools/scala_source_units.py) independently
replays all 80 revised transports against their original captures. All stock
and observed parser pairs agree exactly. After removing only the three new
NoType marker fields and restoring the old graph-problem classification, every
original AST is unchanged. Original source bytes, UTF-16 boundary maps, token
intervals, scanner events, comments and whitespace remain identical. The frozen
token auditor also replays 9,030 intervals and 48 raw-token anchors. There are
72 complete positive cases and the same eight intentional rejections.

The input identities are:

| Evidence | SHA-256 |
| --- | --- |
| [Native v2 report](../native-token-capture-v2/report.json) | `a2b5a96c833d7c16e73c6a070e863d832d051048b4d87611543b4dbc17c97287` |
| [Prior independent v2 review](../native-token-capture-v2-review.json) | `d6154d35fbc7f8f5a25b82a0e1d7a98fb8188e1c8a0fe9ada1ceb59e7ce3a18f` |
| [Frozen native reader](../candidate-token-capture-v2/SourceReader.scala) | `5b737df6a85493c7517a688ff9c731656709cdb3ee82f8769901f649b65792c5` |

The [projection review](results-v1/review.json) binds the source, tests, shared
rule files, original owner contract, all 80 native input captures and all 51
projection artifacts. Native process lifetimes and the compiled reader closure
remain evidence of the separate native stage; this pure stage does not rehash
that runtime closure.

## Authored owners

The projector walks actual native statement and child roles. Each counted
event records its native node ID, UTF-16 and UTF-8 source span, exact source
slice, counted weight and uniquely assigned physical token IDs. A declaration
header's source span can contain separately assigned constructor fields; token
IDs, rather than overlapping enclosing spans, establish individual ownership.

Written method, class, object, callback and control headers count once. Their
opening braces add no unit. Authored body statements and each written executable
closing brace remain visible. Native constructor scaffolding, plain formal
parameters, empty sentinels and layout exits add no units. Tuple destructuring
is one binding. Scalar expression functions and conditional values stay
composed. Parenthesized expression callbacks differ from explicitly braced
callbacks because only the latter have a written executable close.

Literal data and argument wrapping retain occupied physical rows. This includes
the wrapped literal-array fixture, FASTA's seven-row ALU string and its wrapped
array arguments, and N-body's fourteen-row numeric array initializer. Arrays
are identified through actual native call/type-application nodes. Their scalar
elements remain visible in the source ledger; no generated values are counted.
Other multiline composed values remain review cases when their shared-rule
ownership has not been established.

Each token has at most one assigned owner. Semicolons and proven closing
argument punctuation are retained as structural zero-weight events. Literal
and comment tokens are never re-lexed. Source bytes and boundary maps are
verified, node references and structural edges must agree, every native node
must be reachable, and cycles or unrecognized field layouts fail closed.
Missing tokens, unexplained source intervals, unsupported nodes and disputed
ownership produce diagnostics and a null candidate count.

## Current qualification boundary

All 41 original owner contracts replay: 34 have concrete candidate counts,
five remain explicit ownership reviews, and two remain parser rejections.
The [fixture owner review](fixture-owner-review.md) describes the native owner
decisions; fixture expectations are checked only after projecting the AST and
are never input to the counter.

All ten application projections retain `normalized_loc=null`,
`canonical_LOC_admitted=false`, and `chart_admission=false`. Eight have complete
candidate owner maps. K-nucleotide and regex-redux retain additional null
candidate counts for native `Match`/pattern callbacks and their multiline
ownership. Manual inspection of every application owner map is still required,
including the eight maps without diagnostics. A complete token partition alone
does not approve the semantic counting policy.

Written `end` markers are recognized from the native definition's end-name
span. Ordinary bindings named `end` do not trigger that gate. Executable string
interpolation, match/case ownership, meaningful directives, annotations, derives
clauses and explicit type-bound owners remain review gates. Source correctness,
compiled runtime work and performance qualification are separate stages.

The [30 focused pure tests](../../../../tools/test_scala_source_units.py) check
the original contracts and native owner kinds, packed/expanded invariance,
braced/layout differences, constructor fields, callback ownership, control
bodies, data rows, interpolation and directives, Unicode/CRLF offsets, and
application admission gates. Negative tests alter source bytes, tokens,
whitespace, edges, nodes, parser parity and typed-node markers. They launch no
native subject and acquire no timing mutex.

To replay into a **fresh** additive directory, use the retained Python:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/scala_source_units.py --output /private/tmp/mech-benchmark-completion/experiments/scala/source-counts-v1/canonical-projection-v1/results-v2
```

An existing output directory is refused. The retained v1/v2 readers, native
captures, receipts, fixture contracts and earlier evidence are not modified.
