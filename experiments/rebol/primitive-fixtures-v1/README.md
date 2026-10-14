# General Rebol primitive fixtures

This packet supplies executable source fixtures for the nine-command general
extension used by the ten retained Rebol benchmark mains. It does not add source
aliases, replace those mains, regenerate the SDK, or claim native qualification.
The fixture sources, syscall interposer and execution specification are unrun.
The extension itself has not yet been built or loaded.

`common.reb` loads the unchanged `clbg_primitives.reb` through the explicit
absolute `MECH_REBOL_FIXTURE_SUPPORT` directory. That retained loader imports the
absolute `MECH_CLBG_REBOL_PRIMITIVES` path and checks the nine typed commands.
Every fixture exits zero only after its assertions. Non-IO fixtures emit one
specified ASCII success line; IO fixtures emit exact binary data. Unexpected
errors, missing observations, stderr, timeouts and failed process cleanup are
failed outcomes. A failed fixture must remain recorded; there is no retry or
fallback admission in this packet.

Caught failures must also contain the exact retained C diagnostic payload in
the moulded Rebol error value. The surrounding native error representation is
not assumed. An unrelated error or a missing payload cannot satisfy a negative
case.

The source inputs are under
`archive/languages/rebol/20261013/drafts/private-v1`: the ten `sources/*/main.reb`
files and five `support` files remain unchanged. `PRIMITIVE_CONTRACT.md` defines
the byte, arithmetic, formatting, error and ownership contracts. The completed
Builder spec and pending complete-SDK generator remain described in
[`../sdk-generation-v1/README.md`](../sdk-generation-v1/README.md).

| Fixture | Required observations |
| --- | --- |
| `arithmetic.reb` | Canonical decimal binaries; values beyond u64; signed mathematical floor; both operand positions reject invalid bytes; zero division; indexed operands; unchanged operands; distinct results and recovery after ordinary errors. |
| `formatting.reb` | Exact C-format bytes, including binary64 2.675, exact halfway ties in both signs, signed zero, zero and eighteen places, nine-place benchmark output and precision errors. LC_ALL=C and ordinary round-to-nearest are required. |
| `regex.reb` | Case-sensitive byte matching, NUL/high bytes, actual series indices, start/end/empty/absent matches, explicit LF policy, whole-match offsets, independent result blocks and compilation/bounds/match-time errors. The match-error case uses a pattern-local zero match limit with start optimizations disabled. |
| `gc-ownership.reb` | Live operand and returned binary/block values survive ordinary allocation churn; distinct arithmetic results remain live; actual `stats/profile/recycles` increases with no manual collection or policy change. |
| `io-roundtrip.reb` | Every byte value, lengths around the 32768-byte native chunk boundary, regular file and pipe inputs, streaming and collected output, indexed writes, empty writes and stable EOF. |
| `io-faults.c` with IO fixture | Actual interception of extension stdin/stdout calls; two injected EINTR returns for each operation, read requests capped at seven and writes at eleven, exact byte preservation and an independently checked activation/counter receipt. |

The IO input recipe is `byte[i] = i % 256` for the specified length. It needs no
random seed or benchmark data. Ordinary pipe fragmentation and a slow reader do
not establish that a write syscall returned short. Only the separately labelled
fault-injection case may establish that branch, and only when its actual
interposer counters and raw bytes agree. Its 17-byte activation marker is real
stdout and part of the expected output; it is never silently stripped.

The diagnostic interposer includes the selected SDK's
`mach-o/dyld-interposing.h`; it does not author a replacement dyld ABI. Apple's
[official header and example](https://raw.githubusercontent.com/apple-oss-distributions/dyld/main/include/mach-o/dyld-interposing.h)
specify the `DYLD_INTERPOSE` declaration and calls to the original function from
its replacement. Actual macOS loader behavior, extension symbol binding and
activation still need the future native receipt. A missing/zero activation
record is a failure, not evidence of successful fault handling. The interposer
is a test dependency only and must be absent from benchmark environments.

The regex failure fixture follows PCRE2's documented
[pattern-local resource limits and start-optimization controls](https://www.pcre.org/current/doc/html/pcre2pattern.html).
It keeps ordinary byte mode and does not require an optional Unicode feature.
The expected failure must still be observed with the selected native library.

`spec.json` lists concrete commands, input/output recipes, sidecar requirements,
dependencies and future execution gates. After the complete SDK and extension
ABI/build/load gates close, prepare fresh absolute paths under the common timing
mutex, pin their source/library/SDK/compiler/runtime closures, and independently
review the resulting plan. The fixed invocation is the retained Rebol binary
with `-q -s`, one of these scripts and its listed arguments. Use the reviewed
isolated runtime directory, child-local REBOL_HOME and an explicit environment;
no startup file may be inherited silently. Future execution needs the existing
owned process-group supervisor, deadlines, raw stdout/stderr, exact exit and
cleanup receipts, pre/post pins and closed artifact inventories. A specification
is not an executable supervisor or a completed plan.

GC observations report actual before/after counts, without predicting a numeric
collection count. The bounded churn can fail if it does not trigger a collection;
it must not be expanded or retried automatically. Repeated ordinary errors and
surviving values are correctness observations, not a proof of zero native leaks,
fatal vendor-OOM recovery, VM allocation-trap cleanup or every native ABI path.
Nonfinite decimal argument construction and forced VM/vendor allocation failures
remain separate full-SDK failure-probe work. These fixtures do not prove tree
allocation/lifetime, seven full k-mer maps, both executed pi divisions, canonical
LOC, full benchmark correctness or performance. Those remain their existing
independent gates.

`bounded-corpus-map.json` connects the ten exact retained main sources to all
149 existing shared cases (142 successful references and seven invalid-input
references), their real primitive usage and argument/stdin routes. It does not
duplicate the corpus or claim that these sources pass it. The Rebol negative
exit/stderr adapter remains pending actual runtime evidence; the source-only
expectation of empty revcomp output follows its final buffered write.
