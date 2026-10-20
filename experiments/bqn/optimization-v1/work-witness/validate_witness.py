#!/usr/bin/env python3
"""Validate an untimed CBQN hash-work trace; never executes CBQN."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys


COUNT_PREFIX = "MECH_COUNT_WITNESS "
MAP_PREFIX = "MECH_HASHMAP_WITNESS "
FRAME_PREFIX = "MECH_FRAME_WITNESS "
DEFAULT_WIDTHS = (1, 2, 3, 4, 6, 12, 18)


def expected_jobs(length, widths=DEFAULT_WIDTHS, pieces=8):
    jobs = {}
    for width in widths:
        for frame in range(width):
            total = max(0, (length - frame) // width)
            for piece in range(pieces):
                first = total * piece // pieces
                last = total * (piece + 1) // pieces
                jobs[(width, frame, piece)] = last - first
    return jobs


def expected_chunk_jobs(length, widths=DEFAULT_WIDTHS, chunk_size=100000):
    """Marker identities are (width, global_window_start, 0)."""
    return {(width, start, 0): max(0, min(chunk_size, length - start - width + 1))
            for start in range(0, length, chunk_size) for width in widths}


def read_trace(text):
    scopes, active, outside, errors = [], {}, [], []
    records = []
    for number, line in enumerate(text.splitlines(), 1):
        try:
            if line.startswith(FRAME_PREFIX):
                # Deliberately simple for a BQN •term.ErrRaw marker.
                event, pid, width, frame, piece, rows = line[len(FRAME_PREFIX):].split()
                pid, width, frame, piece, rows = map(int, (pid, width, frame, piece, rows))
                key = (width, frame, piece)
                if event == "begin":
                    if pid in active:
                        raise ValueError(f"nested frame for pid {pid}")
                    active[pid] = dict(pid=pid, key=key, rows=rows, records=[], line=number)
                elif event == "end":
                    if pid not in active:
                        raise ValueError(f"end without begin for pid {pid}")
                    scope = active.pop(pid)
                    if scope["key"] != key or scope["rows"] != rows:
                        raise ValueError(f"begin/end mismatch for pid {pid}")
                    scopes.append(scope)
                else:
                    raise ValueError(f"unknown frame event {event!r}")
                continue
            if line.startswith(COUNT_PREFIX):
                record = json.loads(line[len(COUNT_PREFIX):])
                record["kind"] = "count"
            elif line.startswith(MAP_PREFIX):
                record = json.loads(line[len(MAP_PREFIX):])
                record["kind"] = "hashmap"
            else:
                continue
            record["line"] = number
            records.append(record)
            if record["pid"] in active:
                active[record["pid"]]["records"].append(record)
            else:
                outside.append(record)
        except (ValueError, KeyError, TypeError) as error:
            errors.append(f"line {number}: {error}")
    errors.extend(f"unclosed frame {scope['key']} for pid {pid}" for pid, scope in active.items())
    return dict(scopes=scopes, outside=outside, records=records, errors=errors)


def check_generic(record, rows, errors, context):
    def require(condition, message):
        if not condition:
            errors.append(f"{context}: {message}")
    require(record.get("path") == "generic", f"native path is {record.get('path')!r}, expected generic")
    require(record.get("boxed") is True and record.get("rank") == 1,
            "expected a rank-one list of boxed actual keys")
    require(record.get("n") == rows, f"input has {record.get('n')} keys, expected {rows}")
    require(record.get("lookups") == rows, "not exactly one native lookup per key")
    require(record.get("updates") == rows, "not exactly one native count assignment/increment per key")
    require(record.get("inserts", -1) + record.get("increments", -1) == rows,
            "insertions plus value increments do not equal keys")
    require(record.get("unique") == record.get("inserts"), "unique-key count differs from insertions")
    require(record.get("initial_capacity") == 64, "generic table did not start at the pinned default of 64 slots")
    final, growths = record.get("final_capacity", 0), record.get("growths", -1)
    require(isinstance(final, int) and final >= 64 and final & (final - 1) == 0,
            "final capacity is not a power of two >=64")
    require(isinstance(growths, int) and growths >= 0 and growths < 63 and 64 << max(growths, 0) == final,
            "capacity and observed doubling count disagree")
    require(0 <= record.get("inserts", -1) <= rows, "invalid insertion count")
    require(0 <= record.get("increments", -1) <= rows, "invalid increment count")
    return record.get("updates", 0)


def check_explicit(records, rows, errors, context):
    maps = [record for record in records if record["kind"] == "hashmap"]
    gets = [record for record in maps if record.get("operation") == "get"]
    sets = [record for record in maps if record.get("operation") == "set"]
    if len(sets) != rows:
        errors.append(f"{context}: {len(sets)} HashMap.Set calls, expected {rows}")
    if len(gets) < rows:
        errors.append(f"{context}: fewer HashMap.Get calls than updates")
    if rows:
        if not maps or maps[0].get("before_population") != 0 or maps[0].get("before_capacity") != 96:
            errors.append(f"{context}: explicit HashMap did not start empty at its pinned 64+32-slot default")
        if len({record.get("map") for record in maps}) != 1:
            errors.append(f"{context}: expected one explicit map for the frame piece")
    for record in sets:
        before, after = record.get("before_population"), record.get("after_population")
        if not isinstance(before, int) or after not in (before, before + 1):
            errors.append(f"{context}: invalid HashMap.Set population change")
    return len(sets)


def validate(text, length, widths=DEFAULT_WIDTHS, pieces=8, mode="occurrence", allow_unscoped=False, chunk_size=None):
    trace = read_trace(text)
    errors = list(trace["errors"])
    expected = (expected_jobs(length, widths, pieces) if chunk_size is None
                else expected_chunk_jobs(length, widths, chunk_size))
    expected_updates = sum(expected.values())
    actual_updates = 0
    increments = insertions = growths = 0
    scoped = bool(trace["scopes"])
    if scoped:
        seen = Counter(scope["key"] for scope in trace["scopes"])
        if set(seen) != set(expected):
            missing, extra = sorted(set(expected) - set(seen)), sorted(set(seen) - set(expected))
            errors.append(f"frame identity coverage mismatch; missing={missing[:12]}, extra={extra[:12]}")
        for key, count in seen.items():
            if count != 1:
                errors.append(f"frame {key} has {count} scopes, expected one")
        for scope in trace["scopes"]:
            key, rows = scope["key"], expected.get(scope["key"])
            context = f"frame {key}, pid {scope['pid']}"
            if rows is None:
                continue
            if rows != scope["rows"]:
                errors.append(f"{context}: marker rows={scope['rows']}, expected {rows}")
            native = [record for record in scope["records"] if record["kind"] == "count"]
            if mode == "hashmap" or rows == 1:
                actual_updates += check_explicit(scope["records"], rows, errors, context)
                for record in native:
                    if record.get("path") != "trivial" or record.get("n", 2) > 1:
                        errors.append(f"{context}: unexpected native occurrence call during explicit-map fallback")
            elif rows == 0:
                actual_updates += check_explicit(scope["records"], 0, errors, context)
                for record in native:
                    if record.get("path") != "trivial" or record.get("n") != 0:
                        errors.append(f"{context}: nonempty count invocation in empty piece")
            else:
                if len(native) != 1:
                    errors.append(f"{context}: {len(native)} occurrence calls, expected exactly one")
                for record in native:
                    actual_updates += check_generic(record, rows, errors, context)
                    increments += record.get("increments", 0)
                    insertions += record.get("inserts", 0)
                    growths += record.get("growths", 0)
                if any(record["kind"] == "hashmap" and record.get("operation") == "set" for record in scope["records"]):
                    errors.append(f"{context}: unexpected additional explicit-map updates")
    elif allow_unscoped and mode == "occurrence":
        # Useful only for exploration: invocation sizes cannot establish frame identity.
        wanted = Counter(expected.values())
        wanted.pop(0, None)
        if wanted.get(1):
            errors.append("unscoped mode cannot prove singleton HashMap fallback")
        for record in trace["records"]:
            rows = record.get("n")
            if record["kind"] == "count" and record.get("path") == "generic" and wanted.get(rows, 0):
                wanted[rows] -= 1
                actual_updates += check_generic(record, rows, errors, f"unscoped call at line {record['line']}")
                increments += record.get("increments", 0)
                insertions += record.get("inserts", 0)
                growths += record.get("growths", 0)
        if any(wanted.values()):
            errors.append(f"missing generic invocation sizes: {dict(+wanted)}")
    else:
        errors.append("no Frame scopes found; add begin/end markers, or use --allow-unscoped for weaker exploratory evidence")
    if actual_updates != expected_updates:
        errors.append(f"observed {actual_updates} required updates, expected {expected_updates}")
    return dict(
        schema="bqn-hash-work-witness.v1",
        status="fail" if errors else ("pass" if scoped else "heuristic-only"),
        evidence_level="scoped-frame-identity" if scoped else "unscoped-invocation-size-matching",
        mode=mode, dna_length=length, widths=list(widths), pieces=pieces if chunk_size is None else None,
        job_plan="frame-pieces" if chunk_size is None else "window-start-chunks", chunk_size=chunk_size,
        expected_frames=len(expected), observed_frames=len(trace["scopes"]),
        expected_updates=expected_updates, observed_updates=actual_updates,
        generic_insertions=insertions, generic_value_increments=increments,
        generic_growths=growths, all_count_paths=dict(Counter(r.get("path") for r in trace["records"] if r["kind"] == "count")),
        outside_scope_records=len(trace["outside"]),
        outside_scope_count_paths=dict(Counter(r.get("path") for r in trace["outside"] if r["kind"] == "count")),
        worker_pids=sorted({scope["pid"] for scope in trace["scopes"]}), errors=errors,
        limitation="Work witness only; verify exact stdout separately and exclude the instrumented executable from timing."
    )


def self_test():
    # Synthetic witnesses exercise rejection of a dense shortcut and a missing
    # update; they do not run CBQN or stand in for native evidence.
    def sample(path="generic", updates=3):
        event = dict(pid=9, call=1, path=path, n=3, rank=1, boxed=True, el_type=6,
                     lookups=3, updates=updates, inserts=2, increments=1,
                     initial_capacity=64, final_capacity=64, growths=0, unique=2)
        return "\n".join(("MECH_FRAME_WITNESS begin 9 1 0 0 3", COUNT_PREFIX + json.dumps(event),
                          "MECH_FRAME_WITNESS end 9 1 0 0 3"))
    assert validate(sample(), 3, (1,), 1)["status"] == "pass"
    assert validate(sample("lookup8"), 3, (1,), 1)["status"] == "fail"
    assert validate(sample(updates=2), 3, (1,), 1)["status"] == "fail"
    assert validate(sample().replace("end 9", "end 10"), 3, (1,), 1)["status"] == "fail"
    assert sum(expected_jobs(125_000_000).values()) == 874_999_961
    assert sum(expected_jobs(5000).values()) == 34_961
    assert validate("", 3, (1,), 1)["status"] == "fail"
    # A singleton primitive returns without hashing: only explicit Get+Set proves work.
    one = ["MECH_FRAME_WITNESS begin 9 1 0 0 1"]
    for operation in ("get", "set"):
        one.append(MAP_PREFIX + json.dumps(dict(pid=9, operation=operation, map="abc",
                    before_capacity=96, after_capacity=96, before_population=0,
                    after_population=int(operation == "set"))))
    one.append("MECH_FRAME_WITNESS end 9 1 0 0 1")
    assert validate("\n".join(one), 1, (1,), 1)["status"] == "pass"
    assert validate("\n".join((one[0], one[-1])), 1, (1,), 1)["status"] == "fail"
    # Chunk identities use global window starts, not reading-frame/piece IDs.
    assert expected_chunk_jobs(9, (1, 2, 3), 4) == {
        (1, 0, 0): 4, (2, 0, 0): 4, (3, 0, 0): 4,
        (1, 4, 0): 4, (2, 4, 0): 4, (3, 4, 0): 3,
        (1, 8, 0): 1, (2, 8, 0): 0, (3, 8, 0): 0}
    chunk_scopes = []
    for call, ((width, start, piece), rows) in enumerate(expected_chunk_jobs(20, (1, 2), 7).items(), 1):
        event = dict(pid=9, call=call, path="generic", n=rows, rank=1, boxed=True, el_type=6,
                     lookups=rows, updates=rows, inserts=2, increments=rows - 2,
                     initial_capacity=64, final_capacity=64, growths=0, unique=2)
        chunk_scopes.append("\n".join((f"MECH_FRAME_WITNESS begin 9 {width} {start} 0 {rows}",
                            COUNT_PREFIX + json.dumps(event),
                            f"MECH_FRAME_WITNESS end 9 {width} {start} 0 {rows}")))
    chunk_text = "\n".join(chunk_scopes)
    assert validate(chunk_text, 20, (1, 2), chunk_size=7)["status"] == "pass"
    assert validate(chunk_text, 20, (1, 2), chunk_size=7)["expected_updates"] == 39
    assert validate("\n".join(chunk_scopes[:-1]), 20, (1, 2), chunk_size=7)["status"] == "fail"
    assert validate(chunk_text, 20, (1, 2), 1)["status"] == "fail"
    print("Synthetic validator checks passed; no CBQN execution performed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stderr", type=Path)
    parser.add_argument("--dna-length", type=int)
    parser.add_argument("--widths", default=",".join(map(str, DEFAULT_WIDTHS)))
    parser.add_argument("--pieces", type=int, default=8)
    parser.add_argument("--chunk-size", type=int, help="Use (width, chunk_start, 0) marker identities; each chunk covers all widths. Overrides --pieces.")
    parser.add_argument("--mode", choices=("occurrence", "hashmap"), default="occurrence")
    parser.add_argument("--allow-unscoped", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.stderr is None or args.dna_length is None:
        parser.error("--stderr and --dna-length are required unless --self-test is used")
    widths = tuple(map(int, args.widths.split(",")))
    if args.dna_length < 0 or args.pieces <= 0 or (args.chunk_size is not None and args.chunk_size <= 0) or not widths or min(widths) <= 0 or len(set(widths)) != len(widths):
        parser.error("length must be nonnegative; pieces, chunk size and unique widths must be positive")
    report = validate(args.stderr.read_text(), args.dna_length, widths, args.pieces, args.mode, args.allow_unscoped, args.chunk_size)
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded)
    sys.stdout.write(encoded)
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
