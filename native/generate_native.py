"""Research CSV -> exact-template native Origin OLE candidate, never OPJU.

The original numeric record allocation, selectors and graph objects survive.
Only existing FPC residual bytes may change. Unsupported inputs fail closed.
Original cached graphics are deliberately NOT synchronized. This native-only
revision generates no preview, refit, or image.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import struct

import bootstrap
from modern_fpc_patch import parse_record, rewrite_segment, bits_f64, PatchRefused
from csv_contract import parse_csv, numeric_bits, read_limited, MAX_CSV_BYTES
from atomic_output import publish_new_directory
from modern_embedded_reader import read_modern_embedded_numeric
from modern_sparse_binding import read_modern_xy_bindings, _read_modern_xy_bindings_unscoped
from quantized.io.origin_project import opju_codec
from quantized.io.origin_project.container import ORIGIN_MISSING
from writeback import AllocatedCFB, sha, guard, patch_cfb, make_delta, restore_delta

SOURCE_PPT_SHA = '207de07f76806d1059f4b6829203c2e3a4a74823df8b457cf03497cf9262a250'
SOURCE_CFB_SHA = '25536b607581c5161af6e859b69c09d21be4ba3df3a51ab620829ad46e9bfa7c'
SOURCE_NATIVE_SHA = '73d800c56814c8870e30bcebc20d931aa6f222480d7e42a7b3401def81fa323f'
NUMERIC_COLUMNS = ('Book1_A', 'Book1_B')
LIMITATIONS = [
    'Template-derived native embedded Origin95.Graph candidate, not blank graph generation or a standalone OPJU.',
    'Exactly two existing 9-value numeric columns; stored order and binding metadata preserved, worksheet row alignment unverified.',
    'Fixed original FPC controls/residual widths; some otherwise ordinary finite input datasets must be refused.',
    'Missing cells, NaN, infinity, Origin missing sentinel, extra columns and changed row count unsupported; never coerced to zero.',
    'Origin graph objects, labels, axes, smoothing settings and all unknown records remain the original template bytes.',
    'Unknown metadata/checksum dependencies may need updates after data changes; preserving them does not prove native internal integrity.',
    'Native OLE cached preview is stale original content, NOT the synthetic demo. No PowerPoint candidate is produced.',
    'No SVG, PNG, plot reconstruction or fitted-curve recalculation is performed by this native-only revision.',
    'Origin, Windows, PowerPoint, macOS reopen/save/recalculation acceptance NOT RUN.',
]


def need(condition, message):
    if not condition:
        raise PatchRefused(message)


def snapshot_without_values(snapshot):
    result = copy.deepcopy(snapshot)
    result.pop('source_sha256', None)
    # Exact-source public wrapper annotations do not describe record contents.
    result.pop('source_profile', None)
    result.pop('scope', None)
    for column in result['columns']:
        column.pop('stored_values')
    return result


def build_native(cfb_bytes: bytes, columns):
    need(type(cfb_bytes) is bytes, 'Immutable CFB input required')
    guard(cfb_bytes, SOURCE_CFB_SHA, 'Exact original object90 OLE template')
    need(type(columns) in (tuple, list) and len(columns) == 2, 'Two column arrays required')
    need(all(type(c) in (tuple, list) and len(c) == 9 for c in columns), 'Exactly nine stored values per column required')
    wanted = [[numeric_bits(value) for value in values] for values in columns]
    cfb = AllocatedCFB(cfb_bytes)
    source = cfb.read_stream('Contents')
    guard(source, SOURCE_NATIVE_SHA, 'Exact original native Contents')
    need(len(source) == 13662, 'Unexpected source length')
    need(set(cfb.streams) == {('Contents',), ('\x01Ole',), ('\x02OlePres000',)}, 'Unexpected OLE streams')
    before = read_modern_xy_bindings(source)
    need(not before['rejected'], 'Unresolved numeric record')
    need(tuple(c['name'] for c in before['columns']) == NUMERIC_COLUMNS, 'Unexpected dataset inventory')
    need(before['resolved_xy_count'] == 1 and len(before['resolved_curves']) == 1, 'One explicit curve binding required')
    curve = before['resolved_curves'][0]
    need((curve['x'], curve['y']) == NUMERIC_COLUMNS, 'X/Y binding differs')
    need(all(not c['undecoded_gap_flags'] and c['stored_count'] == 9 for c in before['columns']), 'Unresolved gaps/counts')
    result = source
    spans = []
    evidence = []
    for column, required in zip(before['columns'], wanted):
        original_bits, segments, end = parse_record(source, column['ff_offset'])
        need(end == column['end_offset'] and len(original_bits) == 9, 'Independent framing disagrees')
        need(original_bits == [numeric_bits(v) for v in column['stored_values']], 'Independent source bits disagree')
        for segment in segments:
            need(segment['kind'] == 'fpc', 'Repeat segment rewriting is unsupported')
            start = segment['first']
            result = rewrite_segment(result, segment, required[start:start + segment['count']])
            # Only residual bytes, not even the original control nibbles, are allowed to change.
            spans.extend((entry['offset'], entry['width']) for entry in segment['trace'] if entry['width'])
        after_bits, after_segments, after_end = parse_record(result, column['ff_offset'])
        need(after_bits == required and segments == after_segments and end == after_end, 'Native bit verification failed')
        external = opju_codec._decode_record(result, column['ff_offset'])
        need(external is not None and external[1] == end, 'Pinned independent decoder cannot read output')
        external_bits = [numeric_bits(float(v)) for v in external[0]]
        need(external_bits == required, 'Independent decoder does not match every input bit')
        evidence.append({'name': column['name'], 'count': 9, 'ff_offset': column['ff_offset'],
                         'end_offset': end, 'before_values': column['stored_values'],
                         'input_values': [bits_f64(b) for b in required],
                         'output_binary64_hex': [f'{b:016x}' for b in external_bits],
                         'segments_and_controls_unchanged': True,
                         'independent_decoder_bit_exact': True})
    need(result != source, 'No-op dataset is not generation evidence')
    need(len(result) == len(source), 'Native stream length changed')
    after = _read_modern_xy_bindings_unscoped(result)
    need(snapshot_without_values(before) == snapshot_without_values(after), 'Native metadata or inventory changed')
    for column, required in zip(after['columns'], wanted):
        need([numeric_bits(v) for v in column['stored_values']] == required, 'Full numeric scan differs from input')
    allowed = {offset for start, count in spans for offset in range(start, start + count)}
    changed = [i for i, (a, b) in enumerate(zip(source, result)) if a != b]
    need(set(changed) <= allowed, 'Native edit escaped permitted numeric residuals')
    native_delta_result, native_delta = make_delta(source,
        [(start, source[start:start+count], result[start:start+count]) for start, count in spans],
        kind='exact-object90-fpc-data', detail={'limitations': LIMITATIONS})
    need(native_delta_result == result and restore_delta(result, native_delta) == source, 'Native restoration failed')
    patched_cfb, cfb_delta = patch_cfb(cfb_bytes, result, stream_path='Contents',
        expected_source_sha256=SOURCE_CFB_SHA, expected_stream_sha256=SOURCE_NATIVE_SHA, allowlist=spans)
    rebuilt = AllocatedCFB(patched_cfb)
    need(restore_delta(patched_cfb, cfb_delta) == cfb_bytes, 'OLE restoration failed')
    need(rebuilt.read_stream('\x02OlePres000') == cfb.read_stream('\x02OlePres000'), 'Cache was modified')
    need(rebuilt.read_stream('\x01Ole') == cfb.read_stream('\x01Ole'), 'OLE metadata modified')
    report = {
        'status': 'Native data mutation and independent decode verified; application acceptance untested',
        'synthetic_demo_data_not_measurements': True,
        'template_provenance': {'url': 'https://doi.org/10.5281/zenodo.20155927', 'license': 'CC-BY-4.0',
            'pptx_sha256': SOURCE_PPT_SHA, 'pptx_part': 'ppt/embeddings/oleObject90.bin',
            'original_ole_sha256': SOURCE_CFB_SHA, 'original_contents_sha256': SOURCE_NATIVE_SHA},
        'candidate_ole_sha256': sha(patched_cfb), 'candidate_contents_sha256': sha(result),
        'native_stream_bytes': len(result), 'native_changed_offsets': changed,
        'native_changed_byte_count': len(changed), 'permitted_residual_spans': spans,
        'all_bytes_outside_numeric_residuals_unchanged': True,
        'all_18_input_binary64_values_verified_by_two_implementations': True,
        'existing_XY_selectors_and_graph_records_byte_identical': True,
        'record_lengths_counts_and_compression_controls_unchanged': True,
        'unknown_native_metadata_or_checksum_dependencies_recomputed': False,
        'complete_native_internal_integrity_verified': False,
        'CFB_allocation_directory_and_other_streams_unchanged': True,
        'original_OLE_and_native_contents_exactly_restorable': True,
        'worksheet_row_alignment_verified': False,
        'cached_preview_matches_candidate_data': False,
        'original_smooth_curve_recalculated': False,
        'Origin_reopen_save': 'NOT RUN', 'macOS_PowerPoint_acceptance': 'NOT RUN',
        'full_standalone_OPJU': False, 'column_evidence': evidence,
        'limitations': LIMITATIONS,
        'approved_quantized_revision': bootstrap.PROVENANCE['approved_quantized_revision'],
    }
    return result, patched_cfb, native_delta, cfb_delta, report


def generate(source_path, csv_path, output_dir):
    source_path, csv_path, output_dir = Path(source_path), Path(csv_path), Path(output_dir)
    need(not output_dir.exists() and not output_dir.is_symlink(), 'Output directory must be new')
    original = read_limited(source_path, 51712)
    csv_bytes = read_limited(csv_path, MAX_CSV_BYTES)
    columns = parse_csv(csv_bytes)
    native, ole, nd, cd, report = build_native(original, columns)
    report['input_csv_sha256'] = sha(csv_bytes)
    report['tool_revision'] = 2
    report['native_only_no_preview_generation'] = True
    outputs = {'synthetic-demo.origin_payload': native, 'synthetic-demo.ole.bin': ole,
               'synthetic-demo.csv': csv_bytes}
    for name, value in [('native-restore-manifest.json', nd), ('ole-restore-manifest.json', cd), ('verification.json', report)]:
        outputs[name] = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
    inventory = {'schema': 'origin-native-artifacts-v2',
                 'status': 'native-byte-verification-passed-Origin-untested',
                 'files': {name: {'sha256': sha(value), 'bytes': len(value)} for name, value in outputs.items()}}
    outputs['artifacts.json'] = (json.dumps(inventory, indent=2)+'\n').encode()

    def recheck_inputs():
        guard(read_limited(source_path, 51712), SOURCE_CFB_SHA, 'Unchanged template input')
        need(read_limited(csv_path, MAX_CSV_BYTES) == csv_bytes, 'CSV changed during generation')

    recheck_inputs()
    publication = publish_new_directory(output_dir, outputs, before_publish=recheck_inputs)
    return dict(report, publication=publication)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template_ole', type=Path)
    parser.add_argument('csv', type=Path)
    parser.add_argument('new_output_directory', type=Path)
    args = parser.parse_args()
    report = generate(args.template_ole, args.csv, args.new_output_directory)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
