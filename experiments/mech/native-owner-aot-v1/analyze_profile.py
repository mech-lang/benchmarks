"""Verify profiling code identity and summarize the retained macOS stack samples."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text_section(path):
    data = path.read_bytes()
    header = struct.unpack_from("<8I", data)
    assert header[0] == 0xFEEDFACF, "Expected a little-endian 64-bit Mach-O"
    position = 32
    for _ in range(header[4]):
        command, size = struct.unpack_from("<II", data, position)
        assert size >= 8 and position + size <= len(data)
        if command == 0x19:  # LC_SEGMENT_64
            sections = struct.unpack_from("<I", data, position + 64)[0]
            assert 72 + sections * 80 <= size
            for index in range(sections):
                section = position + 72 + index * 80
                name, segment, _, length, offset = struct.unpack_from(
                    "<16s16sQQI", data, section
                )
                if (segment.rstrip(b"\0"), name.rstrip(b"\0")) == (b"__TEXT", b"__text"):
                    assert offset + length <= len(data)
                    return data[offset:offset + length]
        position += size
    raise AssertionError("Missing machine-code section")


def stack_threads(content, patterns):
    """Retain each thread's denominator; union inclusive subtrees per category."""
    graph = content.split("Call graph:\n", 1)[1].split("Total number in stack", 1)[0]
    threads = []
    ancestors = []

    def finish_node():
        _, count, children, labels = ancestors.pop()
        assert 0 <= children <= count, "Stack children exceed their parent sample count"
        for label in labels:
            threads[-1]['exclusive_samples'][label] += count - children

    for line in graph.splitlines():
        match = re.match(r"^[\s+!:|]*(\d+) (\S+)", line)
        if not match:
            continue
        count, symbol = int(match[1]), match[2]
        depth = match.start(1)
        if symbol.startswith("Thread_"):
            while ancestors:
                finish_node()
            threads.append({
                'thread': symbol.rstrip(':'),
                'header': line.strip(),
                'main_thread': 'com.apple.main-thread' in line or bool(re.search(r'\bMain Thread\b', line)),
                'samples': count,
                'samples_unwound_to_start': 0,
                'inclusive_samples': {label: 0 for label in patterns},
                'exclusive_samples': {label: 0 for label in patterns},
            })
            continue
        assert threads, "Stack node precedes its thread root"
        while ancestors and ancestors[-1][0] >= depth:
            finish_node()
        if ancestors:
            ancestors[-1][2] += count
        active = set().union(*(node[3] for node in ancestors))
        matched = {label for label, choices in patterns.items()
                   if any(pattern in symbol for pattern in choices)}
        for label in matched - active:
            threads[-1]['inclusive_samples'][label] += count
        if symbol == 'start':
            threads[-1]['samples_unwound_to_start'] += count
        ancestors.append([depth, count, 0, matched])
    while ancestors:
        finish_node()
    # A pre-armed trace can repeat one thread ID when its label changes from
    # startup to a dispatch queue. Each root is a disjoint observed phase.
    merged = {}
    for phase in threads:
        key = phase['thread']
        if key not in merged:
            merged[key] = phase
            continue
        thread = merged[key]
        thread.setdefault('header_phases', [thread['header']]).append(phase['header'])
        thread['main_thread'] |= phase['main_thread']
        for label in ('samples', 'samples_unwound_to_start'):
            thread[label] += phase[label]
        for kind in ('inclusive_samples', 'exclusive_samples'):
            for label, count in phase[kind].items():
                thread[kind][label] += count
    threads = list(merged.values())
    assert threads and sum(thread['main_thread'] for thread in threads) == 1
    for thread in threads:
        total = thread['samples']
        assert total > 0 and all(0 <= count <= total for kind in ('inclusive_samples', 'exclusive_samples')
                                 for count in thread[kind].values())
        for kind in ('inclusive', 'exclusive'):
            thread[f'{kind}_percent'] = {label: 100 * count / total
                                        for label, count in thread[f'{kind}_samples'].items()}
        counts = thread['inclusive_samples']
        evidence = [label for label in ('generated_program_entry', 'parallel_worker_entry', 'parallel_dispatch')
                    if counts.get(label, 0) > 0]
        thread['worker_evidence_categories'] = evidence if not thread['main_thread'] else []
        thread['observed_native_worker'] = not thread['main_thread'] and bool(evidence)
    return threads


def thread_totals(threads, patterns):
    total = sum(thread['samples'] for thread in threads)
    result = {'thread_count': len(threads), 'thread_samples': total}
    for kind in ('inclusive', 'exclusive'):
        counts = {label: sum(thread[f'{kind}_samples'][label] for thread in threads)
                  for label in patterns}
        result[f'{kind}_samples'] = counts
        result[f'{kind}_percent'] = {label: 100 * count / total if total else None
                                     for label, count in counts.items()}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timing', default='cache-timing-v2')
    parser.add_argument('--profile-build', default='profile-cache-build-v2')
    parser.add_argument('--samples', default='full-profile-cache-v1')
    parser.add_argument('--binary', default='counting-cache')
    parser.add_argument('--sample-index', type=int, action='append', help='Explicit diagnostic capture selection; recorded in analysis; never filters timing observations')
    args = parser.parse_args()
    timing = json.loads((HERE / args.timing / 'results.json').read_text())
    profile = json.loads((HERE / args.profile_build / 'results.json').read_text())
    capture = json.loads((HERE / args.samples / 'results.json').read_text())
    timed_binary = HERE / '.build' / args.binary
    profile_binary = Path(profile["binary"])
    assert sha(timed_binary.read_bytes()) == timing["candidate_sha256"]
    assert sha(profile_binary.read_bytes()) == profile["binary_sha256"]
    assert capture['binary_sha256'] == profile['binary_sha256']
    assert capture['object_sha256'] == profile['object_sha256']
    timed_code = text_section(timed_binary)
    profile_code = text_section(profile_binary)
    assert timed_code == profile_code

    patterns = {
        "generated_program_entry": "mech_canonical_program_entry_v1",
        "packed_map_runtime": "program_packed_map",
        "ordinary_library_invocation": "CallCacheLane6invoke",
        "caller_cache_metadata_total": "CallCacheLane21caller_retained_nodes",
        "changed_cache_metadata_demand": "retained_metadata_demand",
        "range_snapshot": "range_snapshot",
        "canonical_string_selection": "canonical_string_selection",
        "retained_map_helper": "retained_map_helper",
        "closed_map_storage_binding": "10map_owners6closed",
        "private_map_read": "11native_read",
        "private_map_lookup": "13native_lookup",
        "private_map_insert": "13native_insert",
        "library_work_scope": "16with_call_limits",
        "library_scope_guard": "ControlWorkScopeGuard",
        "library_call_scope_guard": "10ScopeGuard",
        "library_call_account_guard": "12AccountGuard",
        "library_account_scope": "10with_scope",
        "map_publication": "owned_string_map11publication",
        "selected_key_projection": "State11project_key",
        "selected_range_cardinality": "selected_u64_range_cardinality",
        "selected_range_shape_reuse": "selected_u64_string_span_selector_reusing_shape",
        "selected_range_endpoint_count": "selected_u64_range_count",
        "selected_range_shape_validation": "validate_selected_u64_range_shape",
        "generated_block_admission": "program_runtime5admit",
        "runtime_boundary_validation": "7Context5visit",
        "iteration_transition_validation": "10visit_from",
        "native_work_debit": "NativeWorkMeter6charge",
        "library_work_debit": "NativeLibraryWorkBudget6charge",
    }
    # Keep the established category names while accepting either symbol style.
    patterns = {label: (pattern,) for label, pattern in patterns.items()}
    # Lock reuse moves the same checked debits into a distinct leaf meter.
    # Include it so a new symbol does not masquerade as eliminated debit work.
    patterns['library_work_debit'] += ('NativeWorkDebitBatch6charge', '::NativeWorkDebitBatch::charge')
    patterns.update({
        'parallel_worker_entry': ('10run_worker', '::run_worker'),
        'parallel_dispatch': ('12run_parallel', '::run_parallel'),
        'thread_wait': ('__psynch_cvwait', '__psynch_mutexwait', '__ulock_wait',
                        'semaphore_wait_trap', '__semwait_signal', 'mach_msg2_trap'),
        'thread_join': ('pthread_join', 'JoinInner', 'join_unchecked'),
    })
    summaries = []
    selected = args.sample_index if args.sample_index is not None else list(range(len(capture['samples'])))
    assert selected and len(selected) == len(set(selected)) and all(0 <= i < len(capture['samples']) for i in selected)
    for index in selected:
        item = capture['samples'][index]
        # Use only capture-owned paths, not unrelated files in the directory.
        # Rebase the recorded sample name so archived receipts remain readable
        # after moving the checkout from its original absolute path.
        recorded = Path(item['stacks'])
        assert recorded.name == 'stacks.txt' and re.fullmatch(r'sample-\d+', recorded.parent.name)
        path = HERE / args.samples / recorded.parent.name / recorded.name
        if 'stacks_sha256' in item:
            assert sha(path.read_bytes()) == item['stacks_sha256']
        threads = stack_threads(path.read_text(), patterns)
        main_thread = next(thread for thread in threads if thread['main_thread'])
        workers = [thread for thread in threads if thread['observed_native_worker']]
        summaries.append({
            "stacks": str(path.relative_to(HERE)),
            "stacks_sha256": sha(path.read_bytes()),
            # Preserve historical serial/SSA report fields as main-only values.
            "main_thread_samples": main_thread['samples'],
            "samples_unwound_to_start": main_thread['samples_unwound_to_start'],
            "inclusive_samples": main_thread['inclusive_samples'],
            "inclusive_percent": main_thread['inclusive_percent'],
            "main_thread": main_thread,
            "all_threads": thread_totals(threads, patterns),
            "observed_workers": thread_totals(workers, patterns),
            "threads": threads,
        })
    assert summaries, "No retained stack captures"
    result = {
        "status": "machine-code-identity-verified",
        "scope": "Current candidate only; observations include running and waiting threads, partial unwinds and profiling overhead. Summed thread samples are not wall time, CPU utilization, benchmark timings, or a matched baseline profile",
        "source_commit": timing["source_commit"],
        "timed_binary_sha256": timing["candidate_sha256"],
        "profiling_binary_sha256": profile["binary_sha256"],
        "machine_code_section": "__TEXT,__text",
        "machine_code_bytes": len(timed_code),
        "machine_code_sha256": sha(timed_code),
        "machine_code_identical": True,
        "symbol_patterns": patterns,
        "aggregation": "Inclusive counts union matching subtrees within each category and thread; exclusive counts use node count minus immediate children. Categories may overlap. Per-thread denominators are that thread's observations; all-thread and observed-worker denominators sum only their listed thread observations. Legacy top-level sample fields remain main-thread only",
        "worker_identification": "Non-main threads with observed generated-program, run_worker or run_parallel frames; threads that ended before sampling or whose stacks omit all identifying frames cannot be inferred",
        "completed_output_verified": capture.get('completed_output_verified'),
        "native_counters": capture.get('native_counters'),
        "samples": summaries,
        "selected_capture_indices": selected,
        "attempted_capture_count": len(capture["samples"]),
        "analysis_script_sha256": sha(Path(__file__).read_bytes()),
    }
    output = HERE / args.samples / 'analysis.json'
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
