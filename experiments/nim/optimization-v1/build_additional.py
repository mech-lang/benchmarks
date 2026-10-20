"""Compile independently pinned Nim encoding/target-CPU variants outside timing."""
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import time
import shutil

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'experiments/nim/optimization-v1'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    original=json.loads((HERE/'matched-build-plan.json').read_text())
    commands=[]
    output=HERE/'.build/additional-v1'
    assert not output.exists()
    with open('/tmp/mech-clbg-timing.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for name,base,source,native in [
            ('parent-native','parent',HERE/'.build/matched-v1/parent/knucleotide.nim',True),
            ('mgetorput-native','mgetorput',HERE/'sources/knucleotide-mgetorput.nim',True),
            ('preencoded','mgetorput',HERE/'sources/knucleotide-preencoded.nim',False),
            ('preencoded-native','mgetorput',HERE/'sources/knucleotide-preencoded.nim',True)]:
            old=next(r for r in original['commands'] if r['id']==base)
            assert sha(old['source'])==old['source_sha256']
            assert sha(old['command'][0])==original['compiler_sha256']
            for p,digest in original['pinned_native_build_dependencies'].items():assert sha(p)==digest
            folder=output/name;folder.mkdir(parents=True)
            dst=folder/'knucleotide.nim';shutil.copyfile(source,dst)
            cmd=[c.replace(str(Path(old['source']).parent),str(folder)) for c in old['command']]
            if native:cmd.insert(-1,'--passC:-mcpu=apple-m3')
            start=time.monotonic()
            with (folder/'build.stdout').open('wb') as out,(folder/'build.stderr').open('wb') as err:
                r=subprocess.run(cmd,cwd=folder,stdout=out,stderr=err,timeout=180)
            receipt=dict(schema='nim-additional-compilation.v1',id=name,command=cmd,source_sha256=sha(dst),
                compiler_sha256=original['compiler_sha256'],exit_status=r.returncode,elapsed_build_seconds=time.monotonic()-start,
                native_cpu=native,build_only=True,benchmark_processes=0,
                artifacts={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()})
            (folder/'build.json').write_text(json.dumps(receipt,indent=2)+'\n');r.check_returncode()
            commands.append(dict(id=name,source=str(dst),source_sha256=sha(dst),binary=str(folder/'knucleotide'),command=cmd))
        plan={**original,'schema':'nim-additional-build-plan.v1','commands':commands,
            'parent_build_plan_sha256':sha(HERE/'matched-build-plan.json'),
            'variants':'Preencode ASCII DNA once to uint8 via ordinary std/sequtils map; independently compare Apple M3 target codegen. No fast math or fp contraction changes.',
            'build_tool_sha256':sha(__file__)}
        (HERE/'additional-build-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
        print(json.dumps(dict(status='BUILT',variants=[r['id'] for r in commands])))

if __name__=='__main__':main()
