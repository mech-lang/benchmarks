@codex review

Please review commit `25de11f6c5c5d9eec524d14a64b0e69ba039479c`.

The seeded packed tally computes one descending address for sixteen candidate literals. It checks the first four before loading and checking the remaining twelve packed records. A mixed tail resumes the checked path after the verified prefix. The full-batch admission bounds both the packed records and the source-byte load.

I compared the two prebuilt compilers with the preceding recipe and `MECH_COMPACT_SEEDED_HISTOGRAM=1` on Apple M1. The matched runs used all 81 original cases with 96 balanced blocks per case in each order, against libdeflate 1.26 level 12. Control won 66 cases in each order. The candidate won 72 forward and 70 reverse. Every protected win held. The three random prefixes at 65,535 B, 65,536 B and 65,537 B and the 65,537 B held-out random case won both orders.

The fixed 18-case mean positive gap fell from 6.745% to 5.604%, a 1.142 percentage-point reduction. The mean using each case’s slower order fell from 7.057% to 5.984%. The maximum paired gap moved from 23.998% to 24.014%. The verifier recomputed 1,965,312 runtime observations. Gaps below are paired ratios and elapsed times are the separate per-order medians.

| Case | Control gap F / R | Candidate gap F / R | Control µs F / R | Candidate µs F / R | libdeflate µs F / R | Mean contribution improvement (pp) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix-random-1048576` | -3.622% / -2.726% | -5.454% / -4.443% | 19608.13 / 19582.48 | 19235.94 / 19209.75 | 20342.31 / 20332.65 | +0.0000 |
| `prefix-random-262144` | -1.671% / -1.880% | -3.539% / -3.874% | 4974.19 / 4953.48 | 4875.56 / 4855.04 | 5052.87 / 5049.83 | +0.0000 |
| `prefix-random-131072` | -1.137% / -1.931% | -3.126% / -3.756% | 2443.33 / 2427.92 | 2398.96 / 2384.29 | 2472.10 / 2478.33 | +0.0000 |
| `prefix-random-65535` | +1.093% / +0.963% | -1.147% / -1.207% | 1172.69 / 1171.63 | 1151.94 / 1148.35 | 1158.46 / 1159.98 | +0.0571 |
| `prefix-random-65536` | +1.013% / +0.808% | -0.950% / -1.500% | 1173.98 / 1169.15 | 1150.83 / 1145.63 | 1158.38 / 1160.31 | +0.0506 |
| `prefix-random-65537` | +1.492% / +0.922% | -0.672% / -1.158% | 1189.67 / 1180.00 | 1164.44 / 1159.13 | 1167.35 / 1171.25 | +0.0670 |
| `heldout-random-65537` | +1.548% / +1.555% | -0.787% / -0.590% | 1166.44 / 1167.38 | 1142.08 / 1145.25 | 1147.25 / 1150.33 | +0.0862 |
| `prefix-random-32768` | +2.326% / +2.622% | -0.268% / +0.729% | 530.00 / 532.19 | 515.27 / 522.90 | 516.35 / 517.35 | +0.1247 |
| `prefix-random-32767` | +2.178% / +2.928% | -0.032% / +1.007% | 530.29 / 532.67 | 517.90 / 523.08 | 517.46 / 516.90 | +0.1148 |
| `random-32769` | +2.499% / +2.997% | +0.062% / +1.063% | 540.02 / 546.10 | 527.15 / 536.27 | 525.69 / 530.31 | +0.1214 |
| `prefix-random-33027` | +3.303% / +3.262% | +0.822% / +1.261% | 549.02 / 551.15 | 536.27 / 539.94 | 530.40 / 532.65 | +0.1245 |
| `prefix-random-32769` | +3.908% / +3.234% | +1.940% / +1.432% | 553.27 / 545.40 | 542.96 / 535.35 | 529.75 / 527.54 | +0.1047 |
| `prefix-random-16384` | +9.102% / +9.302% | +5.769% / +7.413% | 259.27 / 258.54 | 250.87 / 253.27 | 237.38 / 236.73 | +0.1452 |
| `16384-distribution-change` | +10.948% / +13.220% | +9.745% / +11.576% | 534.17 / 542.71 | 529.90 / 536.21 | 481.81 / 482.54 | +0.0790 |
| `prefix-random-8192` | +18.764% / +19.172% | +17.653% / +16.997% | 148.33 / 147.88 | 146.42 / 145.67 | 124.77 / 125.00 | +0.0913 |
| `prefix-natural-1024` | +18.268% / +18.192% | +18.110% / +18.176% | 69.38 / 69.71 | 69.42 / 69.67 | 58.96 / 59.13 | +0.0048 |
| `reymont-prefix-1024` | +21.117% / +18.136% | +22.055% / +18.247% | 69.79 / 69.50 | 69.63 / 69.58 | 59.00 / 59.08 | -0.0288 |
| `prefix-random-4096` | +25.039% / +22.967% | +24.838% / +23.196% | 95.19 / 92.63 | 95.17 / 92.98 | 76.06 / 75.52 | -0.0009 |

The checker reproduced the artifacts, and six altered plans used the checked path. The linked gates passed 162 exact output and alias observations, six named errors and 12 recoveries. The guarded-end probe covered all 16 tail lengths and 256 deliberate lane mismatches. Peak stack measured 4,720 B. Encoder text grew from 64,568 B to 64,728 B. Lookup data measured 3,200 B, the constants section 17,728 B and the stripped executable 210,024 B.

The 32 matched source-through-link builds measured medians of 2.185 s for the control, 2.190 s for the candidate and 0.482 s for libdeflate. Deployment checks independently inflated 324 outputs.