"""Raw source measures for inspected F# bundles and uncompiled source drafts."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import zlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def build():
    path=ROOT/'tools/source_metrics.py'
    spec=importlib.util.spec_from_file_location('fsharp_raw_metrics',path)
    metrics=importlib.util.module_from_spec(spec);spec.loader.exec_module(metrics)
    encoder,tokenizer=metrics.tokenizer();assert encoder is not None
    review=json.loads((HERE/'review.json').read_bytes())
    candidates=json.loads((HERE.parent/'candidates-v1.json').read_bytes())
    sources={s['path']:s['sha256'] for r in review['inspected_profiles'] for s in r['source_bundle']}
    sources.update({r['source']:r['source_sha256'] for r in candidates['candidates']})
    assert len(sources)==22
    profiles={}
    for name,digest in sorted(sources.items()):
        p=ROOT/name;assert metrics.sha(p.read_bytes())==digest
        profiles[name]=dict(**metrics.measure(p.read_text(),encoder),normalized_loc=None,native_formatted_loc=None,source_counts_qualified=False)
    return dict(schema='fsharp-raw-source-measures.v1',profiles=profiles,tokenizer=tokenizer,
                scope='Complete application source including all declarations, helpers, pragmas, notices and whitespace; external framework/runtime/GMP are dependencies.',
                python=sys.version,zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,native_processes_started=0,chart_admission=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    result=build();output=HERE/'source-measures-v1.json'
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status='checked' if args.check else 'written',unique_sources=len(result['profiles']))))
