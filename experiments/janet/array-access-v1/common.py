"""Source set and unchanged shared native ownership for array-access candidates."""
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('array_owned',HERE.parent/'knucleotide-bytes-v1/process.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
PLAN=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
SOURCES={
    'binarytrees-parent':('binarytrees',HERE.parent/'source-v2/binarytrees.janet'),
    'binarytrees-cached':('binarytrees',HERE/'sources/binarytrees-cached.janet'),
    'fannkuch-parent':('fannkuchredux',HERE.parent/'source-v2/fannkuchredux.janet'),
    'fannkuch-get':('fannkuchredux',HERE/'sources/fannkuch-get.janet'),
    'fannkuch-bulk':('fannkuchredux',HERE/'sources/fannkuch-bulk.janet')}
sys.path.insert(0,str(HERE.parent/'bounded-v1'))
from outputs import validate_success
