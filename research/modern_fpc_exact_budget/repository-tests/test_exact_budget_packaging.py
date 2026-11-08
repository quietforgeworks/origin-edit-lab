"""Read-only repository guards for the frozen codec-only research snapshot."""
from pathlib import Path
import hashlib
import json
import unittest

MODULE = Path(__file__).resolve().parents[1]
SNAPSHOT = MODULE / "snapshot"
REPO = MODULE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ExactBudgetPackagingTests(unittest.TestCase):
    def test_snapshot_inventory(self):
        manifest = json.loads((SNAPSHOT / "MANIFEST.json").read_text())
        actual = {p.relative_to(SNAPSHOT).as_posix() for p in SNAPSHOT.rglob("*") if p.is_file()}
        expected = {row["path"] for row in manifest["files"]} | {"MANIFEST.json", "SHA256SUMS"}
        self.assertEqual(len(actual), 44)
        self.assertEqual(actual, expected)
        for row in manifest["files"]:
            path = SNAPSHOT / row["path"]
            self.assertFalse(path.is_symlink())
            self.assertEqual(path.stat().st_size, row["bytes"])
            self.assertEqual(sha(path), row["sha256"])

    def test_snapshot_checksum_inventory(self):
        records = [(line[:64], line[66:]) for line in (SNAPSHOT / "SHA256SUMS").read_text().splitlines()]
        self.assertEqual(len(records), 43)
        self.assertEqual(len({name for _, name in records}), 43)
        for digest, name in records:
            self.assertEqual(sha(SNAPSHOT / name), digest)

    def test_reviewed_code_and_audit_pins(self):
        pins = {
            "package/code/experimental_exact_fpc.py": "982b2c9119e8a460bcd850e46db14268164dc28a78faf38fc4153123e2031e25",
            "package/code/run_codec_experiments.py": "a0d2ea12255d8fdcecc8ebf0234ad3868a145db27ffe6d0bd755a33e7371df7b",
            "audit/PORTABLE_PUBLIC_AUDIT.md": "63936bda1e969f285be36fd385c732ca242f435e55e87a579fa6c7ad8707c411",
        }
        for name, digest in pins.items():
            self.assertEqual(sha(SNAPSHOT / name), digest)

    def test_fixed_public_provenance(self):
        path = SNAPSHOT / "package/evidence/public-template-streams.json"
        self.assertEqual(sha(path), "4f59150060fd427f97fea59829c8cd7b070010287b6f030097b61c28b89810ec")
        evidence = json.loads(path.read_text())
        self.assertEqual(len(evidence["files"]), 3)
        self.assertEqual(len(evidence["streams"]), 13)
        names = {row["file"] for row in evidence["files"]}
        for row in evidence["files"]:
            self.assertTrue(row["public"])
            self.assertEqual(row["license"], "Etalab-2.0")
            self.assertFalse((SNAPSHOT / row["file"]).exists())
        for row in evidence["streams"]:
            self.assertIn(row["file"], names)
            self.assertEqual(row["end"] - row["start"], row["original_bytes"])

    def test_recorded_portable_evidence(self):
        for mode in ("normal", "optimized"):
            oracle = json.loads((SNAPSHOT / f"package/results/oracle-{mode}.json").read_text())
            self.assertEqual(oracle["width_multisets_through_length_12"], 125970)
            self.assertEqual(oracle["word_streams_through_length_3"], 1111)
            self.assertEqual(oracle["serialized_encodings_independently_decoded"], 63627)
            adversarial = json.loads((SNAPSHOT / f"package/results/adversarial-{mode}.json").read_text())
            self.assertEqual(adversarial["accepted_budgets"], 12465)
            self.assertEqual(adversarial["rejected_budgets"], 18656)
            self.assertEqual(adversarial["invalid_calls"], 43)
            self.assertEqual(adversarial["hard_boundary_streams"], 2)

    def test_root_inventory_license_and_source_only(self):
        manifest_path = REPO / "SOURCE-PACKAGE-MANIFEST.json"
        self.assertEqual((REPO / "SOURCE-PACKAGE-MANIFEST.json.sha256").read_text().split()[0], sha(manifest_path))
        inventory = {row["path"]: row for row in json.loads(manifest_path.read_text())["files"]}
        for path in MODULE.rglob("*"):
            self.assertFalse(path.is_symlink())
            if path.is_file():
                self.assertNotIn(path.suffix.lower(), {".pyc", ".opju", ".opj", ".oggu", ".ole", ".pptx", ".png", ".jpg", ".exe"})
                row = inventory[path.relative_to(REPO).as_posix()]
                self.assertEqual(sha(path), row["sha256"])
                self.assertEqual(path.stat().st_size, row["bytes"])
        self.assertIn("MIT License", (SNAPSHOT / "package/LICENSE").read_text())


if __name__ == "__main__":
    unittest.main()
