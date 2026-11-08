"""Explicit, hash-verified external source loader; no installs or downloads."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys
import types

from diagnostics import Rejected

HERE = Path(__file__).resolve().parent
REVISION = "431deeb7c8473503970ca56b78cc1678f57d373d"
MODULE_ORDER = ("container", "opju_codec", "curve_style_color", "tree", "tree_opju", "opju_figure_curves")


def checked_bytes(path: Path, expected_hash: str, expected_size: int | None = None) -> bytes:
    """Hash checks use explicit exceptions, including under Python -O."""
    if path.is_symlink() or not path.is_file():
        raise Rejected("Missing, nonregular, or symlinked required input")
    data = path.read_bytes()
    if expected_size is not None and len(data) != expected_size:
        raise Rejected("Required input size mismatch")
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise Rejected("Required input SHA-256 mismatch")
    return data


def verified_module_bytes(root: Path) -> dict[str, bytes]:
    pin = json.loads((HERE / "quantized_sources.json").read_text(encoding="utf-8"))
    expected_paths = {f"io/origin_project/{name}.py" for name in MODULE_ORDER}
    if pin["revision"] != REVISION or set(pin["files"]) != expected_paths:
        raise Rejected("Unexpected external module manifest")
    root = root.resolve(strict=True)
    result = {}
    for relative, digest in pin["files"].items():
        path = root / relative
        if not path.resolve(strict=True).is_relative_to(root):
            raise Rejected("External module escapes explicit source root")
        result[relative] = checked_bytes(path, digest)
    return result


@contextmanager
def pinned_quantized(root: Path):
    """Execute only six verified files, not an arbitrary package initializer.

    Bytes are read and verified before execution, avoiding a verify/reopen race.
    Existing NumPy is an external runtime prerequisite, not downloaded here.
    The fresh namespace is removed on exit, including failure paths.
    """
    sources = verified_module_bytes(root)
    if any(name == "quantized" or name.startswith("quantized.") for name in sys.modules):
        raise Rejected("Quantized already imported; use a fresh Python process")
    previous_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        for package in ("quantized", "quantized.io", "quantized.io.origin_project"):
            module = types.ModuleType(package)
            module.__path__ = []
            module.__package__ = package
            sys.modules[package] = module
        for name in MODULE_ORDER:
            relative = f"io/origin_project/{name}.py"
            qualified = "quantized.io.origin_project." + name
            module = types.ModuleType(qualified)
            module.__package__ = "quantized.io.origin_project"
            module.__file__ = "<verified-quantized/" + relative + ">"
            sys.modules[qualified] = module
            exec(compile(sources[relative], module.__file__, "exec"), module.__dict__)
        yield sys.modules["quantized.io.origin_project.opju_figure_curves"]
    finally:
        for name in list(sys.modules):
            if name == "quantized" or name.startswith("quantized."):
                del sys.modules[name]
        sys.dont_write_bytecode = previous_bytecode
