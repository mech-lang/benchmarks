"""Inspect candidate-value code and unchanged unrelated Mach-O bodies."""
import fcntl,hashlib,json,re,struct,sys
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

def instruction_body(path,symbol):
    lines=path.read_text().splitlines();start=lines.index(symbol+':');result=[]
    for line in lines[start+1:]:
        if line and not line[0].isspace() and line.endswith(':'):break
        match=re.match(r'\s*([0-9a-fA-F]+)\s+(.+)',line)
        if match:result.append((int(match[1],16),match[2]))
    assert result
    return result

plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
project=HERE/'.build'/(plan['binary']+'.project')
parent=HERE/'.build'/(plan['parent_binary']+'.project')
separate=HERE/'.build'/(plan['separate_binary']+'.project')
x=read(project/'native-descriptor.json')['descriptor'];y=read(parent/'native-descriptor.json')['descriptor']
m=read(project/'linked-manifest.json')['object']
assert (m['typed_ir_version'],m['abi_version'],m['work_policy_version'])==(94,33,69)
for field in ['plan','visits','scalar_aggregates','borrowed_strings','closed_tails']:
    assert x[field]==y[field],field
loops=m['compiled_scalar_loops'];assert len(loops)==1,'Actual benchmark did not select the new scalar graph'
proof=loops[0];assert proof['register_words']>3 and proof['register_words']<=192
assert proof['source_sites']>0 and proof['product_nodes']<=1024
assert proof['folded_branches'] and proof['known_latches']
assert proof['maximum_source_instructions']<=512 and proof['fixed_template_instructions']<=1024
entry='_mech_canonical_program_entry_v1';a=functions(project/'program.o');b=functions(parent/'program.o')
assert set(a)==set(b) and len(a)==14
expected={'_'+r['symbol'] for r in m['compiled_steady_loops']}
assert len(expected)==2
for record in m['compiled_steady_loops']:
    assert record['candidate_value_loads']==record['paired_candidate_loads']==38
    assert record['lookup_cache_function']['candidate_value_loads']==record['lookup_cache_function']['paired_candidate_loads']==0
comparison=[]
for name in sorted(a):
    row=dict(symbol=name,candidate_bytes=len(a[name]),parent_bytes=len(b[name]),candidate_sha256=hashlib.sha256(a[name]).hexdigest(),parent_sha256=hashlib.sha256(b[name]).hexdigest(),identical=a[name]==b[name])
    comparison.append(row)
    if name not in expected:assert row['identical'],name
    else:assert not row['identical'],name
out=STUDY/'object-disassembly-v1';out.mkdir(exist_ok=False)
env=read(HERE/plan['compiler']/'results.json')['environment'];captures=[]
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino==83858837
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for label,folder in [('candidate',project),('parent',parent),('separate',separate)]:
        r=process.execute(['/usr/bin/otool','-tvV',str(folder/'program.o')],out/label,env,lock,deadline=30,quantitative=False)
        assert r['exit_status']==0
        captures.append(dict(subject=label,process_sha256=process.sha(out/label/'process.json'),assembly_sha256=process.sha(out/label/'stdout.bin')))
roots={}
for label in ['candidate','parent','separate']:
    code=[i for name in sorted(expected) for i in instruction_body(out/label/'stdout.bin',name)]
    op=lambda text:text.split()[0].split('.')[0]
    summary=dict(instructions=len(code),loads=sum(op(t) in ['ldr','ldur','ldp','ldrb','ldrh','ldrsw','ldar'] for _,t in code),stores=sum(op(t) in ['str','stur','stp','strb','strh','stlr'] for _,t in code),calls=sum(op(t) in ['bl','blr'] for _,t in code),backward_branch_intervals=[])
    addresses={a for a,_ in code}
    for address,text in code:
        if op(text) not in ['b','cbz','cbnz','tbz','tbnz'] and not text.split()[0].startswith('b.'):continue
        match=re.search(r'0x([0-9a-fA-F]+)\s*$',text)
        if not match:continue
        target=int(match[1],16)
        if target>=address or target not in addresses:continue
        interval=[(a,t) for a,t in code if target<=a<=address]
        if len(interval)<8:continue
        summary['backward_branch_intervals'].append(dict(start=hex(target),end=hex(address),instructions=len(interval),loads=sum(op(t) in ['ldr','ldur','ldp','ldrb','ldrh','ldrsw','ldar'] for _,t in interval),stores=sum(op(t) in ['str','stur','stp','strb','strh','stlr'] for _,t in interval)))
    roots[label]=summary
paired_windows={}
for name in sorted(expected):
    code=instruction_body(out/'candidate/stdout.bin',name)
    windows=[]
    for i,(address,text) in enumerate(code):
        if re.match(r'ldp\s+x\d+,\s*x\d+,\s*\[x\d+',text):
            windows.append(dict(address=hex(address),instructions=[dict(address=hex(a),assembly=t) for a,t in code[max(0,i-2):i+8]]))
    paired_windows[name]=windows
process.save(STUDY/'paired-load-placement.json',dict(source=before,object_sha256=process.sha(project/'program.o'),functions=paired_windows,scope='All non-stack integer LDP windows in both hashed functions; actual pairing must be reviewed before any primary timing.'))
result=dict(status='selected-paired-values-and-twelve-unchanged-other-functions-inspected',source=before,driver_sha256=process.sha(Path(__file__)),object_sha256=process.sha(project/'program.o'),parent_object_sha256=process.sha(parent/'program.o'),scalar_loops=loops,function_comparisons=comparison,assembly_captures=captures,hash_loop_static_code=roots,scope='Only the two hashed funded functions may change; all twelve remaining bodies including scalar source execution match the timed parent. Static totals and linear backward spans do not infer runtime speedup or prove load placement; inspect exact assembly before the primary gate.')
assert source_state()==before
process.save(STUDY/'code-inspection.json',result)
print(result['status']);print('selected graph',proof)
print('hash loop static totals',{k:{f:v for f,v in row.items() if f!='backward_branch_intervals'} for k,row in roots.items()})
