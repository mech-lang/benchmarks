"""Project retained AOT and JIT comparisons without changing observations."""
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
from urllib.parse import urlencode


def _qualified(program, mode):
    seconds = program.get('seconds')
    return (program.get('eligible_for_chart') is not False
            and isinstance(seconds, (int, float)) and math.isfinite(seconds) and seconds > 0
            and program.get('execution_mode') == mode and bool(program.get('samples')))


def jit_admission(program, recipes):
    """Recognize recorded JIT modes or a source-bound JIT-enabled launch.

    A launcher establishes the enabled runtime, not a trace proving that every
    operation ran as machine code. Historical mode/verification fields stay intact.
    """
    if _qualified(program, 'jit'):
        return {'basis': 'recorded-jit-mode', 'recorded_execution_mode': 'jit'}
    if program.get('execution_mode') not in (None, 'unknown'):
        return None
    seconds = program.get('seconds')
    if (program.get('eligible_for_chart') is False or not isinstance(seconds, (int, float))
            or not math.isfinite(seconds) or seconds <= 0 or not program.get('samples')):
        return None
    recipe = recipes.get(program['key'], {})
    command = recipe.get('command') or []
    if not command or recipe.get('source_sha256') != program['files']:
        return None
    executable, arguments = Path(command[0]).name, command[1:]
    runtime_languages = {'java': {'java', 'kotlin', 'scala', 'clojure'}, 'julia': {'julia'},
                         'node': {'javascript', 'typescript', 'elm'}, 'luajit': {'luajit'}}
    if program.get('language') not in runtime_languages.get(executable, set()):
        return None
    environment = recipe.get('environment') or {}
    flags = arguments + [flag for key in ('NODE_OPTIONS', 'JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS')
                         for flag in shlex.split(str(environment.get(key, '')))]
    pair = lambda first, second: any(flags[index:index+2] == [first, second] for index in range(len(flags)))
    documentation = {
        'java': 'https://docs.oracle.com/en/java/javase/24/docs/specs/man/java.html',
        'julia': 'https://docs.julialang.org/en/v1/manual/command-line-interface/',
        'node': 'https://nodejs.org/download/release/v22.23.0/docs/api/cli.html',
        'luajit': 'https://luajit.org/running.html',
    }
    enabled = (executable == 'java' and '-Xint' not in flags and '-XX:-UseCompiler' not in flags
               or executable == 'julia' and not any(flag == '--compile=no' for flag in flags) and not pair('--compile', 'no')
               or executable == 'node' and not any(flag in ('--jitless', '--no-opt') for flag in flags)
               or executable == 'luajit' and '-joff' not in flags and not pair('-j', 'off'))
    if not enabled:
        return None
    return {'basis': 'recorded-jit-enabled-runtime-launch', 'command': command,
            'recorded_execution_mode': program.get('execution_mode'),
            'source_sha256': recipe['source_sha256'], 'runtime_version': recipe.get('version_label'),
            'documentation': documentation[executable], 'machine_code_trace_recorded': False}


def _endpoint(program, catalog, output, recipes):
    files = []
    for digest in program['files']:
        original = catalog['files'][digest]
        source = original['code'].encode()
        if hashlib.sha256(source).hexdigest() != digest:
            raise ValueError('Benchmarks Game source does not match its recorded hash')
        suffix = Path(original['name']).suffix
        if not re.fullmatch(r'\.[a-zA-Z0-9]+', suffix):
            suffix = '.source'
        target = output/'implementation-sources'/(digest + suffix + '.txt')
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
    return {'program': program['key'], 'seconds': program['seconds'],
            'samples': program['samples'], 'files': files,
            'source_url': files[0]['url'], 'original_url': original_url,
            'report': program.get('report'), 'recorded_at': recipe.get('recorded_at'),
            'version': recipe.get('version_label', 'Not recorded'), 'host': recipe.get('host'),
            'implementation_url': '/benchmarks/#' + urlencode({'v': '1', 'inspect': '1', 'detail.program': program['key']})}


def export_game_comparisons(catalog, output, reproduction=None):
    output = Path(output)
    recipes = (reproduction or {}).get('programs', {})
    cases, jit_cases = [], []
    programs = {**catalog.get('program_inventory', {}), **catalog['programs']}
    languages = {language['key']: language for language in catalog.get('languages', [])}
    for benchmark in catalog['benchmarks']:
        groups = {group['language']: group for group in benchmark['groups']}
        if {'mech', 'rust'} <= groups.keys():
            case = {key: benchmark[key] for key in ('key', 'title', 'workload')}
            for language in ('mech', 'rust'):
                program = catalog['programs'][groups[language]['fast']]
                if not _qualified(program, 'aot'):
                    raise ValueError('Benchmarks Game endpoint is not a qualified AOT timing')
                case[language] = _endpoint(program, catalog, output, recipes)
            cases.append(case)
        if 'mech-jit' not in groups:
            continue
        mech = programs[groups['mech-jit']['fast']]
        if not _qualified(mech, 'jit'):
            raise ValueError('Mech JIT endpoint is not a qualified JIT timing')
        peers = sorted((program for program in programs.values()
                        if program.get('benchmark') == benchmark['key']
                        and not program.get('language', '').startswith(('mech', 'rust'))
                        and not program.get('timing_alias_of') and jit_admission(program, recipes)),
                       key=lambda program: (program['seconds'], program['key']))
        if not peers:
            continue
        peer = peers[0]
        jit_cases.append({key: benchmark[key] for key in ('key', 'title', 'workload')} | {
            'mech': _endpoint(mech, catalog, output, recipes),
            'reference': _endpoint(peer, catalog, output, recipes) | {
                'language': peer['language'], 'label': languages[peer['language']]['label'], 'execution_mode': 'jit',
                'jit_admission': jit_admission(peer, recipes)},
            'eligible_external_jit_programs': len(peers)})
    bundle = {'schema': 'mech.benchmarks-game-comparisons.v1',
              'hardware': catalog.get('protocol', {}).get('hardware'),
              'timing': catalog.get('protocol', {}).get('timing'),
              'selection': 'Retained fastest qualified Mech AOT and Rust endpoints; observations from their respective recorded reports.',
              'cases': cases, 'jit_cases': jit_cases,
              'jit_selection': 'Fastest recorded eligible external JIT runtime per workload across retained programs and inventory. Selection uses recorded JIT modes or source-bound launcher recipes with JIT enabled; it does not claim a machine-code trace for every operation. Full-process time includes runtime startup, JIT compilation, input/output and shutdown; these are not warmed-kernel timings.'}
    (output/'game-comparisons.json').write_text(json.dumps(bundle, ensure_ascii=False, separators=(',', ':')) + '\n')
    return bundle
