# Controls and the metrics view

Rust is the default control for a task. Controls appear beside Mech in the same
row at [mech-lang.org/metrics](https://mech-lang.org/metrics/). A language runtime
is not a task. JVM is removed from the active catalog; its original observations
and Java correctness evidence remain in their unchanged historical campaigns.

The default view combines accepted measurements across runs. It selects the
first qualified execution path declared by each task, then the newest accepted
run on that path. It never takes the fastest sample or combines boundaries.
Source and decoded paths remain selectable. A later failed qualification does
not erase a successful result; named campaigns and “Needs attention” retain
failed observations. Tasks without a result for the selected view are omitted
instead of appearing with empty timing cells. Each result links to its own run.

Every active task now has a measured control in the default view. The new paired
campaigns cover all 44 resident/scalar-JIT cases, 1/2/4-process scaling, the native
build, full K-nucleotide and all 12 compressor inputs. N-body and Related Post Gen
retain their previously qualified controls. Each control exposes its individual
observations and exact source. Earlier campaigns retain their original missing
controls rather than receiving fabricated or mismatched historical timings.
Existing previous-compiler comparisons remain under **History comparison**.

The [independent Rust package](controls/rust/README.md) links no Mech code and
does not read oracle answers. Python checks full trajectories, publication before
execution, recovery, retained snapshots and ownership teardown. Mech additionally
performs its runtime scheduling, admission and budget accounting; these are task
comparisons rather than claims of identical internal machinery. Native Rust
ownership is not reported as a fictitious Mech resource ledger or artifact.

The resident campaign uses five independent forks and 1,000 complete input
schedule cycles, with fixed catalog cycles for EKF and the suspended state
machine. Source, decoded and Rust workers run in seeded random order within each
block on the same machine. Every measured observation, including adverse ones,
is preserved. The separate verification clocks are not accepted timings.
The capacity cases use a later independent five-fork repeat with 256 complete
cycles after disabling an expensive progress monitor. The first sweep remains
inspectable and is identified in the findings; its samples were not removed.

Compression reports **output size alongside time**. Rust uses genuine Rust
zlib-rs 0.6.8 at maximum level 9; Mech level 12 must match its pinned Roc stream.
Both consume the complete input, preserve the prefix and aliases, produce an
independently owned stream and pass independent inflation/EOF/no-trailing-data
checks. Different compressed sizes make the time ratio a codec tradeoff rather
than an equal-quality speed claim. Historical Roc/libdeflate observations remain
in their original campaigns and downloads.

## Fixed Mech controls

[control-policy.json](control-policy.json) pins promoted Mech controls. Promotion
requires a frozen Rust target, retained primary samples and independent
confirmation. The exporter checks the qualification hash and the confirmed
checkpoint. A faster current observation cannot move that control. A different
source or measurement boundary cannot silently inherit its qualification.
Controls are specific to the task, execution path and metric: a processing win
does not promote the whole-process control.

Related Post Gen is the other application benchmark developed in November. Its
fixed target is the unchanged examples in
[zupat/related_post_gen](https://github.com/zupat/related_post_gen) at
`fc2982b0c929b1b701209d401a1dc30c773ef4ab`. It processes all 5,000 posts and
materializes the complete ordered JSON result. The retained November 12 primary
and confirmation cohorts have 31 and 13 randomized fresh-process rounds.
`tools/import_related_posts.py` imports those observations, preserving original
reports, source/binary hashes, all other variants and adverse samples. Imported
timings are not new runs. Every receipt is checked against its parent report.

The managed IR355 confirmation median is 1.400292 ms; the compact IR353 median
is 1.174375 ms. Both beat the fixed original `rust_con` reference, 1.866250 ms,
in all confirmation pairs. The original Rust example initializes its eight-thread
Rayon pool before its processing timer. Mech's four workers are created and
joined inside the larger continuous post-JSON interval. The conservative winning
comparison preserves that Rust advantage; it does not claim identical timers
or a win over every additional custom Rust experiment. Compact omits ordinary
managed admission/resource/recovery and remains a separate execution path.

Those confirmed Mech checkpoints are held as the post-JSON controls. Whole
process remains separate: managed Mech 48.851250 ms, compact 19.878875 ms, original
Rust 17.980292 ms in confirmation. Rust remains the whole-process control.

## Fresh Rust measurements

`2026-11-17-rust-nbody-001` runs the full 50,000,000-step task in five seeded,
randomized Mech/Rust pairs. The Rust source is the unchanged retained Benchmarks
Game #3 implementation, including its authorship record. Both clocks include
launch, all computation, complete output and exit. Mech startup JIT is included;
building either executable is excluded. There are no discarded warmups. Every
output is validated against the independently preserved initial/final energy.

Mech median: 1.329558333 s. Rust median: 1.068109792 s. This is an informational
task comparison, allowing implementation/vectorization differences. It does not
promote a new Mech control. Exact Rust build flags, compiler version, binary hash,
commands, run order and outputs accompany the campaign.

```sh
python3 tools/run_rust_control.py --application-worker .local/applications/worker.json --forks 5 --seed 202611171 --output results/campaigns/NEW-RUST-CONTROL
python3 tools/import_related_posts.py --source /path/to/pinned/mech/benchmarks/related-post-gen --output results/campaigns
```

Use new campaign directories; never overwrite an earlier measurement.
