# Paired candidate key and count loads

Compiler source `d8d9a7d64944cd3de78fe3f8190284924069c508` emits one
scalar 128-bit load and splits its two complete u64 words for an admitted,
initialized 16-byte narrow hash slot. The actual AArch64 code uses `LDP`
before the full-key comparison. A mismatching candidate never consumes the
count. Pointer changes, mutations, helpers and source-state reloads retain
the previous candidate-value invalidation. Wide keys retain separate loads;
direct caches are unchanged. Neither counts nor source work are narrowed.

The pass applies from ownership and layout proofs, without benchmark names,
input constants or DNA-specific dispatch. Its differential corpus includes a
renamed, parameterized function with an unrelated eight-letter immutable
producer, complete maps, growth, refill boundaries, changed extents and
source/bytecode execution. The paired-load pass can be disabled independently
of the earlier separate candidate-value pass. Existing wide-key, overflow,
failure-origin and resource-limit comparisons remain in the native suite.

Ten focused tests, 415 native checks (with three existing ignored tests),
30 line-processing checks, 36 worker-credit checks and the catalog check pass
at one clean source. Compiler v94 and the unchanged one-million-base prefix
are qualified. Guest IR is 94, host ABI is 33 and work policy is 69. Source,
bytecode, canonical resources, complete maps, all updates and finite prices
are retained.

Assembly inspection finds 38 actual paired candidate loads in each of the
two hashed funded functions. All twelve other object functions, including
the pure scalar scanner, are byte-identical to the retained production
parent. Across both hashed functions there are 11,072 static instructions,
4,108 load instructions and 2,482 stores, versus 11,200 / 4,146 / 2,482 for
the production parent and 11,328 / 4,184 / 2,482 for the unpromoted separate
load trial. These static totals do not establish a runtime improvement.

`qualify-code.py` verifies the regression receipts, source pins, exact guest
object and actual paired-load windows before creating the primary timing
gate. `plan.json` predeclares two serial six-subject sessions, each with twelve
balanced orders: candidate, retained pure-scalar production parent, separate
load trial, byte-table anchor, ordinary finite-credit anchor and unchanged
upstream Rust. No full-input warmups or outliers are excluded. Full-input
timing and fresh matching profiles/counters are pending; production remains
the pure-scalar source `93015bc6298b77fd10402e88baea5e3bfd89b28d`.
