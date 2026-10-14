# Remaining offline Julia captures

The original eleven-command stage retained nine successful native LLVM decodes.
Its post-validator accepted eight and rejected the ninth because no positive RSS
sample had been recorded. The original [failed report](run-v1/report.json),
[terminal](run-v1/terminal.json), and all raw command artifacts remain unchanged.
The [closed-stage review](nine-capture-closure-review-v1.json) binds all 46 saved
files and records the ninth command's normal exit, owned identity, complete
output, reaping and empty process group.

`tools/qualification/julia_native_inspection_remaining.py` schedules exactly
the original slots 9 and 10: `llvm-objdump --disassemble --reloc --syms` on the
retained native archive and final executable. It never repeats an LLVM decode
or executes Julia/N-body. Preparation reconstructs the original eleven-command
input and declared tool closure through the frozen metadata adapter, verifies
the closed nine-command prefix, then selects only these two unstarted slots.
All original artifact paths, library paths and 31 exact metadata mappings stay
unchanged. The new plan records and pins the prior failed stage explicitly.

The frozen observer still enforces a 30-second deadline, five-second cleanup,
2 GiB process-group RSS limit and 64 MiB stream limit. Commands are sequential,
with one attempt each, while the common mutex (inode 79859134) is continuously
held. Input identities, output hashes, serial execution, child birth identity,
normal exit, reaping, empty process group and final artifact closure remain
required. A failure stops the stage; it does not trigger a retry.

The derived RSS field is `null` only when the raw producer recorded zero and
the child was already the same owned zombie at registration and before reap.
This is an unavailable live observation, not a zero-byte memory measurement or
proof that a peak stayed below the limit. A zero following a live registration
is rejected as ambiguous. Raw process JSON is preserved. Every derived capture
records `rss_observation_complete=false` and `memory_usage_qualified=false`,
including captures with sampled positive peaks. Missing identity, dirty groups,
an observed RSS above the limit, failed exits and unexpected output remain
failures.

After source review and release of the shared measurement lane, prepare with:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/julia_native_inspection_remaining.py prepare --plan /private/tmp/mech-benchmark-completion/experiments/julia-aot/trimmed-native-inspection-v1/remaining-plan-v1.json --output /private/tmp/mech-benchmark-completion/experiments/julia-aot/trimmed-native-inspection-v1/run-remaining-v1
```

Review that concrete plan before submitting its exact digest and absolute path
to the shared durable launcher. The controller command is the same pinned Python
invocation followed by `run --plan <absolute-plan> --plan-sha256 <reviewed-sha>`.
Use a fresh durable job name such as `julia-offline-inspection-remaining2-v1`.
There is no prepared plan or native success claimed by this source packet.

The focused test file is `tools/qualification/test_julia_native_inspection_remaining.py`.
It uses synthetic files and receipts; running it does not start LLVM, Julia or
any child process. All 16 focused tests passed in 0.028 seconds. Actual plan
preparation and native validation remain pending for this source packet.

These captures supply inspection evidence only. Native owner, actual IR
removal, fallback closure, runtime AOT and chart admission remain false. Static
declared Mach-O dependencies do not assert which images were dynamically loaded.
