"""Pure contract for one proposed unchanged-main N4 tree observation.

The caller uses the unchanged primitive-fixtures-v2 adapter.observation parser
on complete retained sidecar bytes, and independently checks all source/input
pins, normal owned process closure, resource limits and exact file membership.
This validator does not load a runtime, parse an arbitrary Rebol program or
qualify the full-size benchmark. No actual observation is supplied here.
"""

CORPUS_SHA256 = '92767a167dafd97745361221cd5a9fe04a2388ba6be7f591756f6153ab3895f1'
CORPUS_CASE = ('binarytrees', 'n-4')
EXPECTED_STDOUT = (
    b'stretch tree of depth 7\t check: 255\n'
    b'64\t trees of depth 4\t check: 1984\n'
    b'16\t trees of depth 6\t check: 2032\n'
    b'long lived tree of depth 6\t check: 127\n'
)
EXACT = {
    'schema': 'rebol-binarytrees-work-observation-v1',
    'main-n': 4, 'main-maximum-depth': 6,
    'nodes-before': 127, 'leaves-before': 64, 'internal-before': 63, 'identity-pairs-before': 8001,
    'nodes-after': 127, 'leaves-after': 64, 'internal-after': 63, 'identity-pairs-after': 8001,
    'check-before': 127, 'check-after': 127,
    'fresh-leaf-calls': 2, 'fresh-leaves-distinct': True,
    'fresh-leaf-mutation-isolated': True, 'long-root-same': True,
    'discarded-buffer-count': 65536, 'discarded-buffer-capacity': 1024,
    'diagnostic-root-aliases': 1, 'diagnostic-node-lists-during-churn': 0,
    'manual-gc': False, 'gc-policy-changed': False, 'per-tree-frees-observed': False,
    'full-size-work-qualified': False, 'source-work-qualified': False, 'chart-admission': False,
}


def require(value, message):
    if not value:
        raise ValueError(message)


def validate(stdout, stderr, exit_status, observed):
    """Validate a decoded exact sidecar without promoting any admission gate."""
    require(isinstance(stdout, bytes) and isinstance(stderr, bytes), 'Complete byte streams required')
    require(type(exit_status) is int and exit_status == 0 and stderr == b'', 'Normal zero exit and empty stderr required')
    require(stdout == EXPECTED_STDOUT, 'Unchanged bounded N4 stdout differs')
    require(type(observed) is dict and set(observed) == set(EXACT) | {'recycles-before', 'recycles-after'},
            'Exact tree observation fields required')
    for name, expected in EXACT.items():
        require(type(observed[name]) is type(expected) and observed[name] == expected,
                'Tree observation differs: ' + name)
    before, after = observed['recycles-before'], observed['recycles-after']
    require(type(before) is int and type(after) is int and 0 <= before < after,
            'Actual increasing automatic collection counter required')
    return dict(case='binarytrees:n-4', observation_contract_satisfied=True,
                observations=dict(observed), native_process_verified=False,
                runtime_source_equivalence_proven=False, full_size_work_qualified=False,
                source_work_qualified=False, per_tree_frees_observed=False,
                full_timing_qualified=False, chart_admission=False)
