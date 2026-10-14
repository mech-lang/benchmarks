# Elixir catalog and site publication source

This packet defines the publication transition after the full cohort has closed.
Source preparation and pure tests do not admit timings, create a real publication
candidate, change the dataset, export program bundles or build the site. The
frozen full-run controller, plan and historical evidence remain unchanged.

`tools/qualification/import_elixir.py` is an additive importer. The Pony importer
is specific to Pony's prerequisite schema and is retained unchanged. The Elixir
importer loads the frozen Elixir exporter by its recorded SHA-256, reproduces
the independently reconciled candidate, and requires exact JSON equality with
the explicitly pinned saved candidate before any admission decision.
The CLI also requires the independently reviewed importer SHA-256. It verifies
that source pin before entering the file phase, immediately before staging,
before each applied replacement, and before the receipt; the recorded tool pin
is the required input digest.

The exporter binds the corrected Elixir-specific durable validator, and the
importer binds that exporter by its updated source digest. This validator checks
the recorded controller's exact `-I -S -B` invocation without inserting `-u`.
The four argv/cwd records, observed command listings, PID/birth/parent identity
and terminal ownership checks remain mandatory; original receipts are preserved.

All three completed-job leases (durable job, Elixir cohort, original common
timing mutex inode 79859134) remain held through verification, private staging,
optional apply and receipt writing. All physical prerequisite/artifact pins are
rechecked before writing, the closed run's exact artifact inventory is checked
again, and named lease identities are checked before each publication file
replacement. A failed replacement restores the exact three original files.

## Admission and preservation

- All 20 independent source-form records enter `program_inventory`, including
  failed forms, prior successful partial samples, failed attempt evidence and
  skipped slots. Source aliases retain separate receipt keys and timings; no
  distinct optimization or reused timing is claimed.
- Only forms with three qualified subject samples **and** a complete qualified
  matched Mech control receive `eligible_for_chart=true` and chart coordinates.
  Failed forms retain null median/SD. A successful subject with a failed control
  retains its actual median/samples/SD but has null coordinates and matched
  ratio. Controls remain evidence and never become extra catalog programs or
  replace fixed chart baselines. If an eligible Elixir form improves an existing
  time, canonical LOC or formatted LOC minimum, the importer stops before
  staging/apply and requires a separate review of baseline updates; the current
  fixed-best labels therefore cannot silently become stale.
- Canonical and formatted endpoints are independently selected from eligible
  forms. Source coverage remains all ten workloads even where timing admission
  fails. Application, authored support, and launcher all remain in both source
  counts and exported bundles.
- Canonical aggregate coordinates use the admitted workload set and record its
  coverage. The full-suite `formatted_reference_summary` gains an Elixir entry
  only when all ten workloads have qualified formatted endpoints. Its independent
  fastest/fewest-lines aggregates use formatted LOC ratios and their own selected
  timings. Missing formatted coordinates or an excluded workload leave that
  full-suite aggregate absent. Existing entries and fixed baselines are preserved.
- Original candidate/report admission flags remain false and immutable. Each
  admitted row records the original false flags separately from the new
  reviewed admission, and references the candidate/reconciliation/release
  evidence. The dataset audit also binds the importer source.
- Public retained source, AST, report and review references are repository
  relative. Original external compiler/runtime/source identities remain
  explicit provenance; they are not guessed into archive links.
- Elixir is BEAM JIT, dynamically typed, functional, with tracing GC plus
  reference-counted large binaries. The retained runtime metadata scope remains
  separate qualification-process observations, not instrumentation of every
  timed process. Numeric GC defaults and Regex JIT remain unclaimed.

The separate `release-metadata-v1.json` binds the official May 25, 2012 v0.5.0
announcement and project history. Its definition is the public release of the
rewritten language. It explicitly acknowledges the creator's earlier v0.3.0
release around April 2011; it does not claim that development began in 2012.
Primary pages: [v0.5.0 announcement](https://elixir-lang.org/blog/2012/05/25/elixir-v0-5-0-released/)
and [development history](https://elixir-lang.org/development/).

## Generic integration changes

`tools/export_catalog.py` retains a new optional `publication_record` in each
portable `program.json`. It contains the finalized complete evidence record,
including failure/exclusion/alias information, three-role counts and sample
receipts. Its independently reviewed `timing_sd`, including null for incomplete
cohorts, supplies the portable summary. Existing programs without this field
retain the prior output schema and statistics. `tools/verify_repository.py`
checks the same additive contract.

The site uses an explicit `eligible_for_chart=false` gate for endpoints,
inventory comparisons, recorded samples, density and chart bounds. Excluded
forms remain available for source and observation inspection. The importer also
sets null coordinates for excluded forms. Existing rows without an eligibility
field preserve their prior admission behavior. Launcher roles are labeled, and
incomplete forms retain visible successful samples without a claimed median.

## Post-cohort command workflow

Do not run the importer or full file verification while a timing cohort owns
the lane. First run the already reviewed independent reconciliation and private
export commands in `result-review-source-v1.md`, retain their actual outputs,
and review their exact SHA-256 values. No currently running/partial report can
satisfy those commands.

From the repository root, use the pinned Python:

```sh
ELIXIR_PYTHON=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
```

Read the actual pins from the just-reviewed result files and current three
publication files into the following task-specific variables. These are exact
input pins, not bypass switches: `ELIXIR_RECONCILIATION_SHA`,
`ELIXIR_CANDIDATE_SHA`, `ELIXIR_BENCHMARKS_SHA`, `ELIXIR_LANGUAGES_SHA`, and
`ELIXIR_MODULE_SHA`. Set `ELIXIR_IMPORTER_SHA` to the reviewed source-packet pin.
The actual prepared plan SHA is fixed below.

```sh
"$ELIXIR_PYTHON" -I -S -B tools/qualification/import_elixir.py \
  --importer-sha256 "$ELIXIR_IMPORTER_SHA" \
  --plan /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/plan-v1.json \
  --plan-sha256 af436ecfba5c795646ca579db3d28af8c3588f1135d25a4a0736c2c3cf365055 \
  --durable-directory /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/owned-jobs/full90-v1 \
  --reconciliation /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/reconciliation-v1.json \
  --reconciliation-sha256 "$ELIXIR_RECONCILIATION_SHA" \
  --candidate /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/publication-candidate-v1.json \
  --candidate-sha256 "$ELIXIR_CANDIDATE_SHA" \
  --benchmarks-sha256 "$ELIXIR_BENCHMARKS_SHA" \
  --languages-sha256 "$ELIXIR_LANGUAGES_SHA" \
  --module-sha256 "$ELIXIR_MODULE_SHA" \
  --output /private/tmp/elixir-publication-preview-v1
```

This writes only a new private tree with the proposed three files, their exact
original backups, and `import-receipt.json`. Review the output and run the pure
site regressions after the native lane is idle:

```sh
"$ELIXIR_PYTHON" -I -S -B tools/qualification/test_import_elixir.py
"$ELIXIR_PYTHON" -I -S -B tools/qualification/test_catalog_publication.py
node site/tests/publication.mjs
node site/tests/layers.mjs
```

To apply the reviewed transition, repeat the same import command with a fresh
private output directory and
`--apply`; it re-verifies all evidence and current publication input pins. It
replaces only `data/benchmarks.json`, `data/languages.json`, and
`site/src/languages.mjs`. Then run the existing portable export and validation:

```sh
"$ELIXIR_PYTHON" -I -S -B tools/export_catalog.py
"$ELIXIR_PYTHON" -I -S -B tools/verify_repository.py
"$ELIXIR_PYTHON" -I -S -B tools/build_site.py
```

The export writes the 20 Elixir bundles under
`programs/elixir/<benchmark>/<elixir-form>/`, including `main.ex`, `support.ex`,
`runner.exs`, and `program.json`; current CSV/summary outputs go under
`results/current/`. The normal site build writes `site/public/`. Run the existing
broader site checks and review the newly built catalog/site before publication.
No such mutation or build has been run as
part of this source-preparation packet.

## Source validation

Seventeen pure importer tests pass, including actual saved source/count metadata
joined to explicitly synthetic timings, failed subject/failed control cases,
partial preservation, endpoint gates, three roles, aliases, portable refs,
original-row preservation, release pin, lock-path replacement and replacement
rollback and rejection of a newcomer improving any retained fixed baseline.
Canonical and formatted aggregate regressions cover all ten workloads, preserve
prior summary entries and reject an incomplete formatted aggregate when a
baseline or qualified matched control is unavailable.
Missing or wrong importer-source pins are rejected before the file phase or any
staged write.
Five pure portable-catalog tests pass. New Node eligibility and
renderer regressions are authored but intentionally deferred until the cohort
closes. A failed-control regression verifies that source coverage includes
workloads whose timing results are excluded from the chart.
