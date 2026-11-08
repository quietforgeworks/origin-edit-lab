"""Check generated example hashes and optional exact public-fixture candidates.

No downloading, application execution, binary output, or private data input.
The optional fixture must match the public template hash before transformation.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(value, message):
    if not value:
        raise ValueError(message)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify(fixture=None):
    matrix = json.loads((ROOT / 'NATIVE-DATA-PROVENANCE.json').read_bytes())
    original = None
    if fixture is not None:
        original = Path(fixture).read_bytes()
        need(sha(original) == matrix['public_template']['sha256'], 'wrong public fixture hash')
    multi = ROOT / 'legacy_multicurve'
    sys.path.insert(0, str(multi))
    generator = load('provenance_multicurve_examples', multi / 'make_cases.py')
    custom = ROOT / 'legacy_custom_data'
    examples = load('provenance_custom_examples', custom / 'tests/test_custom.py')
    adapter = load('provenance_custom_adapter', custom / 'src/custom_data.py')
    results = []
    for case in matrix['cases']:
        if case['branch'] == 'legacy_multicurve':
            raw = generator.raw_for(case['curves'])
            if original is not None:
                candidate, _ = generator.patch_bytes(original, raw, research_only=True)
        else:
            raw = examples.csv_bytes(case['rows'])
            need(raw == (custom / case['input_path']).read_bytes(), 'CSV is not the generated synthetic example')
            declaration = examples.provenance()
            need(declaration == (custom / 'inputs/synthetic-declaration.json').read_bytes(), 'synthetic declaration differs')
            need(sha(declaration) == case['declaration_sha256'], 'declaration hash differs')
            if original is not None:
                candidate = adapter.expected_artifacts(original, raw, declaration, research_opt_in=True)['candidate.opj']
        need(sha(raw) == case['raw_input_sha256'], 'synthetic raw input hash differs')
        if original is not None:
            need(sha(candidate) == case['native_candidate_sha256'], 'generated candidate differs from historical public case')
        results.append({'case': case['case'], 'raw_input_sha256': sha(raw), 'synthetic_regeneration': 'PASS',
                        'native_candidate_regeneration': 'PASS' if original is not None else 'NOT_RUN'})
    return {'schema': 'native-data-provenance-check-v1', 'cases': results,
            'application_rerun': 'NOT_RUN', 'origin_lifecycle': 'NOT_RUN'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fixture', type=Path)
    a = p.parse_args()
    print(json.dumps(verify(a.fixture), indent=2))
