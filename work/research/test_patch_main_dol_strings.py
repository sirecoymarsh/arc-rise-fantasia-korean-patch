#!/usr/bin/env python3
"""Unit and CLI tests for patch_main_dol_strings.py."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
TOOL = HERE / "patch_main_dol_strings.py"
ENCODER = HERE / "encode_custom_euc28.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("patch_main_dol_strings_under_test", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PATCHER = load_tool()


class MainDolPatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "main.dol"
        # Two independent fields: [4,8)+NUL and [12,18)+NUL.
        self.source_bytes = b"HEAD" + "日本".encode("euc_jp") + b"\0XYZ" + "テスト".encode("euc_jp") + b"\0TAIL"
        self.source.write_bytes(self.source_bytes)
        self.source_sha = hashlib.sha256(self.source_bytes).hexdigest().upper()
        self.codebook = self.root / "codebook.json"
        self.codebook.write_text(
            json.dumps(
                {
                    "format": PATCHER.CODEBOOK_FORMAT,
                    "characters": {
                        "한": {"bytes_hex": "B0A1"},
                        "글": {"bytes_hex": "B0A2"},
                        "가": {"bytes_hex": "B0A3"},
                        "나": {"bytes_hex": "B0A4"},
                        "다": {"bytes_hex": "B0A5"},
                        "라": {"bytes_hex": "B0A6"},
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.translations = self.root / "translations.jsonl"
        self.output = self.root / "patched.dol"
        self.report = self.root / "report.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_rows(self, rows: list[dict]) -> None:
        self.translations.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
            encoding="utf-8",
        )

    def run_patch(self):
        return PATCHER.patch_file(
            self.source,
            self.translations,
            self.codebook,
            self.output,
            self.report,
            self.source_sha,
            ENCODER,
        )

    def test_success_preserves_size_terminators_and_zero_pads(self) -> None:
        self.write_rows(
            [
                {
                    "id": "field-a",
                    "offset": 4,
                    "byte_length": 4,
                    "raw_hex": "日本".encode("euc_jp").hex(),
                    "source_text": "日本",
                    "translation_ko": "한",
                },
                {
                    "id": "field-b",
                    "offset": 12,
                    "byte_length": 6,
                    "raw_hex": "テスト".encode("euc_jp").hex(),
                    "translation_ko": "글가",
                },
            ]
        )
        report = self.run_patch()
        result = self.output.read_bytes()
        self.assertEqual(len(result), len(self.source_bytes))
        self.assertEqual(result[4:8], bytes.fromhex("B0A1") + b"\0\0")
        self.assertEqual(result[8], 0)
        self.assertEqual(result[12:18], bytes.fromhex("B0A2B0A3") + b"\0\0")
        self.assertEqual(result[18], 0)
        self.assertEqual(result[:4], self.source_bytes[:4])
        self.assertEqual(result[9:12], self.source_bytes[9:12])
        self.assertEqual(result[19:], self.source_bytes[19:])
        self.assertTrue(report["valid"])
        self.assertTrue(report["summary"]["all_original_raw_verified"])
        self.assertTrue(report["summary"]["all_original_terminating_nuls_preserved"])
        self.assertEqual(report["output"]["sha256"], hashlib.sha256(result).hexdigest().upper())
        self.assertEqual(json.loads(self.report.read_text(encoding="utf-8")), report)

    def assert_rejected_without_output(self, expected_message: str) -> None:
        with self.assertRaisesRegex(PATCHER.PatchError, expected_message):
            self.run_patch()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.report.exists())

    def test_rejects_source_sha_mismatch(self) -> None:
        self.write_rows([{"offset": 4, "byte_length": 4, "raw_hex": "C6FCCBDC", "translation_ko": "한"}])
        self.source_sha = "00" * 32
        self.assert_rejected_without_output("source SHA-256 mismatch")

    def test_rejects_raw_mismatch(self) -> None:
        self.write_rows([{"offset": 4, "byte_length": 4, "raw_hex": "41414141", "translation_ko": "한"}])
        self.assert_rejected_without_output("original raw bytes mismatch")

    def test_rejects_capacity_overflow(self) -> None:
        self.write_rows([{"offset": 4, "byte_length": 4, "raw_hex": "C6FCCBDC", "translation_ko": "한글가"}])
        self.assert_rejected_without_output("encoded translation is 6 bytes, capacity is 4")

    def test_rejects_missing_original_terminator(self) -> None:
        damaged = bytearray(self.source_bytes)
        damaged[8] = 0x7F
        self.source.write_bytes(damaged)
        self.source_sha = hashlib.sha256(damaged).hexdigest().upper()
        self.write_rows([{"offset": 4, "byte_length": 4, "raw_hex": "C6FCCBDC", "translation_ko": "한"}])
        self.assert_rejected_without_output("not NUL-terminated")

    def test_rejects_overlap_or_shared_terminator(self) -> None:
        self.write_rows(
            [
                {"offset": 4, "byte_length": 4, "raw_hex": "C6FCCBDC", "translation_ko": "한"},
                {"offset": 6, "byte_length": 2, "raw_hex": "CBDC", "translation_ko": "A"},
            ]
        )
        self.assert_rejected_without_output("overlapping spans or shared terminator")

    def test_rejects_control_code_that_encodes_nul(self) -> None:
        self.write_rows([{"offset": 4, "byte_length": 4, "raw_hex": "C6FCCBDC", "translation_ko": "<$00>"}])
        self.assert_rejected_without_output("encoded translation contains NUL")

    def test_refuses_source_overwrite(self) -> None:
        self.write_rows([{"offset": 4, "byte_length": 4, "raw_hex": "C6FCCBDC", "translation_ko": "한"}])
        self.output = self.source
        before = self.source.read_bytes()
        with self.assertRaisesRegex(PATCHER.PatchError, "refusing to overwrite"):
            self.run_patch()
        self.assertEqual(self.source.read_bytes(), before)
        self.assertFalse(self.report.exists())

    def test_cli_success(self) -> None:
        self.write_rows([{"offset": 4, "byte_length": 4, "raw_hex": "C6FCCBDC", "translation_ko": "한글"}])
        process = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                str(self.source),
                str(self.translations),
                str(self.codebook),
                str(self.output),
                str(self.report),
                "--expected-source-sha256",
                self.source_sha,
                "--encoder",
                str(ENCODER),
            ],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        summary = json.loads(process.stdout)
        self.assertTrue(summary["valid"])
        self.assertEqual(summary["patch_rows"], 1)
        self.assertTrue(self.output.is_file())
        self.assertTrue(self.report.is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
