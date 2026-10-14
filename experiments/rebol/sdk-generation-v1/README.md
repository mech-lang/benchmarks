# Retained-spec SDK generation

This next step consumes the completed Builder spec command. It does not repeat
Builder intake, spec resolution, runtime discovery, or their fixtures.

The closed receipt is
`archive/qualification/rebol/checks/rebol-builder-spec-only-closed-review-v1/receipt.json`
(SHA-256 `2573872ee1076a173ebb225f320e9a38389d7ed0addcdaf2120ef686f06aa542`).
Its native command exited zero as PID 35514, and its durable command exited
zero as PID 35504. It preserved 898 source files and saved the actual spec
with SHA-256 `960a9e74aa4a0bbdc35f02a8ea18e1cba90dfb7681e04853dff524e0922dba5e`.
These are 898 vendor source files plus one resolved spec, not 899 source files.

`spec-source-review.json` records all 179 top-level fields and their spans in
that exact saved map. The selected product is Bulk 3.22.1, macOS, arm64,
apple/darwin, with 4 MiB stack size and a single pre-make action. The resolved
compile list contains 212 distinct files. The generator's lists preserve
243 core entries (191 distinct), 18 host entries (17 distinct), and all
mezzanine duplicates; the unchanged vendor generator performs its own `unique`
operations. No replacement SDK spec is manufactured by the host reader.

`tools/qualification/rebol_sdk.py prepare --plan <new-plan.json> --work
<new-private-work-directory> --output <new-receipt-directory>` verifies retained
receipts and sources under the existing common lock, copies all 898 vendor
files, checks every selected source path, and freezes an execution plan. Run
with the pinned measurement Python and `-I -S -B`. This prepare step has not run.

After independent source and plan review, launch `generate --plan <plan.json>
--plan-sha256 <digest>` through the existing durable owner. It runs exactly the
retained Rebol 3.22.1 binary with `-q -s generate.reb`, the saved spec, fresh
source copy, and output directory. The native wrapper loads the complete
original map, records its native readback, changes only the root-dependent
paths, and invokes the unchanged `make/pre-make.r3` and its six vendor stages.
The locally pinned supervisor gives the process group 300 seconds, writes
actual output directly to retained files, and holds the common lock through
child exit and cleanup. Each process scan has a deadline within the remaining
execution budget. Cleanup has one additional five-second budget. The leader
remains unreaped until no live group members remain, so its PID cannot be
reused while cleanup signals are possible. Historical services are not
executed or modified. The closed Builder/source owners remain leased for reading.

The common lock and all three historical leases are checked by both open-file
and named-file identity again before terminal retention. Input and artifact
reads require regular files; a FIFO, symlink, or other special file is rejected
without a blocking read. Readable failure artifacts are retained alongside
explicit errors.

`test_supervisor.py` exercises timeout cleanup, descendant exit, PID ownership,
deadline propagation, and partial evidence retention with mocked processes.
An unreadable artifact is recorded alongside readable artifacts and does not
prevent writing the report and terminal receipt. These are controller fixtures,
not native SDK observations.

`test_terminal.py` adds temporary-file faults for late input, generated-header,
stream, report, inventory, and lease changes. It also covers special-file
rejection and exact source-copy membership. These new closure tests and the
updated supervisor fixtures pass: 13 terminal cases and 13 supervisor cases.
They use temporary files and mocked processes, without SDK preparation or
native execution.

The wrapper records the actual `sw_vers -productVersion` and `ldd --version`
shell calls. The selected PATH, shell, sw_vers binary, and system version plist
are pinned; ldd must remain absent at prepare and dispatch. The vendor's
fallback release-file shell is rejected. This is child-local instrumentation
of the unscored generator, with unchanged vendor source bytes; independent
kernel post-exec child-image observation is not claimed. Generator dates and
OS query results remain actual observations.

After execution, the controller compares the complete native spec readback and
relocated map, preserves all generated files, checks allowed write paths, and
rechecks original inputs. A successful command means only that vendor SDK
generation completed. The complete `reb-lib.h`, `reb-lib-lib.h`, `reb-host.h`,
`host-lib.h`, `reb-ext.h`, and `ext-types.h` still require layout/API review
before building the existing general extension.

The validated generated files, native spec readbacks, command receipts, and
complete output inventory are retained as exact digests. After writing the
report, the controller rechecks immutable inputs, that inventory, and the
serialized report bytes before its final lease check. A late change records a
failed terminal instead of adopting new bytes as successful evidence.

Remaining gates are generated SDK/API and extension ABI compatibility; exact
Clang, macOS SDK, GMP, and PCRE2 source/header/image bindings; extension build
and load; ordinary byte/pipe IO, rounding, signed arithmetic, regex, error,
ownership and default-GC fixtures; ten complete authored source bundles;
bounded outputs and workload witnesses; native-reader canonical LOC; full90;
runtime publication metadata and chart admission. Independent Git-tree and
runtime/source build equivalence remain unproved. No command or generated
header in this packet is presented as an observed success.
