# Rolling Elixir: retained source-count replay

The exact retained Elixir 1.20.4 frontend read both unchanged rolling candidates,
the original parent, generic support and runner in one native source-only
process. It also replayed the fourteen retained grammar fixtures. No application
module was evaluated, compiled, loaded or called. The reader exited successfully
with empty stdout/stderr and released the common mutex. No timing was performed.

The unchanged retained counter produces **81 application units over 67 physical
lines for the serial source**. The parallel source remains **unqualified with
a null retained count**, over 71 physical lines: its task-stream pipeline exposes
three ownership diagnostics. Neither candidate is independently approved.

| Source | Retained application units | Application physical lines | Native formatted physical lines |
| --- | ---: | ---: | ---: |
| Exact parent control | 47 | 39 | 50 |
| Serial rolling candidate | 81, pending owner review | 67 | 74, pending formatter review |
| Parallel rolling candidate | null: owner diagnostics | 71 | 81, pending formatter review |
| Unchanged general helper, excluded | 61 | 53 | 68 |
| Unchanged general runner, excluded | 1 | 1 | 1 |

These observed or candidate values do not populate approved application LOC,
formatted LOC, logical LOC or chart eligibility. The native reader and original
counter retain their unqualified flags. The final review approval remains null.

## Exact frontend, counter and control

The retained reader is
`experiments/elixir/source-counts-v1/read_sources.exs`, SHA256
`b2f2102e16ed2213eaf012704952c5bda9da116fb7af736363664eda321e0b3b`.
Its `parse`, semantic AST, tagged-term, native formatting and inspection function
bytes are reused unchanged. The original executable entrypoint hardcodes the
historical mutex inode. A separate, source-bound host replaces only that final
entrypoint invocation and validates the current inherited descriptor against
the frozen plan. The historical assertion remains unchanged in the unused
original main. The staged file is checked against the exact original module
prefix plus the separate host; no frozen file or constant is patched.

The Python counter is the unchanged
`tools/qualification/elixir_source_units.py`, SHA256
`d1070e8f38fdebdfe2523c918bfb4367958667f34bf3c77efb6d6725544dc07f`.
Its public `replay`/`count_source` functions receive the new captures as ordinary
arguments. All fourteen historical fixture expectations pass, including the
deliberately unresolved interpolation and two expected syntax rejections.

For the parent main, helper and runner, the complete original and formatted
counter records match the historical replay exactly: physical/retained counts,
every ownership event, expansion, continuation and diagnostic. All fifteen
native source, tagged AST, ETF and formatted artifacts also match the retained
controls byte for byte. This is an exact control of the reused frontend and
counter, rather than merely reproducing the old total.

Raw plan, inherited-lock/process receipt, 91 native artifacts, unchanged runtime
file manifest, tagged JSON/ETF and native formatter copies are retained beneath
`run-v1/`. The source capture invokes only the auditing reader; the application
files remain parser inputs. It uses the same restored 723-file Elixir release
and 4,243-file OTP distribution already verified by native qualification.

## Application boundary

The original Elixir qualification counted complete bundles. The later published
[application policy](../../../../docs/methodology.md#timing-and-source-size)
excludes reusable hosts and general I/O/formatting libraries. The parent is
therefore **47/39 application units/physical lines**, while its historical whole
bundle remains **109/93**. The exact helper and runner account for **62/54** of
that difference. Their source hashes and existing exclusion roles are unchanged.

This packet applies that same boundary to both rolling candidates. The serial
whole bundle is 143 retained units over 121 physical lines, with 81/67 proposed
for the application. The parallel whole bundle has 125 physical lines, while its
retained normalized total remains null. All domain parsing, base encoding,
rolling recurrence, complete map construction, query lookup, ordering, decoding
and output construction stay in the counted main. No benchmark helper is moved
to excluded support. The earlier frozen native/pilot packets are not edited;
their provisional support-scope prose is clarified by this later accounting
receipt. Those packets still assign no candidate source count.

## Parallel diagnostics

The unchanged counter rejects the original task-stream pipeline at line 74's
`output =` binding and line 76's callback close for overlapping native owner
spans. It also reports a non-scalar expression continuation beginning after
that callback. The native formatted source reports the same three diagnostic
classes at lines 88/90. The counter's arithmetic candidate of 83 units, and the
per-line arithmetic ledger, are **diagnostics only**; neither is a certified or
approved fallback count. This packet does not change the counter, suppress the
diagnostics, manually patch a total or rewrite the frozen source. A separate
reviewed retained-policy extension or counter qualification would be needed.

The serial source has no original or formatted owner diagnostics. Its ledger
preserves array/comprehension expressions, pure expression functions and ordinary
library calls. It never expands their implementation into imagined scalar work.
Independent written statements and explicit block owners remain visible.

## Retained policy versus uniform logical units

This replays `canonical-source-units-20261012-approved-rule-v2` with
`elixir-native-position-owners-v1`. That retained policy charges written closers
and preserves some wrapped expression/data rows. It differs from the separate
uniform `logical-source-owners` proposal, which excludes structural closers and
literal continuation rows. Native AST capture and retained-policy qualification
do not by themselves certify that uniform logical axis. Logical counts remain
null, and no new whole-language grammar qualification is claimed.

`replay.py --check` reproduces the offline counter receipt, exact controls and
per-source ledgers without an Elixir process. `source-count-receipt-v1.json`
binds the final unapproved observations and their evidence. No catalog, source,
timing, existing qualification or pilot plan is changed.
