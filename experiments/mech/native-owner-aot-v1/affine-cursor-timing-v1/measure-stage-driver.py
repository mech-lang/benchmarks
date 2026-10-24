"""Build a source-preserving stage and compare it with its parent and upstream Rust."""
import argparse
import fcntl
import json
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process


def closed_key_domains(descriptor):
    """Record the runtime/codegen domain choice for every closed-tail region."""
    regions = []
    for index, region in enumerate(descriptor['closed_tails']['regions']):
        packed = region.get('packed')
        domain = packed.get('domain') if packed is not None else None
        # Domain::packing retains an injective bit window; absent proofs and
        # finite alphabets without such a window use the full ASCII encoding.
        packing = domain if domain is not None and domain.get('shift') is not None else dict(
            alphabet=[(1 << 64) - 1, (1 << 64) - 1], bits=7, shift=0)
        regions.append(dict(region=index, map_owner=region.get('map'),
                            packed_proof=packed is not None, source_domain=domain,
                            packing_domain=packing if packed is not None else None))
    return regions


def require_key_domains(regions, bits):
    """Reject fallback or noninjective source proofs before any timed process."""
    maps = [region for region in regions if region['map_owner'] is not None]
    assert maps, 'Candidate has no closed map domains to qualify'
    for region in maps:
        domain = region['source_domain']
        assert region['packed_proof'] and domain is not None, 'Closed map lacks a source-derived packed domain'
        assert domain['bits'] == bits and region['packing_domain'] == domain, 'Closed map uses a different or fallback encoding'
        shift = domain['shift']
        assert type(shift) is int and 0 <= shift <= 7 - bits, 'Packed domain lacks a valid bit window'
        alphabet = domain['alphabet']
        assert len(alphabet) == 2 and all(type(word) is int and 0 <= word < (1 << 64) for word in alphabet)
        symbols = [byte for byte in range(128) if alphabet[byte // 64] & (1 << (byte % 64))]
        assert symbols and max(1, (len(symbols) - 1).bit_length()) == bits, 'Packed domain has an inconsistent symbol width'
        codes = {(byte >> shift) & ((1 << bits) - 1) for byte in symbols}
        assert len(codes) == len(symbols), 'Packed domain bit window loses character identity'


def require_edge_facts(metadata, descriptor, minimum_guards, minimum_arithmetic, threaded_headers=frozenset()):
    """Qualify actual emitted substitutions against the retained source CFG."""
    assert metadata and metadata['complete'] is True, 'Missing or truncated emission receipt'
    regions = metadata['regions']
    by_header = {region['header']: region for region in regions}
    assert len(by_header) == len(regions), 'Duplicate compiled region headers'
    closed = descriptor['closed_tails']
    expected = {region['tail']['header']: index for index, region in enumerate(closed['regions'])
                if region.get('map') is not None and region.get('packed') is not None}
    assert expected and set(expected) <= set(by_header), 'Packed source region lacks emission receipt'
    qualified = []
    for header, owner in expected.items():
        region = by_header[header]
        guards, arithmetic = region['guards'], region['arithmetic']
        distinct_guards = {json.dumps(record, sort_keys=True) for record in guards}
        distinct_arithmetic = {json.dumps(record, sort_keys=True) for record in arithmetic}
        assert len(distinct_guards) >= minimum_guards, 'Too few distinct actual field-guard substitutions'
        assert len(distinct_arithmetic) >= minimum_arithmetic, 'Too few distinct actual arithmetic substitutions'
        if header not in threaded_headers:
            assert len(guards) == len(distinct_guards) and len(arithmetic) == len(distinct_arithmetic), 'Duplicate emission records without qualified state versions'
        for record in guards + arithmetic:
            site = record['site']
            assert type(site) is int and 0 <= site < len(closed['sites'])
            assert closed['sites'][site] == owner, 'Substitution belongs to another source region'
        for record in guards:
            site = record['site']
            owner_words = descriptor['map_owner_words']
            layout = (owner_words['aggregates']
                      if owner_words['action_regions'][site] == closed['regions'][owner]['map']
                      else descriptor['scalar_aggregates'])
            encoded = layout['actions'][site]
            assert encoded and len(encoded) == 1
            kind, action = next(iter(encoded.items()))
            assert kind in ('Observe', 'Project'), 'Guard is not an actual aggregate projection'
            assert action['source'] == record['source']
            assert type(record['offset']) is int and record['offset'] >= 0
            assert [record['offset'], record['ordinal']] in action['guards'], 'Guard does not match its exact projection'
        for record in arithmetic:
            action = descriptor['plan']['blocks'][record['site']]['action']['Scalar']['Primitive']
            assert record['op'] in ('U64Add', 'U64Sub')
            assert action['op'] == record['op'] and action['operands'] == record['operands']
        qualified.append(dict(header=header, source_region=owner,
                              field_guards=len(distinct_guards), arithmetic=len(distinct_arithmetic),
                              emitted_field_guards=len(guards), emitted_arithmetic=len(arithmetic)))
    return qualified


def require_tag_threading(metadata, descriptor, minimum_branches, minimum_latches):
    """Tie actual emitted state-specialized entries to their original CFG."""
    assert metadata and metadata['complete'] is True, 'Missing or truncated state-threading receipt'
    records = metadata['regions']
    by_header = {record['header']: record for record in records}
    assert len(by_header) == len(records), 'Duplicate state-threading headers'
    closed, owner_words = descriptor['closed_tails'], descriptor['map_owner_words']
    expected = {region['tail']['header']: index for index, region in enumerate(closed['regions'])
                if region.get('map') is not None and region.get('packed') is not None}
    assert expected and set(expected) <= set(by_header), 'Packed source region lacks state-threading receipt'
    qualified = []
    for header, owner in expected.items():
        record, tail = by_header[header], closed['regions'][owner]['tail']
        carrier = tail['carrier']
        slot = owner_words['aggregates']['slots'][carrier]
        assert slot and record['carrier_word'] == slot[0]
        ordinals = set()
        for site, action in enumerate(owner_words['aggregates']['actions']):
            if closed['sites'][site] != owner or not action:
                continue
            observe = action.get('Observe')
            if observe and observe['source'] == carrier and observe['offset'] == 0 and observe['ordinal'] is not None:
                ordinals.add(observe['ordinal'])
        assert ordinals and record['variants'] == sorted(ordinals), 'Unexpected specialized enum variants'
        assert record['source_sites'] == sum(value == owner for value in closed['sites'])
        assert 0 < record['source_sites'] <= 256 and 0 < record['product_nodes'] <= 1024
        assert record['header_versions'] >= 3, 'Missing initial, recurring or terminal entry'
        branches, latches = record['folded_branches'], record['known_latches']
        assert len(branches) >= minimum_branches and len(latches) >= minimum_latches
        for site in branches:
            assert type(site) is int and 0 <= site < len(closed['sites'])
            assert closed['sites'][site] == owner
            branch = descriptor['plan']['blocks'][site]['terminator'].get('Scalar', {})
            assert 'Branch' in branch or 'LiteralBranch' in branch, 'Folded site is not an original branch'
        assert all(site == tail['latch'] for site in latches), 'Known latch differs from source latch'
        qualified.append(dict(header=header, source_region=owner,
                              folded_branches=len(branches), known_latches=len(latches),
                              header_versions=record['header_versions'], product_nodes=record['product_nodes']))
    return qualified


def require_frame_effects(metadata, descriptor):
    """Verify narrow synchronization against the unchanged ABI24–26 Frame."""
    assert metadata and metadata['complete'] is True, 'Missing or truncated frame-effect receipt'
    records = metadata['regions']
    by_header = {record['header']: record for record in records}
    assert len(by_header) == len(records), 'Duplicate frame-effect headers'
    expected = {region['tail']['header'] for region in descriptor['closed_tails']['regions']
                if region.get('map') is not None and region.get('packed') is not None}
    assert expected and expected == set(by_header), 'Frame-effect headers differ from the exact packed source regions'
    # Fields are word indices in the unchanged nineteen-word ABI24–26 Frame.
    # These expectations are deliberately independent of the compiler's masks.
    effects = {0: ([3, 8], [3, 7, 8]),
               7: ([3, 4, 5, 6, 7, 8], [0, 1, 2, 4, 7, 15, 16, 17, 18]),
               6: ([], []), 8: ([], []), 9: ([], []),
               10: ([3, 8], []), 11: ([3, 8], []), 12: ([3, 8], [])}
    qualified = []
    for header in sorted(expected):
        operations = by_header[header]['operations']
        by_op = {record['operation']: record for record in operations}
        assert len(by_op) == len(operations) and set(by_op) == set(effects), 'Missing, duplicate or unproved helper effects'
        for op, (stores, loads) in effects.items():
            record = by_op[op]
            assert type(record['emitted_calls']) is int and record['emitted_calls'] > 0
            assert record['stored_words'] == stores and record['reloaded_words'] == loads, 'Private helper effects disagree with its exact frame contract'
        qualified.append(dict(header=header, operations=operations,
                              scope='Actual compiled call templates; not runtime callback frequencies'))
    return qualified


def require_lookup_facts(metadata, descriptor, tags, explicit_source_variant=False):
    """Bind emitted lookup substitutions to exact original map operations."""
    assert metadata and metadata['complete'] is True
    records = metadata['regions']
    by_header = {record['header']: record for record in records}
    expected = {region['tail']['header'] for region in descriptor['closed_tails']['regions']
                if region.get('map') is not None and region.get('packed') is not None}
    assert expected and len(by_header) == len(records) and set(by_header) == expected
    assert tags and tags['complete'] is True
    tag_headers = {record['header']: record for record in tags['regions']}
    qualified = []
    for header in sorted(expected):
        record = by_header[header]
        assert 1 <= record['source_nodes'] <= 1024
        assert record['emitted_nodes'] == tag_headers[header]['product_nodes']
        assert record['emitted_nodes'] in (record['source_nodes'], 2 * record['source_nodes'], 4 * record['source_nodes'])
        region_id = descriptor['closed_tails']['sites'][header]
        substitutions = record['substitutions']
        seen, facts, sites = set(), set(), set()
        for substitution in substitutions:
            node, site = substitution['node'], substitution['site']
            assert type(node) is int and 0 <= node < record['emitted_nodes'] and node not in seen
            seen.add(node)
            assert descriptor['closed_tails']['sites'][site] == region_id
            call = descriptor['plan']['blocks'][site]['action']['LibraryCall']
            selected = call['template']['selected']
            assert len(selected) == 1
            primitive = next(iter(selected.values()))['leaf']['primitive']
            operation = {'MapContainsKey': 3, 'MapKeyAccess': 4, 'MapInsert': 5}[primitive]
            assert substitution['operation'] == operation
            fact = substitution['fact']
            assert fact in ('Fresh', 'Cached', 'Present', 'Absent')
            facts.add(fact)
            sites.add(site)
        if record.get('state_threading') is not None:
            # The ORIGINAL merged-count source now has distinct compiled
            # Present/Absent continuations; qualify their exact nodes below.
            assert {'Fresh', 'Present', 'Absent'} <= facts
            require_lookup_threading(dict(complete=True, regions=[record]), descriptor)
        elif explicit_source_variant:
            # A branch-local insert can retain Present/Absent rather than the
            # weaker Cached fact required by the original merged-count source.
            assert any(s['operation'] == 3 and s['fact'] == 'Fresh' for s in substitutions)
            assert any(s['operation'] == 4 and s['fact'] == 'Present' for s in substitutions)
            inserts = [s for s in substitutions if s['operation'] == 5]
            assert inserts and all(s['fact'] in ('Cached', 'Present', 'Absent') for s in inserts)
        else:
            assert {'Fresh', 'Present', 'Cached'} <= facts
        assert len(sites) >= 3
        qualified.append(dict(header=header, source_nodes=record['source_nodes'], emitted_nodes=record['emitted_nodes'],
                              substitutions=substitutions,
                              scope='Actual compiled current-key substitutions; not dynamic per-path frequencies. Runtime packed SSA selection is separately required.'))
    return qualified


def require_lookup_threading(metadata, descriptor):
    """Bind bounded current-key product nodes to original source operations."""
    assert metadata and metadata['complete'] is True
    result = []
    for region in metadata['regions']:
        proof = region.get('state_threading')
        assert isinstance(proof, dict), 'Current-key state expansion was not emitted'
        states = proof['states']
        assert 0 < proof['original_tag_nodes'] <= 256
        assert 0 < len(states) == region['source_nodes'] <= 256
        assert region['emitted_nodes'] <= 1024
        source_region = descriptor['closed_tails']['sites'][region['header']]
        original_sites, by_original = {}, {}
        for node, state in enumerate(states):
            assert len(state) == 4 and state[0] == node
            _, original, site, fact = state
            assert type(original) is int and 0 <= original < proof['original_tag_nodes']
            assert descriptor['closed_tails']['sites'][site] == source_region
            assert original_sites.setdefault(original, site) == site
            assert fact in ('Unknown', 'Fresh', 'Cached', 'Present', 'Absent')
            by_original.setdefault(original, set()).add(fact)
        split_inserts = []
        for original, facts in by_original.items():
            site = original_sites[original]
            call = descriptor['plan']['blocks'][site]['action'].get('LibraryCall')
            if call and {'Present', 'Absent'} <= facts:
                selected = call['template']['selected']
                primitive = next(iter(selected.values()))['leaf']['primitive']
                if primitive == 'MapInsert':
                    split_inserts.append(dict(original_node=original, source_site=site))
        assert split_inserts, 'No original insertion join retains both source-derived states'
        for substitution in region['substitutions']:
            state = states[substitution['node'] % len(states)]
            assert (state[2], state[3]) == (substitution['site'], substitution['fact'])
        for node, site in proof['folded_predicate_branches']:
            assert states[node][2] == site
            branch = descriptor['plan']['blocks'][site]['terminator'].get('Scalar', {})
            assert 'Branch' in branch or 'LiteralBranch' in branch
        result.append(dict(header=region['header'], original_tag_nodes=proof['original_tag_nodes'],
                           product_nodes=len(states), split_insert_joins=split_inserts,
                           scope='Actual compiled current-key versions and source sites; not dynamic path frequencies.'))
    assert result
    return result


def require_frozen_maps(candidate_count, descriptor):
    """Bind private-map inventory to source sites; loaders rederive its proof."""
    layout, plan = descriptor['frozen_maps'], descriptor['plan']
    regions, closed = layout['regions'], descriptor['closed_tails']['regions']
    owners = descriptor['map_owner_words']['regions']
    assert type(candidate_count) is int and candidate_count == len(regions) == 1
    assert all(len(layout[key]) == len(plan['blocks']) for key in ('exits', 'copies', 'reads'))
    qualified = []
    for index, region in enumerate(regions):
        assert type(region['closed']) is int and 0 <= region['closed'] < len(closed)
        source = closed[region['closed']]
        assert source['packed'] is not None and source['map'] == region['owner']
        assert type(region['owner']) is int and 0 <= region['owner'] < len(owners)
        tail = source['tail']
        assert owners[region['owner']]['tail'] == tail
        assert region['exit'] == tail['exit'] and region['output'] == tail['result']
        assert region['parent'] == plan['iterations'][source['iteration']]['Tail']['parent']
        aliases = region['aliases']
        assert aliases and aliases == sorted(set(aliases)) and region['output'] in aliases
        result_type = plan['values'][region['output']]
        body = result_type['definition']['body']['Map']
        assert body['key'] == 'String' and body['value'] == {'UnsignedInteger': 'W64'}
        for alias in aliases:
            assert type(alias) is int and 0 <= alias < len(plan['values'])
            assert plan['values'][alias] == result_type
            assert plan['value_scopes'][alias] == {'Immutable': {'iteration': region['parent']}}
        exit_sites = [site for site, selected in enumerate(layout['exits']) if selected == index]
        assert exit_sites == [region['exit']]
        exit_block = plan['blocks'][region['exit']]
        assert exit_block['iteration'] == region['parent']
        assert exit_block['action'] == {'Scalar': {'Copy': {'source': tail['returned'], 'output': tail['result']}}}
        copies = [site for site, selected in enumerate(layout['copies']) if selected == index]
        reads = [site for site, selected in enumerate(layout['reads']) if selected == index]
        assert reads
        primitives = []
        for site in copies:
            block = plan['blocks'][site]
            assert block['iteration'] == region['parent']
            copy = block['action']['Scalar']['Copy']
            assert copy['source'] in aliases and copy['output'] in aliases
        for site in reads:
            block = plan['blocks'][site]
            assert block['iteration'] == region['parent']
            call = block['action']['LibraryCall']
            assert len(call['operands']) == 2 and call['operands'][0] in aliases
            assert plan['values'][call['operands'][1]]['definition']['body'] == 'String'
            selected = call['template']['selected']
            assert len(selected) == 1
            primitive = next(iter(selected.values()))['leaf']['primitive']
            assert primitive in ('MapContainsKey', 'MapKeyAccess')
            primitives.append(primitive)
        assert sorted(primitives) == ['MapContainsKey', 'MapKeyAccess']
        qualified.append(dict(owner=region['owner'], closed=region['closed'], header=tail['header'],
                              parent=region['parent'], exit=region['exit'], output=region['output'],
                              aliases=aliases, copies=copies, reads=reads,
                              scope='Source-bound complete-map candidates; actual retention and reads are separately required'))
    for key in ('exits', 'copies', 'reads'):
        assert all(value is None or type(value) is int and 0 <= value < len(regions) for value in layout[key])
    return qualified


def require_guarded_loops(metadata, descriptor, tag_metadata, invariant_metadata=()):
    """Bind emitted checked/fast versions to the original guarded source loop."""
    assert metadata and metadata['complete'] is True, 'Missing or truncated guarded-loop receipt'
    assert tag_metadata and tag_metadata['complete'] is True, 'Guarded loops require qualified state-threading metadata'
    closed, plan = descriptor['closed_tails'], descriptor['plan']
    owners = descriptor['map_owner_words']
    expected = {region['tail']['header']: index for index, region in enumerate(closed['regions'])
                if region.get('map') is not None and region.get('packed') is not None}
    records, tags = metadata['regions'], tag_metadata['regions']
    by_header = {record['header']: record for record in records}
    by_tag_header = {record['header']: record for record in tags}
    assert expected and len(by_header) == len(records) and set(by_header) == set(expected), 'Guarded headers differ from the exact packed source regions'
    assert len(by_tag_header) == len(tags) and set(by_tag_header) == set(expected), 'Guarded tag graphs differ from the packed source regions'
    blocks, values = plan['blocks'], plan['values']
    constants = {record['value']: record['constant']['data'] for record in plan['constants']}
    definitions = {}
    for site, block in enumerate(blocks):
        action = block['action']
        scalar = action.get('Scalar')
        if isinstance(scalar, dict):
            output = next(iter(scalar.values())).get('output')
        else:
            output = next(iter(action.values())).get('output') if 'Scalar' not in action else None
        if output is not None:
            definitions.setdefault(output, []).append(site)

    def u64(value):
        assert type(value) is int and 0 <= value < len(values), 'Guarded scalar value is outside its source plan'
        definition = values[value]['definition']
        assert definition['dimension_parameters'] == [] and definition['body'] == {'UnsignedInteger': 'W64'}, 'Guarded scalar is not a plain U64'

    qualified = []
    for header, region_id in expected.items():
        record, region, tag = by_header[header], closed['regions'][region_id], by_tag_header[header]
        tail, packed = region['tail'], region['packed']
        carrier = tail['carrier']
        slot = owners['aggregates']['slots'][carrier]
        index, width, limit = (record[key] for key in ('index_word', 'width_word', 'limit_word'))
        assert slot and type(index) is int and slot[0] < index < slot[0] + slot[1], 'Guarded index is outside the carrier payload'
        assert tag['carrier_word'] == slot[0]
        assert width == packed['end_offset'] and packed['inclusive'] is True, 'Guarded width differs from the proved inclusive range'
        u64(width)
        u64(limit)
        variants = values[carrier]['definition']['body']['Enum']['variants']
        active = record['active_tag']
        assert type(active) is int and 0 <= active < len(variants) and active in tag['variants'], 'Guarded state is not an actual root enum variant'
        source_tail = plan['iterations'][region['iteration']]['Tail']
        assert all(source_tail[key] == tail[key] for key in
                   ('carrier', 'header', 'latch', 'initialize', 'body', 'exit'))
        ancestors, current = set(), source_tail['parent']
        while current is not None:
            assert current not in ancestors, 'Cyclic source iteration ancestry'
            ancestors.add(current)
            control = next(iter(plan['iterations'][current].values()))
            current = control['parent']
        for value in (width, limit):
            scope = plan['value_scopes'][value].get('Immutable')
            assert scope is not None and (scope['iteration'] is None or scope['iteration'] in ancestors), 'Guarded width/limit is not immutable outside the loop'

        def expression(value, seen=frozenset()):
            u64(value)
            assert value not in seen and len(seen) < 32, 'Cyclic or excessive guarded scalar expression'
            if value == width:
                return ('width',)
            if value == limit:
                return ('limit',)
            if value in constants:
                data = constants[value]
                assert set(data) == {'U64'} and type(data['U64']) is int
                return ('constant', data['U64'])
            sites = definitions.get(value, [])
            assert len(sites) == 1, 'Guarded expression has no unique source producer'
            site = sites[0]
            assert closed['sites'][site] == region_id, 'Guarded expression leaves its original region'
            action = blocks[site]['action']
            scalar = action.get('Scalar', {})
            if isinstance(scalar, dict) and 'Copy' in scalar:
                return expression(scalar['Copy']['source'], seen | {value})
            if isinstance(scalar, dict) and 'Primitive' in scalar:
                primitive = scalar['Primitive']
                assert primitive['op'] in ('U64Add', 'U64Sub') and len(primitive['operands']) == 2
                return (primitive['op'], *(expression(v, seen | {value}) for v in primitive['operands']))
            aggregate = (owners['aggregates'] if owners['action_regions'][site] == region['map']
                         else descriptor['scalar_aggregates'])
            observed = (aggregate['actions'][site] or {}).get('Observe')
            structural = action.get('Structural')
            assert observed and structural and structural['source'] == carrier and structural['observation'] == 'U64', 'Guarded index is not a source U64 payload projection'
            assert observed['source'] == carrier and observed['ordinal'] is None and observed['output'] == value
            assert slot[0] + observed['offset'] == index and [0, active] in observed['guards'], 'Guarded index projection differs from the active carrier payload'
            assert structural['path'] and structural['path'][0] == {'EnumPayload': {'ordinal': active}}
            return ('index',)

        guards = record['stop_guards']
        assert len(guards) == 3 and len(set(guards)) == 3, 'Guarded stop sites must be three distinct source guards'
        expected_ops = ('U64Eq', 'U64Ge', 'U64Gt')
        for ordinal, site in enumerate(guards):
            assert type(site) is int and 0 <= site < len(blocks) and closed['sites'][site] == region_id
            block = blocks[site]
            primitive = block['action']['Scalar']['Primitive']
            assert primitive['op'] == expected_ops[ordinal] and len(primitive['operands']) == 2
            branch = block['terminator']['Scalar']['Branch']
            assert branch['condition'] == primitive['output'], 'Guarded comparison does not control its source branch'
            assert branch['yes'] != branch['no'] and all(type(branch[arm]) is int and 0 <= branch[arm] < len(blocks)
                and closed['sites'][branch[arm]] == region_id for arm in ('yes', 'no'))
            operands = tuple(expression(v) for v in primitive['operands'])
            if ordinal == 0:
                assert operands in ((('width',), ('constant', 0)), (('constant', 0), ('width',))), 'First stop is not width == 0'
            elif ordinal == 1:
                assert primitive['operands'][1] == limit and operands == (('index',), ('limit',)), 'Second stop is not index >= limit'
            else:
                assert operands == (('width',), ('U64Sub', ('limit',), ('index',))), 'Third stop is not width > limit - index'
        assert record['recurrence_latches'] == [tail['latch']], 'Guarded recurrence differs from the unique original latch'
        latch = blocks[tail['latch']]
        assert latch['action'] == {'Latch': {'iteration': region['iteration']}}
        assert latch['terminator'] == {'Scalar': {'Jump': header}}
        site = record['range_site']
        assert type(site) is int and site == packed['range_site'] and closed['sites'][site] == region_id
        spans = [span for span in owners['spans'] if span['region'] == region['map'] and span['range_site'] == site]
        assert len(spans) == 1 and spans[0]['selection_site'] == packed['selection_site']
        call = blocks[site]['action']['LibraryCall']
        assert call['operands'] == spans[0]['operands'] and len(call['operands']) == 2
        selected = call['template']['selected']
        assert len(selected) == 1 and next(iter(selected.values()))['leaf']['primitive'] == 'RangeInclusive'
        selection = blocks[packed['selection_site']]['action']['LibraryCall']
        selected = selection['template']['selected']
        assert len(selected) == 1 and next(iter(selected.values()))['leaf']['primitive'] == 'StringRangeAccess'
        assert selection['operands'] == [spans[0]['source'], call['output']] and selection['output'] == spans[0]['output']
        endpoints = [expression(value) for value in call['operands']]
        assert endpoints[0] in (('U64Add', ('index',), ('constant', 1)), ('U64Add', ('constant', 1), ('index',)))
        assert endpoints[1] in (('U64Add', ('index',), ('width',)), ('U64Add', ('width',), ('index',)))
        nodes = record['emitted_nodes']
        assert type(nodes) is int and 0 < nodes <= 1024 and nodes % 2 == 0 and nodes == tag['product_nodes'], 'Guarded versions differ from the actual qualified tag graph'
        certified = record['certified_range_versions']
        assert certified and len(set(certified)) == len(certified)
        invariant = next((r for r in invariant_metadata if r['header'] == header), None)
        first_guarded = invariant['version_stride'] if invariant else nodes // 2
        if invariant: assert nodes == 4 * first_guarded
        assert all(type(version) is int and first_guarded <= version < nodes for version in certified), 'Range certification escapes the guarded versions'
        assert record['checked_fallback'] is True
        fixed = record['fixed_template_instructions']
        assert type(fixed) is int and 1 <= fixed <= 1024, 'Guarded fixed templates exceed the unchanged work envelope'
        qualified.append(dict(header=header, source_region=region_id, index_word=index,
                              width_word=width, limit_word=limit, active_tag=active,
                              stop_guards=guards, range_site=site, recurrence_latches=record['recurrence_latches'],
                              emitted_nodes=nodes, certified_range_versions=certified,
                              fixed_template_instructions=fixed, checked_fallback=True,
                              scope='Actual checked/fast emission records; runtime selection is independently required'))
    return qualified


def require_loop_invariants(records, descriptor, lookups, guarded):
    assert isinstance(records, list) and 0 < len(records) <= 256
    by_header = {r['header']: r for r in records}
    lookup = {r['header']: r for r in lookups}
    bounds = {r['header']: r for r in guarded}
    assert len(by_header) == len(records) and set(by_header) == set(lookup) == set(bounds)
    qualified = []
    blocks = descriptor['plan']['blocks']
    for header, record in sorted(by_header.items()):
        stride, nodes = record['version_stride'], record['emitted_nodes']
        assert type(stride) is int and 0 < stride <= 256
        assert stride == lookup[header]['source_nodes'] and nodes == 4 * stride == bounds[header]['emitted_nodes']
        assert record['fixed_template_work'] == bounds[header]['fixed_template_instructions'] <= 1024
        calls, sites, seen = {}, set(), set()
        for node, site, op in record['call_substitutions']:
            assert type(node) is int and 2 * stride <= node < nodes and node not in seen
            seen.add(node)
            if op == 10: assert site == bounds[header]['range_site']
            else:
                call = blocks[site]['action']['LibraryCall']
                selected = call['template']['selected']
                assert len(selected) == 1
                primitive = next(iter(selected.values()))['leaf']['primitive']
                assert op == {'MapContainsKey': 3, 'MapKeyAccess': 4, 'MapInsert': 5}[primitive]
            calls.setdefault((node % stride, site, op), set()).add(node // stride)
            sites.add(op)
        assert all(modes == {2, 3} for modes in calls.values()) and {3, 4, 5, 10} <= sites
        rolling = record['rolling_substitutions']
        assert rolling and len({n for n,s in rolling}) == len(rolling)
        assert all(3 * stride <= n < nodes and site == bounds[header]['range_site'] for n,site in rolling)
        expected_ranges = {n % stride + mode * stride for n,site in rolling for mode in (1, 2, 3)}
        assert expected_ranges == set(bounds[header]['certified_range_versions'])
        latches = record['steady_latches']
        assert latches and all(2 * stride <= n < nodes and site in bounds[header]['recurrence_latches'] for n,site in latches)
        refreshes = {}
        for node, site in record['refreshes']:
            assert stride <= node < nodes
            call = blocks[site]['action']['LibraryCall']
            selected = call['template']['selected']
            assert len(selected) == 1 and next(iter(selected.values()))['leaf']['primitive'] == 'MapInsert'
            refreshes.setdefault((node % stride, site), set()).add(node // stride)
        assert refreshes and all(modes == {1, 2, 3} for modes in refreshes.values())
        assert set(refreshes) == {(n,site) for n,site,op in calls if op == 5}
        qualified.append(dict(record, scope='Source-bound emitted call guards, peeled ranges, proved recurrence entries and exact post-insertion redispatch sites; not dynamic per-substitution frequencies. Initial guarded-call selection is independently required.'))
    return qualified


def require_mutation_facts(records, descriptor, tags, guarded, lookups, invariants):
    """Bind actual progress/storage substitutions to their unchanged source sites."""
    expected = {record['header']: record for record in guarded}
    assert records and len(records) <= 256 and len(records) == len(expected)
    by_header = {record['header']: record for record in records}
    assert len(by_header) == len(records) and set(by_header) == set(expected)
    tag_headers = {record['header']: record for record in tags['regions']}
    lookup_headers = {record['header']: record for record in lookups['regions']}
    invariant_headers = {record['header']: record for record in invariants}
    qualified = []
    for header, record in by_header.items():
        bound = expected[header]
        stride, nodes = record['version_stride'], record['emitted_nodes']
        assert type(stride) is int and 0 < stride <= 256 and nodes == 4 * stride <= 1024
        assert nodes == tag_headers[header]['product_nodes'] == invariant_headers[header]['emitted_nodes']
        assert stride == invariant_headers[header]['version_stride']
        assert record['index_word'] == bound['index_word'] and record['active_tag'] == bound['active_tag']
        assert record['alignment_guard'] is True
        region = bound['source_region']
        owners = descriptor['map_owner_words']

        def primitive(site):
            assert type(site) is int and 0 <= site < len(descriptor['plan']['blocks'])
            assert descriptor['closed_tails']['sites'][site] == region
            assert owners['call_regions'][site] == descriptor['closed_tails']['regions'][region]['map']
            call = descriptor['plan']['blocks'][site]['action']['LibraryCall']
            return next(iter(call['template']['selected'].values()))['leaf']['primitive']

        insertions = dict(record['source_insert_nodes'])
        assert insertions and len(insertions) == len(record['source_insert_nodes'])
        assert all(type(node) is int and 0 <= node < stride and primitive(site) == 'MapInsert'
                   for node, site in insertions.items())
        for key in ('counter_headers', 'counter_checks_removed', 'nonempty_probes'):
            rows = record[key]
            assert rows and len(rows) == len({tuple(row) for row in rows})
            assert all(type(node) is int and stride <= node < nodes for node, _ in rows)
        assert all(site == header for _, site in record['counter_headers'])
        assert all(insertions[node % stride] == site for node, site in record['counter_checks_removed'])
        facts = {(row['node'], row['site']): row['fact'] for row in lookup_headers[header]['substitutions']}
        for node, site in record['nonempty_probes']:
            assert node // stride == 3 and primitive(site) in ('MapContainsKey', 'MapKeyAccess', 'MapInsert')
            assert facts[(node, site)] == 'Fresh'
        qualified.append(dict(header=header, index_word=record['index_word'],
                              source_insert_nodes=record['source_insert_nodes'],
                              guarded_counter_headers=len(record['counter_headers']),
                              counter_checks_removed=len(record['counter_checks_removed']),
                              steady_nonempty_probes=len(record['nonempty_probes']),
                              scope='Actual source-bound emission records plus the active entry alignment guard; compiler CFG proofs and runtime guarded-loop selection are separately checked. Not dynamic per-substitution frequencies.'))
    return qualified


def require_count_values(records, descriptor, mutation):
    """Bind guarded count substitutions to their actual source reads/adds."""
    assert isinstance(records, list) and 0 < len(records) <= 256
    by_header = {record['header']: record for record in records}
    parents = {record['header']: record for record in mutation}
    assert len(by_header) == len(records) and set(by_header) == set(parents)
    constants = {item['value']: item['constant']['data'] for item in descriptor['plan']['constants']}
    qualified = []
    for header, record in by_header.items():
        parent = parents[header]
        for key in ('index_word', 'active_tag', 'version_stride', 'emitted_nodes'):
            assert record[key] == parent[key]
        assert parent['alignment_guard'] is True and record['empty_seed_checked'] is True
        stride, nodes = record['version_stride'], record['emitted_nodes']
        assert 0 < stride <= 256 and nodes == 4 * stride
        region = descriptor['closed_tails']['sites'][header]
        owner = descriptor['closed_tails']['regions'][region]['map']
        pairs = {}
        for key in ('source_read_nodes', 'source_add_nodes'):
            rows = record[key]
            assert rows and len(rows) == len({tuple(row) for row in rows})
            pairs[key] = dict(rows)
            assert len(pairs[key]) == len(rows)
            for node, site in rows:
                assert type(node) is int and 0 <= node < stride
                assert descriptor['closed_tails']['sites'][site] == region
                action = descriptor['plan']['blocks'][site]['action']
                if key == 'source_read_nodes':
                    assert descriptor['map_owner_words']['call_regions'][site] == owner
                    selected = action['LibraryCall']['template']['selected']
                    assert len(selected) == 1
                    assert next(iter(selected.values()))['leaf']['primitive'] == 'MapKeyAccess'
                else:
                    scalar = action['Scalar']['Primitive']
                    assert scalar['op'] == 'U64Add' and len(scalar['operands']) == 2
                    assert any(constants.get(value) == {'U64': 1} for value in scalar['operands'])
        removed = record['overflow_checks_removed']
        assert removed and len(removed) == len({tuple(row) for row in removed})
        expected = {(node + mode * stride, site) for node, site in pairs['source_add_nodes'].items()
                    for mode in (1, 2, 3)}
        assert {tuple(row) for row in removed} == expected
        qualified.append(dict(header=header, source_read_nodes=record['source_read_nodes'],
                              source_add_nodes=record['source_add_nodes'], guarded_checks_removed=len(removed),
                              scope='Actual emitted source-read/unit-add records bound to the existing guarded empty-owner induction; source CFG proof and runtime guarded-loop entry are separately checked. Not dynamic substitution frequencies or an independent reimplementation of the compiler proof.'))
    return qualified


def require_header_cache(records, descriptor, tags, lookups):
    """Bind actual cache clears to proved original headers and emitted graphs."""
    assert tags['complete'] is True and lookups['complete'] is True
    assert isinstance(records, list) and 0 < len(records) <= 256
    tagged = {r['header']: r for r in tags['regions']}
    lookup = {r['header']: r for r in lookups['regions']}
    assert len(records) == len({r['header'] for r in records})
    assert {r['header'] for r in records} == set(lookup)
    qualified, total = [], 0
    for record in records:
        header = record['header']
        tag, facts = tagged[header], lookup[header]
        block = descriptor['plan']['blocks'][header]
        assert block['action'] == {'Scalar': 'None'} and 'TailHeader' in block['terminator']
        assert record['cleared_words'] == [7, 8]
        stride, nodes = record['version_stride'], record['emitted_nodes']
        assert stride == facts['source_nodes'] and 0 < stride <= 1024
        assert nodes == facts['emitted_nodes'] == tag['product_nodes']
        assert nodes in (stride, 2 * stride, 4 * stride)
        resets = record['resets']
        assert len(resets) == tag['header_versions'] and resets
        assert len(resets) == len({row[0] for row in resets})
        for node, site in resets:
            assert type(node) is int and 0 <= node < nodes and site == header
        total += len(resets)
        assert total <= 4096
        qualified.append(dict(header=header, version_stride=stride, emitted_nodes=nodes,
                              header_resets=len(resets), cleared_words=[7, 8],
                              scope='Actual emitted cache clears bound to original source headers and the existing lookup-analysis graph. Compiler header invalidation and runtime equivalence are separately checked; no dynamic reset-frequency claim.'))
    return qualified


def require_loop_constants(records, loops, guarded, descriptor, stack_bytes):
    """Bind immutable caller packets to actual callees and source endpoints."""
    assert records['complete'] is True
    callers = records['callers']
    assert isinstance(callers, list) and 0 < len(callers) <= 256
    by_header = {r['header']: r for r in callers}
    callee = {r['header']: r for r in loops}
    bounds = {r['header']: r for r in guarded['regions']}
    assert len(by_header) == len(callers) and set(by_header) == set(callee) == set(bounds)
    qualified = []
    for header, caller in by_header.items():
        loop, proof = callee[header], bounds[header]
        assert 'TailHeader' in descriptor['plan']['blocks'][header]['terminator']
        assert caller['stack_bytes'] == loop['constant_packet_bytes'] == 24
        assert caller['hash_values'] == [0xbf58476d1ce4e5b9, 0x94d049bb133111eb]
        words = [proof['width_word'], proof['limit_word']]
        assert caller['endpoint_words'] == loop['constant_endpoint_words'] == words
        assert 0 < caller['template_instructions'] <= loop['caller_template_bound'] == 64
        assert 0 < loop['emitted_hash_constant_loads'] <= 2 * proof['emitted_nodes']
        assert loop['emitted_hash_constant_loads'] % 2 == 0 and loop['emitted_endpoint_loads'] == 1
        assert stack_bytes >= loop['stack_bytes'] + 24
        qualified.append(dict(header=header, caller_stack_bytes=24, source_endpoint_words=words,
                              emitted_hash_loads=loop['emitted_hash_constant_loads'], emitted_endpoint_loads=1,
                              caller_template_instructions=caller['template_instructions'],
                              scope='Actual caller stack binding and callee load emissions, tied to source-certified width/limit words. Native code placement, exact stack limits and runtime equivalence are checked separately; no dynamic per-load-frequency claim.'))
    return qualified


def require_steady_loops(records, descriptor, loops, guarded, invariants, lookups, pre_data_passes=0, preserve_entry_inputs=False, specialize_widths=False, fuel_edge_checks=False, productive_entry=False, separate_header_snapshots=False, peeled_entry_probes=False, prepaid_extent=False, caller_prepaid_extent=False, affine_cursor=False):
    """Bind helper-free functions and cold continuations to actual source nodes."""
    assert isinstance(records, list) and 0 < len(records) <= 256
    expected = {r['header']: r for r in loops}
    bounds = {r['header']: r for r in guarded['regions']}
    invariant = {r['header']: r for r in invariants}
    lookup = {r['header']: r for r in lookups['regions']}
    assert len(records) == len(expected) and {r['header'] for r in records} == set(expected)
    closed = descriptor['closed_tails']
    owners = {r['tail']['header']: i for i, r in enumerate(closed['regions']) if r.get('packed') is not None}
    qualified, total = [], 0
    for record in records:
        header = record['header']
        assert record['symbol'] == expected[header]['symbol'] + '_funded'
        assert record['native_calls'] == 0 and record['caller_instructions'] > 0
        assert record['active_tag'] == bounds[header]['active_tag']
        assert invariant[header]['fixed_template_work'] == bounds[header]['fixed_template_instructions'] <= 1024
        assert 0 < record['entry_instructions'] <= 512
        assert 0 < record['maximum_source_instructions'] <= 512
        assert 0 < record['maximum_snapshot_instructions'] <= 512
        assert record['code_bytes'] > 0 and record['stack_bytes'] >= 0
        assert record['cleanup']['enabled'] is True and record['cleanup']['pre_codegen_data_passes'] == pre_data_passes
        stride = lookup[header]['source_nodes']
        assert 0 < stride <= 256
        nodes = dict(record['source_nodes'])
        assert len(nodes) == len(record['source_nodes']) and nodes
        assert record['active_node'] in nodes and nodes[record['active_node']] == header
        for node, site in nodes.items():
            assert type(node) is int and 0 <= node < stride
            assert type(site) is int and 0 <= site < len(closed['sites'])
            assert closed['sites'][site] == owners[header], 'Steady node belongs to another source region'
        assert set(record['present_nodes']) <= set(nodes)
        max_words = descriptor['map_owner_words']['frame_words']
        def live(words):
            assert words == sorted(set(words)) and all(type(w) is int and 0 <= w < max_words for w in words)
        live(record['entry_words'])
        assert bounds[header]['index_word'] in record['entry_words']
        if specialize_widths:
            assert record['specialized_widths'] == list(range(1, 19)), 'Width versions differ from the complete private storage domain'
            total += len(record['specialized_widths'])
        if fuel_edge_checks:
            checks = record['fuel_check_edges']
            assert checks.count(None) == 1 and len(checks) >= 2
            assert len(checks) == len(set(checks))
            assert all(node is None or node in nodes for node in checks)
            assert 0 < record['maximum_fuel_check_instructions'] <= record['maximum_source_instructions']
            total += len(checks)
        if productive_entry:
            assert record['entry_stop_index_word'] == bounds[header]['index_word']
            assert record['entry_stop_endpoint_words'] == [bounds[header]['width_word'], bounds[header]['limit_word']]
        if separate_header_snapshots:
            assert record['header_snapshot_edges'] == record['fuel_check_edges'], 'Cold snapshots do not cover the exact incoming source edges'
            total += len(record['header_snapshot_edges'])
        if peeled_entry_probes:
            fresh = {item['node'] % stride for item in lookup[header]['substitutions']
                     if item['operation'] == 3 and item['fact'] == 'Fresh'}
            expected_peeled = sorted((fresh & set(nodes)) - set(record['present_nodes']))
            assert expected_peeled and record['peeled_probe_nodes'] == expected_peeled, 'Direct-entry probes do not match the actual fresh source memberships'
            total += len(record['peeled_probe_nodes'])
        if prepaid_extent:
            assert record['prepaid_stop_edges'] == sorted(node for node in record['fuel_check_edges'] if node is not None), 'Prepaid extent does not cover every original completed source recurrence'
            assert record['fuel_reconstructed_at_exits'] is True
            total += len(record['prepaid_stop_edges'])
        if caller_prepaid_extent:
            assert prepaid_extent and record['prepaid_extent_arguments'] == 2
        if affine_cursor:
            assert caller_prepaid_extent
            assert record['cursor_range_site'] == bounds[header]['range_site']
            assert record['cursor_index_word'] == bounds[header]['index_word']
            assert record['cursor_recurrence_edges'] == record['prepaid_stop_edges']
            total += len(record['cursor_recurrence_edges']) + 2
        if preserve_entry_inputs:
            preserved = record['preserved_entry_words']
            live(preserved)
            assert set(preserved) <= set(record['entry_words'])
            assert bounds[header]['index_word'] not in preserved
            total += len(preserved)
        continuations = record['continuations']
        assert continuations and len({row[0] for row in continuations}) == len(continuations)
        for code, site, words in continuations:
            assert type(code) is int and 1 <= code <= stride + 1
            if site is None:
                assert code == stride + 1
            else:
                assert nodes[code - 1] == site, 'Continuation differs from its exact original source node'
            live(words)
        total += len(nodes) + sum(len(row[2]) for row in continuations)
        assert total <= 4096
        qualified.append(dict(header=header, source_region=owners[header], source_nodes=len(nodes),
            active_node=record['active_node'], native_calls=0, continuations=len(continuations),
            caller_instructions=record['caller_instructions'], fixed_template_work=invariant[header]['fixed_template_work'],
            scope='Actual native emission metadata bound to the original guarded source graph and live continuation words. Full liveness/presence proofs and machine-code helper absence are checked by compiler tests and separate disassembly; no dynamic entry count is claimed.'))
    return qualified


parser = argparse.ArgumentParser()
parser.add_argument('--compiler', required=True)
parser.add_argument('--reuse-build-receipt', help='Reuse an owned completed build from a pinned failed qualification attempt; never reuse timing observations')
parser.add_argument('--source-variant', help='Explicit candidate Mech source, relative to this study directory; the unchanged parent remains separately pinned')
parser.add_argument('--source-variant-sha256', help='Required exact SHA-256 for an explicitly changed candidate source')
parser.add_argument('--parent-receipt', required=True)
parser.add_argument('--parent-binary', required=True)
parser.add_argument('--binary', required=True)
parser.add_argument('--package', required=True)
parser.add_argument('--work-policy', required=True, type=int)
parser.add_argument('--receipt', required=True)
parser.add_argument('--minimum-closed-map-regions', type=int, default=0)
parser.add_argument('--allow-equal-admissions', action='store_true',
                    help='For improvements inside an already selected closed loop; still reject more admissions')
parser.add_argument('--require-packed-map', action='store_true',
                    help='Require every candidate execution to select packed storage for all regions and updates')
parser.add_argument('--require-packed-ssa', action='store_true',
                    help='Require all seven candidate regions to complete in generated SSA loops')
parser.add_argument('--require-key-bits', type=int, choices=range(1, 8),
                    help='Require every closed map to use this source-derived injective character bit width; also require packed storage and SSA')
parser.add_argument('--require-parallel-tasks', type=int, choices=[7],
                    help='Require one combined batch, two source regions and seven tasks; also require packed storage and SSA')
parser.add_argument('--minimum-parallel-peak', type=int,
                    help='Minimum observed simultaneous workers (1–7; defaults to 1 when parallel tasks are required)')
parser.add_argument('--minimum-edge-guards', type=int, default=0,
                    help='Minimum actual field-guard substitutions in each compiled packed map region')
parser.add_argument('--minimum-edge-arithmetic', type=int, default=0,
                    help='Minimum actual checked-arithmetic substitutions in each compiled packed map region')
parser.add_argument('--minimum-tag-branches', type=int, default=0,
                    help='Minimum actual folded branches in each compiled state-specialized map entry')
parser.add_argument('--minimum-tag-latches', type=int, default=0,
                    help='Minimum actual known-state latch routes in each compiled map entry')
parser.add_argument('--require-frame-effects', action='store_true',
                    help='Require exact narrow frame synchronization for every compiled packed-map helper')
parser.add_argument('--require-guarded-loops', action='store_true',
                    help='Require source-qualified guarded versions and seven actual runtime selections; also require packed storage, SSA and tag metadata')
parser.add_argument('--require-frozen-maps', action='store_true',
                    help='Require source-qualified private maps, five actual retained maps and ten original source queries')
parser.add_argument('--require-lookup-facts', action='store_true',
                    help='Require exact-source current-key substitutions in both emitted packed regions')
parser.add_argument('--require-cfg-cleanup', action='store_true',
                    help='Require bounded constant-branch cleanup in the exact emitted native function')
parser.add_argument('--require-outlined-loops', action='store_true',
                    help='Require source-bound local native functions for every emitted packed loop')
parser.add_argument('--require-preserving-calls', action='store_true', help='Require source-bound preserving bridge calls and included nested stack/code')
parser.add_argument('--require-mutation-facts', action='store_true', help='Require guarded source progress and completed-insertion storage facts')
parser.add_argument('--require-count-values', action='store_true', help='Require source-qualified count-value overflow substitutions')
parser.add_argument('--require-header-cache', action='store_true', help='Require proof-gated private lookup-cache invalidation at every emitted header')
parser.add_argument('--require-lookup-threading', action='store_true', help='Require source-bound present/absent continuations at original insertion joins')
parser.add_argument('--require-loop-constants', action='store_true', help='Require owned caller storage for immutable hashes and source loop endpoints')
parser.add_argument('--require-steady-loops', action='store_true', help='Require source-bound helper-free funded functions and precise cold continuations')
parser.add_argument('--require-loop-invariants', action='store_true',
                    help='Require source-bound guarded calls, steady rolling and seven actual initial call-guard selections')
args = parser.parse_args()
if bool(args.source_variant) != bool(args.source_variant_sha256):
    parser.error('--source-variant and --source-variant-sha256 must be supplied together')
if min(args.minimum_edge_guards, args.minimum_edge_arithmetic, args.minimum_tag_branches, args.minimum_tag_latches) < 0:
    parser.error('Emission receipt requirements must be nonnegative')
if args.minimum_parallel_peak is not None and (
        args.require_parallel_tasks is None or not 1 <= args.minimum_parallel_peak <= args.require_parallel_tasks):
    parser.error('--minimum-parallel-peak requires --require-parallel-tasks 7 and a value from 1 to 7')
minimum_parallel_peak = (args.minimum_parallel_peak or 1) if args.require_parallel_tasks else None
require_edge_emissions = bool(args.minimum_edge_guards or args.minimum_edge_arithmetic)
require_tag_emissions = bool(args.minimum_tag_branches or args.minimum_tag_latches or args.require_guarded_loops or args.require_lookup_facts)
require_packed_map = args.require_packed_map or args.require_parallel_tasks is not None or args.require_key_bits is not None or require_edge_emissions or require_tag_emissions or args.require_frame_effects or args.require_frozen_maps
require_packed_ssa = args.require_packed_ssa or args.require_parallel_tasks is not None or args.require_key_bits is not None or require_edge_emissions or require_tag_emissions or args.require_frame_effects or args.require_frozen_maps
out = HERE / args.receipt
out.mkdir(exist_ok=False)
prepared = json.loads((HERE / args.compiler / 'results.json').read_text())
parent = json.loads((HERE / args.parent_receipt / 'results.json').read_text())
assert prepared['status'] == 'compiler-built'
assert parent['status'] == 'all-outputs-and-update-counts-verified'
assert subprocess.check_output(['git', '-C', str(WORKSPACE), 'rev-parse', 'HEAD'], text=True).strip() == prepared['source_commit']
assert not subprocess.check_output(['git', '-C', str(WORKSPACE), 'status', '--porcelain'])
env = prepared['environment']
cli = HERE / '.build/mech-canonical'
assert process.sha(cli) == prepared['compiler_sha256']
original_source = HERE / 'knucleotide-source-map.mec'
assert process.sha(original_source) == parent['source_sha256'] == 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
source = HERE / args.source_variant if args.source_variant else original_source
if args.source_variant:
    assert process.sha(source) == args.source_variant_sha256
else:
    assert process.sha(source) == parent['source_sha256']
targets = dict(candidate=HERE / '.build' / args.binary,
               baseline=HERE / '.build' / args.parent_binary,
               rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
if args.reuse_build_receipt:
    previous_build = HERE / args.reuse_build_receipt
    previous = json.loads((previous_build / 'results.json').read_text())
    built = json.loads((previous_build / 'build/process.json').read_text())
    assert built['exit_status'] == 0 and built['reaped'] and built['group_closed'] and not built['cleanup_errors']
    assert previous['source_commit'] == prepared['source_commit']
    assert previous['source_sha256'] == process.sha(source) == process.sha(previous_build / 'candidate.mec')
    assert previous['configuration']['compiler'] == args.compiler
    assert previous['configuration']['binary'] == args.binary and previous['configuration']['package'] == args.package
    assert process.sha(targets['candidate']) == previous['candidate_sha256']
else:
    assert not targets['candidate'].exists()
assert process.sha(targets['baseline']) == parent['candidate_sha256']
assert process.sha(targets['rust']) == parent['rust_sha256'] == 'f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763'
inp = HERE / 'rust-span-diagnostic-v2/input.fasta'
assert process.sha(inp) == 'e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb'
policy = HERE / 'full-timing-v1/launch.json'
assert process.sha(policy) == '3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec'
expected = (HERE / 'rust-span-diagnostic-v2/expected.txt').read_bytes()
report = dict(status='building', source_commit=prepared['source_commit'],
              baseline_source_commit=parent['source_commit'],
              source_sha256=process.sha(source), baseline_source_sha256=parent['source_sha256'],
              source_comparison='explicit-source-variant' if args.source_variant else 'unchanged-source',
              input_sha256=process.sha(inp),
              launch_sha256=process.sha(policy), baseline_sha256=process.sha(targets['baseline']),
              rust_sha256=process.sha(targets['rust']), input_bases=1000000,
              expected_table_updates=6999961, samples=[], configuration=vars(args),
              require_packed_map=require_packed_map, require_packed_ssa=require_packed_ssa,
              require_key_bits=args.require_key_bits,
              require_guarded_loops=args.require_guarded_loops,
              require_frozen_maps=args.require_frozen_maps,
              require_lookup_facts=args.require_lookup_facts,
              require_cfg_cleanup=args.require_cfg_cleanup,
              require_outlined_loops=args.require_outlined_loops,
              require_loop_invariants=args.require_loop_invariants,
              require_preserving_calls=args.require_preserving_calls,
              require_mutation_facts=args.require_mutation_facts,
              require_count_values=args.require_count_values,
              require_header_cache=args.require_header_cache,
              require_lookup_threading=args.require_lookup_threading,
              require_loop_constants=args.require_loop_constants,
              require_steady_loops=args.require_steady_loops,
              require_parallel_tasks=args.require_parallel_tasks, minimum_parallel_peak=minimum_parallel_peak,
              native_executions=[],
              scope='One-million-base standard THREE prefix; complete fresh processes; secured Mech AOT; diagnostic only')
process.save(out / 'results.json', report)
(out / 'candidate.mec').write_bytes(source.read_bytes())
report['study_driver_sha256'] = process.sha(Path(__file__))
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    command = [str(cli), '--no-config', 'build', str(source), '--backend', 'cranelift',
               '--profile', 'release', '--keep-project', '--offline', '--workspace-root',
               str(WORKSPACE), '--name', args.package, '-o', str(targets['candidate'])]
    if args.reuse_build_receipt:
        process.save(out / 'reused-build.json', dict(receipt=args.reuse_build_receipt,
                     source_results_sha256=process.sha(previous_build / 'results.json'),
                     process_receipt_sha256=process.sha(previous_build / 'build/process.json'),
                     executable_sha256=process.sha(targets['candidate']), timing_observations_reused=0))
    else:
        result = process.execute(command, out / 'build', env, lock, deadline=1800)
        assert result['exit_status'] == 0, (out / 'build/stderr.bin').read_text()[-5000:]
    report['candidate_sha256'] = process.sha(targets['candidate'])
    project = Path(str(targets['candidate']) + '.project')
    report['bytecode_sha256'] = process.sha(project / 'program.mecb')
    report['baseline_bytecode_sha256'] = process.sha(Path(str(targets['baseline']) + '.project/program.mecb'))
    report['same_bytecode_as_baseline'] = report['bytecode_sha256'] == report['baseline_bytecode_sha256']
    assert report['baseline_bytecode_sha256'] == '050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0'
    if not args.source_variant:
        assert report['same_bytecode_as_baseline']
    process.save(out / 'results.json', report)
    manifest = json.loads((project / 'linked-manifest.json').read_text())
    assert manifest['object']['work_policy_version'] == args.work_policy
    report['native_admission_groups'] = manifest['object']['retained_map_scalar_admission_groups']
    descriptor = json.loads((project / 'native-descriptor.json').read_text())['descriptor']
    if args.require_frame_effects:
        assert manifest['object']['abi_version'] in (24, 25, 26, 27), 'Frame-effect masks require the audited ABI24–27 Frame'
        report['compiled_frame_effects'] = manifest['object'].get('compiled_frame_effects')
        report['qualified_frame_regions'] = require_frame_effects(report['compiled_frame_effects'], descriptor)
        report['source_frame_effects_qualified'] = True
        report['object_sha256'] = process.sha(project / 'program.o')
        report['linked_manifest_sha256'] = process.sha(project / 'linked-manifest.json')
    if require_tag_emissions:
        report['compiled_tag_threading'] = manifest['object'].get('compiled_tag_threading')
        report['qualified_tag_regions'] = require_tag_threading(
            report['compiled_tag_threading'], descriptor,
            args.minimum_tag_branches, args.minimum_tag_latches)
        report['source_tag_threading_qualified'] = True
        report['object_sha256'] = process.sha(project / 'program.o')
        report['linked_manifest_sha256'] = process.sha(project / 'linked-manifest.json')
    if args.require_guarded_loops:
        report['compiled_guarded_loops'] = manifest['object'].get('compiled_guarded_loops')
        report['qualified_guarded_regions'] = require_guarded_loops(
            report['compiled_guarded_loops'], descriptor, report['compiled_tag_threading'],
            manifest['object'].get('compiled_loop_invariants', []))
        report['source_guarded_loops_qualified'] = True
        report['object_sha256'] = process.sha(project / 'program.o')
        report['linked_manifest_sha256'] = process.sha(project / 'linked-manifest.json')
    if args.require_frozen_maps:
        assert manifest['object']['abi_version'] in (26, 27) and manifest['object']['work_policy_version'] == 65
        report['frozen_map_layout'] = descriptor['frozen_maps']
        report['qualified_frozen_regions'] = require_frozen_maps(
            manifest['object'].get('private_frozen_map_candidates'), descriptor)
        report['source_frozen_maps_qualified'] = True
        report['object_sha256'] = process.sha(project / 'program.o')
        report['linked_manifest_sha256'] = process.sha(project / 'linked-manifest.json')
    if args.require_lookup_facts:
        assert manifest['object']['typed_ir_version'] in (50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74) and manifest['object']['work_policy_version'] == 65
        report['compiled_lookup_facts'] = manifest['object'].get('compiled_lookup_facts')
        report['qualified_lookup_regions'] = require_lookup_facts(report['compiled_lookup_facts'], descriptor,
                                                                  manifest['object'].get('compiled_tag_threading'), bool(args.source_variant))
        report['source_lookup_facts_qualified'] = True
        report['object_sha256'] = process.sha(project / 'program.o')
        report['linked_manifest_sha256'] = process.sha(project / 'linked-manifest.json')
    if args.require_lookup_threading:
        assert args.require_lookup_facts and manifest['object']['typed_ir_version'] == 63
        report['qualified_lookup_thread_regions'] = require_lookup_threading(report['compiled_lookup_facts'], descriptor)
        report['lookup_threading_qualified'] = True
    if args.require_cfg_cleanup:
        assert manifest['object']['typed_ir_version'] in (51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74) and manifest['object']['work_policy_version'] == 65
        cleanup = manifest['object'].get('compiled_cfg_cleanup')
        assert isinstance(cleanup, dict) and cleanup['enabled'] is True
        assert type(cleanup['rounds']) is int and 1 <= cleanup['rounds'] <= 8
        assert type(cleanup['constant_branches_removed']) is int and cleanup['constant_branches_removed'] >= 0
        assert type(cleanup['fixed_point']) is bool
        for key in ('before_blocks', 'before_instructions', 'after_blocks', 'after_instructions'):
            assert type(cleanup[key]) is int and cleanup[key] > 0
        report['compiled_cfg_cleanup'] = cleanup
        report['cfg_cleanup_qualified'] = True
        report['object_sha256'] = process.sha(project / 'program.o')
        report['linked_manifest_sha256'] = process.sha(project / 'linked-manifest.json')
    if args.require_outlined_loops:
        assert args.require_cfg_cleanup and args.require_lookup_facts
        assert manifest['object']['typed_ir_version'] in (52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74)
        loops = manifest['object'].get('compiled_outlined_loops')
        assert isinstance(loops, list) and 0 < len(loops) <= 256
        expected_headers = {region['header'] for region in report['qualified_lookup_regions']}
        assert len(loops) == len(expected_headers) and {loop['header'] for loop in loops} == expected_headers
        for loop in loops:
            assert loop['symbol'] == f"mech_canonical_program_entry_v1_packed_loop_{loop['header']}"
            assert loop['caller_template_bound'] == 64
            assert type(loop['stack_bytes']) is int and 0 <= loop['stack_bytes'] <= manifest['object']['stack_bytes']
            assert type(loop['code_bytes']) is int and 0 < loop['code_bytes'] < manifest['object']['code_bytes']
            cleanup = loop['cleanup']
            assert cleanup['enabled'] is True and type(cleanup['rounds']) is int and 1 <= cleanup['rounds'] <= 8
            assert type(cleanup['constant_branches_removed']) is int and cleanup['constant_branches_removed'] > 0
        assert sum(loop['code_bytes'] for loop in loops) < manifest['object']['code_bytes']
        report['compiled_outlined_loops'] = loops
        report['outlined_loops_qualified'] = True
    if args.require_cfg_cleanup:
        removed = report['compiled_cfg_cleanup']['constant_branches_removed'] + sum(
            loop['cleanup']['constant_branches_removed'] for loop in report.get('compiled_outlined_loops', []))
        assert removed > 0, 'No actual constant branch was removed in the qualified emitted functions'
        report['cfg_cleanup_removed_total'] = removed
        if manifest['object']['typed_ir_version'] in (54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74):
            functions = [report['compiled_cfg_cleanup']] + [loop['cleanup'] for loop in report.get('compiled_outlined_loops', [])]
            assert all(function['pre_codegen_data_passes'] == 0 for function in functions)
            report['single_data_pass_qualified'] = True

    if args.require_loop_invariants:
        assert args.require_outlined_loops and args.require_guarded_loops and args.require_lookup_facts
        assert manifest['object']['typed_ir_version'] in (53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74) and manifest['object']['abi_version'] == 27
        report['compiled_loop_invariants'] = manifest['object'].get('compiled_loop_invariants')
        report['qualified_invariant_regions'] = require_loop_invariants(report['compiled_loop_invariants'], descriptor,
            report['qualified_lookup_regions'], report['qualified_guarded_regions'])
        report['loop_invariants_qualified'] = True
    if args.require_preserving_calls:
        assert args.require_loop_invariants and args.require_outlined_loops
        assert manifest['object']['typed_ir_version'] in (55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74) and manifest['object']['abi_version'] == 27
        shim = manifest['object'].get('compiled_bound_call_shim')
        regions = manifest['object'].get('compiled_preserving_call_regions')
        assert isinstance(shim, dict) and shim['symbol'] == 'mech_canonical_program_entry_v1_preserving_bound_call'
        assert shim['template_bound'] == 128 and 0 < shim['code_bytes'] <= 4 * 128
        assert 16 <= shim['stack_bytes'] < manifest['object']['stack_bytes']
        assert isinstance(regions, list) and len(regions) == len(report['compiled_outlined_loops'])
        by_header = {r['header']: r for r in regions}
        assert len(by_header) == len(regions)
        for loop in report['compiled_outlined_loops']:
            region = by_header[loop['header']]
            assert region['emitted_calls'] > 0 and 0 < region['maximum_source_template_work'] <= 512
            assert region['extra_entry_work'] == 128
            assert loop['stack_bytes'] + shim['stack_bytes'] + 16 <= manifest['object']['stack_bytes']
        assert sum(loop['code_bytes'] for loop in report['compiled_outlined_loops']) + shim['code_bytes'] < manifest['object']['code_bytes']
        report['compiled_bound_call_shim'] = shim
        report['compiled_preserving_call_regions'] = regions
        report['preserving_calls_qualified'] = True
    if args.require_mutation_facts:
        assert args.require_loop_invariants and args.require_guarded_loops and args.require_lookup_facts
        assert manifest['object']['typed_ir_version'] in (58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74) and manifest['object']['abi_version'] == 27
        report['compiled_mutation_loops'] = manifest['object'].get('compiled_mutation_loops')
        report['qualified_mutation_regions'] = require_mutation_facts(report['compiled_mutation_loops'], descriptor,
            manifest['object']['compiled_tag_threading'], report['qualified_guarded_regions'],
            report['compiled_lookup_facts'], report['compiled_loop_invariants'])
        report['mutation_facts_qualified'] = True
    if args.require_count_values:
        assert args.require_mutation_facts and args.require_guarded_loops and args.require_loop_invariants
        assert manifest['object']['typed_ir_version'] in (59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74) and manifest['object']['abi_version'] == 27
        report['compiled_count_value_loops'] = manifest['object'].get('compiled_count_value_loops')
        report['qualified_count_value_regions'] = require_count_values(
            report['compiled_count_value_loops'], descriptor, report['compiled_mutation_loops'])
        report['count_values_qualified'] = True
    if args.require_header_cache:
        assert args.require_lookup_facts
        assert manifest['object']['typed_ir_version'] == 61 and manifest['object']['abi_version'] == 27
        report['compiled_header_cache_loops'] = manifest['object'].get('compiled_header_cache_loops')
        report['qualified_header_cache_regions'] = require_header_cache(report['compiled_header_cache_loops'],
            descriptor, report['compiled_tag_threading'], report['compiled_lookup_facts'])
        report['header_cache_qualified'] = True
    if args.require_loop_constants:
        assert args.require_outlined_loops and args.require_guarded_loops
        assert manifest['object']['typed_ir_version'] in (62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74) and manifest['object']['abi_version'] == 27
        report['compiled_loop_constants'] = manifest['object'].get('compiled_loop_constants')
        report['qualified_loop_constant_regions'] = require_loop_constants(report['compiled_loop_constants'],
            report['compiled_outlined_loops'], report['compiled_guarded_loops'], descriptor, manifest['object']['stack_bytes'])
        report['loop_constants_qualified'] = True
    if args.require_steady_loops:
        assert args.require_loop_constants and args.require_count_values and args.require_loop_invariants
        assert manifest['object']['typed_ir_version'] in (64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74) and manifest['object']['abi_version'] == 27
        report['compiled_steady_loops'] = manifest['object'].get('compiled_steady_loops')
        report['qualified_steady_regions'] = require_steady_loops(report['compiled_steady_loops'], descriptor,
            report['compiled_outlined_loops'], report['compiled_guarded_loops'], report['compiled_loop_invariants'], report['compiled_lookup_facts'],
            pre_data_passes=int(manifest['object']['typed_ir_version'] >= 65),
            preserve_entry_inputs=manifest['object']['typed_ir_version'] == 66,
            specialize_widths=manifest['object']['typed_ir_version'] in (67, 68, 69, 70, 71, 72, 73, 74),
            fuel_edge_checks=manifest['object']['typed_ir_version'] in (68, 69, 70, 71, 72, 73, 74),
            productive_entry=manifest['object']['typed_ir_version'] in (69, 70, 71, 72, 73, 74),
            separate_header_snapshots=manifest['object']['typed_ir_version'] in (70, 71, 72, 73, 74),
            peeled_entry_probes=manifest['object']['typed_ir_version'] in (71, 72, 73, 74),
            prepaid_extent=manifest['object']['typed_ir_version'] in (72, 73, 74),
            caller_prepaid_extent=manifest['object']['typed_ir_version'] in (73, 74),
            affine_cursor=manifest['object']['typed_ir_version'] == 74)
        report['steady_loops_qualified'] = True
    if args.minimum_edge_guards or args.minimum_edge_arithmetic:
        report['compiled_source_edge_facts'] = manifest['object'].get('compiled_source_edge_facts')
        report['qualified_source_edge_regions'] = require_edge_facts(
            report['compiled_source_edge_facts'], descriptor,
            args.minimum_edge_guards, args.minimum_edge_arithmetic,
            {region['header'] for region in report.get('qualified_tag_regions', [])})
        report['source_edge_facts_qualified'] = True
        report['object_sha256'] = process.sha(project / 'program.o')
        report['linked_manifest_sha256'] = process.sha(project / 'linked-manifest.json')
    report['native_descriptor_sha256'] = process.sha(project / 'native-descriptor.json')
    report['closed_key_domains'] = closed_key_domains(descriptor)
    report['closed_map_regions'] = sum(region.get('map') is not None
                                      for region in descriptor['closed_tails']['regions'])
    assert report['closed_map_regions'] >= args.minimum_closed_map_regions
    process.save(out / 'results.json', report)
    if args.require_key_bits is not None:
        require_key_domains(report['closed_key_domains'], args.require_key_bits)
        report['source_key_domains_qualified'] = True
        process.save(out / 'results.json', report)

    def run(label, round_number, timed):
        name = f'{round_number}-{label}'
        command = [str(targets[label])]
        if label != 'rust':
            command += [str(policy), str(out / (name + '.report.json')), '--']
        result = process.execute(command, out / name, env, lock, stdin=inp, deadline=120, quantitative=timed)
        assert result['exit_status'] == 0, (out / name / 'stderr.bin').read_text()[-4000:]
        assert (out / name / 'stdout.bin').read_bytes() == expected
        if label != 'rust':
            native = json.loads((out / (name + '.report.json')).read_text())
            assert native['native_aot'] and not native['jit'] and not native['resident_body_evaluation']
            assert native['shutdown'] == 'completed'
            assert native['native_hash_table_regions'] == 7 and native['native_hash_table_updates'] == 6999961
            packed = dict(packed_map_regions=native.get('native_packed_map_regions'),
                          packed_map_updates=native.get('native_packed_map_updates'),
                          packed_ssa_regions=native.get('native_packed_ssa_regions'),
                          guarded_loop_regions=native.get('native_guarded_loop_regions'),
                          guarded_call_regions=native.get('native_guarded_call_regions'),
                          frozen_map_regions=native.get('native_frozen_map_regions'),
                          frozen_map_reads=native.get('native_frozen_map_reads'))
            parallel = dict(parallel_batches=native.get('native_parallel_batches'),
                            parallel_regions=native.get('native_parallel_regions'),
                            parallel_tasks=native.get('native_parallel_tasks'),
                            parallel_peak_workers=native.get('native_parallel_peak_workers'))
            report['native_executions'].append(dict(label=label, round=round_number,
                                                     timed=timed, native_visits=native['native_visits'],
                                                     **packed, **parallel))
            process.save(out / 'results.json', report)
            if label == 'candidate' and require_packed_map:
                assert packed['packed_map_regions'] == 7, 'Candidate fell back from packed map regions'
                assert packed['packed_map_updates'] == 6999961, 'Candidate did not complete every update in packed storage'
            if label == 'candidate' and require_packed_ssa:
                assert packed['packed_ssa_regions'] == 7, 'Candidate fell back from generated SSA loops'
            if label == 'candidate' and args.require_guarded_loops:
                assert packed['guarded_loop_regions'] == 7, 'Candidate did not select all seven guarded loop versions'
            if label == 'candidate' and args.require_loop_invariants:
                assert packed['guarded_call_regions'] == 7, 'Candidate did not select all seven guarded-call entries'
            if label == 'candidate' and args.require_frozen_maps:
                assert packed['frozen_map_regions'] == 5 and packed['frozen_map_reads'] == 10, 'Candidate did not retain five complete query maps and perform ten original reads'
            if label == 'candidate' and args.require_parallel_tasks:
                assert parallel['parallel_batches'] == 1, 'Candidate did not combine work into one batch'
                assert parallel['parallel_regions'] == 2, 'Candidate did not complete both source comprehensions in parallel'
                assert parallel['parallel_tasks'] == args.require_parallel_tasks, 'Candidate did not complete all seven parallel tasks'
                assert isinstance(parallel['parallel_peak_workers'], int) and minimum_parallel_peak <= parallel['parallel_peak_workers'] <= args.require_parallel_tasks, 'Candidate did not reach the required simultaneous worker count'
        if timed:
            row = dict(label=label, seconds=result['elapsed_seconds'], maximum_rss_bytes=result['maximum_rss_bytes'])
            report['samples'].append(row)
            process.save(out / 'results.json', report)
            print(json.dumps(row), flush=True)

    for label in targets:
        run(label, 'warmup', False)
    if args.minimum_closed_map_regions or args.require_parallel_tasks:
        candidate = json.loads((out / 'warmup-candidate.report.json').read_text())
        baseline = json.loads((out / 'warmup-baseline.report.json').read_text())
        if args.require_parallel_tasks:
            # Scheduling and original worker preludes add legitimate boundaries.
            # Actual receipts above prove the required execution strategy.
            report['admission_comparison'] = 'record-only: required parallel execution'
        elif args.allow_equal_admissions:
            assert candidate['native_visits'] <= baseline['native_visits'], 'The candidate added runtime admissions'
        else:
            assert candidate['native_visits'] < baseline['native_visits'], 'The new path did not reduce runtime admissions'
        report['warmup_native_visits'] = {label: native['native_visits']
                                         for label, native in [('candidate', candidate), ('baseline', baseline)]}
        process.save(out / 'results.json', report)
    for index, order in enumerate([['candidate', 'baseline', 'rust'], ['rust', 'baseline', 'candidate'], ['baseline', 'candidate', 'rust']]):
        for label in order:
            run(label, index, True)
report['median_seconds'] = {label: statistics.median(row['seconds'] for row in report['samples'] if row['label'] == label) for label in targets}
report['x_rust'] = {label: seconds / report['median_seconds']['rust'] for label, seconds in report['median_seconds'].items()}
report['denominator'] = 'Unmodified upstream Rust #7 on the same one-million-base input and machine'
report['status'] = 'all-outputs-and-update-counts-verified'
process.save(out / 'results.json', report)
print(json.dumps(report), flush=True)
