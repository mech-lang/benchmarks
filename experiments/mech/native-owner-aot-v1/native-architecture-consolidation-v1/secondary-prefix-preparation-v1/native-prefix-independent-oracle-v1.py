"""Read retained data only; derive an oracle without running any subject executable."""
from collections import Counter
from pathlib import Path
import hashlib,json,struct
ROOT=Path('/private/tmp/mech-benchmark-publication')
BASE=ROOT/'experiments/mech/native-owner-aot-v1'
DATA=BASE/'rust-span-diagnostic-v2/input.fasta'
EXPECTED=BASE/'rust-span-diagnostic-v2/expected.txt'

def pin(path):
 h=hashlib.sha256();size=0
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block);size+=len(block)
 return {'path':str(path),'sha256':h.hexdigest(),'bytes':size}

def require(value,message):
 if not value:raise ValueError(message)

def selected_record(path,limit=None):
 sequence=bytearray();headers=[];selected=False
 with path.open('rb') as f:
  for raw in f:
   line=raw.rstrip(b'\r\n')
   if line.startswith(b'>'):
    headers.append(line.decode('ascii'))
    if selected:break
    selected=line==b'>THREE' or line.startswith((b'>THREE ',b'>THREE\t'))
   elif selected:
    sequence.extend(line)
    if limit is not None and len(sequence)>=limit:return bytes(sequence[:limit]),headers
 return bytes(sequence),headers

sequence,headers=selected_record(DATA)
require(len(sequence)==1000000 and len(headers)==1 and DATA.read_bytes().endswith(b'\n'),'Unexpected retained FASTA structure')
require(set(sequence.upper())<=set(b'ACGT'),'Non-DNA input')
full=ROOT/'experiments/janet/.build/inputs/fasta-n25000000.stdin'
full_prefix,full_headers=selected_record(full,len(sequence))
require(sequence==full_prefix,'Retained record differs from the full input THREE prefix')
sequence=sequence.upper();n=len(sequence)
counts={k:Counter(sequence[i:i+k] for i in range(n-k+1)) for k in (1,2)}

def percentage(value,total):
 # Mech source computes f64 100.0 * value / total; Rust reference computes
 # rounded f32 (100 * value) / total. Verify both independent representations
 # format identically for this input (the A frequency is a decimal half case).
 f32=lambda x:struct.unpack('f',struct.pack('f',x))[0]
 mech=format(100.0*value/total,'.3f')
 rust=format(f32(f32(100*value)/f32(total)),'.3f')
 require(mech==rust,'Mech/Rust percentage rounding differs on this input')
 return mech

parts=[]
for k in (1,2):
 require(len(set(counts[k].values()))==len(counts[k]),'Frequency ties would require checking both subjects ordering')
 parts.append(''.join(f'{key.decode()} {percentage(value,n-k+1)}\n' for key,value in sorted(counts[k].items(),key=lambda item:(-item[1],item[0])))+'\n')
queries=['GGT','GGTA','GGTATT','GGTATTTTAATT','GGTATTTTAATTTATAGT'];query_counts={}
for query in queries:
 count=0;position=0;needle=query.encode()
 while True:
  found=sequence.find(needle,position)
  if found<0:break
  count+=1;position=found+1
 query_counts[query]=count
parts.append(''.join(f'{query_counts[q]}\t{q}\n' for q in queries))
oracle=''.join(parts).encode();require(oracle==EXPECTED.read_bytes(),'Independently derived output differs')
Path('/private/tmp/native-prefix-independent-oracle-v1.txt').write_bytes(oracle)
widths=[1,2,*map(len,queries)];updates=[n-k+1 for k in widths]
report={'input':pin(DATA),'expected_output':pin(EXPECTED),'independent_oracle':pin(Path('/private/tmp/native-prefix-independent-oracle-v1.txt')),
 'oracle_method':'Independent byte-window Counter for widths1/2; overlapping byte search for queries; independent f64 and rounded f32 percentage paths agree; no subject executable invoked',
 'headers':headers,'record_bases':n,'uppercase_record_sha256':hashlib.sha256(sequence).hexdigest(),
 'full_input':pin(full),'full_headers_before_selected_record':full_headers,'exact_THREE_prefix_of_full_input':True,
 'frequency_counts':{str(k):{a.decode():b for a,b in sorted(v.items())} for k,v in counts.items()},'query_counts':query_counts,
 'histogram_widths':widths,'updates_per_histogram':updates,'expected_updates':sum(updates),'update_derivation':'sum(N-k+1), k=[1,2,3,4,6,12,18] = 7*N-39',
 'funded_batch_capacity':1024,'expected_funded_batches':sum((value+1023)//1024 for value in updates),
 'batch_derivation':'sum(ceil((N-k+1)/1024)) with ample retained finite work caps; this is a diagnostic check, not a new budget',
 'execution_observations':0,'primary_timing_samples':0}
Path('/private/tmp/native-prefix-independent-oracle-v1.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:report[key] for key in ['record_bases','exact_THREE_prefix_of_full_input','expected_updates','expected_funded_batches','query_counts']},indent=2))
print('Independent oracle matches retained output byte-for-byte; no subject executable invoked.')
