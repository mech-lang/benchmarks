# Janet spectral-norm candidate

The v2 implementation constructs a result array for each of 40 matrix-vector
products and calls `coefficient` inside every inner iteration. The v3 candidate
uses three reusable arrays: u, v and a temporary. It retains all 20 forward and
20 transpose products and every element of each product. Input and output arrays
are distinct at each call. Accumulation order, reciprocal-then-multiplication,
and final dot products remain unchanged. No matrix is precomputed or omitted.

For fixed row i, the forward denominator starts at i(i+1)/2+i+1 and advances by
i+j+1 after column j. The transpose denominator starts at i(i+1)/2+1 and advances
by i+j+2. Both identities follow by subtracting adjacent triangular numbers in
the prescribed coefficient. At N=5500 every denominator and increment is an
integer exactly representable in binary64. The unit test checks all 5500 rows
at five column boundaries for both forms; this is algebra/domain verification,
not a full native benchmark run.

All seven original bounded output contracts pass for the uninstrumented v3
candidate. Fourteen additional native source projections (parent and candidate,
each over all seven cases) add counters only. Each performs exactly 40 products
and 40*N*N terms, while retaining the independent expected stdout. Their stderr
contains only the explicitly checked counter record. Those diagnostic executions
are excluded from quantitative measurements. The precise projected sources and
complete process streams are retained in `spectral-work-v1`.

This is a performance candidate with matching bounded work and output evidence.
No speed improvement, full-size correctness, normalized LOC improvement or
universal optimality is claimed. The source retains the v2 Apache-2.0 license;
Codex GPT-6 family authored the local change, exact serving model unknown.
Full-size output checks, native dependency closure and three whole-process
samples with the equivalent Mech AOT denominator remain pending.
