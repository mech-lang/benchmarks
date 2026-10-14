# Retained Elixir compiled-work evidence

This stage inspects the twenty separately retained Elixir main/support BEAM
pairs after their completed 156-case bounded output study. The
[native study](run-v1/report.json) completed all twenty observations using retained
BEAM files. Direct compiled-instruction review remains required. The study does
not recompile the subjects or collect benchmark timings.

Fifteen native diagnostic fixtures passed before the study. The
[fixture review](probe-fixtures-v2-review.json) binds the clean native exit and
ExUnit's `Result: 15 passed` output. The original summary parser expected the
older summary format; the separate review preserves that controller failure
and verifies the successful execution without repeating it. The executed
`probe-v2.exs` also fixes parentheses around a nested comprehension in a diagnostic
artifact call; the original probe and failed attempt remain retained.

`tools/qualification/elixir_work.py` provides four commands:

- `draft --output PATH` copies retained identities into an unverified metadata
  draft. It does not load BEAMs or hash the runtime closure.
- `prepare --plan PATH --output PATH` binds the completed bounded report and
  terminal, exact sources/BEAMs, runtime dependencies, diagnostic, and contract.
- `run --plan PATH --plan-sha256 SHA256` executes twenty sequential bounded
  diagnostic mains. Output must be fresh; failed runs retain evidence and are
  not automatically retried.
- `qualify --report PATH --report-sha256 SHA256 --decisions PATH
  --decisions-sha256 SHA256 --output PATH` records explicit review of every
  numbered compiled-work obligation against actual retained artifacts.

Use the retained Python with `-I -S -B`, without optimization. Every command
except metadata-only `draft` acquires the existing nonblocking common timing
mutex and verifies its inode. The native observer is the exact reviewed
`kotlin_bounded_v2.py` implementation at SHA-256
`c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc`.
It supplies the 30-second process deadline, five-second cleanup bound,
2 GiB observed process-group RSS limit, 8 MiB native-file limit, bounded stdout
pipe, atomic launch registration, inherited lock, and owned-child cleanup.
The v2 observer retries a transient RSS-monitor teardown race within the
original bounds. The earlier Kotlin bounded-run infrastructure failure
established no Elixir subject-source fault. This stage continues to require
the unchanged completed Elixir 156-case report and terminal.

The diagnostic records BEAM chunks, decoded instructions and function inventories,
framed traces, call counts, dynamic observations, and complete output. Witnesses
cover returned tree graphs and identity, the seven complete K-nucleotide maps,
pi state arithmetic, and the remaining workloads' operation structure. The
contract in `contracts.json` defines each required review. Correct output and
positive call totals do not independently establish compiled instruction
semantics, optimizer behavior, or normal-GC lifetime.

The controller binds the executed specification to the prepared main/helper
paths and bounded arguments, checks copied stdin and expected output against
their references, and retains the native probe's observed mutex descriptor and
inode. Each successful observation snapshots its complete artifact inventory.
Finalization reconciles the actual launch ID/PID/PGID/kind ledger with all twenty
saved process receipts and summaries, including exact start/active/final records,
resource policy, stream hashes, and process birth identity. Changed, deleted,
unreadable, or symlinked evidence prevents successful finalization.

Qualification repeats the receipt and artifact checks, binds the report's input
closure to its prepared plan, checks the complete terminal inventory, and rechecks
it after direct review. Every obligation must cite the corresponding profile's
generated `main-disassembly.txt` or `support-disassembly.txt` with a hash and
function/label location. Additional supporting citations are preserved. The
qualification result must be outside the closed native output directory.

The Python tests use invented receipts and small temporary artifacts. They check
failure handling and evidence binding without launching Elixir or hashing the
runtime. `probe-review-tests.exs` contains diagnostic regression fixtures that
require a later serialized Elixir execution; their presence is not an execution
result. Neither test suite substitutes for the actual twenty-form witness run
and direct instruction review.

A successful explicit review closes only required compiled work. Source-count
qualification, full measurements, and chart admission remain separate stages.
