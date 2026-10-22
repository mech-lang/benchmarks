# Full-size Janet spectral-norm comparison

Three fresh whole-process samples of each exact parent and candidate source run
sequentially under the shared mutex, at N=5500. Every sample produces the complete
12-byte output with SHA-256
`f9d5b5e3eb7657cf1bbba4cc856651864df9cd9fd9a6be9b9bc5fcbb67150deb`, the retained
full-size reference in `experiments/bqn/spectral-sum-v1/run_serial.py`. Source,
runtime, controller, catalog and dependency identities are checked before launch.
All owned groups close and direct children are reaped before the next process.

| Implementation | Median seconds | Sample SD seconds | × retained Mech AOT |
| --- | ---: | ---: | ---: |
| Parent v2 | 66.827 | 2.173 | 776.4× |
| Reusable-vector / denominator-recurrence v3 | 16.531 | 0.146 | 192.1× |

The observed median improvement is 4.04×. The denominator is the retained
N=5500 Mech AOT median, **0.086075292 seconds (1.0×)**, from catalog program
`spectralnorm:mech-integer-simd1-u4-r4-p8-g8`. It is not a newly measured paired
control. Raw seconds, six individual samples, original median precision, source
hashes and the unchanged catalog SHA are in `run-v1/results.json`.

These are exploratory local results, not chart admission. The Apple M3 host runs
macOS 26.2 build 25C56. AC power and Low Power Mode off are checked before and after
each sample and approximately every ten seconds during execution. Process
snapshots show no detected competing compiler, but substantial desktop background
activity, including media analysis, filesystem work and signpost reporting. This
cohort does not establish results on an idle machine. Thermal state and CPU
frequency were not continuously measured. Quiet-host confirmation remains pending.

The timing interval starts immediately before fork and ends at observed process
exit. A dedicated observer polls at 1ms independently of the telemetry callback;
scheduling can add observation latency. Parsing, bytecode compilation, VM startup,
all 40 full matrix products, output and shutdown are included. Output hashing and
owned-group cleanup follow the recorded interval. The observer test specifically
checks that slow telemetry does not inflate the exit timestamp and that timeout
cleanup reaps the child and closes the group. Observer and process setup overhead
is not claimed to have been subtracted.

The original untimed controller remains unchanged in `../native-v1/run.py`.
`process.py` is its explicit quantitative derivative, adding an independent exit
observer and power/process monitor callback. The plan and frozen preparation
inputs are reused without changing any historical source, count or timing.

The candidate uses three reusable vectors and exact coefficient recurrences.
`../native-v1/spectral-review.md` and the retained fourteen native counter checks
establish matching bounded work; algebra establishes the full-size coefficient
domain. Full-size output now passes all six observations. Native normalized LOC,
canonical formatting and final admission review remain pending.
