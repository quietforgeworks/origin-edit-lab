#!/usr/bin/env python3
"""Read-only CSV/metadata acceptance for externally supplied synthetic legacy OPJ."""
from __future__ import annotations

import argparse
import csv
import hashlib
from decimal import Decimal
import json
import math
import re
import struct
import subprocess
from pathlib import Path

READER_VERSION = "0.3-7"
FILES = ("workbook.opj", "raw.csv", "schema.json")
CASE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
BOOK = re.compile(r"[A-Za-z][A-Za-z0-9]{0,19}\Z")
MAX_BYTES = 32 * 1024 * 1024
NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


class VerificationError(ValueError):
    """The narrow acceptance contract was not satisfied."""


def require(condition, message):
    # Deliberately not assert: validation remains active under python -O.
    if not condition:
        raise VerificationError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label(value):
    return (isinstance(value, str) and 0 < len(value) <= 128
            and value == value.strip()
            and all(32 <= ord(c) < 127 for c in value))


def load_expected(folder):
    """Validate and hash three explicit files; no OPJ parser or writer is used."""
    for name in FILES:
        p = folder / name
        require(p.is_file() and not p.is_symlink(), f"Missing or symlinked {name}")
        require(p.stat().st_size <= MAX_BYTES, f"File exceeds size limit: {name}")
    before = {name: digest(folder / name) for name in FILES}
    require((folder / "workbook.opj").read_bytes()[:4] == b"CPYA",
            "Only legacy CPYA OPJ inputs are within this contract")
    schema = json.loads((folder / "schema.json").read_text(encoding="utf-8"))
    require(isinstance(schema, dict), "Schema must be an object")
    require(schema.get("source_kind") == "synthetic_demo", "Synthetic fixtures only")
    require(schema.get("numeric_mode") == "binary64", "binary64 mode required")
    book = schema.get("book")
    require(isinstance(book, str) and BOOK.fullmatch(book), "Invalid workbook short name")
    columns = schema.get("columns")
    require(isinstance(columns, list) and 2 <= len(columns) <= 256, "Invalid column count")
    require(all(isinstance(c, dict) and label(c.get("header")) and label(c.get("unit"))
                for c in columns), "Nonempty printable ASCII column labels/units required")
    headers = [c["header"] for c in columns]
    require(len(set(headers)) == len(headers), "Duplicate column labels")
    with (folder / "raw.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f, strict=True))
    require(len(rows) >= 2 and rows[0] == headers, "CSV header mismatch or empty data")
    rows = rows[1:]
    require(1 <= len(rows) <= 65535 and len(rows) * len(columns) <= 1_000_000,
            "Fixture row/cell limit exceeded")
    require(all(len(r) == len(columns) for r in rows), "Ragged CSV")
    data = []
    for row in rows:
        parsed = []
        for token in row:
            token = token.strip()
            require(0 < len(token) <= 256 and NUMBER.fullmatch(token), "Invalid decimal CSV cell")
            try:
                value = float(token)
            except ValueError as e:
                raise VerificationError("Non-numeric CSV cell") from e
            require(math.isfinite(value), "Non-finite CSV cell")
            decimal = Decimal(token)
            require(not (value == 0 and decimal != 0), "Nonzero decimal underflow")
            require(decimal != decimal.to_integral_value() or Decimal.from_float(value) == decimal,
                    "Integer would change under binary64 conversion")
            parsed.append(value)
        data.append(parsed)
    payload = b"".join(struct.pack("<d", row[c])
                       for c in range(len(columns)) for row in data)
    return {"book": book, "rows": len(rows), "columns": columns,
            "payload": payload, "input_sha256": before}


def read_tsv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", strict=True))


def compare_readback(expected, observed):
    info = read_tsv(observed / "reader.tsv")
    require(len(info) == 1, "Invalid reader identity record")
    info = info[0]
    require(info.get("ropj_version") == READER_VERSION, "Untested Ropj version")
    ncols = len(expected["columns"])
    require(info.get("rows") == str(expected["rows"]) and info.get("columns") == str(ncols),
            "Returned worksheet dimensions differ")
    values = (observed / "values.f64le").read_bytes()
    require(values == expected["payload"], "Numeric binary64 bytes differ")
    cells = expected["rows"] * ncols
    require((observed / "missing.u8").read_bytes() == bytes(cells),
            "Missing-cell flags differ or have an invalid length")
    metadata = read_tsv(observed / "metadata.tsv")
    require(len(metadata) == ncols, "Returned metadata column count differs")
    for i, (actual, column) in enumerate(zip(metadata, expected["columns"]), 1):
        require(actual.get("column") == str(i), "Returned column order differs")
        require(bool(actual.get("short_name")), "Missing native column short name")
        require(actual.get("comment") == column["header"] + "\r\n" + column["unit"],
                "Column long name or unit differs")
        require(actual.get("command") == "", "Column commands are not explicitly empty")
    return {"rows": expected["rows"], "columns": ncols, "cells": cells,
            "binary64_equal": True, "longname_unit_pairs_equal": ncols,
            "commands_empty": True, "ropj_version": info["ropj_version"],
            "r_version": info.get("r_version", ""),
            "input_sha256": expected["input_sha256"],
            "numeric_sha256": hashlib.sha256(values).hexdigest()}


def check_unchanged(folder, expected):
    require({name: digest(folder / name) for name in FILES} == expected["input_sha256"],
            "Input file changed during verification")


def verify_case(rscript, folder, out, timeout=120):
    expected = load_expected(folder)
    out.mkdir(exist_ok=False)
    command = [str(rscript), "--vanilla", str(Path(__file__).with_name("readback.R")),
               str(folder / "workbook.opj"), str(out), expected["book"],
               str(expected["rows"]), str(len(expected["columns"])), READER_VERSION]
    # Paths/arguments are passed directly, never through a shell.
    result = subprocess.run(command, capture_output=True, timeout=timeout, check=False)
    check_unchanged(folder, expected)
    # Diagnostics stay local to the chosen output directory, not the source package.
    (out / "runtime.stdout.txt").write_bytes(result.stdout)
    (out / "runtime.stderr.txt").write_bytes(result.stderr)
    require(result.returncode == 0, f"Ropj readback failed with exit {result.returncode}; see local logs")
    report = compare_readback(expected, out)
    report["inputs_unchanged"] = True
    (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rscript", required=True, type=Path, help="User-provided Rscript executable")
    parser.add_argument("--fixtures", required=True, type=Path, help="External synthetic fixture directory")
    parser.add_argument("--case", required=True, action="append", help="Explicit immediate child directory")
    parser.add_argument("--out", required=True, type=Path, help="New local evidence directory, outside fixtures")
    args = parser.parse_args(argv)
    require(all(CASE.fullmatch(c) for c in args.case), "Invalid case name")
    require(len(set(args.case)) == len(args.case), "Duplicate cases")
    runtime = args.rscript.expanduser().resolve(strict=True)
    require(runtime.is_file(), "Rscript is not a file")
    fixtures = args.fixtures.expanduser().resolve(strict=True)
    require(fixtures.is_dir(), "Fixture root is not a directory")
    out = args.out.expanduser().absolute()
    require(not out.exists() and not out.is_symlink(), "Output must not already exist")
    require(out.parent.is_dir(), "Output parent must already exist")
    require(not out.resolve().is_relative_to(fixtures), "Output must be outside fixtures")
    for case in args.case:
        folder = fixtures / case
        require(folder.is_dir() and not folder.is_symlink(), "Case is missing or symlinked")
        load_expected(folder)  # Validate all cases before starting the runtime.
    out.mkdir(exist_ok=False)
    reports = []
    for case in args.case:
        report = verify_case(runtime, fixtures / case, out / case)
        report["case"] = case
        reports.append(report)
    summary = {"schema": "ropj-readback-v1", "cases": reports,
               "verified_cells": sum(r["cells"] for r in reports),
               "verified_longname_unit_pairs": sum(r["columns"] for r in reports),
               "original_graph_rendered": False, "origin_reopen": False,
               "independent_parser_implementation": False}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {summary['verified_cells']} cells; {summary['verified_longname_unit_pairs']} name/unit pairs")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, UnicodeError, csv.Error, json.JSONDecodeError, subprocess.SubprocessError) as e:
        raise SystemExit(f"Verification stopped: {e}")
