#!/usr/bin/env python3
"""Run the original correctness inventory on the current authoritative head."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
DRIVER = Path('/private/tmp/native-final-correctness-driver-v1.py')
assert hashlib.sha256(DRIVER.read_bytes()).hexdigest() == 'ca8743be72315fca351bf36419443c7138afc429697dd8f66bc0ed1d59264bf1'
comparison = json.loads((ROOT / 'current-head-snapshot-comparison.json').read_text())
assert comparison['status'] == 'passed' and comparison['exactly_identical_files'] == 32
assert comparison['subjects'][1]['source']['commit'] == '36bcb9292ed40676a4547c91588c96735785b139'
assert comparison['subjects'][1]['source']['status'] == ''
spec = importlib.util.spec_from_file_location('original_correctness', DRIVER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
original_state = module.source_state


def checked_state(workspace, head):
    # Stop before starting another build batch if the workspace would fall
    # below the existing free-space requirement. Never alter test commands.
    assert shutil.disk_usage(ROOT).free >= 50_000_000_000, 'Need at least50GB free before another build batch'
    return original_state(workspace, head)


module.source_state = checked_state
module.__file__ = __file__
os.environ['M4'] = '/opt/homebrew/Cellar/m4/1.4.21/bin/m4'
sys.argv = [__file__, '--workspace', '/private/tmp/mech-native-consolidation-semantics-v1',
            '--head', '36bcb9292ed40676a4547c91588c96735785b139',
            '--target-dir', '/private/tmp/native-935-current-head-target-v1',
            '--evidence', '/private/tmp/native-935-current-correctness-v1']
if __name__ == '__main__':
    module.main()
