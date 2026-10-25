# Candidate payload loads in owned hash probes

This experiment moves the initialized candidate count load beside the key
load, before full-key equality, in both helper-free ordinary hash functions.
It is correctness-qualified but **unpromoted**: all twenty matched full-input
pairs are slower than the retained pure-scalar parent.

Source `ff4dc1608ec2a8af1296a9d629aa600333c2eeed` uses IR93, ABI33 and
work policy69. The implementation is `4c89898df`; the final revision corrects
a test-selection assertion without changing production code. The working
performance baseline remains `93015bc629` and its original executable.

## Implementation and correctness

Only actual fingerprint candidates in admitted, initialized owned slots are
read. Full-key equality must succeed before the count supplies a source result.
A callee-local SSA value and separate valid bit retain zero/MAX value semantics;
pointer changes, writes, helpers and reloads invalidate the cache. An ordinary
reload remains available. The cache changes no runtime frame or storage ABI.

The same emitter covers narrow and wide keys. Original source, bytecode,
resource image, key equality, source arithmetic, finite prices, cold exits,
growth, all seven tables and all 874,999,961 physical updates remain.

All **414 native**, 30 line-storage, 36 credit and one catalog checks pass at
the final clean source. Nine focused loop checks, a subset of the native
suite, also pass. Differential tests compare renamed parameterized source,
original/decoded artifacts, complete maps, growth/refills, prepaid boundaries,
nonempty seeds, overflows, exact first errors and original work. The first
focused run retained eight passes and one selection-assertion failure: a test
incorrectly demanded the optimization on deliberately declined overflow graphs.
The correction retains positive selection on admitted graphs and every runtime
error/work assertion.

Actual assembly contains **38 early-load windows in each hashed function**.
Both key and count loads precede full-key comparison and its mismatch branch.
The other **twelve function bodies**, including the scalar scanner, are
byte-identical to the timed parent. The two changed functions contain 128 more
static instructions and 38 more static load sites across all width arms and
their slow probes; these are static totals, not dynamic counts. Counts remain
separate loads, with additional address arithmetic. No load pairing is claimed.

## Complete-process timings

Two predetermined Williams sessions contain ten complete processes per subject.
All subjects run serially under the original mutex. No full warmup or outlier is
excluded. Every output, original physical update and credited batch is checked.
Each ratio uses its own session's Rust median.

| Subject | Session 1 seconds / × Rust | Session 2 seconds / × Rust |
|---|---:|---:|
| Candidate separate early loads | 0.57103 s / 1.027× | 0.56643 s / 1.010× |
| Retained pure-scalar parent | **0.55027 s / 0.989×** | **0.54182 s / 0.966×** |
| Byte-table anchor | 0.60604 s / 1.090× | 0.60127 s / 1.072× |
| Ordinary control | 0.60148 s / 1.081× | 0.60650 s / 1.081× |
| Protected Rust #7 | 0.55619 s / 1.000× | 0.56107 s / 1.000× |

Paired candidate regressions against the parent are **+3.55%** (95% interval
+2.42% to +4.42%) and **+4.66%** (+2.59% to +6.08%). The candidate wins zero
of ten parent pairs in either session. Its paired intervals against Rust are
also positive. The unchanged parent's contemporary ratios remain separate
observations, rather than a pooled score or evidence for this candidate.

The one-million-base prefix retains its separate warmup and three measured
processes per subject. It is not extrapolated to the full input.

## Fresh profile, counters and sizes

Three pre-armed full-input captures per language use exact-byte copies with
owned matching PIDs. The Mech profile's entire machine-code text matches the
timed executable. Counting accounts for 87.0% of included Mech worker
observations, storage helpers 5.95%, active accounting 3.18% and the helper
bridge 1.63%. Observations include profiling overhead and are not wall/CPU
time allocations. All complete outputs and original table work pass.

Twenty separate counter processes, excluded from primary timings, report:

| Counter median | Candidate | Pure-scalar parent | Rust |
|---|---:|---:|---:|
| Instructions | 23,360,971,610 | 23,101,870,205 | 33,156,613,207 |
| Cycles | 5,893,417,712 | 5,694,093,259 | 7,919,881,910 |
| User CPU | 1.665 s / 0.713× Rust | 1.605 s / 0.687× | 2.335 s / 1.000× |
| System CPU | 0.030 s / 1.000× Rust | 0.030 s / 1.000× | 0.030 s / 1.000× |

The candidate retires approximately 259 million more instructions and 3.5%
more cycles than the parent. This is consistent with extra generated work;
the measurements do not isolate the effect of one address instruction.
Both files occupy 5,517,792 bytes. Primary peak RSS remains around 163 MB;
there is no useful memory-size improvement.

## Verification and follow-up

`verify-v2.py` checks all **159 retained owned-process receipts**, including
the failed focused test, 100 primary full processes, prefix executions,
exact-text profiles, counter processes and object inspection. All processes
are reaped with closed groups and no cleanup signals. The initial counter
driver stopped before launch on an incorrect cohort path; `counters-v2.py`
uses the existing measurements. The first verifier retained a stale inspection
status label; its corrected successor reuses all observations. No successful
native execution was repeated to repair analysis.

The separate-load arrangement remains available for controlled interactions.
The next contained experiment is a combined load of the adjacent key/count
words in the admitted narrow layout, retaining the full-width fallback. It
must be compared with the good pure-scalar parent as well as this unpromoted
trial, with actual emitted pairing inspected before primary timings.
