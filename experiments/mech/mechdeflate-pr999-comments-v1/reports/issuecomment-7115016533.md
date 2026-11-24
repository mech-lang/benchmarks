@codex review

Review `eeac6ffd291474c3b0ad6226947518c1cec98e22` against `3d1b51a24040bd9aef7f8ac9850878c7e2e5a6f3`.

The compiler proves when an unsigned sum’s carry test is constant by checking both addends on every incoming edge. It also folds a zero high product when the operand bounds fit the full low word. The sum, product and checks whose inputs remain unbounded retain their existing semantics.

The release enables the proof for both equivalent preparations of each of the two affected pricing helpers. This keeps the selected entry points, the controller and every unrelated function’s bytes identical. The existing register and layout profiles are unchanged.

### Runtime and correctness

The 81-case run at 96 blocks per case and order held 77/81 against libdeflate and 81/81 against the independent reference in both orders. The matched mean positive slowdown over the fixed 18 cases fell from 2.167079% to 2.145186%, a reduction of 0.021894 percentage points.
The maximum paired deficit is 11.438627%. The average using the slower order of each case is 2.249489%.

| Case | Control µs F / R | Candidate µs F / R | libdeflate µs F / R | Candidate gap F / R | Paired gap before → after | Contribution pp before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix-random-4096` | 86.21 / 84.50 | 85.52 / 83.38 | 76.12 / 76.96 | +12.824% / +10.070% | +12.253% → +11.439% | 0.680705 → 0.635479 |
| `prefix-natural-1024` | 65.25 / 65.21 | 65.29 / 65.25 | 59.00 / 59.08 | +10.812% / +11.039% | +10.949% → +10.925% | 0.608293 → 0.606965 |
| `reymont-prefix-1024` | 65.38 / 65.12 | 65.46 / 65.25 | 59.00 / 59.06 | +11.303% / +11.116% | +10.922% → +11.209% | 0.606762 → 0.622743 |
| `prefix-random-8192` | 130.67 / 130.52 | 129.71 / 131.44 | 124.62 / 125.15 | +4.756% / +5.325% | +4.884% → +5.040% | 0.271319 → 0.279999 |
| `prefix-random-16384` | 235.19 / 231.54 | 232.27 / 230.77 | 236.69 / 237.60 | -1.839% / -3.052% | -1.575% → -2.448% | 0.000000 → 0.000000 |
| `16384-distribution-change` | 481.23 / 470.06 | 481.79 / 476.60 | 484.40 / 484.02 | -1.030% / -1.918% | -1.883% → -1.475% | 0.000000 → 0.000000 |
| `prefix-random-33027` | 515.62 / 507.29 | 514.50 / 505.96 | 533.35 / 534.31 | -3.956% / -5.556% | -4.512% → -4.760% | 0.000000 → 0.000000 |
| `prefix-random-32767` | 499.08 / 488.67 | 496.96 / 486.77 | 519.04 / 518.15 | -4.671% / -5.949% | -5.152% → -5.312% | 0.000000 → 0.000000 |
| `random-32769` | 507.48 / 502.23 | 508.56 / 502.96 | 527.40 / 529.44 | -4.098% / -5.363% | -4.670% → -4.733% | 0.000000 → 0.000000 |
| `prefix-random-32769` | 509.04 / 500.31 | 508.46 / 499.04 | 527.94 / 528.19 | -4.241% / -5.575% | -4.798% → -4.910% | 0.000000 → 0.000000 |
| `prefix-random-32768` | 498.83 / 490.02 | 497.33 / 489.46 | 519.52 / 519.81 | -4.867% / -5.580% | -5.179% → -5.224% | 0.000000 → 0.000000 |
| `heldout-random-65537` | 1,108.35 / 1,098.58 | 1,106.71 / 1,095.83 | 1,149.69 / 1,150.06 | -4.039% / -4.732% | -4.096% → -4.386% | 0.000000 → 0.000000 |
| `prefix-random-65535` | 1,109.94 / 1,100.46 | 1,107.54 / 1,099.50 | 1,160.77 / 1,163.29 | -5.055% / -5.602% | -4.996% → -5.329% | 0.000000 → 0.000000 |
| `prefix-random-65537` | 1,118.77 / 1,108.10 | 1,116.27 / 1,103.98 | 1,169.04 / 1,172.04 | -4.986% / -5.794% | -5.144% → -5.391% | 0.000000 → 0.000000 |
| `prefix-random-65536` | 1,106.69 / 1,099.96 | 1,103.58 / 1,094.71 | 1,161.52 / 1,164.00 | -5.264% / -6.113% | -5.229% → -5.690% | 0.000000 → 0.000000 |
| `prefix-random-131072` | 2,303.10 / 2,291.42 | 2,301.44 / 2,291.87 | 2,475.40 / 2,474.15 | -7.128% / -7.371% | -7.237% → -7.250% | 0.000000 → 0.000000 |
| `prefix-random-262144` | 4,702.06 / 4,688.23 | 4,698.85 / 4,688.58 | 5,058.77 / 5,052.69 | -7.343% / -7.216% | -7.202% → -7.280% | 0.000000 → 0.000000 |
| `prefix-random-1048576` | 18,573.42 / 18,559.88 | 18,579.06 / 18,560.25 | 20,357.90 / 20,320.90 | -8.763% / -8.615% | -8.636% → -8.689% | 0.000000 → 0.000000 |

The focused tests cover all four carry-comparison forms, exact-addend matching, and refusal when an incoming high-product operand is unbounded. The release passed 162 exact success and alias checks, six named errors, 12 same-process recoveries, and 324 deployment smokes.
On random 4 KiB, diagnostic instruction counts fell from 39,798 to 38,712 in one helper and from 24,856 to 24,310 in the other. Primary timings used the original uninstrumented workers.

### Artifact binding

- Encoder text is 65,464 B, lookup data 65,536 B, the whole const section 80,064 B, and the stripped executable 276,072 B. Peak stack is 4,864 B.
- Codec source SHA-256 is `653597f08f889908c48610e90aa65e94a77847fb34500d0cc3a046f83cd3d299`.
- Canonical bytecode SHA-256 is `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.
- Encoder object SHA-256 is `8aa71fb264e8e1f76cccaaea9c743b812a8e1817a1fc8b04085de10e68a34ddf`.
- Bound worker SHA-256 is `59aadabc840bebbf73fcc6e1c5c3cb6008a8dd4d2f7afb8ca178caa696773c3b`.
- Full timing result SHA-256 is `cfd0150d652e02e2b4dac2e879269f8786c79f75d6d87a9e8297c42855cf4d23`.
- Timing verification SHA-256 is `7515b998923a5824bef91abdbd1f37d484335c80106481db64697d9743b20bba`.
- Add `MECH_COMPACT_FOLD_PHASE_CHECKED_ARITHMETIC=mech_compact_numeric_5895;mech_compact_numeric_5895_vector;mech_compact_numeric_6633;mech_compact_numeric_6633_vector` to the previous release recipe. The release compiler reproduced both timed workers byte for byte.

### Complete builds

The timer starts at the original source and ends at the completed executable link. Both compilers and fixed host support are prebuilt for each actor.
- Control source 2.172524 s link 0.035868 s source_through_link 2.211565 s strip 0.010757 s source_through_strip 2.224079 s.
- Candidate source 2.174470 s link 0.037829 s source_through_link 2.214280 s strip 0.010853 s source_through_strip 2.225198 s.
- libdeflate source 0.447198 s link 0.034530 s source_through_link 0.481818 s strip 0.010775 s source_through_strip 0.492795 s.
- Independent reference source 2.955444 s link 0.035267 s source_through_link 2.991056 s strip 0.010767 s source_through_strip 3.002122 s.
