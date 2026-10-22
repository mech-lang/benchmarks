"""Read-only loader diagnostics on owned complete applications, outside measurements."""
import fcntl
import json
from pathlib import Path
from common import HERE,ROOT,PLAN,SOURCES,process,reference

SOURCES={name:HERE/'sources'/(name+'.janet') for name in ('positive-division','compact')}

out=HERE/'refined-library-v1';out.mkdir(exist_ok=False)
report=dict(status='running',benchmark_samples=0,chart_admission=False,profiles={},metadata={})
gmp=Path(PLAN['environment']['MECH_GMP_LIBRARY']);assert process.sha(gmp)==PLAN['gmp_resolution']['sha256']
environment={**PLAN['environment'],'DYLD_PRINT_LIBRARIES':'1'}
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for label in ('positive-division','compact'):
        source=SOURCES[label];d=out/label
        r=process.execute([PLAN['runtime'],'-R','-n',str(source),'30'],d,environment,lock)
        assert r['exit_status']==0 and (d/'stdout.bin').read_bytes()==reference(30)[0]
        lines=(d/'stderr.bin').read_text().splitlines();assert lines and all(line.startswith('dyld[') for line in lines)
        assert any(str(gmp) in line for line in lines)
        report['profiles'][label]=dict(source_sha256=process.sha(source),gmp_path=str(gmp),gmp_sha256=process.sha(gmp),complete_loader_capture_sha256=process.sha(d/'stderr.bin'),diagnostic_environment_override=dict(DYLD_PRINT_LIBRARIES='1'))
    for name,command in [('gmp-links',['/usr/bin/otool','-L',str(gmp)]),('runtime-links',['/usr/bin/otool','-L',PLAN['runtime']]),('os-build',['/usr/bin/sw_vers'])]:
        d=out/name;r=process.execute(command,d,PLAN['environment'],lock)
        warning=(d/'stderr.bin').read_bytes()
        allowed=b"otool: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead\n"
        assert r['exit_status']==0 and (not warning or (command[0]=='/usr/bin/otool' and warning==allowed))
        report['metadata'][name]=dict(command=command,stdout_sha256=process.sha(d/'stdout.bin'),stderr_sha256=process.sha(d/'stderr.bin'),known_temp_directory_warning=bool(warning))
    report['status']='both-applications-load-pinned-gmp; loader-and-link-metadata-retained';process.save(out/'results.json',report)
print(report['status'])
