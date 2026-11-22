# Shared immutable code pages: retained experiments

The selected default is `m1-shared-code-pages-64` (`pages-6-sqrt-plain`): **all 81/81 Roc and 63/81 libdeflate wins preserved in both complete 81-case, 96-block orders**. It emits **63,800 B of code, 3,200 B of readonly lookup data and a 210,024-B stripped executable**, down from 276,072 B. The single natural4KiB loss in the initial smaller-table trial was repaired with actual register weights and a fresh machine layout. No 64th win or formal confidence claim is added. The original 2,719-line Mech program and canonical bytecode are unchanged; no new LLVM dependency.

## Compiler change

The optional `MECH_COMPOSE_IMMUTABLE_COST_CODE_PAGE_SHIFT=4..12` replaces an already admitted immutable byte table with a byte directory and deduplicated fixed-size pages. The option is globally off. Empty, oversized, nonbeneficial or more than 256-page dictionaries retain dense storage. Partial final pages are initialized. Cache identity includes page geometry. The original index proof and cost-array admission are unchanged; metadata reports actual physical data size.

All 65,536 values from each actual compiler-emitted table reconstruct exactly. Focused tests execute 1,310,910 native lookup calls across every admitted word for dense/all nine page sizes, a partial final page, and full width invalid words rejected before a null table read. Maintained scalar 79, composed admission 6, packet 6 and select/range/SSA families pass. No full GPU suite claim.

## Timings and parity

27-case discovery panels cover all 18 remaining C losses plus nine win canaries. Five-case repair screens examine natural4KiB/natural8KiB, natural1KiB, distribution change and random1MiB. Every panel runs 96 blocks in both orders. Smaller paired Mech/C elapsed-time ratios are better. All missing named wins, slower trials and zero samples remain included; no confidence claim. The selected role also passed independent full 81 qualification in both orders; the other alternatives remain experimental.

| Candidate | Order | Cases | Text B | Lookup data B | Mech 1 MiB ms | C ms | Paired Mech/C | Mech reduction to parity | Missing required panel wins |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| pages-12 | forward | 27 | 63,800 | 40,976 | 22.443500 | 20.346417 | 1.104176 | 9.43% | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | 27 | 63,800 | 40,976 | 22.449438 | 20.310834 | 1.106142 | 9.60% | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | 27 | 63,800 | 3,200 | 22.419833 | 20.340312 | 1.102885 | 9.33% | {'roc': [], 'libdeflate': []} |
| pages-6 | reverse | 27 | 63,800 | 3,200 | 22.441208 | 20.322667 | 1.105803 | 9.57% | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6-linear-plain | forward | 5 | 63,800 | 3,200 | 22.445791 | 20.313271 | 1.105801 | 9.57% | {'roc': [], 'libdeflate': []} |
| pages-6-linear-plain | reverse | 5 | 63,800 | 3,200 | 22.443500 | 20.333416 | 1.105535 | 9.55% | {'roc': [], 'libdeflate': []} |
| pages-6-linear-plain-raw | forward | 5 | 63,816 | 3,200 | 22.523708 | 20.330333 | 1.108578 | 9.79% | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-plain-raw | reverse | 5 | 63,816 | 3,200 | 22.518354 | 20.313000 | 1.110350 | 9.94% | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-preserved | forward | 5 | 63,800 | 3,200 | 22.442667 | 20.341021 | 1.104261 | 9.44% | {'roc': [], 'libdeflate': []} |
| pages-6-linear-preserved | reverse | 5 | 63,800 | 3,200 | 22.447354 | 20.314750 | 1.105725 | 9.56% | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6-linear-preserved-raw | forward | 5 | 63,816 | 3,200 | 22.453500 | 20.296833 | 1.106560 | 9.63% | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-preserved-raw | reverse | 5 | 63,816 | 3,200 | 22.516083 | 20.320437 | 1.109037 | 9.83% | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain | forward | 5 | 63,800 | 3,200 | 22.432209 | 20.337500 | 1.102788 | 9.32% | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | 5 | 63,800 | 3,200 | 22.444834 | 20.315229 | 1.105807 | 9.57% | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain-raw | forward | 5 | 63,816 | 3,200 | 22.510166 | 20.303125 | 1.108849 | 9.82% | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain-raw | reverse | 5 | 63,816 | 3,200 | 22.515355 | 20.313645 | 1.109267 | 9.85% | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-preserved | forward | 5 | 63,800 | 3,200 | 22.445145 | 20.325854 | 1.104549 | 9.47% | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-preserved | reverse | 5 | 63,800 | 3,200 | 22.437917 | 20.318105 | 1.104639 | 9.47% | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-preserved-raw | forward | 5 | 63,816 | 3,200 | 22.455167 | 20.310875 | 1.107343 | 9.69% | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-preserved-raw | reverse | 5 | 63,816 | 3,200 | 22.524917 | 20.384813 | 1.104650 | 9.47% | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain | forward | 81 | 63,800 | 3,200 | 22.439792 | 20.334146 | 1.105437 | 9.54% | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | 81 | 63,800 | 3,200 | 22.447979 | 20.361208 | 1.104388 | 9.45% | {'roc': [], 'libdeflate': []} |

The small-page variants are retained for repair if a required win is lost. Actual register weights and the prior preserved-register preference are tested both before and after fresh actual-count machine layouts. The data saving is separate from encoder text. The 64-byte-page representation uses 3,200 B versus 65,536 B of data, while its final encoder text is 63,800 B, 16 B above the previous default. The larger-page alternative uses 40,976 B of data.

## Complete builds

Twelve balanced serial orders, six actors, equally prebuilt compilers and fixed support. Original source through final executable linking; compiler construction and strip separate. No CPU-heavy work overlaps primary runtime or complete-build clocks.

| Actor | Source through final link s | Strip s | Stripped executable B |
|---|---:|---:|---:|
| mech-control-reference | 2.210819 | 0.011171 | 276,072 |
| mech-new-disabled | 2.213911 | 0.011139 | 276,072 |
| mech-pages-6-sqrt-plain | 2.212942 | 0.011147 | 210,024 |
| mech-pages-12 | 2.212153 | 0.011245 | 259,560 |
| roc | 2.989513 | 0.011032 | 191,912 |
| libdeflate | 0.482922 | 0.010894 | 155,752 |

## Reproduce and verify

```sh
python3 build_compiler.py /tmp/mech-code-page-compiler
python3 reproduce.py /tmp/mech-code-page-compiler/release/compile_profile /tmp/mech-code-page-control --role control
python3 reproduce.py /tmp/mech-code-page-compiler/release/compile_profile /tmp/mech-code-page-candidate --role pages-6-sqrt-plain --checked
python3 verify.py
```

All source alternatives reproduce exact objects, full metadata and bytecode in normal and checked mode. Per role: 162 success/output/alias/resource observations, six checked failures, twelve injected failure/recovery pairs and 4,736-B stack under 5,280 B. The verifier recomputes every actual lookup value, source identities, native counters, raw runtime observations, complete-build orders and 486 independently inflated deployed outputs. Earlier failed/interrupted build attempts are retained; final V3 compiler/tests pass. Construction timings are separate and are not an isolated compiler-bootstrap comparison.

[All timings](PARITY.md) · [Recipes](recipes.json) · [Verification totals](verification.json) · [Raw archive manifest](archives.json)

## Source alternatives

| Role | Text B | Lookup data B | Stack B |
|---|---:|---:|---:|
| control-raw | 63,800 | 65,536 | 4,736 |
| control | 63,784 | 65,536 | 4,736 |
| pages-12 | 63,800 | 40,976 | 4,736 |
| pages-12-raw | 63,816 | 40,976 | 4,736 |
| pages-5-raw | 63,816 | 3,232 | 4,736 |
| pages-6 | 63,800 | 3,200 | 4,736 |
| pages-6-linear-plain | 63,800 | 3,200 | 4,736 |
| pages-6-linear-plain-raw | 63,816 | 3,200 | 4,736 |
| pages-6-linear-preserved | 63,800 | 3,200 | 4,736 |
| pages-6-linear-preserved-raw | 63,816 | 3,200 | 4,736 |
| pages-6-raw | 63,816 | 3,200 | 4,736 |
| pages-6-sqrt-plain | 63,800 | 3,200 | 4,736 |
| pages-6-sqrt-plain-raw | 63,816 | 3,200 | 4,736 |
| pages-6-sqrt-preserved | 63,800 | 3,200 | 4,736 |
| pages-6-sqrt-preserved-raw | 63,816 | 3,200 | 4,736 |
| pages-7-raw | 63,816 | 4,352 | 4,736 |
| pages-8-raw | 63,816 | 6,912 | 4,736 |
