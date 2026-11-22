[Mech #995 at `94eeda948`](https://github.com/mech-lang/mech/commit/94eeda948abddf988fc470848847a23cd3331aa7) is the compiler-source basis for this handoff. The selected `reuse-byte-all-sqrt` combines fixed word-shift definition reuse with the earlier byte-comparison reuse experiment. Both full 81-case / 96-block run orders preserve every named **81 Roc / 63 libdeflate win**. No 64th C win yet.

| Case | Previous selected recipe | New selected recipe | Paired change in both orders |
|---|---:|---:|---:|
| Random 1 MiB | 21.277–21.299 ms | 21.206–21.211 ms | 0.36–0.46% less time |
| Periodic 1 MiB | 11.126–11.132 ms | 10.482–10.483 ms | about 5.8% less time |
| Repeated 1 MiB | 12.926 ms | 12.275 ms | about 5.0% less time |

**28 cases use at least 1% less time in both orders.** Random 1 MiB is **1.0430–1.0450× libdeflate time**, versus C medians 20.317–20.348 ms. Removing another **4.12–4.30% of Mech time** would reach parity on that case. Random4K is approximately flat forward and faster reverse; a robust gain in both orders is not established there. Every named win remains intact.

The generic opt-in `MECH_ARM64_REUSE_I32_SHIFTS=1` reuses the zero upper word written by nonzero fixed I32 logical-right shifts. It excludes identity shifts, arbitrary narrow inputs, variable shifts and other producers. `MECH_NARROW_PRIVATE_ARITHMETIC=after-prefetch` keeps both future-write hints before narrowing the shifts. The selected recipe also uses the existing `MECH_ARM64_REUSE_I8_DEFINITIONS=all`, with fresh declared nine-case register and machine profiles. No benchmark name or input length selects compiler flags.

The first repair retained broad gains but added roughly 2.1 million shift-result copies in the focus allocation. Those copies are now removed. The new selected matcher executes 168,197,657 instructions on random1M versus 170,329,253 previously, while keeping all 2,097,082 prefetches. The original idiomatic 2,719-line source and canonical bytecode remain unchanged. No LLVM dependency is added.

| Fresh source through final executable link | Median | Stripped executable |
|---|---:|---:|
| Mech previous selected | 2.1839 s | 210,024 B |
| Mech new selected | 2.1866 s | 210,024 B |
| Roc | 2.9780 s | 191,912 B |
| libdeflate C | 0.4859 s | 155,752 B |

Eight balanced serial orders on **Apple M1 / macOS15.6.1 / arm64** use compilers and identical fixed support prebuilt equally. Every codec is compiled fresh through final executable linking. Compiler construction and stripping are separate. Paired build time is 0.734× Roc and 4.540× C, effectively unchanged from control (1.0008×). Encoder text is **63,992 B**, down 48 B; lookup data 3,200 B and measured stack 4,736 B are unchanged.

Validation includes four native JIT test executions covering **1,038,800 actual native calls** with dirty upper bits, shared signed/unsigned/narrow users, modulo shift counts, joins and guarded null pointers. Identity and excluded producer cases retain exact machine bytes. The tiny shared-result fixtures grow 4 B because register allocation changes despite one fewer VCode instruction; these are correctness tests, not a universal speed or size claim. Eight codec images each pass 162 output/inflation/alias/resource/cleanup observations, six named errors and 12 recoveries. Normal/checked/inspection emissions match. The verifier recomputes 1,965,312 runtime observations, checks 32 timed builds, independently inflates 324 standalone outputs and verifies 22 exact artifact replays. The public source-build and native-probe workflows are also executed and verified. Full GPU tests, full CI and formal confidence are not claimed.

To build the compiler from this source checkout and reproduce both the previous control and new selected recipe:

```sh
python3 reproduce.py --mech-root /path/to/mech --output /tmp/word-replay
python3 reproduce.py --mech-root /path/to/mech --output /tmp/word-checked --checked
python3 probe.py --mech-root /path/to/mech --output /tmp/word-native-probe
python3 verify.py
```

`--role reuse-byte-all-sqrt` selects only the new recipe; `--compiler` reuses an existing compiler. Profiles are named by content hash. Both the earlier qualified shift variant and all new partials remain reproducible. Raw logs, counters, native probe bodies, trials, standalone streams and source bindings are content-addressed in `raw.tar.gz` through `raw-manifest.json`. Compiler/test build caches are excluded. See `next-experiments.json` for the remaining comparison-extension, prefetch-setup and larger-loss targets.
