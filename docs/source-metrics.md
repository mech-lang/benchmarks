# Complementary source measurements

[The additive report](../experiments/source-metrics/v1/metrics.json) and
[CSV](../experiments/source-metrics/v1/metrics.csv) measure all 1,070 retained
profiles, covering 971 distinct source files and 63 execution variants. The
report preserves the saved canonical catalog, source bytes, timings and
coordinates. The chart offers separate source-size projections described below.
Profiles remain separate records even when execution modes
or timing aliases share the same source. Join by program key to the source
authorship audit when restricting the analysis to suite-authored programs;
inclusion here makes no claim that upstream code was authored by the suite.

No single metric in this packet is a language-neutral measure of expressiveness.
The purpose is to make the same application boundary inspectable through
several measures and expose gaps in the existing normalization rules.

## Metrics and exact text boundaries

| Field | Definition and practical limits |
| --- | --- |
| `retained_application_loc` | The catalog's existing nonblank, noncomment application count, with its recorded metric and evidence. Cohort rules differ; copying the count does not recertify it as uniform logical LOC. |
| `canonical_formatted_loc` | Existing qualified native formatter LOC under the application boundary. Only 61 profiles have complete evidence; 835 are pending, 151 unavailable and 20 not qualified. No guessed formatting fills these gaps. Native formatter styles and versions can also differ. |
| `utf8_bytes` | Exact UTF-8 text size, including comments, indentation, blank lines, BOM and retained line endings. A Unicode glyph can take multiple bytes. |
| `unicode_codepoints` | Python Unicode string length, including comments/whitespace. This is neither grapheme count nor visual width, and no Unicode normalization is applied. |
| `physical_lines` | All rows in the selected text, including blank/comment rows, using Python `splitlines`. This differs deliberately from retained noncomment `physical_loc`. |
| `gzip_bytes` | Sum of independently compressed, nonempty per-file scope fragments, gzip level 9, timestamp 0, empty filename, OS byte 255. The DEFLATE implementation/version is recorded. Repetition compresses well; small files pay a gzip-member overhead and splitting source into files can change the result. |
| `cl100k_base_tokens` | Ordinary-text BPE token count from pinned tiktoken 0.12.0, regex 2026.1.15 and the exact `cl100k_base` vocabulary. Counts are summed per file without chat wrappers, filenames, inserted separators or special-token interpretation. This is tokenizer-dependent text size, not language lexical tokens. |

Every profile has three scopes. **Submitted** includes every attached catalog
file, including reusable support. **Application** includes `application`,
`application-helper` and meaningful `runtime-setup` files, removing reviewed
embedded support line ranges. **Excluded support** contains separate
`runtime-support` files and those embedded fragments. It does not represent
every installed dependency, compiler or runtime. The submitted scope is an
attached-source bundle, not a total-authored-source claim.

Per-profile roles override global file roles. The retained application LOC
policy supplies the reviewed exclusion decisions; the tool does not infer
exclusions from a helper's name or generic-looking API. Workload-specific
helpers remain application source. Each unit records the source SHA-256,
inclusive original line ranges retained/removed, exact selected-text SHA-256,
raw sizes, compressed size and compressed SHA-256. Selected lines retain their
original endings and concatenate within each file, without masking removed
lines with spaces. Submitted bytes and code points must equal application plus
excluded bytes and code points. Gzip sizes and BPE tokens do not have this
additivity property across a split.

These byte, code-point, gzip and BPE measures include comments and whitespace
*inside the selected application boundary*. They are not described as
comment-stripped lexical sizes. No common regular-expression lexer could
honestly strip comments/literals for all the represented grammars. The
`language_lexical_tokens` field explicitly remains unavailable pending
language-specific qualification.

The chart's Source metric selector includes application UTF-8 bytes, gzip bytes
and BPE tokens alongside retained normalized LOC and qualified formatted LOC.
Each text measure has its own fixed minimum per workload over every admitted,
timed candidate with an available positive count, including candidates beyond
the retained LOC endpoint pool. It independently selects fastest and smallest
endpoints; display filters and disabled programs do not renormalize its
baseline. Missing counts never become zero or borrow a different measure.
Saved seconds and samples stay unchanged, timing aliases share their recorded
runs, and every measure retains the fixed best-time baseline and common time
domain. Submitted and excluded-support sizes remain available in Data, source
details and exports. These text measures include comments and whitespace;
BPE retains the vocabulary and Unicode biases described below.

The regenerated report includes the separately admitted BQN nucleotide, Nim
nucleotide, corrected MATLAB regex, BQN spectral-sum and BQN FASTA Bins source/count receipts.
Their exact-source retained counts do not certify a uniform native ownership
grammar. In this catalog, 249 profiles have attached or embedded excluded
support. Source partitions and report/catalog hashes are regenerated and bound
for the complete admitted catalog, including these additions.

## What the normalization audit actually establishes

The packet runs eight tiny source-counter probes against retained counter
implementations, without importing their benchmark runners or executing any
workload. Counter implementations, the vendored Pygments version/mapping and
related owner-review tools are hash-bound in `normalization_audit.counter_pins`.
The source snippets and both results are saved in the report.

| Probe | Packed count | Expanded count | Finding |
| --- | ---: | ---: | --- |
| Python: `x = 1; y = 2` versus separate rows | 1 | 2 | Legacy lexical-line rule does not normalize independent statements. |
| Julia: the same assignment pair | 1 | 2 | Legacy lexical-line rule has the same gap. |
| Mech: `x := 1; y := 2` versus separate rows | 1 | 2 | Text-only probe; native syntax acceptance is unverified, so this is not a confirmed packing gap. |
| C#: `x=1; y=2;` versus separate rows | 2 | 2 | Positive control for retained semicolon expansion. |
| F#: two imperative assignments versus separate rows | 2 | 2 | Positive control; array/list separators are handled separately. |
| Zig: two assignments versus separate rows | 2 | 2 | Positive control for retained expansion. |
| F#: one array literal on one versus two rows | 1 | 2 | Literal wrapping still affects the baseline, although its semicolons are structural data syntax. |
| Mech: one matrix literal on one versus two rows | 1 | 2 | Matrix row punctuation is data shape; physical wrapping still affects the historical count. |

These are counter behavior probes, not general language compiler acceptance tests or
proof that the eight snippets occur verbatim in scored sources. Python's two
snippets also pass the running CPython native `ast.parse`; its version is
recorded. The Mech assignment probe asks what the historical scanner does; a native parser still
must establish which statement-separator forms are admissible. The matrix
probe follows the retained Mech matrix notation. Passing a positive control
does not certify all strings, interpolation, macros, nested control or
multiline literals in that language.

The existing labels span 679 `statement-normalized`, 63
`assignment-normalized`, 29 `canonical-source-units` and 293
`unspecified-legacy` profiles. These labels are provenance, not equivalent
language-grammar certificates. BQN/K's retained review applies explicit
packed-body adjustments to exact sources. APL and R owner tools bind reviewed
decisions to exact hashes and reject changed source. Those are useful
source-specific guarantees with narrower scope than a general parser.
Consequently `uniform_logical_loc` is explicitly unavailable. The current
canonical ranking is preserved while these differences remain visible.

Concise array notation is legitimate expression syntax. A reduction, matrix
operation, tacit composition or glyph function should not be expanded into
imagined scalar loops or charged for implicit operations that other language
libraries also perform. Independent written assignments or statement owners
still need separate units when packed together. A blanket split on semicolons,
diamonds, commas, braces or glyphs would conflate these two cases.

## Qualification plan before a uniform logical ranking

The packet supplies a concrete proposed policy,
`logical-source-owners.v1-draft`, with machine-readable paired acceptance
cases and expected unit counts. It is not a qualified replacement ranking.
The proposed units are one for each independent binding, expression statement,
control header or explicit function/type declaration; written closing
delimiters, structural punctuation and literal continuation rows add zero.
A pure expression function binding owns one unit, while a block function
declaration owns a header plus its independent body owners. Loop init/test/step
remain inside their header owner. A destructuring pattern with one initializer
is one binding. Chained written assignments require a native binding-owner
decision. These choices deliberately differ from retained policies that charge
written closes or wrapped literal rows.

Under this policy the one-row and wrapped Mech/MATLAB matrices both have one
unit, the two Python assignments both have two, and a C-like loop with one
expression statement has two (header and body). These expected values define
what a future native implementation must establish, rather than inventing
counts for the current suite. Require every significant character to have an
owner or an explicit syntax/data exclusion, and fail on unknown or ambiguous
source instead of falling back to physical rows.

| Syntax family | Required paired cases and protection against false expansion |
| --- | --- |
| C-like imperative languages | Semicolon-packed and line-separated statements; declarations with several initialized bindings; chained assignments; `for(init;test;step)`; empty statements; one-line control bodies; braces; macros and attributes. Semicolons in loop headers, strings and comments are structural or literal. |
| Indentation languages | Packed/simple statements versus separate rows; multiline expressions and arrays; suites after colons; comprehensions; decorators; interpolation; comments and pragmas. Indentation boundaries require native ownership. |
| Functional/expression languages | Expression functions versus block functions; independent `let`/binding owners; pattern clauses; pipelines, tacit composition and reductions; literal containers; callbacks with several statements. A pure composed expression remains one expression. |
| Matrix/array and glyph languages | Mech/MATLAB matrix row separators versus independent statements; APL diamonds and BQN/K statement boundaries versus trains, functions and data; vector literals across line wraps; nested arrays, axes and indexing. Preserve concise array operations; split only distinct written executable owners. |
| Logic/term languages | Clause and directive terminators; conjunction/disjunction; DCGs; quoted punctuation; lists and term data; native term ranges. Specify clause/header/body ownership without treating every punctuation token as a line. |
| Stack/combinator languages | Uiua and related function trains, modifiers, array construction and stack operations; separate written definitions and blocks; glyph strings and multiline data. Do not scalarize primitive functions. |
| Message/block and homoiconic languages | Smalltalk cascades versus statements/returns; Lisp/Racket expression trees, binding lists, macros and quoted forms. Distinguish executable owners from code-shaped quoted data. |

For each supported language, require native fixture acceptance, packing and
wrapping equivalence cases, negative cases, an ownership coverage check over
every exact scored source, and independent review of embedded support
partitions. Record parser/runtime, tool, config, source and policy hashes.
Recount all candidates before changing minima or comparing language means;
qualification of one source or one construct cannot silently certify an
entire language. Keep native formatted LOC and raw size metrics separate
because they answer different questions.

The separate [v2 Python/Julia qualification](../experiments/source-normalization/v2/README.md)
now records native statement ownership, source coverage and paired packing/literal
wrapping evidence for 52 exact Python/Julia/JIT-AOT profiles. It is an additive
qualified subset, kept separate from the full-cohort retained counts. The separate
[Clojure v1 qualification](../experiments/source-normalization/clojure-v1/README.md)
adds 21 exact profiles with native-reader-bound source owners. An explicitly
reviewed [compact-source extension](../experiments/source-normalization/clojure-extensions/v1/README.md)
adds one further Clojure profile without altering that original proof. The browser's
**Qualified logical units · partial coverage** option exposes these 74 profiles,
with blank counts elsewhere. Each source records its versioned policy and proof
references; Python/Julia v2 and Clojure v1 remain distinct reviewed conventions.
This option uses a fixed per-workload minimum over eligible, qualified timed
candidates and never borrows retained LOC or formatted counts. Data, source
details and CSV/JSON exports include the count and policy. The browser payload
contains compact counts/hashes, not native syntax trees. Its parser/rule limits
and unsupported forms remain explicit; it does not
certify the remaining syntax families or authorize a uniform ranking.

The two measured Clojure n-body alternatives illustrate why the measures remain
separate. Both counts use the same application/support partition:

| Candidate | Retained LOC | Physical code lines | Logical units | UTF-8 bytes | gzip bytes | BPE tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Explicit primitive updates | 111 | 52 | 66 | 3,546 | 1,185 | 1,225 |
| Compact typed setters | 109 | 49 | 63 | 3,385 | 1,186 | 1,166 |

The compact candidate is smaller under the written-source and token measures,
while independently compressing to one byte more. That compression difference
is tiny, but demonstrates that gzip can reverse the ordering. In their fresh
matched full-process comparison, the compact version takes 22.22 s versus
2.69 s for the primitive control. Source-size and runtime objectives therefore
retain separate candidate selections; no single score establishes the most
expressive or fastest possible program. See the
[comparison and evidence](../experiments/clojure/compact-primitive-v1/MEASURED.md).

## Tokenizer pins and bias

The optional token metric follows the primary
[tiktoken 0.12.0 release](https://pypi.org/project/tiktoken/0.12.0/) and its
[encoding definition](https://github.com/openai/tiktoken/blob/0.12.0/tiktoken_ext/openai_public.py).
The local vocabulary is the upstream `cl100k_base.tiktoken` asset, SHA-256
`223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7`.
The exact pre-tokenization regex and special-token table have a separate
definition digest. `encode_ordinary` treats special-looking strings in source
as ordinary characters. The vocabulary and its MIT license are retained for
offline runs; package dependencies are pinned in the packet's requirements.

BPE reflects the tokenizer's learned vocabulary and Unicode spelling. With
this pin, the single glyph `⍳` costs 3 tokens while the four ASCII characters
`iota` cost 2; these are spelling examples, not equivalent whole programs.
One matrix literal's one-row and wrapped variants cost 12 and 11 tokens even
though they have the same byte and code-point length. Identifier spelling,
comments and whitespace also affect BPE. It is a useful complementary text
measure with these biases disclosed, not an improved universal logical count.

## Reproduction and schema

Use an isolated environment; no global installation is required:

```sh
python3 -m venv experiments/source-metrics/.build/venv
experiments/source-metrics/.build/venv/bin/python -m pip install -r experiments/source-metrics/v1/requirements.txt
experiments/source-metrics/.build/venv/bin/python tools/test_source_metrics.py
experiments/source-metrics/.build/venv/bin/python tools/source_metrics.py --require-tokenizer
experiments/source-metrics/.build/venv/bin/python tools/source_metrics.py --require-tokenizer --check
```

The saved run used Python 3.9.6 and zlib 1.2.12. On a machine where Python's
virtual-environment bootstrap is unavailable, select another installed Python
with `venv` support; changing zlib may change compressed bytes. The
`--require-tokenizer` flag fails if the vocabulary, tiktoken version or regex
version differs or is unavailable. Without it, unavailable token counts are
null with an explicit reason. `--tokenizer none` deliberately generates a
different report without BPE counts. It must not be used to verify the saved
token-enabled artifact. Runtime tokenization makes no network request: the
tool loads the local, hash-verified vocabulary directly.

The `benchmark-source-metrics.v1` JSON binds the raw catalog and measuring tool
hashes, states text boundaries and compression/tokenizer definitions, saves
normalization probes, and maps `profiles` by canonical program key. Each
profile contains retained LOC provenance, formatter availability, the three
aggregate scopes, and full per-file selection/measurement records. Empty
program fragments cost no gzip member in aggregates; per-file records retain
the measurable gzip size of empty text. Aggregation is by exact attached-file
order, with a content-manifest digest. The CSV flattens program-level sizes
and availability, leaving unavailable numerical fields empty. The tool's
`--check` compares both generated artifacts byte for byte and writes nothing.

The separate [Mech native-owner qualification](../experiments/source-normalization/mech-v1/README.md)
adds three exact pi-digits source forms: 38 logical units for the parent, 39 for
the shared-numerator helper form and 37 for the shorter form. Native token
coverage, eighteen manual fixtures and twenty-one closed capture processes are
retained. These counts are pending browser/catalog projection; they do not change
the older Python/Julia or Clojure proofs or qualify canonical formatted LOC.
