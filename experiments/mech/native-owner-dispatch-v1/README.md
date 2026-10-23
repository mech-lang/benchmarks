# Generated retained-map dispatch

Compiler revision `9e2d1a29cdeee612dcae850c32eb326755e14d8a` selects retained String/U64 map storage for proved closed map-valued state machines. The generated CFG still performs traversal, window selection, membership/defaulting, arithmetic and state transitions. Generic hashbrown storage accepts the values produced by Mech. No Rust counting body, source-name match or nucleotide-specific helper is introduced.

Each candidate has an appended native live flag. Checked entry imports the typed seed and copies admitted carrier words into a disjoint native slice. Refused metadata/table admission performs the ordinary canonical MOVE on the same visit and ledger. Subsequent generated blocks choose between canonical execution and native pack/project/observe/latch transport. Selected map calls pass versioned references, canonical String keys and caller-produced U64 values through checked helpers. Exit publishes an independent canonical map and clears the flag. Ordinary helpers are rejected at active native sites; required-helper and loop-retirement checks still apply. An active owner cannot survive program completion.

Build-owned metadata now includes constant-time action/call-to-region indices. Descriptor and compiler derive the same layout and finite extra visit costs. The owner lane accounts for all private tables and fixed metadata, while an active-table counter makes completion checks constant-time. IR31, work policy47 and ABI16 fence the selected representation, appended flags, metadata and helper protocol. The scalar frame prefix is unchanged.

Actual generated-code observations qualify original and decoded artifacts. The basic fixture performs three retained insertions and membership/lookup calls, with zero canonical map calls on the selected path. A nonempty seed and a wider carrier verify caller-produced replacements using two scalar state fields; both zero-body and three-step cases publish independently expected maps. Foreign descriptor/ledger probes, malformed operand pointers, stale references, repeated operations and ordinary-helper substitution are rejected. Deliberately corrupted native references and an injected failure after insertion release all table, key, lane and snapshot claims. Fixed metadata refusal executes the canonical path and produces the same expected result.

The source-written counting procedure additionally has 42 explicitly observed cases: seven widths, three input strings and original/decoded artifacts. Each case performs exactly the expected number of retained insertions, has zero canonical map calls, and checks every returned key/count against an independent reference. These are bounded counting cases, not full-input or standalone executable qualification.

All 209 native checks and eleven map integration checks pass: 220 distinct checks, with three pre-existing native exclusions. The initial compile-only invocation accidentally matched no tests and is retained without claiming test coverage. The first native run passed 208 checks and failed an obsolete ABI15 assertion; the corrected ABI16 assertion passes in the complete rerun. Focused owner and counting runs retain their separate records. All subjects execute serially under the shared benchmark mutex, with bounded process control and terminal cleanup records.

The explicit source hash-table contract, full-input source/decoded standalone work qualification and fresh complete-process secured/trusted timing cohort remain unfinished. The complete workload must still prove seven tables and 874,999,961 actual window updates for this source implementation. This checkpoint did not change protected upstream sources or the website dataset.

## Maintained cache metadata totals

Compiler `f6ee09e631048fb831d2032e8013a56d876efc63` replaces repeated whole-cache metadata scans with totals reconciled at each cache mutation. The lane retains the exact library account and rejects a foreign account or invalid total. Reconciliation also runs after a failed operation; a failed reconciliation leaves the total unusable. Original/decoded caller-geometry observations independently recompute the complete inventory and compare it with both the per-cache values and aggregate, including selected String projections. Work policy 48 identifies this accounting change; IR31 and ABI16 are unchanged.

[cache-census-v1](cache-census-v1) passes all 209 native checks with three pre-existing exclusions. Fresh complete-process source-map measurements on a 100,000-base prefix improve from 8.4683 seconds (1.81× current Mech AOT) to 4.6755 seconds (1.00×); every output matches the independent reference. The [standalone study](../native-owner-aot-v1/README.md) retains paired timings, the matched executable profile and the distinction between historical #909 and its source rebuilt with the current compiler. These diagnostic gains do not qualify the full 125-million-base source-map workload.

## Borrowed selected String keys

Compiler `7aa1bea1b5565113cd07ddeaeea2bed30ed84a54` projects nonescaping selected String keys through the existing maintained String index. The original range and selection visits remain checked. The selected key retains a strong source owner and validated byte bounds until the owning state transition retires the view. Every consumer must be a membership, lookup or insertion in the same map region; other observers decline the optimization. Hash storage receives the caller's computed values and does not implement the source traversal or counting algorithm.

The image includes the selection proof and constant-time indices. The lane accounts for fixed metadata and live pins; bounds/cardinality errors, Unicode/CRLF semantics, account identity, finite work limits, helper freshness and refused owner entry remain enforced. IR32, work policy49 and ABI17 reject stale images and host protocols. The scalar frame prefix is unchanged. Execution reports now count actual retained-map imports and successful updates.

| Compiler | Input | Median seconds | × `7aa1bea1b` Mech AOT |
|---|---:|---:|---:|
| Parent `f6ee09e63` | 100,000 bases | 4.686 | 3.40× |
| Selected keys `7aa1bea1b` | 100,000 bases | 1.380 | 1.00× |

Each row contains three alternating fresh secured processes, with startup/shutdown included and one excluded warmup. All outputs match the independent reference. The candidate reports seven tables and 699,961 actual updates on every run. [Standalone receipts](../native-owner-aot-v1/key-span-timing-v1/results.json) retain raw samples and exact artifact identities. This diagnostic does not qualify full-input performance.

[key-span-validation-v2](key-span-validation-v2) passes 211 native checks with three pre-existing exclusions. The source counting fixture covers 84 original/decoded cases: seven widths and six inputs, including Unicode, CRLF and an empty input. It independently checks returned maps, actual update counts, both projection visits and the absence of canonical range/key calls. Additional checks cover extra key observers, invalid bounds, refused owner entry, stale or substituted helpers, corrupted map references and cleanup after failure.

The retained failed diagnostics are not passing evidence: `key-span-count-v1` exposed an incorrect assumption about Tail iteration counters, corrected by retiring views at the actual Tail latch/exit boundary; `key-span-validation-v1` failed an obsolete ABI16 assertion, updated to ABI17 before the complete rerun. `key-span-count-v2` and `key-span-validation-v2` contain the corrected passing records.

## Grouped native instruction admission

Compiler `a3b1ddfcdf501f4bc3c6eb81a7e975849295fcc4` groups consecutive native owner instructions with single-entry interiors and no intervening library helper, loop transition or ownership boundary. One checked entry prepays every original visit's work plus proof overhead. The generated CFG retains every operation and its original failure origin. The runtime advances to the proved group end for the next callback; exceptional arithmetic returns are accepted only at an original member of that live, admitted group. Refused owner entry keeps ordinary per-instruction admission. IR33, work policy50 and ABI18 pin the protocol and decoded layout.

[map-admission-validation-v1](map-admission-validation-v1) passes 213 native checks with three pre-existing exclusions. Original/decoded and build-owned-image tests observe actual emitted callbacks, verify correct outputs through native and fallback paths, reject replay/interior entry, refuse one-short fuel before advancing the group or spending a partial debit, preserve an interior division failure's exact origin and verify complete cleanup. The 84 independently checked source counting cases also pass.

| Executable, one million bases | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0184 | 1.00× |
| Previous Mech AOT `7aa1bea1b` | 12.570 | 682× |
| Grouped Mech AOT `a3b1ddfcd` | 9.600 | 521× |

Three fresh complete processes per executable run serially in alternating order, after excluded warmups. Every stdout matches the independent reference. Both Mech executables perform seven tables and 6,999,961 updates; actual admission callbacks fall from 321,998,942 to 139,717,328. The [standalone receipts](../native-owner-aot-v1/map-admission-timing-v1/results.json) retain all samples and identities. This 23.6% improvement leaves a substantial gap to Rust and does not qualify the full-input source-map workload.
