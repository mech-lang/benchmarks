# Native route memory qualification

Use the Mech source and benchmark tooling commits in each campaign manifest.
The fixed controls are the reviewed compiler R and the previous measured
compiler O. Create a fresh directory under
`stabilization/route-memory/<candidate-sha>/<campaign-id>/` for every new
candidate or measurement implementation. Keep `campaign.json`, the bound
recipe, and `prepared-bindings.json` in that directory. The manifest binds
the committed tooling files, the recipes, actual builds, machine, corpus
and policy. [Fixed policy](policy.json)

Use the maintained `rebuild.py` to prepare the actors from the pinned
checkouts. The compiler scope uses ordinary fresh compiler processes with
reporting and census disabled. Use the explicitly selected encoder test
and census separately before measurement. Retain previous campaign
directories and any partial or unfavorable observations.

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

A memory-repair campaign ends with its compiler assessment. A final
qualification runs the same sequence again with `SCOPE=runtime` after its
compiler assessment passes verification. Runtime calibration uses fresh
worker-slot assignments in both legs. The verifier checks each mapping and
startup order, then forms crossed cycles with ratios oriented to the actual
compilers. Invalid runtime calibration stops before candidate timing.

Compiler sessions rotate their starting slot by session ordinal. The
rotation assigns each role to each absolute launch position across every
three sessions. Each individual session retains one warmup per role and
all six permutations. For campaigns already collected, use the tooling
and policy pinned in their manifests.

In Round 2, the integrated source passed M1 correctness and compiler
qualification. The same-build runtime calibration was unresolved, so that
campaign stopped before candidate timing.
[Round 2 assessment](3a66a014c853e082ad907ed4db1673c9dadf0c69/F-m1-20261126T181433Z/assessment.md)

## Direct M1 comparison

The integrated compiler recorded **81/81 fixture and 12/12 Silesia wins**
against the pinned libdeflate peers in all three sessions and both case
orders after combining the two slot mappings.
[Completed direct comparison](3a66a014c853e082ad907ed4db1673c9dadf0c69/F-m1-direct-20261127T162006Z/report.md)

The original tooling and checkout commits are available at their recorded
identities. The exact collector and summarizer are in the record's
[`commands` directory](3a66a014c853e082ad907ed4db1673c9dadf0c69/F-m1-direct-20261127T162006Z/commands).
[Tooling tag](https://github.com/mech-lang/benchmarks/tree/mech-native-route-direct-m1-tooling-20261127)
· [Checkout tag](https://github.com/mech-lang/benchmarks/tree/mech-native-route-direct-m1-checkout-20261127)

From the benchmark checkout root, use Python 3.11 or later on Linux or
macOS. Choose a new absolute scratch directory for the regenerated files.

```sh
RECORD="$(pwd)/experiments/mech/mechdeflate-cranelift-v1/stabilization/route-memory/3a66a014c853e082ad907ed4db1673c9dadf0c69/F-m1-direct-20261127T162006Z"
python3 -B experiments/mech/mechdeflate-cranelift-v1/verify_direct_runtime.py \
  --record "$RECORD" --output /tmp/mech-direct-m1-replay
```

The replay checks the retained artifact bytes and timing records offline.
It regenerates all 1,116 case rows and the three individual-leg exceptions.
[Replay result](3a66a014c853e082ad907ed4db1673c9dadf0c69/F-m1-direct-20261127T162006Z/replay-verification.json)

## Shared handoff

Use this evidence branch for each sealed checkpoint, including unresolved
measurements. The Round 2 handoff binds the integrated source, recipe and
benchmark tooling, and includes the Round 1 compiler records. [Integrated source](https://github.com/mech-lang/mech/commit/3a66a014c853e082ad907ed4db1673c9dadf0c69), [verified release assets](https://github.com/mech-lang/benchmarks/releases/tag/mech-native-route-m1-round-2-20261126)

The original M1 release supplies the pinned R and O control builds. Verify
downloaded archives against the checksum file in their respective release.
[Original control builds](https://github.com/mech-lang/benchmarks/releases/tag/mech-native-route-m1-evidence-20261126)
