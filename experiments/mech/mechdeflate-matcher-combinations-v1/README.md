# Matcher combinations and effects across Mechdeflate inputs

Compiler source remains [Mech PR #995 at `13b8e0698`](https://github.com/mech-lang/mech/pull/995/commits/13b8e06983895d8d8be1665862b8879175b37e4d). These experiments combine existing compiler options and fresh measured profiles. The original idiomatic codec source and canonical bytecode remain unchanged. No LLVM dependency is added.

## Qualified improvement across inputs

The [preceding full81 study](../mechdeflate-literal-pairs-v1/) improved several input types while retaining every named **81 Roc / 63 libdeflate win** in both measurement orders. Derived point estimates are in [qualified-cross-case-effects.json](qualified-cross-case-effects.json).

| Input | Before → after, forward | Less time across both orders |
| --- | ---: | ---: |
| Distribution change, 16 KiB | 0.593688 → 0.580000 ms | 2.31–2.44% |
| Random, 32,769 bytes | 0.631667 → 0.621730 ms | 1.41–1.57% |
| Periodic, 128 KiB | 1.453625 → 1.430376 ms | 1.26–1.60% |
| Periodic, 1 MiB | 11.277271 → 11.144687 ms | 1.18–1.23% |
| Repeated, 1 MiB | 13.099813 → 12.967541 ms | 0.99–1.01% |
| Random, 1 MiB | 22.273333 → 22.061771 ms | 0.93–0.95% |

Natural-text results are mixed: some cases slow roughly 0.3–0.9%, with all named peer wins retained. This establishes improvement across the Mechdeflate suite; unrelated Mech program benchmarks have not been measured.

## New discovery screens

Apple M1 / macOS 15.6.1 / arm64. Eight variants each receive two six-case screens, using 96 balanced blocks per case and pinned Roc/libdeflate workers. The control is the qualified 64,120 B paired image above. Cases cover distribution-change 16 KiB, natural 4 KiB and 16 KiB, random 4 KiB and 1 MiB, and periodic 1 MiB. Native checks, source emission, counters, builds, Git and archive work are terminal before clocks. All individual observations are retained; no formal confidence claim is made.

The all-arithmetic balanced variant (`MECH_NARROW_PRIVATE_ARITHMETIC=1`, `MECH_ARM64_REUSE_I32_ARITHMETIC=all`) gives the most useful random1M screen result:

| Random 1 MiB | Forward | Reverse |
| --- | ---: | ---: |
| Qualified Mech control | 22.019501 ms | 22.026104 ms |
| All-arithmetic balanced | 21.893521 ms | 21.895313 ms |
| libdeflate | 20.305854 ms | 20.313188 ms |
| Candidate / libdeflate, paired blocks | 1.080247× | 1.079245× |

This is about 0.6% less Mech time. Encoder text is 64,088 B, 32 B smaller than the control; actual stack is 4,736 B. All required named wins present in this subset hold in both orders. **It has not passed full81 qualification and has not replaced the qualified image.** Fresh-process source-through-final-link time and stripped executable size have not been newly measured for these variants.

Shift narrowing is a retained partial result: periodic1M improves about 3% (11.14 → 10.80 ms), while random1M slows about 2.5% (22.02 → 22.59 ms). Keep it for selective repair or combination. Earlier byte-load combinations are also retained; two narrowly lose the natural4K C win in reverse order. None is discarded merely for one loss.

Five fresh register/machine layouts plus two selected-value refinement candidates pass native output/error/recovery gates. The latter two are prepared for profiling and have no new timing claim. The existing spill forwarding pass is already enabled; its control experiment is not counted as a new optimization.

## Validation and replay

All ten public candidate recipes pass exact normal and checked source replay: object, metadata and canonical bytecode hashes match. Native gates cover 162 exact output/inflation/alias/resource/cleanup observations, six named checked errors and 12 recovery pairs per candidate. Measured stack is 4,736 B for the word/refinement candidates and 4,864 B for the byte-load combinations, below the 5,280 B limit. Source JIT/scalar tests were also rerun with the actual `MECH_ARM64_REUSE_I32_ARITHMETIC=add` key; an earlier test-only runner had used an ignored `...DEFINITIONS` key. Benchmark recipes always used the actual key, so their measurements are unaffected.

Use the preceding study's source-built compiler, or let this replay construct one from the linked Mech checkout:

```sh
python3 reproduce.py --mech-root /path/to/mech --output /tmp/matcher-replay \
  --target-dir /tmp/matcher-target --role paired-word-all-balanced
python3 reproduce.py --mech-root /path/to/mech --output /tmp/matcher-checked \
  --compiler /tmp/matcher-replay/compile_profile --checked \
  --role paired-word-all-balanced
python3 verify.py
```

All profiles are content-addressed. The raw archive includes every variant, fresh profiles and counts, native gate reports, primary screen observations, exact replay logs and the helper-repair record. Some private historical helper files are no longer present locally. A standalone census/link helper replaces that import chain; it matches the qualified image's complete symbol census and reproduces the qualified worker byte-for-byte. The failed loader attempt is retained as history and is not a replay dependency. Historical absolute paths remain in raw records; the portable replay above verifies source emission. Full runtime campaign replay additionally needs the pinned fixed support described in those records.
