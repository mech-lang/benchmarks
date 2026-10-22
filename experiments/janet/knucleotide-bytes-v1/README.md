# Janet k-nucleotide byte-input candidates

The parent constructs a normalized whole-input value, selected DNA buffer,
uppercase data, a numeric byte array and a second numeric array of encoded bases.
The byte-buffer candidate retains the parser but encodes directly into a byte
buffer, accepting both ASCII cases without the two numeric-array intermediates.
The line-reader candidate uses the standard Janet line iterator, preserving exact
THREE token selection, comments, CR/CRLF normalization and first-record stopping
state. It retains one LF-delimited line at a time; an arbitrarily long or CR-only
input line is not claimed to have a fixed memory cap.

All seven independent ordinary hash tables remain, for widths 1, 2, 3, 4, 6, 12
and 18. Every window contributes an update, including the complete long-width
tables. No query-only counting, precomputed input-period shortcut, dense fixed
count array or native workload helper is introduced. Rolling numeric keys remain
exact through all 36 bits, and lexical frequency tie order remains ACGT.

`qualification-v1` records 42 complete output checks and 42 actual-source table
witnesses across the fourteen shared cases and three sources. The diagnostic
copies add only sorted emission of every histogram entry immediately before
returning each map. An independent Python byte parser and rolling-key oracle
checks every key/count pair: 294 complete tables, including short/missing records,
comments, lowercase data, empty input and long keys. The normal application
sources have no diagnostic path.

The full three-source cohort in `run-v1` uses one verified N=25,000,000 FASTA
fixture, 125,000,000 THREE bases and 874,999,961 required hash updates. Every
whole-process output must match all 259 bytes and the retained full-size SHA.
Three sequential shuffled rounds share the mutex and power/process controls.
The owned controller additionally records macOS wait4 peak RSS, user CPU and
system CPU. Its memory-unit, clock/telemetry separation and bounded-cleanup test
passed before measurement. Source parsing, VM startup, input, all maps, output
and shutdown are included.

The additional `byte-modulo` and `line-modulo` sources change only the hot key
operator from `%` to standard Janet `mod`. The pinned runtime implements numeric
remainder with fmod and positive modulo with quotient floor/multiply/subtract.
All operands here are nonnegative integers below 2^38, and each divisor is a power
of four through 2^36. Those values and their binary-scaled quotients are exactly
representable in binary64, so the two operators agree throughout this domain.
This does not authorize replacement for arbitrary floating or signed inputs.

`modulo-qualification-v1` checks another 28 complete outputs and 196 full tables.
`native-domain-v1` adds 72,360 boundary/reachable-value checks in the actual runtime;
the pure domain test also checks those bounds. The two modulo files preserve
all original loops and maps. Their separate six-sample full cohort confirms the improvement; exact results
and adjacent-cohort limits are in [RESULTS.md](RESULTS.md).

The input is generated outside measurement using the already verified Janet FASTA
source, then checked against its complete 254,166,745-byte reference. Its payload
is retained only in the ignored `.build/inputs` directory for this and later
stdin workloads; generation command, source/runtime identities and relocation
receipt remain in `input-generation-v1`. It is input preparation, not a timing
observation. Source/case/runtime identities are pinned before quantitative work.

All sources preserve the Janet parent's TypeScript rolling-number lineage and
notices through `source-manifest.json`. Local changes are authored by Codex GPT-6
family, exact serving model unknown. Every authored parser, map, decoder and
summary helper remains application source. Normalized LOC, native canonical
formatting and chart admission remain separate pending gates.

The [complete study](RESULTS.md) also qualifies a standard seven-worker variant,
including full-map transfer, all seven unique completions and worker-error
propagation. Its three full-size samples retain every prescribed window update.
All eighteen samples, 84 bounded outputs and 588 complete table witnesses pass.
