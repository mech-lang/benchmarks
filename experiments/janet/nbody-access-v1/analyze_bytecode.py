"""Reproducible static evidence for array-call removal and scalar loop state."""
from collections import Counter
import json
from common import HERE,process

rows={}
for label in ('parent','intrinsic-get','cached-pairs','scalar-registers'):
    path=HERE/'bytecode-v1'/label/'stdout.bin';lines=path.read_text().splitlines()
    assert lines[0].startswith('S ')
    instructions=[line[1:-1].split() for line in lines[1:]]
    assert all(line.startswith('(') and line.endswith(')') for line in lines[1:])
    rows[label]=dict(virtual_register_slots=int(lines[0].split()[1]),static_instructions=len(instructions),static_opcode_counts=dict(sorted(Counter(v[0] for v in instructions).items())),bytecode_sha256=process.sha(path))
    if label=='scalar-registers':
        backward=[(i,int(v[-1])) for i,v in enumerate(instructions) if v[0].startswith('jmp') and int(v[-1])<0]
        assert len(backward)==1
        end,offset=backward[0];start=end+offset;hot=instructions[start:end+1];ops=Counter(v[0] for v in hot)
        assert ops['call']==10 and ops['div']==10
        assert not any(op in ops for op in ('get','geti','put','puti','in','ini','next'))
        rows[label]['single_time_step_loop']=dict(first_instruction_zero_based=start,last_instruction_zero_based=end,static_opcode_counts=dict(sorted(ops.items())),aggregate_state_reads_or_writes=0)
assert rows['parent']['static_opcode_counts']['call']-rows['intrinsic-get']['static_opcode_counts']['call']==18
assert rows['intrinsic-get']['static_opcode_counts']['get']==18
result=dict(schema='janet-nbody-native-bytecode-review.v1',status='verified-source-bound-static-instruction-findings',profiles=rows,
            limitations='Static instruction sites and register slots are not dynamic instruction counts or source LOC. The scalar loop is the only backward branch in advance-n; initialization and final aggregate stores are outside it. Dynamic required work is checked separately by source-projected counters.')
process.save(HERE/'bytecode-review.json',result)
print('Verified 18 replaced array-call sites and no aggregate accesses inside the scalar time-step loop')
