# Julia entry dispatch diagnostic

This source draft observes one execution of the unchanged retained N-body image
with argument `1`. It resolves the actual entry target and records any observed
interpreter or code-generation fallback. It does not repeat the full benchmark,
rewrite the executable, or establish an AOT classification by itself.

[The static owner review](../trimmed-native-inspection-v1/static-owner-chain-review-v1.json)
already joins native bodies from the exported entry to state construction, the
original driver, both energy calls and the integration loop. Its proposed input
was `1000`; [this draft](plan-draft.json) uses `1` to minimize the diagnostic work.
No retained input-1000 output oracle is reused for that different input.

## Concrete observations

[trace.py](trace.py) contains the exact retained file addresses and bounded LLDB
observation routines. The owner supplies physical module identities, an event
sink and an already registered owned process. The module never launches or
attaches to a process and never evaluates an expression inside it.
The owner binds that stopped process once with its PID, LLDB unique process ID
and recorded birth identity. Every subsequent stop and exit must belong to that
same target; stop IDs must advance, so repeated state events cannot count a
single breakpoint visit twice. Module membership and breakpoint identity are
rechecked on module events and stops.

The final disassembly at `run-remaining-v1/10-final-executable/stdout.bin`,
lines 6233–6251 of the inspection packet, loads `jl_ext_4` at `0x10004c5b0`,
compares its cached world against the runtime world at `0x1000045a0`, optionally
calls the ABI converter, and calls the selected target through `x8` at
`0x1000045c4`. The trace records registers before that call and after its return.
The native entry is `0x10001afcc`; a matching observed target plus the downstream
constructor/driver/energy/integration stops would establish that actual bounded
execution path. The `nbody` entry records its `x1` argument; the decrement stop
records the original loop's `x13` before it becomes zero.

The interpreter and code-generation breakpoints use the retained runtime symbol
values, resolved through the loaded image rather than treated as process
addresses. The runtime hash, header and matching debug information remain exact
prerequisites. Every breakpoint must resolve to one location. Unexpected stops,
unknown module changes, missing locations, incomplete logs or missing positive
native witnesses leave fallback absence unqualified.

The debugger reads the eight-word `cfuncdata` structure and directly selected
`CodeInstance` objects without calling Julia. Its layout comes from the matching
DWARF type and must agree with the retained header. The
[Julia runtime implementation](https://github.com/JuliaLang/julia/blob/v1.13.1/src/runtime_ccall.cpp#L343-L479)
permits reuse of a native target as well as selection of a generic thunk; entering
the converter alone is not evidence of interpretation. The retained
`julia.h:452–511` permits several `inferred` representations. Raw pointers and
bounded headers are therefore retained for review, with no automatic claim that
a non-null value is executable serialized IR. Method bodies and alternate paths
outside this selected chain remain a separate question.

## Prepared execution boundary

The 5 ownership-component test methods passed on 2026-10-15 UTC in
[the initial pure-validation record](../../shared/pure-validation-20261015/post-prolog-pure-validation-run-v1/report.json); the 4 controller methods
passed in [the repaired-run record](../../shared/pure-validation-20261015/post-prolog-pure-validation-repaired-v1/report.json). The original
controller failures remain in the first record. These use fake children and
small local files, without a debugger or Julia process. Preparation of the owned
diagnostic and its subject execution remain pending. Exact local
LLDB/debugserver/Python intake remains required. [controller.py](controller.py)
now provides the source-only `prepare` and `run` entry points; it accepts no
unreviewed tool discovery or automatic capability probe. [client.py](client.py) contains the bounded
remote connection and observation loop. It uses synchronous continue operations;
queued process notifications are retained separately and cannot be counted as
extra breakpoint visits. The draft uses documented
[target and module APIs](https://lldb.llvm.org/python_api/lldb.SBTarget.html),
[process memory reads](https://lldb.llvm.org/python_api/lldb.SBProcess.html),
[DWARF type fields](https://lldb.llvm.org/python_api/lldb.SBType.html), and
[file specifications](https://lldb.llvm.org/python_api/lldb.SBFileSpec.html).
Those references support the proposed API route; they do not establish the API
or debug-type behavior of a locally selected tool.

The existing common mutex must remain held from input replay through final
cleanup. [owned_processes.py](owned_processes.py) supplies a concrete draft
boundary: directly spawn the unchanged subject with Darwin
`POSIX_SPAWN_START_SUSPENDED`, pre-register its PID slot, and record its kernel
birth, separate process group and stopped state before creating the debugger.
The SDK declares this flag in `sys/spawn.h:60`, with the opaque spawn handles and
file-action API in `spawn.h`. Debugserver's normal
[Darwin launch implementation](https://github.com/llvm/llvm-project/blob/main/lldb/tools/debugserver/source/MacOSX/MachProcess.mm)
also starts suspended before `PT_ATTACHEXC`.

The owner then creates an explicit debugserver child with
`[debugserver, private_unix_socket, --attach=owned_subject_pid]`; it accepts no
external PID. The separate LLDB client connects only to that owned endpoint.
The upstream [debugserver command interface](https://github.com/llvm/llvm-project/blob/main/lldb/tools/debugserver/source/debugserver.cpp)
supports the socket-path/attach form, and the
[LLDB connection implementation](https://github.com/llvm/llvm-project/blob/main/lldb/source/Host/posix/ConnectionFileDescriptorPosix.cpp)
supports `unix-connect`. Exact locally retained tool compatibility remains an
intake requirement; these upstream sources are not a native capability receipt.

This route owns the inferior before any debugger transport operation, so a hung
attach cannot lose an unreported subject PID. The journal retains all three
direct children until cleanup. It monitors their separate groups and allows only
the known tracer's temporary subject-parent transition. Every failure must kill
and reap the owned set; normal completion requires the same group/identity and
exit proof. The source component reuses the reviewed kernel and atomic lifecycle
interfaces, without changing their frozen implementation. The initial stopped
state is recorded separately; only subsequent registered breakpoint stops enter
`Trace.stopped`. The fresh stdout, stderr, debugger and event files stay separate.
Failed normal closure escalates to forced cleanup. Each phase has a five-second
bound, for at most ten additional seconds; the outer owner must reserve both.
A sampled RSS read may retry at most twice only when the same subject's exact
birth/group identity shows the permitted controller/tracer parent transition.
Other kernel failures remain fatal. The pure fault cases cover synthetic
children; actual three-child ownership remains to be exercised.

Preparation consumes an explicitly pinned JSON intake with schema
`julia-entry-debugger-tool-intake-v1` and status
`reviewed-local-debugger-transport-and-api-intake`. That receipt must record zero
executions of the Julia subject, exact physical LLDB/debugserver/scripting-Python
paths and dependencies, capability-evidence file pins, the two module UUIDs,
the matching DWARF/header, a physical working directory and both complete
environments. Its seven named capability fields are defined in `CAPABILITIES`;
they cover the local spawn ABI, owned Unix attach interface, LLDB batch/Python
APIs and settings, UUIDs and CodeInstance fields. No such actual intake exists
yet. Preparation hashes the declared closure under the common mutex and writes
a fresh plan; run reconstructs the same plan before creating any child.

The retained `canary-observation-v2` packet already records CLT
`lldb-1500.0.404.7` / Swift 5.10, the selected LLDB location and its `-P` scripting
resource path. Its `native-observation/prelaunch-modules.json` records runtime
UUID `A9EAD8CA-7573-3B14-8DD6-39BDC818E737`; the same packet binds that image's
bytes to the retained runtime digest. The successful `official-static-io-safe-link-v3`
image-load-command capture records main UUID
`ABB0315D-ABDF-3208-A9E7-97CD2EF84005`. These are reusable static observations,
subject to exact receipt and current-tool pin replay; they are not observations
of the future diagnostic process. Both packets are under
`archive/languages/julia-aot/20261012/jobs/`.

The static intake uses one no-subject LLDB batch observation of the
required settings, scripting identity, exact modules, CodeInstance DWARF fields
and retained file-address breakpoints, plus bounded local debugserver interface
help. The selected command interface must support the private Unix endpoint and
`--attach` form. A successful prior attach to this Julia executable is not an
intake prerequisite: the single owned diagnostic is the first test of that
transport. SDK declarations and existing version/location records can be reused.
[intake_probe.py](intake_probe.py) is the source for that static LLDB
observation. It reuses the exact `Trace` constructor and requires an invalid
`target.GetProcess()` before and after inspection. It contains no launch,
connect, attach, resume or target-expression evaluation call. Its JSON preserves
the scripting identity, local API member presence, command results, raw type
fields, required layout, module UUID/file addresses and all breakpoint records.
Process API members are explicitly listed as unexercised; interface presence
does not qualify the later owned transport. Partial metadata and the error are
retained on failure. The outer bounded command must propagate `entry`'s status.

The [second tool capture](intake-run-v2/report.json) completed on October 15,
2026 at 04:07 UTC. Its LLDB process exited zero and retained complete structured
output: both settings, 27 breakpoint locations, the two expected module UUIDs,
Python 3.9.6 and the 128-byte CodeInstance layout. Debugserver's no-argument
usage route retained the Unix-socket attach syntax and exited 1, as expected for
that invocation; the observer's unsuccessful status remains unchanged. Both
processes were reaped and their groups were empty. No Julia process was created.
The first capture's rejected `--help` option and truncated LLDB output remain
preserved. Physical dependency review and the owned diagnostic are separate
remaining steps.

The eventual CLI shape, after that intake has actually been reviewed, is:

```text
<retained-python> -I -S -B <absolute-controller.py> prepare \
  --intake <absolute-reviewed-intake.json> --intake-sha256 <reviewed-digest> \
  --plan <fresh-absolute-plan.json> --output <fresh-absolute-run-directory>
<retained-python> -I -S -B <absolute-controller.py> run \
  --plan <absolute-plan.json> --plan-sha256 <actual-prepared-digest>
```

The owner records separate stdout/stderr for each of the three children,
`owner.jsonl`, `trace.jsonl`, the exact client configuration and LLDB command
file, then report and terminal records. It binds each capture inode before
launch, snapshots all exact bytes after child reaping, replays input pins and
compares the snapshots again before terminal closure. The private socket path
is retained separately; a socket removed by a terminated debugserver is allowed
only after that owned server is a zombie or has been reaped. Unexpected endpoint
replacement fails the capture. LLDB exits explicitly with the client result;
Python script errors cannot silently become a successful CLI exit. Raw-capture
success still leaves application-output and native-owner semantic review open.

The proposed limits and the exact remaining preparation checks are explicit in
the draft. Completion of this bounded capture would still leave full timing,
universal fallback exclusion, serialized-IR removal and chart admission false.
