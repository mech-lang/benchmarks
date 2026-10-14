"""Read 22 original Prolog sources and reconcile 44 actual compiled copies."""
import argparse
from contextlib import ExitStack
from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import traceback

P = Path(__file__).resolve().parent
H = P.parents[1]
LOCK = Path('/tmp/mech-clbg-timing.lock')


def main():
    parser = argparse.ArgumentParser()
    for name in ('worker-sha256', 'evidence-sha256', 'review-sha256', 'scored-review-sha256'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    assert sys.dont_write_bytecode
    assert all(len(digest) == 64 and set(digest) <= set('0123456789abcdef') for digest in vars(args).values())
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Prolog original source replay interrupted: ' + str(signum))
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM):
        signal.signal(signum, interrupted)
    print('WAIT common mutex: original22 Prolog reader replay, no subject execution', flush=True)
    with LOCK.open('r+') as lock, ExitStack() as dependencies:
        fcntl.flock(lock, fcntl.LOCK_EX)
        actual, named = os.fstat(lock.fileno()), LOCK.stat()
        assert (actual.st_dev, actual.st_ino) == (named.st_dev, named.st_ino) and actual.st_ino == 79859134
        output = H / 'source-counts/original22-replay-v1'
        output.mkdir(parents=True, exist_ok=False)
        pins, failure, evidence = {}, None, None
        report = dict(status='running-original22-Prolog-owner-replay', language='prolog',
            sources={}, profiles={}, compiler_bound_input_inventory={}, scanner_commands=0,
            compiled_copy_reconciliations=0, unresolved=[], original_subject_executions=0,
            original_QLF_rebuilds=0, original_WAM_reexecutions=0, preparation_or_fixture_reexecutions=0,
            source_work_qualified=False, canonical_LOC_admitted=False, chart_admission=False)
        signal.alarm(1200)
        try:
            path = P / 'evidence.py'
            raw = path.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == args.evidence_sha256 and not path.stat().st_mode & 0o222
            spec = importlib.util.spec_from_file_location('prolog_original22_evidence_v1', path)
            evidence = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = evidence
            exec(compile(raw, str(path), 'exec'), evidence.__dict__)
            for path, digest in ((P / 'replay.py', args.worker_sha256), (P / 'evidence.py', args.evidence_sha256),
                                 (P / 'REVIEW.md', args.review_sha256)):
                assert not path.stat().st_mode & 0o222
                evidence.bind(path, digest, pins)
            authority, modules, gates = evidence.load(pins, dependencies, args.scored_review_sha256)
            assert Path(sys.executable).resolve() == Path(evidence.PYTHON).resolve()
            reader_pins = gates['reader']['report']['input_pins']
            scanner = evidence.bind(evidence.READER / 'scan_source.pl', reader_pins[str(evidence.READER / 'scan_source.pl')], pins)
            projector = evidence.cold(evidence.READER / 'foreign_prolog.py',
                reader_pins[str(evidence.READER / 'foreign_prolog.py')], 'prolog_original22_owner_projector_v5', pins)
            original = modules['report']['profiles']
            assert len(original) == 20
            paths = {}
            references = 0
            for identifier, row in original.items():
                for entry in row['source_bundle']:
                    origin = evidence.bind(entry['original_path'], entry['sha256'], pins)
                    measured = evidence.bind(entry['path'], entry['sha256'], pins)
                    assert origin.read_bytes() == measured.read_bytes()
                    assert str(origin) not in paths or paths[str(origin)]['sha256'] == entry['sha256']
                    paths[str(origin)] = dict(sha256=entry['sha256'], role=entry['role'])
                    references += 1
            assert len(paths) == 22 and references == 44
            service, guard, harness = [modules[key] for key in ('service', 'guard', 'harness')]
            environment = dict(harness.compact.ENV) | modules['config']['environment']
            packets = {}
            for index, (source, declaration) in enumerate(sorted(paths.items()), 1):
                folder = output / 'sources' / f'{index:02d}'
                folder.mkdir(parents=True)
                path = evidence.bind(source, declaration['sha256'], pins)
                raw = path.read_bytes()
                (folder / 'original-source.pl').write_bytes(raw)
                command = [str(modules['binary']), '-q', '-f', 'none', '-l', str(scanner),
                    '-g', 'prolog_source_scan_v1:main', '--', source]
                evidence.verify(pins)
                result = service.owned_command(guard, harness, command, environment, folder,
                    lock.fileno(), 20, 'original-reader')
                report['scanner_commands'] += 1
                modules['prep'].owned_receipt(result['detail'], command)
                assert result['stderr'] == b''
                packet = json.loads(result['stdout'])
                assert packet['source'] == source and packet['source_text'].encode('utf8') == raw
                packets[source] = packet
                report['sources'][source] = dict(source=source, source_sha256=declaration['sha256'],
                    source_language='prolog', role=declaration['role'], scanner_command=command,
                    scanner_receipt=str(folder / 'original-reader.json'),
                    scanner_receipt_sha256=evidence.sha(folder / 'original-reader.json'),
                    scanner_stdout=str(folder / 'original-reader.stdout'),
                    scanner_stdout_sha256=evidence.sha(folder / 'original-reader.stdout'),
                    retained_source=str(folder / 'original-source.pl'),
                    original_reader_packet=packet, profile_projections={})
            assert len(packets) == report['scanner_commands'] == 22
            profile_files, metrics_by_origin = {}, {}
            for identifier, row in sorted(original.items()):
                bundle = row['source_bundle']
                context = projector.BundleContext([packets[entry['original_path']] for entry in bundle])
                files = []
                for entry in [bundle[-1]] + bundle[:-1]:
                    source = entry['original_path']
                    raw = Path(source).read_bytes()
                    metric = projector.count_prolog(raw, packets[source], language='prolog', context=context)
                    assert metric['rule_version'] == 'canonical-source-units-20261012-approved-rule-v2'
                    assert metric['source_hash_verified'] is metric['actual_fixtures_qualified'] is metric['chart_admission'] is False
                    expansions = []
                    text = raw.decode('utf8')
                    for event in metric['canonical_events']:
                        assert 0 <= event['full_owner_start'] <= event['start'] < event['end'] <= event['full_owner_end'] <= len(text)
                        assert text[event['start']:event['end']].encode('utf8') == raw[event['byte_start']:event['byte_end']]
                        expansions.append(dict(event, original_source=text[event['full_owner_start']:event['full_owner_end']]))
                    record = dict(original_source=source, original_source_sha256=entry['sha256'],
                        compiled_source=entry['path'], compiled_source_sha256=entry['sha256'],
                        exact_original_and_compiled_bytes_equal=True, original_projection=metric,
                        full_owner_expansions=expansions)
                    folder = output / 'profiles' / identifier
                    folder.mkdir(parents=True, exist_ok=True)
                    receipt = folder / (Path(source).stem + '-owners.json')
                    evidence.save(receipt, record)
                    report['sources'][source]['profile_projections'][identifier] = dict(path=str(receipt), sha256=evidence.sha(receipt))
                    if source in metrics_by_origin:
                        assert metrics_by_origin[source] == metric, ('Context changes original source owners', source)
                    else:
                        metrics_by_origin[source] = deepcopy(metric)
                    files.append(dict(path=entry['path'], origin=source, sha256=entry['sha256'],
                        role='application' if entry['role'] == 'main-source' else 'application-helper',
                        normalized_loc=metric['normalized_loc'], physical_loc=metric['physical_loc'],
                        count_receipt=dict(path=str(receipt), sha256=evidence.sha(receipt)),
                        unresolved_diagnostics=deepcopy(metric['diagnostics'])))
                    report['compiled_copy_reconciliations'] += 1
                    for diagnostic in metric['diagnostics']:
                        report['unresolved'].append(dict(profile=identifier, original_source=source, diagnostic=diagnostic))
                assert files[0]['path'] == row['measured_source']
                profile_files[identifier] = files
                pending = any(item['normalized_loc'] is None for item in files)
                report['profiles'][identifier] = dict(id=identifier, benchmark=row['benchmark'], variant=row['variant'],
                    source=row['measured_source'], source_origin=row['source'], source_sha256=row['source_sha256'],
                    source_bundle=files, canonical_loc=None if pending else sum(item['normalized_loc'] for item in files),
                    physical_loc=sum(item['physical_loc'] for item in files),
                    original_scored_profile=deepcopy(row), source_alias_of=row.get('source_alias_of'),
                    semantic_review_pending=True, source_work_qualified=False, chart_admission=False)
                report['compiler_bound_input_inventory'][identifier] = dict(
                    status='compiled-copy-bridge-reconciled-awaiting-owner-admission',
                    source_sha256=row['source_sha256'], binary_sha256=row['binary_sha256'],
                    original_compiler_input_evidence=deepcopy(row['compiler_bound_input_inventory']),
                    independently_retained_compiler_input_evidence=deepcopy(row), files=deepcopy(files))
            assert report['compiled_copy_reconciliations'] == 44 and len(metrics_by_origin) == 22 and len(report['profiles']) == 20
            report.update(status='original22-Prolog-owner-replay-awaiting-exact-meaning-review',
                original_source_count=22, profile_count=20, complete_authored_source_bundles=True,
                reader_fixture_receipt=dict(path=gates['reader']['report_path'], sha256=gates['reader']['report_sha256']),
                retained_gate_reviews={key: dict(path=value['root_path'], sha256=value['root_sha256']) for key, value in gates.items()},
                scored_source_WAM_review=dict(path=str(evidence.SCORING), sha256=args.scored_review_sha256),
                actual_preparation=dict(path=str(authority.OLD / 'report.json'), sha256=authority.REPORT_SHA))
        except BaseException as error:
            failure = error
            report.update(status='failed-original22-Prolog-owner-replay', error=str(error), error_type=type(error).__name__)
            (output / 'error.log').write_text(traceback.format_exc())
        finally:
            signal.alarm(0)
            errors, artifacts = [], {}
            for path, digest in pins.items():
                try:
                    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
                except BaseException as error:
                    errors.append(dict(path=path, error=str(error)))
            for path in output.rglob('*'):
                if path.is_file():
                    with path.open('rb') as stream:
                        artifacts[str(path)] = hashlib.file_digest(stream, 'sha256').hexdigest()
            if errors:
                report.update(status='failed-terminal-integrity', terminal_integrity_errors=errors)
            report.update(pins=pins, artifact_pins=artifacts, terminal_evidence_complete=not errors,
                exclusive_common_mutex_held=True, common_mutex_inode=79859134)
            with (output / 'replay.json').open('x') as stream:
                json.dump(report, stream, indent=2, ensure_ascii=False)
                stream.write('\n')
            with (output / 'replay.json').open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            with (output / 'terminal.json').open('x') as stream:
                json.dump(dict(status=report['status'], replay=str(output / 'replay.json'), replay_sha256=digest,
                    input_pins=pins, artifact_pins=artifacts, exclusive_common_mutex_held=True,
                    common_mutex_inode=79859134, integrity_errors=errors, canonical_LOC_admitted=False,
                    source_work_qualified=False, chart_admission=False), stream, indent=2)
                stream.write('\n')
            if failure is not None:
                raise failure
            assert not errors
            print(json.dumps(dict(status=report['status'], replay=str(output / 'replay.json'), sha256=digest,
                original_sources=22, compiled_copy_reconciliations=44, unresolved=len(report['unresolved']))), flush=True)


if __name__ == '__main__':
    main()
