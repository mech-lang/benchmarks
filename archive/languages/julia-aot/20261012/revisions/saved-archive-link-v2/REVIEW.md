# Complete the existing raw harness source closure before Julia's link

The original reviewed link1 stopped at02:15:31 with normal exit1 before any
native command. Worker39106/target39112 attempted/completed lists and native
receipt list are all empty; no link request or output image was created. Its
exact failed outcome is `509e7a79817cd0ef3f4b1b69891e5cedb559c3ea6d3e6d096098f05f80aeacd8`,
durable `9976859a82f6d5af5201b60e2014ad3394f91af83aba61b78401e169fb2ff5a3`.
The preserved closed review verified9,947 paths and mirrored failure/durable
bytes: continuation/jobs/julia-saved-safe-archive-link-v1-closed-review/receipt.json
SHA `8ae2486acb41edf5aff7024797e0beaa38232c7dd7f65d9514a6bd76089b4b8c`.
Every original safe compiler/archive and all earlier native0 receipts remain
unchanged. Link1's worker/review/output/build and its source gate stay frozen.

The source-only v2 is a copy of the accepted v1 worker with three small changes:

1. Before the unchanged strict raw loader, bind four genuine transitive Python
   harness files from the original qualified C3 private-v3 report. That report
   already occurs in the actual archive prerequisite pins with SHA
   `7cb4a25819935f3e15b3c270595efc9df3dbc056982625892abc3b16bef2f20c`.
   Its actual recorded pins3943–3946 are the literal expected values below.
2. Bind the closed failed link1 receipt and hold its closed private lease,
   requiring its normal1/zero-native/empty-attempt evidence before commands.
3. Use fresh v2 output/build/owner paths. The original recorded plan's old
   output is still asserted exactly; only the new binary destination differs.

The exact missing import chain is:

| Original old-host helper | Actual qualified SHA |
| --- | --- |
| r-apl-uiua-comparison/20261011/prepare.py | 27fcf050ed21db40e747f2e8801ca6f227d82f1ea98f8592bba7b10a768109e5 |
| array-comparison/all-20261009/run.py | 8b7f1b408fb5838dc6adc2404bcfa6146e48e770e602fbe78255454f3cacb8c7 |
| compact/run.py | 6926e288a7b9b59b030c9226227df967aa1d92b3e395789467706e2241d987ae |
| nbody/run.py | e907f71b3fdf8fc6f65adc76aab6dfc424811875388c14f0eb2f31e14e9cffcf |

The existing guard's load_harness loads its pinned run.py, which imports the
first helper; that helper loads arrays, arrays loads compact, compact loads
nbody common. Their module bodies initialize paths/constants/environment and
define helpers; native/benchmark/CLI mains are not called. Full source seams
and the original report's four entries were read. The raw loader still requires
every local source path to be pinned and checks raw bytes immediately before
compile. It never accepts an arbitrary new file, cached bytecode or physical
fallback. No original source/receipt/fixture or importer changes.

The original one180-second Clang22 driver compile/link and four60-second image
observations are untouched. This is their first actual execution, because
link1 reached zero commands. Same original driver/object/runtime/flags/rpaths,
same owned command service, normal native0/PGID cleanup/drain, same source
ancestry/pins and common inode79859134 remain. Four closed leases now include
the preserved failed link1. Attempt/failure evidence remains additive.

Success still requires real thin arm64 Mach-O executable, lipo arm64, raw
linked-library/load-command outputs and one `_clbg_entry`; it leaves native
owner, IR removal, fallback closure, runtime AOT and chart admission false.
No Julia compile/runtime, archive read/extract, fixture, benchmark or debugger
is repeated or added. The reviewer must review this exact small diff before freezing
new worker/review hashes and launching the intended five commands once.

```text
BUNDLED_PYTHON -I -S -B -u NEW_REPO/benchmarks/clbg/julia-aot-comparison/20261012/revisions/saved-archive-link-v2/link.py
  --revision official-static-io-safe-link-v2
  --worker-sha256 ACTUAL_V2_SOURCE_SHA --review-sha256 ACTUAL_V2_REVIEW_SHA
  --lipo-sha256 3e7d30871a9740446f33a907b14d28f10ebe6d4e1c146a4c0788308f573a6609
  --otool-sha256 3e7d30871a9740446f33a907b14d28f10ebe6d4e1c146a4c0788308f573a6609
```

These two actual tool hashes are preserved from link1's common-locked capture;
both macOS invocation paths are the same dispatcher bytes. No extra tool
query or fixture gate is needed. Fresh jobs/official-static-io-safe-link-v2
and .build/official-static-io-safe-link-v2 preserve the original failed folders.
