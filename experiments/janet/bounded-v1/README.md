# Janet bounded-output preparation

This packet prepares all 149 cases of the frozen shared corpus for the ten
active Janet drafts. It is a source/input/dependency identity and output-policy
check, with no Janet process started and no correctness or timing admission.

The schedule includes 142 success cases: complete byte equality for 136 cases
and the retained two-line, nine-decimal energy tolerance for six N-body cases.
The pure [checker](outputs.py) uses integer decimal units at the tolerance
boundary. Its tests cover changed expected bytes, binary padding/truncation,
extra output, nonzero or signalled exits, diagnostics, malformed energy output,
both energy lines and attempts to substitute a different validation policy.
Replaying reference bytes through a checker is a checker test, not an execution
of Janet or qualification of any Janet implementation.

All seven malformed-IUPAC inputs remain in the schedule as capture-only cases.
The current source throws a generic error without identifying the invalid byte.
Its actual diagnostic, partial output, exit behavior and reverse traversal
order need native inspection and a separate Janet-specific rejection adapter.
No nonzero exit by itself can qualify a rejection, and the Scala/TypeScript
language-specific adapters are not used for Janet.

The local runtime, all application sources, the explicit Spork regex module,
GMP binary, source/license metadata and corpus artifacts are hashed in
[plan-v1.json](plan-v1.json). The exact release's retained
[CLI source](../dependencies-v1/runtime-cli/snapshot.json) establishes script
argument handling and the `-R`/`-n` launch options. Source parsing and bytecode
compilation remain in each fresh process. The plan does not claim a complete
native loader dependency closure or a fresh locked version preflight.

Preparation is reproducible without launching Janet:

```sh
python3 experiments/janet/bounded-v1/test_preparation.py
python3 experiments/janet/bounded-v1/prepare.py --check
```

A native controller still needs to register each owned child's birth identity
before `exec`, enforce bounded launch/capture/cleanup, retain complete streams,
and verify group closure while inheriting the unchanged common benchmark mutex.
The failed downloaded-runtime version probe must release that mutex before any
case starts. Preparation neither releases nor replaces the mutex. Native output
validation, required-work review, native source normalization/formatting,
full-size outputs and fresh complete-process timing remain subsequent gates.
