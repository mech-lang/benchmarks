"""Compare actual emitted Mach-O functions before primary timing."""
import hashlib
import fcntl
import struct
import sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import PLAN,process,read,source_state

def functions(path):
    data=path.read_bytes();header=struct.unpack_from('<8I',data)
    assert header[0]==0xfeedfacf
    position=32;table=None;sections=[]
    for _ in range(header[4]):
        command,size=struct.unpack_from('<II',data,position)
        assert size>=8 and position+size<=len(data)
        if command==2:table=struct.unpack_from('<4I',data,position+8)
        if command==0x19:
            count=struct.unpack_from('<I',data,position+64)[0]
            for i in range(count):
                name,segment,address,length,offset=struct.unpack_from('<16s16sQQI',data,position+72+i*80)
                assert offset+length<=len(data)
                sections.append((name.rstrip(b'\0'),address,length,offset))
        position+=size
    assert table is not None
    symoff,count,stroff,strsize=table;symbols=[]
    for i in range(count):
        name,kind,section,desc,address=struct.unpack_from('<IBBHQ',data,symoff+i*16)
        if kind&0xe==0xe and section and sections[section-1][0]==b'__text':
            end=data.index(0,stroff+name)
            symbols.append((address,data[stroff+name:end].decode(),section))
    symbols.sort();result={}
    for i,(address,name,section) in enumerate(symbols):
        _,base,length,offset=sections[section-1]
        finish=symbols[i+1][0] if i+1<len(symbols) and symbols[i+1][2]==section else base+length
        result[name]=data[offset+address-base:offset+finish-base]
    return result

def version_instruction(old,new,previous,current):
    # Both tests constrain one exact instruction/register and change only the
    # ABI immediate. Any other instruction change stops qualification for review.
    mask=0xffff<<5
    movz=(old&0x7f800000)==0x52800000 and (old>>21)&3==0
    if movz and old&~mask==new&~mask:
        return (old>>5)&0xffff==previous and (new>>5)&0xffff==current
    mask=0xfff<<10
    cmp=(old&0x7f80001f)==0x7100001f and not old&(1<<22)
    return cmp and old&~mask==new&~mask and (old>>10)&0xfff==previous and (new>>10)&0xfff==current

import re

def instruction_body(path,symbol):
    lines=path.read_text().splitlines();start=lines.index(symbol+':');result=[]
    for line in lines[start+1:]:
        if line and not line[0].isspace() and line.endswith(':'):break
        match=re.match(r'\s*([0-9a-fA-F]+)\s+(.+)',line)
        if match:result.append((int(match[1],16),match[2]))
    assert result
    return result

def row_loop(body):
    addresses={a for a,_ in body};leaders={body[0][0]};branches={}
    for index,(address,text) in enumerate(body):
        op=text.split()[0]
        assert op not in {'br','blr','bl'},'Unexpected indirect control/call in bounded leaf'
        branch=op=='b' or op.startswith('b.') or op in {'cbz','cbnz','tbz','tbnz'}
        if branch:
            match=re.search(r'0x([0-9a-fA-F]+)\s*$',text);assert match,text
            target=int(match[1],16);branches[address]=(target,op!='b')
            if target in addresses:leaders.add(target)
        if branch or op.startswith('ret') or op=='brk':
            if index+1<len(body):leaders.add(body[index+1][0])
    blocks={};home={};current=None
    for address,text in body:
        if address in leaders:current=address;blocks[current]=[]
        blocks[current].append((address,text));home[address]=current
    starts=list(blocks);succ={k:set() for k in blocks}
    for index,key in enumerate(starts):
        address,text=blocks[key][-1];op=text.split()[0]
        if address in branches:
            target,conditional=branches[address]
            if target in home:succ[key].add(home[target])
            if conditional and index+1<len(starts):succ[key].add(starts[index+1])
        elif not op.startswith('ret') and op!='brk' and index+1<len(starts):succ[key].add(starts[index+1])
    reachable=set();todo=[starts[0]]
    while todo:
        key=todo.pop()
        if key in reachable:continue
        reachable.add(key);todo.extend(succ[key])
    pred={key:{p for p in reachable if key in succ[p]} for key in reachable}
    dom={key:({key} if key==starts[0] else set(reachable)) for key in reachable}
    changed=True
    while changed:
        changed=False
        for key in starts:
            if key not in reachable or key==starts[0]:continue
            value={key}|set.intersection(*(dom[p] for p in pred[key]))
            if value!=dom[key]:dom[key]=value;changed=True
    loops=[]
    for tail in reachable:
        for head in succ[tail]:
            if head not in dom[tail]:continue
            nodes={head,tail};todo=[] if head==tail else [tail]
            while todo:
                for parent in pred[todo.pop()]:
                    if parent not in nodes:nodes.add(parent);todo.append(parent)
            loops.append(dict(head=head,tail=tail,nodes=nodes))
    assert loops
    outer=max(loops,key=lambda r:len(r['nodes']))
    return outer,home,dom

def audit(path,symbol):
    body=instruction_body(path,symbol);loop,home,dom=row_loop(body)
    narrow=[(a,t) for a,t in body if t.split()[0].startswith('uqxtn')]
    stack=[(a,t) for a,t in body if t.split()[0] in {'ldr','ldur','ldp'} and re.search(r'\bq\d+\b',t.split('[')[0]) and '[sp' in t]
    loads=[(a,t) for a,t in body if t.split()[0] in {'ldr','ldur','ldp'} and re.search(r'\bq\d+\b',t.split('[')[0]) and re.search(r'\[x2(?:,|\])',t)]
    vectors=sum(len(re.findall(r'\bq\d+\b',t.split('[')[0])) for _,t in loads)
    hoisted=all(home[a] not in loop['nodes'] and home[a] in dom[loop['head']] for a,_ in loads)
    return dict(row_loop_head=hex(loop['head']),row_loop_backedge=hex(loop['tail']),row_loop_blocks=len(loop['nodes']),narrowing_instructions=len(narrow),narrowing_inside_row_loop=sum(home[a] in loop['nodes'] for a,_ in narrow),stack_vector_loads=len(stack),table_vector_registers_loaded=vectors,table_loads_dominate_and_are_outside_row_loop=hoisted,table_loads=[dict(address=hex(a),instruction=t) for a,t in loads],stack_loads=[dict(address=hex(a),instruction=t) for a,t in stack],row_loop_vector_constants=sum(t.split()[0].startswith('movi') and home[a] in loop['nodes'] for a,t in body))

plan=read(STUDY/'plan.json');before=source_state();assert before['commit']==plan['source_commit'] and not before['status']
project=HERE/'.build'/(plan['binary']+'.project');x=read(project/'native-descriptor.json')['descriptor'];manifest=read(project/'linked-manifest.json')['object']
assert (manifest['typed_ir_version'],manifest['abi_version'],manifest['work_policy_version'])==(88,32,69)
copies=manifest['compiled_join_map_copies'];assert len(copies)==1
copy='_'+copies[0]['symbol'];entry='_mech_canonical_program_entry_v1';a=functions(project/'program.o')
assert copies[0]['geometry_words']==copies[0]['initialized_extent_word']==6
comparisons=[];review=[]
for label,binary in [('parent',plan['parent_binary']),('ordinary',plan['ordinary_binary'])]:
    parent=HERE/'.build'/(binary+'.project');b=functions(parent/'program.o')
    assert set(a)==set(b) if label=='parent' else set(a)==set(b)|{copy}
    y=read(parent/'native-descriptor.json')['descriptor'];pm=read(parent/'linked-manifest.json')['object']
    for field in ['plan','visits','scalar_aggregates','borrowed_strings','closed_tails']:assert x[field]==y[field],(label,field)
    records=[]
    for name in b:
        same=a[name]==b[name];changes=[];expected=name==copy
        qualified=same or expected or (label=='ordinary' and name==entry)
        if not qualified and len(a[name])==len(b[name]) and len(a[name])%4==0:
            aw=struct.unpack('<'+'I'*(len(a[name])//4),a[name]);bw=struct.unpack('<'+'I'*(len(b[name])//4),b[name])
            changes=[dict(offset=i*4,previous=hex(v),current=hex(aw[i]),abi_immediate=bool(version_instruction(v,aw[i],pm['abi_version'],manifest['abi_version']))) for i,v in enumerate(bw) if v!=aw[i]]
            qualified=bool(changes) and all(c['abi_immediate'] for c in changes)
        if not qualified:review.append(dict(control=label,symbol=name))
        records.append(dict(symbol=name,candidate_bytes=len(a[name]),control_bytes=len(b[name]),identical=same,expected_byte_table_change=expected,qualified=qualified,changes=changes,candidate_sha256=hashlib.sha256(a[name]).hexdigest(),control_sha256=hashlib.sha256(b[name]).hexdigest()))
    assert len([r for r in records if r['symbol'] not in {entry,copy}])==8
    comparisons.append(dict(control=label,object_sha256=process.sha(parent/'program.o'),abi_version=pm['abi_version'],functions=records))
result=dict(source=before,script_sha256=process.sha(Path(__file__)),candidate_object_sha256=process.sha(project/'program.o'),compiled_join_map_copies=copies,copy_function=dict(symbol=copy,bytes=len(a[copy]),sha256=hashlib.sha256(a[copy]).hexdigest()),comparisons=comparisons,review_required=review,source_plan_visits_aggregate_borrowed_and_scalar_prices_identical=True,scope='Only the joined-table leaf and qualified ABI gates may change versus the immediate parent. Actual assembly must eliminate narrowing/table spills before full timing. No source checks, finite prices or complete updates change.')
out=STUDY/'object-disassembly-v1';out.mkdir(exist_ok=False)
env=read(HERE/plan['compiler']/'results.json')['environment'];result['static_disassembly']=[]
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino==83858837
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for label,binary in [('candidate',plan['binary']),('parent',plan['parent_binary']),('ordinary',plan['ordinary_binary'])]:
        folder=out/label;obj=HERE/'.build'/(binary+'.project/program.o')
        receipt=process.execute(['/usr/bin/otool','-tvV',str(obj)],folder,env,lock,deadline=60,quantitative=False);assert receipt['exit_status']==0
        result['static_disassembly'].append(dict(subject=label,folder=str(folder.relative_to(STUDY)),process_sha256=process.sha(folder/'process.json'),stdout_sha256=process.sha(folder/'stdout.bin')))
result['assembly']={name:audit(out/name/'stdout.bin',copy) for name in ['candidate','parent']}
ca=result['assembly']['candidate'];pa=result['assembly']['parent']
assert pa['narrowing_inside_row_loop']==16 and pa['stack_vector_loads']==3 and pa['table_vector_registers_loaded']==16 and pa['table_loads_dominate_and_are_outside_row_loop']
assembly_ok=ca['narrowing_instructions']==ca['stack_vector_loads']==0 and ca['table_vector_registers_loaded']==8 and ca['table_loads_dominate_and_are_outside_row_loop']
result['assembly_gate_qualified']=assembly_ok
result['status']='prepared-byte-table-and-unaffected-bodies-qualified' if assembly_ok and not review else 'byte-table-assembly-or-body-review-required'
assert source_state()==before
process.save(STUDY/'code-inspection.json',result)
print(result['status']);print('copy function',result['copy_function']);print('assembly',result['assembly']);print('body review',review)
assert assembly_ok and not review,'Actual code does not yet qualify for extensive timing; preserve this capture and investigate.'
