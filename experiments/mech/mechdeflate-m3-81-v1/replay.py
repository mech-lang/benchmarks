"""Replay the pinned M3 workers with the original 81-case timing protocol."""
import argparse
from hashlib import file_digest
import json
from pathlib import Path
from runpy import run_path
import shutil,subprocess,sys

HERE=Path(__file__).resolve().parent
PREVIOUS=HERE.parent/'mechdeflate-81-v1'
ROUTES=HERE.parent/'mechdeflate-phase-routes-v1'
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as stream:return file_digest(stream,'sha256').hexdigest()
def prepare(out):
    sys.path.insert(0,str(ROUTES))
    helpers=run_path(str(ROUTES/'replay_timings.py'))
    run_path(str(PREVIOUS/'replay_timings.py'))['prepare'](out,helpers)
    bindings=read(HERE/'actors/bindings.json')
    for role,files in bindings.items():
        bound=out/'actors'/role/'bound';bound.mkdir(parents=True,exist_ok=True)
        for name,digest in files.items():
            source=HERE/'actors'/role/name
            assert sha(source)==digest
            shutil.copyfile(source,bound/name)
        (bound/'mech-worker').chmod(0o755)
    source=HERE/'support/controller.py'
    assert sha(source)==read(HERE/'protocol.json')['controller_sha256']
    shutil.copyfile(source,out/'controller.py')
    return bindings
def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--candidate-bound',type=Path,help='Use the bound directory emitted by rebuild.py.')
    args=parser.parse_args();out=args.output.resolve()
    if out.exists() and any(out.iterdir()):parser.error('Choose a new or empty directory.')
    out.mkdir(parents=True,exist_ok=True);prepare(out)
    candidate=args.candidate_bound.resolve() if args.candidate_bound else out/'actors/llvm-root/bound'
    if args.prepare_only:
        print('Pinned workers, peers, original fixtures, oracle and controller prepared:',out);return
    name='m3-llvm';runs=[]
    for order in ['forward','reverse']:
        command=[sys.executable,'-B',str(out/'controller.py'),name+'-'+order,str(out/'actors/control/bound'),str(candidate)]
        if order=='reverse':command.append(order)
        subprocess.run(command,check=True)
        folder=out/(name+'-'+order);summary=read(folder/'summary.json')
        runs.append({'order':order,'summary_sha256':sha(folder/'summary.json'),'results':summary})
        print(order,{p:sum(v['paired_x_'+p]['mech-experiment']<1 for v in summary) for p in ['roc','libdeflate']})
    (out/(name+'-results.json')).write_text(json.dumps({'complete':True,'runs':runs,'blocks_per_case':96,'controller_sha256':sha(out/'controller.py')},indent=2)+'\n')
    subprocess.run([sys.executable,'-B',str(ROUTES/'verify_timings.py'),str(out),name,str(out/'pinned-peers/libdeflate-output-oracle.json')],check=True)
if __name__=='__main__':main()
