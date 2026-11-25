# Native compiler stabilization handoff

The Apple M1 qualification retained 81/81 fixture and 12/12 Silesia wins
against both pinned references in both timing orders. The completed M1 run
and the open M3 qualification are documented in the [qualification record](qualification.md).

| Snapshot | Source revision | Recipe |
| --- | --- | --- |
| Frozen | `35784003b9149fe8059fa83dd5d0aff10dbcd631` | [Frozen recipe](evidence/frozen/recipe.json) |
| Reconciled | `5b9f252fc7e775bf8e4d850ca368da581e9f5386` | [Reconciled recipe](evidence/reconciled/recipe.json) |
| Configured | `8ce620d1b165b868210378ef260945ee3c398d05` | [Configured recipe](evidence/configured/recipe.json) |

All three recipes pin the same native object, canonical bytecode, descriptor
and [profile inputs](../word-mismatch-order/profiles). Reconciled integrates
the parent stack and preserves set semantics. Configured captures native
compiler inputs and selected profile contents and adds optional host reporting.
The [merge map](stack.tsv) records the parent pins used for the reconciliation.

## Rebuild on Apple M3

Historical checkout pin correction: use benchmark revision
`f9eb6c48905ff02e2a5771d1812f6bb42598a57f` for the replay commands below.

Use Apple Silicon macOS with Apple Command Line Tools, Python 3.12 or later,
and Rustup. Run these commands in a folder where you can create two checkouts.

```sh
git clone --filter=blob:none --single-branch --branch codex/m3-deflate-81 \
  https://github.com/mech-lang/mech.git mech-stabilization
git clone --filter=blob:none --sparse --single-branch --branch codex/m3-deflate-81 \
  https://github.com/mech-lang/benchmarks.git benchmarks-stabilization
git -C benchmarks-stabilization checkout --detach f9eb6c48905ff02e2a5771d1812f6bb42598a57f
git -C benchmarks-stabilization sparse-checkout set \
  experiments/mech/mechdeflate-cranelift-v1 \
  experiments/mech/mechdeflate-81-v1 \
  experiments/mech/mechdeflate-phase-routes-v1 \
  experiments/mech/mechdeflate-masked-fields-v1 \
  experiments/mech/mechdeflate-silesia-v1

mech="$PWD/mech-stabilization"
bench="$PWD/benchmarks-stabilization"
packet="$bench/experiments/mech/mechdeflate-cranelift-v1"
evidence="$packet/native-first-batch/evidence"
silesia_packet="$bench/experiments/mech/mechdeflate-silesia-v1"
run=$(mktemp -d /tmp/mech-native-stabilization.XXXXXX)
silesia="$run/silesia-inputs"

rustup toolchain install nightly-2026-03-03 --profile minimal
git -C "$mech" worktree add --detach "$run/frozen" 35784003b9149fe8059fa83dd5d0aff10dbcd631
git -C "$mech" worktree add --detach "$run/reconciled" 5b9f252fc7e775bf8e4d850ca368da581e9f5386
git -C "$mech" worktree add --detach "$run/configured" 8ce620d1b165b868210378ef260945ee3c398d05
python3 -B "$silesia_packet/fetch_silesia.py" \
  --manifest "$silesia_packet/corpus.json" "$silesia"

rebuild() {
  snapshot=$1
  shift
  python3 -B "$packet/rebuild.py" --mech-root "$run/$snapshot" \
    --recipe "$evidence/$snapshot/recipe.json" --build-repeats 3 \
    --output "$run/builds/$snapshot" "$@"
}
rebuild frozen
rebuild reconciled
rebuild configured --with-host-report
```

## Run both timing suites

Run the commands serially on the M3. Each pair measures all 81 fixtures and
all 12 full Silesia inputs in both orders. The final replay measures the
Configured Silesia encoder against both pinned references. Keep each
`binding.json`, `comparison.json`, and the raw timing directories.

```sh
compare() {
  control=$1
  candidate=$2
  python3 -B "$packet/compare_rebuilt.py" \
    --control "$control" --control-build "$run/builds/$control" \
    --control-recipe "$evidence/$control/recipe.json" \
    --candidate "$candidate" --candidate-build "$run/builds/$candidate" \
    --candidate-recipe "$evidence/$candidate/recipe.json" \
    --corpus "$silesia" --output "$run/results/$candidate-vs-$control"
}
compare frozen reconciled
compare reconciled configured
compare frozen configured
python3 -B "$packet/replay.py" --suite silesia --corpus "$silesia" \
  --build "$run/builds/configured" --recipe "$evidence/configured/recipe.json" \
  --output "$run/results/configured-silesia-references"
```

The [portable handoff archive](native-first-batch-handoff.tar.gz) includes the
resource probes, worker and profile checks, and supplemental measurement
scripts. The [M1 observations archive](native-first-batch-m1-observations.tar.gz)
contains the raw timing blocks, compiler samples and rebuilt actors.
Verify both downloads with the [SHA-256 manifest](native-first-batch-archives.sha256).
