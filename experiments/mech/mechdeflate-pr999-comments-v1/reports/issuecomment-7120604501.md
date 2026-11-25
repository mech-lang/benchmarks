@codex review

Review `ac44d607b6dbf626ddc850c93b896390837afb09` against `c119153e7c543e8350a9628c7d3a33e9e91fc9e5`.

The native route compacts nonzero U32 frequencies into packed words in ascending symbol order. It proves both the zero-frequency and active-frequency loop paths against the original checked recurrence. Each grouped load and store must fit within disjoint source and destination spans.

Empty groups skip the write. A dense group packs four symbols with a vector store. Mixed groups write each nonzero symbol in order. The checked loop processes the tail, advanced cursors, overlapping views and short buffers.

To reproduce the candidate, use the same source, toolchain and flags as the parent and enable `MECH_COMPACT_NONZERO_U32_PACK=1` for compact code generation. The encoder starts at `hosts/gpu/tests/fixtures/native/compact-compiler-regression.mec`.

### Runtime and correctness

The balanced run measured 81/81 libdeflate wins forward and 80/81 reverse, with 80/81 in both orders. All previously protected cases held. All 81 cases beat the independent reference in each order.
The fixed-cohort mean positive slowdown fell from 0.222516% to 0.004503%, an improvement of 0.218013 percentage points. The maximum paired deficit was 0.081046%, and the mean using each case’s slower order was 0.040627%.

| Case | Control µs F / R | Candidate µs F / R | libdeflate µs F / R | Candidate gap F / R | Paired gap before → after | Contribution pp before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `reymont-prefix-1024` | 59.79 / 59.88 | 58.46 / 58.62 | 58.96 / 59.00 | -0.565% / +0.731% | +2.325% → +0.081% | 0.129185 → 0.004503 |
| `prefix-natural-1024` | 59.75 / 59.79 | 58.50 / 58.46 | 58.96 / 58.96 | -0.518% / -0.061% | +1.680% → -0.290% | 0.093331 → 0.000000 |
| `prefix-random-4096` | 72.77 / 70.58 | 73.79 / 68.60 | 76.15 / 76.17 | -3.705% / -8.548% | -5.175% → -6.158% | 0.000000 → 0.000000 |
| `prefix-random-8192` | 109.94 / 112.90 | 110.65 / 109.79 | 124.90 / 123.96 | -11.168% / -10.615% | -9.699% → -10.892% | 0.000000 → 0.000000 |
| `prefix-random-16384` | 216.71 / 210.44 | 213.31 / 207.92 | 247.96 / 236.83 | -13.141% / -12.071% | -11.514% → -12.607% | 0.000000 → 0.000000 |
| `16384-distribution-change` | 456.48 / 467.08 | 455.75 / 461.50 | 481.23 / 482.27 | -6.123% / -4.320% | -4.413% → -5.226% | 0.000000 → 0.000000 |
| `prefix-random-33027` | 471.29 / 479.15 | 470.71 / 476.04 | 531.69 / 531.60 | -11.850% / -10.465% | -10.699% → -11.161% | 0.000000 → 0.000000 |
| `prefix-random-32767` | 451.13 / 459.71 | 448.48 / 456.83 | 515.98 / 516.73 | -13.200% / -11.602% | -11.923% → -12.405% | 0.000000 → 0.000000 |
| `random-32769` | 464.46 / 468.73 | 459.98 / 465.44 | 523.38 / 526.62 | -12.163% / -11.302% | -11.207% → -11.733% | 0.000000 → 0.000000 |
| `prefix-random-32769` | 462.48 / 471.40 | 460.94 / 470.19 | 524.92 / 526.38 | -12.413% / -10.753% | -11.255% → -11.587% | 0.000000 → 0.000000 |
| `prefix-random-32768` | 451.35 / 458.50 | 449.54 / 454.42 | 515.46 / 516.29 | -12.703% / -11.950% | -11.922% → -12.327% | 0.000000 → 0.000000 |
| `heldout-random-65537` | 1,063.35 / 1,062.92 | 1,062.88 / 1,059.90 | 1,150.88 / 1,150.69 | -7.857% / -7.798% | -7.722% → -7.828% | 0.000000 → 0.000000 |
| `prefix-random-65535` | 1,052.54 / 1,055.90 | 1,050.65 / 1,053.69 | 1,162.92 / 1,163.31 | -9.868% / -9.380% | -9.410% → -9.624% | 0.000000 → 0.000000 |
| `prefix-random-65537` | 1,063.60 / 1,067.73 | 1,062.58 / 1,062.81 | 1,172.90 / 1,172.94 | -9.441% / -9.300% | -9.184% → -9.371% | 0.000000 → 0.000000 |
| `prefix-random-65536` | 1,048.85 / 1,055.33 | 1,048.58 / 1,050.40 | 1,162.50 / 1,163.00 | -10.058% / -9.693% | -9.610% → -9.875% | 0.000000 → 0.000000 |
| `prefix-random-131072` | 2,228.29 / 2,229.25 | 2,223.69 / 2,225.31 | 2,473.08 / 2,477.10 | -10.241% / -10.128% | -10.108% → -10.185% | 0.000000 → 0.000000 |
| `prefix-random-262144` | 4,571.06 / 4,564.96 | 4,571.88 / 4,557.62 | 5,056.75 / 5,054.67 | -9.731% / -9.730% | -9.671% → -9.730% | 0.000000 → 0.000000 |
| `prefix-random-1048576` | 18,182.29 / 18,187.33 | 18,181.98 / 18,184.83 | 20,354.85 / 20,361.23 | -10.690% / -10.610% | -10.606% → -10.650% | 0.000000 → 0.000000 |

On the two 1 KiB cases the packing phase used 5,308 instructions and 1,024 branches per encode. The same phase in the matched parent used 14,380 instructions and 5,545 branches. The native differential covered 46,080 inputs across all 16 lane masks. It checked partial writes, overlapping buffers, arbitrary cursor states and 16,463 original fault returns. The proof rejected five changes to the source recurrence, including a potentially trapping division.
All 23 native runtime tests passed for each of four inline owner counts. Exact native gates covered 162 output and alias checks, six named errors and 12 same-process recoveries. The linked C harness passed 324 deployment smokes.

### Artifact binding

- Encoder text is 67,272 B, lookup data 65,536 B, const data 80,064 B, and the stripped executable 291,768 B. Peak stack is 5,184 B.
- Codec source SHA-256 `653597f08f889908c48610e90aa65e94a77847fb34500d0cc3a046f83cd3d299`.
- Canonical bytecode SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.
- Encoder object SHA-256 `d6453375270ba383cf831f98d93aa531a46d255d946a1667120506e403b1bc11`.
- Bound worker SHA-256 `6b0912f4d97c50f52174dbff28d685bf622183b32208a594e8a35df7051c0a51`.
- Full timing result SHA-256 `6c054b3f1077c59680448477aafb4708ce26787d1c6bbcd7fd939a8547156472`.
- Timing verification SHA-256 `5bdd3f9ae4a01c817c39037719e6eec5011406b4fa998e042a86f1c07fda1010`.
- Candidate runtime library SHA-256 `46b1dd6fe9b6c4a7accc2986b52558a7f7a61f6bcd848ba9c609f744b6d1bca3`.
- Static deployment support SHA-256 `0dbf3c960815c24295614485e3e7ed0eb9971a57678d053767cb44ab35557a8e`.
- Re-emission and runtime rebuild reproduced the exact timed artifacts and workers.

### Complete source-through-link builds

This comparison uses prebuilt compilers and each actor’s verified prebuilt host support.

- Control source 2.167602 s link 0.037854 s source_through_link 2.206626 s strip 0.010926 s source_through_strip 2.217739 s.
- Candidate source 2.169138 s link 0.038687 s source_through_link 2.216188 s strip 0.010890 s source_through_strip 2.227144 s.
- libdeflate source 0.447124 s link 0.034581 s source_through_link 0.482005 s strip 0.010793 s source_through_strip 0.492848 s.
- Independent reference source 2.959175 s link 0.035496 s source_through_link 2.994894 s strip 0.010700 s source_through_strip 3.005697 s.
