# Janet pi-digits results

Positive-operand quotient division gives a **0.295-second median (0.98× retained
Mech AOT)** versus the parent's **0.402 seconds (1.34×)**, a **1.36× observed
speedup within Janet**. The shorter composed form measures **0.299 seconds
(1.00×)** and uses **417 lexical tokens versus 454** for the parent.

| Final-cohort implementation | Median seconds | × Mech AOT | Maximum peak RSS across seven samples |
|---|---:|---:|---:|
| Parent | 0.402 | 1.34× | 6.22 MiB |
| Unsigned emitted digit | 0.402 | 1.34× | 6.69 MiB |
| Fused advance/removal | 0.390 | 1.30× | 5.86 MiB |
| Fused extraction numerator | 0.390 | 1.30× | 5.91 MiB |
| Fused numerator + unsigned digit | 0.392 | 1.30× | 6.36 MiB |
| Fused positive division | 0.295 | 0.98× | 5.73 MiB |
| Compact initialization, floor division | 0.390 | 1.30× | 5.86 MiB |
| Compact initialization, positive division | 0.299 | 1.00× | 5.77 MiB |

Mech AOT's retained same-input median is **0.300272042 seconds (1.0×)**, profile
`pidigits:mech-pi-final-advance-signed`. It is not a freshly paired Mech control;
these close ratios do not establish a current cross-language ordering.

The final cohort has seven shuffled serial rounds across all eight exact sources,
always 10,000 digits. All 56 complete outputs match the independent 16,893-byte
reference and the preserved historical full-output SHA-256. Earlier exploratory
cohorts contain another 35 and 49 valid observations. All 140 are retained;
none are discarded or pooled across cohorts to select the final medians.
Every positive-division form is faster than its within-round parent in all seven
final rounds. The raw elapsed values drift during the cohorts. Paired round
ratios support the main effect, but the small gap between the two fastest forms
is not a universal ranking. The unsigned conversion alone shows no clear gain.

## Why the library API matters

Both advance/removal fusion changes use ordinary general GMP multiply-accumulate
operations. They give only a modest improvement on their own. The larger gain
comes from the division API. Numerator and denominator are initialized positive
and multiplied only by positive values. At an extraction, the unchanged guard
requires accumulator > numerator, so both extraction numerators are positive.
Floor and truncating integer division consequently return the same quotient.
The source still evaluates both divisions independently using unbounded GMP
integers, then compares their results before accepting a digit.

The official GMP 6.3.0 source supplies a consistent explanation: `mpz_fdiv_q`
allocates a remainder and calls `mpz_tdiv_qr` to support floor correction;
`mpz_tdiv_q` calls the quotient-only `mpn_div_q` path. Selecting the latter under
the proven positive domain avoids that library work without omitting either
required extraction. The version-matched release files and their licenses are
retained under `gmp-release-source-v1`; this is source inspection, not a claim of
an independently reconstructed source-to-installed-binary chain.

## Source measures

| Implementation | Physical rows | UTF-8 bytes | Deterministic gzip bytes | BPE tokens | Janet lexical tokens |
|---|---:|---:|---:|---:|---:|
| Parent | 59 | 2,538 | 863 | 709 | 454 |
| Unsigned emitted digit | 59 | 2,555 | 862 | 713 | 457 |
| Fused advance/removal | 57 | 2,463 | 855 | 696 | 442 |
| Fused extraction numerator | 58 | 2,510 | 861 | 715 | 452 |
| Fused numerator + unsigned digit | 58 | 2,527 | 860 | 719 | 455 |
| Fused positive division | 57 | 2,463 | 855 | 696 | 442 |
| Compact, floor division | 53 | 2,385 | 842 | 671 | 417 |
| Compact, positive division | 53 | 2,385 | 842 | 671 | 417 |

The compact form uses one destructuring/map initializer while still initializing
and clearing six distinct native integers. Every FFI declaration, the native
layout, helpers, loop/control, conversions and formatting remain application
source. The unchanged runtime and GMP are external. Physical rows, gzip, BPE and
native grammar tokens remain complementary measures; normalized logical and
canonical formatted LOC are still unqualified. No smallest-possible-program or
globally fastest implementation claim follows.

## Required work and controls

Across all eight sources, 96 bounded complete outputs and 96 exact traces match
an independent Python arbitrary-integer reference. Every advance state, both
actual candidate quotients, accepted digit and removal state is compared,
including negative accumulators between extraction tests. Full-size diagnostic
runs separately verify **33,209 advances, 22,454 extract(3) calls, 22,454 extract(4)
calls, 10,000 emissions and 9,999 removals**, with six initializations and clears.
Diagnostics and their GMP string-conversion helpers are never timed sources.

Owned loader captures identify the exact GMP library in complete applications;
static link metadata and OS evidence remain available. The first diagnostic's
unsigned-size error and the stricter metadata attempt's known temporary-directory
warning are preserved with their source drafts. They have no accepted timing or
source-size status. Correct final sources explicitly convert an emitted 0..9
unsigned value to a Janet number. No unbounded state is narrowed for logic.

Fresh-process timing includes source parsing, bytecode/FFI compilation, library
loading, all arithmetic/output, native clears and shutdown. Every subject holds
the common mutex, has identity established before exec, closes its group and is
reaped. No other benchmark, language compilation or native validation runs
concurrently. Read-only power/process snapshots and ordinary host activity are
recorded; no pristine-idle or continuous thermal/frequency claim is made. No power
setting is changed and CPU throttling is not disabled. Both compared applications
use general GMP-backed arithmetic, but the exact historical GMP binary/build for
Mech is not independently established here. The results remain exploratory and
do not change the public chart.

`verify.py` replays the output/state/work traces, library captures, complete raw
and summary observations, paired ratios, source/runtime identities and closed
ownership. `seal.json` hashes all retained study artifacts. The canonical catalog
remains unchanged; original contributors, consulted sources and license scope
are preserved in `source-manifest.json`.
