# Elixir source-count inspection

This stage reads all sixty physical authored inputs from the twenty retained
compiled forms: one main, the complete helper, and the launcher per form. It
also parses fourteen grammar fixtures. The application files are data inputs;
the reader does not compile, evaluate, or load their modules.

The retained Elixir 1.20.4 parser supplies the AST, comments, columns, literal
metadata and explicit block boundaries. Lossless tagged JSON and native ETF
retain those observations. The native formatter produces separate copies at a
fixed line length of 98, and their metadata-stripped ASTs must match the inputs.
Original files remain unchanged. The API options follow the official
[Code parser documentation](https://elixir.hexdocs.pm/1.20.4/Code.html#string_to_quoted/2)
and [comment-preserving reader documentation](https://elixir.hexdocs.pm/1.20.4/Code.html#string_to_quoted_with_comments/2).

The fixtures cover packed statements, explicit and expression-only functions,
callback bodies, branches, match chains, destructuring, wrapped data, comments,
literals, interpolation, Unicode/CRLF, malformed syntax, and a source expression
that must never execute. These are reader observations, not passing canonical
count fixtures: expected owner counts must be reconciled with actual parser
positions before a count can be admitted.

Preparation and execution both require the existing shared timing mutex. The
controller binds the completed bounded-work plan and result, source bytes,
runtime closure, reader and supervisor before freezing a fresh plan. Execution
uses the atomic unreaped-child supervisor, with a 300-second limit and five
seconds for cleanup. It records partial outputs on failure and never retries.

The reader's original canonical and formatted LOC fields remain null. A separate
[qualification record](../source-units-v1/qualified-source-counts.json) now binds
the native positions, reviewed source-unit rule, every authored input, formatter
evidence, and equivalent-source pairs. It qualifies both source-size metrics for
all twenty forms; compiled required work and timing publication remain separate.

The [native reader run](run-v1/report.json) completed on 14 October 2026 in one
owned process. All sixty authored files and fourteen fixtures were read; the
twelve valid fixtures parsed and the two invalid fixtures were rejected as
expected. The [terminal receipt](run-v1/terminal.json) binds all 372 artifacts,
with no integrity, artifact or process-receipt errors. Original and formatted
ASTs preserve semantics. The corrected [source-unit replay](../source-units-v1/replay-v2.json)
passes all fourteen fixture expectations. The completed
[ownership review](../source-units-v1/review.md) explains the counts and the
one-unit spectral-norm correction.
