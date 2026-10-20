"""Untimed production-BEAM map-call/whole-histogram witness, fresh processes.

All shared cases plus explicit prefix, leading-zero, maximum-key and default
flatmap-to-HAMT fixtures. No pilot/full mode, source rewrite or native kernel.
"""
import argparse
from collections import Counter
import fcntl
import json
import os
from pathlib import Path

from native_process import atom,now,one,sha,success
import run_bounded_v2 as bounded

ROOT,HERE,RUNTIME,LOCK,NAMES=bounded.ROOT,bounded.HERE,bounded.RUNTIME,bounded.LOCK,bounded.NAMES
PLAN=HERE/'work-plan-v2.json'
OUTPUT=HERE/'work-v2'
BUILDS=HERE/'bounded-v2/report.json'
FIXTURES=HERE/'generated-fixtures-v1'
WIDTHS=[1,2,3,4,6,12,18]
QUERIES=['GGT','GGTA','GGTATT','GGTATTTTAATT','GGTATTTTAATTTATAGT']
require,ref=bounded.require,bounded.ref


def dna_from_fasta(raw):
    selected=False;parts=[]
    for line in raw.replace(b'\r\n',b'\n').replace(b'\r',b'\n').split(b'\n'):
        if line.startswith(b'>'):
            if selected:break
            token=line[1:].replace(b'\t',b' ').split(b' ',1)[0];selected=token==b'THREE'
        elif selected and line and not line.startswith(b';'):
            text=line.upper();require(all(c in b'ACGT' for c in text),'Unexpected generated nucleotide');parts.append(text)
    return b''.join(parts).decode()


def histograms(dna):
    return {k:Counter(dna[i:i+k] for i in range(max(0,len(dna)-k+1))) for k in WIDTHS}


def reference_output(dna):
    counts=histograms(dna);parts=[]
    for k in [1,2]:
        for key,amount in sorted(counts[k].items(),key=lambda x:(-x[1],x[0])):
            parts.append(f'{key} {100.0*amount/max(0,len(dna)-k+1):.3f}\n')
        parts.append('\n')
    parts.extend(f'{counts[len(q)][q]}\t{q}\n' for q in QUERIES)
    return ''.join(parts).encode()


def generated_inputs():
    seq=b'ACGTGGTATTTTAATTTATAGTGGTACGTT'
    rows={f'prefix-{n:02}':b'>THREE\n'+seq[:n]+b'\n' for n in range(20)}
    rows.update({f'all-{chr(base)}-64':b'>THREE\n'+bytes([base])*64+b'\n' for base in b'AGT'})
    # Complete Cartesian triplets guarantee every three-base key and >32 keys.
    alphabet=b'ACGT';triplets=b''.join(bytes([a,b,c]) for a in alphabet for b in alphabet for c in alphabet)
    rows['all-triplets']=b'>THREE\n'+triplets+b'\n'
    rows['mixed-leading-A']=b'>ONE\nTTT\r\n>THREE\tmixed\r\naaaaGgTaTtTtAaTtTaTaGt\r\n;ignoreXYZ\r\nCCCCggggtttt\r\n>FOUR\nAAAA\n'
    return rows


def make_plan(create=False):
    builds=json.loads(BUILDS.read_bytes());require(builds['status']=='PASSED' and builds['complete_output_observations']==42,'Bounded output gate incomplete')
    bp=json.loads(bounded.PLAN.read_bytes());require(builds['plan']==ref(bounded.PLAN),'Build plan differs')
    pins={}
    def bind(path):
        r=ref(path);pins[r['path']]=r['sha256'];return r
    for path in [__file__,HERE/'work_probe_v2.exs',HERE/'native_process.py',HERE/'run_bounded_v2.py',BUILDS,bounded.PLAN]:bind(path)
    cases=[]
    for row in bp['cases']:
        raw=(ROOT/row['stdin']['path']).read_bytes();dna=dna_from_fasta(raw)
        cases.append(dict(**row,dna=dna));bind(ROOT/row['stdin']['path']);bind(ROOT/row['expected']['path'])
    if create:require(not FIXTURES.exists(),'Fresh generated fixture directory required');FIXTURES.mkdir()
    for name,raw in generated_inputs().items():
        dna=dna_from_fasta(raw);directory=FIXTURES/name
        if create:
            directory.mkdir();(directory/'stdin.bin').write_bytes(raw);(directory/'expected.stdout').write_bytes(reference_output(dna))
        require((directory/'stdin.bin').read_bytes()==raw and (directory/'expected.stdout').read_bytes()==reference_output(dna),'Generated fixture changed')
        cases.append(dict(case=name,n=0,stdin=bind(directory/'stdin.bin'),expected=bind(directory/'expected.stdout'),dna=dna))
    programs=builds['programs']
    for p in programs.values():
        for field in ['source_snapshot','support_snapshot','runner_snapshot']:bind(ROOT/p[field]['path'])
        for path,digest in p['beams'].items():require(bind(ROOT/path)['sha256']==digest,'Production BEAM changed')
    return dict(schema='elixir-rolling-work-plan.v1',status='PREPARED',controller=ref(__file__),probe=ref(HERE/'work_probe_v2.exs'),
        builds=ref(BUILDS),programs=programs,cases=cases,pins=pins,environment={k:v for k,v in bp['environment'].items() if k!='ERL_COMPILER_OPTIONS'},runtime_files=bp['runtime_files'],
        probe_environment_note='Omit the empty ERL_COMPILER_OPTIONS variable for the untimed diagnostic module compilation; OTP otherwise emits Ignoring bad term. Production BEAM bytes and VM flags are unchanged.',
        widths=WIDTHS,fixture_count=len(cases),common_mutex=str(LOCK),production_source_rewritten=False,
        quantitative_benchmark=False,chart_admission=False,source_count=None,
        scope='Actual production Map.update/4 invocation and return tracing; all complete histograms against independent windows. No internal one-probe claim.')


def check_witness(plan,case,name,output):
    w=json.loads((output/'witness.json').read_bytes());counts=histograms(case['dna'])
    require(w['status']=='PASSED' and w['variant']==name and w['dna_length']==len(case['dna']) and w['production_source_rewritten'] is False
        and w['standard_map_update_calls_traced'] is True and w['complete_histograms_compared']==7 and w['application_descendants_cleaned'] is True,'Incomplete work witness')
    require(w['update_invocations']==sum(sum(c.values()) for c in counts.values())==len(w['updates']),'Per-occurrence map invocation total differs')
    require([row['width'] for row in w['histograms']]==WIDTHS,'Incomplete width inventory')
    for row in w['histograms']:
        require(dict(row['entries'])==counts[row['width']] and row['updates']==sum(counts[row['width']].values()) and row['distinct']==len(counts[row['width']]),'Whole histogram differs')
    for width in WIDTHS:
        rows=[row for row in w['updates'] if row['width']==width];current={}
        for i,row in enumerate(rows):
            key=case['dna'][i:i+width];old=current.get(key,0)
            require(row['key']==key and row['previous']==old and row['value']==old+1 and row['before_size']==len(current),'Occurrence update differs')
            current[key]=old+1;require(row['after_size']==len(current),'Map growth differs')
        require(current==counts[width],'Trace update reconstruction differs')
    if name=='parallel':require(len(set(row['pid'] for row in w['updates']))<=7,'More than seven counting workers')
    return w


def run():
    plan=json.loads(PLAN.read_bytes());require(plan==make_plan(),'Witness plan/controller changed');require(not OUTPUT.exists(),'Fresh witness attempt required')
    with LOCK.open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);require(os.fstat(lock.fileno()).st_ino==LOCK.stat().st_ino,'Common lock changed')
        bounded.unchanged(plan);OUTPUT.mkdir()
        report=dict(schema='elixir-rolling-work-execution.v1',status='RUNNING',started_utc=now(),plan=ref(PLAN),cases=[],active=None,
            common_mutex_inode=os.fstat(lock.fileno()).st_ino,quantitative_benchmark=False,chart_admission=False)
        try:
            for case in plan['cases']:
                for name in NAMES:
                    directory=OUTPUT/case['case']/name;directory.mkdir(parents=True)
                    p=plan['programs'][name];beam=next((ROOT/path,d) for path,d in p['beams'].items() if path.endswith('Elixir.Clbg.Main.beam'))
                    spec=dict(output=str(directory),variant=name,dna=case['dna'],main_beam_sha256=beam[1],lock_fd=str(lock.fileno()),lock_inode=os.fstat(lock.fileno()).st_ino)
                    atom(directory/'spec.json',spec);report['active']=[case['case'],name];atom(OUTPUT/'report.json',report)
                    argv=[str(RUNTIME/'bin/elixir'),'-pa',p['ebin'],str(HERE/'work_probe_v2.exs'),str(directory/'spec.json')]
                    raw=one(argv,directory/'process',plan['environment'],ROOT,lock.fileno(),timeout=60,stdin=ROOT/case['stdin']['path']);success(raw)
                    require(Path(raw['stderr']['path']).read_bytes()==b'','Unexpected witness diagnostic retained')
                    require(Path(raw['stdout']['path']).read_bytes()==(ROOT/case['expected']['path']).read_bytes(),'Traced production output differs')
                    w=check_witness(plan,case,name,directory)
                    report['cases'].append(dict(source=name,case=case['case'],process=raw,witness=ref(directory/'witness.json'),raw_trace=ref(directory/'trace-framed.etf'),
                        exact_output=True,updates=w['update_invocations'],whole_histograms=7));atom(OUTPUT/'report.json',report)
            bounded.unchanged(plan);report.update(status='PASSED',active=None,finished_utc=now(),pins_unchanged=True,
                observations=len(report['cases']),whole_histograms=7*len(report['cases']),total_traced_updates=sum(r['updates'] for r in report['cases']),
                production_source_rewritten=False,standard_map_update_invocations=True,source_count=None)
        except BaseException as error:report.update(status='FAILED',error=repr(error),finished_utc=now());raise
        finally:atom(OUTPUT/'report.json',report)
    print(report['status'],report['observations'],report['whole_histograms'],report['total_traced_updates'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--run',action='store_true');args=parser.parse_args()
    require(args.prepare!=args.run,'Choose one mode')
    if args.prepare:require(not PLAN.exists(),'Fresh plan required');atom(PLAN,make_plan(create=False))
    else:run()
