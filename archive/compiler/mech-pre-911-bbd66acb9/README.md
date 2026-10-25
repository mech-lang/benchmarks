# Mech before the #911 cleanup

Frozen source: `mech-lang/mech@bbd66acb9b3beacdc95356084df259ca172c8b98`
(#910). The downstream #911 head observed for this work was
`e070bec0f24ce78cb192d0c10380197bbc927376`.

`source/` preserves original bytes and paths. `manifest.json` records repository,
commit, repository-qualified original path, archive path, Git blob, SHA256, byte
size and classification for every file. Historical receipts retain their original
qualifications and describe their recorded revisions, not the cleanup candidate.
The frozen full-input runner is historical replay material; maintained tooling
and current candidate regression tests must qualify future changes separately.

Verify from the benchmark repository root:

```sh
python3 archive/compiler/mech-pre-911-bbd66acb9/verify.py
python3 archive/compiler/mech-pre-911-bbd66acb9/test_historical_receipt.py
python3 tools/resolve_archive.py mech-lang/mech/docs/validation/benchmark-compiler-status-v1.json
```

To compare every archived byte to the original Git objects, add
`--mech /absolute/path/to/mech` to `verify.py`. This does not require checking out
the historical revision.

## Replay

Use a separate Mech checkout at the full source commit above. Use its preserved
`Cargo.lock` and Cargo manifests, and the feature profiles and exact selectors in
`source/.github/workflows/ci-full.yml` and `ci-native-plan.yml`. These workflows
pin `nightly-2026-03-03`; retain their platform-specific setup and environment.
For example, from that original Mech checkout:

```sh
cargo +nightly-2026-03-03 test --locked -p mech-gpu --features canonical-native-program-host --test canonical_hosted_artifact
cargo +nightly-2026-03-03 test --locked -p mech-gpu --features canonical-native-program-host --lib complete_secured_knucleotide_original_and_decoded_setup_debit_diagnostic -- --ignored --exact
```

The diagnostic's full test path includes its enclosing modules; list it first
with `-- --list` and use the complete name with `--exact`, verifying one execution.
Receipts themselves retain commands, inputs, expected outputs, environment,
toolchain identities and machine-specific paths. Those references are evidence,
not a promise that external files or binaries are available. Full-input replay
requires the separately pinned input/oracle/launch configuration and explicit
serial measurement attestation documented by the frozen runner. No external
input, executable, machine state or measurement has been regenerated here.

`test_historical_receipt.py` transfers the PR903 receipt-specific unique-key and
publication-history test. The complete original Python module is frozen under
`source/tests/ci/`; its other workflow tests remain current Mech responsibilities.
Print-only inventory and accounting observations are historical diagnostics;
actual work charging, visits, transaction publication and finite-denial tests
remain compiler/runtime responsibilities. See the cleanup's coverage-transfer
ledger for current selectors and execution evidence; archive verification alone
does not qualify a compiler candidate.
