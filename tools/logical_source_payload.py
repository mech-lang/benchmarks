"""Bind compact logical-owner measurements to exact browser application scopes.

This validates saved proof metadata and source hashes. It never parses input,
recounts native syntax, launches a runtime, or sends native/source trees to JS.
"""
from pathlib import Path
import hashlib
import json
from source_metrics import metadata_for
from clojure_logical_extensions import bind as bind_clojure_extension

ROOT = Path(__file__).resolve().parents[1]
V2 = Path('experiments/source-normalization/v2/qualification.json')
CLOJURE = Path('experiments/source-normalization/clojure-v1')
V2_POLICY = 'logical-source-owners.v2-python-julia'
CLOJURE_POLICY = 'logical-source-owners.clojure-v1'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def require(value, message):
    if not value:
        raise ValueError('Invalid qualified logical source units: ' + message)


def load_reports(root=ROOT):
    root = Path(root)
    paths = dict(v2=V2, clojure=CLOJURE/'qualification.json', inputs=CLOJURE/'inputs.json',
                 review=CLOJURE/'independent-review.json', policy=CLOJURE/'policy.json')
    return {name: (root/path).read_bytes() for name, path in paths.items()}


def project(text, spans):
    lines = text.splitlines(keepends=True); excluded, previous = set(), 0
    for span in spans:
        a, b = span['start'], span['end']
        require(type(a) is int and type(b) is int and previous < a <= b <= len(lines), 'invalid embedded support range')
        previous = b; excluded.update(range(a, b + 1))
    return b''.join(bytes(c if c in (10, 13) else 32 for c in line.encode()) if number in excluded else line.encode()
                    for number, line in enumerate(lines, 1))


def bind(catalog, catalog_raw, reports, root=ROOT):
    root = Path(root); digest = sha(catalog_raw)
    require(json.loads(catalog_raw) == catalog, 'catalog bytes differ')
    docs = {name: json.loads(raw) for name, raw in reports.items()}
    programs = {**catalog.get('program_inventory', {}), **catalog['programs']}
    profiles, policies = {}, {}

    def source_parts(row):
        parts = []
        for source_hash in row['files']:
            source = catalog['files'][source_hash]; raw = source['code'].encode()
            require(sha(raw) == source_hash, 'source hash differs: ' + row['key'])
            meta, role, included = metadata_for(row, source_hash, source)
            require(meta.get('code', source['code']) == source['code'] and meta.get('sha256', source_hash) == source_hash,
                    'source override differs: ' + row['key'])
            spans = meta.get('support_line_ranges', [])
            parts.append(dict(source_sha256=source_hash, role=role, included=included,
                              support_line_ranges=spans, projection=project(source['code'], spans) if included else None))
        return parts

    v2 = docs['v2']
    require(v2.get('schema') == 'benchmark-source-normalization.v2' and v2.get('catalog_sha256') == digest, 'v2 report/catalog drift')
    require(v2.get('policy', {}).get('id') == V2_POLICY and v2['policy'].get('status') == 'native-qualified-exact-source-subset', 'v2 policy differs')
    require(all(v2.get(key) is False for key in ('input_evaluation', 'macro_expansion', 'lowering', 'canonical_fields_changed', 'source_bytes_changed')),
            'v2 source/evaluation scope differs')
    require(set(v2.get('tool_pins', {})) == {'tools/logical_source_units.py', 'tools/julia_source_tree.jl'}, 'v2 producer pin inventory differs')
    for path, expected in v2['tool_pins'].items():
        require(sha((root/path).read_bytes()) == expected, 'v2 producer tool differs: ' + path)
    expected = {key for key, row in programs.items() if row['language'] in ('python', 'julia', 'julia-aot')}
    require(set(v2['profiles']) == expected, 'v2 profile coverage differs')
    used_sources = set()
    for key in sorted(expected):
        row, qualified = programs[key], v2['profiles'][key]
        require(qualified.get('status') == 'qualified-exact-source-native-owners' and qualified.get('policy') == V2_POLICY
                and qualified.get('language') == row['language'] and qualified.get('benchmark') == row['benchmark']
                and qualified.get('retained_loc') == row['loc'], 'v2 profile identity/count differs: ' + key)
        sources, total = [], 0
        for part in source_parts(row):
            if not part['included']:
                continue
            projection_hash = sha(part['projection']); evidence = v2['sources'].get(projection_hash, {})
            require(evidence.get('accepted') is True and evidence.get('source_sha256') == projection_hash
                    and evidence.get('full_source_sha256') == part['source_sha256']
                    and evidence.get('support_line_ranges') == part['support_line_ranges']
                    and evidence.get('coverage', {}).get('unowned_significant_tokens') == 0,
                    'v2 application projection differs: ' + key)
            count = evidence.get('logical_loc')
            require(type(count) is int and count >= 0 and sum(owner['units'] for owner in evidence['owners']) == count, 'v2 owner total differs')
            for owner in evidence['owners']:
                a, b = owner['start'], owner['end']
                require(type(owner['units']) is int and owner['units'] >= 0 and 0 <= a <= b <= len(part['projection'])
                        and sha(part['projection'][a:b]) == owner['source_sha256'], 'v2 owner/source span differs')
            sources.append(dict(source_sha256=part['source_sha256'], application_projection_sha256=projection_hash,
                                application=count, support_line_ranges=part['support_line_ranges']))
            used_sources.add(projection_hash); total += count
        require(qualified.get('sources') == [s['application_projection_sha256'] for s in sources]
                and qualified.get('logical_loc') == total, 'v2 profile sum differs: ' + key)
        profiles[key] = dict(status='qualified', application=total, submitted=None, excluded_support=None,
                             policy=V2_POLICY, sources=sources)
    require(used_sources == set(v2['sources']), 'v2 source inventory differs')
    policies[V2_POLICY] = dict(id=V2_POLICY, report_path=V2.as_posix(), report_sha256=sha(reports['v2']),
        definition='Native Python AST / Julia syntax owners; exact application projections only.',
        native_parsers='CPython3.14.8 AST/tokenize; Julia1.13.1 Base.JuliaSyntax',
        scope='Application logical units only; submitted/excluded logical totals unavailable.',
        evidence_path='experiments/source-normalization/v2/README.md')

    clj, inputs, review, policy = (docs[name] for name in ('clojure', 'inputs', 'review', 'policy'))
    extension = bind_clojure_extension(catalog, catalog_raw, root)
    require(clj.get('schema') == 'clojure-logical-source-qualification.v1' and clj.get('policy') == CLOJURE_POLICY
            and clj.get('status') == 'native-qualified-exact-source-subset' and clj.get('canonical_changed') is False,
            'Clojure report status differs')
    require(inputs.get('policy') == CLOJURE_POLICY
            and clj.get('inputs_sha256') == sha(reports['inputs']), 'Clojure input/catalog drift')
    if inputs.get('catalog_sha256') != digest:
        require(extension is not None and extension.get('catalog_sha256') == digest
                and extension.get('base_inputs_sha256') == sha(reports['inputs'])
                and extension.get('base_report_sha256') == sha(reports['clojure'])
                and extension.get('base_review_sha256') == sha(reports['review']), 'Clojure narrow current source projection missing')
    require(review.get('decision') == 'qualified-exact-source-subset' and policy.get('id') == CLOJURE_POLICY, 'Clojure policy review missing')
    approved = review['approved_source_scope']
    require(approved.get('policy') == CLOJURE_POLICY and approved.get('policy_sha256') == sha(reports['policy'])
            and approved.get('tool_sha256') == sha((root/'tools/clojure_logical_source_units.py').read_bytes())
            and approved.get('helper_sha256') == sha((root/CLOJURE/'capture.clj').read_bytes())
            and approved.get('tests_sha256') == sha((root/CLOJURE/'test_replay.py').read_bytes())
            and approved.get('native_capture_sha256') == sha((root/CLOJURE/'native-capture.json.gz').read_bytes())
            and approved.get('source_proof_sha256') == sha(encoded(clj['outcomes'])), 'Clojure reviewed source proof drift')
    require(review['current_projection'].get('report_sha256') == sha(reports['clojure'])
            and review['current_projection'].get('inputs_sha256') == sha(reports['inputs']), 'Clojure reviewed projection drift')
    current = {key for key, row in programs.items() if row['language'] == 'clojure'}
    expected = set(inputs['programs'])
    require(set(clj['programs']) == set(inputs['programs']) == expected
            and review['current_projection'].get('programs') == sorted(expected), 'Clojure profile coverage differs')
    require(current == expected | set(extension['profiles'] if extension else {})
            and not expected.intersection(extension['profiles'] if extension else {}), 'Clojure exact old/new profile inventory differs')
    for key in sorted(expected):
        row, qualified = programs[key], clj['programs'][key]
        require(qualified.get('status') == 'native-qualified-exact-source-subset' and qualified.get('retained_loc') == row['loc']
                and qualified.get('files') == inputs['programs'][key]['files'], 'Clojure profile status differs: ' + key)
        sources, application, submitted, excluded = [], 0, 0, 0
        parts = source_parts(row)
        require([part['source_sha256'] for part in parts] == [part['source_sha256'] for part in qualified['files']], 'Clojure source bundle differs')
        for part, binding in zip(parts, qualified['files']):
            require(not part['support_line_ranges'] and binding.get('role') == part['role']
                    and binding.get('included_in_application') is part['included'], 'Clojure source partition differs')
            job = inputs['jobs'][binding['job']]; outcome = clj['outcomes'][binding['job']]
            raw = catalog['files'][part['source_sha256']]['code'].encode()
            require(job.get('source_sha256') == part['source_sha256'] and job['text'].encode() == raw
                    and outcome.get('status') == 'native-qualified-exact-source-subset'
                    and outcome.get('coverage', {}).get('unowned_significant_tokens') == 0, 'Clojure source outcome differs')
            count = outcome.get('logical_units'); require(type(count) is int and count >= 0, 'Invalid Clojure count')
            submitted += count
            if part['included']:
                application += count
            else:
                excluded += count
            sources.append(dict(source_sha256=part['source_sha256'], application_projection_sha256=part['source_sha256'] if part['included'] else None,
                application=count if part['included'] else 0, submitted=count, excluded_support=0 if part['included'] else count,
                role=part['role'], support_line_ranges=[]))
        require([qualified.get(field) for field in ('application_logical_units', 'submitted_logical_units', 'excluded_support_logical_units')]
                == [application, submitted, excluded], 'Clojure scoped totals differ')
        profiles[key] = dict(status='qualified', application=application, submitted=submitted, excluded_support=excluded,
                             policy=CLOJURE_POLICY, sources=sources)
        if extension:
            projected = extension['base_profiles'].get(key, {})
            require(projected.get('files') == qualified['files'] and projected.get('retained_loc') == qualified['retained_loc']
                    and [projected.get(field) for field in ('application', 'submitted', 'excluded_support')] == [application, submitted, excluded],
                    'Clojure sealed base/current scope projection differs')
    if extension:
        profiles.update(extension['profiles'])
    policies[CLOJURE_POLICY] = dict(id=CLOJURE_POLICY, report_path=(CLOJURE/'qualification.json').as_posix(),
        report_sha256=sha(reports['clojure']), policy_path=(CLOJURE/'policy.json').as_posix(), policy_sha256=sha(reports['policy']),
        independent_review_path=(CLOJURE/'independent-review.json').as_posix(), independent_review_sha256=sha(reports['review']),
        definition='Native-reader-bound Clojure written form owners; conditional expressions remain expressions, explicit blocks remain visible.',
        native_parsers='Clojure1.12.6 + tools.reader1.6.0; read-eval disabled; no source execution/macroexpand.',
        scope='Application, submitted and excluded-support logical units.', evidence_path=(CLOJURE/'README.md').as_posix())
    if extension:
        policies[CLOJURE_POLICY]['source_extensions'] = dict(proof=extension['extension_proof'], independent_review=extension['extension_review'],
            profiles=sorted(extension['profiles']), projection_path='experiments/source-normalization/clojure-extensions/v1/projection.json')
    metadata = dict(schema='browser-qualified-logical-source-units.v1', catalog_sha256=digest, partial_coverage=True,
        generic_language_certificate=False, default_status='unavailable', policies=policies,
        coverage=dict(qualified_profiles=len(profiles), retained_profiles=len(programs),
                      profiles_by_language={lang: sum(programs[key]['language'] == lang for key in profiles)
                                            for lang in sorted({programs[key]['language'] for key in profiles})}),
        definition='Qualified logical units · partial coverage. Exact native parse/owner policies, separate from formatter lines and retained cohort LOC; no missing-value fallback or universal fairness claim.')
    return metadata, profiles
