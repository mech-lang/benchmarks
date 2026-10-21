# Exact source-review coverage with C#

This report extends the frozen [first reconciliation](../coverage-v1/README.md)
with twenty exact C# JIT/AOT profiles sharing ten inspected source bundles.
It reuses the hash-pinned reconciliation code and its source-boundary checks;
the earlier report remains intact.

| Current retained scope | Profiles |
| --- | ---: |
| Local/derived sources with a recorded source/idiom inspection | 313 |
| Local/derived sources still awaiting that inspection | 360 |
| Unresolved ownership requiring lineage review | 46 |
| Protected unchanged upstream submissions | 351 |
| Total retained profiles | 1,070 |

These are static source-inspection counts. They do not certify optimization
completion, native correctness/work, source normalization/formatting or new
performance results. The 673 editable profiles still contain 596 distinct
application source bundles, and runtime profiles remain separate. The four
supplemental review packets cover 49 exact profiles. Source identities are
rehash-checked against retained catalog text and available files, including the
explicitly recorded 51 retired private-build locations with preserved bytes.

```sh
python3 experiments/implementation-audit/coverage-v2/build.py --check
```

[coverage.json](coverage.json) retains per-family totals and exact bindings.
No canonical source, timing, source count, eligibility or chart selection changes.
