#!/usr/bin/env python3
"""Replay the retained qualified Crystal policy; never relabel it uniform LOC."""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT/'archive/validation/loc-normalization/20261012'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    fixture = BASE/'crystal-brace-repair-v2/jobs/fixtures-replay-v1/fixture-receipt.json'
    qualified = json.loads(fixture.read_bytes())
    assert qualified['status'] == 'passed' and qualified['tests_run'] == 36
    assert qualified['failures'] == qualified['errors'] == 0
    assert sys.version.split()[0] == qualified['python_version'].split()[0]
    nim = json.loads((ROOT/'experiments/nim/fannkuch-v1/source-counter-v1/plan-v2.json').read_bytes())
    pygments = Path(nim['pygments_root'])
    assert sha(pygments/'__init__.py') == qualified['pygments_module_sha256']
    counter = BASE/'crystal-brace-repair-v2/foreign_crystal.py'
    assert sha(counter) == 'df4481e27581d106e9bd7af181395dd5ba5d40d1848d077dda79b98550a17b8a'
    dependencies = {name: ROOT/pin['path'] for name, pin in nim['counter'].items() if name != 'foreign_nim.py'}
    for name, path in dependencies.items():
        assert sha(path) == nim['counter'][name]['sha256']
    overlay_path = ROOT/'archive/languages/crystal/20261012/source-counts/corrected-qualified-overlay-v2/qualified-loc-overlay.json'
    overlay = json.loads(overlay_path.read_bytes())
    output = HERE/'source-counts-v1'
    output.mkdir(exist_ok=False)
    lockpath = Path('/private/tmp/mech-clbg-timing.lock')
    with lockpath.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        inode = os.fstat(lock.fileno()).st_ino
        assert inode == lockpath.stat().st_ino == 82961857
        sys.path.insert(0, str(pygments.parent))
        for name in ['canonical.py', 'foreign_core.py', 'foreign_future_mask.py']:
            spec = importlib.util.spec_from_file_location(name[:-3], dependencies[name])
            module = importlib.util.module_from_spec(spec)
            sys.modules[name[:-3]] = module
            spec.loader.exec_module(module)
        spec = importlib.util.spec_from_file_location('foreign_crystal', counter)
        normalizer = importlib.util.module_from_spec(spec)
        sys.modules['foreign_crystal'] = normalizer
        spec.loader.exec_module(normalizer)
        records = []
        for name, parent in [('compact', 'compact'), ('parallel', 'optimized')]:
            old = ROOT/f'programs/crystal/regexredux/crystal-regexredux-{parent}/{parent}.cr'
            new = HERE/f'source/{name}.cr'
            saved = overlay['profiles']['crystal-regexredux-'+parent]
            assert sha(old) == saved['source_sha256']
            control = normalizer.normalize(old.read_text(), 'crystal')
            for key in ['physical_loc', 'canonical_loc', 'expansions', 'diagnostics']:
                if key in saved:
                    assert control[key] == saved[key], ('Parent control differs', name, key)
            proposed = normalizer.normalize(new.read_text(), 'crystal')
            assert not control['diagnostics'] and not proposed['diagnostics']
            assert proposed['physical_loc'] == control['physical_loc']
            assert proposed['canonical_loc'] == control['canonical_loc']
            assert [[(e['kind'], e['units'], e['scope']) for e in r.get('canonical_events', [])]
                    for r in proposed['expansions']] == [
                    [(e['kind'], e['units'], e['scope']) for e in r.get('canonical_events', [])]
                    for r in control['expansions']]
            record = {'variant': name, 'source_sha256': sha(new), 'parent_sha256': sha(old),
                      'parent_full_retained_metric_matches': True, 'control': control, 'candidate': proposed,
                      'application_loc': None, 'independent_approval': None}
            (output/(name+'.json')).write_text(json.dumps(record, indent=2)+'\n')
            records.append({'variant': name, 'proposed_retained_loc': proposed['canonical_loc'],
                            'physical_loc': proposed['physical_loc']})
        modules = {}
        for name, module in sys.modules.items():
            filename = getattr(module, '__file__', None)
            if filename and (name in ['canonical', 'foreign_core', 'foreign_future_mask', 'foreign_crystal'] or name.startswith('pygments')):
                path = Path(filename)
                modules[str(path)] = sha(path)
        receipt = {'schema': 'crystal-byte-offset-source-replay.v1', 'status': 'passed-proposals-awaiting-independent-review',
                   'fixture': {'path': str(fixture.relative_to(ROOT)), 'sha256': sha(fixture), 'tests_reused': 36},
                   'modules_actually_imported': modules, 'profiles': records, 'native_processes_started': 0,
                   'policy_limit': 'Exact retained Crystal lexical/owner policy; not native AST, formatted LOC or uniform logical LOC.',
                   'counter_or_constants_modified': False, 'chart_admission': False}
        (output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        assert os.fstat(lock.fileno()).st_ino == lockpath.stat().st_ino == inode
        print(json.dumps({k:v for k,v in receipt.items() if k != 'modules_actually_imported'}))


if __name__ == '__main__':
    main()
