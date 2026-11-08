"""Read-only native verifier; explicit checks remain active under python -O.

Imports no generator/writer action. CSV validation is shared intentionally so
accepted encoding, shape, finite-value and zero semantics stay identical.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import bootstrap
from csv_contract import parse_csv, read_limited, MAX_CSV_BYTES
from writeback import AllocatedCFB, restore_delta
from modern_fpc_patch import parse_record
from modern_sparse_binding import read_modern_xy_bindings, _read_modern_xy_bindings_unscoped
from quantized.io.origin_project.opju_codec import _decode_record

ARTIFACT_NAMES = {'synthetic-demo.origin_payload', 'synthetic-demo.ole.bin',
                  'synthetic-demo.csv', 'native-restore-manifest.json',
                  'ole-restore-manifest.json', 'verification.json'}


class VerificationError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise VerificationError(message)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def verify(template, folder):
    template, folder = Path(template), Path(folder)
    source_bytes = read_limited(template, 51712)
    need(sha(source_bytes) == '25536b607581c5161af6e859b69c09d21be4ba3df3a51ab620829ad46e9bfa7c', 'Original OLE SHA mismatch')
    original = AllocatedCFB(source_bytes)
    old = original.read_stream('Contents')
    need({p.name for p in folder.iterdir()} == ARTIFACT_NAMES | {'artifacts.json'}, 'Unexpected or incomplete artifact inventory')
    for name in ARTIFACT_NAMES | {'artifacts.json'}:
        need(not (folder/name).is_symlink() and (folder/name).is_file(), 'Artifact must be a regular nonsymlink file: ' + name)
    inventory = json.loads(read_limited(folder/'artifacts.json', 16384))
    need(inventory.get('schema') == 'origin-native-artifacts-v2', 'Unknown artifact inventory schema')
    need(inventory.get('status') == 'native-byte-verification-passed-Origin-untested', 'Artifact status missing')
    need(set(inventory.get('files', {})) == ARTIFACT_NAMES, 'Artifact hash inventory differs')
    artifacts = {}
    for name in ARTIFACT_NAMES:
        limit = MAX_CSV_BYTES if name.endswith('.csv') else 2*1024*1024
        artifacts[name] = read_limited(folder/name, limit)
        record = inventory['files'][name]
        need(record.get('sha256') == sha(artifacts[name]) and record.get('bytes') == len(artifacts[name]), 'Artifact hash/size mismatch: ' + name)
    raw, ole = artifacts['synthetic-demo.origin_payload'], artifacts['synthetic-demo.ole.bin']
    final = AllocatedCFB(ole)
    need(final.read_stream('Contents') == raw, 'Native artifact differs from OLE Contents')
    need(len(raw) == len(old) == 13662, 'Native stream length changed')
    need(original.streams == final.streams, 'CFB directory changed')
    need(original.physical_owners == final.physical_owners and original.mini_owners == final.mini_owners, 'CFB allocation changed')
    for path in original.streams:
        if path != ('Contents',):
            need(original.read_stream(path) == final.read_stream(path), 'Non-target OLE stream changed')
    columns = parse_csv(artifacts['synthetic-demo.csv'])
    expected = [[struct.pack('<d', value) for value in column] for column in columns]
    old_info = read_modern_xy_bindings(old)
    new_info = _read_modern_xy_bindings_unscoped(raw)
    for key in ('dataset_manifest', 'resolved_curves', 'curve_tokens', 'pages'):
        need(old_info[key] == new_info[key], 'Native graph/binding metadata changed: ' + key)
    need(not new_info['rejected'] and len(new_info['columns']) == 2, 'Numeric inventory changed')
    allowed = set()
    records = []
    for i, column in enumerate(old_info['columns']):
        old_values, old_segments, old_end = parse_record(old, column['ff_offset'])
        values, segments, end = parse_record(raw, column['ff_offset'])
        need(old_segments == segments and old_end == end == column['end_offset'], 'Native record controls/boundaries changed')
        need([v.to_bytes(8, 'little') for v in values] == expected[i], 'Authored decoder differs from input CSV')
        decoded = _decode_record(raw, column['ff_offset'])
        need(decoded is not None, 'Approved independent decoder rejected a record')
        other, other_end = decoded
        need(other_end == end, 'Independent record boundary disagrees')
        need([struct.pack('<d', float(v)) for v in other] == expected[i], 'Independent decoder differs from input CSV')
        for segment in segments:
            need(segment['kind'] == 'fpc', 'Unexpected numeric segment kind')
            for item in segment['trace']:
                allowed.update(range(item['offset'], item['offset']+item['width']))
        records.append({'column': column['name'], 'verified_values': len(values),
                        'independent_output_hex': [v.hex() for v in expected[i]],
                        'record_boundary': [column['ff_offset'], end]})
    changed = [i for i, (a, b) in enumerate(zip(old, raw)) if a != b]
    need(bool(changed) and set(changed) <= allowed, 'Changed native bytes escape numeric residuals, or no-op candidate')
    nd = json.loads(artifacts['native-restore-manifest.json'])
    od = json.loads(artifacts['ole-restore-manifest.json'])
    need(restore_delta(raw, nd) == old, 'Native exact restoration failed')
    need(restore_delta(ole, od) == source_bytes, 'OLE exact restoration failed')
    physical = set()
    for i in allowed:
        mapping = original.mapping('Contents', i, 1)
        need(len(mapping) == 1, 'Numeric byte has ambiguous physical mapping')
        physical.add(mapping[0][1])
    physical_changes = [i for i, (a, b) in enumerate(zip(source_bytes, ole)) if a != b]
    need(len(source_bytes) == len(ole) and set(physical_changes) <= physical, 'Changed CFB bytes escape numeric allocation')
    need(len(physical_changes) == len(changed), 'CFB/native changed-byte counts disagree')
    recorded = json.loads(artifacts['verification.json'])
    need(recorded.get('candidate_contents_sha256') == sha(raw), 'Recorded Contents hash disagrees')
    need(recorded.get('candidate_ole_sha256') == sha(ole), 'Recorded OLE hash disagrees')
    need(recorded.get('native_changed_offsets') == changed, 'Recorded changed-byte offsets disagree')
    need(recorded.get('input_csv_sha256') == sha(artifacts['synthetic-demo.csv']), 'Recorded CSV hash disagrees')
    need(recorded.get('cached_preview_matches_candidate_data') is False, 'Stale cache limitation missing')
    need(recorded.get('Origin_reopen_save') == 'NOT RUN', 'Origin acceptance limitation missing')
    need(recorded.get('worksheet_row_alignment_verified') is False, 'Worksheet row-oracle limitation missing')
    need(recorded.get('native_only_no_preview_generation') is True and recorded.get('tool_revision') == 2, 'Native-only revision identity missing')
    return {'status': 'PASS', 'verification_method': 'Explicit read-only checks; active under python -O; no generator call',
            'native_changed_bytes': len(changed), 'OLE_changed_bytes': len(physical_changes),
            'all_18_values_bit_exact_in_two_decoders': True,
            'unchanged_graph_binding_and_metadata': True,
            'all_other_native_and_CFB_bytes_preserved': True,
            'exact_original_restoration_verified': True,
            'generated_images': False, 'native_OLE_cache': 'Stale original content, unchanged',
            'Origin_reopen_save': 'NOT RUN', 'records': records}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('original_ole', type=Path)
    p.add_argument('output_directory', type=Path)
    a = p.parse_args()
    print(json.dumps(verify(a.original_ole, a.output_directory), indent=2))
