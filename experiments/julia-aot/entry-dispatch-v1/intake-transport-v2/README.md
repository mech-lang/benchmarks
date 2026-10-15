# Static debugger intake transport

This additive source packet repairs only the output transport for the existing
[static LLDB probe](../intake_probe.py). It leaves that probe, its target/module
inspection, the entry controller and all prior captures unchanged. It does not
launch, attach, connect or resume a Julia subject.

The first [intake report](../intake-run-v1/report.json) and its
[failure disposition](../intake-run-v1/disposition.json) remain authoritative:
debugserver rejected `--help` with exit 1 and 42 stderr bytes; LLDB exited 0 with
empty stderr, but its 268,124-byte stdout ended inside the JSON result. The
complete-result requirement therefore failed. No successful debugger intake,
native-owner classification, AOT classification or timing admission follows.

[transport.py](transport.py) captures the unchanged probe's Python stdout and
stderr separately, then writes every UTF-8 byte directly to descriptors 1 and 2.
Partial writes and interrupted writes are handled before returning the exact
probe status. This avoids relying on LLDB's scripting-output queue when exiting
explicitly. Buffered-output loss is a supported explanation for the first
capture, not a dynamically proven cause. The generated outer command pins the
transport, catches loading or forwarding failures, writes the diagnostic directly
to stderr and exits 1. It cannot treat an incomplete descriptor write as success.

## Validation and pending observations

The six methods in [test_transport.py](test_transport.py) passed on 2026-10-15 UTC,
recorded in [the follow-up validation receipt](../../../shared/follow-up-pure-validation-20261015/validation.json).
They cover partial writes and EINTR, complete JSON larger than
the failed capture, independent stderr, probe exceptions and nonzero statuses,
invalid statuses and source pins, zero writes and broken pipes, and the exact
generated command's failure-to-exit boundary. They use fake probes and descriptor
writes; they do not require LLDB or execute a native subject.

The focused tests used the retained Python interpreter and `-I -S -B` after the
serial timing lane was released. Their receipt records the exact source identities;
new tool invocations still require their separate intake review. The next two bounded observations are:

1. The same pinned debugserver with `--log-file=stderr` and **no positional
   argument, socket, PID or program**. The proposed route emits missing-endpoint
   usage with exit 1; the frozen observer's failed status must stay unchanged.
   Review the actual complete version/usage output separately. The local image
   contains the Unix-path and `--attach=<pid>` usage strings. Versioned upstream
   [option handling and missing-endpoint logic](https://github.com/llvm/llvm-project/blob/llvmorg-17.0.6/lldb/tools/debugserver/source/debugserver.cpp#L1086-L1267)
   support this route, but do not bind the exact Apple build or establish local
   behavior. Logging is explicit because non-terminal usage goes through the
   logging callback.
2. The same pinned LLDB with `--no-lldbinit --batch --source` and one generated
   command using this adapter and the unchanged static probe. Accept only a
   complete JSON result, both final module UUIDs, the exact DWARF path, all 27
   file-address breakpoints, required settings/API fields and unchanged false
   admission flags. Preserve any actual failure without truncation or retry.

Both observations reuse the unchanged `kotlin_bounded_v2.py` observer and common
mutex: 30 seconds per command, 5 seconds cleanup, 2 GiB process-group RSS, 8 MiB
native stream limits, fresh per-command output directories and full process/group
closure. The probe's JSON bound remains 1 MiB. Version, scripting-resource and
UUID captures already retained in the first intake are reused with exact pins.

The private invocation draft writes only a fresh `intake-run-v2`, retains the
existing two-tool plan/result schemas and binds the failed v1 report/disposition.
Successful output parsing still does not create the controller's reviewed
`julia-entry-debugger-tool-intake-v1` prerequisite. Exact physical debugger and
scripting-runtime dependencies, capability evidence, complete environments,
working directory and final independent intake review remain required. The
three-child owned entry diagnostic is a separate, still-unexecuted stage.
