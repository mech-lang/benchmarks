"""Exact archived-metadata intake for the frozen eleven-command Julia inspector.

Only the 31 absent historical evidence names in the reviewed manifest may move.
Native tools, libraries, bitcode, objects and executable inputs remain physical.
The original inspector still owns the common mutex, processes and finalization.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import types

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = Path(__file__).resolve()
ORIGINAL = ROOT/'tools/qualification/julia_native_inspection.py'
ORIGINAL_SHA = '877bda82e014e16a5380cc46b283ba90dca71f02c4a285994df5c54ab883489a'
MANIFEST = ROOT/'experiments/julia-aot/trimmed-native-inspection-v1/metadata-relocation-evidence-v1.json'
MANIFEST_SHA = 'f4746664ac280a1a30954de518ed8fb4b33c174b6efec0201fad713cbe5a008f'
OLD_ROOT = Path('/Users/cim310/mech-lang/benchmarks')
LINK_RESULT = ROOT/'archive/languages/julia-aot/20261012/jobs/official-static-io-safe-link-v3/link-result.json'
LINK_RESULT_SHA = '03e770888f20bca9eca6ca7c13d287eb841e4cc1c4a1a90922f18b5d2f4cd991'


def require(value, message):
    if not value: raise AssertionError(message)


def regular(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, 'Physical absolute metadata required: '+str(path))
    require(stat.S_ISREG(path.lstat().st_mode), 'Regular metadata required: '+str(path))
    return path


def digest(path):
    return hashlib.sha256(regular(path).read_bytes()).hexdigest()


class ExactMetadata:
    def __init__(self, root, rows):
        self.root = root
        self.rows = {}
        self.used = set()
        targets = set()
        for row in rows:
            old = Path(row['original_path']); target = root/row['archived_path']
            require(old.is_absolute() and old.is_relative_to(OLD_ROOT), 'Unsupported historical evidence root')
            require(target.is_relative_to(root/'archive') and target.suffix in ('.json','.stdout','.stderr'),
                    'Only archived JSON/stdout/stderr evidence may move')
            require(old.suffix == target.suffix and str(old) not in self.rows and target not in targets,
                    'Duplicate or changed metadata path kind')
            require(type(row['bytes']) is int and row['bytes'] >= 0 and len(row['sha256']) == 64,
                    'Invalid exact metadata identity')
            self.rows[str(old)] = dict(row, target=str(target)); targets.add(target)

    def check(self):
        for old, row in self.rows.items():
            require(not os.path.lexists(old), 'Historical evidence path reappeared: '+old)
            target = regular(row['target'])
            raw = target.read_bytes()
            require(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'],
                    'Archived evidence changed: '+str(target))

    def pin(self, original_pin, pins, path, expected=None):
        row = self.rows.get(str(path))
        if row is None:
            return original_pin(pins, path, expected)
        require(expected == row['sha256'], 'Historical metadata pin differs')
        require(not os.path.lexists(path), 'Historical evidence path reappeared: '+str(path))
        target = regular(row['target'])
        require(target.stat().st_size == row['bytes'], 'Archived evidence length differs')
        result = original_pin(pins, target, expected)
        self.used.add(str(path))
        return result


def reviewed_mapping():
    require(digest(MANIFEST) == MANIFEST_SHA, 'Exact metadata mapping manifest changed')
    manifest = json.loads(MANIFEST.read_bytes())
    require(manifest['schema'] == 'julia-inspection-metadata-relocation-evidence-v1'
            and manifest['missing_metadata_paths'] == 31 and len(manifest['mappings']) == 31,
            'Exact 31-entry mapping required')
    index = ROOT/manifest['migration_index']['path']
    require(index == ROOT/'migration/reorganization-paths.tsv'
            and digest(index) == manifest['migration_index']['sha256'], 'Migration index changed')
    lines = index.read_text().splitlines()
    require(digest(LINK_RESULT) == LINK_RESULT_SHA, 'Retained link receipt changed')
    original_pins = json.loads(LINK_RESULT.read_bytes())['pins']
    for row in manifest['mappings']:
        require(row['source_record'] == 'link_result'
                and row['source_record_ref'] == {'path':str(LINK_RESULT),'sha256':LINK_RESULT_SHA},
                'Mapping must belong to the exact retained link receipt')
        require(original_pins.get(row['original_path']) == row['sha256'], 'Mapping lacks original pin')
        expected = [str(Path(row['original_path']).relative_to(OLD_ROOT)), row['archived_path'],
                    row['migration_git_blob'], row['migration_mode']]
        require(lines[row['migration_line']-1].split('\t') == expected, 'Mapping differs from migration row')
    resolver = ExactMetadata(ROOT, manifest['mappings'])
    resolver.check()
    return resolver, index


def load_original():
    raw = regular(ORIGINAL).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == ORIGINAL_SHA, 'Frozen inspector changed')
    module = types.ModuleType('julia_original_inspection'); module.__file__ = str(ORIGINAL)
    exec(compile(raw, str(ORIGINAL), 'exec'), module.__dict__)
    require(module.ROOT == ROOT, 'Original inspection root differs')
    return module


def install(original):
    """Keep original ROOT, main, lock, observer and lifecycle functions intact."""
    pin, verify, build_plan, finish = original.pin, original.verify, original.build_plan, original.finish
    resolver = None

    def mapped_pin(pins, path, expected=None):
        return resolver.pin(pin, pins, path, expected) if resolver is not None else pin(pins, path, expected)

    def mapped_verify(pins, resolutions, unavailable=()):
        require(resolver is not None, 'Reviewed metadata intake not initialized')
        require(digest(MANIFEST) == MANIFEST_SHA, 'Metadata mapping manifest changed')
        resolver.check()
        verify(pins, resolutions, unavailable)
        resolver.check()
        require(digest(MANIFEST) == MANIFEST_SHA, 'Metadata mapping manifest changed')

    def mapped_plan(output):
        nonlocal resolver
        resolver, index = reviewed_mapping()
        plan = build_plan(output)
        require(resolver.used == set(resolver.rows), 'Not all exact historical mappings were consumed')
        for path, expected in ((ORIGINAL,ORIGINAL_SHA),(ADAPTER,None),(MANIFEST,MANIFEST_SHA),
                               (index,None),(LINK_RESULT,LINK_RESULT_SHA)):
            pin(plan['pins'],path,expected)
        plan['original_controller'] = {'path':str(ORIGINAL),'sha256':ORIGINAL_SHA}
        plan['controller'] = str(ADAPTER); plan['controller_sha256'] = digest(ADAPTER)
        plan['historical_metadata_mapping_manifest'] = {'path':str(MANIFEST),'sha256':MANIFEST_SHA}
        plan['historical_evidence_mappings'] = [
            {'original_path':old,'archived_path':row['target'],'sha256':row['sha256'],'bytes':row['bytes']}
            for old,row in resolver.rows.items()]
        plan['input_resolutions'] = {name:str(Path(name).resolve()) for name in plan['pins']}
        resolver.check()
        return plan

    def mapped_finish(report, plan, *args):
        # The original report controller_sha256 names the frozen implementation.
        # The actual entry adapter and its exact mapping are separately explicit.
        report['entry_adapter'] = {'path':str(ADAPTER),'sha256':plan['controller_sha256']}
        report['historical_metadata_mapping_manifest'] = plan['historical_metadata_mapping_manifest']
        return finish(report,plan,*args)

    original.pin = mapped_pin; original.verify = mapped_verify
    original.build_plan = mapped_plan; original.finish = mapped_finish
    return original


def main():
    return install(load_original()).main()


if __name__ == '__main__': raise SystemExit(main())
