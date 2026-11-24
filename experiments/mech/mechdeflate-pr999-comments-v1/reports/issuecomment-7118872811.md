@codex review

Review `390b6217a4ba0a1cba36d18c4bc0b754a1d2e15e` against `c2139f6f13407e2c6615fb4a092ae834ed109459`.

Verify the typed packed-tree recurrence, including all loads, writes and state transitions. A single entry check proves the cursor, index and arithmetic limits for the loop. The bounded path emits the same operations directly and otherwise preserves the original checked body.

After eight successful contiguous pairs of literal appends, group four visits in the existing disjoint writable span. Every group checks its own headers before a write. A rejected group enters the paired loop at the same state, preserving the original checked transition order.

### Runtime and correctness

The balanced run measured 79/81 libdeflate wins forward and 79/81 reverse, with 79/81 in both orders. All previously protected cases held. All 81 cases beat the independent reference in each order.
The fixed-cohort mean positive slowdown fell from 1.109165% to 0.778492%, an improvement of 0.330672 percentage points. The maximum paired deficit was 7.055972%, and the mean using each case’s slower order was 0.794641%.

| Case | Control µs F / R | Candidate µs F / R | libdeflate µs F / R | Candidate gap F / R | Paired gap before → after | Contribution pp before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `reymont-prefix-1024` | 64.12 / 64.04 | 63.12 / 62.83 | 58.96 / 59.00 | +7.223% / +6.889% | +9.089% → +7.056% | 0.504952 → 0.391998 |
| `prefix-natural-1024` | 64.08 / 64.04 | 62.96 / 62.88 | 58.92 / 59.00 | +7.080% / +6.834% | +8.948% → +6.957% | 0.497106 → 0.386494 |
| `prefix-random-4096` | 77.56 / 75.44 | 75.10 / 73.85 | 76.42 / 75.83 | -0.332% / -1.318% | +1.928% → -0.826% | 0.107107 → 0.000000 |
| `prefix-random-8192` | 117.85 / 120.44 | 114.58 / 115.00 | 124.81 / 123.87 | -8.021% / -6.134% | -3.978% → -7.082% | 0.000000 → 0.000000 |
| `prefix-random-16384` | 217.12 / 218.96 | 213.87 / 213.25 | 235.94 / 234.50 | -9.235% / -8.896% | -6.854% → -9.065% | 0.000000 → 0.000000 |
| `16384-distribution-change` | 465.44 / 470.65 | 471.38 / 476.83 | 482.96 / 482.98 | -2.697% / -1.376% | -3.284% → -2.039% | 0.000000 → 0.000000 |
| `prefix-random-33027` | 486.85 / 488.88 | 479.38 / 479.79 | 530.77 / 532.35 | -10.191% / -10.076% | -8.305% → -10.133% | 0.000000 → 0.000000 |
| `prefix-random-32767` | 470.65 / 514.31 | 461.60 / 500.90 | 517.42 / 554.10 | -11.103% / -4.619% | -7.056% → -7.918% | 0.000000 → 0.000000 |
| `random-32769` | 480.00 / 481.92 | 468.69 / 473.35 | 524.02 / 526.27 | -10.727% / -10.032% | -8.555% → -10.380% | 0.000000 → 0.000000 |
| `prefix-random-32769` | 479.81 / 481.90 | 472.85 / 475.94 | 525.81 / 526.46 | -10.271% / -9.731% | -8.501% → -10.001% | 0.000000 → 0.000000 |
| `prefix-random-32768` | 467.94 / 467.02 | 460.98 / 459.71 | 516.85 / 516.19 | -10.808% / -11.096% | -9.551% → -10.952% | 0.000000 → 0.000000 |
| `heldout-random-65537` | 1,079.90 / 1,082.40 | 1,061.31 / 1,063.67 | 1,151.19 / 1,151.33 | -7.823% / -7.698% | -5.983% → -7.761% | 0.000000 → 0.000000 |
| `prefix-random-65535` | 1,075.94 / 1,078.23 | 1,059.50 / 1,055.29 | 1,160.85 / 1,163.35 | -8.917% / -9.243% | -7.397% → -9.080% | 0.000000 → 0.000000 |
| `prefix-random-65537` | 1,079.98 / 1,088.08 | 1,064.08 / 1,066.48 | 1,169.46 / 1,173.65 | -9.228% / -9.007% | -7.445% → -9.118% | 0.000000 → 0.000000 |
| `prefix-random-65536` | 1,067.67 / 1,075.29 | 1,049.52 / 1,055.62 | 1,160.25 / 1,163.83 | -9.557% / -9.283% | -7.732% → -9.420% | 0.000000 → 0.000000 |
| `prefix-random-131072` | 2,259.46 / 2,267.02 | 2,217.21 / 2,227.60 | 2,474.12 / 2,475.35 | -10.367% / -10.006% | -8.470% → -10.187% | 0.000000 → 0.000000 |
| `prefix-random-262144` | 4,660.02 / 4,668.50 | 4,564.81 / 4,563.00 | 5,056.73 / 5,057.90 | -9.810% / -9.776% | -7.781% → -9.793% | 0.000000 → 0.000000 |
| `prefix-random-1048576` | 18,476.21 / 18,476.90 | 18,170.42 / 18,168.71 | 20,336.23 / 20,346.33 | -10.621% / -10.608% | -9.112% → -10.615% | 0.000000 → 0.000000 |

The native tree differential covered 8,448 bounded and fallback calls. Four changes to the recorded recurrence were declined. The literal-append differential covered 59,820 calls including the promotion boundary, selector failures, wrapping costs and exact aliases.
All 23 native runtime tests passed for each of four inline owner counts. Exact native gates covered 162 output and alias checks, six named errors and 12 same-process recoveries. The linked C harness passed 324 deployment smokes.

### Artifact binding

- Encoder text is 66,024 B, lookup data 65,536 B, const data 80,064 B, and the stripped executable 291,768 B. Peak stack is 5,184 B.
- Codec source SHA-256 `653597f08f889908c48610e90aa65e94a77847fb34500d0cc3a046f83cd3d299`.
- Canonical bytecode SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.
- Encoder object SHA-256 `7bf0d897e8bc7afd195f3b0499961dbc66b2c403d2e514c2be00bb86d1810cd8`.
- Bound worker SHA-256 `17f0198bb1e1b375872cedd2c334796bda5ddd8f3f7ea080370401772733f87d`.
- Full timing result SHA-256 `306b4d57b20d1088ca749418fa0d7ddb35ea18edc9e9089cc968e5536724b68d`.
- Timing verification SHA-256 `a1a7cc6465a4ba4c15bbea7a748fd184ea2047467e721a31a87f692f1e62e412`.
- Candidate runtime library SHA-256 `46b1dd6fe9b6c4a7accc2986b52558a7f7a61f6bcd848ba9c609f744b6d1bca3`.
- Static deployment support SHA-256 `b900000378567cd8717c9029438c6be539086412b0f0c6e6d181ba556df6d0c5`.
- Re-emission and runtime rebuild reproduced the exact timed artifacts and workers.

### Complete source-through-link builds

This comparison uses prebuilt compilers and each actor’s verified prebuilt host support.

- Control source 2.167568 s link 0.036403 s source_through_link 2.204179 s strip 0.010793 s source_through_strip 2.214975 s.
- Candidate source 2.164988 s link 0.044191 s source_through_link 2.210549 s strip 0.010719 s source_through_strip 2.221446 s.
- libdeflate source 0.447463 s link 0.034527 s source_through_link 0.482128 s strip 0.010642 s source_through_strip 0.492979 s.
- Independent reference source 2.959504 s link 0.034980 s source_through_link 2.994804 s strip 0.010621 s source_through_strip 3.005556 s.
