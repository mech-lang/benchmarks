"""Serial, bounded local publication QA; no benchmark subjects are launched."""
import sys,os,json,fcntl,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('owned',ROOT/'experiments/janet/knucleotide-bytes-v1/process.py');process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
NODE='/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def main():
 out=HERE/'validation';out.mkdir(exist_ok=False)
 env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin','HOME':'/Users/cim310','LC_ALL':'C','LANG':'C','TZ':'UTC','PYTHONPATH':str(ROOT/'tools'),'PLAYWRIGHT_MODULE':'/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs','CHROME_BINARY':'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}
 modules=['test_mech_revcomp_publication','test_mech_pidigits_publication','test_authorship','test_family_authorship','test_source_accounting','test_export_catalog','test_reproducibility','test_build_site','test_logical_source_payload','test_mech_logical_extensions','test_clojure_logical_extensions']
 js=['benchmark_traits','density','labels','languages','layers','rankings','relative_comparisons','source_axes','source_metrics','sample_data','view_state','publication']
 commands=[('python',[sys.executable,'-m','unittest',*modules,'-v']),('repository',[sys.executable,'tools/verify_repository.py']),('authorship',[sys.executable,'tools/audit_authorship.py','--check']),('reproducibility',[sys.executable,'tools/build_reproducibility.py','--check']),('source-metrics',[str(ROOT/'experiments/source-metrics/.build/venv39/bin/python'),'tools/source_metrics.py','--require-tokenizer','--check']),('logical-source',[sys.executable,'tools/logical_source_units.py','--check']),('clojure-projection',[sys.executable,'tools/clojure_logical_extensions.py','check'])]
 commands += [('js-'+name,[NODE,'site/tests/'+name+'.mjs']) for name in js]
 commands += [('data-projection',[NODE,'site/tests/data_projection.mjs','data/benchmarks.json','site/public/data.json']),('source-axes-browser',[NODE,'site/tests/source-axes-browser.mjs','site/public',str(out/'source-axes-browser.json')]),('sample-table-browser',[NODE,'site/tests/sample-table.mjs','site/public',str(out/'sample-table-browser.json')])]
 with Path('/private/tmp/mech-clbg-timing.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for name,command in commands:
   r=process.execute(command,out/name,env,lock,deadline=180)
   assert r['exit_status']==0,dict(check=name,stderr=(out/name/'stderr.bin').read_text(errors='replace')[-3000:])
   print(name,'passed',flush=True)
 catalog=json.loads((ROOT/'data/benchmarks.json').read_bytes());browser=json.loads((ROOT/'site/public/data.json').read_bytes());repro=json.loads((ROOT/'data/reproducibility.json').read_bytes());admission=catalog['mech_revcomp_20261022_audit'];new={}
 for key in admission['programs']:
  p=catalog['programs'][key];r=repro['programs'][key]
  assert r['status']=='recorded-recipe'
  assert r['compiler_identity']['runtime_source_commit'][:9] in r['version_label']
  assert r['compiler_identity']['compiler_source_commit']=='6de19875e2266f39c93712800c400672a44b98c9'
  assert r['dependencies']['runtime_details']['compiler_build']['root_build_command']
  assert len(r['samples'])==len(p['samples'])==7 and browser['programs'][key]['seconds']==p['seconds']
  assert p['files']==catalog['programs']['revcomp:mech-revcomp-optimized']['files'] and p['loc']==7
  new[key]=dict(status=r['status'],version_label=r['version_label'],compiler_identity=r['compiler_identity'],samples=7)
 result=dict(status='verified-local-publication',checks=len(commands),javascript_core_suites=len(js),catalog_programs=len({**catalog['program_inventory'],**catalog['programs']}),catalog_samples=sum(len(p['samples']) for p in {**catalog['program_inventory'],**catalog['programs']}.values()),new_mech_samples=28,qualified_logical_profiles=browser['logical_source_units']['coverage']['qualified_profiles'],site_version=json.loads((ROOT/'site/public/build.json').read_text())['version'],reproduction_records=new,benchmark_jobs_started=0)
 process.save(out/'summary.json',result);print(json.dumps(result))
if __name__=='__main__':main()
