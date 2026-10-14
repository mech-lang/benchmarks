# Generic debugger launch diagnostic

This experiment tests the host debugger needed for Julia interpreter-observation
canaries. It launches the previously compiled, SHA-256-pinned generic C helper;
it does not launch Julia or produce benchmark samples.

The single diagnostic used normal ASLR, a fixed minimal environment, no LLDB
initialization file, stop-at-entry, symbolic `main` and `calibration_probe`
breakpoints, and debugserver plus GDB-remote transport logs. The supervisor held
the shared benchmark mutex throughout execution and cleanup. No security or
authorization settings were changed.

The debugger did not return from `SBTarget.Launch` before the 25-second deadline.
The retained transport log shows a successful debugger/debugserver handshake,
followed by a `vAttach` request for the newly launched helper. The last
debugserver record is immediately before `task_for_pid` for that helper; no
success or error return was recorded. Upstream [MachTask source](https://github.com/llvm/llvm-project/blob/main/lldb/tools/debugserver/source/MacOSX/MachTask.mm)
places that log immediately before the task-port request. This locates the stall
at host task-port acquisition; the evidence does not establish an authorization
refusal or its underlying cause.

The supervisor killed its LLDB process group and the two observed descendants
(the stopped helper and debugserver), checking each process's kernel birth
identity before signalling it. No tracked process remained alive. The pinned
helper and LLDB bytes were unchanged. No helper breakpoint or output was
observed, so debugger calibration and Julia AOT admission remain incomplete.

`result/report.json` records the exact command, environment, lock identity,
process ownership, cleanup, and hashes. `result/launch-entered.json` records the
actual launch flags and breakpoint locations. `supervise.py` and `observer.py`
are the exact executed sources. Their paths in the receipts identify the
original temporary experiment directory; this directory preserves those bytes.
