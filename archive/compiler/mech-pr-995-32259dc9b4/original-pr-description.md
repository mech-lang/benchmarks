# Original Mech PR #995 description

Preserved before benchmark relocation. Measurements and source references below are historical and retain their original qualifications.

AArch64 lowering repeated zero extensions after native operations had already cleared the upper bits. Reusing those definitions removes hot scorer/matcher work; actual-count register weights and machine layout recover the earlier natural4KiB partial loss.

**Selected: `m1-native-zero-extensions`, every named 81/81 Roc and 63/81 libdeflate win retained in both complete 81-case, 96-block orders.** The compiler reuses already zero-extended ARM64 I32 arithmetic and I8 load definitions. Actual-count matcher weights and machine layouts repair the earlier word-only natural4KiB loss. The original 2,719-line Mech source and canonical bytecode are unchanged.

Encoder text is **63,832 B**, 32 B above the prior default; readonly data remains **3,200 B**, the stripped executable **210,024 B**, and stack **4,736 B**. The separately full-qualified **63,784-B** comparison alternative is retained with a 210,024-B executable and 4,864-B stack. The executable is **1.094× Roc /1.348× libdeflate**; selected encoder text is **1.106× Roc /1.721× C**.

| Case / order | Mech ms | Matched Mech control ms | libdeflate ms | Paired Mech/C | Mech reduction to parity |
|---|---:|---:|---:|---:|---:|
| prefix-random-1048576, forward | 22.274187 | 22.451874 | 20.353396 | 1.095205× | 8.69% |
| prefix-random-4096, forward | 0.103813 | 0.105875 | 0.075584 | 1.381515× | 27.62% |
| prefix-natural-4096, forward | 0.387833 | 0.390646 | 0.392188 | 0.988990× | 0.00% |
| prefix-random-1048576, reverse | 22.329896 | 22.495188 | 20.383605 | 1.099229× | 9.03% |
| prefix-random-4096, reverse | 0.103708 | 0.106770 | 0.076500 | 1.370895× | 27.05% |
| prefix-natural-4096, reverse | 0.386708 | 0.388917 | 0.392292 | 0.992752× | 0.00% |

Across the eighteen remaining C losses, descriptive equal-case geometric time changes versus the matched control are **0.990970× /0.989859×**, about **0.90% /1.01% less time**. Small slowdowns remain included, including distribution change; every required peer win holds. **No 64th win or formal confidence claim is added.**

Latest matched fresh-process original-source-through-final-executable-link builds take **2.185589 s Mech /2.990179 s Roc /0.483009 s libdeflate**, paired **0.732022× Roc /4.526886× C**. Parser/frontend/native/link medians are **0.679448 /0.223067 /1.208653 /0.035343 s**; independent medians do not add exactly. Twelve balanced serial orders use equally prebuilt compilers/support; bootstrap and strip are separate. The parser repairs recover the incoming regression: the matched regressed compiler takes 2.647433 s, versus 2.205278 s for the prior qualified compiler. Selected paired time is **0.825019× the regressed compiler /0.991579× the prior compiler**.

**36 public normal/checked source replays and both actual main/default recipes reproduce the entire object, metadata and bytecode exactly.** Four test modes each execute **48,960 byte-definition and 14,144 arithmetic native differential calls**, plus 79 maintained scalar tests. All eighteen alternatives pass 162 output/alias/resource observations, six checked failures and twelve injected failure/recovery pairs. All 486 timed executable deployments pass independent inflation. The full GPU suite is not claimed.

Native lowering and runtime-measurement source: `e112b5dcd5e01c22938aaf20dad49fad3d442a1e`, bound to all 73 frozen producer inputs. The latest integrated compiler is `be392dedfe0e8439bf632882e4bb302b92f4dbcc`; its standard builders reproduce the qualified images exactly. New controls are off globally and the named M1 recipe enables `add`/`load`. No new LLVM dependency, operation interpreter or weaker admission is introduced.

[Source recipes and every retained alternative](https://github.com/mech-lang/mech/blob/8642e081e4dd7d0b5e712cbc1a04bb87038b148c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/arm64-byte-extensions/README.md) · [All measured timings](https://github.com/mech-lang/mech/blob/8642e081e4dd7d0b5e712cbc1a04bb87038b148c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/arm64-byte-extensions/PARITY.md) · [Portable verifier](https://github.com/mech-lang/mech/blob/8642e081e4dd7d0b5e712cbc1a04bb87038b148c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/arm64-byte-extensions/verify.py) · [Verification totals](https://github.com/mech-lang/mech/blob/8642e081e4dd7d0b5e712cbc1a04bb87038b148c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/arm64-byte-extensions/verification.json).

**64 libdeflate wins is next; 1× libdeflate across all 81 remains the goal.**


**Current integrated source and evidence are pushed at `32259dc9b`.** The incoming ordered-list/subtitle lookahead exceeded the original parser fuel limit; checking the list prefix first restores the unchanged codec to **3,967,302 steps under the unchanged 4,000,000-step default**. Restoring completed-node reuse and keeping cached lexical scanner phases intact repairs the compilation slowdown. **586 parser tests pass**, including cached/uncached identity, Unicode scanner state, logical-work and finite-limit comparisons.

**Six actual standard source replays, four checked source replays and two linked default-executable builds pass.** Both source generations reproduce object, complete metadata and bytecode exactly. The portable verifier recomputes **24 complete-build orders and 972 actual stripped-executable outputs**, with independent inflation and retained initial failures and all eight parser alternatives. The original runtime qualification remains attached to the identical generated images; the score remains **81 Roc /63 libdeflate**, with 64 next.

[Parser source, timing table and replay commands](https://github.com/mech-lang/mech/blob/32259dc9b45d64aabd5e1ee602165e27f168a510/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/parser-cache-repair/README.md) · [Complete measured build data](https://github.com/mech-lang/mech/blob/32259dc9b45d64aabd5e1ee602165e27f168a510/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/parser-cache-repair/summary.json) · [Portable verification totals](https://github.com/mech-lang/mech/blob/32259dc9b45d64aabd5e1ee602165e27f168a510/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/parser-cache-repair/verification.json). Historical native runtime/source records below remain bound to their measured compiler.

Portable record and ordinary verification both pass: **8,709,120 runtime observations, 1,167,881 retained zero durations, 243 actual counter cases, 22 runtime orders, 12 build orders and 486 deployed outputs**. All eighteen alternatives and their slower/failed trials remain archived. The earlier word-only partial is retained in [its evidence](https://github.com/mech-lang/mech/blob/8642e081e4dd7d0b5e712cbc1a04bb87038b148c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/arm64-word-extensions/README.md).
