"""Recompute bounded source edits; never trust stored preservation flags.

This source-integrity audit is separate from the application's numerical and
Qt-point evidence. It is not independent evidence of Origin acceptance.
"""
from pathlib import Path
import json
import native_active_rows as patcher

def need(ok, message):
    if not ok:
        raise RuntimeError(message)

def exact_json(value):
    # Python equality alone conflates -0.0 with 0.0, and True with 1.
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

_ABSENT = object()

def verify_candidate(original, raw, candidate, manifest, before=_ABSENT, after=_ABSENT):
    expected, computed, expected_before, expected_after = patcher.patch_bytes(original, raw)
    need(candidate == expected, 'candidate differs from exact regenerated bounded edit')
    need(exact_json(manifest) == exact_json(computed), 'manifest differs from recomputed evidence')
    if before is not _ABSENT:
        need(exact_json(before) == exact_json(expected_before), 'before inspection differs from actual source')
    if after is not _ABSENT:
        need(exact_json(after) == exact_json(expected_after), 'after inspection differs from actual candidate')
    need(patcher.restore_bytes(candidate, manifest) == original, 'rollback is not byte-exact')
    return computed

def verify_hash_records(directory, expected):
    before = (directory / 'input.before.sha256').read_bytes()
    after = (directory / 'input.after.sha256').read_bytes()
    need(before == after, 'application source hash records differ')
    lines = before.decode('utf-8').splitlines()
    need(len(lines) == 1 and len(lines[0]) > 66, 'malformed input hash record')
    need(lines[0][:64] == patcher.sha(expected) and lines[0][64:66] in ('  ', ' *'),
         'recorded source hash is not the actual expected input hash')
    need((directory / 'source-evidence.opj').read_bytes() == expected,
         'application source snapshot differs from exact candidate')

def verify_case_source(root, count):
    root = Path(root)
    original_directory = root / 'application/results/original'
    original = (original_directory / 'source-evidence.opj').read_bytes()
    need(patcher.sha(original) == patcher.TEMPLATE_HASH, 'wrong original application fixture')
    generated = root / 'candidates' / f'generated{count}'
    candidate = (generated / 'candidate.opj').read_bytes()
    raw = (root / 'candidates' / f'raw{count}.csv').read_bytes()
    need((generated / 'raw.csv').read_bytes() == raw, 'generation and observed CSV differ')
    manifest = json.loads((generated / 'manifest.json').read_text())
    before = json.loads((generated / 'before.json').read_text())
    after = json.loads((generated / 'after.json').read_text())
    computed = verify_candidate(original, raw, candidate, manifest, before, after)
    need(computed['active_rows'] == count, 'source row count differs from case')
    need((generated / 'rollback.opj').read_bytes() == original, 'retained rollback differs')
    verify_hash_records(original_directory, original)
    verify_hash_records(root / 'application/results' / f'active{count}', candidate)
    return {
        'candidate_exactly_regenerated': True,
        'manifest_exactly_recomputed': True,
        'source_and_rollback_and_application_input_bit_exact': True,
        'allowed_byte_count': computed['allowed_byte_count'],
        'changed_byte_count': len(computed['changed_byte_offsets']),
        'preserved_byte_sha256': computed['preserved_byte_sha256'],
        'candidate_sha256': computed['candidate_sha256'],
        'native_graph_and_opaque_tail_bytes_unchanged': True,
        'semantic_validity_of_opaque_native_content': 'NOT ESTABLISHED',
    }

def verify_run_input(name, source, package_root):
    """The observer accepts only the pinned public fixture or this toy experiment."""
    source = Path(source)
    candidate = source.read_bytes()
    if name == 'original':
        need(patcher.sha(candidate) == patcher.TEMPLATE_HASH, 'original must be the pinned public fixture')
        return
    need(name in ('active7', 'active49', 'active50'), 'unknown observation case')
    count = int(name[6:])
    directory = source.parent
    original = (directory / 'rollback.opj').read_bytes()
    raw = (directory / 'raw.csv').read_bytes()
    need(raw == (Path(package_root) / 'candidates' / f'raw{count}.csv').read_bytes(),
         'observer input must use the published toy CSV')
    manifest = json.loads((directory / 'manifest.json').read_text())
    before = json.loads((directory / 'before.json').read_text())
    after = json.loads((directory / 'after.json').read_text())
    computed = verify_candidate(original, raw, candidate, manifest, before, after)
    need(computed['active_rows'] == count, 'observer case and candidate row count differ')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=('original', 'active7', 'active49', 'active50'))
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    verify_run_input(args.case, args.input, Path(__file__).resolve().parent)
