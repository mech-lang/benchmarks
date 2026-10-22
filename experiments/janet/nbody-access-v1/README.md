# Janet n-body state-access study

This study compares the historical `source-v2/nbody.janet` with three local
Janet implementations of the same five-body symplectic integrator. Source changes
preserve all ten pair interactions, velocity arithmetic order, fifteen position
component updates per step, initial momentum offset and both energy evaluations.
The full input is 50,000,000 steps: 500,000,000 force-pair calculations and
750,000,000 position component updates. No force kernel crosses the FFI.
The standard runtime and its ordinary square-root primitive remain unchanged.

- `intrinsic-get` replaces callable-array syntax with direct `get` operations.
- `cached-pairs` additionally retains the outer body's coordinates, mass and
  velocities in local variables across its subsequent pair updates. The latest
  velocities are stored before proceeding to the next body. No force uses a
  velocity, so this changes storage traffic while preserving operation order.
- `scalar-registers` uses an ordinary Janet macro to expand the fixed five-body
  pair graph and hold state in VM scalar variables across all time steps. Every
  generated variable has a private gensym. The macro, initialization, ten pair
  updates, fifteen position updates, output stores and all helpers count as
  application source. Macro expansion is bytecode compilation at process startup;
  it does not precompute the trajectory or turn the VM program into native AOT.

## Native qualification

`qualify.py` tests all six retained n-body cases for each source against the
complete finite two-line reference, using the specified 1e-8 energy tolerance.
It separately projects diagnostic counters into the same sources and captures
all 35 final state values using round-trip decimal output. Each projection
performs exactly 10*N pair calculations and 15*N component updates, retains the
complete stdout contract and matches the parent's complete state bits.
The projections are diagnostics and are not timed subjects.

`qualify_perturbed.py` tests six other systems across all four implementations.
It varies initial coordinates, velocities, planet masses, step sizes and counts.
`reference.py` independently implements the scalar integration in Python. All
35 state values match this reference bit-for-bit in all 24 captures. This checks
these explicit systems, not an arbitrary-state proof. The macro's fixed graph
is appropriate for this specified five-body workload; it is not a generic
variable-body simulator.

`capture_bytecode.py` compiles separate source-bound projections and records the
runtime's native disassembly of the actual advance functions, without running
the application. Its evidence distinguishes written shorthand from the VM code
and scalar registers that implement it. Static instruction counts are not
execution counts for nested loops.

## Timing and source-size boundaries

`full.py` runs three shuffled serial rounds for each exact source using the
shared benchmark mutex. Its inherited owner acquires child birth identity before
exec, observes exit independently of telemetry, collects macOS `wait4` resources,
closes the process group and reaps the child. Startup, parsing, macro expansion,
bytecode compilation, VM work, output and shutdown are included. Validation
and cleanup are outside the elapsed interval. Read-only power/process snapshots
are taken before/after subjects and periodically while a subject runs; those live
snapshots can contribute ordinary host contention inside the measured wall time.
The independent exit observer prevents a slow post-exit snapshot from extending
the recorded exit time. No timing run overlaps another benchmark or native
validation. The [measurement-boundary clarification](../measurement-boundary-review-v1.json)
disambiguates the
frozen controller report's shorthand about excluded telemetry.

The output reference and Mech AOT denominator come from the pinned retained
50-million-step replication report. Mech is not rerun in this cohort. Nested
`output_contract` records are the pure output validator's result: they do not
certify process ownership or source work. Those requirements are independently
checked through the owned receipts, source-bound counters and state comparisons.
The full captures retain complete stdout/stderr, raw observations and resources.
Power/process snapshots do not establish continuous temperature/frequency or a
perfectly idle host. This study changes no power setting and disables no CPU
throttling. These experimental results do not enter the public chart.

`measure.py` reports exact physical rows, UTF-8 bytes, deterministic gzip, pinned
BPE and native grammar lexical tokens for every complete application source.
Macros are counted as written, with every authored helper included; generated
VM instructions are not relabeled as source LOC. Normalized logical and canonical
formatted LOC remain unqualified. The register variant also exposes a specific
normalization requirement: its written executable code template must receive an
explicit source-ownership treatment. Dropping that template as ordinary quoted
data, or substituting the expanded VM instruction count, would hide a source
cost. Neither treatment is qualified here. Exact-text and lexical measures
include the entire template. The source manifest retains original authors,
consulted upstream lineage and applicable Apache-2.0/BSD notices. Local changes
identify Codex GPT-6 family; exact serving model is unknown.

Reproduce in a fresh output directory with the pinned runtime present, keeping
all native commands outside other timing windows:

```sh
python3 experiments/janet/nbody-access-v1/qualify.py
python3 experiments/janet/nbody-access-v1/qualify_perturbed.py
python3 experiments/janet/nbody-access-v1/full.py
python3 experiments/janet/nbody-access-v1/capture_bytecode.py
python3 experiments/janet/nbody-access-v1/analyze_bytecode.py
python3 experiments/janet/nbody-access-v1/review_boundary.py
experiments/source-metrics/.build/venv39/bin/python experiments/janet/nbody-access-v1/measure.py --run
python3 experiments/janet/nbody-access-v1/verify.py
```

Workload: https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/nbody.html
Janet macros: https://www.janet-lang.org/docs/macros.html
