#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read-only diagnostics for source-verified semantic figure observations.

This does not extract observations, recognize an image, authenticate approvals,
edit a figure, or establish application reopen/save/refresh behavior.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import sys

SCHEMA_PATH = Path(__file__).with_name('figure_observations.schema.json')
MAX_INPUT_BYTES = 4 * 1024 * 1024
LIMITATIONS = [
    'Observations and their evidence references must be independently verified; hashes bind files, not the truth or completeness of supplied observations.',
    'No automatic image recognition, source extraction, source mutation, approval authentication, or application lifecycle testing is performed.',
    'Only text-involving collision pairs are checked; non-text occlusion (such as colorbar over map or inset over data) requires separate verified review.',
    'Bounding-box intersections are candidates only. A collision requires supplied reliable glyph/contour, mask, source-geometry, or manual intersection evidence.',
    'Marker semantics and complete layer/ancestor transforms must be source-verified; ellipse tags, path tags, or stroke visibility do not identify scientific roles.',
    'Directional ink gaps require independently observed ink/stroke anchors and task-specific tolerances; equal frame gaps do not prove equal visual clearance.',
    'Final-size glyph measurements must come from actual rendered ink or verified outlines, not nominal font sizes or unverified query bounds.',
    'Declared transforms and thresholds are task observations, not authorization; unchanged fingerprints prove only the declared semantic payloads.',
    'An unchanged source/candidate or intentional accessory does not establish scientific visibility; inherited occlusion still needs independent review.',
    'Passing checks is not whole-figure acceptance. Full-view review, source inventory completeness, guide reversibility, and application persistence require separate evidence.',
]

class InvalidObservation(ValueError):
    pass


def _pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise InvalidObservation('Duplicate JSON key: ' + k)
        out[k] = v
    return out


def load_json(path):
    p = Path(path)
    if p.stat().st_size > MAX_INPUT_BYTES:
        raise InvalidObservation('Observation JSON exceeds 4 MiB limit')
    return json.loads(p.read_text(encoding='utf-8'), object_pairs_hook=_pairs,
                      parse_constant=lambda v: (_ for _ in ()).throw(InvalidObservation('Nonfinite JSON number: ' + v)))


def _finite(value, path='$'):
    if isinstance(value, float) and not math.isfinite(value):
        raise InvalidObservation(path + ': number must be finite')
    if isinstance(value, dict):
        for k, v in value.items():
            _finite(v, path + '.' + k)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _finite(v, f'{path}[{i}]')


def validate_schema(value, schema, root=None, path='$'):
    """Validate the deliberately small JSON Schema subset used by the local schema.

    The schema is bundled/trusted, never obtained from the observation document.
    """
    root = root or schema
    if '$ref' in schema:
        return validate_schema(value, root['$defs'][schema['$ref'].split('/')[-1]], root, path)
    if 'anyOf' in schema:
        for choice in schema['anyOf']:
            try:
                validate_schema(value, choice, root, path)
                return
            except InvalidObservation:
                pass
        raise InvalidObservation(path + ': does not match a permitted schema type')
    typ = schema.get('type')
    types = {'object': dict, 'array': list, 'string': str, 'boolean': bool, 'null': type(None)}
    if typ in ('number', 'integer'):
        ok = not isinstance(value, bool) and isinstance(value, (float, int))
        if typ == 'integer':
            ok = ok and isinstance(value, int)
    else:
        ok = isinstance(value, types[typ]) if typ else True
    if not ok:
        raise InvalidObservation(f'{path}: expected {typ}')
    if 'const' in schema and value != schema['const']:
        raise InvalidObservation(path + ': wrong schema version/constant')
    if 'enum' in schema and value not in schema['enum']:
        raise InvalidObservation(path + ': value outside enum')
    if typ == 'object':
        missing = set(schema.get('required', [])) - set(value)
        extra = set(value) - set(schema.get('properties', {}))
        if missing or (extra and schema.get('additionalProperties') is False):
            raise InvalidObservation(f'{path}: missing={sorted(missing)}, unexpected={sorted(extra)}')
        for k, v in value.items():
            validate_schema(v, schema['properties'][k], root, path + '.' + k)
    elif typ == 'array':
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', float('inf')):
            raise InvalidObservation(path + ': invalid array length')
        if schema.get('uniqueItems') and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            raise InvalidObservation(path + ': duplicate array entries')
        for i, v in enumerate(value):
            validate_schema(v, schema['items'], root, f'{path}[{i}]')
    elif typ == 'string':
        if not schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', float('inf')):
            raise InvalidObservation(path + ': invalid string length')
        if 'minLength' in schema and not value.strip():
            raise InvalidObservation(path + ': evidence/string cannot be blank')
        if 'pattern' in schema and re.fullmatch(schema['pattern'], value) is None:
            raise InvalidObservation(path + ': invalid identifier/hash format')
    elif typ in ('number', 'integer'):
        if isinstance(value, float) and not math.isfinite(value):
            raise InvalidObservation(path + ': number must be finite')
        for key, bad in [('minimum', lambda b: value < b), ('maximum', lambda b: value > b),
                         ('exclusiveMinimum', lambda b: value <= b)]:
            if key in schema and bad(schema[key]):
                raise InvalidObservation(path + ': number outside permitted bounds')


def _index_unique(items, name):
    result = {}
    for item in items:
        if item['id'] in result:
            raise InvalidObservation('Duplicate ' + name + ' id: ' + item['id'])
        result[item['id']] = item
    return result


def validate_document(doc):
    _finite(doc)
    schema = json.loads(SCHEMA_PATH.read_text())
    validate_schema(doc, schema)
    elems = _index_unique(doc['elements'], 'element')
    anchors = _index_unique(doc['anchors'], 'anchor')
    _index_unique(doc['alignment_checks'], 'alignment')
    _index_unique(doc['selection_checks'], 'selection')
    def exists(eid):
        if eid not in elems:
            raise InvalidObservation('Unknown element reference: ' + str(eid))
    for e in elems.values():
        for field in ('parent_id', 'source_parent_id'):
            parent = e[field]
            if parent is not None:
                exists(parent)
                if parent == e['id']:
                    raise InvalidObservation('Self parent: ' + parent)
                if e['present' if field == 'parent_id' else 'source_present'] and not elems[parent]['present' if field == 'parent_id' else 'source_present']:
                    raise InvalidObservation('Present child under absent parent: ' + e['id'])
        if not e['present'] and not e['source_present']:
            raise InvalidObservation('Element absent in both source and candidate: ' + e['id'])
        for field in ('bbox', 'source_bbox', 'clip_bbox'):
            box = e[field]
            if box is not None and (box[2] <= 0 or box[3] <= 0):
                raise InvalidObservation(e['id'] + ': bbox width/height must be positive, even for visible strokes')
        if not e['present'] and any(e[k] is not None for k in ('bbox', 'glyph', 'transform', 'clip_bbox')):
            raise InvalidObservation('Absent candidate has final observations: ' + e['id'])
        kinds = [f['kind'] for f in e['fingerprints']]
        if len(kinds) != len(set(kinds)):
            raise InvalidObservation('Duplicate fingerprint kind: ' + e['id'])
        if e['glyph'] is not None and e['kind'] != 'text':
            raise InvalidObservation('Glyph metrics require text kind: ' + e['id'])
        if e['ownership'] is not None:
            own = e['ownership']
            if e['kind'] != 'text':
                raise InvalidObservation('Ownership check requires text kind')
            exists(own['frame_id'])
            if elems[own['frame_id']]['kind'] not in ('frame', 'image', 'panel'):
                raise InvalidObservation('Ownership must reference own frame/image/panel')
            if own['frame_id'] in own['neighbor_frame_ids']:
                raise InvalidObservation('Owner also listed as neighbor')
            for nid in own['neighbor_frame_ids']:
                exists(nid)
                if elems[nid]['kind'] not in ('frame', 'image', 'panel'):
                    raise InvalidObservation('Neighbor must reference frame/image/panel')
            lineage = set()
            p = e['parent_id']
            while p is not None and p not in lineage:
                lineage.add(p)
                p = elems[p]['parent_id']
            owner = elems[own['frame_id']]
            owner_panel = owner['id'] if owner['kind'] == 'panel' else owner['parent_id']
            if owner_panel is not None and owner_panel not in lineage:
                raise InvalidObservation('Ownership contradicts semantic parent: ' + e['id'])
        if e['scale_bar'] is not None:
            exists(e['scale_bar']['image_id'])
            if e['kind'] != 'scale_bar' or elems[e['scale_bar']['image_id']]['kind'] != 'image':
                raise InvalidObservation('Scale-bar relation must join scale_bar to image')
    for field in ('parent_id', 'source_parent_id'):
        for eid in elems:
            seen = set()
            p = eid
            while p is not None:
                if p in seen:
                    raise InvalidObservation('Cyclic ' + field + ': ' + eid)
                seen.add(p)
                p = elems[p][field]
    pairs = set()
    for c in doc['collision_checks']:
        exists(c['a']); exists(c['b'])
        key = tuple(sorted((c['a'], c['b'])))
        if c['a'] == c['b'] or key in pairs:
            raise InvalidObservation('Duplicate/self collision pair')
        pairs.add(key)
        if not any(elems[x]['kind'] == 'text' for x in key):
            raise InvalidObservation('Collision scope requires at least one text element')
        if c['method'] == 'bbox_only' and c['intersects'] is not None:
            raise InvalidObservation('A bbox-only observation cannot prove true/false ink intersection')
    for sel in doc['selection_checks']:
        exists(sel['owner_id'])
        for eid in sel['expected_ids'] + sel['selected_ids']:
            exists(eid)
        if sel['owner_id'] not in sel['expected_ids']:
            raise InvalidObservation('Selection expectation omits its owner')
    for a in anchors.values():
        exists(a['element_id'])
        expected_axis = 'x' if a['kind'] in ('left', 'right', 'center_x') else 'y'
        if a['kind'] != 'baseline' and a['axis'] != expected_axis:
            raise InvalidObservation('Anchor kind/axis mismatch: ' + a['id'])
        if (a['kind'] == 'baseline') != (a['basis'] == 'baseline'):
            raise InvalidObservation('Baseline anchors must use actual baseline basis')
        if a['basis'] == 'baseline' and elems[a['element_id']]['kind'] != 'text':
            raise InvalidObservation('Baseline anchor must belong to text')
    for c in doc['alignment_checks']:
        if len(c['anchor_ids']) != len(c['target_offsets_pt']) or c['target_offsets_pt'][0] != 0:
            raise InvalidObservation('Alignment offsets must match anchors and start at zero')
        if any(a not in anchors for a in c['anchor_ids']):
            raise InvalidObservation('Alignment references unknown anchor')
        aa = [anchors[a] for a in c['anchor_ids']]
        if len({a['axis'] for a in aa}) != 1:
            raise InvalidObservation('Alignment anchors must share one coordinate axis')
        if c['relationship'] == 'peer_layout' and any(elems[a['element_id']]['coordinate_space'] == 'data' for a in aa):
            raise InvalidObservation('Data-coordinate elements are not interchangeable layout peers')
    return elems, anchors


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _rect(b, width, height):
    return (b[0] * width, b[1] * height, (b[0] + b[2]) * width, (b[1] + b[3]) * height)


def _gap(a, b):
    return math.hypot(max(a[0] - b[2], b[0] - a[2], 0), max(a[1] - b[3], b[1] - a[3], 0))


def _overlap(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def _outside(a, b, tolerance):
    return any((a[0] < b[0] - tolerance, a[1] < b[1] - tolerance,
                a[2] > b[2] + tolerance, a[3] > b[3] + tolerance))


def _linear_metrics(matrix):
    a, b, c, d, tx, ty = matrix
    det = a * d - b * c
    trace = a*a + b*b + c*c + d*d
    disc = math.sqrt(max(0.0, trace * trace - 4 * det * det))
    hi = math.sqrt(max(0.0, (trace + disc) / 2))
    lo = abs(det) / hi if hi else 0.0
    return hi, lo, det


def check(doc, source, candidate):
    elems, anchors = validate_document(doc)
    actual_source, actual_candidate = sha256_file(source), sha256_file(candidate)
    if actual_source != doc['source_sha256']:
        raise InvalidObservation('Stale/mismatched source SHA-256; observations do not bind supplied source')
    if actual_candidate != doc['candidate_sha256']:
        raise InvalidObservation('Stale/mismatched candidate SHA-256; observations do not bind supplied candidate')
    width, height = doc['canvas']['width_pt'], doc['canvas']['height_pt']
    t = doc['thresholds']
    findings = []
    def add(code, status, ids, evidence, measurements=None, threshold=None, protected=False, method='supplied_semantic_observations'):
        findings.append(dict(code=code, status=status, element_ids=ids, evidence=evidence,
                             measurements=measurements or {}, threshold=threshold,
                             protected_fidelity=protected, method=method))
    add('file_bindings', 'pass', [], ['Actual source and candidate files hashed by this run'],
        {'source_sha256': actual_source, 'candidate_sha256': actual_candidate}, method='sha256_bytes')
    boxes = {eid: _rect(e['bbox'], width, height) for eid, e in elems.items() if e['present'] and e['bbox'] is not None}
    ink_basis = {'ink', 'stroke_outer', 'image_edge'}
    required_fp = {'text': 'text', 'axis': 'axes', 'tick': 'axes', 'curve': 'data', 'marker': 'data',
                   'image': 'content', 'roi': 'content', 'connector': 'association', 'scale_bar': 'association'}
    glyphs = defaultdict(list)
    for eid, e in elems.items():
        if e['source_present'] and not e['present']:
            add('source_content_removed', 'failure', [eid], [e['evidence']], protected=True)
        if not e['source_present']:
            add('new_content_requires_review', 'review_needed', [eid], [e['evidence']])
        if e['source_present'] and e['present']:
            add('semantic_parent', 'pass' if e['source_parent_id'] == e['parent_id'] else 'failure', [eid], [e['evidence']],
                {'source_parent_id': e['source_parent_id'], 'parent_id': e['parent_id']}, protected=True)
        fp = {f['kind']: f for f in e['fingerprints']}
        expected = required_fp.get(e['kind'])
        if e['source_present'] and expected is not None and expected not in fp:
            add('fingerprint_' + expected, 'unmeasured', [eid], [e['evidence']], protected=True)
        for name, f in fp.items():
            status = 'unmeasured' if f['before'] is None or f['after'] is None else ('pass' if f['before'] == f['after'] else 'failure')
            add('fingerprint_' + name, status, [eid], [f['evidence']], {'before': f['before'], 'after': f['after']}, protected=True, method='semantic_sha256_comparison')
        for axis in ('x', 'y'):
            status = {'measured': 'pass', 'unmeasured': 'unmeasured', 'not_applicable': 'not_applicable'}[e['coverage'][axis]]
            add('coverage_' + axis, status, [eid], [e['coverage']['reason']], method='source_verified_inventory_declaration')
        if not e['present']:
            continue
        if e['coordinate_space'] == 'unknown':
            add('scientific_role', 'unmeasured', [eid], [e['evidence']])
        if eid not in boxes:
            add('content_bounds', 'unmeasured', [eid], [e['evidence']])
        else:
            clip = _rect(e['clip_bbox'], width, height) if e['clip_bbox'] else (0, 0, width, height)
            outside = _outside(boxes[eid], (0, 0, width, height), t['geometry_tolerance_pt']) or _outside(boxes[eid], clip, t['geometry_tolerance_pt'])
            reliable = e['bbox_basis'] in ink_basis
            status = ('failure' if reliable else 'review_needed') if outside else ('pass' if reliable else 'unmeasured')
            add('content_bounds', status, [eid], [e['evidence']], {'bounds_pt': boxes[eid], 'clip_pt': clip, 'basis': e['bbox_basis']}, t['geometry_tolerance_pt'], protected=reliable and outside, method='full_unclipped_extent_vs_canvas_and_clip')
        tr = e['transform']
        if tr is None:
            add('transform', 'unmeasured', [eid], [e['evidence']])
        else:
            a, b, c, d, tx, ty = tr['matrix']
            hi, lo, det = _linear_metrics(tr['matrix'])
            if lo <= 1e-12:
                add('singular_transform', 'failure', [eid], [tr['evidence']], {'matrix': tr['matrix']}, protected=True)
            else:
                # Numerical operation classification is separate from visual, task-bound tolerance.
                eps = 1e-9
                operations = set()
                if abs(tx) > eps or abs(ty) > eps: operations.add('translate')
                if det < 0: operations.add('reflect')
                # QR convention: rotation follows the source x axis, followed by
                # axis scale and x shear. Pure x shear is not mislabeled rotation.
                sx = math.hypot(a, b)
                sy = abs(det) / sx
                if abs(b) > eps or a < -eps: operations.add('rotate')
                shear = abs(a*c + b*d) / (sx*sx)
                if shear > eps: operations.add('shear')
                if abs(sx - sy) > eps: operations.add('anisotropic_scale')
                elif abs(sx - 1) > eps: operations.add('uniform_scale')
                anisotropy = hi / lo - 1
                if not operations: operations.add('identity')
                unlisted = sorted(operations - set(tr['allowed']))
                add('allowed_transform', 'failure' if unlisted else 'pass', [eid], [tr['evidence']],
                    {'operations': sorted(operations), 'unlisted': unlisted, 'matrix': tr['matrix']}, protected=bool(unlisted))
                if e['kind'] in ('text', 'marker') or e['coordinate_space'] == 'measurement':
                    add('anisotropic_distortion', 'failure' if anisotropy > t['anisotropy_relative_tolerance'] else 'pass',
                        [eid], [tr['evidence']], {'singular_values': [hi, lo], 'relative_anisotropy': anisotropy},
                        t['anisotropy_relative_tolerance'], protected=True, method='source_to_final_linear_singular_values')
        if e['kind'] == 'text':
            if e['glyph'] is None:
                add('final_glyph_ink', 'unmeasured', [eid], [e['evidence']])
            else:
                g = e['glyph']
                glyphs[g['peer_group']].append(e)
                add('final_glyph_ink', 'pass', [eid], [g['evidence']], {'ink_height_pt': g['ink_height_pt'], 'role': e['role']}, method=g['method'])
        own = e['ownership']
        if e['role'] == 'panel_label' and own is None:
            add('label_ownership', 'unmeasured', [eid], [e['evidence']])
        if own is not None:
            ids = [eid, own['frame_id']] + own['neighbor_frame_ids']
            reliable = all(i in boxes and elems[i]['bbox_basis'] in ink_basis for i in ids)
            if not reliable:
                add('label_ownership', 'unmeasured', ids, [own['evidence']], method='verified_ink_to_frame_distance')
            else:
                own_gap = _gap(boxes[eid], boxes[own['frame_id']])
                neighbor = {n: _gap(boxes[eid], boxes[n]) for n in own['neighbor_frame_ids']}
                bad = own_gap > t['ownership_max_gap_pt'] or any(d - own_gap < t['ownership_neighbor_margin_pt'] for d in neighbor.values())
                add('label_ownership', 'failure' if bad else 'pass', ids, [own['evidence']],
                    {'owner_gap_pt': own_gap, 'neighbor_gaps_pt': neighbor},
                    {'max_gap_pt': t['ownership_max_gap_pt'], 'min_neighbor_advantage_pt': t['ownership_neighbor_margin_pt']}, method='verified_ink_to_frame_distance')
        ratio = e['scientific_ratio']
        if e['coordinate_space'] == 'measurement' and ratio is None:
            add('scientific_ratio', 'unmeasured', [eid], [e['evidence']], protected=True)
        if ratio is not None:
            delta = abs(ratio['final'] / ratio['source'] - 1)
            add('scientific_ratio', 'failure' if delta > t['ratio_relative_tolerance'] else 'pass', [eid], [ratio['evidence']],
                {'source': ratio['source'], 'final': ratio['final'], 'relative_change': delta}, t['ratio_relative_tolerance'], protected=True)
        bar = e['scale_bar']
        if e['kind'] == 'scale_bar' and bar is None:
            add('scale_bar_calibration', 'unmeasured', [eid], [e['evidence']], protected=True)
        if bar is not None:
            delta = abs(bar['final_fraction'] / bar['source_fraction'] - 1)
            label_changed = bar['source_value'] != bar['final_value'] or bar['source_unit'] != bar['final_unit']
            add('scale_bar_calibration', 'failure' if label_changed or delta > t['scale_bar_relative_tolerance'] else 'pass',
                [eid, bar['image_id']], [bar['evidence']], {'source_fraction': bar['source_fraction'], 'final_fraction': bar['final_fraction'], 'relative_change': delta, 'label_changed': label_changed}, t['scale_bar_relative_tolerance'], protected=True)
    for group, members in glyphs.items():
        keys = {(e['role'], e['glyph']['comparison_key'], e['glyph']['face'], e['glyph']['weight']) for e in members}
        if len(keys) != 1:
            raise InvalidObservation('Glyph peer group mixes unmatched role/glyph/font/weight: ' + group)
        heights = [e['glyph']['ink_height_pt'] for e in members]
        delta = max(heights) / min(heights) - 1
        status = 'not_applicable' if len(heights) < 2 else ('failure' if delta > t['glyph_relative_tolerance'] else 'pass')
        add('glyph_peer_size', status, [e['id'] for e in members], [e['glyph']['evidence'] for e in members],
            {'peer_group': group, 'min_pt': min(heights), 'max_pt': max(heights), 'relative_range': delta}, t['glyph_relative_tolerance'], method='matched_final_size_glyph_ink')
    collision_records = {tuple(sorted((c['a'], c['b']))): c for c in doc['collision_checks']}
    candidates = set(collision_records)
    ids = list(boxes)
    for i, a in enumerate(ids):
        for b in ids[i+1:]:
            if not any(elems[x]['kind'] == 'text' for x in (a,b)):
                continue
            if any(elems[x]['kind'] in ('panel', 'guide') for x in (a,b)):
                continue
            if _overlap(boxes[a], boxes[b]):
                candidates.add(tuple(sorted((a,b))))
    if len(candidates) > 10000:
        raise InvalidObservation('More than 10000 collision candidates; split the figure into bounded review records')
    for pair in sorted(candidates):
        c = collision_records.get(pair)
        if c is None:
            add('text_collision', 'review_needed', list(pair), [elems[x]['evidence'] for x in pair], method='bbox_candidate_only')
        elif c['exemption'] is not None:
            add('text_collision', 'exempt', list(pair), [c['evidence'], c['exemption']['evidence'], c['exemption']['reason']], method='explicit_intentional_overlap_observation')
        elif c['method'] == 'bbox_only' or c['intersects'] is None:
            add('text_collision', 'review_needed', list(pair), [c['evidence']], method='bbox_candidate_only' if c['method']=='bbox_only' else c['method'])
        else:
            add('text_collision', 'failure' if c['intersects'] else 'pass', list(pair), [c['evidence']], {'intersects': c['intersects']}, protected=bool(c['intersects']), method=c['method'])
    for sel in doc['selection_checks']:
        owner = sel['owner_id']
        required = {owner}
        for eid, e in elems.items():
            if not e['source_present'] or e['kind'] == 'connector':
                continue
            p = e['source_parent_id']
            while p is not None:
                if p == owner:
                    required.add(eid)
                p = elems[p]['source_parent_id']
        expected, selected = set(sel['expected_ids']), set(sel['selected_ids'])
        missing_inventory = sorted(required - expected)
        missing, unexpected = sorted(expected - selected), sorted(selected - expected)
        add('logical_selection', 'failure' if missing_inventory or missing or unexpected else 'pass', sorted(expected | selected), [sel['evidence']],
            {'selection_id': sel['id'], 'owner_id': owner, 'inventory_members_omitted': missing_inventory, 'expected_not_selected': missing, 'unexpected_selected': unexpected}, protected=True, method='source_semantic_membership_set_comparison')
    if not doc['selection_checks']:
        add('logical_selection', 'unmeasured', [], ['No selection observations supplied'])
    for c in doc['alignment_checks']:
        aa = [anchors[aid] for aid in c['anchor_ids']]
        values = [a['position_pt'] for a in aa]
        ids = [a['element_id'] for a in aa]
        evidence = [c['evidence']] + [a['evidence'] for a in aa]
        if any(v is None for v in values) or any(not elems[e]['present'] for e in ids):
            add('semantic_alignment', 'unmeasured', ids, evidence, {'constraint_id': c['id'], 'positions_pt': values}, c['tolerance_pt'], method='source_verified_semantic_anchors')
        else:
            residuals = [v - values[0] - target for v,target in zip(values, c['target_offsets_pt'])]
            bad = any(abs(r) > c['tolerance_pt'] for r in residuals)
            add('semantic_alignment', 'failure' if bad else 'pass', ids, evidence,
                {'constraint_id': c['id'], 'anchor_ids': c['anchor_ids'], 'positions_pt': values, 'observed_offsets_pt': [v - values[0] for v in values], 'target_offsets_pt': c['target_offsets_pt'], 'residuals_pt': residuals, 'axis': aa[0]['axis'], 'basis': [a['basis'] for a in aa]}, c['tolerance_pt'], method='source_verified_semantic_anchors')
    if not doc['alignment_checks']:
        add('semantic_alignment', 'unmeasured', [], ['No required semantic alignment constraints supplied'])
    counts = dict(Counter(f['status'] for f in findings))
    status = 'failure' if counts.get('failure') else ('review_needed' if counts.get('unmeasured') or counts.get('review_needed') else 'checks_passed')
    return dict(report_version=1, status=status, checked_source_sha256=actual_source, checked_candidate_sha256=actual_candidate,
                canvas=doc['canvas'], thresholds=t, counts=counts, findings=findings, limitations=LIMITATIONS)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('observations', help='Strict version-1 observation JSON')
    parser.add_argument('--source', required=True, help='Intact source file, read only')
    parser.add_argument('--candidate', required=True, help='Actual candidate file, read only')
    parser.add_argument('--output', help='New report path; refuses existing files and input-path aliases')
    args = parser.parse_args(argv)
    try:
        inputs = {Path(p).resolve() for p in (args.observations, args.source, args.candidate)}
        if args.output and Path(args.output).resolve() in inputs:
            raise InvalidObservation('Report path aliases an input; refusing to overwrite source/observations')
        if args.output and Path(args.output).exists():
            raise InvalidObservation('Report path already exists; use a new output name')
        doc = load_json(args.observations)
        report = check(doc, args.source, args.candidate)
        code = {'checks_passed': 0, 'failure': 1, 'review_needed': 3}[report['status']]
    except (InvalidObservation, OSError, ValueError, RecursionError) as exc:
        report = dict(report_version=1, status='invalid_input', error=str(exc), findings=[], limitations=LIMITATIONS)
        code = 2
    encoded = json.dumps(report, indent=2, allow_nan=False) + '\n'
    if args.output and code != 2:
        try:
            # Exclusive creation prevents races; never overwrite existing evidence.
            with open(args.output, 'x', encoding='utf-8') as handle:
                handle.write(encoded)
        except OSError as exc:
            report = dict(report_version=1, status='invalid_input', error='Cannot create report: ' + str(exc), findings=[], limitations=LIMITATIONS)
            encoded, code = json.dumps(report, indent=2) + '\n', 2
    sys.stdout.write(encoded)
    return code

if __name__ == '__main__':
    sys.exit(main())
