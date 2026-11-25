@codex review

Review `c119153e7c543e8350a9628c7d3a33e9e91fc9e5` against `390b6217a4ba0a1cba36d18c4bc0b754a1d2e15e`.

Verify both checked pricing recurrences before selecting their bounded native routes. The blend weights cover eight parts. The vector path distributes the division across quotients and restores the exact remainder, and the full-default case writes four values per visit.

The code-price loop reuses a lookup for four identical packed entries and reads four consecutive low symbols together when all four addresses are admitted. The checked scalar branch handles other groups. The normal checked entry remains available for unsupported spans, overlaps and arithmetic.

### Runtime and correctness

The balanced run measured 79/81 libdeflate wins forward and 79/81 reverse, with 79/81 in both orders. All previously protected cases held. All 81 cases beat the independent reference in each order.
The fixed-cohort mean positive slowdown fell from 0.768786% to 0.212690%, an improvement of 0.556096 percentage points. The maximum paired deficit was 1.953565%, and the mean using each case’s slower order was 0.222626%.

| Case | Control µs F / R | Candidate µs F / R | libdeflate µs F / R | Candidate gap F / R | Paired gap before → after | Contribution pp before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix-natural-1024` | 62.96 / 62.79 | 59.83 / 59.88 | 58.92 / 58.96 | +1.725% / +2.025% | +6.934% → +1.875% | 0.385247 → 0.104159 |
| `reymont-prefix-1024` | 63.00 / 62.71 | 59.92 / 59.79 | 58.96 / 58.96 | +1.925% / +1.982% | +6.904% → +1.954% | 0.383539 → 0.108531 |
| `prefix-random-4096` | 74.71 / 73.88 | 71.10 / 72.65 | 75.54 / 75.77 | -5.011% / -4.037% | -1.114% → -4.525% | 0.000000 → 0.000000 |
| `prefix-random-8192` | 114.23 / 116.27 | 113.44 / 111.58 | 124.23 / 124.46 | -8.341% / -9.787% | -7.053% → -9.067% | 0.000000 → 0.000000 |
| `prefix-random-16384` | 214.38 / 209.71 | 208.69 / 209.04 | 235.73 / 236.62 | -11.202% / -11.684% | -10.181% → -11.443% | 0.000000 → 0.000000 |
| `16384-distribution-change` | 471.04 / 475.52 | 469.19 / 466.90 | 481.94 / 483.67 | -3.488% / -3.404% | -2.074% → -3.446% | 0.000000 → 0.000000 |
| `prefix-random-33027` | 483.29 / 480.98 | 481.52 / 476.19 | 530.56 / 532.77 | -9.502% / -10.395% | -9.425% → -9.950% | 0.000000 → 0.000000 |
| `prefix-random-32767` | 463.29 / 458.35 | 464.29 / 457.00 | 515.98 / 517.52 | -10.193% / -11.582% | -10.777% → -10.890% | 0.000000 → 0.000000 |
| `random-32769` | 478.73 / 472.00 | 475.77 / 469.58 | 525.15 / 523.88 | -9.740% / -10.243% | -9.393% → -9.992% | 0.000000 → 0.000000 |
| `prefix-random-32769` | 476.88 / 472.69 | 475.56 / 470.35 | 525.04 / 527.31 | -9.690% / -10.928% | -10.026% → -10.311% | 0.000000 → 0.000000 |
| `prefix-random-32768` | 465.42 / 458.83 | 464.12 / 457.33 | 515.96 / 519.12 | -10.140% / -11.733% | -10.561% → -10.940% | 0.000000 → 0.000000 |
| `heldout-random-65537` | 1,074.79 / 1,062.90 | 1,069.12 / 1,064.54 | 1,148.69 / 1,150.54 | -7.314% / -7.713% | -7.142% → -7.513% | 0.000000 → 0.000000 |
| `prefix-random-65535` | 1,068.88 / 1,058.08 | 1,063.60 / 1,053.04 | 1,160.63 / 1,162.81 | -8.391% / -9.423% | -8.585% → -8.908% | 0.000000 → 0.000000 |
| `prefix-random-65537` | 1,076.69 / 1,062.46 | 1,076.06 / 1,062.77 | 1,168.62 / 1,175.73 | -8.252% / -9.575% | -8.690% → -8.916% | 0.000000 → 0.000000 |
| `prefix-random-65536` | 1,065.25 / 1,054.40 | 1,066.40 / 1,052.83 | 1,160.73 / 1,162.73 | -8.499% / -9.576% | -8.965% → -9.039% | 0.000000 → 0.000000 |
| `prefix-random-131072` | 2,239.67 / 2,226.54 | 2,237.10 / 2,223.48 | 2,479.54 / 2,476.02 | -9.720% / -10.195% | -9.824% → -9.958% | 0.000000 → 0.000000 |
| `prefix-random-262144` | 4,616.81 / 4,568.94 | 4,623.90 / 4,565.50 | 5,091.81 / 5,055.69 | -9.173% / -9.615% | -9.083% → -9.395% | 0.000000 → 0.000000 |
| `prefix-random-1048576` | 18,200.46 / 18,181.33 | 18,183.69 / 18,181.62 | 20,347.48 / 20,350.44 | -10.682% / -10.568% | -10.579% → -10.625% | 0.000000 → 0.000000 |

The blend and code-price differentials covered 13,207 and 12,974 native calls, including boundary positions, overlapping views, overflow and preserved checked errors. Each witness declined four modifications of its recorded recurrence.
All 23 native runtime tests passed for each of four inline owner counts. Exact native gates covered 162 output and alias checks, six named errors and 12 same-process recoveries. The linked C harness passed 324 deployment smokes.

### Artifact binding

- Encoder text is 66,888 B, lookup data 65,536 B, const data 80,064 B, and the stripped executable 291,768 B. Peak stack is 5,184 B.
- Codec source SHA-256 `653597f08f889908c48610e90aa65e94a77847fb34500d0cc3a046f83cd3d299`.
- Canonical bytecode SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.
- Encoder object SHA-256 `04e31242e6f56ad663c33f766040d973d3f3afa37b772446abb798141460598d`.
- Bound worker SHA-256 `ad4d7b98fa244dd85d78f35cfe6379d8a2ca4c883fd6439e87bd6ce57a25d241`.
- Full timing result SHA-256 `2fea00f53e83602231b7b1d169f7b35f313e98cccf2499c1047b7ca1b7f3250a`.
- Timing verification SHA-256 `3cc16d2fed4fd34d0286e63a44749451f10cdb874932737d40cf0716d880b16c`.
- Candidate runtime library SHA-256 `46b1dd6fe9b6c4a7accc2986b52558a7f7a61f6bcd848ba9c609f744b6d1bca3`.
- Static deployment support SHA-256 `c05fdf420fcc95e477f12f110c4ee4f23cd0c31833b4e6e5986d123639104d75`.
- Re-emission and runtime rebuild reproduced the exact timed artifacts and workers.

### Complete source-through-link builds

This comparison uses prebuilt compilers and each actor’s verified prebuilt host support.

- Control source 2.163935 s link 0.037010 s source_through_link 2.202358 s strip 0.010853 s source_through_strip 2.213378 s.
- Candidate source 2.168827 s link 0.037827 s source_through_link 2.209206 s strip 0.010818 s source_through_strip 2.220254 s.
- libdeflate source 0.447541 s link 0.034638 s source_through_link 0.482496 s strip 0.010579 s source_through_strip 0.493301 s.
- Independent reference source 2.951320 s link 0.034782 s source_through_link 2.986491 s strip 0.010805 s source_through_strip 2.997319 s.
