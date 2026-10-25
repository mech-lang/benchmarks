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

plan=read(STUDY/'plan.json');before=source_state();assert before['commit']==plan['source_commit'] and not before['status']
project=HERE/'.build'/(plan['binary']+'.project')
x=read(project/'native-descriptor.json')['descriptor'];manifest=read(project/'linked-manifest.json')['object']
copies=manifest['compiled_join_map_copies'];assert len(copies)==1
added={'_'+row['symbol'] for row in copies};a=functions(project/'program.o');assert added<=set(a)
assert all(row['geometry_words']==row['initialized_extent_word']==6 for row in copies)
entry='_mech_canonical_program_entry_v1'
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
comparisons=[];review=[]
for label,binary in [('parent',plan['parent_binary']),('ordinary',plan['ordinary_binary'])]:
 parent=HERE/'.build'/(binary+'.project');b=functions(parent/'program.o')
 assert set(a)==set(b)|added and not set(b)&added
 y=read(parent/'native-descriptor.json')['descriptor'];pm=read(parent/'linked-manifest.json')['object']
 for field in ['plan','visits','scalar_aggregates','borrowed_strings','closed_tails']:assert x[field]==y[field],(label,field)
 records=[]
 for name in b:
  same=a[name]==b[name];changes=[];qualified=same or name==entry
  if not qualified and len(a[name])==len(b[name]) and len(a[name])%4==0:
   aw=struct.unpack('<'+'I'*(len(a[name])//4),a[name]);bw=struct.unpack('<'+'I'*(len(b[name])//4),b[name])
   changes=[dict(offset=i*4,previous=hex(v),current=hex(aw[i]),abi_immediate=bool(version_instruction(v,aw[i],pm['abi_version'],manifest['abi_version']))) for i,v in enumerate(bw) if v!=aw[i]]
   qualified=bool(changes) and all(c['abi_immediate'] for c in changes)
  if not qualified:review.append(dict(control=label,symbol=name))
  records.append(dict(symbol=name,candidate_bytes=len(a[name]),control_bytes=len(b[name]),identical=same,qualified=qualified,changes=changes,candidate_sha256=hashlib.sha256(a[name]).hexdigest(),control_sha256=hashlib.sha256(b[name]).hexdigest()))
 comparisons.append(dict(control=label,object_sha256=process.sha(parent/'program.o'),abi_version=pm['abi_version'],functions=records))
result=dict(status='direct-copy-function-and-existing-bodies-or-ABI-gates-qualified' if not review else 'changed-body-inspection-required',source=before,script_sha256=process.sha(Path(__file__)),candidate_object_sha256=process.sha(project/'program.o'),compiled_join_map_copies=copies,added_functions=[dict(symbol=name,bytes=len(a[name]),sha256=hashlib.sha256(a[name]).hexdigest()) for name in sorted(added)],comparisons=comparisons,review_required=review,source_plan_visits_aggregate_borrowed_and_scalar_prices_identical=True,scope='Compare actual Mach-O function bytes against BOTH old binaries. Every existing nonentry body must be identical or differ only by an exact ABI-version movz/cmp immediate. Unknown changes stop before primary timing. New direct-copy code is separately retained and tested; no source table/update is removed.')
out=STUDY/'object-disassembly-v1';out.mkdir(exist_ok=False)
env=read(HERE/plan['compiler']/'results.json')['environment'];result['static_disassembly']=[]
with Path(PLAN['common_mutex']).open('a+') as lock:
 assert Path(PLAN['common_mutex']).stat().st_ino==83858837
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for label,binary in [('candidate',plan['binary']),('parent',plan['parent_binary']),('ordinary',plan['ordinary_binary'])]:
  folder=out/label;obj=HERE/'.build'/(binary+'.project/program.o')
  receipt=process.execute(['/usr/bin/otool','-tvV',str(obj)],folder,env,lock,deadline=60,quantitative=False)
  assert receipt['exit_status']==0
  result['static_disassembly'].append(dict(subject=label,folder=str(folder.relative_to(STUDY)),process_sha256=process.sha(folder/'process.json'),stdout_sha256=process.sha(folder/'stdout.bin')))
assert source_state()==before
process.save(STUDY/'code-inspection.json',result)
print(result['status']);print('new functions',result['added_functions']);print('review',review)
assert not review,'Unqualified nonentry instruction changes require a versioned assembly review before timing'
