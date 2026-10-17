#!/usr/bin/env python3
"""Attach source-bound authorship and license evidence without altering measurements."""
from pathlib import Path
import argparse,collections,hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
REPO='https://github.com/mech-lang/benchmarks'
BSD='https://benchmarksgame-team.pages.debian.net/benchmarksgame/license.html'
APACHE=REPO+'/blob/main/LICENSE'
HANABI='https://github.com/hanabi1224/Programming-Language-Benchmarks'
MIT_NOTICE=REPO+'/blob/main/site/reports/programming-language-benchmarks-license.txt'

def source_identity(p):return list(p['files'])
def http(url):return isinstance(url,str) and url.startswith(('https://','http://'))
def public_source(url):return http(url) and not url.startswith(REPO)
def origin(url):
    for token,label in [('benchmarksgame-team','Benchmarks Game'),('kragen/shootout','Benchmarks Game archive'),
                        ('hanabi1224/Programming-Language-Benchmarks','Programming Language Benchmarks'),
                        ('reactorlabs/RBenchmarking','RBenchmarking'),('def-/nim-benchmarksgame','Nim Benchmarks Game'),
                        ('mikeleppane/mojo-rust-python-perf','mojo-rust-python-perf'),('cemrehancavdar/faster-python-bench','faster-python-bench'),
                        ('leanprover/lean4','Lean compiler benchmarks')]:
        if token in url:return label
    return 'Upstream source'
def implementation_url(url):return public_source(url) and '/description/' not in url

def notices(data,p):
    found=[]
    for key in p['files']:
        lines=data['files'][key]['code'].splitlines()
        for i,line in enumerate(lines[:80]):
            if re.search(r'contributed by|\bauthors?:|\btranslated.*\bby\b|\bbased on\b|\bported (?:by|from)\b',line,re.I):
                text=line.strip().strip('/*#;! -')
                if text and len(text)<400:found.append({'source_sha256':key,'line':i+1,'text':text})
    return found

def audit(data,models):
    catalog={**data.get('program_inventory',{}),**data['programs']};by_key=collections.defaultdict(list)
    # Recover references from retained source audits, never from timing values.
    for path in sorted((ROOT/'archive').rglob('source-audit.json')):
        try:obj=json.loads(path.read_text())
        except (ValueError,OSError):continue
        records=obj.get('programs',[]) if isinstance(obj,dict) else []
        if not isinstance(records,list):continue
        for r in records:
            if isinstance(r,dict) and r.get('key') in catalog:
                by_key[r['key']].append((path.relative_to(ROOT).as_posix(),r))
    records={}
    for key,p in catalog.items():
        refs=[];evidence=[];unresolved=[]
        def ref(url,relationship='implementation'):
            if public_source(url) and not any(r['url']==url for r in refs):refs.append({'label':origin(url),'url':url,'relationship':relationship})
        source=p.get('source_url');ref(source,'workload' if source and '/description/' in source else 'implementation')
        ref(p.get('upstream_source_url'))
        details=p.get('source_provenance_record') or {}
        if isinstance(details,dict) and details.get('upstream'):
            repo=details.get('upstream_repository');revision=details.get('upstream_commit')
            if repo and revision and 'upstream/hanabi/' in details['upstream']:
                ref(repo+'/blob/'+revision+'/'+details['upstream'].split('upstream/hanabi/',1)[1])
        for path,r in by_key[key]:
            if r.get('source_sha256') and r['source_sha256'] not in p['files']:continue
            evidence.append(path);ref(r.get('source_url'),'workload' if '/description/' in (r.get('source_url') or '') else 'implementation')
        if p['language'] in ['scala','typescript']:
            evidence.append('experiments/'+p['language']+'/source-v1/source-manifest.json')
            # Both retained manifests document explicit translations from existing
            # Benchmark Game Java/JavaScript entries and carry the BSD notice.
            ref('https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/'+p['benchmark']+'.html','workload')
        if p['language']=='nim':
            evidence.append('archive/languages/nim/20261012/PROVENANCE.md')
            ref('https://github.com/def-/nim-benchmarksgame/tree/466e4b8dcc9d70a6e619c6145db92dbd4f921e63','source collection')
            ref(HANABI+'/tree/ad18b203dd1769724f4eea94fc3ac1e99f6593e0/bench/algorithm','source collection')
        if p['language']=='c3':
            evidence.append('archive/languages/c3/20261012/PROVENANCE.md')
        if p['language'] in ['clojure','gleam','prolog']:
            evidence.append('archive/languages/'+p['language']+'/20261012/PROVENANCE.md' if p['language']!='prolog' else 'archive/languages/prolog/20261013/PROVENANCE.md')
        if p['language']=='pony':
            evidence.append('archive/languages/pony/20261012/PROVENANCE.md')
            if p['benchmark'] in ['binarytrees','nbody']:
                ref(HANABI+'/blob/ad18b203dd1769724f4eea94fc3ac1e99f6593e0/bench/algorithm/'+p['benchmark']+'/1.pony')
            elif p['benchmark']=='mandelbrot':
                ref('https://github.com/ponylang/ponyc/tree/85eb7c6a9a6b2a9433f70e9d4bc2f152509d30b4/examples/benchmarks/mandelbrot')
            elif p['benchmark']=='spectralnorm':
                ref('https://gist.github.com/renatoathaydes/83461b6a789042f2e95f9860957444c6/9cf63693e55f495a277362fe7b3b856b8e15587b')
        if p['language']=='lean4':
            evidence.append('experiments/lean4/source-provenance-v1.json')
            if p['benchmark']=='binarytrees':ref('https://github.com/leanprover/lean4/blob/v4.35.0/tests/compile_bench/binarytrees.lean','reference implementation')
        if p['language']=='julia-aot':
            parent=catalog.get(details.get('original_program_key') or p.get('original_program_key'))
            if parent:ref(parent.get('source_url'))
        if p['language']=='mojo':
            evidence.append('archive/comparisons/additional-languages/20261009-full-suite/provenance.json')
        attrs=notices(data,p)
        if p['language']=='crystal' and any('hanabi1224' in n['text'] for n in attrs):
            ref(HANABI+'/tree/ad18b203dd1769724f4eea94fc3ac1e99f6593e0/bench/algorithm','source collection')
        impl=[r for r in refs if r['relationship'] in ['implementation','source collection']]
        # Explicit local source records take priority over collection URLs that
        # were retained only as API/reference context.
        local_v=isinstance(details,dict) and details.get('kind')=='locally-authored-V'
        if local_v:impl=[]
        if not impl and p['key'] in ['nbody:chapel-3','nbody:rust-3']:
            lang='chapel' if p['language']=='chapel' else 'rust'
            ref('https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/nbody-'+lang+'-3.html');impl=refs[-1:]
        explicit_new=p['language'] in ['mech','mech-jit','mech-resident','bqn','k','futhark','roc','elm','c3','lean4','uiua'] or local_v
        if explicit_new:kind='ai-generated'
        elif p.get('local_adaptation') or p['language'] in ['mojo','scala','typescript']:
            kind='ai-adapted' if impl or p['language'] in ['scala','typescript'] else 'ai-generated'
        elif impl:kind='upstream'
        else:kind='unverified'
        label={'upstream':'Published','ai-adapted':'AI adapted','ai-generated':'AI generated','unverified':'Unverified'}[kind]
        origins=list(dict.fromkeys(r['label'] for r in impl))
        if kind=='ai-generated':label+=' · Mech suite'
        elif origins:label+=' · '+' / '.join(origins)
        elif kind=='ai-adapted':label+=' · Benchmarks Game' if p['language'] in ['scala','typescript'] else ' · upstream'
        matches=[r for f in p['files'] for r in models.get(f,[])] if kind!='upstream' else []
        model_ids=sorted({r['model'] for r in matches});matched_files=sorted({r['source_sha256'] for r in matches})
        ai_status='not-applicable' if kind=='upstream' else 'verified-source-writes' if len(matched_files)==len(p['files']) else 'partial-source-writes' if matches else 'unverified'
        licenses=[]
        def license_(ident,url,scope,evidence_path):
            row={'id':ident,'url':url,'scope':scope,'evidence':evidence_path}
            if row not in licenses:licenses.append(row)
        if kind in ['ai-generated','ai-adapted']:license_('Apache-2.0',APACHE,'Suite-authored source and local changes','LICENSE')
        for r in impl:
            u=r['url']
            if 'benchmarksgame-team' in u or 'kragen/shootout' in u:
                license_('BSD-3-Clause',BSD,'Retained upstream benchmark source','site/reports/benchmarks-game-license.txt')
            elif 'hanabi1224/Programming-Language-Benchmarks' in u:
                license_('MIT',MIT_NOTICE,'Upstream repository; per-file notices retained','archive/comparisons/zig-odin-roc-elm-comparison/20261010/upstream/hanabi/LICENSE')
            else:unresolved.append('Upstream license not established: '+r['label'])
        if p['language'] in ['scala','typescript']:
            license_('BSD-3-Clause',BSD,'Translated upstream application','experiments/'+p['language']+'/source-v1/LICENSE.benchmarksgame')
        if p['language']=='lean4' and p['benchmark']=='binarytrees':
            license_('Apache-2.0','https://github.com/leanprover/lean4/blob/v4.35.0/LICENSE','Referenced Lean compiler benchmark','experiments/lean4/source-provenance-v1.json')
        for f in p['files']:
            if 'The MIT License' in data['files'][f]['code']:
                license_('MIT',REPO+'/blob/main/programs/'+p['language'],'Bundled source with an MIT notice',data['files'][f]['path'])
        if not licenses:unresolved.append('No license evidence recorded for this source bundle')
        if p.get('license_url')=='./benchmarks-game-license.txt':
            license_('BSD-3-Clause',BSD,'Retained upstream application','site/reports/benchmarks-game-license.txt')
        if p.get('license_url')=='./programming-language-benchmarks-license.txt':
            license_('MIT',MIT_NOTICE,'Retained upstream application','site/reports/programming-language-benchmarks-license.txt')
        status='partial' if licenses and unresolved else 'identified' if licenses else 'unverified'
        records[key]={'schema':'benchmark-authorship.v1','kind':kind,'label':label,'source_sha256':source_identity(p),
            'sources':refs,'attribution_notices':attrs,'ai':{'tool':'OpenAI Codex' if kind in ['ai-generated','ai-adapted'] else None,
            'models':model_ids,'status':ai_status,'matched_source_files':matched_files,'total_source_files':len(p['files']),
            'evidence':matches},'license':{'status':status,'licenses':licenses,'unresolved':sorted(set(unresolved))},
            'evidence':sorted(set(evidence))}
    return records

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    path=ROOT/'data/benchmarks.json';raw=path.read_bytes();data=json.loads(raw)
    model_doc=json.loads((ROOT/'data/source-model-evidence.json').read_text());models=model_doc['files']
    records=audit(data,models)
    for pool in ['programs','program_inventory']:
        for key,p in data.get(pool,{}).items():
            if args.check and p.get('authorship')!=records[key]:raise ValueError('Stale authorship: '+key)
            p['authorship']=records[key]
    if not args.check:
        path.write_text(json.dumps(data,ensure_ascii=True,indent=2)+'\n')
        summary={'schema':'benchmark-authorship-audit.v1','programs':len(records),
            'kinds':dict(collections.Counter(r['kind'] for r in records.values())),
            'license_status':dict(collections.Counter(r['license']['status'] for r in records.values())),
            'ai_status':dict(collections.Counter(r['ai']['status'] for r in records.values())),
            'source_model_evidence':'data/source-model-evidence.json',
            'measurement_fields_unchanged':True}
        (ROOT/'data/authorship-audit.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'status':'passed','programs':len(records),'kinds':dict(collections.Counter(r['kind'] for r in records.values()))}))
if __name__=='__main__':main()
