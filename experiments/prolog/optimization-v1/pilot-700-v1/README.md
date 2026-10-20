# Spectral-norm N700 pilot preparation

This sealed plan contains **no pilot observations**. It prepares one complete fresh SWI process for each exact source: parent, eight-block candidate, serial candidate, in that predeclared order. Its [plan](plan.json) is SHA `c9d368e2a1db0aecd190fd238cf17d101b044eae485872756a676a5ee89c7bc4`; the source revision is `612fb31e030be207779c03cddb00a16af56f0173`. All3232 input/artifact/runtime pins and the completed [native qualification](../qualification-v1/README.md) are bound before execution.

The [runner](run_pilot.py) has no full-size mode. At N=700, each unchanged main still performs ten power iterations, twenty AtA applications, forty products and19,600,000 coefficient evaluations. The timing boundary includes fresh SWI launch, runtime and QLF loads, worker creation/copies/results, all matrix work, dots, complete output/flush and process exit. It excludes pin checks, independent reference generation and power/competition checks. The [observer](process.py) derives from the frozen untimed qualification observer with only its description and quantitative metadata changed.

Before the first measured process, the locked controller generates the independent12byte reference through the pinned archived Python `spectralnorm(700)` function and retains its complete output/source/hash. Every native output must exactly match that reference, and all three complete outputs must also match the parent. No numerical tolerance is used. The control checks require AC power, low-power mode disabled, no competing subject/compiler processes, no timeout/process-group survivor, empty stderr and bounded RSS. Every attempted process and stream remains available, including failures; there is no automatic retry.

This is a diagnostic screen with one observation per source, not a full-size speed comparison or precision estimate. The parallel retained normalized count remains unavailable under unchanged V5; the serial114/78 reproduction also awaits independent count admission. Timing this experiment does not admit either source or count to a chart.

Use the pinned bundled Python3.12. Metadata-only verification takes the common mutex and launches no SWI, oracle, compiler or benchmark process:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -B experiments/prolog/optimization-v1/pilot-700-v1/run_pilot.py --check-only
```

In a separately coordinated quiet timing window, with the common mutex available:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -B experiments/prolog/optimization-v1/pilot-700-v1/run_pilot.py --output experiments/prolog/optimization-v1/pilot-700-v1/pilot-v1
```

The source-only preparation did not run either command. Runtime binaries and generated QLFs are local dependencies checked by the runner; durable native receipts/streams and the restoration recipe remain separate from any claim of archived binary availability. Further candidate selection and full-size rounds require their own declared plan and preserved evidence.
