"""Retain exact runtime refill code for comparing the mutex callback paths."""
import hashlib,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
OUT=HERE/'refill-fastpath-codegen-audit-v1'
records={}
sha=lambda data:hashlib.sha256(data).hexdigest()
for label,stem in [('baseline','lookup-split'),('candidate','refill-fastpath')]:
 build=json.loads((HERE/f'profile-{stem}-build-v1/results.json').read_text())
 binary=Path(build['binary'])
 assert sha(binary.read_bytes())==build['binary_sha256']
 assert build['whole_machine_code_matches_timed']
 command=['/usr/bin/nm',str(binary)]
 names=subprocess.check_output(command,text=True)
 symbols=[line.split()[-1] for line in names.splitlines() if 'program_packed_map' in line and ('6refill' in line or '10RefillPlan5debit' in line) and 'drop_in_place' not in line]
 assert symbols and len(symbols)<=8,symbols
 functions=[]
 for index,symbol in enumerate(symbols):
  command=['/usr/bin/otool','-tvV','-p',symbol,str(binary)]
  raw=subprocess.check_output(command)
  lines=raw.decode().splitlines(); start=lines.index(symbol+':')
  end=next((i for i in range(start+1,len(lines)) if lines[i].endswith(':')),len(lines))
  retained=('\n'.join(lines[start:end])+'\n').encode()
  path=OUT/f'{label}-refill-{index}.s'; path.write_bytes(retained)
  instructions=[(m[1],m[2]) for line in lines[start+1:end] if (m:=re.match(r'^([0-9a-fA-F]{16})\s+(.+)$',line))]
  functions.append(dict(symbol=symbol,path=str(path.relative_to(HERE)),sha256=sha(retained),command=command,raw_output_sha256=sha(raw),instructions=len(instructions),divisions=[dict(address=at,instruction=text) for at,text in instructions if text.startswith('udiv')]))
 records[label]=dict(binary_sha256=build['binary_sha256'],timed_machine_code_sha256=build['machine_code_sha256'],functions=functions)
result=dict(status='runtime-refill-disassembly-retained',records=records,script_sha256=sha(Path(__file__).read_bytes()),scope='Static runtime code of each exact-machine-code profiling copy. Division presence does not establish dynamic branch frequency or elapsed-time savings.')
(OUT/'runtime-refill.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:[dict(instructions=f['instructions'],divisions=len(f['divisions'])) for f in v['functions']] for k,v in records.items()}))
