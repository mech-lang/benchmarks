# Corrected k-nucleotide qualification

The controller prepares a new, serial native qualification cohort. No plan,
native record, compiled artifact, source count or successful qualification has
been created by this source packet.

It reuses the frozen `prepare_qlf.pl`, common-mutex observer, process-receipt
validator, and original Prolog source-owner counter. It preserves the complete
physical prerequisite closure from the original study. The immutable observer
validator retains its historical `prolog-revcomp-bounded` record tag; the new
plan, report, paths and commands identify this k-nucleotide cohort explicitly.

The planned 88 processes run one at a time:

| Evidence | Processes |
| --- | ---: |
| Compile two unchanged helpers and both corrected main aliases | 4 |
| Load each main QLF with the two helper QLFs; record runtime, loaded inputs and WAM | 2 |
| Check 31 complete-output/error fixtures per alias | 62 |
| Inspect all seven complete maps on four fixtures per alias | 8 |
| Inspect the retained runtime's ordinary `system:atom_string/2` binding | 1 |
| Exercise seven focused source-owner binding fixtures | 7 |
| Read both original mains and both helpers without loading them | 4 |

The correctness oracle counts byte-string slices with independent Python
counters. During preparation it must reproduce all twelve retained expected
outputs exactly, then adds nineteen deterministic boundary, overlap, lowercase,
long-line and invalid-base cases. Five rejection cases require the precise
invalid byte diagnostic and empty stdout. The map inspector invokes the
candidate's unchanged parser and complete-map builder, serializes every key and
count, and compares each table to the independent slice oracle. This inspector
is diagnostic code and is absent from measured commands. The actual main's
one-time conversion and seven-map invocation still require review in its WAM.

The source adapter adds only the observed ordinary `atom_string/2` binding to
the frozen grammar. Local definitions retain precedence; another module,
another builtin and hidden goal data remain rejected. Both source bundles
include the main, `clbg_io.pl` and `clbg_records.pl`. Native reader bytes must
equal both the original and actual compiler inputs, and their definition
inventory must equal the corresponding WAM. Every owner expansion is retained
for independent review. Projections remain unadmitted until that review.

Preparation and execution require the existing common mutex and retained
Python interpreter. Preparation performs physical input verification and must
wait for the measurement and publication lane to be free:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/prolog_knucleotide_bounded.py prepare --plan experiments/prolog/knucleotide-linear-v1/qualification/plan-v1.json --fixtures experiments/prolog/knucleotide-linear-v1/qualification/fixtures-v1 --output experiments/prolog/knucleotide-linear-v1/qualification/run-v1
```

After reviewing the actual plan and its printed SHA-256, execute the same
controller with `run --plan … --plan-sha256 …` through the existing durable
owner. Each native invocation retains its full stdout, stderr, owned-process
lifetime and resource outcomes. Limits remain 30 seconds, 2 GiB process-group
RSS, an 8 MiB native file and five seconds for cleanup. There are no automatic
retries. A failure retains its actual partial evidence and does not become a
successful sample.

The resulting report can establish bounded outputs and exact compiler inputs.
It grants neither source-work nor canonical-count admission. Independent
review must inspect both actual WAM listings, all owner expansions, closed
native receipts and full runtime/dependency pins before issuing the separate
`prolog-knucleotide-linear-qualified-v1` disposition. That disposition supplies
the original two profile IDs with corrected source/QLF/count bindings, four
evidence references (compilation, bounded, source counts and required work),
all physical pins and exact closed artifact inventories. Original runtime,
environment, workers and other unchanged profile fields remain identical.
Its full-timing and chart-admission flags stay false. The remaining-slot
controller rejects a missing or incomplete disposition.

The 21 pure regressions in `tools/qualification/test_prolog_knucleotide_bounded.py`
passed in 0.025 seconds. They include retained-control selection, exact outputs,
source binding and late report/artifact mutation failures. They launch no Prolog
process and perform no runtime-closure hashing. Full-size timings remain a later,
separately owned serial stage.
