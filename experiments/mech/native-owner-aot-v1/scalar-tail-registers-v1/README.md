# Scalar Tail loan registers

**Decision: retain the finite-worker-credit parent; do not promote this candidate.** Both balanced full-input sessions show a slowdown.

Candidate source: [`bd690a4eb`](https://github.com/mech-lang/mech/tree/bd690a4eb931fad284fc2ae6ceda8cdea6b62de4). Parent: `7a715c12a`. The independent design is described in [design.md](design.md).

Three private scalar-loan words use Cranelift entry-local SSA, with synchronization to their original homes at preparation, leave, pause, checkpoint clearing and error boundaries. Every original two-dimensional header debit, finite cap and checked fallback remains. The source, bytecode and resource image are unchanged. IR83 identifies the changed guest; ABI29 and work policy68 remain.

## Complete-process timings

Each session contains all six balanced three-subject orders, six complete processes per subject. These timings include secured startup through process exit on the same 125-million-selected-base input. No full-input warmups or outliers were excluded. Sessions remain separate.

| Session | Candidate | Candidate / Rust | Parent | Parent / Rust | Rust | Paired candidate change (95% interval) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 0.6425 s | 1.160× | 0.6186 s | 1.117× | 0.5537 s | +3.54% [+0.17%, +4.81%] |
| 2 | 0.6430 s | 1.159× | 0.6265 s | 1.129× | 0.5547 s | +2.84% [+1.70%, +3.52%] |

The separate one-million-selected-base prefix check uses one excluded warmup and three measured processes per subject. It does not establish short-input parity.

| Prefix subject | Seconds | × Rust |
|---|---:|---:|
| Candidate | 0.1113 | 5.757× |
| Parent | 0.0950 | 4.913× |
| Rust | 0.0193 | 1.000× |

## Code, work and diagnostics

[Actual function-byte comparison](code-inspection.json) confirms that only the main entry changed: all eight normalization, call-bridge and packed-count functions remain byte-for-byte identical. Entry bytes including trailing alignment grow from 43,376 to 44,616. Total admitted code grows from 112,356 to 113,596 bytes; admitted stack grows from 1,216 to 1,248 bytes. Both executable files remain 5,501,200 bytes because of file alignment. Median peak RSS is 162.75 / 163.01 MB for the candidate, 162.31 / 162.69 MB for the parent and 140.71 / 140.46 MB for Rust across the two sessions (decimal MB). No memory improvement is established.

Every full process retains seven complete hash maps, default hash-table growth, all 874,999,961 original updates, five lookup caches and the seven-worker cap. Every candidate reports exactly 854,497 original funded batches; [independent reconciliation](selection-verification.json) checks all twelve reports. No dense replacement, query-only scan, input recognition or altered OS setting is introduced.

Separate hardware-counter medians are diagnostics, not primary elapsed samples:

| Subject | Instructions | Cycles | User CPU | System CPU |
|---|---:|---:|---:|---:|
| Candidate | 24.833 B | 6.111 B | 1.72 s | 0.03 s |
| Parent | 24.985 B | 5.955 B | 1.68 s | 0.03 s |
| Rust | 33.130 B | 7.870 B | 2.32 s | 0.03 s |

The candidate retires about 0.6% fewer instructions while taking about 2.6% more cycles in these separate diagnostics. This does not establish a cause such as register pressure; it demonstrates that the reduced metadata traffic did not produce an elapsed win. The larger entry and additional stack requirement are retained for subsequent assembly analysis.

[Fresh profiles](analysis.json) use a symbolized binary whose complete machine-code section equals the exact timed candidate. They contain three complete Mech and three Rust executions. Generated counting loops account for 85.67% of Mech worker leaf observations; active budget accounting accounts for 3.38%, credit handling 0.03% and budget waits 0.77%. These perturbed observations are not percentages of recoverable elapsed time. The independently measured parent preparation diagnostic remains [credit-preparation-workers-v1](../credit-preparation-workers-v1/README.md); it is not a phase decomposition of this candidate.

## Verification and retained attempts

All 394 native checks and the catalog check pass; three existing manual tests remain ignored. The new direct differential test covers original and decoded bytecode, repeated empty/growing prefixes, EOF, Unicode/CRLF/empty rows, missing markers, compute/comparison exhaustion, exact work/error origins and cleared checkpoint homes. All owned memory retires.

[Verification](verification.json) checks 83 terminal native receipts, output hashes, source/bytecode/resource pins, both full sessions, prefix observations, exact-text profiles and counters. Three unsuccessful test-build attempts remain recorded. The first profile attempt could not enumerate processes in the sandbox; its bounded sampler was killed and reaped, its benchmark subject completed with correct output, and no sample from that attempt is used. Fresh `v2` paths contain the successful profiles.

The scalar-register branch remains available for interaction experiments. The qualified performance checkpoint remains the finite local worker-credit parent, and the Rust parity goal remains incomplete.
