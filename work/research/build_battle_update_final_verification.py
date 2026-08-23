#!/usr/bin/env python3
"""Consolidate the final battle-update static, runtime, release, and installer proof."""

from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
OUTPUT = W / "validation" / "battle_update_final_verification.json"
PATHS = {
    "battle_application": W / "battle_enemy_application" / "application_report.json",
    "staging_integration": W / "battle_enemy_application" / "staging_integration_report.json",
    "font_injection": W / "font" / "final_v3" / "injection_verification.json",
    "battle_coverage": W / "validation" / "battle_text_independent_coverage_audit.json",
    "system_residue": W / "system_text_residue_application" / "application_report.json",
    "system_residue_integration": W / "system_text_residue_application" / "staging_integration_report.json",
    "residue_closure": W / "validation" / "localization_residue_closure.json",
    "all_btl_vld": W / "validation" / "all_btl_vld_surface_classification.json",
    "full_text_closure": W / "validation" / "full_text_surface_closure.json",
    "geometry_repair": W / "runtime_validation" / "fixed_table_geometry_repair_validation.json",
    "staging_manifest": W / "final_runtime_staging" / "staging_manifest.json",
    "runtime": W / "validation" / "dolphin_runtime_validation.json",
    "release_validation": W / "validation" / "final_release_validation.json",
    "installer_fixture": W / "validation" / "installer_fixture.json",
    "package_manifest": ROOT / "outputs" / "Arc_Rise_Fantasia_Korean_Patch_v1.0.2" / "MANIFEST.json",
    "zip": ROOT / "outputs" / "Arc_Rise_Fantasia_Korean_Patch_v1.0.2.zip",
    "zip_checksum": ROOT / "outputs" / "Arc_Rise_Fantasia_Korean_Patch_v1.0.2.zip.sha256",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, **details: Any) -> None:
        row = {"name": name, "passed": bool(passed), **details}
        checks.append(row)
        if not passed:
            errors.append({"check": name, **details})

    for name, path in PATHS.items():
        check(f"artifact_exists:{name}", path.is_file(), path=str(path))
    if errors:
        raise SystemExit(json.dumps(errors, ensure_ascii=False, indent=2))

    app = load(PATHS["battle_application"])
    check("battle_application_valid", app.get("valid") is True and app.get("error_count") == 0)
    check("battle_translation_counts", app.get("counts") == {
        "entries": 270, "display_names": 270, "alternate_display_names": 87,
        "part_names": 3, "skill_names": 672, "total_units": 1032,
        "entries_fitting_source_slots": 270,
        "changed_outside_allowed_bytes": 0,
    }, actual=app.get("counts"))
    check("battle_temp_files_cleaned", app.get("repacked_entry_temp_files_cleaned") is True)
    coverage = load(PATHS["battle_coverage"])
    check("battle_independent_coverage", coverage.get("catalog", {}).get("unit_count") == 1032
          and coverage.get("counts", {}).get("uncovered_before_first_rtdp") == 0
          and coverage.get("counts", {}).get("unchanged_before_first_rtdp") == 0)
    residue = load(PATHS["system_residue"])
    check("system_residue_valid", residue.get("valid") is True
          and residue.get("error_count") == 0
          and residue.get("counts", {}).get("translated_fields") == 30
          and residue.get("counts", {}).get("ability_names") == 14
          and residue.get("counts", {}).get("changed_outside_allowed_bytes") == 0
          and residue.get("coverage", {}).get("semantic_japanese_unmatched_after") == 0)
    residue_integration = load(PATHS["system_residue_integration"])
    check("system_residue_integration_valid", residue_integration.get("valid") is True
          and residue_integration.get("error_count") == 0)
    closure = load(PATHS["residue_closure"])
    check("localization_residue_closure_valid", closure.get("valid") is True
          and closure.get("error_count") == 0
          and closure.get("summary", {}).get("semantic_japanese_unmatched_after") == 0
          and closure.get("summary", {}).get("changed_outside_declared_text_slots") == 0)
    all_btl_vld = load(PATHS["all_btl_vld"])
    check("all_btl_vld_surface_classification_valid",
          all_btl_vld.get("valid") is True
          and all_btl_vld.get("exact_compound_hit_count") == 0
          and sum(row.get("entry_count", 0) for row in all_btl_vld.get("summary", [])) == 863)
    full_text = load(PATHS["full_text_closure"])
    check("full_text_surface_closure_valid",
          full_text.get("valid") is True and full_text.get("error_count") == 0
          and full_text.get("summary", {}).get("semantic_japanese_in_korean_targets") == 0
          and full_text.get("summary", {}).get("unmatched_semantic_japanese_after") == 0
          and full_text.get("summary", {}).get("exact_burst_shot_source_hits") == 0)


    font = load(PATHS["font_injection"])
    check("font_v3_valid", font.get("valid") is True and font.get("error_count") == 0)
    check("font_v3_counts", font.get("assigned_characters") == 1370
          and font.get("approved_units_encoded") == 30933
          and font.get("approved_unit_encoding_errors") == 0)

    geometry = load(PATHS["geometry_repair"])
    check("fixed_table_geometry_repair_valid", geometry.get("valid") is True
          and geometry.get("summary", {}).get("protected_changed_bytes_sum") == 0
          and geometry.get("item_record_id_invariant", {}).get("payload_mismatch_count") == 0
          and geometry.get("item_record_id_invariant", {}).get("payload_duplicate_id_groups") == 0)

    staging = load(PATHS["staging_manifest"])
    integration = load(PATHS["staging_integration"])
    check("staging_integration_valid", integration.get("valid") is True
          and integration.get("error_count") == 0)
    check("staging_counts", staging.get("counts", {}).get("staged_physical_files") == 684
          and staging.get("riivolution", {}).get("file_count") == 684
          and staging.get("riivolution", {}).get("memory_count") == 926)
    check("staging_manifest_binding",
          integration.get("staging_manifest", {}).get("sha256") == sha(PATHS["staging_manifest"]))
    check("battle_application_binding",
          staging.get("battle_enemy_application", {}).get("report_sha256")
          == sha(PATHS["battle_application"]))
    check("system_residue_binding",
          staging.get("system_text_residue_application", {}).get("report_sha256")
          == sha(PATHS["system_residue"])
          and staging.get("counts", {}).get("system_text_residue_translation_occurrences") == 30
          and residue_integration.get("staging_manifest", {}).get("sha256")
          == sha(PATHS["staging_manifest"]))
    staged_paths = {row.get("physical_path") for row in staging.get("static_validation", {}).get("staged_files", [])}
    sfd_repair = staging.get("sfd_runtime_compatibility", {})
    check("unsafe_reencoded_sfd_overlay_absent", "Movie/RAY_OP_02.sfd" not in staged_paths
          and sfd_repair.get("overlay_present") is False
          and sfd_repair.get("source_disc_file_used") is True
          and sfd_repair.get("valid") is True)

    runtime = load(PATHS["runtime"])
    expected_runtime_checks = {
        "final_patch_reaches_original_cinematic",
        "original_sfd_sequence_reaches_live_battle",
        "korean_battle_monster_and_result_text_renders",
        "battle_frames_continue_advancing",
        "runtime_session_bound_and_logs_clean",
    }
    observed_runtime_checks = {row.get("name") for row in runtime.get("checks", [])}
    check("runtime_report_valid", runtime.get("valid") is True
          and runtime.get("error_count") == 0 and runtime.get("failed_count") == 0)
    check("runtime_check_closure", observed_runtime_checks == expected_runtime_checks,
          expected=sorted(expected_runtime_checks), actual=sorted(str(x) for x in observed_runtime_checks))
    settings = runtime.get("runtime_session", {}).get("settings", {})
    check("runtime_vulkan_original_sfd_contract", settings.get("GFXBackend") == "Vulkan"
          and settings.get("FastDiscSpeed") is False and settings.get("MMU") is False)
    check("runtime_staging_binding",
          runtime.get("staging_manifest_sha256") == sha(PATHS["staging_manifest"]))

    package = load(PATHS["package_manifest"])
    check("package_counts", package.get("game_replacement_file_count") == 684
          and package.get("overlay_file_count") == 685)
    check("package_staging_binding",
          package.get("staging_manifest_sha256") == sha(PATHS["staging_manifest"]))
    check("runtime_package_binding",
          runtime.get("package_manifest_sha256") == sha(PATHS["package_manifest"]))

    release = load(PATHS["release_validation"])
    check("release_validation_valid", release.get("valid") is True
          and release.get("error_count") == 0 and not release.get("errors"))
    check("release_counts", release.get("game_replacement_file_count") == 684
          and release.get("overlay_file_count") == 685)
    check("release_zip_binding", release.get("zip_sha256") == sha(PATHS["zip"]))
    sidecar = PATHS["zip_checksum"].read_text(encoding="ascii").split()
    check("zip_sidecar_binding", bool(sidecar) and sidecar[0].upper() == sha(PATHS["zip"]))

    installer = load(PATHS["installer_fixture"])
    check("installer_fixture_valid", installer.get("valid") is True
          and installer.get("failed_count") == 0)
    check("installer_checks_all_passed",
          installer.get("passed_count") == len(installer.get("checks", []))
          and all(row.get("passed") is True for row in installer.get("checks", [])))

    artifacts = [
        {"name": name, "path": str(path.relative_to(ROOT)).replace("\\", "/"),
         "size_bytes": path.stat().st_size, "sha256": sha(path)}
        for name, path in PATHS.items()
    ]
    report = {
        "schema": "arf-ko-battle-update-final-verification-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "checks": checks,
        "passed_count": sum(row["passed"] for row in checks),
        "failed_count": sum(not row["passed"] for row in checks),
        "error_count": len(errors),
        "errors": errors,
        "artifacts": artifacts,
        "valid": not errors,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "passed_count": report["passed_count"], "failed_count": report["failed_count"],
        "error_count": report["error_count"], "output": str(OUTPUT),
        "sha256": sha(OUTPUT), "valid": report["valid"],
    }, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
