# DEFLATE level-12 reference correction

The metrics page selects retained libdeflate 1.26 level-12 observations for all
12 DEFLATE inputs. The wrapper explicitly calls
`libdeflate_alloc_compressor(12)`. Reference selection requires its pinned
wrapper and library identities, the same task, and the same environment.
Historical zlib-rs 0.6.8 level-9 observations remain in their original campaigns;
they are not an equivalent level-12 control and are never a fallback.

The retained libdeflate and Mech timers have different boundaries. Raw medians
are labelled **Reference only**, with no automatic speed ratio. No benchmark was
rerun, and no recorded sample, timing, source hash, or campaign was changed.

The website correction is commit
`9a0bd549cd2807932ddecc3f2d24fa6c9d127e97`. Follow-up
`0f46fd25125e71a496a231b2fd50741bbc9880ac` publishes the existing mobile detail
layout from benchmark commit `e0a70cb48f2ee0f3ffa86db575d849e7fb18d1a7`.
The full browser check exposed that this earlier layout fix had not reached
the website. The follow-up changes no measurement or reference selection.

Validation evidence:

- `selection.json`: all 12 default DEFLATE rows select level 12, match task and
  environment, and expose no ratio or percentage.
- `live-files.json`: published asset bytes match the website commit.
- `browser.json`: live desktop and mobile interaction checks, source and sample
  links, lazy loading, and absence of browser errors.
- Model and entry-point rendering tests cover missing references, mismatched
  provenance, task/environment changes, and rejection of level-9 fallbacks.

The source fix is retained on `codex/deflate-level12-reference`, with a draft
[pull request](https://github.com/mech-lang/benchmarks/pull/8) targeting the active
`codex/rust-controls` branch.
