#!/usr/bin/env python3
"""Materialize portable bounded inputs and independent expected outputs.

This preparation runs only Python reference/data handling. It never executes
benchmark subjects, compilers, Node, or a JVM, and grants no qualification.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE_READER = 'tools/qualification/elixir_bounded.py'
BASE_READER_SHA = 'b5cc9fbe2847048206771fa4eb13551380f3e3c998f72def77bd37963fbfaa75'
SUPPLEMENT = 'experiments/kotlin/specified-cases-v1'
SUPPLEMENT_PINS = {
    'plan-v1.json': '05661999cad521810653ace36f472cd262b2f508f3d74af20837e17bacca07d0',
    'run-v1/report.json': '90c993aff85bc26ebcee7a59f8f43f02c86186d9a6e1f155155856f99b2a3260',
    'run-v1/terminal.json': '1e8078c6b3accc95294896902c9a47ee96fba78a9364e4abdbca864e0b687f96',
}
REVCOMP_ORACLE = 'experiments/prolog/revcomp-linear-v1/fixtures.py'
REVCOMP_ORACLE_SHA = '0e761400188ce52ec987135fca94975cea41cef8eaac7af5fcc89c4c92f79e4a'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned_module(name, expected, module_name):
    path = ROOT / name
    raw = path.read_bytes()
    require(digest(raw) == expected, 'Changed reference reader: ' + name)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT))


def portable(value):
    if isinstance(value, dict):
        return {key: relative(item) if key == 'path' else portable(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [portable(item) for item in value]
    return value


def collect():
    base = pinned_module(BASE_READER, BASE_READER_SHA, 'bounded_reference_reader')
    evidence = base.Evidence()
    evidence.bind(ROOT / BASE_READER, BASE_READER_SHA)
    cases = []

    def retain(benchmark, row, provenance):
        expected = evidence.bind(row['expected']['path'], row['expected']['sha256'])
        expected_bytes = expected.read_bytes()
        require(digest(expected_bytes) == row['expected']['sha256'],
                'Reference output changed while reading')
        stdin = (evidence.bind(row['stdin']['path'], row['stdin']['sha256']).read_bytes()
                 if row['stdin'] else b'')
        require(not row['stdin'] or digest(stdin) == row['stdin']['sha256'],
                'Reference input changed while reading')
        cases.append(dict(benchmark=benchmark, case=row['case'], n=row['n'],
                          input_kind='stdin' if row['stdin'] else 'integer-argument',
                          input_bytes=stdin, expected_bytes=expected_bytes,
                          validation=row['validation'], expected_exit=0,
                          provenance=provenance))

    for benchmark, rows in base.reference_cases(evidence).items():
        for row in rows:
            retain(benchmark, row, dict(kind='retained-independent-reference',
                                        evidence=portable(row)))
    require(len(cases) == 78, 'Expected 78 base cases')

    saved = {name: evidence.read(ROOT / SUPPLEMENT / name, sha)
             for name, sha in SUPPLEMENT_PINS.items()}
    plan, report, terminal = (saved[name] for name in
                             ('plan-v1.json', 'run-v1/report.json', 'run-v1/terminal.json'))
    require(report['status'] == terminal['status'] ==
            'specified-30-cases-passed-awaiting-work-JIT-and-LOC' and
            report['plan_sha256'] == SUPPLEMENT_PINS['plan-v1.json'] and
            terminal['report_sha256'] == SUPPLEMENT_PINS['run-v1/report.json'] and
            report['qualified_supplemental_cases'] == 30 and report['active'] is None and
            report['integrity_errors'] == report['process_receipt_errors'] == [] and
            terminal['integrity_errors'] == terminal['artifact_errors'] ==
            terminal['process_receipt_errors'] == [], 'Supplement is not closed successfully')
    completed = {(row['id'], row['case']): row for row in report['cases']}
    require(len(completed) == len(report['cases']) == 30, 'Supplement case inventory differs')
    for profile in plan['profiles']:
        if not profile['id'].endswith('-compact'):
            continue
        for row in profile['bounded_cases']:
            saved_case = completed[(profile['id'], row['case'])]
            proof = evidence.read(saved_case['validated'], saved_case['validated_sha256'])
            require(saved_case['status'] == proof['status'] == 'specified-case-output-passed' and
                    proof['id'] == profile['id'] and proof['case'] == row['case'] and
                    proof['reference_evidence'] == row and
                    proof['validation']['reference_match'] is True and
                    proof['validation']['expected_sha256'] == row['expected']['sha256'],
                    'Supplement reference and saved validation differ')
            for key in ('oracle_source', 'retained_independent_oracle'):
                evidence.bind(row[key]['path'], row[key]['sha256'])
            retain(profile['benchmark'], row,
                   dict(kind='retained-independent-supplement', evidence=portable(row),
                        validation_receipt=dict(path=relative(saved_case['validated']),
                                                sha256=saved_case['validated_sha256'])))
    require(len(cases) == 93, 'Expected 93 retained cases')

    oracle = pinned_module(REVCOMP_ORACLE, REVCOMP_ORACLE_SHA, 'revcomp_reference')
    evidence.bind(ROOT / REVCOMP_ORACLE, REVCOMP_ORACLE_SHA)
    oracle.self_check()
    for name, data in oracle.cases():
        row = dict(benchmark='revcomp', case='extended-' + name, n=0,
                   input_kind='stdin', input_bytes=data,
                   provenance=dict(kind='independent-python-byte-oracle',
                                   path=REVCOMP_ORACLE, sha256=REVCOMP_ORACLE_SHA,
                                   oracle_case=name))
        try:
            row.update(expected_bytes=oracle.reference(data), expected_exit=0,
                       validation='exact-complete-bytes')
        except oracle.InvalidNucleotide as error:
            row.update(expected_bytes=None, expected_invalid_byte=error.code,
                       expected_exit='nonzero', validation='language-specific-invalid-iupac',
                       rejection_adapter_qualified=False)
        cases.append(row)
    for benchmark, expected in [('mandelbrot', b'P4\n0 0\n'),
                                ('fannkuchredux', b'0\nPfannkuchen(0) = 0\n')]:
        cases.append(dict(benchmark=benchmark, case='n-0', n=0,
                          input_kind='integer-argument', input_bytes=b'',
                          expected_bytes=expected, expected_exit=0,
                          validation='exact-complete-bytes',
                          provenance=dict(kind='handwritten-empty-workload',
                                          rationale='Zero pixels or zero-element permutation summary.')))
    require(len(cases) == len({(c['benchmark'], c['case']) for c in cases}) == 149,
            'Expected 149 distinct cases')
    require(sum(c['expected_bytes'] is None for c in cases) == 7,
            'Expected seven explicit rejection cases')
    return cases, {relative(path): sha for path, sha in evidence.pins.items()}


def write(output):
    require(not output.exists(), 'Use a fresh output directory')
    cases, pins = collect()
    output.mkdir(parents=True)
    manifest = dict(schema='shared-bounded-workload-corpus-v1',
                    status='reference-data-prepared-subject-execution-pending',
                    generator_sha256=digest(Path(__file__).read_bytes()),
                    native_processes_started=0, subject_executions=0,
                    subject_output_qualified=False, source_work_qualified=False,
                    chart_admission=False, reference_pins=pins, cases=[])
    for source in cases:
        row = {key: value for key, value in source.items()
               if key not in ('input_bytes', 'expected_bytes')}
        directory = output / source['benchmark'] / source['case']
        directory.mkdir(parents=True)
        for key, filename in [('input_bytes', 'stdin.bin'), ('expected_bytes', 'expected.stdout')]:
            data = source[key]
            if data is None:
                continue
            path = directory / filename
            path.write_bytes(data)
            row['stdin' if key == 'input_bytes' else 'expected'] = dict(
                path=str(path.relative_to(output)), sha256=digest(data), bytes=len(data))
        manifest['cases'].append(row)
    manifest.update(case_count=len(cases), success_cases=142, rejection_cases=7)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return dict(cases=149, success_cases=142, rejection_cases=7,
                native_processes_started=0, output=str(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(write(args.output)))
