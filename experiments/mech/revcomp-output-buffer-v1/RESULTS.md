# Native output-policy results

Each table is its own seven-round shuffled serial cohort. Ratios use that
cohort's fresh **current Mech Cranelift AOT control as 1.00×**. Lower is faster.
Input contains 250 million generated bases. Every subject includes fresh-process
startup, all stdin/stdout, flush and shutdown. Compilation is excluded.

## Larger native spans

Denominator: current Mech **0.123605625 s = 1.00×**.

| Variant | Median (s) | SD (s) | × Mech AOT | Peak RSS (MiB) |
| --- | ---: | ---: | ---: | ---: |
| Original Mech | 0.14452 | 0.00571 | 1.169× | 367.2 |
| Current Mech | 0.12361 | 0.00168 | 1.000× | 125.1 |
| 2 MiB wrap / 1 MiB stream | 0.12523 | 0.00314 | 1.013× | 126.7 |
| 4 MiB wrap / 1 MiB stream | 0.13273 | 0.00137 | 1.074× | 188.7 |
| Unchanged published Rust | 0.11083 | 0.00189 | 0.897× | 125.1 |

The 2 MiB policy uses 1.3% more median elapsed time and is faster in only two of
seven paired rounds. The 4 MiB policy uses 7.4% more time and loses every round.
The latter has consistently higher child system CPU and RSS. That observation
does not prove an allocation, I/O or scheduler cause. One original-parent run
has markedly higher RSS/time than its other runs; it is retained without trimming.

## Smaller outer buffers

Denominator: current Mech **0.1234035 s = 1.00×**.

| Variant | Median (s) | SD (s) | × Mech AOT | Peak RSS (MiB) |
| --- | ---: | ---: | ---: | ---: |
| Current Mech | 0.12340 | 0.00133 | 1.000× | 125.1 |
| 256 KiB wrap / 128 KiB stream | 0.13729 | 0.00884 | 1.113× | 124.1 |
| 1 MiB wrap / 512 KiB stream | 0.12625 | 0.00466 | 1.023× | 125.4 |
| Unchanged published Rust | 0.10926 | 0.00196 | 0.885× | 125.1 |

The smaller stream buffer with the existing wrap size loses every round, with
11.3% more median time and substantial variation. The 1 MiB policy loses six of
seven rounds and uses 2.3% more median time. These reduce median child user CPU
slightly but fail to improve wall time. No fastest-candidate selection is made.

The current runtime remains selected. Its original compaction and reuse gains
are not undone. The remaining Rust gap is still present; this experiment does
not assign it a proven cause. Copy elimination alone is not evidence of an
end-to-end improvement. Native wrapping work and complete outputs are unchanged.

All four policies pass thirteen runtime tests, both three-way comparisons retain
identical behavior on all 61 inputs, all nine official output checks pass, and all
63 full-size outputs match. Eleven existing extended source limitations remain
explicit. The [study](README.md) links exact sources, objects and closure proof.

AC power, disabled low-power mode and default power settings are recorded before
and throughout both cohorts. Swap is nonzero; exact first/last observations are
in `analysis.json`. Frequency, temperature, core placement and allocation traces
are not captured. Short timings and system variability limit generalization;
all samples remain available. No benchmark-specific CPU/power policy is applied,
and no published Rust source is edited.
