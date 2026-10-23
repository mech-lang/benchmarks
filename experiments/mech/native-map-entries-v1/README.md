# Native map entry bindings

This correctness study connects general map operations to the selected native library-call mechanism. It does not add a counting or histogram implementation.

The compiler assigns constructor-private witnesses to `map/new`, `map/insert` and `map/contains-key`, validates their exact schemas and contracts, and supports canonical snapshot keys and Boolean results at the native-call boundary. Tuple, record and enum constructor witnesses admit scalar/map state carriers; the existing constructors still fund and validate their actual recursive payloads. Publicly replacing an implementation's metadata removes its private authority.

`native_map_entries` checks original and bytecode-decoded artifacts. Entry insertion and membership execute through prepared native leaf calls with finite budgets. Insertion preserves the input map; membership publishes true and false values. Denied membership and tuple construction preserve their previous outputs, and membership succeeds on retry. Source arithmetic remains a native scalar addition in the lowered program.

The full counting state machine is **not qualified for AOT**. After resolving tuple-of-map witness selection, all seven diagnostic widths reach the next compiler restriction: structural pattern binding supports only U64 fields. The final test explicitly checks this outstanding rejection; it is not a successful execution test. These bindings also make no physical hash-table representation guarantee. Full-input work validation and quantitative timing remain pending.

`templates-v1` through `templates-v7` retain failed diagnostic attempts, including two unchanged retries following preparation-script errors. `templates-v4` contains the temporary schema diagnostic identifying the tuple-of-map restriction; that diagnostic print is absent from the final compiler. `templates-v5` records a test-code API error corrected before the final check. `templates-v8` is the final four-test map-specific suite. `native-regressions-v1` covers the existing native collection templates and general map source contracts.

All subjects run serially under the shared benchmark mutex. Process receipts identify these runs as non-quantitative and record owned-process cleanup. No benchmark sample or canonical timing record changes in this study.
