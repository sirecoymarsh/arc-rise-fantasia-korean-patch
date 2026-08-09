#!/usr/bin/env python3
"""Cross-check the final source-free ARF localization checkpoint state."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sha256(relative: str) -> str:
    digest = hashlib.sha256()
    with (ROOT / relative).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    errors: list[dict[str, object]] = []

    def require(condition: bool, code: str, **details: object) -> None:
        if not condition:
            errors.append({"code": code, **details})

    contract = load("work/project/language_contract.json")
    coverage = load("work/translation/current/coverage.json")
    memory = load("work/translation/current/translation_memory_draft.json")
    boundary = load(
        "work/translation/boundary_audit/canonical_system_boundary_audit.json"
    )
    fit = load("work/font/canonical_v1/fit_preflight.json")
    corpus = load("work/font/canonical_v1/corpus_manifest.json")
    codebook = load("work/font/canonical_v1/codebook.json")
    injection = load("work/font/canonical_v1/injection_verification.json")
    table_proof = load("work/system_table_application/application_proof.json")
    staging = load("work/partial_runtime_staging/staging_manifest.json")

    require(
        contract["translation_policy"]["codex_internal_models_only"] is True,
        "internal_translation_policy_not_true",
    )
    prohibited = set(contract["translation_policy"]["prohibited"])
    require(
        {"external translation APIs", "external generative AI models"}.issubset(
            prohibited
        ),
        "external_translation_not_prohibited",
    )
    boundary_hash = sha256(
        "work/translation/boundary_audit/canonical_system_boundary_audit.json"
    )
    require(
        boundary["scope"]["audited_tm_units"]
        == boundary["summary"]["resolved_tm_units"],
        "boundary_scope_tm_count",
    )
    require(
        boundary["scope"]["linked_table_units"]
        == boundary["summary"]["linked_table_units"],
        "boundary_scope_field_count",
    )
    require(boundary["summary"]["ambiguous_tm_units"] == 0, "boundary_ambiguous")
    require(boundary["summary"]["unmatched_tm_units"] == 0, "boundary_unmatched")

    component_hash_errors = []
    component_tm_total = 0
    component_field_total = 0
    for component in boundary["components"]:
        actual = sha256(str(component["path"]))
        if actual != str(component["sha256"]).upper():
            component_hash_errors.append(component["path"])
        component_tm_total += int(component["audited_tm_units"])
        component_field_total += int(component["linked_table_units"])
    require(not component_hash_errors, "boundary_component_hashes", files=component_hash_errors)
    require(
        component_tm_total == boundary["summary"]["resolved_tm_units"],
        "boundary_component_tm_total",
    )
    require(
        component_field_total == boundary["summary"]["linked_table_units"],
        "boundary_component_field_total",
    )

    validators = {}
    reviewed_batches = [
        Path(path).stem for path in coverage.get("batch_files", [])
    ]
    require(
        len(reviewed_batches) == len(set(reviewed_batches)),
        "coverage_duplicate_batch_files",
    )
    for batch in reviewed_batches:
        report = load(f"work/translation/validation/{batch}_reviewed.json")
        validators[batch] = {
            "completed_units": report["completed_units"],
            "error_count": report["error_count"],
            "warning_count": report["warning_count"],
            "valid": report["valid"],
            "sha256": sha256(
                f"work/translation/validation/{batch}_reviewed.json"
            ),
        }
        require(report["completed_units"] == 200, "batch_unit_count", batch=batch)
        require(report["error_count"] == 0, "batch_validation_errors", batch=batch)
        require(report["warning_count"] == 0, "batch_validation_warnings", batch=batch)
        require(report["valid"] is True, "batch_validation_invalid", batch=batch)

    expected_reviewed_units = len(reviewed_batches) * 200
    require(
        coverage["reviewed_units"] == expected_reviewed_units,
        "coverage_reviewed_units",
    )
    require(
        coverage["translated_units"] == coverage["reviewed_units"],
        "coverage_translated_units",
    )
    require(coverage["translated_occurrences"] > 0, "coverage_occurrences")
    require(
        memory["reviewed_unit_count"] == coverage["reviewed_units"],
        "tm_reviewed_count",
    )
    require(
        memory["translated_unit_count"] == coverage["translated_units"],
        "tm_translated_count",
    )

    require(
        fit["approved_tm_units"] == coverage["reviewed_units"],
        "fit_approved_units",
    )
    require(
        fit["matched_unique_tm_units"] == fit["approved_tm_units"],
        "fit_matched_units",
    )
    require(fit["matched_table_fields"] >= fit["matched_unique_tm_units"], "fit_fields")
    require(fit["unmatched_system_tm_count"] == 0, "fit_unmatched")
    require(fit["fixed_overflow_count"] == 0, "fit_fixed_overflow")
    require(fit["encoding_error_count"] == 0, "fit_encoding_errors")
    require(fit["global_encoding_error_count"] == 0, "fit_global_encoding_errors")
    require(fit["safe_for_fixed_table_insertion"] is True, "fit_not_safe")

    pairs = [str(item["bytes_hex"]).upper() for item in codebook["characters"].values()]
    reserved = {
        token.strip().upper()
        for token in (
            ROOT / "work/font/original_reserved_pairs_v2.txt"
        ).read_text(encoding="utf-8").split()
        if token.strip()
    }
    require(
        codebook["assigned"] >= corpus["unique_hangul"],
        "codebook_assigned_below_corpus",
    )
    require(len(pairs) == len(set(pairs)), "codebook_duplicate_pairs")
    require(not (set(pairs) & reserved), "codebook_reserved_collision")
    for backup_path in sorted(
        (ROOT / "work/font/canonical_v1").glob("codebook_before_*.json")
    ):
        backup = json.loads(backup_path.read_text(encoding="utf-8"))
        moved = [
            char
            for char, value in backup["characters"].items()
            if codebook["characters"].get(char) != value
        ]
        require(not moved, "codebook_not_append_only", backup=str(backup_path), sample=moved[:20])
    require(injection["valid"] is True, "font_injection_invalid")
    require(injection["error_count"] == 0, "font_injection_errors")
    require(
        injection["approved_units_encoded"] == coverage["reviewed_units"],
        "font_encoded_units",
    )
    require(
        injection["assigned_characters"] == codebook["assigned"],
        "font_assigned_characters",
    )

    current_tm_hash = sha256("work/translation/current/translation_memory_draft.json")
    codebook_hash = sha256("work/font/canonical_v1/codebook.json")
    require(table_proof["translation_memory_sha256"] == current_tm_hash, "table_tm_hash")
    require(table_proof["codebook_sha256"] == codebook_hash, "table_codebook_hash")
    require(table_proof["boundary_audit_sha256"] == boundary_hash, "table_boundary_hash")
    require(
        table_proof["approved_system_tm_units"] == coverage["reviewed_units"],
        "table_approved_units",
    )
    require(
        table_proof["applied_unique_tm_units"]
        == table_proof["approved_system_tm_units"],
        "table_applied_units",
    )
    require(
        table_proof["replacement_table_fields"] == fit["matched_table_fields"],
        "table_fields",
    )
    require(table_proof["payloads_rebuilt"] == 13, "table_payloads")
    require(table_proof["fixed_payload_changes_outside_declared_slots"] == 0, "table_diff_confinement")
    require(table_proof["verification_error_count"] == 0, "table_errors")
    require(table_proof["valid"] is True, "table_invalid")

    require(staging["output_system_vol"]["edited_entries"] == 20, "staging_edits")
    require(len(staging["direct_files"]) == 2, "staging_direct_files")
    require(staging["output_system_vol"]["rebuild_policy"] == "standard-resize", "staging_policy")
    require(staging["static_validation"]["valid"] is True, "staging_invalid")
    require(staging["static_validation"]["error_count"] == 0, "staging_errors")
    require(staging["static_validation"]["riivolution_xml_valid"] is True, "staging_xml")
    require(staging["dolphin_screen_test"] == "pending", "staging_runtime_status")

    report = {
        "schema": "arf-ko-final-static-verification-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "canonical_boundary_audit_sha256": boundary_hash,
        "reviewed_units": coverage["reviewed_units"],
        "translated_occurrences": coverage["translated_occurrences"],
        "validators": validators,
        "fit": {
            "matched_unique_tm_units": fit["matched_unique_tm_units"],
            "matched_table_fields": fit["matched_table_fields"],
            "fixed_overflow_count": fit["fixed_overflow_count"],
            "unmatched_system_tm_count": fit["unmatched_system_tm_count"],
            "encoding_error_count": fit["encoding_error_count"],
            "global_encoding_error_count": fit["global_encoding_error_count"],
            "safe_for_fixed_table_insertion": fit[
                "safe_for_fixed_table_insertion"
            ],
        },
        "font": {
            "assigned_characters": codebook["assigned"],
            "reserved_source_pairs": len(reserved),
            "verification_errors": injection["error_count"],
            "valid": injection["valid"],
        },
        "table_application": {
            "approved_system_tm_units": table_proof["approved_system_tm_units"],
            "replacement_table_fields": table_proof["replacement_table_fields"],
            "payloads_rebuilt": table_proof["payloads_rebuilt"],
            "verification_error_count": table_proof["verification_error_count"],
            "valid": table_proof["valid"],
        },
        "partial_runtime_staging": {
            "edited_system_vol_entries": staging["output_system_vol"][
                "edited_entries"
            ],
            "direct_files": len(staging["direct_files"]),
            "static_error_count": staging["static_validation"]["error_count"],
            "static_valid": staging["static_validation"]["valid"],
            "dolphin_screen_test": staging["dolphin_screen_test"],
        },
        "error_count": len(errors),
        "errors": errors,
        "valid": not errors,
    }
    output = ROOT / "work/validation/final_static_verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "reviewed_units": report["reviewed_units"],
                "translated_occurrences": report["translated_occurrences"],
                "matched_table_fields": report["fit"]["matched_table_fields"],
                "error_count": report["error_count"],
                "valid": report["valid"],
                "output": str(output),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
