# Bounded scalar choices in the native match finder

**Selected: `m1-matcher-existing-linear`, 63,192 B, every named 81/81 Roc and 63/81 libdeflate win preserved in both full 81-case, 96-block orders.** After SSA cleanup, the compiler selects between existing scalar values without speculating arm arithmetic. The original **2,719-line Mech codec and canonical bytecode are unchanged**.

| Runtime case / order | Mech | Matched Mech control | libdeflate | Paired Mech ÷ C time | Mech time reduction to parity |
| --- | ---: | ---: | ---: | ---: | ---: |
| Random 1 MiB, forward | 22.825000 ms | 23.032000 ms | 20.337771 ms | 1.121954× | 10.87% |
| Random 1 MiB, reverse | 22.819605 ms | 23.034625 ms | 20.357958 ms | 1.121295× | 10.82% |
| Random 4 KiB, forward | 0.108438 ms | 0.108563 ms | 0.076355 ms | 1.432743× | 30.20% |
| Random 4 KiB, reverse | 0.107687 ms | 0.109375 ms | 0.075667 ms | 1.434561× | 30.29% |

Paired 1-MiB time is **0.991409× /0.991367×** the qualified 63,192-B control, **0.86% /0.86% less time**, at unchanged encoder size. Across the eighteen remaining C losses, descriptive equal-case geometric changes are **0.991892× /0.991092×**. Small slowdowns remain included. **No 64th C win or formal confidence claim is added.**

Fresh-process source through final executable linking takes **2.212859 s Mech /2.988437 s Roc /0.481830 s C**, paired **0.739774× Roc /4.585656× C**. The paired build change versus the matched prior producer is **1.001884×**; no compile-time gain is established. Twelve balanced serial orders use equally prebuilt compilers/fixed support and include final executable linking. Parse/frontend/native/link medians are **0.703912 /0.218331 /1.211676 /0.035921 s**; independently computed phase medians do not add exactly. Bootstrap and strip are separate. No builds, tests, counters, sampling, archives or Git work overlaps primary clocks.

Encoder text is **1.095× Roc /1.704× C**. Stripped executables remain **276,072 B Mech /191,912 B Roc /155,752 B C**. Peak stack is **4,736 B**, below the 5,280-B cap. Both improved layouts pass the complete named-win gates; the smaller linear layout is selected because its remaining-loss aggregate and whole-suite tradeoff are better. The sixteen-byte-larger alternate and every slower trial remain available.

The actual main default and explicit alternate reproduce object, complete metadata and bytecode exactly. **20 public normal/checked source replays**, sixteen earlier-source identity replays and the optimized select/scalar/histogram/current-predicate/SSA/increment tests pass. Portable verification checks **16,849,152 runtime observations**, retains 2,574,930 zero samples, recomputes **207 actual counter cases**, seven register-profile arms and fourteen machine layouts, and checks all twelve complete-build orders plus **486 actual stripped-executable outputs**. Fresh sampling separately checks another **200,800 observations**. The full GPU suite is not claimed.

[All retained trials and source reproduction](README.md) · [All 81 elapsed times and parity gaps](PARITY.md) · [Fresh native sampling](PROFILE.md). Rebasable compiler implementation: `a26552db4f1dc44b3892d6d7936de53cdc17b269`. The new flags remain off globally and the selected measured recipe enables the bounded late pass. No new LLVM dependency, source rewrite, generic operation dispatch or shipping native-byte patch is added.

**64 C wins is next; 1× libdeflate across all 81 remains the goal.** A separate follow-up will test proved unsigned min/max ranges after scalar selects; no gain from that unimplemented idea is claimed.

Compiler source: [`a26552db4`](https://github.com/mech-lang/mech/commit/a26552db4f1dc44b3892d6d7936de53cdc17b269). The original 2,719-line Mech codec and canonical bytecode are unchanged. The source uses Cranelift, with no new LLVM dependency. The preceding [histogram checkpoint](../histogram-counter-capacity/README.md) remains reproducible.

The compiler already converts small pure branch arms into native scalar selects. This study bounds that conversion and revisits it after identical SSA argument cleanup. `MECH_COMPACT_PHASE_SELECT_LIMITS=instructions:results` caps the pure instructions moved from either arm and the distinct selected results. The original maximums, whitelist, dominance requirements and trap/effect exclusions remain intact. `MECH_COMPACT_LATE_PHASE_SELECTS` enables the same proof after SSA cleanup. These options are off globally.

The first five variants all slowed the random 1 MiB case, despite branch or spill-count reductions. They remain available. The next trial separates choices between values already computed (`0:1`) from paired-result choices (`1:2`). In particular, selecting existing values avoids speculatively calculating a decrement or increment in the hot loop. Actual elapsed measurements determine selection; instruction counts are diagnostics.

All timings use the Apple M1, macOS 15.6.1, arm64. Discovery uses both 21-case, 96-balanced-block orders with the exact qualified 63,192-byte worker as control. Every required named panel win is checked. A panel is not a complete 81-case qualification. Full qualification requires both 81-case, 96-block orders and all prior named 81 Roc /63 libdeflate wins. Confidence support is separate from point wins. Bootstrap, native diagnostics, tests, builds, archives and Git work run outside primary clocks.

`recipes.json` retains the control and every actually timed candidate. `reproduce.py` compiles the original Mech source with relocated, hash-checked register and machine-layout profiles; normal and checked emission reproduce the complete object, metadata and bytecode. `build_compiler.py` builds the compiler from this checkout. The published source provenance binds the current compiler to 52 frozen Rust inputs and reproduces 16 earlier artifacts with the changed compiler.

The strict native gates check 162 exact output/inflation/alias/resource/cleanup observations, six source-mapped checked errors, twelve injected failures and exact recoveries, and a measured 4,736-byte peak stack under the 5,280-byte cap. Optimized tests cover eight select-filter tests, 79 scalar tests, ten current-predicate tests, two SSA tests, four increment tests and five histogram tests. The histogram family includes 40,725 focused native calls; the common select test includes twelve full-width/nonzero-truth native calls. These overlapping test families are not added together. An initial harness expected two tests for a filter that actually matched eight; all eight passed before the harness count was corrected. This was a harness assertion failure, not a semantic test failure.

The diagnostic counter clones are never used for runtime timing or deployed code. Native-body hashes and address translation bind all 207 actual match-finder counter cases to their production objects. Register profiles derive from all static heads, retaining unvisited zeros before the frequency floor. Machine-layout priorities preserve exact solved flow constraints and label unresolved flow as heuristic. Earlier Huffman and scorer profiles are reused only after native-body and relocation identity checks.

```sh
python3 build_compiler.py /tmp/mech-select-compiler
python3 reproduce.py /tmp/mech-select-compiler/release/compile_profile /tmp/mech-select-replay --role late-existing-linear
python3 verify.py
```

The raw measurements, slower candidates, exact source replays, compiler and test source inputs, native gates and diagnostic derivations are retained in the content-addressed archives. The verifier checks source bindings, public replays, native gates, counters, register-profile derivation and every saved runtime observation, including zero-duration observations. The complete GPU test suite is not claimed.

| Discovery arm | Encoder B | 1 MiB Mech ms, forward /reverse | Paired Mech ÷ C | Required panel wins missing |
| --- | ---: | ---: | ---: | --- |
| select-sqrt | 63,448 | 23.175521 /23.183562 | 1.141173 /1.141926× | prefix-natural-4096 |
| late-paired-linear | 63,256 | 23.431500 /23.430812 | 1.154391 /1.155651× | none |
| late-existing-sqrt | 63,208 | 22.799479 /22.788958 | 1.123072 /1.122651× | none |
| late-paired-sqrt | 63,272 | 23.382416 /23.385958 | 1.151345 /1.152252× | none |
| late-cheap-linear | 63,208 | 23.402479 /23.401104 | 1.150590 /1.152886× | none |
| late-existing-linear | 63,192 | 22.818855 /22.815937 | 1.123394 /1.123159× | none |
| late-cheap-sqrt | 63,208 | 23.362188 /23.379271 | 1.150449 /1.152306× | none |
| early-cheap-linear | 63,400 | 23.981084 /23.976125 | 1.181162 /1.180809× | none |
| combined-cheap-sqrt | 63,400 | 24.028459 /24.024208 | 1.184946 /1.183209× | prefix-natural-4096 |

The first five discovery arms were repaired by the existing-value policy rather than discarded as a whole. Both `late-existing` arms then received full81 qualification. Early unprofiled alternatives and other unmeasured layouts are retained in the native archive without a runtime claim.
