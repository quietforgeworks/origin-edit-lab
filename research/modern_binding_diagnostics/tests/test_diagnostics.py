"""Pure synthetic contracts; optional exact public proof is explicitly skipped."""
import contextlib
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import diagnostics as d
import prove_public as proof
import runtime


def varint(number):
    result = bytearray()
    while number >= 128:
        result.append((number & 127) | 128)
        number >>= 7
    return bytes(result + bytes([number]))


def literal_frame(decoded):
    payload = b"".join(bytes([len(decoded[i:i + 127])]) + decoded[i:i + 127]
                       for i in range(0, len(decoded), 127))
    return b"\x80" + varint(len(payload)) + payload


def descriptor(name=b"Synthetic_A", field82=0):
    data = bytearray(147)
    data[82:86] = field82.to_bytes(4, "little")
    data[88:88 + len(name)] = name
    return literal_frame(data)


def property_frame(dataset_id=1, name=b"A", designation=1, size=515):
    data = bytearray(size)
    data[0] = 16
    data[4:6] = dataset_id.to_bytes(2, "little")
    data[17] = designation
    data[18:18 + len(name)] = name
    return literal_frame(data)


class SparseTests(unittest.TestCase):
    def test_synthetic_literals_and_zero_repeat(self):
        blob = literal_frame(b"abc" + bytes(130))
        self.assertEqual(d.sparse_candidate(blob, 0), (b"abc" + bytes(130), len(blob)))
        self.assertEqual(d.sparse_candidate(b"\x80\x03\x80\xc0Z", 0)[0], bytes(3) + b"ZZZ")

    def test_frame_negative_empty_and_outside(self):
        for blob, start in ((b"", 0), (b"x", 0), (b"\x80", -1), (b"\x80", 1), (b"\x80\0", 0)):
            with self.subTest(blob=blob, start=start), self.assertRaises(d.Rejected):
                d.sparse_candidate(blob, start)

    def test_varint_truncation_noncanonical_overflow(self):
        for blob in (b"", b"\x80", b"\x80\0", b"\xff\xff\xff\xff\x10", b"\xff" * 6):
            with self.subTest(blob=blob), self.assertRaises(d.Rejected):
                d.uleb(blob, 0)
        with self.assertRaises(d.Rejected):
            d.uleb(b"\0", -1)

    def test_bad_opcode_literal_repeat_and_large_size(self):
        cases = (b"\x80\x01\xc4", b"\x80\x01\x01", b"\x80\x01\xc0",
                 b"\x80" + varint(8193) + bytes(8193), b"\x80\x02\0")
        for blob in cases:
            with self.subTest(blob=blob[:6]), self.assertRaises(d.Rejected):
                d.sparse_candidate(blob, 0)

    def test_decoded_output_bound(self):
        payload = b"\xbf" * 125  # 66 zero bytes each, above 8192.
        with self.assertRaises(d.Rejected):
            d.sparse_candidate(b"\x80" + varint(len(payload)) + payload, 0)

    def test_descriptor_and_partial_property_are_candidates_only(self):
        before = descriptor()
        blob = before + property_frame()
        result = d.scan_candidates(blob, [(len(before), "Synthetic")])
        self.assertEqual(len(result["descriptors"]), 1)
        self.assertEqual(len(result["properties"]), 1)
        d.verify_property_candidates(result["descriptors"], result["properties"], complete=True)
        with self.assertRaises(d.Rejected):
            d.require_supported_binding(result)

    def test_unrecognized_names_are_not_silently_dataset_slots(self):
        result = d.scan_candidates(descriptor(b"") + descriptor(b"\xff"), [])
        self.assertEqual(len(result["descriptors"]), 0)
        self.assertEqual(result["other147_candidates"], 2)

    def test_frame_crossing_page_boundary_is_not_property(self):
        blob = property_frame()
        self.assertEqual(d.scan_candidates(blob, [(0, "Synthetic"), (5, "GraphSynthetic")])["properties"], [])

    def test_invalid_page_candidates_reject(self):
        for pages in ([(5, "A"), (3, "B")], [(0, "A"), (1, "A")], [(-1, "A")], [(0, "")], [(10, "A")]):
            with self.subTest(pages=pages), self.assertRaises(d.Rejected):
                d.scan_candidates(bytes(10), pages)

    def test_graph_requires_recognized_immediate_marker(self):
        anchor = bytearray(489)
        anchor[:4] = b"\1\0\0\0"
        anchor[4:6] = (1).to_bytes(2, "little")
        frame = literal_frame(anchor)
        marker = b"\x01\x58\x80\x09\x98\x03\x40\xb3"
        self.assertEqual(len(d.scan_candidates(frame + marker, [])["graphs"]), 1)
        self.assertEqual(len(d.scan_candidates(frame + b"X" * 5 + marker, [])["graphs"]), 0)
        self.assertEqual(len(d.scan_candidates(frame, [])["graphs"]), 0)

    def test_candidate_inside_opaque_payload_does_not_certify_dataset(self):
        result = d.scan_candidates(b"SYNTHETIC_OPAQUE_PAYLOAD" + descriptor(), [])
        self.assertEqual(len(result["descriptors"]), 1)
        with self.assertRaises(d.Rejected):
            d.require_supported_binding(result)


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.ds = [d.DescriptorCandidate("Synthetic_A", 0), d.DescriptorCandidate("Synthetic_B", 1)]
        self.ps = [d.PropertyCandidate(1, "Synthetic", "A", 0, 3),
                   d.PropertyCandidate(2, "Synthetic", "B", 1, 0)]

    def test_exact_candidate_coverage(self):
        d.verify_property_candidates(self.ds, self.ps, complete=True)

    def test_missing_descriptor_duplicate_wrong_identity_and_out_of_range(self):
        cases = ((self.ds[1:], self.ps), (self.ds, self.ps + [self.ps[0]]),
                 ([replace(self.ds[0], name="Synthetic_WRONG"), self.ds[1]], self.ps),
                 (self.ds, [replace(self.ps[0], dataset_id=3), self.ps[1]]))
        for descriptors, properties in cases:
            with self.subTest(descriptors=descriptors, properties=properties), self.assertRaises(d.Rejected):
                d.verify_property_candidates(descriptors, properties, complete=True)

    def test_empty_property_map_does_not_mean_absent_records(self):
        with self.assertRaises(d.Rejected):
            d.verify_property_candidates(self.ds, [], complete=True)

    def test_partial_is_not_complete(self):
        d.verify_property_candidates(self.ds, self.ps[1:], complete=False)
        with self.assertRaises(d.Rejected):
            d.verify_property_candidates(self.ds, self.ps[1:], complete=True)

    def test_partial_duplicate_and_zero_id_reject(self):
        for properties in (self.ps * 2, [replace(self.ps[0], dataset_id=0)],
                           [replace(self.ps[0], dataset_id=True)]):
            with self.subTest(properties=properties), self.assertRaises(d.Rejected):
                d.verify_property_candidates(self.ds, properties, complete=False)

    def test_synthetic_id_above_255_not_truncated_or_renumbered(self):
        descriptors = [d.DescriptorCandidate(f"Synthetic_C{i}", 0) for i in range(1, 301)]
        properties = [d.PropertyCandidate(256, "Synthetic", "C256", 0, 1)]
        d.verify_property_candidates(descriptors, properties, complete=False)
        with self.assertRaises(d.Rejected):
            d.verify_property_candidates(descriptors, properties, complete=True)

    def test_zero_x_stays_absent(self):
        x, y = d.candidate_xy(self.ds, d.GraphCandidate(0, 0, 2))
        self.assertIsNone(x)
        self.assertEqual(y, self.ds[1])

    def test_graph_selector_disagreement_does_not_fallback(self):
        for x, y in ((2, 2), (-1, 2), (3, 2), (1, 0), (1, 3), (True, 2)):
            with self.subTest(x=x, y=y), self.assertRaises(d.Rejected):
                d.candidate_xy(self.ds, d.GraphCandidate(0, x, y))

    def test_unknown_slot_is_not_filtered_or_renumbered(self):
        descriptors = [d.DescriptorCandidate("OpaqueUnknownKind", 0), *self.ds]
        self.assertEqual(d.candidate_xy(descriptors, d.GraphCandidate(0, 0, 2))[1], self.ds[0])
        with self.assertRaises(d.Rejected):
            d.require_supported_binding(descriptors)

    def test_sheet_suffix_preserved_despite_candidate_name_comparison(self):
        descriptors = [d.DescriptorCandidate("Synthetic_A@1", 0), d.DescriptorCandidate("Synthetic_A@2", 0)]
        properties = [d.PropertyCandidate(i, "Synthetic", "A", 0, 1) for i in (1, 2)]
        d.verify_property_candidates(descriptors, properties, complete=True)
        self.assertNotEqual(descriptors[0].name, descriptors[1].name)
        self.assertEqual(len({(p.page, p.name) for p in properties}), 1)
        with self.assertRaises(d.Rejected):
            d.require_supported_binding(descriptors, properties)


class InputRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.input = self.root / "input.bin"
        self.input.write_bytes(b"SYNTHETIC")
        self.digest = hashlib.sha256(b"SYNTHETIC").hexdigest()

    def test_hash_size_missing_and_symlink_rejection(self):
        self.assertEqual(runtime.checked_bytes(self.input, self.digest, 9), b"SYNTHETIC")
        for path, digest, size in ((self.input, "0" * 64, 9), (self.input, self.digest, 8),
                                   (self.root / "missing", self.digest, 9)):
            with self.subTest(path=path), self.assertRaises(d.Rejected):
                runtime.checked_bytes(path, digest, size)
        link = self.root / "link"
        link.symlink_to(self.input)
        with self.assertRaises(d.Rejected):
            runtime.checked_bytes(link, self.digest)

    def test_corpus_requires_explicit_root_and_rejects_missing(self):
        with self.assertRaises(d.Rejected):
            proof.locate_inputs([], "minimal")
        with self.assertRaises(d.Rejected):
            proof.locate_inputs([self.root], "minimal")

    def test_wrong_hash_corpus_never_invokes_runtime(self):
        (self.root / proof.MINIMAL).write_bytes(b"SYNTHETIC")
        with patch.object(proof, "pinned_quantized") as loader, self.assertRaises(d.Rejected):
            proof.run([self.root], self.root, "minimal")
        loader.assert_not_called()

    def test_ambiguous_and_duplicate_roots_reject(self):
        other = self.root / "other"
        other.mkdir()
        for folder in (self.root, other):
            (folder / proof.MINIMAL).write_bytes(b"SYNTHETIC")
        for roots in ([self.root, other], [self.root, self.root]):
            with self.subTest(roots=roots), self.assertRaises(d.Rejected):
                proof.locate_inputs(roots, "minimal")

    def synthetic_runtime(self):
        entries = {}
        for name in runtime.MODULE_ORDER:
            relative = f"io/origin_project/{name}.py"
            data = b"SYNTHETIC = True\n"
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            entries[relative] = hashlib.sha256(data).hexdigest()
        pin = {"revision": runtime.REVISION, "files": entries}
        (self.root / "quantized_sources.json").write_text(json.dumps(pin))
        (self.root / "__init__.py").write_text("raise RuntimeError('MUST NOT EXECUTE')\n")

    def test_only_verified_synthetic_sources_execute_and_namespace_cleans(self):
        self.synthetic_runtime()
        with patch.object(runtime, "HERE", self.root):
            with runtime.pinned_quantized(self.root) as module:
                self.assertTrue(module.SYNTHETIC)
                self.assertTrue(sys.dont_write_bytecode)
            self.assertNotIn("quantized", sys.modules)
        self.assertFalse(list(self.root.rglob("*.pyc")))

    def test_changed_module_rejects_before_execution(self):
        self.synthetic_runtime()
        (self.root / "io/origin_project/opju_codec.py").write_bytes(b"SYNTHETIC = False\n")
        with patch.object(runtime, "HERE", self.root), self.assertRaises(d.Rejected):
            with runtime.pinned_quantized(self.root):
                self.fail("Unverified runtime executed")
        self.assertNotIn("quantized", sys.modules)

    def test_existing_quantized_namespace_is_not_replaced(self):
        self.synthetic_runtime()
        existing = types.ModuleType("quantized")
        with patch.dict(sys.modules, {"quantized": existing}), patch.object(runtime, "HERE", self.root):
            with self.assertRaises(d.Rejected):
                with runtime.pinned_quantized(self.root):
                    self.fail("Mixed runtime accepted")
            self.assertIs(sys.modules["quantized"], existing)

    def test_runtime_namespace_cleaned_on_failure(self):
        self.synthetic_runtime()
        previous = sys.dont_write_bytecode
        with patch.object(runtime, "HERE", self.root), self.assertRaises(RuntimeError):
            with runtime.pinned_quantized(self.root):
                raise RuntimeError("SYNTHETIC failure")
        self.assertNotIn("quantized", sys.modules)
        self.assertEqual(sys.dont_write_bytecode, previous)

    def test_output_never_overwrites_existing_file(self):
        with patch.object(proof, "run") as run, contextlib.redirect_stderr(io.StringIO()):
            result = proof.main(["--public-root", str(self.root), "--quantized-root", str(self.root),
                                 "--out", str(self.input)])
        self.assertEqual(result, 2)
        run.assert_not_called()
        self.assertEqual(self.input.read_bytes(), b"SYNTHETIC")

    def test_expected_counts_and_source_manifest_self_consistency(self):
        expected = json.loads((HERE / "expected_counts.json").read_text())
        summary = expected["all"]["summary"]
        self.assertEqual(summary["explicit_property_candidates"], 313)
        self.assertEqual(summary["complete_candidate_property_ids"], 295)
        self.assertEqual(summary["partial_candidate_property_ids"], 18)
        manifest = json.loads((HERE / "public_sources.json").read_text())
        self.assertEqual(len(manifest["files"]), 110)
        self.assertEqual(sum(f["source"] == "heliox" for f in manifest["files"]), 106)
        self.assertEqual(sum(f["source"] == "dataverse" for f in manifest["files"]), 3)
        self.assertEqual(sum(f["source"] == "spectral" for f in manifest["files"]), 1)
        for source in manifest["sources"].values():
            self.assertIn("license", source)
            self.assertIn("url", source)

    def test_production_safety_checks_are_not_python_asserts(self):
        import ast
        for name in ("diagnostics.py", "runtime.py", "prove_public.py"):
            tree = ast.parse((HERE / name).read_text())
            self.assertFalse(any(isinstance(node, ast.Assert) for node in ast.walk(tree)))


class ExternalPublicProof(unittest.TestCase):
    def test_exact_public_minimal_proof(self):
        corpus = os.environ.get("MODERN_BINDING_PUBLIC_ROOT")
        runtime_root = os.environ.get("MODERN_BINDING_QUANTIZED_ROOT")
        if not corpus and not runtime_root:
            self.skipTest("External public proof requires explicit MODERN_BINDING_PUBLIC_ROOT and MODERN_BINDING_QUANTIZED_ROOT")
        self.assertTrue(corpus and runtime_root, "Both explicit external roots are required")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "counts.json"
            flags = ["-B"] if __debug__ else ["-B", "-O"]
            result = subprocess.run([sys.executable, *flags, str(HERE / "prove_public.py"),
                                     "--public-root", corpus, "--quantized-root", runtime_root,
                                     "--case", "minimal", "--out", str(output)],
                                    capture_output=True, text=True, timeout=120, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text())
            self.assertTrue(report["source_inputs_unchanged"])
            self.assertFalse(report["origin_acceptance"])
            self.assertEqual(report["files"][0]["graphs"][0]["pinned_extracted_rows"], 1)


if __name__ == "__main__":
    unittest.main()
