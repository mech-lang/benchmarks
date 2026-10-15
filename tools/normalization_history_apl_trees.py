"""Add the APL nine-to-ten coverage boundary to the retained history validator.

Existing adapters and their original identities are loaded unchanged. The new
boundary has no coordinate rebase; it binds the added samples and aggregate.
"""
import hashlib
import importlib.util
from pathlib import Path

PARENT_SHA = '67d252c4c8ae7435b7a4f5ac220ca1974436046871618d5898281de4b3b27683'
# Exact reviewed publication leaf, retained in the tested-source transfer record.
# The original producer and its already prepared plan do not depend on this leaf.
PUBLICATION_SHA = 'c3ae7260e5b3ec345b58e814bafb586d6ee3d2d82508bc553c0fea685463e456'


def attach(parent, publication):
    p = publication
    require = parent.require
    require(p.AUDIT not in parent.ADAPTERS, 'APL tree history adapter already installed')

    def validate(root, audit, before, after):
        require(audit['schema'] == 'apl-workspace-tree-catalog-admission-v1'
                and audit['status'] == 'prepared-qualified-six-observation-cohort'
                and audit['language'] == 'apl' and audit['normalizations'] == [], 'Wrong APL tree boundary')
        candidate = parent.strict_json(parent.checked(root, audit['candidate']))
        p.validate_candidate(candidate)
        for field in ('report','source_counts','source_work','runtime_metadata_basis','reconciliation'):
            require(candidate[field] == audit[field], 'APL tree evidence reference changed')
        review = parent.strict_json(parent.checked(root, candidate['reconciliation']))
        sources = {digest:parent.checked(root,dict(path=path,sha256=digest)) for path,digest,_,_ in p.BUNDLE}
        counts, work, runtime = (parent.strict_json(parent.checked(root,candidate[field]))
                                for field in ('source_counts','source_work','runtime_metadata_basis'))
        references = {key:candidate[key] for key in ('report','source_counts','source_work','runtime_metadata_basis',
                                                    'reconciliation','consumer_sources','native_cohort')}
        require(p.build_candidate(review,sources,counts,work,runtime,references) == candidate,
                'Candidate does not reproduce from its exact saved independent evidence')
        for ref in candidate['consumer_sources'].values():
            parent.checked(root,ref)
        for name, ref in candidate['native_cohort'].items():
            require(p.public_ref(review['references'][name]) == ref, 'Native cohort reference differs')
            parent.checked(root,ref)
        report = parent.strict_json(parent.checked(root,candidate['report']))
        require(report['status'] == 'complete' and report['active'] is None
                and report['pins_unchanged_at_end'] is True and len(report['attempts']) == 6
                and report['qualified_samples'] == report['full_performance_runs'] == 6,
                'Complete successful native producer required')
        for key, profile in review['profiles'].items():
            recorded = report['programs'][key]
            require(recorded['samples_seconds'] == profile['samples_seconds']
                    and recorded['median_seconds'] == profile['median_seconds'], 'Saved producer sample identity differs')
        # This pure replay changes no runtime or evidence state. Dummy language
        # metadata is sufficient because it affects only the separate document.
        expected, _, expected_audit = p.build_publication(before,dict(languages={'apl':{}}),candidate,audit['candidate'])
        require(expected == after and expected_audit == audit, 'APL tree publication differs from exact replay')
        additions = dict(programs={p.SUBJECT},program_inventory={p.SUBJECT,p.ALIAS})
        return additions, ({'apl'} if not any(r['lang'] == 'apl' for r in before['reference_summary']) else set())

    parent.ADAPTERS = dict(parent.ADAPTERS, **{p.AUDIT:validate})
    return parent


def load():
    root = Path(__file__).resolve().parent
    modules = []
    for name,path,expected in (
            ('apl_tree_previous_history',root/'normalization_history_v2.py',PARENT_SHA),
            ('apl_tree_publication',root/'qualification/apl_workspace_publication.py',PUBLICATION_SHA)):
        if expected is None:
            raise ValueError('APL tree history source draft is not frozen for execution')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Reviewed APL tree history dependency changed: '+str(path))
        spec = importlib.util.spec_from_file_location(name,path)
        module = importlib.util.module_from_spec(spec)
        exec(compile(raw,str(path),'exec'),module.__dict__)
        modules.append(module)
    return attach(*modules)


def historical_view(root, data):
    return load().historical_view(root,data)
