from pathlib import Path
import collections
import hashlib
import json
import re
import subprocess

ROOT = Path('/private/tmp/mech-post-native-cleanup-final')
AUDIT = Path('/private/tmp/benchmarks-native-consolidation/experiments/mech/native-owner-aot-v1/post-native-architecture-cleanup-v1/audit/visibility-reexports-v1')
BASE = '6d6a99aeca3bf249be47f5b7a1198b3bd337dc2a'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)
sources = {p: p.read_text() for p in ROOT.rglob('*.rs') if '.git' not in p.parts and 'target' not in p.parts}
path_targets = set()
for path, text in sources.items():
    for match in re.finditer(r'#\[path\s*=\s*"([^"]+)"\]\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)\s*;', text):
        path_targets.add((path.parent / match[1]).resolve())

edits = collections.defaultdict(list)
modules = []
excluded = collections.defaultdict(list)
for path, text in sources.items():
    relative = path.relative_to(ROOT)
    matches = list(re.finditer(r'^pub\(in (crate(?:::\w+)*)\) mod (\w+)\s*;', text, re.M))
    if not matches:
        continue
    reason = None
    if 'src' not in relative.parts:
        reason = 'non-src file'
    elif any(path.resolve() == target or (target.name == 'mod.rs' and target.parent in path.resolve().parents) for target in path_targets):
        reason = 'path-remapped source subtree'
    elif re.search(r'^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+\w+\s*\{', text, re.M):
        reason = 'inline module source'
    if not reason:
        source_root = max(i for i, part in enumerate(relative.parts) if part == 'src')
        components = list(relative.parts[source_root + 1:])
        components[-1] = path.stem
        if components[-1] in ('mod', 'lib', 'main'):
            components.pop()
        current = 'crate' + ''.join('::' + part for part in components)
    for match in matches:
        why = reason
        if not why and match[1] != current:
            why = 'ancestor or other restriction'
        if not why and text[:match.start()].rstrip().rsplit('\n', 1)[-1].startswith('#[path'):
            why = 'path attr on declaration'
        if not why:
            base = path.parent if path.name in ('mod.rs', 'lib.rs', 'main.rs') else path.parent / path.stem
            targets = [p for p in (base / (match[2] + '.rs'), base / match[2] / 'mod.rs') if p.is_file()]
            if len(targets) != 1:
                why = 'default target unresolved'
        row = {'file': str(relative), 'line_before': text.count('\n', 0, match.start()) + 1, 'before': match[0]}
        if why:
            excluded[why].append(row)
            continue
        replacement = 'mod ' + match[2] + ';'
        row.update(after=replacement, current_module=current, target=str(targets[0].relative_to(ROOT)))
        modules.append(row)
        edits[path].append((match.start(), match.end(), replacement))

pattern = re.compile(r'(?P<attrs>(?:^#\[[^\n]*\]\n)*)(?P<vis>pub(?:\(in crate(?:::\w+)*\))?) use (?P<parent>(?:crate|self|super)(?:::\w+)*)::(?P<item>\w+(?: as \w+)?);\n', re.M)
groups = []
for path, text in sources.items():
    if not path.is_relative_to(ROOT / 'hosts/gpu/src/native_artifact'):
        continue
    runs = []
    run = []
    for match in pattern.finditer(text):
        key = (match['attrs'], match['vis'], match['parent'])
        if run and (key != run[-1][0] or text[run[-1][1].end():match.start()].strip()):
            if len(run) > 1:
                runs.append(run)
            run = []
        run.append((key, match))
    if len(run) > 1:
        runs.append(run)
    for run in runs:
        (attributes, visibility, parent), first = run[0]
        end = run[-1][1].end()
        items = [match['item'] for _, match in run]
        replacement = attributes + visibility + ' use ' + parent + '::{\n' + ''.join('    ' + item + ',\n' for item in items) + '};\n'
        groups.append({'file': str(path.relative_to(ROOT)), 'line_before': text.count('\n', 0, first.start()) + 1, 'before': text[first.start():end], 'after_before_format': replacement, 'attributes': attributes, 'visibility': visibility, 'source_module': parent, 'items': items})
        edits[path].append((first.start(), end, replacement))

assert len(modules) == 179, len(modules)
assert len(groups) == 17, len(groups)
assert sum(len(row['items']) for row in groups) == 68
assert len({row['file'] for row in modules}) == 81
assert len({row['file'] for row in groups}) == 9
AUDIT.mkdir(parents=True, exist_ok=False)
manifest = {'before_commit': BASE, 'module_declarations': len(modules), 'module_files': 81, 'reexport_groups': len(groups), 'reexport_items': 68, 'reexport_files': 9, 'rationale': 'A module declaration restricted to its exact enclosing module has the same effective visibility as a private declaration. Only file-scope declarations with a unique default target are changed. Consecutive reexports are grouped only when attributes, effective visibility and source module match exactly; all aliases remain unchanged.', 'exclusions': {key: len(rows) for key, rows in excluded.items()}, 'primary_timing_samples': 0, 'qualification': 'Static cleanup only; pending base repair/coverage adoption and runtime qualification.', 'files': {}}
for path, changes in sorted(edits.items()):
    text = sources[path]
    ordered = sorted(changes)
    assert all(a[1] <= b[0] for a, b in zip(ordered, ordered[1:]))
    for start, end, replacement in reversed(ordered):
        text = text[:start] + replacement + text[end:]
    path.write_text(text)
    manifest['files'][str(path.relative_to(ROOT))] = {'before_sha256': hashlib.sha256(sources[path].encode()).hexdigest(), 'after_before_format_sha256': hashlib.sha256(text.encode()).hexdigest()}
for filename, data in [('modules.json', modules), ('reexports.json', groups), ('excluded.json', excluded), ('manifest.json', manifest)]:
    (AUDIT / filename).write_text(json.dumps(data, indent=2) + '\n')
(AUDIT / 'transform.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({key: value for key, value in manifest.items() if key != 'files'}, indent=2))
