# Late matcher routes and prefetch address reuse

The encoder recipe `shared-bases-linear-4096` reduced the fixed 18-case mean positive slowdown from **14.649091% to 11.643025%** on an Apple M1 running macOS 15.6.1, a decrease of **3.006066 percentage points**. Random 1 MiB measured **1.005668 / 1.006461×** libdeflate time in two balanced 96-block orders. The matched control measured 1.030728 / 1.031867×. [`f90bc5228`](https://github.com/mech-lang/mech/commit/f90bc52287a7e809685faf1116b2c77b7bf48ee8) · [Mech PR #999](https://github.com/mech-lang/mech/pull/999).

The comparison used all 81 fixtures, the original 2,719-line Mech codec and its exact canonical bytecode, the pinned Roc actor and libdeflate 1.26 at level 12. The runtime verifier recomputed 1,965,312 observations from the saved timing blocks.

| Encoder | Fixture order | Roc wins | libdeflate wins | Missing protected cases |
|---|---|---:|---:|---|
| Matched control | forward | 81/81 | 63/81 | None |
| Matched control | reverse | 81/81 | 63/81 | None |
| Candidate | forward | 81/81 | 63/81 | None |
| Candidate | reverse | 81/81 | 63/81 | None |

The 64th libdeflate win remains open. The benchmark index selects this recipe on the strength of the lower cohort margin and the complete protected win floor. [Selected recipe](../mechdeflate-latest.json) · [Protected win floor](protected-floor.json).

## Fixed 18-case loss cohort

The maximum paired loss moved from 33.714318% to 30.108824%. The mean of the worse orders moved from 14.851959% to 11.901415%. Both 1 KiB natural and Reymont names remain in the cohort. Their input hashes match, and their calls and timings are recorded independently.

Each paired ratio and median time column is forward / reverse. The last column is the change in the case's contribution to the fixed-cohort mean, in percentage points. Positive values are improvements. [Exact per-case data](case-margins.json).

| Fixture | Control / C | Candidate / C | Control ms | Candidate ms | C ms | Contribution decrease |
|---|---:|---:|---:|---:|---:|---:|
| `prefix-random-4096` | 1.328397 / 1.345947 | 1.293047 / 1.309180 | 0.100562 / 0.101771 | 0.098084 / 0.098729 | 0.076000 / 0.075917 | +0.200305 |
| `prefix-random-8192` | 1.296752 / 1.306406 | 1.251618 / 1.272076 | 0.160875 / 0.162542 | 0.155687 / 0.158438 | 0.124563 / 0.124688 | +0.220915 |
| `prefix-natural-1024` | 1.213428 / 1.209024 | 1.199016 / 1.196591 | 0.071292 / 0.071209 | 0.070458 / 0.070583 | 0.059041 / 0.059042 | +0.074561 |
| `reymont-prefix-1024` | 1.208967 / 1.208777 | 1.195074 / 1.197364 | 0.071250 / 0.071125 | 0.070417 / 0.070375 | 0.059042 / 0.059041 | +0.070299 |
| `16384-distribution-change` | 1.200910 / 1.199099 | 1.179355 / 1.188460 | 0.578250 / 0.576104 | 0.569875 / 0.574499 | 0.481396 / 0.482229 | +0.089477 |
| `prefix-random-16384` | 1.219366 / 1.218484 | 1.171337 / 1.170497 | 0.288541 / 0.289042 | 0.276896 / 0.276458 | 0.236625 / 0.236854 | +0.266712 |
| `random-32769` | 1.132329 / 1.129889 | 1.101215 / 1.094148 | 0.599042 / 0.598042 | 0.581042 / 0.578666 | 0.526917 / 0.529250 | +0.185738 |
| `prefix-random-33027` | 1.130954 / 1.134280 | 1.093489 / 1.099251 | 0.604083 / 0.606708 | 0.583854 / 0.586645 | 0.532667 / 0.534791 | +0.201388 |
| `prefix-random-32769` | 1.125087 / 1.133195 | 1.091013 / 1.100013 | 0.593937 / 0.601917 | 0.576083 / 0.583917 | 0.526875 / 0.530417 | +0.186831 |
| `prefix-random-32767` | 1.124071 / 1.131042 | 1.090117 / 1.096704 | 0.583812 / 0.585229 | 0.565021 / 0.567875 | 0.517459 / 0.517958 | +0.189696 |
| `prefix-random-32768` | 1.124763 / 1.123887 | 1.089416 / 1.087893 | 0.583584 / 0.583500 | 0.564917 / 0.564063 | 0.517188 / 0.519062 | +0.198170 |
| `heldout-random-65537` | 1.102582 / 1.100069 | 1.069621 / 1.069358 | 1.269687 / 1.267771 | 1.232917 / 1.233854 | 1.148624 / 1.150875 | +0.176864 |
| `prefix-random-65537` | 1.090254 / 1.092802 | 1.061620 / 1.062911 | 1.278625 / 1.281270 | 1.243604 / 1.245500 | 1.168833 / 1.172188 | +0.162567 |
| `prefix-random-65535` | 1.089917 / 1.094373 | 1.059108 / 1.061556 | 1.269437 / 1.272730 | 1.233083 / 1.235667 | 1.161396 / 1.161771 | +0.176731 |
| `prefix-random-65536` | 1.090128 / 1.092042 | 1.057157 / 1.059498 | 1.267813 / 1.269604 | 1.229124 / 1.233396 | 1.160438 / 1.162084 | +0.181989 |
| `prefix-random-131072` | 1.055104 / 1.055684 | 1.028566 / 1.030049 | 2.613583 / 2.616146 | 2.548875 / 2.554063 | 2.472917 / 2.477604 | +0.144925 |
| `prefix-random-262144` | 1.049821 / 1.053369 | 1.025122 / 1.028129 | 5.311063 / 5.326728 | 5.181875 / 5.203521 | 5.052646 / 5.057834 | +0.138718 |
| `prefix-random-1048576` | 1.030728 / 1.031867 | 1.005668 / 1.006461 | 20.952938 / 20.967645 | 20.455917 / 20.475646 | 20.347708 / 20.348667 | +0.140180 |

## Compiler changes and discovery results

The matcher recipe forwards 26 eligible late acyclic edges and allows the existing AArch64 compare-and-branch lowering in the private vector phase. After egraph optimization, equal wrapping I64 prefetch address adds can share a dominating definition. Memory operations, hints and guards retain their order. The options are opt-in at compile time.

Complete-invocation samples put about 75% of random 1 MiB time and 30% of random 4 KiB time in the matcher. The untimed diagnostic image for random 1 MiB executed 147,708,320 matcher instructions, down from 164,668,189 in the reference, with all 2,097,082 prefetches and at least the original 1,044,626 paired reload instructions retained. [Invocation profiles](profile-summary.json).

The 25-case discovery panel includes all 18 losses and seven protected libdeflate wins. Each measured recipe ran both 24-block orders with its own matched control. The full run used the recipe with the closest random 1 MiB result in both discovery orders.

| Discovery recipe | Random 1 MiB / C, forward / reverse | Cohort mean decrease (pp) | Missing protected cases |
|---|---:|---:|---|
| `reprofiled-linear-4096` | 1.024788 / 1.031694 | 0.191540 | `320-overlap` (forward) |
| `combined-linear-65536` | 1.009266 / 1.010791 | 2.433492 | None |
| `combined-sqrt-65536` | 1.014375 / 1.018585 | 1.240051 | None |
| `combined-linear-4096` | 1.007367 / 1.010302 | 2.172301 | None |
| `forward-linear-4096` | 1.013371 / 1.014569 | 1.618797 | None |
| `zero-linear-4096` | 1.024227 / 1.027753 | 0.551824 | None |
| `shared-bases-linear-4096` | 1.005008 / 1.007098 | 2.663861 | None |
| `shared-bases-linear-65536` | 1.005465 / 1.007317 | 2.748577 | None |
| `shared-bases-edges-linear-4096` | 1.008897 / 1.010109 | 3.010679 | None |
| `shared-bases-visits-linear-4096` | 1.006660 / 1.011731 | 2.702393 | None |

The reprofile-only candidate and its matched control each missed `320-overlap` in the forward discovery order. Late predicate refinement removed zero additional branches and produced identical artifacts with both combinations. The address-reuse layout weighted by dynamic edges gave the largest discovery cohort reduction. Its random 1 MiB gap exceeded the selected layout's gap in both orders.

The next target-specific comparison can use the saved matcher trace to locate the remaining 7,679,623 stack-load instructions in random 1 MiB. Trace the most frequent repeated reloads to their defining values before testing value reuse with the paired reloads and prefetch order preserved.

## Native checks, size and complete builds

The candidate passed 162 exact output, independent inflation and alias observations, 6 named errors and 12 exact recovery pairs. Normal, checked and inspection emissions agree. The encoder with the experimental options disabled reproduced the pinned control object, metadata, bytecode and linked worker. Focused AArch64 branch and prefetch tests, formatting, warning policy and unsafe-boundary checks also passed.

| Image | Encoder text | Lookup data | Whole const | Stripped executable | Peak stack |
|---|---:|---:|---:|---:|---:|
| Control | 63,720 B | 3,200 B | 17,728 B | 210,024 B | 4,832 B |
| Candidate | 63,592 B | 3,200 B | 17,728 B | 210,024 B | 4,832 B |

The stack cap is 5,280 B. Mech, Roc and C use equally prebuilt compilers and fixed host support for 32 serial balanced source-through-final-executable-link builds. Stripping is timed separately. All 324 executable outputs independently inflated and passed their expected-byte rules. [Qualification record](qualification.json).

| Original source through final executable link | Median seconds |
|---|---:|
| Mech control | 2.195981 |
| Mech candidate | 2.202889 |
| Roc | 2.986964 |
| libdeflate C | 0.482534 |

## Reproduce and verify

Check out `f90bc52287a7e809685faf1116b2c77b7bf48ee8` to rebuild the compiler and verify exact encoder artifact hashes. The source script accepts a prebuilt compiler with `--compiler`. The timing replay verifies and restores the published fixtures and peer binaries from the sibling masked-field packet. Use an arm64 macOS host for the executable replay.

Source replays from the final compiler reproduced the pinned control and the normal and checked candidate artifacts. [Control replay](control-source-replay.json) · [Candidate replay](source-replay.json) · [Checked replay](checked-source-replay.json).

```sh
python3 verify_archive.py
python3 reproduce_candidate.py --mech-root /path/to/mech --output /tmp/phase-encoder --role shared-bases-linear-4096
python3 replay_timings.py --output /tmp/phase-clocks --role shared-bases-linear-4096
python3 verify_timings.py /tmp/phase-clocks shared-bases-linear-4096 /tmp/phase-clocks/pinned-peers/libdeflate-output-oracle.json
python3 ../mechdeflate-average-margin-v1/score.py --results /tmp/phase-clocks/shared-bases-linear-4096-results.json
```

The original clocks can be verified by extracting the archive after checking its manifest.

```sh
mkdir /tmp/phase-evidence
tar -xzf raw-evidence.tar.gz -C /tmp/phase-evidence
python3 verify_timings.py /tmp/phase-evidence/candidates-next/timings-qualification shared-bases-linear-4096 libdeflate-output-oracle.json
```

The archive contains both complete timing orders, discovery observations, checked recovery and stack records, and original-source build receipts. Each archive member has a recorded content hash. [Role bindings](roles.json) · [Raw evidence](raw-evidence.tar.gz) · [Manifest](raw-manifest.json).
