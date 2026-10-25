"""Compare actual emitted Mach-O functions before primary timing."""
import hashlib
import struct
import sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import process,read,source_state

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
project=HERE/'.build'/(plan['binary']+'.project');parent=HERE/'.build'/(plan['parent_binary']+'.project')
a=functions(project/'program.o');b=functions(parent/'program.o');assert set(a)==set(b)
entry='_mech_canonical_program_entry_v1';assert entry in a and a[entry]!=b[entry]
records=[]
for name in a:
    same=a[name]==b[name]
    if name!=entry:assert same,'Scalar emitter unexpectedly changed a normalization, bridge or packed-count function'
    records.append(dict(symbol=name,candidate_bytes=len(a[name]),parent_bytes=len(b[name]),identical=same,
        candidate_sha256=hashlib.sha256(a[name]).hexdigest(),parent_sha256=hashlib.sha256(b[name]).hexdigest()))
x=read(project/'native-descriptor.json')['descriptor'];y=read(parent/'native-descriptor.json')['descriptor']
for field in ['plan','visits','scalar_aggregates','borrowed_strings','closed_tails']:
    assert x[field]==y[field],field
scalar=[dict(header=r['tail']['header'],words=r['words'],compute_price=r['compute'],comparison_price=r['comparison']) for r in x['closed_tails']['regions'] if r.get('map') is None]
manifest=read(project/'linked-manifest.json')['object']
assert len(scalar)>0 and manifest['scalar_tail_register_regions']==len(scalar)
result=dict(status='entry-changed-all-eight-nonentry-functions-identical',source=before,script_sha256=process.sha(Path(__file__)),
    candidate_object_sha256=process.sha(project/'program.o'),parent_object_sha256=process.sha(parent/'program.o'),
    functions=records,scalar_regions=scalar,source_plan_visits_aggregate_borrowed_and_fuel_layouts_identical=True,
    scope='Object function bytes include their trailing alignment padding; nonentry function bytes, not only source declarations, are compared. Entry changes include scalar loan SSA; source state/actions and prices remain identical.')
assert source_state()==before
process.save(STUDY/'code-inspection.json',result)
print(result['status']);print('entry bytes',len(b[entry]),'->',len(a[entry]));print('scalar regions',len(scalar))
