# Reuse validated input-fragment facts

The candidate does not demonstrate a reliable complete-process runtime gain.
Both predeclared full-input sessions remain about 1.18–1.20× exact upstream
Rust. The separate prefix cohort is slower for the candidate. This branch is
retained as an unpromoted experiment; no startup improvement or Rust parity is
claimed.

## Implementation

Source revision `76d17b03f7536132369b7d221f18727a1a045d03`, branch
`codex/native-utf8-fragment-facts`, builds on aligned-probe parent
`8dfe57af5b116244ee8d10e1133bec95c02a4425`.

The generic text decoder combines ASCII validation and LF counting in a
bounded byte reduction. ASCII proves valid UTF-8; every other fragment still
uses the standard UTF-8 validator. Private fields tie the borrowed certificate
to the actual validated bytes. Resource delivery passes these facts to line
capture, removing repeated ASCII checks and an additional complete-prefix LF
count. The original line-capture admission and debit happen before facts are
used. Pending lines, CRLF trimming, Unicode fallback, input caps, deferred
consumer errors/panics and acquisition-error precedence remain.

The certificate is stack-only. No persistent owner, concrete map layout,
allocation admission, work price or cap changes. IR80, ABI28 and work-policy67
remain. The Mech program, bytecode, resource image and raw generated guest
object are byte-identical to the parent. All seven complete maps and
874,999,961 physical updates remain. This change affects shared input capture,
not the generated histogram kernels or a whole-workload Rust bridge.

Two core checks validate all single bytes, UTF-8 errors, dense LF counts,
alignments and vector tails. Nine runtime checks cover short reads, split
Unicode, interrupted I/O, caps, error/panic ordering and bounded scratch. The
24 line-storage checks include differential legacy/certified fragment paths
at every UTF-8 split, exact work/capacity observations and exact/one-short
memory admission. Broader native and catalog results are retained separately.

## Complete-process timings

The standard input has 254,166,745 bytes and 125 million selected bases.
Secured startup through complete shutdown is measured. Exact upstream Rust #7
is unchanged. Each session has six balanced serial orders of parent,
candidate and Rust, with session two reversing the order list. No full-input
warmup or outlier is excluded. Both sessions preserve every stdout and native
update report.

| Session | Parent Mech | Fragment-fact Mech | Exact Rust |
|---|---:|---:|---:|
| 1 | 0.6650 s · 1.199× | 0.6673 s · 1.203× | 0.5547 s · 1.000× |
| 2 | 0.6640 s · 1.191× | 0.6603 s · 1.184× | 0.5575 s · 1.000× |

Candidate/parent median changes are +0.34% and −0.56%. Paired median changes
are −0.22% and −1.91%, with 95% bootstrap intervals [−2.31%, +0.66%] and
[−3.82%, +0.52%]. Both include zero. Three of six pairs favor the candidate
in session one and four in session two. Sessions and Rust denominators are
not pooled. Raw observations remain in
[session one](../full-utf8-fragment-facts-v1/results.json) and
[session two](../full-utf8-fragment-facts-v2/results.json).

The separate prefix cohort has one excluded warmup and three measured
complete processes per subject: candidate **0.1178 s / 9.375× Rust**, parent
**0.0807 s / 6.422×**, Rust **0.0126 s / 1.000×**. Its roughly 46% candidate
regression is retained; this single startup-sensitive cohort does not establish
a causal phase cost, but it prevents a claim of improved startup.

## Diagnostics and verification

Fresh exact-code profiles, counters, owned-thread observations and disassembly
are separate from primary timings. Three captures per subject use the exact
full input. The whole executable text section of the symbol-bearing image
matches the timed executable; every sampled PID is the owned completed subject.

| Diagnostic median | Parent | Candidate | Rust |
|---|---:|---:|---:|
| First workers observed | 0.2258 s · 1.435× | 0.2148 s · 1.365× | 0.1574 s · 1.000× |
| Main-thread CPU endpoint | 0.2080 s · 1.540× | 0.1890 s · 1.400× | 0.1350 s · 1.000× |
| Largest worker CPU endpoint | 0.4224 s · 1.075× | 0.4457 s · 1.134× | 0.3930 s · 1.000× |

All seven workers first appear in the same polling snapshot in all nine
executions. The candidate's main CPU endpoint is about 19 ms lower and its
first worker observation about 11 ms earlier than the parent's. This supports
less input-side work, while primary elapsed-time intervals still include zero.
The largest observed worker CPU endpoint is about 23 ms higher. These endpoints
are lower bounds, can miss retirement work, and include polling effects. They
do not establish a worker regression, isolate exact phase CPU, or form an
additive elapsed-time decomposition. The unchanged guest object is insufficient
to assign the difference to scheduling, cache behavior or host helpers.

The two most-observed Mech workers spend 77.7% of stack observations in generated
counting, 9.8% in active budget work, 8.7% in storage helpers and 1.5% in budget
waits. Across all workers, the corresponding counting and active-budget shares
are 74.7% and 17.0%. Observation shares are not fractions of process elapsed time
or measurements of a proposed speedup. Main-thread leaves still include the
generated record-selection entry (97 observations), copying (56), character
mapping (30), captured-line access (29), offset construction (16) and the new
combined scan (16). These identify broader input representation/fusion and
worker critical-path accounting/storage as remaining investigation targets.

Separate counter medians are:

| Counter | Parent | Candidate | Rust |
|---|---:|---:|---:|
| Instructions retired | 25.526 billion | 25.066 billion | 33.148 billion |
| Cycles | 6.994 billion | 7.076 billion | 7.884 billion |
| Aggregate user CPU | 1.99 s · 0.854× | 2.02 s · 0.867× | 2.33 s · 1.000× |
| Aggregate system CPU | 0.04 s · 1.333× | 0.04 s · 1.333× | 0.03 s · 1.000× |
| Involuntary context switches | 6,525 | 6,137 | 611 |

About 460 million fewer aggregate instructions do not imply a shorter critical
path. Candidate file size is 5,468,144 bytes versus 5,468,112 for the parent;
executable code decreases 1,456 bytes to 4,300,748. Full-session median peak RSS
is about 0.36 MB and 1.06 MB higher. No memory or binary-size gain is claimed.

The retained [121-instruction combined scan](code-audit/byte-facts.s) has 48
vector-register instructions, including four-lane dot products and wide loads.
LLVM generates this from ordinary Rust reductions; the Mech histogram object
remains unchanged. The first analysis expected vector lane suffixes on register
names, while Apple otool prints them on mnemonics. The
[corrected analysis](code-audit/analysis-v2.json) reads the identical retained
assembly and preserves the original report. No native execution was repeated.

The broader native suite passes 387 cases, with three existing manual cases
ignored; the catalog check also passes. Alongside the 35 component cases, this
is **423 passed test executions**. The
[final verifier](verification-v2.json) checks all 91 terminal process receipts,
complete outputs, updates, source pins and code identity. Every owned process
exits successfully, is reaped, and has its process group closed without cleanup
signals or errors. Canonical benchmark data is unchanged.

The candidate remains an interaction factor on its own branch. The qualified
aligned-probe parent remains the baseline. More precise worker-completion CPU
observations and broader record-selection/join/mapping fusion are follow-up
opportunities; no speedup is inferred before they are implemented and measured.

The earlier aligned-probe captures observed all seven workers for each subject
in the same polling snapshot in every execution. That resolves no staggered
launch; it does not measure thread creation as instantaneous. The preceding
82 ms first-sighting gap is an observation of the path before workers appear,
with polling overhead and coarse resolution.

[Plan](plan.json), [sequential driver](run.py), [timing driver](measure.py),
[diagnostic driver](diagnostics.py) and [final verifier](verify-v2.py) retain source,
input, executable, policy and output pins. Native jobs run sequentially under
the existing shared lock, inode 83858837. Every owned process must be reaped,
its group closed, and its source unchanged. Existing receipt directories are
never overwritten to repair analysis.
