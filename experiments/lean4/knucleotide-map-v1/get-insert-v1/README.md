# Public lookup/insert comparison — source only

This addendum preserves the sealed [alter proposal](../plan.json) and both of its
source files. It adds [Nat](sources/nat-get-insert.lean) and
[UInt64](sources/uint64-get-insert.lean) variants that replace only the counter
update expression with the ordinary public lookup/insert idiom:

```lean
let encodedKey := mapKey key
counts := counts.insert encodedKey (counts.getD encodedKey 0 + 1)
```

The key conversion is written once per completed window. The map is read for
the old count, then the resulting value is passed to insertion; no historical
map version is retained deliberately. This is a static source comparison,
not evidence that the compiler maintains uniqueness or eliminates RC/boxing.
Neither new source has been parsed, compiled, executed, counted or timed.
Application counts and all qualification flags remain null/false in
[plan.json](plan.json). No existing catalog, source, plan or measurement changes.

## What the pinned implementation actually does

The inspected public [HashMap API](../vendor/lean-4.35.0/src/lean/Std/Data/HashMap/Basic.lean)
provides `insert` at92–94 and `getD` at157–159. `insert` forwards through
`DHashMap.insert` to the standard `Raw₀.insert`; `getD` forwards through
`DHashMap.Const.getD` to `Raw₀.Const.getD`.

The pinned [map internals](../vendor/lean-4.35.0/src/lean/Std/Data/DHashMap/Internal/Defs.lean)
show that `Const.getD` (531–535) hashes/selects a bucket and traverses its chain
for the value/default. `insert` (228–238) hashes/selects a bucket, checks whether
the key is present, then replaces an existing value or inserts a new entry and
possibly grows/rehashes. The [association-list implementation](../vendor/lean-4.35.0/src/lean/Std/Data/DHashMap/Internal/AssocList/Basic.lean)
has a recursive `getD` at178–180 and `replace` at188–190.

Thus this is **two public calls, not a two-probe guarantee**. On a hit, the source
contains a lookup chain traversal plus insertion's membership and replacement
traversals. The original `Const.alter` path has membership, alteration and
post-update membership traversals. Both have multiple internal walks; lookup/
insert also has two public hash/index computations, while alter has an Option
callback and the final membership check. Inlining, specialization, common
subexpressions, collision lengths and allocation can affect the actual cost.
Source inspection establishes no winner and does not prove that either is the
fastest public idiom. Both are reasonable ordinary APIs to compare without
modifying the standard library.

The default public capacity8, standard hashing/equality, all seven complete
histogram passes and every overlapping occurrence remain identical. There is no
input-sized reservation, dense count array, query-only accumulation, custom
hash/table, raw bucket access, unsafe access or native counting helper. A query
is read only after its complete histogram. Nat/UInt64 key representation remains
the separate static hypothesis described in the [base source review](../README.md),
with no new boxing/RC evidence supplied here. The parser and generic Format.c
FFI boundary are byte-identical to the respective alter candidate.

## Count and provenance qualification plan

[source-count-plan.json](source-count-plan.json) binds all four exact application
sources and the unchanged generic Format.c to the retained native Lean count
policy, helper and prior evidence. It is a plan, not a count result. Every
written application definition, parser, key conversion, loop, binding, map call,
decode/sort/output operation and FFI declaration counts as application source.
The added `encodedKey` binding is visible independent work; it is not hidden by
packing or treated as generic support.

The retained count convention uses native Lean token spans for noncomment
physical rows plus expansion of independent `doSeqItem` statements sharing a
row. It preserves literal row layout and is not a universal logical-owner
metric. A future run must capture exact native parser output for each new source,
token/statement byte spans, diagnostics, helper/compiled-reader identity,
trusted Std imports/initializers, commands, environment and source hashes.
Existing source-specific counts or a predicted delta cannot replace that run.
The helper explicitly enables trusted module initializers; do not describe it
as a proof that no initialization of any kind occurs. Application execution
and performance measurements remain separate from parsing/counting.

The generic fixed formatter may reuse its retained C-token/count evidence only
after exact source/hash and unchanged support-role checks. Keep its submitted
size visible and exclude it from application LOC under the current generic
binding policy. All authored workload helpers remain included. No formatted LOC
or Python/Julia/Clojure logical-owner qualification transfers to these sources.
Future count fixtures must cover the actual new binary parser/control layout,
the added binding, one-line versus wrapped call spelling, comments/Unicode and
literal wrapping, while documenting the retained convention's limits.

The [base parent-authorship snapshot](../parent-authorship.json), original source
citations, suite Apache2.0 terms and unchanged Lean vendor notices remain
preserved. These new edits belong to the current Codex GPT-6 family session;
exact model version is unknown and no parent's model attribution is borrowed.
Future qualification must bind the actual compiler-loaded application, generic
formatter and standard-library inputs, retain every failed attempt and obtain
independent source/work/count review before any separate timing/admission plan.
