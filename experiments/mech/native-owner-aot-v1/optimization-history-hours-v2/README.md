# Direct exponential fits of the full-input trajectory

This revision preserves exactly the 118 full-input cohorts, 708 process
observations and elapsed-hour coordinates in `optimization-history-hours-v1`.
It fits the runtime ratios directly instead of fitting their logarithms.
Neither the first observation nor a Rust parity floor is fixed.

For `r(h) = A exp(-k h)`, direct nonlinear least squares gives
`A = 215.6051`, `k = 1.15324` per hour and original-scale R² = 0.993465.
For `r(h) = C + A exp(-k h)`, it gives `C = 1.55418`, `A = 214.33265`,
`k = 1.19639` per hour and original-scale R² = 0.999037. These scores apply to
the original ratio scale and are not the log-space scores in the earlier
figure. The observation weights remain equal per retained cohort.

At each fixed `k`, the linear least-squares parameters `A` and `C` are solved
analytically. A broad logarithmic scan of positive `k` brackets local minima;
each is refined with golden-section search. The smallest error is selected,
checked against the scan, and its first derivatives are recorded. Amplitude
and offset are nonnegative. The offset optimum is in the interior of this
constraint. `analysis.json` retains parameters, residual errors, derivative
checks, search bounds and the input analysis hash. No benchmark is rerun.

The main plot uses a linear vertical axis so the initial decay is visible.
A magnified inset uses the same full-input observations from hour 3 onward
with a logarithmic vertical axis. The inset exposes the later data falling
below the offset model's fitted 1.55× level, toward approximately 1× Rust.
The model is descriptive: its high original-scale R² is dominated by the
large early values and does not establish a physical floor or a forecast.
The plain exponential also underpredicts the later tail.

Numbered annotations preserve the major measured drops. Percentages compare
each candidate median with its contemporaneous parent, rather than with an
adjacent historical dot. The first three highlighted checkpoints are single
runs. Repeated cohorts and unsuccessful trials are included throughout.
The actual initial ratio in the retained receipt is 216.164749× Rust, the
checkpoint previously described as approximately 218×.

The original full-input evidence and exclusion rules remain in the v1 packet.
The SVG/PNG, fitting script and browser layout checks are retained here for
reproduction with `python3 build.py` followed by `node export-png.cjs`.
