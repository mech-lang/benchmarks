# Prepare joined-map byte tables once

The intended machine-code change is verified, but this isolated byte-table
trial remains **unpromoted**. Neither primary session establishes an elapsed
improvement over its immediate direct-transform parent. Both sessions improve
against the qualified ordinary control; that comparison includes the earlier
private-buffer/direct-transform work. Rust parity remains unproved.

## Complete-process results

All subjects execute serially under the original shared mutex, with seven
workers inside each process. Each session has eight balanced four-subject
orders and eight observations per subject. Session 2 reverses the order list.
Mech includes secured startup through exit. No full-input warmup or outlier
is excluded.

| Session | Byte-table candidate | Direct-transform parent | Ordinary control | Exact Rust #7 |
| --- | ---: | ---: | ---: | ---: |
| [1](../full-joined-byte-table-v1/results.json) | 0.595305 s / 1.071× Rust | 0.593758 s / 1.068× | 0.619501 s / 1.114× | 0.556019 s / 1.000× |
| [2](../full-joined-byte-table-v2/results.json) | 0.585668 s / 0.992× Rust | 0.590431 s / 1.000× | 0.611504 s / 1.036× | 0.590512 s / 1.000× |

| Paired candidate change | Session 1; 95% interval | Session 2; 95% interval |
| --- | ---: | ---: |
| Versus direct-transform parent | +0.49%; [−0.68%, +1.19%] | −0.22%; [−2.72%, +1.07%] |
| Versus ordinary control | −4.76%; [−5.56%, −2.74%] | −4.25%; [−6.29%, −2.99%] |

Every matched pair versus the ordinary control is faster, sixteen of sixteen.
Against the immediate parent, three of eight and five of eight are faster.
The incremental byte-table gain is not established. The second-session Rust
median is substantially slower than the first, and its paired interval versus
the candidate includes zero. The isolated 0.992× ratio does not establish a
repeatable Rust win. Every raw observation is retained.

The separate one-million-base [prefix cohort](../joined-byte-table-timing-v1/results.json)
gives candidate 0.088913 s / 4.563× Rust, parent 0.087416 s / 4.486× and Rust
0.019485 s / 1.000×. Each subject has one excluded prefix warmup and three
measured processes. These observations are not pooled with the full input.

## Change and private contract

Production source is [8946ccbae9](https://github.com/mech-lang/mech/commit/8946ccbae9ef213e52832b3847c7c019a8e112e2),
branch `codex/native-joined-byte-table`. Its immediate parent is
`6cf5877fa9`; the qualified ordinary control remains `bdb3c511c`.

The admitted immutable joined-map table now stores 128 bytes. Values 0..127
are valid outputs, including zero; a high-bit entry denotes a missing key.
The owning host constructs this representation once. Both the generated SIMD
path and its scalar fallback read that same table. The scalar path still
rejects non-ASCII raw keys distinctly from absent ASCII keys.

IR88 / ABI32 separate this private encoding from the parent's u16 table.
Old IR87/ABI31 identities are explicitly rejected. Frame banks, five-argument
copy signature, six immutable geometry words and exact initialization receipt
are unchanged. The original conservative 256-byte table allowance and fixed
4,096-byte metadata envelope remain; the actual table allocation is 128 bytes.
Work policy69, finite prices, limits, source/error boundaries and ownership
checks remain unchanged. No additional readonly, nontrapping, alignment or
movement promise is introduced.

Original Mech source, bytecode, resource image, launch policies, inputs and
protected Rust executable remain unchanged. Every full Mech process verifies
the complete output, seven complete maps, **874,999,961 original physical
updates** and **854,497 original credited batches**. Candidate and immediate
parent each transform 125 million fused bytes. The change applies to arbitrary
eligible immutable ASCII maps; it recognizes no input name, content, alphabet,
benchmark or query. No benchmark dataset timing is replaced.

## Actual assembly gate

[Code inspection](code-inspection.json) runs before both full timing sessions.
It builds the function's actual control-flow graph and dominators from the
retained disassembly, identifying the outer row loop and table-load placement.

| Joined transform/copy function | Parent | Candidate |
| --- | ---: | ---: |
| Raw table vector registers loaded | 16 | 8 |
| Table loads outside and dominating row loop | Yes | Yes |
| Narrowing instructions inside row loop | 16 | **0** |
| Stack-vector reload instructions | 3 | **0** |
| Row-loop vector constant materializations | 8 | 8 |
| Emitted function code | 980 bytes | 800 bytes |
| Stack frame | 160 bytes | 48 bytes |
| Mach-O function span, including alignment | 1,024 bytes | 896 bytes |

The eight constant materializations remain inside the row loop. The mapping
still uses eight swizzles per input vector. This trial therefore removes the
repeated narrowing and related spills without claiming that every setup
operation is now hoisted.

All eight unrelated nonentry functions remain byte-identical to both controls,
including the ordinary mapper and all long counting-loop variants. The main
entry differs from the immediate parent only at qualified ABI-version
instructions. Source plans, visits, aggregate layouts, borrowed layouts and
finite scalar prices are identical. An initial read-only inspection preflight
matched `x20` when searching for `x2`; its retained failure record explains the
exact-register correction. The corrected gate reproduces the parent's known
sixteen narrowing instructions and three reloads. No native execution failed
or was repeated for that analysis correction.

## Correctness, profiles and counters

The final clean source passes **405 native tests**, 30 line-storage tests,
36 finite-credit tests, one catalog test, four focused generated-kernel tests,
seven focused source/error tests and two focused owner tests. Three existing
manual native tests remain ignored. The generated tests cover all ASCII
inputs and outputs, valid zero, every byte-range missing marker, larger
unsigned marker conversion, all relevant short tails and alignments, CRLF/EOF,
inactive copying, invalid extents, source immutability and sentinel-protected
outputs. Every raw non-ASCII byte is tested in scalar and SIMD execution;
failure leaves the initialized-extent receipt unpublished. Original/decoded
artifacts and finite admission/error behavior retain their existing coverage.

The [fresh profile](analysis.json) matches the timed executable's entire
machine-text section. Three captures per subject retain waits and partial
unwinds. Of 3,786 Mech worker observations, 86.16% are in generated counting
loops, 6.10% in active storage helpers, 3.59% in active accounting and 0.77% in
accounting waits. The joined kernel appears in 57 main-thread observations.
These counts are not elapsed-time shares.

Sixteen separate balanced [counter processes](counters/results.json), four per
subject, give:

| Diagnostic median | Candidate | Immediate parent | Ordinary control | Rust |
| --- | ---: | ---: | ---: | ---: |
| Instructions | 24.389 billion | 24.427 billion | 24.519 billion | 33.156 billion |
| Cycles | 5.952 billion | 5.846 billion | 5.938 billion | 7.953 billion |
| User CPU | 1.685 s | 1.655 s | 1.680 s | 2.350 s |
| System CPU | 0.030 s | 0.030 s | 0.030 s | 0.030 s |

Instructions decrease modestly, but summed cycles and CPU do not improve in
this diagnostic. These results cannot promote the candidate over its immediate
parent. The separate [matching phase/per-width cohort](../joined-byte-table-preparation-workers-v1/README.md)
now isolates approximately 2.2 ms less kernel and post-EOF CPU: 0.023698 s
versus 0.025892 s in the kernel, and 0.029920 s versus 0.032114 s after EOF.
Its 37 terminal receipts and 224 full worker intervals are verified. The
source scanner remains near 73 ms. These observations do not replace primary
timings or establish an incremental whole-process win.

The executable is 5,501,280 bytes, versus the parent's 5,501,264 bytes.
Machine text is 4,329,012 versus 4,329,140 bytes. Candidate primary peak RSS
medians are 162.82/163.57 MB, parent 162.75/162.42 MB and Rust
140.44/140.73 MB. No whole-binary or peak-memory improvement is established.

[Verification](verification.json) checks **121 terminal owned-process
receipts**, all 64 full and nine prefix primary samples, exact output/update
counts, unchanged source/resources/limits, actual object boundaries and assembly
gates, whole-text profile equivalence and separate counter observations.
Every native process exits successfully, inherits the original mutex, is
reaped and closes its process group, with no signal or cleanup error.

The next independent compiler change makes borrowed-view field loads
selective; narrowly proved nontrapping home accesses follow as a separate
experiment. Compact shared mapping plans,
maintained scalar graph/tag/SSA optimization, row-cursor simplification and
both long-loop experiments remain queued.
