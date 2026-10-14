# Prolog reverse-complement: repeated string copying and a linear traversal design

The retained reverse-complement program performs a whole-record string copy
for every sequence character through its SWI-Prolog 10.0.2 runtime interface.
For a record of length `L`, this creates quadratic copying work. The source
and retained VM listing identify the call responsible; the runtime source
explains its cost.

This note records source analysis and a separate [draft candidate](candidate.pl).
The candidate has not been compiled, executed, qualified, or measured.
It provides no new timing result, profiler observation, or completion estimate.
The original source, compiled artifacts, qualification evidence, and timing
study remain separate, unchanged evidence.

## Retained implementation and compiler evidence

The [full-study plan](../full90-v1/plan.json) identifies the exact
`prolog-revcomp-compact` measured source and its two helpers in
`manifests.revcomp.profiles[].source_bundle`. The following repository copies
were compared directly with those measured source files and are byte-identical.
Line numbers refer to these retained files.

| Source | Relevant behavior |
| --- | --- |
| [compact.pl](../../../archive/languages/prolog/20261013/qualification/prepare-explicit-goal-rest-v1/builds/prolog-revcomp-compact/input/sources/revcomp/compact.pl#L23), lines 23–28 | `reverse_codes/5` calls `get_string_code(Position0, Sequence, Original)` once per base while decrementing the position. The same complete `Sequence` is passed to every call. |
| [compact.pl](../../../archive/languages/prolog/20261013/qualification/prepare-explicit-goal-rest-v1/builds/prolog-revcomp-compact/input/sources/revcomp/compact.pl#L30), lines 30–42 | Output is assembled into fresh lists of at most 60 codes. Each list is formatted once; the complete record string is constructed before this loop. |
| [compact.pl](../../../archive/languages/prolog/20261013/qualification/prepare-explicit-goal-rest-v1/builds/prolog-revcomp-compact/input/sources/revcomp/compact.pl#L6), lines 6–20 | Complement lookup scans a fixed 32-character table, covering uppercase and lowercase IUPAC symbols. |
| [clbg_records.pl](../../../archive/languages/prolog/20261013/qualification/prepare-explicit-goal-rest-v1/builds/prolog-revcomp-compact/input/support/clbg_records.pl#L2), lines 2–10 and 21–23 | Input is split at CR or LF. Reversed line chunks are reversed once and concatenated once with `atomics_to_string/3`. |
| [clbg_io.pl](../../../archive/languages/prolog/20261013/qualification/prepare-explicit-goal-rest-v1/builds/prolog-revcomp-compact/input/support/clbg_io.pl#L8), lines 8–14 | Input and output use octet encoding; successful completion flushes output. |

The retained [original-scored.wam](../../../archive/languages/prolog/20261013/qualification/prepare-explicit-goal-rest-v1/builds/prolog-revcomp-compact/original-scored.wam#L188)
lists `clbg_revcomp:reverse_codes/5` at line 188. Its recursive clause contains
`i_call(get_string_code/3)` at line 211 and `i_call(complement/2)` at line 214.
This is an observed listing of the retained compiled program, not a new
disassembly. The optimized compilation did not eliminate the character-access
call identified here.

The plan records the same main-source SHA-256 for both authored forms:
`2460ba65f9231222000980236c6c4ca7b101f6fef3313aa37f125dc171bc59fc`.
Its optimized form is explicitly an equivalent-source alias. Selecting that
alias therefore preserves this source-level cost.

## Why a character access copies the whole record

These locations refer to the retained official SWI-Prolog 10.0.2 source tree
whose logical path ends in
`benchmarks/clbg/prolog-comparison/20261013/.build/swi-runtime-directory-v1/official-source/swipl-10.0.2/`.
The full host paths and recorded pins are available in the
[full-study plan](../full90-v1/plan.json). These are locations in that retained
version, rather than an assumption about all SWI versions or all Prolog systems.

| Runtime source location | Effect in this call chain |
| --- | --- |
| `src/pl-string.c`, lines 342–362, `get_string_code/3` | Calls `PL_get_text(A2, &t, CVT_ALL\|CVT_EXCEPTION)`, then returns the indexed character. |
| `src/SWI-Prolog.h`, lines 940–963 | `CVT_ALL` includes string conversion; neither it nor `CVT_EXCEPTION` includes the separate `BUF_ALLOW_STACK` flag. |
| `src/pl-fli.c`, lines 907–918, `get_string_text` | Retrieves the string data and marks its storage `PL_CHARS_PROLOG_STACK`. |
| `src/os/pl-text.c`, lines 219–224, `PL_get_text` | Calls `PL_from_stack_text` for a string after obtaining that storage descriptor. |
| `src/os/pl-text.c`, lines 129–143, `PL_from_stack_text` | Without `BUF_ALLOW_STACK`, copies `length + 1` character units out of the Prolog stack into local storage or a temporary buffer. A full sequence takes the buffer branch. |
| `src/os/pl-buffer.h`, lines 91–104, `addMultipleBuffer` | Copies every requested element in a loop. Buffer reuse does not remove the data copy. |
| `src/os/pl-text.h`, lines 127–131, `text_get_char` | The final indexed lookup is constant-time; the preceding whole-string copy causes the scaling problem. |

For ASCII sequence data, each access consequently copies `L + 1` bytes and
the application makes `L` such accesses per record. The dominant copied-byte
volume is therefore `sum(L * (L + 1))` across records. The fixed-size complement
lookup contributes additional bounded work per base; it does not change this
quadratic term.

For the canonical input size `n = 25,000,000`, the FASTA record lengths are
`2n`, `3n`, and `5n`: 50 million, 75 million, and 125 million bases. The
[retained FASTA source](../../../archive/workloads/fasta/fasta-optimized.mec#L37),
lines 37–43, shows these lengths, and the reverse-complement plan specifies
this full input size. Applying the formula gives
`23,750,000,250,000,000` copied bytes, approximately **23.75 decimal PB**.
This is an analytical count implied by the source path. It is not measured
memory traffic, allocated resident memory, disk I/O, or an elapsed-time
prediction. Actual cache and memory traffic depend on the compiled runtime and
hardware; each copy also reads its input and writes its destination.

Other costs remain: one native line-reader operation per input line,
short-lived line strings, a list node per retained line, a fixed-table scan per
base, fresh output code lists, and one format operation per output line.
The reader's character loop is in `src/pl-string.c:465–502`; the application's
output call is once per 60 bases, not once per base. Prepending input chunks
and concatenating them once is distinct from the repeated whole-record access.

## Draft bounded-chunk traversal

A follow-up implementation can keep the complete workload in authored Prolog
while avoiding repeated conversion of a whole record. The draft uses
ordinary bounded stream reads, code-list conversion, list traversal,
string storage, and output formatting. No runtime modification or specialized
reverse-complement foreign primitive is required by the design.

1. **Read bounded octet blocks.** Choose a fixed block capacity `B`, independent
   of record and physical-line length. Read at most `B` bytes and convert each
   block to a code list once. Traverse that list directly. Keep parser state
   across block boundaries, so a long input line never becomes a repeatedly
   indexed whole-line string.
2. **Parse record boundaries without retaining ignored text.** Track whether
   the parser is at the start of a line, inside a header, inside a comment, or
   inside sequence text. Recognize `>` and `;` only as the first byte of a line.
   Ignore preheader sequence text and comment lines. Retain header bytes in
   bounded segments when necessary, preserving the complete header.
3. **Retain one record as bounded sequence chunks.** Pack sequence codes into
   chunks of at most `B` bases, preserving their order within each chunk.
   Convert each finished chunk to compact string storage once and prepend it
   to a chunk list. Flush a nonempty partial chunk at the end of a record.
   This list is already in reverse chunk order. Do not concatenate it into
   one large sequence string.
4. **Reverse the entire record.** At the next header or EOF, emit the saved
   header followed by LF. Visit the reversed chunk list from its head. Convert
   each chunk to a code list once, reverse that bounded list, and complement
   every code while consuming it. Reversing both the chunk order and the codes
   within each chunk yields exactly the reverse complement of the complete
   record, including across input-line and block boundaries.
5. **Carry output position across chunks.** Keep a 0–59 output-column state
   and a bounded output buffer. Emit a newline after every 60 bases. At record
   end, emit a newline only if a partial sequence line remains. Do not reset
   the column at an input line or internal chunk boundary. An empty record
   emits its header and LF with no additional blank sequence line.
6. **End the completed record's lifetime.** The next record begins with an
   empty chunk list and pending buffer. Caller frames may retain the old chunk
   list until emission returns; immediate per-chunk reclamation is not
   established by this source review. Ordinary runtime collection remains
   enabled. Record reversal still requires retaining the current record;
   bounded chunks do not imply constant total memory.

With constant-time code classification and complement selection, each input
byte and retained sequence code participates in a bounded number of traversals
and conversions. The intended bound is `O(N + H)` work and
`O(max_record_bases + max_header_bytes + B)` retained storage, with
`O(max_record_bases / B)` chunk-list nodes. Temporary code lists and output
buffers are bounded by `B` and the chosen output-buffer capacity. `N` includes
all input bytes and `H` the header bytes written. Runtime behavior, garbage
collection, and these bounds still require compiled review and testing.

The complement mapping must preserve all sixteen symbols, accepting either
case and producing uppercase output:

| Input, either case | A | C | B | D | G | H | K | M | N | S | R | U | T | W | V | Y |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Output | T | G | V | H | C | D | M | K | N | S | Y | A | A | W | B | R |

Direct clauses indexed by input code, or an explicitly reviewed bounded lookup,
can replace the current symbol scan. Sequence characters outside this table
must not be silently dropped, normalized, or replaced. Complementing in the
reverse emission order also preserves which invalid sequence code is reached
first; the current error is `domain_error(iupac_nucleotide, Code)`.
The candidate buffers a whole 60-base output line before formatting it. If
complementing a code fails, it emits none of the affected line, matching the
retained program's output-prefix behavior.

CR, LF, and CRLF terminate input lines. Parser state must handle CRLF split
between read blocks. Treating CRLF as one terminator preserves the existing
helper's effective sequence behavior: its separate delimiter reads add an
empty line, which contributes no sequence bases. Header text excludes the
terminator; output uses LF. Blank lines add no bases. Spaces and tabs inside
a sequence are not silently stripped. An EOF without a trailing newline
finishes the current line and record; header-only EOF emits that header, while
empty input and input with no header emit nothing. Consecutive headers retain
empty records and their original order.

## Candidate interface and source-only review

`candidate.pl` is self-contained authored Prolog. Production `main/0` uses a
fixed capacity of 65,536 bytes. Its startup wrapper selects octet encoding,
calls the main predicate, flushes successful output, and exits through the
same success/error pattern as the retained helper. Octet encoding provides
byte-valued input and output; the draft does not change the streams to SWI's
distinct binary stream type.

The exported diagnostic entry point is
`clbg_revcomp_linear:diagnostic(Capacity)`. It requires a positive integer,
selects the same octet streams, processes stdin with that capacity, flushes
successful output, and exits. This supports future fixtures with capacities
1, 2, 3, 7, 59, 60, 61, 64, 127 and the production boundary without changing
production `main/0`. No diagnostic invocation has run. Its explicit runtime
goal must be selected by the later qualification controller instead of running
both the production initialization and a diagnostic goal.

Source review traced the line-state transitions, header and sequence chunk
ordering, all sixteen mappings and lowercase folding, 60-column carry, and
EOF cases. An independent source reader found no functional blocker and
identified the record-lifetime qualification stated above. This is inspection
of the draft, not a Prolog parser result or execution-based correctness proof.
The runtime source for `read_string/3` at `src/pl-string.c:524–555` bounds reads
by its supplied length. Each draft string/code conversion is called once for
a bounded block or chunk; no loop indexes a whole-record string.

All startup, diagnostic, parser, chunk-building, mapping, error-handling, and
output predicates belong to the authored source bundle and must be included
in its eventual source-unit count. The generic SWI stream, string conversion,
list reversal, and formatting operations remain vendor dependencies under the
existing methodology. No custom FFI or hidden native reverse-complement work
has been introduced. The longer explicit parser is a source-size tradeoff;
neither canonical nor formatted LOC has been qualified, and no shorter-source
claim is made.

## Evidence needed for a follow-up result

The implementation would be a new candidate with its own source, compiler
inputs, VM listing, work review, source counts, and timing evidence. Existing
results describe the unchanged retained program and remain attached to it.

The independent [fixtures.py](fixtures.py) prepares 54 cases: 47 with exact
expected output bytes and seven with an expected invalid-IUPAC code. Its
reference collects whole records and uses Python byte reversal and translation,
rather than reproducing the candidate's chunk traversal. It includes nine
diagnostic capacities and sequence lengths 65,535, 65,536, 65,537, and 131,073,
plus long headers and comments. Handwritten oracle self-checks have passed;
the candidate has not been run against these cases. Invalid-case expectations
identify the rejected code without specifying partial stdout.

The separate [bounded conformance protocol](bounded-protocol.md) covers all 54
fixtures through the production entry and nine diagnostic capacities. Its
controller is prepared as source; compilation and native execution remain
pending the shared measurement lane.

The pure oracle checks can be repeated with:

```sh
python3 -I -S -B experiments/prolog/revcomp-linear-v1/fixtures.py
```

To materialize input, expected-output, and manifest files in a fresh directory:

```sh
python3 -I -S -B experiments/prolog/revcomp-linear-v1/fixtures.py \
  --output NEW-FIXTURE-DIRECTORY
```

Neither command invokes Prolog. These are unscored qualification utilities;
their results do not establish candidate correctness or performance.

Before full-size measurement, bounded conformance cases should compare complete
output bytes for every IUPAC symbol in both cases; empty and header-only input;
preheader and comment text; consecutive empty records; CR, LF, CRLF, split CRLF,
and missing final newline; and record lengths around 60 and `B`. Include long
physical lines, headers and comments spanning several blocks, and several
unequal records. Vary the test block capacity to demonstrate that internal
chunk boundaries do not alter output. Check invalid sequence codes explicitly.

The compiled review should establish that no per-base operation converts or
copies the complete record or an unbounded physical line. A separately owned,
bounded scaling experiment could then test the proposed linear behavior, with
ordinary allocation and collection visible. Only subsequent complete canonical
input/output validation and independently reviewed full timing samples can
establish a successful optimization or a new performance comparison.
