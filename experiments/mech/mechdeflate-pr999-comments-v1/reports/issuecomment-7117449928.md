@codex review

Review `82bae670a21f71c43725e8815c9f18ef21dff774` against `f3f5cc87fea0b74c973839df90acde00ace4a930`.

Reuse a successful fixed U32 numeric phase within the current invocation after matching the operator, scalar inputs, view geometry and every initialized input word. The compiler requires one exclusive fixed view and a direct result. A hit copies the previous values into the current view and preserves its owner. Any other input still runs the admitted source phase.

The cache allocates two bounded entries on demand. Failed visits leave the cache empty for that operator. The runtime releases the cache with its invocation heap. Physical cache storage and logical array requests are tracked independently.

### Runtime and correctness

The balanced run measured 77/81 libdeflate wins forward and 77/81 reverse, with 77/81 in both orders. All previously protected cases held. All 81 cases beat the independent reference in each order.
The fixed-cohort mean positive slowdown fell from 1.986376% to 1.655809%, an improvement of 0.330567 percentage points. The maximum paired deficit was 9.942133%, and the mean using each case’s slower order was 1.789863%.

| Case | Control µs F / R | Candidate µs F / R | libdeflate µs F / R | Candidate gap F / R | Paired gap before → after | Contribution pp before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix-random-4096` | 84.92 / 83.48 | 82.75 / 80.06 | 76.42 / 76.50 | +8.751% / +5.995% | +11.766% → +7.364% | 0.653692 → 0.409117 |
| `prefix-natural-1024` | 64.62 / 64.67 | 64.50 / 64.54 | 58.96 / 59.00 | +9.855% / +9.860% | +10.126% → +9.858% | 0.562570 → 0.547644 |
| `reymont-prefix-1024` | 64.67 / 64.54 | 64.67 / 64.50 | 59.00 / 59.00 | +10.102% / +9.783% | +9.981% → +9.942% | 0.554519 → 0.552341 |
| `prefix-random-8192` | 129.83 / 127.65 | 128.38 / 125.58 | 124.48 / 124.50 | +3.505% / +1.784% | +3.881% → +2.641% | 0.215595 → 0.146708 |
| `prefix-random-16384` | 227.94 / 228.92 | 226.29 / 226.44 | 236.71 / 236.50 | -4.150% / -4.403% | -3.220% → -4.277% | 0.000000 → 0.000000 |
| `16384-distribution-change` | 474.19 / 479.85 | 477.69 / 478.79 | 483.00 / 485.98 | -1.250% / -1.957% | -1.570% → -1.604% | 0.000000 → 0.000000 |
| `prefix-random-33027` | 513.44 / 513.56 | 507.06 / 508.12 | 533.77 / 533.96 | -5.252% / -4.825% | -4.053% → -5.039% | 0.000000 → 0.000000 |
| `prefix-random-32767` | 495.06 / 494.79 | 488.38 / 488.54 | 519.29 / 518.46 | -6.367% / -5.802% | -4.903% → -6.085% | 0.000000 → 0.000000 |
| `random-32769` | 509.60 / 507.29 | 504.23 / 501.77 | 527.83 / 527.08 | -4.596% / -4.890% | -3.961% → -4.743% | 0.000000 → 0.000000 |
| `prefix-random-32769` | 505.42 / 507.17 | 499.94 / 498.67 | 529.19 / 527.96 | -5.659% / -5.472% | -4.433% → -5.565% | 0.000000 → 0.000000 |
| `prefix-random-32768` | 492.65 / 492.48 | 487.62 / 484.58 | 519.00 / 518.31 | -6.150% / -6.594% | -5.355% → -6.373% | 0.000000 → 0.000000 |
| `heldout-random-65537` | 1,101.81 / 1,107.90 | 1,102.69 / 1,106.27 | 1,148.71 / 1,150.81 | -4.353% / -4.158% | -3.896% → -4.255% | 0.000000 → 0.000000 |
| `prefix-random-65535` | 1,103.71 / 1,109.56 | 1,098.60 / 1,102.62 | 1,161.56 / 1,162.46 | -5.895% / -5.285% | -4.810% → -5.590% | 0.000000 → 0.000000 |
| `prefix-random-65537` | 1,117.71 / 1,117.00 | 1,106.58 / 1,108.40 | 1,170.50 / 1,172.60 | -5.684% / -5.761% | -4.783% → -5.723% | 0.000000 → 0.000000 |
| `prefix-random-65536` | 1,102.37 / 1,106.90 | 1,098.21 / 1,098.15 | 1,162.02 / 1,162.06 | -6.017% / -5.684% | -5.185% → -5.850% | 0.000000 → 0.000000 |
| `prefix-random-131072` | 2,296.04 / 2,297.52 | 2,289.88 / 2,293.81 | 2,471.56 / 2,475.02 | -7.553% / -7.346% | -7.245% → -7.450% | 0.000000 → 0.000000 |
| `prefix-random-262144` | 4,699.56 / 4,703.77 | 4,694.52 / 4,689.96 | 5,057.98 / 5,054.58 | -7.409% / -7.294% | -7.153% → -7.352% | 0.000000 → 0.000000 |
| `prefix-random-1048576` | 18,553.08 / 18,563.75 | 18,551.08 / 18,541.42 | 20,344.69 / 20,372.88 | -8.664% / -8.844% | -8.743% → -8.754% | 0.000000 → 0.000000 |

All 21 native runtime tests passed at each of the four supported inline owner counts. Exact native gates covered 162 output and alias checks, six named errors and 12 same-process recoveries. The linked C harness passed 324 deployment smokes.

### Artifact binding

- Encoder text is 65,544 B, lookup data 65,536 B, const data 80,064 B, and the stripped executable 274,952 B. Peak stack is 4,896 B.
- Codec source SHA-256 `653597f08f889908c48610e90aa65e94a77847fb34500d0cc3a046f83cd3d299`.
- Canonical bytecode SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.
- Encoder object SHA-256 `2b451466909cc1e385a7a67293234816e9397e69424ea715e6dcb8a9cc33fbcf`.
- Bound worker SHA-256 `4f5f487eb698ce977e9c9909fb87d3ded6481d3fb41183088e678882e369a4c9`.
- Full timing result SHA-256 `fb379640a14dc8c15ae7025411dc1dfb9c571fe03e412d7735c45fb8f0401c42`.
- Timing verification SHA-256 `60e6f8b78e6ca61e77c13d5e11cdbdd4cd765426c7314461d50e02cb76ddf030`.
- Candidate runtime library SHA-256 `6302dc159946369b568dd1aafb4734ee52e4bd2a806faa63dd4ba08a270a436e`.
- Static deployment support SHA-256 `ca0915321f4c4b7136b9313c737bf2b0b5407ecae7775cc8e351cdf41b2c85ce`.
- Re-emission and runtime rebuild reproduced the exact timed artifacts and workers.

### Complete source-through-link builds

This comparison uses prebuilt compilers and each actor’s verified prebuilt host support.

- Control source 2.168717 s link 0.036424 s source_through_link 2.205507 s strip 0.010626 s source_through_strip 2.216303 s.
- Candidate source 2.171521 s link 0.040435 s source_through_link 2.217861 s strip 0.010780 s source_through_strip 2.229385 s.
- libdeflate source 0.447289 s link 0.034663 s source_through_link 0.482261 s strip 0.010731 s source_through_strip 0.493047 s.
- Independent reference source 2.956817 s link 0.034438 s source_through_link 2.991471 s strip 0.010705 s source_through_strip 3.002419 s.
