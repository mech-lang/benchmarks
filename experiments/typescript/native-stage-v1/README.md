# TypeScript strict compilation and native AST capture

This additive source preparation defines two serial owned commands: one direct
TypeScript 7.0.2 compilation of ten retained application sources, then one Node
24.19.0 AST reader for those sources and thirty parser fixtures. It has not run.
No runnable plan, application JavaScript, AST result or benchmark timing is
included. Existing source bundles, compiler configuration and reader remain
unchanged.

[typescript_native_stage.py](../../../tools/qualification/typescript_native_stage.py)
requires the closed [native version observations](../toolchain-v1/native-versions-v1/terminal.json),
the exact four-package receipt, all original source/configuration pins and the
new [reader-v2.mjs](reader-v2.mjs). The controller reuses the frozen generic
process observer: a 30-second deadline per owned command, five-second cleanup,
2 GiB observed process-group RSS, 8 MiB individual native file bound, exact raw
stdout/stderr receipts, direct-child birth identity, reaping and no live group
members. The common timing mutex covers both commands and final reconciliation.
There is no automatic retry or implicit resume.
Termination and hangup signals enter the observer's owned-group cleanup path;
final reconciliation blocks interruptions while writing failure or success
receipts. Staged sources, configuration and package metadata must still match
their original pins after compilation. Artifact snapshots bracket validation,
and final inventory checks retain those exact bytes before rechecking all input
pins and the named/held mutex identity.

The reader's preserved source-counts-v1 predecessor has SHA-256
`5376ab0a67541801ec3265d213f3fbb884101a49a15945638d8021600c36e219`.
The additive change introduces the version-2 input schema and child lifecycle
records; the AST extraction and closed filesystem remain as originally authored.

The retained compiler executable is
`../toolchain-v1/.build/packages-v1/node_modules/@typescript/typescript-darwin-arm64/lib/tsc`.
The API is loaded from the sibling `typescript/dist/api/sync/api.js`, with
`typescript/dist/ast/index.js` and the complete retained package closure.
`@types/node` 24.19.2 and its `undici-types` 7.24.6 dependency remain compiler
inputs. Compilation uses a fresh exact copy of all ten `.ts` files, the original
`tsconfig.json` and CommonJS `package.json`. Only the command-line type-root
location and file-inventory reporting are supplied separately:

```text
<retained-tsc> --project <fresh-project>/tsconfig.json --typeRoots <retained-node_modules>/@types --pretty false --listFiles --listEmittedFiles --incremental false
```

Strict/noEmitOnError and the complete original source configuration remain in
effect. `useDefineForClassFields:false` is retained; its actual compiler-option
compatibility remains a native gate. A rejected option or type error is retained
as failure. No JavaScript-only or ignored-error fallback is allowed. Success
requires exactly ten JavaScript files and ten source maps, each map retaining
the original typed source and exact source path. The compiler's full source-file
list must contain only the ten copied applications and pinned declaration files.
Emitted JavaScript is retained for independent review; it is never evaluated by
this stage.

The installed TypeScript API source confirms the existing reader's snapshot,
source, diagnostics, UTF-16 span and virtual-filesystem methods. It also exposes
an unreferenced compiler child. Its `SyncRpcChannel.close()` sends SIGTERM but
does not wait for close. The additive reader records the exact child PID,
parent, executable and argv, references it while active, calls the original
API close and awaits matching exit/close events within five seconds. A clean
zero exit or the API's expected SIGTERM is retained; a different signal, missing
close or error fails. The outer observer independently requires the Node process
group to be empty before reaping Node. No API package is patched.

The reader receives a closed virtual parse-only project with noEmit, noLib,
noResolve and no automatic type packages. The controller validates forty source
records, two expected parse rejections, exact source bytes, UTF-16 slices,
connected parent/child ownership and role links. This records transport evidence;
independent transport review and the canonical owner projection are still
required. Types, parameter properties and source punctuation are not erased or
replaced by emitted-JavaScript counts.

Header-only Mach-O inspection records vendor install names. Node links
CoreFoundation, Security, libc++ and libSystem; the compiler links libSystem,
libresolv, CoreFoundation and CoreServices. No nonvendor install name or rpath
was found in those headers. This is a static boundary observation, not a newly
qualified complete runtime dependency closure. The future locked prepare checks
the complete retained file pins and package inventories, with a minimal explicit
environment and eight Go/Node worker-pool slots.

The eventual commands use the retained Python with `-I -S -B -u`:

```text
typescript_native_stage.py prepare --plan <fresh-absolute-plan.json> --output <fresh-physical-absolute-output>
typescript_native_stage.py run --plan <reviewed-absolute-plan.json> --plan-sha256 <reviewed-sha256>
```

Compiler output, child lifecycle, application correctness, required work,
canonical/formatted counts and timing are separate gates. This stage leaves
conformance, required-work, runtime-closure, transport and chart admission false,
and both source counts null. The independent 149-case shared corpus is reserved
for a later bounded execution stage using the reviewed emitted programs.
