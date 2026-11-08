"""Load only hash-pinned reviewed research helpers and approved codec modules.

Namespace-only package objects avoid unrelated quantized application imports.
No network, package installation, or modification of imported files occurs.
"""
from pathlib import Path
import hashlib
import json
import sys
import types

HERE = Path(__file__).resolve().parent
DEPENDENCIES = HERE / 'dependencies'
sys.dont_write_bytecode = True


def setup():
    manifest = json.loads((DEPENDENCIES / 'PROVENANCE.json').read_text())
    for name, record in manifest['files'].items():
        path = DEPENDENCIES / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Pinned dependency differs: ' + name)
    sys.path.insert(0, str(DEPENDENCIES / 'helpers'))
    for name in ('quantized', 'quantized.io', 'quantized.io.origin_project'):
        package_path = DEPENDENCIES.joinpath(*name.split('.'))
        if name in sys.modules:
            if list(getattr(sys.modules[name], '__path__', [])) != [str(package_path)]:
                raise ValueError('Foreign quantized import would defeat isolated codec provenance')
        else:
            module = types.ModuleType(name)
            module.__path__ = [str(package_path)]
            sys.modules[name] = module
    return manifest


PROVENANCE = setup()
