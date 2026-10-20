#!/usr/bin/env python3
"""Attach source-bound authorship and license evidence without altering measurements."""
from pathlib import Path
import argparse,collections,hashlib,json,re
from source_lineage import lineage,exact_source,retained_path,SOURCE_REVISION
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
    if 'kostya/crystal-benchmarks-game' in url:return 'Crystal Benchmarks Game · kostya'
    if url.startswith(REPO):return 'Mech suite source'
    return 'Upstream source'
def implementation_url(url):return public_source(url) and exact_source(url)

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
    parents,extra_refs,lineage_evidence=lineage(data)
    checks_path=ROOT/'data/source-citation-checks.json'
    citation_checks={r['url']:r for r in json.loads(checks_path.read_text())['citations']} if checks_path.exists() else {}
    # Recover references from retained source audits, never from timing values.
    for path in sorted((ROOT/'archive').rglob('source-audit.json')):
        try:obj=json.loads(path.read_text())
        except (ValueError,OSError):continue
        records=obj.get('programs',obj.get('rows',[])) if isinstance(obj,dict) else []
        if not isinstance(records,list):continue
        for r in records:
            key=r.get('key') or r.get('id') if isinstance(r,dict) else None
            keys=[key] if key in catalog else [k for k,p in catalog.items() if
                p['language']==r.get('language') and p['benchmark']==r.get('benchmark') and
                (r.get('source_sha256') or r.get('sha256')) in p['files']]
            for key in keys:by_key[key].append((path.relative_to(ROOT).as_posix(),r))
    records={}
    for key,p in catalog.items():
        refs=[];evidence=[];unresolved=[]
        def ref(url,relationship='implementation',**metadata):
            if not public_source(url):return
            if '/description/' in url:relationship='workload'
            elif relationship=='implementation' and not exact_source(url):relationship='source collection'
            if not any(r['url']==url for r in refs):refs.append({'label':origin(url),'url':url,'relationship':relationship,**metadata})
        source=p.get('source_url');ref(source,'workload' if source and '/description/' in source else 'implementation')
        ref(p.get('upstream_source_url'))
        for r in extra_refs.get(key,[]):
            ref(r['url'],r['relationship'],**{k:v for k,v in r.items() if k not in ['url','relationship']})
        evidence+=lineage_evidence.get(key,[])
        details=p.get('source_provenance_record') or {}
        if isinstance(details,dict) and details.get('upstream'):
            repo=details.get('upstream_repository');revision=details.get('upstream_commit')
            if repo and revision and 'upstream/hanabi/' in details['upstream']:
                ref(repo+'/blob/'+revision+'/'+details['upstream'].split('upstream/hanabi/',1)[1])
        for path,r in by_key[key]:
            sha=r.get('source_sha256') or r.get('sha256')
            if sha and sha not in p['files']:continue
            evidence.append(path);ref(r.get('source_url'),'workload' if '/description/' in (r.get('source_url') or '') else 'implementation')
            ref(r.get('upstream'),'reference implementation',evidence=path)
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
        # Resolve documented translations transitively to the specific published
        # files. The retained parent sources remain separately inspectable.
        def ancestors(child,seen):
            if child in seen:return
            seen.add(child)
            for parent_key in parents.get(child,[]):
                parent=catalog[parent_key]
                for field in ['source_url','upstream_source_url']:
                    url=parent.get(field)
                    if implementation_url(url):ref(url,'reference implementation',via_program=parent_key)
                for r in extra_refs.get(parent_key,[]):ref(r['url'],'reference implementation',via_program=parent_key)
                ancestors(parent_key,seen)
        ancestors(key,set())
        impl=[r for r in refs if r['relationship']=='implementation' and exact_source(r['url'])]
        # Explicit local source records take priority over collection URLs that
        # were retained only as API/reference context.
        local_v=isinstance(details,dict) and details.get('kind')=='locally-authored-V'
        if local_v:impl=[]
        if not impl and p['key'] in ['nbody:chapel-3','nbody:rust-3']:
            lang='chapel' if p['language']=='chapel' else 'rust'
            ref('https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/nbody-'+lang+'-3.html');impl=refs[-1:]
        # A missing citation cannot establish that an AI originated the program.
        # Only an explicit source-origin record supports that claim.
        explicit_new=p['language']=='lean4' or local_v
        if explicit_new:kind='ai-generated'
        elif p.get('local_adaptation') or p['language'] in ['mojo','scala','typescript']:
            kind='ai-adapted' if impl or parents.get(key) else 'local-origin-unverified'
        elif impl:kind='upstream'
        else:kind='unverified'
        # These retained records explicitly document source changes even though
        # an older local_adaptation flag was false or absent.
        documented_changes=any(word in (p.get('source_provenance') or '').lower() for word in ['darwin import port','all changed application output']) or 'neon' in p['id']
        unchanged=any(citation_checks.get(r['url'],{}).get('body_sha256') in p['files'] or
                      set(citation_checks.get(r['url'],{}).get('matching_retained_source_sha256',[])).intersection(p['files']) for r in impl)
        if kind=='upstream' and documented_changes and not unchanged:kind='ai-adapted'
        label={'upstream':'Published','ai-adapted':'AI adapted','ai-generated':'AI generated','unverified':'Origin unverified',
               'local-origin-unverified':'Local · origin unverified'}[kind]
        origins=list(dict.fromkeys(r['label'] for r in impl))
        if kind=='ai-generated':label+=' · Mech suite'
        elif origins:label+=' · '+' / '.join(origins)
        elif kind=='ai-adapted':label+=' · Benchmarks Game' if p['language'] in ['scala','typescript'] else ' · local predecessor' if parents.get(key) else ' · upstream'
        matches=[r for f in p['files'] for r in models.get(f,[])] if kind!='upstream' else []
        model_ids=sorted({r['model'] for r in matches});matched_files=sorted({r['source_sha256'] for r in matches})
        ai_status='not-applicable' if kind=='upstream' else 'verified-source-writes' if len(matched_files)==len(p['files']) else 'partial-source-writes' if matches else 'unverified'
        licenses=[]
        def license_(ident,url,scope,evidence_path):
            row={'id':ident,'url':url,'scope':scope,'evidence':evidence_path}
            if row not in licenses:licenses.append(row)
        if kind in ['ai-generated','ai-adapted','local-origin-unverified']:license_('Apache-2.0',APACHE,'Suite-authored source and local changes only','LICENSE')
        for r in [r for r in refs if r['relationship'] in ['implementation','reference implementation'] and exact_source(r['url'])]:
            u=r['url']
            if 'benchmarksgame-team' in u or 'kragen/shootout' in u:
                license_('BSD-3-Clause',BSD,'Retained upstream benchmark source','site/reports/benchmarks-game-license.txt')
            elif 'hanabi1224/Programming-Language-Benchmarks' in u:
                license_('MIT',MIT_NOTICE,'Upstream repository; per-file notices retained','archive/comparisons/zig-odin-roc-elm-comparison/20261010/upstream/hanabi/LICENSE')
            elif 'github.com/ponylang/ponyc/blob/85eb7c6a9a6b2a9433f70e9d4bc2f152509d30b4/' in u:
                license_('BSD-2-Clause','https://github.com/ponylang/ponyc/blob/85eb7c6a9a6b2a9433f70e9d4bc2f152509d30b4/LICENSE',
                    'Referenced official Pony compiler example','site/reports/ponyc-license.txt')
            else:unresolved.append('Upstream license not established: '+r['label'])
        if p['language'] in ['scala','typescript']:
            license_('BSD-3-Clause',BSD,'Translated upstream application','experiments/'+p['language']+'/source-v1/LICENSE.benchmarksgame')
        if p['language']=='lean4' and p['benchmark']=='binarytrees':
            license_('Apache-2.0','https://github.com/leanprover/lean4/blob/v4.35.0/LICENSE','Referenced Lean compiler benchmark','experiments/lean4/source-provenance-v1.json')
        for f in p['files']:
            if 'The MIT License' in data['files'][f]['code']:
                source_path=data.get('archive_paths',{}).get(data['files'][f]['path'],data['files'][f]['path'])
                license_('MIT',REPO+'/blob/main/'+source_path,'Bundled source with an MIT notice',source_path)
        if not licenses:unresolved.append('No license evidence recorded for this source bundle')
        if p.get('license_url')=='./benchmarks-game-license.txt':
            license_('BSD-3-Clause',BSD,'Retained upstream application','site/reports/benchmarks-game-license.txt')
        if p.get('license_url')=='./programming-language-benchmarks-license.txt':
            license_('MIT',MIT_NOTICE,'Retained upstream application','site/reports/programming-language-benchmarks-license.txt')
        gaps=[]
        if not any(r['relationship'] in ['implementation','reference implementation'] and exact_source(r['url']) for r in refs) and not explicit_new:
            gaps.append('Original implementation source not established; a workload description or collection is not an original-source citation.')
        if any('kragen/shootout' in r['url'] or 'reactorlabs/RBenchmarking' in r['url'] for r in refs):
            gaps.append('A retained historical copy is cited; its earlier original publication has not been established.')
        if gaps:unresolved.append('Source lineage incomplete; additional upstream terms may apply.')
        status='partial' if licenses and unresolved else 'identified' if licenses else 'unverified'
        for r in refs:
            check=citation_checks.get(r['url'])
            if check:
                r['citation_check']={k:v for k,v in check.items() if k in ['status','body_sha256','normalized_source_sha256','matching_retained_source_sha256','retrieved_url']}
                r['citation_check']['evidence']='data/source-citation-checks.json'
        retained_revision=p.get('retained_source_revision',SOURCE_REVISION)
        if not re.fullmatch('[0-9a-f]{40}',retained_revision):raise ValueError('Invalid retained-source revision: '+key)
        retained=[{'source_sha256':sha,'url':REPO+'/blob/'+retained_revision+'/'+retained_path(data,sha)} for sha in p['files']] if data.get('archive_paths') is not None else []
        parent_sources=[{'program_key':parent,'label':catalog[parent]['id'],'source_sha256':sha,
                         'url':REPO+'/blob/'+catalog[parent].get('retained_source_revision',SOURCE_REVISION)+'/'+retained_path(data,sha),'relationship':'local predecessor'}
                        for parent in parents.get(key,[]) for sha in catalog[parent]['files']] if data.get('archive_paths') is not None else []
        records[key]={'schema':'benchmark-authorship.v1','kind':kind,'label':label,'source_sha256':source_identity(p),
            'origin_status':'unresolved' if gaps else 'suite-authored' if explicit_new else 'cited',
            'origin_gaps':gaps,'retained_sources':retained,'parent_programs':parents.get(key,[]),'parent_sources':parent_sources,
            'sources':refs,'attribution_notices':attrs,'ai':{'tool':'OpenAI Codex' if kind in ['ai-generated','ai-adapted'] else None,
            'models':model_ids,'status':ai_status,'matched_source_files':matched_files,'total_source_files':len(p['files']),
            'evidence':matches},'license':{'status':status,'licenses':licenses,'unresolved':sorted(set(unresolved))},
            'evidence':sorted(set(evidence))}
        # This later optimization has a source-bound admission packet and a
        # known current contributor family. Its predecessor's original author,
        # exact model and inherited terms remain unresolved. Never infer these
        # facts for another BQN file from a missing citation or shared language.
        if key=='knucleotide:array-bqn-occurrence-frame':
            from qualification.import_bqn_knucleotide import bound_authorship
            records[key]=bound_authorship(data,p,ROOT)
        if key=='knucleotide:nim-knucleotide-preencoded-v1':
            from qualification.import_nim_knucleotide import bound_authorship
            records[key]=bound_authorship(data,p,ROOT)
        # These exact sources were written in the archived 20261012 cohort.
        # Current evidence review cannot establish their source-writing model.
        if key in {'regexredux:matlab-case-compact','regexredux:matlab-case-optimized'}:
            from qualification.import_matlab_regex import bound_authorship
            records[key]=bound_authorship(data,p,ROOT)
        if key=='spectralnorm:array-bqn-native-sum':
            from qualification.import_bqn_spectral import bound_authorship
            records[key]=bound_authorship(data,p,ROOT)
        if key=='fasta:array-bqn-bins':
            from qualification.import_bqn_fasta import bound_authorship
            records[key]=bound_authorship(data,p,ROOT)
        if key=='nbody:clojure-nbody-primitive-updates-v1':
            from qualification.import_clojure_nbody import bound_authorship
            records[key]=bound_authorship(data,p,ROOT)
        if key=='nbody:clojure-nbody-compact-hot-aset-v1':
            from qualification.import_clojure_compact import bound_authorship
            records[key]=bound_authorship(data,p,ROOT)
        if key=='spectralnorm:prolog-spectralnorm-blocks8-v1':
            from qualification.import_prolog_spectral import bound_authorship
            records[key]=bound_authorship(data,p,ROOT)
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
            'origin_status':dict(collections.Counter(r['origin_status'] for r in records.values())),
            'source_model_evidence':'data/source-model-evidence.json',
            'measurement_fields_unchanged':True}
        (ROOT/'data/authorship-audit.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'status':'passed','programs':len(records),'kinds':dict(collections.Counter(r['kind'] for r in records.values()))}))
if __name__=='__main__':main()
