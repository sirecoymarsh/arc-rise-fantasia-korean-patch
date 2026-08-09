#!/usr/bin/env python3
"""Validate independently reviewed Arc Rise Fantasia translation batches."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


CONTROL_RE = re.compile(r"<\$[0-9A-F]{2}>")
ACCEPTED_POLICY_LABELS = {
    "Codex internal models only",
    "Codex internal model only",
    "Codex 내부 모델 전용",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("batches", nargs="+")
    parser.add_argument("--boundary-audit", type=Path)
    parser.add_argument(
        "--batch-manifest",
        type=Path,
        help=(
            "Batch manifest containing the authoritative per-batch unit_count. "
            "Defaults to work/translation/tm_v2/batch_manifest.json under root."
        ),
    )
    parser.add_argument(
        "--validation-dir",
        type=Path,
        help=(
            "Directory containing batch_NNNN_reviewed.json reports. Relative "
            "paths are resolved below root; defaults to "
            "work/translation/validation."
        ),
    )
    parser.add_argument("--require-zero-warnings", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()

    def resolve_under_root(path: Path | None, default: str) -> Path:
        selected = path if path is not None else Path(default)
        return selected.resolve() if selected.is_absolute() else (root / selected).resolve()

    manifest_path = resolve_under_root(
        args.batch_manifest, "work/translation/tm_v2/batch_manifest.json"
    )
    validation_dir = resolve_under_root(
        args.validation_dir, "work/translation/validation"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_counts: dict[str, int] = {}
    for entry in manifest.get("batches", []):
        batch_name = Path(str(entry["file"])).stem
        if batch_name in manifest_counts:
            raise ValueError(f"duplicate batch in manifest: {batch_name}")
        manifest_counts[batch_name] = int(entry["unit_count"])
    if not manifest_counts:
        raise ValueError(f"batch manifest contains no batches: {manifest_path}")
    manifest_unit_count = sum(manifest_counts.values())
    if int(manifest.get("unit_count", manifest_unit_count)) != manifest_unit_count:
        raise ValueError(
            "batch manifest unit_count does not equal the sum of per-batch unit_count"
        )

    boundary_by_id: dict[str, dict[str, object]] = {}
    if args.boundary_audit:
        boundary = json.loads(args.boundary_audit.read_text(encoding="utf-8"))
        boundary_by_id = {
            str(item["tm_id"]): item for item in boundary.get("units", [])
        }

    errors: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    union_ids: set[str] = set()
    requested_batches: list[str] = []

    def require(condition: bool, code: str, **details: object) -> None:
        if not condition:
            errors.append({"code": code, **details})

    for raw_batch in args.batches:
        normalized = Path(raw_batch).stem
        batch = normalized if normalized.startswith("batch_") else f"batch_{normalized}"
        if batch in requested_batches:
            errors.append({"code": "duplicate_batch_argument", "batch": batch})
            continue
        requested_batches.append(batch)
        if batch not in manifest_counts:
            errors.append({"code": "batch_missing_from_manifest", "batch": batch})
            continue
        expected_units = manifest_counts[batch]
        source_path = root / f"work/translation/tm_v2/batches/source/{batch}.jsonl"
        draft_path = root / f"work/translation/drafts/{batch}.jsonl"
        reviewed_path = root / f"work/translation/reviewed/{batch}.jsonl"
        review_path = root / f"work/translation/reviews/{batch}_review.json"
        validation_path = validation_dir / f"{batch}_reviewed.json"

        source = read_jsonl(source_path)
        draft = read_jsonl(draft_path)
        reviewed = read_jsonl(reviewed_path)
        review = json.loads(review_path.read_text(encoding="utf-8"))
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        source_ids = [str(item["tm_id"]) for item in source]
        draft_ids = [str(item["tm_id"]) for item in draft]
        reviewed_ids = [str(item["tm_id"]) for item in reviewed]

        require(
            len(source) == expected_units,
            "source_count",
            batch=batch,
            expected=expected_units,
            actual=len(source),
        )
        require(
            len(draft) == expected_units,
            "draft_count",
            batch=batch,
            expected=expected_units,
            actual=len(draft),
        )
        require(
            len(reviewed) == expected_units,
            "reviewed_count",
            batch=batch,
            expected=expected_units,
            actual=len(reviewed),
        )
        require(
            source_ids == draft_ids == reviewed_ids,
            "id_or_order_mismatch",
            batch=batch,
        )
        require(len(set(reviewed_ids)) == len(reviewed_ids), "duplicate_id", batch=batch)
        duplicate_cross_batch = sorted(set(reviewed_ids) & union_ids)
        require(
            not duplicate_cross_batch,
            "cross_batch_duplicate_id",
            batch=batch,
            sample=duplicate_cross_batch[:10],
        )
        union_ids.update(reviewed_ids)

        metadata_mismatches = []
        token_mismatches = []
        line_break_mismatches = []
        blank_targets = []
        for source_item, reviewed_item in zip(source, reviewed):
            tm_id = str(source_item["tm_id"])
            source_metadata = {
                key: value
                for key, value in source_item.items()
                if key not in {"translation_ko", "notes", "boundary_audit"}
            }
            reviewed_metadata = {
                key: value
                for key, value in reviewed_item.items()
                if key not in {"translation_ko", "notes", "boundary_audit"}
            }
            if source_metadata != reviewed_metadata:
                metadata_mismatches.append(tm_id)
            target = str(reviewed_item.get("translation_ko") or "")
            if not target.strip():
                blank_targets.append(tm_id)
            comparison_source = str(source_item["source_text"])
            if tm_id in boundary_by_id:
                comparison_source = str(boundary_by_id[tm_id]["clean_source_text"])
            if CONTROL_RE.findall(comparison_source) != CONTROL_RE.findall(target):
                token_mismatches.append(tm_id)
            if comparison_source.count("\n") != target.count("\n"):
                line_break_mismatches.append(tm_id)

        require(
            not metadata_mismatches,
            "source_metadata_changed",
            batch=batch,
            sample=metadata_mismatches[:10],
        )
        require(not blank_targets, "blank_target", batch=batch, sample=blank_targets[:10])
        require(
            not token_mismatches,
            "control_token_mismatch",
            batch=batch,
            sample=token_mismatches[:10],
        )
        if args.require_zero_warnings:
            require(
                not line_break_mismatches,
                "line_break_mismatch",
                batch=batch,
                sample=line_break_mismatches[:10],
            )
        reviewer = str(
            review.get("reviewer") or review.get("independent_reviewer") or ""
        )
        drafter = str(
            review.get("draft_author") or review.get("draft_translator") or ""
        )
        review_schema = str(review.get("schema") or "")
        independently_reviewed = (
            review.get("independent_review") is True
            or "independent-review" in review_schema
            or (bool(reviewer) and bool(drafter) and reviewer != drafter)
        )
        require(independently_reviewed, "review_not_independent", batch=batch)
        policy_label = str(
            review.get("translation_engine_policy")
            or review.get("translation_method")
            or ""
        )
        require(
            policy_label in ACCEPTED_POLICY_LABELS,
            "review_policy_mismatch",
            batch=batch,
            actual=policy_label,
        )
        external_records = [
            review[key]
            for key in (
                "external_translation_services_used",
                "external_translation_models_or_apis_used",
                "external_services_used",
                "external_service_status",
            )
            if key in review
        ]

        def is_no_external_use(value: object) -> bool:
            if value is None or value is False or value == []:
                return True
            if isinstance(value, str):
                return value.strip().casefold() in {
                    "",
                    "none",
                    "not used",
                    "없음",
                    "미사용",
                }
            return False

        require(
            bool(external_records)
            and all(is_no_external_use(value) for value in external_records),
            "external_translation_service_recorded",
            batch=batch,
            actual=external_records,
        )
        if drafter and reviewer:
            require(
                drafter != reviewer,
                "same_drafter_and_reviewer",
                batch=batch,
            )
        reported_reviewed_units = review.get(
            "reviewed_units", review.get("reviewed_record_count")
        )
        if reported_reviewed_units is not None:
            require(
                int(reported_reviewed_units) == expected_units,
                "review_report_unit_count",
                batch=batch,
                expected=expected_units,
                actual=reported_reviewed_units,
            )
        require(
            validation.get("source_units") == expected_units,
            "validation_source_count",
            batch=batch,
            expected=expected_units,
            actual=validation.get("source_units"),
        )
        require(
            validation.get("translation_units") == expected_units,
            "validation_translation_count",
            batch=batch,
            expected=expected_units,
            actual=validation.get("translation_units"),
        )
        require(
            validation.get("completed_units") == expected_units,
            "validation_count",
            batch=batch,
            expected=expected_units,
            actual=validation.get("completed_units"),
        )
        require(validation.get("error_count") == 0, "validation_errors", batch=batch)
        require(validation.get("valid") is True, "validation_invalid", batch=batch)
        if args.require_zero_warnings:
            require(validation.get("warning_count") == 0, "validation_warnings", batch=batch)

        summaries.append(
            {
                "batch": batch,
                "units": len(reviewed),
                "expected_units": expected_units,
                "modified_units": sum(
                    str(a.get("translation_ko") or "")
                    != str(b.get("translation_ko") or "")
                    for a, b in zip(draft, reviewed)
                ),
                "validator_errors": validation.get("error_count"),
                "validator_warnings": validation.get("warning_count"),
                "line_break_mismatch_count": len(line_break_mismatches),
                "line_break_mismatch_sample": line_break_mismatches[:10],
                "reviewer": reviewer,
                "drafter": drafter or None,
                "review_policy_label": policy_label,
                "source_sha256": sha256(source_path),
                "draft_sha256": sha256(draft_path),
                "reviewed_sha256": sha256(reviewed_path),
                "review_report_sha256": sha256(review_path),
                "validation_sha256": sha256(validation_path),
            }
        )

    expected_requested_units = sum(
        manifest_counts[batch]
        for batch in requested_batches
        if batch in manifest_counts
    )
    require(
        len(union_ids) == expected_requested_units,
        "reviewed_union_count",
        expected=expected_requested_units,
        actual=len(union_ids),
    )
    supplied_set = set(requested_batches)
    manifest_set = set(manifest_counts)
    report = {
        "schema": "arf-reviewed-translation-chain-validation-v1",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "batch_manifest": str(manifest_path),
        "batch_manifest_sha256": sha256(manifest_path),
        "manifest_batch_count": len(manifest_counts),
        "manifest_unit_count": manifest_unit_count,
        "validation_dir": str(validation_dir),
        "batches": summaries,
        "batch_count": len(summaries),
        "expected_reviewed_units": expected_requested_units,
        "reviewed_units": len(union_ids),
        "all_manifest_batches_supplied": supplied_set == manifest_set,
        "missing_manifest_batches": sorted(manifest_set - supplied_set),
        "unexpected_batches": sorted(supplied_set - manifest_set),
        "error_count": len(errors),
        "errors": errors,
        "valid": not errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "batches": report["batch_count"],
                "reviewed_units": report["reviewed_units"],
                "error_count": report["error_count"],
                "valid": report["valid"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
