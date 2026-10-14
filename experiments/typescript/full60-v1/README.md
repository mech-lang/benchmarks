# First full TypeScript timing cohort

This packet defines sixty serial fresh-process samples: one retained TypeScript
implementation and one matched Mech AOT control for each of ten workloads,
with three observations per profile. It adds no source aliases or optimization
variants. This source packet has not prepared an executable plan or run timings.

The controller binds the actual strict compilation and native AST captures,
149 bounded correctness cases, ten canonical source-count admissions, and the
27 required-work contracts. The work admission includes the saved full-input
tree and pi diagnostic captures. The first capture producer remains failed on
its original output-parser assumption; additive lossless output and native-work
reviews reuse its complete tree output, and the missing pi was captured once.
No correctness, parser, compiler or diagnostic process is repeated here.

Each command is the retained Node executable followed by the exact emitted
CommonJS main and its prescribed argument, where applicable. The authored
TypeScript, unchanged compiler input, JavaScript and source map remain pinned.
There is no compiler, launcher script, warmup, forced optimization, diagnostic
flag or custom heap/collector setting in the timed command. The environment
retains `UV_THREADPOOL_SIZE=8`; this is not a claim that every program uses eight
workers. Ambient `NODE_*` settings and native injection variables are rejected,
including compile-cache and preload settings.

The runtime admission identifies the exact Node 24.19.0 binary, actual recorded
`process.versions`, application imports, embedded dependencies, Mach-O declared
system libraries and retained OS build. Its scope is static declared dependency
closure, not an observed loaded-image inventory for every timed process. This
controller preserves that scope and introduces no new runtime probe.

The shared sampler measures fresh process launch through exit: Node startup,
script loading, tiered JIT, input, full work, complete output and shutdown.
Offline TypeScript compilation, harness file setup, source/runtime pin checks,
environment waits and post-run output validation are outside elapsed time.
The sampler and process supervisor are unchanged. The controller's timing,
masked receipt transfer and terminal lifecycle functions match the reviewed
Scala full60 controller, apart from family names. All ten authored source counts
are canonical-only; formatted counts remain null and unqualified.

The round order alternates subject and control, with five workloads starting
with each language. Full inputs are regex 5,000,000; reverse complement, FASTA
and k-nucleotide 25,000,000; pi 10,000; spectral norm 5,500; Mandelbrot 16,000;
trees 21; n-body 50,000,000; fannkuch 12. Each attempt uses the established
six-hour native deadline, separate supervision/cleanup bound and 10 GiB sampled
group-RSS limit. Bounded correctness does not guarantee these resource limits
will suffice. An isolated workload failure retains the receipt and skips only
that profile's remaining slots. Integrity, environment or ownership failures
stop the cohort without retry.

The existing common mutex, inode `79859134`, remains held throughout the entire
cohort, environment waits, cleanup and final evidence writes. A separate
TypeScript suite lease prevents another cohort. Preparation and execution verify
all flat source/runtime pins under the mutex. Five prerequisite artifact
inventories are exact: compile/AST, bounded correctness, original tree/capability
capture, missing-pi capture, and canonical projections. Every returned attempt
is persisted under an interrupt mask before validation; its raw, native sampler
and outer-supervisor bytes are independently checked and snapshotted. Finalization
replays the ledger, serial clocks, exact artifact membership and receipt digests,
then rechecks the prerequisites and snapshots after inventory collection.
Successful producer completion does not itself admit timings to the chart.

## Preparation and execution

Use fresh paths on the retained host and independently review the prepared plan
before launch. Preparation hashes the full closure and belongs in the serial
lane. These are command templates, not evidence of execution.

```sh
TYPESCRIPT_FULL_PYTHON=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
"$TYPESCRIPT_FULL_PYTHON" -I -S -B tools/qualification/typescript_full.py draft \
  --plan experiments/typescript/full60-v1/draft-v1.json \
  --output experiments/typescript/full60-v1/run-v1
"$TYPESCRIPT_FULL_PYTHON" -I -S -B tools/qualification/typescript_full.py prepare \
  --draft experiments/typescript/full60-v1/draft-v1.json \
  --draft-sha256 "$TYPESCRIPT_DRAFT_SHA" \
  --plan experiments/typescript/full60-v1/plan-v1.json
```

Set `TYPESCRIPT_DRAFT_SHA` from the draft output. The reusable durable launcher
is `experiments/shared/owned-jobs-v1/launch_durable.py`, with a fresh job name such
as `typescript-full60-v1`. Its command contains absolute physical paths:

```text
["<retained-python>", "-I", "-S", "-B", "-u",
 "/private/tmp/mech-benchmark-completion/tools/qualification/typescript_full.py", "run",
 "--plan", "/private/tmp/mech-benchmark-completion/experiments/typescript/full60-v1/plan-v1.json",
 "--plan-sha256", "<independently-reviewed-prepared-plan-sha256>"]
```

Matched Mech observations remain separate from published Mech samples and chart
baselines. No prior diagnostic observation is relabeled as a timing sample.

## Pure checks

```sh
"$TYPESCRIPT_FULL_PYTHON" -I -S -B tools/qualification/test_typescript_full.py
```

The tests read saved small metadata and use synthetic receipts and policy faults.
They do not prepare a real plan, launch a native subject, hash runtime binaries
or repeat any qualification stage.
