# Current Mech and upstream Rust: matched profile

The current Mech executable completes the full input in **0.6999 seconds,
1.277× the exact upstream Rust executable's 0.5482 seconds**. The remaining
elapsed-time gap is 0.1517 seconds. The fresh traces point to serial input
preparation and two long-running hashed-map workers, despite Mech retiring
fewer instructions and using less aggregate CPU. This is a diagnosis of the
current executable, not a measured optimization or a Rust-parity result.

## Complete-process measurements

Source: compiler/runtime `bf10d4a51c6af5e1f212548f136a51f97f60ff4a`.
Mech is `counting-prepared-refill`, in secured mode. Rust is the unchanged
upstream #7 executable, SHA-256
`f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763`.
The input has 254,166,745 bytes and 125 million selected bases. Each Mech run
performs seven full histograms and 874,999,961 updates, with seven workers and
five bounded lookup caches. No source program, input, work limit, capability,
worker count, power setting, priority or protected Rust submission changes.

| Measurement | Mech | Rust | Mech / Rust |
|---|---:|---:|---:|
| Complete-process elapsed, 6 runs each | 0.6999 s | 0.5482 s | 1.277× |
| Peak RSS in those processes, decimal MB | 162.1 | 140.4 | 1.154× |
| Instructions retired, separate 3-run diagnostics | 26.11 billion | 33.14 billion | 0.788× |
| Cycles, separate diagnostics | 7.19 billion | 7.91 billion | 0.909× |
| User CPU, separate diagnostics | 2.05 s | 2.34 s | 0.876× |
| System CPU, separate diagnostics | 0.04 s | 0.03 s | 1.333× |
| Involuntary context switches, separate diagnostics | 6,019 | 593 | 10.15× |

Values are within-cohort medians. Six alternating two-subject timing orders
were fixed in [plan.json](plan.json) and committed before execution. No
warmups or observations were excluded. [Timings](timings/results.json) and
[hardware counters](counters/results.json) are separate executions; rounded
`time -l` elapsed values never enter the primary medians. Aggregate CPU and
cycle totals do not measure the longest dependent path to process completion.
Context-switch totals do not by themselves establish their elapsed-time cost.

## Worker and main-thread evidence

Three full captures per language were prearmed before launching an exact-byte
binary copy with a unique short name. Every sampled PID is the owned subject's
birth-verified PID. The complete Mech `__TEXT,__text` section matches the timed
executable: 4,306,720 bytes, SHA-256
`643fa7158181e7475db480ebbc4c544cb7db9d272d633344b1b830b9f9ff8aa9`.
All outputs and native update counts pass. Raw captures, bounded symbol-tool
receipts and exact-address demangling are retained in
[early-mech-profile-v1](early-mech-profile-v1/results.json) and
[early-rust-profile-v1](early-rust-profile-v1/results.json).

| Exclusive Mech worker location | All 7 workers | Longest pair |
|---|---:|---:|
| Generated counting loops | 72.7% | 76.2% |
| Active finite-work accounting, including bounded lock spins | 16.3% | 9.6% |
| Storage helper paths | 5.7% | 9.3% |
| Generated helper bridge | 2.0% | 2.1% |
| Blocked accounting waits | 1.2% | 1.7% |
| Other active locations | 2.1% | 1.0% |

These percentages partition stack observations, **not elapsed time or CPU
time**. The denominators are 4,821 all-worker and 2,174 longest-pair
observations. The longest pair is selected transparently by the two largest
worker roots in each capture; both execute `packed_loop_284_funded`. The five
other tasks use bounded lookup caches. Source widths 12 and 18 exceed the
cache's source-derived 12-bit eligibility limit, identifying the ordinary
hashed pair by source and dispatch behavior; opaque polling thread handles
are not matched to sampled OS thread IDs.

Of Mech's 786 active-accounting observations, 642 are loop refills, 116 are
missing-key charges, 26 are frozen-map charges and two are other operations.
The 56 blocked accounting observations split into 20 refill and 36 frozen-map
observations. Reducing active refill/lock work remains useful; removing blocked
waits alone would not remove most observed worker work.

Rust's observed task-worker roots contain 72.1% active counting-task locations,
27.8% waiting and 0.1% other active locations. Its Tokio workers stay alive
waiting after their tasks complete, whereas Mech's workers retire. Therefore
those percentages do not show equivalent utilization or a comparable wait
penalty. Rust's active task leaves are dominated by `freq::<u8>` and the
future-poll bodies for the typed u16/u32/u64 hash tables. It has no counterpart
to Mech's finite-work accounting contract.

Mech main-thread leaves show 105 observations at the generated entry during
input capture, 37 in the final selected-line join's copy, 18 in the capture
page-pool copy, 31 in the character-map region, 28 in line access, 23 in `read`,
18 in chunk push and 15 in UTF-8 validation. Rust's main thread primarily shows
its input/decode body, line scanning, `read` and copies. Main-thread waits and
partial `_dyld_start` roots are retained in [analysis.json](analysis.json);
they are not attributed to startup CPU or assigned wall seconds.

The worker traces also contain 152 exclusive ASCII-flag observations: 78
under generic String length and 74 under closed-map admission. Source review
confirms calls through `pure_text::execute_length`/grapheme counting and
`State::begin_closed`/`is_ascii_without_crlf`, respectively. These are additional
whole-string inspections, distinct from the already cached captured-line
representation facts. Their contexts appear in the retained analysis.

## Independent thread CPU/lifetime polling

Three further executions per language use read-only libproc polling of owned,
birth-and-path-verified direct children. Every output passes. Requested polling
is 1 ms; actual observations are coarser and include supervisor overhead.
The [raw observations](thread-observations/results.json) and derived
[verification](verification.json) retain every thread and snapshot.

| Diagnostic median | Mech | Rust | Mech / Rust |
|---|---:|---:|---:|
| First observed counting worker after launch | 0.2257 s | 0.1604 s | 1.407× |
| Observed main-thread CPU endpoint | 0.2099 s | 0.1342 s | 1.564× |
| Largest worker CPU endpoint | 0.4700 s | 0.3935 s | 1.194× |
| Sum of seven worker CPU endpoints | 1.8944 s | 2.2452 s | 0.844× |
| First-to-last observed worker span | 0.4698 s | 0.3934 s | 1.194× |

CPU endpoints are lower bounds: the last poll can miss final work. First and
last sightings are coarse observations, not exact phase boundaries. These
diagnostic medians must not be added to reconstruct primary elapsed time.
They are consistent with approximately 65 ms later worker availability and
longer critical workers, explaining how fewer total instructions and CPU
seconds can coexist with longer wall time. Five cheaper Mech tasks finish
earlier while the ordinary hashed pair determines the end of execution.

## Optimization targets

1. Reuse certified immutable String length and ASCII/no-CRLF facts across
   worker preparation and closed-map admission, retaining first validation,
   source identity, resource charges and Unicode fallback. Both scan sites
   are directly observed. The existing same-entry ASCII fact cache does not
   automatically cover these distinct routes.
2. Reduce serial input capture, line selection/join and character-map work
   before the worker batch can start. The final contiguous join genuinely
   copies separate captured lines; there is no already joined String to
   merely move. Earlier larger-buffer trials were inconclusive and are not
   grounds for changing the default.
3. Compare the two ordinary hashed generated loops with Rust's active table
   paths, targeting probe/address dependencies and preparation on their
   critical path. Their 76.2% counting-loop share leaves room beyond accounting.
   No gain is assigned before an exact-source, correctness-checked experiment.
4. Reduce active refill/escrow work without changing finite work limits,
   prices, source failure order or capability validation. The latest prepared
   quote remains an inconclusive timing factor, not an established speedup.

## Qualification and retained analysis failure

[verify.py](verify.py) checks all 40 terminal process receipts: 12 primary
subjects, six profile subjects, six samplers, six counter runs, six thread
polling runs and four symbol tools. All are reaped, process groups closed,
with no cleanup errors or signals. Compiler source is clean and unchanged
before and after. Canonical benchmark timings and website data are untouched.

The initial analysis verifier incorrectly compared a compact thread-driver
source record with a full record containing an additional tree field. Its
[initial source](verify-initial.py) and
[failure record](verification-initial-failure.json) are retained. The corrected
verifier compares all recorded fields; no successful native run was repeated.
This correction affects evidence analysis only.
