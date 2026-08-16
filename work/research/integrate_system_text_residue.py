#!/usr/bin/env python3
"""Integrate the closed system-table residue lane into cumulative staging."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
APP = W / "system_text_residue_application"
REPORT = APP / "application_report.json"
SYSTEM = APP / "system.vol"
MANIFEST = W / "final_runtime_staging/staging_manifest.json"
FILES = W / "final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files"
BATTLE_INTEGRATION = W / "battle_enemy_application/staging_integration_report.json"


def h(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def need(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def one(rows: list[dict], physical: str) -> dict:
    matches = [row for row in rows if row.get("physical_path") == physical]
    need(len(matches) == 1, f"expected one manifest row: {physical}")
    return matches[0]


def main() -> int:
    for path in (REPORT, SYSTEM, MANIFEST, BATTLE_INTEGRATION):
        need(path.is_file(), f"missing input: {path}")
    app = load(REPORT)
    need(app.get("valid") is True and app.get("error_count") == 0, "residue application invalid")
    need(app.get("counts") == {
        "translated_fields": 30, "ability_names": 14, "chat_titles": 15,
        "shop_names": 1, "payloads_rebuilt": 3, "changed_outside_allowed_bytes": 0,
    }, "unexpected residue counts")
    need(app.get("coverage", {}).get("semantic_japanese_unmatched_after") == 0, "system residue remains")
    need(h(SYSTEM) == app["system"]["output_sha256"], "system output hash mismatch")

    staged_system = FILES / "Sys/system.vol"
    shutil.copy2(SYSTEM, staged_system)
    need(h(staged_system) == h(SYSTEM), "staged system copy mismatch")

    doc = load(MANIFEST)
    static = doc["static_validation"]
    system_row = one(static["staged_files"], "Sys/system.vol")
    system_row.update({"output_sha256": h(SYSTEM), "output_size": SYSTEM.stat().st_size})
    system = static["system"]
    system.update({
        "mode": "rebuilt_cumulatively_from_final_tables_fonts_v3_nowloading_and_residue_closure",
        "output_system_sha256": h(SYSTEM), "output_system_size": SYSTEM.stat().st_size,
        "rebuild_report": "work/system_text_residue_application/system_rebuild_report.json",
    })
    payload_hashes = {Path(row["output"]).name: row["output_sha256"] for row in app["payloads"]}
    found = set()
    for entry in system["verified_internal_entries"]:
        name = entry.get("name")
        if name in payload_hashes:
            entry["sha256"] = payload_hashes[name]
            found.add(name)
    need(found == set(payload_hashes), "manifest internal payload entries incomplete")

    doc["inputs"]["system_text_residue_translations"] = {
        "path": app["translation_map"]["path"], "sha256": app["translation_map"]["sha256"],
        "translation_engine_policy": "Codex internal model only",
        "external_translation_models_or_apis_used": False,
    }
    doc["inputs"]["system_text_residue_application_report"] = {
        "path": str(REPORT), "sha256": h(REPORT),
    }
    doc["counts"]["system_text_residue_translation_occurrences"] = 30
    doc["system_text_residue_application"] = {
        "report": str(REPORT), "report_sha256": h(REPORT),
        "translated_fields": 30, "ability_names": 14, "chat_titles": 15,
        "shop_names": 1, "semantic_japanese_unmatched_after": 0,
        "changed_outside_allowed_bytes": 0, "valid": True,
    }
    doc["runtime_ready_release"] = False
    doc["dolphin_screen_test"] = "pending_final_single_run"
    MANIFEST.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    battle = load(BATTLE_INTEGRATION)
    battle["staging_manifest"] = {"path": str(MANIFEST), "sha256": h(MANIFEST)}
    battle["outputs"]["Sys/system.vol"] = {
        "path": str(staged_system), "size": staged_system.stat().st_size, "sha256": h(staged_system),
    }
    battle["system_text_residue"] = {
        "report": str(REPORT), "report_sha256": h(REPORT),
        "translated_fields": 30, "semantic_japanese_unmatched_after": 0, "valid": True,
    }
    battle["error_count"] = 0
    battle["errors"] = []
    battle["valid"] = True
    BATTLE_INTEGRATION.write_text(json.dumps(battle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    integration = {
        "schema": "arf-system-text-residue-staging-integration-v1", "game_id": "RPJJ99",
        "application_report": {"path": str(REPORT), "sha256": h(REPORT)},
        "staging_manifest": {"path": str(MANIFEST), "sha256": h(MANIFEST)},
        "staged_system": {"path": str(staged_system), "sha256": h(staged_system), "size": staged_system.stat().st_size},
        "updated_internal_entries": payload_hashes,
        "valid": True, "error_count": 0, "errors": [],
    }
    output = APP / "staging_integration_report.json"
    output.write_text(json.dumps(integration, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(integration, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
