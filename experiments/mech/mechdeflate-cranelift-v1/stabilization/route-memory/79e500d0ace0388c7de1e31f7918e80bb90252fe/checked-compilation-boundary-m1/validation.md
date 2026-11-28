# Checked compiler boundary validation

Baseline F is `3a66a014c853e082ad907ed4db1673c9dadf0c69`. The tested and measured candidate C is `79e500d0ace0388c7de1e31f7918e80bb90252fe`.
The checks ran on native Apple M1 with Rust nightly-2026-03-03 and locked offline dependencies.
Execution used the release profile and one test thread. The public linked test retained its generated-app profile.

| Check | F | C |
| --- | --- | --- |
| Compiler coordinator | [5 passed, 1 ignored](baseline/coordinator.log) | [5 passed, 1 ignored](candidate/coordinator.log) |
| Certified scalar primitives | [1 passed](baseline/scalar-primitives.log) | [1 passed](candidate/scalar-primitives.log) |
| Checked scalar denial | [1 passed](baseline/scalar-denial.log) | [1 passed](candidate/scalar-denial.log) |
| Program denials and recovery | [1 passed](baseline/program-denials.log) | [1 passed](candidate/program-denials.log) |
| Arithmetic denial after a library call | [1 passed](baseline/program-library-denial.log) | [1 passed](candidate/program-library-denial.log) |
| Secured k-nucleotide | [1 passed](baseline/secured-knucleotide.log) | [1 passed](candidate/secured-knucleotide.log) |
| Secured denial and recovery | [1 passed](baseline/secured-recovery.log) | [1 passed](candidate/secured-recovery.log) |
| Independent artifact producer | Candidate only | [1 passed](candidate/independent-producer.log) |
| Public linked k-nucleotide | [1 passed](baseline/public-linked-knucleotide.log) | [1 passed](candidate/public-linked-knucleotide.log) |
| Compiler-only library check | [passed](baseline/compiler-feature.log) | [passed](candidate/compiler-feature.log) |
| Runtime-only library check | [passed](baseline/runtime-feature.log) | [passed](candidate/runtime-feature.log) |

The coordinator's full-encoder test remains ignored. Every explicitly selected test executed.
All prescribed checks were supported on the M1. The runtime-only dependency tree excludes Cranelift. [Dependency tree](runtime-dependency-tree.log)

## Exact command transcript

The baseline and candidate used the same selectors, with the independent producer on C only.

```sh
cargo +nightly-2026-03-03 test --release --locked --offline -p mech-gpu --no-default-features --features canonical-native-program-host --lib native_artifact::program::compilation_report::tests:: -- --test-threads=1
cargo +nightly-2026-03-03 test --release --locked --offline -p mech-gpu --no-default-features --features canonical-native-program-host --test canonical_artifact_native all_certified_scalar_primitives_match_ordinary_resident_original_and_decoded -- --exact --test-threads=1
cargo +nightly-2026-03-03 test --release --locked --offline -p mech-gpu --no-default-features --features canonical-native-program-host --test canonical_artifact_native checked_u64_failure_matches_resident_and_never_publishes_partial_outputs -- --exact --test-threads=1
cargo +nightly-2026-03-03 test --release --locked --offline -p mech-gpu --no-default-features --features canonical-native-program-host --test canonical_artifact_program generated_denials_preserve_every_prior_output_and_allow_recovery -- --exact --test-threads=1
cargo +nightly-2026-03-03 test --release --locked --offline -p mech-gpu --no-default-features --features canonical-native-program-host --test canonical_artifact_program generated_arithmetic_denial_after_a_library_call_keeps_prior_typed_roots -- --exact --test-threads=1
cargo +nightly-2026-03-03 test --release --locked --offline -p mech-gpu --no-default-features --features canonical-native-program-host --test canonical_hosted_artifact complete_knucleotide_original_and_decoded_run_through_actual_secured_cli -- --exact --test-threads=1
cargo +nightly-2026-03-03 test --release --locked --offline -p mech-gpu --no-default-features --features canonical-native-program-host --test canonical_hosted_artifact failed_native_body_prepares_no_effect_and_recovers_without_retaining_native_memory -- --exact --test-threads=1
cargo +nightly-2026-03-03 test --release --locked --offline -p mech-gpu --no-default-features --features canonical-native-program-host --test canonical_artifact_program compilation_boundary::source_and_direct_artifacts_use_the_same_checked_boundary -- --exact --test-threads=1
cargo +nightly-2026-03-03 test --release --locked --offline -p mech --no-default-features --features full_compiler,cranelift_build --test canonical_native_build public_source_and_bytecode_builds_run_unchanged_knucleotide_without_fallback -- --ignored --exact --test-threads=1
cargo +nightly-2026-03-03 check --locked --offline -p mech-gpu --no-default-features --features canonical-native-program --lib
cargo +nightly-2026-03-03 check --locked --offline -p mech-gpu --no-default-features --features canonical-native-program-runtime --lib
```

## Compact rebuild

The candidate recipe updates the source commit. Its source bytes, settings, profiles and expected artifacts match the frozen recipe.
All three artifacts matched their pinned SHA-256 values, and the 26 runtime-support tests passed.
[Rebuild command and result](rebuild.log) · [Artifact hashes and sizes](artifact-preservation.json) · [Candidate recipe](candidate-recipe.json)

## Bounded compiler cost

One warmup per compiler preceded four source-to-artifact pairs. Negative changes mean C used less time or peak RSS.

| Pair | Order | F elapsed (ms) | C elapsed (ms) | F peak RSS (bytes) | C peak RSS (bytes) |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | F then C | 2174.969417 | 2180.027292 | 393,478,144 | 393,576,448 |
| 2 | C then F | 2149.992708 | 2173.334750 | 393,461,760 | 393,560,064 |
| 3 | F then C | 2173.380958 | 2178.030708 | 393,461,760 | 393,560,064 |
| 4 | C then F | 2173.955125 | 2170.252750 | 393,543,680 | 393,248,768 |

The median paired difference was +4.853813 ms and +98,304 bytes peak RSS for C relative to F.
The sample uses the same compact input and settings for both compilers.
[Raw pairs, warmups, and emitted sizes](compiler-cost/compiler-cost.json)
