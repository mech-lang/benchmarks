# Kotlin JVM measurement and publication

The [completed cohort](../run-v1/report.json) contains 90 qualified full-process
samples: three for each of twenty Kotlin source-form records and three matched
Mech AOT controls per workload. The [independent reconciliation](../reconciliation-v1.json)
verifies every scheduled sample, complete-output validation, process closure,
and 9,528 pinned files. There are no failed forms or skipped slots.

Each sample starts a fresh JVM and invokes the retained application main once.
JVM startup, class loading, HotSpot compilation, input, work, output, and shutdown
are timed. Kotlin compilation to class files occurs before measurement. The
retained runtime is Kotlin 2.4.21 on Eclipse Temurin HotSpot 25.0.4.1+1 with
`-XX:ActiveProcessorCount=8 -Xms64m -Xmx8g -XX:+UseG1GC`. An individual method
may remain interpreted during its invocation. The [runtime evidence](../runtime-metadata-v1.json)
binds compiler-version output, the original and retained JDK release files,
and the exact measured launch flags.

The compact and optimized labels identify retained source aliases. Their
samples remain independent; these records do not claim a compiler optimization
or reuse one form's timing for the other. Both the application and authored
support file count toward canonical LOC. Formatted LOC is unavailable, so the
publication transformer creates no formatted coordinates, endpoints, or
aggregate for Kotlin.

## Closed-evidence reproduction

The following tools read the completed evidence. They do not invoke Kotlin,
Java, a compiler, or a benchmark. Each requires the retained Python with
`-I -S -B`; paths must be absolute physical paths. The original plan binds its
installation and source paths, so a new machine needs a separately prepared
plan to execute a new cohort. Reproducing this completed cohort's publication
also requires the pinned installation and archived files to remain available.

Use these retained inputs:

| Input | SHA-256 |
| --- | --- |
| [Plan](../plan-v1.json) | `fa50e8f327ac960623be79f99730aa94ba1c8588c9008854830a3b74495550f5` |
| [Reconciliation](../reconciliation-v1.json) | `e4c802a61b3836d38d1bcfa654a2fac99e5dc9321f81f4eb610f09490fc9444a` |
| [Reconciler](../../../../tools/qualification/kotlin_reconcile.py) | `568de52b6c0ea434e2aedfe61d50908ce39edb0ab9df4d21c3c362a244b3a0c0` |
| [Exporter](../../../../tools/qualification/kotlin_export.py) | `f6b37dbd313614341ebd4c62641f78ee410ad9d763160e5367c3d4fba8624382` |
| [Importer](../../../../tools/qualification/import_kotlin.py) | `fb512101e2f2b118904241469de2d9cceed39b820aaa415828cd2072fcb4ae9d` |

The durable job directory is
`experiments/shared/owned-jobs-v1/owned-jobs/kotlin-full90-v2`.
The independent file phase holds that completed job's lease, the Kotlin suite
lease, and the original common timing mutex until its final integrity checks
complete. Every output path below must be new.

```text
<retained-python> -I -S -B tools/qualification/kotlin_reconcile.py \
  --plan <repo>/experiments/kotlin/full90-v2/plan-v1.json \
  --plan-sha256 fa50e8f327ac960623be79f99730aa94ba1c8588c9008854830a3b74495550f5 \
  --durable-directory <repo>/experiments/shared/owned-jobs-v1/owned-jobs/kotlin-full90-v2 \
  --output <fresh-reconciliation.json>

<retained-python> -I -S -B tools/qualification/kotlin_export.py \
  --plan <repo>/experiments/kotlin/full90-v2/plan-v1.json \
  --plan-sha256 fa50e8f327ac960623be79f99730aa94ba1c8588c9008854830a3b74495550f5 \
  --durable-directory <repo>/experiments/shared/owned-jobs-v1/owned-jobs/kotlin-full90-v2 \
  --reconciliation <repo>/experiments/kotlin/full90-v2/reconciliation-v1.json \
  --reconciliation-sha256 e4c802a61b3836d38d1bcfa654a2fac99e5dc9321f81f4eb610f09490fc9444a \
  --output <fresh-candidate.json>
```

The candidate retains all twenty source-form records, their individual samples,
raw and supervisor receipt references, ten matched controls, and proposed
canonical endpoints. Its chart-admission flags remain false. A subject failure
would retain its partial samples without a median; a failed matched control
would retain subject measurements but exclude that workload from admission.

## Publication preview and application

The importer independently reproduces the candidate before transforming the
catalog. It preserves every existing program, source file, historical report,
and fixed benchmark baseline. A new minimum requires a separate baseline
review. Matched Mech controls remain comparison evidence rather than replacing
existing Mech measurements.

Pin the exact candidate and current catalog files before preparing a preview:

```text
<retained-python> -I -S -B tools/qualification/import_kotlin.py \
  --candidate <repo>/<candidate.json> --candidate-sha256 <candidate-sha256> \
  --reconciliation <repo>/experiments/kotlin/full90-v2/reconciliation-v1.json \
  --reconciliation-sha256 e4c802a61b3836d38d1bcfa654a2fac99e5dc9321f81f4eb610f09490fc9444a \
  --plan <repo>/experiments/kotlin/full90-v2/plan-v1.json \
  --plan-sha256 fa50e8f327ac960623be79f99730aa94ba1c8588c9008854830a3b74495550f5 \
  --durable-directory <repo>/experiments/shared/owned-jobs-v1/owned-jobs/kotlin-full90-v2 \
  --importer-sha256 fb512101e2f2b118904241469de2d9cceed39b820aaa415828cd2072fcb4ae9d \
  --benchmarks-sha256 <data/benchmarks.json-sha256> \
  --languages-sha256 <data/languages.json-sha256> \
  --module-sha256 <site/src/languages.mjs-sha256> \
  --output <fresh-directory-outside-repository>
```

Without `--apply`, the importer writes the three proposed catalog files, exact
original backups, and an import receipt to the private output directory. Adding
`--apply` performs the checked replacements. A write, lease, or final integrity
failure restores still-owned catalog bytes and removes an owned success
receipt. Externally altered bytes are preserved and reported as an error.
Success is reported only after the independent context's final checks pass.

The [source peer review](../../full90-reconciliation-v1/publication-source-peer-review-v1.json)
records the frozen implementation review. Nine exporter tests and fifteen
importer tests cover independent alias samples, canonical-only counts, source
bundles, failed subjects and controls, fixed baselines, receipt ownership, and
rollback. Their timing fixtures are synthetic; they do not stand in for the
actual completed-run reconciliation.

```text
<retained-python> -I -S -B tools/qualification/test_kotlin_export.py
<retained-python> -I -S -B tools/qualification/test_import_kotlin.py
```

The original packet README and measurement artifacts remain unchanged because
they are pinned inputs to the completed cohort.
