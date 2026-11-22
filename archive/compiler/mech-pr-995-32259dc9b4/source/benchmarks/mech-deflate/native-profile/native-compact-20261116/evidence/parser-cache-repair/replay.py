"""Build the original source with both standard recipes and check image identity."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json,subprocess,sys
here=Path(__file__).resolve().parent;p=ArgumentParser(__doc__);p.add_argument('output',type=Path);p.add_argument('--target-dir',type=Path);p.add_argument('--mimalloc-object',type=Path);args=p.parse_args()
root=here.parents[5];profile=here.parent.parent;summary=json.loads((here/'summary.json').read_text());out=args.output.resolve();out.mkdir(parents=True)
for role,variant in [('byte-load-linear',None),('control','m1-shared-code-pages-64')]:
 dest=out/role;cmd=[sys.executable,str(profile/'rebuild.py'),str(dest)]
 if variant:cmd+=['--variant',variant]
 if args.target_dir:cmd+=['--target-dir',str(args.target_dir.resolve())]
 if args.mimalloc_object:cmd+=['--mimalloc-object',str(args.mimalloc_object.resolve())]
 subprocess.run(cmd,cwd=root,check=True)
 files={'program.o':dest/'native/program.o','metadata.json':dest/'native/metadata.json','program.mecb':dest/'frontend/program.mecb'}
 actual={name:sha256(path.read_bytes()).hexdigest() for name,path in files.items()};assert actual==summary['qualified_artifacts'][role]
 print(role,'object, metadata and bytecode exactly match the qualified image')
