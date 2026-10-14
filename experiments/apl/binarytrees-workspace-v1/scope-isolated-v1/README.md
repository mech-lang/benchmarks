# Scope-isolated binary-tree allocation diagnostics

These two unexecuted diagnostic sources preserve the subject's exact `Make` and
`Check` definitions. They test allocation ownership separately from output checks.
They do not change the benchmark program, runtime, setup, existing plans or saved
outcomes. No native preparation, execution, timing or admission is recorded here.

The [earlier allocation witness](../allocation-witness.apl) reported construction
deltas `1,2,9` and release deltas `4,2,1`; its exact-output check failed. That result
and its [closed receipts](../remaining-three-v1/actual-closure-v1.json) remain
unchanged. The saved aggregate counts do not identify the extra values, and the
new oracle does not substitute the observed release values.

The retained interpreter implements `⎕SYL[4;1]` as its global count of APL `Value`
objects. Prefix reductions can leave owning tokens in logically popped stack
slots until those slots are overwritten or their function context is destroyed.
The earlier witness inserts a larger `Check`/formatting expression between the
construction and release readings. This is a concrete source of interference;
exact attribution of its additional values remains unresolved.

In both new sources, all functions are defined before `Probe` runs. A void
initializer creates the empty roots and the seven-element integer result vector.
Each construction/release operation runs in its own void function and returns
before sampling. Each sample uses the same fresh `Record I` function, storing one
integer cell without returning a value. The driver only calls these helpers with
preparsed constant indices. It does not inspect trees, construct a strand, perform
arithmetic or format output during the measurement sequence. Function return
destroys that context's entire prefix-token array, including inactive slots.

`Counts` is initialized within a completed helper and never returned, passed as a
whole value or read during the sequence. The initializer also writes its first
cell before returning: the parser can constant-fold `7⍴0`, and this indexed write
isolates the writable vector from any compiled-literal owner. The indexed
assignment isolates before acquiring its temporary read reference. After the
initializer returns, the writable vector's sole persistent owner is its symbol.
This avoids an additional result-vector copy after the baseline.
Empty literals and numeric indices are parsed before the baseline. A fixed
recorder context and the system-variable read itself contribute the same observer
overhead at every sample.

For [allocation.apl](allocation.apl), each leaf owns one freshly constructed node.
A depth-two tree owns `1 + 2 × (1 + 2 × 1) = 7` nodes, with independent left and
right subtrees. The three roots therefore retain `1`, `2`, then `9` additional
values. Releasing the depth-two root, the first leaf and the second leaf leaves
`2`, `1`, then `0`. Child pointers release their ownership recursively when a
node's final owner disappears. These counts follow the retained construction and
reference-counting code, independently of the earlier observed release deltas.

[zero-allocation-control.apl](zero-allocation-control.apl) changes only the three
construction helpers to assignments of already parsed empty literals and changes
the output label. All six expected deltas are zero. It tests the same recorder,
scope boundaries and release helpers without newly allocated tree nodes. Both
sources print their captured deltas only after `Probe` returns, then reconstruct
two leaves and a depth-two tree in a separate scope for the `1,1,7` output checks.

The proposed exact stdout contracts are:

```text
live_deltas=1,2,9,2,1,0
checks=1,1,7
```

```text
control_deltas=0,0,0,0,0,0
checks=1,1,7
```

The existing exact shutdown-diagnostic disposition remains applicable to a later
reviewed runner; neither source strips or accepts stderr itself. A later bounded
run must require both exact stdout contracts and the existing process-ownership
checks. Failure of either diagnostic leaves the ownership gate unresolved.
Passing these diagnostics alone would not qualify the full subject or timings.

`test_source_contract.py` checks only the fixed source structure and ownership
invariants, including mutations that leak a return value, inline an operation,
insert checking between samples or add allocation to the control. It is not an
APL parser, native test or runtime-allocation observation. Its direct command is:

```sh
python3 -I -S -B experiments/apl/binarytrees-workspace-v1/scope-isolated-v1/test_source_contract.py
```

The accompanying source review binds the new files, preserved failed evidence
and relevant retained interpreter source locations. Native syntax and exact
counter behavior still require the separately reviewed bounded execution.
