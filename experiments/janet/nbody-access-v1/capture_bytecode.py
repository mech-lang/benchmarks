"""Compile-only disassembly evidence; never run concurrently with measurements."""
import fcntl
import json
from pathlib import Path
from common import HERE,ROOT,PLAN,SOURCES,process

def main():
    out=HERE/'bytecode-v1';out.mkdir(exist_ok=False)
    report=dict(status='running',profiles={},benchmark_samples=0,chart_admission=False)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for label,source in SOURCES.items():
            text=source.read_text();text=text[:text.index('(defn main')]
            function='advance-n' if label=='scalar-registers' else 'advance'
            text+='''(defn main [& args]
  (print (string/format "S %d" (disasm FUNCTION :slotcount)))
  (each instruction (disasm FUNCTION :bytecode)
    (print (string/format "%n" instruction))))
'''.replace('FUNCTION',function)
            projection=out/(label+'.janet');projection.write_text(text)
            d=out/label;r=process.execute([PLAN['runtime'],'-R','-n',str(projection)],d,PLAN['environment'],lock)
            assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes()
            report['profiles'][label]=dict(source_sha256=process.sha(source),projection_sha256=process.sha(projection),bytecode_sha256=process.sha(d/'stdout.bin'),function=function)
            process.save(out/'results.json',report)
        report['status']='four-source-bound-native-disassemblies-captured';process.save(out/'results.json',report)
    print(report['status'])

if __name__=='__main__':main()
