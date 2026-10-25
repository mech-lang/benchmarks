# Maintained canonical hosted runner

This crate owns full-input and staged qualification/performance orchestration.
The frozen predecessor lives separately in
`archive/compiler/mech-pre-911-bbd66acb9/source/hosts/gpu/tests/support/`.
Changes here do not rewrite historical evidence. Normal Mech correctness tests
use a compact local policy control and do not fetch this archive or crate.

Mech's current build harness remains responsible for building and checking its
candidate binaries, generated launchers, tamper/rebuild/recovery controls and
runtime-only closure. It passes original/decoded binary result rows plus an
explicit `Qualification`: immutable runner commit, candidate Mech commit, exact
source SHA256 and the current small-gate launch policy. The runner refuses
missing/malformed revision pins or disagreement with either source pin before
dispatch. Receipts record both revisions. The process supervision dependency is
the existing `mech-build` implementation, pinned in Cargo.toml and Cargo.lock.

The API preserves the existing opt-in configuration/environment names and
finite policies. `run` and `run_comparison` execute configured single or staged
workloads; `comparison_control` accepts an explicit configuration, including
zero timing samples. Both original/decoded binaries run secured/trusted during
comparison qualification: exactly four required correctness executions before
any samples. Every output is compared in full. Partial failures retain attempt
receipts and cannot qualify or publish a timing sample count.

Tests move with the runner, including strict/duplicate JSON, mutation, launch
derivation, four-way accounting, failed-attempt and partial-stage receipt
contracts. They run independently of any frozen archive implementation:

```sh
cargo +nightly-2026-03-03 test --manifest-path tools/canonical-hosted-runner/Cargo.toml --locked
```

Fresh machines need network access to fetch the pinned dependencies first;
subsequent tests may use `--offline`. Full measurements also require the actual
predeclared absolute input/oracle/launch paths, SHA256 pins, finite deadlines
and `MECH_CANONICAL_HOSTED_TIMING_SERIAL=1`. The attestation is required for
nonzero samples; it is not evidence that unrelated host processes were idle.

The executable consumes Mech's `release-qualifier-results.json` after all
current-candidate small gates, launcher tests and pin/rebuild controls complete:

```sh
cargo run --release --locked --manifest-path tools/canonical-hosted-runner/Cargo.toml -- \
  comparison /absolute/results.json /absolute/fresh-evidence \
  CANDIDATE_MECH_COMMIT RUNNER_COMMIT SOURCE_SHA256 /absolute/small-launch.json
```

Use `production` for the production launcher pair. Set the existing single or
staged configuration environment variable for this process, rather than Mech's
small-gate process. Both revisions must be full immutable commit IDs; the source
SHA256 must agree with both already-qualified result rows. The small launch
policy is the current candidate's unchanged gate policy, exported separately.
Build/check out the runner at `RUNNER_COMMIT` and retain the invocation alongside
the resulting receipts. Timing remains serial and includes every spawned
application's complete process lifecycle; compiler builds precede it.
