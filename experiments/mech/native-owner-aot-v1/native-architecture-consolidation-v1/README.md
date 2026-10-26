# Native architecture consolidation

This study fixes baseline I at `8aafe1e16b50b333d7990dd107e79124405bb71b`,
replacing the handoff’s earlier baseline before measurements. It preserves
the merged pre-911 cleanup and all later #911 integration fixes.

`plan.json` predeclares both complete four-subject schedules, paired analysis,
seed and acceptance policy. `retained-controls.json` verifies the exact W/R
files and winning object, without rebuilding them. No primary observations
have been collected. Final F pins and correctness gates are still required.

`baseline/public-aot.json` records the actual public CLI build of I, its clean
source, compiler/environment/executable pins, and owned process receipt. Its
bytecode and guest object match the retained winning pins. This is not timing
qualification. `baseline/native-tests.json` records 415 actual native passes
and two pre-existing ignores at I. The setup-work diagnostic was already
archived by #929; it is not restored as production instrumentation.

Four representative source/decoded fixtures retain complete flat descriptor
images, bytecode, metadata and guest disassembly. The initial preparation
refactor produces byte-identical objects and metadata for these fixtures;
this is targeted equivalence evidence, not an exhaustive final code audit.

Final correctness, changed-input execution, full guest-code comparison and
the two final timing sessions remain pending. Historical W timings are not
measurements of I or F.
