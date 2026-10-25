# Compact immutable ASCII mapping

The compact mapper at Mech source `d1ae94f68423c88602ee55794fc47ea0da0e05a3`
is a repeatable complete-process improvement over both its immediate parent
and the retained byte-table performance anchor. Rust parity remains unresolved.
The original Mech program, bytecode, input, seven complete hash maps, finite
work prices and 874,999,961 histogram updates are unchanged.

## Complete-process measurements

Each independent session contains ten observations of each of five subjects.
The ten Williams orders balance position and preceding subject; the second
session reverses the order list. All 100 observations remain in the record,
with no excluded full-input warmups or outliers. Runs are serial under the
shared benchmark mutex. Each process verifies its complete output and native
work receipt.

| Subject | Session 1 seconds | × Rust | Session 2 seconds | × Rust |
|---|---:|---:|---:|---:|
| Compact mapper, `d1ae94f684` | **0.583496** | **1.070×** | **0.581508** | **1.048×** |
| Immediate parent, `cfd54ab14d` | 0.594530 | 1.090× | 0.589064 | 1.062× |
| Byte-table anchor, `8946ccbae9` | 0.604018 | 1.107× | 0.603112 | 1.087× |
| Qualified ordinary control, `bdb3c511c` | 0.622439 | 1.141× | 0.623764 | 1.125× |
| Exact upstream Rust | 0.545531 | 1.000× | 0.554612 | 1.000× |

Paired changes use matched observations within each session. They differ from
ratios of subject medians.

| Candidate versus | Session 1 change, 95% interval | Faster pairs | Session 2 change, 95% interval | Faster pairs |
|---|---:|---:|---:|---:|
| Immediate parent | −1.52% [−2.54%, −0.05%] | 8/10 | −1.53% [−3.14%, −0.45%] | 9/10 |
| Byte-table anchor | −3.09% [−4.30%, −1.70%] | 10/10 | −3.20% [−6.08%, −1.19%] | 9/10 |
| Ordinary control | −5.98% [−6.96%, −4.20%] | 10/10 | −6.90% [−7.69%, −5.38%] | 10/10 |
| Rust | +6.48% [+5.47%, +9.66%] | 0/10 | +4.21% [−5.58%, +6.27%] | 3/10 |

The direct anchor comparison avoids crediting a recovery from the selective-field
regression as a new gain. These cohorts establish a combined improvement over
the anchor despite retaining that cleanup in the source ancestry. They do not
prove that the cleanup contributes positively or identify the best interaction.
The second Rust interval includes zero and the first is entirely slower;
repeatable parity and a stable 4.8% gap are not established. Earlier cohorts
are retained separately and are not pooled with these results.

Raw results: [session 1](../full-compact-ascii-map-v1/results.json),
[session 2](../full-compact-ascii-map-v2/results.json),
[plan and subject pins](plan.json), [primary driver](measure.py).

## General compiler transformation

The prepared format has a 16-byte header followed by a 128-byte allocation,
within the original conservative table admission. All missing entries use
`0x80`; all ASCII results, including zero, retain their value.

From the immutable source mapping alone, preparation attempts a low-five-bit
projection to 32 cells and derives the common high-bit domain predicate. A
conflicting projection retains the full 128-entry table. Before selecting a
projected representation, preparation exhaustively compares every one of the
128 ASCII inputs against the full value/missing semantics. This bounded work
fits the existing preparation price. It reads no benchmark input, recognizes
no alphabet or workload name, and creates no additional heap allocation.

Ordinary and joined mappers use the same representation and code-generation
algebra. Each selects a full or projected leaf once per invocation, outside
vector and row traversal. Non-ASCII raw input retains its defensive rejection
and scalar continuation. Source ownership, initialized destination extents,
first-missing boundaries, original error locations, logical body prices and
fallback behavior remain checked. No source-memory promise is strengthened.

The [source-map proof](source-map-equivalence.json) independently checks the
unchanged source table. It is not a claim about input frequencies.

## Actual machine code

The [assembly gate](code-inspection.json) verifies the actual emitted leaves,
their row-loop dominators and all unaffected counting/bridge functions.

| Joined mapping leaf | Vector lookups | Table vectors hoisted before rows | Per-row vector constants | Vector stack reloads |
|---|---:|---:|---:|---:|
| Full fallback | 8 | 8 | 8 | 0 |
| Projected | **2** | **2** | **3** | 0 |

Both joined leaves contain 224 total static instructions. The projected leaf
reduces work on the vector path; extra domain logic in scalar continuation
prevents claiming that the whole leaf is smaller. The ordinary full/projected
leaves contain 160/192 instructions and eight/two lookups. All fourteen
generated functions and nested dispatcher/leaf stack use are admitted.

All seven unrelated counting and preserving-call bridge bodies are byte-identical
to the controls. The root changes only at the qualified ABI-32-to-33 comparison.
The timed executable is 5,501,280 bytes, unchanged in file size; its whole text
is 4,331,020 bytes, 2,048 bytes larger than the immediate parent.

## Profiles, counters and memory

Three completed prearmed captures for each language use the exact timed machine
code. The profiled Mech host has a different file hash because it retains
symbols, but its **entire text section** matches the timed executable. Among
3,748 Mech worker observations, 86.93% fall in generated counting, 5.82% in
storage helpers, 3.34% in active accounting and 1.79% in the generated bridge.
Main-thread observations include the actual projected joined leaf, scanner,
allocation, input and final validation. These are profiler observations, not
elapsed-time or CPU-time phase shares. No new scanner duration is inferred
from them. See [profile analysis](analysis.json).

Twenty separate counter processes are diagnostic observations, outside the
100 primary timing samples.

| Subject | Retired instructions | Cycles | User CPU seconds | System CPU seconds |
|---|---:|---:|---:|---:|
| Compact mapper | 24.262 B | 5.922 B | 1.685 | 0.030 |
| Immediate parent | 24.378 B | 5.875 B | 1.660 | 0.030 |
| Byte-table anchor | 24.389 B | 5.993 B | 1.695 | 0.030 |
| Ordinary control | 24.514 B | 6.066 B | 1.715 | 0.030 |
| Rust | 33.162 B | 7.949 B | 2.350 | 0.030 |

The candidate retires about 116 million fewer instructions than its immediate
parent, but this cohort has slightly higher cycles and CPU. It does not
corroborate a CPU improvement or localize the primary elapsed saving. Matching
actual-path phase/worker measurements are the next diagnostic; earlier byte-table
phases must not be assigned to this new build. Candidate peak RSS medians are
163.04/162.65 MB in the two primary sessions, versus Rust 141.07/141.01 MB.
See [counter receipts](counters/results.json).

## Correctness and retained attempts

Final-source qualification passes **410 native**, **30 line-storage**,
**36 finite-credit** and **one catalog** checks. Three existing manual native
checks remain ignored. Eight focused generated-window checks also pass, and
the final suite includes those tests. Prefix qualification is separate from
the full workload: three measured observations per subject plus one excluded
prefix warmup each are retained.

The first source commit failed to compile because a geometry-block variable
shadowed the new mapping kind. Its correction passed focused tests; the first
full suite then exposed a stale ABI-32 test expectation. The final commit
changes only that assertion to ABI 33, and all scopes were rerun. Both failed
receipts remain. The first assembly parser did not recognize the `tbl.16b`
opcode suffix; `inspect-code-v2.py` reuses the same four completed captures.
The first verifier used an incomplete validation-folder glob; `verify-v2.py`
includes all nine validation receipts. Executed scripts and original reports
remain immutable. Neither analysis correction repeated a native observation.

The [final verification](verification.json) checks **164 terminal owned process
receipts**, all source/input/output/object pins, full updates, finite credit,
seven tasks, profiler text, admission and shutdown. Every owned process is
reaped and its process group is closed; no cleanup signal was required.

The compact mapper is the current qualified candidate. Pure-scalar graph/state
execution and a shared optimization of both long hash loops remain open.
Final UTF-8 validation and chunk administration have smaller measured scope.
