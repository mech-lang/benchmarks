Compiler source: [Mech #995 at `48a08687f`](https://github.com/mech-lang/mech/commit/48a08687f1e850b098b675262d900fd89b98cdbd). This adds optional private integer spill storage in otherwise unused caller-saved FP registers. The current closest-target recipe remains [`shared-linear4096`](../mechdeflate-prefetch-bases-v1); its object, full metadata and canonical bytecode reproduce exactly from this source. **FP2 is a qualified alternative**, preserving every named **81/81 Roc and 63/81 libdeflate win** in both full orders with 81 cases and 96 blocks per case. No 64th C win is added.

| Case | Matched qualified control | FP2 alternative | Paired change |
|---|---:|---:|---:|
| Periodic 1 MiB |10.508–10.512 ms|10.392–10.395 ms|1.10–1.13% less time|
| Repeated 1 MiB |12.316 ms|12.204–12.206 ms|0.86–0.92% less time|
| Random 1 MiB |20.953–20.990 ms|20.995–21.053 ms|0.26–0.35% more time|

The full-suite geometric-mean point estimate is 0.99704×/0.99723× control. Small slowdowns with all named wins preserved are allowed. FP2 is 1.0322–1.0353× C on random 1 MiB; the previous closest-target selection remains available at 1.0314–1.0326× C in its published cohort. Formal confidence is not claimed.

The pass admits only Apple AArch64 leaf bodies with no calls, safepoints, stack maps or uncertain debug locations. It excludes source-addressable and overlapping/multiword spill storage, then uses only FP registers absent from every original operand, edit and implicit clobber. One register holds each selected cell for the complete function, with every read and write rewritten as an exact 64-bit transfer. No floating-point arithmetic, native allocation, runtime dispatch or weaker admission is introduced. The original frame stays allocated. The register-allocation checker runs again in checked mode. Compiler defaults remain unchanged. The original idiomatic 2,719-line codec and canonical bytecode are unchanged; no LLVM dependency is added.

The three final layouts each preserve **63,720 B encoder text**, **3,200 B lookup data**, **17,728 B whole object const section**, **4,832 B measured stack** and a **210,024 B stripped executable**. The largest limit replaces all 21 eligible private cells: random 1 MiB SP load instructions fall 11,204,255→210, yet elapsed time worsens. Memory-work reduction alone is insufficient. Three limits using UMOV and the same limits using scalar FMOV retain both six-case screens and all raw evidence; only FP2 has full qualification across all 81 cases.

| Fresh source through final executable link | Median | Stripped executable |
|---|---:|---:|
| Current Mech control |2.19244 s|210,024 B|
| Mech FP2 |2.19235 s|210,024 B|
| Roc |2.98473 s|191,912 B|
| libdeflate C |0.48306 s|155,752 B|

Eight balanced serial orders on Apple M1 / macOS 15.6.1/arm64 use equally prebuilt compilers and fixed support. Every codec is compiled fresh through final linking; compiler construction and stripping are separate. FP2 is 1.0003× control, 0.7346× Roc and4.5443× C; compile time is unchanged. Parsing/frontend/native medians are0.6787/0.2231/1.2173 s. No heavy work overlaps primary clocks.

Each of the two private native probe executions makes 256,800 actual native calls. The public source build repeats exactly the scalar-FMOV corpus, including its 100 recorded function bodies. Two optimization levels, forwarding enabled/disabled, five integer/FP/call-pressure shapes, five cache limits, 256 dirty-bit seeds, five loop counts, exact aliases, guarded invalid pointers and a callback destroying caller-saved FP registers are covered. Nine new codec images each pass 162 success observations, six named errors and 12 recovery pairs. All normal/checked/inspection artifacts agree. Formatting, warning policy and unsafe-boundary checks pass. Ten public artifact replays, 32 timed complete builds and 324 actual stripped-executable outputs are checked. The full GPU suite and CI is not claimed.

```sh
python3 reproduce.py --mech-root /path/to/mech --output /tmp/spill-replay
python3 reproduce.py --mech-root /path/to/mech --output /tmp/spill-checked --checked
python3 probe.py --mech-root /path/to/mech --output /tmp/spill-native-probe
python3 verify.py
```

Reproduction builds the compiler from source, then checks the unchanged qualified control and FP2. `--role fp8` and `--role fp24` reproduce the screened alternatives; `--compiler` reuses a built compiler. Every profile is named by content hash. Raw observations, both source overlays, actual counters, partials, native checks, public replays and standalone streams are archived; build caches are excluded. The failed public feature-selection attempt is retained and corrected in the public script.

The next repair is concrete: FP2 caches cells at SP 240 and SP 200. Removing SP 200 splits an LDP of SP 192/200 executed 1,044,385 times on random 1 MiB, adding exactly 1,044,385 executed instructions. Test the existing one-cell option before changing the compiler: it keeps the scalar SP 240 cache and leaves that pair intact. No gain is assumed. See [next-experiments.json](next-experiments.json).
