# Native formatter expansion: source-only plan

This packet prepares a **later, separate formatted-source qualification**. It has
run no formatter, compiler, language parser, benchmark or application. Counts,
outputs and preservation receipts for new work are explicitly unavailable. It
changes none of the catalog, publication assets, retained LOC, logical-owner
policies, source partitions or timing samples.

[The deterministic preparer](prepare.py) produces [the Nim plan](nim-plan.json)
and [the Clojure plan](clojure-plan.json) from the exact current catalog. Plans pin
source text hashes, current roles, existing formatter evidence and required
runtime/configuration artifacts. Re-running it is a read/hash operation only:

```sh
python3 experiments/source-formatting/v1/prepare.py
```

The prepared catalog contains 1,065 profiles. Nim has **21 profiles / 22 attached
source units** (34,219 UTF-8 bytes), including twenty already qualified formatter
profiles and one newly admitted nucleotide candidate. Clojure has **21 profiles /
22 attached source units** (41,446 bytes), none with admitted formatter totals.
These are source inventories, not new timing observations.

## Nim: the immediate additional target

The only missing Nim total is
`knucleotide:nim-knucleotide-preencoded-v1`, exact source SHA-256
`b8373233e975e0a09fcab239b827c6535d8b024b2c7ec4d60ac4d34820bb745b`.
Its retained 72 normalized / 64 physical LOC and saved samples remain unchanged.
The archived parent formatter total of 66 is evidence for the parent source only;
it is **not** a predicted or admitted count for the child.

The restored official distribution already contains `bin/nimpretty`, verified by
reading bytes, without launching it. Its SHA-256 is
`cdf07fca977cfcfbeceb0189317657280ea89b11bed7220524bfef66db862cd5`, identical to
the archived formatter. The distribution is Nim **2.2.12**, source revision
`8e8fbf60693418dc95bb0d762fd660231d08a583`; the formatter has its separate **0.2**
version. [The restoration receipt](../../nim/optimization-v1/runtime-restoration.json)
binds the release archive and distribution-tree pins, while
[the saved version receipt](../../nim/optimization-v1/runtime-version.json)
binds the compiler version. Preparation verifies selected formatter/parser bytes,
not a new complete tree verification. The native stage must reverify its actual
runtime closure and record `nimpretty --version` afresh.

The [pinned language-project source](https://github.com/nim-lang/Nim/blob/8e8fbf60693418dc95bb0d762fd660231d08a583/nimpretty/nimpretty.nim)
sets autodetected indentation and line length 80 by default. `--out` and `--outDir`
select separate destinations; omission overwrites input. `--stdin`, `--indent`,
`--maxLineLen`, `--version` and `--help` are implemented. The plan uses the exact
existing explicit arguments `--indent:0 --maxLineLen:80 --out:{output} {input}`,
one isolated file at a time. No recursive directory input or in-place output is
needed. Unknown options can print help and exit successfully, so exit zero alone
cannot establish that formatting happened.

The existing [configuration](../../../archive/qualification/nim/records/formatted-nim-plan-v1/jobs/actual-plans-v1/native-formatter-config.json)
is SHA-256 `b80b9a5c52aec06be91bca55c20a29487db5f7aff1e3248392d1ff8612199d86`.
It pins formatter, layouter, lexer, parser and syntax adapter sources. Native
formatting parses source and emits layout; it does not enter the semantic
compiler/application execution pipeline. The syntax adapter explicitly rejects
source filters in the formatter build. The formatter's `finalCheck` reparses its
output, but its call to `goodEnough(newAst, origAst)` is commented out: **native
parse acceptance is not native AST equality**. This source observation is why the
new stage needs an explicit preservation gate rather than inferring equality
from a zero exit code.

Autodetected indentation and native layout heuristics remain part of this
formatter-specific metric. No statement-packing or matrix-wrap invariance is
claimed for formatted physical lines. The separate logical-owner option answers
that different question.

## Preserving the earlier twenty Nim observations

The plan reads and rehashes each retained formatted output and verifies the
current application sum against the saved total. It stores per-file original
source, formatted-output, formatter/configuration, process/version and physical
counter evidence hashes. These are **replayed metadata/output bindings**, not new
native runs or a new claim that every old tool/runtime dependency was rehashed.

The optimized pi-digits profile is an important boundary case. Its
`gmp_ops.nim` generic binding is still attached and has eighteen archived
formatted physical lines, but its **current role is excluded runtime support**.
The main contributes 61 formatted application lines; the previous attached
bundle total was 79. A replay must preserve that difference. Reusing the old
`application-helper` evidence role without the current partition would count the
support incorrectly. All other Nim scopes and any future workload-specific
helpers remain included according to current reviewed roles. This packet finds
no embedded support ranges in the retained Nim files.

## Required next Nim native stage

1. Acquire the common timing lock nonblocking before native work. Reverify the
   exact catalog/source, restored tool/runtime and worker/configuration pins.
   Use bounded serial owned process groups; record commands, environment, cwd,
   raw stdout/stderr, exit/cleanup status and all artifact hashes. An isolated
   empty home/config directory prevents incidental user configuration. Copies
   are writable; original catalog/program sources remain read-only.
2. Format the new exact main to a separate fresh output. Format that output
   again with the identical options to another fresh output. Require byte-level
   idempotence; preserve both outputs and process receipts. Run a few source-only
   adversarial fixtures for packed statements, multiline matrices, nested block
   comments, comment-looking strings/raw/triple strings, pragmas and Unicode.
3. Build a **verification helper**, separately identified from `nimpretty`, from
   the same pinned compiler parser/lexer modules. It must only parse/tokenize
   original and formatted source, never load application imports, run semantic
   analysis, evaluate `static`/macros, compile input or call FFI. Reject source
   filter syntax. Compare ordered AST kinds, child structure, identifier/operator
   identity and literal values with source positions/comments excluded; serialize
   both trees and an exact comparison decision. Any normalization such as a
   singleton statement-list wrapper needs a named, reviewed rule and fixtures.
   Do not copy the disabled `goodEnough` result as if it ran inside `nimpretty`.
4. Independently compare ordered significant native token payloads, retaining
   literal contents and pragma/operator tokens. Layout can differ; changed
   lexical payloads need a narrow reviewed formatter-specific explanation, or
   fail the source. AST equality catches indentation/binding changes that a
   whitespace-insensitive token stream alone could miss. Comments get an explicit
   preservation/change record; parse success alone supplies neither proof.
5. Count formatted rows under the **same retained physical policy**:
   `nonblank-noncomment-physical-lines-v1`, diagnostic-free exact Nim lexical mask.
   The original physical-only shim and its import closure are bound by the saved
   plan. Restore the exact archived dependencies in an isolated namespace before
   import; do not silently use a later `canonical.py` with a different hash.
   Check mask length and all row boundaries, count nonblank masked rows and
   retain mixed code/comment lines and multiline literal rows. No source-owner
   or semantic normalization function may contribute to this physical count.
6. Produce a separate qualification record binding input, first/second output,
   native AST/tokens, counter, version/config/tool/runtime, process and review
   hashes. Missing/rejected/unstable outputs leave the count null with a reason.
   A later guarded overlay may add only this source's formatter metadata and
   reselect the formatter baseline; it must prove all source, retained/logical
   counts and timing observations unchanged. Current publication admission is
   false. The earlier twenty totals remain untouched.

A cold helper build is the uncertain cost. Reserve **30–90 seconds** for build,
version probe, fixtures and parse-only verification; formatting this small main
itself should be tiny (the archived parent formatter process took about 10 ms).
That estimate is planning guidance, not a measurement of the new stage. No
benchmark rerun is needed for a source-formatting-only overlay. Once the helper
is built, the additional main should need only a short serial window. The old
22-source replay can be optional hardening, rather than delaying the one new gap.

## Clojure: genuine formatter, explicit community provider

The next useful expansion is all **21 exact retained mains**, plus the shared
`clbg.support` unit under submitted/excluded scope. Runtime/source aliases are
kept as profile records but a repeated source is formatted once by its source
hash. No future compact experimental source enters this manifest automatically.

[cljfmt 0.16.6](https://github.com/weavejester/cljfmt/blob/0.16.6/README.md) is a
genuine community source formatter. Its documented aim is to repair formatting
with limited changes to existing structure; that can retain packing/layout
choices. Its EDN configuration route is suitable for an isolated worker, while
code configuration is inappropriate here. For full source layout the project
itself points to zprint. These are community tools, not the Clojure core reader
or an official compiler formatter.

**Proposed first tool: zprint 1.3.0**, subject to artifact/dependency restoration
and static review. The [release](https://github.com/kkinnear/zprint/releases/tag/1.3.0)
provides source-formatting distributions. The project's
[reference](https://github.com/kkinnear/zprint/blob/main/doc/reference.md)
documents whole-source string formatting, a fixed width, comment handling,
configuration isolation, optional preserved newlines and sorting. This plan
selects source-text formatting, not printing evaluated values or loaded
functions. Before any run, pin the exact release's code/API and resolved
JAR/native dependency closure; the browsed development reference is design
evidence, **not** a reproducible release pin. Candidate artifact/config hashes
remain null until restored. No package is installed by this preparation.

The proposed configuration contract is width 80, deterministic serial processing,
no ambient configuration, no source-controlled executable directives or function
hooks, no sorting/reordering of maps/sets/ns references, no source reader-macro
rewriting and no load/require of input code. Each option must be checked against
that exact release, and the fully materialized defaults/configuration hashed.
Use the source-file API; do not turn forms into runtime values and pretty-print
those, because comments, reader spelling, metadata and form order can disappear.
Where the release cannot enforce this contract, leave the source unavailable or
choose a separately reviewed formatter/configuration.

The existing [formatted admission overlay](../../../archive/validation/loc-normalization/20261013/formatted-loc-v1/overlay.py)
accepts `provider=language-project` only. **Clojure community formatting therefore
needs a separately reviewed provider/schema policy** before admission. Do not
make it pass by relabelling zprint/cljfmt as Clojure core. A genuine native
executable is one distribution form, not evidence that a project is the official
language implementation. The UI metric can remain qualified formatted LOC if
its tool/provider/style is explicit and the qualification policy is extended;
that decision belongs to the later additive overlay review.

## Required Clojure evidence and fixtures

Format every exact source unit twice and require byte idempotence. Preserve
input, outputs, complete raw receipts and configuration/tool/runtime/dependency
hashes. The existing pinned Clojure 1.12.6 and tools.reader 1.6.0 restoration can
supply a separate native acceptance check with read-eval disabled, empty custom
readers, no macro expansion and no application source on the classpath. Accepting
both files is necessary but insufficient.

Compare a lossless source-node/token sequence, ignoring only explicitly allowed
trivia. Keep every source form, literal/regex/character spelling and value,
metadata/type hint, collection order and reader prefix. Preserve comment text or
record an explicit policy for reflow; comments do not become executable rows.
Native reader values alone are insufficient because generated anonymous-function
gensym identities and reader-generated location metadata differ, while metadata
or source spelling may be lost. Any structural normalization of native values
must be narrow, versioned and covered by fixtures. The source-preservation test
must reject reordered expressions/maps/sets even when ordinary collection value
equality says they are equal.

Count nonblank, noncomment **physical output rows** with comment-aware source
nodes. Mixed code/comment rows count; multiline string/docstring/regex rows count
as source, even if their text begins with a semicolon. Commas, whitespace and
comment-only rows do not count. Retain per-row/range evidence and fail on unknown
reader forms, unresolved lexer diagnostics or incomplete coverage. This physical
counter is separate from Clojure v1's logical-owner counts.

Required paired fixtures include packed top-level definitions, packed function
body calls, independent `let` bindings, destructuring, matrix/vector row wrapping,
`if` versus explicit `do`, nested collection literals, syntax/comment punctuation
inside strings/regex/character literals, metadata, anonymous reader functions,
Unicode symbols, CRLF and final-newline cases. Include invalid input and disabled
reader-eval/tag/config/directive probes. Source-only fixture acceptance does not
certify whole-language parsing or macro semantics. Formatting variants need not
have the same physical count; report any retained layout sensitivity explicitly.

A first cold JVM/dependency restore can dominate this work. Budget **2–5 minutes**
for restoration/review and **30–90 seconds** for a warmed serial formatting,
idempotence and native acceptance batch over 22 small units, plus offline review.
These are estimates pending pinned artifact selection; no Clojure formatter
process or new formatter count is claimed now.

## Other priority-language paths

| Language | Practical path and next qualification issue |
| --- | --- |
| Elixir | Twenty existing native `mix format` totals are already qualified. Preserve them; audit coverage of any later exact source separately. |
| Futhark | Project [`futhark fmt`](https://futhark.readthedocs.io/en/stable/man/futhark-fmt.html). The manual explicitly documents sensitivity to existing line breaks, so it is useful formatted LOC with a layout caveat, not canonical logical normalization. Native C support/host files need their own formatter or remain excluded according to current roles. |
| Uiua | Project [formatter API](https://docs.rs/uiua/latest/uiua/format/index.html) and `uiua fmt`. Pin the measured release and full formatting configuration. Glyph/name conversion needs native token/AST equivalence, not spelling equality alone. No qualification here yet. |
| Ada | AdaCore [`gnatpp`](https://learn.adacore.com/courses/GNAT_Toolchain_Intro/chapters/gnat_tools.html) or a separately pinned GNATformat distribution. Freeze casing/layout/project switches and parse complete `.ads`/`.adb` source sets without elaborating input code. |
| D | Community [`dfmt`](https://github.com/dlang-community/dfmt), backed by its own parser. Freeze release/submodules and EditorConfig; no ambient parent configuration. Review the community-provider gate and verify native parse/token preservation. |
| R | Community [`styler::style_text`](https://github.com/r-lib/styler) / `style_file`. Pin package/runtime/dependencies and exact style; source parsing must not source/evaluate the input. Community-provider review required. |
| Ruby | Community [`SyntaxTree`](https://github.com/ruby-syntax-tree/syntax_tree) source formatter. Pin release/runtime, preserve AST/comments/magic directives and disable executable plugins. Original Game sources stay byte-identical; separate formatted copies are allowed. Community-provider review required. |
| Prolog | Native [`portray_clause`](https://www.swi-prolog.org/pldoc/man?predicate=portray_clause/1) pretty-prints terms/clauses, including variable-name decisions. It is not automatically a lossless whole-file formatter: comments, directives/operators and original variable names need explicit preservation. Do not admit its default term serialization as source-format evidence. |
| BQN, K, APL, Smalltalk, MATLAB | No complete reproducibly pinned source-formatter route is established by this packet. Runtime value printers, editor indentation and workspace/method serializers must not be renamed universal source formatters. Investigate exact implementations and file/workspace boundaries separately; retain explicit unavailability meanwhile. |

All routes require complete included application/helper coverage. A trustworthy
partial result remains partial; formatter rows, native logical owners and raw
UTF-8/gzip/BPE source sizes continue to describe distinct properties.
