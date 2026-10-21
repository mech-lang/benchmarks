#!/usr/bin/env python3
"""Compile exact Gleam candidates and compare complete bounded outputs; no timings admitted."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOCK = Path('/private/tmp/mech-clbg-timing.lock')
PROCESS = ROOT/'experiments/elixir/rolling-v1/qualification-v1/native_process.py'
REFERENCES = ROOT/'experiments/implementation-audit/remaining-v1/native_bounded.py'
BUILD = HERE/'.build/native-v1'
TOOL = HERE/'.build/toolchain-v1'
COMPILER = TOOL/'compiler/gleam'
OTP = Path('/opt/homebrew/Cellar/erlang/29.1.1_2')
SNAPSHOT = ROOT/'archive/languages/gleam/20261012/qualification/private-v5/source-snapshot/support'
SUPPORT = ['clbg_io.gleam','clbg_io_ffi.erl','clbg_runner.erl','clbg_process.gleam','clbg_process_ffi.erl']
SOURCES = {'parent':ROOT/'programs/gleam/knucleotide/gleam-knucleotide-optimized/benchmark.gleam',
           'raw-tail':HERE/'source/raw-tail.gleam','preencoded-tail':HERE/'source/preencoded-tail.gleam'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path, value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2);stream.write('\n')


def pins():
    paths = [Path(__file__),PROCESS,REFERENCES,HERE/'proposal.json',HERE/'toolchain-v1/restore.json',
             *SOURCES.values(),*[SNAPSHOT/name for name in SUPPORT],
             OTP/'bin/erl',OTP/'bin/erlc',OTP/'lib/erlang/erts-17.1/bin/beam.smp']
    paths += [p for p in TOOL.rglob('*') if p.is_file()]
    return {str(p):sha(p) for p in sorted(set(paths))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare',action='store_true');parser.add_argument('--run',action='store_true')
    parser.add_argument('--plan-sha256');args=parser.parse_args();planpath=HERE/'native-plan-v1.json'
    if args.prepare:
        write(planpath,dict(schema='gleam-binary-tail-bounded-plan.v1',pins=pins(),mutex_inode=LOCK.stat().st_ino,
            sources={k:str(v) for k,v in SOURCES.items()},all_authored_helpers=SUPPORT,
            quantitative_benchmark=False,full_timing_available=False,
            scope='Compilation, complete independent bounded outputs and saved BEAM disassembly; work traces, counts and timing remain separate.'))
        print(sha(planpath));return
    assert args.run and sha(planpath)==args.plan_sha256
    plan=json.loads(planpath.read_bytes());assert pins()==plan['pins']
    output=HERE/'native-v1';output.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False)
    process=load('gleam_native_process',PROCESS);refs=load('gleam_independent_references',REFERENCES)
    report=dict(schema=plan['schema'],plan_sha256=sha(planpath),status='running',quantitative_benchmark=False,
                builds=[],cases=[],all_authored_helpers=SUPPORT)
    with LOCK.open('r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert os.fstat(lock.fileno()).st_ino==plan['mutex_inode']==LOCK.stat().st_ino
        env={'PATH':str(OTP/'bin')+':/usr/bin:/bin','LC_ALL':'C','LANG':'C','TZ':'UTC',
             'ERL_FLAGS':'+S 8:8 +A 1 +SDcpu 1:1 +SDio 1','ERL_CRASH_DUMP':str(BUILD/'erl_crash.dump'),
             'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
        def one(command,name,stdin=None):
            result=process.one(list(map(str,command)),output/name,env,BUILD,lock.fileno(),timeout=120,stdin=stdin)
            assert os.fstat(lock.fileno()).st_ino==plan['mutex_inode']==LOCK.stat().st_ino
            return result
        def success(command,name):
            result=one(command,name);process.success(result);return result
        try:
            success([COMPILER,'--version'],'gleam-version')
            assert (output/'gleam-version/stdout.bin').read_bytes()==b'gleam 1.19.0\n'
            success([OTP/'bin/erl','-noshell','-noinput','-eval','io:format("~p ~p~n",[erlang:system_info(otp_release),erlang:system_info(version)]),halt().'],'otp-version')
            libraries=BUILD/'libraries';libraries.mkdir()
            success([COMPILER,'compile-package','--target','erlang','--no-dev','--package',TOOL/'stdlib',
                     '--out',libraries/'gleam_stdlib','--lib',libraries],'compile-stdlib')
            library_files=[dict(path=str(p),sha256=sha(p)) for p in sorted(libraries.rglob('*')) if p.is_file()]
            report['compiled_stdlib_artifacts']=library_files
            compiled=[]
            for label,source in SOURCES.items():
                package=BUILD/'packages'/label;(package/'src').mkdir(parents=True)
                shutil.copyfile(source,package/'src/benchmark.gleam')
                for name in SUPPORT:shutil.copyfile(SNAPSHOT/name,package/'src'/name)
                (package/'gleam.toml').write_text('name = "clbg_benchmark"\nversion = "1.0.0"\ntarget = "erlang"\n\n[dependencies]\ngleam_stdlib = "1.0.5"\n')
                dest=BUILD/'applications'/label
                result=one([COMPILER,'compile-package','--target','erlang','--no-dev','--package',package,
                            '--out',dest,'--lib',libraries],'compile-'+label)
                clean=result['exit_code']==0 and not result['timed_out'] and not result['remaining_process_group']
                row=dict(label=label,source_sha256=sha(source),compiler_inputs=[dict(path=str(p),sha256=sha(p))
                    for p in sorted(package.rglob('*')) if p.is_file()],compiled=clean)
                if not clean:
                    report['builds'].append(row);continue
                artifacts=[dict(path=str(p),sha256=sha(p)) for p in sorted(dest.rglob('*')) if p.is_file()]
                row['artifacts']=artifacts;report['builds'].append(row);compiled.append((label,dest))
                binary=dest/'ebin/benchmark.beam'
                expression='io:format("~tp~n",[beam_disasm:file("'+str(binary)+'")]),halt().'
                success([OTP/'bin/erl','-noshell','-noinput','-eval',expression],'disassembly-'+label)
            for name,raw in refs.nucleotide_cases().items():
                inp=output/(name+'.stdin');inp.write_bytes(raw)
                expected=output/(name+'.expected');expected.write_bytes(refs.nucleotide_reference(raw))
                for label,dest in compiled:
                    command=[OTP/'bin/erl','+S','8:8','+A','1','+SDcpu','1:1','+SDio','1','-noshell','-noinput',
                             '-pa',dest/'ebin',libraries/'gleam_stdlib/ebin','-s','clbg_runner','main']
                    result=one(command,label+'-'+name,stdin=inp);process.success(result)
                    match=(output/(label+'-'+name)/'stdout.bin').read_bytes()==expected.read_bytes()
                    assert not (output/(label+'-'+name)/'stderr.bin').read_bytes()
                    report['cases'].append(dict(label=label,case=name,complete_output_matches=match))
                    assert match,(label,name)
            report['status']='passed-complete-bounded-outputs' if len(compiled)==len(SOURCES) else 'partial-build-failure-preserved'
        except Exception as error:
            report.update(status='failed',error=repr(error));raise
        finally:
            report['pins_unchanged']=pins()==plan['pins']
            report['lock_identity_unchanged']=os.fstat(lock.fileno()).st_ino==plan['mutex_inode']==LOCK.stat().st_ino
            write(output/'report.json',report)
            print(json.dumps({k:v for k,v in report.items() if k not in ['compiled_stdlib_artifacts','builds','cases']}),flush=True)
            assert report['pins_unchanged'] and report['lock_identity_unchanged']


if __name__=='__main__': main()
