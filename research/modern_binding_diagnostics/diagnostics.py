"""Bounded, read-only candidate diagnostics. Never a native parser or writer.

Only metadata is inspected. Byte/character positions below describe observed
record layouts, not a complete CPYUA typed dataset or owner grammar. Candidate
identities must never be promoted to supported graph bindings by this module.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass


class Rejected(ValueError):
    """An explicit diagnostic contract was not satisfied."""


@dataclass(frozen=True)
class DescriptorCandidate:
    name: str
    field82: int


@dataclass(frozen=True)
class PropertyCandidate:
    dataset_id: int
    page: str
    name: str
    worksheet_x: int
    designation: int


@dataclass(frozen=True)
class GraphCandidate:
    position: int  # In-memory only; never included in public reports.
    x: int
    y: int


def uleb(blob: bytes, position: int) -> tuple[int, int]:
    if position < 0:
        raise Rejected("Negative varint position")
    value = 0
    for i in range(5):
        if position >= len(blob):
            raise Rejected("Truncated varint")
        byte = blob[position]
        position += 1
        if i == 4 and byte > 15:
            raise Rejected("Varint exceeds uint32")
        value |= (byte & 127) << (7 * i)
        if byte < 128:
            if i and byte == 0:
                raise Rejected("Noncanonical varint")
            return value, position
    raise Rejected("Overlong varint")


def sparse_candidate(blob: bytes, position: int) -> tuple[bytes, int]:
    """Decode one bounded sparse frame, without treating it as a dataset."""
    if not 0 <= position < len(blob) or blob[position] != 128:
        raise Rejected("Missing sparse frame tag")
    size, cursor = uleb(blob, position + 1)
    end = cursor + size
    if not 0 < size <= 8192 or end > len(blob):
        raise Rejected("Sparse frame bounds")
    decoded = bytearray()
    while cursor < end:
        opcode = blob[cursor]
        cursor += 1
        if opcode < 128:
            if cursor + opcode > end:
                raise Rejected("Literal exceeds frame")
            decoded.extend(blob[cursor:cursor + opcode])
            cursor += opcode
        elif opcode < 192:
            decoded.extend(bytes(opcode - 125))
        elif opcode < 196:
            if cursor == end:
                raise Rejected("Missing repeated byte")
            decoded.extend(bytes([blob[cursor]]) * (opcode - 189))
            cursor += 1
        else:
            raise Rejected("Unsupported sparse opcode")
        if len(decoded) > 8192:
            raise Rejected("Sparse output exceeds bound")
    return bytes(decoded), end


def page_spans(blob: bytes, pages):
    """Validate external page candidates, without certifying page ownership."""
    previous = -1
    names = set()
    for start, name in pages:
        if type(start) is not int or not previous < start < len(blob):
            raise Rejected("Invalid page candidate order or bounds")
        if not isinstance(name, str) or not name or name in names:
            raise Rejected("Invalid or duplicate page candidate name")
        previous = start
        names.add(name)
    return [(a, b, name) for (a, name), (b, _) in
            zip(pages, [*pages[1:], (len(blob), "")])]


def scan_candidates(blob: bytes, pages) -> dict:
    spans = page_spans(blob, pages)
    first_page = spans[0][0] if spans else len(blob)
    descriptors = []
    graphs = []
    layers = 0
    other147 = 0
    for match in re.finditer(b"\x80", blob):
        position = match.start()
        try:
            decoded, end = sparse_candidate(blob, position)
        except Rejected:
            continue
        if len(decoded) == 147 and position < first_page:
            name = decoded[88:113].split(b"\0", 1)[0]
            if name and all(32 <= byte < 127 for byte in name):
                descriptors.append(DescriptorCandidate(
                    name.decode("ascii"), int.from_bytes(decoded[82:86], "little")))
            else:
                other147 += 1
        if (len(decoded) in (489, 515, 519) and decoded[:4] == b"\1\0\0\0"
                and blob[end:end + 16].find(b"\x01\x58\x80\x09\x98\x03\x40\xb3") in range(5)):
            graphs.append(GraphCandidate(position,
                                         int.from_bytes(decoded[35:37], "little"),
                                         int.from_bytes(decoded[4:6], "little")))
        if (len(decoded) in (341, 361, 385, 393)
                and decoded[:4] in (b"\0\0\x1f\0", b"\0\0\x17\0", b"\0\0\x5f\0")):
            layers += 1
    properties = []
    for start, end, page in spans:
        if page.startswith("Graph"):
            continue
        for match in re.finditer(b"\x80", blob[start:end]):
            try:
                decoded, after = sparse_candidate(blob, start + match.start())
            except Rejected:
                continue
            if (after > end or len(decoded) not in (515, 519)
                    or decoded[0] != 16 or decoded[2:4] != b"\0\0"):
                continue
            name = decoded[18:30].split(b"\0", 1)[0]
            if not re.fullmatch(rb"[A-Za-z0-9][A-Za-z0-9_]*", name):
                continue
            properties.append(PropertyCandidate(
                int.from_bytes(decoded[4:6], "little"), page, name.decode("ascii"),
                int.from_bytes(decoded[35:37], "little"), decoded[17]))
    return {"descriptors": descriptors, "graphs": graphs, "properties": properties,
            "layer_candidates": layers, "other147_candidates": other147}


def sheetless(name: str) -> str:
    """Comparison only; never remove suffixes from retained descriptor identities."""
    return re.sub(r"@\d+$", "", name)


def verify_property_candidates(descriptors, properties, *, complete: bool):
    """Check ID/identity agreement against candidates, not a complete dataset list."""
    n = len(descriptors)
    counts = Counter(p.dataset_id for p in properties)
    if not properties:
        raise Rejected("No explicit property candidates")
    if any(type(p.dataset_id) is not int or not 1 <= p.dataset_id <= n for p in properties):
        raise Rejected("Property ID outside candidate range")
    if any(count != 1 for count in counts.values()):
        raise Rejected("Duplicate property ID")
    if complete and counts != Counter(range(1, n + 1)):
        raise Rejected("Property IDs do not cover candidate slots exactly once")
    for prop in properties:
        if sheetless(descriptors[prop.dataset_id - 1].name) != prop.page + "_" + prop.name:
            raise Rejected("Property ID disagrees with candidate identity")


def candidate_xy(descriptors, graph):
    """A consistency-check helper, never a supported binding resolver.

    X=0 means no explicit X dataset. The plot-mode semantics remain unknown;
    preserve None instead of substituting A or using Python's negative index.
    """
    if type(graph.x) is not int or type(graph.y) is not int:
        raise Rejected("Selectors must be integers")
    if not 1 <= graph.y <= len(descriptors) or not 0 <= graph.x <= len(descriptors):
        raise Rejected("Graph selector outside candidate range")
    y = descriptors[graph.y - 1]
    if graph.x == 0:
        return None, y
    if y.field82 != graph.x:
        raise Rejected("Graph X disagrees with candidate descriptor field82")
    return descriptors[graph.x - 1], y


def require_supported_binding(*_args, **_kwargs):
    """Explicit fail-closed boundary: this supplement never certifies a binding."""
    raise Rejected("Complete typed dataset and owner grammar is unproved; binding unsupported")
