The compiler source for this handoff is [Mech #995 at `0b15e658c`](https://github.com/mech-lang/mech/commit/0b15e658c123b4aa12e30bde2ad9d47d1f156318). The selected `control` recipe reproduces the prior qualified `address-focus` image exactly. Another agent can rebase on this compiler-source commit and run the source generator below.

The retained `shift-balanced` alternative narrows masked word shifts after prefetch admission. The earlier placement removed both future-write hints; this placement keeps them. Both full 81-case / 96-block run orders preserve every named **81 Roc / 63 libdeflate win** for both recipes. There is no 64th C win yet. Compiler defaults stay unchanged.

| Case | Current recipe | Retained shifts | Paired change across both orders |
|---|---:|---:|---:|
| Periodic 1 MiB | 11.122–11.133 ms | 10.798–10.809 ms | 2.91–3.23% less time |
| Repeated 1 MiB | 12.933–12.936 ms | 12.605–12.614 ms | 2.50–2.53% less time |
| Distribution change 16 KiB | 0.578–0.582 ms | 0.569–0.573 ms | 1.49–1.53% less time |
| Random 1 MiB | 21.269–21.288 ms | 21.413–21.423 ms | 0.52–0.68% more time |

**28 cases use at least 1% less time in both orders.** Random1M remains closer to parity with the current recipe, so it stays selected while the extra shift-result copies are repaired. The retained shifts are 1.0545–1.0554× C on that case; current timing is about 1.049× C. The alternative is retained for combination, not discarded because of the slowdown.

| Complete source-through-final-link build | Median | Stripped executable |
|---|---:|---:|
| Mech current | 2.1745 s | 210,024 B |
| Mech retained shifts | 2.1742 s | 210,024 B |
| Roc | 2.9703 s | 191,912 B |
| libdeflate C | 0.4789 s | 155,752 B |

These are eight balanced serial orders on **Apple M1 / macOS15.6.1 / arm64**, with compilers and identical fixed support prebuilt equally. Each codec is built fresh through its final executable link. Compiler bootstrap and stripping are separate. The retained Mech build takes 0.732× Roc time and 4.538× C time; it is effectively unchanged from control. Encoder text is 64,024 B versus 64,040 B control; lookup data 3,200 B and actual stack 4,736 B are unchanged.

The optional composed-address hook also transforms 14 scorer addresses. Both allocation trials were flat on random1M and lost the close natural4K C win in reverse. Those source recipes, counts and trials are included under `scorer-study`; they remain unselected.

Validation includes 172 focused native test executions (80 scalar and three append tests under each mode, plus four prefetch and two indexed-address JIT tests). Seven shift images and six scorer images each pass 162 output/inflation/alias/resource/cleanup observations, six named errors and 12 recovery pairs. All 32 timed build outputs match their artifact pins; 324 executions of the timed standalone images independently inflate correctly. The verifier recomputes the full runtime statistics and named wins from 1,965,312 observations. Normal and checked source replays reproduce all three artifacts for all 12 recipes, including the current image and earlier scorer trials, from this pushed compiler source. The public script also builds a compiler from this source checkout with cached dependencies and reproduces both default recipes afresh. Full GPU tests, full CI and a formal confidence claim are not added.

The original idiomatic 2,719-line codec and canonical bytecode remain unchanged. No LLVM dependency is added. The source changes are generic guarded compiler options; no benchmark name or input length selects them.

To build the compiler from this Mech revision and reproduce both recipes:

```sh
python3 reproduce.py --mech-root /path/to/mech --output /tmp/prefetch-replay
python3 reproduce.py --mech-root /path/to/mech --output /tmp/prefetch-checked --checked
python3 verify.py
```

Use `--role control` for the selected random-data recipe or `--role shift-balanced` for the retained broad gain. `--compiler /path/to/compile_profile` reuses a prebuilt compiler. Profiles are named by content hash; the script checks exact object, metadata and bytecode hashes. Source emission replay is separate from performance qualification. `raw-manifest.json` maps logical evidence paths to the content-addressed blobs in `raw.tar.gz`; compiler/test build caches are excluded.
