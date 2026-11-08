"""Separate fixed50 custom-data research adapter. Never a native-safe export API."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import struct
import sys
import tempfile
import types

ROOT = Path(__file__).resolve().parent
PINNED = {
    'numeric_support.py': 'f9a5a2b9a672c90512d5b97b1ca3c2991b105b088fb41e859e1f6167b0b21f2d',
    'native_active_rows.py': '03d99c1d46da61a85b7a1b4ef16f006f97916dcd99e1b1f4e548989d59eec8d3',
    'verify_source_artifacts.py': '312e3beef37e843b649cc8944bc19524bd1d00e6ba3ddd903427722d65d2b565',
}
FILES = {'candidate.opj', 'raw.csv', 'declaration.json', 'rollback.opj',
         'manifest.json', 'before.json', 'after.json', 'bundle.json'}
SCHEMA = 'custom-fixed50-bundle-v1'

class Rejected(ValueError):
    pass

def need(ok, why):
    if not ok:
        raise Rejected(why)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def checked_path(value):
    p = Path(value)
    need('..' not in p.parts, 'lexical parent traversal refused')
    p = p.absolute()
    for part in (p, *p.parents):
        need(not part.is_symlink(), 'symlink path component refused')
    return p

def read_file(path, limit):
    p = checked_path(path)
    before = p.stat()
    need(stat.S_ISREG(before.st_mode), 'regular files only; FIFO/device refused')
    need(before.st_size <= limit, 'file exceeds bound')
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(p, flags), 'rb') as f:
        opened = os.fstat(f.fileno())
        need(stat.S_ISREG(opened.st_mode), 'opened input not regular')
        need((before.st_dev, before.st_ino) == (opened.st_dev, opened.st_ino), 'input replaced while opening')
        data = f.read(limit + 1)
        after = os.fstat(f.fileno())
    need(len(data) <= limit, 'file exceeds bound')
    need((opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) ==
         (after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'input changed while reading')
    checked_path(p)
    return data

def strict_json(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            need(k not in result, 'duplicate JSON key')
            result[k] = v
        return result
    def constant(value):
        raise Rejected('nonfinite JSON constant')
    def number(token):
        value = float(token)
        need(math.isfinite(value), 'nonfinite JSON numeric conversion')
        return value
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant, parse_float=number)

def json_bytes(obj):
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()

def opt_in(value):
    need(value is True, 'explicit Boolean research opt-in required; Origin lifecycle NOT_RUN')

def load_backend():
    """Hash bytes before execution; preserve existing import state, no shared module cache."""
    source = {}
    directory = checked_path(ROOT / 'vendor')
    need({p.name for p in directory.iterdir()} == set(PINNED), 'vendor inventory differs')
    for name, digest in PINNED.items():
        source[name] = read_file(directory / name, 128000)
        need(sha(source[name]) == digest, 'frozen source hash mismatch: ' + name)
    old = {}; modules = {}
    try:
        for filename in PINNED:
            name = filename[:-3]
            old[name] = sys.modules.get(name)
            module = types.ModuleType(name)
            module.__file__ = str(directory / filename)
            sys.modules[name] = module
            exec(compile(source[filename], module.__file__, 'exec'), module.__dict__)
            modules[name] = module
    finally:
        for name, previous in old.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous
    return modules['native_active_rows'], modules['verify_source_artifacts']

def declaration(raw):
    need(type(raw) is bytes and len(raw) <= 8192, 'bounded raw declaration bytes required')
    obj = strict_json(raw)
    need(type(obj) is dict and set(obj) == {'schema', 'declared_kind', 'statement'}, 'declaration keys differ')
    need(obj['schema'] == 'custom-data-provenance-v1', 'declaration schema differs')
    need(type(obj['declared_kind']) is str and obj['declared_kind'] in ('synthetic', 'measured', 'unspecified'), 'unknown provenance declaration')
    need(type(obj['statement']) is str and 1 <= len(obj['statement']) <= 2048, 'explicit bounded provenance statement required')
    return obj

def expected_artifacts(original, raw, provenance, *, research_opt_in=False):
    """Pure bounded generation. Provenance is caller-declared, never authenticated."""
    opt_in(research_opt_in)
    declared = declaration(provenance)
    backend, verifier = load_backend()
    candidate, manifest, before, after = backend.patch_bytes(original, raw)
    verifier.verify_candidate(original, raw, candidate, manifest, before, after)
    n = manifest['active_rows']
    retained = []
    for col in before['columns']:
        retained.append({'dataset': col['name'], 'first_inactive_row_one_based': n + 1 if n < 50 else None,
            'last_inactive_row_one_based': 50 if n < 50 else None,
            'retained_binary64_little_endian_hex': col['binary64_le'][n:],
            'retained_binary64_hex_float': [struct.unpack('<d', bytes.fromhex(x))[0].hex() for x in col['binary64_le'][n:]]})
    files = {'candidate.opj': candidate, 'raw.csv': raw, 'declaration.json': provenance,
             'rollback.opj': backend.restore_bytes(candidate, manifest),
             'manifest.json': json_bytes(manifest), 'before.json': json_bytes(before), 'after.json': json_bytes(after)}
    envelope = {'schema': SCHEMA, 'branch': 'fixed50-single-curve-active-prefix',
        'active_rows': n, 'allocated_rows': 50, 'series_count': 1,
        'source_template_sha256': backend.TEMPLATE_HASH, 'source_template_url': backend.SOURCE_URL,
        'frozen_algorithm_sha256': PINNED,
        'input_provenance': {'caller_declaration': declared, 'independently_verified': False,
                             'statement': 'Declaration is retained exactly and is not measurement verification.'},
        'artifacts': {k: {'sha256': sha(v), 'bytes': len(v)} for k, v in files.items()},
        'inactive_template_cells_retained': retained,
        'raw_input_byte_exact': True, 'all_active_input_cells_in_conversion_ledger': True,
        'unrelated_template_content_retained': True, 'private_template_sanitization_supported': False,
        'origin_lifecycle': 'NOT_RUN', 'input_specific_labplot_observation': 'NOT_RUN',
        'native_safe_export_supported': False,
        'scope': 'Source-integrity research only. Legacy template includes unrelated original content. No Origin acceptance claim.'}
    files['bundle.json'] = json_bytes(envelope)
    return files

def check_anchors(raw, provenance, expected_csv_sha256, expected_declaration_sha256):
    for name, value in [('CSV', expected_csv_sha256), ('declaration', expected_declaration_sha256)]:
        need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), name + ' external SHA-256 anchor required')
    need(sha(raw) == expected_csv_sha256, 'CSV differs from external source anchor')
    need(sha(provenance) == expected_declaration_sha256, 'declaration differs from external source anchor')

def verify_artifacts(files, *, expected_csv_sha256, expected_declaration_sha256, research_opt_in=False):
    opt_in(research_opt_in)
    need(type(files) is dict and set(files) == FILES, 'bundle inventory differs')
    need(all(type(v) is bytes for v in files.values()), 'bundle artifacts must be bytes')
    for name, value in files.items():
        need(len(value) <= 2000000, 'artifact exceeds bound')
        if name.endswith('.json'):
            strict_json(value)
    check_anchors(files['raw.csv'], files['declaration.json'], expected_csv_sha256, expected_declaration_sha256)
    expected = expected_artifacts(files['rollback.opj'], files['raw.csv'], files['declaration.json'], research_opt_in=True)
    for name in sorted(FILES):
        need(files[name] == expected[name], 'artifact differs from exact regeneration: ' + name)
    envelope = strict_json(expected['bundle.json'])
    return {'schema': SCHEMA, 'source_integrity': 'PASS', 'all_artifacts_exactly_regenerated': True,
            'active_rows': envelope['active_rows'], 'allocated_rows': 50,
            'input_provenance': envelope['input_provenance'],
            'inactive_source_cells_retained': 2 * (50 - envelope['active_rows']),
            'unrelated_template_content_retained': True,
            'raw_csv_sha256': expected_csv_sha256, 'declaration_sha256': expected_declaration_sha256,
            'candidate_sha256': sha(files['candidate.opj']),
            'origin_lifecycle': 'NOT_RUN', 'input_specific_labplot_observation': 'NOT_RUN',
            'native_safe_export_supported': False}

def read_bundle(bundle):
    p = checked_path(bundle)
    need(p.is_dir(), 'bundle must be a directory')
    need({x.name for x in p.iterdir()} == FILES, 'bundle inventory differs')
    return {name: read_file(p / name, 2000000) for name in FILES}

def verify(bundle, *, expected_csv_sha256, expected_declaration_sha256, research_opt_in=False):
    opt_in(research_opt_in)
    return verify_artifacts(read_bundle(bundle), expected_csv_sha256=expected_csv_sha256,
                            expected_declaration_sha256=expected_declaration_sha256, research_opt_in=True)

def new_output(path):
    need(platform.system() == 'Linux', 'Linux-only no-overwrite research publication')
    p = checked_path(path)
    package = ROOT.parent
    research_outputs = package / 'runs'
    in_package = p == package or package in p.parents
    in_outputs = research_outputs in p.parents
    need(not in_package or in_outputs, 'output inside source package refused; only dedicated runs descendants are allowed')
    need(not p.exists(), 'output exists; no overwrite')
    need(p.parent.is_dir(), 'output parent must exist')
    return p

def publish(files, out):
    p = new_output(out)
    backend, _ = load_backend()
    stage = Path(tempfile.mkdtemp(prefix='.custom-data-', dir=p.parent))
    try:
        for name, data in files.items():
            (stage / name).write_bytes(data)
        for name, data in files.items():
            need(read_file(stage / name, 2000000) == data, 'staged bytes differ')
        backend.publish_noreplace(stage, p)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return p

def generate(template, csv, provenance, out, *, research_opt_in=False):
    opt_in(research_opt_in)
    new_output(out)
    original = read_file(template, 231494)
    raw = read_file(csv, 32768)
    declared = read_file(provenance, 8192)
    artifacts = expected_artifacts(original, raw, declared, research_opt_in=True)
    summary = verify_artifacts(artifacts, expected_csv_sha256=sha(raw),
                              expected_declaration_sha256=sha(declared), research_opt_in=True)
    publish(artifacts, out)
    summary['output'] = str(Path(out).absolute())
    return summary

def recover(bundle, out, *, expected_csv_sha256, expected_declaration_sha256, research_opt_in=False):
    opt_in(research_opt_in)
    new_output(out)
    files = read_bundle(bundle)
    summary = verify_artifacts(files, expected_csv_sha256=expected_csv_sha256,
                              expected_declaration_sha256=expected_declaration_sha256, research_opt_in=True)
    recovery = {'restored-original.opj': files['rollback.opj'], 'raw.csv': files['raw.csv'],
                'declaration.json': files['declaration.json']}
    publish(recovery, out)
    return {'recovery': 'PASS', 'restored_original_sha256': sha(files['rollback.opj']),
            'raw_input_byte_exact': True, 'declaration_byte_exact': True,
            'output': str(Path(out).absolute()), 'origin_lifecycle': 'NOT_RUN'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--accept-labplot-only-research', action='store_true')
    sub = p.add_subparsers(dest='command', required=True)
    g = sub.add_parser('generate')
    for flag in ('template', 'csv', 'provenance', 'out'):
        g.add_argument('--' + flag, required=True)
    for name in ('verify', 'recover'):
        v = sub.add_parser(name)
        v.add_argument('--bundle', required=True)
        v.add_argument('--expected-csv-sha256', required=True)
        v.add_argument('--expected-declaration-sha256', required=True)
        if name == 'recover':
            v.add_argument('--out', required=True)
    args = vars(p.parse_args())
    command = args.pop('command')
    args['research_opt_in'] = args.pop('accept_labplot_only_research')
    try:
        result = globals()[command](**args)
        print(json.dumps(result, indent=2, allow_nan=False))
    except Exception as error:
        failure = {'status': 'FAILED_OR_REJECTED', 'reason': str(error), 'origin_lifecycle': 'NOT_RUN', 'rollback_performed': False}
        if 'out' in args:
            output = Path(args['out']).absolute()
            failure.update(output=str(output), output_path_exists=output.exists() or output.is_symlink(), output_ownership='Not inferred from path existence')
        print(json.dumps(failure), file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
