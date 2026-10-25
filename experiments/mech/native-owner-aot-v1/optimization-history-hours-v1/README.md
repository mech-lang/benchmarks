# Full-input optimization history in elapsed hours

This figure collects the 125-million-base source-map compiler trials from the
first completed full-input run through the latest separate-load trial. It
contains 82 implementation stages, 118 retained cohorts and 708 unique Mech
process observations. All measurements include complete process startup and
exit. No benchmark subject is executed to build the figure.

The horizontal coordinate is elapsed hours from the first completed run,
2026-10-23 17:22:52.061441 UTC. It uses exact retained process launch receipts,
not commit timestamps, and includes all intervening gaps. A cohort appears at
the median launch time of its observations. The initial run took
118.600627083 seconds versus Rust's 0.5486585 seconds, or 216.164749× Rust; this
is the checkpoint previously described as approximately 218×.

`build.py` reads the original `optimization-history-v1/history.json` snapshot
without modifying it and adds the two subsequently completed separate-load
cohorts. It checks receipt hashes, process completion, launch timestamps,
medians and input identity. Parent and anchor measurements are retained in
the underlying studies but are not treated as new implementation stages.
Smaller inputs, the earlier different library-update lowering, censored
timeouts and instrumented runs are excluded from this figure. Repeated
cohorts and negative trials remain visible; it is not a best-so-far envelope.

The latest two dots are the separate early count-load experiment, an
unpromoted regression. The retained production source is still
`93015bc6298b77fd10402e88baea5e3bfd89b28d`. Its first two full-input medians
were 0.5574536455 and 0.5560369795 seconds, both approximately 1.00× their
contemporaneous Rust medians. The paired Rust confidence intervals include
zero; these observations do not establish a speed advantage.

## Exponential fit

The fit is `r(h) = A exp(-k h)`, where `r` is the Mech/Rust runtime ratio and
`h` is elapsed hours. Ordinary least squares is applied to the natural log of
the ratio, with equal weight for each retained cohort. The intercept is free;
the fit is not forced through the first extreme observation, and no Rust
floor or future asymptote is imposed. The curve is drawn only over the
observed time range. Repeated cohorts affect this descriptive fit, and the
cohorts are not claimed to be statistically independent observations of an
optimization process.

The fitted values are `A = 4.6403394646`, `k = 0.03883408068` per hour,
log-space R² = 0.5217015322, and `exp(RMSE(log r)) = 1.6737468467`. The same
curve's R² in the original ratio scale is only 0.02065817633. A single global
exponential describes this trajectory poorly: the early changes produce
large discrete drops, followed by a much slower tail. Its implied half-life
is a property of this poor descriptive fit, not a forecast.

## Discontinuities

Numbered labels identify major drops and representative later improvements.
Their percentages compare a candidate median with the parent median from the
same study. They do not divide adjacent historical dots, which can have
different Rust denominators or different parent branches. The first three
highlighted changes have one candidate observation each; those percentages
are descriptive measurements without an independent replication claim.
The labels do not imply that every timed trial was cumulatively retained or
that the individual percentage reductions can be added.

`analysis.json` preserves all observations, fitted parameters and source
receipt hashes. `cohorts.csv` gives the graph's cohort data;
`discontinuities.csv` gives before/after seconds and ratios for the labels.
The SVG and PNG use a white background and blue measured dots. The companion
export checks text bounds and label overlaps in an isolated browser and
records image hashes in `export-verification.json`. The PNG was also
visually inspected.

Regenerate from the complete retained evidence checkout with
`python3 build.py`, then export with `node export-png.cjs`. The export script
uses the installed isolated Playwright/Chrome runtime and writes the same
PNG into the evidence folder and the durable visualization directory.
