# Native route memory qualification

Use the Mech source and benchmark tooling commits in each campaign manifest.
The fixed controls are the reviewed compiler R and the previous measured
compiler O. Create a fresh directory under
`stabilization/route-memory/<candidate-sha>/<campaign-id>/` for every new
candidate or measurement implementation. Keep `campaign.json`, the bound
recipe, and `prepared-bindings.json` in that directory. The manifest binds
the committed tooling files, the recipes, actual builds, machine, corpus
and policy. [Fixed policy](policy.json)

Use the maintained `rebuild.py` for new actor builds. The shared-fixture
qualification reuses the exact bound compilers, workers and correctness
receipts from the integrated campaign. The compiler scope uses ordinary
fresh compiler processes with reporting and census disabled. Retain
previous campaign directories and any partial or unfavorable observations.

For this final qualification, resolve `BENCH_ROOT` and the existing parent
of the new campaign before choosing its basename. Create that new `RUN`
directory once. In the pinned tooling checkout, run this preparation
command from `BENCH_ROOT`.

```sh
PYTHONPATH="$PACKET" python3 -B - "$RUN" "$BENCH_ROOT" <<'PY'
import json
from pathlib import Path
import sys
from replay import prepare_fixture_stage

run, bench = (Path(value).resolve(strict=True) for value in sys.argv[1:])
binding = prepare_fixture_stage(run / "fixture-stage", bench / "experiments/mech")
print(json.dumps(binding, indent=2))
PY
```

Include the printed binding as `fixture_stage` in the campaign manifest.
Bind the complete host record with the Mach timebase reported by
`campaign_host()`. The active controller and all four actors use the
shared stage paths through every runtime leg. Each leg writes results
and its execution receipt under its own `suite81` directory.

Set `PACKET` to the absolute benchmark packet directory and `RUN` to the
absolute campaign directory. Run each stage serially with `SCOPE=compiler`.

```sh
CAMPAIGN="$RUN/campaign.json"
CALIBRATION="$RUN/$SCOPE/calibration.json"
python3 -B "$PACKET/compare_rebuilt.py" --campaign "$CAMPAIGN" --scope "$SCOPE" --stage calibrate
python3 -B "$PACKET/compare_rebuilt.py" --campaign "$CAMPAIGN" --scope "$SCOPE" --stage qualify --calibration "$CALIBRATION"
python3 -B "$PACKET/compare_rebuilt.py" --campaign "$CAMPAIGN" --scope "$SCOPE" --stage confirm --calibration "$CALIBRATION"
python3 -B "$PACKET/compare_rebuilt.py" --campaign "$CAMPAIGN" --scope "$SCOPE" --stage assess --calibration "$CALIBRATION"
python3 -B "$PACKET/verify.py" --campaign "$CAMPAIGN" --campaign-record "$RUN" --scope "$SCOPE"
```

A memory-repair campaign ends with its compiler assessment. After a
passing compiler assessment for this same manifest, run the calibration
and verification commands with `SCOPE=runtime`. Inspect the calibration
seal before candidate timing. The verifier checks the shared execution
paths and each crossover mapping, then forms crossed cycles with ratios
oriented to the actual compilers. A passing seal requires zero inclusion
for both controls and log interval widths at or below the pinned widths
for all eight precision coordinates. With a passing seal, run qualification,
confirmation, assessment and final verification in order. An unresolved
seal ends the campaign at calibration. [Precision reference](3a66a014c853e082ad907ed4db1673c9dadf0c69/F-m1-20261126T181433Z/runtime/calibration.json)

Compiler sessions rotate their starting slot by session ordinal. The
rotation assigns each role to each absolute launch position across every
three sessions. Each individual session retains one warmup per role and
all six permutations. For campaigns already collected, use the tooling
and policy pinned in their manifests.

The integrated source passed correctness and compiler qualification on M1.
The final runtime candidate remains unmeasured after the same-build runtime
calibration returned unresolved. The assessment links the complete calibration
and the timing diagnostics. [Round 2 assessment](3a66a014c853e082ad907ed4db1673c9dadf0c69/F-m1-20261126T181433Z/assessment.md)

## Runtime continuation

Use purpose `runtime-continuation` for the fixed M1 continuation. Its compiler
parent is the completed shared-fixture campaign
`F-m1-shared-fixtures-20261127T044557Z` at tooling
`0108617d529244d87e34fcbda26fb64170333f44` and evidence
`d827ea55471c2d7000cd2addc9b105a15699e2ec`. Keep its original compiler
records available at the paths declared in its manifest. The verifier reads the
pinned Git blobs and reconstructs its calibration, qualification, confirmation
and assessment from the raw records. It writes `parent-verification.json` in
the new run after successful reconstruction.

Create a new canonical run named `F-m1-runtime-continuation-<UTC timestamp>`.
Use the shared-stage preparation command above with this new run. Carry the
parent's complete R, O and F bindings, recipes, corpus, host and fixed policy
into the new manifest. Bind the parent paths and hashes in `compiler_parent`
and pin the continuation tooling commit. The runtime precision reference is
the earlier calibration pinned in the policy.

After preparation, run the verifier with `--scope runtime` before collecting
observations. A valid prepared continuation reports its reconstructed compiler
decision and runtime `not_run`. A verified unresolved compiler parent is
eligible for runtime calibration. The continuation forbids compiler collection.

Run the six-session runtime calibration once and verify its seal. Use the
runtime calibration decision, including its precision checks, to determine
whether to collect qualification and confirmation. An unresolved calibration
ends collection before candidate timing. The report records the compiler,
calibration, runtime and combined decisions and the completed session counts.
A passing runtime assessment with an unresolved compiler parent leaves the
combined assessment unresolved.
