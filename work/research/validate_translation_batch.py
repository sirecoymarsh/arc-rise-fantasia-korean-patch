#!/usr/bin/env python3
"""Validate a Codex-produced ARF translation JSONL batch against its source."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CONTROL_RE = re.compile(r"<\$[0-9A-F]{2}>")
JAPANESE_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def read_jsonl(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            records.append(value)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("translation", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument(
        "--boundary-audit",
        type=Path,
        help=(
            "Optional verified system-table boundary audit.  For listed TM IDs, "
            "control and line-break checks use clean_source_text rather than the "
            "known-corrupt NUL-scanner source boundary."
        ),
    )
    args = parser.parse_args()
    source = read_jsonl(args.source)
    translated = read_jsonl(args.translation)
    source_by_id = {str(item.get("tm_id")): item for item in source}
    translated_by_id = {str(item.get("tm_id")): item for item in translated}
    errors: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    boundary_units: dict[str, dict[str, object]] = {}
    if args.boundary_audit:
        audit = json.loads(args.boundary_audit.read_text(encoding="utf-8"))
        boundary_units = {
            str(item["tm_id"]): item for item in audit.get("units", [])
        }

    if len(source_by_id) != len(source):
        errors.append({"code": "duplicate_source_id", "count": len(source) - len(source_by_id)})
    if len(translated_by_id) != len(translated):
        errors.append({"code": "duplicate_translation_id", "count": len(translated) - len(translated_by_id)})
    missing = sorted(set(source_by_id) - set(translated_by_id))
    extra = sorted(set(translated_by_id) - set(source_by_id))
    if missing and not args.allow_partial:
        errors.append({"code": "missing_ids", "count": len(missing), "sample": missing[:20]})
    if extra:
        errors.append({"code": "unknown_ids", "count": len(extra), "sample": extra[:20]})

    completed = 0
    hangul: set[str] = set()
    for tm_id, source_item in source_by_id.items():
        item = translated_by_id.get(tm_id)
        if item is None:
            continue
        if item.get("source_text") != source_item.get("source_text"):
            errors.append({"code": "source_text_changed", "tm_id": tm_id})
        translation = str(item.get("translation_ko") or "")
        if not translation.strip():
            if not args.allow_partial:
                errors.append({"code": "empty_translation", "tm_id": tm_id})
            continue
        completed += 1
        comparison_source = str(source_item["source_text"])
        boundary = boundary_units.get(tm_id)
        if boundary is not None:
            comparison_source = str(boundary["clean_source_text"])
        source_controls = CONTROL_RE.findall(comparison_source)
        target_controls = CONTROL_RE.findall(translation)
        if source_controls != target_controls:
            errors.append(
                {
                    "code": "control_token_mismatch",
                    "tm_id": tm_id,
                    "source": source_controls,
                    "translation": target_controls,
                }
            )
        if "\0" in translation:
            errors.append({"code": "embedded_nul", "tm_id": tm_id})
        visible = CONTROL_RE.sub("", translation)
        if "\ufffd" in visible:
            errors.append({"code": "unicode_replacement_character", "tm_id": tm_id})
        question_count = visible.count("?")
        source_question_count = (
            comparison_source.count("?") + comparison_source.count("？")
        )
        hangul_count = sum(
            "가" <= char <= "힣" or "㄰" <= char <= "㆏" for char in visible
        )
        # Repeated ASCII question marks are a valid translation of repeated
        # Japanese full-width question marks.  Flag only newly introduced
        # repetition; otherwise strings such as "？？？" -> "???" are false
        # positives rather than evidence of codepage loss.
        suspicious_questions = (
            "??" in visible
            or (question_count >= 3 and question_count >= hangul_count)
        )
        if suspicious_questions and question_count > source_question_count:
            errors.append(
                {
                    "code": "suspected_codepage_question_mark_corruption",
                    "tm_id": tm_id,
                    "question_mark_count": question_count,
                    "source_question_mark_count": source_question_count,
                    "hangul_count": hangul_count,
                }
            )
        remaining_japanese = sorted(set(JAPANESE_RE.findall(visible)))
        if remaining_japanese:
            warnings.append(
                {
                    "code": "japanese_remaining",
                    "tm_id": tm_id,
                    "characters": "".join(remaining_japanese),
                }
            )
        if comparison_source.count("\n") != translation.count("\n"):
            warnings.append(
                {
                    "code": "line_break_count_changed",
                    "tm_id": tm_id,
                    "source_count": comparison_source.count("\n"),
                    "translation_count": translation.count("\n"),
                }
            )
        hangul.update(char for char in translation if "가" <= char <= "힣" or "㄰" <= char <= "㆏")

    report = {
        "schema": "arf-translation-batch-validation-v2",
        "source": str(args.source.resolve()),
        "translation": str(args.translation.resolve()),
        "source_units": len(source),
        "translation_units": len(translated),
        "completed_units": completed,
        "unique_hangul": len(hangul),
        "hangul_characters": "".join(sorted(hangul, key=ord)),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "valid": not errors,
        "translation_engine_policy": "Codex internal models only",
        "boundary_audit": str(args.boundary_audit.resolve()) if args.boundary_audit else None,
        "boundary_audit_units_available": len(boundary_units),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("completed_units", "error_count", "warning_count", "unique_hangul", "valid")}, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
