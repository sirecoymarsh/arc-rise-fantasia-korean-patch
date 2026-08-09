#!/usr/bin/env python3
"""Freeze and verify the final Arc Rise Fantasia text/font integration state.

This report builder is deliberately read-only with respect to the source RVZ.
It rehashes the immutable image, verifies every final-stage count and artifact,
then atomically replaces the integration report under ``work/``.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "work/final_text_font_integration_report.json"

EXPECTED_SYSTEM_CATALOGS = {
    "ability.json",
    "chat.json",
    "dragon.json",
    "help.json",
    "item.json",
    "magic.json",
    "monster_book.json",
    "operation.json",
    "quest.json",
    "shop.json",
    "special.json",
    "todo.json",
    "treasure.json",
}
EXPECTED_RVZ_SHA256 = (
    "4671E3E74EB664E441FA927FF6BE9FC06B7D4860782BC4CECCF7DBBB4108AAC5"
)
EXPECTED_RVZ_SIZE = 3_589_772_720
NESTED_TM_ID = "ARF-TM-B9E4C48F9B1EA3670863"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def count_jsonl(path: Path) -> int:
    return sum(bool(line.strip()) for line in path.read_text(encoding="utf-8").splitlines())


def load_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved)


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": relative(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    paths = {
        "baseline": ROOT / "work/project/baseline_manifest.json",
        "batch_manifest": ROOT / "work/translation/tm_v2/batch_manifest.json",
        "review_chain": ROOT / "work/translation/final_validation/review_chain.json",
        "warning_inventory": ROOT
        / "work/scratch/heuristic_warning_inventory.json",
        "warning_waivers": ROOT
        / "work/translation/final_validation/heuristic_warning_waivers.json",
        "warning_qa_application": ROOT
        / "work/translation/final_validation/heuristic_warning_qa_application.json",
        "warning_waiver_verification": ROOT
        / "work/translation/final_validation/heuristic_warning_waiver_verification.json",
        "canonical_boundary": ROOT
        / "work/translation/boundary_audit/canonical_system_boundary_audit.json",
        "remaining_discovery": ROOT
        / "work/translation/boundary_audit/remaining_system_discovery_preflight.json",
        "remaining_component": ROOT
        / "work/translation/boundary_audit/final_remaining_system.json",
        "memory": ROOT / "work/translation/final/translation_memory_draft.json",
        "memory_csv": ROOT / "work/translation/final/translation_memory_draft.csv",
        "coverage": ROOT / "work/translation/final/coverage.json",
        "integrity_corrections": ROOT
        / "work/translation/reviews/final_validation_integrity_corrections.json",
        "fixed_preflight": ROOT
        / "work/translation/fixed_field_fit/preflight_before_corrections.json",
        "fixed_application": ROOT
        / "work/translation/fixed_field_fit/application_report.json",
        "occurrence_delta": ROOT
        / "work/translation/fixed_field_fit/system_occurrence_field_delta.json",
        "approved_units": ROOT / "work/font/final_v1/approved_units.jsonl",
        "corpus": ROOT / "work/font/final_v1/approved_korean_corpus.txt",
        "corpus_manifest": ROOT / "work/font/final_v1/corpus_manifest.json",
        "final_approved_units": ROOT / "work/font/final_v2/approved_units.jsonl",
        "final_approved_units_manifest": ROOT
        / "work/font/final_v2/approved_units_manifest.json",
        "main_dol_translations": ROOT
        / "work/runtime_fix/main_dol_translations.jsonl",
        "supplemental_corpus": ROOT / "work/font/final_v2/supplemental_corpus.txt",
        "baseline_codebook": ROOT / "work/font/final_v1/codebook.json",
        "codebook": ROOT / "work/font/final_v2/codebook.json",
        "codebook_verification": ROOT
        / "work/font/final_v2/codebook_append_only_verification.json",
        "reserved_pairs": ROOT / "work/font/original_reserved_pairs_v2.txt",
        "injection_manifest": ROOT / "work/font/final_v2/injection_manifest.json",
        "injection_verification": ROOT
        / "work/font/final_v2/injection_verification.json",
        "fit": ROOT / "work/font/final_v2/fit_preflight.json",
        "geometry_correction": ROOT
        / "work/translation/fixed_field_fit/geometry_regression_correction.json",
        "geometry_repair_validation": ROOT
        / "work/runtime_validation/fixed_table_geometry_repair_validation.json",
        "main_dol_translations": ROOT / "work/runtime_fix/main_dol_translations.jsonl",
        "main_dol_crossreview": ROOT / "work/runtime_fix/main_dol_crossreview.json",
        "main_dol_patch_report": ROOT / "work/runtime_fix/main_dol_patch_report_v2.json",
        "system_proof": ROOT
        / "work/final_system_table_application/application_proof.json",
    }
    for name, path in paths.items():
        require(path.is_file(), f"missing required artifact {name}: {path}")

    baseline = load_json(paths["baseline"])
    batch_manifest = load_json(paths["batch_manifest"])
    review_chain = load_json(paths["review_chain"])
    warning_inventory = load_json(paths["warning_inventory"])
    warning_waivers = load_json(paths["warning_waivers"])
    warning_qa_application = load_json(paths["warning_qa_application"])
    warning_waiver_verification = load_json(paths["warning_waiver_verification"])
    canonical = load_json(paths["canonical_boundary"])
    memory = load_json(paths["memory"])
    coverage = load_json(paths["coverage"])
    integrity = load_json(paths["integrity_corrections"])
    fixed_application = load_json(paths["fixed_application"])
    occurrence_delta = load_json(paths["occurrence_delta"])
    corpus_manifest = load_json(paths["corpus_manifest"])
    final_approved_units_manifest = load_json(paths["final_approved_units_manifest"])
    codebook = load_json(paths["codebook"])
    codebook_verification = load_json(paths["codebook_verification"])
    injection_manifest = load_json(paths["injection_manifest"])
    injection_verification = load_json(paths["injection_verification"])
    fit = load_json(paths["fit"])
    geometry_correction = load_json(paths["geometry_correction"])
    geometry_repair_validation = load_json(paths["geometry_repair_validation"])
    system_proof = load_json(paths["system_proof"])
    main_dol_crossreview = load_json(paths["main_dol_crossreview"])
    main_dol_patch_report = load_json(paths["main_dol_patch_report"])

    # Immutable source image: rehash the current bytes and compare to baseline.
    baseline_rvz = baseline["immutable_source"]
    rvz_path = Path(str(baseline_rvz["path"]))
    require(rvz_path.is_file(), f"immutable RVZ is missing: {rvz_path}")
    rvz_stat = rvz_path.stat()
    current_rvz_hash = sha256(rvz_path)
    rvz_matches = (
        rvz_stat.st_size == EXPECTED_RVZ_SIZE
        and str(baseline_rvz["sha256"]).upper() == EXPECTED_RVZ_SHA256
        and current_rvz_hash == EXPECTED_RVZ_SHA256
    )
    require(rvz_matches, "immutable source RVZ no longer matches the baseline")

    # Authoritative 149-batch review chain and the nonstandard final batch size.
    manifest_entries = {
        Path(str(item["file"])).stem: item for item in batch_manifest["batches"]
    }
    batch_0149_manifest = manifest_entries["batch_0149"]
    batch_0149_source = (
        ROOT / "work/translation/tm_v2/batches/source/batch_0149.jsonl"
    )
    batch_0149_reviewed = ROOT / "work/translation/reviewed/batch_0149.jsonl"
    require(int(batch_0149_manifest["unit_count"]) == 177, "batch_0149 is not 177 units")
    require(count_jsonl(batch_0149_source) == 177, "batch_0149 source count is not 177")
    require(count_jsonl(batch_0149_reviewed) == 177, "batch_0149 reviewed count is not 177")
    require(int(batch_manifest["batch_count"]) == 149, "batch manifest count is not 149")
    require(int(batch_manifest["unit_count"]) == 29_777, "manifest units are not 29,777")
    require(review_chain.get("valid") is True, "review chain is invalid")
    require(int(review_chain["batch_count"]) == 149, "review chain count is not 149")
    require(int(review_chain["reviewed_units"]) == 29_777, "reviewed units are not 29,777")
    require(int(review_chain["error_count"]) == 0, "review chain has errors")
    require(
        review_chain.get("all_manifest_batches_supplied") is True,
        "not all manifest batches were supplied to review validation",
    )
    for row in review_chain["batches"]:
        batch = str(row["batch"])
        hash_bound_paths = {
            "source_sha256": ROOT
            / f"work/translation/tm_v2/batches/source/{batch}.jsonl",
            "draft_sha256": ROOT / f"work/translation/drafts/{batch}.jsonl",
            "reviewed_sha256": ROOT / f"work/translation/reviewed/{batch}.jsonl",
            "review_report_sha256": ROOT
            / f"work/translation/reviews/{batch}_review.json",
            "validation_sha256": ROOT
            / f"work/translation/final_validation/{batch}_reviewed.json",
        }
        for field, path in hash_bound_paths.items():
            require(path.is_file(), f"missing review-chain input: {path}")
            require(
                str(row.get(field, "")).upper() == sha256(path),
                f"stale review-chain hash: {batch} {field}",
            )

    warning_codes: Counter[str] = Counter()
    for report_path in sorted(
        (ROOT / "work/translation/final_validation").glob("batch_*_reviewed.json")
    ):
        validation = load_json(report_path)
        require(validation.get("valid") is True, f"invalid batch validation: {report_path}")
        require(int(validation.get("error_count", -1)) == 0, f"batch errors: {report_path}")
        warning_codes.update(
            str(item.get("code") or "unknown") for item in validation.get("warnings", [])
        )
    validator_warning_count = sum(
        int(item.get("validator_warnings") or 0) for item in review_chain["batches"]
    )
    require(
        sum(warning_codes.values()) == validator_warning_count,
        "warning aggregate differs from the review-chain summaries",
    )
    require(int(warning_inventory["warning_events"]) == 148, "initial warning inventory is not 148")
    require(warning_qa_application.get("valid") is True, "heuristic warning QA application is invalid")
    require(
        int(warning_qa_application["warning_events_corrected"]) == 7
        and int(warning_qa_application["warning_events_waived"]) == 141
        and int(warning_qa_application["adjacent_contamination_corrections"]) == 1
        and int(warning_qa_application["total_target_corrections"]) == 8,
        "heuristic warning QA decision counts changed",
    )
    require(warning_waivers.get("valid") is True, "heuristic warning waivers are invalid")
    require(int(warning_waivers["waived_warning_events"]) == 141, "waiver count is not 141")
    require(
        warning_waiver_verification.get("valid") is True
        and int(warning_waiver_verification["remaining_warning_events"]) == validator_warning_count
        and int(warning_waiver_verification["waiver_entries"]) == validator_warning_count
        and int(warning_waiver_verification["unwaived_warning_events"]) == 0
        and int(warning_waiver_verification["stale_waiver_entries"]) == 0,
        "remaining heuristic warnings are not exactly covered by current waivers",
    )

    # Canonical boundary state must be both complete and bound to reviewed bytes.
    boundary_scope = canonical["scope"]
    boundary_summary = canonical["summary"]
    require(int(boundary_scope["audited_tm_units"]) == 720, "boundary TM count is not 720")
    require(int(boundary_scope["linked_table_units"]) == 727, "boundary field count is not 727")
    require(boundary_scope.get("reviewed_state_verified") is True, "reviewed boundary state is stale")
    require(int(boundary_summary["ambiguous_tm_units"]) == 0, "ambiguous boundaries remain")
    require(int(boundary_summary["unmatched_tm_units"]) == 0, "unmatched boundaries remain")
    require(int(boundary_summary["reviewed_translation_mismatches"]) == 0, "boundary review mismatch")

    # Frozen 29,777-unit merge and 84,761 occurrence coverage.
    units = memory["units"]
    require(len(units) == 29_777, "merged TM unit count is not 29,777")
    require(all(item.get("review_status") == "approved" for item in units), "unapproved merged TM unit")
    require(all(str(item.get("translation_ko") or "").strip() for item in units), "blank merged target")
    require(int(memory["translated_unit_count"]) == 29_777, "translated merge count mismatch")
    require(int(memory["reviewed_unit_count"]) == 29_777, "reviewed merge count mismatch")
    require(int(coverage["total_occurrences"]) == 84_761, "occurrence count is not 84,761")
    require(int(coverage["translated_occurrences"]) == 84_761, "translated occurrence mismatch")
    require(float(coverage["coverage_percent"]) == 100.0, "translation coverage is not 100%")

    # Corpus, append-only mapping, and font rendering closure.
    expected_approved_rows = [
        {
            "tm_id": str(item["tm_id"]),
            "translation_ko": str(item["translation_ko"]),
        }
        for item in units
        if item.get("review_status") == "approved"
        and str(item.get("translation_ko") or "").strip()
    ]
    approved_rows = load_jsonl(paths["approved_units"])
    final_approved_rows = load_jsonl(paths["final_approved_units"])
    main_dol_rows = load_jsonl(paths["main_dol_translations"])
    require(
        approved_rows == expected_approved_rows,
        "approved corpus units are not an exact projection of the current TM",
    )
    require(
        final_approved_rows[: len(approved_rows)] == approved_rows,
        "final font unit list is not prefixed by the current TM approved units",
    )
    require(
        final_approved_rows[len(approved_rows) :] == main_dol_rows,
        "final font unit list is not suffixed by the current main.dol units",
    )
    require(int(corpus_manifest["approved_units"]) == 29_777, "approved corpus count mismatch")
    require(int(corpus_manifest["unique_hangul"]) == 1_366, "Hangul closure count mismatch")
    require(count_jsonl(paths["approved_units"]) == 29_777, "approved unit JSONL count mismatch")
    require(count_jsonl(paths["final_approved_units"]) == 30_702, "final font unit count mismatch")
    require(
        str(corpus_manifest.get("translation_memory_sha256", "")).upper()
        == sha256(paths["memory"]),
        "approved corpus is not hash-bound to the current TM",
    )
    require(
        str(corpus_manifest["approved_units_jsonl_sha256"]).upper()
        == sha256(paths["approved_units"]),
        "approved corpus manifest unit hash mismatch",
    )
    require(
        str(corpus_manifest["corpus_sha256"]).upper() == sha256(paths["corpus"]),
        "approved corpus manifest text hash mismatch",
    )
    require(final_approved_units_manifest.get("valid") is True, "final font unit manifest is invalid")
    require(
        str(final_approved_units_manifest.get("base_approved_units_sha256", "")).upper()
        == sha256(paths["approved_units"]),
        "final font units are not bound to the current approved corpus units",
    )
    require(
        str(final_approved_units_manifest.get("main_dol_translations_sha256", "")).upper()
        == sha256(paths["main_dol_translations"]),
        "final font units are not bound to the current main.dol translations",
    )
    require(
        str(final_approved_units_manifest.get("output_sha256", "")).upper()
        == sha256(paths["final_approved_units"]),
        "final font unit manifest output hash mismatch",
    )
    require(codebook_verification.get("valid") is True, "append-only codebook is invalid")
    require(
        str(codebook_verification.get("extended_codebook_sha256", "")).upper()
        == sha256(paths["codebook"]),
        "append-only verification codebook hash mismatch",
    )
    require(
        str(codebook_verification.get("corpus_sha256", "")).upper()
        == sha256(paths["supplemental_corpus"]),
        "append-only verification supplemental corpus hash mismatch",
    )
    require(int(codebook_verification["existing_assigned"]) == 1_368, "baseline codebook count mismatch")
    require(int(codebook_verification["extended_assigned"]) == 1_369, "final codebook count mismatch")
    require(int(codebook_verification["appended_characters"]) == 1, "appended mapping count mismatch")
    require(int(codebook_verification["existing_assignments_changed"]) == 0, "existing mapping changed")
    require(int(codebook_verification["reserved_pair_collisions"]) == 0, "reserved mapping collision")
    require("\u00b7" in codebook["characters"], "U+00B7 custom glyph is absent")
    require("\uff5e" in codebook["characters"], "U+FF5E custom glyph is absent")
    require(injection_verification.get("valid") is True, "font injection is invalid")
    require(
        str(injection_verification.get("approved_units_sha256", "")).upper()
        == sha256(paths["final_approved_units"]),
        "font verification is not bound to the current final approved units",
    )
    require(int(injection_verification["approved_units_encoded"]) == 30_702, "font encoding closure mismatch")
    require(int(injection_verification["approved_unit_encoding_errors"]) == 0, "font encoding errors remain")
    require(int(injection_verification["assigned_cells_without_pixel_change"]) == 0, "unchanged assigned glyph cell")

    injected_dir = ROOT / "work/font/final_v2/injected"
    wtm_paths = sorted(injected_dir.glob("EUC28-*.wtm"))
    require(len(wtm_paths) == 9, "final injected WTM page count is not 9")
    manifest_files = {Path(str(item["output"])).name: item for item in injection_manifest["files"]}
    require(set(manifest_files) == {path.name for path in wtm_paths}, "WTM manifest set mismatch")
    wtm_payloads = []
    for path in wtm_paths:
        item = manifest_files[path.name]
        actual_hash = sha256(path)
        require(actual_hash == str(item["output_sha256"]).upper(), f"WTM hash mismatch: {path.name}")
        wtm_payloads.append(
            {
                "file": path.name,
                "path": relative(path),
                "size_bytes": path.stat().st_size,
                "sha256": actual_hash,
                "changed_from_source": bool(item["changed"]),
            }
        )

    # Fixed-field fit and authoritative 13-payload system-table application.
    require(fit.get("safe_for_fixed_table_insertion") is True, "fixed-field fit is unsafe")
    require(int(fit["approved_tm_units"]) == 29_777, "fit approved count mismatch")
    require(int(fit["matched_unique_tm_units"]) == 4_343, "fit system TM count mismatch")
    require(int(fit["matched_table_fields"]) == 5_236, "fit structured field count mismatch")
    require(int(fit["fixed_overflow_count"]) == 0, "fixed overflows remain")
    require(int(fit["unmatched_system_tm_count"]) == 0, "unmatched system TM remains")
    require(int(fit["encoding_error_count"]) == 0, "system encoding errors remain")
    require(int(fit["global_encoding_error_count"]) == 0, "global encoding errors remain")
    require(int(fit["table_specific_boundary_fields_matched"]) == 1, "nested override fit is absent")
    require(
        str(fit.get("translation_memory_sha256", "")).upper()
        == sha256(paths["memory"]),
        "fit report is not bound to the current TM",
    )
    require(
        str(fit.get("codebook_sha256", "")).upper() == sha256(paths["codebook"]),
        "fit report is not bound to the current codebook",
    )
    require(
        str(fit.get("boundary_audit_sha256", "")).upper()
        == sha256(paths["canonical_boundary"]),
        "fit report is not bound to the current boundary audit",
    )
    fit_catalog_dir = Path(str(fit["catalog_dir"]))
    fit_catalog_artifacts = {
        str(item["name"]): item for item in fit.get("catalog_artifacts", [])
    }
    require(
        set(fit_catalog_artifacts) == EXPECTED_SYSTEM_CATALOGS,
        "fit catalog hash allowlist is not the authoritative 13",
    )
    for name, item in fit_catalog_artifacts.items():
        catalog_path = fit_catalog_dir / name
        require(catalog_path.is_file(), f"missing fit catalog: {catalog_path}")
        require(
            int(item["size_bytes"]) == catalog_path.stat().st_size
            and str(item["sha256"]).upper() == sha256(catalog_path),
            f"fit catalog hash mismatch: {name}",
        )

    # Late fixed-field geometry regression: preserve the old corrupt audit as
    # incident evidence, but require the corrected TM and independent repair
    # validation to be hash-bound to the current bytes.
    require(geometry_correction.get("valid") is True, "geometry correction is invalid")
    geometry_record = dict(geometry_correction["correction"])
    require(
        geometry_record.get("tm_id") == "ARF-TM-7983B232461623CDF50F",
        "unexpected geometry-correction TM ID",
    )
    geometry_tm_unit = next(
        item for item in units if item["tm_id"] == geometry_record["tm_id"]
    )
    require(
        geometry_tm_unit["translation_ko"] == geometry_record["after"],
        "geometry-corrected TM target is stale",
    )
    geometry_artifacts = dict(geometry_correction["artifacts"])
    require(
        str(geometry_artifacts["final_tm_sha256"]).upper()
        == sha256(paths["memory"]),
        "geometry correction TM hash mismatch",
    )
    require(
        str(geometry_artifacts["final_tm_csv_sha256"]).upper()
        == sha256(paths["memory_csv"]),
        "geometry correction CSV hash mismatch",
    )
    for item in geometry_correction["audits"]:
        audit_path = ROOT / str(item["path"])
        require(audit_path.is_file(), f"missing geometry incident audit: {audit_path}")
        require(
            str(item["sha256"]).upper() == sha256(audit_path),
            f"geometry incident audit hash mismatch: {audit_path}",
        )
    require(
        geometry_repair_validation.get("valid") is True,
        "geometry repair validation is invalid",
    )
    geometry_repair_summary = dict(geometry_repair_validation["summary"])
    require(
        int(geometry_repair_summary["schemas_with_protected_changes"]) == 0
        and int(geometry_repair_summary["protected_changed_bytes_sum"]) == 0,
        "protected metadata changes remain after geometry repair",
    )
    require(system_proof.get("valid") is True, "system-table application proof is invalid")
    require(
        str(system_proof.get("translation_memory_sha256", "")).upper()
        == sha256(paths["memory"]),
        "system proof is not bound to the current TM",
    )
    require(
        str(system_proof.get("codebook_sha256", "")).upper()
        == sha256(paths["codebook"]),
        "system proof is not bound to the current codebook",
    )
    require(
        str(system_proof.get("boundary_audit_sha256", "")).upper()
        == sha256(paths["canonical_boundary"]),
        "system proof is not bound to the current boundary audit",
    )
    require(int(system_proof["approved_system_tm_units"]) == 4_343, "proof TM count mismatch")
    require(int(system_proof["applied_unique_tm_units"]) == 4_343, "proof applied TM mismatch")
    require(int(system_proof["replacement_table_fields"]) == 5_236, "proof field count mismatch")
    require(int(system_proof["system_database_scanner_occurrences"]) == 5_236, "scanner occurrence mismatch")
    require(
        system_proof.get("structured_field_coverage_matches_scanner_occurrences") is True,
        "structured field/scanner occurrence closure failed",
    )
    require(int(system_proof["payloads_rebuilt"]) == 13, "proof payload count is not 13")
    require(int(system_proof["verification_error_count"]) == 0, "proof verification errors remain")
    require(
        int(system_proof["fixed_payload_changes_outside_declared_slots"]) == 0,
        "fixed payload has changes outside declared slots",
    )
    proof_catalogs = {str(item["catalog"]) for item in system_proof["payloads"]}
    require(proof_catalogs == EXPECTED_SYSTEM_CATALOGS, "proof catalog allowlist is not the authoritative 13")
    system_payloads = []
    for item in sorted(system_proof["payloads"], key=lambda value: str(value["catalog"])):
        output_path = Path(str(item["output_path"]))
        actual_hash = sha256(output_path)
        require(actual_hash == str(item["output_sha256"]).upper(), f"system payload hash mismatch: {output_path}")
        system_payloads.append(
            {
                "catalog": item["catalog"],
                "schema": item["schema"],
                "replacement_fields": item["replacement_fields"],
                "boundary_mapped_fields": item["boundary_mapped_fields"],
                "table_specific_boundary_fields": item.get("table_specific_boundary_fields", 0),
                "path": relative(output_path),
                "size_bytes": output_path.stat().st_size,
                "sha256": actual_hash,
                "verification_errors": item["verification_errors"],
                "changes_outside_declared_slots": item[
                    "changes_outside_declared_slots"
                ],
            }
        )

    require(int(fixed_application["fixed_fields_corrected"]) == 42, "fixed correction count mismatch")
    require(int(fixed_application["fixed_fields_fit_after_correction"]) == 42, "fixed correction fit mismatch")
    require(fixed_application.get("valid") is True, "fixed correction application is invalid")
    require(int(integrity["correction_count"]) == 3, "integrity correction count mismatch")
    require(
        integrity.get("translation_engine_policy") == "Codex internal models only"
        and integrity.get("external_translation_models_or_apis_used") is False,
        "integrity correction provenance is invalid",
    )
    require(int(occurrence_delta["system_occurrences"]) == 5_236, "delta scanner count mismatch")
    require(int(occurrence_delta["applied_structured_fields"]) == 5_236, "delta field count mismatch")
    require(int(occurrence_delta["net_occurrence_minus_field_delta"]) == 0, "occurrence/field delta remains")
    require(int(occurrence_delta["units_with_count_delta"]) == 0, "per-unit occurrence delta remains")

    # The late main.dol audit is a separate, independently cross-reviewed
    # runtime lane.  It extends the font closure by exactly one glyph (켬).
    require(count_jsonl(paths["main_dol_translations"]) == 925, "main.dol translation count mismatch")
    require(main_dol_crossreview.get("valid") is True, "main.dol cross-review is invalid")
    require(int(main_dol_crossreview["result"]["reviewed_rows"]) == 925, "main.dol reviewed count mismatch")
    require(main_dol_patch_report.get("valid") is True, "main.dol patch report is invalid")
    require(int(main_dol_patch_report["summary"]["patch_rows"]) == 925, "main.dol patch row count mismatch")
    require(str(main_dol_patch_report["source"]["sha256"]).upper() == "4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC", "main.dol source anchor mismatch")

    nested = next(item for item in canonical["units"] if item["tm_id"] == NESTED_TM_ID)
    require(nested.get("application_mode") == "table_specific_only", "nested mode is not table-specific")
    require(nested["reviewed_translation_ko"] == "행동", "nested reviewed TM target changed")
    require(nested["table_specific_translation_ko"] == "최속 행동", "nested field target changed")
    nested_evidence = nested["evidence"][0]

    malgun_path = Path(str(injection_manifest["font"]))
    require(sha256(malgun_path) == str(injection_manifest["font_sha256"]).upper(), "font source hash mismatch")

    scripts = [
        "work/research/validate_translation_batch.py",
        "work/research/validate_review_chain.py",
        "work/research/merge_translation_batches.py",
        "work/research/build_remaining_system_boundary_audit.py",
        "work/research/apply_boundary_audit.py",
        "work/research/apply_boundary_audit_final_remaining.py",
        "work/research/build_canonical_boundary_audit.py",
        "work/research/apply_fixed_field_fit_corrections.py",
        "work/research/build_approved_corpus.py",
        "work/research/build_final_font_approved_units.py",
        "work/research/verify_append_only_codebook.py",
        "work/research/font_agent/arf_euc28_mapping.py",
        "work/research/verify_injected_fonts.py",
        "work/research/encode_custom_euc28.py",
        "work/research/check_translation_fit.py",
        "work/research/build_system_table_application_proof.py",
        "work/research/apply_final_heuristic_warning_qa.py",
        "work/research/verify_final_heuristic_warning_waivers.py",
        "work/scratch/analyze_system_occurrence_field_delta.py",
        "work/research/build_final_text_font_integration_report.py",
        "work/research/audit_final_release_refresh_dependencies.py",
    ]
    script_artifacts = [artifact(ROOT / value) for value in scripts]

    report = {
        "schema": "arf-final-text-font-integration-report-v2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "source_language": "ja-JP",
        "target_language": "ko-KR",
        "scope": {
            "included": [
                "149-batch independent review chain",
                "exhaustive classification of all 148 heuristic warnings",
                "29,777-unit frozen translation memory",
                "canonical structured-table boundary audit",
                "append-only custom glyph codebook",
                "9 injected EUC28 WTM font pages",
                "13 authoritative system-table payloads",
                "925 independently cross-reviewed main.dol runtime strings",
            ],
            "excluded": [
                "runtime ISO/RVZ rebuild",
                "Dolphin runtime playthrough",
            ],
        },
        "immutable_source_rvz": {
            "path": str(rvz_path),
            "format": "RVZ",
            "size_bytes": rvz_stat.st_size,
            "baseline_sha256": EXPECTED_RVZ_SHA256,
            "current_sha256": current_rvz_hash,
            "current_sha256_reverified_during_report_build": True,
            "baseline_size_matches": rvz_stat.st_size == EXPECTED_RVZ_SIZE,
            "hash_matches_immutable_baseline": rvz_matches,
            "creation_time_utc": datetime.fromtimestamp(
                rvz_stat.st_ctime, timezone.utc
            ).isoformat(),
            "last_write_time_utc": datetime.fromtimestamp(
                rvz_stat.st_mtime, timezone.utc
            ).isoformat(),
            "write_operations_performed_by_this_stage": 0,
            "modified": False,
        },
        "review_chain": {
            "artifact": artifact(paths["review_chain"]),
            "batch_manifest": artifact(paths["batch_manifest"]),
            "manifest_batches": batch_manifest["batch_count"],
            "manifest_units": batch_manifest["unit_count"],
            "validated_batches": review_chain["batch_count"],
            "reviewed_units": review_chain["reviewed_units"],
            "all_manifest_batches_supplied": review_chain[
                "all_manifest_batches_supplied"
            ],
            "batch_0149": {
                "manifest_unit_count": batch_0149_manifest["unit_count"],
                "source_unit_count": count_jsonl(batch_0149_source),
                "reviewed_unit_count": count_jsonl(batch_0149_reviewed),
                "source_sha256": sha256(batch_0149_source),
                "reviewed_sha256": sha256(batch_0149_reviewed),
            },
            "validation_errors": review_chain["error_count"],
            "advisory_warnings": validator_warning_count,
            "advisory_warning_codes": dict(sorted(warning_codes.items())),
            "unwaived_advisory_warnings": warning_waiver_verification[
                "unwaived_warning_events"
            ],
            "warning_policy": (
                "Every original warning received an internal-model semantic/layout "
                "decision. Genuine defects were corrected; each remaining acting-mark "
                "or Korean line-reflow warning has an exact current-state waiver."
            ),
            "valid": review_chain["valid"],
        },
        "heuristic_warning_final_qa": {
            "initial_inventory": artifact(paths["warning_inventory"]),
            "application": artifact(paths["warning_qa_application"]),
            "waivers": artifact(paths["warning_waivers"]),
            "waiver_verification": artifact(paths["warning_waiver_verification"]),
            "original_warning_events": warning_waivers["original_warning_events"],
            "genuine_warning_defects_corrected": warning_qa_application[
                "warning_events_corrected"
            ],
            "adjacent_contamination_corrections": warning_qa_application[
                "adjacent_contamination_corrections"
            ],
            "total_target_corrections": warning_qa_application[
                "total_target_corrections"
            ],
            "remaining_warning_events": warning_waiver_verification[
                "remaining_warning_events"
            ],
            "waiver_entries": warning_waiver_verification["waiver_entries"],
            "waiver_categories": warning_waivers["waiver_categories"],
            "unwaived_warning_events": warning_waiver_verification[
                "unwaived_warning_events"
            ],
            "stale_waiver_entries": warning_waiver_verification[
                "stale_waiver_entries"
            ],
            "all_original_warnings_classified_exactly_once": warning_waivers[
                "all_original_warnings_classified_exactly_once"
            ],
            "all_remaining_warnings_exactly_waived": warning_waiver_verification[
                "all_remaining_warnings_exactly_waived"
            ],
            "external_translation_models_or_apis_used": False,
            "valid": warning_waiver_verification["valid"],
        },
        "canonical_boundary_audit": {
            "artifact": artifact(paths["canonical_boundary"]),
            "component_count": len(canonical["components"]),
            "reviewed_batches_bound": len(boundary_scope["reviewed_batches"]),
            "audited_tm_units": boundary_scope["audited_tm_units"],
            "linked_table_units": boundary_scope["linked_table_units"],
            "ambiguous_tm_units": boundary_summary["ambiguous_tm_units"],
            "unmatched_tm_units": boundary_summary["unmatched_tm_units"],
            "reviewed_translation_mismatches": boundary_summary[
                "reviewed_translation_mismatches"
            ],
            "reviewed_state_verified": boundary_scope["reviewed_state_verified"],
            "final_remaining_component": artifact(paths["remaining_component"]),
        },
        "frozen_translation_memory": {
            "json": artifact(paths["memory"]),
            "csv": artifact(paths["memory_csv"]),
            "coverage": artifact(paths["coverage"]),
            "total_units": coverage["total_units"],
            "translated_units": coverage["translated_units"],
            "reviewed_units": coverage["reviewed_units"],
            "coverage_percent": coverage["coverage_percent"],
            "total_occurrences": coverage["total_occurrences"],
            "translated_occurrences": coverage["translated_occurrences"],
            "translated_by_surface": coverage["translated_by_surface"],
        },
        "approved_corpus": {
            "approved_units": artifact(paths["approved_units"]),
            "corpus": artifact(paths["corpus"]),
            "manifest": artifact(paths["corpus_manifest"]),
            "approved_units_count": corpus_manifest["approved_units"],
            "unique_hangul": corpus_manifest["unique_hangul"],
            "translation_memory_sha256": corpus_manifest[
                "translation_memory_sha256"
            ],
            "final_font_approved_units": artifact(paths["final_approved_units"]),
            "final_font_approved_units_manifest": artifact(
                paths["final_approved_units_manifest"]
            ),
            "final_font_approved_units_count": len(final_approved_rows),
            "main_dol_supplement_count": len(main_dol_rows),
        },
        "append_only_codebook": {
            "baseline": artifact(paths["baseline_codebook"]),
            "final": artifact(paths["codebook"]),
            "verification": artifact(paths["codebook_verification"]),
            "reserved_pairs": artifact(paths["reserved_pairs"]),
            "existing_assigned": codebook_verification["existing_assigned"],
            "final_assigned": codebook_verification["extended_assigned"],
            "appended_characters": codebook_verification["appended_characters"],
            "required_hangul": codebook_verification["required_hangul"],
            "required_custom_glyphs": codebook_verification[
                "required_custom_glyphs"
            ],
            "custom_non_euc_jp_glyphs": {
                "U+00B7": codebook["characters"]["\u00b7"],
                "U+FF5E": codebook["characters"]["\uff5e"],
            },
            "existing_assignments_changed": codebook_verification[
                "existing_assignments_changed"
            ],
            "reserved_source_pairs": codebook_verification["reserved_source_pairs"],
            "reserved_pair_collisions": codebook_verification[
                "reserved_pair_collisions"
            ],
            "errors": codebook_verification["errors"],
            "valid": codebook_verification["valid"],
        },
        "main_dol_runtime_extension": {
            "translations": artifact(paths["main_dol_translations"]),
            "crossreview": artifact(paths["main_dol_crossreview"]),
            "patch_report": artifact(paths["main_dol_patch_report"]),
            "translated_strings": 925,
            "new_font_glyph": "켬",
            "source_sha256": main_dol_patch_report["source"]["sha256"],
            "patched_semantic_sha256": main_dol_patch_report["output"]["sha256"],
            "valid": True,
        },
        "font_injection": {
            "font_source": artifact(malgun_path),
            "font_size": injection_manifest["font_size"],
            "manifest": artifact(paths["injection_manifest"]),
            "verification": artifact(paths["injection_verification"]),
            "wtm_pages": len(wtm_payloads),
            "assigned_characters": injection_verification["assigned_characters"],
            "approved_units_encoded": injection_verification[
                "approved_units_encoded"
            ],
            "approved_units_sha256": injection_verification[
                "approved_units_sha256"
            ],
            "approved_unit_encoding_errors": injection_verification[
                "approved_unit_encoding_errors"
            ],
            "assigned_cells_without_pixel_change": injection_verification[
                "assigned_cells_without_pixel_change"
            ],
            "total_changed_pixels": injection_verification["total_changed_pixels"],
            "payloads": wtm_payloads,
            "errors": injection_verification["errors"],
            "valid": injection_verification["valid"],
        },
        "fixed_field_fit": {
            "artifact": artifact(paths["fit"]),
            "translation_memory_sha256": fit["translation_memory_sha256"],
            "codebook_sha256": fit["codebook_sha256"],
            "catalog_tree_sha256": fit["catalog_tree_sha256"],
            "boundary_audit_sha256": fit["boundary_audit_sha256"],
            "approved_tm_units": fit["approved_tm_units"],
            "matched_unique_system_tm_units": fit["matched_unique_tm_units"],
            "matched_table_fields": fit["matched_table_fields"],
            "fixed_overflow_count": fit["fixed_overflow_count"],
            "resizable_table_in_place_overflow_count": fit[
                "resizable_table_in_place_overflow_count"
            ],
            "unmatched_system_tm_count": fit["unmatched_system_tm_count"],
            "encoding_error_count": fit["encoding_error_count"],
            "global_encoding_error_count": fit["global_encoding_error_count"],
            "boundary_tm_units_matched": fit["boundary_audit_tm_units_matched"],
            "boundary_table_fields_matched": fit[
                "boundary_audit_table_fields_matched"
            ],
            "table_specific_boundary_fields_matched": fit[
                "table_specific_boundary_fields_matched"
            ],
            "known_fixed_fields_fit": fit["known_fixed_fields_fit"],
            "safe_for_fixed_table_insertion": fit[
                "safe_for_fixed_table_insertion"
            ],
            "geometry_regression_correction": artifact(
                paths["geometry_correction"]
            ),
            "geometry_repair_validation": artifact(
                paths["geometry_repair_validation"]
            ),
            "geometry_corrected_tm_id": geometry_record["tm_id"],
            "geometry_capacity_including_nul": geometry_record[
                "capacity_including_nul"
            ],
            "geometry_target_bytes_after": geometry_record["after_bytes"],
            "protected_metadata_changed_bytes_after_repair": geometry_repair_summary[
                "protected_changed_bytes_sum"
            ],
        },
        "system_table_application": {
            "proof": artifact(paths["system_proof"]),
            "catalog_allowlist": sorted(EXPECTED_SYSTEM_CATALOGS),
            "approved_system_tm_units": system_proof["approved_system_tm_units"],
            "applied_unique_tm_units": system_proof["applied_unique_tm_units"],
            "replacement_table_fields": system_proof["replacement_table_fields"],
            "system_database_scanner_occurrences": system_proof[
                "system_database_scanner_occurrences"
            ],
            "structured_field_coverage_matches_scanner_occurrences": system_proof[
                "structured_field_coverage_matches_scanner_occurrences"
            ],
            "table_specific_boundary_replacement_fields": system_proof[
                "table_specific_boundary_replacement_fields"
            ],
            "payloads_rebuilt": system_proof["payloads_rebuilt"],
            "fixed_payload_changes_outside_declared_slots": system_proof[
                "fixed_payload_changes_outside_declared_slots"
            ],
            "verification_error_count": system_proof["verification_error_count"],
            "payloads": system_payloads,
            "valid": system_proof["valid"],
        },
        "nested_boundary_resolution": {
            "tm_id": NESTED_TM_ID,
            "scanner_source_text": nested["corrupt_scanner_source_text"],
            "reviewed_tm_translation_ko": nested["reviewed_translation_ko"],
            "coexisting_exact_occurrence": nested_evidence[
                "coexisting_exact_occurrence"
            ],
            "nested_occurrence_id": nested_evidence["occurrence_id"],
            "nested_logical_locator": nested_evidence["logical_locator"],
            "nested_scanner_offset": nested_evidence["scanner_offset"],
            "nested_scanner_raw_hex": nested_evidence["scanner_raw_hex"],
            "parent_table_unit_id": nested_evidence["table_unit_id"],
            "parent_table_offset": nested_evidence["table_offset"],
            "parent_table_raw_hex": nested_evidence["table_raw_hex"],
            "missing_real_field_prefix_hex": nested_evidence[
                "missing_real_field_prefix_hex"
            ],
            "parent_clean_source_text": nested["clean_source_text"],
            "table_specific_translation_ko": nested[
                "table_specific_translation_ko"
            ],
            "application_mode": nested["application_mode"],
            "capacity_including_nul": nested["capacity"],
            "required_with_nul": nested["encoded_fit"]["required_with_nul"],
            "raw_source_sha256": nested_evidence["raw_source_sha256"],
            "raw_bytes_verified": (
                nested_evidence["raw_source_sha256_verified"]
                and nested_evidence["raw_field_bytes_verified"]
                and nested_evidence["raw_scanner_bytes_verified"]
            ),
            "occurrence_field_delta_after_resolution": {
                "artifact": artifact(paths["occurrence_delta"]),
                "system_occurrences": occurrence_delta["system_occurrences"],
                "applied_structured_fields": occurrence_delta[
                    "applied_structured_fields"
                ],
                "net_delta": occurrence_delta[
                    "net_occurrence_minus_field_delta"
                ],
                "units_with_count_delta": occurrence_delta[
                    "units_with_count_delta"
                ],
            },
            "resolved": True,
        },
        "resolved_incidents": [
            {
                "id": "heuristic_warning_exhaustive_final_qa",
                "initial_warning_events": 148,
                "resolution": (
                    "All warnings were reviewed with source, target, surface, and "
                    "context. Seven genuine warning-bearing defects plus one adjacent "
                    "cross-unit contamination were explicitly corrected. The 141 "
                    "remaining punctuation acting-mark and Korean line-reflow warnings "
                    "are individually hash-bound and waived."
                ),
                "target_corrections": warning_qa_application[
                    "total_target_corrections"
                ],
                "waivers": warning_waiver_verification["waiver_entries"],
                "unwaived_warnings": warning_waiver_verification[
                    "unwaived_warning_events"
                ],
                "evidence": artifact(paths["warning_waiver_verification"]),
                "resolved": True,
            },
            {
                "id": "review_validation_initial_6_errors",
                "initial_errors": 6,
                "resolution": (
                    "Three false repeated-question-mark heuristic hits were "
                    "corrected in the validators; three cross-unit contaminated "
                    "targets were restored without automatic retranslation."
                ),
                "integrity_corrections": 3,
                "evidence": artifact(paths["integrity_corrections"]),
                "final_errors": 0,
                "resolved": True,
            },
            {
                "id": "font_encoding_initial_48_errors",
                "initial_errors": 48,
                "breakdown": {"U+00B7": 47, "U+FF5E": 1},
                "resolution": (
                    "The append-only mapping now extracts and renders required "
                    "non-EUC-JP custom glyphs in addition to Hangul."
                ),
                "final_errors": injection_verification[
                    "approved_unit_encoding_errors"
                ],
                "resolved": True,
            },
            {
                "id": "initial_417_unmatched_system_boundaries",
                "initial_unmatched_tm_units": 417,
                "discovery": artifact(paths["remaining_discovery"]),
                "resolution": (
                    "Exact scanner/table byte-range overlap mapped and reviewed "
                    "every remaining boundary; the final component also records "
                    "the separately discovered nested occurrence."
                ),
                "final_component_units": 418,
                "final_unmatched_tm_units": 0,
                "resolved": True,
            },
            {
                "id": "initial_42_fixed_width_overflows",
                "initial_fixed_overflows": 42,
                "preflight": artifact(paths["fixed_preflight"]),
                "application": artifact(paths["fixed_application"]),
                "resolution": (
                    "Forty-two explicitly pinned internal-model compact rewrites "
                    "were applied with line breaks and mechanical meaning preserved."
                ),
                "final_fixed_overflows": fit["fixed_overflow_count"],
                "resolved": True,
            },
            {
                "id": "fixed_schema_capacity_overlapped_binary_metadata",
                "initial_protected_metadata_bytes_changed": 1_231,
                "initial_affected_record_file_instances": 621,
                "affected_schemas": [
                    "item",
                    "shop",
                    "special",
                    "help",
                    "monster_book",
                ],
                "resolution": (
                    "Corrected five fixed-field capacities to exclude adjacent "
                    "binary metadata, compacted the one newly overflowing shop "
                    "name with the internal model, rebuilt all 13 payloads, and "
                    "independently verified zero protected-byte changes."
                ),
                "correction": artifact(paths["geometry_correction"]),
                "repair_validation": artifact(
                    paths["geometry_repair_validation"]
                ),
                "final_protected_metadata_bytes_changed": geometry_repair_summary[
                    "protected_changed_bytes_sum"
                ],
                "resolved": True,
            },
            {
                "id": "discarded_26_catalog_intermediate_proof",
                "initial_catalogs_scanned": 26,
                "resolution": (
                    "The proof allowlist was restricted to the 13 authoritative "
                    "system tables, excluding one battle tutorial and twelve party "
                    "BTEM catalogs that could create cross-surface false matches."
                ),
                "final_catalogs_scanned": system_proof["payloads_rebuilt"],
                "final_proof": artifact(paths["system_proof"]),
                "resolved": True,
            },
            {
                "id": "scanner_occurrence_5236_vs_structured_field_5235",
                "initial_scanner_occurrences": 5_236,
                "initial_structured_fields": 5_235,
                "resolution": (
                    "The second 行動 scanner occurrence was proven to be a nested "
                    "suffix of ability:218:name 最速行動.  The shared reviewed TM "
                    "target 행동 was preserved for help:0:title while the parent "
                    "field receives the table-specific target 최속 행동."
                ),
                "final_scanner_occurrences": system_proof[
                    "system_database_scanner_occurrences"
                ],
                "final_structured_fields": system_proof[
                    "replacement_table_fields"
                ],
                "final_delta": occurrence_delta[
                    "net_occurrence_minus_field_delta"
                ],
                "resolved": True,
            },
        ],
        "implementation_scripts": script_artifacts,
        "final_invariants": {
            "internal_model_only": True,
            "original_rvz_unchanged": rvz_matches,
            "review_chain_149_batches_29777_units": True,
            "heuristic_warnings_148_classified_unwaived_zero": True,
            "batch_0149_has_177_units": True,
            "canonical_boundary_720_tm_727_fields_zero_ambiguity": True,
            "translation_memory_29777_units_84761_occurrences_100_percent": True,
            "append_only_codebook_1369_characters_zero_collisions": True,
            "font_pages_9_zero_encoding_errors": True,
            "system_tables_13_payloads_5236_fields_zero_errors": True,
        },
        "error_count": 0,
        "errors": [],
        "advisory_warning_count": validator_warning_count,
        "valid": True,
    }

    temp = OUTPUT.with_suffix(OUTPUT.suffix + ".tmp")
    temp.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temp, OUTPUT)
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "sha256": sha256(OUTPUT),
                "reviewed_units": review_chain["reviewed_units"],
                "canonical_tm_units": boundary_scope["audited_tm_units"],
                "canonical_table_units": boundary_scope["linked_table_units"],
                "font_pages": len(wtm_payloads),
                "system_payloads": system_proof["payloads_rebuilt"],
                "system_fields": system_proof["replacement_table_fields"],
                "error_count": 0,
                "valid": True,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
