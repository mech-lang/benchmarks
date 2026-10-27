"""Require the public source/decoded wide-slot artifact proof before sampling."""
from pathlib import Path
from study import (STUDY_ID, build_receipt_path, process, read, source_state)

FILES = {'program.o', 'program.mecb', 'native-descriptor.json',
         'native-descriptor.bin', 'object-identity.bin', 'native-resources.json'}
SUBJECTS = {'I', 'A', 'C'}
ROUTES = {'source', 'decoded'}


def inventory(report, protocol, candidate, baseline, study_id):
    assert report['schema'] == 'mech.wide-slot-public-artifacts.v1'
    assert report['status'] == 'passed-six-public-builds-wide-guest-artifacts-identical'
    assert report['benchmark_samples'] == 0 and report['performance_qualified'] is False
    assert protocol['status'] == 'ready'
    assert protocol['subjects_order'] == ['I', 'A', 'C']
    assert protocol['routes'] == ['source', 'decoded'] and protocol['builds'] == 6
    assert set(protocol['guest_files']) == FILES
    assert (protocol['aot_deadline_seconds'], protocol['clean_deadline_seconds']) == (1800, 180)
    fixture = protocol['fixture']
    assert (fixture['packing_bits'], fixture['width'], fixture['key_bits'],
            fixture['slot_bytes'], fixture['text_length']) == (4, 17, 68, 24, 42)
    assert fixture['source_inputs'] == fixture['resources'] == 0
    rows = report['builds']
    assert len(rows) == 6
    assert {(row['subject'], row['route']) for row in rows} == {
        (subject, route) for subject in SUBJECTS for route in ROUTES}
    reference = rows[0]['guest_artifacts']
    assert set(reference) == FILES
    assert all(isinstance(digest, str) and len(digest) == 64 and
               all(c in '0123456789abcdef' for c in digest) for digest in reference.values())
    for row in rows:
        assert row['guest_artifacts'] == reference
        assert row['source']['status'] == ''
        assert row['source']['commit'] == protocol['subjects'][row['subject']]['commit']
        geometry = row['descriptor_evidence']
        assert (geometry['packing_bits'], geometry['selected_width'],
                geometry['selected_key_bits'], geometry['payload_bytes']) == (4, 17, 68, 24)
    before, after = ('I', 'A') if study_id == 'native-architecture-consolidation-v1' else ('A', 'C')
    assert study_id in ('native-architecture-consolidation-v1', 'post-native-architecture-cleanup-v1')
    for subject, receipt in ((before, baseline), (after, candidate)):
        assert protocol['subjects'][subject]['compiler_sha256'] == receipt['compiler_sha256']
        assert all(row['source'] == receipt['source'] for row in rows if row['subject'] == subject)


def owned(receipt, digest, command, deadline):
    assert receipt['exit_status'] == 0 and receipt['command'] == command
    assert receipt['deadline_seconds'] == deadline and receipt['quantitative_benchmark'] is False
    assert receipt['inherited_common_mutex'] is True and receipt['group_closed'] is True
    assert receipt['reaped'] is True and receipt['cleanup_errors'] == receipt['signals'] == []
    assert not receipt.get('error') and not receipt.get('observer_still_waiting')
    assert receipt['controller_sha256'] == digest


def check(reference, candidate, baseline):
    assert reference['study_id'] == 'native-architecture-consolidation-v1'
    path = build_receipt_path(reference, shared=True)
    root = path.parent
    report = read(path)
    protocol_path = root / 'prospective-protocol.json'
    protocol = read(protocol_path)
    assert process.sha(protocol_path) == report['protocol_sha256']
    assert process.sha(root / 'executed-runner.py') == protocol['runner_sha256']
    assert process.sha(root / 'fixture.mec') == protocol['fixture']['sha256']
    inventory(report, protocol, candidate, baseline, STUDY_ID)
    assert report['pins'] and all(process.sha(Path(p)) == digest for p, digest in report['pins'].items())
    files = [path, protocol_path, root / 'executed-runner.py', root / 'fixture.mec']
    controller = protocol['controller_pins']['experiments/janet/knucleotide-bytes-v1/process.py']
    for row in report['builds']:
        subject, route = row['subject'], row['route']
        spec = protocol['subjects'][subject]
        assert source_state(Path(spec['workspace'])) == row['source']
        command = row['command']
        assert command == [command[0], '--no-config', 'build', command[3], '--backend', 'cranelift',
                           '--profile', 'release', '--keep-project', '--offline', '--workspace-root',
                           spec['workspace'], '--name', 'native-wide-slot-evidence', '-o', command[-1]]
        assert report['pins'][command[0]] == spec['compiler_sha256']
        input_hash = protocol['fixture']['sha256'] if route == 'source' else row['guest_artifacts']['program.mecb']
        assert report['pins'][command[3]] == input_hash
        directory = root / 'artifacts' / subject / route
        for name in FILES:
            artifact = directory / name
            assert artifact.is_file() and not artifact.is_symlink()
            assert process.sha(artifact) == row['guest_artifacts'][name]
            files.append(artifact)
        image = read(directory / 'native-descriptor.json')['descriptor']
        assert image['plan']['inputs'] == image['plan']['resource_requirements'] == []
        packed = [region['packed'] for region in image['closed_tails']['regions']
                  if region['packed'] is not None]
        assert len(packed) == 1 and packed[0]['domain']['bits'] == 4 and packed[0]['domain']['shift'] == 0
        constants = [item['constant']['data'].get('U64') for item in image['plan']['constants']]
        assert 17 in constants and 42 in constants
        aot = root / 'processes' / subject / route / 'aot.json'
        assert process.sha(aot) == row['aot_process_sha256']
        owned(read(aot), controller, row['command'], 1800)
        disassembly = root / 'processes' / subject / route / 'disassembly'
        stdout = disassembly / 'stdout.bin'
        assert stdout.stat().st_size > 0 and process.sha(stdout) == row['disassembly_sha256']
        receipt = read(disassembly / 'process.json')
        original_object = row['command'][-1] + '.project/program.o'
        owned(receipt, controller, [protocol['objdump'], '--disassemble', '--no-show-raw-insn', original_object], 180)
        files += [aot, disassembly / 'process.json', stdout, disassembly / 'stderr.bin']
    return files
