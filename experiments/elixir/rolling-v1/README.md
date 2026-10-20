# Elixir k-nucleotide: rolling-key candidates

These are **unexecuted source proposals**. No Elixir parser, compiler, runtime,
formatter, test or benchmark has run for this packet. They change no catalog
entry, source count, eligibility or timing. Compilation, correctness, work and
performance remain open gates.

The retained compact and optimized implementations have identical source bundles.
Their counting loop creates a `binary_part` key and calls `Map.update` for every
overlapping window, scanning all seven widths serially. The candidate keeps the
standard growing Elixir map and every occurrence update, but encodes each input
base once and carries a rolling integer key through a binary-pattern tail loop.
It does not replace table updates with a histogram, dense lookup or query-only
counting kernel.

The complete serial source is [sources/serial.ex](sources/serial.ex). The
parallel form uses the same source-owned parser, rolling loop, complete maps and
formatting, with at most seven ordinary `Task.async_stream` workers, one per
width. These are independent language-level processes, not native nucleotide
executors. Both variants keep all workload logic in the counted main source;
the unchanged generic support and runner remain separately inspectable.

## Required work and representation

For width k, `prefix` consumes exactly k-1 symbols or returns `:short`. Each
remaining symbol shifts the key by two, incorporates that symbol and masks to
2k bits, then calls `Map.update` once. Thus each width updates its default-empty
map exactly max(0, n-k+1) times. The seven widths are 1,2,3,4,6,12,18; full
N=125,000,000 calls for **874,999,961 occurrence updates**. These are source
counts, not an executed witness or a claim of one internal hash probe per update.
All 36 key bits at the largest width represent actual bases; no approximate
hash or unchecked overflow substitutes for the key.

Each complete histogram is built before its frequency or query result is used.
Only widths1/2 need frequency output; each longer-width task can release its
complete map after its required query. Returning final output rather than the
whole map may avoid expensive interprocess map copies in the parallel variant.
No occurrence or distinct key is omitted, and the map remains the ordinary
built-in data structure growing from `%{}`. The serial variant isolates integer
keys and binary traversal from the additional scheduling change.

For a fixed width, base-4 integer order equals A/C/G/T lexical order, so frequency
ties retain the same ordering before decoding keys for output. Formatting uses
the unchanged locale-independent generic helper. Empty maps produce the same
blank frequency section and zero query count. The old exact-token THREE parser,
case handling, comment skipping and complete input/output boundaries remain;
these source claims still require the shared adversarial corpus and additional
short/record cases before admission.

## Qualification and measurement gates

Restore the exact retained Elixir/OTP distribution and flags; do not substitute
a newer JIT/runtime and attribute that effect to source changes. Compile each
candidate in an isolated module/output path with the unchanged generic support;
retain every warning and inspect actual BEAM/JIT lowering. Binary tail syntax
is a hypothesis about efficient match-context reuse, not proof that the VM
eliminates all sub-binary/tuple/callback allocations.

Run the complete shared k-nucleotide corpus, including mixed case, record token
boundaries, comments, missing/empty/short sequences, all widths and sorting ties.
Compare every full histogram at small sizes against the original, not only its
five final query counts. A separate untimed witness must show every occurrence
update, default map growth and all widths. Check actual task bounds, failure
propagation, complete output and worker cleanup. No benchmark may overlap another.

Use a bounded fresh-process pilot before committing resources to the full input.
Then compare qualified candidates in sequential shuffled complete-process rounds,
including VM startup, input parsing/encoding, all map operations, output and exit.
Keep old measurements unchanged and report source-size tradeoffs independently
from timing. Retained-rule and canonical-formatted counts are unassigned until
qualified; byte/gzip/BPE measures must use the same reviewed application scope.

The new edits have current Codex GPT-6-family authorship; no exact model variant
or original predecessor author is inferred. Preserve the predecessor references,
notices and unresolved inherited terms at any future intake.
