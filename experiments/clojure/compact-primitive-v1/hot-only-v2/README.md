# Clean compact hot-store qualification

The original four-source packet and its failed build are unchanged. Its
`compact-all-aset` momentum substitution emitted a new application reflection
warning, so the sealed builder rejected it. The parent selected only the clean
`compact-hot-aset` source; no warning was waived and no coercion variant was added.
This separate three-source packet records that decision and pins the old failed
attempt. The candidate's source bytes remain those committed before native work.

The clean qualification passed on 2026-10-20:

- Three fresh isolated builds: original compact, qualified scalar primitive
  control, and compact hot-store candidate. Every class, command and diagnostic
  stream is retained. Only the exact previously accepted generic support warning
  appeared; there were no application warnings.
- Three-way raw-bit comparison of all 35 state slots and energy after fresh
  initialization, momentum and every step at N = 0, 1, 2, 3, 10, 100: 348 actual
  calls to the compiled applications' `advance` functions.
- Thirty complete-process bounded outputs, three sources at N = 0, 1, 2, 3, 7,
  10, 31, 1000, 1001, 10000. All matched the independent reference bytes exactly.
  Six cases use the shared bounded corpus; four odd cases use the pinned shared
  reference implementation. The established 1e-8 comparison also passes.
- Runtime/class/source/prerequisite pins remained unchanged. Each process group
  ended, and the common timing lock was released after qualification.

[qualification-summary.json](qualification-summary.json) binds the exact build,
state, bounded and execution-plan receipts. It records bytecode evidence and its
limits. No quantitative pilot or full timing has been run for the new candidate;
bounded elapsed records are qualification evidence and are not chart samples.
The 109 retained / 49 physical count remains a proposal pending independent
approval. The candidate's separate logical-unit count remains unavailable until
its exact source receives native-reader qualification.

The actual compiled hot-store `advance` method has primitive
`RT.aset(double[], int, double)` stores. Its five static store sites reflect the
two updates duplicated by chunked/unchunked `doseq` expansion and the position
store; this is not five dynamic stores per interaction. Three `Double.valueOf`,
four `Tuple.create`, and object-axis arithmetic instruction sites remain. The
scalar primitive control has seven static typed-store sites and no such boxing
or tuple sites. Static bytecode does not establish heap allocations after
HotSpot optimization, and it does not establish the new candidate's speed.

The separate sealed runner supports bounded qualification and a one-million-step
diagnostic screen only. A future parent-coordinated pilot compares the primitive
control with the clean compact candidate, omitting the slow original parent.
Pilot/full execution remains subject to a quiet window; this qualification did
not start either. Full timing requires a later explicit selection protocol.
