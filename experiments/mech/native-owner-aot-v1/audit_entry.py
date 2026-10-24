"""Retain exact entry disassembly and map observed worker PC groups to it."""
import argparse
import json
import re
import subprocess
from pathlib import Path
from analyze_profile import sha, text_section

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--receipt', required=True)
parser.add_argument('--timing', required=True)
parser.add_argument('--profile-build', required=True)
parser.add_argument('--samples', required=True)
parser.add_argument('--binary', required=True)
args = parser.parse_args()
timing = json.loads((HERE / args.timing / 'results.json').read_text())
build = json.loads((HERE / args.profile_build / 'results.json').read_text())
analysis = json.loads((HERE / args.samples / 'analysis.json').read_text())
binary = Path(build['binary'])
assert sha(binary.read_bytes()) == build['binary_sha256'] == analysis['profiling_binary_sha256']
assert sha((HERE / '.build' / args.binary).read_bytes()) == timing['candidate_sha256']
assert text_section(binary) == text_section(HERE / '.build' / args.binary)
assert analysis['machine_code_identical'] and analysis['completed_output_verified']
symbols = ['mech_canonical_program_entry_v1'] + [loop['symbol'] for loop in timing.get('compiled_outlined_loops', [])]
assert len(symbols) == len(set(symbols))
functions, commands, entries, command_hashes = {}, [], [], []
for symbol in symbols:
    command = ['/usr/bin/otool', '-tvV', '-p', '_' + symbol, str(binary)]
    run = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    lines = run.stdout.decode().splitlines()
    start = lines.index('_' + symbol + ':')
    end = next((i for i in range(start + 1, len(lines)) if lines[i].endswith(':')), len(lines))
    instructions = {int(m[1], 16): m[2] for line in lines[start + 1:end]
                    if (m := re.match(r'^([0-9a-fA-F]{16})\s+(.+)$', line))}
    assert instructions
    functions[symbol] = dict(base=min(instructions), instructions=instructions)
    commands.append(command)
    command_hashes.append(sha(run.stdout))
    entries.append(('\n'.join(lines[start:end]) + '\n').encode())
entry = b'\n'.join(entries)
base = functions[symbols[0]]['base']
out = HERE / args.receipt
out.mkdir(exist_ok=False)
(out / 'entry.s').write_bytes(entry)
groups = []
for capture in analysis['samples']:
    path = HERE / capture['stacks']
    assert sha(path.read_bytes()) == capture['stacks_sha256']
    workers = {thread['thread'] for thread in capture['threads'] if thread['observed_native_worker']}
    ancestors = []
    current = None

    def finish():
        node = ancestors.pop()
        count = node['count'] - node['children']
        assert count >= 0
        if current not in workers or not count or node['symbol'] not in functions:
            return
        function = functions[node['symbol']]
        base, instructions = function['base'], function['instructions']
        offsets = re.search(r'\+ ([0-9.,]+)\s+\[', node['line'])[1]
        listed = [int(n) for n in offsets.split(',') if n.isdigit()]
        assert listed and all(base + n in instructions for n in listed)
        groups.append(dict(thread=current, function=node['symbol'], entry_base=hex(base), exclusive_observations=count, source_line=node['line'].strip(),
                           listed_offsets=listed, additional_offsets_collapsed='...' in offsets,
                           instructions=[dict(offset=n, address=hex(base + n), instruction=instructions[base + n]) for n in listed]))

    graph = path.read_text().split('Call graph:\n', 1)[1].split('Total number in stack', 1)[0]
    for line in graph.splitlines():
        match = re.match(r'^[\s+!:|]*(\d+) (\S+)', line)
        if not match:
            continue
        count, symbol, depth = int(match[1]), match[2], match.start(1)
        if symbol.startswith('Thread_'):
            while ancestors: finish()
            current = symbol
            continue
        while ancestors and ancestors[-1]['depth'] >= depth: finish()
        if ancestors: ancestors[-1]['children'] += count
        ancestors.append(dict(count=count, symbol=symbol, depth=depth, children=0, line=line))
    while ancestors: finish()
groups.sort(key=lambda group: group['exclusive_observations'], reverse=True)
scope = 'Collapsed groups may contain several or undisplayed PCs. Group observations are not individual-instruction frequencies or elapsed-time shares.'
mapped = dict(status='retained-sampled-PC-groups-mapped-to-exact-entry', entry_base=hex(base), groups=groups,
              worker_generated_entry_exclusive_observations=sum(group['exclusive_observations'] for group in groups), scope=scope)
(out / 'hot-offset-groups.json').write_text(json.dumps(mapped, indent=2) + '\n')
result = dict(status='exact-code-static-disassembly-and-sampled-PCs-retained', source_commit=timing['source_commit'],
              commands=commands, exit_status=0, profiling_binary_sha256=build['binary_sha256'],
              machine_code_bytes=build['machine_code_bytes'], machine_code_sha256=build['machine_code_sha256'],
              whole_machine_code_matches_timed=True, disassembly_sha256=sha(entry), command_stdout_sha256=command_hashes,
              hot_offset_groups_sha256=sha((out / 'hot-offset-groups.json').read_bytes()),
              entry_instruction_count=sum(len(function['instructions']) for function in functions.values()),
              functions={symbol: dict(entry_base=hex(function['base']), instruction_count=len(function['instructions'])) for symbol, function in functions.items()},
              script_sha256=sha(Path(__file__).read_bytes()),
              configuration=vars(args), benchmark_samples=0, scope=scope)
(out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(instructions=result['entry_instruction_count'], functions=len(functions), observed_groups=len(groups), receipt=args.receipt)))
