# Pharo Smalltalk: complete retained-source review

Source-only review of all **13 retained Smalltalk applications across ten
workloads**. Three are locally corrected derivatives of named Game submissions
(n-body, Mandelbrot and pi); ten are locally authored/adapted alternatives.
Original upstream notices and cited copies remain protected. Exact hashes and
ownership evidence are indexed by program in [inventory.json](inventory.json)
and the [source bundles](../../../programs/smalltalk/). Catalog model attribution
remains separate from the explicit local adaptation assertions. No Smalltalk
VM, compiler, benchmark or browser was started and no source/count/time changed.

The runtime is the retained native ARM64 **Pharo 14 snapshot, Cog/Spur JIT**, in
a fresh headless image process. Application source is filed into pinned images
before timing; startup, image loading, execution-time JIT, computation, I/O and
shutdown are inside the saved whole-process observation. This is a JIT image
workflow, not source parsing in every sample or a proof of pure AOT execution.
The [manifest](../../../archive/comparisons/remaining-languages-comparison/20261011/smalltalk_manifest.json)
retains VM/image/loader/dependency identities and preparation details. Generic
green-process concurrency should not be presented as demonstrated multicore
benchmark parallelism; any independent VM-worker candidate needs a separate
whole-process/transport measurement and source review.

| Workload and every retained ID | What is actually implemented | Concrete candidate / acceptance work |
| --- | --- | --- |
| N-body: `nbody-smalltalk-published-1`, `nbody-smalltalk-floatarrays` | Published derivative stores coordinates/masses as Body instance variables and dispatches pair updates; local alternative uses per-body Float64Arrays and indexed updates. The object form is faster in this pool: 60.72 s versus 99.77 s, despite 174 versus 65 retained LOC. Both retain ten unordered pairs and all dependent steps. | Flat/typed arrays are already tried and did not win. Compare coordinate-wise arrays or a tighter scalar hot method, reducing repeated indexed access only where the pinned JIT actually benefits. Profile message/Float costs rather than assuming allocations from syntax. Preserve pair order, exact sqrt law, initial momentum and both energies; no approximate inverse cube or parallel time steps. |
| Mandelbrot: `mandelbrot-smalltalk-published-2` | One locally corrected published source, scalar pixel loops, z0=0, at most fifty iterates, radius-2 rejection, byte packing and a buffered output stream. Median 167.26 s; this one candidate is not an optimization search. | Review ordinary source-owned row/tile jobs and scalar/two-lane state layouts supported by the pinned VM/libraries. Any vector API must be shown to exist and keep recurrence in Smalltalk. Recheck odd widths, tail bits, coordinate arithmetic order and full PBM output; no symmetry/known-interior shortcut. Buffering is already present. |
| K-nucleotide: `knucleotide-smalltalk-packed` | Whole target sequence is collected, uppercased and recoded to a ByteArray. Seven serial passes roll exact two-bit keys (up to 36 bits) through ordinary growing Dictionaries. Existing associations mutate their value after one lookup; it is not the common get/default-plus-set hit path. Median 87.90 s. | Focus on serial-width scheduling, input/String/ByteArray copy volume and generic map insertion behavior for new keys, not rediscovering rolling keys or Association reuse. Compare bounded independent worker VMs or a source-owned chunk parser with k−1 carries. Preserve every width, actual map growth and every overlapping update; use exact THREE-token fixtures below. |
| Spectral norm: `spectralnorm-smalltalk-recurrence` | Float64Arrays and exact integer denominator recurrences avoid recomputing the triangular formula with division in every cell. It still performs all forty dense products and does not cache a matrix. Median 12.88 s. | Recurrence and typed storage are already implemented. Compare ordinary row-block jobs, result-buffer reuse and indexed-loop dispatch on the same VM. Preserve the independent dimension, both transpose formulas, coefficient work policy and forty passes. Do not turn a successful recurrence into a cached coefficient matrix or hidden native multiply kernel. |
| Reverse complement: `revcomp-smalltalk-streaming` | Streams records, collects one record in a String, converts it to bytes, reverses/complements in place with a 256-entry table, and uses buffered bulk 60-column writes. Median 12.05 s. It already has the desirable in-place symmetric swap and lookup-table design. | Compare direct byte record collection to remove String-to-byte copies, retaining headers/comments/CRLF/empty-record behavior. Audit U/u and unknown-byte policy against the exact task contract before extending the table. Do not advertise already present lookup/in-place/buffering as new optimizations. |
| Fannkuch-redux: `fannkuchredux-smalltalk-reuse` | Reuses permutation/count/scratch arrays. It avoids copying when the first element already requires zero flips, then actually swaps every prefix in scratch; rank/checksum/maximum remain source-owned. Median 131.00 s. | Compare the pinned collection's ordinary bulk copy/reversal operations and source-owned independent rank ranges, with factoradic initialization and bounded VM workers if supported. Existing scratch reuse is already good. Preserve all permutations, every required flip and checksum signs; no closed-form count or native permutation executor. |
| FASTA: `fasta-smalltalk-buffered` | Reuses a 61-byte line buffer, advances every LCG state, divides in binary64, performs cumulative-probability binary search, and writes through a buffered binary stream. It carries seed state from TWO into THREE and avoids generator-period caching. Median 9.79 s. | Buffer reuse/binary search are already implemented. Compare larger ordinary output batches, reusable CDF data and supported source-loop forms, retaining exact floating comparisons and all random draws. A generic affine-scan candidate would need its own work-policy review; no integer cutoff or output/period cache is silently equivalent. |
| Binary trees: `binarytrees-smalltalk-arrays` | Every leaf/branch is a new two-slot Array. Stretch is immediately checked then dropped, the long-lived root is retained, and repeated trees are built and traversed. Saved adversarial evidence checks identity and equal size at depths 0–8. Median 17.09 s. | Compare ordinary two-field node instances and bounded independent iteration jobs, measuring GC/allocation behavior. Do not assume Array is slower than an object or that a small identity check proves full-size resource feasibility. Preserve fresh leaves, equal-size nodes, stretch release and root lifetime; no shared constants, flattening, arenas or algebraic checks. |
| Regex-redux: `regexredux-smalltalk-regex`, `regexredux-smalltalk-pcre2` | Native Pharo regex source takes 524.23 s; PCRE2/UFFI source takes 2.86 s. PCRE2 version copies input once to stable native storage, uses general JIT compilation/matching and exact overflow-sized substitutions, while the Smalltalk application owns nine counts, five ordered substitutions, buffers and output. Generic binding methods are a reviewed excluded section. | The main engine alternative is already tried. Compare a reusable arbitrary-pattern count-only primitive like the existing APL/K/BQN interfaces to reduce one UFFI crossing per match, with all nine pattern calls still visible in Smalltalk. Keep generic library authorship/source cost separate, and do not implement a native nine-pattern redux executor. Parallel counts need independent matcher state and whole-process copy/IPC accounting; substitutions stay ordered. |
| Pi digits: `pidigits-smalltalk-published-1`, `pidigits-smalltalk-compact` | Both use unbounded native Pharo integers and source-controlled spigot updates. Published derivative was corrected to perform both actual extraction divisions and proper partial-line padding. Compact is 35 versus 75 retained LOC; published is slightly faster, 3.93 versus 4.23 s. | Compare generic integer/library arithmetic and intermediate reuse without removing either extraction or the impossible-candidate guard policy. GMP is an optional general-library experiment, not an already measured Smalltalk win. Preserve arbitrary precision, source-owned consume/produce and all padded output; no digit generator helper or answer table. |

## Parser and alphabet coverage limits

The nucleotide recognizer uses `line beginsWith: '>THREE'` at source line 19,
so it accepts a misleading `>THREEX` header as the target. Its saved independent
[Python reference](../../../archive/comparisons/remaining-languages-comparison/20261011/support/smalltalk/validate.py)
uses the same prefix test. Existing fixtures include `>THREE varied` and a later
record, but do not distinguish the exact token from a longer identifier.
Canonical output success therefore does not establish that distinction. A local
candidate needs missing/empty target, exact token, longer-prefix, description,
trailing-header and chunk/line-boundary fixtures. Preserve the original saved
observations; this audit did not execute a failing Smalltalk case.

Reverse complement's table is initialized to zero and populated from
`'ABCDGHKMNRSTVWY'` plus lowercase. **U/u are absent**, so those bytes would map
to zero in this implementation. The saved Python reference also omits U, and
the [saved fixture producer](../../../archive/comparisons/remaining-languages-comparison/20261011/support/smalltalk/adversarial.py)
tests canonical FASTA and a mixed-case/comment/CRLF fixture without U. Canonical
FASTA's generator does not produce U. The local workload README does not retain
the full primary alphabet contract; other retained language mappings include
U→A, but those implementations do not themselves establish the authoritative
input rule. This is an **unresolved extended-alphabet/fixture gap**, not a new
claim that the saved canonical timing failed validation. Reconcile the exact
task contract and add U/u/unknown-byte cases before changing eligibility or
claiming general IUPAC coverage. Shared omissions in an oracle and application
are not independent evidence of the missing behavior.

## General support, source size and idiom

The PCRE2 source's reviewed generic `BenchmarkPCRE` section is **lines 2–78**,
excluded by the current application-accounting partition. Patterns, cleanup,
length tracking, nine-pattern/five-substitution orchestration and application
buffer ownership remain in the 65 application units. The old provenance prose
still says all FFI declarations count; use the explicit current
`source_accounting`/`support_line_ranges` metadata for actual totals. Generic
loaded VM plugins, standard integer/collection code and installed PCRE2 are
outside application LOC consistently with installed libraries in other languages.

Published n-body and pi sources also contain generic `StdioStream` formatting
extensions, still counted because no embedded partition has been qualified for
those exact sections. They are a legitimate future accounting-review question,
not an automatic deduction. Workload-specific classes, accessors, recurrence,
parsing and output construction remain application source. Moving a whole
benchmark behind a native/helper method cannot remove its cost or establish a
pure Smalltalk implementation.

Smalltalk cascades, closures, collection messages, literal arrays and message
composition are genuine expressive constructs. Literal periods/semicolons,
method/file-in delimiters and multiline data must not become guessed executable
units. Independently sequenced assignments and side effects still need native
AST owner treatment. The retained cohort uses significant-row counts plus
Smalltalk-specific packed-statement/cascade heuristics; it is not a complete
native parser certificate or the same policy as the new Python/Julia logical
metric. No fresh logical recount or qualified native formatter is claimed here.
