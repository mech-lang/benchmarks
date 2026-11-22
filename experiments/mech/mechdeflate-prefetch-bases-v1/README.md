[Mech #995 at `442345f19`](https://github.com/mech-lang/mech/commit/442345f1916fe2a752a32491420f95da0c34cdd6) is the compiler-source basis. Selected `shared-linear4096` preserves every named **81 Roc / 63 libdeflate win** in both full 81-case / 96-block orders. No 64th C win yet.

| Case | Previous selected recipe | New selected recipe | Paired reduction in time |
|---|---:|---:|---:|
| Random 1 MiB | 21.083–21.115 ms | 20.986–20.988 ms | 0.47–0.62% |
| Random 256 KiB | 5.353–5.354 ms | 5.327–5.334 ms | 0.52–0.53% |
| Random 64 KiB | 1.271–1.278 ms | 1.269–1.270 ms | 0.44–0.86% |
| Natural 4 KiB | 0.386–0.388 ms | 0.382–0.384 ms | 0.83–0.94% |

Random 1 MiB is **1.0314–1.0326× libdeflate time**, with C at 20.341–20.346 ms. Another **3.04–3.16% of Mech time** must be removed for parity. Random 4 KiB also improves in both full orders. Periodic/repeated 1 MiB are roughly flat. Distribution-change 16 KiB is about 1% slower; it loses no named win. Small slowdowns without lost wins are allowed. Formal confidence is not claimed.

`MECH_COMPACT_HOIST_PREFETCH_BASES=1` enables a per-function late pass on private vector phases. Cranelift's egraph recreates constant additions near uses, undoing earlier sharing. The new pass runs afterward, reusing a dominating identical I64 sum or placing one pure wrapping addition after its base definition. It preserves all hint addresses, write intent, guards, memory effects and shared uses. The search is bounded, and unsupported shapes remain unchanged. Compiler defaults stay unchanged; the disabled control reproduces the published object, metadata and bytecode exactly. The original idiomatic 2,719-line source and canonical bytecode remain unchanged; compilation uses Cranelift without an LLVM dependency.

Actual random1M matcher instructions fall **166,080,651 → 164,668,154**. All **2,097,082 prefetches** remain. Stack loads rise **10,112,887 → 11,204,255**, so the saved arithmetic has a register-pressure tradeoff. Uniform nine-case linear weights repair the first square-root profile's much larger spill cost. The smaller linear-65536 alternative remains reproducible; it passes both six-case screens but has a narrower natural4K margin, and has no full81 qualification. Earlier sharing produced an exactly identical final image; its source overlay and failed-placement evidence are retained without rerunning clocks for identical code.

Encoder text grows **80 B: 63,640 → 63,720 B**. The immutable lookup table remains **3,200 B**; the entire object `__TEXT,__const` section is separately measured at **17,728 B**, unchanged. Measured stack remains **4,832 B**, within the 5,280 B cap. The stripped executable stays **210,024 B**.

| Fresh source through final executable link | Median | Stripped executable |
|---|---:|---:|
| Mech previous selected | 2.2023 s | 210,024 B |
| Mech new selected | 2.2150 s | 210,024 B |
| Roc | 3.0039 s | 191,912 B |
| libdeflate C | 0.4930 s | 155,752 B |

Eight balanced serial orders on **Apple M1 / macOS15.6.1 / arm64** prebuild compilers and identical fixed support equally. Every codec is compiled fresh through final executable linking; compiler construction and stripping are separate. Paired build time is **0.731× Roc**, **4.521× C** and **0.9985× control**, roughly unchanged. Parsing takes 0.678 s and native codegen 1.220 s. No heavy jobs overlap primary clocks.

One native JIT test execution checks **202,860 actual native calls** across both optimization levels with the register checker, seven placements, seven signed bias boundaries, 1,032 accepted indices and three rejected inputs. Dirty wrapping addresses, sibling/later definitions, guarded null pointers, shared memory uses and neighboring cells are covered. Seven new codec images each pass 162 success observations, six named errors and 12 recovery pairs. Normal/checked/inspection emissions agree. Formatting, warning policy and unsafe-boundary checks pass; pinned upstream lint attributes were re-audited unchanged. The public source build/native probe repeats the same corpus. All eight roles replay in normal and checked modes, and 324 actual timed standalone executions independently inflate correctly. The verifier recomputes 1,965,312 runtime observations, 32 timed builds and 18 public artifact replays. Full GPU/CI is not claimed.

```sh
python3 reproduce.py --mech-root /path/to/mech --output /tmp/prefetch-replay
python3 reproduce.py --mech-root /path/to/mech --output /tmp/prefetch-checked --checked
python3 probe.py --mech-root /path/to/mech --output /tmp/prefetch-native-probe
python3 verify.py
```

`--role shared-linear4096` selects only the new recipe; `--compiler` reuses a built compiler. Default reproduction builds the compiler from source and checks the control plus selected recipe. All profiles are named by content hash. Raw observations, source bindings, native checks, counters, partials, public replays and standalone streams are archived; build caches are excluded. `next-experiments.json` and `spill-census.json` identify a broader target: repeated stack loads while 22 caller-saved FP registers are unused. Mapping these cells to actual allocator spill edits is required before experimenting with private register storage; no such rewrite or gain is claimed yet.
