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
