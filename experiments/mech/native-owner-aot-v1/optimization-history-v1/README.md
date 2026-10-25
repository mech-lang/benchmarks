# K-nucleotide optimization history

This packet reconstructs the retained current-machine measurements from the
earlier required-hash-work implementation through the explicit source-map
compiler experiments. It collects 94 measured stages, 220 cohort records and
1,009 Mech process observations. It runs no benchmark subjects and changes no
canonical timings or website data.

`history.json` retains every observation, its exact process receipt and hash,
cohort medians, input size, contemporaneous Rust denominator, compiler commit,
source receipt and relevant paired comparisons. `history.csv` provides the
cohort-level data. `history.html` is the interactive conversation fragment;
its horizontal axes use actual calendar time, displayed in America/New_York.
The `png-white-blue` directory contains static white-background exports with
blue circles for all cohorts, including uncertain and negative trials, plus
their export script and source/image hashes. Input sizes remain separate.

## Time recovery

Every plotted process has a retained macOS birth identity with epoch seconds
and microseconds. The builder matches each candidate duration to exactly one
quantitative process in its own study or explicitly referenced aggregate
studies. It requires successful exit, reaping and process-group closure.
All 1,009 observations have recovered launch timestamps; none uses a file
modification time or a commit-time approximation.

A raw dot appears at its process launch time. A cohort marker appears at the
median launch timestamp of its observations. The first launch and last
completion are retained as the measurement window. Compiler commit timestamps
are separate metadata, not the horizontal coordinate. The recorded series
runs from October 22, 2026 at 22:12 EDT to October 25 at 13:41 EDT, about
63.5 calendar hours. This is a measurement interval, not an estimate of active
agent time or a claim that every intervening minute was spent benchmarking.

## Reading the measurements

- Each input size has its own plot. No small-input duration is extrapolated to
  the 125-million-base input. The 330× Rust checkpoint belongs to the
  one-million-base diagnostic.
- Each ratio divides that cohort's Mech median by its own Rust median. Rust
  observations vary across sessions; historical ratios are not a controlled
  experiment isolating each individual compiler change.
- Independent repeat cohorts remain separate. Five earlier aggregates are
  exact observation subsets of later expansions and are listed in `excluded`
  rather than counted twice as independent replication.
- Circles represent cohort medians or explicitly identified single runs.
  Diamonds flag selected explicitly uncertain or negative experiments. A
  circle does not assert a statistically established individual improvement.
  Faint dots preserve all candidate process observations.
- The trace connects the earliest recorded cohort for each source-map stage,
  ordered by measurement time. It includes failed performance trials and does
  not imply that all successive changes were cumulatively retained.
- The earlier 9.39939-second required-work lowering uses the same full input
  and machine but a different source/lowering. Its square is separate from
  the explicit source-map trace. The source-map path's earliest completed
  full-input qualification is 118.60063 seconds, one process.
- An earlier full-input process exceeded 180 seconds. Its receipt remains
  linked in `notes`; the deadline is a censored lower bound, not a completed
  time or a fabricated Rust ratio.
- The older M1/PR909 observation is outside these curves because it used a
  different lowering. No cross-machine timing is joined into this trajectory.
- Some implementation and correctness milestones have no primary timing
  cohort. They do not receive invented numeric points. The earlier rolling
  key and batched-callback experiments explicitly retain diagnostic profiles
  without quantitative timing cohorts in their own study records.

The final pure-scalar source has full-input medians of 0.5574536455 and
0.5560369795 seconds, versus contemporaneous Rust medians of 0.55756275 and
0.556436021 seconds. Both paired Rust confidence intervals include zero.
These are practical matching medians, without a proved speed advantage or
predeclared equivalence result. The current one-million-base diagnostic
regression remains visible.

## Reproduction and display checks

Run `python3 build.py` from this directory, with the complete evidence checkout
and the compiler history available at the `SOURCE` path specified near the
start of the builder. The builder uses only Python's standard library and
Git, validates medians against all observations, verifies the full input hash,
and reconstructs process clocks directly from retained JSON receipts.

The fragment embeds the plotting data and loads version-pinned D3 7.9.0. It
keeps selection details above the charts, supports point and step-list
selection, and remembers a pinned stage in the conversation. The retained
preview check covers four plots at desktop, 360-pixel and 320-pixel outer
widths, matching SVG widths, no horizontal overflow, the complete stage list,
and selecting the earliest and latest stages. It is a display check, not a
benchmark process or a new timing result.
