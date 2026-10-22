"""Native published-grammar lexical counts, independent of physical wrapping."""
import fcntl
import importlib.util
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('janet_lexical_owned',HERE.parent/'native-v1/run.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)


def main():
    plan=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
    for name,pin in plan['pins'].items():
        p=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p)==pin['sha256'],name
    library=HERE.parent/'dependencies-v2/spork-format'
    snapshot=json.loads((library/'snapshot.json').read_bytes())
    for name,pin in snapshot['files'].items():assert process.sha(library/name)==pin['sha256']
    plan['environment']['JANET_PATH']=str(library)
    out=HERE/'run-v1';out.mkdir(exist_ok=False)
    report=dict(schema='janet-native-lexical-tokens.v1',status='running',benchmark_samples=0,chart_admission=False,
                counter_sha256=process.sha(HERE/'count.janet'),controller_sha256=process.sha(Path(__file__)),
                runtime_sha256=process.sha(Path(plan['runtime'])),grammar_snapshot_sha256=process.sha(library/'snapshot.json'),
                profiles=[],probes=[],logical_normalized_loc=None)
    with Path(plan['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        def count(source,label):
            directory=out/label
            result=process.execute([plan['runtime'],'-R','-n',str(HERE/'count.janet'),str(source)],directory,plan['environment'],lock)
            raw=(directory/'stdout.bin').read_bytes()
            assert result['exit_status']==0 and not (directory/'stderr.bin').read_bytes() and re.fullmatch(rb'[0-9]+\n',raw)
            return int(raw)
        core_path=HERE.parent/'source-count-v1/run-v1/results.json'
        published_path=HERE.parent/'source-count-v2/run-v1/results.json'
        core=json.loads(core_path.read_bytes());published=json.loads(published_path.read_bytes())
        report['format_evidence']={str(p.relative_to(ROOT)):process.sha(p) for p in (core_path,published_path)}
        for index,row in enumerate(core['sources']):
            source=ROOT/row['source'];native=ROOT/row['formatted_source']
            other=next(r for r in published['sources'] if r['source']==row['source'])
            assert process.sha(source)==row['source_sha256'] and process.sha(native)==row['formatted_sha256']
            third=ROOT/other['formatted_source'];assert process.sha(third)==other['formatted_sha256']
            values=[count(p,f'{index:02d}-{label}') for label,p in [('source',source),('reader',native),('published',third)]]
            assert len(set(values))==1,row['source']
            report['profiles'].append(dict(source=row['source'],source_sha256=process.sha(source),language_lexical_tokens=values[0],
                                           identical_token_count_after_both_formatters=True))
        expected={'independent-forms':10,'matrix-data':14,'quoted-code':18,'comment-and-string':5,
                  'mutable-values':16,'long-literal':206,'deep-tree':45,'function-body':18}
        fixtures=HERE.parent/'source-count-v1'
        probes=json.loads((fixtures/'probes.json').read_bytes())
        for row in probes['equivalent_pairs']:
            a=count(fixtures/row['packed'],'probe-'+row['name']+'-packed')
            b=count(fixtures/row['wrapped'],'probe-'+row['name']+'-wrapped')
            assert a==b==expected[row['name']],(row['name'],a,b)
            report['probes'].append(dict(name=row['name'],hand_count=expected[row['name']],packed=a,wrapped=b))
        directory=out/'malformed'
        result=process.execute([plan['runtime'],'-R','-n',str(HERE/'count.janet'),str(fixtures/'fixtures/malformed.janet')],directory,plan['environment'],lock)
        assert result['exit_status']!=0 and not (directory/'stdout.bin').read_bytes() and (directory/'stderr.bin').read_bytes()
        report['malformed_input_rejected_without_count']=True
        report['status']='13-source-grammar-counts-and-eight-hand-counted-layout-probes-pass'
        process.save(out/'results.json',report)
    print(report['status'])


if __name__=='__main__':main()
