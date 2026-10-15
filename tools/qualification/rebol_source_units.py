"""Finite Rebol source-owner proposal, with no native reader or parser claim.

The source ledger is deliberately unprepared. `propose` can produce a future
review artifact; `count_source` rejects sources until their exact digest has
been independently frozen in that ledger. Neither path grants admission.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / 'experiments/rebol/source-counts-v1/owner_ledger.py'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_ledger():
    spec = importlib.util.spec_from_file_location('rebol_exact_owner_ledger', LEDGER)
    require(spec is not None and spec.loader is not None, 'Owner ledger unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row_numbers(spelling):
    """Expand written row lists only; no source-derived row inference."""
    seen = set()
    result = []
    for part in spelling.split():
        require(re.fullmatch(r'[1-9][0-9]*(?:-[1-9][0-9]*)?', part), 'Bad explicit row list')
        ends = [int(value) for value in part.split('-')]
        first, last = (ends[0], ends[0]) if len(ends) == 1 else ends
        require(first <= last, 'Reversed row range')
        for number in range(first, last + 1):
            require(number not in seen, 'Duplicate explicit row')
            seen.add(number)
            result.append(number)
    return result


def project(source, specification, kinds):
    """Apply explicit owner spans; changed or unowned significant text fails.

    This does not authenticate source identity. Its result is always a proposal
    until count_source additionally matches the separately reviewed digest.
    ASCII-only reviewed files make byte and character offsets identical.
    """
    require(type(source) is bytes, 'Source must be exact bytes')
    text = source.decode('ascii')
    require(text.endswith('\n') and '\r' not in text, 'Reviewed LF/ASCII source required')
    lines = text.splitlines(keepends=True)
    require(len(lines) == specification['expected_line_count'], 'Source row count differs')
    starts = []
    cursor = 0
    for line in lines:
        starts.append(cursor)
        cursor += len(line)
    owners = []
    claimed_rows = set()

    def row(number):
        require(type(number) is int and 1 <= number <= len(lines), 'Owner row outside source')
        raw = lines[number - 1].rstrip('\n')
        left = starts[number - 1] + len(raw) - len(raw.lstrip())
        right = starts[number - 1] + len(raw.rstrip())
        require(left < right, 'Explicit owner targets blank row')
        return left, right

    def claim(first, last=None):
        last = first if last is None else last
        require(type(first) is int and type(last) is int and 1 <= first <= last <= len(lines),
                'Invalid explicit owner extent')
        numbers = set(range(first, last + 1))
        require(not numbers & claimed_rows, 'Duplicate row decisions')
        for number in numbers:
            row(number)
        claimed_rows.update(numbers)

    def add(kind, first, last, left, right):
        require(kind in kinds and left < right, 'Unknown or empty source owner')
        label, units = kinds[kind]
        require(type(units) is int and units in (0, 1), 'Owner must be zero or one unit')
        owners.append(dict(kind=label, tag=kind, line=first, last_line=last,
                           start=left, end=right, canonical_units=units, text=text[left:right]))

    for kind, numbers in specification['rows'].items():
        require(kind in kinds and kind not in ('H', 'O'), 'Header/open needs explicit extent')
        for number in row_numbers(numbers):
            claim(number)
            left, right = row(number)
            spelling = text[left:right]
            if kind == 'C':
                require(spelling in (']', '}'), 'Standalone executable close differs')
            elif kind == 'P':
                require(spelling.startswith('#'), 'Semantic directive differs')
            add(kind, number, number, left, right)

    for extent in specification.get('headers', ()):
        first, last = (extent, extent) if type(extent) is int else extent
        claim(first, last)
        left, _ = row(first)
        _, right = row(last)
        require(text[right - 1] in ('[', '{'), 'Written executable opener differs')
        header_end = right - 1
        while header_end > left and text[header_end - 1].isspace():
            header_end -= 1
        add('H', first, last, left, header_end)
        add('O', last, last, right - 1, right)

    for extent in specification.get('raw_headers', ()):
        first, last = (extent, extent) if type(extent) is int else extent
        claim(first, last)
        left, _ = row(first)
        _, right = row(last)
        add('H', first, last, left, right)

    for number, fragments in specification.get('packed', {}).items():
        claim(number)
        left, right = row(number)
        at = left
        require(fragments, 'Packed row has no owners')
        for kind, literal in fragments:
            require(type(literal) is str and literal and literal == literal.strip(),
                    'Packed fragment must be a nonempty exact literal')
            while at < right and text[at].isspace():
                at += 1
            require(text.startswith(literal, at) and at + len(literal) <= right,
                    'Packed source fragment differs on row ' + str(number))
            end = at + len(literal)
            if kind == 'O':
                require(literal in ('[', '{'), 'Invalid executable opener')
            if kind == 'C':
                require(literal in (']', '}', '};'), 'Invalid written close')
            add(kind, number, number, at, end)
            at = end
        require(not text[at:right].strip(), 'Unowned tail on packed source row')

    owners.sort(key=lambda owner: (owner['start'], owner['end']))
    occupied = set()
    for owner in owners:
        span = set(range(owner['start'], owner['end']))
        require(not occupied & span, 'Overlapping owner spans')
        occupied.update(span)
    missing = [offset for offset, char in enumerate(text) if not char.isspace() and offset not in occupied]
    require(not missing, 'Unowned significant source characters')
    physical_rows = set()
    for owner in owners:
        if owner['tag'] != 'M':
            physical_rows.update(range(owner['line'], owner['last_line'] + 1))
    per_row = [dict(line=number,
                    canonical_units=sum(owner['canonical_units'] for owner in owners if owner['line'] == number))
               for number in sorted(claimed_rows)]
    return dict(schema='rebol-exact-source-owner-proposal-v1',
                source_path=specification['path'], source_sha256=hashlib.sha256(source).hexdigest(),
                canonical_loc=sum(owner['canonical_units'] for owner in owners),
                physical_loc=len(physical_rows), formatted_loc=None,
                source_owners=owners, row_totals=per_row, unowned_significant_characters=[],
                source_identity_reviewed=False, canonical_LOC_admitted=False,
                generic_language_certificate=False, native_execution=False,
                compiler_input_qualified=False, runtime_qualified=False,
                required_work_qualified=False, chart_admission=False)


def count_source(source, identity, ledger=None):
    ledger = load_ledger() if ledger is None else ledger
    require(identity in ledger.SOURCES, 'Unregistered source identity')
    specification = ledger.SOURCES[identity]
    expected = specification['reviewed_source_sha256']
    require(type(expected) is str and re.fullmatch(r'[0-9a-f]{64}', expected),
            'Source-owner digest freeze and independent review are pending')
    require(type(source) is bytes and hashlib.sha256(source).hexdigest() == expected,
            'Source bytes differ from exact owner review')
    result = project(source, specification, ledger.KINDS)
    result.update(identity=identity, rule_version=ledger.RULE, source_identity_reviewed=True)
    return result


def regular_source(root, relative):
    path = root / relative
    require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,
            'Source path escapes repository')
    require(path.resolve(strict=True) == path, 'Source must have physical nonsymlink path')
    require(stat.S_ISREG(path.lstat().st_mode), 'Source must be a regular file')
    return path.read_bytes()


def propose(root, ledger=None):
    ledger = load_ledger() if ledger is None else ledger
    root = Path(root).resolve(strict=True)
    require(len(ledger.SOURCES) == 15 and len(ledger.BUNDLES) == 10, 'Finite source scope differs')
    require(len({spec['path'] for spec in ledger.SOURCES.values()}) == 15, 'Duplicated counted source')
    projections = {}
    for identity, specification in ledger.SOURCES.items():
        result = project(regular_source(root, specification['path']), specification, ledger.KINDS)
        result.update(identity=identity, rule_version=ledger.RULE)
        projections[identity] = result
    bundles = {}
    for workload, members in ledger.BUNDLES.items():
        require(len(members) == len(set(members)), 'A shared source is counted twice in one bundle')
        require(tuple(members[:4]) == (workload, 'io', 'loader', 'extension'), 'Required counted bundle differs')
        expected_extra = ('big',) if workload == 'pidigits' else ('regex',) if workload == 'regexredux' else ()
        require(tuple(members[4:]) == expected_extra, 'Conditional facade bundle differs')
        bundles[workload] = dict(
            files=[dict(identity=name, path=projections[name]['source_path'],
                        sha256=projections[name]['source_sha256'],
                        canonical_loc=projections[name]['canonical_loc'],
                        physical_loc=projections[name]['physical_loc']) for name in members],
            canonical_loc=sum(projections[name]['canonical_loc'] for name in members),
            physical_loc=sum(projections[name]['physical_loc'] for name in members),
            source_forms=1, native_samples=0, canonical_LOC_admitted=False)
    return dict(schema='rebol-fifteen-source-count-proposal-v1', status='unreviewed-projection',
                rule_version=ledger.RULE, source_identity_reviewed=False,
                corrected_c_substitution=dict(original=ledger.ORIGINAL_C,
                    counted=ledger.CORRECTED_C, original_modified=False, count_both_revisions=False),
                corrected_fannkuch_substitution=dict(original=ledger.ORIGINAL_FANN,
                    counted=ledger.CORRECTED_FANN, original_modified=False, count_both_revisions=False),
                sources=projections, bundles=bundles, decisions=ledger.DECISIONS,
                source_files=15, workloads=10, four_file_bundles=8, five_file_bundles=2,
                canonical_LOC_admitted=False, native_execution=False, compiler_input_qualified=False,
                required_work_qualified=False, full_timing_qualified=False, chart_admission=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('propose',))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = propose(args.root)
    raw = (json.dumps(result, indent=2, ensure_ascii=True) + '\n').encode('ascii')
    # A proposal never overwrites an existing observation or review receipt.
    with args.output.open('xb') as stream:
        stream.write(raw)


if __name__ == '__main__':
    main()
