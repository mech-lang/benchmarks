"""Normalize Luau source using its native lexer/AST; count authored C++ hosts."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from luau_run import ROOT, HERE, SOURCE, BUILD
from lean_run import sha


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output=args.output.resolve()
    args.output.mkdir(parents=True,exist_ok=False)
    reader=BUILD/'luau-source-reader'
    fixtures={
        'packed-bindings':('local a=1; local b=2\n',2),
        'expanded-bindings':('local a=1\nlocal b=2\n',2),
        'parallel-binding':('local a,b=1,2\n',1),
        'inline-conditional':('if true then print(1) end\n',3),
        'expanded-conditional':('if true then\n print(1)\nend\n',3),
        'function-body':('local function f() return "--not a comment" end\n',3),
        'comments':('-- comment\n--[[ block\ncomment ]]\n',0),
        'native-directive':('--!native\nlocal a=1\n',2),
        'typed-compound':('local a: number=1\na += 2\n',2),
        'nested-packed':('for i=1,3 do if i>0 then print(i) else break end end\n',7),
    }
    captured={}
    for name,(source,expected) in fixtures.items():
        path=args.output/(name+'.luau')
        path.write_text(source)
        result=subprocess.run([reader,path],capture_output=True,text=True,check=True)
        record=json.loads(result.stdout)
        assert record['canonical_loc']==expected,(name,record,expected)
        captured[name]=record
    invalid=args.output/'invalid.luau';invalid.write_text('local function broken(\n')
    assert subprocess.run([reader,invalid],capture_output=True).returncode==1
    units={}
    for path in sorted(SOURCE.glob('*.luau')):
        result=subprocess.run([reader,path],capture_output=True,text=True,check=True)
        record=json.loads(result.stdout)
        record.update(sha256=sha(path),path=str(path.relative_to(ROOT)),source_language='Luau')
        record['expansions']=[dict(line=o['line'],extra_units=o['units']-1,reason='Native AST statement/control owners and written closing or else tokens sharing one line')
                              for o in record['owners'] if o['units']>1]
        units[path.name]=record
    for path in sorted(SOURCE.glob('*.cpp')):
        command=['/usr/bin/clang++','-fsyntax-only','-Xclang','-dump-raw-tokens',str(path)]
        result=subprocess.run(command,capture_output=True,text=True,check=True)
        (args.output/(path.name+'.tokens')).write_text(result.stderr)
        pattern=re.compile(r"^(\w+) .*Loc=<"+re.escape(str(path))+r':(\d+):(\d+)>',re.M)
        lines={int(m[2]) for m in pattern.finditer(result.stderr) if m[1] not in ('unknown','comment','eof')}
        assert lines
        units[path.name]=dict(sha256=sha(path),path=str(path.relative_to(ROOT)),source_language='C++',
                             physical_loc=len(lines),canonical_loc=len(lines),token_lines=sorted(lines),expansions=[],
                             policy='Native raw-token lines exclude comments/whitespace; retained C++ is written with one independent statement per line. Preprocessor directives count; all authored host units count.')
    profiles={}
    for path in sorted(SOURCE.glob('*.luau')):
        files=[path.name,'Host.cpp']+(['Regex.cpp'] if path.stem=='regexredux' else ['Bigint.cpp'] if path.stem=='pidigits' else [])
        profiles[path.stem]=dict(files=files,canonical_loc=sum(units[n]['canonical_loc'] for n in files),
                                 physical_loc=sum(units[n]['physical_loc'] for n in files),formatted_loc=None)
    report=dict(schema='luau-source-counts.v1',status='QUALIFIED_FOR_RETAINED_SOURCE_BUNDLES',
                fixtures=captured,syntax_rejection_verified=True,units=units,profiles=profiles,
                reader_sha256=sha(reader),reader_source_sha256=sha(HERE/'source-counts-v1/Reader.cpp'),
                controller_sha256=sha(__file__),toolchain_revision='9d7748a4f324213a18cb8283fa2a77c330225fa0',
                rule='Native Luau token lines plus packed independent AST statement/control and written closing/branch owners. Parallel assignments remain a single language statement. All authored host/interface compilation units count in each using bundle.',
                formatted_loc_qualified=False,benchmark_samples=0,chart_admission=False)
    (args.output/'qualified-counts.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(profiles,indent=2))


if __name__=='__main__':
    main()
