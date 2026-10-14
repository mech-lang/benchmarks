# Independent four-cohort reconciliation

`tools/qualification/prolog_knucleotide_reconcile.py` validates the prepared
36-slot continuation against 54 preserved observations. It does not import a
measurement controller, sampler, native runtime or compiler. Its only imported
validators are the frozen independent Prolog and Pony receipt consumers.

The combined sample ledger retains four distinct origins:

| Cohort | Reused observations | Excluded or new work |
| --- | ---: | --- |
| Original full90 | 9 regex observations | Original interrupted reverse-complement attempt 10 remains excluded |
| Linear full81 | 31 observations | Original stopped producer remains stopped |
| Linear remaining50 | 14 observations | Deliberately interrupted k-nucleotide attempt 15 remains unqualified, without a timeout claim |
| K-nucleotide remaining36 | None | Only the 36 prepared unfinished slots may execute |

The complete schedule has 90 slots. Successful new observations may complete
the 30 three-sample profiles; isolated failures retain their actual attempts,
exclude partial medians and skip only that profile's later slots. Matched-control
failure excludes the corresponding chart ratio without discarding valid subject
observations. No completed observation is repeated or assigned to another source.

The exact prepared plan is
`../plan-v1.json`, SHA-256
`f9953cbdc051cf2d536fab8b5e74f342e6d1a4ebd41783d7ad8e8e27f2d3f75c`.
Only the two qualified k-nucleotide profile rows may differ from the earlier
plan. Their independently reviewed three-file source bundles, compiler input,
main/helper QLF, canonical projections and required work are bound by
`../../knucleotide-linear-v1/qualification/qualified-source-work-counts-v2.json`,
SHA-256 `4fe44e66ff923d914c1f7c6a368457ab014ded14df9153c61216713eaa5eef68`.
The matched control and other 18 Prolog profiles retain their original identities
and runtime policies. Equivalent-source labels remain explicit aliases.

The pure ledger phase checks exact raw/supervisor/outer receipt membership,
source and runtime fingerprints, full-output validation, native ownership,
cleanup, serial intervals, sample membership, statistics and failure handling.
The completed 14 receipt trios are checked against the pre-stop checkpoint;
the interrupted raw/wrapper/outer trio remains separately bound. Prior failed
producer statuses and all original receipts are preserved.

The file phase holds six existing leases: four durable owners, the original
suite lease and the common timing mutex. It replays original physical pins,
all four closed output inventories and the corrected source qualification
inventory. Immutable pin and inventory snapshots are checked again before the
final consumer callback and lease release. A newly written reconciliation is
bound by its creation inode and exact bytes; a late failure removes only an
unchanged owned output and preserves external edits.

After the actual continuation closes and the serial timing lane is free:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/prolog_knucleotide_reconcile.py --output /private/tmp/mech-benchmark-completion/experiments/prolog/full36-knucleotide-v1/reconciliation/actual-v1.json
```

The output must be fresh. Source preparation and pure tests do not constitute
an actual reconciliation. The consumer retains `chart_admission=false` and
`runtime_publication_metadata_qualified=false`; downstream runtime review,
publication and repository validation remain separate gates. Complete stdout
was validated by the sampler but not retained; saved evidence contains output
byte counts, digests and validation receipts. Sampled RSS does not establish an
unobserved peak bound.

The focused pure suite replays the small saved stopped-prefix receipts and uses
synthetic future observations only in memory:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/test_prolog_knucleotide_reconcile.py
```

It covers cancellation preservation, changed source/ownership evidence,
replacement bundle and plan boundaries, exact four-cohort attribution,
subject/control failures, schedule changes and guarded output restoration.
It does not read full historical plans, hash runtime closures or execute native
subjects. Sixteen cases pass; independent source review remains pending.
