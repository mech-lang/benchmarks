# What the Rust controls show — 17 November 2026

Implemented and measured Rust controls for the 61 remaining tasks: 380 new Rust observations and 730 paired Mech observations, five fresh forks per implementation and path. Together with the retained N-body and related-post controls, all 63 active tasks now have a measured control in the default metrics view.

The resident results below use the preferred source path. Decoded artifacts were measured separately in the same randomized blocks. Both languages run the same input schedules; verification checks complete trajectories, owned snapshots and recovery against independent Python oracles. Rust is an independent AOT task implementation. Mech also performs runtime scheduling, admission and resource accounting. These are task comparisons, not matched kernel attribution.

| Task | Mech median µs | Rust median µs | Mech / Rust |
| --- | ---: | ---: | ---: |
| scalar-changed | 0.189320 | 0.022715 | 8.33× |
| scalar-unchanged | 0.144945 | 0.004694 | 30.88× |
| numerical-pipeline | 0.362299 | 0.027778 | 13.04× |
| ekf | 1.311768 | 0.110748 | 11.84× |
| filter-cardinality | 118.837692 | 0.079625 | 1492.47× |
| retained-snapshots | 118.981292 | 0.069225 | 1718.76× |
| table-joins | 41.032358 | 0.157942 | 259.79× |
| graphs | 17.003967 | 0.077750 | 218.70× |
| strings | 2.553716 | 0.024394 | 104.69× |
| jit | 1.389667 | 0.232844 | 5.97× |

Changed scalar work costs 189.3 ns in Mech; unchanged work costs 144.9 ns. Skipping the scalar computation saves 23.4% here. Both Mech cases allocate zero times inside the timed block. The remaining turn cost matters for tiny tasks.

The eight-element filter costs 118.84 µs and 3,161 allocations per Mech turn, versus 0.0796 µs and 3 allocations in Rust. Keeping all 5,000 snapshots costs 118.98 µs per Mech turn with the same allocation count. Its retained managed storage grows from 5,223 to 8,248,921 bytes. The similar filter timings suggest that snapshot retention is not the main source of the execution gap; investigate the filter path and its allocation volume first.

The full 4,096-step EKF trajectory costs 1.312 µs per Mech step, with zero allocations in the timed block. It is 11.84× the Rust time. This separates allocation-heavy collection paths from the numerical path rather than suggesting one universal Mech overhead.

## Cardinality sweep

The initial sweep is preserved in full. A progress monitor was found reading the growing result index during later capacity measurements. The capacity figures below use a fresh independent five-fork sweep with that monitor disabled and 256 complete schedule cycles (1,280 accepted turns per fork). No original samples were removed. The campaign index now keeps previews and links to complete raw trajectories, avoiding repeated serialization of all outputs between forks.

Every row scans 65 input elements. The schedule crosses each indicated output-cardinality boundary, including A → B → A and unchanged output. These are output-capacity tests, not larger input-size tests.

| Output threshold | Mech median µs | Rust median µs | Mech allocations/turn |
| ---: | ---: | ---: | ---: |
| 0 | 496.868 | 0.069857 | 12,902 |
| 7 | 652.063 | 0.141080 | 15,174 |
| 8 | 590.740 | 0.155012 | 15,508 |
| 9 | 604.632 | 0.167513 | 15,842 |
| 15 | 677.010 | 0.176726 | 17,846 |
| 16 | 682.834 | 0.185514 | 18,180 |
| 17 | 695.391 | 0.197070 | 18,514 |
| 31 | 861.518 | 0.211881 | 23,190 |
| 32 | 889.529 | 0.235579 | 23,524 |
| 33 | 900.843 | 0.242416 | 23,858 |
| 63 | 1263.379 | 0.264973 | 33,878 |
| 64 | 1287.794 | 0.275814 | 34,212 |
| 65 | 1280.410 | 0.167545 | 34,479 |

Even the almost-empty result scans all 65 inputs. This exposes the scan/evaluation cost before most output storage is needed. Exact shapes, complete values and every retained sample are in the linked campaign.

## Complete applications and builds

Full compressor native-code preparation takes 83.267 seconds, plus 3.435 seconds to compile the source artifact. One full 6.6 MB warm compression call takes 1.872 seconds. Native-code preparation alone is 44.5× the warm call duration. At this tested size, it remains a major cost for one-shot use. Preparation is shared across the 12 inputs in each complete worker fork; it is not charged twelve times.

Full K-nucleotide (254,166,745 input bytes): Mech 0.909184 s; unchanged upstream Rust #7 0.688168 s, 1.321×. Both clocks include fresh process startup, input reading, all computation, full output and exit. Mech uses four partitions; Rust retains its upstream thread-pool policy.

Native scalar source → executable: Mech 7.157430 s; Rust 0.160854 s. Each measured build starts from a fresh project/source after a separate support-cache qualification. The resulting executable is run and checked on all six scheduled inputs. The paths have different support machinery: Mech includes compiler-worker startup, dependency resolution and checked runtime support; rustc uses its prebuilt standard library.

Full Reymont compression (6,627,202 bytes): Mech level 12 1.871506 s, 1,696,488 output bytes; Rust zlib-rs maximum level 9 0.177674 s, 1,826,397 bytes. Output allocation and scratch destruction are included in the call, input import/warmup/returned-output destruction excluded. Both complete streams independently inflate to the exact input, preserve prefix/aliases and contain no trailing data. Different codec output sizes must be considered with time; this is not equal-quality compression.

## Fixed total work across processes

196,608 accepted numerical turns in total, with complete supervised group startup through exit. One application execution thread per process.

| Processes | Mech group seconds | Rust group seconds | Mech turns/s | Rust turns/s |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0.105044 | 0.020163 | 1,871,674 | 9,750,890 |
| 2 | 0.075289 | 0.025125 | 2,611,393 | 7,825,298 |
| 4 | 0.068458 | 0.021566 | 2,871,937 | 9,116,449 |

The full-process application gaps and tiny resident gaps describe different tasks and boundaries. They do not establish a same-task input-size crossover. Every median, range, standard deviation, source hash, compiler command and raw fork remains inspectable. No adverse observations were removed and these exploratory results do not automatically move a pinned Mech control.

## Evidence

[Machine-readable study](rust-controls-2026-11-17.json). These reports include the complete per-task tables and raw-evidence archives:

- [2026-11-17-rust-resident-001](campaign-evidence/2026-11-17-rust-resident-001/report.md)
- [2026-11-17-rust-capacity-002](campaign-evidence/2026-11-17-rust-capacity-002/report.md)
- [2026-11-17-rust-concurrent-001](campaign-evidence/2026-11-17-rust-concurrent-001/report.md)
- [2026-11-17-rust-native-001](campaign-evidence/2026-11-17-rust-native-001/report.md)
- [2026-11-17-rust-applications-001](campaign-evidence/2026-11-17-rust-applications-001/report.md)
- [2026-11-17-rust-strings-002](campaign-evidence/2026-11-17-rust-strings-002/report.md)
