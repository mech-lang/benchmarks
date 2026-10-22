# Janet source-size qualification

The [reconciliation](results.json) combines exact-text measures, native grammar
token counts and two formatting experiments for all thirteen unique Janet files:
ten v2 parents and three v3 overlays. All authored application logic and helpers
remain in scope. The general runtime and unmodified Spork dependencies are not
application source. Nothing changes the canonical catalog or any saved timing.

## Qualified lexical measure

The [native lexical counter](../lexical-v1/count.janet) uses the unmodified Spork
source grammar at revision `26af769b7fd8f7214ea8f95dad5c2d360a79f6b4`, with native
Janet `parse-all` validation before counting. The exact grammar and MIT license
are in the [dependency snapshot](../dependencies-v2/spork-format/snapshot.json).
It accesses the pinned module's private `make-tree` binding explicitly; a changed
or missing binding is an error and requires requalification, not a fallback.

An atom, number, keyword, string or buffer literal counts as one token. A sequence
or dictionary contributes opening and closing delimiters plus its contained
tokens. A reader prefix contributes one token. Comments and physical whitespace
contribute zero. Unknown grammar node kinds fail rather than supplying a guess.
Quoted code remains source syntax and contributes tokens; it is not treated as
executable statements. Mutable collection prefixes are part of their opening
delimiter. These are declared language-specific lexical conventions, not logical
LOC or a language-neutral complexity score. Literal length, shorthand readers
and compound punctuation can favor one spelling; raw bytes, gzip and BPE remain
separate complementary measures.

All thirteen source counts match after both formatting projections. Eight
hand-counted probes cover separate versus packed declarations, matrix wrapping,
quoted code, comment-looking string content and escaped NUL, mutable literals,
200-element literals, deeply nested data and function bodies. Every packed/wrapped
pair has the same lexical count. Malformed input supplies no count. Native process
streams and ownership/cleanup receipts are retained under `../lexical-v1/run-v1`.
This qualifies the exact sources and exercised grammar boundaries, not arbitrary
future Janet syntax or arbitrary semantics-preserving source rewrites.

| Spectral source measure | Parent | Candidate |
| --- | ---: | ---: |
| Physical rows, including comments and blanks | 31 | 32 |
| UTF-8 bytes | 815 | 983 |
| Deterministic gzip bytes | 451 | 469 |
| Pinned cl100k_base BPE tokens | 283 | 304 |
| Native grammar lexical tokens | 244 | 253 |

The richer source measure does not erase the source cost of the optimization.
No smallest-possible-source or globally fastest implementation claim follows.

## Formatting findings and the normalization gap

The [core reader experiment](../source-count-v1/run-v1/results.json) parses with
Janet, prints every complete top-level form using colorless untruncated `%80m`,
checks reader-tree equality with `%n`, and checks idempotence. It produces stable
layout for the eight probes but expands the parent spectral source to 78 nonblank
rows. This is a data pretty-printer, not the selected source formatter, so its row
count is not admitted as canonical application LOC.

The [published Spork formatter experiment](../source-count-v2/run-v1/results.json)
uses the unmodified `fmt/format` documented at
<https://janet-lang.org/spork/api/fmt.html>. It preserves source layout. Two
independent packed assignments remain one row versus two rows when separated;
a wrapped four-element matrix remains three rows versus one row when packed.
It is suitable for checking native source style, but its output row count cannot
stand in for layout-independent normalized LOC. These findings are actual native
executions, not hypothetical string-counter probes.

Both experiments format all thirteen sources, reparse and independently reformat
them, and pass clean native compile-only checks. The ten active source views from
each formatter also pass all 149 bounded contracts, including seven exact
Janet-specific invalid-byte rejections: 298 application executions in total.
The complete sources, outputs and diagnostics are retained. Reader comparison
preserves tuple bracket/parens syntax, preventing data literals from being
silently replaced by function applications.

The raw experiment fields named `reader_formatted_loc` and
`published_formatted_loc` actually count all nonblank output rows, including any
preserved comments. The reconciled fields explicitly call them
`*_nonblank_rows`. They are not noncomment application LOC. Logical normalized
LOC and canonical formatted LOC remain null. Filling those fields requires a
reviewed ownership grammar for executable statements and literal layout, not
renaming either formatter's row total.

## Reproduction

With the pinned runtime and libraries restored, the three native `run.py` tools
in `source-count-v1`, `source-count-v2` and `lexical-v1` run serially under the
common mutex into new, non-overwriting output directories. Their existing run
snapshots are historical evidence; replay requires a new output version.
`python3 experiments/janet/source-qualification-v1/build.py --check` verifies the
reconciliation without starting any native process. It checks source and grammar
hashes, formatter/controller identities, raw native token captures, formatter
row counts, hand-counted probe results, 471 complete owned-process cleanup
receipts, and preservation of the canonical dataset SHA.
