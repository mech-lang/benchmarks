"""Project the retained Mech AOT/Rust endpoints without changing observations."""
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlencode


def export_game_comparisons(catalog, output, reproduction=None):
    output = Path(output)
    recipes = (reproduction or {}).get('programs', {})
    cases = []
    for benchmark in catalog['benchmarks']:
        groups = {group['language']: group for group in benchmark['groups']}
        if not {'mech', 'rust'} <= groups.keys():
            continue
        case = {key: benchmark[key] for key in ('key', 'title', 'workload')}
        for language in ('mech', 'rust'):
            program = catalog['programs'][groups[language]['fast']]
            if (program.get('eligible_for_chart') is False
                    or not math.isfinite(program['seconds']) or program['seconds'] <= 0
                    or program.get('execution_mode') != 'aot'):
                raise ValueError('Benchmarks Game endpoint is not a qualified AOT timing')
            files = []
            for digest in program['files']:
                original = catalog['files'][digest]
                source = original['code'].encode()
                if hashlib.sha256(source).hexdigest() != digest:
                    raise ValueError('Benchmarks Game source does not match its recorded hash')
                suffix = '.mec.txt' if language == 'mech' else '.rs.txt'
                target = output/'implementation-sources'/(digest + suffix)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source)
                files.append({'name': original['name'], 'sha256': digest,
                              'url': '/benchmarks/implementation-sources/' + target.name})
            recipe = recipes.get(program['key'], {})
            if recipe and recipe.get('source_sha256') != program['files']:
                raise ValueError('Benchmarks Game reproduction source identity differs')
            original_url = program.get('source_url')
            if not original_url:
                original_url = next((source.get('url') for source in program.get('authorship', {}).get('sources', [])
                                     if source.get('relationship') == 'implementation'), None)
            case[language] = {
                'program': program['key'], 'seconds': program['seconds'],
                'samples': program['samples'], 'files': files,
                'source_url': files[0]['url'], 'original_url': original_url,
                'report': program.get('report'), 'recorded_at': recipe.get('recorded_at'),
                'version': recipe.get('version_label', 'Not recorded'),
                'host': recipe.get('host'),
                'implementation_url': '/benchmarks/#' + urlencode({'v': '1', 'inspect': '1', 'detail.program': program['key']}),
            }
        cases.append(case)
    bundle = {'schema': 'mech.benchmarks-game-comparisons.v1',
              'hardware': catalog.get('protocol', {}).get('hardware'),
              'timing': catalog.get('protocol', {}).get('timing'),
              'selection': 'Retained fastest qualified Mech AOT and Rust endpoints; observations from their respective recorded reports.',
              'cases': cases}
    (output/'game-comparisons.json').write_text(json.dumps(bundle, ensure_ascii=False, separators=(',', ':')) + '\n')
    return bundle
