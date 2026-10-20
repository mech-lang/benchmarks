# BQN FASTA native-search experiment

The complete empty-safe candidate passed the exhaustive lookup check, all16
shared bounded cases, and three complete full-workload outputs. Three matched
original-source controls also passed their full outputs. Historical profiles and
sources are unchanged; chart admission is a separate evidence review.

| Exact source | Full-process median (s) | Retained application LOC |
| --- | ---: | ---: |
| Original control | 10.782258 |24|
| Native Bins, empty-safe | 10.348043 |24|

The matched median ratio is **1.042×**,
a **4.03%** reduction in elapsed
time. Each new observation is below every control observation in this small
cohort. This is a modest measured effect, with no global optimality or universal
runtime claim. Samples, standard deviations, process/power records and exact
output identities are retained in [the full report](full-matched-v1/report.json).

The native f64 Bins call replaces a boolean comparison matrix and its reduction.
It searches the original floating cumulative probabilities and keeps every one
of the200,000,000 naive LCG updates, both original random records, ALU repetition,
formatting, all254,166,745 output bytes and process startup/exit. No state lookup
table, random-period reuse, threshold scaling or new native workload helper is
introduced. All full outputs have SHA-256
`3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa`.

An independent untimed test compares both lookup forms on all139,968 normalized
generator states for both probability vectors, exact threshold ties, duplicate
thresholds and empty input. [Bounded evidence](bounded-v1/report.json) records
all16 exact complete-output checks for the candidate. The unchanged parent and
minimal lookup-only control each retain an observed N=0 failure at their empty
last-state pick. These two failures are explicitly recorded as control failures;
they are never counted as correct outputs or transferred to the complete
candidate. All other control cases pass. The empty-safe source preserves the
seed when no random values are generated.

[The approved source ledger](source-ownership-v1/bins-empty-safe-counts.json)
retains the exact existing24/24 rule, including standalone closing rows. This is
an exact-source extension of the old rule, not native formatter qualification or
a universal logical-source certificate. UTF-8, gzip and BPE sizes remain separate.

The runtime is the pinned uninstrumented rebuilt CBQN release used in the other
BQN audit experiments. Full runs were serial under the common timing mutex,
with AC power and low-power mode disabled. Complete measured stdout is retained
locally and excluded from Git because six copies total over1.5GB. Committed raw
process receipts retain complete-output size/hash; an offline replay without
those streams cannot independently rehash their full contents. The bounded
streams and source/controller snapshots remain in the repository.

The frozen [pre-run source review](REVIEW.md), [execution plan](execution-plan.json)
and [controller instructions](RUNNER.md) preserve what was proposed before
execution. This result does not establish whether remaining time is dominated
by the LCG scan, allocation, wrapping or output; those require separate evidence.
