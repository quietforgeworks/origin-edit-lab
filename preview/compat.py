#!/usr/bin/env python3
"""Compatibility gates. No Origin reader/writer is claimed by this module."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path

VERSION = "0.1.0"
SUFFIXES = {".opj", ".opju"}
UNCHECKED = [
    "graph appearance, labels, annotations, legend and layout",
    "worksheet formulas, recalculation state, cell formatting and rich text",
    "folder hierarchy, matrices, images, embedded objects and attachments",
    "unknown/private format records and newer Origin features",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def inspect_file(path: Path) -> dict:
    """Only inspect bytes; do not execute embedded scripts or infer compatibility."""
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ValueError("Input must be a regular file")
    with path.open("rb") as stream:
        header = stream.read(64)
    return {
        "name": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "header_hex": header.hex(),
        "header_ascii": "".join(chr(b) if 32 <= b < 127 else "." for b in header),
        "recognized_extension": path.suffix.lower() in SUFFIXES,
        "signature_hint": ("CPYUA" if header.startswith(b"CPYUA") else
                           "CPYA" if header.startswith(b"CPYA") else "unrecognized"),
        "parsed": False,
        "origin_reopen_verified": False,
        "compatibility_complete": False,
    }


def validate_paths(source: Path, output: Path) -> tuple[Path, Path]:
    source = Path(source).resolve(strict=True)
    output = Path(output).absolute()
    if output.is_symlink():
        raise ValueError("Refusing an output symlink, including a dangling symlink")
    output = output.resolve()
    if not source.is_file():
        raise ValueError("Source must be a regular file")
    if source.suffix.lower() not in SUFFIXES:
        raise ValueError("Only explicit .opj or .opju paths are accepted")
    if source == output:
        raise ValueError("Refusing to overwrite the source")
    if source.suffix.lower() != output.suffix.lower():
        raise ValueError("Same-format test requires exactly the same extension")
    if output.exists():
        raise ValueError("Refusing to overwrite an existing output")
    if not output.parent.is_dir():
        raise ValueError("Output parent directory must already exist")
    return source, output


def normalize(value):
    """Stable JSON representation; preserve strings, null, NaN and infinities."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return {"$number": "NaN"}
        if math.isinf(value):
            return {"$number": "+Infinity" if value > 0 else "-Infinity"}
        return value
    if isinstance(value, (list, tuple)):
        return [normalize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): normalize(v) for k, v in value.items()}
    # NumPy scalar support without importing NumPy in the pure core.
    item = getattr(value, "item", None)
    if callable(item):
        return normalize(item())
    raise TypeError(f"Unsupported snapshot value: {type(value).__name__}")


def number_equal(a, b, *, rtol=1e-12, atol=1e-14):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=rtol, abs_tol=atol)
    return a == b


def differences(expected, actual, path="$", *, rtol=1e-12, atol=1e-14):
    """Return paths only, never silently discard extra/missing data or objects."""
    out = []
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(expected.keys() | actual.keys()):
            child = f"{path}.{key}"
            if key not in expected:
                out.append({"path": child, "reason": "unexpected"})
            elif key not in actual:
                out.append({"path": child, "reason": "missing"})
            else:
                out.extend(differences(expected[key], actual[key], child, rtol=rtol, atol=atol))
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            out.append({"path": path, "reason": "length_changed"})
        for i, (x, y) in enumerate(zip(expected, actual)):
            out.extend(differences(x, y, f"{path}[{i}]", rtol=rtol, atol=atol))
    elif not number_equal(expected, actual, rtol=rtol, atol=atol):
        out.append({"path": path, "reason": "value_changed"})
    return out


def apply_expected_edits(snapshot: dict, edits: list[dict]) -> dict:
    """Apply explicit numeric test edits to a COPY of the expected snapshot."""
    expected = copy.deepcopy(snapshot)
    seen = set()
    for edit in edits:
        required = {"book", "sheet", "row", "col", "old", "new"}
        if set(edit) != required:
            raise ValueError(f"Each edit must have exactly these keys: {sorted(required)}")
        for axis in ("row", "col"):
            if type(edit[axis]) is not int or edit[axis] < 0:
                raise ValueError("Row and column must be non-negative integers (zero-based)")
        for kind in ("old", "new"):
            if type(edit[kind]) not in (int, float) or not math.isfinite(edit[kind]):
                raise ValueError("Phase 1 edits support finite numeric cells only")
        identity = tuple(edit[k] for k in ("book", "sheet", "row", "col"))
        if identity in seen:
            raise ValueError("Duplicate cell edit")
        seen.add(identity)
        books = [b for b in expected["workbooks"] if b["name"] == edit["book"]]
        if len(books) != 1:
            raise ValueError("Workbook name must resolve uniquely")
        sheets = [s for s in books[0]["sheets"] if s["name"] == edit["sheet"]]
        if len(sheets) != 1:
            raise ValueError("Worksheet name must resolve uniquely")
        sheet = sheets[0]
        row, col = edit["row"], edit["col"]
        if col >= len(sheet["columns"]) or row >= len(sheet["columns"][col]["values"]):
            raise ValueError("Cell is outside the existing data extent")
        old = sheet["columns"][col]["values"][row]
        if type(old) not in (int, float) or not number_equal(old, edit["old"]):
            raise ValueError("Expected old cell value does not match")
        if number_equal(edit["new"], edit["old"]):
            raise ValueError("Edit must actually change the cell")
        sheet["columns"][col]["values"][row] = edit["new"]
    return expected


def evaluate(before, after, edits, *, origin_reopened=False, source_unchanged=False):
    diff = differences(apply_expected_edits(before, edits), after)
    phase1 = bool(origin_reopened and source_unchanged and not diff)
    return {
        "tool_version": VERSION,
        "status": "phase1_pass_manual_review_required" if phase1 else "not_passed",
        "phase1_data_and_structure_passed": phase1,
        "origin_reopen_verified": bool(origin_reopened),
        "source_unchanged": bool(source_unchanged),
        "differences": diff,
        "unchecked": UNCHECKED,
        "compatibility_complete": False,
        "note": "A phase-1 pass is not proof of complete or lossless Origin compatibility.",
    }


def write_json_exclusive(path: Path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(normalize(value), stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Read-only header/hash inspection")
    args = parser.parse_args()
    print(json.dumps(inspect_file(args.file), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
