# Account-wide admitted snapshot node witnesses

The shared memory account now exposes a constant-time sum of the canonical node witnesses retained by its admitted snapshot owners. This includes caller-held values outside a native arena, such as prior outputs, without inspecting those values during activation or walking their payloads at every maintained map call.

Each immutable admitted owner holds one non-cloneable witness claim. Ordinary aliases and same-account reuse share the claim; independent imports conservatively add claims even when data storage aliases. Account clones observe the same sum; foreign accounts remain independent. A weak import-registry entry cannot retain a claim after the admitted owner retires. The claim reuses the footprint computed during admission and allocates no separate heap object.

Overflow is rejected before byte admission transfers. Registration/wrapper allocation failure leaves both the node sum and caller reservation intact. Last-owner retirement releases the claim. Successful String ownership transfer removes the canonical snapshot claim; refreezing establishes a new one. Denied transfer keeps the existing claim. The counter installs no new node quota and grants no execution or ownership authority.

The witness claim's inline storage remains part of complete snapshot byte admission. Native work policy43 distinguishes its accounting from policy42. Typed IR30 and ABI15 remain unchanged; preceding policy42 objects are rejected.

Validation passes 536 distinct checks: 322 core, two catalog, 201 native and eleven map integration checks. Three pre-existing native checks remain excluded. Coverage includes Unicode/NUL payloads, same-owner aliases, independent and foreign imports, weak references, retirement, injected registration/wrapper allocation failures, overflow without reservation consumption, shared atomic claims across eight threads, String transfer/refreezing, and existing native call/ownership boundaries.

`core-regressions-v1` retains a closed test failure: the new independent-import case incorrectly used the zero-cost alias reservation planner. The test now reserves independent import storage. `core-regressions-v2` passes all 322 core and two catalog checks. `native-regressions-v1` and `map-contracts-v1` pass their respective 201 and eleven checks. Every subject runs serially under the shared benchmark mutex with bounded process control and complete cleanup records.

This sum covers admitted canonical snapshots only. Raw unadmitted values, private builders and native metadata require separate accounting. Complete generated-caller geometry and retained-map entry/call/exit routing remain unfinished. There are no quantitative benchmark samples or canonical dataset changes, and the normal compiled path still uses canonical maps. Full-input qualification and fresh complete-process timings remain pending.
