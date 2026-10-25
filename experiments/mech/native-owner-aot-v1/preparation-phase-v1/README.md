# Preparation phase diagnostic

This study measures preparation in direct-offset production candidate `91f725adc16b1ba349d77cc898e6e24de4a79bf6`. Diagnostic host commit `19b3b1ae292e21b1c91aa598ddd2bfe14d084f9f` wraps the unchanged guest object with main-thread CPU and monotonic wall clocks. These instrumented executions contribute **zero primary benchmark samples**.

Six full-input observations per subject run serially in the predeclared balanced order, with no excluded warmups or outliers. The original 125 million selected bases, all seven maps and 874,999,961 Mech updates, launch policy, output digest and exclusive lock are checked. Rust uses the previously qualified boundary-instrumented copy of the protected upstream implementation. Neither executable changes CPU, power, priority or scheduler settings.

| Diagnostic preparation milestone | Median main-thread CPU, seconds |
| --- | ---: |
| Mech capture begins | 0.007329 |
| Mech successful EOF and source scanning complete | 0.145102 |
| Mech byte-map loop begins | 0.180577 |
| Mech byte-map loop completes | 0.193558 |
| Mech worker launch begins | 0.195870 |
| Rust input ready | 0.127853 |

The two final milestones reflect each implementation's preparation boundary, rather than identical internal phases. Mech's main-thread CPU before launch is 1.53 times Rust's input-ready CPU in this diagnostic. Thread creation itself was separately measured at roughly 75 microseconds in the preceding worker study; the main delay precedes it.

| Mech measured span | Median CPU, seconds |
| --- | ---: |
| Borrow line windows | 0.001001 |
| Execute source scanner | 0.072775 |
| Selected join, total | 0.028292 |
| Selected join, copying subspan | 0.028280 |
| Prepare byte-map loop | 0.001906 |
| Execute byte-map loop | 0.012981 |
| Finish byte-map result | 0.002274 |

Nested spans are not additive: join copying is contained in selected join, and borrowing/scanning are contained in capture. Differences between milestone totals and named spans include uninstrumented admissions, source initialization, copying and cleanup. Phase medians are taken independently, so their sums need not equal a median milestone difference. Every borrowed window used the direct LF-offset representation; none materialized a temporary row directory. Capturing and scanning still account for most preparation CPU. The next independent candidate should compose the existing selected join and byte map after successful EOF, preserving source errors, join admissions, complete-use ownership and cold fallback.

The diagnostic host binary SHA-256 is `b4c649da2568d91a740a7c95791fe955ca3cbd647c303ed47e5ec72391a840e1`; its unchanged guest object is `7b1fa85e74cc23a88ce5d9937ad68c7bf003fe5038b4da4e9039171cee3210ea`. All launcher/object/resource checks remain active; the copied launcher adds only the phase guard and refreshes its own source pins. Build, prefix qualification, raw full-process receipts, phase records and the fixed plan are retained here. `verify.py` rechecks 14 terminal native receipts without rerunning subjects.

Primary complete-process comparison remains in the [direct-offset study](../borrowed-offset-cursor-v1/README.md): Mech 0.6713 seconds versus Rust 0.5479 seconds (1.23× Rust) in the first session, and 0.6713 versus 0.5593 seconds (1.20× Rust) in the repeat. The diagnostic durations here do not replace those measurements or establish a new production speedup.
