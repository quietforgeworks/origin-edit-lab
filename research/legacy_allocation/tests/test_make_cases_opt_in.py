"""The toy wrapper must preserve the native-safe default refusal."""
import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE))
import make_cases
import native_allocation as native

FIXTURE = Path(os.environ['ORIGIN_PUBLIC_FIXTURE']) if os.environ.get('ORIGIN_PUBLIC_FIXTURE') else None
EXPECTED = {
    51: '95e76a8dbc04d79671375c92479c546a9b8387a677de2f35c80074cb8625779e',
    257: '652f7758eceae81740850e132bdc44b58999a48843454562837dbdab7ad9a666',
    1024: '799cc39149fd7eca0a24b1a8c427fdc7bc614e0016adcfa0eb24ec3a816b21fe',
}

class DenyEnvironment:
    def __getitem__(self, key):
        raise AssertionError('environment accessed before opt-in: ' + key)
    def get(self, key, default=None):
        raise AssertionError('environment accessed before opt-in: ' + key)

def copy_cli(root):
    for name in ('make_cases.py', 'native_allocation.py', 'numeric_support.py'):
        shutil.copyfile(SOURCE / name, root / name)
    return [sys.executable] + (['-O'] if sys.flags.optimize else []) + [str(root / 'make_cases.py')]

def tree_bytes(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}

class RefusalTests(unittest.TestCase):
    def test_default_refuses_before_environment_or_paths(self):
        with patch.object(make_cases.os, 'environ', DenyEnvironment()), patch.object(make_cases, 'checked_path', side_effect=AssertionError('path access')):
            with self.assertRaisesRegex(native.Rejected, 'Origin-safe allocation expansion refused'):
                make_cases.main()

    def test_nonliteral_opt_in_refused_before_environment(self):
        for mode in (False, None, 1, 'true'):
            with self.subTest(mode=mode), patch.object(make_cases.os, 'environ', DenyEnvironment()):
                with self.assertRaisesRegex(native.Rejected, 'Origin-safe allocation expansion refused'):
                    make_cases.main(research_only=mode)

    def test_default_creates_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(make_cases, 'ROOT', root), patch.object(make_cases.os, 'environ', DenyEnvironment()):
                with self.assertRaisesRegex(native.Rejected, 'Origin-safe allocation expansion refused'):
                    make_cases.main()
            self.assertEqual(list(root.iterdir()), [])

    def test_cli_default_without_fixture_environment_creates_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = copy_cli(root)
            before = tree_bytes(root)
            env = dict(os.environ)
            env.pop('ORIGIN_PUBLIC_FIXTURE', None)
            env.pop('PYTHONDONTWRITEBYTECODE', None)
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=20)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, '')
            self.assertIn('Origin-safe allocation expansion refused', result.stderr)
            self.assertNotIn('KeyError', result.stderr)
            self.assertEqual(tree_bytes(root), before)
            self.assertEqual(sorted(p.name for p in root.iterdir()), sorted(before))

@unittest.skipUnless(FIXTURE is not None and FIXTURE.is_file(), 'exact public fixture is external prerequisite')
class OptInTests(unittest.TestCase):
    def verify_candidates(self, root):
        for n, expected in EXPECTED.items():
            folder = root / 'candidates' / f'generated{n}'
            self.assertEqual(native.sha((folder / 'candidate.opj').read_bytes()), expected)
            self.assertEqual((folder / 'rollback.opj').read_bytes(), FIXTURE.read_bytes())
            self.assertEqual(native.sha((folder / 'raw.csv').read_bytes()), make_cases.TOY_HASHES[n])

    def test_api_explicit_opt_in_matches_reviewed_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(make_cases, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                make_cases.main(research_only=True)
            self.verify_candidates(root)

    def test_cli_explicit_opt_in_matches_reviewed_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = subprocess.run(copy_cli(root) + ['--labplot-only-research'], cwd=root, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.verify_candidates(root)

if __name__ == '__main__':
    unittest.main(verbosity=2)
