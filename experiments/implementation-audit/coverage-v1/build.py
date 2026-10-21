#!/usr/bin/env python3
"""Reconcile exact static source reviews without extending native qualification."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CATALOG = ROOT / 'data/benchmarks.json'
BASE = ROOT / 'experiments/implementation-audit/v1/inventory.json'
LANGUAGES = ROOT / 'data/languages.json'
SUPPLEMENTS = (
    ('typescript', ROOT / 'experiments/implementation-audit/remaining-v1/typescript-review.json'),
    ('odin', ROOT / 'experiments/odin/source-review-v1/review.json'),
    ('ocaml', ROOT / 'experiments/ocaml/source-review-v1/review.json'))
UNREVIEWED = 'not-yet-source-performance-reviewed'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=sha(path))


def build():
    base = json.loads(BASE.read_bytes())
    data = json.loads(CATALOG.read_bytes())
    languages = json.loads(LANGUAGES.read_bytes())['languages']
    programs = {**data.get('program_inventory', {}), **data['programs']}
    require(base['canonical_input']['sha256'] == sha(CATALOG)
            and set(base['programs']) == set(programs), 'Base inventory/catalog identity differs')
    source_files = {}
    for record in base['programs'].values():
        for source in record['source_bundle']:
            path = source['path']
            require(path not in source_files or source_files[path] == source['sha256'],
                    'Conflicting retained source identity')
            source_files[path] = source['sha256']
    missing_legacy_paths = []
    for path, digest in source_files.items():
        embedded = data['files'][digest]['code'].encode('utf-8')
        require(hashlib.sha256(embedded).hexdigest() == digest,
                'Catalog source bytes changed: ' + path)
        if (ROOT / path).is_file():
            require(sha(ROOT / path) == digest, 'Retained source file changed: ' + path)
        else:
            missing_legacy_paths.append(dict(path=path, source_sha256=digest,
                retained_representation='data/benchmarks.json files[source_sha256].code; exact UTF-8 hash verified'))
    supplements = {}
    inputs = [pin(path) for path in (Path(__file__), CATALOG, BASE, LANGUAGES)]
    for family, path in SUPPLEMENTS:
        report = json.loads(path.read_bytes())
        inputs.append(pin(path))
        if family == 'typescript':
            require(report['new_native_or_timing_qualification_claimed'] is False
                    and report['canonical_changed'] is False, 'TypeScript static scope changed')
            doc = ROOT / report['document']['path']
            require(sha(doc) == report['document']['sha256'], 'TypeScript review prose changed')
            rows = report['programs'].items()
        else:
            require(report['native_processes_started'] == report['new_timing_samples'] == 0
                    and report['canonical_changes'] is report['chart_admission'] is False,
                    'Supplement cannot grant native/timing admission')
            doc = path.parent / report['findings']
            rows = [(row['program'], row) for row in report['inspected_profiles']]
        inputs.append(pin(doc))
        for key, row in rows:
            require(key in programs and key not in supplements, 'Missing or duplicate reviewed profile')
            record = base['programs'][key]
            require(languages[record['language']].get('family', record['language']) == family,
                    'Supplement language family differs')
            require(row['source_bundle'] == record['source_bundle'], 'Changed source boundary: ' + key)
            for source in row['source_bundle']:
                require(sha(ROOT / source['path']) == source['sha256'], 'Inspected source changed')
            require(not record['ownership']['preserve_upstream_source'],
                    'Supplement must not rewrite protected source-review scope')
            supplements[key] = dict(report=pin(path), document=pin(doc),
                source_sha256_reviewed=[source['sha256'] for source in row['source_bundle']
                                        if source['included_in_application_loc']],
                qualification_scope='Exact-source static inspection only; no native or count qualification.')

    records = {}
    grouped = defaultdict(list)
    for key, record in base['programs'].items():
        ownership = record['ownership']
        protected = ownership['preserve_upstream_source']
        editable = not protected and ownership['classification'] in ('derived-adapted', 'suite-authored')
        status = record['audit']['status']
        supplement = supplements.get(key)
        reviewed = status != UNREVIEWED or supplement is not None
        if supplement is not None and status == UNREVIEWED:
            status = 'source-and-idiom-reviewed-in-supplement; native-candidates-pending'
        family = languages[record['language']].get('family', record['language'])
        row = dict(program=key, language=record['language'], family=family,
            benchmark=record['benchmark'], ownership=ownership['classification'],
            protected_upstream=protected, editable_source_scope=editable,
            source_reviewed=reviewed, source_review_status=status,
            source_bundle=record['source_bundle'],
            base_review_evidence=record['audit'].get('evidence', []),
            supplemental_source_review=supplement,
            new_native_or_count_qualification=False)
        records[key] = row
        grouped[family].append(row)

    def summary(rows):
        editable = [row for row in rows if row['editable_source_scope']]
        bundles = {tuple((source['sha256'], source['role']) for source in row['source_bundle']
                         if source['included_in_application_loc']) for row in editable}
        return dict(profiles=len(rows), protected_upstream=sum(row['protected_upstream'] for row in rows),
            editable_profiles=len(editable), distinct_editable_source_bundles=len(bundles),
            reviewed_editable_profiles=sum(row['source_reviewed'] for row in editable),
            unreviewed_editable_profiles=sum(not row['source_reviewed'] for row in editable),
            unresolved_ownership_profiles=sum(row['ownership'] == 'unknown' for row in rows),
            supplemental_exact_source_profiles=sum(row['supplemental_source_review'] is not None for row in rows))

    return dict(schema='exact-source-review-coverage.v1', inputs=inputs,
        policy='Reconcile the current base inventory with exact supplemental static reviews. A reviewed source is not a qualified native implementation or proof of global optimality.',
        scope='All retained profiles, with protected upstream and unresolved ownership shown separately.',
        summary=summary(list(records.values())),
        retained_source_identities_rehashed=len(source_files),
        missing_legacy_paths_with_verified_catalog_bytes=missing_legacy_paths,
        source_review_statuses=dict(sorted(Counter(row['source_review_status'] for row in records.values()).items())),
        families={family: summary(rows) for family, rows in sorted(grouped.items())},
        programs=records, native_processes_started=0, new_benchmark_samples=0,
        canonical_changed=False, source_counts_changed=False, chart_admission=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build()
    path = HERE / 'coverage.json'
    if args.check:
        require(json.loads(path.read_bytes()) == result, 'Coverage report differs')
    else:
        with path.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps(result['summary']))
