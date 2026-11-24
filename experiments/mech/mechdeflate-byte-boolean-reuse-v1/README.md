[Mech #995 at `5159c29f3`](https://github.com/mech-lang/mech/commit/5159c29f3ec1d1a0ff7272095d2cfa23b09cc85d) is the compiler-source basis. The selected `boolean-sqrt` reuses fully clean byte Boolean definitions and combines them with the previously qualified word/byte recipe. Both full 81-case / 96-block orders preserve every named **81 Roc / 63 libdeflate win**. No 64th C win yet.

| Case | Previous selected recipe | New selected recipe | Paired reduction in time |
|---|---:|---:|---:|
| Random 1 MiB | 21.239–21.252 ms | 21.170–21.184 ms | 0.31–0.35% |
| Distribution-change 16 KiB | 0.574–0.578 ms | 0.569–0.574 ms | 1.03–1.14% |
| Biased dynamic 128 B | 15.959–16.500 us | 15.792–16.209 us | 1.32–1.88% |

Random 1 MiB is **1.0404–1.0407× libdeflate time**; C takes 20.365–20.368 ms. Another **3.88–3.91% of Mech time** must be removed for parity. Periodic/repeated 1 MiB are approximately flat against the immediately previous selected recipe. Random4K is mixed between orders (about 1.34–1.38× C); every named win holds. The earlier broad gains are recorded in the previous word-shift packet.

The independent opt-in `MECH_ARM64_REUSE_I8_BOOLEAN_DEFINITIONS=1` proves full-register 0/1 values through scalar integer comparisons, exact 0/1 constants and byte AND/OR/XOR. The proof has fixed depth/node budgets and declines arbitrary narrow inputs, unknown joins, reductions and other producers. Existing load/compare/all modes and flag-off images stay exact. This removes all **1,048,545 remaining UXTB executions** from the random1M matcher; total matcher instructions fall from **168,197,657 to 167,147,120**. Both **2,097,082 prefetches** remain. Declared fresh nine-case allocation/layout profiles apply equally to all inputs. The original idiomatic 2,719-line source and canonical bytecode are unchanged; compilation uses Cranelift without an LLVM dependency.

Encoder text falls **368 B: 63,992 → 63,624 B**. Lookup data remains 3,200 B. Measured stack rises **4,736 → 4,832 B**, within the 5,280 B cap. The stripped executable remains 210,024 B.

| Fresh source through final executable link | Median | Stripped executable |
|---|---:|---:|
| Mech previous selected | 2.1811 s | 210,024 B |
| Mech new selected | 2.1815 s | 210,024 B |
| Roc | 2.9888 s | 191,912 B |
| libdeflate C | 0.4815 s | 155,752 B |

Eight balanced serial orders on **Apple M1 / macOS15.6.1 / arm64** prebuild compilers and identical fixed support equally. Every codec is compiled fresh through final executable linking; compiler construction and stripping are separate. Paired build time is **0.730× Roc**, **4.528× C** and **0.9990× control**, effectively unchanged. Native codegen takes about 1.207 s and parsing about 0.679 s. No heavy jobs overlap primary clocks.

Eight native JIT test executions check **4,177,920 actual native calls** across both optimization levels, ordinary/combined comparisons, all ten integer conditions and four mixed-width pairs. Dirty high bits, shared signed/unsigned/narrow users, aliases, guarded pointers, signed loads, unknown joins and both proof budgets are covered. The 320 excluded parameter/over-budget bodies stay exact; 1,360 changed fixture bodies shrink by 4 or 8 B. Five new codec images each pass 162 success observations, six named errors and 12 recovery pairs. The previous control is byte-exact. Public source bootstrap and native-probe rebuilds pass, all six roles replay in normal/checked modes, and all 324 actual timed stripped-image executions independently inflate correctly. The verifier recomputes the full runtime observations and 32 timed builds. Full GPU/CI and formal confidence are not claimed.

```sh
python3 reproduce.py --mech-root /path/to/mech --output /tmp/boolean-replay
python3 reproduce.py --mech-root /path/to/mech --output /tmp/boolean-checked --checked
python3 probe.py --mech-root /path/to/mech --output /tmp/boolean-native-probe
python3 verify.py
```

`--role boolean-sqrt` selects only the new recipe; `--compiler` reuses an existing compiler. The default source replay builds the compiler and reproduces `control` plus `boolean-sqrt`. The focus allocation and raw intermediates remain reproducible; its periodic slowdown is recorded rather than discarded. Profiles are named by content hash. The archive includes raw trials, independent standalone streams, counters, probe bodies, source bindings and exact public replays; build caches are excluded. `next-experiments.json` traces the remaining halfword masks to the actual packed-cache operation and records the next proof and broader setup targets.
