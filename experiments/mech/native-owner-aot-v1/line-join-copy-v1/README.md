# Validated captured-line copying

Production candidate `630921324a65c385cf63e871d3241dbb0847b8d6` improves the empty-separator selected join over captured lines. It copies constructor-validated UTF-8 spans into the already admitted output allocation, checking capacity once per physical chunk rather than repeating String capacity and UTF-8 boundary checks per line. Complete chunks reuse their exact cached payload size; partial edge chunks retain checked row geometry. The unsafe copy has a local lifetime/capacity proof, and the new String length is published only after all bytes are initialized.

The original source predicates, LF and CRLF behavior, unterminated final lines, Unicode, selected coordinates, incremental chunk retirement, work charges and memory limits remain. Other separators keep the original append path. No benchmark name, header string, line length or input alphabet selects this optimization. It neither starts counting before EOF nor replaces any map operation. The Mech program, bytecode, resource image, descriptor and **entire generated guest object** are byte-for-byte identical to parent `91f725adc16b1ba349d77cc898e6e24de4a79bf6`. IR81, ABI29 and work policy68 remain unchanged.

## Complete-process timings

Each session contains all six balanced orders of candidate, parent and exact upstream Rust, with six observations per executable. Session two reverses the order list. All observations include startup and secured shutdown. The input contains 125 million selected bases; all seven complete maps and **874,999,961 original Mech updates** remain. No full-input warmup or outlier is excluded. Benchmark subjects run serially under the unchanged shared lock; seven workers execute inside each subject.

| Session | Parent Mech, s | Candidate Mech, s | Rust, s | Candidate / Rust |
| --- | ---: | ---: | ---: | ---: |
| First | 0.6756 | 0.6531 | 0.5535 | 1.180× |
| Repeat | 0.6673 | 0.6574 | 0.5522 | 1.191× |

The candidate improves five of six matched pairs in the first session and four of six in the repeat. Median paired changes are −3.67% (95% bootstrap interval −5.02% to −0.15%) and −2.12% (−5.72% to +1.64%). The repeat includes zero: retain the candidate and parent independently, and treat the complete-process gain as **provisional**. Rust parity remains unachieved. The separate one-million-base prefix cohort has one excluded warmup plus three measured processes per subject and is not pooled with these sessions.

## Direct copy-phase comparison

Diagnostic commit `1c7da235f04fe9cde20fc9dcc28d490be4c7f6a3` adds the identical phase clocks used by the retained parent diagnostic. Both diagnostic hosts contain the same guest object and probe code. Six fresh full-input observations per host run in the predeclared balanced order after candidate prefix qualification. These executions supply **zero primary benchmark samples**.

| Main-thread CPU span or milestone | Parent, s | Candidate, s |
| --- | ---: | ---: |
| Source scanner | 0.073218 | 0.072805 |
| Selected join copying | 0.026553 | 0.020671 |
| Normalization kernel | 0.013024 | 0.013028 |
| Worker launch begins, from main entry | 0.192999 | 0.186544 |

The isolated copy span falls about **5.9 ms**, and main-thread CPU before launch falls about **6.5 ms**. The scanner and normalization loop are essentially unchanged. This supports a concrete preparation saving, but does **not** causally establish the entire 10–23 ms difference between primary elapsed medians. These are CPU intervals in instrumented hosts, not a decomposition of the elapsed-time gap. Selected-join totals include the copying subspan; capture includes scanning and borrowing, so nested phase totals must not be added.

The preceding [preparation breakdown](../preparation-phase-v1/README.md) identifies borrowing at about 1 ms, source scanning at about 73 ms, and a still-separate normalization pass around 13 ms. This candidate optimizes copying only. Join/map composition, bounded local worker reservations and pipelining of the long ordinary-hash workers remain unimplemented next experiments.

## Exact-code profiles, counters and size

The unstripped profile executable matches **every byte of the primary executable's 4,310,520-byte `.text` section**, SHA-256 `7500bd8d628cc5d7119ae786fe48a3ccbd401077aff6e31db035b204b892f91e`. Three pre-armed owned-process captures per language retain the sampled PID, original outputs, all-thread stacks and immutable source/binary pins. No debugger, pause or environment injection is used; profiling overhead is included in these diagnostics and excluded from primary timing claims.

Across all Mech worker observations, 73.93% are in generated counting loops, 18.33% in active work accounting, 0.87% in accounting waits and 3.75% in storage helpers. Most accounting observations occur during loop refill. These proportions describe sampled locations, not recoverable percentages of elapsed time. The [per-width study](../worker-completion-v1/README.md) separately establishes widths 12 and 18 as the long ordinary-hash tasks; aggregate instruction savings in cached widths do not establish an equally shorter critical path.

Nine separate counter runs retain the exact timed files and original output/update checks. Their medians are diagnostic, rather than replacements for complete-process primary medians:

| Counter | Parent Mech | Candidate Mech | Rust |
| --- | ---: | ---: | ---: |
| Instructions, billions | 25.252 | 25.106 | 33.162 |
| Summed cycles, billions | 7.027 | 6.804 | 7.953 |
| User CPU, s | 2.01 | 1.94 | 2.35 |
| System CPU, s | 0.04 | 0.04 | 0.03 |

Primary median peak RSS is 161.80/161.23 MB for the candidate, 162.14/161.75 MB for the parent and 140.44/140.74 MB for Rust across the two sessions. These small RSS differences do not establish a memory improvement. The candidate file is **5,484,672 bytes**, 16,512 bytes larger than the parent; executable instruction bytes grow by 2,176. No new output allocation or renewed source allowance is introduced.

## Qualification and retained evidence

The clean production revision passes 26 engine line-storage tests, 29 focused prefix checks, all 392 native checks and the catalog check; three existing manual native tests remain ignored. New coverage checks every UTF-8 fragment split and contiguous selection for representative empty, CRLF, repeated-CR, multibyte and combining-character inputs, including pre-existing output prefixes, short capacity, unchanged allocation capacity, retirement and unchanged producer work.

`verify.py` audits 81 terminal native process receipts for the production study, including all primary timings, exact-code profiles and counter diagnostics. One initial engine run succeeded while unrelated formatter whitespace remained outside the commit. Its source snapshots are retained and it is excluded from immutable-revision qualification; the clean rerun passes all 26 cases. `verify-phase.py` checks another 14 receipts for the separate diagnostic build, prefix qualification and 12 full captures. Every owned process exits normally, is reaped and has a closed process group, with no signals or cleanup errors. Canonical benchmark data is unchanged.

Primary binary SHA-256: `e7d5b3f2c4363128a0cd8a4139c04928e5f884c88a9c5663d60382af3bedad73`. Unchanged guest object: `7b1fa85e74cc23a88ce5d9937ad68c7bf003fe5038b4da4e9039171cee3210ea`. Plans, drivers, source snapshots, raw output, complete process receipts, phase records and independent verifications accompany this report.
