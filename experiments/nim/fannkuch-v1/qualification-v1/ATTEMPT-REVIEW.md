# Preserved qualification attempts and observer correction

Neither failed attempt changes candidate eligibility, source counts, retained
source bytes or historical measurements. Both native processes exited and the
common mutex was released. No bounded subject or detailed work check ran in
either failed attempt. The original controller, observer, protocol and plans
are preserved unchanged.

`attempt-v1/report.json` records the sandboxed attempt. The first unchanged
compact control compiled and linked with exit status zero, but its linker
emitted `confstr()` / `DARWIN_USER_TEMP_DIR` lookup warning and used `/tmp`.
The no-warning gate rejected the attempt. Root authorized a fresh run on the
normal unrestricted execution surface, with exactly the same controller,
environment, sources and flags. No warning was waived or filtered.

`attempt-v2/report.json` records that unrestricted attempt. The normal compact
control compiled cleanly, and its complete generated C and disassembly were
captured. The first witness build then failed a real Nim effect check:
unconditional trace I/O inside generic `reverse` propagated side effects into
the unrelated pure `strutils.rsplit` implementation for strings. This is an
observer defect, not a failed benchmark source or evidence of incorrect results.
All raw diagnostics, processes and partial artifacts remain preserved.

The additive `instrument_sources_v2.py` keeps the real generic swap and loop
unchanged. The post-swap observer is instantiated only for `int` and `uint8`,
and emits only when a thread-local trace file is active and the actual array
length is twelve. String and character reversal instantiations contain no
observer I/O. A separate `effect_probe.nim` compiles and checks both from
explicitly pure functions against the private witness library. That diagnostic
is outside every application source and every timing boundary. No effect cast,
compiler warning suppression or algorithm replacement is used.

`run_qualification_v2.py` binds this additive observer, the pure-function probe
and the new protocol; both prior failures and their raw process streams are
bound too. Every other production source, compiler setting and work replay
remains as before. `protocol-v2.json` is a native-witness-only protocol; normal
applications still use the untouched restored standard library. Preparation
and native execution require a fresh plan/output and root's clearance.
