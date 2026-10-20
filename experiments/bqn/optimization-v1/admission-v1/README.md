# BQN frame-candidate admission

`tools/qualification/import_bqn_knucleotide.py` prepares one additive candidate,
`knucleotide:array-bqn-occurrence-frame`. It does not run BQN, compile a runtime,
or collect timings. `--prepare` writes the pinned plan, reconciled results and
reviewable catalog preview. Canonical data changes only with `--apply` and the
exact reviewed before/preview hashes printed by preparation.

The selected source is the lowest median among the five sources measured in
three matched rounds. Only the frame candidate is admitted here. Its full output,
all fourteen retained edge cases, and untimed scoped hash-work trace are checked
independently. The trace replays 874,999,961 occurrence updates and default hash
growth from 64 slots. Diagnostic processes never supply chart samples. This is a
best-retained-measured-candidate claim, with no global optimality claim.

The new application has 43 significant physical lines and 48 independently
reviewed units under the retained BQN manual rule. The exact line/owner ledger
is pinned. The separate logical policy v2 proposal remains unqualified. Every
prior profile, source, sample and normalization baseline remains exact; the old
BQN k-nucleotide source still has 39 retained units and its historical timings.

Local preparation additionally checks the current runtime, dependencies and full
input bytes. Archived replay relies on their exact bound build/input receipts,
retained raw output/process records, source snapshots and trace validation; it
does not require host-specific binaries or the large input in a new checkout.
The original recorded repository prefix is derived from the exact runtime
suffix, checked consistently across commands, and mapped only for evidence
lookup. Recorded commands and working directory remain historical facts.

The runtime build receipt records the source commit, submodules, compiler, SDK,
flags and dependency digests. The native make command runs in
`experiments/bqn/optimization-v1/.build/CBQN`; `runtime_restoration` records the
repository-root reconstruction recipe separately. The earlier runtime binary
was unavailable, so the speedup uses the fresh matched control on the restored
runtime, without claiming byte identity with historical execution.

Current local changes are attributed to OpenAI Codex, GPT-6 family, with the
exact model version unknown. The retained predecessor's original authorship and
inherited license gaps remain unresolved. Its missing citation is not evidence
that an AI originated it. New source links use the immutable checkpoint that
contains the exact selected source.

Offline checks:

```sh
python3 -m unittest discover -s tools -p test_bqn_knucleotide_publication.py
python3 tools/qualification/import_bqn_knucleotide.py --prepare
```

After reviewing `prepared.json`, apply only that exact preview:

```sh
python3 tools/qualification/import_bqn_knucleotide.py --apply \
  --expected-before-sha256 REVIEWED_BEFORE_HASH \
  --expected-prepared-sha256 REVIEWED_PREVIEW_HASH
```

Historical source-accounting replay applies this extension after the earlier
Ruby runtime extension, then compares the entire catalog for exact equality.
