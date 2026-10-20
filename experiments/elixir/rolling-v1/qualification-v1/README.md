# Elixir rolling keys: bounded native qualification

The unchanged retained source and both rolling-key candidates compile and pass
all fourteen shared k-nucleotide output cases on the restored historical Elixir
1.20.4 distribution with the existing Erlang/OTP 29.1.1_2 installation. The
production BEAM work witness additionally passes **117 fresh processes across
39 cases, 819 complete histograms and 222,597 standard Map.update calls**. A
separate injected task failure propagates and leaves no observed application
descendant alive. No pilot or full-size timing has run for this packet. Source
counts, canonical formatting and chart admission remain pending.

The source-only proposal in the parent directory remains unchanged. These
completed records supersede its unexecuted status for the bounded gates only.
The original compact/optimized source bundle and all historical measurements
remain intact. The main source, unchanged general I/O/formatting helper and
runner retain their application-source scope; no helper exclusion is claimed.

## Exact runtime, source and compiler boundary

The official [OTP 29 Elixir 1.20.4 ZIP](https://github.com/elixir-lang/elixir/releases/download/v1.20.4/elixir-otp-29.zip)
matches SHA256 `7863c546cda13fecc949e562e326042451dacf8fd8698a36783cb71eeb223b46`.
Every one of its 723 files and all 4,243 retained OTP installation file pins
match the historical manifest. No system installation changed. Actual version
output exactly matches the retained Elixir 1.20.4 / OTP 29 / ERTS 17.1 report.
The VM uses eight schedulers, one dirty CPU scheduler, one dirty I/O scheduler,
one async thread and its existing JIT/default GC policy. Build/runtime flags
remain `+S 8:8 +A 1 +SDcpu 1:1 +SDio 1`, supplied once through
`ELIXIR_ERL_OPTIONS`. Runtime manifests and raw download/version receipts are
retained; ignored distribution bytes are not claimed present in an archive.

The exact main source hashes are:

| Source | SHA256 |
| --- | --- |
| Retained binary-key parent | `325d3d1992f3fcd2128973802904dd842659c34d20d48ff8ffa73a21620f863c` |
| Serial rolling keys | `c42abaa7c1e04edfea27e2965e70e8d40a1a79294dd1fbc23e74f9b26e62968f` |
| Seven-width task stream | `b5e24735c6f0494c0d61fca1ec713011b9a689b3c7dc70c23d4adca4441adddb` |

The helper remains `c9fbb60888c46fb50195245761a411716f1256145af367e03a23f70aea270e89`
and runner remains `bdad2389d437fd4c69122e5d25b3065412b4bca0c272631667283273392ba8ff`.
Each source compiles in its own module-output directory. Native chunk/debug
information binds both loaded BEAM modules to their exact copied source paths;
raw chunks, Code-chunk disassembly, compiler commands and all diagnostics are
saved. The `count/4` instructions contain an actual `Map.update/4` call and
tail call, plus binary match-context operations. They also contain a callback
construction site. This is instruction evidence, not a claim that JIT execution
removes every callback, sub-binary, boxed value or allocation. No native profile
or machine-code allocation measurement has been made.

## Required work and complete state

All seven widths, 1/2/3/4/6/12/18, build complete default-empty standard maps.
Every occurrence invokes ordinary `Map.update/4`; long widths finish their
histograms before looking up the requested query. The source formula is
`sum(max(0,L-k+1))`; full L 125,000,000 requires 874,999,961 updates. This full
total is a source-derived requirement, not an executed full-size witness.

The work probe loads the exact production BEAM, traces private count functions
and the standard library call, and compares every occurrence key/order and
old value against direct independent windows. It does not rewrite the source,
export private functions, replace a table or change a counted source. All seven
final maps are compared entry for entry, including keys unrelated to the five
queries. Cases cover the fourteen shared parser/output fixtures, lengths 0..19,
64 identical A/G/T bases, all 64 Cartesian three-base keys, mixed case, leading
A keys, comments and record boundaries.

On the 114 processes with at most 256 selected bases the probe also records
each real returned map and checks that exactly the selected value increased.
For the three shared arbitrary-width processes with 10,021 bases, compact VM
match-spec messages record every real key, old value and pre-update table size;
complete final maps are still recorded. Per-step returned maps are not copied
in these three traces. Their post-update sizes are reconstructed, checked by
subsequent actual table sizes, and checked against final maps. This limit avoids
quadratic diagnostic map copies; it is not a one-internal-hash-probe claim.

Native `erts_internal.term_type/1`, used only in the untimed observer, confirms
actual flatmap/HAMT representations. For all-triplets DNA length 192 each source
performs 1,305 updates and retains 4/16/64/123/187/181/175 distinct keys by width;
widths 3 and above finish as actual hashmaps. The small-case traces retain the
empty starts and flatmap-to-hashmap transitions. Parallel work uses seven
counting PIDs, plus the standard task-stream monitor process. No hand-written
table, reserved dense key space or pre-sized map was introduced. The exact
vendor Map/Task sources and the pinned OTP internal type declaration are saved.
[Tagged Map source](https://github.com/elixir-lang/elixir/blob/v1.20.4/lib/elixir/lib/map.ex),
[tagged Task source](https://github.com/elixir-lang/elixir/blob/v1.20.4/lib/elixir/lib/task.ex).

The failure check compiles a separately bound twin that changes only the task
callback: width 3 raises after 100 ms while other widths wait 10 s. The monitored
caller receives that failure, and all traced descendants are dead within the
two-second cleanup allowance. The production candidate and its BEAM remain
unchanged. This exercises failure propagation and cleanup, not workload output
or timing. Its expected native exception/logger streams are retained.

## Attempts and diagnostic limits

| Attempt | Outcome and retained reason |
| --- | --- |
| runtime-v1 | FAILED: sandbox DNS could not resolve the official host; raw curl receipt retained. |
| runtime-v2 | PASSED: authorized official download, exact 723/4243 file verification and native version output. |
| bounded-v1 | FAILED: initially unclassified unchanged support.ex:33 unreachable-error type warning, compiler exited0. |
| bounded-v2 | PASSED: that exact warning is recognized with only copied source-path substitution; all 3 builds and 42 complete outputs pass. |
| work-v1 | FAILED: observer expected four-element call messages but requested an additional match-spec message. Production output remained correct; raw trace/error retained. |
| work-v2 | FAILED after 18 passing traces: copying growing full maps for the10,021-base case exceeded the 60 s diagnostic watchdog. Partial raw trace retained. |
| work-v3 | PASSED: corrected trace messages and compact large-case payloads; all 117 complete outputs/work states pass. |
| failure-v1 | PASSED: isolated injected callback failure propagates; traced descendants and external process group are clean. |

The empty `ERL_COMPILER_OPTIONS` value produces the native compiler notice
“Ignoring bad term” when the diagnostic module itself is compiled. That notice
is preserved in the early attempt and production compiler stdout. Only the
untimed work/failure observer environments omit this empty, ignored option;
they load the same production BEAM and use unchanged VM flags. Production CLI
output checks use the bound original environment. The helper warning is not
suppressed or edited out of native streams.

Large raw ETF traces and three large witness JSON files have deterministic,
lossless gzip copies. `lossless-archive-v1/manifest.json` binds both compressed
and original bytes, including the failed 426 MB partial trace. Original raw
paths and sealed reports are unchanged and originals remain local. An archived
checkout can verify every decompressed byte without original paths or runtime
binaries; this is explicitly distinguished from rehashing present local raw
files. No parsed summary substitutes for a raw capture. `archive_traces.py
--recover` writes a fresh copy only beneath the ignored `.build` recovery tree.

Qualification is specific to these source/runtime bytes and bounded cases.
It establishes no speedup, complete full-size run, source-count certification,
canonical formatting, originality or global optimality. Current edits are
Codex GPT-6-family adaptations; exact model and inherited predecessor authorship
and terms remain unresolved. Historical support citations must be inherited
unchanged at any later admission.
