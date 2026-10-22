# Janet n-body results

Scalar VM registers and a fixed pair graph reduce the full-process median from
**105.393 seconds (101.4× Mech AOT)** to **23.864 seconds (23.0×)**, an observed
**4.42× improvement**. All twelve full-size outputs exactly match the retained
26-byte energy output, stricter than the specified 1e-8 output tolerance.

| Implementation | Median seconds | × Mech AOT | Maximum peak RSS across three samples |
|---|---:|---:|---:|
| Historical callable-array parent | 105.393 | 101.4× | 4.09 MiB |
| Direct indexed access | 80.591 | 77.5× | 4.12 MiB |
| Cached outer-body fields | 76.270 | 73.4× | 4.20 MiB |
| Scalar registers and fixed pair graph | 23.864 | 23.0× | 4.31 MiB |

Mech AOT's retained same-input median is **1.039486459 seconds (1.0×)**, profile
`nbody:pairwise-mass-tails`. It is not a freshly paired Mech control. The study
uses three shuffled sequential rounds across all four sources, each at
50,000,000 steps. Raw samples, sample standard deviations, CPU usage, source and
runtime hashes, power/process snapshots and complete output remain in `run-v1`.
This establishes the measured alternatives, not a globally optimal Janet program.

## Mechanism and work

Replacing callable-array notation with `get` removes 18 static call sites from
the compiled advance function and introduces 18 indexed-get sites. This is a
source-bound native disassembly observation, not a dynamic instruction count.
Caching additionally retains the outer body's state across its following pairs.

The register version uses a standard Janet macro to unroll the fixed ten-pair
and fifteen-component graph and keeps all state in VM variables across the
runtime step loop. It also avoids calling a separate advance function for each
step. Native disassembly has 49 virtual-register slots, versus the parent's 23.
Its single time-step loop contains no aggregate state reads/writes; initialization
and final stores remain outside the loop. Ten scalar divisions and ten native
calls remain in the loop for the ten ordinary square-root force calculations.
All arithmetic and integration remain in the application VM program. No custom
C, native force primitive, precomputed trajectory, omitted pair or reduced step
count is introduced. Source, disassembly and reproducible static analysis are in
`bytecode-v1` and `bytecode-review.json`.

The standard six cases give 24 complete bounded output checks. Another 24
instrumented executions verify 10*N pair visits, 15*N position-component updates,
complete stdout and all 35 state values bit-for-bit against the parent. A further
24 source-projected executions vary masses, positions, velocities, time steps
and step counts. Every state value matches an independent Python scalar
reference bit-for-bit. These checks cover their explicit systems; the fixed
five-body macro is not a generic variable-body integrator.

## Source measures

Every macro, authored helper, code template, initializer and output statement is
included. The standard runtime is unchanged and external to application size.
Generated VM instructions are not counted as source lines.

| Implementation | Physical rows | UTF-8 bytes | Deterministic gzip bytes | BPE tokens | Janet lexical tokens |
|---|---:|---:|---:|---:|---:|
| Parent | 64 | 2,747 | 1,126 | 1,027 | 705 |
| Direct indexed access | 64 | 2,899 | 1,131 | 1,065 | 743 |
| Cached fields | 74 | 3,033 | 1,174 | 1,112 | 781 |
| Scalar registers | 86 | 3,709 | 1,450 | 1,268 | 902 |

The fastest tested form costs about 28% more lexical tokens than the parent.
Its written executable template must not disappear from a future logical owner
measure merely because it uses quasiquote. An explicit treatment of authored
code templates remains necessary. Normalized logical and canonical formatted
LOC remain unqualified; physical rows, native lexical tokens, BPE and gzip stay
separate. The original authors, consulted upstream programs, applicable licenses
and exact local source hashes are in `source-manifest.json`. Local changes are
Codex GPT-6 family; exact serving model is unknown.

## Measurement limits

Owned processes inherit the shared timing mutex, close their process groups and
are reaped. No benchmark or native validation runs overlap. Fresh-process timing
includes source parsing, macro expansion, bytecode compilation, VM startup, the
entire simulation, both output lines and shutdown. The child exit observer runs
independently of the controller's callbacks; output checking and cleanup follow
exit. AC power and Low Power Mode off are observed. The study changes no power
setting and disables no CPU throttling.

Read-only power/process snapshots also occur periodically during a live subject.
Their scheduling/I/O contention can affect the measured wall time. A later
callback does not directly extend the independently observed exit timestamp.
The additive [boundary clarification](../measurement-boundary-review-v1.json)
corrects the frozen controller report's shorthand about excluded telemetry and
the historical reverse-complement README. It demonstrates snapshots strictly
inside 24 subject windows. No elapsed value, sample or prior sealed artifact is
changed. Background activity is recorded, but continuous temperature/frequency
and a pristine idle host are not established. These results remain exploratory
and do not change the public chart.

`verify.py` replays complete outputs, native work counters, exact state bits,
source/controller/input identities, raw/summary timing values, resources,
disassembly, telemetry-boundary evidence and process closure. `seal.json` hashes
all retained study artifacts. The canonical catalog remains unchanged.
