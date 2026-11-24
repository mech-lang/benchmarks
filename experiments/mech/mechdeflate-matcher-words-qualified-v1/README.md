# Qualified matcher word arithmetic

Use [Mech PR #995 at `13b8e0698`](https://github.com/mech-lang/mech/pull/995/commits/13b8e06983895d8d8be1665862b8879175b37e4d) with `--role paired-word-all-balanced` in this directory's replay. [recommended-recipe.json](recommended-recipe.json) identifies the current qualified benchmark recipe. It combines existing generic private-word arithmetic with the paired scorer and fresh measured register/machine profiles. Global compiler defaults remain unchanged.

The original 2,719-line idiomatic Mech source and canonical bytecode are unchanged. There is no LLVM dependency. The separate address-reassociation compiler experiment is not part of this qualification.

## Runtime and size

Apple M1, macOS 15.6.1, arm64. Both full81 runs use 96 balanced blocks per case. Every named **81 Roc / 63 libdeflate win** is retained in both orders. There is no 64th libdeflate win yet.

| Random 1 MiB | Forward order | Reverse order |
| --- | ---: | ---: |
| Qualified paired control | 22.001750 ms | 21.999042 ms |
| Matcher words | 21.883979 ms | 21.877792 ms |
| libdeflate | 20.355500 ms | 20.339417 ms |
| Matcher words / libdeflate, paired blocks | 1.076005× | 1.074853× |

The new recipe takes about 0.54–0.55% less time than its matched control. Another **6.96–7.06% reduction in Mech time** is required to reach parity on this closest losing case. Individual point estimates are retained without a formal confidence claim. The score is based on each named paired result, not an aggregate speedup.

Encoder text falls from **64,120 B to 64,088 B**. Readonly data remains 3,200 B, measured total stack remains 4,736 B, and the stripped executable remains 210,024 B. Text bytes and executable bytes are different measurements.

## Complete builds

Eight balanced serial orders compare fresh processes from unchanged source through final executable linking. Compilers and the same fixed host/allocator support are prebuilt equally. No old encoder object is reused as compiler input. Compiler construction and stripping are separate. Every emitted Mech object, metadata file and canonical bytecode image matches its qualified hash in every build.

| Build or size | Paired control | Matcher words | Roc | libdeflate |
| --- | ---: | ---: | ---: | ---: |
| Source through executable link | 2.182965 s | 2.177533 s | 2.993411 s | 0.480064 s |
| Stripping, separately | 0.010513 s | 0.010580 s | 0.010690 s | 0.010389 s |
| Stripped executable | 210,024 B | 210,024 B | 191,912 B | 155,752 B |

The paired median build ratios are **0.9992× control**, **0.7293× Roc**, and **4.5415× libdeflate**. Mech build time is effectively unchanged. Median Mech phases: parsing 0.6771 s, frontend 0.2237 s, native compilation 1.2069 s, final link 0.0349 s. These phases are measured within the same fresh source builds.

All four timed warmup executable images also pass all81 standalone input checks: **324 executions**, independent inflation, and stored raw output streams. Fixed inputs and compilers are pinned by hash. The complete-build timer is recovered byte-for-byte from the tracked benchmark archive, matching the preceding study's timer hash; the retired private import chain is not needed.

## Counter evidence and retained alternatives

Actual matcher counts on random1M fall from 176,294,737 instructions in the paired control to **174,177,704**. Branch count remains 28,766,024; stack loads are 11,197,350. These diagnostic counters run separately from elapsed-time clocks.

The shift-narrowing partial remains available in the [preceding discovery study](../mechdeflate-matcher-combinations-v1/). It takes about 3% less time on periodic1M but about 2.5% more on random1M. Fresh counters show that it removes **2,097,082 prefetch hints** and 4,194,164 adds while introducing 2,097,152 moves on random1M. This identifies a changed prefetch path as an important part of the tradeoff; instruction count alone does not establish a performance gain.

Two selected-value-refinement candidates retain smaller raw text and pass native checks, but the refined raw word candidate executes only 2,770 fewer branches than its unrefined control on random1M before layout. They remain recorded for combination; they are not presented as the next large runtime gain. The next compiler experiment targets repeated affine table-address calculations observed in the hot matcher blocks.

## Checks and replay

The native word tests pass **186 test executions** across arithmetic and shift modes: wrapping/shared/dirty-input extension tests, selected-value and loop-width proofs, paired append differentials, and the 80-test scalar filter. This does not claim full GPU tests or full CI. The selected candidate also retains its 162 codec output/inflation/alias/resource/cleanup observations, six checked-error cases and 12 recovery pairs.

```sh
python3 reproduce.py --mech-root /path/to/mech --output /tmp/word-replay \
  --target-dir /tmp/word-target --role paired-word-all-balanced
python3 reproduce.py --mech-root /path/to/mech --output /tmp/word-checked \
  --compiler /tmp/word-replay/compile_profile --checked \
  --role paired-word-all-balanced
python3 verify.py
```

Exact normal and checked source replays use the retained source-built `13b8e0698` compiler. All profiles are content-addressed. The archive includes every full81 timing observation, complete build command/result/artifact, standalone raw stream, native-test log, and fresh diagnostic count. Historical absolute paths remain in raw records; the portable replay verifies source emission. A full timing campaign additionally requires the pinned peer compilers and fixed support described in the plan.
