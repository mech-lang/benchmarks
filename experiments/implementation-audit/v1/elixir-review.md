# Elixir: complete retained-source review

Reviewed **all twenty retained Elixir profiles**, comprising ten distinct main
applications plus their common support/launcher. Every compact/optimized pair
has identical retained application bytes. Their separately measured observations
must remain separate; the labels do not establish two algorithm designs. Exact
main/helper/launcher SHA-256s and source roles remain in
[inventory.json](inventory.json) and the [source bundles](../../../programs/elixir/).
No BEAM/native program, compilation, browser or timing was started.

The recorded configuration is Elixir 1.20.4 / OTP 29 / ERTS 17.1 BEAM JIT,
`+S 8:8 +A 1 +SDcpu 1:1 +SDio 1`. Eight enabled schedulers do **not** make these
serial applications parallel. All ten main texts currently execute their
workload loops in one source process. Source-origin metadata records local
adaptation but leaves original implementation/model identity unresolved; preserve
that uncertainty rather than inferring authorship.

The generic support already provides binary Latin-1 I/O, 65,536-byte input reads,
CRLF/CR/LF splitting, argument checks, and exact binary64 decimal formatting.
Its input helper eventually concatenates all chunks. The launcher calls
`Clbg.Main.main(System.argv())`; recorded commands load compiled BEAM modules.
Startup/module loading, I/O, JIT/runtime work, GC and shutdown belong in the final
whole-process timing. The recommendations below are unmeasured candidates.

| Workload / both reviewed profile suffixes | Source-specific cost and existing strengths | Valid optimized/expressive alternative and checks |
| --- | --- | --- |
| N-body / `elixir-nbody-compact`, `elixir-nbody-optimized` | Immutable seven-field body tuples are nested in a five-body tuple. Every pair builds a displacement tuple, nested `Enum.reduce` closures and index ranges; each axis makes new `put_elem` body tuples, then outer tuples are replaced. Median winner 142.33 s. | Pattern-match the fixed body tuples once, calculate all three velocity components together, and reconstruct each affected body once per pair. Compare source-owned tail recursion or ordinary compile-time specialization of the ten pairs with repeated generic enumeration. Keep pair order, exact sqrt/division, every sequential step, momentum and both energies; no NIF executor or parallel time steps. Count any workload-specific generator/macro source under an explicit policy. |
| Mandelbrot / `elixir-mandelbrot-compact`, `elixir-mandelbrot-optimized` | A scalar recursive `inside` correctly escape-tests each new iterate; serial rows pack bits through a list then convert to binary. Every pixel recomputes `2*y/n-1`, and `rows = for ...` retains the complete bitmap until one write. Median 311.85 s. | Hoist row coordinates and immutable real coordinates, then use ordered bounded row/block tasks with ordinary `Task`/process APIs. Stream bounded completed blocks rather than collecting the whole image. Preserve every pixel, fifty-step limit, PBM bit order and odd-width tail padding. Current n=0 rejection is explicit; do not silently invent a zero-size timing. No analytic-interior/periodicity shortcut. |
| K-nucleotide / `elixir-knucleotide-compact`, `elixir-knucleotide-optimized` | The parser already uses exact header-name tokens, first-selected-record stopping, comment handling and explicit ACGT validation. Each of seven serial passes takes `binary_part` for every window and makes a persistent `Map.update`; complete growing maps are retained. Median 393.20 s. | Transfer this exact-token parser to weaker ports. Compare rolling integer keys, binary-pattern recursion and ordinary private mutable-table/counter APIs, with explicit proof of pinned integer width and map growth. Independently schedule widths with bounded tasks if shared binary ownership/GC costs permit. Preserve all seven full maps and every window update; no query-only counts, preallocated dense answer array or native counting loop. Check empty/short records and CRLF/EOF through the shared line splitter. |
| Spectral norm / `elixir-spectralnorm-compact`, `elixir-spectralnorm-optimized` | Input vectors are tuples, providing direct indexed access. Every element runs through `Enum.reduce`, computes the coefficient and tests a transpose flag. Output rows become a list then a tuple. Ten recursive rounds perform forty dense products. Median 15.85 s. | Specialize ordinary forward/transpose source loops to remove per-element orientation dispatch; compare tail-recursive numeric row loops and bounded independent row blocks. Reuse immutable indices only where it reduces allocation rather than building more lists. Preserve coefficient/forward/transpose/composition functions, every coefficient recomputation, accumulation rules and all forty passes; no matrix cache or native eigensolver. |
| Reverse complement / `elixir-revcomp-compact`, `elixir-revcomp-optimized` | Parses complete records correctly, but converts each concatenated binary record to a per-byte list, reverses it, makes another mapped list using a map lookup per byte, then builds wrapping lists. `collect` retains all completed output records. Median 90.55 s. | Compare reverse binary indexing/patterns in bounded blocks with an ordinary byte lookup tuple/binary and bounded iodata writes. A 256-entry general lookup avoids per-byte persistent-map lookup; validate unknown-byte behavior explicitly. Preserve headers, comments, all IUPAC/lowercase/U mappings, empty records, line endings, EOF and 60-column output. Do not move record reversal/complement orchestration into a native helper. |
| Fannkuch / `elixir-fannkuchredux-compact`, `elixir-fannkuchredux-optimized` | Uses canonical rotation/carry and actual flips, but `flips` converts the tuple to a list and immediately back before processing. Every prefix reverse/rotation repeatedly `put_elem`s an immutable tuple inside `Enum.reduce`. Execution is serial. Median 472.74 s. | First remove the redundant tuple/list round trip only after confirming no ownership witness depends on it. Compare constructing a changed tuple once per prefix, a source-owned binary/list representation, and bounded factorial-rank workers with private state. Existing K/Uiua/D rank-interval sources supply concrete design references. Preserve every permutation and actual reversal, rank parity and maximum; no cached flip counts. Test n=1 and carry boundaries as well as n=12. |
| FASTA / `elixir-fasta-compact`, `elixir-fasta-optimized` | Tail-recursive loops execute each LCG step and binary64 division, use ordinary cumulative probabilities and carry the seed from TWO to THREE. Sixty-base lines become binaries, which is already better than per-byte writes. However, all ONE/TWO/THREE line lists are retained until the final `S.write`. Median 6.35 s. | Flush bounded iodata batches while preserving seed and ALU position, then compare line/batch size and allocation. Review source-level CDF selection and possible ordinary specialization before importing a more complex affine design. Preserve all seeds/divisions, exact 2n/3n/5n bases, unscaled thresholds, headers and partial lines; no cached RNG period or precomputed record. |
| Binary trees / `elixir-binarytrees-compact`, `elixir-binarytrees-optimized` | Each node is `{make_ref(), left, right}`, including leaves. The reference is an intentional fresh-identity/allocation witness, not used by `check`. Temporary trees are built then recursively checked; the long-lived tree is passed through depth recursion. Work is serial. Median 7.12 s. | Compare ordinary bounded independent iteration tasks, ensuring long-lived data is not pointlessly copied into every message. Examine a supported fresh two-child tuple/record allocation route only with independent identity/lifetime proof. Do not simply remove `make_ref()` and allow compiler-shared literal leaves. Keep equal-size nodes, every constructor/traversal, stretch release and retained root; no algebraic check, flat tree or custom native allocator. |
| Regex-redux / `elixir-regexredux-compact`, `elixir-regexredux-optimized` | Custom recursive count/replacement loops call `Regex.run` for each match, return index lists, create binary slices and finally flatten iodata. Nine patterns and five replacement pairs are clear module attributes; replacements stay ordered. Median 23.94 s. | Compare the pinned runtime's ordinary bulk `Regex.replace`/general regex APIs against the custom per-match loop, preserving literal replacements and byte semantics. Review a generic count-only API if available, or bounded independent count tasks. Keep all nine nonoverlapping scans, case rules, five dependent substitutions and the three byte-length fields. General PCRE work is allowed; a native redux orchestrator is not. |
| Pi digits / `elixir-pidigits-compact`, `elixir-pidigits-optimized` | A compact tail-recursive unbounded integer spigot performs two real divisions before acceptance, carries simultaneous state explicitly and buffers ten-character rows in an output list. Median 1.76 s. | Preserve this idiomatic baseline. Compare sharing the `3*q+r` numerator then deriving `4*q+r` by adding q, without dropping either quotient; diagnose startup versus immutable big-integer allocation separately. Keep sequential unbounded state, actual stable-digit checks, row counts/padding and complete output. Do not replace big-integer arithmetic with a fixed precision approximation or native pi executor. |

## Priority and techniques already available

Prioritize the concrete allocation/dispatch patterns in n-body, fannkuch and
reverse complement, plus serial Mandelbrot/nucleotide scheduling. The exact-token
nucleotide parser, shared byte-oriented I/O, iodata formatting, tuple-indexed
spectral vectors and compact Pi recursion are existing strengths worth
transferring. Duplicate “optimized” labels offer no evidence that idiomatic BEAM
representations, task schedules or library APIs have been compared.

Ordinary task/process candidates should bound outstanding work as well as worker
count, preserve output ordering, and avoid sending whole deep trees/maps to every
worker. The fixed scheduler/async/dirty-thread settings must be reviewed with any
new tasks and native general libraries; enabling schedulers alone is not an
optimization. No benchmark-specific NIF, foreign executable or hidden bulk
kernel is proposed.

## Source-count and provenance boundaries

Module attributes/literal tables, pipelines, pattern matching, comprehensions,
recursion and general `Enum`/`Map`/iodata primitives are valid expressive source;
their implicit scalar steps must not be expanded into fictional LOC. Written
independent bindings, packed keyword clauses, callback bodies and meaningful
directives still need explicit owner rules. Main files are actual compiler-bound
sources, while the generic support/launcher are separately partitioned in the
current accounting. Do not move workload parsing, packing, recurrence or
application-specific scheduling into excluded support to manufacture a shorter
application.

Retained normalized counts and qualified native-formatter counts are different
metrics. Use exact source partitions for application/submitted bytes, gzip and
BPE; those include comments/whitespace and do not certify logical or lexical
token counts. Source aliases and runtime medians remain separately identified.
Preserve original lineage/license gaps and source-write evidence without treating
locally retained bytes as proof of earliest authorship or model identity.
