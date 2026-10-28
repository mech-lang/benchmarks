"""Require the public source/decoded wide-slot artifact proof before sampling."""
from pathlib import Path
import re
from study import (CODE_DIR, ROOT, STUDY_ID, STUDY_IDS, build_receipt_path, process, read, source_state)

FILES = {'program.o', 'program.mecb', 'native-descriptor.json',
         'native-descriptor.bin', 'object-identity.bin', 'native-resources.json'}
SUBJECTS = {'I', 'A', 'C'}
ROUTES = {'source', 'decoded'}


def adopted_subjects(candidate, baseline):
    """The shared six-build proof must use both studies' adopted sources."""
    plans = {name: CODE_DIR.parent / name / 'plan.json' for name in STUDY_IDS}
    architecture, cleanup = (read(plans[name]) for name in STUDY_IDS)
    refs = {'I': architecture['baseline_receipt'], 'A': architecture['candidate_receipt'],
            'C': cleanup['candidate_receipt']}
    # Resolve local references in their named study, including when this module
    # is imported by the other study's campaign.
    for subject, study in (('I', STUDY_IDS[0]), ('A', STUDY_IDS[0]), ('C', STUDY_IDS[1])):
        if isinstance(refs[subject], str):
            path = CODE_DIR.parent / study / refs[subject]
            refs[subject] = dict(study_id=study, path=refs[subject], sha256=process.sha(path))
    paths = {name: build_receipt_path(ref, shared=True) for name, ref in refs.items()}
    receipts = {name: read(path) for name, path in paths.items()}
    shared_before = build_receipt_path(cleanup['baseline_receipt'], shared=True)
    assert shared_before == paths['A'] and read(shared_before) == receipts['A']
    assert architecture['implementation_base'] == receipts['I']['source']['commit']
    assert architecture['final_compiler_source'] == cleanup['implementation_base'] == receipts['A']['source']['commit']
    assert cleanup['final_compiler_source'] == receipts['C']['source']['commit']
    for receipt in receipts.values():
        assert receipt['status'] == 'public-subject-built' and receipt['benchmark_samples'] == 0
        assert receipt['source']['status'] == ''
    before, after = ('I', 'A') if STUDY_ID == STUDY_IDS[0] else ('A', 'C')
    assert baseline == receipts[before] and candidate == receipts[after]
    return receipts, [*plans.values(), *paths.values()]


def inventory(report, protocol, receipts):
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
    assert set(receipts) == SUBJECTS
    for subject, receipt in receipts.items():
        assert protocol['subjects'][subject]['commit'] == receipt['source']['commit']
        assert protocol['subjects'][subject]['compiler_sha256'] == receipt['compiler_sha256']
        assert all(row['source'] == receipt['source'] for row in rows if row['subject'] == subject)


def geometry(image, disassembly):
    """Derive the selected key from descriptor dataflow and inspect slot addressing."""
    plan = image['plan']
    assert plan['inputs'] == plan['resource_requirements'] == []
    regions = [region for region in image['closed_tails']['regions'] if region['packed'] is not None]
    assert len(regions) == 1
    region = regions[0]
    packed = region['packed']
    assert packed['domain']['bits'] == 4 and packed['domain']['shift'] == 0
    constants = {row['value']: row['constant']['data'] for row in plan['constants']}
    primitives = {primitive['output']: primitive for block in plan['blocks']
                  if isinstance(block['action'].get('Scalar'), dict)
                  for primitive in [block['action']['Scalar'].get('Primitive')] if primitive}
    range_call = plan['blocks'][packed['range_site']]['action']['LibraryCall']
    assert range_call['template']['selected_key'] == dict(module_path=['range'], operation_name='inclusive')
    start, end = [primitives[value] for value in range_call['operands']]
    assert start['op'] == end['op'] == 'U64Add' and start['operands'][0] == end['operands'][0]
    assert [op['operands'][1] for op in (start, end)] == [packed['start_offset'], packed['end_offset']]
    offsets = [constants[op['operands'][1]]['U64'] for op in (start, end)]
    assert offsets == [1, 17]
    assert packed['inclusive'] is True
    width = offsets[1] - offsets[0] + 1
    selection = plan['blocks'][packed['selection_site']]['action']['LibraryCall']
    assert selection['template']['selected_key'] == dict(module_path=['access'], operation_name='range')
    assert selection['operands'][1] == range_call['output']
    text = constants[selection['operands'][0]]['String']
    assert len(text.encode('utf-8')) == 42 and width == 17 and width * packed['domain']['bits'] == 68

    symbol = f'_mech_canonical_program_entry_v1_packed_loop_{region["tail"]["header"]}_funded'
    functions = re.split(r'^([0-9a-f]+) <([^>]+)>:\s*$', disassembly, flags=re.M)
    bodies = {functions[i + 1]: functions[i + 2] for i in range(1, len(functions), 3)}
    assert symbol in bodies and 'file format mach-o arm64' in disassembly
    instructions = []
    for line in bodies[symbol].splitlines():
        match = re.match(r'\s*[0-9a-f]+:\s*(\S+)\s*(.*?)\s*$', line)
        if match:
            instructions.append((match[1], re.sub(r'\s+', '', match[2])))
    probes = []
    for i, (op, operands) in enumerate(instructions[:-1]):
        stride = re.fullmatch(r'(x\d+),#(16|24)', operands) if op == 'mov' else None
        if not stride:
            continue
        next_op, next_operands = instructions[i + 1]
        address = re.fullmatch(r'(x\d+),(x\d+),' + stride[1] + r',(x\d+)', next_operands)
        if next_op != 'madd' or not address:
            continue
        assert int(stride[2]) == 24, 'Packed-loop addressing uses a narrow slot'
        base = address[1]
        window = instructions[i + 2:i + 24]
        offsets_seen = set()
        for j, (mnemonic, args) in enumerate(window):
            field = re.fullmatch(r'(x\d+),' + base + r',#(8|16)', args) if mnemonic == 'add' else None
            if field and any(m == 'ldr' and re.fullmatch(r'x\d+,\[' + field[1] + r',x\d+\]', a)
                             for m, a in window[j + 1:j + 4]):
                offsets_seen.add(int(field[2]))
        if offsets_seen == {8, 16} and sum(op == 'cmp' for op, _ in window) >= 2:
            probes.append(i)
    assert probes, 'No emitted 24-byte packed-map probe in the selected loop'
    return dict(packing_bits=4, selected_width=width, selected_key_bits=68, payload_bytes=24)


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
    receipts, adopted_files = adopted_subjects(candidate, baseline)
    inventory(report, protocol, receipts)
    assert report['pins'] and all(process.sha(Path(p)) == digest for p, digest in report['pins'].items())
    files = [path, protocol_path, root / 'executed-runner.py', root / 'fixture.mec', *adopted_files]
    controller = protocol['controller_pins']['experiments/janet/knucleotide-bytes-v1/process.py']
    for row in report['builds']:
        subject, route = row['subject'], row['route']
        spec = protocol['subjects'][subject]
        public_receipt = (ROOT / spec['receipt']).resolve()
        assert read(public_receipt) == receipts[subject] and process.sha(public_receipt) == spec['receipt_sha256']
        assert spec['workspace'] == receipts[subject]['workspace']
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
        aot = root / 'processes' / subject / route / 'aot.json'
        assert process.sha(aot) == row['aot_process_sha256']
        owned(read(aot), controller, row['command'], 1800)
        disassembly = root / 'processes' / subject / route / 'disassembly'
        stdout = disassembly / 'stdout.bin'
        assert stdout.stat().st_size > 0 and process.sha(stdout) == row['disassembly_sha256']
        derived = geometry(image, stdout.read_text())
        assert all(row['descriptor_evidence'][key] == value for key, value in derived.items())
        receipt = read(disassembly / 'process.json')
        original_object = row['command'][-1] + '.project/program.o'
        owned(receipt, controller, [protocol['objdump'], '--disassemble', '--no-show-raw-insn', original_object], 180)
        files += [aot, disassembly / 'process.json', stdout, disassembly / 'stderr.bin']
    return files
