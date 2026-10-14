# Select the existing pinned macOS SDK for the retained Julia link

This build-environment correction follows the actual Clang22 link failure: its baked default SDK26 path does not exist, and
the Darwin linker therefore cannot find `-lm`. No Julia/compiler/archive
stage is repeated. The original driver15 lines, object archive, runtime,
library flags, rpaths and strict raw helper/service/ownership gates stay exact.

Actual failed v2 worker40124/target40131 exited1 normally at02:23:13. Owned
Clang40173 exited1, cleanly reaped; four image commands never started. Complete
raw stderr, actual argv/receipts/request/outcome and input pins are retained in
continuation/jobs/julia-saved-safe-archive-link-v2-closed-review/receipt.json,
SHA `ca573bb7c1f02e21117b9885ca6d3aa3e1cef5b6014efea068d77265280bf6c2`.
Its9,962 verified paths include the unchanged SDK14.4 source/tbd tree already
captured by the original successful compiler/archive ancestry. Failed outcome
is `ad6ef3f94e93cab77c7db683e9d89a34e0003b3ae01eadf5079fbdc2bfb85715`;
durable `c3fd2663c82e586fdddf8c888c04383a91674e9e8c78f30af633bc519e277946`.
V1's earlier zero-command failed source loader and all prior evidence remain
unchanged too.

V3 copies v2 and inserts exactly `-isysroot
/Library/Developer/CommandLineTools/SDKs/MacOSX14.4.sdk` after Clang argv0.
The original recorded archive link plan is still compared byte-for-byte before
this declared SDK addition and the fresh binary output relocation. Link request
now accurately says output_relocation_only=false and records the explicit SDK.
It checks already pinned SDKSettings.json SHA
`45e88fdfde9be16796dbb0f95891d44d47549236ae51d299d535834f5abdfb35`,
whose actual Version is14.4 and CanonicalName macosx14.4. No SDK discovery
command, tool query, download, sysroot install, replacement or permissions change.

Only fresh v3 output/build/owner names plus the closed failed-v2 receipt/lease
are added. The original five commands remain one180-second driver link then
four60-second lipo/otool/nm observations. This repeats the failed link using
the correct existing environment, while every successful Julia compile and
archive command remains reused. Neither earlier link produced a usable binary.
No passed fixture is rerun and no Julia process/workload executes here.

Common inode79859134 covers source/read/hash/native/terminal operations;
all five retained dependency leases and original new-PGID cleanup/drain rules
stay held. Native0 remains mandatory; warnings stay in exact raw stderr.
Success still records a thin arm64 executable and one native entry, while
native owner, actual IR removal, fallback, AOT and chart qualification remain
false pending actual image/runtime evidence. The source diff was reviewed for this environment correction: one corrected
link and four image inspections.

```text
BUNDLED_PYTHON -I -S -B -u NEW_REPO/benchmarks/clbg/julia-aot-comparison/20261012/revisions/saved-archive-link-v3/link.py
  --revision official-static-io-safe-link-v3
  --worker-sha256 ACTUAL_V3_SOURCE_SHA --review-sha256 ACTUAL_V3_REVIEW_SHA
  --lipo-sha256 3e7d30871a9740446f33a907b14d28f10ebe6d4e1c146a4c0788308f573a6609
  --otool-sha256 3e7d30871a9740446f33a907b14d28f10ebe6d4e1c146a4c0788308f573a6609
```

New jobs/official-static-io-safe-link-v3 and .build/official-static-io-safe-link-v3
never overwrite the two actual failed attempts. Further runtime/controller
source needs maintainer review before execution; a successful link alone is not AOT.
