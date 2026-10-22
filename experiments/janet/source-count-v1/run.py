"""Qualify a native-reader formatting projection without evaluating input ASTs."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('janet_owned_format',HERE.parent/'native-v1/run.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
sys.path.insert(0,str(HERE.parent/'native-v1'))
from outputs import validate_success
from rejections import validate as validate_rejection


def main():
    plan_path=HERE.parent/'bounded-v1/plan-v1.json'
    plan=json.loads(plan_path.read_bytes())
    for name,pin in plan['pins'].items():
        p=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p)==pin['sha256'],name
    overlays_path=HERE.parent/'source-overlays-v1.json'
    overlays=json.loads(overlays_path.read_bytes())
    active={r['benchmark']:ROOT/r['path'] for r in overlays['sources']}
    sources={r['path']:ROOT/r['path'] for r in overlays['sources']}
    for row in overlays['sources']:
        assert process.sha(ROOT/row['path'])==row['sha256']
        sources[row['parent_path']]=ROOT/row['parent_path']
    out=HERE/'run-v1';out.mkdir(exist_ok=False)
    report=dict(schema='janet-native-reader-format.v1',status='running',chart_admission=False,
        benchmark_samples=0,method='Janet 1.42.1 parse-all then untruncated colorless %80m per top-level form; native %n reader-tree equality and idempotence asserted.',
        controller_sha256=process.sha(Path(__file__)),formatter_sha256=process.sha(HERE/'format.janet'),
        runtime_sha256=process.sha(Path(plan['runtime'])),overlay_manifest_sha256=process.sha(overlays_path),
        sources=[],probes=[],bounded_outputs=[],normalized_source_units=None)
    def save():process.save(out/'results.json',report)
    with Path(plan['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report['mutex_inode']=os.fstat(lock.fileno()).st_ino
        def execute(command,directory):
            return process.execute(command,directory,plan['environment'],lock)
        def render(source,label):
            directory=out/label
            result=execute([plan['runtime'],'-R','-n',str(HERE/'format.janet'),str(source)],directory)
            assert result['exit_status']==0 and not (directory/'stderr.bin').read_bytes(),label
            return (directory/'stdout.bin').read_bytes()
        formatted={}
        for index,(name,source) in enumerate(sorted(sources.items())):
            data=render(source,f'format-{index:02d}')
            path=out/f'{index:02d}-{source.parent.name}-{source.name}';path.write_bytes(data)
            again=render(path,f'idempotence-{index:02d}')
            assert data==again
            directory=out/f'compile-{index:02d}'
            result=execute([plan['runtime'],'-R','-k',str(path)],directory)
            assert result['exit_status']==0 and not (directory/'stdout.bin').read_bytes() and not (directory/'stderr.bin').read_bytes()
            row=dict(source=name,source_sha256=process.sha(source),formatted_source=str(path.relative_to(ROOT)),formatted_sha256=process.sha(path),
                     native_reader_roundtrip_verified=True,independent_process_idempotence_verified=True,native_compile_clean=True,
                     reader_formatted_loc=len([line for line in data.splitlines() if line.strip()]),
                     historical_normalized_loc=None,language_lexical_tokens=None)
            report['sources'].append(row);formatted[str(source)]=path;save()
        probes=json.loads((HERE/'probes.json').read_bytes())
        for row in probes['equivalent_pairs']:
            a=render(HERE/row['packed'],'probe-'+row['name']+'-packed')
            b=render(HERE/row['wrapped'],'probe-'+row['name']+'-wrapped')
            assert a==b,row['name']
            report['probes'].append(dict(name=row['name'],identical_formatted_bytes=True))
        a,b=probes['distinct_pair']
        assert render(HERE/a,'probe-parens')!=render(HERE/b,'probe-brackets')
        report['probes'].append(dict(name='paren-call-versus-bracket-data',different_formatted_bytes=True))
        directory=out/'probe-malformed'
        result=execute([plan['runtime'],'-R','-n',str(HERE/'format.janet'),str(HERE/probes['malformed'])],directory)
        assert result['exit_status']!=0 and (directory/'stderr.bin').read_bytes() and not (directory/'stdout.bin').read_bytes()
        report['probes'].append(dict(name='malformed-reader-input',rejected_without_partial_formatted_output=True))
        corpus_path=ROOT/plan['corpus'];corpus=json.loads(corpus_path.read_bytes())
        for row in plan['schedule']:
            case=corpus['cases'][row['corpus_index']]
            source=formatted[str(active[row['benchmark']])]
            command=list(row['command']);command[3]=str(source)
            directory=out/f"case-{row['slot']:03d}"
            result=process.execute(command,directory,plan['environment'],lock,ROOT/row['stdin'])
            stdout=(directory/'stdout.bin').read_bytes();stderr=(directory/'stderr.bin').read_bytes()
            if case['expected_exit']==0:
                receipt=validate_success(case,stdout,stderr,result['exit_status'],(corpus_path.parent/case['expected']['path']).read_bytes())
            else:
                receipt=validate_rejection(case,(ROOT/row['stdin']).read_bytes(),stdout,stderr,result['exit_status'],source)
            report['bounded_outputs'].append(receipt);save()
        report['status']='native-reader-format-roundtrip-compile-and-149-contracts-pass';save()
    print(report['status'])


if __name__=='__main__':main()
