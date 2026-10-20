# Native logical source ownership, v2

This additive qualification supplies **new native logical counts for 52 exact
retained application sources**: 18 Python, 17 Julia and 17 Julia AOT profiles.
It uses CPython's native AST/tokenizer and Julia 1.13.1's native JuliaSyntax
syntax nodes with exact UTF-8 ranges and a lossless token stream. It does not
change canonical LOC, source bytes, timings, eligibility, minima or charts.
The catalog identifies 17 of these profiles as AI-adapted Julia AOT derivatives
and 35 as upstream implementations; no suite-authored Python profile exists in
the current catalog. Other languages remain unqualified under this new metric.

The versioned policy is `logical-source-owners.v2-python-julia`. Each independent
native statement, binding, definition or control header costs one unit. Written
closing delimiters, structural separators and literal continuation rows cost
zero. A true tuple/destructuring binding with one initializer costs one;
independent semicolon-separated statements remain separate; chained written
assignments charge their separate targets. A matrix literal costs one enclosing
binding/expression regardless of row wrapping. Pure expression functions,
lambdas, array primitives, comprehensions, reductions and function composition
stay expressions; no scalar loops or implicit operations are invented. A block
function has a header and independently written body owners. Decorators and
whitelisted Julia annotation/task macros belong to their written payload.
Macro expansions and installed implementation code are outside the metric.

These choices differ from old significant-row and header/body/close policies.
For example, native ownership gives Python spectral norm #8 **32** units versus
25 retained LOC; its line 25 contains three statements and line 34 contains a
loop header and two updates. Julia regex-redux #3 has **19** units versus 38
retained LOC: the nine-pattern tuple is one constant binding, and written `end`
tokens add no units. Julia fannkuch #1 is **59** versus 69, with packed bindings
still counted separately. Counts differ for 50 of the 52 profiles. These are
measured source-owner counts under this policy, not proof of minimum possible
program size or universal language neutrality.

`qualification.json` records every program's old/new count, source identity,
policy, native owner ranges, coverage digest, parser/tool pins, native syntax
fixture results and source-bound priority-language findings. Every significant
native token is covered by an owner or explicit zero-unit syntax; there are
zero unowned significant tokens in this exact subset. Native owners can nest:
an enclosing function/control range covers its syntax while its child
statements retain separate owners. The smallest containing owner determines
token coverage. Zero-unit syntax owners are visible and are not physical-row
fallbacks.

The application boundary uses the current reviewed file roles and embedded
support line ranges. For native parsing, excluded support is replaced with the
same number of ASCII space **bytes**, preserving original UTF-8 byte offsets
and line endings. The full source and projected source hashes are both saved.
No projected source is executed. Standalone reusable support files are excluded,
while workload-specific helper code remains counted. Raw bytes in the earlier
[source metrics packet](../../source-metrics/v1/README.md) use its separately
documented exact-text fragment representation, so its application text hash is
not the native projection hash used here.

The native Julia capture accepts every valid captured input and rejects a
deliberately unfinished function. It does **not** include, evaluate, lower or
macro-expand any benchmark input. Native syntax acceptance establishes parsing,
not name resolution, macro semantics or successful program execution. Existing
benchmark validation remains separate.

The 20 qualification cases include:

- Native Python and Julia semicolon-packed versus expanded assignments.
- Native Python nested-list and Julia matrix literals with layout changes;
  each remains one binding.
- Packed versus expanded loop bodies, literal punctuation, keyword semicolons,
  pure expression functions and explicit multi-statement blocks.
- Quoted Julia code treated as data, plus supported macro wrappers.
- Full real Julia fannkuch sources before and after unpacking existing
  semicolons, with accepted variants and equal logical counts.
- A real Julia pi-digits tuple binding with five targets and one initializer,
  still one logical unit.
- A second native-unparsed, syntax-accepted layout of every real Python
  application, with exact AST equivalence and equal owner counts.

The regression suite also rejects source-hash drift, corrupted native tree
edges, unsupported macros and unsupported Python statement/assignment-expression
forms. Unknown syntax fails qualification; no physical-row substitution occurs.
The qualification is for the exact recorded hashes and supported forms, not a
generic certificate for every construct in either language.

## Retained evidence and reproduction

`native-trees.json.gz` contains the native syntax trees and lossless tokens;
`native-capture.json` binds their result, exporter, official distribution,
command and parser executable. The capture used inherited environment settings
with startup/history disabled and one Julia thread; unrecorded inherited
environment is a reproducibility limitation. `runtime-download.json` records
the official Julia archive URL, size and SHA-256. The verified archive was
extracted only into ignored `.build` storage and then removed. No runtime
archive or binary is committed.

Replaying the native evidence requires no Julia process:

```sh
python3 tools/test_logical_source_units.py
python3 tools/logical_source_units.py --check
```

The saved Python parser is CPython 3.14.8, with executable and standard-library
AST/tokenizer files pinned in the report. Reproduction under a different parser
version deliberately changes that binding. To refresh Julia evidence, restore
the exact official archive recorded in `runtime-download.json`, verify its
SHA-256, and run during a quiet measurement window:

```sh
python3 tools/logical_source_units.py --refresh-julia --julia experiments/source-normalization/.build/julia-1.13.1/bin/julia
python3 tools/logical_source_units.py --check
```

Refresh starts one bounded 30-second parse-only process. The default command
only replays saved evidence. The new counts stay separate from the complete
catalog and source-metrics UI pending review and broader language coverage.

The priority-language audit links actual source lines and pins the old counter
implementations. It identifies Mech matrix-layout costs, F# multiline literal
layout costs, and written-close units in Kotlin, TypeScript, Elixir and APL.
Those findings establish concrete policy differences; this packet does not
claim fresh native parser certification or replacement counts for those
languages. A consistent extension needs language-native acceptance, complete
source ownership and the same reviewed application boundary before comparing
new cross-language minima.

Primary parser references: [CPython AST](https://docs.python.org/3.14/library/ast.html),
[Julia ASTs](https://docs.julialang.org/en/v1/devdocs/ast/), and the
[Julia 1.13.1 native syntax implementation](https://github.com/JuliaLang/julia/tree/v1.13.1/base/JuliaSyntax).
