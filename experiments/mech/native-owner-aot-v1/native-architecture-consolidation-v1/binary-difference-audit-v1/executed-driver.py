#!/usr/bin/env python3
"""Inspect the exact timed Mach-O files without rebuilding or executing them."""
import collections
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tomllib

ROOT = Path('/private/tmp/benchmarks-native-consolidation/experiments/mech/native-owner-aot-v1')
CODE = ROOT/'native-architecture-consolidation-v1'
OUT = CODE/'binary-difference-audit-v1'
RECEIPTS = dict(
    I=CODE/'baseline-builds/published-a093aea-v1/public-aot.json',
    A=CODE/'candidate-builds/published-7543c56-v1/public-aot.json',
    C=ROOT/'post-native-architecture-cleanup-v1/candidate-builds/published-a68fb2e-v1/public-aot.json')

def digest(data): return hashlib.sha256(data).hexdigest()
def sha(path): return digest(Path(path).read_bytes())
def read(path): return json.loads(Path(path).read_text())
def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def string(raw): return raw.split(b'\0',1)[0].decode()

class Image:
    def __init__(self,path):
        self.path=Path(path);self.data=self.path.read_bytes()
        header=struct.unpack_from('<IiiIIIII',self.data)
        assert header[0]==0xfeedfacf and header[1]==0x100000c
        self.sections={};self.segments={};self.commands=[];self.symtab=None;self.function_starts=[]
        offset=32
        for _ in range(header[4]):
            command,size=struct.unpack_from('<II',self.data,offset)
            self.commands.append(dict(command=hex(command),size=size,offset=offset))
            if command==0x19:
                _,_,name,addr,vmsize,fileoff,filesize,maxprot,initprot,nsects,flags=struct.unpack_from('<II16sQQQQiiII',self.data,offset)
                name=string(name)
                self.segments[name]=dict(address=addr,vm_size=vmsize,file_offset=fileoff,file_size=filesize)
                for index in range(nsects):
                    section=struct.unpack_from('<16s16sQQIIIIIIII',self.data,offset+72+80*index)
                    sect,seg=map(string,section[:2])
                    row=dict(address=section[2],size=section[3],offset=section[4],alignment=section[5],
                             relocation_offset=section[6],relocation_count=section[7],flags=section[8])
                    if row['flags']&0xff not in (1,0xc,0x12):
                        row['sha256']=digest(self.data[row['offset']:row['offset']+row['size']])
                    self.sections[(seg,sect)]=row
            elif command==2:
                _,_,*self.symtab=struct.unpack_from('<IIIIII',self.data,offset)
            elif command==0x1b:
                self.uuid=self.data[offset+8:offset+24].hex()
            elif command==0x26:
                _,_,start,length=struct.unpack_from('<IIII',self.data,offset)
                raw=self.data[start:start+length];value=shift=0;address=self.segments['__TEXT']['address']
                for byte in raw:
                    value|=(byte&127)<<shift
                    if byte&128:shift+=7;continue
                    if not value:break
                    address+=value;self.function_starts.append(address);value=shift=0
            offset+=size
        assert offset==32+header[5]

    def section(self,name):
        key=next(k for k in self.sections if k[1]==name)
        row=self.sections[key]
        return row,self.data[row['offset']:row['offset']+row['size']]

    def symbols(self):
        if self.symtab is None:return []
        symoff,nsyms,stroff,strsize=self.symtab
        strings=self.data[stroff:stroff+strsize];rows=[]
        for index in range(nsyms):
            strx,kind,section,desc,value=struct.unpack_from('<IBBHQ',self.data,symoff+16*index)
            name=string(strings[strx:])
            rows.append(dict(name=name,type=kind,section=section,address=value))
        return rows

def guest_proof(obj,exe):
    section,guest=obj.section('__text');linked_section,linked=exe.section('__text')
    relocations=[]
    for index in range(section['relocation_count']):
        address,bits=struct.unpack_from('<iI',obj.data,section['relocation_offset']+8*index)
        assert address>=0
        relocations.append(dict(offset=address,size=1<<((bits>>25)&3),kind=bits>>28,
                                external=bool(bits&(1<<27)),symbol_index=bits&0xffffff))
    mask=bytearray(b'\1'*len(guest))
    for row in relocations:
        mask[row['offset']:row['offset']+row['size']]=b'\0'*row['size']
    runs=[];start=None
    for index,present in enumerate(mask+b'\0'):
        if present and start is None:start=index
        if not present and start is not None:runs.append((start,index));start=None
    anchor_start,anchor_end=max(runs,key=lambda row:row[1]-row[0])
    anchor=guest[anchor_start:anchor_end]
    found=[];position=linked.find(anchor)
    while position!=-1:
        candidate=position-anchor_start
        if candidate>=0 and candidate+len(guest)<=len(linked):
            emitted=linked[candidate:candidate+len(guest)]
            if all(a==b for a,b,keep in zip(guest,emitted,mask) if keep):found.append(candidate)
        position=linked.find(anchor,position+1)
    assert len(found)==1,(exe.path,found,len(anchor))
    offset=found[0];emitted=linked[offset:offset+len(guest)]
    changed=[i for i,(a,b) in enumerate(zip(guest,emitted)) if a!=b]
    assert all(not mask[i] for i in changed)
    symbols=sorted([s for s in obj.symbols() if s['section']==1 and s['type']&0xe==0xe],key=lambda s:s['address'])
    functions=[]
    for index,symbol in enumerate(symbols):
        a=symbol['address']-section['address']
        b=(symbols[index+1]['address']-section['address']) if index+1<len(symbols) else len(guest)
        original=guest[a:b];relocated=emitted[a:b]
        functions.append(dict(name=symbol['name'],object_offset=a,size=b-a,
                              executable_address=linked_section['address']+offset+a,
                              byte_identical=original==relocated,
                              nonrelocation_bytes_identical=all(x==y for x,y,keep in zip(original,relocated,mask[a:b]) if keep),
                              relocation_count=sum(a<=r['offset']<b for r in relocations)))
    return dict(guest_text_bytes=len(guest),linked_file_offset=linked_section['offset']+offset,
                linked_address=linked_section['address']+offset,
                relocation_records=relocations,relocated_byte_differences=len(changed),
                nonrelocation_bytes_identical=True,functions=functions,
                guest_text_sha256=digest(guest),linked_guest_text_sha256=digest(emitted))

OUT.mkdir(exist_ok=False)
reports={};images={}
for subject,path in RECEIPTS.items():
    receipt=read(path);image=Image(receipt['executable']);images[subject]=image
    assert digest(image.data)==receipt['executable_sha256']
    project=Path(receipt['executable']+'.project');obj=Image(project/'program.o')
    manifest=tomllib.loads((project/'Cargo.toml').read_text())
    report=dict(source=receipt['source'],executable=receipt['executable'],executable_sha256=digest(image.data),
                file_bytes=len(image.data),uuid=image.uuid,
                sections={seg+','+sect:row for (seg,sect),row in image.sections.items()},
                defined_symbols=[s for s in image.symbols() if s['section']],
                function_start_count=len(image.function_starts),
                rust_release_profile=manifest['profile']['release'],
                dependency_features={key:value.get('features',[]) if isinstance(value,dict) else [] for key,value in manifest['dependencies'].items()},
                direct_dependencies=sorted(manifest['dependencies']),
                project_inputs={str(p.relative_to(project)):sha(p) for p in project.rglob('*') if p.is_file()},
                main_rs_lines=len((project/'src/main.rs').read_text().splitlines()),
                guest=guest_proof(obj,image),
                dynamic_libraries=subprocess.check_output(['otool','-L',receipt['executable']],text=True).splitlines()[1:])
    reports[subject]=report
    save(subject+'.json',report)
    print(subject,'bytes',report['file_bytes'],'text',image.sections[('__TEXT','__text')]['size'],
          'guest functions',len(report['guest']['functions']),'guest text verified',report['guest']['guest_text_bytes'],flush=True)
comparisons=[]
for before,after in [('I','A'),('A','C')]:
    a,b=reports[before],reports[after]
    comparisons.append(dict(before=before,after=after,file_bytes_delta=b['file_bytes']-a['file_bytes'],
        section_size_delta={key:b['sections'][key]['size']-a['sections'].get(key,dict(size=0))['size'] for key in b['sections']},
        same_release_profile=a['rust_release_profile']==b['rust_release_profile'],
        same_direct_dependencies=a['direct_dependencies']==b['direct_dependencies'],
        same_guest_text_after_relocations_removed=True,
        guest_functions_byte_identical=[f['name'] for f in b['guest']['functions'] if f['byte_identical']]))
save('result.json',dict(schema='mech.exact-timed-binary-difference-audit.v1',
    status='passed-three-exact-executables-linked-guest-text-verified',
    rebuilt_or_executed_subjects=False,subjects={s:dict(path=s+'.json',sha256=sha(OUT/(s+'.json'))) for s in reports},
    comparisons=comparisons,performance_causality_established=False,
    limitation='Public executables intentionally strip Rust symbols. Named host-function growth needs a separate diagnostic link map; section growth alone cannot identify its function or prove a runtime cost.'))
for subject,path in RECEIPTS.items():assert sha(read(path)['executable'])==reports[subject]['executable_sha256']
print(json.dumps(comparisons,indent=2))
