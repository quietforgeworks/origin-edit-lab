#!/usr/bin/env python3
"""Guard derived final execution coordinates, never workbench guide positions.

Workbench positions are nonbinding relationship hints. Derive this concrete plan
from approved relationships plus aesthetics before binding and checking it.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

EDGES = {'left', 'right', 'top', 'bottom', 'center_x', 'center_y', 'baseline'}
ROLES = {'plot_frame', 'panel_title', 'x_axis_title', 'y_axis_title', 'legend_title', 'other_title', 'panel_label', 'tick_label', 'condition_label', 'reference_label'}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def exact_keys(value, keys, name):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f'{name} has missing or unknown fields')


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def nonempty_text(value, limit=200):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit


def validate_anchor(anchor):
    exact_keys(anchor, {'panel', 'object', 'role', 'edge', 'basis', 'axis'}, 'Anchor')
    if not nonempty_text(anchor['panel']) or not nonempty_text(anchor['object']) or anchor['edge'] not in EDGES or anchor['role'] not in ROLES:
        raise ValueError('Anchor needs a panel, exact object, semantic role and supported edge')
    if anchor['axis'] not in {'x', 'y'}:
        raise ValueError('Anchor axis must be x or y in final slide coordinates')
    if anchor['edge'] in {'left', 'right', 'center_x'} and anchor['axis'] != 'x':
        raise ValueError('Left/right/center_x require the x coordinate')
    if anchor['edge'] in {'top', 'bottom', 'center_y'} and anchor['axis'] != 'y':
        raise ValueError('Top/bottom/center_y require the y coordinate')
    if anchor['role'] == 'plot_frame':
        if anchor['basis'] != 'stroke_outer' or anchor['edge'] == 'baseline':
            raise ValueError('Plot frame anchors use outer stroke geometry, not text baselines')
    elif anchor['edge'] == 'baseline':
        if anchor['basis'] != 'baseline':
            raise ValueError('Baseline anchors require an actual transformed text baseline')
    elif anchor['basis'] != 'ink':
        raise ValueError('Text edges and centers must use glyph ink, not a text box')
    return tuple(anchor[key] for key in ('panel', 'object', 'role', 'edge', 'basis', 'axis'))


def validate_plan(plan):
    exact_keys(plan, {'schema_version', 'plan_version', 'source_sha256', 'guides_sha256', 'alignments', 'questions'}, 'Plan')
    if type(plan['schema_version']) is not int or plan['schema_version'] != 1:
        raise ValueError('Unsupported plan schema version')
    if not nonempty_text(plan['plan_version'], 128):
        raise ValueError('Plan needs an explicit version')
    if not all(valid_hash(plan[key]) for key in ('source_sha256', 'guides_sha256')):
        raise ValueError('Plan needs source and presented guide SHA-256 hashes')
    if not isinstance(plan['questions'], list) or not all(nonempty_text(q, 2000) for q in plan['questions']):
        raise ValueError('Questions must be a list of unresolved clarification strings')
    if not isinstance(plan['alignments'], list) or not plan['alignments']:
        raise ValueError('Plan needs explicit alignment pairs')
    ids, targets = set(), set()
    anchor_coordinates = {}
    for item in plan['alignments']:
        exact_keys(item, {'id', 'reference', 'target', 'coordinate_pt', 'certainty'}, 'Alignment')
        if not nonempty_text(item['id']) or item['id'] in ids:
            raise ValueError('Alignment IDs must be unique and nonempty')
        ids.add(item['id'])
        reference = validate_anchor(item['reference'])
        target = validate_anchor(item['target'])
        if reference == target or target in targets:
            raise ValueError('Duplicate target or self-alignment')
        targets.add(target)
        if item['reference']['axis'] != item['target']['axis']:
            raise ValueError('Cannot align horizontal and vertical anchors')
        n = item['coordinate_pt']
        if type(n) not in {int, float} or not math.isfinite(n):
            raise ValueError('Alignment coordinate must be finite points')
        for anchor in (item['reference'], item['target']):
            key=tuple(anchor[k] for k in ('panel','object','edge','basis','axis'))
            if key in anchor_coordinates and anchor_coordinates[key] != n:
                raise ValueError('Conflicting derived coordinates for the same anchor')
            anchor_coordinates[key]=n
        if item['certainty'] not in {'clear', 'needs_confirmation'}:
            raise ValueError('Certainty must be clear or needs_confirmation')
    return plan


def plan_digest(plan):
    validate_plan(plan)
    return sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8'))


def alignment_bindings(plan):
    validate_plan(plan)
    return [{'id': item['id'], 'reference': dict(item['reference']), 'target': dict(item['target'])} for item in plan['alignments']]


def review_summary(plan):
    return {'status': 'review_required', 'plan_version': plan['plan_version'],
            'source_sha256': plan['source_sha256'], 'guides_sha256': plan['guides_sha256'],
            'plan_sha256': plan_digest(plan), 'alignments': alignment_bindings(plan),
            'questions': plan['questions'],
            'coordinate_policy': 'derived-final-plan-not-workbench-guide-positions',
            'note': 'Review alignment relationships and aesthetic scope; bind derived execution coordinates. This report is not approval.'}


def require_alignment_approval(source_bytes, guides_bytes, plan, approval):
    """Call before any alignment mutation; approval must come from actual user evidence."""
    validate_plan(plan)
    if plan['questions']:
        raise ValueError('Unresolved alignment questions must be answered before applying')
    if sha256(source_bytes) != plan['source_sha256'] or sha256(guides_bytes) != plan['guides_sha256']:
        raise ValueError('Source or bound final guide changed; regenerate execution binding and verify authorization scope')
    exact_keys(approval, {'decision', 'plan_version', 'source_sha256', 'guides_sha256', 'plan_sha256', 'alignments', 'user_confirmation'}, 'Approval')
    if approval['decision'] != 'approve' or not nonempty_text(approval['user_confirmation'], 4000):
        raise ValueError('Explicit user confirmation is required')
    for key in ('plan_version', 'source_sha256', 'guides_sha256'):
        if approval[key] != plan[key]:
            raise ValueError(f'Approval {key} does not match the reviewed plan')
    if approval['plan_sha256'] != plan_digest(plan):
        raise ValueError('Approval does not match the complete plan')
    if approval['alignments'] != alignment_bindings(plan):
        raise ValueError('Approval does not match the panel-edge bindings')
    return {'status': 'approved_binding_verified', 'plan_sha256': plan_digest(plan),
            'alignment_count': len(plan['alignments']), 'files_modified': False,
            'note': 'This verifies binding, not user identity. The caller must verify trusted user confirmation and perform guarded edits.'}


def read_json(path):
    if path.stat().st_size > 1024 * 1024:
        raise ValueError('JSON exceeds 1 MiB limit')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    inspect = sub.add_parser('inspect')
    inspect.add_argument('plan', type=Path)
    check = sub.add_parser('check')
    check.add_argument('plan', type=Path)
    check.add_argument('--source', required=True, type=Path)
    check.add_argument('--guides', required=True, type=Path)
    check.add_argument('--approval', required=True, type=Path)
    args = parser.parse_args()
    try:
        plan = read_json(args.plan)
        validate_plan(plan)
        if args.action == 'inspect':
            report = review_summary(plan)
        else:
            report = require_alignment_approval(args.source.read_bytes(), args.guides.read_bytes(), plan, read_json(args.approval))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print(json.dumps({'status': 'blocked_or_failed', 'error': str(error)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
