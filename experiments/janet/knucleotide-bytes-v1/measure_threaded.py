"""Add the threaded source without rewriting the five-source measurement packet."""
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
    metrics=load('knuc_threaded_text_metrics',ROOT/'tools/source_metrics.py')
    encoder,tokenizer=metrics.tokenizer();assert encoder is not None
    owned=load('knuc_threaded_metric_owner',HERE.parent/'native-v1/run.py')
    plan=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
    library=HERE.parent/'dependencies-v2/spork-format'
    grammar=json.loads((library/'snapshot.json').read_bytes())
    for name,pin in grammar['files'].items():assert owned.sha(library/name)==pin['sha256']
    plan['environment']['JANET_PATH']=str(library)
    source=HERE/'sources/threaded-modulo.janet';counter=HERE.parent/'lexical-v1/count.janet'
    out=HERE/'metrics-native-v2'
    if native:
        with Path(plan['common_mutex']).open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            result=owned.execute([plan['runtime'],'-R','-n',str(counter),str(source)],out,plan['environment'],lock)
            assert result['exit_status']==0 and not (out/'stderr.bin').read_bytes()
    raw=(out/'stdout.bin').read_bytes();assert raw.endswith(b'\n') and raw[:-1].isdigit()
    process=json.loads((out/'process.json').read_bytes())
    assert process['reaped'] and process['group_closed'] and not process['cleanup_errors']
    base_path=HERE/'source-measures.json';base=json.loads(base_path.read_bytes())
    profiles=dict(base['profiles'])
    profiles['threaded-modulo']=dict(source=str(source.relative_to(ROOT)),**metrics.measure(source.read_text(),encoder),language_lexical_tokens=int(raw),normalized_logical_loc=None,canonical_formatted_loc=None)
    return dict(schema='janet-knucleotide-source-measures.v2',profiles=profiles,base_sha256=owned.sha(base_path),
                producer_sha256=owned.sha(Path(__file__)),counter_sha256=owned.sha(counter),grammar_snapshot_sha256=owned.sha(library/'snapshot.json'),
                tokenizer=tokenizer,python=sys.version,zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,
                application_boundary=base['application_boundary'],chart_admission=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--check',action='store_true');args=p.parse_args();assert args.run!=args.check
    result=build(args.run);output=HERE/'source-measures-v2.json'
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status='checked' if args.check else 'written',sources=len(result['profiles']))))
