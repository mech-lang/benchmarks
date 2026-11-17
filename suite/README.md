# Repeatable Mech campaigns

This suite measures the canonical compiler and resident runtime, and keeps every
campaign as a dated, inspectable record. It adds 18 resident experiments and a
native build/footprint experiment to the existing ten application workloads.
`catalog.json` also names the remaining coverage explicitly as planned work.
An implemented family does not imply that all of its operations are qualified.

The **Mech over time** link in the existing explorer opens the campaign dashboard.
Run `python3 tools/serve.py --port 8766` from the repository root, then open
<http://127.0.0.1:8766/benchmarks/campaigns.html>. No additional web dependencies
or hosted service are required. Rebuild or restart the server after adding a run.

## Build independently pinned workers

Use clean compiler checkouts. The initial candidate is
`9087b1f07727a9bfcb7c09059f48edaca6dc2301`; the comparison baseline is
`fc2b73103ce97a1907b3c8ba6792bc248e01e3b5`. This asks how the later qualified
compiler compares with the generated-code-volume revision on identical tasks.
It is not an old-interpreter-versus-new-runtime comparison.

```sh
python3 tools/build_worker.py --mech /path/to/candidate --revision 9087b1f07727a9bfcb7c09059f48edaca6dc2301 --output .local/candidate --online
python3 tools/build_worker.py --mech /path/to/baseline --revision fc2b73103ce97a1907b3c8ba6792bc248e01e3b5 --output .local/baseline --online
```

Build workers sequentially, before timing. Each worker has separate build output,
a standard f64/dynamic-shape compiler feature profile matching the initial corpus,
a dependency lockfile, exact compiler/adapter/binary hashes, feature selection,
toolchain details and selected build flags in `worker.json`. Offline dependency
resolution is the default; `--online` permits initial downloads. The template is
an adapter for this architecture, not a universal adapter for old `main`.
`--adapter` accepts a revision-specific implementation of the same protocol.
Use `--lockfile` with a retained campaign's worker `Cargo.lock` to require exact
dependency resolution on a rebuild. CI pins the qualified nightly toolchain.

Add `--native` to **both** builds to include the canonical native application
generator. This profile deliberately enables `canonical-native-program`: the
pinned revision's narrower codegen feature combination does not build. The
generated scalar executable itself uses the ordinary checked scalar runtime.
Its build explicitly enables `mech-engine/pure_text` because the pinned scalar
metadata code references an image-proof module behind that feature. This
compatibility setting is part of the native measurement contract and every
saved build command; compiler sources and generated Mech objects are unchanged.

Compiler checkout changes during a build invalidate the provenance. Tracked
edits require `--allow-dirty` and their diff hash is recorded. The installed
`mech` command is never substituted for a pinned worker.

## Run and retain a campaign

```sh
python3 tools/run_suite.py --worker .local/candidate/worker.json --baseline .local/baseline/worker.json --profile standard --output results/campaigns/my-machine-candidate-001
python3 tools/build_site.py
```

`--case` and `--backend` may be repeated to select a subset. Profiles are:

| Profile | Independent forks | Schedule cycles | Untimed warmup turns |
| --- | ---: | ---: | ---: |
| smoke | 1 | 2 | 2 |
| standard | 3 | 50 | 32 |
| regression | 5 | 200 | 64 |

`--forks`, `--cycles`, `--seed` and `--timeout` are explicit controls. Changing
cycle count or warmup changes the measurement contract. Every output directory
must be new. A shared checkout lock prevents overlapping suite-owned campaigns
and worker builds. Other machine activity is uncontrolled, so these results are
informational until a dedicated runner is qualified.

Before measuring, an independent Python process computes the full
measurement-sized trajectory. Separate verification workers check every turn,
the no-execution control and retained snapshots, for both source and decoded
bytecode paths. Measurement workers warm a temporary instance, discard it,
activate a fresh instance and run the exact same bounded schedule. The final
measured output is checked again outside the timer. Timings from failed,
incorrect or partial cases never enter accepted summaries.

Each campaign preserves task/measurement contracts, ordinary Mech sources,
worker manifests, Cargo manifests and lockfiles, raw requests, stdout/stderr,
every fork observation, comparison order, summaries and `report.md`.
`evidence.json` hashes the retained inputs and observations. Process timeouts
terminate and reap the owned process group, including compiler/linker children.
Raw observations are also preserved byte for byte in deterministic `raw.tar.gz`
archives, with an archive hash and all original per-file hashes. Local `raw/`
directories are ignored caches. Builds verify and expand the archive for every
individual sample link; the dashboard also offers the complete archive download.

## Native build, runtime and footprint

After building the candidate worker with `--native`:

```sh
python3 tools/run_native.py --worker .local/candidate/worker.json --forks 3 --output results/campaigns/my-machine-native-001
```

The 128-node source chain goes through `ProgramCompiler`, canonical artifact
lowering, checked Cranelift object generation and a linked scalar application.
An untimed qualification build warms runtime/support dependencies. Each measured
fork generates a new project and includes compiler-worker startup, source
compilation, native generation, dependency lock resolution, support build and
link. Complete native processes run the declared A → B → A schedule; every
declared scalar output is consumed and the named result is checked independently.

Recorded outcomes include source-to-executable time, complete native lifecycle
time, object file bytes, object and linked code sections, executable bytes,
stripping policy and exact object/executable identities. Section reports are
retained; unavailable section metrics stay absent. Compiler-process-tree peak
memory is not claimed. This is the public **scalar** linked route, rather than a
claim of general hosted-native coverage. Generated applications use their normal
release policy, `strip = "symbols"`.

Choose `--experiment compiler_acceleration` when comparing compilers intended to
preserve output identity. The independent campaign comparison then additionally
requires identical object and executable hashes. `code_generation` allows code
to change while preserving task obligations and recording the footprint.

## Interpreting comparisons

Task contracts describe required values, shapes, ordering, multiplicity,
arithmetic and ownership. Measurement contracts describe the timed boundary,
input schedule, reset, warmup, cache and thread policy. Implementation details
remain provenance: reducing allocations or eliminating intermediate storage
does not invalidate an improvement. Compiler-attribution comparisons additionally
require the exact same source and environment.

Paired campaigns alternate a seeded baseline/candidate order within independent
fork blocks. They retain every sample. Fewer than five fork pairs produce an
informational ratio. Five or more permit a deterministic bootstrap screening
interval on paired log ratios, with a 5% practical effect threshold. A suspected
regression needs an independent confirmation campaign; no performance gate is
enabled. A fixed fork count is not a claim of sufficient precision.

To compare separate campaigns (independent, rather than paired observations):

```sh
python3 tools/compare_campaigns.py --baseline results/campaigns/run-001/campaign.json --candidate results/campaigns/run-002/campaign.json --metric resident_turn_seconds --output .local/comparison.json
```

The dashboard shows compatible history and median changes, marks incompatible
contracts, and links to the raw observations. It distinguishes progress
(`planned`, `implemented`, `verified`, `measured`), backend-specific capability
(`unknown`, `supported`), and actual outcomes (`ok`, `incorrect`, `error`,
`crash`, `timeout`). A failed attempt is not automatically labelled unsupported.

## Boundaries and current limits

| Outcome | Exact scope |
| --- | --- |
| Source-to-artifact | `ProgramCompiler.compile_source`; parsing and canonical semantic compilation |
| Encoding/decoding | Bytecode-v1 artifact serialization or validation/reconstruction |
| Resident activation | `activate_with_options`; planning, managed backing and instance creation |
| Resident turn | `ReactiveInstance.turn`; captured-input submission, managed execution, publication and summary |
| Initial turn | First accepted turn on the separate warmup instance; main execution block also includes its own first turn |
| Retention experiment | Above turn plus a copied result retained for every turn |
| Abort experiment | Prepared candidate destruction followed by an accepted turn |
| Output observation | Borrow and copied snapshot separately timed |
| Teardown | Instance and retained snapshot destruction, outside the turn timer |
| Managed storage | Admission-account live backing and planned arena capacity; not process RSS |
| Allocations | Allocation/reallocation calls and requested bytes over the whole execution block; counting-allocator overhead included |
| Worker peak RSS | Entire measured worker lifetime, including preparation; independent oracle excluded |
| Toolchain construction | Worker build duration in provenance; separate from compiling a Mech program |

The initial adapter admits one f64 scalar/vector input and the named `result`
output, observed as f64 scalar/matrix or set. The catalog declares the concrete
task and schedule for each case. Reserved/committed/pinned/device ledger
categories not exposed by this adapter are not approximated by the aggregate
admission counter. Pure preparation boundaries are reported as enclosing
operations rather than invented internal phase timings.

Existing compiler correctness tests stay in `mech-lang/mech`. Catalog entries
link to relevant maintained tests; these are evidence pointers, not claims that
unit-test duration is a benchmark. Here, the benchmark repository owns ordinary
source fixtures, the out-of-tree revision adapter, campaigns, reports and UI.

## Existing applications and expansion

The current cross-language catalog, samples, fixed chart baselines, reproduction
records, optimization history and application source bundles remain authoritative.
The campaign exporter writes `campaigns.json` beside that catalog and never
imports resident timings into cross-language rankings.

K-nucleotide and N-body retain links to their full historical task contracts.
Automating those qualified full-size programs, the relevant Deflate stream
contract (including Roc/libdeflate controls), EKF, broader table/graph/string
coverage, rejected-candidate scenarios, capacity sweeps, JVM comparisons and
controlled-runner performance gates are named planned cases. The small spring
simulation is a numerical mechanism application, not a replacement qualification
for N-body or EKF.

Add a new ordinary `.mec` fixture, independent oracle and task/measurement entry
to broaden the suite. Deterministic alternate values, signs, empty/nonempty
outputs and sizes around 7/8 and 31/32/33 already exercise generalization within
the initial fixtures. Larger size/source-form sweeps should become explicit
cases, with their own task contracts and preserved inputs.

## Checks

```sh
python3 -m unittest discover -s tools/tests -v
node site/tests/campaigns.mjs
RUSTC_BOOTSTRAP=1 cargo test --release --manifest-path .local/candidate/Cargo.toml
```

The adapter's timing self-check keeps preparation and slow output destruction
outside the same timing helper used by the real worker. Supervisor tests reject
stale/aliased answers, changed snapshots, malformed/nonfinite results, missing
outputs, binary changes and incompatible comparisons, and exercise process-tree
cleanup. CI runs these checks plus small current-architecture correctness
campaigns. Shared-runner timing changes never fail CI.
