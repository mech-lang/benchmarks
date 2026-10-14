# Kotlin source and class-owner review

The retained twenty compiler results contain ten baseline algorithms, each built
independently as compact and optimized. Each pair records the same main, helper,
and generated class hashes. These are aliases; neither a distinct optimization
nor interchangeable future timing samples is implied.

This review covers the complete ten mains, the complete counted `Support.kt`,
and the corresponding fourteen distinct class bodies in the retained `javap`
captures. Across twenty compilations there are 46 class artifacts: twenty
`MainKt`, twenty `Support`, two `Node`, and four generated k-nucleotide comparator
classes. The module metadata adds twenty artifacts. The two tree captures are
under `archive/languages/kotlin/20261013/revisions/subject20-compile-owners-v1/`;
the other eighteen are under `../additive-compile-owners-v1/`.

`review.json` indexes the source bindings, recorded artifact hashes, complete
owner sets, and retained disassembly paths. It records a source review, not a
new runtime integrity seal. Before any native qualification, verify every
original receipt, physical source, class, runtime dependency, and review input
against the retained pins under the shared mutex. No original source, class,
receipt, or qualification flag is changed by this packet.

## Source ownership and required work

All mains expose `public static final void main(java.lang.String[])`, descriptor
`([Ljava/lang/String;)V`. Main dispatch calls the counted `clbg.Support` methods.
The generated tree node and comparator owners come from the counted main source;
they do not add independent source files or hide an uncounted kernel. JDK
BigInteger, BigDecimal, regex, arrays, collections, and Kotlin standard-library
operations are vendor primitives. The authored algorithm loops remain in the
recorded main classes.

Bytecode offsets below refer to the compact capture. The paired optimized
artifact has the same recorded class hash.

| Workload | Source and bytecode evidence |
| --- | --- |
| Binary trees | `tree(I)` allocates `Node` at offsets 4 and 16; the internal case calls `tree` twice at 23 and 29, with `depth - 1`. Its constructor stores distinct left/right references. `check(Node)` recursively visits both children at 22 and 34. `main` constructs and checks stretch at 36/39, constructs the long root at 52 and stores it in local 3, loops over every short-tree iteration at 81–112 and every even depth at 59–134, then reloads local 3 at 139 and checks it at 140. No leaf singleton, arena, node pool, memoized check, or closed-form result appears. This establishes authored construction and lifetime demand; actual fresh identity, GC retention, and JIT allocation still need runtime evidence. |
| K-nucleotide | `table(String,I)` creates a new `HashMap` at 6 on every call. The loop at 16–91 visits each start with `i+k <= length`, constructs the substring at 31, gets the old count at 51, increments it at 69–70, and stores it at 82. `main` materializes lengths 1, 2, 3, 4, 6, 12, 18 at 366–435, invokes `table` at 540 for each, and stores every returned map in the outer `LinkedHashMap` before rendering. All seven full maps remain reachable through the query phase. The first comparator reverses count operands; the second compares keys only when the count comparison is zero. The two frequency tables use all entries, count descending then key ascending, with denominator `max(0,L-k+1)`. Five queries look up the corresponding retained maps. Input selects the exact `THREE` token, skips comments/empty lines, accepts ASCII A/C/G/T case variants, and stops at the next record. |
| Pi digits | `main` performs `BigInteger.divide` at 122 and 201 on every extraction iteration, before candidate comparison at 216. The numerators are `3*q+r` and `4*q+r`; both divide by the same `t`. Emission updates `q` by ten and `(r-t*digit)` by ten. Refinement computes `(r+2*q)*(2*k+1)`, `q*k`, and `t*(2*k+1)` before incrementing `k`. There is no cached digit table, narrowed substitute, or omitted fourth-candidate division. Ten-column padding and the partial final line remain in the main. |
| Fannkuch-redux | `flips` calls `Arrays.copyOf` at 9 before its reversal loop, preserving the current permutation. Rotation shifts the prefix and restores its original first value. `main` builds two integer arrays, performs the factoradic counter/rotation loop, calls `flips` at 112 for every visited permutation, uses rank parity at 121–140 for the signed checksum, updates the maximum at 147, and increments rank before the next permutation. |
| FASTA | The main emits all three headers and calls repeat/random with `2*n`, `3*n`, `5*n`. The first random call starts at 42 and its returned seed is passed to the second. `random` applies 3877/29573/139968 at 24–38 for every base, performs a binary64 division and sequential cumulative-threshold search, emits the chosen character, and wraps at 60. `repeated` cycles through the complete ALU string. The initialized tables contain all 15 IUB entries and four human-frequency entries. |
| Mandelbrot | `inside` performs up to fifty binary64 recurrences, tests the new squared magnitude against four, and exits only after escape or the iteration limit. `main` visits every row and column, calls `inside` at 120, accumulates bits MSB first, emits full bytes, and shifts the partial final byte at 175 so unused low bits are zero. The output is raw P4 bytes. |
| N-body | `main` creates five separate seven-double body arrays: the sun directly and four calls to `planet`, which executes `newarray double`. It sums all three momentum axes and corrects the sun, calls `energy` at 280 and 338, and calls `advance` once per requested step at 320. `advance` visits all `i<j` pairs, updates both bodies on all three axes, then updates every position. `energy` visits all bodies and all ten unique pairs. The saved constants, solar factor, days factor, and 0.01 step remain in the class. |
| Spectral norm | `multiply` has both complete length-by-length loops and chooses `a(j,i)` or `a(i,j)` through the transpose branch. `ata` calls both directions at 21 and 27. `main` creates three double arrays, initializes every `u` entry, calls `ata` twice per each of ten iterations at 107/114, completes both dot products, divides, and calls `Math.sqrt` at 183. At prescribed n=5,500, the integer coefficient intermediates are within their authored ranges. |
| Regex-redux | All nine patterns and all five ordered replacement pairs are initialized in the class. `matches` compiles the supplied pattern and increments for every `Matcher.find`. `replace` performs its own find/prefix/literal-replacement/cursor/suffix loop; replacement text never passes through a replacement-template interpreter. `main` cleans headers/newlines once, runs all nine counts over the same cleaned string, and feeds each of five replacements into the next. Latin-1 input makes the three String lengths byte-equivalent for this input domain. The cleanup expression intentionally matches the prescribed LF FASTA stream; it is not a claim of universal newline normalization. |
| Reverse complement | The main iterates every record, preserves the header, skips comment and empty lines, flushes the previous record on the next header and the final record at EOF. `record` walks every nucleotide in reverse and emits a newline every 60 bases plus a partial final newline. `complement` applies the complete uppercase ambiguity mapping, including U to A, and rejects unsupported nucleotides. CRLF and standalone CR are normalized by the counted helper. |

The prescribed input sizes fit the relevant integer intermediates: FASTA's
largest count is 125,000,000 and its RNG multiplication is below Int maximum;
the matrix coefficient uses Long multiplication; tree shifts at maximum 21 and
the fannkuch n=12 rank/checksum use Long. This is a review of the prescribed
domain, not a promise that every nonnegative Int is a feasible workload.

## Complete helper

`Support.size` checks zero or one argument, uses `Integer.parseInt`, then rejects
negative values. The helper therefore inherits that parser's accepted syntax;
an ASCII-only integer contract must not be inferred from its source.

`input` calls the Kotlin stream reader on `System.in`. `text` and `bytes` use
explicit ISO-8859-1. `write(byte[])` invokes `PrintStream.write` and flushes;
`write(String)` delegates through the explicit encoding. Every byte round-trips
through a Latin-1 string. Arbitrary non-Latin-1 Unicode text is outside that
round-trip claim. Because PrintStream records some I/O errors internally, the
supervisor must independently compare complete raw stdout and normal exit.

`fixed` rejects nonfinite values and precision outside 0–18, constructs
`BigDecimal(double)` at bytecode 67–72, applies `HALF_EVEN` at 76–79, and uses
`toPlainString`. It tests the original raw binary64 sign at 88 and restores a
minus when rounding removed it, covering negative zero. `lines` first replaces
CRLF with LF, then CR with LF, then splits on LF. All helper methods, including
ones unused by a particular main, remain counted in every source form.

## Remaining gates and feasibility

The source and retained bytecode support the required authored work. They do not
close actual loaded-runtime dependencies, native workload method compilation,
heap allocations after JIT optimization, helper execution, exact workload
outputs, canonical/formatted LOC, or full-study eligibility. Those flags remain
false or null in the retained receipts. `bounded-checks.json` specifies the next
unscored checks and their evidence requirements.

The seven complete String-key maps are a material memory risk at the prescribed
125,000,000-base k-nucleotide input. The 18-mer map can approach one distinct
entry per window while the other six maps remain reachable. The fixed 8 GiB
heap may be insufficient. Small-map success cannot establish full-size memory
qualification. Preserve any actual bounded/full failure; do not substitute
query-only counts, enlarge the measured heap, or silently change this source.

Each alias still needs its own qualified runtime binding, source count, and
fresh-process measurements. Full admission requires sixty Kotlin samples and
thirty unchanged Mech controls plus independent reconciliation. This source
review neither repeats successful compilations nor admits timings or charts.
