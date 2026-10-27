# Post-architecture native cleanup

This is the primary evidence study for the cleanup following mech-lang/mech
#935 and preceding the 19 downstream PRs. The audited source is
`01b8b397011b6a774b7d9f730578a4ef92bf30f6`. Its retained public AOT executable
and build receipt in `../native-architecture-consolidation-v1/` remain historical
evidence. The actual before subject must be the final repaired #935; the after
subject must be the cleanup directly above it. The current prospective sources
are architecture `7543c56d5efc4df30d0b60961922024d74caa9d7` (#935) and cleanup
`a68fb2e60d7afbc59bc146f8878b17181e275645` (#939). The complete Rust cleanup
patch preserves the six-profile/four-runtime-closure checkpoint; exact final-head
qualification remains in progress. Fresh public builds at all three published
heads have passed independent validation; their six ordinary guest artifacts
are byte-identical, and the actual build receipts are now adopted. The earlier
`a3e805a`/`870fdde` builds and fourteen changed-input executions remain historical
evidence at their original pins. Their receipts do not qualify these new heads.
The former b05/569 subjects also remain recorded in `plan.json`. No candidate
has final timing qualification.

`changed-inputs-published-a68fb2e-v1/` passes all seven direct-oracle cases on the
actual architecture/cleanup binaries (fourteen executions with independently
checked output, update, pin and process-cleanup receipts). The shared
`../native-architecture-consolidation-v1/supplemental-wide-slot-published-v1/`
proof passes all six public source/decoded builds at the three published heads
and the mandatory gate for this study. Neither result qualifies runtime speed.

`audit/` retains the complete 363-file inventory, exact-body candidates,
256 resolved default-module paths, 19 inherited feature guards, and original
migration/architecture documents with hashes. These records preceded code edits.
They establish provenance and candidate deletions; existing semantic contracts
and exact before/after evidence determine whether a consolidation is acceptable.

Manual window/histogram timings and region inspection are maintained under
`tools/native-compiler-probes/` in this repository. Their exact original Rust
source is preserved. They are diagnostic tools with a pinned test overlay;
complete-process performance qualification remains a separate study gate.

`probe-compile-569aa84-v1/` preserves all three actual preparation attempts.
The corrected host-feature build compiles both harnesses at `569aa84` and selects
each of the three exact ignored probes once, with clean bounded process receipts.
No probe body or primary timing sample was run. The earlier interrupted compile
and empty-selection failure remain recorded alongside the successful attempt.

The final plan must pin the actual after-cleanup source and public AOT file,
verify unchanged source/output/resource contracts, and compare before/after
k-nucleotide timings using the retained W/R controls and the same two-session
192-observation acceptance policy. There are zero primary timing samples for
this cleanup. Full raw receipts and unsuccessful attempts remain part of the
study. No historical performance claim is transferred to the new candidate.

`plan.json` is **UNFROZEN**. It retains the original workload/control pins,
two-session schedule and acceptance policy. Its source candidates are recorded,
while fresh F/I build receipt adoption remains pending. The before receipt will be an immutable
hash-pinned reference to architecture F; the cleanup candidate receipt stays
local. Both studies adopt the same hash-pinned
`runtime-environment-v1.json`. `retained-controls.json`
is a byte-for-byte snapshot of the same W/R provenance; no control was rebuilt.
Final correctness, generated-process, changed-input, 32 representative and wide-slot artifact evidence must be
adopted before filling qualification/controller pins and freezing the plan.

Use the shared implementation in `../native-architecture-consolidation-v1/`:

```sh
python3 experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1/build-candidate.py \
  --study post-native-architecture-cleanup-v1 \
  --workspace /path/to/final-cleanup --target-dir /path/to/its-own-target --run-id F_RUN_ID
```

The build command becomes usable after the actual candidate source is adopted.
The same `--study` choice selects this directory for `changed-inputs.py`,
`measure.py`, `analyze.py` and `qualify.py`; no controller or analysis code is
copied into this study. An unfrozen plan cannot start the primary campaign.

The before-build may be adopted without rebuilding by setting `baseline_receipt`
to a hash-pinned `{study_id, path, sha256}` reference to the final #935 public AOT
receipt in the architecture study. Its original build-subject label remains F;
this plan explicitly assigns that immutable file the role I. Candidate receipts
and all primary observations stay local to this study.

Both plans must explicitly adopt one identical `runtime_environment_receipt`
before changed-input checks or primary sampling. This avoids changing the runtime environment merely
because architecture F becomes cleanup I. The shared receipt format and
pre-sampling commitment rules are documented in the architecture study README.
Final source/build qualification is pending; no placeholder is executable.

`audit/final-rebase-870fdde-v1/` proves all 113 Rust cleanup patches remained
byte-identical through the launcher-fixture rebase. The final independent review
is retained at `audit/final-independent-review-870fdde-v1.json`.
`audit/downstream-restack-v3/` records the verified local 19-branch stack and its
preserved original patches/authors; it does not claim remote publication.

## Final build metrics and secondary prefix diagnostic

`public-build-metrics-final-v1.json` records actual pinned executable sizes and
separate compiler/public AOT build durations, with exact raw receipt references.
The values retain their original cache and concurrent-build conditions. Retained
W/R historical build scopes are listed separately in that record.

| Subject | Executable bytes | Compiler build (s) | Public AOT build (s) |
| --- | ---: | ---: | ---: |
| F (`870fdde`) | 5,550,864 | 852.457 | 175.230 |
| I (`a3e805a`) | 5,550,864 | 602.947 | 199.701 |

`secondary-prefix-protocol.json` prospectively pins the original million-base
THREE input, independently verified exact output, native counters, final F/I/W/R
executables and unchanged primary policy. The shared `secondary-prefix.py`
entrypoint validates all four completed primary sessions before it can execute
its single 16-observation block. It records all observations and per-subject
medians, without warmups, exclusions, replacement samples or a performance
acceptance claim. The entrypoint has not been run; prefix time remains pending.

After both primary campaigns validate, use:

```sh
python3 experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1/secondary-prefix.py \
  --study post-native-architecture-cleanup-v1
```
