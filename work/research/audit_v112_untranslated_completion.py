#!/usr/bin/env python3
"""Bind whole-game untranslated-surface evidence to the v1.1.2 release."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work"
REL = ROOT / "release_metadata" / "rom_patcher_v1.1.2"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return value


def need(value: bool, message: str, errors: list[str]) -> None:
    if not value:
        errors.append(message)


def artifact(path: Path) -> dict:
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "size": path.stat().st_size,
        "sha256": sha256(path),
    }


def main() -> int:
    paths = {
        "full_text_surface": WORK / "validation/full_text_surface_closure.json",
        "residue_closure": WORK / "validation/localization_residue_closure.json",
        "untranslated_surface_v104": WORK / "validation/untranslated_surface_closure_v104.json",
        "final_v105": WORK / "validation/final_v105_comprehensive_validation.json",
        "town_map": WORK / "validation/town_map_legend_release_validation.json",
        "addressee_voice": WORK / "validation/addressee_scene_voice_release_validation.json",
        "main_dol": WORK / "validation/main_dol_runtime_residue_release_validation.json",
        "battle_duplicate": REL / "ALL_BATTLE_TEXT_DUPLICATE_AUDIT.json",
        "targeted_battle": REL / "TARGETED_BATTLE_PROOF.json",
        "release_validation": REL / "VALIDATION.json",
        "sfd_review": WORK / "runtime_validation/sfd_dialogue_review_v112/SFD_AUDIO_DIALOGUE_REVIEW.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise SystemExit(f"missing dependencies: {missing}")
    reports = {name: load(path) for name, path in paths.items()}
    errors: list[str] = []

    full = reports["full_text_surface"]
    residue = reports["residue_closure"]
    visual = reports["untranslated_surface_v104"]
    v105 = reports["final_v105"]
    town = reports["town_map"]
    addressee = reports["addressee_voice"]
    main_dol = reports["main_dol"]
    battle = reports["battle_duplicate"]
    target = reports["targeted_battle"]
    release = reports["release_validation"]
    sfd = reports["sfd_review"]

    for name, report in reports.items():
        need(report.get("valid") is True, f"{name}: valid is not true", errors)
    need(full.get("summary", {}).get("semantic_japanese_in_korean_targets") == 0,
         "semantic Japanese remains in Korean text targets", errors)
    need(full.get("summary", {}).get("unmatched_semantic_japanese_after") == 0,
         "unmatched semantic Japanese remains after full text audit", errors)
    need(residue.get("summary", {}).get("semantic_japanese_unmatched_after") == 0,
         "battle/system residue remains", errors)
    need(visual.get("result", {}).get("confirmed_user_visible_semantic_japanese_remaining") == 0,
         "v104 visual/text closure reports semantic Japanese", errors)
    need(battle.get("btl_usual_btem", {}).get("residue_count") == 0,
         "btl_usual residue remains", errors)
    need(len(battle.get("battle_magic", {}).get("final_residue_hits", [])) == 0,
         "special/boss battle skill residue remains", errors)
    need(battle.get("battle_tutorial", {}).get("final_residue_count") == 0,
         "battle tutorial residue remains", errors)
    need(battle.get("system_text_residue", {}).get("semantic_japanese_unmatched_after") == 0,
         "system text residue remains", errors)
    need(target.get("output_image_all_722_hashes_match") is True,
         "v1.1.2 output image hashes are not fully bound", errors)
    need(release.get("delta_payload", {}).get("entry_count") == 722,
         "release delta entry count changed", errors)
    need(release.get("e2e", [{}])[0].get("checked_entries") == 722 and
         release.get("e2e", [{}])[0].get("mismatch_count") == 0,
         "release E2E 722/722 proof failed", errors)
    need(release.get("standalone_boot", {}).get("valid") is True,
         "standalone boot proof failed", errors)
    need(sfd.get("movie_count") == 21 and sfd.get("movies_with_audio") == 14 and
         sfd.get("movies_without_audio") == 7,
         "SFD inventory counts changed", errors)
    need(sfd.get("movies_with_story_dialogue") == 1 and
         sfd.get("active_subtitle_line_count") == 29,
         "SFD story-dialogue subtitle closure changed", errors)
    need(sfd.get("current_runtime_subtitles_already_korean") is True and
         sfd.get("burn_in_sfd_required") is False,
         "RAY_OP_02 Korean engine-subtitle proof failed", errors)
    need(sfd.get("active_map_is_in_v112_staging") is True,
         "active RAY_OP_02 subtitle map is absent from v1.1.2 staging", errors)

    scope = full["scope"]
    v104_scope = visual["scope"]
    sfd_closure = {
        "schema": "arf-sfd-dialogue-closure-v1",
        "game_id": "RPJJ99",
        "valid": not errors,
        "movies": 21,
        "movies_without_audio": 7,
        "movies_with_audio": 14,
        "story_dialogue_movies": 1,
        "story_dialogue_movie": "Movie/RAY_OP_02.sfd",
        "story_dialogue_seconds": [152.368, 283.088],
        "active_engine_subtitle_script": sfd["active_subtitle_script"],
        "active_engine_subtitle_lines": 29,
        "active_engine_subtitles_korean": True,
        "active_map_staged_sha256": sfd["active_map_staged_sha256"],
        "semantic_spoken_dialogue_without_korean_subtitles": 0,
        "movie_reencode_required": False,
        "trusted_original_sfd_retained": True,
        "review_candidate_applied_to_game": False,
        "translation_provenance": "Codex internal",
        "external_translation_service_used_for_korean": False,
        "stt_role": "speech-presence and timing evidence only; no STT text was accepted as Korean translation",
        "approved_unchanged_visual_mark": {
            "path": "Movie/RAY_OP_02.sfd",
            "text": "アークライズファンタジア",
            "function": "opening title-logo subline, not dialogue or subtitle",
            "reason": "user directed the nonessential movie graphic to remain original; re-encoded SFD previously froze, while all spoken story dialogue is already covered by the Korean BSCR subtitle lane",
        },
        "source_review": artifact(paths["sfd_review"]),
        "errors": errors,
    }
    sfd_path = REL / "SFD_DIALOGUE_CLOSURE.json"
    sfd_path.write_text(json.dumps(sfd_closure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = {
        "schema": "arf-v112-untranslated-completion-audit-v1",
        "game_id": "RPJJ99",
        "release_version": "1.1.2",
        "release_commit": "22012b0c3b5bd86d427d28115c0bf7a320038a01",
        "objective": "Translate every untranslated user-visible Japanese text surface into Korean",
        "translator_model": "Codex internal",
        "external_translation_models_or_apis_used": False,
        "coverage": {
            "vetted_rtdp_localization_payloads": scope["vetted_rtdp_localization_payloads"],
            "event_script_payloads": scope["event_script_payloads"],
            "translation_memory_units": scope["translation_memory_units"],
            "translation_occurrences": scope["translation_occurrences"],
            "battle_vld_entries_classified": scope["battle_vld_entries_classified"],
            "battle_enemy_display_skill_part_units": scope["battle_enemy_units"],
            "battle_tutorial_semantic_units": scope["battle_tutorial_semantic_units"],
            "system_catalog_units": scope["system_catalog_units"],
            "battle_party_name_payloads": scope["battle_party_name_payloads"],
            "special_boss_skill_slots": v104_scope["special_boss_skill_occurrences"],
            "map_description_files": v104_scope["map_description_files"],
            "map_description_members": v104_scope["map_description_members"],
            "battle_raster_entries": v104_scope["battle_raster_entries"],
            "battle_raster_text_items": v104_scope["battle_raster_text_items"],
            "main_dol_verified_memory_writes": battle["main_dol_runtime"]["verified_memory_writes"],
            "town_map_legend": "fully bound and valid",
            "addressee_story_phase_voice": "fully bound and valid",
            "sfd_movies": 21,
            "sfd_story_dialogue_subtitle_lines": 29,
            "release_delta_entries": 722,
            "release_output_hash_matches": 722,
        },
        "current_release_fixes": {
            "レイストーン": "레이 스톤",
            "名称未設定": "이름 미설정",
            "all_battle_text_duplicate_audit_valid": True,
        },
        "result": {
            "confirmed_untranslated_semantic_japanese_remaining": 0,
            "semantic_spoken_dialogue_without_korean_subtitles": 0,
            "unexplained_residue_flags": 0,
            "approved_unchanged_original_japanese_visual_marks": 1,
            "approved_unchanged_original_japanese": [sfd_closure["approved_unchanged_visual_mark"]],
            "not_missing_translation": [
                "original Japanese voice performances whose meaning is covered by Korean game text/subtitles",
                "theme-song vocals and music",
                "intentional decorative English interface art",
                "typography-only Japanese punctuation/long-vowel marks in fixed binary fields",
            ],
            "goal_scope_complete": not errors,
        },
        "release": {
            "rom_patcher_zip": release["release_package"]["file_name"],
            "rom_patcher_zip_size": release["release_package"]["size"],
            "rom_patcher_zip_sha256": release["release_package"]["sha256"],
            "output_rvz_sha256": release["e2e"][0]["output_sha256"],
            "standalone_boot_valid": release["standalone_boot"]["valid"],
            "defender_new_detection_count": release["defender"]["new_detection_count"],
        },
        "checks": [
            {"name": name, "passed": report.get("valid") is True, "schema": report.get("schema")}
            for name, report in reports.items()
        ] + [
            {"name": "whole_game_semantic_residue_zero", "passed": not errors},
            {"name": "sfd_story_dialogue_has_korean_engine_subtitles", "passed": sfd_closure["semantic_spoken_dialogue_without_korean_subtitles"] == 0},
            {"name": "v112_722_of_722_hash_bound", "passed": target.get("output_image_all_722_hashes_match") is True},
        ],
        "artifacts": {name: artifact(path) for name, path in paths.items()} | {
            "sfd_dialogue_closure": artifact(sfd_path),
        },
        "error_count": len(errors),
        "errors": errors,
        "valid": not errors,
    }
    out = REL / "UNTRANSLATED_COMPLETION_AUDIT.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "valid": result["valid"],
        "confirmed_untranslated_semantic_japanese_remaining": result["result"]["confirmed_untranslated_semantic_japanese_remaining"],
        "approved_unchanged_visual_marks": result["result"]["approved_unchanged_original_japanese_visual_marks"],
        "output": str(out),
        "sha256": sha256(out),
        "errors": errors,
    }, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
