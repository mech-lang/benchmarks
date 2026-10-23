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

## Stable caller inventory

Compiler `913450a68c609070b2f12f8f5f5bbf742fa11b75` hoists the caller's fixed node census to entry of a closed native map loop. A paid scan rejects nested control and nonselected managed operations. Only the outer fixed holdings are retained: snapshot owners, call-cache metadata, map entries, key views and actual memory use remain fresh observations. Each loop invocation gets its own census and releases it at exit. Work policy51 funds the changed setup/accounting; IR33 and ABI18 are unchanged.

[caller-census-validation-v2](caller-census-validation-v2) passes 215 native checks with three pre-existing exclusions. Every cached observation in generated-code tests is checked against a fresh complete inventory. The original/decoded counting cases exercise cache population, table growth and view retirement, including Unicode and CRLF. Managed key construction and nested scalar control both decline the cache and preserve correct output. The earlier `caller-census-validation-v1` record retains a syntax failure in the newly added nested-control fixture; the corrected binding syntax passes in the full rerun.

| Executable, one million bases | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0208 | 1.00× |
| Previous Mech AOT `a3b1ddfcd` | 9.679 | 465× |
| Cached caller inventory `913450a68` | 8.944 | 430× |

The [fresh paired measurements](../native-owner-aot-v1/caller-census-timing-v1/results.json) show 7.6% less elapsed time. All nine complete-process outputs match, and both Mech binaries perform seven tables and 6,999,961 updates. Source and program bytecode are unchanged. Ratios use Rust from this same cohort; this is a diagnostic result, not full-input qualification or Rust parity.

## Native paths and fused helper admission

Compiler `32a3a7b449f64740ecf137ba3539a08cda2240e2` replaces straight-line groups with acyclic native paths across scalar branches and joins. All interior predecessors belong to the same entry. Headers cut backedges; helpers remain observable boundaries. The runtime retains the admitted anchor and accepts only a proved frontier, with native Tail-latch retirement at the original next-header boundary. Every original generated instruction and arithmetic failure location remains. Selected map/key helpers admit their boundary inside their own callback; refused owner entry keeps the canonical protocol. IR34, work policy52 and ABI19 identify the change.

[map-path-validation-v2](map-path-validation-v2/summary.json) passes 215 native checks with three pre-existing exclusions. The actual original/decoded and restored-image tests require multiple frontier successors, fewer emitted callbacks and exactly one admission per fused helper. Replay, foreign frontier, missing fuel and interior-error checks preserve control/storage state and cleanup. All 84 independent source counting cases pass. The first full run retains one obsolete ABI18 expectation failure; the corrected ABI19 expectation passes in the complete rerun.

| Executable, one million bases | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0222 | 1.00× |
| Previous Mech AOT `913450a68` | 8.988 | 405× |
| Native paths `32a3a7b44` | 7.331 | 330× |

[Fresh paired measurements](../native-owner-aot-v1/map-path-timing-v1/results.json) show 18.4% less elapsed time. All outputs match and both Mech binaries perform seven tables and 6,999,961 updates. Admitted runtime boundaries fall from 139,717,328 to 55,717,707; the new count includes fused helper admissions and should not be described as standalone callback calls. The source and program image are unchanged. [Matching executable profiles](../native-owner-aot-v1/full-profile-path-v1/analysis.json) identify retained map/key helpers as the largest remaining sampled category. Full-input qualification and Rust parity remain unfinished.

## Closed native map loops

Compiler `7091f025d2489ef511c4650b2c5e6d6dfe29102b` binds a closed generated map loop to private invocation-owned storage. Mech retains traversal, branching, scalar arithmetic and all caller-produced map updates. Entry pins and validates the source String, ownership and account; private general map calls retain checked growth and finite work on that same account. Generated iterations use bounded prepaid fuel, never renewed allowances. Unicode/CRLF and refused admission retain the guarded path. A suspended outer comprehension permits a closed map child; child control inside the map body still declines this optimization. IR36/work policy53/ABI20 fence the selected layout and protocol.

[closed-map-nested-validation-v1](closed-map-nested-validation-v1/summary.json) records 217 passing native checks with three pre-existing exclusions. New original/decoded/restored-image cases use non-DNA keys and caller increments, nested repeated invocations, actual admission reduction, refused entry, exhausted/renewed fuel and invalid callback rejection. All 84 counting cases exercise guarded, native and restored metadata, with independent count oracles and complete cleanup. The version-only IR36 update has its own [identity/counting follow-up](closed-map-nested-identity-v1/process.json). Earlier failing preparation and frontier/geometry diagnostics remain separately retained.

| Executable, one million bases | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0211 | 1.00× |
| Previous Mech AOT `32a3a7b44` | 7.336 | 347× |
| Closed map loops `7091f025d` | 1.985 | 94× |

[Fresh paired measurements](../native-owner-aot-v1/closed-map-timing-v2/results.json) show a 3.70× speedup with unchanged source and program bytecode. All nine complete outputs match; both Mech executables perform seven tables and 6,999,961 updates. Admissions fall from 55,717,707 to 443. The initial top-level-only attempt selected no closed map loops and produced no gain; its [receipt](../native-owner-aot-v1/closed-map-timing-v1/results.json) and selection analysis remain explicit. The final harness requires two selected regions and fewer actual admissions before timing. [Matching profiles](../native-owner-aot-v1/full-profile-closed-v1/analysis.json) now identify repeated range shape/cardinality validation as the largest remaining category. Full-input qualification and Rust parity remain unfinished.
