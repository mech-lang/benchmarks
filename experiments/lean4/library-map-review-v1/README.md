# Lean4 k-nucleotide: required library-map work

Source-only review, 2026-10-20. The two exact suite-authored Lean4 applications
do not perform the hash-table work required by the official task. This review
proposes an additive eligibility correction; it does not change the catalog,
source text, retained counts, samples or historical work assertions.

The [official task](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/knucleotide.html)
requires an existing built-in/library hash table, accumulation by lookup/update,
growth from a small default and counts for **all** keys at widths1,2,3,4,6,12,18.
This is the exact same [retained primary snapshot](../../futhark/library-map-review-v1/primary/knucleotide-description.html)
used by the [Futhark policy correction](../../futhark/library-map-review-v1/README.md),
not a different interpretation for Lean. See snapshot lines34–40 and49–53.
The current official page agrees. No claim is made about when that wording was
first introduced.

| Profile | Application SHA-256 | Retained LOC / saved median |
| --- | --- | --- |
| `knucleotide:lean4-knucleotide-native-v1` | `e3aa2ec057ae485f939062523f90e5427cf214cfc5c36a8e090a4e5ecd7a2e3a` | 81 / 6.74196675s |
| `knucleotide:lean4-knucleotide-optimized-v1` | `e2cb4dc950de63f0cb3ceded840eda8057c71a8307d82fe80e6928a3d9bb33c0` | 83 / 6.785259833s |

In the [native source](../source-v1/knucleotide.lean), `histogram` (lines35–43)
allocates `Array.replicate (4 ^ width) 0` and increments by direct array index.
`main` calls it only for widths1 and2 (lines79–80). `occurrences` (65–75)
instead rolls a UInt64 key and increments a single scalar only when the key
equals the requested query. Its five calls (81–82) cover query lengths3,4,6,12,18.
It does not accumulate counts for the other keys at those widths.

The [optimized source](../optimization-v1/build-fast-v5/source/knucleotide.lean)
has the same design at lines38–46,68–78 and82–85. Neither source constructs a
hash map, performs a map lookup/update, or grows a table. `Common.lean` only
provides generic argument/stream/formatting wrappers; `Format.c` only formats a
number. No hidden map implementation exists in those excluded support files.
Scanning every sequence byte and producing the right requested counts does not
replace the required accumulation work. The narrow exclusion does not depend
on untested parsing edge cases or timing differences.

Both profiles have `authorship.origin_status: suite-authored`; their retained
[provenance](../source-provenance-v1.json) describes local suite applications.
Neither is an unchanged upstream submission. This decision affects only these
two exact sources and does not transfer to other languages or protected
upstream programs. Existing source/model attribution is preserved as recorded.

The saved [native work review](../required-work-v1/review.json) and
[optimized work review](../optimization-v1/work-fast-v5/review.json) contain
broad assertions of complete nucleotide work, but their actual detailed native
witnesses concern tree allocation and pi extraction (plus optimized permutation
visits). They contain no library-map witness for nucleotide counting. Those
historical assertions and the old ten-workload qualification remain intact as
evidence of the prior decision; the new source-bound policy decision is separate.

[review.json](review.json) pins both complete profile records, all source bytes,
the exact shared primary policy, provenance, toolchain, count and work reports,
and existing timing reports. The new
[correction module](../../../tools/qualification/apply_lean4_knucleotide_eligibility.py)
requires those identities and rejects new fallbacks, changed source/support
boundaries or altered historical observations. Its guarded preview/apply
interface is separate from the frozen Futhark module.

The proposed correction removes the two profiles from eligible `programs` while
retaining their complete rows in `program_inventory`, with explicit eligibility
metadata and reason. Both already appear in both pools, so their identical
inventory copies must also receive the same additive metadata. Data remains
able to inspect their source and samples. Only the Lean4 k-nucleotide endpoint
group is removed. Current eligible coverage becomes9/10; historically measured
coverage remains10/10. The prior language metadata, removed group and fixed
Lean4 reference summary are saved in the correction marker. Only the Lean4
reference summary is recomputed over the remaining nine groups; its changed
coverage is not a measured speedup. Global baselines and every profile's
timing/source coordinates remain fixed.

No replacement is qualified here. A future ordinary `Std.HashMap` candidate
must use the exact restored Lean version's public API, start with a small default
table, and genuinely accumulate every overlapping key for all seven widths.
Its source, required-work witness, output, counts and fresh complete-process
timings need separate qualification. Calling a dense array a map or merely
restoring a historical eligibility flag cannot supply that evidence.
