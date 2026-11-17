#!/usr/bin/env python3
"""Independent Python task oracles. Run in a separate process from every measured worker."""
import json
import math
import sys
from extended_oracles import table_join, graph, ekf


def outputs(case, count):
    name = case['task']['oracle']
    schedule = case['measurement']['schedule']
    if name == "ekf":
        return ekf(schedule, count)
    result = []
    position, velocity = 1.0, 0.0
    for index in range(count):
        frame = schedule[index % len(schedule)]
        x = frame[0] if frame else 0.0
        if name.startswith('table-'):
            result.append(table_join(name[6:], x))
            continue
        if name == 'graph':
            result.append(graph(x))
            continue
        if name == 'strings':
            value = {'':0,'é':1,'é':2,'👩🏽‍💻':3,'\r\n':4}.get(x,9)
        elif name == 'graphemes':
            # The declared corpus supplies the second grapheme after ASCII x.
            value = 2 if x.startswith('xé') else 1 if x.startswith('xé') else 3
        elif name == 'fsm':
            result.append({'kind':'unpublished'} if index==0 else {'kind':'scalar','value':schedule[0][0]=='é'})
            continue
        elif name == 'filter':
            values = [n * n for n in frame if n > 0]
            result.append({'kind': 'matrix', 'shape': [1, len(values)], 'values': values})
            continue
        if name == 'collection':
            result.append({'kind': 'set', 'values': sorted({x, 2.0, 3.0})})
            continue
        if name in ('strings','graphemes'):
            pass
        elif name == 'scalar':
            value = x * x + 1.0
        elif name == 'pipeline':
            value = math.sqrt(x * x + 1.0) + math.sin(x)
        elif name == 'matrix':
            # Independent triple-loop matrix product, then the specified diagonal sum.
            a, b = [[x, 2.0], [3.0, 4.0]], [[2.0, 0.0], [1.0, 3.0]]
            c = [[sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
            value = c[0][0] + c[1][1]
        elif name == 'map':
            value = {1.0: 10.0, 2.0: 20.0, 3.0: 30.0}[x] + 1.0
        elif name == 'branch':
            value = 100.0 if x == 0 else x * x + 1.0
        elif name == 'recursion':
            value = sum(range(1, int(x) + 1))
        elif name == 'record':
            value = x * x + x + 1.0
        elif name == 'state':
            value = (index + 1.0) ** 2 + 1.0
        elif name == 'oscillator':
            velocity -= position * 0.01
            position += velocity * 0.01
            value = position
        elif name == 'wide':
            value = sum(x * (i + 1) + i for i in range(32))
        elif name == 'chain':
            value = x
            for _ in range(128):
                value = value * 1.0001 + 0.01
        else:
            raise ValueError(f'no independent oracle for {name}')
        result.append({'kind': 'scalar', 'value': value})
    return result


if __name__ == '__main__':
    request = json.load(sys.stdin)
    print(json.dumps({'protocol': 1, 'outcome': 'ok', 'outputs': outputs(request['case'], request['count'])}, allow_nan=False))
