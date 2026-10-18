"""Reconcile saved Luau process observations and complete stream digests."""
import argparse
import json
from pathlib import Path
import statistics
import subprocess
import re

from luau_run import ROOT,HERE,source_pins,host
from lean_run import sha,FULL,now


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=HERE/'results-v1.json')
    args=parser.parse_args();assert not args.output.exists()
    path=HERE/'full-v1/report.json';report=json.loads(path.read_text())
    assert report['status']=='PASSED' and report['active'] is None and report['benchmark_samples']==60
    assert report['sources']==source_pins() and len(report['cases'])==60
    assert all(sha(host(b))==digest for b,digest in report['binaries'].items())
    results={};processes=set()
    for language,mode in [('luau','vm'),('luau-jit','jit')]:
        results[language]={}
        for b in FULL:
            rows=[r for r in report['cases'] if r['benchmark']==b and r['execution_mode']==mode]
            assert len(rows)==3 and len({r['pid'] for r in rows})==3
            for r in rows:
                assert r['valid'] and not r['timed_out'] and r['exit_code']==0
                stdout=ROOT/r['stdout']['path'];stderr=ROOT/r['stderr']['path']
                assert stdout.stat().st_size==r['stdout']['bytes'] and sha(stdout)==r['stdout']['sha256']
                assert stderr.stat().st_size==0 and sha(stderr)==r['stderr']['sha256']
                process=stdout.parent/'process.json';assert json.loads(process.read_text())==r
                assert str(process) not in processes;processes.add(str(process))
                assert 'AC Power' in r['power']['before'] and 'AC Power' in r['power']['after']
            samples=[r['elapsed_seconds'] for r in rows]
            results[language][b]=dict(samples_seconds=samples,median_seconds=statistics.median(samples),
                sample_sd_seconds=statistics.stdev(samples),minimum_seconds=min(samples),maximum_seconds=max(samples))
    ordered=report['cases']
    assert all(a['finished_utc']<=b['started_utc'] for a,b in zip(ordered,ordered[1:]))
    hardware={name:subprocess.check_output(['/usr/sbin/sysctl','-n',key],text=True).strip()
              for name,key in [('cpu','machdep.cpu.brand_string'),('model','hw.model'),('memory_bytes','hw.memsize'),('logical_cpus','hw.ncpu')]}
    os_version=subprocess.check_output(['/usr/bin/sw_vers'],text=True).strip()
    sdk_path=subprocess.check_output(['/usr/bin/xcrun','--show-sdk-path'],text=True).strip()
    build=json.loads((HERE/'build-v2/report.json').read_text())
    cache=(HERE/'.build/native-v1/CMakeCache.txt').read_text()
    compiler=re.search(r'^CMAKE_CXX_COMPILER:FILEPATH=(.+)$',cache,re.M)[1]
    versions={}
    for name,header,macros in [('GMP',Path('/opt/homebrew/opt/gmp/include/gmp.h'),
                             ('__GNU_MP_VERSION','__GNU_MP_VERSION_MINOR','__GNU_MP_VERSION_PATCHLEVEL')),
                            ('PCRE2',Path('/opt/homebrew/opt/pcre2/include/pcre2.h'),('PCRE2_MAJOR','PCRE2_MINOR'))]:
        text=header.read_text()
        versions[name]=dict(version='.'.join(re.search(r'^#define\s+'+macro+r'\s+(\d+)',text,re.M)[1] for macro in macros),
                            header=str(header),header_sha256=sha(header))
    rebuild=[['git','clone','https://github.com/luau-lang/luau.git','/private/tmp/mech-luau-toolchain-0.743'],
             ['git','-C','/private/tmp/mech-luau-toolchain-0.743','checkout',build['revision']],
             *[c['command'] for c in build['commands']]]
    toolchain=dict(schema='luau-retained-toolchain.v1',release=build['release'],revision=build['revision'],
        repository='https://github.com/luau-lang/luau',compiler=dict(path=compiler,sha256=sha(compiler),
        version=subprocess.check_output([compiler,'--version'],text=True)),sdk=sdk_path,dependencies=versions,
        build_evidence=dict(path='experiments/luau/build-v2/report.json',sha256=sha(HERE/'build-v2/report.json')),
        binaries=build['artifacts'],rebuild_commands=rebuild,observed_at=now())
    (HERE/'toolchain-v1.json').write_text(json.dumps(toolchain,indent=2)+'\n')
    result=dict(schema='luau-full-workload-results.v1',status='SIXTY_FULL_SIZE_SAMPLES_RECONCILED',
        language='Luau',toolchains={language:dict(version='Luau '+build['release'],revision=build['revision']) for language in results},
        hardware=hardware,os=os_version,host_context_observed_at=now(),sdk=sdk_path,
        source_commit=report['source_commit'],timing_boundary=report['timing_boundary'],
        input_pins=report['input_pins'],inputs=report['input_pins'],library_pins=build['dependencies'],
        libraries=versions,rebuild_commands=rebuild,
        support_files={'toolchain':dict(path='experiments/luau/toolchain-v1.json',sha256=sha(HERE/'toolchain-v1.json'))},
        report=dict(path=str(path.relative_to(ROOT)),sha256=sha(path)),
        samples_per_workload_and_mode=3,benchmark_samples=60,matched_mech_controls=0,
        all_full_outputs_validated=True,all_saved_stream_hashes_recomputed=True,
        all_process_records_reconciled=True,sources_and_binaries_unchanged=True,timing_processes_serial=True,
        existing_other_language_measurements_changed=False,results=results,chart_admission=False)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],samples=60,results=results),indent=2))


if __name__=='__main__':main()
