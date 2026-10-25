"""Read-only audit of the exact retained direct-copy object before changing it."""
import hashlib,json,re
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
path=HERE/'joined-transform-copy-v1/object-disassembly-v1/candidate/stdout.bin'
inspection=load(HERE/'joined-transform-copy-v1/code-inspection.json')
pin=next(r for r in inspection['static_disassembly'] if r['folder'].endswith('/candidate'))
assert sha(path)==pin['stdout_sha256']
lines=path.read_text().splitlines();start=lines.index('_mech_join_map_copy_region_0:')
body=[]
for line in lines[start+1:]:
    if line and not line[0].isspace() and line.endswith(':'):break
    match=re.match(r'\s*([0-9a-fA-F]+)\s+(.+)',line)
    if match:body.append((int(match[1],16),match[2]))
assert body[0][0]==0x280
setup=[(a,s) for a,s in body if 0x46c<=a<=0x4d4]
narrows=[(a,s) for a,s in setup if s.split()[0].startswith('uqxtn')]
reloads=[(a,s) for a,s in setup if s.split()[0] in {'ldr','ldur','ldp'} and s.split()[1].startswith('q') and '[sp' in s]
constants=[(a,s) for a,s in setup if s.split()[0].startswith('movi')]
assert len(setup)==27 and len(narrows)==16 and len(reloads)==3 and len(constants)==8
assert dict(body)[0x61c]=='b\t0x378'
raw=[(a,s) for a,s in body if 0x320<=a<=0x368 and s.startswith('ldr\tq')]
assert len(raw)==16
normalized=[(i,re.sub(r'\s+',' ',line.strip())) for i,line in enumerate(lines)]
waste=[]
for index,(_,line) in enumerate(normalized[:-2]):
    if line.endswith('ldr x0, [x23, #0x908]'):
        triple=normalized[index:index+3]
        if triple[1][1].endswith('ldr x0, [x23, #0x910]') and triple[2][1].endswith('str x0, [x23, #0x1d0]'):
            waste.append([text for _,text in triple])
assert waste
result=dict(status='exact-object-repeated-table-conversion-and-unused-field-load-confirmed',source=inspection['source'],object_sha256=inspection['candidate_object_sha256'],disassembly_sha256=sha(path),script_sha256=sha(Path(__file__)),table_raw_vector_loads_before_row_loop=len(raw),per_active_row_setup_instructions=len(setup),per_active_row_narrowing_instructions=len(narrows),per_active_row_stack_vector_reloads=len(reloads),per_active_row_stack_read_bytes=48,per_active_row_constants=len(constants),setup=[dict(address=hex(a),instruction=s) for a,s in setup],row_backedge=dict(address='0x61c',target='0x378'),unused_pointer_load_sequences=waste,scope='Static instruction placement in the exact retained object. No elapsed saving is inferred.')
(STUDY/'byte-table-baseline-inspection.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:result[k] for k in ['status','per_active_row_setup_instructions','per_active_row_narrowing_instructions','per_active_row_stack_vector_reloads']})
