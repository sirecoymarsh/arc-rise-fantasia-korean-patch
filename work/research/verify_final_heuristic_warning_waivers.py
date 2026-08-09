#!/usr/bin/env python3
"""Verify that every remaining final validator warning has an exact QA waiver."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WAIVERS = ROOT / "work/translation/final_validation/heuristic_warning_waivers.json"
APPLICATION = ROOT / "work/translation/final_validation/heuristic_warning_qa_application.json"
REVIEW_CHAIN = ROOT / "work/translation/final_validation/review_chain.json"
OUTPUT = ROOT / "work/translation/final_validation/heuristic_warning_waiver_verification.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def warning_key(batch: str, tm_id: str, warning: dict[str, object]) -> tuple:
    return (
        batch,
        tm_id,
        str(warning.get("code")),
        str(warning.get("characters", "")),
        int(warning.get("source_count", -1)),
        int(warning.get("translation_count", -1)),
    )


def main() -> int:
    waiver_doc = json.loads(WAIVERS.read_text(encoding="utf-8"))
    application = json.loads(APPLICATION.read_text(encoding="utf-8"))
    review_chain = json.loads(REVIEW_CHAIN.read_text(encoding="utf-8"))
    errors: list[dict[str, object]] = []

    waiver_by_key = {
        warning_key(str(item["batch"]), str(item["tm_id"]), item["warning"]): item
        for item in waiver_doc["waivers"]
    }
    if len(waiver_by_key) != len(waiver_doc["waivers"]):
        errors.append({"code": "duplicate_waiver_key"})

    current_by_key: dict[tuple, dict[str, object]] = {}
    for path in sorted(
        (ROOT / "work/translation/final_validation").glob("batch_*_reviewed.json")
    ):
        batch = path.name.replace("_reviewed.json", "")
        validation = json.loads(path.read_text(encoding="utf-8"))
        if validation.get("valid") is not True or int(validation.get("error_count", -1)):
            errors.append({"code": "invalid_batch_validation", "batch": batch})
        reviewed_path = ROOT / "work/translation/reviewed" / f"{batch}.jsonl"
        reviewed = {str(item["tm_id"]): item for item in read_jsonl(reviewed_path)}
        reviewed_hash = sha256(reviewed_path)
        for warning in validation.get("warnings", []):
            tm_id = str(warning["tm_id"])
            key = warning_key(batch, tm_id, warning)
            if key in current_by_key:
                errors.append({"code": "duplicate_current_warning", "key": key})
                continue
            current_by_key[key] = {
                "batch": batch,
                "tm_id": tm_id,
                "warning": warning,
                "translation_ko": reviewed[tm_id]["translation_ko"],
                "reviewed_batch_sha256": reviewed_hash,
            }

    missing_waivers = sorted(set(current_by_key) - set(waiver_by_key))
    stale_waivers = sorted(set(waiver_by_key) - set(current_by_key))
    if missing_waivers:
        errors.append(
            {"code": "unwaived_current_warning", "count": len(missing_waivers), "sample": missing_waivers[:20]}
        )
    if stale_waivers:
        errors.append(
            {"code": "stale_waiver", "count": len(stale_waivers), "sample": stale_waivers[:20]}
        )

    target_mismatches = []
    batch_hash_mismatches = []
    for key in sorted(set(current_by_key) & set(waiver_by_key)):
        current = current_by_key[key]
        waiver = waiver_by_key[key]
        if current["translation_ko"] != waiver["translation_ko"]:
            target_mismatches.append(current["tm_id"])
        if current["reviewed_batch_sha256"] != waiver["reviewed_batch_sha256"]:
            batch_hash_mismatches.append(current["tm_id"])
    if target_mismatches:
        errors.append(
            {"code": "waived_target_changed", "count": len(target_mismatches), "sample": target_mismatches[:20]}
        )
    if batch_hash_mismatches:
        errors.append(
            {
                "code": "waiver_reviewed_batch_hash_changed",
                "count": len(batch_hash_mismatches),
                "sample": batch_hash_mismatches[:20],
            }
        )

    corrected_warning_ids = {
        str(item["tm_id"])
        for item in application["corrections"]
        if item.get("warning_code") is not None
    }
    still_warning = sorted(
        corrected_warning_ids
        & {str(item["tm_id"]) for item in current_by_key.values()}
    )
    if still_warning:
        errors.append(
            {"code": "corrected_warning_still_present", "count": len(still_warning), "sample": still_warning}
        )

    if review_chain.get("valid") is not True or int(review_chain.get("error_count", -1)):
        errors.append({"code": "review_chain_invalid"})
    if int(review_chain.get("reviewed_units", -1)) != 29_777:
        errors.append({"code": "review_chain_unit_count"})

    report = {
        "schema": "arf-final-heuristic-warning-waiver-verification-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "waiver_artifact": str(WAIVERS.relative_to(ROOT)).replace("\\", "/"),
        "waiver_artifact_sha256": sha256(WAIVERS),
        "application_artifact": str(APPLICATION.relative_to(ROOT)).replace("\\", "/"),
        "application_artifact_sha256": sha256(APPLICATION),
        "review_chain": str(REVIEW_CHAIN.relative_to(ROOT)).replace("\\", "/"),
        "review_chain_sha256": sha256(REVIEW_CHAIN),
        "original_warning_events": waiver_doc["original_warning_events"],
        "corrected_warning_events": waiver_doc["corrected_warning_events"],
        "remaining_warning_events": len(current_by_key),
        "waiver_entries": len(waiver_by_key),
        "unwaived_warning_events": len(missing_waivers),
        "stale_waiver_entries": len(stale_waivers),
        "waived_target_mismatches": len(target_mismatches),
        "waived_batch_hash_mismatches": len(batch_hash_mismatches),
        "corrected_warnings_still_present": len(still_warning),
        "all_remaining_warnings_exactly_waived": (
            set(current_by_key) == set(waiver_by_key)
        ),
        "error_count": len(errors),
        "errors": errors,
        "valid": not errors,
    }
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "remaining_warning_events": len(current_by_key),
                "waiver_entries": len(waiver_by_key),
                "unwaived_warning_events": len(missing_waivers),
                "error_count": len(errors),
                "valid": not errors,
                "sha256": sha256(OUTPUT),
            },
            ensure_ascii=False,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
