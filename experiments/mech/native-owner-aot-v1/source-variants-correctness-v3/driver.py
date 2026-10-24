"""Execute all three histogram sources and check every entry against Python windows.

This is correctness validation, not a timing cohort. No histogram builtin is used.
The generated fixture contains the actual source definitions with renamed symbols.
"""
import fcntl
import json
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

SOURCES = {
    'original': ('knucleotide-source-map.mec', 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'),
    'match': ('knucleotide-source-match-insert.mec', '0ad41e928ac322366eb6d82506072765226ea631a98babd84e85f77357392540'),
    'end': ('knucleotide-source-loop-end.mec', '6e13b552abae576725ac08de94ae3abfbf5737454fa52e0f13461f8dbcd13538'),
}
compiler = json.loads((HERE / 'compiler-v33/results.json').read_text())
assert compiler['status'] == 'compiler-built'
assert subprocess.check_output(['git', '-C', str(WORKSPACE), 'rev-parse', 'HEAD'], text=True).strip() == compiler['source_commit']
assert not subprocess.check_output(['git', '-C', str(WORKSPACE), 'status', '--porcelain'])
cli = HERE / '.build/mech-canonical'
assert process.sha(cli) == compiler['compiler_sha256']
out = HERE / sys.argv[1]
out.mkdir(exist_ok=False)
rng = random.Random(7329)
texts = ['', 'A', 'AAAAAA', 'ACGTACGT', 'GGTAGGT',
         ''.join(rng.choice('ACGT') for _ in range(83)),
         ''.join(rng.choice('ACGTN') for _ in range(521))]
widths = [0, 1, 2, 3, 4, 6, 12, 18, 522]
source = '+> map\n+> number\n+> sequence\n+> text\n+> @in := cli/stdin\n+> @out := cli/stdout\n'
for label, (name, sha) in SOURCES.items():
    path = HERE / name
    assert process.sha(path) == sha
    content = path.read_text()
    body = content[content.index('increment('):content.index('\nfrequencies(')]
    body = body.replace('increment(', f'increment-{label}(').replace('#Count', f'#Count{label.title()}').replace('histogram(', f'histogram-{label}(')
    source += '\n' + body
source += '''
dump(h<{string:u64}>) => (out<string>) :=
  keys := h_keys
  counts := map/values(h)
  order := sequence/sort-indices(counts, "desc", keys, "asc")
  out := text/join([keys[i] + "=" + number/format(counts[i], 0u64) | i <- order], ";").
'''
source += 'texts := text/lines(@in/text)\n'
source += 'widths := [' + ' '.join(f'{width}u64' for width in widths) + ']\n'
rendered = []
for label in SOURCES:
    source += f'{label}-output := text/join([text/join([dump(histogram-{label}(s, width)) | width <- widths], "\\n#\\n") | s <- texts], "\\n@\\n")\n'
    rendered.append(f'{label}-output')
source += '@out/text <- ' + ' + "\\n===\\n" + '.join(rendered) + '\n'
fixture = out / 'all-entries.mec'
fixture.write_text(source)
input_path = out / 'input.txt'
input_path.write_text('\n'.join(texts) + '\n')
(out / 'driver.py').write_bytes(Path(__file__).read_bytes())
expected_groups = []
for text in texts:
    outputs = []
    for width in widths:
        counts = Counter(text[i:i + width] for i in range(len(text) - width + 1)) if 0 < width <= len(text) else Counter()
        outputs.append(';'.join(f'{key}={counts[key]}' for key in sorted(counts, key=lambda k: (-counts[k], k))))
    expected_groups.append('\n#\n'.join(outputs))
expected_one = '\n@\n'.join(expected_groups)
expected = '\n===\n'.join([expected_one] * len(SOURCES)).encode()
(out / 'expected.txt').write_bytes(expected)
binary = HERE / '.build' / out.name
assert not binary.exists()
report = dict(status='building', source_commit=compiler['source_commit'],
              compiler_sha256=process.sha(cli), fixture_sha256=process.sha(fixture), input_sha256=process.sha(input_path), driver_sha256=process.sha(Path(__file__)),
              source_pins=SOURCES, texts=texts, widths=widths,
              histogram_cases_per_variant=len(texts) * len(widths),
              every_entry_checked=False, benchmark_samples=0)
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    command = [str(cli), '--no-config', 'build', str(fixture), '--backend', 'cranelift',
               '--profile', 'release', '--keep-project', '--offline', '--workspace-root',
               str(WORKSPACE), '--name', 'owner-' + out.name, '-o', str(binary)]
    built = process.execute(command, out / 'build', compiler['environment'], lock, deadline=1800)
    assert built['exit_status'] == 0, (out / 'build/stderr.bin').read_text()[-5000:]
    report['candidate_sha256'] = process.sha(binary)
    result = process.execute([str(binary), str(HERE / 'full-timing-v1/launch.json'), str(out / 'native.report.json'), '--'],
                             out / 'run', compiler['environment'], lock, stdin=input_path, deadline=120)
    assert result['exit_status'] == 0, (out / 'run/stderr.bin').read_text()[-5000:]
    actual = (out / 'run/stdout.bin').read_bytes()
    assert actual == expected, 'Full map contents differ from the independent windows oracle'
    native = json.loads((out / 'native.report.json').read_text())
    assert native['native_aot'] and not native['jit'] and not native['resident_body_evaluation']
    assert native['shutdown'] == 'completed'
    report.update(status='every-entry-verified', output_sha256=process.sha(out / 'run/stdout.bin'),
                  independent_oracle='Python Counter over every overlapping window; width zero and oversize are empty',
                  cases_checked=len(texts) * len(widths) * len(SOURCES), every_entry_checked=True)
process.save(out / 'results.json', report)
print(json.dumps(report))
