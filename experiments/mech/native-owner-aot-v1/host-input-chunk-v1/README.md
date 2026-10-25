# Host input-buffer comparison and early full profiles

This experiment varies only the copied generated host's requested input chunk
size: the existing **64 KiB** default, **256 KiB** and **1 MiB**. The compiler
and runtime remain at clean revision
`1b7c79b3e1d6713f0648cbe59794fab8b091d245`. No production source or website
timing entry changes. All variants remain available.

**Keep the 64 KiB default.** Larger chunks do not establish a consistent large
runtime improvement. The 256 KiB variant improves the repeated full-input
session but regresses the first; 1 MiB reduces peak RSS by roughly 4–6 MB while
regressing the short-input cohort. These small exploratory cohorts do not prove
an optimal buffer size. Rust parity remains incomplete.

## Controlled builds and complete-process timings

The [plan](plan.json) and [driver](pilot.py) were committed before execution at
`c9ee00e8390e21f2289958bf87b8c1260af88880`. The two copied projects change one
chunk-size literal and update the exact generated-main/build manifest pins.
Source, bytecode, descriptor JSON/compressed image, resource image, Object
identity, native Object, Cargo manifest/lock and runtime dependencies are
unchanged. The native Object hash remains
`f25ada28ff389713076fcb342b3b13f807741bfda91ca2274e6eb4d8ebc36335`.

Capabilities, input limits, finite memory/work/library limits, source visits,
worker count/order and actual map operations remain. Input storage already
uses the same admitted private page-pooling policy in every build. No power,
affinity or QoS change is used. Final host flags remain release opt-level3,
FatLTO and one codegen unit, with the same checked Cranelift Object linked in.

Each session uses four balanced sequential four-subject orders, four
observations per executable. All **32 full-input and 16 prefix observations**
are included: no excluded warmups or outliers. Full sessions and prefix results
remain separate. Full input contains 125 million selected bases, with fresh
secured startup through process exit.

| Configuration | Full session 1 seconds | × Rust | Full session 2 seconds | × Rust |
|---|---:|---:|---:|---:|
| Exact upstream Rust #7 | 0.5614 | 1.000× | 0.5521 | 1.000× |
| Existing 64 KiB | 0.6786 | 1.209× | 0.6916 | 1.253× |
| 256 KiB | 0.6843 | 1.219× | 0.6794 | 1.231× |
| 1 MiB | 0.6888 | 1.227× | 0.6802 | 1.232× |

Matched-order median log-ratio changes versus 64 KiB are:

| Variant | Session 1 change and 95% interval | Faster pairs | Session 2 change and 95% interval | Faster pairs |
|---|---:|---:|---:|---:|
| 256 KiB | +0.84% [−3.20%, +41.85%] | 1/4 | −2.04% [−4.04%, −0.30%] | 4/4 |
| 1 MiB | +1.47% [−3.03%, +46.47%] | 2/4 | −2.45% [−2.64%, +11.87%] | 3/4 |

Descriptive intervals resample four whole matched orders 20,000 times with
fixed seeds. Paired estimates differ from ratios of marginal medians. Four
pairs are a small sample; the direction reversal limits conclusions. The new
variants' first full executions take **0.9503 s and 0.9812 s**, versus their
subsequent lower observations. Their user-plus-kernel CPU is roughly 2.15 and
2.12 seconds. The extra elapsed time's cause is not identified, and neither
observation is removed or attributed to loader/security behavior without
evidence.

The separate one-million-base prefix gives:

| Configuration | Seconds | × Rust |
|---|---:|---:|
| Rust | 0.02068 | 1.000× |
| 64 KiB | 0.09104 | 4.402× |
| 256 KiB | 0.09424 | 4.557× |
| 1 MiB | 0.10628 | 5.139× |

The 1 MiB prefix is slower in all four matched pairs: paired +17.57%
[+9.80%, +29.18%]. The 256 KiB paired change is +0.18%
[−3.85%, +27.30%], two pairs faster. Prefix startup and work differ from full
input; these results are not pooled.

[Full session 1](full-v1/results.json), [session 2](full-v2/results.json) and
[prefix](prefix-v1/results.json) retain all samples, deviations, source/input/
policy/binary pins and native reports. Every full Mech execution verifies
complete output, seven complete maps, five admitted caches, seven peak workers
and **874,999,961 physical updates**. Prefix executions verify complete output
and **6,999,961 updates**.

## Memory and executable size

RSS is the median of each original timing process's macOS `wait4` peak.
MB means 1,000,000 bytes; buffer labels use binary KiB/MiB units.

| Configuration | Full session 1 RSS MB | Full session 2 RSS MB | Prefix RSS MB |
|---|---:|---:|---:|
| Rust | 140.41 | 140.73 | 16.40 |
| 64 KiB | 161.20 | 161.96 | 27.86 |
| 256 KiB | 162.37 | 161.42 | 27.89 |
| 1 MiB | 157.03 | 155.92 | 27.71 |

All three Mech files occupy **5,468,144 bytes**, with **4,304,368 machine-code
bytes**; host code hashes differ. Larger buffers do not remove shipped code.
The lower 1 MiB RSS is a storage result, not proof that startup or worker
execution improves. Copied main/build sources and repaired manifest pins are
retained alongside both supervised builds.

## Early-start full-input profiling

[The profile driver](early-profile.py), committed before capture at
`a34986753069a6a215c50689748254c937381a0f`, pre-arms the macOS sampler before
launch. This captures input preparation that normal post-launch inventory and
attachment can miss. There are three full-input captures each for current
64 KiB Mech and exact unchanged upstream Rust, in sequential order
Mech/Rust/Rust/Mech/Mech/Rust. These are diagnostics, not timing observations.

Each target is an owned direct child with an exact-byte executable copy under
a random unique name. Sampled PIDs must match; every process completes and
verifies output. Mech also verifies the complete map/update counters. The Mech
profile image's entire machine-code section matches the timed 64 KiB binary;
Rust is the exact timed binary. No debugger, stop, environment injection or
security-setting change is used. All six captures contain stack observations.

[Analysis](early-analysis.py) resolves names from each exact executable and
retains complete ancestor contexts. Repeated main-thread roots are merged by
thread ID. Exclusive main-thread observations include:

| Observed location | Mech observations | Rust observations |
|---|---:|---:|
| Main thread total | 1,564 | 1,525 |
| Principal worker-wait leaf | 1,050 | 1,268 |
| Partial loader/start root | 143 | 63 |
| Generated capture/prefix program entry | 92 | — |
| Source input/encoding body in Rust `calc` | — | 74 |
| Memory copies | 48 | 33 |
| Compiled constant string map | 30 | — |
| Captured line retrieval | 29 | — |
| Input `read` | 20 | 20 |
| Delimiter offset construction | 18 | — |
| Captured chunk push | 17 | — |
| ASCII checking | 16 | — |
| UTF-8 validation | 15 | — |
| Rust delimiter search | — | 35 |

These are stack-location counts across different executions, **not wall-time
or CPU-time shares**. Waits, partial unwinds and profiler overhead remain.
In particular, loader/start-root counts cannot be converted into an executable
loading cost or used to explain the slower timing samples.

The largest Mech copy context is final selected-line joining: 33 observations.
Another 13 are input page-pool copying. Source inspection confirms that final
joining constructs a contiguous string from separate captured lines; there is
no already joined owned buffer available for a simple move. Window borrowing
already caches ASCII qualification and complete-chunk payload geometry. Its
remaining line walk constructs the pointer/length table consumed by generated
code. Eliminating that walk requires a different private row representation,
not deletion of an unnecessary validation loop.

[Mech main contexts](early-mech-profile-v1/main-analysis.json),
[Rust main contexts](early-rust-profile-v1/main-analysis.json) and
[summary](early-main-summary.json) retain exact symbols, raw sample hashes,
thread denominators and contexts. No profile observation is pooled into
timings. The existing generated-loop/work-accounting worker profile remains
available in the [decoder-validation trial](../packed-domain-validation-v1/README.md).

## Verification and retained state

[Verification](verification.json) recomputes the predeclared plan, both copied
host builds, all 48 complete-process observations, balanced orders, raw output,
physical updates, paired bootstrap intervals, RSS, exact profile images,
main-thread observation totals and **62 terminal, reaped, closed-group process
receipts** for builds, timing subjects, profilers and profile subjects.
Read-only symbol listings and their hashes are retained separately. Compiler
source stays clean and unchanged, all native work is serial under the retained
shared mutex, and canonical dataset bytes are unchanged.

Run `python3 host-input-chunk-v1/verify.py` from this study directory in the
qualified checkout. No new compiler default or fastest-program claim is made.
The retained [Rust strategy comparison](../strategy-comparison-v3/results.json)
already isolates representation width: its unchanged Rust reference is
0.5513 s / 1.000×, while wide keys/counts take 0.5609 s / 1.017×. A separate
[table-algorithm diagnostic](../table-strategy-v1/results.json) reproduces
Mech's 16-byte payload, folded hash, eight-byte NEON controls and linear probing
in Rust; its linear variant takes 0.5473 s / 0.988× its own 0.5539 s Rust
reference. Those studies use older Mech controls and do not replace current
Mech observations. The Rust-only counterfactuals do not establish a Mech layout
speedup, and do not support predicting a large remaining gain from payload
width alone. Reuse those retained controls before implementing a new table ABI.
The current follow-up instead prepares exact refill costs before acquiring
shared worker accounting, keeping every original debit and limited-budget path.
