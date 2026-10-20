# Futhark k-nucleotide: library-table policy correction

Static review, 2026-10-20. No Futhark/JVM execution, compiler invocation, native
test, timing, large archive download or canonical-data edit was performed by this
review. Only small primary policy, version, license and source files were
retrieved. [review.json](review.json) records the exact-source decision and
proposed additive correction; its `applied:false` describes this review artifact,
not the later catalog state.

**The two currently retained Futhark k-nucleotide profiles are ineligible under
the current required-algorithm policy.** Their shared `stdlib/hashmap.fut` is the
cohort's own complete table implementation. Calling it reusable support does not
satisfy the official requirement to use a built-in or library table. Preserve
their complete sources, source counts, observations and historical audit; remove
their eligibility for default performance/source-size comparisons through a
separately reviewed additive transform. No replacement has yet been qualified.

## Rule and exact-source finding

The [official task description](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/knucleotide.html)
explicitly says: “Please don't implement your own custom "hash table" - it will not
be accepted.” It separately requires table lookup/update accumulation for each
reading frame and growth from a small default. The current policy snapshot is
retained in [primary/knucleotide-description.html](primary/knucleotide-description.html).
This finding applies the currently stated rule; it makes no unsupported claim
about when the wording first appeared.

| Retained profile | Main SHA-256 | Saved median / application LOC | Shared table use |
| --- | --- | --- | --- |
| `knucleotide:futhark-knucleotide-compact` | `83dda7809af2c2884e0e977d3a90ad11b6c04f63593aa2860d1f9ed29090b06c` | 29.069172291 s / 37 LOC | Import line 2; `empty 16` line 10; `increment` line 12 |
| `knucleotide:futhark-knucleotide-optimized` | `86279a96aff35f6dc90a7ffff727c33cf9da642e647856e341139836aea97dc6` | 9.040219375 s / 54 LOC | Import line 2; `empty 16` line 17; `reserve` line 19; `increment_slots` line 22 |

The exact shared table is
[`archive/comparisons/additional-languages/20261009-full-suite/stdlib/hashmap.fut`](../../../archive/comparisons/additional-languages/20261009-full-suite/stdlib/hashmap.fut),
SHA-256 `0c1b898695cbe779412defe8208936b59631d4689f2b0230175575e5fe6ddcbf`.
It supplies the storage type and initial arrays (lines 2–5), hash mixing (6–9),
linear probing (10–13), lookup (14–17), insertion (18–23), doubling/rehashing
(24–27), load-factor decisions (28–39), reserve (41–43), and direct slot updates
(45–50). These are table internals, not a thin binding to an independently
maintained library. Neither main imports a package-provided hash table.

The cohort [README](../../../archive/comparisons/additional-languages/20261009-full-suite/README.md)
and [provenance](../../../archive/comparisons/additional-languages/20261009-full-suite/provenance.json)
describe local Futhark ports and locally supplied data operations. The
[old source audit](../../../archive/comparisons/additional-languages/20261009-full-suite/audit_sources.py)
asserts all seven passes and every update, and lists this local table as support;
it never checks the prohibition on a custom table. General collision/growth tests
can establish correctness of that code, but do not establish eligibility.
The earlier [implementation review](../../implementation-audit/v1/futhark-review.md)
left this as an admission question. The primary rule plus complete local table
implementation now settle that question for these exact profiles.

The archived `sources/knucleotide.fut` baseline also imports the same table
(lookup/put at lines 18–19; saved median 16.7053486 s). It is not a current
catalog profile and must not become a fallback after the two endpoints are
excluded. Its raw evidence remains preserved. Parser concerns about THREE token
boundaries, absent/short records and later records are additional qualification
work for a replacement; the confirmed exclusion here does not rely on those
untested cases. Original authorship/model gaps remain unchanged.

## Additive correction and regression checks

Bind the two exact main hashes and shared table hash before changing eligibility.
Add a source-bound policy decision with `eligible_for_chart: false`, identifying
the custom-table rule and this review. Preserve every existing sample, timing
summary, source/file-role record, citation and historical work assertion. The
historical assertion is not erased or silently rewritten as a new observation.

The separately guarded
[`apply_futhark_knucleotide_eligibility.py`](../../../tools/qualification/apply_futhark_knucleotide_eligibility.py)
implements this correction. It binds the complete original profile records,
review and 41 retained policy/package/source artifacts. It moves the two profiles
from the eligible `programs` map to `program_inventory`; Data reads the union and
continues to expose their exact samples and source text. `eligible_for_chart:false`
and an explicit reason accompany each retained profile. It removes only their
Futhark k-nucleotide endpoint group and records the former group and language
coverage as historical metadata. The original local table's excluded-support
roles and all retained application counts remain unchanged.

Eleven small Python regression checks passed before admission. They cover exact
historical replay, all 351 protected upstream profiles and their pool membership,
every source/count/sample/work assertion, the exact two eligibility changes,
8/10 eligible versus 9/10 historically measured coverage, no unreviewed fallback,
browser Data projection, repeat-apply rejection, and source/configuration/review
drift. This is metadata validation; it adds no timing observations. The preview
and report live under `correction-v1/`; only the parent workflow may run the
guarded apply after reviewing their hashes.

There is no eligible Futhark k-nucleotide fallback in the current pool. Therefore
the later transform must also remove that language/workload endpoint group from
eligible selection and record an explicit “no eligible implementation” gap.
Merely setting two flags while leaving an empty eligible group is insufficient:
the existing source-accounting endpoint recomputation calls `min(candidates)`.
Recompute coverage and language summaries over the remaining eligible workloads
(currently eight of ten for Futhark), while preserving all historical records.
Verify all other profiles/sources/observations unchanged. No new LOC rule or
rewritten source is a remedy for this algorithm-policy failure.

No fixed Futhark `reference_summary` exists in the catalog. Its displayed endpoint
geometric means are computed from the remaining groups. The fast endpoint means
change from `(LOC × best=2.54279, time × best=3.87393)` over nine workloads to
`(2.47304, 3.20628)` over eight; the small endpoint means change from
`(1.88648, 10.99837)` to `(1.85306, 8.96226)`. These are different coverage sets,
not a matched-workload speedup. No global time/LOC baseline or any retained
profile coordinate changes. The transform fails closed if a baseline would
change rather than renormalizing unrelated records.

This proposal covers these exact suite-derived Futhark profiles only. It does not
exclude R/APL/Uiua grouped counting without separate source/library/work evidence,
nor authorize rewriting unchanged upstream submissions.

## Genuine DIKU containers package: useful API, important limits

The official [package index](https://futhark-lang.org/pkgs/) lists containers
**0.10.9** at review time. GitHub's exact `v0.10.9` tag resolves to commit
`508b2f198d4e2776b339a381823d637c24c94152`; the lightweight tag response and
selected source bytes are retained under [primary](primary/). This is an
independently maintained generic package, licensed
[ISC](https://github.com/diku-dk/containers/blob/508b2f198d4e2776b339a381823d637c24c94152/LICENSE).

Version 0.10.9 uses flat paths such as
[`containers/hashmap.fut`](https://github.com/diku-dk/containers/blob/508b2f198d4e2776b339a381823d637c24c94152/lib/github.com/diku-dk/containers/hashmap.fut).
The newer inspected main commit
`98d3778b37b6702b73de95a866f7abdb2c184c44` reorganizes these into `map/` and
`core/`; it is a separate unreleased commit, not the 0.10.9 package layout.
Both inspected files describe static hash maps. Do not infer a growable mutable
table from the directory reorganization or package version number alone.

The release provides `mk_hashmap` and `mk_linear_hashmap`, integer key modules,
`lookup`, `update` and `insert`. However, its `update` scans/rebuilds the value
array with `hist`/`map2`; `insert` reconstructs a map from existing pairs plus new
keys. The linear implementation selects four slots per input key. There is no
reserve/default-capacity amortized-growing mutable table API in these inspected
implementations. Current main retains these same broad behaviors. This is a
source-level complexity finding, not a measured performance result.

The abstract [map API](https://github.com/diku-dk/containers/blob/508b2f198d4e2776b339a381823d637c24c94152/lib/github.com/diku-dk/containers/map.fut)
distinguishes updating existing keys from insertion that can increase map size.
Thus logical growth through existing library operations is available; a fast
drop-in for the local open-addressed table is not established. The release
[manifest](https://github.com/diku-dk/containers/blob/508b2f198d4e2776b339a381823d637c24c94152/futhark.pkg)
pins sorts 0.7.0, cpprandom 1.4.1 and segmented 0.5.0, each at an explicit commit.
The retained main manifest instead names newer dependencies. A future build must
pin one complete version/dependency closure rather than mixing those layouts.

## Concrete replacement investigation

A source-only API sequence worth testing uses the existing `mk_linear_hashmap`
with `static_u64key`: begin with the library's empty `from_array () []`, perform
one `lookup` per overlapping window, call `update` with one `(key, count+1)` pair
when present, and `insert` with one `(key, 1)` pair when absent. The exact key,
optional-value and map-size types must be checked by the pinned compiler; this
paragraph is not a claimed compilable candidate. It adds no custom probing or
rehashing implementation. Logical growth starts empty and the library chooses
the first small allocation, but its precise growth behavior still needs explicit
task-policy acceptance and required-work qualification.

Do not construct all input keys first, prebuild their complete key set, replace
each window update with `from_array_hist`, or accumulate duplicates in an
application batch before touching the table. Those choices would evade the
required occurrence-by-occurrence work even with a genuine library import.
Library internals using general `hist` operations are distinct from an application
substituting a grouped histogram for table updates; review actual call granularity.

Any prototype must retain all seven widths, every overlapping window, complete
histograms before queries, a correct exact-token record parser and deterministic
output order. First compile and test unrelated key/count operations, collision
and insertion cases, empty/short DNA and record boundaries; then require bounded
output and source-work review. Because singleton updates scan current values and
new-key insertion reconstructs storage, begin with strictly bounded sizes and
resource limits. Do not launch a 125-million-base run on an untested potentially
quadratic path. If no practical compliant library path qualifies, publish the
unsupported gap rather than relax the rule or add a native nucleotide executor.

Vendored package bytes must retain ISC notices. No license attribution is inferred
for the old local table from the new library's license. Existing C adapter source
and all workload-specific parsing/count/query orchestration stay within their
current inspected boundaries; a replacement receives its own complete source
count and independent library/runtime proof before measurement or admission.
