#!/usr/bin/env python3
"""Replay retained TypeScript output/update witnesses without native execution."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load():
    spec = importlib.util.spec_from_file_location('typescript_map_replay', HERE / 'qualify.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def replay():
    native = load()
    plan_raw = (HERE / 'native-plan-v1.json').read_bytes()
    plan = json.loads(plan_raw)
    report_path = HERE / 'native-v1/results.json'
    report = json.loads(report_path.read_bytes())
    assert report['status'] == 'passed' and report['plan_sha256'] == digest(plan_raw)
    assert report['quantitative_benchmark'] is False
    assert report['chart_admission'] is False and report['timing_admission'] is False
    verified = {}
    unavailable = []
    for name, expected in plan['pins'].items():
        path = Path(name)
        if not path.exists():
            unavailable.append(name)
            continue
        assert native.sha(path) == expected, name
        verified[name] = expected
    # Missing build dependencies are explicit, never substituted. All owned
    # sources/controller and captured JavaScript must remain available.
    for path in [HERE / 'qualify.py', HERE / 'proposal.json', HERE / 'map-witness.cjs',
                 *native.SOURCES.values()]:
        assert str(path) in verified
    expected_sources = set(native.SOURCES)
    assert {row['label'] for row in report['compilations']} == expected_sources
    for row in report['compilations']:
        assert row['source_sha256'] == native.sha(native.SOURCES[row['label']])
        assert row['emitted_sha256'] == native.sha(HERE / 'native-v1' / (row['label'] + '.js'))
    corpus = native.cases()
    assert {name: digest(raw) for name, raw in corpus.items()} == plan['cases']
    wanted = {(label, name, diagnostic) for label in native.SOURCES
              for name in corpus for diagnostic in [False, True]}
    seen = set()
    histograms = updates = 0
    for row in report['cases']:
        identity = row['label'], row['case'], row['diagnostic']
        assert identity in wanted and identity not in seen
        seen.add(identity)
        label, name, diagnostic = identity
        raw = corpus[name]
        directory = HERE / 'native-v1'
        assert (directory / (name + '.stdin')).read_bytes() == raw
        expected = native.shared.nucleotide_reference(raw)
        assert (directory / (name + '.expected')).read_bytes() == expected
        capture = label + '-' + name + ('-work' if diagnostic else '-plain')
        process = json.loads((directory / capture / 'process.json').read_bytes())
        assert process['exit_code'] == 0 and process['timed_out'] is False
        assert process['remaining_process_group'] is False and process['common_mutex_inherited'] is True
        assert process['common_mutex_inode'] == plan['mutex_inode']
        assert process['quantitative_benchmark'] is False
        assert not (directory / capture / 'stderr.bin').read_bytes()
        actual = (directory / capture / 'stdout.bin').read_bytes()
        assert actual == expected and row['complete_output_matches'] is True
        assert digest(actual) == row['output_sha256'] == process['stdout']['sha256']
        assert process['stdin'] == str(directory / (name + '.stdin'))
        javascript = HERE / '.build/native-v1' / label / 'emitted/knucleotide.js'
        command = [str(native.NODE)] + (['--require', str(HERE / 'map-witness.cjs')] if diagnostic else []) + [str(javascript)]
        assert process['command'] == command
        if diagnostic:
            witness_raw = (directory / (capture + '.maps.json.gz')).read_bytes()
            assert digest(witness_raw) == row['witness_sha256']
            witness = json.loads(gzip.decompress(witness_raw))
            assert witness['target'] == str(javascript)
            expected_work = native.expected_maps(native.bases(raw))
            native.check_witness(witness, expected_work, 'cells' in label)
            assert row['complete_work_matches'] is True and row['map_count'] == 7
            assert row['total_updates'] == sum(len(value['events']) for value in expected_work)
            histograms += 7
            updates += row['total_updates']
    assert seen == wanted and len(seen) == report['output_checks'] == 280
    assert sum(row['diagnostic'] for row in report['cases']) == report['complete_work_checks'] == 140
    rejected = set()
    for row in report['rejections']:
        identity = row['label'], row['case']
        assert identity not in rejected and row['label'] in expected_sources
        assert row['case'] in plan['rejection_cases'] and row['rejected'] is True
        rejected.add(identity)
        directory = HERE / 'native-v1'
        assert native.sha(directory / (row['case'] + '.stdin')) == plan['rejection_cases'][row['case']]
        capture = directory / (row['label'] + '-' + row['case'])
        process = json.loads((capture / 'process.json').read_bytes())
        assert process['exit_code'] != 0 and process['timed_out'] is False
        assert process['remaining_process_group'] is False
        assert process['common_mutex_inode'] == plan['mutex_inode']
        assert b'Invalid nucleotide in THREE record' in (capture / 'stderr.bin').read_bytes()
        assert not (capture / 'stdout.bin').read_bytes()
    assert len(rejected) == report['rejection_checks'] == 12
    return dict(schema='typescript-complete-work-replay.v1', status='passed',
        native_plan_sha256=digest(plan_raw), native_report_sha256=native.sha(report_path),
        output_checks=len(seen), complete_histograms=histograms,
        ordered_updates_reconciled=updates, rejections=len(rejected),
        available_pins_verified=len(verified), unavailable_pins=unavailable,
        native_processes_started=0, quantitative_benchmarks_started=0,
        source_counts_qualified=False, chart_admission=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = replay()
    if args.output:
        with args.output.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps(result), flush=True)
