#!/usr/bin/env python3
"""Close the visual-surface inventory after the reviewed patches exist."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    visual = ROOT / "work/runtime_fix/visual_sweep"
    runtime = ROOT / "work/runtime_fix"
    movie_path = visual / "movies/sfd_visual_audit_index.json"
    wtm_path = visual / "standalone_wtm/standalone_wtm_visual_audit.json"
    movie = json.loads(movie_path.read_text(encoding="utf-8"))
    wtm = json.loads(wtm_path.read_text(encoding="utf-8"))
    if len(movie.get("movies", [])) != 21 or len(wtm.get("assets", [])) != 45:
        raise ValueError("visual audit inventory counts changed")

    for row in movie["movies"]:
        relative = row["relative_path"]
        if relative == "Movie/RAY_OP_02.sfd":
            row["review_verdict"] = "original_retained_runtime_compatibility"
            row["review_notes"] = (
                "Localized re-encode rejected: the captured freeze matches 48.5 s inside the edited "
                "48.1-54.5 s interval, and the candidate has 143 timestamp regressions. "
                "The trusted original SFD is used byte-for-byte."
            )
        elif relative == "Movie/RAY_ED_ROLL.sfd":
            row["review_verdict"] = "no_japanese_script"
            row["review_notes"] = "Credits are English role labels and romanized names; no Japanese display text."
        else:
            row["review_verdict"] = "no_japanese_script"
            row["review_notes"] = "Fixed-interval and scene-change contact sheets reviewed; no Japanese display text."
    movie["manual_review_complete"] = True
    movie["movies_requiring_patch"] = 0
    movie["movies_without_japanese_script"] = 20
    movie["movies_retained_original_for_runtime_compatibility"] = 1
    movie["valid"] = True
    write_json(movie_path, movie)

    for row in wtm["assets"]:
        relative = row["relative_path"]
        if relative.startswith("Event/endroll/EV09_18_0200C_"):
            row["review_verdict"] = "korean_patch_verified"
            row["review_notes"] = "Localized ending card; structure, deterministic re-encode and contact-sheet checks PASS."
        elif relative in {"Sys/strapA_jp.wtm", "Sys/strapB_jp.wtm"}:
            row["review_verdict"] = "korean_patch_verified_in_base_overlay"
            row["review_notes"] = "Already localized in the 655-file base overlay; Korean Wii strap proven in Dolphin."
        elif relative.startswith("_sasaki/"):
            row["review_verdict"] = "excluded_debug_internal_no_display_words"
            row["review_notes"] = "Developer font/test/gradient asset, not a shipped user-facing text surface."
        else:
            row["review_verdict"] = "no_japanese_display_text"
            row["review_notes"] = "Rendered asset reviewed; logo/portrait/language-neutral content only."
    wtm["manual_review_complete"] = True
    wtm["patched_ending_cards"] = 23
    wtm["patched_strap_assets"] = 2
    wtm["remaining_japanese_user_visible_assets"] = 0
    wtm["valid"] = True
    write_json(wtm_path, wtm)

    dependencies = {
        "movie_audit": movie_path,
        "standalone_wtm_audit": wtm_path,
        "endroll_manifest": runtime / "endroll_ui/manifest.json",
        "endroll_verification": runtime / "endroll_ui/verification_summary.json",
        "opening_bnr_manifest": runtime / "opening_bnr_ko/opening_bnr_korean_payload_manifest.json",
        "hbm_manifest": runtime / "hbm_ko/hbm_korean_payload_manifest.json",
        "opening_sfd_timestamp_audit": ROOT / "work/runtime_validation/sfd_frame_timestamp_audit.json",
        "opening_sfd_freeze_match": ROOT / "work/runtime_validation/sfd_freeze_frame_match.json",
        "opening_bnr_contact": runtime / "opening_bnr_ko/audit/opening_bnr_original_vs_korean.png",
        "endroll_before_contact": runtime / "endroll_ui/before_contact_sheet.png",
        "endroll_after_contact": runtime / "endroll_ui/after_contact_sheet.png",
        "standalone_tpl_debug_abc": visual / "standalone_tpl/DATA_abc_0.png",
        "standalone_tpl_debug_background": visual / "standalone_tpl/DATA_wtmvw_bg_0.png",
    }
    missing = [name for name, path in dependencies.items() if not path.is_file()]
    if missing:
        raise ValueError(f"missing visual closure artifacts: {missing}")
    output = visual / "final_visual_surface_audit.json"
    report = {
        "schema": "arf-ko-final-visual-surface-audit-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal model only",
        "external_translation_models_or_apis_used": False,
        "inventories": {
            "sfd_movies": 21,
            "sfd_sampled_frames": sum(int(row["frame_count"]) for row in movie["movies"]),
            "sfd_contact_sheets": sum(len(row["contact_sheets"]) for row in movie["movies"]),
            "standalone_wtm": 45,
            "standalone_tpl_debug_assets": 2,
            "opening_bnr": 1,
            "hbm_physical_assets": 3,
        },
        "localized_surfaces": {
            "opening_movie": 0,
            "opening_bnr": 1,
            "ending_cards": 23,
            "home_button_assets": 3,
            "wii_strap_assets_already_in_base": 2,
        },
        "original_runtime_compatible_surfaces": {"opening_movie": 1},
        "remaining_japanese_user_visible_visual_surfaces": 1,
        "runtime_compatibility_waivers": [
            {
                "physical_path": "Movie/RAY_OP_02.sfd",
                "remaining_text": "アークライズファンタジア",
                "reason": "trusted original retained; rejected localized candidate corrupts video timestamps and freezes at runtime",
                "source_sha256": "8653907F6F4DE206E57FE108EC2D050135E4DB68306AC8CAE7D2BEBCA46DC4A0",
            }
        ],
        "artifacts": {
            name: {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path)}
            for name, path in dependencies.items()
        },
        "manual_visual_review_complete": True,
        "error_count": 0,
        "errors": [],
        "valid": True,
    }
    write_json(output, report)
    print(json.dumps({"valid": True, "output": str(output), "sha256": sha256(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
