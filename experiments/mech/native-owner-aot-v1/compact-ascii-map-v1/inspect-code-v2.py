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

def mapping_audit(path,symbol,joined):
    body=instruction_body(path,symbol)
    records=lambda items:[dict(address=hex(a),instruction=text) for a,text in items]
    tbl=[(a,text) for a,text in body if text.split()[0].split('.')[0] in {'tbl','tbx'}]
    narrow=[(a,text) for a,text in body if text.split()[0].startswith('uqxtn')]
    vectors=[(a,text) for a,text in body if text.split()[0] in {'ldr','ldur','ldp'} and re.search(r'\bq\d+\b',text.split('[')[0])]
    stack=[(a,text) for a,text in vectors if '[sp' in text]
    result=dict(symbol=symbol,instructions=len(body),vector_lookups=len(tbl),lookups=records(tbl),narrowing_instructions=len(narrow),stack_vector_loads=records(stack),all_vector_loads=records(vectors))
    if joined:
        loop,home,dom=row_loop(body)
        loads=[(a,text) for a,text in vectors if '[sp' not in text and home[a] not in loop['nodes'] and home[a] in dom[loop['head']]]
        count=sum(len(re.findall(r'\bq\d+\b',text.split('[')[0])) for a,text in loads)
        result.update(row_loop_head=hex(loop['head']),row_loop_backedge=hex(loop['tail']),table_vector_registers_hoisted=count,table_loads_before_and_dominating_rows=records(loads),row_loop_vector_constants=sum(text.split()[0].startswith('movi') and home[a] in loop['nodes'] for a,text in body))
    return result

def dispatch_audit(path,symbol):
    body=instruction_body(path,symbol)
    calls=[(a,text) for a,text in body if text.split()[0] in {'bl','blr'}]
    conditions=[(a,text) for a,text in body if text.split()[0].startswith('b.') or text.split()[0] in {'cbz','cbnz','tbz','tbnz'}]
    return dict(symbol=symbol,instructions=len(body),calls=[dict(address=hex(a),instruction=text) for a,text in calls],conditional_branches=[dict(address=hex(a),instruction=text) for a,text in conditions])

plan=read(STUDY/'plan.json');before=source_state();assert before['commit']==plan['source_commit'] and not before['status']
project=HERE/'.build'/(plan['binary']+'.project');x=read(project/'native-descriptor.json')['descriptor'];manifest=read(project/'linked-manifest.json')['object']
assert (manifest['typed_ir_version'],manifest['abi_version'],manifest['work_policy_version'])==(91,33,69)
copies=manifest['compiled_join_map_copies'];assert len(copies)==1
copy='_'+copies[0]['symbol'];entry='_mech_canonical_program_entry_v1';ordinary='_mech_string_map_region_'+str(copies[0]['collection']);a=functions(project/'program.o')
new={name+'_'+suffix for name in [copy,ordinary] for suffix in ['full','projected']}
assert new<=a.keys() and copies[0]['geometry_words']==copies[0]['initialized_extent_word']==6
comparisons=[];review=[]
controls=[('parent',plan['parent_binary']),('byte_parent',plan['byte_parent_binary']),('ordinary',plan['ordinary_binary'])]
for label,binary in controls:
    parent=HERE/'.build'/(binary+'.project');b=functions(parent/'program.o');pm=read(parent/'linked-manifest.json')['object']
    assert set(a)==set(b)|new|(set() if label!='ordinary' else {copy})
    y=read(parent/'native-descriptor.json')['descriptor']
    for field in ['plan','visits','scalar_aggregates','borrowed_strings','closed_tails']:assert x[field]==y[field],(label,field)
    records=[]
    for name in b:
        same=a[name]==b[name];changes=[];expected=name in {ordinary,copy}
        qualified=same or expected or (label!='parent' and name==entry)
        if not qualified and name==entry and len(a[name])==len(b[name]) and len(a[name])%4==0:
            aw=struct.unpack('<'+'I'*(len(a[name])//4),a[name]);bw=struct.unpack('<'+'I'*(len(b[name])//4),b[name])
            changes=[dict(offset=i*4,previous=hex(v),current=hex(aw[i]),abi_immediate=bool(version_instruction(v,aw[i],pm['abi_version'],manifest['abi_version']))) for i,v in enumerate(bw) if v!=aw[i]]
            qualified=bool(changes) and all(c['abi_immediate'] for c in changes)
        if not qualified:review.append(dict(control=label,symbol=name))
        records.append(dict(symbol=name,candidate_bytes=len(a[name]),control_bytes=len(b[name]),identical=same,expected_mapping_change=expected,qualified=qualified,changes=changes,candidate_sha256=hashlib.sha256(a[name]).hexdigest(),control_sha256=hashlib.sha256(b[name]).hexdigest()))
    unchanged=[r for r in records if r['symbol'] not in {entry,ordinary,copy}]
    assert len(unchanged)==7 and all(r['identical'] for r in unchanged)
    comparisons.append(dict(control=label,object_sha256=process.sha(parent/'program.o'),abi_version=pm['abi_version'],functions=records))
result=dict(source=before,script_sha256=process.sha(Path(__file__)),candidate_object_sha256=process.sha(project/'program.o'),comparisons=comparisons,review_required=review,new_functions=sorted(new),entry_function=dict(symbol=entry,bytes=len(a[entry]),sha256=hashlib.sha256(a[entry]).hexdigest()),source_plan_visits_aggregate_borrowed_and_scalar_prices_identical=True,scope='Both mapping entry points dispatch to full/projected leaves; all seven counting/bridge functions must be byte-identical. Actual vector lookup counts and hoisted table loads qualify the intended physical change before full timing.')
out=STUDY/'object-disassembly-v1';assert out.is_dir()
result['static_disassembly']=[]
for label,binary in [('candidate',plan['binary']),*controls]:
    folder=out/label;obj=HERE/'.build'/(binary+'.project/program.o')
    receipt=read(folder/'process.json')
    assert receipt['command']==['/usr/bin/otool','-tvV',str(obj)]
    assert receipt['exit_status']==0 and receipt['inherited_common_mutex'] and receipt['reaped'] and receipt['group_closed'] and not receipt['signals'] and not receipt['cleanup_errors']
    result['static_disassembly'].append(dict(subject=label,folder=str(folder.relative_to(STUDY)),process_sha256=process.sha(folder/'process.json'),stdout_sha256=process.sha(folder/'stdout.bin')))
result['analysis_correction']='Recognize the disassembler opcode suffix tbl.16b as tbl; reuse all four completed native captures without recapture.'
assembly={};path=out/'candidate/stdout.bin'
for label,name in [('joined',copy),('ordinary',ordinary)]:
    full=mapping_audit(path,name+'_full',label=='joined');projected=mapping_audit(path,name+'_projected',label=='joined')
    assembly[label]=dict(full=full,projected=projected,dispatch=dispatch_audit(path,name))
    assert full['vector_lookups']==8 and projected['vector_lookups']==2
    assert full['narrowing_instructions']==projected['narrowing_instructions']==0
    assert len(assembly[label]['dispatch']['calls'])==2 and len(assembly[label]['dispatch']['conditional_branches'])==1
    if label=='joined':assert full['table_vector_registers_hoisted']==8 and projected['table_vector_registers_hoisted']==2
    if label=='joined':assert copies[0]['code_bytes']<=sum(len(a[n]) for n in [name,name+'_full',name+'_projected'])
result['assembly']=assembly;result['assembly_gate_qualified']=not review
result['status']='compact-mapping-two-lookup-leaves-full-fallback-and-unchanged-counting-qualified' if not review else 'compact-mapping-review-required'
assert source_state()==before
process.save(STUDY/'code-inspection.json',result)
print(result['status']);print('new functions',len(new));print('lookups',{k:{mode:v[mode]['vector_lookups'] for mode in ['full','projected']} for k,v in assembly.items()});print('root',result['entry_function']);print('review',review)
assert not review
