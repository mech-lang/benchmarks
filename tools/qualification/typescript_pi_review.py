"""Review retained V8 pi instructions without executing Node or changing captures."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / 'experiments/typescript/single-entry-work-v1'
CAPTURE = PACKET / 'run-pi-v1/00-pidigits'


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def instructions(text, kind):
    marker = f'kind = {kind}\nname = calculatePi\n'
    assert text.count(marker) == 1
    body = text.split(marker)[1].split('Instructions (size = ', 1)[1].split('\n\n', 1)[0]
    rows = {}
    for line in body.splitlines()[1:]:
        match = re.fullmatch(r'(0x[0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]{8})\s+(.*)', line)
        if match:
            address = int(match[1], 16)
            assert address not in rows
            rows[address] = {'offset': int(match[2], 16), 'word': int(match[3], 16), 'text': match[4]}
    assert rows
    return rows


def called_builtin(rows, call, builtins):
    assert rows[call]['word'] == 0xd63f0200 and rows[call]['text'] == 'blr x16'
    load = rows[call - 4]
    match = re.fullmatch(r'ldr x16, pc\+[0-9]+ \(addr (0x[0-9a-f]+)\)', load['text'])
    assert match
    pool = int(match[1], 16)
    assert rows[pool]['text'] == rows[pool + 4]['text'] == 'constant'
    target = rows[pool]['word'] | (rows[pool + 4]['word'] << 32)
    assert target in builtins
    return {'instruction': hex(call), 'offset': hex(rows[call]['offset']), 'literal_pool': hex(pool),
            'target': hex(target), 'builtin': builtins[target]}


def review():
    code_path = CAPTURE / 'code-2755-0.asm'
    log_path = CAPTURE / 'isolate-0xa4740c000-2755-v8.log'
    stdout_path = CAPTURE / 'stdout.bin'
    source_path = ROOT / 'experiments/typescript/native-stage-v1/run-v1/compile/project/emitted/pidigits.js'
    code, log, stdout, source = [p.read_text() for p in (code_path, log_path, stdout_path, source_path)]
    report_path, terminal_path = PACKET / 'run-pi-v1/report.json', PACKET / 'run-pi-v1/terminal.json'
    report, terminal, native = [json.loads(p.read_bytes()) for p in (report_path, terminal_path, CAPTURE/'process.json')]
    assert pin(report_path)['sha256'] == 'fd8f59f43a65a7d2e04b8bff9d9a39b3f3b38ec02f81b237714f4c1558015d73'
    assert terminal['report_sha256'] == pin(report_path)['sha256']
    assert report['integrity_errors'] == terminal['integrity_errors'] == []
    assert native['pid'] == 2755 and native['exit_status'] == 0 and native['direct_child_reaped'] is True
    assert native['remaining_process_group'] == native['cleanup_errors'] == []
    assert native['stdout_sha256'] == pin(stdout_path)['sha256'] and native['stderr_bytes'] == 0
    assert report['pins'][str(source_path)] == pin(source_path)['sha256']
    assert source[807] == source[836] == '/' and source[859:862] == '==='
    assert source[801:811] == 't = m / d;'
    assert source[824:840] == 'u = (m + n) / d;'
    expected = (ROOT/'archive/workloads/pidigits/inputs/output-full.txt').read_bytes()
    app_lines = [line for line in stdout.splitlines(keepends=True) if re.fullmatch(r'[0-9]{10}\t:[0-9]+\n', line)]
    assert len(app_lines) == 1000 and ''.join(app_lines).encode() == expected
    # The initial Ignition dump is followed by a separate Maglev bytecode dump.
    first = stdout.split('Compiling ', 1)[0]
    for offset, operation in ((118, 'Div r6, [11]'), (130, 'Div r11, [12]'), (136, 'TestEqualStrict r8, [14]')):
        assert re.search(r'@\s+'+str(offset)+r' : [0-9a-f ]+\s'+re.escape(operation)+r'\n', first)
    builtins = {int(m[1], 16): m[2] for m in re.finditer(r'^code-creation,Builtin,[^,]+,[^,]+,(0x[0-9a-f]+),[0-9]+,([^\n]+)$', log, re.M)}
    regions = []
    for kind, pairs in (
        ('MAGLEV', ((0x1286cf18c, 0x1286cf1cc, 0x1286cf1e8), (0x1286cf688, 0x1286cf6c8, 0x1286cf6e4))),
        ('TURBOFAN_JS', ((0x1286d05fc, 0x1286d0640, 0x1286d06fc), (0x1286d0d34, 0x1286d0d78, 0x1286d0e2c)))):
        rows = instructions(code, kind)
        for first_call, second_call, comparison in pairs:
            calls = [called_builtin(rows, p, builtins) for p in (first_call, second_call)]
            assert all(c['builtin'] == ('Divide_WithFeedback' if kind == 'MAGLEV' else 'BigIntDivideNoThrow') for c in calls)
            if kind == 'MAGLEV':
                assert called_builtin(rows, comparison, builtins)['builtin'] == 'StrictEqual_WithFeedback'
            else:
                assert rows[comparison]['word'] == 0xeb0700df and rows[comparison]['text'] == 'cmp x6, x7'
            regions.append({'tier': kind, 'division_calls': calls, 'comparison': hex(comparison),
                            'comparison_offset': hex(rows[comparison]['offset']),
                            'manual_control_and_operand_flow_review': 'Both separately computed quotients reach this comparison; error/deoptimization exits do not bypass an extraction into digit emission.'})
    assert builtins[0x105817c20] == 'BigIntDivideNoThrow'
    assert 'name = BigIntDivideNoThrow\n' in code and 'Instructions (size = 496)' in code
    assert '0x105817d44   124  d63f0200       blr x16' in code
    assert code.count('[OSR - entry. function: calculatePi, osr offset: 260]') == 2
    deopts = [line for line in log.splitlines() if line.startswith('code-deopt,')]
    pi_deopts = [line for line in deopts if str(source_path) in line]
    assert len(pi_deopts) == 1 and 'prepare for on stack replacement (OSR)' in pi_deopts[0]
    for tier in ('interpreter', 'baseline', 'maglev', 'turbofan'):
        assert re.search(r'^function,'+tier+r',[^\n]*,calculatePi$', log, re.M)
    evidence = [source_path, stdout_path, code_path, log_path, CAPTURE/'process.json', report_path, terminal_path,
                PACKET/'plan-pi-v1.json', ROOT/'experiments/typescript/required-work-v1/static-review-v1.json', Path(__file__).resolve()]
    return {'schema': 'typescript-pi-instruction-peer-review-v1', 'status': 'two-extractions-retained-in-bytecode-and-entered-optimized-tiers',
            'reviewed_at': datetime.now(timezone.utc).isoformat(), 'profile': 'typescript-pidigits-v1',
            'evidence': [pin(p) for p in evidence], 'source_positions': {'first_division': 807, 'second_division': 836, 'equality': 859},
            'ignition_offsets': {'first_division': 118, 'second_division': 130, 'equality': 136},
            'native_regions': regions, 'both_divisions_dominate_comparison': True,
            'actual_osr_entries': ['Maglev', 'TurboFan'], 'pi_deoptimization_events': pi_deopts,
            'complete_application_output': {'bytes': len(expected), 'sha256': hashlib.sha256(expected).hexdigest(), 'lines': 1000},
            'manual_findings': [
                'The two divisions use m/d and (m+n)/d; each pair retains the shared denominator and separate numerators/results.',
                'The compiled bodies each contain an entry region and a continuing-loop region. Four static division sites per tier represent two sites in each region, not four extractions per iteration.',
                'TurboFan literal pools resolve to the captured 496-byte BigIntDivideNoThrow builtin. Its body retains general quotient-result allocation and the external arithmetic call, with ordinary zero/unit-denominator/error branches.',
                'The code-creation log and explicit OSR entries bind both inspected optimized bodies to this invocation. The only pi deoptimization transitions Maglev to TurboFan at the loop backedge.',
                'Ignition arithmetic/operand flow and both optimized regions were manually reviewed. Guard/deoptimization exits return to the retained bytecode semantics rather than replacing the second extraction with an inequality.'
            ],
            'limits': [
                'Sparkplug baseline code creation is recorded; its machine body was not disassembled. No claim of exhaustive machine-instruction observation across every runtime tier is made.',
                'Call targets are general V8 arithmetic support. This review does not disassemble every C++ arithmetic implementation or count dynamic division calls.',
                'Tracing disables concurrent Maglev and changes diagnostic scheduling. This invocation supplies work evidence, not a benchmark sample or an unchanged-scheduling claim.',
                'Complete lossless stdout partition and the combined ten-workload admission are separate reviews.'
            ], 'native_processes_started_by_review': 0, 'runtime_dependency_closure_qualified': False,
            'full_timings_qualified': False, 'benchmark_samples': 0, 'chart_admission': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review()
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'output': str(args.output), 'sha256': pin(args.output.resolve())['sha256']}))
