# C# implementation audit

The [retained-source review](source-review-v1/README.md) covers the ten
local/derived source bundles shared by twenty JIT/AOT profiles across nine
workloads. Nineteen unchanged upstream profiles remain protected. A shared
source inspection does not merge execution modes or qualify their runtime
behavior.

Five source-only candidates retain their original implementation citations and
licenses: [spectral scratch reuse](spectral-scratch-v1/README.md),
[nucleotide input/counting](knucleotide-general-v1/README.md),
[ordinary managed regex](regex-managed-v1/README.md),
[source-generated regex](regex-generated-v1/README.md), and
[reverse-complement short reads](revcomp-short-read-v1/README.md).
All are uncompiled and unmeasured. Native output/work validation, generated-code
review, exact source normalization/formatting and fresh complete-process
comparisons remain pending.
