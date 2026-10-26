#!/usr/bin/env python3
"""Run the existing changed-input authority and audit its raw process receipts."""
if not __debug__:
    raise RuntimeError('Optimized Python is forbidden')
import argparse, importlib.util, json, shutil, sys
from pathlib import Path
CODE = Path('/private/tmp/benchmarks-native-consolidation/experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1')
sys.path.insert(0,str(CODE))
from study import HERE, ROOT, STUDY_ID, process, read_plan, read, subjects, source_state, runtime_environment, build_receipt_path
parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
run_id=args.run_id
assert run_id and all(c.isalnum() or c in '-_' for c in run_id)
out=HERE/('changed-inputs-'+run_id)
context_path=HERE/('changed-inputs-'+run_id+'.context.json')
assert not out.exists() and not context_path.exists()
plan=read_plan();targets,pins,f,i=subjects()
sources={s:source_state(Path(r['workspace'])) for s,r in [('F',f),('I',i)]}
assert sources=={'F':f['source'],'I':i['source']} and all(not s['status'] for s in sources.values())
files=[CODE/'changed-inputs.py',CODE/'study.py',ROOT/'experiments/janet/knucleotide-bytes-v1/process.py',ROOT/'tools/qualification/prolog_supervisor.py',HERE/'plan.json',build_receipt_path(plan['candidate_receipt']),build_receipt_path(plan['baseline_receipt'],shared=True),build_receipt_path(plan['runtime_environment_receipt'],shared=True)]
held={str(p):process.sha(p) for p in files}
context=dict(status='prepared',study_id=STUDY_ID,run_id=run_id,source=sources,subject_pins=pins,runtime_environment=runtime_environment(plan),input_pins=held,wrapper_sha256=process.sha(Path(__file__)),scope='Existing seven-oracle/fourteen-process correctness authority; zero primary or secondary timing observations.')
process.save(context_path,context)
try:
    spec=importlib.util.spec_from_file_location('changed_inputs',CODE/'changed-inputs.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    sys.argv=[str(CODE/'changed-inputs.py'),'--run-id',run_id]
    module.main()
    report=read(out/'results.json')
    assert report['status']=='seven-independent-oracles-and-fourteen-pinned-AOT-executions-verified' and len(report['cases'])==7
    receipts=[];identities=set()
    for case in report['cases']:
        assert {row['subject'] for row in case['executions']}=={'F','I'}
        folder=out/case['name']
        for row in case['executions']:
            subject=row['subject'];path=folder/subject/'process.json';r=read(path)
            assert r['exit_status']==0 and not r.get('error') and not r.get('observer_still_waiting')
            assert r['cleanup_errors']==[] and r['signals']==[] and r['group_closed'] is True and r['reaped'] is True
            assert r['deadline_seconds']==30 and r['quantitative_benchmark'] is False and r['inherited_common_mutex'] is True
            assert r['controller_sha256']==held[str(ROOT/'experiments/janet/knucleotide-bytes-v1/process.py')]
            assert process.sha(path)==row['process_sha256']
            assert process.sha(folder/subject/'stdout.bin')==case['expected_stdout_sha256']==row['stdout_sha256']
            assert process.sha(folder/(subject+'.native.json'))==row['native_sha256']
            birth=r['birth_identity'];identity=(birth['pid'],birth['birth_seconds'],birth['birth_microseconds'])
            assert identity not in identities;identities.add(identity)
            receipts.append(dict(path=str(path.relative_to(HERE)),sha256=process.sha(path),stdout_sha256=process.sha(path.parent/'stdout.bin'),stderr_sha256=process.sha(path.parent/'stderr.bin')))
    assert len(identities)==14 and len(receipts)==14
    assert all(process.sha(Path(path))==digest for path,digest in held.items())
    assert all(process.sha(targets[s])==pins[s] for s in targets)
    assert sources=={s:source_state(Path(r['workspace'])) for s,r in [('F',f),('I',i)]}
    assert runtime_environment(plan)==context['runtime_environment']
    context.update(status='all-fourteen-raw-process-receipts-validated',source_after=sources,receipts=receipts,results_sha256=process.sha(out/'results.json'),benchmark_samples=0)
except BaseException as error:
    context.update(status='failed',error=repr(error));raise
finally:
    process.save(context_path,context)
    if out.exists():
        shutil.copy2(context_path,out/'validation-context.json')
        shutil.copy2(__file__,out/'executed-validation-wrapper.py')
