# Rebol ten-program publication intake

The additive [importer](../../../../tools/qualification/import_rebol60.py) reproduces the independently reviewed full60 export, then previews or applies it to a separate publication checkout. It retains ten canonical programs and fifteen physical authored source files. Each successful program has three fresh process samples and three matched Mech controls; the same program may supply both fastest and fewest-lines endpoints. No second program or timing alias is created.

The source, qualification, raw measurements, runtime metadata and historical release metadata must be independently reviewed before publication. Failed programs or controls preserve their actual observations without a comparative endpoint. Runtime-source equivalence, numeric GC defaults and per-sample loaded-image inventories remain unclaimed. The complete authored application, loader, facades and general C extension count once per bundle; formatted LOC remains unavailable.

Only `data/benchmarks.json`, `data/languages.json` and `site/src/languages.mjs` are targets. Existing observations, sources, baselines, metadata and program records remain unchanged. A new time or LOC minimum requires a separate normalization review. Public evidence links must reproduce the exact retained bytes in both checkouts.

The CLI retains the [original importer's preview/apply arguments and transaction semantics](../../full90-v1/publication/README.md), using `import_rebol60.py` and the full60 plan, candidate, independent reader and exporter. Preview records three prepared targets and their original bytes outside both roots. Apply requires all three original target digests and all three reviewed preview digests. The exact qualification, cohort and durable leases remain held through final checks. Late failures restore only owned bytes and preserve external edits.

The source-review schema is `rebol-full60-import-source-review-v1`, with status `independent-source-review-complete-actual-import-pending`, `independent_review: true`, and false `native_execution` and `chart_admission`. Its files map binds this README, `import_rebol60.py` and `test_import_rebol60.py`; dependencies bind `rebol_export60.py` and the unchanged `import_typescript.py` transaction source. The runtime and historical release metadata schemas remain unchanged.

This packet contains source and synthetic tests. Actual timing, independent reconciliation, export, preview and catalog application remain pending.
