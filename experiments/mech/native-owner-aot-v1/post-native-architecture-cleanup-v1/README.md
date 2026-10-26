# Post-architecture native cleanup

This is the primary evidence study for the cleanup following mech-lang/mech
#935 and preceding the 19 downstream PRs. The audited source is
`01b8b397011b6a774b7d9f730578a4ef92bf30f6`. Its retained public AOT executable
and build receipt in `../native-architecture-consolidation-v1/` remain historical
evidence. The actual before subject must be the final repaired #935; the after
subject must be the cleanup rebased above it. The current source candidates are
architecture `b05a3f8a81e34b39b625b7e55c1bf90790ca1092` and cleanup
`569aa84ed0e80c08e954fe39add6f83ab21e5a3a`; fresh public build receipts and
complete qualification remain pending. Neither candidate has timing evidence.

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
but F/I build receipts remain null. Both studies adopt the same hash-pinned
`runtime-environment-v1.json`. `retained-controls.json`
is a byte-for-byte snapshot of the same W/R provenance; no control was rebuilt.
Final correctness, generated-process, changed-input and object evidence must be
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
