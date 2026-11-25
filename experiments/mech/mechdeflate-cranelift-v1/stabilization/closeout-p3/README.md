# Native route qualification

This packet qualifies one scheduling change against the reviewed compiler and
the configuration closeout. [Fixed campaign policy](policy.json)

## Restore the pinned checkouts

Use the benchmark tooling commit and the three source commits in the campaign
manifest. Keep that manifest and its evidence outside either source checkout.
Use build and output directories specific to the host. The recorded M1 and
M3 sessions are independent campaigns.

```sh
python3 - "$CAMPAIGN" <<'PY'
import json
from pathlib import Path
import subprocess
import sys

campaign = json.loads(Path(sys.argv[1]).read_text())
bench = campaign["bench_root"]
subprocess.run(["git", "-C", bench, "checkout", "--detach", campaign["tooling_commit"]], check=True)
for label, source in campaign["actors"].items():
    pin = campaign["source_commits"][{"reviewed": "R", "closeout": "C", "candidate": "O"}[label]]
    subprocess.run(["git", "-C", source["source"], "checkout", "--detach", pin], check=True)
PY
```

Materialize all five benchmark packet directories in the pinned checkout.
A sparse checkout must include all files under each of these directories.

```text
experiments/mech/mechdeflate-cranelift-v1
experiments/mech/mechdeflate-81-v1
experiments/mech/mechdeflate-phase-routes-v1
experiments/mech/mechdeflate-masked-fields-v1
experiments/mech/mechdeflate-silesia-v1
```

Install the pinned Rust toolchain and prepare the complete Silesia corpus with
the existing `fetch_silesia.py --manifest` command. Use each actor's absolute
`source`, `recipe` and `build` paths from the manifest to prepare its ordinary
compiler and timing executables. The runner checks the source pin, profile
digests, native object, bytecode, descriptor and runtime support.

```sh
PACKET="$BENCH_ROOT/experiments/mech/mechdeflate-cranelift-v1"
python3 -B "$PACKET/rebuild.py" --recipe "$RECIPE" --mech-root "$SOURCE" \
  --output "$BUILD" --bench-root "$BENCH_ROOT"
```

For the maintained ignored encoder test, use the `--qualify-encoder` option
with a fresh evidence directory. Run host reporting and construction-census
diagnostics separately from ordinary compiler timings.

## Run the fixed sessions

Run one stage at a time on a quiet qualification machine. The two controls
each get three A/A calibration sessions. Three qualification sessions and
three confirmation sessions then compare the candidate to both controls.
The verifier recomputes the bootstrap and reference decisions from sealed
records without running the benchmarks.

```sh
python3 -B "$PACKET/compare_rebuilt.py" --campaign "$CAMPAIGN" --stage calibrate
python3 -B "$PACKET/compare_rebuilt.py" --campaign "$CAMPAIGN" --stage qualify \
  --calibration "$RUN/calibration.json"
python3 -B "$PACKET/compare_rebuilt.py" --campaign "$CAMPAIGN" --stage confirm \
  --calibration "$RUN/calibration.json"
python3 -B "$PACKET/compare_rebuilt.py" --campaign "$CAMPAIGN" --stage assess \
  --calibration "$RUN/calibration.json"
python3 -B "$PACKET/verify.py" --campaign-record "$RUN" --campaign "$CAMPAIGN"
```

Keep the manifest, session start markers, complete raw records and stage
seals together. A stage can resume sessions that have not started. Keep any
incomplete session as evidence and start a newly identified campaign if a
restart is required.
