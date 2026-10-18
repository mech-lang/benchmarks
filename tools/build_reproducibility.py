#!/usr/bin/env python3
"""Index recorded reproduction evidence, without running or changing benchmarks."""
from pathlib import Path
from functools import lru_cache
import argparse,collections,hashlib,json,re
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]
REPO='https://github.com/mech-lang/benchmarks'
# These retained reports identify both source and executable bytes. They can
# supply build provenance for later timings of that exact executable.
BINARY_BUILD_REPORTS=('archive/workloads/nbody/results/apple-m3-chapel-tricks-50m.json',)

class Index:
    def __init__(self,data):
        self.data=data;self.paths=data.get('archive_paths',{});self.fingerprints={}
    def resolve(self,value):
        if isinstance(value,dict):value=value.get('path')
        if not isinstance(value,str):return None
        value=value.split('/benchmarks/clbg/')[-1]
        if '/experiments/' in value and value.startswith('/'):value='experiments/'+value.split('/experiments/',1)[1]
        value=self.paths.get(value,value)
        if not (ROOT/value).is_file() and value.split('/')[0] in {b['key'] for b in self.data['benchmarks']}:
            value='archive/workloads/'+value
        if not (ROOT/value).is_file():
            match=re.match(r'([a-z0-9]+)-comparison/(\d{8})/(.*)',value)
            if match:value=f'archive/languages/{match[1]}/{match[2]}/{match[3]}'
        return value if not value.startswith('/') and (ROOT/value).is_file() else None
    @lru_cache(maxsize=None)
    def load(self,path):
        resolved=self.resolve(path)
        if resolved:
            try:return json.loads((ROOT/resolved).read_text())
            except (ValueError,UnicodeError):pass
        return {}
    @lru_cache(maxsize=None)
    def receipt(self,path,field=None):
        path=self.resolve(path)
        if not path:return None
        if path not in self.fingerprints:self.fingerprints[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        result=dict(path=path,sha256=self.fingerprints[path],url=REPO+'/blob/main/'+quote(path,safe='/'))
        if field:result['field']=field
        return result

def nodes(value,path=''):
    if isinstance(value,dict):
        yield path,value
        for k,v in value.items():
            if isinstance(v,(dict,list)):yield from nodes(v,path+'/'+str(k))
    elif isinstance(value,list):
        for i,v in enumerate(value):
            if isinstance(v,(dict,list)):yield from nodes(v,path+'/'+str(i))

def recorded_samples(row):
    for key in ['samples_seconds','samples','full_process_samples_seconds']:
        value=row.get(key)
        if isinstance(value,list) and value and all(isinstance(n,(int,float)) for n in value):return value
        if isinstance(value,list) and value and all(isinstance(n,dict) and isinstance(n.get('seconds'),(int,float)) for n in value):return [n['seconds'] for n in value]
    return None

def binary_build_contexts(index,profile):
    binary=profile.get('binary_sha256')
    if not binary:return []
    contexts=[]
    for path in BINARY_BUILD_REPORTS:
        doc=index.load(path)
        for selector,row in nodes(doc):
            if row.get('binary_sha256')!=binary or row.get('language')!=profile['language']:continue
            source=row.get('source') or {}
            hashes=set(source.get('sha256',{}).values()) if isinstance(source,dict) and isinstance(source.get('sha256'),dict) else set()
            if row.get('source_sha256'):hashes.add(row['source_sha256'])
            if hashes!=set(profile['files']):continue
            contexts.append((doc,path,selector,row))
    return contexts

def version_text(value):
    if isinstance(value,str):return value
    if isinstance(value,list) and value and all(isinstance(line,str) for line in value):return '\n'.join(value)
    if isinstance(value,dict):
        for key in ['version','version_stdout','version_text','actual_version','stdout']:
            if isinstance(value.get(key),str):return value[key]
        if isinstance(value.get('commit'),str):return 'commit '+value['commit']
    return None

def native_compiler_keys(language,commands):
    """Identify compilers from executable argv, never library/source filenames."""
    keys=[]
    for stage in commands:
        command=stage['command']
        vectors=command if isinstance(command,list) and command and isinstance(command[0],list) else [command]
        for argv in vectors:
            if not isinstance(argv,list) or not argv or not isinstance(argv[0],str):continue
            executable=Path(argv[0]).name.lower()
            if re.fullmatch(r'clang(?:\+\+)?(?:-\d+(?:\.\d+)*)?',executable):aliases=['clang','llvm']
            elif re.fullmatch(r'(?:gcc|g\+\+)(?:-\d+(?:\.\d+)*)?',executable):aliases=['gpp','cpp','gcc'] if language=='cpp' else ['gcc','c']
            else:continue
            keys.extend(alias for alias in aliases if alias not in keys)
    return keys

def version_label(versions):
    labels=[]
    names={'csharp':'.NET SDK','fsharp':'.NET SDK','csharp-aot':'.NET SDK','fsharp-aot':'.NET SDK','lean4':'Lean',
           'haskell':'GHC','ocaml':'OCaml','smalltalk':'Pharo','pharo':'Pharo','bqn':'CBQN','k':'Growler',
           'luau':'Luau','luau-jit':'Luau'}
    for version in versions:
        value=re.split(r';| · ',version['value'].splitlines()[0])[0]
        if re.match(r'^(?:\d|commit )',value):value=names.get(version['component'],version['component'])+' '+value
        if value not in labels:labels.append(value)
    return ' / '.join(labels) or 'Not recorded'

def build(data):
    index=Index(data);catalog={**data.get('program_inventory',{}),**data['programs']};records={}
    languages={l['key']:l for l in data['languages']};benchmarks={b['key']:b for b in data['benchmarks']}
    for key,p in catalog.items():
        lang=p['language'];e=p.get('measured_backend',{}).get('evidence',{}) or {}
        report=p.get('report','');doc=index.load(report)
        # A selector is usable only with its actual report and exact samples.
        candidates=[]
        for field,row in nodes(doc):
            same_source=isinstance(row.get('source_sha256'),str) and row['source_sha256'] in p['files']
            if recorded_samples(row)==p['samples'] and (row.get('id')==p['id'] or row.get('key')==key or field.endswith('/'+p['id']) or same_source):
                candidates.append((field,row))
        matched=candidates[0] if len(candidates)==1 else ('',{})
        field,row=matched
        sample_meta=p.get('sample_execution_metadata') or []
        first=sample_meta[0] if sample_meta else {}
        evidence=[]
        profile_field='/'+('programs' if key in data['programs'] else 'program_inventory')+'/'+key.replace('~','~0').replace('/','~1')
        profile_receipt=index.receipt('data/benchmarks.json',profile_field)
        if profile_receipt:evidence.append(profile_receipt)
        for path,selector in [(report,field),(e.get('report'),e.get('measurement_selector'))]:
            if path:
                receipt=index.receipt(path,selector)
                if receipt and receipt not in evidence:evidence.append(receipt)
        contexts=[(doc,report)]
        for name in ['plan','manifest']:
            path=doc.get(name)
            if isinstance(path,str) and index.resolve(path):contexts.append((index.load(path),path))
        # Follow the producer of a reconciled observation, rather than borrowing
        # a nearby cohort's runtime or build recipe.
        for name in ['producer_plan','producer_report']:
            path=first.get(name);path=path.get('path') if isinstance(path,dict) else path
            if path and index.resolve(path):contexts.append((index.load(path),path))
        original=row.get('original_report')
        original_pin=doc.get('original_reports',{}).get(original,{})
        original_receipt=index.receipt(original) if original else None
        if original_receipt and original_receipt['sha256']==original_pin.get('sha256'):
            contexts.append((index.load(original),original))
        bound_builds=binary_build_contexts(index,p)
        bound_paths={path for _,path,_,_ in bound_builds}
        contexts.extend((ctx,path) for ctx,path,_,_ in bound_builds if path not in {path for _,path in contexts})
        command=p.get('command') or first.get('command') or e.get('command') or row.get('command')
        build_commands=[]
        for name in ['generation_command','compile_command','build_command']:
            value=row.get(name) or p.get(name) or (e.get('actual_native_build_command') if name=='compile_command' else None)
            if value:build_commands.append(dict(stage=name,command=value))
        for ctx,path in contexts[1:]:
            for selector,node in nodes(ctx):
                if path in bound_paths and not any(path==bound_path and selector==bound_selector for _,bound_path,bound_selector,_ in bound_builds):continue
                if node.get('id')==p['id'] or node.get('key')==key:
                    for name in ['generation_command','compile_command','build_command','compile_commands']:
                        value=node.get(name)
                        if value:
                            item=dict(stage=name,command=value)
                            if path in bound_paths:
                                item.update(scope='binary-matched build provenance',evidence=index.receipt(path,selector))
                            if item not in build_commands:build_commands.append(item)
                    receipt=index.receipt(path,selector)
                    if receipt and receipt not in evidence:evidence.append(receipt)
        versions=[]
        def add_version(component,text,path,selector,scope='measurement cohort'):
            if not text or not re.search(r'\d',text):return
            item=dict(component=component,value=text.strip(),scope=scope)
            receipt=index.receipt(path,selector)
            if receipt:item['evidence']=receipt
            if not any(v['component']==component and v['value']==item['value'] for v in versions):versions.append(item)
        aliases={'javascript':['javascript','node'],'cpp':['clang','gcc'],'c':['clang','gcc'],
                 'csharp-aot':['csharp'],'fsharp-aot':['fsharp'],'dart-jit':['dart'],'julia-aot':['julia'],
                 'lisp':['sbcl'],'smalltalk':['smalltalk','pharo'],'k':['k','growler'],'bqn':['bqn','cbqn']}.get(lang,[lang])
        if lang in ['c','cpp']:
            aliases=native_compiler_keys(lang,build_commands)
        for ctx,path in contexts:
            for name in ['toolchains','runtimes','compilers','toolchain_versions']:
                pool=ctx.get(name,{})
                if isinstance(pool,dict):
                    seen_native_families=set()
                    for alias in aliases:
                        family='gcc' if alias in ['gcc','gpp','c','cpp'] else 'clang' if alias in ['clang','llvm'] else alias
                        if lang in ['c','cpp'] and family in seen_native_families:continue
                        text=version_text(pool.get(alias))
                        if text:
                            add_version(alias,text,path,'/'+name+'/'+alias,
                                'binary-matched build provenance; not recaptured during timing' if path in bound_paths else
                                'retained build provenance; not recaptured during timing' if path==original else 'measurement cohort')
                            seen_native_families.add(family)
            if lang in ['swift','lean4']:add_version(lang,version_text(ctx.get('compiler')),path,'/compiler')
            if lang=='d':add_version('d',version_text(ctx.get('runtime')),path,'/runtime')
            if lang=='rust' and ctx is doc and row:add_version('rust',version_text(ctx.get('rustc')),path,'/rustc')
        runtime_receipt=e.get('runtime_receipt') or {}
        if 'version' in (runtime_receipt.get('field') or '').lower():
            add_version(lang,runtime_receipt.get('value'),runtime_receipt.get('report'),runtime_receipt.get('field'),'source-bound runtime receipt')
        runtime_evidence=p.get('runtime_evidence') or {}
        policy=runtime_evidence.get('runtime') or p.get('runtime_policy')
        if not versions and policy and re.search(r'(?:\d+\.\d|R\d{4}[ab])',policy):
            policy_field='/runtime_evidence/runtime' if runtime_evidence.get('runtime') else '/runtime_policy'
            add_version(lang,policy,'data/benchmarks.json',profile_field+policy_field,'recorded profile metadata')
        if not versions and version_text(doc.get('runtime_policy')):
            add_version(lang,doc['runtime_policy'],report,'/runtime_policy','measurement cohort policy')
        if lang=='matlab' and version_text(doc.get('runtime_policy')):
            add_version(lang,doc['runtime_policy'],report,'/runtime_policy','measurement cohort policy')
        # Compiler snapshots are identities even when no release string exists.
        report_compiler_context={name:doc[name] for name in ['compiler_sha256','compiler_snapshot','compiler_source_commit','array_source_commit','source_commit'] if doc.get(name)}
        # Mixed-language reports often pin Mech's development compiler. Those
        # pins are report context, not the compiler identity of every competitor.
        compiler_identity=report_compiler_context.copy() if lang.startswith('mech') else {}
        # Match build receipts by executable hash, not by a neighboring version
        # number or a source filename shared by successive builds.
        if lang=='julia-aot':
            for build_path in sorted((ROOT/'experiments/julia/packagecompiler-v1/builds').glob('*/report.json')):
                build_doc=index.load(build_path.relative_to(ROOT).as_posix())
                if (build_doc.get('executable') or {}).get('sha256')!=p.get('binary_sha256'):continue
                rel=build_path.relative_to(ROOT).as_posix();build_commands.append(dict(stage='packagecompiler_build',command=build_doc['command']))
                receipt=index.receipt(rel)
                if receipt not in evidence:evidence.append(receipt)
                # This lockfile is the exact project used by the recorded command.
                import tomllib
                lock='experiments/julia/packagecompiler-v1/toolchain/Manifest.toml'
                manifest=tomllib.loads((ROOT/lock).read_text())
                add_version('Julia',manifest['julia_version'],lock,'julia_version','locked build project')
                add_version('PackageCompiler',manifest['deps']['PackageCompiler'][0]['version'],lock,'deps.PackageCompiler.version','locked build project')
                compiler_identity['packagecompiler_manifest']=index.receipt(lock)
                break
        if lang=='lean4':
            toolchain='experiments/lean4/toolchain-v1.json';tool_doc=index.load(toolchain)
            add_version('Lean',tool_doc.get('version'),toolchain,'/version','retained native toolchain')
            compiler_identity['native_toolchain']=tool_doc
            for build_path in sorted((ROOT/'experiments/lean4/optimization-v1').glob('build-*/report.json')):
                build_doc=index.load(build_path.relative_to(ROOT).as_posix());profile=build_doc.get('profiles',{}).get(p['benchmark'],{})
                if profile.get('binary_sha256')!=p.get('binary_sha256'):continue
                for c in build_doc.get('commands',[]):
                    if any(p['benchmark']+'.' in str(arg) or str(arg).endswith('/'+p['benchmark']) for arg in c['command']):
                        build_commands.append(dict(stage='native_build',command=c['command'],cwd=c.get('cwd')))
                receipt=index.receipt(build_path.relative_to(ROOT).as_posix())
                if receipt not in evidence:evidence.append(receipt)
                break
        if row.get('runtime_commit') and not versions:add_version(lang,'commit '+row['runtime_commit'],report,field+'/runtime_commit')
        environment={}
        protocol=doc.get('protocol')
        if isinstance(protocol,dict):environment.update(protocol.get('environment') or {})
        for value in [row.get('runtime_environment'),row.get('environment_overrides'),p.get('runtime_environment'),first.get('runtime_environment')]:
            if isinstance(value,dict):environment.update(value)
        boundary=p.get('timing_boundary') or e.get('original_timing_boundary') or doc.get('timing_boundary')
        if not boundary:boundary=protocol.get('timed_region') if isinstance(protocol,dict) else protocol
        hardware=doc.get('hardware') or doc.get('host') or doc.get('machine')
        host=dict(hardware=hardware,os=doc.get('os'),power=doc.get('power') or doc.get('required_power') or first.get('power_at_start'))
        input_records={name:doc[name] for name in ['inputs','input','workloads','full_workload_n','steps','full_steps'] if doc.get(name) is not None}
        sample_input=[{k:s[k] for k in ['stdin','workload_n','validation','stdout','stdout_bytes','stdout_sha256','exit_code','exit_status','started_at','started_utc','raw_evidence','result_path'] if k in s} for s in sample_meta]
        dependencies={name:doc[name] for name in ['libraries','library_pins','external_library_pins','runtime_details','support_files'] if doc.get(name)}
        if isinstance(doc.get('runtimes'),dict):dependencies['toolchain_pins']={a:doc['runtimes'][a] for a in aliases if a in doc['runtimes']}
        parameters=dict(workload=benchmarks[p['benchmark']]['workload'],n=first.get('workload_n') or doc.get('full_workload_n') or doc.get('steps') or doc.get('full_steps'))
        missing=[]
        if not versions:missing.append('Exact compiler/runtime release string not recorded in the indexed cohort evidence.')
        elif all(v['scope'].endswith('not recaptured during timing') for v in versions):
            missing.append('Compiler release comes from retained build evidence; its version was not recaptured in the timing cohort.' if any(v['scope'].startswith('binary-matched') for v in versions) else
                'Compiler release comes from the pinned original build report; its version was not recaptured in the timing cohort.')
        if not command:missing.append('Timed command not recovered.')
        if not build_commands and p.get('execution_mode')=='aot':missing.append('Complete AOT build command not recovered.')
        if not hardware:missing.append('Cohort-specific hardware/OS record not recovered; suite methodology identifies Apple M3 macOS.')
        if not host['os']:missing.append('Exact OS version not recorded in indexed cohort evidence.')
        if not boundary:missing.append('Cohort timing boundary not recovered; see suite methodology and original report.')
        if p['benchmark'] in ['regexredux','knucleotide','revcomp'] and not input_records and not any(s.get('stdin') for s in sample_input):missing.append('Exact stdin generator/path/hash not recovered from indexed evidence.')
        for reason in p.get('measured_backend',{}).get('missing_evidence',[]):
            if reason not in missing:missing.append(reason)
        # Even a complete recipe is a historical record, not an automated clean
        # machine replay. Existing absolute paths are retained exactly as evidence.
        records[key]=dict(schema='benchmark-reproduction.v1',source_sha256=p['files'],
            version_label=version_label(versions),versions=versions,
            compiler_identity=compiler_identity,source_revision=p.get('retained_source_revision',SOURCE_REVISION),command=command,build_commands=build_commands,
            cwd=p.get('cwd') or first.get('cwd') or row.get('cwd'),environment=environment,parameters=parameters,
            input_records=input_records,dependencies=dependencies,host=host,timing_boundary=boundary,
            samples=sample_input,output_validation=p.get('full_output_validation') or row.get('correctness_full') or row.get('full_validation') or row.get('sample_validation'),
            recorded_at=first.get('started_at') or first.get('started_utc') or doc.get('created_at') or doc.get('started_at'),
            binary_sha256=p.get('binary_sha256') or row.get('binary_sha256') or (e.get('executable') or e.get('historical_executable') or {}).get('sha256'),evidence=evidence,
            status='gaps' if missing else 'recorded-recipe',missing=missing,
            replay_verified=False,methodology_url=REPO+'/blob/main/docs/methodology.md')
        if report_compiler_context and not lang.startswith('mech'):
            records[key]['report_compiler_context']=dict(scope='Report-wide metadata; not established as this implementation\'s compiler identity.',metadata=report_compiler_context)
    return dict(schema='benchmark-reproduction-index.v1',source_revision=SOURCE_REVISION,programs=records,
                summary=dict(programs=len(records),version_strings=sum(bool(r['versions']) for r in records.values()),
                             statuses=dict(collections.Counter(r['status'] for r in records.values()))))

from source_lineage import SOURCE_REVISION
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    result=build(json.loads((ROOT/'data/benchmarks.json').read_text()));path=ROOT/'data/reproducibility.json'
    if args.check:
        if json.loads(path.read_text())!=result:raise ValueError('Reproduction index is stale')
    else:path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result['summary']))
if __name__=='__main__':main()
