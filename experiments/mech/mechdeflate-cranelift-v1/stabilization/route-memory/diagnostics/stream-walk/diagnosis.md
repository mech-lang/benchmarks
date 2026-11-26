# Repair-walk timing probes

The inactive-block probe counted 31,914 visits with no active replacements across 51,494 visited blocks. Skipping those visits reduced median native-stage elapsed time by 0.661 ms in eight diagnostic pairs. The median change across the full ordinary process was -0.357 ms. The probe used 18 timing invocations, including warmups, and one separate invocation for the block census.

The second probe used the same compiler binary for each of three roles. The roles retained B's walk, skipped inactive blocks, or skipped inactive blocks and iterated the Cranelift layout directly. Each mode compiled the pinned encoder to matching object, bytecode and descriptor hashes. The probe used each of the six run orders once plus one warmup per role. Host reporting and construction census were disabled for these timing probes.

| Diagnostic comparison with B's walk | Median native change | Median compiler-process change | Median peak RSS change |
| --- | ---: | ---: | ---: |
| Skip inactive blocks | -0.684 ms | -1.585 ms | +152 KiB |
| Skip inactive blocks and iterate instructions directly | -2.142 ms | -2.052 ms | +152 KiB |

These observations identify a local source change to test prospectively. After installing the block's repair mappings, walk its instructions only when the active mapping is nonempty. Borrow the function layout and data-flow graph separately and iterate the layout directly. Keep the selective branch-call detachment, traversal order, and argument checks. All six full-process pairs and their variability remain in the raw record. The diagnostic did not qualify a source change. [Raw observations](diagnostic-record.json)
