"""Bind final tree/regex counts without changing historical ledgers or reviews.

The caller must pin the review and original ledger before calling this helper.
No source is read or counted here. The existing count_source function still
checks actual source bytes against each bound digest and replays its owners.
"""
from copy import deepcopy
from pathlib import Path
import re
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
RULE = 'canonical-source-units-20261012-approved-rule-v2'
BASE = 'archive/languages/rebol/20261013/drafts/private-v1/'
WORKLOADS = ('binarytrees', 'fannkuchredux', 'fasta', 'knucleotide', 'mandelbrot',
             'nbody', 'pidigits', 'regexredux', 'revcomp', 'spectralnorm')
PATHS = {name: BASE + 'sources/' + name + '/main.reb' for name in WORKLOADS}
PATHS.update(binarytrees='experiments/rebol/tree-leaves-v1/main.reb',
             regexredux='experiments/rebol/regex-literals-v1/main.reb',
             fannkuchredux='experiments/rebol/fannkuch-zero-v1/main.reb',
             io=BASE + 'support/clbg_io.reb',
             loader=BASE + 'support/clbg_primitives.reb',
             big=BASE + 'support/clbg_big.reb',
             regex=BASE + 'support/clbg_regex.reb',
             extension='experiments/rebol/extension-api-v2/clbg_primitives.c')
ORIGINAL_REGEX_PATH = BASE + 'sources/regexredux/main.reb'
ORIGINAL_REGEX_SHA = '11ae616b62e40366e4877576363ffc7b70c3861ed6bbdb28ea2ee6c095571674'
CORRECTED_REGEX_SHA = 'e031f15f60e0b53cd565a87a2993efec9fcecc9ea5dcde35f1a6f13576c7f650'
REGEX_SUBSTITUTION = dict(original=ORIGINAL_REGEX_PATH,
    original_sha256=ORIGINAL_REGEX_SHA, counted=PATHS['regexredux'],
    counted_sha256=CORRECTED_REGEX_SHA, original_modified=False,
    count_both_revisions=False)
ORIGINAL_TREE_PATH = BASE + 'sources/binarytrees/main.reb'
ORIGINAL_TREE_SHA = '3b64b0c84db6a25b1dc5b156e4ecf9229be7e0db54f4cbc19692199de4eb8932'
CORRECTED_TREE_SHA = '128df2a9e4c9d5d5be798b07d8ff0ab967c5969ee38746de9c7ee635502574ef'
TREE_SUBSTITUTION = dict(original=ORIGINAL_TREE_PATH,
    original_sha256=ORIGINAL_TREE_SHA, counted=PATHS['binarytrees'],
    counted_sha256=CORRECTED_TREE_SHA, original_modified=False,
    count_both_revisions=False)
FIELDS = ('RULE', 'SOURCES', 'BUNDLES', 'KINDS', 'DECISIONS',
          'ORIGINAL_C', 'CORRECTED_C', 'ORIGINAL_FANN', 'CORRECTED_FANN')
FALSE_GATES = ('runtime_qualified', 'runtime_source_equivalence_proven',
               'compiler_input_qualified', 'required_work_qualified',
               'full_timing_qualified', 'chart_admission')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256_spelling(value):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def bind_ledger(ledger, review):
    """Return copied owners with only the two exact main path/digest substitutions."""
    require(type(review) is dict
            and review.get('schema') == 'rebol15-independent-source-count-review-v1'
            and review.get('status') == 'qualified-exact-fifteen-source-owner-counts'
            and review.get('independent_review') is True
            and review.get('canonical_LOC_admitted') is True
            and all(review.get(gate) is False for gate in FALSE_GATES),
            'Independent count-only admission required')
    require(getattr(ledger, 'RULE', None) == review.get('rule_version') == RULE,
            'Exact approved counting rule required')
    references = review.get('references')
    expected_refs = {
        'proposal': ROOT / 'experiments/rebol/tree-leaves-v1/source-counts-v1/proposal-v1.json',
        'rule': ROOT / 'archive/validation/loc-normalization/20261012/PLAN.md',
    }
    require(type(references) is dict and set(references) == set(expected_refs),
            'Exact proposal and rule references required')
    for name, path in expected_refs.items():
        item = references[name]
        require(type(item) is dict and set(item) == {'path', 'sha256'}
                and item['path'] == str(path) and sha256_spelling(item['sha256']),
                'Count reference identity differs: ' + name)
    source_specs = getattr(ledger, 'SOURCES', None)
    reviewed_sources = review.get('sources')
    require(type(source_specs) is dict and type(reviewed_sources) is dict
            and set(source_specs) == set(reviewed_sources) == set(PATHS),
            'Exact fifteen source identities required')
    require(all(hasattr(ledger, field) for field in FIELDS), 'Original ledger data incomplete')
    bound = SimpleNamespace(**{field: deepcopy(getattr(ledger, field)) for field in FIELDS})
    substitution = review.get('corrected_regex_substitution')
    require(type(substitution) is dict and substitution == REGEX_SUBSTITUTION
            and substitution['original_modified'] is False
            and substitution['count_both_revisions'] is False,
            'Exact corrected regex substitution required')
    original_regex = bound.SOURCES['regexredux']
    require(type(original_regex) is dict and original_regex.get('path') == ORIGINAL_REGEX_PATH
            and original_regex.get('reviewed_source_sha256') in (None, ORIGINAL_REGEX_SHA),
            'Original regex path or approved digest differs')
    require(type(reviewed_sources['regexredux']) is dict
            and reviewed_sources['regexredux'].get('sha256') == CORRECTED_REGEX_SHA,
            'Corrected regex digest differs')
    # Only these reviewed replacements may supersede their exact old approvals.
    # All source-owner decisions are preserved in the private copied view.
    original_regex['path'] = PATHS['regexredux']
    original_regex['reviewed_source_sha256'] = None
    tree_substitution = review.get('corrected_tree_substitution')
    require(type(tree_substitution) is dict and tree_substitution == TREE_SUBSTITUTION
            and tree_substitution['original_modified'] is False
            and tree_substitution['count_both_revisions'] is False,
            'Exact corrected tree substitution required')
    original_tree = bound.SOURCES['binarytrees']
    require(type(original_tree) is dict and original_tree.get('path') == ORIGINAL_TREE_PATH
            and original_tree.get('reviewed_source_sha256') in (None, ORIGINAL_TREE_SHA),
            'Original tree path or approved digest differs')
    require(type(reviewed_sources['binarytrees']) is dict
            and reviewed_sources['binarytrees'].get('sha256') == CORRECTED_TREE_SHA,
            'Corrected tree digest differs')
    original_tree['path'] = PATHS['binarytrees']
    original_tree['reviewed_source_sha256'] = None
    for identity, relative in PATHS.items():
        spec = bound.SOURCES[identity]
        item = reviewed_sources[identity]
        require(type(spec) is dict and spec.get('path') == relative
                and 'reviewed_source_sha256' in spec,
                'Original source path differs: ' + identity)
        require(type(item) is dict
                and set(item) == {'path', 'sha256', 'canonical_loc', 'physical_loc'}
                and item['path'] == str(ROOT / relative)
                and sha256_spelling(item['sha256'])
                and all(type(item[key]) is int and item[key] > 0
                        for key in ('canonical_loc', 'physical_loc')),
                'Reviewed source identity or count differs: ' + identity)
        previous = spec['reviewed_source_sha256']
        require(previous is None or previous == item['sha256'],
                'Existing approved source digest differs: ' + identity)
        spec['reviewed_source_sha256'] = item['sha256']
    require(set(bound.BUNDLES) == set(review.get('bundles', {})) == set(WORKLOADS),
            'Exact ten workload bundles required')
    for workload in WORKLOADS:
        members = (workload, 'io', 'loader', 'extension') + (
            ('big',) if workload == 'pidigits' else ('regex',) if workload == 'regexredux' else ())
        require(tuple(bound.BUNDLES[workload]) == members, 'Original bundle differs: ' + workload)
        expected = dict(members=list(members),
                        canonical_loc=sum(reviewed_sources[name]['canonical_loc'] for name in members),
                        physical_loc=sum(reviewed_sources[name]['physical_loc'] for name in members))
        require(review['bundles'][workload] == expected, 'Reviewed bundle differs: ' + workload)
    return bound
