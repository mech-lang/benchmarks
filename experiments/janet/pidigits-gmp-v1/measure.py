"""Complementary exact-text and pinned native-grammar source measures."""
import argparse
import fcntl
import importlib.util
import json
from pathlib import Path
import sys
import zlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def build(native=False):
    metrics=load('knuc_source_measures',ROOT/'tools/source_metrics.py')
    encoder,tokenizer=metrics.tokenizer()
    assert encoder is not None and tokenizer['status']=='available'
    owned=load('knuc_metric_owned',HERE.parent/'native-v1/run.py')
    plan=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
    library=HERE.parent/'dependencies-v2/spork-format'
    grammar=json.loads((library/'snapshot.json').read_bytes())
    for name,pin in grammar['files'].items():assert owned.sha(library/name)==pin['sha256']
    plan['environment']['JANET_PATH']=str(library)
    counter=HERE.parent/'lexical-v1/count.janet'
    from common import SOURCES
    sources={**SOURCES,**{name:HERE/'sources'/(name+'.janet') for name in ('positive-division','compact','compact-positive')}}
    directory=HERE/'metrics-native-v1'
    if native:
        directory.mkdir(exist_ok=False)
        with Path(plan['common_mutex']).open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            for label,source in sources.items():
                result=owned.execute([plan['runtime'],'-R','-n',str(counter),str(source)],directory/label,plan['environment'],lock)
                assert result['exit_status']==0 and not (directory/label/'stderr.bin').read_bytes()
    rows={}
    for label,source in sources.items():
        record=json.loads((directory/label/'process.json').read_bytes())
        assert record['reaped'] and record['group_closed'] and not record['cleanup_errors'] and record['exit_status']==0
        raw=(directory/label/'stdout.bin').read_bytes()
        assert raw.endswith(b'\n') and raw[:-1].isdigit()
        rows[label]=dict(source=str(source.relative_to(ROOT)),**metrics.measure(source.read_text(),encoder),
                        language_lexical_tokens=int(raw),normalized_logical_loc=None,canonical_formatted_loc=None)
    return dict(schema='janet-pidigits-source-measures.v1',profiles=rows,tokenizer=tokenizer,python=sys.version,zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,
                counter_sha256=owned.sha(counter),grammar_snapshot_sha256=owned.sha(library/'snapshot.json'),
                producer_sha256=owned.sha(Path(__file__)),metric_implementation_sha256=owned.sha(ROOT/'tools/source_metrics.py'),
                application_boundary='Complete authored application file, all helpers/comments/whitespace included; unchanged runtime and general dependencies excluded.',
                chart_admission=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    assert args.run != args.check
    result=build(native=args.run);output=HERE/'source-measures.json'
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status='checked' if args.check else 'written',sources=len(result['profiles']))))
