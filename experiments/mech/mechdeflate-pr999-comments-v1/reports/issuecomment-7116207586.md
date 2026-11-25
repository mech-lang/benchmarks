@codex review

Review `f3f5cc87fea0b74c973839df90acde00ace4a930` against `eeac6ffd291474c3b0ad6226947518c1cec98e22`.

Keep the first owner in the invocation heap and allocate an owner registry when a second live owner needs a slot. The registry holds 24 secondary slots, with a free list for further slots. A borrowed invocation can use four size classes to store small numeric payloads with their owner descriptors. Worker heaps continue using transferable allocations, and byte results transfer as an owned Vec.

The registry and its scratch backing are invocation-owned. Both timings used the same encoder object, canonical bytecode, runtime boundary and pinned peers. Only the candidate runtime used the lazy registry.

### Runtime and correctness

The 81-case run at 96 blocks per case and order held 77/81 against libdeflate and 81/81 against the independent reference in both orders. The matched mean positive slowdown over the fixed 18 cases fell from 2.247186% to 1.987433%, a reduction of 0.259754 percentage points.
The maximum paired deficit is 11.040855%. The average using the slower order of each case is 2.073211%.

| Case | Control µs F / R | Candidate µs F / R | libdeflate µs F / R | Candidate gap F / R | Paired gap before → after | Contribution pp before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix-random-4096` | 84.19 / 85.06 | 84.85 / 82.50 | 76.23 / 75.73 | +11.580% / +10.505% | +12.722% → +11.041% | 0.706753 → 0.613381 |
| `reymont-prefix-1024` | 65.25 / 65.25 | 64.67 / 64.67 | 58.96 / 59.00 | +9.973% / +9.943% | +11.012% → +9.958% | 0.611750 → 0.553209 |
| `prefix-natural-1024` | 65.25 / 65.25 | 64.67 / 64.67 | 59.00 / 59.04 | +9.959% / +9.770% | +10.929% → +9.864% | 0.607158 → 0.548013 |
| `prefix-random-8192` | 132.71 / 130.62 | 131.52 / 128.54 | 125.10 / 124.29 | +5.807% / +4.023% | +5.787% → +4.911% | 0.321526 → 0.272830 |
| `prefix-random-16384` | 237.54 / 230.71 | 235.46 / 227.17 | 238.02 / 235.75 | -1.308% / -3.296% | -1.391% → -2.307% | 0.000000 → 0.000000 |
| `16384-distribution-change` | 478.44 / 507.15 | 478.02 / 498.77 | 484.33 / 505.33 | -1.532% / -0.842% | -0.771% → -1.188% | 0.000000 → 0.000000 |
| `prefix-random-33027` | 515.69 / 511.46 | 517.48 / 513.56 | 535.33 / 533.15 | -3.895% / -3.907% | -4.154% → -3.901% | 0.000000 → 0.000000 |
| `prefix-random-32767` | 502.08 / 495.77 | 499.65 / 494.88 | 521.50 / 518.46 | -4.939% / -4.917% | -4.611% → -4.928% | 0.000000 → 0.000000 |
| `random-32769` | 509.33 / 506.40 | 506.98 / 504.21 | 527.31 / 528.96 | -4.034% / -4.811% | -3.994% → -4.423% | 0.000000 → 0.000000 |
| `prefix-random-32769` | 509.58 / 506.56 | 508.06 / 506.38 | 529.90 / 527.38 | -4.583% / -4.250% | -4.117% → -4.417% | 0.000000 → 0.000000 |
| `prefix-random-32768` | 498.50 / 493.29 | 496.33 / 491.96 | 519.98 / 518.15 | -5.154% / -5.454% | -4.913% → -5.304% | 0.000000 → 0.000000 |
| `heldout-random-65537` | 1,108.02 / 1,103.92 | 1,106.21 / 1,107.02 | 1,146.94 / 1,149.17 | -4.128% / -4.171% | -3.898% → -4.149% | 0.000000 → 0.000000 |
| `prefix-random-65535` | 1,111.58 / 1,105.81 | 1,108.35 / 1,105.02 | 1,163.04 / 1,161.60 | -5.226% / -5.095% | -4.869% → -5.161% | 0.000000 → 0.000000 |
| `prefix-random-65537` | 1,116.67 / 1,118.69 | 1,119.00 / 1,114.63 | 1,171.67 / 1,171.42 | -4.845% / -5.142% | -4.664% → -4.994% | 0.000000 → 0.000000 |
| `prefix-random-65536` | 1,107.98 / 1,107.15 | 1,106.21 / 1,102.25 | 1,162.77 / 1,161.73 | -5.433% / -5.287% | -4.976% → -5.360% | 0.000000 → 0.000000 |
| `prefix-random-131072` | 2,311.65 / 2,301.98 | 2,301.48 / 2,299.44 | 2,469.29 / 2,477.08 | -7.118% / -7.201% | -6.873% → -7.159% | 0.000000 → 0.000000 |
| `prefix-random-262144` | 4,704.60 / 4,706.23 | 4,695.81 / 4,694.04 | 5,055.38 / 5,056.46 | -7.199% / -7.230% | -7.004% → -7.215% | 0.000000 → 0.000000 |
| `prefix-random-1048576` | 18,588.06 / 18,603.00 | 18,547.79 / 18,552.44 | 20,369.08 / 20,327.00 | -8.961% / -8.664% | -8.597% → -8.813% | 0.000000 → 0.000000 |

All 20 runtime tests passed at each supported inline owner count. The candidate completed 162 exact success and alias checks, six named errors and 12 same-process recoveries. The existing C harness passed all 324 deployment smokes with the candidate runtime statically linked.
The allocator requests 264 B for the lazy registry and 21,504 B for its lazy numeric slab. These are physical allocator requests. The logical payload counters match the control for every case, and the tiny sole-owner path needs neither reservation.

### Artifact binding

- Encoder text is 65,464 B, lookup data 65,536 B, the whole const section 80,064 B, and the stripped executable 274,712 B. Peak stack is 4,896 B.
- Codec source SHA-256 is `653597f08f889908c48610e90aa65e94a77847fb34500d0cc3a046f83cd3d299`.
- Canonical bytecode SHA-256 is `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.
- Encoder object SHA-256 is `8aa71fb264e8e1f76cccaaea9c743b812a8e1817a1fc8b04085de10e68a34ddf`.
- Bound worker SHA-256 is `06e3cedbf4344fe6dad63d42bf794c98a844cfaac98f1e892a2c72710e45252f`.
- Full timing result SHA-256 is `5776ad32bb369c476f0ee6045aaf683cf24f6b474ac17063216cc6184e89c2e3`.
- Timing verification SHA-256 is `2a436618d0ca0810a10a1fbd1855bf3f427f7f0a415d4785255c694c70aaf68a`.
- Candidate runtime library SHA-256 is `3eaa3bc47a5bb87562c624e4e6da9cd03a0ebfd5348f059e802d9cf27643aacf`.
- Rebuilt static deployment support SHA-256 is `ef59082cc67f2aad818095fa3f3975212e68947e30b9b06e9ecb4144a3debe2a`.
- The release compiler reproduced the exact encoder artifacts. Rebuilding the runtime from the source files reproduced the timed worker byte for byte.

### Complete builds

The timer starts at the original source and ends at the completed executable link. Both compilers and fixed host support are prebuilt for each actor.

- Control source 2.171260 s link 0.035457 s source_through_link 2.207279 s strip 0.010837 s source_through_strip 2.218322 s.
- Candidate source 2.176030 s link 0.038669 s source_through_link 2.217796 s strip 0.011032 s source_through_strip 2.229436 s.
- libdeflate source 0.446665 s link 0.034834 s source_through_link 0.481956 s strip 0.010913 s source_through_strip 0.492756 s.
- Independent reference source 2.955573 s link 0.035469 s source_through_link 2.991067 s strip 0.010896 s source_through_strip 3.002193 s.
