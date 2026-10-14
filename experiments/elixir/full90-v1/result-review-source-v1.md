# Independent Elixir result and export preparation

This packet defines independent result reconciliation and a private publication
candidate. Pure tests use synthetic full ledgers plus the five retained durable
launch receipts. Synthetic timings, PIDs, completed statuses and file-verification
attestations are confined to in-memory fixtures and are never written as measured
evidence. These tests perform no file-phase closure verification or publication.

`tools/qualification/elixir_reconcile.py` reads the closed measurement ledger
independently of the producer. It imports only pinned, existing independent
Prolog/Pony reconciliation primitives. It never imports or executes the sampler,
measurement controller, compiler or language runtime. It binds the actual
prepared Elixir plan SHA
`af436ecfba5c795646ca579db3d28af8c3588f1135d25a4a0736c2c3cf365055`.

Durable validation uses the exact retained Elixir controller invocation:
Python `-I -S -B`, without `-u`, followed by the pinned controller, `run`, plan
path and plan SHA. The Pony continuation helper expects an additional `-u`, so
its command-shape validator is not used for Elixir. The local validator requires
exact agreement across all four argv/cwd records and both observed controller
command listings, with matching controller/worker identities, birth records,
parent PID, terminal status and ownership policy. It never normalizes arguments.
The frozen measurement plan, producer and original durable receipts are unchanged.

The pure ledger checks all 90 planned slots, exact rotations, source/runtime
identity, raw/supervised/outer receipt joins, complete-output references,
nbody energies, timing intervals, environment/resource/cleanup gates,
authoritative process groups, durable command ownership and terminal accounting.
It independently recomputes medians, sample standard deviations and matched
Mech ratios. A failed form retains earlier valid samples but has no median,
standard deviation or ratio. Its remaining slots can only be skipped after its
first verified isolated workload failure. A failed Mech control removes ratios
without discarding independently valid subject samples.

The frozen execution fingerprint contains historical compiler-owner names as
well as current archived owner records. The reconciler admits only the two
explicit same-hash, same-filename original-to-retained owner mappings recorded
in each qualified form. These are descriptive evidence names; physical file
verification reads only the already-pinned retained files. No runtime or source
execution path is substituted.

The file phase requires the completed durable owner lease, the Elixir cohort
lease and the original common timing mutex inode 79859134. All three descriptors
remain held through full physical pin verification, exact artifact inventory,
the exclusive reconciliation output write and result hash. It refuses a live,
stopped, incomplete, integrity-failed or unexplained cohort. Reconciliation does
not grant chart admission or runtime publication approval.

`tools/qualification/elixir_export.py` has no apply or publish mode. It first
reproduces the entire independent reconciliation under those same leases and
requires exact equality with an explicitly pinned saved reconciliation. It
then writes one new private JSON candidate outside the original run, `data/`
and `site/` paths. Original reports and admission flags remain unchanged.

The candidate retains all 20 forms and ten matched controls. Its publication
keys explicitly map `<benchmark>:<id>` to the original bare Elixir receipt key.
It includes the main, authored helper and launcher; original physical LOC,
qualified canonical LOC, qualified formatted LOC; original/formatted AST
bindings; complete sample evidence; failures; skipped slots; and source aliases.
Identical compact/optimized sources retain distinct measured samples and carry
no distinct optimization claim. Endpoint proposals include only forms whose
own three samples and matched control both qualify. They remain proposals with
chart admission false.

Runtime metadata uses only evidence already bound by the full plan: the closed
20-form compiled probe assertions, source-reader runtime banner, exact retained
Elixir/BEAM/launcher/library pins, recorded flags and complete authored source
scan. It reports Elixir 1.20.4, OTP 29/ERTS 17.1, aarch64 BEAM JIT and the retained
scheduler configuration. Those observations belong to separate qualification
processes, not an instrumented runtime probe in every timed process. Numeric GC
defaults, maximum total VM thread count, regex JIT and exact regex engine version
are not claimed. The memory taxonomy follows the existing reviewed BEAM entry;
literal source scanning is explicitly limited and does not claim a numeric
collector configuration.

Tests and independent review:

- `test_elixir_reconcile.py`: 17 pure tests passed. Cases include
  complete90, each failure round, failed controls, partial-median rejection,
  command/runtime/source/owner mutations, missing or repeated attempts, orphan
  artifacts, changed output, overlap, stderr, process ownership, cleanup,
  invalid statistics, boolean counts, live jobs and nbody tolerance. The retained
  no-`-u` launch passes; added/removed/reordered options, argv/cwd disagreement,
  controller/worker PID or birth changes, observed command changes, wrong parent,
  failed ownership policy and a missing interpreter pin are rejected.
- `test_elixir_export.py`: 15 pure tests passed. Cases include
  exact work/count/runtime/source/BEAM joins, three source roles, formatted LOC,
  distinct aliases, all failure rounds, failed-control exclusion, observation
  limits and immutable raw/supervisor receipt ownership.
- Independent source review found no concrete blocker in the durable correction.
  Tests read saved source/plan metadata and the five small launch receipts;
  no measured sample report, runtime image or prerequisite closure is read or
  hashed by the fixtures.

After the actual cohort and durable owner have closed, run:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/elixir_reconcile.py --plan /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/plan-v1.json --plan-sha256 af436ecfba5c795646ca579db3d28af8c3588f1135d25a4a0736c2c3cf365055 --durable-directory /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/owned-jobs/full90-v1 --output /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/reconciliation-v1.json
```

After reviewing that result, use its exact returned digest:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/elixir_export.py --plan /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/plan-v1.json --plan-sha256 af436ecfba5c795646ca579db3d28af8c3588f1135d25a4a0736c2c3cf365055 --durable-directory /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/owned-jobs/full90-v1 --reconciliation /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/reconciliation-v1.json --reconciliation-sha256 REVIEWED_RECONCILIATION_SHA256 --output /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/publication-candidate-v1.json
```

Candidate review and catalog/site validation remain necessary before
publication changes the dataset or website.
