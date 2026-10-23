# Direct String-map cost control

This diagnostic separates the cost of a serial String/U64 hash-table algorithm from the current generated Mech caller. It was written for this experiment; it is not an upstream submission, a Mech implementation or a replacement benchmark result.

[string_maps.rs](string_maps.rs) uses the same pinned hashbrown 0.15.5 library and `HashMap<Box<str>, u64>` representation as Mech's retained map. Non-inlined lookup and insertion functions preserve separate membership, lookup, insertion-freshness and update operations. Every width builds its complete table before producing its output; the program performs all seven widths and every window update. It uses neither packed keys nor parallel workers. The input is restricted to the ACGT workload used for this control.

The control omits Mech's descriptor/ownership/admission machinery, resource accounting and canonical map publication. LLVM generates its loop, while Cranelift generates the Mech loop. Therefore this comparison does not isolate one optimization, establish a guaranteed speedup or qualify an alternative Mech implementation. Together with the Mech executable's profile, it tests whether retaining String keys and separate storage calls inherently explains the observed runtime gap.

## One-million-base measurements

| Executable | Median seconds | × upstream Rust time |
|---|---:|---:|
| Protected upstream Rust #7 | 0.0176 | 1.00× |
| Direct native String-map control | 0.2034 | 11.58× |
| Mech AOT `32a3a7b44` | 7.3861 | 420.47× |

The control takes 36.3 times less elapsed time than Mech in this cohort. Each median contains three alternating serial processes, includes startup, input, complete output and shutdown, and excludes one warmup. All nine measured outputs exactly match the independent reference. Both the control and Mech verify seven tables and 6,999,961 updates. [Measurements](timing-v1/results.json) retain all samples, source/library/binary hashes, environment and compile command. The Mech executable is unchanged from [the native-path cohort](../native-owner-aot-v1/map-path-timing-v1/results.json); its different Rust multiple reflects the denominator from this separate cohort, not a compiler regression.

## Exact-binary profile and full-input correctness

The exact timed control binary also completed the standard 125-million-base input under profiling. Its full stdout matches the established reference and its update report verifies seven tables and 874,999,961 updates. [Receipts](full-profile-v1/results.json) record the owned process and terminal cleanup. This profiled duration is excluded from benchmark samples.

Three one-second captures during the beginning of that execution show 62–66% inclusive lookup stacks, 32–35% insertion, 29–35% String comparison and 11–16.5% UTF-8 validation. Categories overlap. [Analysis](full-profile-v1/analysis.json) uses all main-thread samples, including partial unwinds, as its denominator. These profiles describe this control, not the generated Mech executable or every width.

## Compiler target

The primary target is a complete native map-loop binding: admit and pin the map and input once, retain source-generated traversal/branches/arithmetic, and use thin general storage calls inside the loop. Source bounds and representation must be established through maintained String facts, including CRLF/Unicode fallback. Capacity growth and publication remain checked boundaries. Finite work must be prepaid or charged in bounded batches on the same invocation account; the optimization must not disable accounting or renew spent allowances.

The current compiler already proves owner exclusivity, nonescaping selected String keys and stable caller inventory. Its closed scalar Tail also demonstrates native finite fuel, but it currently excludes map helpers. Connecting these mechanisms should target the repeated descriptor, geometry, key-projection, reference and budget setup responsible for most observed Mech counting time. This is the next implementation target, not an implemented speedup. General lookup reuse, packed representations and parallel independent loops remain subsequent opportunities.

Reproduction uses `measure.py`, followed by `profile.py` and `analyze.py`. Build, timed subjects and profiles all use the existing shared benchmark mutex and bounded owned-process cleanup. The canonical dataset and protected upstream programs are unchanged.
