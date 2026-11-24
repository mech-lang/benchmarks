[Mech #995 at `91a7702d3`](https://github.com/mech-lang/mech/commit/91a7702d3c280383ac8b901748987a59474c01e2) is the compiler-source basis. The selected `pack-sqrt` combines native narrow-field packing with the previously qualified word/byte/Boolean recipe. Both full 81-case / 96-block orders preserve every named **81 Roc / 63 libdeflate win**. No 64th C win yet.

| Case | Previous selected recipe | New selected recipe | Paired reduction in time |
|---|---:|---:|---:|
| Random 1 MiB | 21.115–21.116 ms | 21.012–21.024 ms | 0.40–0.57% |
| Random 256 KiB | 5.347–5.353 ms | 5.320–5.329 ms | 0.38–0.65% |
| Random 64 KiB | 1.277–1.278 ms | 1.272–1.273 ms | 0.40–0.46% |

Random 1 MiB is **1.0346–1.0352× libdeflate time**; C takes 20.331–20.334 ms. Another **3.34–3.40% of Mech time** must be removed for parity. Periodic/repeated 1 MiB are approximately flat. Random4K is mixed between orders (about 1.34–1.35× C), with every named win intact. Tiny slowdowns without losses are allowed. Formal confidence is not claimed.

Two independent opt-ins are supplied. `MECH_ARM64_FOLD_SHIFTED_EXTENSIONS=1` skips an unsigned extension when a fixed word shift discards every physical bit above the narrow input. `MECH_ARM64_PACK_NARROW_HALVES=1` packs two unsigned half-fields using native BFI, with explicit tied-input register allocation and correct shared uses. Both scalar32- and 64-bit packs are supported; original producers, guards and memory order remain maintained. Existing flag-off artifacts reproduce exactly. Fresh declared nine-case matcher/scorer profiles apply equally to every input. The original idiomatic 2,719-line source and canonical bytecode remain unchanged; compilation uses Cranelift without an LLVM dependency.

The selected matcher executes **166,080,651 instructions** on random1M versus **167,147,120** previously. All **2,097,082 UXTH executions** disappear, replaced by 1,048,541 BFI operations and additional register copies. Both **2,097,082 prefetches** remain. The shift-only alternative has the same matcher instruction count but retains one halfword mask per iteration; elapsed screens favor the insert candidate. The scorer adds 2,649 register copies on random1M; its profile is refreshed rather than reusing stale virtual-register metadata.

This is a runtime gain with a size tradeoff: encoder text grows **16 B: 63,624 → 63,640 B**. Lookup data remains **3,200 B**, measured stack **4,832 B**, and stripped executable **210,024 B**. The 63,624 B shift-only variant and exactly equivalent both-options raw image remain reproducible.

| Fresh source through final executable link | Median | Stripped executable |
|---|---:|---:|
| Mech previous selected | 2.1833 s | 210,024 B |
| Mech new selected | 2.1876 s | 210,024 B |
| Roc | 2.9755 s | 191,912 B |
| libdeflate C | 0.4805 s | 155,752 B |

Eight balanced serial orders on **Apple M1 / macOS15.6.1 / arm64** prebuild compilers and identical fixed support equally. Every codec is compiled fresh through final executable linking; compiler construction and stripping are separate. Paired build time is **0.736× Roc**, **4.543× C** and **1.0028× control**, roughly unchanged. Parsing takes about 0.677 s and native codegen about 1.211 s. No heavy jobs overlap primary clocks.

Eight native JIT test executions check **13,328,640 actual native calls** across both optimizer levels and all four option combinations. Dirty upper bits, signed and unsigned users, shared values, joined narrow inputs, fixed/modulo/variable counts, constants, guarded pointers, and aliased loads with an intervening store are covered. Excluded raw, variable and identity-shift bodies stay exact. Both insert geometries match an independent assembler oracle. Six new codec images each pass 162 success observations, six named errors and 12 recovery pairs; the disabled control is byte-exact. The public source build/native-probe workflows repeat the same corpus, all eight roles replay in normal/checked modes, and 324 actual timed stripped-image executions independently inflate correctly. The verifier recomputes the full 1,965,312 runtime observations, 32 timed builds and 18 public artifact replays. Full GPU/CI is not claimed.

```sh
python3 reproduce.py --mech-root /path/to/mech --output /tmp/pack-replay
python3 reproduce.py --mech-root /path/to/mech --output /tmp/pack-checked --checked
python3 probe.py --mech-root /path/to/mech --output /tmp/pack-native-probe
python3 verify.py
```

`--role pack-sqrt` selects only the new recipe; `--compiler` reuses an existing compiler. The default replay builds the compiler from source and reproduces the control plus selected recipe. Profiles are named by content hash. Raw logs, counters, source bindings, probes, exact replays and standalone streams are content-addressed in the archive; build caches are excluded. `next-experiments.json` records the two biased prefetch bases that are still recomputed on every loop visit, possible scaling/constant improvements and larger setup losses.
