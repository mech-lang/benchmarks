# Nim k-nucleotide optimization audit

The retained locally adapted source uses seven private standard-library tables,
rolling packed keys and one bounded thread per required width. This experiment
preserves that work and parser while testing ordinary implementation techniques.
No unchanged upstream submission is edited.

The first matched comparison uses the exact retained Nim 2.2.12 distribution
and compiler/dependency flags. A one-line change replaces `getOrDefault` followed
by indexed assignment with `mgetOrPut(key, 0'i64).inc`. Both variants pass all
fourteen retained edge cases and all three complete full-input outputs.

| Variant | Three-run median |
| --- | ---: |
| Retained source, freshly rebuilt | 3.370471 s |
| Standard mutable-value update | 3.031135 s |

That is an 11.2% speedup in this matched comparison. Historical measurements are
preserved. See [full samples](full-matched-v1/report.json), [bounded qualification](bounded-v1/report.json),
[exact source/provenance plan](plan.json), [runtime restoration](runtime-restoration.json)
and [build recipe](matched-build-plan.json). Build receipts and streams are copied
into each execution packet; binaries/generated compilation artifacts remain
local and are hash-recorded. Startup, input, all threads, output and process exit
are included; compilation, validation and file hashing are excluded.

Additional source and CPU-target variants test one-time byte encoding and
`-mcpu=apple-m3` independently. Their source/build preparation does not by itself
qualify them for chart admission or establish better performance. They retain
ordinary standard tables, every per-window update, all seven widths, and the
existing numeric policy. No source-size or canonical-catalog update is implicit.

## Encoding and target-code comparison

[`additional-full-v1/report.json`](additional-full-v1/report.json) contains
three fresh full-size samples for each of six configurations, with randomized
serial order and identical exact output. Each new configuration also passes
all fourteen [bounded cases](additional-bounded-v1/report.json).

| Configuration | Median seconds |
| --- | ---: |
| parent | 3.459123 |
| mgetorput | 3.039232 |
| parent-native | 3.459511 |
| mgetorput-native | 3.027260 |
| preencoded | 2.606080 |
| preencoded-native | 2.612867 |

The one-time uint8 encoding plus standard mutable-value table update is
1.33× faster than the matched original (3.459123→2.606080 seconds).
Every generic/Apple-M3 pair has identical executable bytes, as verified in
[target-binary-equivalence.json](target-binary-equivalence.json). Their timing
differences are variation of the same machine code, not a CPU-target speedup. The source and CPU-target effects are separate configurations,
with no fast-math change. The proposed speed candidate is the simpler
preencoded configuration, not a claim of global optimality.

The map remains an ordinary default-growing Table. `mapIt` encodes DNA once
using standard Nim expressions; it does not count windows. Every histogram
thread still visits every required overlapping window and updates its private
table. No kernel is moved to handwritten C.
