# Clojure: complete retained-source and idiom review

Reviewed all **twenty distinct Clojure main applications**, compact and optimized
forms for ten workloads, plus their shared generic support. Exact retained
compiler-bound hashes and roles are in [inventory.json](inventory.json) and
[programs/clojure](../../../programs/clojure/). These are documented local
adaptations with independent references, not unchanged published Game files.
Original-origin/model gaps and citations remain as recorded. No JVM/Clojure
program, compiler, benchmark, browser or generator was run or changed.

The runtime record is Clojure 1.12.6 bytecode on Temurin 25.0.4.1+1 HotSpot JIT,
native macOS ARM64. Sources already use primitive Java arrays, mutable buffers,
BigInteger and ordinary Java regex APIs. The shared `s/jobs` creates a **new
fixed thread pool on every call**, submits at most eight workers, awaits all
results, then shuts down the pool. Thus spectral norm creates a fresh pool for
every one of forty product phases, and tree work creates another pool per depth.
That is a concrete lifecycle candidate, not evidence that parallelism is absent.

| Workload and every reviewed ID | Actual source / measured retained comparison | Concrete performance and smallest-idiomatic source alternatives |
| --- | --- | --- |
| N-body: `clojure-nbody-compact`, `clojure-nbody-optimized` | Both hold five primitive `double-array` bodies inside an object array. Compact allocates/destructures `[[0 dx] [1 dy] [2 dz]]` for every pair update. Optimized avoids that temporary but makes two passes over persistent-vector pair descriptors, stores/reloads 30 deltas and ten magnitudes, and repeatedly destructures `(nth pairs pair)`. Compact is faster: 165.36 s versus 207.67 s. | Compare direct primitive scalar updates or a primitive indexed coordinate loop in the compact single-pair pass. Replace pair descriptor vectors with fixed primitive indices if a two-pass candidate remains useful; first inspect boxing/reflection/direct-call evidence rather than assuming array hints eliminate everything. A small source helper for three-axis updates can reduce duplication, but must remain primitive and preserve exact ten-pair order, sqrt/division, every step, momentum and both energies. No parallel time steps or foreign n-body kernel. |
| Mandelbrot: `clojure-mandelbrot-compact`, `clojure-mandelbrot-optimized` | Compact recomputes both coordinates inside scalar pixel calls. Fast precomputes primitive real coordinates, hoists CI per row, and assigns disjoint output rows to bounded workers, improving 13.37 s to 3.45 s. Both pack full PBM bytes into a complete bitmap. | Preserve hoisting and disjoint primitive output. Review JIT/inlining of `inside?`, byte-packing dispatch, task grain and bounded output blocks. Share one row-building helper between serial/parallel compact forms as a concrete idiomatic-size alternative; do not hide the pixel algorithm in generic support. Keep all pixels, exact escape tests, fifty-step maximum and odd-width padding; no analytic interiors/periodicity. |
| K-nucleotide: `clojure-knucleotide-compact`, `clojure-knucleotide-optimized` | Both have an exact THREE-token/first-record parser with comments, explicit CRLF/CR/LF splitting and Locale.ROOT uppercase. Compact creates a substring per window and uses a transient persistent map. Fast uses rolling integer keys, seven private default-growing Java HashMaps and parallel width tasks (7.47 s versus 55.30 s); updates still perform `.getOrDefault` then `.put`, with boxed keys/counts. | Transfer the correct parser to weaker ports. Review one-time byte encoding, primitive-key general map APIs or private mutable numeric counters, with dependency/runtime pins and actual map growth. Preserve every update and seven maps; no query-only or grouped count replacement. A shared encode/decode/count-default helper and paired width/query data are idiomatic-size candidates that avoid repeated orchestration; do not replace explicit evaluation with an unverified native counting helper. |
| Spectral norm: `clojure-spectralnorm-compact`, `clojure-spectralnorm-optimized` | Primitive input/output arrays and a primitive denominator function are already present. Fast partitions rows, retaining each row's scalar sum and all coefficient evaluations (0.574 s versus 1.288 s). Both allocate new vectors in every multiply and branch on transpose per element; `s/jobs` repeatedly creates/shuts down pools. | Compare one application-scoped ordinary executor and reusable distinct input/output/temporary arrays, preserving phase joins. Review orientation specialization and actual arithmetic boxing/code generation before new SIMD. A shared ordinary row helper gives a smaller source, while specialized loops trade size for speed; either must retain separate required coefficient/forward/transpose/composition functions and all forty products. No cached matrix or eigensolver. |
| Reverse complement: `clojure-revcomp-compact`, `clojure-revcomp-optimized` | Both retain all parsed records in StringBuilders. Compact reverse-indexes characters into 60-character StringBuilder lines. Fast copies each record to a byte array, swaps/complements in-place, but still calls the general character/map-based `complement-byte` for every byte and writes each 60-byte line through System.out. **Fast is slower:** 24.34 s versus 11.14 s. | Start with the compact winner. Compare a primitive 256-entry lookup and bounded consistent output buffer, avoiding per-byte map/character conversions and unnecessary record/string copies. Review a streaming parser so raw text, split lines and all record builders need not coexist. Existing `zipmap` and compact reverse loop are genuine expressive baselines; a primitive fork is not automatically smaller. Preserve comments, headers, all IUPAC/lowercase/U, empty records, CRLF/EOF, unknown-byte policy and exact wrapping; keep writer/raw-stream flushing explicit. |
| Fannkuch: `clojure-fannkuchredux-compact`, `clojure-fannkuchredux-optimized` | Both have typed mutable integer arrays and canonical actual prefix reversals. Fast uses factorial-ranked private worker intervals, improving 957.06 s to 176.21 s. **Both call `aclone` for every permutation's flip count**, so scratch allocation remains substantial despite primitive storage. | Compare one reusable `int-array` per worker and ordinary `System/arraycopy` before each flip count; preserve complete reset and no cross-worker sharing. Existing rank initialization/carry is the correct design reference. For idiomatic size, share common carry/rotation/formatting helpers across complete forks or a qualified generic primitive-array helper, counting workload logic. Keep all ranks, flips, checksum parity, maximum and small-n/carry cases; no cached flip counts. |
| FASTA: `clojure-fasta-compact`, `clojure-fasta-optimized` | Compact allocates a StringBuilder/string per 60-base line and prints it. Fast uses a 65,536-byte BufferedOutputStream but still crosses `.write(int)` per base; draw state is a one-element primitive array, with direct binary64 division and an unscaled CDF. Fast improves 16.98 s to 11.03 s. | Preserve stream buffering but compare reusable primitive line/block buffers and fewer interop calls. Share ordinary record wrapping between repeat/random forms through a source-owned character producer, measuring callback cost separately. The CDF is already a primitive array and the seed is continuous across records; do not propose those as missing. Preserve every draw/division, 2n/3n/5n bases, exact headers and tail lines; no RNG period/output cache. |
| Binary trees: `clojure-binarytrees-compact`, `clojure-binarytrees-optimized` | Both allocate a fresh two-slot `object-array` before testing depth, including every leaf, then check actual child references. Fast partitions each depth's iterations into bounded private work and joins totals (1.219 s versus 3.246 s). The stretch tree is checked before the retained tree is created. | Preserve fresh arrays and independent iteration intervals. Review persistent executor lifecycle and chunk grain, plus primitive recursion counters without reflection. A local `if-let` binding of the left child can express checking without repeating the lookup; this is a concrete concise source alternative, not a new LOC result. Keep every equal-size node, full constructor/traversal and long-lived root use. No constant leaf, flat tree or algebraic check. |
| Regex-redux: `clojure-regexredux-compact`, `clojure-regexredux-optimized` | Uses direct Java Matcher `.find` to count without retaining all matches, and five `.replaceAll` operations in a source-visible ordered `reduce`. Fast schedules independent counts through the capped pool (3.25 s versus 7.84 s). Generic input-text uses ISO-8859-1, so source character counts correspond to original bytes. | Preserve count-only iteration and byte-preserving decode. Review pattern preparation/lifetime, possible overlap of independent count/replacement work and generic executor reuse. The existing vector literals/ordered reduce are already idiomatic and small; `re-seq`/`count` is a concise alternative only with allocation and semantics reviewed, not an assumed improvement. Retain nine nonoverlapping counts, case rules, five ordered substitutions and all lengths. |
| Pi digits: `clojure-pidigits-compact`, `clojure-pidigits-optimized` | Both use immutable Java BigInteger and two actual quotient extracts. Fast explicitly retains small coefficient objects and buffers output in StringBuilders (4.108 s versus 4.185 s). This tiny saved difference does not isolate coefficient caching or output cost; the pinned JDK may already cache `valueOf` constants. | Compare deriving the fourth numerator by adding q to the third numerator, while retaining both divisions. Keep a concise idiomatic loop/recur state and ordinary formatting; do not replace explicit flushing, which the retained source history required. Diagnose JVM startup and BigInteger temporaries separately, without substituting execution-only time for the chart. Preserve unbounded sequential state, recurrence order, full digits and partial-row padding. |

## Priorities and valid transfers

The clearest first candidates are n-body's vector/destructuring/boxing work,
fannkuch's per-permutation clone, reverse complement's slower “optimized” path,
and executor lifecycle in spectral norm/trees. Existing good techniques include
primitive arrays, exact-token record parsing, default-growing private maps,
factorial rank partitions, precomputed Mandelbrot coordinates, count-only Java
regex iteration, buffered streams and explicit output flushing. A conventional
JVM representation/API comparison is warranted before attributing these large
gaps to the language itself.

Any executor reuse change must retain shutdown/exception handling and be pinned
as a new source/helper configuration. Count actual compute workers with the main
thread and runtime/library settings; do not infer worker use just from JVM CPU
availability. Record startup, class loading, execution-time HotSpot compilation,
complete input/output and shutdown in the full process metric. No proposed
alternative is measured or newly qualified in this review.

## Source-size and lineage boundaries

`loop/recur`, destructuring, sequence comprehensions, pure helpers, transients,
primitive arrays, interop and general library operations are legitimate Clojure
expressions. Do not expand implicit iteration into fictitious scalar LOC. Do
review independent `let` bindings, side effects in `do`/callbacks, meaningful type
hints and macro/header ownership under an explicit native policy. Literal vector
wrapping and punctuation are not independent executable statements. Shared
helpers may reduce duplication, but domain parsing, byte packing, RNG and
algorithm-specific worker setup cannot disappear merely by being named support.

The current packet's application/support partitions take precedence over earlier
provenance prose that counted all support under an older boundary. The generic
support has byte-preserving input, locale formatting/flush and a general callable
pool; its actual retained bytes remain inspectable. Retained normalized LOC,
qualified formatter LOC and application/submitted byte/gzip/BPE metrics are
different measurements; none proves a smallest idiomatic program or universal
logical-LOC grammar. Preserve independent reference citations, notices and
remaining earliest-origin/model uncertainty for every future fork.
