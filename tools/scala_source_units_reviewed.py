"""Additive Scala Match/callback owners over the frozen canonical projector.

Only retained native trees and source tokens are read. The explicit Match and
single-case tuple callback accounting has been reviewed against the common
rule. Application admission remains an independent evidence-review decision.
"""
import argparse
import hashlib
import json
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT/'tools/scala_source_units.py'
BASE_SHA = '66f13f502bf494a84b7c11c3805114eacd5349db5d6562441bd1e15f8b4e0bd1'
raw = BASE_PATH.read_bytes()
if hashlib.sha256(raw).hexdigest() != BASE_SHA:
    raise AssertionError('Frozen Scala canonical projector changed')
base = types.ModuleType('scala_frozen_canonical_v1')
base.__file__ = str(BASE_PATH)
exec(compile(raw, str(BASE_PATH), 'exec'), base.__dict__)


class ReviewedProjection(base.Projection):
    def special_roots(self, node):
        if self.product(node) == 'Match':
            return [node]
        return super().special_roots(node)

    def case_shape(self, node):
        start, end = self.span(node)
        if self.product(node) != 'CaseDef' or start is None:
            self.problem('unproved-case-node', node)
            return None
        fields = self.fields(node)
        body = self.child(node, 'body')
        pat = self.child(node, 'pat')
        if not self.empty(self.child(node, 'guard')):
            self.problem('guarded-case-owner-review', node)
            return None
        if self.product(body) != 'Block':
            self.problem('case-body-native-shape-review', node)
            return None
        body_start, body_end = self.span(body)
        tokens = self.within(start, end)
        arrows = self.within(body_start, body_end, '=>')
        # The actual parser's case body starts at its arrow. A nested callback
        # arrow would not prove this boundary and cannot replace a missing arrow.
        arrows = [p for p in arrows if p['start'] == body_start]
        if (not tokens or tokens[0]['source_text'] != 'case' or len(arrows) != 1
                or not (start < self.span(pat)[0] < self.span(pat)[1] <= body_start)
                or body_end != end):
            self.problem('case-arrow-boundary-review', node)
            return None
        children = self.children(body, 'stats')
        expr = self.child(body, 'expr')
        if not self.empty(expr):
            children.append(expr)
        if not children or any(self.span(c)[0] < arrows[0]['end'] for c in children):
            self.problem('case-body-statement-boundary-review', node)
            return None
        return dict(node=node, pattern=pat, body=body, children=children,
                    start=start, end=end, arrow=arrows[0])

    def match_shape(self, node):
        start, end = self.span(node)
        if start is None:
            self.problem('missing-match-span', node)
            return None
        selector = self.child(node, 'selector')
        partial = self.empty(selector)
        cases = self.children(node, 'cases')
        if not cases or partial and len(cases) != 1:
            self.problem('multiple-partial-function-cases-review', node)
            return None
        pairs = self.braces(start, end)
        opens = [p for p in self.within(start, end, '{')
                 if p['start'] in pairs and pairs[p['start']]['end'] == end]
        if len(opens) != 1:
            self.problem('match-written-close-review', node)
            return None
        opening = opens[0]
        if partial:
            if opening['start'] != start:
                self.problem('partial-function-opening-review', node)
                return None
        else:
            a, b = self.span(selector)
            keywords = self.within(b, opening['start'], 'match')
            if a != start or len(keywords) != 1:
                self.problem('match-selector-keyword-review', node)
                return None
        shapes = [self.case_shape(case) for case in cases]
        if any(case is None for case in shapes):
            return None
        if partial:
            pattern = shapes[0]['pattern']
            names = self.children(pattern, 'trees')
            if self.product(pattern) != 'Tuple' or not names or any(self.product(n) != 'Ident' for n in names):
                self.problem('partial-function-pattern-review', node)
                return None
        else:
            # Current used selector match has four literal cases and a wildcard;
            # arbitrary extractors and alternative patterns need their own review.
            if any(self.product(case['pattern']) not in ('Literal', 'Ident') for case in shapes):
                self.problem('selector-match-pattern-review', node)
                return None
        return dict(node=node, partial=partial, opening=opening,
                    closing=pairs[opening['start']], cases=shapes, end=end)

    def emit_match(self, shape, owner, start):
        node = shape['node']
        if not shape['partial']:
            self.emit('match-header', owner, start, shape['opening']['end'])
        for case in shape['cases']:
            header_start = start if shape['partial'] else case['start']
            self.emit('pattern-callback-header' if shape['partial'] else 'case-header',
                      case['node'], header_start, case['arrow']['end'])
            for child in case['children']:
                self.unit(child)
            # The arrow-start native Block is retained, but is not a second
            # executable block and therefore contributes no new open or close.
            self.structural(case['body'], case['arrow']['end'], case['end'], {';'})
        close = shape['closing']
        self.emit('written-close', node, close['start'], close['end'])
        self.structural(node, shape['opening']['end'], close['start'], {';'})

    def expand(self, expr, owner, start, end):
        roots = self.special_roots(expr)
        if not roots or not all(self.product(n) == 'Match' for n in roots):
            return super().expand(expr, owner, start, end)
        shapes = [self.match_shape(n) for n in sorted(roots, key=lambda n: self.span(n)[0])]
        if any(shape is None for shape in shapes):
            return True
        if len(shapes) > 1 and not all(shape['partial'] for shape in shapes):
            self.problem('mixed-match-chain-review', owner)
            return True
        cursor = start
        for shape in shapes:
            if shape['opening']['start'] < cursor:
                self.problem('overlapping-callback-owner-review', owner)
                return True
            self.emit_match(shape, owner, cursor)
            cursor = shape['end']
        self.structural(owner, cursor, end, {')', ']', ','})
        return True

    def if_unit(self, node, start, kind='if-header'):
        thenp, elsep = self.child(node, 'thenp'), self.child(node, 'elsep')
        if self.product(thenp) == 'Block':
            self.block(thenp, start, kind, node)
        else:
            self.emit(kind, node, start, self.span(thenp)[0])
            self.unit(thenp)
        if not self.empty(elsep):
            a, _ = self.span(elsep)
            keywords = self.within(self.span(thenp)[1], a, 'else')
            if len(keywords) != 1:
                self.problem('else-keyword-owner-review', node)
                return
            if self.product(elsep) == 'If':
                self.if_unit(elsep, keywords[0]['start'], 'else-if-header')
            elif self.product(elsep) == 'Block':
                self.block(elsep, keywords[0]['start'], 'else-header', node)
            else:
                self.emit('else-header', node, keywords[0]['start'], a)
                self.unit(elsep)

    def _unit(self, node):
        if self.product(node) == 'If':
            self.if_unit(node, self.span(node)[0])
        elif self.product(node) == 'Match':
            shape = self.match_shape(node)
            if shape:
                self.emit_match(shape, node, self.span(node)[0])
        else:
            super()._unit(node)


def project(record, *, application=False):
    result = ReviewedProjection(record).result(application)
    result['schema'] = 'scala-native-owner-reviewed-projection-v1'
    result['frozen_base_sha256'] = BASE_SHA
    return result


def build_packet(output):
    base.require(not output.exists(), 'Fresh additive output directory required')
    replay, records = base.replay_native()
    results = []
    for item, record in records:
        if item['group'] == 'capture':
            continue
        value = project(record, application=item['group'] == 'application')
        value.update(id=item['id'], native_capture_sha256=replay['cases'][item['index']]['capture_sha256'])
        results.append(value)
    files = {row['id']+'.json': (json.dumps(row, indent=2)+'\n').encode() for row in results}
    summary = dict(schema='scala-reviewed-native-owner-candidate-v1', rule=base.RULE,
        input_replay=replay, frozen_base_sha256=BASE_SHA,
        adapter_sha256=base.digest(Path(__file__).read_bytes()),
        tests_sha256=base.digest((ROOT/'tools/test_scala_source_units_reviewed.py').read_bytes()),
        artifacts={name: dict(sha256=base.digest(raw), bytes=len(raw)) for name, raw in files.items()},
        applications=[dict(id=r['id'], source_sha256=r['source_sha256'],
            candidate_normalized_loc=r['candidate_normalized_loc'], physical_loc=r['physical_loc'],
            diagnostics=r['diagnostics'], normalized_loc=None, canonical_LOC_admitted=False)
            for r in results if r['application_manual_owner_review_required']],
        native_executions=0, chart_admission=False)
    output.mkdir(parents=True)
    for name, raw in files.items():
        (output/name).write_bytes(raw)
    (output/'review.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build_packet(args.output.resolve())
    print(json.dumps(result['applications'], indent=2))
