"""Bounded static path audit of the exact emitted counting functions.

This reads retained disassembly only. Explicit branch assumptions select the
first-candidate successful update; this is not an instruction frequency or a
prediction of elapsed time. Source widths are deliberately not inferred from
native block order.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--audit', required=True)
args = parser.parse_args()
folder = HERE / args.audit
raw = (folder / 'entry.s').read_bytes()
identity = json.loads((folder / 'results.json').read_text())
assert hashlib.sha256(raw).hexdigest() == identity['disassembly_sha256']
functions, current = {}, None
for line in raw.decode().splitlines():
    if line.startswith('_') and line.endswith(':'):
        current = line[1:-1]
        functions[current] = {}
    elif current and (match := re.match(r'^([0-9a-fA-F]{16})\s+(.+)$', line)):
        functions[current][int(match[1], 16)] = match[2]


def successors(pc, instructions):
    text = instructions[pc]
    opcode = text.split()[0]
    target = re.search(r'0x([0-9a-fA-F]+)', text)
    target = int(target[1], 16) if target else None
    if opcode == 'b':
        return [target] if target in instructions else []
    if opcode in ('ret', 'br', 'blr', 'bl'):
        return []
    result = [pc + 4] if pc + 4 in instructions else []
    if (opcode.startswith('b.') or opcode in ('cbz', 'cbnz', 'tbz', 'tbnz')) and target in instructions:
        result.append(target)
    return result


def direct_cache_evidence(start, path, instructions):
    accesses = []
    for pc in path:
        match = re.fullmatch(r'ldr\s+x\d+, \[(x\d+), x\d+, lsl #3\]', instructions[pc])
        if not match: continue
        base = match[1]
        field_load = re.compile(r'ldr\s+' + base + r', \[x1, #0x98\]')
        loads = [at for at, text in instructions.items() if start - 1024 <= at < start and field_load.fullmatch(text)]
        assert loads, (hex(start), base, 'direct lookup lacks actual owned cache field load')
        accesses.append(dict(indexed_access=hex(pc), field_word=19, field_load=hex(max(loads)), base_register=base))
    assert len(accesses) == 1
    return accesses[0]


def cycle(start, instructions, direct):
    path, decisions, pc = [], [], start
    while pc not in path and len(path) < 128:
        path.append(pc)
        text = instructions[pc]
        opcode = text.split()[0]
        choices = successors(pc, instructions)
        if opcode == 'b':
            assert len(choices) == 1
            pc = choices[0]
        elif len(choices) == 2:
            # This deliberately fails on an unrecognized native layout. All
            # predicates on this path mean: a fingerprint exists, the first
            # full key matches, fuel remains and the next index is productive.
            assert opcode in ('b.eq','b.ne','cbz','b.hs','b.hi'), (hex(pc),text)
            taken = opcode == 'b.eq'
            decisions.append(dict(address=hex(pc),instruction=text,taken=taken))
            pc = choices[int(taken)]
        else:
            assert len(choices) == 1, (hex(pc),text)
            pc = choices[0]
    assert pc == start, (hex(start),hex(pc))
    body = [instructions[at] for at in path]
    assert any(t.startswith('cmeq.') for t in body) == (not direct)
    assert any(t.startswith('str\t') for t in body)
    assert any(t.startswith('cmp\t') for t in body)
    return path, decisions


paths = []
for name, instructions in functions.items():
    if not name.endswith('_funded'):
        continue
    for start, text in instructions.items():
        if not text.startswith('ldrb\t'):
            continue
        direct = name.endswith('_lookup_cache_funded')
        addresses, decisions = cycle(start, instructions, direct)
        body = [instructions[pc] for pc in addresses]
        paths.append(dict(function=name, lookup_mode='direct' if direct else 'hash',
            owned_cache=direct_cache_evidence(start, addresses, instructions) if direct else None,
            start=hex(start), instructions=len(body),
            branches=sum(t.split()[0] == 'b' or t.split()[0].startswith('b.') or
                         t.split()[0] in ('cbz','cbnz','tbz','tbnz') for t in body),
            stack_accesses=sum('[sp' in t or '[x29' in t for t in body),
            constant_zero_one_moves=sum(bool(re.fullmatch(r'mov\s+[wx]\d+, #0x[01]', t)) for t in body),
            branch_decisions=decisions,
            ordered_instructions=[dict(address=hex(pc), instruction=instructions[pc]) for pc in addresses]))
assert paths and len(paths) <= 128
result = dict(schema='mech.static-successful-separate-lookup-paths.v1',
    source_commit=identity['source_commit'], disassembly_sha256=identity['disassembly_sha256'],
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), paths=paths,
    scope='Explicitly assumed productive, funded, first-fingerprint/full-key-hit cycles, with every branch decision retained. Unrecognized branch layouts fail closed. Static counts only; no dynamic frequency, source-width assignment or elapsed-time attribution. Both source functions are included. Direct-cache cycles bind their indexed access to the actual immutable ABI28 word-19 load and assume the selected key is present; ordinary hash cycles retain first-fingerprint/full-key-hit assumptions. The cache/width selector is outside these cycles. Unused generic arms are not a claim of dynamically executed widths.')
(folder / 'steady-paths-split.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(audit=args.audit, cycles=len(paths),
    instructions=[min(p['instructions'] for p in paths),max(p['instructions'] for p in paths)],
    branches=sorted({p['branches'] for p in paths}),
    zero_one_moves=sorted({p['constant_zero_one_moves'] for p in paths}))))
