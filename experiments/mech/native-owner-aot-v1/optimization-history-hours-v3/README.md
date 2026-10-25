# Fast and slow exponential components on the original log chart

The 118 full-input cohort ratios and 708 process observations are identical
to `optimization-history-hours-v1`. This revision preserves the original
single chart's logarithmic vertical axis, elapsed-hour horizontal axis,
measured dot coordinates, white background, blue points and nine annotated
changes. Only the fitted curve and fit-related text change. There is no inset.

The fitted model is

`r(h) = C + A_fast exp(-k_fast h) + A_slow exp(-k_slow h)`.

Two exponential components allow a fast initial decline and a slower later
decline. This is a sum of exponentials, rather than one exponential nested
inside another. Both fitting objectives are retained: squared errors in the
original ratios and squared errors in log ratios. The plotted curve uses
the original-ratio optimum, continuing the direct-error criterion of v2.

The plotted parameters are approximately `C = 1.00602`, `A_fast = 212.18074`,
`k_fast = 1.246461` per hour, `A_slow = 2.92074`, and `k_slow = 0.0825811`
per hour. Original-scale R² is 0.999817, log-scale R² is 0.996538, and
`exp(RMSE(log r))` is 1.044795. The log-error optimum has log-scale
R² = 0.997090 and a multiplicative RMSE of 1.040993.

Nelder–Mead optimization uses positive amplitudes and offset and ordered,
positive decay rates. Five different starting points converge to the same
optimum for each objective. The original-error optimum's analytic first
derivatives are checked and recorded. The offset is fitted freely; Rust
parity is not imposed. All trials and repeated cohorts remain in the fit.
No benchmark is rerun, and neither the fitted offset nor either rate is a
forecast or a causal model of compiler development.

`analysis.json` records both objectives, all optimization attempts, source
hashes and the derivative checks. `build.py` verifies that every original
measured dot is unchanged. The SVG is exported to a white-background PNG
with the companion browser export, followed by a visual check. The underlying
measurement provenance and exclusions remain in the v1 packet.
