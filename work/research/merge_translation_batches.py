#!/usr/bin/env python3
"""Merge validated Codex JSONL translation batches into the ARF translation memory."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


CONTROL_RE = re.compile(r"<\$[0-9A-F]{2}>")


def read_batch(path: Path) -> list[dict[str, object]]:
    result = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected object")
        result.append(value)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("translation_memory", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("batches", type=Path, nargs="+")
    parser.add_argument(
        "--reviewed",
        action="store_true",
        help="Mark every merged unit as independently reviewed and approved.",
    )
    parser.add_argument(
        "--reviewer",
        default="",
        help="Reviewer identifier recorded when --reviewed is used.",
    )
    parser.add_argument(
        "--boundary-audit",
        type=Path,
        help=(
            "Optional verified boundary-audit JSON.  Listed TM IDs may use the "
            "clean field control sequence instead of the scanner-corrupt source."
        ),
    )
    args = parser.parse_args()
    document = json.loads(args.translation_memory.read_text(encoding="utf-8"))
    units = document["units"]
    by_id = {unit["tm_id"]: unit for unit in units}
    boundary_units: dict[str, dict[str, object]] = {}
    if args.boundary_audit:
        audit = json.loads(args.boundary_audit.read_text(encoding="utf-8"))
        boundary_units = {
            str(item["tm_id"]): item for item in audit.get("units", [])
        }
    incoming: dict[str, dict[str, object]] = {}
    source_files: list[str] = []
    for specified in args.batches:
        paths = sorted(specified.glob("*.jsonl")) if specified.is_dir() else [specified]
        for path in paths:
            source_files.append(str(path.resolve()))
            for item in read_batch(path):
                tm_id = str(item.get("tm_id"))
                if tm_id not in by_id:
                    raise ValueError(f"unknown tm_id {tm_id} in {path}")
                if item.get("source_text") != by_id[tm_id]["source_text"]:
                    raise ValueError(f"source_text changed for {tm_id} in {path}")
                translation = str(item.get("translation_ko") or "")
                if not translation.strip():
                    continue
                comparison_source = str(by_id[tm_id]["source_text"])
                if tm_id in boundary_units:
                    comparison_source = str(boundary_units[tm_id]["clean_source_text"])
                source_controls = CONTROL_RE.findall(comparison_source)
                target_controls = CONTROL_RE.findall(translation)
                if source_controls != target_controls:
                    raise ValueError(
                        f"control token mismatch for {tm_id} in {path}: "
                        f"{source_controls!r} != {target_controls!r}"
                    )
                if "\0" in translation:
                    raise ValueError(f"embedded NUL for {tm_id} in {path}")
                visible = CONTROL_RE.sub("", translation)
                question_count = visible.count("?")
                source_question_count = (
                    comparison_source.count("?") + comparison_source.count("？")
                )
                hangul_count = sum(
                    "가" <= char <= "힣" or "㄰" <= char <= "㆏" for char in visible
                )
                if "\ufffd" in visible:
                    raise ValueError(f"Unicode replacement character for {tm_id} in {path}")
                suspicious_questions = (
                    "??" in visible
                    or (question_count >= 3 and question_count >= hangul_count)
                )
                if suspicious_questions and question_count > source_question_count:
                    raise ValueError(
                        f"suspected codepage question-mark corruption for {tm_id} in {path}"
                    )
                previous = incoming.get(tm_id)
                if previous and previous.get("translation_ko") != translation:
                    raise ValueError(f"conflicting translations for {tm_id}")
                incoming[tm_id] = item

    for tm_id, item in incoming.items():
        unit = by_id[tm_id]
        unit["translation_ko"] = item["translation_ko"]
        reviewed = args.reviewed or item.get("review_status") == "approved"
        unit["status"] = "translated" if reviewed else "draft"
        unit["review_status"] = "approved" if reviewed else "pending"
        unit["translator"] = str(item.get("translator") or "Codex internal model")
        unit["reviewer"] = str(item.get("reviewer") or (args.reviewer if reviewed else ""))
        unit["notes"] = item.get("notes", "")
        boundary = boundary_units.get(tm_id)
        if boundary is not None:
            unit["boundary_audit"] = {
                "clean_source_text": boundary["clean_source_text"],
                "table_unit_ids": boundary["table_unit_ids"],
                "anomaly_type": boundary["anomaly_type"],
            }
            if boundary.get("application_mode") == "table_specific_only":
                unit["boundary_audit"].update(
                    {
                        "application_mode": "table_specific_only",
                        "table_specific_translation_ko": boundary[
                            "table_specific_translation_ko"
                        ],
                        "reviewed_tm_translation_preserved": True,
                    }
                )
    document["translated_unit_count"] = sum(bool(str(unit.get("translation_ko", "")).strip()) for unit in units)
    document["reviewed_unit_count"] = sum(unit.get("review_status") == "approved" for unit in units)
    document["translation_engine_policy"] = "Codex internal models only"
    document["boundary_audit"] = (
        str(args.boundary_audit.resolve()) if args.boundary_audit else None
    )
    document["merged_batch_files"] = source_files
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "translation_memory_draft.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    columns = [
        "tm_id",
        "primary_surface",
        "occurrence_count",
        "context_sensitive",
        "source_text",
        "translation_ko",
        "status",
        "review_status",
        "translator",
        "reviewer",
        "notes",
    ]
    with (args.output_dir / "translation_memory_draft.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(units)
    translated = [unit for unit in units if str(unit.get("translation_ko", "")).strip()]
    summary = {
        "schema": "arf-translation-coverage-v1",
        "total_units": len(units),
        "translated_units": len(translated),
        "coverage_percent": round(len(translated) * 100 / len(units), 4),
        "translated_occurrences": sum(int(unit["occurrence_count"]) for unit in translated),
        "total_occurrences": sum(int(unit["occurrence_count"]) for unit in units),
        "translated_by_surface": dict(Counter(str(unit["primary_surface"]) for unit in translated)),
        "reviewed_units": sum(unit.get("review_status") == "approved" for unit in units),
        "translation_engine_policy": "Codex internal models only",
        "batch_files": source_files,
    }
    (args.output_dir / "coverage.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
