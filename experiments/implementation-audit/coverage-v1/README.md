# Exact source-review coverage

This additive report reconciles the current catalog and base implementation
inventory with the later exact TypeScript, Odin and OCaml static reviews. It
keeps the frozen queue and original inventory intact. Each supplemental review
must match the complete source boundary of the named profile; a language name
or a review of another source cannot qualify it.

| Current retained scope | Profiles |
| --- | ---: |
| Local/derived sources with a recorded source/idiom inspection | 293 |
| Local/derived sources still awaiting that inspection | 380 |
| Unresolved ownership requiring lineage review | 46 |
| Protected unchanged upstream submissions | 351 |
| Total retained profiles | 1,070 |

The 673 editable profiles contain 596 distinct application source bundles.
Execution-mode profiles stay separate; these counts are not counts of independent
algorithms or benchmark observations. The three supplemental packets account
for 29 exact profiles. A static review identifies designs and alternatives; it
does not establish sufficient optimization, native correctness, required work,
approved source counts, a new timing or global optimality. The base review
statuses are inherited from their recorded evidence, not rerun native reviews.

The builder hashes the current catalog, base inventory, language metadata,
supplemental records/prose and every retained source identity. All 971 embedded
source files reproduce their recorded SHA-256. Fifty-one old Clojure/Gleam
private-build locations are absent; their exact source bytes remain embedded
in the catalog and are verified there. The report lists those old locations
explicitly rather than claiming the files still exist or silently recreating
obsolete build directories.

Native candidate qualification and the source-normalization audit remain
separate work. No catalog measurement, source count, eligibility or chart
selection changes when this report is generated.

```sh
python3 experiments/implementation-audit/coverage-v1/build.py --check
```

[coverage.json](coverage.json) supplies per-family totals, exact profile/source
identities and links to each supplemental review. Unsupported or changed
bindings fail generation; there is no physical-row fallback for missing native
counts.
