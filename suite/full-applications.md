# Full application and scaling measurements

The suite keeps its full application anchors alongside the small mechanism cases.
`run_applications.py` never substitutes the smoke profile for these workloads:

| Task | Required work | Independent validation |
| --- | --- | --- |
| K-nucleotide | FASTA N=25,000,000; 254,166,745 input bytes; 125,000,000 selected bases | Separate C byte-string oracle; both complete frequency tables and all five query counts match the preserved full output |
| N-body | Five bodies, 50,000,000 steps | Separate Java implementation; initial and final energy, declared f64 tolerance |
| Deflate | Nine maintained small streams, both 16,384/33,027-byte boundaries, entire 6,627,202-byte Reymont corpus | Pinned Roc level-12 bytes plus independent Python zlib inflation, EOF and trailing-data checks; libdeflate must produce a valid complete stream |
| Worker scaling | Fixed total 196,608 accepted nonlinear numerical turns across 1, 2 and 4 independent processes | Complete distinct-input schedule, no-execution control, accepted iteration counts, every process endpoint and managed teardown |

Source fixtures and small/boundary streams live in `suite/applications/`. The
large FASTA file is reproduced with the preserved `fasta.c` and argument
`25000000`. The complete Reymont corpus is retrieved from the
[Silesia corpus](https://sun.aei.polsl.pl/~sdeor/index.php?page=silesia), with SHA-256
`0eac0114a3dfe6e2ee1f345a0f79d653cb26c3bc9f0ed79238af4933422b7578`.
The runner refuses a shortened or different corpus. Campaign evidence retains
the complete compression inputs, prefixes and expected streams losslessly.

Rust is the suite control; see [controls.md](controls.md) for measured Rust and
retained Mech controls. Java is used only as an independent N-body correctness
oracle. Its earlier JVM timing remains in historical evidence, outside the active
catalog. Related Post Gen's full retained cohorts are also available in metrics.

## Execution and measurement contracts

The ordinary source and decoded resident cases use the canonical
`ProgramCompiler` / `ProgramArtifact` / `ReactiveInstance` architecture. EKF
explicitly uses the maintained `frozen-ekf-v1` compiler catalog and exact source
fixture. Its independent Python implementation validates all 12 state/covariance
values for all 4,096 turns. It is a conformance-profile measurement, not a claim
that every EKF library operation is exposed by the general standard catalog.

The scalar JIT case uses checked `lower_pure_native_artifact`, `JitArtifact` and
`evaluate_into`. Preparation and invocation are separate observations. The
Deflate program uses public `JitProgramArtifact::compile_with_limits` and
`evaluate_into`, finite compilation/launch/library limits, managed inputs and
owned outputs. A fresh compiler process is created for every fork. It compiles
one complete program, then runs the 12 independently validated inputs. Its
compile measurements are shared by those cases within that fork. The call timer
includes stateless activation, checked execution, publication and scratch cleanup;
input import, warmup and returned-output destruction are outside the call.
The complete compiler/worker process is also preserved in raw supervision.
No unrestricted compilation or `NoLimits` execution is selected.

The linked Deflate route was actually attempted and hit the pinned compiler's
64 MiB descriptor-image packing limit. A larger *finite definition-table budget*
allows lowering but does not remove that separate image limit. Those failed
qualification receipts remain evidence; the complete program is measured through
the checked JIT route. This does not imply that a linked application was produced.

K-nucleotide uses the public typed source-native sequence CLI. N-body uses the
public canonical-artifact fused numerical CLI in `jit-simd` mode, with all optional
arithmetic transformation flags disabled. These are explicit application lanes.
They are not reported as managed resident-turn measurements: the fused numerical
loop omits per-turn resident admission. Whole-process measurements include their
source compilation, JIT preparation, application input/output and shutdown.
Java includes HotSpot startup, JIT execution, output and shutdown; class compilation
is excluded. Its application thread count and GC/JIT flags are recorded.

Roc and libdeflate remain separate, actually executed controls. Roc source
`671077457ff7ef3a3d44caf715a3fc595addf379` and compiler
`d99c7b838fb05bb1047eb0c18d4d06d0f86f345d` are pinned. libdeflate 1.26 is pinned at
`92e6a0db9fa848d742f9eb286c92afc60f2c3dda`. Both controls use system allocation,
level 12, runtime inputs, distinct returned output and held input/prepared-output
aliases. Their complete call includes compressor scratch setup and cleanup.
Their transports, output reservations, warmup and allocation boundaries differ
from Mech's checked program call. They do not inherit the older diagnostic
81-case cohort's warmup, allocator or ratio qualifications. The dashboard does
not manufacture a qualified cross-runtime speed ratio from these results.

The capacity cases request output cardinalities around 0, 8, 16, 32 and 64 while
always inspecting the full 65-element capture. Growth, shrink and reuse appear
in each schedule. Actual allocation, managed storage and publication costs are
observations; a requested cardinality does not assert a physical capacity change.
The rejection case tests capture-admission rollback followed by valid publication.
The FSM case tests actual suspension, resumption and a frozen Unicode capture;
it is a pure FSM with no external effects. These cases do not imply coverage of
execution-time invariant rejection, effectful FSMs or shared-state parallelism.

## Reproduction

Build the canonical worker and the two application CLI executables in separate
profiles. This also keeps the optional GMP/Rug sequence dependencies out of the
canonical native compiler profile.

```sh
python3 tools/build_worker.py --mech /path/to/pinned-mech --revision 9087b1f07727a9bfcb7c09059f48edaca6dc2301 --output .local/canonical --native --online
python3 tools/build_worker.py --mech /path/to/pinned-mech --revision 9087b1f07727a9bfcb7c09059f48edaca6dc2301 --output .local/applications --applications --online
python3 tools/prepare_controls.py --roc /path/to/pinned/roc --reference /path/to/pinned/roc-deflate --libdeflate /path/to/pinned/libdeflate --output .local/controls
python3 tools/run_applications.py --worker .local/canonical/worker.json --application-worker .local/applications/worker.json --controls .local/controls/controls.json --java /path/to/jdk/bin --fasta /path/to/full.fasta --corpus /path/to/reymont --output results/campaigns/NEW-FULL-RUN
python3 tools/run_concurrent.py --worker .local/canonical/worker.json --output results/campaigns/NEW-SCALING-RUN
```

Application CLI compilation needs system GMP/MPFR headers and libraries; record
`C_INCLUDE_PATH` and `LIBRARY_PATH` when supplying their locations. All binaries,
source adapters, dependency locks, policies, compiler revisions and commands are
hash-pinned in evidence. No timing threshold fails CI on a shared runner.

## Attribution and licensing

The N-body Java source retains its original Computer Language Benchmarks Game
author credits. The FASTA C generator retains Paul Hsieh's credits and upstream
reference. Historical Mech application sources are copied without algorithm edits
from this repository's retained workload archive. The complete Mech compressor
is assembled byte-for-byte from the pinned compiler's maintained
`hosts/gpu/tests/fixtures/native/deflate_assembly.rs` components; its source SHA-256
is `742567bc0abc6f37209ac5f82c1e2a05647f35db8ea6368bef81d04b9a03b552`.
It is the maintained port of the pinned Roc/libdeflate algorithm, not a new
compressor implementation in this harness. External control source inventories
and licenses belong to their pinned upstream distributions.
