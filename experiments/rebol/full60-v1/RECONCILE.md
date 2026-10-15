# Independent full60 reconciliation

[`rebol_reconcile60.py`](../../../tools/qualification/rebol_reconcile60.py) independently reconstructs the sixty-slot cohort in [POLICY.md](POLICY.md): one canonical compact Rebol subject and one matched Mech control per workload, with three fresh samples each. The order is subject/control, control/subject, subject/control. There are twenty profile rows, thirty subject slots and thirty control slots. No optimized row or copied timing is created.

The reader validates raw sampler, supervisor and outer ownership receipts, exact output references, serial timing intervals, durable worker/controller identities, the registration ledger and complete artifact membership. It computes medians and sample standard deviations independently. A failed profile retains earlier observations without a median and skips only its remaining slots. A failed matched control excludes the subject endpoint while preserving its descriptive samples. An incomplete or integrity-failed terminal is rejected.

`review_context(plan_path, expected_sha, durable_directory, consumer_sha, *, on_exit_failure=None, final_consumer_check=None)` loads the exact pinned final qualification entry through `load_controller(expected_sha)`, replays its prerequisite context, and holds the original prerequisite leases together with the full60 suite and durable-job leases. The durable directory must be `experiments/shared/owned-jobs-v1/owned-jobs/rebol-full60-v1`. The consumer snapshots its own evidence pins and yielded result, then rechecks artifacts, pins and named lease identities before exit. Consumer cleanup also runs for late inherited-context failures.

The result schema is `rebol-independent-full60-reconciliation-v1`. The pure ledger status is `ledger-reconciled-awaiting-file-runtime-and-publication-review`; the held file review yields `full60-reconciled-awaiting-runtime-and-publication-review`. Profiles retain exact sample provenance and control eligibility. Top-level references identify the plan, report, terminal and durable terminal; source and runtime evidence come from the independently reproduced qualification. Runtime publication metadata, source/runtime equivalence, full-timing admission and chart admission remain false. Publication requires its separate reviewed consumer.

The original full90 producer and independent reader remain unchanged. The new reader does not import the full60 producer. Focused synthetic tests exercise schedule parity, source/policy/qualifier binding, failures in each round, failed-control exclusion, independent receipt checks, statistics and ownership closure. All fixture identities and observations are invented test inputs. No actual full60 plan or reconciliation is included in this source packet.

Run the focused tests with the retained Python interpreter:

```sh
python3.12 -I -S -B tools/qualification/test_rebol_reconcile60.py
```
