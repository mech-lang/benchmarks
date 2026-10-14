# Bounded candidate startup and rejection protocol

This review traces the unchanged [candidate](candidate.pl) and retained
[QLF preparation helper](../../../archive/languages/prolog/20261013/revisions/prepare-success-halt-v1/tools/prepare_qlf.pl)
against SWI-Prolog 10.0.2 source. It establishes the intended startup and message
protocol for a future bounded run; it does not assert that the candidate has
been compiled or executed.

The official source is retained at:

```text
/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg/prolog-comparison/20261013/.build/swi-runtime-directory-v1/official-source/swipl-10.0.2
```

All SWI source paths and line numbers below are relative to that directory.
The source archive SHA retained in
[runtime-config.json](../../../archive/languages/prolog/20261013/runtime-qualified/success-halt-v1/runtime-config.json)
is `e42cc098f7b8a6051c4f79a99b55162d467098aba60f69649bdc7583f0734b57`.
This review reads the retained files; full closure verification belongs to the
serialized preparation and execution step.

## Entry and compilation

Use the retained `swipl` with `-q -O -f none --stack-limit=8g`.
Preparation loads the helper with `-l`, selects `-g clbg_prepare:main`, and
passes exactly `Mode Target Receipt Wam AuthoredRoot` after `--`.
Production selects `-s candidate.qlf -g clbg_revcomp_linear:run`.
Diagnostic cases select the same QLF and the module-qualified
`clbg_revcomp_linear:diagnostic(Capacity)` goal.

| Source | Relevant behavior |
| --- | --- |
| `src/pl-init.c:1124–1138` | `-O` selects optimization; `-l`/`-s` register script files; `-g` registers a goal. |
| `boot/toplevel.pl:404–409` | Arguments after `--` become application `argv`, with script mode `none`. |
| `boot/init.pl:763–777,806–812` | `initialization(Goal, main)` registers a delayed main goal; ordinary loading excludes this goal from load-time initialization. |
| `boot/qlf.pl:77–89` | `qcompile/1` resolves source and calls `load_files` with a QLF output option. |
| `boot/toplevel.pl:587–607` | Script loading precedes explicit `-g` goals, which precede program/main initializers. |
| `boot/toplevel.pl:715–719` | Loading with `-l` additionally suppresses automatic main initialization. |
| Helper `prepare_qlf.pl:53–73` | Compile/inspect finishes, writes runtime/source/foreign-library metadata and WAM, then halts zero. Caught exceptions halt one. |
| Candidate `candidate.pl:3–25` | Both selected wrappers execute the chosen body once and halt; the registered main initializer cannot execute afterward. |

Do not substitute `-g clbg_revcomp_linear:main`: this body returns, allowing
the later registered main initializer to run under `-s`. The explicit `run`
and `diagnostic` wrappers prevent this second entry. A helper goal that merely
fails is also stopped with exit one by `boot/toplevel.pl:759–771`; it cannot
silently advance into the candidate initializer.

## Exact stderr envelopes

Successful candidate fixtures require complete expected stdout, empty stderr
and native exit zero. The 7 invalid fixtures, each repeated in 10 entry modes,
require native exit one and this exact ASCII line, substituting the expected
decimal byte value:

```text
ERROR: [Thread main] Domain error: `iupac_nucleotide' expected, found `<Code>'
```

There is one final LF. The delimiters before `iupac_nucleotide` and the code
are backticks; those after them are apostrophes. The codes for the retained
invalid cases are 32, 9, 0, 255, 62, 59 and 63. The final case rejects `?`
before `!`, following complete-record reversal. The generator leaves partial
failure output unspecified, but the bounded runner can strengthen these seven
cases to require exactly `b'>r\n'`: each has that one header and fewer than 60
sequence bytes. Candidate lines 110–117 write the header before complementing;
no full 60-byte output line is reached before the invalid symbol throws.

Candidate lines 170–171 throw
`error(domain_error(iupac_nucleotide, Code), complement/2)`; lines 22–25 print
the caught error directly and halt one. There is therefore no startup
`-g ...:` wrapper around the expected error. In `boot/messages.pl`, lines
143–147 select ISO error translation; lines 198–200 and 414–418 format the
domain and actual value. The bare `complement/2` context produces no caller
prefix: it matches the empty fallback at lines 556–585, not the
`context(Caller, ...)` clause. Lines 610–632 add no suffix for this context.

`boot/messages.pl:82` defaults message context to `[thread]`. Lines 2278–2286
add `[Thread main]` before startup reaches the interactive top level;
`boot/toplevel.pl:1187–1194` sets the top-level flag around interactive queries.
The stream/tag/prefix rules at `boot/messages.pl:2217–2236` select `user_error`
and `ERROR: `, and lines 2316–2327 append the final newline. With redirected
streams, `library/ansi_term.pl:77–83,377–380` does not add terminal coloring.
Use an isolated C-locale environment and the retained startup files so message
hooks or translations cannot change this protocol.

The header is flushed before error reporting by
`boot/messages.pl:2172–2174`. Normal `halt(1)` also flushes standard streams:
`src/pl-fli.c:5058–5080` calls `haltProlog`, whose `:5022–5030` invokes
`PL_cleanup`; `src/pl-init.c:1843–1847` calls `dieIO`,
`src/os/pl-file.c:1406–1411` calls `closeFiles(true)`, and `:1462–1469` flushes
the standard output/error streams. A missing header or an I/O error remains a
failed fixture; this source trace does not excuse incomplete output.

Compilation and inspection have a different, expected exact stderr line:

```text
Warning: [Thread main] Local definition of clbg_prepare:main/0 overrides weak import from clbg_revcomp_linear
```

This also ends with one LF. Both modules define/export `main/0`. Loading imports
exports by default (`boot/init.pl:2894–2902`), with weak strength for the default
`all` import (`boot/init.pl:3548–3553`). The local definition survives and the
runtime emits `ignored_weak_import` (`src/pl-modul.c:1705–1725`); its warning
text is defined by `boot/messages.pl:842–845`. This is not a subject failure.

The prior actual
[compile stderr](../../../archive/languages/prolog/20261013/qualification/prepare-explicit-goal-rest-v1/builds/prolog-revcomp-compact/compact-compile-command.stderr)
and
[inspect stderr](../../../archive/languages/prolog/20261013/qualification/prepare-explicit-goal-rest-v1/builds/prolog-revcomp-compact/inspect-command.stderr)
record that same line with the earlier module `clbg_revcomp`. These retained
receipts corroborate the thread prefix and weak-import path. The new candidate's
actual receipts must match its own exact line; arbitrary additional warnings,
errors, prefixes or suffixes remain failures. Exit one alone is never an
invalid-IUPAC witness.

## Runtime and artifact binding

The retained
[compile metadata](../../../archive/languages/prolog/20261013/qualification/prepare-explicit-goal-rest-v1/builds/prolog-revcomp-compact/compact-compile.json)
records version components `[10,0,2]`, version text `swi(10,0,2,[])`, architecture
`arm64-darwin`, stack limit 8589934592, `bounded=false`, `gc=true` and the exact
retained `SWI_HOME_DIR`. The architecture string in these VM receipts differs
from the physical binary label `arm64`; compare each field with its own schema.
The new compile and inspect receipts must match all these values, exact target
and output paths, the authored source, and pinned loaded source/foreign-library
paths. `-f none` disables a user initialization file, but retained system startup
files such as `swipl.rc` can still load and must remain in the runtime closure.

`src/os/pl-prologflag.c:2027` binds the optimization flag to the command-line
selection. The helper does not record that flag separately, so the exact
retained executable/VM closure, observed command and emitted WAM provide the
compiler binding. QLF creation writes the QLF version and VM signature
(`src/pl-qlf.c:3658–3660`); inspection checks the version and exact VM signature
(`src/pl-qlf.c:3808–3823,3852–3853`). Preserve and pin the actual newly generated
QLF between compile, inspect and every fixture process. The relevant candidate
WAM predicates include `read_blocks/2` and `emit_codes/5`.

The [fixture generator](fixtures.py) defines 54 cases and 9 diagnostic capacities.
Production plus those capacities gives 540 candidate processes: 470 successful
output cases and 70 expected rejections. One compiler and one inspection process
bring the complete planned native ledger to 542. This bounded protocol grants
no full-work timing, source-work, source-count or chart admission by itself.
