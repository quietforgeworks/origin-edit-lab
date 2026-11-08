"""Read-only source inventory and recorded-evidence checks, not a corpus rerun.

Only Python's standard library is used. No external source is imported and no
native file or application is opened. Checks remain enabled under Python -O.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
CORE_SHA = '43c3415066ed12f1f158e8406f6d62d1dc767daea537e31441865934e6c70dbc'
ARCHIVE_SHA = 'cae754eb202181857b6e5294ae876697260cc16d3c73c8d5d33bff8e334dfb05'
OPTIMIZED_SHA = '42f715203e70a7f795dc6937009d35d986fc9fcf87dba451b8242f14f97e484d'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(rel, root=ROOT):
    return json.loads((root / rel).read_text(encoding='utf-8'))


def safe_relative(path):
    p = PurePosixPath(path)
    require(bool(path) and not p.is_absolute() and '\\' not in path
            and '..' not in p.parts and str(p) == path, 'unsafe inventory path')
    return p


def verify_inventory(root=ROOT):
    manifest = load('MANIFEST.json', root)
    inventory = manifest['files']
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts
              and p.suffix not in ('.pyc', '.pyo')}
    require(actual == set(inventory) | {'MANIFEST.json'}, 'package inventory mismatch')
    for name, record in inventory.items():
        safe_relative(name)
        p = root / name
        require(not p.is_symlink() and p.is_file(), 'nonregular package member')
        data = p.read_bytes()
        require(len(data) == record['bytes'] and digest(data) == record['sha256'],
                'package hash mismatch: ' + name)
    require(manifest['file_count_excluding_manifest'] == len(inventory), 'file count mismatch')
    require(manifest['bytes_excluding_manifest'] == sum(x['bytes'] for x in inventory.values()),
            'package byte total mismatch')
    return inventory


def reconstruct_optimized(normal):
    token = b'"optimize": 0'
    require(normal.count(token) == 1, 'ambiguous optimization marker')
    reconstructed = normal.replace(token, b'"optimize": 1', 1)
    require(digest(reconstructed) == OPTIMIZED_SHA, 'reconstructed report hash mismatch')
    return reconstructed


def verify_upstream(root=ROOT):
    integration = load('INTEGRATION.json', root)
    upstream = load('UPSTREAM-MANIFEST.json', root)
    require(integration['upstream_archive']['sha256'] == ARCHIVE_SHA, 'archive pin mismatch')
    selected = integration['retained_upstream_files']
    excluded = integration['excluded_upstream_files']
    names = [x['upstream_path'] for x in selected] + [x['path'] for x in excluded]
    require(len(names) == len(set(names)) == 37, 'selection count or duplicate mismatch')
    require(set(names) == set(upstream['files']) | {'MANIFEST.json'}, 'incomplete selection audit')
    require({x['path'] for x in excluded} == {
        'results/public-corpus-optimized.json', 'patches/new-source-files.patch'}, 'unexpected exclusion')
    for record in selected:
        safe_relative(record['path'])
        data = (root / record['path']).read_bytes()
        require(len(data) == record['bytes'] and digest(data) == record['sha256'], 'retained source changed')
        if record['upstream_path'] != 'MANIFEST.json':
            require(upstream['files'][record['upstream_path']] == {
                'bytes': record['bytes'], 'sha256': record['sha256']}, 'upstream member hash mismatch')
    for record in excluded:
        require(upstream['files'][record['path']] == {
            'bytes': record['bytes'], 'sha256': record['sha256']}, 'excluded member hash mismatch')
    require(digest((root / 'code/fpc_numeric.py').read_bytes()) == CORE_SHA, 'frozen codec changed')
    require(digest(reconstruct_optimized((root / 'results/public-corpus-normal.json').read_bytes()))
            == integration['reconstructed_optimized_report']['sha256'], 'optimized pin mismatch')
    return integration


def verify_corpus(root=ROOT):
    sources = load('evidence/public_sources.json', root)['files']
    report = load('results/public-corpus-normal.json', root)
    reconciliation = load('evidence/final-reconciliation.json', root)
    source_by_name = {s['file']: s for s in sources}
    require(len(sources) == len(source_by_name) == 167, 'public input count mismatch')
    require(len({s['sha256'] for s in sources}) == 166, 'distinct input count mismatch')
    require(len(report['files']) == 167 and len(report['streams']) == 7843, 'report count mismatch')
    for s in sources:
        require(set(s) in ({'file', 'sha256', 'public', 'source', 'license', 'group'},
                           {'file', 'sha256', 'public', 'source', 'url', 'license', 'group'}),
                'source evidence schema changed')
        if 'url' in s:
            require(s['url'].startswith('https://zenodo.org/api/records/'), 'unexpected public download URL')
        require(s['public'] is True and PurePosixPath(s['file']).name == s['file'], 'nonpublic source')
        require(s['source'].startswith(('https://zenodo.org/', 'https://doi.org/')), 'unexpected source URL')
        require(s['license'] in ('CC-BY-4.0', 'Etalab-2.0'), 'unexpected recorded data license')
    totals = Counter()
    by_file = {name: Counter() for name in source_by_name}
    unique_intervals = set()
    stream_fields = {'file', 'source_sha256', 'slot1', 'start', 'end', 'count',
                     'experimental_matrix_framing', 'additional_to_strict',
                     'original_stream_sha256', 'raw_bits_sha256', 'encoded_stream_sha256',
                     'original_bytes', 'encoded_bytes', 'missing_sentinel_count',
                     'unchanged_external_raw_bit_exact'}
    for s in report['streams']:
        require(set(s) == stream_fields, 'stream evidence contains unexpected fields')
        require(s['source_sha256'] == source_by_name[s['file']]['sha256'], 'source linkage mismatch')
        require(0 <= s['start'] < s['end'] and 0 < s['count'] <= 1_000_000, 'invalid recorded extent')
        require(s['end'] - s['start'] == s['original_bytes'], 'recorded extent length mismatch')
        require(s['original_stream_sha256'] == s['encoded_stream_sha256'], 'recorded wire identity mismatch')
        require(s['unchanged_external_raw_bit_exact'] == (s['missing_sentinel_count'] == 0),
                'sentinel qualification mismatch')
        key = s['file'], s['start'], s['end'], s['count']
        require(key not in unique_intervals, 'duplicate occurrence')
        unique_intervals.add(key)
        values = {'streams': 1, 'values': s['count'], 'original_bytes': s['original_bytes'],
                  'encoded_bytes': s['encoded_bytes'], 'missing_sentinel_values': s['missing_sentinel_count'],
                  'streams_with_missing_sentinel': bool(s['missing_sentinel_count']),
                  'additional_to_strict_streams': s['additional_to_strict'],
                  'additional_to_strict_values': s['count'] if s['additional_to_strict'] else 0,
                  'experimental_matrix_streams': s['experimental_matrix_framing']}
        totals.update(values)
        by_file[s['file']].update(values)
    for k, value in totals.items():
        require(report['summary'][k] == value, 'corpus aggregate mismatch: ' + k)
    require(totals['values'] == 9949997 and totals['additional_to_strict_streams'] == 2404,
            'bounded corpus scope changed')
    require(totals['streams'] - totals['additional_to_strict_streams'] == 5439,
            'strict versus experimental scope mismatch')
    for f in report['files']:
        require(set(f) == {'file', 'sha256_before', 'sha256_after', 'source_bytes', 'source',
                          'strict_summary', 'experimental_summary', 'tested'}, 'file evidence schema changed')
        require(f['sha256_before'] == f['sha256_after'] == source_by_name[f['file']]['sha256'],
                'before/after source mismatch')
        require(Counter(f['tested']) == by_file[f['file']], 'per-file aggregate mismatch')
    require(len({(s['raw_bits_sha256'], s['count']) for s in report['streams']}) == 6245,
            'distinct raw-bit/count-pair mismatch')
    for name, expected in reconciliation['result_hashes'].items():
        data = (reconstruct_optimized((root / 'results/public-corpus-normal.json').read_bytes())
                if name == 'public-corpus-optimized.json' else (root / 'results' / name).read_bytes())
        require(digest(data) == expected, 'recorded result hash mismatch')
    require(report['summary']['native_origin_acceptance'] is False
            and report['summary']['native_containers_modified'] is False, 'native scope changed')
    return dict(totals)


def verify_source_only(root=ROOT):
    for path in root.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts or path.suffix in ('.pyc', '.pyo'):
            continue
        require(not path.is_symlink(), 'symlink in source-only package')
        require(path.suffix in ('.py', '.md', '.json', '.log') or path.name == 'LICENSE',
                'unexpected source-package file type')
        data = path.read_bytes()
        require(b'\0' not in data, 'binary data in source-only package')
        text = data.decode('utf-8')
        # Construct these tokens so the checker itself is not a positive match.
        for token in ('/' + 'workspace/', '/' + 'home/', '/' + 'Users/', '/' + 'tmp/'):
            require(token not in text, 'local absolute path in source-only package')
    return True


def main():
    inventory = verify_inventory()
    verify_upstream()
    summary = verify_corpus()
    verify_source_only()
    print(json.dumps({'inventory_files': len(inventory), 'recorded_streams': summary['streams'],
                      'recorded_words': summary['values'], 'evidence_only': True,
                      'external_corpus_rerun': False, 'native_application_run': False}, sort_keys=True))


if __name__ == '__main__':
    main()
