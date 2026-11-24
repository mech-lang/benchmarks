"""Rebuild the qualified M3 encoder and its complete timing executable."""
import argparse
from hashlib import file_digest
import json,os
from pathlib import Path
import shutil,subprocess,sys,time

HERE=Path(__file__).resolve().parent
PROFILE_SETTINGS=('MECH_COMPACT_PHASE_BLOCK_LAYOUT','MECH_COMPACT_PHASE_REGISTER_WEIGHTS')
def read(path): return json.loads(path.read_text())
def sha(path):
    with path.open('rb') as stream: return file_digest(stream,'sha256').hexdigest()
def checked(path,want):
    got=sha(path)
    if got!=want: raise ValueError(f'{path}: expected {want}, got {got}')
    return got
def run(command,log,env=None,cwd=None):
    with log.open('w') as stream:
        subprocess.run(command,stdout=stream,stderr=stream,env=env,cwd=cwd,check=True)
def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--mech-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--target-dir',type=Path,help='Reuse a Cargo dependency directory.')
    parser.add_argument('--compiler',type=Path,help='Select a driver after resolving the locked build dependencies.')
    args=parser.parse_args()
    recipe=read(HERE/'recipe.json');root=args.mech_root.resolve();out=args.output.resolve()
    if (os.uname().sysname,os.uname().machine)!=('Darwin','arm64'):parser.error('Apple Silicon macOS is required.')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    if commit!=recipe['source_commit']:parser.error('Check out Mech '+recipe['source_commit'])
    if subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=root).returncode:parser.error('Use a clean pinned Mech checkout.')
    checked(root/recipe['codec_source'],recipe['codec_source_sha256'])
    if out.exists() and any(out.iterdir()):parser.error('Choose a new or empty output directory.')
    out.mkdir(parents=True,exist_ok=True)
    env={k:v for k,v in os.environ.items() if not k.startswith(('MECH_','CARGO_PROFILE_'))
         and k not in {'RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER','CARGO_BUILD_TARGET'}}
    env.update(recipe['compiler']['environment'])
    rust=recipe['compiler']['toolchain']
    rustc=subprocess.check_output(['rustc','+'+rust,'-vV'],text=True)
    if 'commit-hash: '+recipe['compiler']['rustc_commit'] not in rustc:parser.error('Install the pinned Rust toolchain.')
    sysroot=Path(subprocess.check_output(['rustc','+'+rust,'--print','sysroot'],text=True).strip())
    llvm_bin=sysroot/'lib/rustlib'/recipe['compiler']['target']/'bin'
    for name,digest in recipe['llvm_tools_sha256'].items():checked(llvm_bin/name,digest)
    driver=out/'compiler-driver';driver.mkdir()
    root_string=json.dumps(str(root),ensure_ascii=False)[1:-1]
    for name,digest in recipe['compiler']['inputs_sha256'].items():
        source=HERE/'compiler-driver'/name;checked(source,digest)
        (driver/name).write_text(source.read_text().replace('@MECH_ROOT@',root_string))
    target=args.target_dir.resolve() if args.target_dir else out/'target'
    command=['cargo','+'+rust,'build','--locked','--release','--message-format=json-render-diagnostics',
             '--config','profile.release.package.libmimalloc-sys.opt-level=1',
             '--manifest-path',str(driver/'Cargo.toml'),'--target-dir',str(target),'--bin','compile_profile']
    # Preserve the repository's compiler flags and select the actual dependency
    # artifacts from Cargo, including when the cache has other feature variants.
    with (out/'compiler-artifacts.jsonl').open('w') as stdout,(out/'compiler-build.log').open('w') as stderr:
        subprocess.run(command,stdout=stdout,stderr=stderr,env=env,cwd=root,check=True)
    cargo_libraries={}
    for line in (out/'compiler-artifacts.jsonl').read_text().splitlines():
        message=json.loads(line)
        if message.get('reason')=='compiler-artifact':
            libraries=[Path(name) for name in message['filenames'] if name.endswith('.rlib')]
            if libraries:cargo_libraries[message['target']['name']]=libraries
    compiler=args.compiler.resolve() if args.compiler else target/'release/compile_profile'
    runtime=out/'runtime.rs'
    runtime.write_text('pub mod native_artifact {\n #[path = '+json.dumps(str(root/'hosts/gpu/src/native_artifact/compact_runtime/mod.rs'))+']\n pub mod compact_runtime;\n}\n')
    library=out/'libmech_gpu_runtime.rlib';runtime_env=env|{'MECH_INLINE_OWNER_RECORDS':'12'}
    runtime_command=['rustc','+'+rust,'--edition=2024','-C','opt-level=3','-D','warnings',str(runtime)]
    run(runtime_command+['--test','-o',str(out/'runtime-tests')],out/'runtime-test-build.log',runtime_env)
    run([str(out/'runtime-tests')],out/'runtime-tests.log')
    run(runtime_command+['--crate-type','rlib','--crate-name','mech_gpu','-o',str(library)],out/'runtime-build.log',runtime_env)
    flags=recipe['flags'].copy();used=set()
    for setting in PROFILE_SETTINGS:
        entries=[]
        for item in flags[setting].split(';'):
            symbol,relative=item.split('@',1);checked(HERE/relative,recipe['profile_inputs_sha256'][relative]);used.add(relative)
            entries.append(symbol+'@'+str(HERE/relative))
        flags[setting]=';'.join(entries)
    assert used==set(recipe['profile_inputs_sha256'])
    flags['MECH_PROFILE_LLVM_BIN']=str(llvm_bin)
    bound=out/'bound';bound.mkdir()
    for name in ['mech-worker.rs','pinned_allocator.rs']:
        checked(HERE/'support'/name,recipe['support_sha256'][name]);shutil.copyfile(HERE/'support'/name,bound/name)
    allocator=HERE/'support/mimalloc-2.1.7.o';checked(allocator,recipe['support_sha256']['mimalloc-2.1.7.o'])
    source_start=time.perf_counter()
    command=[str(compiler),str(root/recipe['codec_source']),str(out/'frontend'),'compact']
    run(command,out/'encoder-build.log',env|flags,root)
    artifacts={name:checked(out/'frontend'/name,digest) for name,digest in recipe['artifacts'].items()}
    object_done=time.perf_counter()
    for name in artifacts:shutil.copyfile(out/'frontend'/name,bound/name)
    deps=target/'release/deps';externs={'mech_gpu':library}
    for crate in ['mech_engine','serde','serde_json','miniz_oxide']:
        paths=cargo_libraries.get(crate,[])
        if len(paths)!=1:raise ValueError(f'Expected one {crate} library in {deps}, got {paths}')
        externs[crate]=paths[0]
    link=['rustc','+'+rust,'--edition=2024','-C','opt-level=3','-D','warnings','-L','dependency='+str(deps),str(bound/'mech-worker.rs'),
          '-o',str(bound/'mech-worker'),'-C','link-arg='+str(allocator),'-C','link-arg='+str(bound/'program.o')]
    for crate,path in externs.items():link+=['--extern',crate+'='+str(path)]
    run(link,out/'worker-build.log',env)
    complete=time.perf_counter()
    record={'source_commit':commit,'compiler_sha256':sha(compiler),'artifacts':artifacts,
            'worker_sha256':sha(bound/'mech-worker'),'source_through_executable_seconds':complete-source_start,
            'source_through_object_seconds':object_done-source_start,'worker_link_seconds':complete-object_done,
            'scope':'Source through complete timing executable, with compiler and host/runtime dependencies prebuilt.',
            'encoder_command':command,'worker_command':link,'llvm_tools_sha256':recipe['llvm_tools_sha256']}
    (out/'reproduction.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
if __name__=='__main__':main()
