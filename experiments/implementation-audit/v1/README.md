# Retained implementation audit, v1

Inventory generation is a source and saved-evidence audit that runs no language
program, benchmark or compiler. Separate measured experiments are linked below. The [inventory](inventory.json) covers **all retained database profiles**, including candidates outside the requested priority
languages. It separates original-source protection, known local changes, explicit
local implementation, unresolved lineage, and the priority review scope.
It does not change canonical measurements, application LOC, source bytes,
citations, model attribution or endpoint selection.

## What “fast” establishes

The generated inventory checks whether each published fastest endpoint has the
lowest saved median in its matching language/workload **catalog pool**, and whether
each saved `seconds` field equals its retained sample median. Its input hash and
per-profile results bind these checks to one exact catalog revision. This verifies
selection arithmetic; it does **not** establish that a language implementation is
well optimized, that two named candidates explore distinct designs, or that a
globally optimal implementation exists in the pool. Some archived experiments
contain additional sources outside the catalog and need a separate intake review.

The same limit applies to expressiveness: “smallest” means lowest retained
application LOC under the current accounting policy. It is not a proof of a
minimum idiomatic implementation. The audit preserves the existing source-size
boundary and keeps performance review separate from idiom review.

The first complete source/idiom review covers all ten workloads in each of the
fifteen priority languages: [BQN](bqn-review.md), [MATLAB](matlab-review.md),
[Nim](nim-review.md), [Prolog](prolog-review.md), [APL](apl-review.md),
[Smalltalk](smalltalk-review.md), [Ruby](ruby-review.md), [Clojure](clojure-review.md),
[Ada](ada-review.md), [Futhark](futhark-review.md), [R](r-review.md),
[Uiua](uiua-review.md), [K](k-review.md), [D](d-review.md), and [Elixir](elixir-review.md).
The generated `summary.source_review_statuses` records current coverage;
other profiles explicitly remain `not-yet-source-performance-reviewed`.
Source review identifies actual designs, policy issues and concrete alternatives;
it does not certify that proposed alternatives run correctly or improve speed.

The separately requested [Mech source/compiler review](mech-review.md) covers
all ten workloads across 44 AOT, JIT and fresh interpreted profiles, including
shared source aliases. It examines general compiler lowering, application/host
boundaries and required-work evidence. It is outside the fifteen-language initial
priority order and proposes compiler improvements rather than native benchmark
executors. Its source review adds no timing observations or source counts.

New admissions have statuses distinct from static candidate suggestions:

| Exact admitted profile | Evidence and scope |
| --- | --- |
| BQN k-nucleotide `array-bqn-occurrence-frame` | [Fresh matched measurements and full-work witness](../../bqn/optimization-v1/admission-v1/results.json); 48 retained-rule application LOC / 43 physical LOC |
| Nim k-nucleotide `nim-knucleotide-preencoded-v1` | [Fresh matched measurements and source/standard-library work review](../../nim/optimization-v1/admission-v1/results.json); 72 retained-rule application LOC / 64 physical LOC |
| BQN spectral norm `array-bqn-native-sum` | [Fresh matched measurements and source-required work](../../bqn/spectral-sum-v1/admission-v1/results.json); 13 retained-rule application LOC / 9 physical LOC |
| BQN FASTA `array-bqn-bins` | [Fresh matched measurements and exhaustive lookup checks](../../bqn/fasta-bins-v1/admission-v1/results.json); modest4% median reduction,24 retained-rule application / physical LOC; full-output archive limits disclosed |
| MATLAB regex `matlab-case-compact`, `matlab-case-optimized` | [Archived correctness correction and six complete-process observations](../../matlab/optimization-v1/admission-v1/results.json); 16 / 19 application LOC respectively, with matching physical LOC; intake adds no native run |

Only catalog-bound admissions receive these statuses; an experiment or prepared
preview alone does not qualify. Predecessors are marked reviewed against an
admitted alternative, while keeping their own observations, source and evidence
limits. Qualification does not transfer to the predecessor. All admitted statuses
keep further search open; no program is labeled globally optimal. The approved
counts extend each retained rule for an exact source, without claiming a uniform
logical normalization across languages.

The [source-measurement report](../../../docs/source-metrics.md) supplies
application/submitted scopes, bytes, deterministic gzip and pinned BPE counts.
A separate [native logical-owner qualification](../../source-normalization/v2/README.md)
covers exact Python/Julia sources; it is not a replacement count for every
language. Generic Ruby worker modules have an unapplied
[embedded-support proposal](../../source-normalization/ruby-support-v1/README.md).

## Ownership and protection

The following table is the **frozen initial 1,058-profile snapshot**, before the
six admissions above. Current counts and the exact catalog hash are generated
in `inventory.json` under `summary` and `canonical_input`.

| Classification | Profiles | Evidence rule |
| --- | ---: | --- |
| Unchanged upstream | 351 | Application source matches retained upstream citation evidence, with CLBG CRLF/outer-whitespace normalization disclosed |
| Derived/adapted | 590 | Retained changes, ports or predecessor/reference lineage; original author may still be unresolved |
| Suite-authored | 71 | An explicit retained assertion identifies a locally implemented application; earlier influences and AI authorship are separate questions |
| Unknown | 46 | The retained evidence does not establish any of the other three categories |

The initial 351 unchanged upstream profiles remain protected from source rewriting. The
classifier also protects cited upstream submissions when identity evidence is
incomplete. Byte-preserving runtime-configuration review is allowed by that
scope. In particular, all **23 Ruby profiles and 19 Ruby ZJIT profiles** retain
unchanged upstream applications. Their runtime/configuration alternatives are
documented in [the existing Ruby JIT study](../../../docs/ruby-jit.md).

Ownership is not inferred from the language name, a missing citation, or a model
writing some later source bytes. The original authorship/model evidence remains
visible in each record. BQN/K/Futhark records explicitly describe local ports,
so local adaptation is established; their original implementation lineage can
remain unresolved. User-directed priority review includes these profiles without
calling them verified AI-generated programs.

Some language-specific evidence matters more than a broad catalog label:

- [Nim provenance](../../../archive/languages/nim/20261012/PROVENANCE.md) says all
  twenty drafts are adaptations, not byte-identical copies, and identifies pinned
  community collections. Preserve that attribution and resolve specific original
  files where still missing.
- [MATLAB's cohort](../../../archive/comparisons/matlab-comparison/20261010/README.md)
  explicitly documents local ports from task descriptions, twenty originally
  measured candidates and general dictionary diagnostics. The initial audit
  catalog retained seventeen profiles, before the two corrected regex admissions.
  A one-profile catalog pool does not mean only one
  design was ever attempted.
- [Prolog provenance](../../../archive/languages/prolog/20261013/PROVENANCE.md)
  records translations from retained local cohorts and deliberately identical
  compact/optimized source aliases. Later storage/linear revisions have their
  own exact retained source evidence; use that rather than assuming the initial
  draft is the published file.
- [Clojure provenance](../../../archive/languages/clojure/20261012/PROVENANCE.md)
  explicitly records locally authored adaptations and independent references.
  Published Smalltalk and Ada corrections and D translations have per-profile
  source assertions and original citations in the inventory.

## Initial review order and measured gaps

This table preserves the **original initial-snapshot review targets and ratios**,
with BQN k-nucleotide first. It is historical, not a table of today's fastest
endpoints. Its values divide the initial saved profile medians by the fastest
Mech AOT median for the same workload in that snapshot, not by the chart's fixed
global time denominator. LOC compares those same source profiles. Newly admitted
alternatives and current ratios appear in the generated inventory.

The range is `min(subject samples)/max(Mech samples)` through
`max(subject samples)/min(Mech samples)`. These ranges remain wholly above 1 for
the listed source-review targets, so observed stopwatch spread does not erase
their separation. They are **descriptive saved-sample envelopes**, not confidence
intervals, paired experimental effects or evidence that the source design caused
the whole gap. Cohort/runtime/startup differences remain relevant.

| Order | Profile to review | Time × Mech | Saved-sample envelope | LOC × Mech fast |
| --- | --- | ---: | ---: | ---: |
| 1 | BQN k-nucleotide `array-bqn-faithful` | 23.24 | 22.15–23.40 | 2.29 |
| 2 | MATLAB binary trees `matlab-compact` | 888.93 | 881.76–894.17 | 1.19 |
| 3 | Nim k-nucleotide `nim-knucleotide-optimized` | 6.98 | 6.97–7.76 | 4.24 |
| 4 | Prolog spectral norm `prolog-spectralnorm-compact` | 2,084.49 | 2,041.76–2,106.54 | 8.00 |
| 5 | APL fannkuch `fannkuchredux-apl-compact` | 4,589.65 | 4,461.79–4,670.33 | 0.64 |
| 6 | Smalltalk k-nucleotide `knucleotide-smalltalk-packed` | 171.08 | See inventory | 4.12 |
| 7 | Ruby: configuration review of unchanged submissions | Source protected | See Ruby JIT study | Source protected |
| 8 | Clojure n-body `clojure-nbody-compact` | 159.08 | 151.89–160.65 | 4.36 |
| 9 | Ada regex-redux `regexredux-ada-pcre2-heap` | 5.15 | 5.09–5.23 | 2.08 |
| 10 | Futhark k-nucleotide `futhark-knucleotide-optimized` | 17.59 | 17.06–17.68 | 3.18 |
| 11 | R fannkuch `fannkuchredux-r-array-batched` | 200.36 | 187.79–203.07 | 0.64 |
| 12 | Uiua binary trees `binarytrees-uiua-compact` | 6,662.80 | 6,573.92–6,699.82 | 0.58 |
| 13 | K fannkuch `array-k-faithful` | 133.17 | 128.04–134.79 | 0.97 |
| 14 | D reverse complement `revcomp-d-optimized` | 4.60 | 4.55–4.68 | 5.00 |
| 15 | Elixir k-nucleotide `elixir-knucleotide-optimized` | 765.24 | 763.62–769.43 | 2.76 |

The inventory independently ranks the current largest three eligible
**fastest-endpoint** gaps in each requested language. Its legacy
`initial_review_queue` field preserves language priority, but the ranked endpoint
entries are regenerated from the bound current catalog; the original BQN
k-nucleotide predecessor remains an explicit review target. Each per-profile
record also gives a ratio to Mech's smallest source. These are workload-specific
gaps, not whole-language scores or predicted gains.

## Concrete source findings and candidate questions

**BQN k-nucleotide:** the original 39-LOC application's saved 11.941989625-second
median is unchanged. The [new frame candidate](../../bqn/optimization-v1/admission-v1/results.json)
uses grouped native numeric keys in the ordinary growing HashMap, exact-token
record parsing and bounded frame scheduling. Its fresh matched median is
3.548158042 seconds versus the matched predecessor's 11.573351291 seconds
(3.26×), with 48 retained-rule LOC / 43 physical LOC. Fourteen bounded cases and
a full-input runtime witness qualify all seven widths and 874,999,961 map updates.
The boxed table stores ordinary numeric atoms; a scalar enclosure allocation per
key is not required. Growth still starts at the native default and doubles.
The [old cohort review](../../../archive/comparisons/array-comparison/all-20261009/README.md)
continues to disqualify the older query-only design. The old source's six-byte
header-prefix concern and unresolved original lineage/model remain explicit;
the replacement's parser/work proof does not retroactively qualify the old one.
Further rolling/chunking, copying and scheduling alternatives remain scoped
questions rather than claims of an optimal implementation.

**BQN spectral norm:** the [new candidate](../../bqn/spectral-sum-v1/admission-v1/results.json)
changes the two row reductions from `+´` to the existing general `•math.Sum`
primitive. Four application functions, twenty AtA iterations, forty dense
products and 1.21 billion coefficient evaluations at N=5500 remain source-owned
required work. Seven bounded inputs and three full observations per candidate
support admission at 13 retained-rule LOC / 9 physical LOC. The final-dot
alternative and all observations remain available. The selected 1.513197125-second
median establishes a retained-candidate result, not global optimality or a precise
effect estimate between closely timed alternatives.

**MATLAB:** the [corrected regex sources](../../matlab/optimization-v1/admission-v1/results.json)
restore case-sensitive `regexp` in place of `regexpi`. Intake replays archived
2026-10-12 sources and three complete-process samples per corrected profile; it
does not constitute a new native timing experiment or attribute the old source
to the current audit model. The 16/19-LOC compact/optimized sources have exact
[source-count reviews](../../matlab/optimization-v1/regex-source-counts.json).
Separately, cell-tree construction/traversal and allocation have a
large enough saved gap to deserve representation and ordinary worker review,
while retaining every distinct equal-size node and prescribed lifetime. The
historical constructor-unrolled source and pointer-identity probes already
exist; no measured new tree implementation is claimed.

**Nim k-nucleotide:** seven native width workers, rolling keys and private growing
maps already existed. The [new candidate](../../nim/optimization-v1/admission-v1/results.json)
uses standard `sequtils.mapIt` once to preencode bytes and `Table.mgetOrPut(...).inc`
for mutable-slot updates. Its fresh median is 2.606080417 seconds versus the
matched parent's 3.459123375 seconds, with the same 72 retained-rule LOC / 64
physical LOC. The parent's historical 3.585653417-second median is unchanged.
Default capacity/growth and every required window remain; resizing can re-probe,
so this is not a claim of exactly one probe per occurrence. Generic/native target
pairs produce identical executable bytes, giving no evidence of a CPU-target
benefit. Original predecessor authorship gaps remain unresolved.

**Prolog, APL, Smalltalk and Clojure:** Prolog spectral norm has recursive numeric
row loops and per-element transpose dispatch; test specialized ordinary source
loops and bounded row workers while retaining all forty dense products and the
required function structure. APL fannkuch's scalar label/branch loop invites an
idiomatic bounded-array candidate with every flip preserved. Smalltalk nucleotide
already updates mutable Associations through one lookup; focus on serial-width
scheduling, byte handling and its THREE prefix parser. Clojure n-body constructs
and destructures `[[0 dx] [1 dy] [2 dz]]` for every pair in the fifty-million-step
loop despite primitive body arrays. Scalar primitive updates or a primitive
indexed loop are a concrete allocation/boxing candidate, with exact pair order
and all steps retained. None is a measured speedup in this audit.

**Ada, Futhark, R, Uiua, K, D and Elixir:** Ada regex already uses PCRE2 JIT and
borrowed heap views; review source-owned scheduling and substitution buffers.
Futhark nucleotide already has piece maps, rolling keys and bounded reserves;
inspect generated copying and reserve granularity, plus its raw substring THREE
parser. R fannkuch already has eight workers and 8192-rank batches; inspect the
per-flip `rep`/`ifelse` gather allocations. Uiua tree source aliases do not show
distinct optimization strategies; review ordinary recursive record/box allocation
and bounded independent tree work. K fannkuch already has eight rank-range
callbacks; review list prefix copying and callback/state overhead. D reverse
complement retains both the full joined input and a full output appender;
consider ordinary in-place/record streaming and adversarial FASTA boundaries.
Elixir nucleotide uses a binary slice and persistent-map update for each window
on seven serial passes; rolling integer keys and ordinary bounded task/table
choices are concrete candidates. Its compact/optimized bundles are identical.

The reviewed Prolog spectral, APL fannkuch, Uiua tree and Elixir nucleotide pairs
each have **two profile labels but one distinct retained source bundle**. Their
saved observations remain distinct where actually measured, and their alias
labels do not count as evidence of two optimized designs. Exact candidate counts
and hashes are available for every workload/language pool.

The [remaining expressiveness review queue](expressiveness-review.md) inventories
all other local/derived language pools, distinguishes aliases from separate designs,
and records concrete boundary and normalization questions.

## Candidate acceptance checklist

1. Bind the original source, citations, exact application/helper/support hashes,
   runtime and configuration. Preserve the original unchanged Game submission.
2. State a concrete algorithm-preserving source/runtime hypothesis and retain an
   isolated complete candidate. Profile labels and copied aliases are not design
   alternatives. Document uncertain lineage without inventing AI authorship.
3. Review ordinary native-language idioms, APIs, primitive representation,
   allocation, copying, lookup count, numeric operations and bounded scheduling.
   Separate diagnostic startup/kernel observations from whole-process rankings.
4. Review compact and idiomatic alternatives independently of speed. Count all
   workload helpers under the common application boundary; generic bindings do
   not authorize moving a workload executor outside the named language.
5. Check arbitrary small/adversarial cases and semantic required work as well as
   full output: record token boundaries, every map update, actual allocations and
   lifetimes, all permutations/flips, ordered substitutions and numeric rules.
6. Any later timing work must use the established guarded full-size fresh-process
   protocol, shuffled sequential rounds, bounded workers and matched controls.
   The inventory generator performs none; separately documented experiments above
   retain their own execution evidence. Keep every valid observation and its source identity.
7. Compare the complete qualified candidate pool, retain speed/source-size
   tradeoffs, and report “fastest measured retained candidate” or “fewest retained
   application LOC.” Do not certify global optimality or assume the most recent
   locally authored implementation is representative of the language.

## Reproduction

`python3 tools/audit_owned_implementations.py` regenerates only this inventory.
`python3 tools/audit_owned_implementations.py --check` verifies it without writing.
`python3 -m unittest discover -s tools -p test_owned_implementations.py` checks
unknown-origin handling, upstream protection, application/support identity,
explicit-local versus translation lineage, input preservation and direct Mech
ratio arithmetic, exact admission binding, archived-versus-new observation status,
and separately scoped Mech compiler review. These are metadata tests; they execute
no language workload.
