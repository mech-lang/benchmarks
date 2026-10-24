"""Recompute primary peak RSS and interpret separate memory diagnostic captures."""
import bisect
from collections import Counter
import json
import re
import statistics
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(STUDY))
from binary import macho, function_ranges, sha


def read(path):
    return json.loads(path.read_text())


def heap_summary(path):
    text = path.read_text()
    match = re.search(r'All zones: (\d+) nodes \((\d+) bytes\)', text)
    assert match
    return dict(live_allocations=int(match[1]), live_allocated_bytes=int(match[2]))


def live_caller_categories(text):
    stack, nodes = [], []
    for line in text.splitlines():
        match = re.match(r'^([ +!:|]*)(\d+) \(([^)]+)\) (.*)$', line)
        if not match:
            continue
        node = dict(depth=len(match[1]), count=int(match[2]), symbol=match[4], children=[], parent=None)
        while stack and stack[-1]['depth'] >= node['depth']:
            stack.pop()
        if stack:
            node['parent'] = stack[-1]
            stack[-1]['children'].append(node)
        stack.append(node)
        nodes.append(node)
    counts = Counter()
    for node in nodes:
        exclusive = node['count'] - sum(c['count'] for c in node['children'])
        assert exclusive >= 0
        if not exclusive:
            continue
        path, ancestor = [], node
        while ancestor:
            path.append(ancestor['symbol'])
            ancestor = ancestor['parent']
        path.reverse()
        selected = next((s.split(' + ')[0] for s in path if any(t in s for t in
            ('program_image_read', 'program_descriptor::image', 'NativeTypedStorage',
             'program_packed_map', 'finish_selected_join', 'RuntimeBuilder', 'PreparedInMemoryCommit'))), None)
        if selected is None:
            selected = next((s.split(' + ')[0] for s in path if s.startswith(('mech_', '<mech_'))), 'other')
        counts[selected] += exclusive
    assert sum(counts.values()) == nodes[0]['count']
    return dict(stack_attributed_live_blocks=sum(counts.values()),
                categories=[dict(first_matching_caller=k, live_blocks=v) for k, v in counts.most_common()],
                scope='Disjoint live-block partition reconstructed from the inverted call tree: parent counts minus child counts, assigned to the first listed loader/storage caller, otherwise the first Mech caller. Counts are not dynamic allocation frequency or CPU cost. Rounded ancestor byte totals are not summed.')


def main():
    out = HERE / 'preparation-interactions-memory-analysis-v1'
    out.mkdir(exist_ok=True)
    inputs = []
    def load(path):
        inputs.append(dict(path=str(path.relative_to(HERE)), sha256=sha(path)))
        return read(path)
    sessions = []
    for number in (1, 2):
        report = load(HERE / f'full-preparation-interactions-v{number}/results.json')
        subjects = {}
        for subject in report['pins']:
            rows = [r for r in report['samples'] if r['subject'] == subject]
            values = []
            for row in rows:
                receipt = read(HERE / row['process'])
                assert sha(HERE / row['process']) == row['process_sha256']
                assert row['maximum_rss_bytes'] == receipt['maximum_rss_bytes']
                values.append(row['maximum_rss_bytes'])
            subjects[subject] = dict(observations=len(values), maximum_rss_bytes=values,
                median_peak_rss_bytes=statistics.median(values), min_peak_rss_bytes=min(values),
                max_peak_rss_bytes=max(values), standard_deviation_bytes=statistics.stdev(values),
                seconds=report['median_seconds'][subject], x_rust=report['x_rust'][subject])
        rust_rss = subjects['rust']['median_peak_rss_bytes']
        for subject, values in subjects.items():
            values['peak_rss_x_rust'] = values['median_peak_rss_bytes'] / rust_rss
        sessions.append(dict(session=number, subjects=subjects))
    timeline_root = HERE / 'preparation-interactions-memory-timeline-v1'
    timeline = load(timeline_root / 'results.json')
    assert timeline['status'] == 'all-owned-memory-observations-and-outputs-verified'
    summaries = {}
    for subject in sessions[0]['subjects']:
        rows = [r for r in timeline['observations'] if r['subject'] == subject]
        assert len(rows) == 3
        summaries[subject] = dict(median_diagnostic_wait4_peak_rss_bytes=statistics.median(r['process']['maximum_rss_bytes'] for r in rows),
            median_sampled_peak_rss_bytes=statistics.median(r['sampled_peak_rss_bytes'] for r in rows),
            median_observed_lifetime_peak_physical_footprint_bytes=statistics.median(r['observed_lifetime_peak_physical_footprint_bytes'] for r in rows))
    snapshot_root = HERE / 'preparation-interactions-memory-snapshot-v1'
    snapshot = load(snapshot_root / 'results.json')
    assert snapshot['status'] == 'all-owned-memory-observations-and-outputs-verified'
    allocations = {}
    for row in snapshot['observations']:
        subject = row['subject']
        folder = snapshot_root / f"{row['order']}-{subject}-heap"
        allocations[subject] = heap_summary(folder / 'stdout.bin')
        assert all(c['exit_status'] == 0 for c in row['captures'])
        for tool in ('heap', 'vmmap'):
            path = snapshot_root / f"{row['order']}-{subject}-{tool}/stdout.bin"
            inputs.append(dict(path=str(path.relative_to(HERE)), sha256=sha(path)))
    callers_root = HERE / 'preparation-interactions-allocation-callers-v1'
    callers = load(callers_root / 'results.json')
    assert callers['status'] == 'all-owned-allocation-diagnostics-and-outputs-verified'
    later = {}
    for row in callers['observations']:
        subject = row['subject']
        later[subject] = heap_summary(callers_root / (subject + '-heap') / 'stdout.bin')
        assert all(c['exit_status'] == 0 for c in row['captures'])
        for tool in ('heap', 'vmmap', 'malloc_history'):
            path = callers_root / (subject + '-' + tool) / 'stdout.bin'
            inputs.append(dict(path=str(path.relative_to(HERE)), sha256=sha(path)))
    sizes = load(HERE / 'preparation-interactions-binary-size-v1/results.json')
    profile = HERE / '.build/counting-preparation-combined-profile'
    ranges = function_ranges(profile, include_all=True)
    assert ranges['machine_code_sha256'] == sizes['subjects']['combined']['machine_code_sha256']
    offsets = sorted(ranges['ranges'], key=lambda r: r['address'])
    starts = [r['address'] for r in offsets]
    profile_parsed = macho(profile)[0]
    timed_parsed = sizes['subjects']['combined']
    def text_layout(parsed):
        section = next(s for s in parsed['sections'] if (s['segment'], s['section']) == ('__TEXT', '__text'))
        base = next(s['vm_address'] for s in parsed['segments'] if s['name'] == '__TEXT')
        return base, section['address'] - base
    base, relative_text = text_layout(profile_parsed)
    assert text_layout(timed_parsed)[1] == relative_text
    raw = (callers_root / 'combined-malloc_history/stdout.bin').read_text()
    resolved, unresolved = 0, 0
    def replace(match):
        nonlocal resolved, unresolved
        address = base + int(match[1], 16)
        index = bisect.bisect_right(starts, address) - 1
        if index >= 0 and address < offsets[index]['address'] + offsets[index]['bytes']:
            row = offsets[index]
            resolved += 1
            return f"{row['symbol']} + {address - row['address']} [timed-image offset 0x{int(match[1], 16):x}]"
        unresolved += 1
        return match[0]
    symbolicated = re.sub(r'\?\?\?  \(in counting-preparation-combined\)  load address 0x[0-9a-f]+ \+ 0x([0-9a-f]+)  \[0x[0-9a-f]+\]', replace, raw)
    (out / 'combined-live-callers-symbolicated.txt').write_text(symbolicated)
    report = dict(status='primary-memory-and-separate-diagnostic-accounting-verified',
        driver_sha256=sha(Path(__file__)), binary_parser_sha256=sha(STUDY / 'binary.py'),
        primary_peak_rss_sessions=sessions, separate_timeline_summaries=summaries,
        first_observed_seven_workers_heap=allocations,
        stack_logged_later_live_heap=later,
        combined_allocation_symbolication=dict(resolved_frames=resolved, unresolved_frames=unresolved,
            output_sha256=sha(out / 'combined-live-callers-symbolicated.txt'),
            exact_machine_code_sha256=ranges['machine_code_sha256']),
        combined_live_caller_categories=live_caller_categories(symbolicated), sources=inputs,
        scope='Primary memory medians come from the original twenty complete processes per subject in each separately reported session. wait4 ru_maxrss is in bytes on macOS. Diagnostic timelines, live heaps and stack-logged allocations are different observations and cannot be substituted for those peaks. Allocation count is live count at a sampled phase, not total churn. The OS warns that some earlier allocations have no stack; full caller coverage is not claimed. All sizes labeled MB are decimal; raw byte counts are retained.')
    (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(primary=[{s: round(v['median_peak_rss_bytes'] / 1e6, 3) for s, v in r['subjects'].items()} for r in sessions],
                          worker_heap=allocations, symbolication=report['combined_allocation_symbolication']), indent=2))


if __name__ == '__main__':
    main()
