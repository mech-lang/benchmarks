"""Map exact sampled PCs to immutable Mach-O symbols and assembly neighborhoods."""
from pathlib import Path
from collections import Counter,defaultdict
from hashlib import sha256
import bisect,json,re,struct,subprocess,xml.etree.ElementTree as ET
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
def load_xml(path):
 tree=ET.parse(path);ids={e.attrib['id']:e for e in tree.iter() if 'id' in e.attrib}
 def resolve(e):
  while e is not None and 'ref' in e.attrib:e=ids[e.attrib['ref']]
  return e
 return tree,resolve
def macho(path):
 data=path.read_bytes();assert struct.unpack_from('<I',data)[0]==0xfeedfacf;at=32;sections=[];symtab=None;base=None
 for _ in range(struct.unpack_from('<I',data,16)[0]):
  kind,size=struct.unpack_from('<II',data,at)
  if kind==0x19:
   if data[at+8:at+24].rstrip(b'\0')==b'__TEXT':base=struct.unpack_from('<Q',data,at+24)[0]
   for j in range(struct.unpack_from('<I',data,at+64)[0]):
    sec=at+72+j*80;sections.append((data[sec:sec+16].rstrip(b'\0'),*struct.unpack_from('<QQI',data,sec+32)))
  if kind==2:symtab=struct.unpack_from('<4I',data,at+8)
  at+=size
 assert base is not None and symtab
 syms={};symoff,count,stroff,strsize=symtab
 for i in range(count):
  string,kind,section,desc,value=struct.unpack_from('<IBBHQ',data,symoff+i*16)
  if kind&0xe!=0xe or not section or sections[section-1][0]!=b'__text':continue
  end=data.index(b'\0',stroff+string,stroff+strsize);name=data[stroff+string:end].decode();syms.setdefault(name,[]).append(value)
 return base,syms

def derive(folder, binary, actor):
 plan=read(folder/'plan.json');recorded_binary=plan['command'][0];assert sha(binary)==plan['worker_sha256'];base,syms=macho(binary)
 raw,r=load_xml(folder/'time-samples.xml');pcs={};kinds=Counter()
 for row in raw.findall('.//row'):
  kind=r(row.find('time-sample-kind'));kinds[kind.text]+=1
  if kind.text!='0':continue
  stamp=int(r(row.find('sample-time')).text);thread=r(row.find('thread'));tid=int(r(thread.find('tid')).text);bt=r(row.find('kperf-bt'));pc=int(r(bt.find('text-address')).text);key=(stamp,tid)
  assert key not in pcs or pcs[key]==pc;pcs[key]=pc
 tree,r=load_xml(folder/'time-profile.xml');root='mech_compact_closed_v2' if actor=='mech' else 'libdeflate_deflate_compress';functions=Counter();sites=Counter();windows=Counter();total=0;matched=0
 for row in tree.findall('.//row'):
  stamp=int(r(row.find('sample-time')).text);thread=r(row.find('thread'));tid=int(r(thread.find('tid')).text);pc=pcs[stamp,tid];frames=[r(f) for f in r(row.find('backtrace'))];leaf=frames[0];assert int(leaf.attrib['addr'],16)==pc+1
  if not any(f.attrib.get('name')==root for f in frames):continue
  weight=int(r(row.find('weight')).text);total+=weight;name=leaf.attrib['name'];functions[name]+=weight;image=r(leaf.find('binary'))
  if image.attrib.get('path')!=recorded_binary or '_'+name not in syms:continue
  value=pc-int(image.attrib['load-addr'],16)+base;possible=[at for at in syms['_'+name] if at<=value];assert possible,(name,hex(value),syms['_'+name]);start=max(possible);offset=value-start;assert offset%4==0;matched+=1;sites[name,start,offset]+=weight;windows[name,start,offset//64*64]+=weight
 disassembly=subprocess.check_output(['otool','-tvV',str(binary)],text=True);ins={}
 for line in disassembly.splitlines():
  m=re.match(r'^([0-9a-f]{16})\s+(\S+)\s*(.*)',line)
  if m:ins[int(m[1],16)]=[m[2],m[3]]
 recorded={}
 for line in (folder/'disassembly.txt').read_text().splitlines():
  match=re.match(r'^([0-9a-f]{16})\s+(\S+)\s*(.*)',line)
  if match:recorded[int(match[1],16)]=[match[2],match[3]]
 assert ins==recorded, 'Disassembly instructions changed'
 def item(name,start,off,weight):
  at=start+off;return {'symbol':name,'symbol_address':hex(start),'offset':off,'weight_ns':weight,'encoder_fraction':weight/total,'instruction':ins.get(at),'context':[{'offset':p-start,'instruction':ins[p]} for p in range(at-12,at+20,4) if p in ins]}
 result={'actor':actor,'worker_sha256':sha(binary),'time_samples_sha256':sha(folder/'time-samples.xml'),'time_profile_sha256':sha(folder/'time-profile.xml'),'root':root,'sample_kinds':dict(kinds),'raw_timer_samples':len(pcs),'encoder_weight_ns':total,'matched_symbol_rows':matched,'exclusive_functions':dict(functions.most_common()),'top_sites':[item(name,start,off,w) for (name,start,off),w in sites.most_common(30)],'top_64_byte_windows':[{'symbol':name,'symbol_address':hex(start),'offset':off,'weight_ns':w,'encoder_fraction':w/total} for (name,start,off),w in windows.most_common(20)],'scope':'Only timer samples under the exact encoder root. Time-profile leaf addresses are checked against raw PCs (+1 symbolication convention). Asynchronous samples identify hot neighborhoods, not exact per-instruction cycle costs; code boundaries differ across compilers.'}
 (folder/'derived.json').write_text(json.dumps(result,indent=2)+'\n');print(actor,'root_ms',total/1e6,'samples',len(pcs))
 for v in result['top_sites'][:12]:print(v['symbol'],hex(v['offset']),round(v['encoder_fraction']*100,2),v['instruction'])
 for v in result['top_64_byte_windows'][:6]:print('window',v['symbol'],hex(v['offset']),round(v['encoder_fraction']*100,2))
if __name__ == '__main__':
 import argparse
 parser=argparse.ArgumentParser(__doc__);parser.add_argument('folder',type=Path);parser.add_argument('binary',type=Path);args=parser.parse_args();derive(args.folder,args.binary,read(args.folder/'plan.json')['actor'])
