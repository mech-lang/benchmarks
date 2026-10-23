# Admitted node witnesses and native arena census

Canonical snapshot admission now retains the node count established by its existing complete footprint traversal. The witness is available only for the exact admitted memory account and schema owner. Admission reuses the same traversal's byte total instead of computing that footprint a second time internally. Immutable snapshots retain their existing ownership and validation rules.

The native value arena maintains a conservative sum of those witnesses. Slot replacement, retirement and transfer update the sum without walking payloads or schemas; repeated aliases count separately. The extra per-slot word and snapshot metadata remain admitted allocations. The work policy advances from 41 to 42, rejecting objects priced under the preceding policy. Typed IR28 and ABI15 remain unchanged.

This sum covers current arena slots. It does not establish complete caller/frame geometry, include every external root or private builder, or grant execution authority. The retained map backend is still not selected by normal generated programs. Counting traversal, window construction and arithmetic remain responsibilities of the Mech program; no DNA counting helper is introduced.

Validation covers 320 core checks, two catalog checks, 197 native checks and eleven map integration checks: 530 distinct passing checks, with three pre-existing native exclusions. The focused witness test is included in the core total. Tests cover unadmitted and foreign-account rejection, same-account reuse, independent import, alias overcounting, replacement, retirement, transfer, stale handles, foreign work ledgers and complete memory-account release. Existing object identity tests reject the preceding work policy.

`core-witness-v1` retains a closed compiler failure caused by an omitted destructuring field; that omission is fixed. `core-witness-v2` passes the focused test. `core-regressions-v1`, `native-regressions-v1` and `map-contracts-v1` retain the broader passing checks. Subjects run serially under the shared benchmark mutex and retain bounded process-control and cleanup records.

The accompanying seal pins the compiler revision and evidence hashes. There are no quantitative benchmark samples, changes to the canonical dataset, or claims of measured runtime improvement. Whole-program retained-map execution, full-input qualification and fresh timings remain unfinished.
