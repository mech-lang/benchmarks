"""Exact source-owner coverage for the APL tree and measured workspace setup.

The frozen reader is loaded into a private module with two additional, manually
reviewed identities. Its source and the existing nine-source registry stay intact.
Unknown source bytes never receive a physical-line fallback.
"""
import hashlib
import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
READER = HERE / 'apl_retained_source_units.py'
READER_SHA = '78eaba5d88172d9ebcf6890baa5818787f5bd313c9644391f2618262a8c44232'
POLICY = 'apl-binarytrees-workspace-exact-source-owners-with-closers-v1'
SOURCES = {
    'binarytrees-main': {
        'path': 'archive/comparisons/r-apl-uiua-comparison/20261011/sources/apl/binarytrees.compact.apl',
        'sha256': 'd1293d125d2d65940137d2d624402d4931f74d1f031bc2261165ad6663c57e74',
        'canonical_loc': 40, 'physical_loc': 40, 'closers': 3,
    },
    'workspace-setup': {
        'path': 'experiments/apl/binarytrees-workspace-v1/setup.apl',
        'sha256': '3adce52a2aea05cc00ee13e011655749f5a03bc81d37a4ee8eb13c14f227e58c',
        'canonical_loc': 1, 'physical_loc': 1, 'closers': 0,
    },
}


def _load_reader():
    if hashlib.sha256(READER.read_bytes()).hexdigest() != READER_SHA:
        raise ValueError('Frozen APL source-owner reader changed')
    spec = importlib.util.spec_from_file_location('_apl_workspace_owner_reader', READER)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    reader.SOURCES = {identity: (row['sha256'], row['canonical_loc'], row['closers'])
                      for identity, row in SOURCES.items()}
    reader.POLICY = POLICY
    return reader


_READER = _load_reader()


def count_source(source, identity):
    return _READER.count_source(source, identity)


def count_bundle(sources):
    if type(sources) is not dict or set(sources) != set(SOURCES):
        raise ValueError('Both the unchanged tree and measured setup are required')
    counts = [dict(path=SOURCES[identity]['path'], **count_source(sources[identity], identity))
              for identity in SOURCES]
    return {
        'schema': 'apl-binarytrees-workspace-source-count-v1',
        'policy': POLICY,
        'sources': counts,
        'canonical_loc': sum(row['canonical_loc'] for row in counts),
        'original_physical_loc': sum(row['original_physical_loc'] for row in counts),
        'formatted_loc': None,
        'formatted_loc_qualified': False,
        'source_forms': ['compact', 'optimized'],
        'source_form_relationship': 'identical-source-and-command-aliases',
        'distinct_authored_main_sources': 1,
        'distinct_source_bundles': 1,
        'setup_assignment_included': True,
        'native_execution': False,
        'generic_language_certificate': False,
        'full_size_work_qualified': False,
        'full_timing_qualified': False,
        'chart_admission': False,
    }
