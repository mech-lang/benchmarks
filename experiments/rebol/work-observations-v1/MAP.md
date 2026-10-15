# Bounded complete-map and final-storage observation

This is an unexecuted source proposal. [`knucleotide.reb`](knucleotide.reb)
loads the unchanged retained knucleotide main with ordinary `do`, using the
existing `knucleotide/arbitrary-widths` corpus input. That input has 10,299
bytes; its exact benchmark stdout has 243 bytes. The original main performs
all seven complete histogram scans and writes its original output before the
diagnostic observes its global `tables`, `widths` and `sequence` values.

The wrapper calls the existing generic `stats/dump-series -1` exactly once,
before creating any diagnostic pair collection or sidecar. It then iterates
each actual map in its existing order and writes every integer key and positive
count to the absolute fresh path in `MECH_REBOL_MAP_OBSERVATION`. The original
main, loader, facades, extension C source and selected runtime/image are not
edited. This is a bounded post-main diagnostic, not an ordinary timing run or
proof of a rebuilt runtime's equivalence.

[`map_contract.py`](map_contract.py) accepts complete byte strings through
`validate(stdin, stdout, stderr, exit_status, sidecar, expected_stdout)`.
It independently selects the THREE record and counts sliced overlapping words
at widths 1, 2, 3, 4, 6, 12 and 18. Every entry, count and window total must
match. The full integer-pair sequence for each actual map must match exactly
one distinct complete value-series record in the dump, with the corresponding
tail and allocation dimensions. Ambiguous equal series, missing maps, missing
or extra entries, malformed captures and inconsistent capacities reject.

The result reports **final backing-series storage**: its displayed address token, value width,
tail, rest, bias and allocated bytes. It does not report hash-bucket capacity,
individual reallocations or a measured growth trajectory. The retained
`t-map.c` implementation separately establishes that maps begin with a block
backing store, append key/value pairs and grow their storage; the hash series
is a different linked object. One final snapshot cannot turn that source
argument into an observed before/after growth trace.
The dump's fixed eight hexadecimal digits are only the low 32 bits of an address
on this 64-bit runtime. They are not full pointer identities. Repeated displayed
tokens reject rather than being treated as distinct, and the complete integer
sequence remains the independent map-matching condition.

## Complete stream policy

The additive [three-diagnostic controller](../../../tools/qualification/rebol_work_observations.py)
supplies this map slot's input, exact sidecar path and retained observer policy;
its [stage README](README.md) describes prerequisites and closure checks. The
controller remains an unexecuted source draft, with no prepared plan or capture.
The unchanged frozen observer captures stderr in an exclusive regular file.
The native stage permits at most 16 MiB of stderr; stdout and the sidecar each
have a 1 MiB acceptance bound. These bounds have not been demonstrated adequate
by a native run. Exceeding them fails and preserves available artifacts, with
no truncation, automatic retry or enlarged-limit rerun.

There are no extra delimiter writes or descriptor changes. The consumer parses
the **whole** stderr stream as consecutive native series headers and payloads.
Every value-series header has exactly one complete normalized value line;
every byte-series header has the exact number of native hex/ASCII rows,
including padding, address progression and the source's 120-row byte-display
cap. No outside lines or ignored prefix/suffix are accepted. Unrelated molded
values are opaque within their declared single-line payload; they cannot
identify a map. Only a complete canonical integer sequence with the exact
declared tail can do that. This structural grammar is not an arbitrary Rebol
parser or a cryptographic origin proof; its attribution also depends on the
pinned single-call wrapper and independently owned normal process capture.
The conservative value-line bound is `tail * (1 + 4 * (1024 + 3))` bytes:
one separator, at most four UTF-8 bytes per character, the formatter's 1024
character limit and its possible three-dot suffix. It does not omit that suffix.

The frozen observer's `Unexpected stderr; raw bytes retained` failure remains
in its original record. A later consumer may accept normal exit zero only when
this exact complete-dump contract passes; other output, resource, ownership or
cleanup failures remain failures. The original benchmark stdout must equal the
entire pinned expected file. The wrapper's fresh-path check is not exclusive
creation; the owned controller must provide an isolated output directory and
independently close its file inventory.

## Retained source authority

All runtime paths below are under
`experiments/rebol/sdk-generation-v1/work-v1/source/src/`.

| Source | Relevant behavior |
| --- | --- |
| `boot/natives.reb:985–992`, `core/n-system.c:195–198` | Existing generic `stats/dump-series`; no new extension command. |
| `core/m-pools.c:937–978` | Enumerates live series and selects value or byte payload by element width. |
| `core/a-constants.c:56–58`, `core/d-print.c:541–565,766–774` | Exact header and eight-digit hexadecimal fields with `#` prefix; high address bits are not printed. |
| `core/d-print.c:373–399` | Prints all `tail` values on one normalized line; the 1024 limit applies to each molded scalar. Integer keys/counts are far below that limit. |
| `core/s-mold.c:1704–1707` | Truncation to the requested limit can append three additional dots. |
| `core/d-dump.c:72–118` | Sixteen-byte hex/ASCII rows; at most 120 rows for unrelated byte payloads. |
| `core/d-print.c:207–229`, `os/posix/dev-stdio.c:639–643` | Untraced debug output is written through the runtime error stream to fd 2. |
| `core/b-init.c:106–110`, `include/sys-value.h:1337–1380` | Retained 64-bit runtime uses 32-byte REBVALs, distinct from the 16-byte extension RXIARG. |
| `include/sys-value.h:414–445` | Tail/rest/bias and `(rest + bias) * wide` total-allocation identity. |
| `core/t-map.c:136–154,287–380,498–526` | Block-backed key/count storage, insertion growth, separate hash series and iteration representation. |
| `core/n-loop.c:391–395,462–478` | `foreach` reads the existing map series in backing order; it does not reflect the complete pairs into a new block. |

The unchanged main is
`archive/languages/rebol/20261013/drafts/private-v1/sources/knucleotide/main.reb`:
record selection is at lines 33–55, the seven full scans at 68–82, and original
output at 83–92. The exact shared input and output live under
`experiments/shared/bounded-corpus-v1/cases/knucleotide/arbitrary-widths/`.
Recorded historical digests are constants in the pure contract; current bytes
have not been rehashed during this source-only preparation.

[`test_map_contract.py`](test_map_contract.py) contains twelve unrun synthetic
tests for complete maps, sequence selection, unique identities, strict stream
and byte-row grammar, capacity dimensions, bounds and separate admission flags.
No import, test, native execution or qualification has occurred. Actual capture,
source/image bindings and independent interpretation remain pending; full-size
work, source work, timing and chart admission remain false.
