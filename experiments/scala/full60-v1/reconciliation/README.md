# Independent Scala full60 reconciliation

The [independent verifier](../../../../tools/qualification/scala_reconcile.py) checks a completed first full-size Scala cohort: one real retained Scala implementation and one matched Mech control for each of ten workloads, three fresh process samples per implementation. It does not import or execute the measurement producer, sampler, JVM, compiler or benchmark. No prepared full60 plan or completed timing cohort is supplied by this source packet.

The pure ledger stage independently reconstructs all 60 alternating slots and verifies the raw sampler, supervised sampler and outer ownership receipt for every actual attempt. It requires the exact durable `Python -I -S -B -u` command, controller birth and parent identity, serial native intervals, normal ownership cleanup, exact source/runtime fingerprints, full-output validation evidence, and the producer's independently validated receipt snapshots. An isolated workload failure preserves its original receipt and any earlier successful samples; the failed profile receives neither a median nor a ratio. A failed matched control also leaves its Scala ratio unset.

The file stage joins the timed source, generated classes, canonical count and runtime to the existing independent work and source-count decisions. It authenticates the original compiler, 149-case correctness, two execution-path captures, parser transports and canonical projections, including all inherited pins and five exact artifact inventories. Matched controls retain their original audited source, binary, command and input identities. Canonical counts are qualified; formatted counts remain unavailable.

Three existing leases remain held throughout verification and any consuming publication operation: the completed durable job's private lease, the Scala cohort lease, and the original common timing mutex. The durable job must have exactly its nine registered files. The completed run must contain exactly its report, terminal and three receipts per actual attempt. All verified bytes, qualification inventories, executable class inventories, output inventories and named lease identities are checked again before releasing the leases. A publication consumer can provide a final closure callback and guarded restoration callback; restoration runs before release if closure validation fails.

The result schema is `scala-independent-full60-reconciliation-v1`. Successful file review returns status `full60-reconciled-awaiting-runtime-and-publication-review`, `file_integrity_verified: true`, authenticated plan/report/terminal references, `verified_file_pins`, and a `profiles` map keyed by the original 20 profile identities. Each entry retains its samples, attempts, median and sample standard deviation, failed-attempt identity and matched-control ratio. `chart_admission`, `full_timings_qualified` and `runtime_publication_metadata_qualified` remain false. Runtime metadata, publication selection and catalog preservation require a separate consumer.

Successful full stdout is validated and discarded by the frozen sampler. The retained evidence is its complete byte count, digest and output-validation receipt. The verifier does not claim to replay stdout bytes that were not retained. Resource limits are checked against sampled process-group RSS, which is not a continuous maximum; any missing kernel identity observations remain explicit in the result.

## Invocation after the cohort closes

Use the actual independently reviewed plan digest and a fresh result path. Do not invoke the file stage during another timing cohort: it takes the common mutex nonblockingly and hashes the complete retained closure.

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/scala_reconcile.py \
  --plan experiments/scala/full60-v1/plan-v1.json \
  --plan-sha256 "$SCALA_FULL60_PLAN_SHA256" \
  --durable-directory experiments/shared/owned-jobs-v1/owned-jobs/scala-full60-v1 \
  --output experiments/scala/full60-v1/reconciliation/result-v1.json
```

The result is written exclusively and retained only after the surrounding closure check succeeds. A late check failure removes only the new file still owned by this invocation; independently replaced or altered files are preserved and reported as restoration failures. The result’s original creation inode and exact bytes are checked after the final input recheck. Success is printed after all final checks complete.

The [pure tests](../../../../tools/qualification/test_scala_reconcile.py) construct synthetic future ledgers in memory and join small saved qualification metadata. They create no executable plan, measurement output or qualification receipt. Their invented times and PIDs are test inputs only.
