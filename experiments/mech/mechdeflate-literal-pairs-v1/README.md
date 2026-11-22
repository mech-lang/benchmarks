# Mechdeflate checked literal pairs

Source: [Mech PR #995 at `13b8e0698`](https://github.com/mech-lang/mech/pull/995/commits/13b8e06983895d8d8be1665862b8879175b37e4d). This is a compiler-source revision another agent can use as its base.

The compiler can now pair two checked literal appends whose cost index has a constant bias. Recognition requires the exact guarded modular index and the existing private no-growth and disjoint-window proofs. Failed lookahead resumes the original scalar visit before either store. Enable `MECH_PAIR_BIASED_APPENDS=1` with the existing checked-pair option and the complete recipe in [recipes.json](recipes.json). The option remains off by default.

The original 2,719-line Mech program and canonical bytecode are unchanged. This pass adds no dependency. The benchmark relocation is preserved; original records remain in [benchmarks PR #10](https://github.com/mech-lang/benchmarks/pull/10).

## Qualified result

Apple M1, macOS 15.6.1, arm64. Both full 81-case runs use 96 balanced blocks per case and preserve all named **81 Roc wins and 63 libdeflate wins**. There is no 64th win yet. Point estimates are reported without a formal confidence claim.

| 1 MiB random | Forward order | Reverse order |
| --- | ---: | ---: |
| Retained Mech | 22.273333 ms | 22.218958 ms |
| Paired Mech | 22.061771 ms | 22.012500 ms |
| libdeflate | 20.339604 ms | 20.333855 ms |
| Paired Mech / libdeflate | 1.084840× | 1.084248× |

The remaining Mech-time reduction to parity is 7.77–7.82%. Larger random, periodic and repeated inputs also improve. Distribution-change input improves about 2.5%. Natural-text results are mixed, with every named peer win retained.

| Build or size | Retained Mech | Paired Mech | Roc | libdeflate |
| --- | ---: | ---: | ---: | ---: |
| Source through executable linking | 2.188560 s | 2.182683 s | 2.984945 s | 0.482034 s |
| Stripped executable | 210,024 B | 210,024 B | 191,912 B | 155,752 B |
| Mech encoder text | 63,832 B | 64,120 B | — | — |

The build comparison uses eight balanced serial orders, equally prebuilt compilers and fixed support, and fresh source compilation through final linking. Compiler construction and stripping are separate. The paired compile-time ratio is 0.9995× the retained Mech build: effectively unchanged. It is 0.7310× Roc and 4.5231× libdeflate. Mech readonly data remains 3,200 B and actual total stack remains 4,736 B. All 324 standalone executable/case checks pass, with independent inflation and stored raw streams.

## Repairs and profiles

The first unprofiled pair candidate loses the natural-text 4 KiB C win. Fresh register and layout profiles restore that win in both directions; the repaired linear variant passes both full panels. All original and repaired alternatives are retained in the raw records.

The scorer executes 57,451,769 instructions in the control and 48,733,617 in the repaired candidate on 1 MiB random input, with unchanged stack traffic. This is about 15% fewer scorer instructions, while whole-call time improves about 1%.

Separate three-second CPU profiles cover Mech control, Mech pairs, Roc and libdeflate on random and natural 1 MiB inputs. Within the paired Mech native compression subtree, random input spends about 75.7% of samples in matcher475 and 12.0% in scorer3009. The next broad optimization target is the matcher. These are approximate sampling fractions; excluded validation frames are outside that denominator.

Three native JIT tests pass, including 3,618 differential calls plus alias and exact-guard fixtures. The 80-test scalar filter passes normally and with pair/native-reuse options. Every candidate passes 162 output/inflation/alias/resource/cleanup checks, six named checked errors and twelve recovery pairs. Formatting, warning policy and the unsafe-boundary audit pass. This does not claim the full GPU test suite or full CI ran.

## Source replay

Use a Mech checkout at the linked revision. The maintained original program is `hosts/gpu/tests/fixtures/native/compact-compiler-regression.mec`.

```sh
python3 reproduce.py --mech-root /path/to/mech \
  --output /tmp/mech-pair-replay --target-dir /tmp/mech-pair-target
python3 reproduce.py --mech-root /path/to/mech \
  --compiler /tmp/mech-pair-replay/compile_profile \
  --output /tmp/mech-pair-checked --checked
```

The first command constructs the compiler from that source, then checks exact object, metadata and bytecode hashes for the retained control and paired candidate. The second repeats emission with the register checker. Compiler templates are unchanged archived harness sources; the replay adjusts their paths for the relocated checkout. All recipe profiles are content-addressed copies.

[summary.json](summary.json) contains precise statistics. The raw archive retains source bindings, producer logs, failed diagnostic requests, native gates, dynamic counts, CPU profiles, every runtime observation, matched build records, executable images and deployment outputs. Its verifier checks file hashes, recomputes paired runtime statistics and named wins from raw observations, and independently inflates standalone outputs against the included inputs.

```sh
python3 verify.py
```

The historical harness paths are preserved in raw records. Replaying the complete performance campaign also requires the pinned peer compilers, workers and fixed support described by those records and the earlier archive. The source replay above is a separate artifact-identity check.
