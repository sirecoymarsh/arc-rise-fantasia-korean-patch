#!/usr/bin/env python3
"""Compose the final font-encoding unit list from TM and main.dol inputs.

The base approved-unit JSONL is produced by ``build_approved_corpus.py``.  The
supplement is the independently reviewed 926-row main.dol translation JSONL.
This builder normalizes only line endings (LF) and records exact input/output
hashes so the font verification cannot silently remain bound to an older TM.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def lines(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_approved_units", type=Path)
    parser.add_argument("main_dol_translations", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--expected-base", type=int, default=29_777)
    parser.add_argument("--expected-main-dol", type=int, default=926)
    args = parser.parse_args()

    base_lines = lines(args.base_approved_units)
    supplemental_lines = lines(args.main_dol_translations)
    base_rows = [json.loads(line) for line in base_lines]
    supplemental_rows = [json.loads(line) for line in supplemental_lines]
    if len(base_rows) != args.expected_base:
        raise ValueError(
            f"base approved-unit count mismatch: {len(base_rows)} != {args.expected_base}"
        )
    if len(supplemental_rows) != args.expected_main_dol:
        raise ValueError(
            "main.dol translation count mismatch: "
            f"{len(supplemental_rows)} != {args.expected_main_dol}"
        )
    if any(set(row) != {"tm_id", "translation_ko"} for row in base_rows):
        raise ValueError("base approved units do not have the canonical two-field schema")
    tm_ids = [str(row["tm_id"]) for row in base_rows]
    if len(tm_ids) != len(set(tm_ids)):
        raise ValueError("duplicate TM ID in base approved units")
    if any(not str(row.get("translation_ko", "")).strip() for row in base_rows):
        raise ValueError("blank base approved translation")
    if any(not str(row.get("translation_ko", "")).strip() for row in supplemental_rows):
        raise ValueError("blank main.dol approved translation")

    output_bytes = ("\n".join(base_lines + supplemental_lines) + "\n").encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_bytes(output_bytes)
    os.replace(temporary, args.output)

    manifest_path = args.manifest or args.output.with_name(
        args.output.stem + "_manifest.json"
    )
    report = {
        "schema": "arf-final-font-approved-units-manifest-v1",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "base_approved_units": str(args.base_approved_units.resolve()),
        "base_approved_units_sha256": sha256(args.base_approved_units),
        "base_approved_units_count": len(base_rows),
        "main_dol_translations": str(args.main_dol_translations.resolve()),
        "main_dol_translations_sha256": sha256(args.main_dol_translations),
        "main_dol_translation_count": len(supplemental_rows),
        "output": str(args.output.resolve()),
        "output_sha256": sha256(args.output),
        "output_count": len(base_rows) + len(supplemental_rows),
        "line_endings": "LF",
        "valid": True,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_temp = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    manifest_temp.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(manifest_temp, manifest_path)
    print(json.dumps({**report, "manifest": str(manifest_path.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
