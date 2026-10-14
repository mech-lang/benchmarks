# Prolog full-study continuation with linear reverse-complement

This additive stage preserves the nine qualified regex-redux samples from the
[closed original study](../full90-v1/cancellation.md) and schedules 81 new full
processes. It replaces only the quadratic reverse-complement implementation.
The original plans, cancelled attempt, raw receipts, sources, and compiled
artifacts remain unchanged.

The controller is source-prepared. No continuation plan or full-workload result
is established by this document. Native execution requires the exact newly
prepared plan digest and a fresh output directory.

| Scope | Processes or samples |
| --- | ---: |
| Reused regex-redux samples: two Prolog slots and their original matched Mech control, three each | 9 |
| New Prolog processes: nine workloads, two slots, three each | 54 |
| New matched Mech control processes: nine workloads, three each | 27 |
| Maximum new full processes | 81 |
| Combined requested sample slots | 90 |
| Original cancelled reverse-complement attempt, excluded from timing | 1 |

The two new reverse-complement IDs are `prolog-revcomp-linear-compact` and
`prolog-revcomp-linear-optimized`. They deliberately execute the same source and
QLF. The second is an explicit equivalent-source alias; it is not evidence of a
distinct optimization. All other 28 profile records, including all ten Mech
controls, retain their original execution metadata. The original rotation and
resource limits remain: three samples, a six-hour native deadline, 22,200-second
outer supervisor deadline, and 10 GiB process-group RSS ceiling per attempt.

## Evidence required before execution

[prolog_linear_full.py](../../../tools/qualification/prolog_linear_full.py)
checks the exact original cancelled plan/report/terminal/durable bindings and
[cancellation closure review](../full90-v1/cancellation-review-v1.json). It
replays each preserved regex sample through the frozen independent receipt and
outer-supervisor validators. All 27 saved raw, supervised, and outer receipts
must match the cancellation's preserved digest map. The interrupted original
attempt 10 contributes no duration, sample, or timeout claim.

For the replacement, preparation and execution replay the closed
[542-process bounded evidence](../revcomp-linear-v1/bounded-run-v1/report.json)
with the existing strict validator, including 540 candidate invocations. They
also verify the nine closed source-reader lifetimes and complete artifact
inventories. The exact additional reviews are:

- [Compiled work and source linearity](../revcomp-linear-v1/compiled-work-review.md),
  SHA-256 `2225c08c30bf3e5aa518c57d96d6e6ffd9596c50e7858abfde96dab03ca7c1ae`.
- [Canonical source ownership](../revcomp-linear-v1/source-counts-v1/source-count-review.json),
  SHA-256 `808f8d4f98d2826925a27b34f4116e5a84d454cc7cb0d55935c0af7a9b4e9677`.
- [Actual native source projection](../revcomp-linear-v1/source-counts-v1/run-v1/candidate-original-source/projection.json),
  SHA-256 `7c42ea94e407bdd62778960292e305e95f51bb5df6067862ee83cb4925f006c5`.

The replacement has 242 canonical units and 146 physical nonblank, noncomment
lines. Its original source and actual compiler input have SHA-256
`bb4826e39721c6e4e61330ee3f56db604e1d48498c32fdd9453b133e35508322`;
its executed QLF has SHA-256
`c4526a2d463d5c9c570e88b5ab68237ecf61244d104825ab1e4fbb66b13c1f9e`.
The compiled review establishes bounded traversal and full-record work, not
measured scaling or full-input completion.

## Execution and accounting

Preparation and execution acquire the existing cancelled owner's private lease,
the existing Prolog suite lease, and the common timing mutex, checking their
recorded inode identities. The common mutex is held continuously throughout
preparation or the complete new cohort, including input/runtime verification,
all attempt cleanup, and final artifact closure. Native children inherit it.
No native or compiler process is used for preparation or evidence replay.

The native command for the new reverse-complement rows is the retained SWI VM
with `-q -O -f none --stack-limit=8g -s candidate.qlf -g
clbg_revcomp_linear:run`, using its retained `SWI_HOME_DIR`. Production capacity
is 65,536. Runtime startup, QLF loading, full input, all work, complete output,
and shutdown remain inside the timing interval. Compilation, pin hashing and
output validation remain outside it. Full reverse-complement input is the
original `n=25000000` fixture, containing 250 million sequence bases; its full
output must be 254,166,745 bytes with the original required digest.

The unchanged frozen sampler and
[ownership supervisor](../../../tools/qualification/prolog_supervisor.py)
perform each attempt. The continuation saves new attempt IDs 1–81 in its own
directory; reused IDs remain explicitly tied to the original directory.
Returned attempts and interruption wrappers are persisted with signals masked.
Every validated raw/supervised/outer receipt is immediately snapshotted, then
checked again during finalization. Successful summaries are reconstructed from
the entire saved ledger. A native failure can skip only subsequent slots for
that same profile under the existing isolated-failure policy; no attempt is
retried. Integrity, environment, or ownership failures stop the continuation.

Each workload's ratios use the median of its own three matched Mech samples.
Regex-redux retains its original matched control; the other nine workloads use
their newly sampled controls. This is an explicitly combined study spanning two
measurement periods, not a claim that all 90 samples were collected in one
continuous session. Successful full stdout is validated and discarded by the
original sampler; byte counts, hashes, and validation receipts are retained.
All producer outputs keep `full_timings_qualified=false` and
`chart_admission=false` pending independent reconciliation and publication.

## Commands

Use the retained Python with `-I -S -B`, without optimization. Paths below are
physical absolute paths. Preparation itself owns the required locks and refuses
an existing plan or output directory:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/prolog_linear_full.py prepare --plan /private/tmp/mech-benchmark-completion/experiments/prolog/full81-linear-v1/plan-v1.json --output /private/tmp/mech-benchmark-completion/experiments/prolog/full81-linear-v1/run-v1
```

After reviewing that concrete plan, its digest is the `--plan-sha256` argument
for the exact target command:

```text
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/prolog_linear_full.py run --plan /private/tmp/mech-benchmark-completion/experiments/prolog/full81-linear-v1/plan-v1.json --plan-sha256 <reviewed-plan-sha256>
```

Run that target through the existing generic
[Prolog durable launcher](../full90-v1/launch_durable.py), with
`--job linear-full81-v1`, repository `--cwd`, and the exact target argument list
as `--command-json`. The new durable folder is
`experiments/prolog/full90-v1/owned-jobs/linear-full81-v1/`. The target argument
list has no `-u`; the launcher's own detached worker may use `-u` independently.
The launcher refuses an existing job folder. Exit zero alone grants no timing
admission.

The focused [pure tests](../../../tools/qualification/test_prolog_linear_full.py)
exercise exact schedule replacement, alias identity, actual preserved sample
semantics, cancellation exclusion, source-count review scope, summary replay,
failed-profile skipping, and detection of changed validated artifacts. They
perform no native execution, acquire no timing lock, and hash no runtime
closure. They do not substitute for concrete-plan review or the future native
continuation.
