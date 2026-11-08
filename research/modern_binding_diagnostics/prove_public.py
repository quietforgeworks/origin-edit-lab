"""Reproduce public-source count evidence, never publish native metadata/payloads."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from diagnostics import (Rejected, candidate_xy, page_spans, scan_candidates,
                         verify_property_candidates)
from runtime import HERE, REVISION, checked_bytes, pinned_quantized

MINIMAL = "oleObject105.Contents.bin"


def locate_inputs(roots: list[Path], case: str):
    manifest = json.loads((HERE / "public_sources.json").read_text(encoding="utf-8"))
    files = manifest["files"]
    if case == "minimal":
        files = [entry for entry in files if entry["file"] == MINIMAL]
    elif case != "all":
        raise Rejected("Unknown proof case")
    if not roots:
        raise Rejected("At least one explicit public corpus root is required")
    normalized = [root.resolve(strict=True) for root in roots]
    if len(set(normalized)) != len(normalized) or any(not root.is_dir() for root in normalized):
        raise Rejected("Corpus roots must be distinct directories")
    names = [entry["file"] for entry in files]
    if len(names) != len(set(names)) or (case == "all" and len(files) != 110):
        raise Rejected("Invalid public corpus manifest")
    selected = []
    for entry in files:
        name = entry["file"]
        if not name or Path(name).name != name:
            raise Rejected("Corpus manifest entry is not a basename")
        found = [root / name for root in normalized if (root / name).exists() or (root / name).is_symlink()]
        if len(found) != 1:
            raise Rejected("Public input missing or ambiguous: " + name)
        path = found[0]
        if not path.resolve(strict=True).is_relative_to(path.parent):
            raise Rejected("Corpus input escapes explicit root")
        # Do not parse any file until every requested input has passed its pin.
        checked_bytes(path, entry["sha256"], entry["bytes"])
        selected.append((path, entry))
    return selected


def compare_complete_graphs(blob, pages, candidates, table, api):
    descriptors = candidates["descriptors"]
    properties = {p.dataset_id: p for p in candidates["properties"]}
    result = []
    for start, end, page in page_spans(blob, pages):
        if not page.startswith("Graph"):
            continue
        graphs = [g for g in candidates["graphs"] if start <= g.position < end]
        # Call the actual pinned extraction function, not a reimplementation.
        actual = api.extract_curves_by_id(blob, start, end, table)
        explicit_pairs = set()
        identities = set()
        lossy_keys = set()
        worksheet_disagreements = 0
        for graph in graphs:
            x, y = candidate_xy(descriptors, graph)
            if x is None:
                # No X substitution is permitted for a non-XY candidate.
                continue
            xp, yp = properties[graph.x], properties[graph.y]
            explicit_pairs.add((xp.page, xp.name, yp.page, yp.name))
            identities.add((x.name, y.name))
            lossy_keys.add((yp.page, yp.name))
            worksheet_disagreements += graph.x != yp.worksheet_x
        actual_pairs = {(r["book"], r["x"], r["book"], r["y"]) for r in actual}
        result.append({
            "explicit_graph_candidates": len(graphs),
            "distinct_descriptor_identity_pairs": len(identities),
            "book_short_y_keys": len(lossy_keys),
            "pinned_extracted_rows": len(actual),
            "graph_x_worksheet_x_disagreements": worksheet_disagreements,
            "pinned_rows_without_matching_explicit_xy": sum(
                (r["book"], r["x"], r["book"], r["y"]) not in explicit_pairs for r in actual),
            "candidate_xy_pairs_not_represented_in_pinned_rows": len(explicit_pairs - actual_pairs),
        })
    return result


def inspect_public(blob: bytes, api):
    if not blob.startswith(b"CPYUA "):
        raise Rejected("Not the pinned modern signature")
    pages = api.opju_pages(blob)
    candidates = scan_candidates(blob, pages)
    table = api.column_id_table(blob, pages)
    descriptors = candidates["descriptors"]
    properties = candidates["properties"]
    graphs = candidates["graphs"]
    # This corpus has no positive-X disagreement. Any new result is a failure,
    # not permission to repair it by guessing worksheet partners or column A.
    for graph in graphs:
        candidate_xy(descriptors, graph)
    coverage = "none"
    if properties:
        verify_property_candidates(descriptors, properties, complete=False)
        if len(properties) == len(descriptors):
            verify_property_candidates(descriptors, properties, complete=True)
            coverage = "complete_candidate_coverage"
        else:
            coverage = "partial_candidate_coverage"
    if table.ids and coverage != "complete_candidate_coverage":
        raise Rejected("Pinned IDs exist without complete property candidate cross-check")
    omitted = [p for p in properties if p.dataset_id not in table.ids]
    report = {
        "descriptor_candidates": len(descriptors),
        "graph_candidates": len(graphs),
        "layer_candidates": candidates["layer_candidates"],
        "explicit_property_candidates": len(properties),
        "pinned_id_count": len(table.ids),
        "property_coverage": coverage,
        "zero_x_candidates": sum(g.x == 0 for g in graphs),
        "positive_x_field82_agreements": sum(g.x > 0 for g in graphs),
        "other147_candidates": candidates["other147_candidates"],
        "omitted_property_candidates": len(omitted),
        "omitted_by_designation": {str(k): v for k, v in sorted(Counter(p.designation for p in omitted).items())},
        "complete_typed_dataset_grammar": False,
        "sheet_ownership_verified": False,
        "supported_bindings": 0,
    }
    if coverage == "complete_candidate_coverage":
        report["graphs"] = compare_complete_graphs(blob, pages, candidates, table, api)
    return report


def summarize(records):
    complete = [r for r in records if r["property_coverage"] == "complete_candidate_coverage"]
    partial = [r for r in records if r["property_coverage"] == "partial_candidate_coverage"]
    return {
        "public_files": len(records),
        "descriptor_candidates": sum(r["descriptor_candidates"] for r in records),
        "graph_candidates": sum(r["graph_candidates"] for r in records),
        "explicit_property_candidates": sum(r["explicit_property_candidates"] for r in records),
        "complete_candidate_files": len(complete),
        "complete_candidate_property_ids": sum(r["explicit_property_candidates"] for r in complete),
        "pinned_ids_in_complete_candidate_files": sum(r["pinned_id_count"] for r in complete),
        "omitted_ids_in_complete_candidate_files": sum(r["omitted_property_candidates"] for r in complete),
        "partial_candidate_files": len(partial),
        "partial_candidate_property_ids": sum(r["explicit_property_candidates"] for r in partial),
        "pinned_ids_in_partial_candidate_files": sum(r["pinned_id_count"] for r in partial),
        "files_without_recognized_property_candidates": sum(r["property_coverage"] == "none" for r in records),
        "files_with_multiple_layer_candidates": sum(r["layer_candidates"] > 1 for r in records),
        "other147_candidates": sum(r["other147_candidates"] for r in records),
        "positive_x_field82_agreements": sum(r["positive_x_field82_agreements"] for r in records),
        "zero_x_candidates": sum(r["zero_x_candidates"] for r in records),
        "supported_bindings": 0,
        "complete_typed_dataset_grammar": False,
        "origin_acceptance": False,
    }


def verify_expected(report):
    expected = json.loads((HERE / "expected_counts.json").read_text(encoding="utf-8"))
    if report["summary"] != expected[report["case"]]["summary"]:
        raise Rejected("Observed aggregate counts differ from published case")
    minimal = next(r for r in report["files"] if r["file"] == MINIMAL)
    if minimal["graphs"] != expected["minimal"]["graphs"]:
        raise Rejected("Minimal actual-extraction counterexample changed")


def run(roots: list[Path], quantized_root: Path, case: str):
    selected = locate_inputs(roots, case)
    records = []
    with pinned_quantized(quantized_root) as api:
        for path, source in selected:
            blob = checked_bytes(path, source["sha256"], source["bytes"])
            record = inspect_public(blob, api)
            record.update({"file": source["file"], "sha256": source["sha256"], "source": source["source"]})
            records.append(record)
    for path, source in selected:
        checked_bytes(path, source["sha256"], source["bytes"])
    report = {"schema": 1, "case": case, "quantized_revision": REVISION,
              "source_manifest": "public_sources.json", "files": records,
              "summary": summarize(records), "source_inputs_unchanged": True,
              "native_files_modified": False, "origin_acceptance": False,
              "output_scope": "Public file identities and counts only; no decoded names, values, raw records, or source positions."}
    verify_expected(report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-root", action="append", required=True, type=Path,
                        help="Explicit directory of exact named public inputs; may repeat")
    parser.add_argument("--quantized-root", required=True, type=Path,
                        help="Explicit existing directory containing pinned quantized io/")
    parser.add_argument("--case", choices=("minimal", "all"), default="minimal")
    parser.add_argument("--out", required=True, type=Path, help="New counts-only JSON file; never overwritten")
    args = parser.parse_args(argv)
    try:
        if args.out.exists() or args.out.is_symlink():
            raise Rejected("Report output already exists")
        report = run(args.public_root, args.quantized_root, args.case)
        with args.out.open("x", encoding="utf-8") as output:
            json.dump(report, output, indent=2)
            output.write("\n")
    except (Rejected, OSError, ImportError, KeyError, TypeError, ValueError) as error:
        # Avoid logging local paths or native metadata in a portable report.
        print("Proof failed: " + (str(error) if isinstance(error, Rejected) else type(error).__name__), file=sys.stderr)
        return 2
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
