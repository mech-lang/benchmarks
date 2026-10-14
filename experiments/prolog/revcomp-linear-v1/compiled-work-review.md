# Compiled reverse-complement work review

The executed linear candidate preserves the complete reverse-complement
transformation in authored Prolog. Its retained QLF traverses bounded input
blocks, stores the current record in bounded strings, reverses the complete
record across chunk boundaries, complements every sequence code, and writes
60-column output. Inspection finds no per-base whole-record conversion or
copying operation. This establishes the source and compiled algorithm's work
structure for the exact artifact below. Full-input completion, measured scaling,
peak memory at the prescribed workload, and timing admission remain separate.

The earlier source-only notes and producer receipts are unchanged. In
particular, the bounded producer's `source_work_qualified`,
`full_timings_qualified`, and `chart_admission` fields remain false. This review
adds evidence; it does not rewrite their recorded scope.

## Executed evidence and identity

The [bounded report](bounded-run-v1/report.json) closed on
2026-10-14 at 11:08:10 UTC with 542 completed native processes: one compiler,
one independent QLF inspection, and 540 candidate invocations. All 54 fixtures
ran through production capacity 65,536 and diagnostic capacities 1, 2, 3, 7,
59, 60, 61, 64, and 127. The registered ledger contains 542 distinct PIDs and
uses the same QLF for all 540 invocations. The outcomes are 470 exact complete
outputs and 70 expected invalid-IUPAC rejections. There are no admitted
benchmark samples in this stage.

The [terminal](bounded-run-v1/terminal.json) binds the complete artifact inventory
and reports no integrity or artifact errors. The
[durable terminal](../full90-v1/owned-jobs/revcomp-linear-bounded542-v1/terminal.json)
records controller PID 58761, exit zero, and no stop signal. Subsequent
[source-reader preparation](source-counts-v1/plan-v1.json) replays the closed
542-process prerequisite, including each process's recorded controller parent,
birth identity, reaping, empty final process group, stdout/stderr and policy.

The raw compiler and inspector receipts deliberately retain their generic
observer status `failed`: both exited zero but emitted the exact previously
reviewed weak-import warning. The bounded controller reconciled only that
110-byte warning. Likewise, the 70 invalid-input receipts retain exit one;
their exact domain error and already-written `>r\n` prefix were required.
Neither class of exception was relabeled inside its raw process receipt.

| Artifact | SHA-256 |
| --- | --- |
| [Candidate source](candidate.pl), also the actual [compiler input](bounded-run-v1/authored/candidate.pl) | `bb4826e39721c6e4e61330ee3f56db604e1d48498c32fdd9453b133e35508322` |
| [Prepared bounded plan](bounded-plan-v1.json) | `0f6e8e4608e0599f5de091160491f51e5b720af7f4cff6c579b9962d3333dfcc` |
| [Fixture manifest](fixtures-v1/manifest.json) | `5c02ccd7d02e39593696325bde6b0f858e5e254ef7e795eaf8261e036d7cae20` |
| [Executed QLF](bounded-run-v1/authored/candidate.qlf), 3,352 bytes | `c4526a2d463d5c9c570e88b5ab68237ecf61244d104825ab1e4fbb66b13c1f9e` |
| [QLF inspection WAM](bounded-run-v1/inspect/candidate.wam) | `c1d9df9c726f093dc642d30e6137bbcebbdb46dc70126ff14be5cf3e16c1e2da` |
| [Inspection metadata](bounded-run-v1/inspect/loaded-inputs.json) | `54891639e089420313cf51823b24ce5dfa70f4c69497feecacc0a2967808e764` |
| [Bounded report](bounded-run-v1/report.json) | `00c1e0482a84cb1b0a2b98e9de9da3c8bbed450f5795ebd420ab98e2900788eb` |
| [Bounded terminal](bounded-run-v1/terminal.json) | `67deb45715f73215e5251884597c2d54d7ae619e9878346c901cfbb712d07686` |
| [Bounded durable terminal](../full90-v1/owned-jobs/revcomp-linear-bounded542-v1/terminal.json) | `8cf447e226f0ecb90bb77832006a1b18479b8a6f19b07e9ad196351959f53589` |

Inspection loaded the QLF in a fresh SWI-Prolog 10.0.2 `arm64-darwin` process,
with `-q -O -f none --stack-limit=8g`. The recorded runtime has `gc=true`,
`bounded=false`, and an 8 GiB stack limit. The loaded authored source is the
exact candidate copy. Vendor sources and the inspector's JSON library appear
in [loaded-inputs.json](bounded-run-v1/inspect/loaded-inputs.json) and are bound
by the prepared physical-runtime pins. This inventory belongs to the actual
compiler/inspector processes; it is not a claim that each fixture process
emitted its own dependency inventory.

The independent native source reader identifies 22 authored predicates, exactly
matching the inspected WAM inventory. Its
[candidate projection](source-counts-v1/run-v1/candidate-original-source/projection.json)
also verifies equality between original and compiler-input bytes. Canonical
owner accounting is reviewed separately; all startup, diagnostic, parser,
mapping, error and output code belongs to this one authored source.

## Instructions retain the required transformation

Line citations in this table refer to the original source and the saved QLF
inspection, not a regenerated disassembly.

| Work obligation | Source and actual WAM evidence |
| --- | --- |
| Fixed production block bound | `candidate.pl:27–36` selects 65,536 and checks a positive integer. WAM `block_capacity/1` at line 518, `main/0` at 666, and `main_with_capacity/1` at 46 retain that path. |
| Read and traverse every input code | `candidate.pl:41–53`; WAM `read_blocks/2` calls `read_string/3` at line 15, `string_codes/2` at 30, and `consume_codes/4` at 35. `consume_codes/4` calls `consume_code/4` at 105 and advances the list tail at 107–114. |
| Store each sequence code and preserve full record order | `candidate.pl:55–102`; WAM `push_code/8` at 184 constructs a list cell, increments the count, and performs `reverse/2` and `string_codes/2` only at the chunk-capacity branch (207, 210). The remaining branch preserves the pending list without traversing it. |
| Reverse across chunks and within each chunk | `candidate.pl:110–128`; `emit_record/3` finishes the pending chunk at WAM line 1078 and calls `emit_chunks/4` at 1083. Each chunk is converted once (702), reversed once (705), and sent to `emit_codes/5` (711); the next chunk is the tail of the already reversed chunk list. |
| Complement each emitted sequence code | `candidate.pl:130–139,147–171`; WAM `emit_codes/5` calls `complement/2` at 745. WAM lines 796–820 retain lowercase folding and dispatch to `complement_upper/3`; lines 228–389 retain the sixteen mappings and the invalid-code throw. |
| Preserve the 60-column output position across chunks | `candidate.pl:123–145`; WAM carries the returned line and column into the next chunk at 712–721. The per-code loop compares with 60 at 753–757, reverses that bounded line at 761, formats it at 767, and resets only after output. The final nonempty tail is emitted separately. |
| Preserve headers, EOF and failure behavior | `candidate.pl:15–25,55–77,98–121`; the corresponding WAM retains octet stream setup, flush, header emission, line termination, final-record emission and error exit. The wrapper has no workload-size shortcut or precomputed output. |

Every WAM foreign/library call used by the transformation is a general stream,
list, string or output operation. There is no `get_string_code/3`, whole-record
concatenation, reverse-complement primitive, generated answer table, or custom
native transformation in the candidate's call inventory. The indirect
`call/1` in the wrapper selects its authored production or capacity diagnostic
goal; it does not move the transformation into a helper outside the counted
source.

## Ordering and boundary proof

After any sequence prefix, `Chunks` holds completed strings in reverse arrival
order, each string's contents remaining forward. `Pending` holds the newest
incomplete suffix in reverse order, with length below the capacity. A full or
final partial chunk is reversed once into a forward string and prepended.
Visiting this chunk list and reversing each string's code list therefore
produces the reverse of the complete sequence, including across physical input
lines and block boundaries. Applying the explicit complement to that traversal
is the complete record reverse complement.

Only a line's first byte can introduce a header or comment. CR and LF each
terminate a line; the second terminator of CRLF creates an empty transition
without adding a base or changing the completed header. An ignored preheader
or comment line never enters the sequence accumulator. An inline `>` or `;`
remains a sequence code and is rejected. Header chunks are reversed into forward
order once, and their bytes are emitted without changing case or encoding.
EOF completes a pending header or the current record. Empty records emit the
header and LF without an extra sequence line.

The native cases cover both cases of all sixteen IUPAC symbols, binary header
bytes, comments and preheader text, consecutive and unequal records, CR/LF/CRLF,
EOF without newline, wrapped and unwrapped input, lengths around 60 and the
production capacity, a 131,073-base line, and long headers/comments. Capacity
one also exercises every possible input boundary, including split CRLF. The
invalid reverse-order case `!AC?` reports code 63 (`?`), confirming reverse
error order; every rejected fixture retained exactly `>r\n` before its error.
The 54 cases provide bounded conformance evidence, not exhaustive testing of
arbitrarily large input.

## Traversal cost and lifetime

For fixed capacity `B`, every input byte is consumed once. Sequence codes are
prepended once, converted/reversed in a completed chunk once, and traversed
again during output. Output-line reversal touches at most 60 codes. Header
chunk-order reversal visits each header chunk once. Each complement lookup has
at most sixteen accepted clauses plus the error clause, independent of record
length. The source-level traversal and conversion work is consequently linear
in input plus output size. The original record-length-squared conversion path
is absent from the inspected QLF.

This bound uses the retained vendor implementations. Their paths are relative
to the pinned `official-source/swipl-10.0.2` tree recorded in the bounded plan:

| Runtime source | Relevant implementation | Pinned SHA-256 |
| --- | --- | --- |
| `src/pl-string.c:135–165,524–565` | `string_codes/2` uses ordinary text conversion; `read_string/3` reads no more than its supplied length. Every candidate conversion argument is a bounded block/chunk. | `53a0ca839f914964fc8c085401b3d85ff66da874d233837975ec25dd28c061a1` |
| `library/lists.pl:403–415` | Proper-list `reverse/2` traverses the list with an accumulator and bound list. The installed library has the same pinned bytes. | `386f3c5f1ee00bc79103cc12628d6ad83b6141e1bf3fdbf41e7bf6b579e902ce` |
| `src/os/pl-fmt.c:789–811` | `~s` converts and writes its supplied text. Candidate arguments are one header chunk or one output line, never a whole sequence record. | `d7d48910d00f1906347c21e249818803b6b590831b285689f179de287a2dc47d` |
| `src/pl-vmi.c:2039–2080,2398–2406,2535–2550` | Conditional last-call paths reuse the current frame when their native conditions hold. The inspected loops retain `l_nolco`, `i_tcall` and `i_depart` instructions. | `e696d895187b92b46f4647977000c8e64aad2de1a518ec04ba18063d0d5e36a2` |
| `src/os/pl-prologflag.c:2033` | Last-call optimization defaults to true. This candidate does not change that flag. | `16faab0f1f94263743430e5d84be363331432441bb2ef2ae14089ad4e8d9d8bb` |

The complete current record remains retained as bounded strings and list
links. `emit_record/3` and its callers can keep the record root alive until
emission returns; the source does not establish immediate per-chunk collection.
The next record begins with empty sequence accumulators. Active input blocks,
temporary chunk code lists and pending lists are bounded by the capacity, and
the output buffer by 60 codes. This supports record-sized application data,
not constant total memory. Garbage-collector scheduling, allocator behavior,
actual last-call paths and process RSS are not inferred from a source bound.

No measured scaling claim follows from this analysis. Full prescribed-input
output validation and separately retained full-process samples are still needed
before this candidate can supply a plotted reverse-complement timing.
