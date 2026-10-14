# GNU APL binary trees: workspace configuration

This source-only packet proposes a bounded qualification of the retained GNU
APL tree program with a larger supported workspace guard. No command in this
packet has run. Native syntax, setting readback, allocation witness, source
counts, full-work qualification and timing admission remain pending.

## Retained failure

[Attempt 075](../../../archive/comparisons/r-apl-uiua-comparison/20261011/uiua-fann-compact-v5/controller_rev2/apl-argv-v1/full-owner/attempts/075-binarytrees-apl-compact.json)
ran the full N=21 input on 2026-10-13, from 01:15:21.251560 to
01:15:28.632197 UTC. It exited zero but produced no stdout and reported
`WS FULL+` at `Make[4]`, before the stretch-tree result. The expected output was
455 bytes. Its 7.161262667-second elapsed observation is a failed attempt,
not an admitted timing or a timeout. The recorded peak process-group RSS was
1,649,776 KiB; the external limit was 10,240 MiB. Resource violation was null,
and the [supervisor receipt](../../../archive/comparisons/r-apl-uiua-comparison/20261011/uiua-fann-compact-v5/controller_rev2/apl-argv-v1/full-owner/attempts/075-binarytrees-apl-compact.supervisor.json)
retains empty cleanup groups and the original qualification rejection.
The optimized label was an execution alias; neither tree label has valid
samples, and its matched Mech control was unmeasured. Completed measurements
for other workloads remain independent of this packet.

## Supported setting and evidence boundary

The retained GNU APL 2.0 source is beneath the `runtime_source_directory` in
[bounded-next-run.json](bounded-next-run.json). Exact source locations are:

| Source | Relevant behavior |
| --- | --- |
| `src/Quad_WA.cc:33,79,118–185` | Default scale is 90%; unavailable `/proc/meminfo` leaves a 3 GiB estimate. |
| `src/Value.cc:196–217` | The workspace guard compares estimated live Value, ravel and interpreter-frame bytes with that estimate times the scale. |
| `src/Workspace.cc:128–165` | Defined-function entry can raise workspace-full from that guard or allocation failure. |
| `src/SystemLimits.def:14–45`, `src/SystemVariable.hh:594–601` | Workspace scale is zero-based row 31 of the system-limit table. |
| `src/SystemVariable.cc:926–943,971,1021–1025` | Indexed assignment accepts scale 45 through 200 and changes only `Quad_WA::WA_scale`. |
| `src/Quad_WA.cc:189–219,306–322` | `--mem` requires Linux proc files; it is unsuitable for this retained macOS build. |
| `src/UserPreferences.cc:566–579`, `src/IO_Files.cc:347` | Repeated `-f` files execute in their queued order. |
| `src/main.cc:632–649` | `--eval` exits after its expressions and cannot be used as a prelude to `-f`. |

The 3 GiB fallback and its 90% guard are a source-supported explanation of the
failure, not an observed readback from attempt 075. Its stderr does not retain
the extended `)MORE` diagnostic needed to distinguish the precise throwing
branch from allocation failure. This packet does not retrofit that evidence.

[setup.apl](setup.apl) sets the supported scale to 200 using the current index
origin. Under the inferred 3 GiB fallback this changes the internal estimated
ceiling from 2.7 GiB to 6 GiB. The runtime binary, subject source, allocator,
reference-count reclamation, numerical primitive policy and external 10 GiB
ceiling remain unchanged. This is an explicitly different runtime
configuration; it must appear in every future profile fingerprint and receipt.
The setup assignment runs inside each complete measured process if a later
full study is approved.

The setup is an authored source file and requires an explicit source-count
owner: its one assignment contributes one canonical unit. It must not be
silently omitted as a command-line option. The unchanged tree source needs
its own canonical owner review; the existing nine-source APL count approval
does not cover it. Diagnostic sources below are separate from that scored
bundle. Formatted LOC remains unavailable.

## Node and lifetime review

The [retained subject](../../../archive/comparisons/r-apl-uiua-comparison/20261011/sources/apl/binarytrees.compact.apl)
constructs a fresh outer three-cell vector in both branches of `Make`, recurses
into both children, and traverses both children in `Check`. Shared empty child
sentinels do not substitute for leaf nodes. The native source route is:

- `Tokenizer.cc:430–434` creates the empty literal; `Parser.cc:280–330`
  collects literal groups before short-primitive folding. The `⊂` folding at
  `Parser.cc:1253–1267` can retain the empty sentinels, but does not rerun
  whole-expression constant collection or fold the outer leaf strand.
- `Prefix.cc:2639–2695` evaluates that strand through `Value::glue`.
  `Value.cc:2146–2236` allocates a new `Value_P` for each resulting strand;
  `Value_P.icc:103–114` constructs a new `Value`. The internal-node strand
  contains the two recursive results and follows the same allocation route.
- `Value.hh:738–771` enables copy-on-write sharing of existing subvalues;
  `PointerCell.cc:31–40,60–69` retains child references. This avoids copying
  entire subtrees and does not merge separately constructed outer nodes.
  `Value.hh:884–895` and `PointerCell.cc:73–86` release unowned values.

The source clears the stretch root before constructing the long-lived tree,
keeps the latter through every temporary-tree loop, and checks it last. The
previous temporary remains live while its replacement is constructed; this
adds memory cost without removing work. At N=21 the stretch tree has 8,388,607
nodes. The long-lived tree plus the two largest consecutive temporary trees
has at most 8,388,605 node containers. The prescribed total is 613,766,494
constructed and traversed nodes, including all leaves, as required by the
[full workload contract](../../../archive/workloads/binarytrees/README.md).

These are source semantics and analytical counts, not measurements of runtime
allocation or proof that the configured full run fits. The retained build has
12 inline cells per Value (`config.h:595`), so each small node carries a whole
Value header and inline storage. The bounded configuration capture must record
the actual `sizeof(Value)` and `sizeof(Cell)` reported by `--cfg`, rather than
adopting an assumed ABI size.

## Bounded next run

The JSON spec fixes five serial commands, their inputs, expected outputs and
limits. It is a source plan, not a prepared or executed controller plan.
Preparation and execution require the existing common timing mutex, including
the exact named inode 79859134. No command may overlap a measured cohort.
Use the existing owned supervisor and fresh process groups, with signal-safe
registration and cleanup. GNU APL's launcher reserves descriptor 3 for program
stdout, so any inherited common-lock descriptor must be promoted to at least
64 before launch and verified as inherited by the native process.

1. Capture retained `--cfg` output, including actual Value/Cell sizes.
2. Execute [readback.apl](readback.apl), setup, and readback again in one fresh
   process; require exact stdout `wa_scale=90\nwa_scale=200\n`. The diagnostic
   opens descriptor 3 in append mode so its second call cannot truncate the
   first result if a supervisor captures to a regular file.
3. Execute [allocation-witness.apl](allocation-witness.apl) after setup. Its
   `Make` and `Check` definitions are byte-identical to the retained subject.
   It holds two separately constructed depth-zero leaves and a depth-two tree,
   expects checks 1, 1 and 7, then releases the roots. System-limit live Value
   deltas must be exactly 1, 2, 9, 2, 1, 0. A preliminary indexed store removes
   the diagnostic counter vector's own copy-on-write transition before the
   baseline. This checks actual node ownership, not just arithmetic output.
4. Run the unchanged complete subject with setup at N=4 (effective maximum 6).
5. Run it at N=10 and compare the saved complete small-output oracle.

Every command needs normal native exit, complete bounded streams, exact source
and runtime bindings, owned child reaping, an empty process group and unchanged
pins. A zero exit code alone is insufficient. Preserve unknown diagnostics as
failures; do not hide a workspace error behind an accepted warning envelope.
The readback and live-count expectations are unexecuted assertions. Any mismatch
blocks qualification and is investigated from retained receipts without an
automatic retry or a weaker oracle.

Only after those native results and the complete node/lifetime source review
establish required work may a separate full study be prepared: three fresh
N=21 subject processes and three matched Mech controls. Keep the existing
14,400-second ceiling and 10 GiB external RSS limit. One distinct APL source
must not become two native observations through its old compact/optimized
alias. Preserve attempt 075 and all valid earlier measurements unchanged.

## Owned bounded controller

[apl_workspace_bounded.py](../../../tools/qualification/apl_workspace_bounded.py)
implements the five-command stage. Its source and
[small fault tests](../../../tools/qualification/test_apl_workspace_bounded.py)
are prepared; no native plan or APL result exists. It reuses the frozen
`kotlin_bounded_v2` kernel identity, group/RSS monitor, bounded failure drain and
signal masking, plus the reviewed Julia static Mach-O dependency reader. Its
local observer separates the exact command working directory from fresh capture
directories and uses actual `DEVNULL` stdin. The controller monitors each native
group directly; it creates no sampler child.

The timing mutex is duplicated to a descriptor of at least 64 before locking.
That exact descriptor is included in `pass_fds`, checked in child setup, and
held until all groups are empty, every direct child is reaped and the terminal
receipt is written. Each process receives the specified 30- or 60-second
deadline, a five-second cleanup deadline, a 10 GiB group-RSS ceiling and 1 MiB
stream limits. A failed stream may retain at most one extra 64 KiB read chunk
for diagnosis; such a capture cannot pass. The first failure stops the stage.
An already exited child may reach the first kernel observation before any live
RSS reading. Its observed peak is recorded as `null`, with
`live_rss_observation_obtained=false`; zero is not reported as measured memory.
All RSS observations are samples: `rss_observation_complete` and
`memory_usage_qualified` remain false, and unobserved peaks are not proven below
the external guard. Exact outputs, normal exit, owned reaping and empty groups
remain mandatory even for these short commands.

Configuration output is matched against the complete retained
`UserPreferences::show_configure_options` grammar and recorded build version.
Actual Value, Cell and header sizes must be positive and mutually consistent.
Every other stderr stream must be empty; no warning filter is installed. All
five stdout contracts remain those in the source specification.

Preparation pins the runtime, launcher, shell/`dirname`, declared non-OS Mach-O
dependencies, exact source inputs and controller dependencies. Existing system
preferences are pinned; absent system/private-home preference paths and loader
candidates must remain absent. This is static dependency evidence, not an actual
loaded-image inventory. Finalization replays input pins and exact per-command
artifact snapshots, binds the serialized result ledger, and rechecks the mutex
before writing a terminal receipt. Required-work, source-count, full-timing and
chart gates stay false pending independent review.

Once the common mutex is free, prepare with the retained Python and physical
absolute paths:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/apl_workspace_bounded.py prepare --plan /private/tmp/mech-benchmark-completion/experiments/apl/binarytrees-workspace-v1/plan-v1.json --output /private/tmp/mech-benchmark-completion/experiments/apl/binarytrees-workspace-v1/bounded-run-v1
```

Independent review of that saved plan must precede `run --plan` with the same
path and `--plan-sha256` set to its actual digest. No automatic retry, full N=21
command or later measurement is authorized by this bounded plan.
