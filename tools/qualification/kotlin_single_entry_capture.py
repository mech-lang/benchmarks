"""Additive replay of retained HotSpot code bytes; no native execution.

The frozen first observer's multiline byte-row expression consumed indentation
from a following row. Parse each physical row independently while preserving
the original complete-range, overlap, nmethod, OopMap and work-gate checks.
"""
import hashlib
import importlib.util
from pathlib import Path
import re

CONTROLLER_SHA = 'a4e2fe9251e9d0453815d7d5917e43617b0f3d54b7116bc4ab1dfa01a426e6da'


def require(value, message):
    if not value: raise AssertionError(message)


def load_original():
    path = Path(__file__).with_name('kotlin_single_entry.py')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == CONTROLLER_SHA, 'Frozen first capture controller changed')
    spec = importlib.util.spec_from_file_location('original_kotlin_capture_for_replay',path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


def instruction_bytes(text, entry):
    require(text.count('[MachCode]') == text.count('[/MachCode]') == 1, 'Incomplete native MachCode boundaries')
    region = re.search(r'main code[ \t]+\[(0x[0-9a-fA-F]+),(0x[0-9a-fA-F]+)\][ \t]*=[ \t]*(\d+)',text)
    require(region, 'Missing native main-code address range')
    start,end,size = int(region[1],16),int(region[2],16),int(region[3])
    require(end-start == size and size > 0 and start <= int(entry,16) < end,
            'Native main-code range/entry differs')
    body = text.split('[MachCode]',1)[1].split('[/MachCode]',1)[0]
    coverage = {}; count = 0
    for line in body.splitlines():
        match = re.fullmatch(r'[ \t]*(0x[0-9a-fA-F]+):[ \t]+([0-9a-fA-F][0-9a-fA-F \t|]*)',line)
        if not match: continue
        groups = re.split(r'[ \t|]+',match[2].strip())
        require(all(len(group)%2 == 0 for group in groups), 'Malformed native byte group')
        data = bytes.fromhex(''.join(groups)); position = int(match[1],16); count += 1
        for offset,value in enumerate(data):
            address = position+offset
            if start <= address < end:
                require(address not in coverage, 'Overlapping native byte rows')
                coverage[address] = value
    require(len(coverage) == size, 'Native instruction bytes do not cover the main-code range')
    return start,bytes(coverage[address] for address in range(start,end)),count


def instruction_coverage(text, entry):
    start,data,count = instruction_bytes(text,entry)
    return dict(start=hex(start),end=hex(start+len(data)),bytes=len(data),retained_instruction_rows=count,
                machine_bytes_sha256=hashlib.sha256(data).hexdigest())


stage = load_original()
# This is a private imported module; frozen files and earlier receipts remain
# untouched. capture_index resolves this one repaired helper in its globals.
stage.instruction_coverage = instruction_coverage
capture_index = stage.capture_index
