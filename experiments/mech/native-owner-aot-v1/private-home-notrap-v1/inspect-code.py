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


def load_home(text):
    m=re.fullmatch(r'ldr\s+(x\d+),\s*\[(x\d+),\s*#0x([0-9a-fA-F]+)\]',text)
    return (m[1],m[2],int(m[3],16)) if m else None

def store_home(text):
    m=re.fullmatch(r'str\s+(x\d+),\s*\[(x\d+),\s*#0x([0-9a-fA-F]+)\]',text)
    return (m[1],m[2],int(m[3],16)) if m else None

def field_sequences(path,entry):
    body=instruction_body(path,entry);dead=[];lengths=[]
    for i,(address,text) in enumerate(body[:-1]):
        a=load_home(text);b=store_home(body[i+1][1])
        if a and b and a[:2]==b[:2] and a[2]==0x910 and b[2]==0x1d0:
            lengths.append(dict(address=hex(address),instructions=[text,body[i+1][1]],preceding=body[i-1][1] if i else None))
        if i+2>=len(body):continue
        a=load_home(text);b=load_home(body[i+1][1]);c=store_home(body[i+2][1])
        if a and b and c and a[:2]==b[:2]==c[:2] and a[0]!=a[1] and b[2]==a[2]+8:
            dead.append(dict(address=hex(address),pointer_offset=hex(a[2]),length_offset=hex(b[2]),output_offset=hex(c[2]),instructions=[text,body[i+1][1],body[i+2][1]]))
    confirmed=[r for r in dead if (r['pointer_offset'],r['length_offset'],r['output_offset'])==('0x908','0x910','0x1d0')]
    return dict(confirmed_discarded_pointer_sequences=confirmed,confirmed_length_store_sequences=lengths,all_adjacent_discarded_field_sequences=dead)

from collections import Counter

def traffic(path):
    rows=instruction_body(path,entry)
    counts=Counter(text.split()[0] for address,text in rows)
    loads=sum(count for opcode,count in counts.items() if opcode.startswith(('ldr','ldp','ldur')))
    stores=sum(count for opcode,count in counts.items() if opcode.startswith(('str','stp','stur')))
    return dict(instructions=len(rows),loads=loads,stores=stores,calls=counts['blr']+counts['bl'],mnemonics=dict(sorted(counts.items())),field_sequences=field_sequences(path,entry))

plan=read(STUDY/'plan.json');before=source_state();assert before['commit']==plan['source_commit'] and not before['status']
project=HERE/'.build'/(plan['binary']+'.project');x=read(project/'native-descriptor.json')['descriptor'];manifest=read(project/'linked-manifest.json')['object']
assert (manifest['typed_ir_version'],manifest['abi_version'],manifest['work_policy_version'])==(90,32,69)
entry='_mech_canonical_program_entry_v1';copies=manifest['compiled_join_map_copies'];assert len(copies)==1;copy='_'+copies[0]['symbol'];a=functions(project/'program.o')
comparisons=[];review=[]
controls=[('parent',plan['parent_binary']),('byte_parent',plan['byte_parent_binary']),('ordinary',plan['ordinary_binary'])]
for label,binary in controls:
    parent=HERE/'.build'/(binary+'.project');b=functions(parent/'program.o')
    assert set(a)==set(b) if label!='ordinary' else set(a)==set(b)|{copy}
    y=read(parent/'native-descriptor.json')['descriptor']
    for field in ['plan','visits','scalar_aggregates','borrowed_strings','closed_tails']:assert x[field]==y[field],(label,field)
    records=[]
    for name in b:
        same=a[name]==b[name];qualified=same or name==entry
        if not qualified:review.append(dict(control=label,symbol=name))
        records.append(dict(symbol=name,candidate_bytes=len(a[name]),control_bytes=len(b[name]),identical=same,qualified=qualified,candidate_sha256=hashlib.sha256(a[name]).hexdigest(),control_sha256=hashlib.sha256(b[name]).hexdigest()))
    comparisons.append(dict(control=label,object_sha256=process.sha(parent/'program.o'),functions=records))
result=dict(source=before,script_sha256=process.sha(Path(__file__)),candidate_object_sha256=process.sha(project/'program.o'),comparisons=comparisons,review_required=review,entry_function=dict(symbol=entry,bytes=len(a[entry]),sha256=hashlib.sha256(a[entry]).hexdigest()),source_plan_visits_aggregate_borrowed_and_scalar_prices_identical=True,scope='Only root instructions may change. Private-homes notrap only; source bounds, finite prices and helper call effects remain. Static traffic counts guide manual assembly review and are not dynamic frequencies.')
out=STUDY/'object-disassembly-v1';out.mkdir(exist_ok=False)
env=read(HERE/plan['compiler']/'results.json')['environment'];result['static_disassembly']=[]
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino==83858837
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for label,binary in [('candidate',plan['binary']),*controls]:
        folder=out/label;obj=HERE/'.build'/(binary+'.project/program.o')
        receipt=process.execute(['/usr/bin/otool','-tvV',str(obj)],folder,env,lock,deadline=60,quantitative=False);assert receipt['exit_status']==0
        result['static_disassembly'].append(dict(subject=label,folder=str(folder.relative_to(STUDY)),process_sha256=process.sha(folder/'process.json'),stdout_sha256=process.sha(folder/'stdout.bin')))
result['assembly']={name:traffic(out/name/'stdout.bin') for name in ['candidate','parent','byte_parent','ordinary']}
ca=result['assembly']['candidate'];pa=result['assembly']['parent']
assert not ca['field_sequences']['confirmed_discarded_pointer_sequences']
result['static_root_reduction']=dict(instructions=pa['instructions']-ca['instructions'],loads=pa['loads']-ca['loads'],stores=pa['stores']-ca['stores'],opaque_call_count_unchanged=pa['calls']==ca['calls'])
result['status']='private-home-object-captured-awaiting-assembly-review'
assert source_state()==before
process.save(STUDY/'code-inspection.json',result)
print(result['status']);print('root',result['entry_function']);print('static reduction',result['static_root_reduction']);print('body review',review)
assert not review,'Keep captures and review changed nonentry bodies before primary timing.'
