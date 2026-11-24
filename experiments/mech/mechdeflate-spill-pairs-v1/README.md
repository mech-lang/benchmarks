Compiler source: [Mech #995 at `269922ab8`](https://github.com/mech-lang/mech/commit/269922ab8023547874fb72f31be4ceff9187f6e7). **Both recipes retain every named 81/81 Roc and 63/81 libdeflate win in both full 81-case, 96-block orders.** The selected recipe is `keep-pairs2`; `keep-pairs65536` is the smallest qualified alternative. No 64th C win is established.

The previous two-cell cache split a hot LDP of two integer spill words. The new opt-in mode retains adjacent paired reloads and mirrors the affected private cell in memory and its unused caller-saved FP register. Separate reloads use the register. Every original write updates both copies. Register copies are placed before runs of stores, so the stores can remain paired too. One-cell and old two-cell recipes reproduce exactly with the new option off. The original idiomatic 2,719-line codec and canonical bytecode are unchanged. No LLVM dependency, runtime dispatch, per-operation allocation or weaker admission is introduced. Compiler defaults remain unchanged.

| Full-suite result | Standard | Compact |
|---|---:|---:|
| Roc / libdeflate wins, both orders |81/81 · 63/81|81/81 · 63/81|
| Encoder text |63,720 B|63,688 B|
| Random 1 MiB |20.972–20.984 ms|21.006–21.010 ms|
| Random 1 MiB / C |1.0312–1.0315×|1.0323–1.0330×|
| Periodic 1 MiB time reduction |1.08–1.16%|1.10%|
| Repeated 1 MiB time reduction |0.91%|0.85–0.99%|
| Distribution-change 16 KiB |roughly flat|1.40–1.77% less time|

Full-suite geometric-mean point estimates are **0.99588× / 0.99593× control** for the standard variant and **0.99680× / 0.99641×** for compact. Small slowdowns with no named losses are allowed. Compact natural 4 KiB retains its win at 0.97690× / 0.99518× C. These are point estimates, without a formal confidence claim.

Lookup data stays **3,200 B**; the entire object const section is **17,728 B**. Measured stack remains **4,832 B**, below the 5,280 B cap. Both stripped executables remain **210,024 B**. The one-cell trial is retained with both six-case screens, actual counters, matched complete builds and 324 checked standalone outputs; it is not separately full-qualified.

| Fresh source through final executable link | Median |
|---|---:|
| Mech control |2.19337 s|
| Mech standard |2.19261 s|
| Mech compact |2.19265 s|
| Roc |2.98966 s|
| libdeflate C |0.48147 s|

Ten balanced serial orders on Apple M1 / macOS 15.6.1 / arm64 use equally prebuilt compilers and fixed support. Each original codec source is compiled fresh through final executable linking. Compiler construction and stripping are separate. No heavy jobs overlap primary clocks.

One private native test execution checks **513,600 actual calls**, with both cache modes, two optimization levels, forwarding on/off, five pressure/call shapes, five cache limits, 256 dirty-bit seeds, five loop counts, exact aliases and invalid guards. The public source probe repeats the same 200 recorded function bodies and corpus exactly. Allocation checking runs after the transformation. Four new codec images each pass 162 success observations, six named errors and 12 recovery pairs. Normal, checked and inspection emissions agree. Formatting, warning-policy and unsafe-boundary checks pass. Both earlier qualified choices and the one-cell trial reproduce exactly from the current source. Full GPU/CI is not claimed.

```sh
python3 reproduce.py --mech-root /path/to/mech --output /tmp/pair-replay
python3 reproduce.py --mech-root /path/to/mech --output /tmp/pair-compact --role keep-pairs65536
python3 probe.py --mech-root /path/to/mech --output /tmp/pair-native-probe
python3 verify.py
```

The standard matcher executes **164,668,189 instructions** on random 1 MiB, only 35 above control and 1,044,350 below the old two-cell cache. It retains all 1,044,626 LDPs, all 2,097,082 prefetches and reduces SP load instructions from 11,204,255 to 10,151,519. This repairs the prior regression. The remaining loss is still about 3% of Mech time. [All remaining losses](parity.json) and [the next profiling work](next-experiments.json) target the larger losses and repeated hot work; further FP-limit variation is not the next priority. All earlier partials and the smaller qualified recipe remain available.

The [untimed hot-block census](hot-block-census.json) records the exact instruction paths behind the next compiler candidates. Redundant masks and proposed bit-field rewrites remain hypotheses until their SSA and bit-preservation proofs pass.
