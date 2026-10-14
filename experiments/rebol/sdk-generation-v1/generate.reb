Rebol [Title: "Generate vendor SDK from the exact retained Builder spec"]

ensure: func [condition message [string!]] [unless condition [cause-error 'script 'invalid-arg message]]
ensure all [block? system/options/args 3 = length? system/options/args] "Three SDK arguments required"
sdk-raw-spec: to file! system/options/args/1
sdk-copy: dirize to file! system/options/args/2
sdk-evidence: dirize to file! system/options/args/3
sdk-original-root: %/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg/rebol-comparison/20261013/.build/sdk-builder-spec-v1/source-copy/

ensure all [system/version/1 = 3 system/version/2 = 22 system/version/3 = 1 system/platform = 'macOS] "Wrong subject runtime"
sdk-original: load sdk-raw-spec
ensure map? sdk-original "Builder output must load as a map"
ensure all [
    sdk-original/name = "rebol3-bulk-macos-arm64"
    sdk-original/version = 3.22.1
    sdk-original/product = 'Bulk
    sdk-original/compiler = 'clang
    sdk-original/arch = 'arm64
    sdk-original/os = 'macos
    sdk-original/sys = 'darwin
    sdk-original/vendor = 'apple
    sdk-original/platform = 'macOS
    sdk-original/root = sdk-original-root
    sdk-original/source = %src/
    sdk-original/stack-size = 4194304
    empty? sdk-original/gits
    empty? sdk-original/post-build
    empty? sdk-original/boot-host-files
] "Retained selected spec semantics changed"
foreach [sdk-field sdk-count] [
    files 212 core-files 243 host-files 18 mezz-base-files 7
    mezz-sys-files 6 mezz-lib-files 76 mezz-prot-files 8 boot-host-files 0
] [
    sdk-list: select sdk-original sdk-field
    ensure all [block? sdk-list sdk-count = length? sdk-list] "Selected source array changed"
    foreach sdk-file sdk-list [ensure file? sdk-file "Source array contains non-file data"]
]
; Preserve the complete native readback, including untouched recipe templates.
save sdk-evidence/native-original-spec.reb sdk-original
sdk-relocated: copy/deep sdk-original
sdk-relocated/root: sdk-copy
foreach sdk-field [files clean] [
    sdk-list: select sdk-relocated sdk-field
    forall sdk-list [
        sdk-file: first sdk-list
        ensure same? sdk-file find sdk-file sdk-original-root "Uncontained absolute SDK file"
        sdk-list/1: join sdk-copy skip sdk-file length? sdk-original-root
    ]
]
ensure same? sdk-relocated/entitlements find sdk-relocated/entitlements sdk-original-root "Uncontained entitlements"
sdk-relocated/entitlements: join sdk-copy skip sdk-relocated/entitlements length? sdk-original-root
ensure string? sdk-relocated/shared "Unexpected shared search path"
replace/all sdk-relocated/shared to string! sdk-original-root to string! sdk-copy
save sdk-evidence/generation-spec.reb sdk-relocated

; Vendor source bytes remain unchanged. This child-local call wrapper records
; the two written OS-query routes and rejects the fallback release-file shell.
; It makes no assertion about independent kernel post-exec image observation.
sdk-call-events: copy []
sdk-native-call: :call
unprotect 'call
call: func [command [string!] /output out /error err /shell /wait /local status event] [
    ensure all [output error shell wait find ["sw_vers -productVersion" "ldd --version"] command] "Unreviewed vendor shell route"
    event: make map! reduce ['command command 'started now/precise]
    append/only sdk-call-events event
    save sdk-evidence/os-query-events.reb sdk-call-events
    status: sdk-native-call/output/error/shell/wait command out err
    put event 'exit-status status
    put event 'stdout copy out
    put event 'stderr copy err
    put event 'finished now/precise
    save sdk-evidence/os-query-events.reb sdk-call-events
    status
]

change-dir join sdk-copy %make/
sdk-failure: try [do/args %pre-make.r3 to-local-file sdk-evidence/generation-spec.reb]
if error? sdk-failure [probe sdk-failure quit/return 1]
ensure 2 = length? sdk-call-events "Expected both vendor OS-query observations"
ensure all [sdk-call-events/1/command = "sw_vers -productVersion" sdk-call-events/1/exit-status = 0
            sdk-call-events/2/command = "ldd --version"] "Vendor OS-query sequence changed"
save sdk-evidence/generator-completed.reb reduce [
    'runtime system/version 'platform system/platform 'original-spec sdk-raw-spec
    'copy sdk-copy 'stages 6 'extension-built false 'chart-admission false
]
quit/return 0
