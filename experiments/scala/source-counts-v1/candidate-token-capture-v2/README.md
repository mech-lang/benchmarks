# Scala native-container capture correction

The retained v1 reader parsed all 70 fixtures and ten application sources with
exact stock/observed transport parity. Its coverage result was complete for 27
inputs and incomplete for 53. This additive candidate addresses the graph
classification error behind 45 otherwise complete inputs. Eight intentional
negative fixtures continue to reject coverage.

| V1 outcome | Inputs |
| --- | ---: |
| Complete | 27 |
| Rejected only because native `NoType` containers were classified as typed trees | 45 |
| Intentional parse/token/XML rejection | 8 |

The original reader, contracts, reports, native receipts and raw transports are
unchanged. The [graph diagnosis](graph-evidence.json) and
[token audit](token-evidence.json) describe saved v1 evidence. They do not claim
that this candidate has compiled or run. Native v2 parity and coverage remain
unqualified; canonical LOC, formatted LOC and chart admission remain unset.

## Native graph distinction

All 71 reported graph problems are accounted for: 41 `EmptyTree` nodes and 30
`Thicket` nodes across 47 inputs. Two of those inputs already reject because of
parser errors. No unexpected typed class or opaque native value was found.

In the exact selected compiler commit, `hasType` tests whether the internal type
slot is non-null. `Thicket` initializes that slot to the `NoType` singleton;
`EmptyTree` inherits `Thicket`. `EmptyValDef`, which v1 already recognized, uses
the same marker. These parser containers therefore report `hasType = true`
without having passed through the typer. The relevant native definitions are
[Trees.scala:132–141](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/ast/Trees.scala#L132),
[1057–1059](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/ast/Trees.scala#L1057)
and [1086–1102](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/ast/Trees.scala#L1086).
The fetched exact file matches retained Git blob
`02077aed374ad3ac5aa1b0292af283e06fbc077a` and SHA-256
`7724f5302bd575e27f796b23e294abed3806492d9a241644e605ddf68a76bf69`.

[SourceReader.scala](SourceReader.scala) accepts a non-null type slot only when
the node is one of those native container/sentinel shapes **and** its actual
`typeOpt` is reference-identical to `NoType`. Other typed nodes still produce
`typed_tree_in_parse_output`, including a recognized container carrying a real
type. The native type marker and container/sentinel distinctions are exported
alongside the unchanged `has_type` value. `typeOpt` is a final direct field read;
the change does not force a lazy tree or invoke a compiler phase.

Graph traversal remains intact. The 30 nonempty thickets contain 60 immediate
children: 30 literals, 18 identifiers, 11 executable blocks and one `This` node.
Their fields, native spans, identity sharing and parent/role edges remain in the
transport. The candidate changes no scanner hooks, token intervals, comment
handling, literal encoding, graph field traversal, diagnostic capture or parity
comparison. It remains a source parser and invokes no benchmark main.

## Token evidence and the XML expectation

The independent saved-evidence audit checks all 80 source byte streams, UTF-16
to UTF-8 boundary maps, exact parser transports, 48 required lexeme anchors and
9,030 physical/whitespace intervals. The only uncovered intervals are the two
intentional rejection cases below. Both CRLF comment-span-overhang cases retain
their native spans/raw text and their separately justified physical bounds.

| Negative fixture | Retained rejection |
| --- | --- |
| Unclosed method; mismatched array delimiter; first-character NUL; unterminated leading comment; unterminated string; mismatched delimiter recovery | Six parser-error cases; the NUL case also retains an `ERROR` token |
| Terminal physical U+001A | Two early-EOF observations and the uncovered interval `9:10` |
| XML literal | Unsupported direct character-reader handoff and uncovered interval `12:39` |

The only fixture correction changes XML's expected parse result from
`diagnostic` to `ok`, with empty diagnostics at source version `3.10`. Its source
bytes, coverage rejection and required handoff/gap checks stay intact. Both saved
native parsers already behave this way. The pinned
[parser](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/Parsers.scala#L624)
routes this diagnostic through `MigrationVersion.XmlLiteral`, whose warning and
error thresholds are both
[`future`](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/config/MigrationVersion.scala#L33).
The [markup parser](https://github.com/scala/scala3/blob/25c18aaa21b6be202945e024cd5180d9d62d650f/compiler/src/dotty/tools/dotc/parsing/xml/MarkupParsers.scala#L74)
still reads the character stream directly, so this scanner observer cannot claim
complete XML coverage. The other 28 capture fixtures, all 41 inherited owner
fixtures and all ten application sources retain their existing contracts.

## Validation boundary

The executable entry point remains
`benchmark.scala310tokencapture.SourceReader`; its source-result schema becomes
`scala310-parser-token-capture-candidate-v2`. It must compile into fresh reader
classes and parse the same 80 unchanged inputs under the retained compiler and
settings. Native review must verify exact stock/observed parity again, the
observed `NoType` marker on every accepted native container, unchanged literal
and graph evidence, 72 complete positive inputs and all eight intentional
rejections. A missing child, changed literal, unknown type or unexplained token
interval remains a failure.

The pure [graph tests](test_graph_evidence.py) verify saved graph accounting,
reject unrecognized classes and missing/duplicate child edges, and check that
the candidate leaves scanner and graph-field transport unchanged. The pure
[token tests](test_token_evidence.py) exercise the independent token audit. They
read retained evidence only; they are not a Scala compilation or a replacement
for native v2 validation. Source ownership and LOC projection remain separate
work after capture coverage is established.

Candidate preparation passed 24 pure tests: seven graph-evidence tests and
17 token-evidence tests. [candidate-manifest.json](candidate-manifest.json)
records the frozen candidate files and original evidence identities.
