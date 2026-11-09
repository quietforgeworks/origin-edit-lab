"""Execute a separately reviewed byte plan; never infer Origin fields or semantics.

Changes contain integer byte values (0..255), not hex strings or ranges. This
validator establishes byte identity only. Scientific semantics are NOT VERIFIED.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

MAX_BYTES = 128 * 1024 * 1024
MAX_PLAN_BYTES = 16 * 1024 * 1024
MAX_CHANGES = 100000

class PatchError(ValueError):
    pass

def need(ok, message):
    if not ok:
        raise PatchError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def check_hash(value):
    need(isinstance(value, str) and re.fullmatch('[0-9a-fA-F]{64}', value), 'Invalid SHA-256')
    return value.lower()

def bounded_read(path, limit=MAX_BYTES):
    with Path(path).open('rb') as handle:
        data = handle.read(limit + 1)
    need(len(data) <= limit, 'Input exceeds byte limit')
    return data

def load_plan(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(bounded_read(path, MAX_PLAN_BYTES), object_pairs_hook=unique)

def patch_native(source, plan):
    need(isinstance(source, bytes) and 5 <= len(source) <= MAX_BYTES, 'Source size outside bounds')
    need(source.startswith(b'CPYUA'), 'Existing CPYUA source required')
    need(isinstance(plan, dict), 'Plan must be an object')
    required = {'source_sha256', 'candidate_sha256', 'changes'}
    allowed = required | {'source_bytes', 'candidate_bytes', 'changed_byte_count'}
    need(required <= plan.keys() and plan.keys() <= allowed, 'Missing or unknown plan fields')
    need(sha(source) == check_hash(plan['source_sha256']), 'Source SHA-256 mismatch')
    candidate_hash = check_hash(plan['candidate_sha256'])
    for key in ('source_bytes', 'candidate_bytes'):
        if key in plan:
            need(type(plan[key]) is int and plan[key] == len(source), 'Length must remain unchanged')
    changes = plan['changes']
    need(isinstance(changes, list) and 0 < len(changes) <= MAX_CHANGES, 'Change count outside bounds')
    declared = {}
    for change in changes:
        if isinstance(change, dict):
            need(set(change) == {'offset', 'old', 'new'}, 'Invalid change fields')
            offset, old, new = (change[k] for k in ('offset', 'old', 'new'))
        else:
            need(isinstance(change, list) and len(change) == 3, 'Invalid change record')
            offset, old, new = change
        need(all(type(v) is int for v in (offset, old, new)), 'Changes require integer bytes/offset')
        need(5 <= offset < len(source), 'Offset outside payload or touches CPYUA signature')
        need(0 <= old <= 255 and 0 <= new <= 255 and old != new, 'Invalid or unchanged byte')
        need(offset not in declared, 'Duplicate/overlapping changes')
        need(source[offset] == old, 'Old byte mismatch')
        declared[offset] = new
    if 'changed_byte_count' in plan:
        need(type(plan['changed_byte_count']) is int and plan['changed_byte_count'] == len(declared), 'Changed byte count mismatch')
    candidate = bytearray(source)
    for offset, value in declared.items():
        candidate[offset] = value
    candidate = bytes(candidate)
    need(sha(candidate) == candidate_hash, 'Candidate SHA-256 mismatch')
    need(len(candidate) == len(source), 'Candidate length changed')
    need(sum(a != b for a, b in zip(source, candidate)) == len(declared), 'Undeclared byte changes')
    return candidate, {'source_sha256': sha(source), 'candidate_sha256': sha(candidate),
                       'bytes': len(source), 'changed_byte_count': len(declared),
                       'scientific_semantics': 'NOT VERIFIED',
                       'preview_updated': False, 'host_transform_updated': False}

def write_new(path, data):
    # Exclusive creation also refuses symlinks and concurrent output creation.
    with Path(path).open('xb') as handle:
        handle.write(data)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    need(args.apply == bool(args.output), '--apply and --output must be used together')
    candidate, report = patch_native(bounded_read(args.input), load_plan(args.plan))
    if args.apply:
        write_new(args.output, candidate)
    report['mode'] = 'applied' if args.apply else 'dry-run'
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
