# Mech native build and footprint campaign

Ordinary source → canonical ProgramArtifact → checked scalar Cranelift object → linked application. All scheduled inputs and the explicitly named result are checked against an independent Python oracle.

Runtime/support dependencies are warmed by the separate qualification build. Each measured fork creates a new project. Source-to-executable includes worker startup, source compilation, lowering/codegen, dependency lock resolution, support generation/build and final link. Complete-process time includes startup, admission, invocation, complete output and shutdown.

Outcome: ok. Experiment: code_generation.

| Measurement | Median |
| --- | ---: |
| executable_bytes | 2968960 |
| linked_text_bytes | 2076508 |
| native_generation_seconds | 0.00771025 |
| native_process_seconds | 0.0518986807 |
| object_bytes | 21824 |
| object_text_bytes | 21136 |
| source_to_artifact_seconds | 0.08259975 |
| source_to_executable_seconds | 6.36790246 |
| support_build_link_seconds | 6.10874367 |

Release stripping policy: symbols stripped by the generated application profile. Exact object/executable hashes, code-section reports, compiler logs, generated input pins and raw process samples are retained. Compiler-process-tree memory is not measured. These scalar measurements make no general hosted-application or resident-turn claim.
