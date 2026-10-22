# Mech pi-digits performance study

This study compares the retained Mech advance-spigot source with a source-level
strength reduction and a shorter equivalent form, unchanged published Rust #3, and the qualified Janet
positive-division form. Every subject computes 10,000 digits sequentially with
unbounded integers and evaluates both candidate divisions. Fresh-process timing
includes startup, all computation, complete output, flushing and shutdown.

The new Mech form reuses the first extraction numerator: after dividing
`3*q + r`, it adds `q` to the preserved scratch integer and divides `4*q + r`.
It uses existing general bigint operations; no native pi kernel, result cache,
quotient inference or omitted second division is introduced. The parent source
remains unchanged. Local candidate authoring used Codex GPT-6 family; the exact
serving model is not independently established.

The compiler's existing floor-to-u64 runtime already selects quotient-only
truncating GMP division when signs agree and preserves floor semantics otherwise.
That optimization is not new to this study. Relevant control compiler/runtime
files are checked against the current upstream branch in `upstream-review.json`.
The complete compiler baseline, exact sources and runtime builds must remain
identified separately from historical website results.

Historical reference medians are Mech AOT 0.300272042 seconds (1.00×), Rust #3
0.303086375 seconds (1.01×), Rust #4 0.491783209 seconds (1.64×), and optimized
Janet 0.294685542 seconds (0.98×). These were not a paired current cohort and do
not establish that Janet is reliably faster than Mech.

Rust #3 is the original retained [Benchmarks Game submission](https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/pidigits-rust-3.html),
contributed by Matt Brubeck, TeXitoi and Takumi Kato with the source's original
inspiration notices. It is rebuilt without changing its application bytes.

`run.py qualify` checks all complete outputs at digit counts 0, 1, 2, 3, 9, 10,
11, 19, 20, 21, 27, 30, 31, 97, 100, 257 and 1,000 against the independently
implemented Python arbitrary-integer reference. `run.py time` requires that
qualification, then runs seven shuffled serial rounds at 10,000 digits. Subjects
inherit the common timing mutex and are independently observed and reaped.
Compiler work must finish before timing. Complete output checks and process
cleanup occur after the observed exit; no process phases are subtracted.

The [verified results](RESULTS.md) include all 35 complete-process samples, 85
bounded output checks, 45 real-GMP work witnesses and five loader captures. The
shorter optimized Mech form takes 0.2901 seconds (1.00× optimized Mech AOT);
Rust takes 0.3097 seconds (1.07×) and Janet 0.3083 seconds (1.06×). The canonical
website catalog is unchanged pending admission of these experimental profiles.
