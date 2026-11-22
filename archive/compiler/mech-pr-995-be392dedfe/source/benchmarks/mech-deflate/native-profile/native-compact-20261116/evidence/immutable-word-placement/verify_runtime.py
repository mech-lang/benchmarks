"""Recompute every guarded-placement paired ratio from the original samples."""
from pathlib import Path
from hashlib import sha256
import argparse,importlib.util,json,tarfile,tempfile
HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
path=HERE.parent/'argument-jump-forwarding/verify_runtime.py'
spec=importlib.util.spec_from_file_location('immutable_word_raw_runtime',path)
raw=importlib.util.module_from_spec(spec);spec.loader.exec_module(raw)
parser=argparse.ArgumentParser(__doc__);parser.add_argument('--span',action='store_true');parser.add_argument('--delay',action='store_true');args=parser.parse_args();assert not(args.span and args.delay)
manifest=read(HERE/('delay-runtime-manifest.json' if args.delay else ('span-runtime-manifest.json' if args.span else 'runtime-manifest.json')));archive=HERE/manifest['archive']
assert sha256(archive.read_bytes()).hexdigest()==manifest['sha256']
assert archive.stat().st_size==manifest['bytes']
results=read(HERE/('delay-results.json' if args.delay else ('span-results.json' if args.span else 'measured-results.json')));recipes=read(HERE/'recipes.json')['roles']
with tempfile.TemporaryDirectory(prefix='mech-immutable-runtime-') as temporary:
 root=Path(temporary)
 with tarfile.open(archive,'r:gz') as stream:stream.extractall(root,filter='data')
 for name,pin in manifest['files_sha256'].items():assert sha256((root/name).read_bytes()).hexdigest()==pin,name
 fixtures={v['name']:v for v in read(root/'runtime/fixtures.json')}
 oracle={v['case']:v for v in read(root/'runtime/C-output-oracle.json')}
 policy=read(root/'runtime/working-selection-policy.json')
 def validate(actor,value,row):
  fixture=fixtures[row['case']]
  assert all(value[k]==fixture[k] for k in ['input_bytes','prefix_bytes'])
  assert not value['warmup'] and not value['profile']
  if actor=='libdeflate':
   assert value['level']==12 and value['version']=='1.26'
   assert all(value[k]==oracle[row['case']][k] for k in ['output_sha256','capacity','raw_bytes','matches_reference_bytes'])
  else:assert value['raw_bytes']==fixture['raw_bytes'] and value['capacity']==fixture['capacity']
 raw.VALUE_VALIDATOR=validate
 observations=zeros=0
 for campaign in results['panels'].values():
  role=campaign.get('recipe_role',campaign['plan']['role']);assert campaign['complete'] and len(campaign['runs'])==2
  assert campaign['plan']['control_worker_sha256']==recipes['control']['worker_sha256']
  assert campaign['plan']['candidate_worker_sha256']==recipes[role]['worker_sha256']
  for run in campaign['runs']:
   cases={r['case'] for r in run['results']}
   for peer,names in policy['required_peer_wins'].items():
    wins={r['case'] for r in run['results'] if r['paired_x_'+peer]['mech-experiment']<1}
    assert sorted((set(names)&cases)-wins)==run['required_named_missing'][peer]==[]
  checked,_,zero=raw.runtime(root/'runtime',campaign['runs'],21,96)
  observations+=checked;zeros+=zero
 print(observations,'runtime observations checked;',zeros,'zero durations retained; allpanelorders and paired ratios reproduced')
