#!/usr/bin/env python3
"""Apply verified scanner-boundary repairs to reviewed ARF translation batches.

This is a deterministic metadata/translation repair.  It consumes only the
Codex-produced offset audit and never changes TM source IDs or source text.
Structured-table insertion uses the audited table_unit_ids stored on each unit.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "work/translation/boundary_audit/batches_0001_0002.json"
EXPECTED_AUDIT_SHA256 = "E47BA47E1B2A33940EB08EFFFF1E313FD6ACC4F23D63C5219680D63DBAEE80C7"
APPLICATION_PATH = ROOT / "work/translation/boundary_audit/application_report.json"
BATCHES = ("batch_0001", "batch_0002")
EXPECTED_AUDITED_UNITS = 61

# help:295:title is fixed at 21 bytes including NUL.  This internal-model
# rewrite preserves the meaning while using exactly 20 encoded payload bytes.
TRANSLATION_OVERRIDES = {
    "ARF-TM-019ABE60D53A27F0D5E8": "코핀에게 전해진 진실",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records),
        encoding="utf-8",
    )


def main() -> int:
    actual_audit_hash = sha256(AUDIT_PATH)
    if actual_audit_hash != EXPECTED_AUDIT_SHA256:
        raise ValueError(
            f"boundary audit hash mismatch: {actual_audit_hash} != "
            f"{EXPECTED_AUDIT_SHA256}"
        )
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    audit_units = {str(item["tm_id"]): item for item in audit["units"]}
    if len(audit_units) != EXPECTED_AUDITED_UNITS:
        raise ValueError(
            f"expected {EXPECTED_AUDITED_UNITS} audited units, "
            f"found {len(audit_units)}"
        )

    adjustments: list[dict[str, object]] = []
    found_ids: set[str] = set()
    batch_results: dict[str, dict[str, object]] = {}

    for batch_name in BATCHES:
        reviewed_path = ROOT / f"work/translation/reviewed/{batch_name}.jsonl"
        draft_path = ROOT / f"work/translation/drafts/{batch_name}.jsonl"
        review_path = ROOT / f"work/translation/reviews/{batch_name}_review.json"
        records = read_jsonl(reviewed_path)

        for record in records:
            tm_id = str(record["tm_id"])
            boundary = audit_units.get(tm_id)
            if boundary is None:
                continue
            found_ids.add(tm_id)
            original_before = str(
                boundary["approved_translation_before_boundary_audit"]
            )
            application_mode = str(boundary.get("application_mode") or "tm_rewrite")
            if application_mode == "table_specific_only":
                if str(record.get("translation_ko") or "") != original_before:
                    raise ValueError(
                        f"table-specific TM target changed before application: {tm_id}"
                    )
                after = original_before
            else:
                after = TRANSLATION_OVERRIDES.get(
                    tm_id, str(boundary["clean_translation_ko"])
                )
            record["translation_ko"] = after
            record["boundary_audit"] = {
                "clean_source_text": boundary["clean_source_text"],
                "table_unit_ids": boundary["table_unit_ids"],
                "anomaly_type": boundary["anomaly_type"],
                "capacity_including_nul": boundary["capacity"],
            }
            if application_mode == "table_specific_only":
                record["boundary_audit"].update(
                    {
                        "application_mode": application_mode,
                        "table_specific_translation_ko": boundary[
                            "table_specific_translation_ko"
                        ],
                        "reviewed_tm_translation_preserved": True,
                    }
                )
            marker = (
                "[boundary-audit] Verified exact table-field mapping; use "
                "clean_source_text/table_unit_ids for insertion."
            )
            notes = str(record.get("notes") or "")
            if marker not in notes:
                record["notes"] = (notes + (" " if notes else "") + marker).strip()
            if original_before != after:
                adjustments.append(
                    {
                        "batch_id": batch_name,
                        "tm_id": tm_id,
                        "corrupt_scanner_source_text": boundary[
                            "corrupt_scanner_source_text"
                        ],
                        "clean_source_text": boundary["clean_source_text"],
                        "before": original_before,
                        "after": after,
                        "table_unit_ids": boundary["table_unit_ids"],
                        "anomaly_type": boundary["anomaly_type"],
                        "capacity_including_nul": boundary["capacity"],
                        "reason": (
                            "fixed-title compact internal-model rewrite"
                            if tm_id in TRANSLATION_OVERRIDES
                            else "verified scanner-boundary repair"
                        ),
                    }
                )

        write_jsonl(reviewed_path, records)

        draft_by_id = {
            str(item["tm_id"]): item for item in read_jsonl(draft_path)
        }
        modified = sum(
            str(item.get("translation_ko", ""))
            != str(draft_by_id[str(item["tm_id"])].get("translation_ko", ""))
            for item in records
        )
        batch_audited = sum(str(item["tm_id"]) in audit_units for item in records)
        review = json.loads(review_path.read_text(encoding="utf-8"))
        review["modified_units"] = modified
        review["unchanged_units"] = len(records) - modified
        review["boundary_audit_application"] = {
            "status": "applied",
            "source": str(AUDIT_PATH.relative_to(ROOT)).replace("\\", "/"),
            "source_sha256": actual_audit_hash,
            "audited_units_in_batch": batch_audited,
            "translation_engine_policy": "Codex internal models only",
            "external_translation_models_or_apis_used": False,
            "insertion_contract": (
                "Use clean_source_text and exact table_unit_ids; do not replace "
                "the corrupt NUL-scanner byte span."
            ),
        }
        if isinstance(review.get("final_change_summary"), dict):
            review["final_change_summary"][
                "final_modified_units_against_original_draft"
            ] = modified
            review["final_change_summary"][
                "final_unchanged_units_against_original_draft"
            ] = len(records) - modified
        review.setdefault("hashes", {})["reviewed_sha256"] = sha256(reviewed_path)
        validation_path = (
            ROOT / f"work/translation/validation/{batch_name}_reviewed.json"
        )
        if validation_path.is_file():
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
            review["boundary_audit_application"]["validation"] = {
                "report": str(validation_path.relative_to(ROOT)).replace("\\", "/"),
                "error_count": validation["error_count"],
                "warning_count": validation["warning_count"],
                "valid": validation["valid"],
                "boundary_audit_units_available": validation.get(
                    "boundary_audit_units_available", 0
                ),
            }
            if isinstance(review.get("validation"), dict):
                review["validation"].update(
                    {
                        "validator_error_count": validation["error_count"],
                        "validator_warning_count": validation["warning_count"],
                        "validator_warnings": validation["warnings"],
                        "status": "passed" if validation["valid"] else "failed",
                    }
                )
            if isinstance(review.get("layout_validation"), dict) and isinstance(
                review["layout_validation"].get("batch_validator"), dict
            ):
                review["layout_validation"]["batch_validator"].update(
                    {
                        "error_count": validation["error_count"],
                        "warning_count": validation["warning_count"],
                        "valid": validation["valid"],
                    }
                )
            review["hashes"]["validation_sha256"] = sha256(validation_path)
        review_path.write_text(
            json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        batch_results[batch_name] = {
            "audited_units": batch_audited,
            "modified_against_draft": modified,
            "reviewed_sha256": sha256(reviewed_path),
        }

    missing = sorted(set(audit_units) - found_ids)
    if missing:
        raise ValueError(f"audited IDs not found in reviewed batches: {missing}")

    application = {
        "schema": "arf-system-table-boundary-audit-application-v1",
        "game_id": "RPJJ99",
        "audit": str(AUDIT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "audit_sha256": actual_audit_hash,
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "audited_units": len(audit_units),
        "translation_adjustments_this_application": len(adjustments),
        "special_fixed_title_rewrites": len(TRANSLATION_OVERRIDES),
        "batches": batch_results,
        "adjustments": adjustments,
    }
    APPLICATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    APPLICATION_PATH.write_text(
        json.dumps(application, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "audited_units": len(audit_units),
                "adjustments": len(adjustments),
                "application_report": str(APPLICATION_PATH),
                "batches": batch_results,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
