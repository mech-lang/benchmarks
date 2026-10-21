#!/usr/bin/env python3
"""Sequential compilation and independent bounded-output checks; no timings admitted."""
import argparse
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import fcntl
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import random
import re
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOCK = Path('/private/tmp/mech-clbg-timing.lock')
NODE = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
PACKAGES = HERE / '.build/typescript/node_modules'
CRYSTAL = HERE / '.build/crystal/distribution/crystal-1.21.1-1'
PROCESS = ROOT / 'experiments/elixir/rolling-v1/qualification-v1/native_process.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def nucleotide_cases():
    cases = {'empty': b'', 'missing': b'>ONE\nACGT\n',
             'decoys-comments-crlf': b'>THREEextra\r\nAAAA\r\n>THREE\tdesc\r\ngGtA\r\n;ignore\r\nct\r\n>NEXT\r\nTTTT\r\n',
             'first-target-only': b'>THREE one\nACGTACGT\n>THREE two\nTTTT\n',
             'all-triplets': b'>THREE\n' + b''.join(bytes(t) for t in itertools.product(b'ACGT', repeat=3)) + b'\n'}
    for n in range(21):
        cases[f'length-{n}'] = b'>THREE\n' + (b'ACGTGGTATTTTAATTTATAGT' * 2)[:n] + b'\n'
    rng = random.Random(81273)
    dna = b'T' * 18 + bytes(rng.choice(b'ACGT') for _ in range(10021))
    cases['wide-keys'] = b'>THREE full\n' + b'\n'.join(dna[i:i+71] for i in range(0, len(dna), 71))
    return cases


def nucleotide_reference(raw):
    bases = bytearray()
    started = False
    for line in re.split(br'\r\n|\r|\n', raw):
        if line.startswith(b';'):
            continue
        if started:
            if line.startswith(b'>'):
                break
            bases.extend(line.upper())
        elif line == b'>THREE' or line.startswith((b'>THREE ', b'>THREE\t')):
            started = True
    sequence = bytes(bases)
    assert all(b in b'ACGT' for b in sequence)
    output = []
    for width in [1, 2]:
        counts = Counter(sequence[i:i+width] for i in range(max(0, len(sequence)-width+1)))
        for key, count in sorted(counts.items(), key=lambda row: (-row[1], row[0])):
            value = Decimal.from_float(100.0 * count / (len(sequence)-width+1))
            output.append(key.decode() + ' ' + str(value.quantize(Decimal('.001'), rounding=ROUND_HALF_UP)))
        output.append('')
    for query in [b'GGT', b'GGTA', b'GGTATT', b'GGTATTTTAATT', b'GGTATTTTAATTTATAGT']:
        counts = Counter(sequence[i:i+len(query)] for i in range(max(0, len(sequence)-len(query)+1)))
        output.append(str(counts[query]) + '\t' + query.decode())
    return ('\n'.join(output) + '\n').encode()


PATTERNS = [b'agggtaaa|tttaccct', b'[cgt]gggtaaa|tttaccc[acg]', b'a[act]ggtaaa|tttacc[agt]t',
            b'ag[act]gtaaa|tttac[agt]ct', b'agg[act]taaa|ttta[agt]cct', b'aggg[acg]aaa|ttt[cgt]ccct',
            b'agggt[cgt]aa|tt[acg]accct', b'agggta[cgt]a|t[acg]taccct', b'agggtaa[cgt]|[acg]ttaccct']


def regex_cases():
    rng = random.Random(5371)
    return {'empty': b'', 'mixed-case': b'>header\nAGGGTAAAagggtaaattTaccct\ntHaNtHaS BY aND WaS aNS\n',
            'adjacent-matches': b'>h\n' + b'agggtaaatttaccct' * 256 + b'\n',
            'substitution-order': b'>h\ntHaN tHat aND caN HaD HaS WaS aN aS at BY <tag> |abc|\n',
            'utf8-gap': '>h\nagggtaaaクリスタルtttaccct\n'.encode(),
            'random': b'>h\n' + bytes(rng.choice(b'ACGTacgt<>|NDHSWtBa') for _ in range(12000)) + b'\n'}


def regex_reference(raw):
    sequence = re.sub(br'>[^\n]*\n|\n', b'', raw)
    rows = [p.decode() + ' ' + str(len(re.findall(p, sequence))) for p in PATTERNS]
    result = sequence
    for pattern, value in [(br'tHa[Nt]', b'<4>'), (br'aND|caN|Ha[DS]|WaS', b'<3>'),
                           (br'a[NSt]|BY', b'<2>'), (br'<[^>]*>', b'|'), (br'\|[^|][^|]*\|', b'-')]:
        result = re.sub(pattern, value, result)
    return ('\n'.join(rows) + f'\n\n{len(raw)}\n{len(sequence)}\n{len(result)}\n').encode()


def reverse_cases():
    alphabet = b'ACBDGHKMNSRUTWVYacbdghkmnsrutwvy'
    cases = {'empty': b'', 'canonical': b'>ONE description\nACGT\n>TWO\nGGTA\n',
             'comments': b'>ONE\nAC\n;not DNA\nGT\n', 'preheader': b'ignored\n>ONE\nACGT\n',
             'crlf-empty': b'>ONE\r\n\r\n>TWO desc\r\nACGT\r\n>EMPTY',
             'carriage-return': b'>ONE\rACGT\r>TWO\rTTA\r',
             'all-iupac': b'>IUPAC\n' + alphabet + b'\n',
             'long-header': b'>' + b'h' * 10000 + b'\nACGT\n'}
    for n in [1, 2, 59, 60, 61, 119, 120, 121, 4097]:
        cases[f'length-{n}'] = b'>ONE\n' + (alphabet * (n // len(alphabet) + 1))[:n]
    return cases


def reverse_reference(raw):
    table = bytes.maketrans(b'ACBDGHKMNSRUTWVYacbdghkmnsrutwvy', b'TGVHCDMKNSYAAWBRTGVHCDMKNSYAAWBR')
    output = bytearray()
    sequence = bytearray()
    header = None
    def finish():
        if header is not None:
            output.extend(header + b'\n')
            bases = bytes(sequence).translate(table)[::-1]
            for start in range(0, len(bases), 60):
                output.extend(bases[start:start+60] + b'\n')
    for line in re.split(br'\r\n|\r|\n', raw):
        if line.startswith(b'>'):
            finish()
            header = line
            sequence.clear()
        elif header is not None and not line.startswith(b';'):
            sequence.extend(line)
    finish()
    return bytes(output)


def pins():
    paths = [Path(__file__), PROCESS, NODE, ROOT/'experiments/typescript/source-v1/tsconfig.json',
             ROOT/'programs/typescript/knucleotide/typescript-knucleotide-v1/knucleotide.ts',
             ROOT/'experiments/typescript/rolling-map-v1/source/knucleotide.ts',
             ROOT/'programs/d/revcomp/revcomp-d-optimized/optimized.d',
             ROOT/'experiments/d/revcomp-inplace-v1/source/inplace.d', Path('/opt/homebrew/Cellar/ldc/1.43.0/bin/ldc2')]
    for name in ['compact', 'parallel']:
        paths.append(ROOT/f'experiments/crystal/regex-byte-offsets-v1/source/{name}.cr')
    for name in ['compact', 'optimized']:
        paths.append(ROOT/f'programs/crystal/regexredux/crystal-regexredux-{name}/{name}.cr')
    for tree in [PACKAGES, CRYSTAL]:
        paths.extend(p for p in tree.rglob('*') if not p.is_symlink() and p.is_file())
    return {str(p): sha(p) for p in sorted(set(paths))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--plan-sha256')
    args = parser.parse_args()
    plan_path = HERE/'native-plan-v1.json'
    if args.prepare:
        write(plan_path, {'schema': 'remaining-languages-bounded-native.v1', 'pins': pins(),
                         'mutex_inode': LOCK.stat().st_ino, 'languages': ['typescript', 'crystal', 'd'],
                         'quantitative_benchmark': False, 'full_timing_available': False,
                         'limits': 'Sequential fresh processes, 120-second command deadline; no full workload.',
                         'scope_limit': 'Output checks only; required-work, ownership counts and runtime closure review remain separate gates.'})
        print(sha(plan_path))
        return
    assert args.run and sha(plan_path) == args.plan_sha256
    plan = json.loads(plan_path.read_bytes())
    assert pins() == plan['pins']
    output = HERE/'native-v1'
    output.mkdir(exist_ok=False)
    build = HERE/'.build/bounded-v1'
    build.mkdir(exist_ok=False)
    spec = importlib.util.spec_from_file_location('bounded_process', PROCESS)
    process = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(process)
    report = {'schema': plan['schema'], 'plan_sha256': sha(plan_path), 'status': 'running',
              'quantitative_benchmark': False, 'cases': [], 'compilations': []}
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert os.fstat(lock.fileno()).st_ino == plan['mutex_inode'] == LOCK.stat().st_ino
        env = {'PATH': '/opt/homebrew/bin:/usr/bin:/bin', 'LC_ALL': 'C', 'LANG': 'C', 'TZ': 'UTC',
               'TMPDIR': str(build) + '/', 'UV_THREADPOOL_SIZE': '8', 'GOMAXPROCS': '8',
               'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'VECLIB_MAXIMUM_THREADS': '1'}
        def one(command, name, stdin=None, environment=None):
            assert os.fstat(lock.fileno()).st_ino == LOCK.stat().st_ino == plan['mutex_inode']
            result = process.one(list(map(str, command)), output/name, environment or env, build,
                                 lock.fileno(), timeout=120, stdin=stdin)
            process.success(result)
            assert not (output/name/'stderr.bin').read_bytes(), 'Unexpected native diagnostic: ' + name
            assert os.fstat(lock.fileno()).st_ino == LOCK.stat().st_ino == plan['mutex_inode']
            return result
        try:
            commands = {}
            one([NODE, '--version'], 'node-version')
            assert (output/'node-version/stdout.bin').read_bytes() == b'v24.19.0\n'
            one(['/opt/homebrew/Cellar/ldc/1.43.0/bin/ldc2', '--version'], 'ldc-version')
            one([CRYSTAL/'embedded/bin/crystal', '--version'], 'crystal-version')
            assert (output/'crystal-version/stdout.bin').read_bytes().startswith(b'Crystal 1.21.1 ')
            original_config = json.loads((ROOT/'experiments/typescript/source-v1/tsconfig.json').read_bytes())
            for label, source in [('ts-parent', ROOT/'programs/typescript/knucleotide/typescript-knucleotide-v1/knucleotide.ts'),
                                  ('ts-rolling', ROOT/'experiments/typescript/rolling-map-v1/source/knucleotide.ts')]:
                project = build/label
                project.mkdir()
                shutil.copyfile(source, project/'knucleotide.ts')
                config = dict(original_config, files=['knucleotide.ts'])
                write(project/'tsconfig.json', config)
                one([PACKAGES/'@typescript/typescript-darwin-arm64/lib/tsc', '--project', project/'tsconfig.json',
                     '--typeRoots', PACKAGES/'@types', '--pretty', 'false', '--listFiles', '--listEmittedFiles',
                     '--incremental', 'false'], 'compile-'+label)
                emitted = project/'emitted/knucleotide.js'
                shutil.copyfile(emitted, output/(label+'.js'))
                report['compilations'].append({'label': label, 'source_sha256': sha(source), 'emitted_sha256': sha(emitted)})
                commands[label] = [NODE, emitted]
            for label, source in [('d-parent', ROOT/'programs/d/revcomp/revcomp-d-optimized/optimized.d'),
                                  ('d-inplace', ROOT/'experiments/d/revcomp-inplace-v1/source/inplace.d')]:
                binary = build/label
                one(['/opt/homebrew/Cellar/ldc/1.43.0/bin/ldc2', '-O3', '-release', '-boundscheck=off',
                     '-mcpu=native', source, '-of='+str(binary)], 'compile-'+label)
                report['compilations'].append({'label': label, 'source_sha256': sha(source), 'binary_sha256': sha(binary)})
                commands[label] = [binary]
            crystal_env = dict(env, CRYSTAL_PATH=str(CRYSTAL/'src'), CRYSTAL_CACHE_DIR=str(build/'crystal-cache'))
            link = ('-isysroot /Library/Developer/CommandLineTools/SDKs/MacOSX14.4.sdk -mmacosx-version-min=14.4 '
                    '-L /opt/homebrew/Cellar/gmp/6.3.0/lib -L /opt/homebrew/Cellar/pcre2/10.49/lib -L ' + str(CRYSTAL/'embedded/lib'))
            for label, source in [('cr-parent', ROOT/'programs/crystal/regexredux/crystal-regexredux-optimized/optimized.cr'),
                                  ('cr-bytes', ROOT/'experiments/crystal/regex-byte-offsets-v1/source/parallel.cr')]:
                binary = build/label
                one([CRYSTAL/'embedded/bin/crystal', 'build', '--release', '--no-debug', '--no-color',
                     '--error-trace', '--mcpu', 'native', '--threads', '1', '--link-flags', link,
                     '-o', binary, source], 'compile-'+label, environment=crystal_env)
                report['compilations'].append({'label': label, 'source_sha256': sha(source), 'binary_sha256': sha(binary)})
                commands[label] = [binary]
            for family, cases, reference, labels in [
                ('typescript', nucleotide_cases(), nucleotide_reference, ['ts-parent', 'ts-rolling']),
                ('crystal', regex_cases(), regex_reference, ['cr-parent', 'cr-bytes']),
                ('d', reverse_cases(), reverse_reference, ['d-parent', 'd-inplace'])]:
                for name, raw in cases.items():
                    inp = output/(family+'-'+name+'.stdin')
                    expected = output/(family+'-'+name+'.expected')
                    inp.write_bytes(raw)
                    expected.write_bytes(reference(raw))
                    for label in labels:
                        directory = label+'-'+name
                        one(commands[label], directory, stdin=inp)
                        actual = output/directory/'stdout.bin'
                        match = actual.read_bytes() == expected.read_bytes()
                        row = {'language': family, 'label': label, 'case': name, 'output_matches': match,
                               'expected_sha256': sha(expected), 'actual_sha256': sha(actual)}
                        report['cases'].append(row)
                        # Historical D parser differences are captured rather than silently repaired.
                        if label != 'd-parent':
                            assert match, 'Independent output mismatch: '+directory
            report['status'] = 'passed-bounded-output-checks'
        except Exception as error:
            report['status'] = 'failed'
            report['error'] = repr(error)
            raise
        finally:
            report['pins_unchanged'] = pins() == plan['pins']
            report['lock_identity_unchanged'] = os.fstat(lock.fileno()).st_ino == LOCK.stat().st_ino == plan['mutex_inode']
            write(output/'report.json', report)
            print(json.dumps({k: v for k, v in report.items() if k not in ('cases', 'compilations')}), flush=True)
            assert report['pins_unchanged'] and report['lock_identity_unchanged']


if __name__ == '__main__':
    main()
