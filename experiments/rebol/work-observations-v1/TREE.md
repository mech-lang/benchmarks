# Rebol bounded tree observation

[binarytrees.reb](binarytrees.reb) is an unexecuted diagnostic around the
unchanged retained binarytrees main at existing bounded input N4. It uses an
ordinary `do` of that exact file; it does not wrap or replace `make-tree` or
`check-tree`. The runtime argv is `-q -s binarytrees.reb 4 /absolute/new-sidecar.reb`.
The first original `system/options/args` element remains `"4"`; `do/args` alone
would set `system/script/args`, which the main's size reader does not use.

The main's ordinary output must remain the complete 143-byte
[shared N4 oracle](../../shared/bounded-corpus-v1/cases/binarytrees/n-4/expected.stdout).
The diagnostic adds no stdout marker and requires empty stderr and normal exit
zero. Its separate sidecar is written only after all observations succeed.

N4 selects maximum depth six. The diagnostic traverses the actual retained
`long-lived` graph, checking 127 two-field blocks, 64 leaves and 63 internal
nodes. It performs all 8,001 pairwise `same?` comparisons, including leaves,
and rejects any shared block. Two additional calls to the actual `make-tree 0`
check independent leaf identities and isolation of a one-field mutation.

The diagnostic clears both extra leaves and its complete node-reference list
before collection observation. It retains one explicitly disclosed root alias
in addition to the main's global `long-lived`. It copies the scalar
`stats/profile/recycles` value before 65,536 ordinary 1,024-byte allocations,
then requires the actual counter to increase without calling `recycle` or
changing collector policy. It verifies that the global root is still `same?`
to that alias, repeats the complete shape/distinctness traversal, and calls the
actual `check-tree` again for 127. The stats object itself is reused by the
runtime, so only the copied integer snapshots are compared.

These observations concern one small graph, its distinct node identities,
two additional leaf calls and survival across observed automatic collection.
The root alias participates in liveness; the diagnostic does not establish
that only the original global root kept the graph alive. Pairwise child checks
before and after establish distinctness, not a retained address log for every
child. Collection counters do not identify which temporary tree or series was
freed. No per-tree freeing, full-size work, full-size timing, runtime/source
equivalence or chart admission follows from this diagnostic.

The retained runtime source supports the proposed observation APIs:
`n-math.c:827–832` dispatches `same?`; `t-block.c:35–43` compares series identity
and index. `sys-base.reb:149–196` and `sys-load.reb:42–57` show ordinary script
binding in the user context. `n-system.c:154–186` supplies the reused stats
object and collector counter; `m-gc.c:670,717–730` increments that counter and
marks roots before sweeping. These files are under the preserved
`sdk-generation-v1/work-v1/source/src` tree. Static API inspection does not
establish native compatibility.

The minimal consumer is [tree_contract.py](tree_contract.py). Its input is the
complete captured stdout/stderr/exit and a sidecar decoded by the unchanged
strict `primitive-fixtures-v2/adapter.py::observation` parser. It requires exact
field membership and types, exact N4 output, graph/identity/mutation results,
an increasing collector counter and explicit false qualification claims.
The additive [three-diagnostic controller](../../../tools/qualification/rebol_work_observations.py)
binds the corpus, wrapper, main, helpers, runtime, extension and parser. Its
tree slot uses the existing owned bounded observer, retains all raw evidence
and rejects extra or missing artifacts; the [stage README](README.md) describes
the required prior approvals and execution limits. This controller is a source
draft: no prepared plan, actual tree capture or successful native review is
supplied. Five focused pure tests are authored in
[test_tree_contract.py](test_tree_contract.py); tests, digest freezing and native
execution remain pending.
