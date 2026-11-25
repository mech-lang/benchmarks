@codex review

Review `c2139f6f13407e2c6615fb4a092ae834ed109459` against `82bae670a21f71c43725e8815c9f18ef21dff774`.

Recognize the checked U32 insertion recurrence by matching its complete control flow and typed memory effects. When the last consumed gap is one, the native sort produces the same ascending prefix from the same initialized private view. The original completion block publishes its result.

The runtime groups a checked narrow range by its high key when the input already orders the low key. A bounded temporary stack buffer preserves that order inside each group. Other admitted inputs use the standard unsigned sort, and other gap patterns continue through the original phase.

### Runtime and correctness

The balanced run measured 78/81 libdeflate wins forward and 78/81 reverse, with 78/81 in both orders. All previously protected cases held. All 81 cases beat the independent reference in each order.
The fixed-cohort mean positive slowdown fell from 1.572161% to 1.178780%, an improvement of 0.393381 percentage points. The maximum paired deficit was 9.110443%, and the mean using each case’s slower order was 1.206857%.

| Case | Control µs F / R | Candidate µs F / R | libdeflate µs F / R | Candidate gap F / R | Paired gap before → after | Contribution pp before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix-natural-1024` | 64.42 / 64.46 | 64.04 / 64.12 | 58.92 / 58.96 | +8.988% / +9.148% | +9.699% → +9.068% | 0.538827 → 0.503777 |
| `reymont-prefix-1024` | 64.50 / 64.50 | 64.12 / 64.12 | 59.00 / 58.92 | +9.023% / +9.198% | +9.695% → +9.110% | 0.538593 → 0.506136 |
| `prefix-random-4096` | 79.96 / 80.79 | 77.38 / 76.83 | 75.56 / 75.65 | +3.377% / +2.704% | +6.750% → +3.040% | 0.375008 → 0.168867 |
| `prefix-random-8192` | 125.02 / 127.21 | 120.40 / 121.19 | 124.19 / 123.71 | -2.828% / -1.484% | +2.155% → -2.158% | 0.119733 → 0.000000 |
| `prefix-random-16384` | 221.54 / 224.94 | 214.85 / 216.10 | 235.25 / 234.90 | -8.531% / -7.752% | -4.889% → -8.142% | 0.000000 → 0.000000 |
| `16384-distribution-change` | 484.02 / 482.02 | 473.81 / 468.96 | 487.21 / 485.96 | -3.245% / -2.985% | -1.140% → -3.115% | 0.000000 → 0.000000 |
| `prefix-random-33027` | 503.08 / 507.96 | 490.60 / 496.13 | 533.00 / 532.85 | -8.377% / -6.872% | -5.194% → -7.627% | 0.000000 → 0.000000 |
| `prefix-random-32767` | 487.65 / 486.21 | 474.81 / 474.81 | 521.75 / 517.85 | -8.983% / -8.301% | -6.361% → -8.642% | 0.000000 → 0.000000 |
| `random-32769` | 498.12 / 500.13 | 487.65 / 485.71 | 526.44 / 526.29 | -7.600% / -7.665% | -5.166% → -7.633% | 0.000000 → 0.000000 |
| `prefix-random-32769` | 495.08 / 501.10 | 482.85 / 489.21 | 527.42 / 526.69 | -8.499% / -7.319% | -5.477% → -7.911% | 0.000000 → 0.000000 |
| `prefix-random-32768` | 484.42 / 485.71 | 471.81 / 473.67 | 516.81 / 518.40 | -8.961% / -8.519% | -6.396% → -8.741% | 0.000000 → 0.000000 |
| `heldout-random-65537` | 1,103.52 / 1,108.50 | 1,092.67 / 1,089.60 | 1,149.29 / 1,150.44 | -5.360% / -5.218% | -3.896% → -5.289% | 0.000000 → 0.000000 |
| `prefix-random-65535` | 1,101.40 / 1,104.79 | 1,085.02 / 1,087.27 | 1,159.35 / 1,163.31 | -6.722% / -6.882% | -5.289% → -6.802% | 0.000000 → 0.000000 |
| `prefix-random-65537` | 1,107.88 / 1,116.48 | 1,093.71 / 1,095.83 | 1,169.83 / 1,172.60 | -6.853% / -6.575% | -5.274% → -6.714% | 0.000000 → 0.000000 |
| `prefix-random-65536` | 1,097.69 / 1,101.50 | 1,083.96 / 1,085.81 | 1,159.38 / 1,165.19 | -7.133% / -6.845% | -5.510% → -6.989% | 0.000000 → 0.000000 |
| `prefix-random-131072` | 2,293.98 / 2,300.81 | 2,275.65 / 2,283.04 | 2,473.21 / 2,474.79 | -8.147% / -7.952% | -7.266% → -8.049% | 0.000000 → 0.000000 |
| `prefix-random-262144` | 4,691.02 / 4,693.81 | 4,682.48 / 4,669.90 | 5,056.83 / 5,056.60 | -7.603% / -7.700% | -7.285% → -7.651% | 0.000000 → 0.000000 |
| `prefix-random-1048576` | 18,547.40 / 18,552.88 | 18,489.79 / 18,488.27 | 20,348.12 / 20,324.54 | -9.142% / -9.038% | -8.699% → -9.090% | 0.000000 → 0.000000 |

All 23 native runtime tests passed at each of the four supported inline owner counts. The focused compiler test also accepts the exact recurrence and rejects six changes to its observable semantics. Exact native gates covered 162 output and alias checks, six named errors and 12 same-process recoveries. The linked C harness passed 324 deployment smokes.

### Artifact binding

- Encoder text is 65,576 B, lookup data 65,536 B, const data 80,064 B, and the stripped executable 291,768 B. Peak stack is 5,184 B.
- Codec source SHA-256 `653597f08f889908c48610e90aa65e94a77847fb34500d0cc3a046f83cd3d299`.
- Canonical bytecode SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.
- Encoder object SHA-256 `fdf96d5ba3fc2b03573eb0ccf8a2c056ff70afbc0a2e50fcd3bfb369e8763e04`.
- Bound worker SHA-256 `83e1905a4b5ad1383d35dcba3e45df0e6921e268b1c0b0a821acc0eaafacfa2c`.
- Full timing result SHA-256 `ba54a5ad1c41975b442be9c80d029f009b2071e262ab30d2804f8600fae199b2`.
- Timing verification SHA-256 `bf9ebec96a89b0a2486173a057e93135e3d7712a4d61488df8e222e57d1694b8`.
- Candidate runtime library SHA-256 `46b1dd6fe9b6c4a7accc2986b52558a7f7a61f6bcd848ba9c609f744b6d1bca3`.
- Static deployment support SHA-256 `aef7f421a978c3161a1eb463c30889feb83e1478ac59bceb14ddc453925dedeb`.
- Re-emission and runtime rebuild reproduced the exact timed artifacts and workers.

### Complete source-through-link builds

This comparison uses prebuilt compilers and each actor’s verified prebuilt host support.

- Control source 2.168693 s link 0.037423 s source_through_link 2.209300 s strip 0.010855 s source_through_strip 2.220265 s.
- Candidate source 2.168933 s link 0.036586 s source_through_link 2.206449 s strip 0.010767 s source_through_strip 2.217237 s.
- libdeflate source 0.446514 s link 0.035028 s source_through_link 0.481683 s strip 0.011048 s source_through_strip 0.492838 s.
- Independent reference source 2.957202 s link 0.035333 s source_through_link 2.992867 s strip 0.010712 s source_through_strip 3.003992 s.
