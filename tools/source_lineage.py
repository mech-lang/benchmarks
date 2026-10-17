"""Resolve source citations through retained, file-specific translation records."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
REPO='https://github.com/mech-lang/benchmarks'
# This revision contains every retained source below, before this metadata audit.
SOURCE_REVISION='c95f900435aca5ae51030eabeffae2e5dc9a2fc2'

def read(path):
    return json.loads((ROOT/path).read_text())

def exact_source(url):
    if not isinstance(url,str) or not url.startswith(('https://','http://')):return False
    if '/description/' in url or '/tree/' in url:return False
    return bool(re.search(r'/program/[^/]+\.html(?:#.*)?$',url) or
                re.search(r'/(?:blob|raw)/[^/]+/.+\.[A-Za-z0-9]+(?:#.*)?$',url) or
                re.search(r'raw\.githubusercontent\.com/[^/]+/[^/]+/[^/]+/.+\.[A-Za-z0-9]+$',url) or
                re.search(r'gist\.github\.com/[^/]+/[a-f0-9]{32}/[a-f0-9]{40}',url))

def retained_path(data,sha):
    path=data['files'][sha]['path']
    path=data.get('archive_paths',{}).get(path,path)
    if (ROOT/path).is_file() and hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha:return path
    # Readable exports also preserve helpers with colliding basenames.
    from export_catalog import slug
    for p in {**data.get('program_inventory',{}),**data['programs']}.values():
        if sha not in p['files']:continue
        directory=ROOT/'programs'/slug(p['language'])/slug(p['benchmark'])/slug(p['id'])
        for candidate in directory.iterdir() if directory.exists() else []:
            if candidate.is_file() and candidate.suffix!='.json' and hashlib.sha256(candidate.read_bytes()).hexdigest()==sha:
                return candidate.relative_to(ROOT).as_posix()
    raise ValueError('Retained source missing: '+sha)

def lineage(data):
    catalog={**data.get('program_inventory',{}),**data['programs']}
    by_sha={}
    for key,p in catalog.items():
        for sha in p['files']:by_sha.setdefault(sha,[]).append(key)
    parents={};references={};evidence={}
    for lang,field in [('scala','programs'),('typescript','profiles')]:
        path=f'experiments/{lang}/source-v1/source-manifest.json'
        for row in read(path)[field]:
            key=(row.get('benchmark') or row['workload'])+':'+row['id']
            if key not in catalog:continue
            refs=row.get('reference_sources') or [row['reference']]
            parents[key]=list(dict.fromkeys(k for r in refs for k in by_sha.get(r['sha256'],[]) if k!=key))
            evidence[key]=[path]
    for key,p in catalog.items():
        detail=p.get('source_provenance_record') or {}
        parent=detail.get('original_program_key') or p.get('original_program_key')
        if parent in catalog:parents[key]=[parent]
    # Both ends of retained translation/consulted-file records must match.
    # A new implementation never inherits ancestry just from its language,
    # workload name or reuse of an existing program ID.
    origin_index='data/source-predecessor-evidence.json'
    for key,record in read(origin_index)['programs'].items():
        if key not in catalog or set(catalog[key]['files'])!=set(record['source_sha256']):continue
        origin=record['evidence']
        if hashlib.sha256((ROOT/origin['path']).read_bytes()).hexdigest()!=origin['sha256']:
            raise ValueError('Source-predecessor evidence changed: '+origin['path'])
        matched=[r['program_key'] for r in record['predecessors'] if r['program_key'] in catalog and
                 set(catalog[r['program_key']]['files'])==set(r['source_sha256'])]
        if len(matched)!=len(record['predecessors']):continue
        parents[key]=matched;evidence.setdefault(key,[]).extend([origin_index,origin['path']])
    # Explicit source comments name the imported file's collection. The retained
    # download receipt pins that particular file, rather than the whole repo.
    downloads=read('archive/languages/crystal/20261012/research/source-downloads.json')
    crystal_profiles={r['id']:r for r in read('archive/languages/crystal/20261012/profiles.json')['profiles']}
    for key,p in catalog.items():
        if p['language']!='crystal':continue
        code='\n'.join(data['files'][s]['code'] for s in p['files'])
        declared=crystal_profiles.get(p['id'],{}).get('upstream_provenance')
        if declared:
            family='hanabi' if 'hanabi1224' in declared['repository'] else 'kostya'
            local=ROOT/f"archive/languages/crystal/20261012/research/upstream/{family}"/declared['path']
            references.setdefault(key,[]).append(dict(url=declared['repository']+'/blob/'+declared['commit']+'/'+declared['path'],
                relationship='implementation',upstream_sha256=hashlib.sha256(local.read_bytes()).hexdigest(),
                evidence='archive/languages/crystal/20261012/profiles.json'))
        family='kostya' if 'From https://github.com/kostya/crystal-benchmarks-game/' in code else 'hanabi' if 'ported from ruby to crystal by hanabi1224' in code else None
        if not family:continue
        task={'fannkuchredux':'fannkuch-redux','spectralnorm':'spectral-norm','regexredux':'regex-redux'}.get(p['benchmark'],p['benchmark'])
        matches=[r for r in downloads if f'upstream/{family}/' in r['path'] and
                 (f'/{p["benchmark"]}/{p["benchmark"]}.cr' in r['path'] if family=='kostya' else f'/{task}/1.cr' in r['path'])]
        for r in matches:
            local=ROOT/'archive/languages/crystal/20261012/research'/r['path']
            references.setdefault(key,[]).append(dict(url=r['url'],relationship='implementation',
                upstream_sha256=hashlib.sha256(local.read_bytes()).hexdigest(),evidence='archive/languages/crystal/20261012/research/source-downloads.json'))
    # Pony's retained research names both files of the official example.
    pony_profiles=read('archive/languages/pony/20261012/profiles.json')['profiles']
    for row in pony_profiles:
        if row['benchmark']!='mandelbrot':continue
        key='mandelbrot:'+row['id']
        source=ROOT/'archive/languages/pony/20261012'/row['source']
        if key not in catalog or hashlib.sha256(source.read_bytes()).hexdigest() not in catalog[key]['files']:continue
        for upstream,filename in [('official-mandel-main.pony','main.pony'),('official-mandel-worker.pony','mandelbrot.pony')]:
            path=ROOT/'archive/languages/pony/20261012/upstream'/upstream
            references.setdefault(key,[]).append(dict(
                url='https://github.com/ponylang/ponyc/blob/85eb7c6a9a6b2a9433f70e9d4bc2f152509d30b4/examples/benchmarks/mandelbrot/'+filename,
                relationship='implementation',upstream_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                evidence='archive/languages/pony/20261012/PROVENANCE.md'))
        evidence.setdefault(key,[]).append('archive/validation/loc-normalization/20261012/PONY-RESEARCH.md')
    # Lean explicitly records related TypeScript sources and the upstream Lean
    # benchmark as references, without claiming downloaded Lean applications.
    lean=read('experiments/lean4/source-provenance-v1.json')
    for key,p in catalog.items():
        if p['language']!='lean4':continue
        r=lean['sources'].get(p['benchmark']+'.lean',{})
        if str(r.get('reference','')).startswith('https://'):
            references.setdefault(key,[]).append(dict(url=r['reference'],relationship='reference implementation',upstream_sha256=r['upstream_sha256'],evidence='experiments/lean4/source-provenance-v1.json'))
        if r.get('related_source'):
            parent=f"{p['benchmark']}:typescript-{p['benchmark']}-v1"
            if parent in catalog:parents[key]=[parent]
        evidence.setdefault(key,[]).append('experiments/lean4/source-provenance-v1.json')
    return parents,references,evidence
