@codex review

Review `59a1b8f6096cecec9e9a6d8be15f47b3143897e9` against `f37b86d2216e62c90f6756aea22828e038d2c612`.

The compiler specializes a shared scalar tail after private index admission when its two incoming edges carry known opposite tags. Each incoming path preserves the original store, operands, memory flags, and continuation. The pass refuses a second effect and a tail definition used directly after the join.

### Runtime and correctness

The complete 81-case run retained all 76 named libdeflate wins and all 81 independent-reference wins in both orders at 96 blocks per case per order. The matched mean positive slowdown over the fixed 18 cases fell from 3.762630% to 3.061167%, a reduction of 0.701464 percentage points.
The largest remaining paired deficit is 18.004518%. Averaging the worse order of each fixed case gives 3.131644%.

| Case | Control µs F / R | Candidate µs F / R | libdeflate µs F / R | Candidate gap F / R | Paired gap before → after | Contribution pp before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix-random-4096` | 92.06 / 90.42 | 88.04 / 88.88 | 75.23 / 76.38 | +18.042% / +17.967% | +20.879% → +18.005% | 1.159966 → 1.000251 |
| `prefix-random-8192` | 145.21 / 144.04 | 138.73 / 139.60 | 124.44 / 124.33 | +11.654% / +12.711% | +16.358% → +12.182% | 0.908754 → 0.676753 |
| `prefix-natural-1024` | 66.62 / 66.58 | 65.79 / 65.79 | 58.92 / 59.04 | +12.493% / +11.953% | +13.769% → +12.223% | 0.764926 → 0.679053 |
| `reymont-prefix-1024` | 66.67 / 66.58 | 65.96 / 65.83 | 59.00 / 59.08 | +12.737% / +11.968% | +13.611% → +12.352% | 0.756140 → 0.686225 |
| `prefix-random-16384` | 245.27 / 244.96 | 237.29 / 238.15 | 236.48 / 237.90 | +0.294% / +0.386% | +3.111% → +0.340% | 0.172845 → 0.018885 |
| `16384-distribution-change` | 481.81 / 480.85 | 477.42 / 482.06 | 483.06 / 484.31 | -1.281% / -1.180% | -0.852% → -1.231% | 0.000000 → 0.000000 |
| `prefix-random-33027` | 518.85 / 517.46 | 515.02 / 514.67 | 533.77 / 534.81 | -3.807% / -3.990% | -3.153% → -3.899% | 0.000000 → 0.000000 |
| `prefix-random-32767` | 500.46 / 498.96 | 498.29 / 496.17 | 518.62 / 519.81 | -4.006% / -4.645% | -3.897% → -4.326% | 0.000000 → 0.000000 |
| `random-32769` | 511.92 / 512.02 | 507.31 / 508.02 | 525.19 / 528.40 | -3.690% / -3.983% | -2.956% → -3.837% | 0.000000 → 0.000000 |
| `prefix-random-32769` | 510.33 / 509.83 | 508.42 / 508.12 | 527.65 / 529.27 | -3.867% / -4.132% | -3.536% → -3.999% | 0.000000 → 0.000000 |
| `prefix-random-32768` | 498.63 / 498.15 | 496.87 / 494.44 | 517.94 / 520.15 | -4.351% / -4.873% | -4.033% → -4.612% | 0.000000 → 0.000000 |
| `heldout-random-65537` | 1,105.33 / 1,102.85 | 1,100.67 / 1,101.33 | 1,146.77 / 1,150.33 | -4.282% / -4.386% | -4.027% → -4.334% | 0.000000 → 0.000000 |
| `prefix-random-65535` | 1,106.46 / 1,110.75 | 1,106.40 / 1,105.96 | 1,160.63 / 1,162.15 | -5.131% / -5.024% | -4.633% → -5.077% | 0.000000 → 0.000000 |
| `prefix-random-65537` | 1,117.83 / 1,120.15 | 1,116.75 / 1,112.75 | 1,170.79 / 1,170.77 | -5.077% / -5.064% | -4.617% → -5.070% | 0.000000 → 0.000000 |
| `prefix-random-65536` | 1,104.98 / 1,109.98 | 1,103.94 / 1,105.50 | 1,161.25 / 1,164.48 | -5.322% / -5.380% | -4.969% → -5.351% | 0.000000 → 0.000000 |
| `prefix-random-131072` | 2,303.60 / 2,299.35 | 2,299.87 / 2,291.65 | 2,473.40 / 2,476.31 | -7.150% / -7.620% | -7.124% → -7.386% | 0.000000 → 0.000000 |
| `prefix-random-262144` | 4,697.81 / 4,704.52 | 4,698.27 / 4,694.79 | 5,055.46 / 5,054.38 | -7.246% / -7.178% | -7.075% → -7.212% | 0.000000 → 0.000000 |
| `prefix-random-1048576` | 18,573.96 / 18,578.96 | 18,567.48 / 18,568.04 | 20,341.71 / 20,350.46 | -8.690% / -8.527% | -8.684% → -8.609% | 0.000000 → 0.000000 |

The focused native test exercised both store paths, escaped join values, and a second store. The qualified artifact passed 162 exact success and alias checks, six named errors, 12 same-process recoveries, and 324 deployment smokes.
The phase’s diagnostic count for random 16 KiB fell from 162,768 to 132,220 instructions and from 57,718 to 42,444 branches. Production timings used the uninstrumented executable. The selected emission keeps every function extent and location and all other native function bytes.

### Artifact binding

- Encoder text is 65,464 B, lookup data 65,536 B, the whole const section 80,064 B, and the stripped executable 276,072 B. Peak stack is 4,864 B.
- Codec source SHA-256 is `653597f08f889908c48610e90aa65e94a77847fb34500d0cc3a046f83cd3d299`.
- Canonical bytecode SHA-256 is `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.
- Encoder object SHA-256 is `b013f098122d4fedd9a79ebd7c8b8abed927e2e3b62425002e743555e671280e`.
- Bound worker SHA-256 is `ce7843a8c224c30981b4831c636ba919bb9a0bb9ec28b60fd00f4e9e07fb91e9`.
- Full timing result SHA-256 is `11974ce1a3c7fee53236692ef40781ab20d520408440abf7a43be0b83469fadb`.
- Timing verification SHA-256 is `e9c8d932bf5d7c35fe2894a0926527f44108b5c2447cca06843cea691450f868`.
- The recipe adds `MECH_COMPACT_SPECIALIZE_TAGGED_STORE_TAILS=mech_compact_numeric_3956_vector` and refreshes the phase allocation and layout profiles.
- `MECH_COMPACT_PHASE_BLOCK_LAYOUT` target-profile SHA-256 is `bd9f1f50504862cb2dda921b94df1ef5cb67632f82e6b0a64e907ac73695e86f`.
- `MECH_COMPACT_PHASE_REGISTER_WEIGHTS` target-profile SHA-256 is `29dd677953bfb9653e99b50c18f634d3daaebaf3370aeb032165defae95cc28c`.

### Complete builds

The retained timer measures original source through final executable link with prebuilt compilers and fixed host support.
- Control source 2.177232 s link 0.035672 s source_through_link 2.216594 s strip 0.010582 s source_through_strip 2.227359 s.
- Candidate source 2.174829 s link 0.036662 s source_through_link 2.215242 s strip 0.010686 s source_through_strip 2.226123 s.
- libdeflate source 0.448160 s link 0.034515 s source_through_link 0.484055 s strip 0.010677 s source_through_strip 0.494930 s.
- Independent reference source 2.953181 s link 0.035118 s source_through_link 2.988379 s strip 0.010707 s source_through_strip 2.999419 s.
