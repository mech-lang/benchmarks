"""Verify exact profile input hashes, encoder observations and raw-PC mappings."""
from pathlib import Path
from hashlib import sha256
import gzip,json,subprocess,sys
HERE=Path(__file__).resolve().parent
DATA=HERE/'profile-data'
read=lambda p:json.loads(p.read_text())
manifest=read(DATA/'manifest.json')
for actor,spec in manifest['actors'].items():
 folder=DATA/actor
 for name,pin in spec['files_sha256'].items():assert sha256((folder/name).read_bytes()).hexdigest()==pin,(actor,name)
 calls=0
 with gzip.open(folder/'observations.json.gz','rt') as stream:
  for line in stream:
   row=json.loads(line);assert row['case']=='prefix-random-1048576' and not row['warmup'] and not row['profile']
   assert row['independent_inflation'] and row['input_alias_unchanged'] and row['borrowed_output_alias_unchanged']
   if actor=='mech':assert row['exact_reference']
   calls+=1
 assert calls==spec['verified_calls']==1000
 subprocess.run([sys.executable,str(HERE/'derive_pc_samples.py'),str(folder),str(folder/'worker')],check=True,stdout=subprocess.DEVNULL)
 assert sha256((folder/'derived.json').read_bytes()).hexdigest()==spec['files_sha256']['derived.json']
 print(actor,calls,'verified encodes; raw PC/symbol/assembly mapping reproduced exactly')
