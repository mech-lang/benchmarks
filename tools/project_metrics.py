#!/usr/bin/env python3
"""Collect a dated project inventory from immutable Git blobs, plus GitHub evidence.

No build, test, checkout modification or publication occurs. Source inventories
are not executed test counts or line coverage. GitHub job counts are CI jobs.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tomllib
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = {'.rs': 'Rust', '.mec': 'Mech', '.py': 'Python', '.js': 'JavaScript',
             '.mjs': 'JavaScript', '.ts': 'TypeScript', '.tsx': 'TypeScript',
             '.sh': 'Shell', '.c': 'C', '.h': 'C/C++ headers', '.cpp': 'C++',
             '.cc': 'C++', '.hpp': 'C/C++ headers', '.html': 'HTML', '.css': 'CSS'}
EXCLUDED_PARTS = {'.git', '.local', 'target', 'node_modules', 'vendor', 'dist', '.build', 'pkg'}
POLICY = dict(id='mech.project-inventory.v1', languages=LANGUAGES,
              excluded_path_parts=sorted(EXCLUDED_PARTS),
              lines='Physical lines, including comments and blank lines; not semantic LOC.',
              tests='Rust files in tests directories or with test/test(s) filename segments; not executed tests.',
              dependencies='Unique registry/Git dependency names declared in first-party Cargo manifests outside fixture folders, including optional/dev/build/target entries. Path dependencies are separate authored packages; this is not the enabled build graph.',
              lockfile='Root Cargo.lock packages with a source, across its recorded resolution; not a particular feature selection.')


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def included(path):
    return not EXCLUDED_PARTS.intersection(Path(path).parts)


def component(path):
    parts = path.split('/')
    return '/'.join(parts[:2]) if len(parts) > 2 and parts[0] in {'src', 'hosts', 'machines'} else parts[0] if len(parts) > 1 else 'root'


def test_file(path):
    return 'tests' in Path(path).parts or bool(re.search(r'(^|_)tests?(_|\.)', Path(path).name))


def summarize_files(files):
    def counts(rows):
        return dict(files=len(rows), bytes=sum(r['bytes'] for r in rows),
                    physical_lines=sum(r['physical_lines'] for r in rows),
                    nonempty_lines=sum(r['nonempty_lines'] for r in rows))
    languages = {language: counts([r for r in files if r['language'] == language])
                 for language in sorted({r['language'] for r in files})}
    components = {name: counts([r for r in files if r['component'] == name])
                  for name in sorted({r['component'] for r in files})}
    return dict(**counts(files), languages=languages, components=components,
                rust_test_files=sum(r['language'] == 'Rust' and r['test_file'] for r in files),
                mech_test_files=sum(r['language'] == 'Mech' and r['test_file'] for r in files))


def dependency_names(manifests):
    names = set()
    packages = []
    def visit(document):
        for key, value in document.items():
            if key in {'dependencies', 'dev-dependencies', 'build-dependencies'} and isinstance(value, dict):
                for name, spec in value.items():
                    if isinstance(spec, str): names.add(name)
                    elif isinstance(spec, dict) and not spec.get('path') and not spec.get('workspace'):
                        names.add(spec.get('package', name))
        if isinstance(document.get('workspace'), dict): visit(document['workspace'])
        for target in document.get('target', {}).values():
            if isinstance(target, dict): visit(target)
    for path, raw in manifests.items():
        document = tomllib.loads(raw.decode())
        if 'package' in document: packages.append(dict(path=path, name=document['package']['name']))
        visit(document)
    return dict(packages=packages, package_count=len(packages), declared_external_names=sorted(names),
                declared_external_count=len(names))


def inventory(root, revision):
    revision = git(root, 'rev-parse', revision + '^{commit}').decode().strip()
    if not re.fullmatch(r'[0-9a-f]{40,64}', revision): raise ValueError('Expected a commit identity')
    records = git(root, 'ls-tree', '-r', '-z', revision).split(b'\0')
    selected = []
    for record in records:
        if not record: continue
        header, path = record.split(b'\t', 1)
        mode, kind, oid = header.decode().split()
        path = path.decode()
        if kind == 'blob' and mode in {'100644', '100755'} and included(path) and (
                Path(path).suffix in LANGUAGES or Path(path).name == 'Cargo.toml' or path == 'Cargo.lock'):
            selected.append((path, oid))
    files, manifests, lock = [], {}, None
    # Batch reads avoid one Git process per source file and ignore working edits.
    process = subprocess.Popen(['git', '-C', str(root), 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for path, oid in selected:
            process.stdin.write((oid + '\n').encode()); process.stdin.flush()
            header = process.stdout.readline().decode().split()
            if len(header) != 3 or header[1] != 'blob': raise ValueError('Missing Git blob')
            raw = process.stdout.read(int(header[2]))
            if len(raw) != int(header[2]) or process.stdout.read(1) != b'\n': raise ValueError('Truncated Git blob')
            if Path(path).name == 'Cargo.toml' and not {'fixtures', 'test-fixtures'}.intersection(Path(path).parts): manifests[path] = raw
            if path == 'Cargo.lock': lock = raw
            language = LANGUAGES.get(Path(path).suffix)
            if not language: continue
            lines = raw.splitlines()
            files.append(dict(path=path, git_blob=oid, sha256=digest(raw), bytes=len(raw),
                              physical_lines=len(lines), nonempty_lines=sum(bool(line.strip()) for line in lines),
                              language=language, component=component(path), test_file=test_file(path)))
    finally:
        process.stdin.close(); process.wait(timeout=30)
        process.stdout.close()
    if process.returncode: raise ValueError('Git blob reader failed')
    dependencies = dependency_names(manifests)
    dependencies['manifest_hashes'] = {path: digest(raw) for path, raw in manifests.items()}
    dependencies['resolved_external_count'] = None
    dependencies['multiple_version_names'] = None
    if lock is not None:
        packages = [p for p in tomllib.loads(lock.decode()).get('package', []) if p.get('source')]
        counts = Counter(p['name'] for p in packages)
        dependencies.update(lockfile_sha256=digest(lock), resolved_external_count=len(packages),
                            multiple_version_names=sorted(name for name, count in counts.items() if count > 1))
    return dict(revision=revision, committed_at=git(root, 'show', '-s', '--format=%cI', revision).decode().strip(),
                policy=POLICY, policy_hash=digest(encoded(POLICY)), summary=summarize_files(files),
                dependencies=dependencies, files=files)


class GitHub:
    def __init__(self, repository):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository): raise ValueError('Invalid repository')
        self.base = 'https://api.github.com/repos/' + repository
        self.headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'mech-project-metrics'}
        # Credentials stay in memory and are never written into evidence.
        if shutil.which('gh'):
            result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, timeout=15)
            if result.returncode == 0 and result.stdout.strip(): self.headers['Authorization'] = 'Bearer ' + result.stdout.strip()
        self.evidence = []

    def get(self, suffix):
        url = self.base + suffix
        with urllib.request.urlopen(urllib.request.Request(url, headers=self.headers), timeout=40) as response:
            raw = response.read(12 * 1024 * 1024 + 1)
            if len(raw) > 12 * 1024 * 1024: raise ValueError('GitHub response exceeds limit')
            following = response.headers.get('X-Next-Page', '')
            link = response.headers.get('Link', '')
        self.evidence.append(dict(url=url, sha256=digest(raw), raw_json=raw.decode('utf-8')))
        return json.loads(raw), ('rel="next"' in link or bool(following))

    def collect(self, revision):
        repo, _ = self.get('')
        runs, more = self.get('/actions/runs?' + urllib.parse.urlencode(dict(head_sha=revision, per_page=20)))
        rows = [r for r in runs.get('workflow_runs', []) if r.get('head_sha') == revision]
        latest = next((r for r in rows if r.get('status') == 'completed'), None)
        jobs, jobs_complete = [], True
        if latest:
            for page in range(1, 11):
                data, more_jobs = self.get('/actions/runs/' + str(latest['id']) + '/jobs?per_page=100&page=' + str(page))
                jobs.extend(data['jobs'])
                if not more_jobs: break
            else: jobs_complete = False
        return dict(observed_at=datetime.now(timezone.utc).isoformat(),
                    repository=dict(full_name=repo['full_name'], html_url=repo['html_url'], default_branch=repo['default_branch'],
                                    stars=repo['stargazers_count'], forks=repo['forks_count'], open_items=repo['open_issues_count']),
                    ci=dict(runs=[{key: r.get(key) for key in ('id', 'name', 'head_sha', 'head_branch', 'event', 'status', 'conclusion', 'created_at', 'html_url')} for r in rows],
                            runs_complete=not more, latest_completed_run=latest['id'] if latest else None,
                            jobs=[{key: j.get(key) for key in ('id', 'name', 'status', 'conclusion', 'started_at', 'completed_at', 'html_url')} for j in jobs],
                            jobs_complete=jobs_complete,
                            note='Workflow runs attached to this Git revision. Jobs are not test cases; reusable workflows may validate another requested ref. No line coverage is inferred.'))


def collect(args):
    output = args.output.resolve()
    if output.exists(): raise ValueError('Snapshot directory must be new')
    result = inventory(args.mech, args.revision)
    result.update(schema='mech.project-snapshot.v1', id=output.name, repository=args.repository,
                  track=args.track, label=args.label, captured_at=datetime.now(timezone.utc).isoformat(),
                  collection='Immutable Git objects; working files and untracked files are not counted.')
    evidence = []
    if args.github:
        client = GitHub(args.repository)
        result['github'] = client.collect(result['revision'])
        evidence = client.evidence
    else: result['github'] = None
    output.mkdir(parents=True)
    (output / 'snapshot.json').write_bytes(encoded(result))
    (output / 'github.json.gz').write_bytes(gzip.compress(encoded(evidence), mtime=0))
    pins = {p.name: digest(p.read_bytes()) for p in output.iterdir() if p.is_file()}
    (output / 'evidence.json').write_bytes(encoded(dict(schema='mech.project-evidence.v1', files=pins)))
    print(json.dumps(dict(id=result['id'], revision=result['revision'], source_files=result['summary']['files'],
                         physical_lines=result['summary']['physical_lines'], rust_test_files=result['summary']['rust_test_files'])))


def export_project(output, root=ROOT):
    snapshots = []
    prepared = []
    for directory in sorted((root / 'results/project').glob('*')):
        if not directory.is_dir(): continue
        evidence = json.loads((directory / 'evidence.json').read_bytes())
        if evidence.get('schema') != 'mech.project-evidence.v1': raise ValueError('Unknown project evidence schema')
        if set(evidence['files']) != {'snapshot.json', 'github.json.gz'}: raise ValueError('Unexpected project evidence files')
        for name, wanted in evidence['files'].items():
            path = directory / name
            if path.is_symlink() or digest(path.read_bytes()) != wanted: raise ValueError('Project evidence changed: ' + str(path))
        snapshot = json.loads((directory / 'snapshot.json').read_bytes())
        if snapshot.get('schema') != 'mech.project-snapshot.v1' or snapshot['id'] != directory.name: raise ValueError('Invalid project snapshot')
        if snapshot['policy_hash'] != digest(encoded(snapshot['policy'])) or snapshot['summary'] != summarize_files(snapshot['files']):
            raise ValueError('Project summary does not match retained inventory')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', snapshot['id']): raise ValueError('Unsafe snapshot identifier')
        prepared.append(directory)
        snapshots.append({key: value for key, value in snapshot.items() if key != 'files'})
        snapshots[-1]['evidence_path'] = 'project-evidence/' + snapshot['id']
    # Validate everything before replacing a previous successful export.
    destination = output / 'project-evidence'
    if destination.exists(): shutil.rmtree(destination)
    for directory in prepared:
        target = destination / directory.name
        target.mkdir(parents=True)
        for name in ('snapshot.json', 'github.json.gz', 'evidence.json'): shutil.copyfile(directory / name, target / name)
    raw = encoded(dict(schema='mech.project-dashboard.v1', snapshots=snapshots))
    (output / 'project.json').write_bytes(raw)
    (output / 'project.json.gz').write_bytes(gzip.compress(raw, mtime=0))
    return snapshots


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mech', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--track', required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--repository', default='mech-lang/mech')
    parser.add_argument('--github', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    collect(parser.parse_args())
