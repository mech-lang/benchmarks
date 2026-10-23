# Rolling ASCII window keys

Compiler revision `c79dda8cd4b075e7a056f390ba6b9579735f927b` moves
injective seven-bit ASCII key construction into the Cranelift loop. It reads
each source byte once per width and keeps the overlapping key in two registers.
Every complete window still updates the pinned hashbrown library table.
No DNA alphabet, requested query or expected answer is built into the lowering.

Finite work is prepaid in groups of at most 1,024 updates on the existing
invocation account. Table growth funds the remaining capacity delta before
the affected lookups. The independent accounting test checks the same final
collision and growth envelope as the preceding per-update implementation.
ABI14/work policy39 rejects preceding private packed-key callback contracts.

All 167 native regression tests pass, with three ignored. The public source
and decoded builds produce identical executable bytes. Twelve bounded cases,
two permission denials, and both standard full-input outputs pass. Each full
execution reports seven completed tables and 874,999,961 actual updates.

`profile-v1` captures one owned, instrumented full-input execution using the
macOS sampling profiler. This is a diagnostic, not a timing cohort. The sampled
binary is stripped: the retained stack addresses and instruction offsets must
not be presented as resolved source-level function names. The two dominant
generated window call sites account for 1,552 of 1,562 captured main-thread
stacks, including 963 stacks beneath their indirect update calls. Disassembly
shows library table probing/count updates on that path. This supports testing
bounded callback batching while retaining every actual table operation.

There are no quantitative benchmark samples in this study. Final timing and
catalog admission are deferred until further optimization. No historical
versions or other languages were remeasured. The canonical dataset and website
are unchanged. `seal.py --check` verifies retained execution closure, exact
full outputs, work witnesses, binary identities and evidence hashes.
