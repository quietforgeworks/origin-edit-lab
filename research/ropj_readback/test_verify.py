"""Stdlib contract tests; optional real Ropj tests require explicit environment inputs."""
import csv
import json
import os
import struct
import subprocess
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import verify


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.folder = self.root / "synthetic"
        self.folder.mkdir()
        # An unmistakably fake header stub, never given to the real R reader.
        (self.folder / "workbook.opj").write_bytes(b"CPYA UNIT-TEST-HEADER-ONLY\n")
        self.schema = {"source_kind": "synthetic_demo", "numeric_mode": "binary64",
                       "book": "Synthetic", "columns": [{"header": "Time", "unit": "s"},
                                                           {"header": "Signal", "unit": "mV"}]}
        self.save_schema()
        # Public algorithm: row i has X=i, Y=(-1)^i*(i+1)/10, with row zero Y=-0.
        self.rows = [[str(i), str(Decimal((-1) ** i * (i + 1)) / Decimal(10))]
                     for i in range(7)]
        self.rows[0][1] = "-0"
        self.save_csv()
        self.expected = verify.load_expected(self.folder)
        self.observed = self.root / "observed"
        self.observed.mkdir()
        self.make_observed(self.observed)

    def save_schema(self):
        (self.folder / "schema.json").write_text(json.dumps(self.schema), encoding="utf-8")

    def save_csv(self, header=None):
        with (self.folder / "raw.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header or ["Time", "Signal"])
            writer.writerows(self.rows)

    def tsv(self, path, rows):
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)

    def make_observed(self, directory):
        (directory / "values.f64le").write_bytes(self.expected["payload"])
        (directory / "missing.u8").write_bytes(bytes(14))
        self.info = [{"ropj_version": "0.3-7", "r_version": "unit-test stub",
                      "rows": "7", "columns": "2"}]
        self.metadata = [{"column": str(i + 1), "short_name": chr(65 + i),
                          "comment": c["header"] + "\r\n" + c["unit"], "command": ""}
                         for i, c in enumerate(self.schema["columns"])]
        self.tsv(directory / "reader.tsv", self.info)
        self.tsv(directory / "metadata.tsv", self.metadata)

    def expect_bad_fixture(self):
        with self.assertRaises(verify.VerificationError):
            verify.load_expected(self.folder)

    def expect_bad_output(self):
        with self.assertRaises(verify.VerificationError):
            verify.compare_readback(self.expected, self.observed)

    def test_exact_bytes_and_metadata(self):
        report = verify.compare_readback(self.expected, self.observed)
        self.assertEqual(report["cells"], 14)
        self.assertEqual(report["longname_unit_pairs_equal"], 2)

    def test_negative_zero_is_not_positive_zero(self):
        data = bytearray(self.expected["payload"])
        self.assertEqual(data[56:64], struct.pack("<d", -0.0))
        data[56:64] = struct.pack("<d", 0.0)
        (self.observed / "values.f64le").write_bytes(data)
        self.expect_bad_output()

    def test_row_swap_fails(self):
        data = self.expected["payload"]
        (self.observed / "values.f64le").write_bytes(data[8:16] + data[:8] + data[16:])
        self.expect_bad_output()

    def test_extra_numeric_byte_fails(self):
        (self.observed / "values.f64le").write_bytes(self.expected["payload"] + b"\0")
        self.expect_bad_output()

    def test_missing_flag_and_length_fail(self):
        for bad in (b"\1" + bytes(13), bytes(13), bytes(15)):
            with self.subTest(bad=bad):
                (self.observed / "missing.u8").write_bytes(bad)
                self.expect_bad_output()

    def test_wrong_reader_version_fails(self):
        self.info[0]["ropj_version"] = "0.3-6"
        self.tsv(self.observed / "reader.tsv", self.info)
        self.expect_bad_output()

    def test_wrong_dimensions_fail(self):
        self.info[0]["rows"] = "8"
        self.tsv(self.observed / "reader.tsv", self.info)
        self.expect_bad_output()

    def test_wrong_label_unit_command_order_fail(self):
        for key, value in (("comment", "Time\r\nms"), ("command", "col(A)"),
                           ("column", "2"), ("short_name", "")):
            with self.subTest(key=key):
                self.make_observed(self.observed)
                self.metadata[0][key] = value
                self.tsv(self.observed / "metadata.tsv", self.metadata)
                self.expect_bad_output()

    def test_missing_command_field_fails(self):
        for row in self.metadata:
            del row["command"]
        self.tsv(self.observed / "metadata.tsv", self.metadata)
        self.expect_bad_output()

    def test_ragged_and_empty_csv_cells_fail(self):
        for row in (["0"], ["0", ""]):
            self.rows[0] = row
            self.save_csv()
            self.expect_bad_fixture()

    def test_nonfinite_underflow_and_inexact_integer_fail(self):
        for token in ("NaN", "Inf", "1e999", "1e-999", "9007199254740993", "1_000"):
            with self.subTest(token=token):
                self.rows[0][1] = token
                self.save_csv()
                self.expect_bad_fixture()

    def test_csv_header_mismatch_fails(self):
        self.save_csv(["Time", "Other"])
        self.expect_bad_fixture()

    def test_modern_header_fails(self):
        (self.folder / "workbook.opj").write_bytes(b"CPYUA NOT-REAL-OPJU\n")
        self.expect_bad_fixture()

    def test_nonsynthetic_schema_fails(self):
        self.schema["source_kind"] = "measurement"
        self.save_schema()
        self.expect_bad_fixture()

    def test_duplicate_labels_fail(self):
        self.schema["columns"][1]["header"] = "Time"
        self.save_schema()
        self.expect_bad_fixture()

    def test_label_control_character_fails(self):
        self.schema["columns"][0]["unit"] = "s\nother"
        self.save_schema()
        self.expect_bad_fixture()

    def test_input_symlink_fails(self):
        target = self.folder / "raw.csv"
        moved = self.root / "moved.csv"
        target.rename(moved)
        target.symlink_to(moved)
        self.expect_bad_fixture()

    def test_input_mutation_detected(self):
        (self.folder / "raw.csv").write_bytes(b"changed\n")
        with self.assertRaises(verify.VerificationError):
            verify.check_unchanged(self.folder, self.expected)

    def test_runtime_is_explicit_no_shell_and_no_download(self):
        out = self.root / "case-output"
        def fake_run(command, **kwargs):
            self.assertEqual(command[0], "/explicit/Rscript")
            self.assertIn("--vanilla", command)
            self.assertNotIn("shell", kwargs)
            self.make_observed(out)
            return subprocess.CompletedProcess(command, 0, b"", b"")
        with patch.object(verify.subprocess, "run", side_effect=fake_run) as run:
            report = verify.verify_case(Path("/explicit/Rscript"), self.folder, out)
        self.assertEqual(run.call_count, 1)
        self.assertTrue(report["inputs_unchanged"])

    def test_runtime_failure_is_not_a_pass(self):
        result = subprocess.CompletedProcess([], 1, b"", b"Mixed column")
        with patch.object(verify.subprocess, "run", return_value=result):
            with self.assertRaises(verify.VerificationError):
                verify.verify_case(Path("/explicit/Rscript"), self.folder, self.root / "failed")
        self.assertFalse((self.root / "failed/verification.json").exists())

    def test_timeout_is_not_a_pass(self):
        with patch.object(verify.subprocess, "run", side_effect=subprocess.TimeoutExpired("R", 120)):
            with self.assertRaises(subprocess.TimeoutExpired):
                verify.verify_case(Path("/explicit/Rscript"), self.folder, self.root / "timeout")

    def test_existing_output_is_not_reused(self):
        with self.assertRaises(FileExistsError), patch.object(verify.subprocess, "run") as run:
            verify.verify_case(Path("/explicit/Rscript"), self.folder, self.observed)
        run.assert_not_called()

    def test_case_name_path_traversal_refused(self):
        with self.assertRaises(verify.VerificationError):
            verify.main(["--rscript", "unused", "--fixtures", "unused", "--case", "../escape", "--out", "unused"])

    def test_r_code_never_installs_or_coerces_text(self):
        source = Path(verify.__file__).with_name("readback.R").read_text(encoding="utf-8")
        self.assertNotIn("install.packages", source)
        self.assertNotIn("as.numeric", source)
        self.assertNotIn("eval(", source)
        self.assertIn('identical(typeof(x), "double")', source)


class ExternalRuntimeTests(unittest.TestCase):
    def test_external_synthetic_fixtures(self):
        runtime = os.environ.get("ROPJ_TEST_RSCRIPT")
        fixtures = os.environ.get("ROPJ_TEST_FIXTURES")
        if not runtime or not fixtures:
            self.skipTest("Real Ropj test requires explicit ROPJ_TEST_RSCRIPT and ROPJ_TEST_FIXTURES")
        cases = os.environ.get("ROPJ_TEST_CASES", "decimal7,decimal161,decimal162,decimal257").split(",")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "evidence"
            argv = ["--rscript", runtime, "--fixtures", fixtures, "--out", str(out)]
            for case in cases:
                argv += ["--case", case]
            self.assertEqual(verify.main(argv), 0)
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(len(summary["cases"]), len(cases))
            self.assertGreater(summary["verified_cells"], 0)
            self.assertFalse(summary["origin_reopen"])


if __name__ == "__main__":
    unittest.main()
