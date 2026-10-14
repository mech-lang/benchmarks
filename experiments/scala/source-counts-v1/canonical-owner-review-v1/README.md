# Scala application source ownership review

All ten exact Scala application sources now have complete canonical owner maps
under `canonical-source-units-20261012-approved-rule-v2`. Their original bytes,
native ASTs and physical token streams remain unchanged. This packet adds a
narrow reviewed adapter and a separate manual source-accounting audit; it runs
no compiler, JVM or benchmark subject.

| Application | Canonical units reviewed | Physical code rows |
| --- | ---: | ---: |
| Binary trees | 42 | 41 |
| Fannkuch-redux | 123 | 122 |
| FASTA | 54 | 52 |
| K-nucleotide | 97 | 84 |
| Mandelbrot | 55 | 53 |
| N-body | 100 | 100 |
| Pi digits | 34 | 32 |
| Regex-redux | 48 | 45 |
| Reverse-complement | 49 | 46 |
| Spectral norm | 60 | 59 |

The [application review JSON](application-owner-review.json) binds every source
and owner artifact and records **every occupied source row**, its exact text,
assigned owner event IDs, reviewed units and rationale. The
[independent audit](../../../../tools/scala_application_owner_review.py) contains
the source-keyed decisions and replays the entire row accounting. It verifies
all owner source slices and the complete unique token partition, rather than
accepting a projected total. A row with packed headers/statements, a continued
signature, or a composed method value has an explicit adjustment. Literal/data
rows retain their physical accounting. The ten totals reconcile with that
separate manual review.

Producer projections keep `normalized_loc=null`, `canonical_LOC_admitted=false`
and `chart_admission=false` for independent admission review. The manual audit
has finished for all ten sources. These source counts establish no claim about
compilation, runtime work, timing or chart admission.

## Narrow additions to the frozen projector

The [reviewed adapter](../../../../tools/scala_source_units_reviewed.py) loads
the exact [frozen first projector](../../../../tools/scala_source_units.py),
SHA-256 `66f13f502bf494a84b7c11c3805114eacd5349db5d6562441bd1e15f8b4e0bd1`.
It retains that projector's original source, graph, token and UTF-16/UTF-8
checks. The [result review](results-v1/review.json) binds all 51 new owner
artifacts and independently replays the original 80 native captures. The old
[candidate packet](../canonical-projection-v1/README.md) remains intact.

The application review resolved these actual source forms:

| Form | Native evidence | Authored accounting |
| --- | --- | --- |
| K-nucleotide `code` method's explicit match | `Match` 38, UTF-16 `[543,728)`; cases 41, 45, 49, 53, 57 | Combined method/match header 1; five case headers and five body expressions; one written match close: 12 units. |
| K-nucleotide chained `map` and `sortBy` | Empty-selector `Match` 454 `[2655,2708)` and 466 `[2735,2775)` | Two actual braced tuple callbacks, each header/body/close: 6 units. The `.toArray.sortBy` continuation belongs to the second header. |
| K-nucleotide row output callback | Empty-selector `Match` 494 `[2859,2987)` | Tuple-pattern callback header, output call, written close: 3 units. |
| Regex replacement callback | Empty-selector `Match` 174 `[1626,1756)` | Tuple-pattern callback header, actual assignment, written close: 3 units. |
| K-nucleotide and reverse-complement `else if` | Native nested `If` with the actual preceding `else` token | One joined `else if` header. A previous branch's written close and an unbraced body remain separate units. |

Each actual case-body `Block` begins at the written `=>` token. The adapter
therefore assigns that arrow to the case/callback header, walks the block's
native statements, and adds no boundary for the parser-created container.
Only physical brace tokens can create a close. The explicit selector match
follows the same joined expression-header accounting already exercised by
the [Kotlin when fixture](../../../../tools/qualification/test_kotlin_source_units.py)
and [Elixir case fixtures](../../../../tools/qualification/test_elixir_source_units.py).
A partial-function callback has no written `match` header, so none is invented.

The original pattern-callback fixture is now explicitly reviewed at three
units. Its old review contract is preserved. The 34 previously concrete fixture
counts remain unchanged. Guarded cases, multiple-case partial functions and
unused pattern forms remain unsupported; they cannot be admitted merely by
matching a broad AST node name. The guarded match fixture therefore remains a
review case.

## Application review details

- Binary trees: two constructor fields remain separate from the class header;
  two scalar expression methods remain composed; anonymous class and method
  bodies retain all written closes and work.
- Fannkuch-redux: plain constructor formals and parent-type continuation are
  header content. Every packed assignment, loop, condition and final value is
  retained. The ordinary identifier `end` is not an end marker.
- FASTA: the seven ALU literal rows and the three- and two-row array argument
  groups remain physical data rows. Three unbraced controls expose their body
  units; the expression-bodied `header` method stays composed.
- K-nucleotide: all five explicit match cases, both callbacks in the sorting
  chain, the row-output callback, loops, updates and joined `else if` are
  separately visible. Pattern bindings do not become additional declarations.
- Mandelbrot: the worker callback, anonymous `Callable`, method, nested loops,
  PBM update and all actual closes are retained; scalar callbacks stay composed.
- N-body: all fourteen written array-initializer rows remain. Every method,
  loop, update and final expression has an owner; no row adjustment is needed.
- Pi digits: both division declarations, both branches and all updates remain;
  the padding loop has an independent body call.
- Regex-redux: nine literal-array rows, both anonymous classes, the counting
  loop, replacement assignment callback and shutdown path remain visible.
- Reverse-complement: the mapping expression callback remains composed, the
  nested `emit` method and all output operations remain visible, and the packed
  `else if` line has exactly close/header/body owners.
- Spectral norm: the wrapped formal-parameter list stays in one header; the
  worker callback and anonymous class, scalar transpose selections, all loops,
  updates and shutdown path remain visible.

The [14 adapter tests](../../../../tools/test_scala_source_units_reviewed.py)
cover exact native cases, chained callbacks, actual assignments, joined `else
if`, all ten complete maps and negative guarded/multiple-case, missing-close,
arrow-span and discarded-body cases. Synthetic body metadata cannot erase work
or invent a close. The [six manual-audit tests](../../../../tools/test_scala_application_owner_review.py)
reject altered totals, missing body ownership, changed token assignments,
collapsed data rows and premature admission. The earlier 30 projector tests
also passed. All 50 tests are pure and bounded; no runtime closure is rehashed.
