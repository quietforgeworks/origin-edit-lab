"""Repository-only bridges for unchanged reviewed tests; never launch an app.

Missing optional external evidence skips the named test class. Explicitly
selected but missing evidence is an error. Source integrity tests always run.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def external(name, *, directory=False):
    value = os.environ.get(name)
    if value is None:
        return None
    if not value:
        raise ValueError(name + ' was explicitly set but is empty')
    path = Path(value)
    if not (path.is_dir() if directory else path.is_file()):
        raise ValueError(name + ' was explicitly set but is missing or wrong type')
    return path.absolute()


def custom_suite():
    root = ROOT / 'legacy_custom_data'
    native = load('reviewed_custom_tests', root / 'tests/test_custom.py')
    observation = load('reviewed_custom_observation_tests', root / 'tests/test_observation.py')
    source = load('reviewed_custom_source_tests', root / 'tests/test_source_audit.py')
    template = external('CUSTOM_TEMPLATE')
    if template is None:
        unittest.skip('external exact public fixture not supplied: CUSTOM_TEMPLATE')(native.CustomTests)
    else:
        native.TEMPLATE = template
    evidence = external('CUSTOM_EVIDENCE_ROOT', directory=True)
    if evidence is None:
        unittest.skip('external real-application evidence not supplied: CUSTOM_EVIDENCE_ROOT')(observation.ObservationTests)
    else:
        # Only these unchanged test globals locate the optional historical files.
        # Validator implementation and external input anchors remain unchanged.
        if not (evidence / 'application/results50').is_dir() or not (evidence / 'runs/custom50').is_dir():
            raise ValueError('CUSTOM_EVIDENCE_ROOT requires application/results50 and runs/custom50')
        observation.ROOT = evidence
        observation.BUNDLE = evidence / 'runs/custom50'
    loader = unittest.TestLoader()
    return unittest.TestSuite(loader.loadTestsFromModule(m) for m in (native, observation, source))


def multicurve_review_suite():
    root = ROOT / 'legacy_multicurve'
    fixture = external('ORIGIN_PUBLIC_FIXTURE')
    os.environ['MULTICURVE_SOURCE'] = str(root)
    previous = os.environ.get('ORIGIN_PUBLIC_FIXTURE')
    if fixture is None:
        os.environ['ORIGIN_PUBLIC_FIXTURE'] = str(root / 'EXTERNAL-FIXTURE-NOT-SUPPLIED.opj')
    try:
        module = load('reviewed_multicurve_guards', root / 'review/test_independent_guards.py')
    finally:
        if previous is None:
            os.environ.pop('ORIGIN_PUBLIC_FIXTURE', None)
        else:
            os.environ['ORIGIN_PUBLIC_FIXTURE'] = previous
    if fixture is None:
        unittest.skip('external exact public fixture not supplied: ORIGIN_PUBLIC_FIXTURE')(module.IndependentGuards)
    return unittest.TestLoader().loadTestsFromModule(module)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('custom', 'multicurve-review'), required=True)
    args = parser.parse_args()
    suite = custom_suite() if args.suite == 'custom' else multicurve_review_suite()
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
