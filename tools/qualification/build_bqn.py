"""Restore/build the pinned CBQN release or separate untimed work-witness runtime."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT/'experiments/bqn/optimization-v1'
COMMIT = 'c893d3e7828899a50150df03ad33c9052fa51d3c'
CC = '/opt/homebrew/opt/llvm@22/bin/clang-22'
SDK = '/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk'
COMMAND = ['/usr/bin/make','o3','REPLXX=0','FFI=1','j=2','notui=1','CC='+CC,
    'CCFLAGS=-mcpu=apple-m3 -isysroot '+SDK+' -I/opt/homebrew/opt/libffi/include',
    'lf=-L/opt/homebrew/opt/libffi/lib -Wl,-rpath,/opt/homebrew/opt/libffi/lib']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def call(command, **kwargs):
    return subprocess.check_output(command, text=True, **kwargs).strip()


def binding_command():
    return [CC,'-O3','-mcpu=apple-m3','-isysroot',SDK,'-I/opt/homebrew/include',
        '-L/opt/homebrew/lib','-lgmp','-lpcre2-8','-dynamiclib',str(HERE/'stdlib/native.c'),
        '-o',str(HERE/'stdlib/libarray-standard.dylib')]


def receipt(tree, witness):
    release = HERE/'.build/CBQN'
    library_paths = [Path('/opt/homebrew/opt/libffi/lib/libffi.8.dylib'),
                     Path('/opt/homebrew/lib/libgmp.10.dylib'),Path('/opt/homebrew/lib/libpcre2-8.0.dylib')]
    files = [tree/'BQN',HERE/'stdlib/libarray-standard.dylib',HERE/'stdlib/standard.bqn',
             HERE/'stdlib/native.c',HERE/'stdlib/khash.h',*library_paths]
    return dict(schema='bqn-runtime-build.v1', runtime_use='untimed-work-witness-only' if witness else 'release-timing',
        official_repository='https://github.com/dzaima/CBQN.git', commit=call(['git','rev-parse','HEAD'],cwd=tree),
        submodules=call(['git','submodule','status','--recursive'],cwd=release),
        release_source_status=call(['git','status','--short'],cwd=release),
        compiler=call([CC,'--version']),sdk_path=SDK,sdk_resolved=str(Path(SDK).resolve()),
        flags=COMMAND,version=call([str(tree/'BQN'),'--version']),
        generic_binding_build=binding_command(),
        bindings_scope='Unmodified retained general-purpose FFI, hash-map operations and at-most-eight-process map; no new workload kernel.',
        artifacts=[dict(path=str(p),resolved_path=str(p.resolve()),sha256=sha(p)) for p in files],
        witness_patch_sha256=sha(HERE/'work-witness/instrument-count.patch') if witness else None,
        restoration_limitation='Compiler, SDK and Homebrew dependency artifacts are hash-recorded; rebuilding with different artifacts is a different runtime configuration. Historical runtime binary was removed; compare sources in this matched rebuilt runtime rather than claiming byte identity with historical timings.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--witness',action='store_true')
    p.add_argument('--receipt-only',action='store_true',help='Inspect existing artifacts without cloning/compiling.')
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    release = HERE/'.build/CBQN'
    tree = HERE/'.build/CBQN-witness' if args.witness else release
    with open('/tmp/mech-clbg-timing.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if not args.receipt_only:
            if not release.exists():
                release.parent.mkdir(parents=True,exist_ok=True)
                subprocess.run(['git','clone','https://github.com/dzaima/CBQN.git',str(release)],check=True)
                subprocess.run(['git','checkout','--detach',COMMIT],cwd=release,check=True)
                subprocess.run(['git','submodule','update','--init','--recursive'],cwd=release,check=True)
            assert call(['git','rev-parse','HEAD'],cwd=release)==COMMIT
            assert not call(['git','status','--short'],cwd=release)
            if args.witness and not tree.exists():
                shutil.copytree(release,tree)
                subprocess.run(['/usr/bin/patch','-p1','-i',str(HERE/'work-witness/instrument-count.patch')],cwd=tree,check=True)
            subprocess.run(COMMAND,cwd=tree,check=True)
            if not args.witness:
                subprocess.run(binding_command(),check=True)
        assert call(['git','rev-parse','HEAD'],cwd=tree)==COMMIT
        value=receipt(tree,args.witness)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(value,indent=2)+'\n')
        print(json.dumps(dict(status='recorded',runtime_use=value['runtime_use'],output=str(args.output))))

if __name__=='__main__':main()
