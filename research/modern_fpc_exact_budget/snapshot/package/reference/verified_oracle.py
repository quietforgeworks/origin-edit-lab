"""Test-only loader for two previously approved SHA-pinned quantized modules.

No package initializers, downloads, installations or code changes. Only the
read buffer that passed verification executes. Independent reader/source hash
verification is required before any production claims. This is not shipped
with copies of the external source.
"""
from contextlib import contextmanager
import hashlib
from pathlib import Path
import sys
import types

PINS = {
    "container": "e80996b8955d46b446bdc4761a55b19b6d760619edb0b94b98f16ebe47cb4115",
    "opju_codec": "5a2c6f000ff8fef0a71ba8aab0876f7de785d5bb4dfa8d07dd612f052b737be9",
}
REVISION = "431deeb7c8473503970ca56b78cc1678f57d373d"


def load_verified(path, name, digest):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
        raise ValueError("verified dependency must be a bounded regular source file")
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != digest:
        raise ValueError("dependency SHA-256 mismatch")
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


@contextmanager
def external_decoder(root):
    """root contains io/origin_project/{container,opju_codec}.py."""
    if any(n == "quantized" or n.startswith("quantized.") for n in sys.modules):
        raise ValueError("use a fresh process without quantized already imported")
    root = Path(root).resolve(strict=True)
    sources = {}
    for name, expected in PINS.items():
        path = root / "io" / "origin_project" / (name + ".py")
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
            raise ValueError("external source is absent, nonregular or too large")
        source = path.read_bytes()
        if hashlib.sha256(source).hexdigest() != expected:
            raise ValueError("external source SHA-256 mismatch")
        sources[name] = source
    try:
        for name in ("quantized", "quantized.io", "quantized.io.origin_project"):
            module = types.ModuleType(name)
            module.__path__ = []
            sys.modules[name] = module
        for short, source in sources.items():
            name = "quantized.io.origin_project." + short
            module = types.ModuleType(name)
            module.__package__ = "quantized.io.origin_project"
            module.__file__ = "<SHA-verified-quantized/" + short + ".py>"
            sys.modules[name] = module
            exec(compile(source, module.__file__, "exec"), module.__dict__)
        yield module
    finally:
        for name in tuple(sys.modules):
            if name == "quantized" or name.startswith("quantized."):
                del sys.modules[name]


def decode_raw_adapter(module, stream, count):
    """Explicit adaptation: disable only application missing-sentinel mapping.

    The SHA-verified decoder source is unchanged. During this synchronous call
    only, module.ORIGIN_MISSING is NaN, so its equality mask is empty. This is
    NOT the unchanged public decoder API; every adapted result is separately
    checked against a fresh independent integer-only decoder. Thread-unsafe:
    test-runner only, never a production/concurrent route.
    """
    previous = module.ORIGIN_MISSING
    try:
        module.ORIGIN_MISSING = float("nan")
        values, used = module._decode(stream, count)
        return values.view("<u8").tobytes(), used
    finally:
        module.ORIGIN_MISSING = previous
