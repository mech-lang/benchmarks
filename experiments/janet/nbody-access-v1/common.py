"""Pinned shared owner, exact source set and retained finite-energy oracle."""
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('nbody_owned',HERE.parent/'knucleotide-bytes-v1/process.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
PLAN=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
SOURCES={'parent':HERE.parent/'source-v2/nbody.janet',**{name:HERE/'sources'/(name+'.janet') for name in ('intrinsic-get','cached-pairs','scalar-registers')}}
sys.path.insert(0,str(HERE.parent/'bounded-v1'))
from outputs import validate_success
