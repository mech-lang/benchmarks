"""Four-subject actual-path diagnostic; never supplies primary timings."""
import fcntl,importlib.util,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import PLAN,process,read,source_state,check_native,INPUT_SHA,OUTPUT_SHA,POLICY_SHA,DATA_SHA,SOURCE_SHA

def parser(name):
    spec=importlib.util.spec_from_file_location(name,STUDY/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.parse
worker_parse=parser('worker-parse');phase_parse=parser('phase-parse')
plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['diagnostic_source'] and not before['status']
mech=read(STUDY/'build-candidate-v1/results.json')
assert mech['status']=='diagnostic-host-built' and mech['source_before']==mech['source_after']==before
assert mech['guest_object_sha256']==read(HERE/'compact-ascii-map-timing-v1/results.json')['object_sha256']
assert mech['probe_sha256']==process.sha(STUDY/'phase_probe.rs')
assert mech['worker_probe_sha256']==process.sha(STUDY/'worker_probe.rs')
subjects={'candidate':mech}
production={'parent':'joined-byte-table-timing-v1','ordinary':'credit-fragment-facts-timing-v1'}
for name,pin in plan['retained_builds'].items():
    path=HERE/pin['path'];assert process.sha(path)==pin['sha256']
    build=read(path);assert build['binary_sha256']==pin['binary_sha256']
    if name!='rust':
        assert build['status']=='diagnostic-host-built'
        assert build['guest_object_sha256']==read(HERE/production[name]/'results.json')['object_sha256']
        assert build['probe_sha256']==process.sha(STUDY/('phase_probe.rs' if name=='parent' else 'phase-probe-parent.rs'))
        assert build['worker_probe_sha256']==mech['worker_probe_sha256']
    else:
        assert build['status']=='diagnostic-rust-built'
        assert build['binary_sha256']=='8edae977edd205240def5fa6e69cd7e00fd1c81c6de7a33bfcd934a21a1f9551'
        assert build['probe_sha256']==process.sha(STUDY/'worker_probe.rs')
        assert build['source_sha256']==process.sha(HERE/'worker-completion-v1/rust-instrumented.rs')
    subjects[name]=build
for build in subjects.values():assert process.sha(Path(build['binary']))==build['binary_sha256']
assert process.sha(HERE.parents[2]/'archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs')=='47548a02d18bbc68734b0ef2145e3bd89523f15fa779682031ddbd462dbf7851'
assert process.sha(HERE.parent/'native-hashmap-work-v1/.build/knucleotide-rust-7')=='f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763'
canonical=HERE.parents[2]/'data/benchmarks.json';inp=HERE.parents[2]/'experiments/janet/.build/inputs/fasta-n25000000.stdin';policy=HERE/'full-disjoint-state-v1/launch.json'
assert process.sha(canonical)==DATA_SHA and process.sha(inp)==INPUT_SHA and process.sha(policy)==POLICY_SHA
assert process.sha(HERE/'knucleotide-source-map.mec')==SOURCE_SHA
out=STUDY/'capture-v1';out.mkdir(exist_ok=False)
report=dict(status='qualifying-prefix',source_before=before,production_source=plan['production_source'],plan_sha256=process.sha(STUDY/'plan.json'),driver_sha256=process.sha(Path(__file__)),worker_parser_sha256=process.sha(STUDY/'worker-parse.py'),phase_parser_sha256=process.sha(STUDY/'phase-parse.py'),primary_benchmark_samples=0,excluded_runs=0,subjects={k:dict(binary=v['binary'],binary_sha256=v['binary_sha256']) for k,v in subjects.items()},prefix=[],samples=[])
process.save(out/'results.json',report)

def observe(subject,folder,input_path,launch,expected_output,full,lock):
    build=subjects[subject];assert process.sha(Path(build['binary']))==build['binary_sha256']
    native=folder.with_name(folder.name+'.native.json')
    command=[build['binary']]+([] if subject=='rust' else [str(launch),str(native),'--'])
    r=process.execute(command,folder,mech['environment'],lock,stdin=input_path,deadline=30,quantitative=False)
    assert r['exit_status']==0 and process.sha(folder/'stdout.bin')==expected_output
    process.save(folder/'workers.json',worker_parse(folder/'stderr.bin',subject))
    if subject!='rust':
        n=read(native)
        assert n['native_hash_table_updates']==n['native_packed_map_updates']==(874999961 if full else 6999961)
        assert n['native_parallel_tasks']==7 and n['policy']=='secured' and n['shutdown']=='completed'
        assert n['native_worker_credit_batches']==854497 if full else n['native_worker_credit_batches']>0
        if full:check_native(native)
        assert n.get('native_fused_string_map_bytes',0)==((125000000 if full else 1000000) if subject in ['candidate','parent'] else 0)
        phases=phase_parse(folder/'stderr.bin',subject)
        if full:assert phases['rows']['direct_rows']==4166671
        process.save(folder/'phases.json',phases)
    return dict(subject=subject,folder=str(folder.relative_to(STUDY)),process_sha256=process.sha(folder/'process.json'),workers_sha256=process.sha(folder/'workers.json'),phases_sha256=process.sha(folder/'phases.json') if subject!='rust' else None,native_sha256=process.sha(native) if subject!='rust' else None,output_sha256=expected_output)

with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino==83858837
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    prefix=HERE/'rust-span-diagnostic-v2/input.fasta';launch=HERE/'full-timing-v1/launch.json'
    assert process.sha(prefix)=='e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb'
    assert process.sha(launch)=='3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec'
    for subject in ['candidate','parent','ordinary','rust']:
        row=observe(subject,out/('prefix-'+subject),prefix,launch,'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa',False,lock)
        report['prefix'].append(row);process.save(out/'results.json',report)
        print(subject,'prefix and physical boundaries qualified',flush=True)
    report['status']='collecting-full';process.save(out/'results.json',report)
    for index,order in enumerate(plan['orders']):
        for position,subject in enumerate(order):
            row=observe(subject,out/f'{index:02d}-{position}-{subject}',inp,policy,OUTPUT_SHA,True,lock)
            row.update(order=index,position=position);report['samples'].append(row);process.save(out/'results.json',report)
        print('diagnostic order',index+1,'of',len(plan['orders']),'verified',flush=True)
    assert source_state()==before and process.sha(canonical)==DATA_SHA
report.update(status='all-thirty-two-full-boundaries-phases-outputs-and-updates-verified',source_after=source_state());process.save(out/'results.json',report)
