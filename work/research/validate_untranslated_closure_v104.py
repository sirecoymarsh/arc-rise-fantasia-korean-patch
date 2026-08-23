#!/usr/bin/env python3
"""Final structured proof for the v1.0.4 untranslated-surface closure."""

from __future__ import annotations

import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
FILES = W / "final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files"
XML = W / "final_runtime_staging/riivolution_sd/riivolution/arc_rise_fantasia_ko_full.xml"
STAGING = W / "final_runtime_staging/staging_manifest.json"
INTEGRATION = W / "validation/remaining_untranslated_integration.json"
MAGIC = W / "battle_magic_application/application_report.json"
MAPS = W / "map_info_application/application_report.json"
UI = W / "battle_ui_raster_application/application_report.json"
BATTLE_START = W / "runtime_fix/battle_start_residue_patch_report.json"
ENEMY = W / "battle_enemy_application/application_report.json"
SYSTEM_RESIDUE = W / "system_text_residue_application/application_report.json"
GEOMETRY = W / "runtime_validation/fixed_table_geometry_repair_validation.json"
TM = W / "translation/final/translation_memory_draft.json"
MAIN_DOL_TRANSLATIONS = W / "runtime_fix/main_dol_translations.jsonl"
MAGIC_TRANSLATIONS = W / "translation/battle_magic/battle_magic_skill_translations.json"
OUTPUT = W / "validation/untranslated_surface_closure_v104.json"

JP_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff]")


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha(path)}


def main() -> int:
    required = [STAGING, XML, INTEGRATION, MAGIC, MAPS, UI, BATTLE_START, ENEMY, SYSTEM_RESIDUE, GEOMETRY, TM, MAIN_DOL_TRANSLATIONS, MAGIC_TRANSLATIONS]
    for path in required:
        need(path.is_file(), f"missing input: {path}")
    staging = load(STAGING)
    integration = load(INTEGRATION)
    magic = load(MAGIC)
    maps = load(MAPS)
    ui = load(UI)
    start = load(BATTLE_START)
    enemy = load(ENEMY)
    system = load(SYSTEM_RESIDUE)
    geometry = load(GEOMETRY)
    tm = load(TM)

    checks: list[dict[str, Any]] = []
    def check(name: str, condition: bool, **evidence: Any) -> None:
        checks.append({"name": name, "passed": bool(condition), **evidence})

    check("staging_identity", staging.get("schema") == "arf-full-runtime-staging-v2" and staging.get("game_id") == "RPJJ99")
    check("staging_counts", staging["counts"]["staged_physical_files"] == 721 and staging["riivolution"]["file_count"] == 721 and staging["riivolution"]["memory_count"] == 943)
    check("integration_report", integration.get("valid") is True and integration["counts"] == {
        "battle_magic_slots": 80,
        "battle_magic_unique_names": 79,
        "map_description_files": 36,
        "map_description_members": 72,
        "battle_ui_wtm_entries": 12,
        "battle_start_memory_patches": 2,
        "staged_physical_files": 721,
    })
    magic_translations = load(MAGIC_TRANSLATIONS)
    provenance_reports = (magic, maps, ui, start, integration)
    check("translation_provenance",
          all(report.get("translator_model") == "Codex internal" for report in provenance_reports)
          and all(report.get("external_translation_models_or_apis_used") is not True for report in provenance_reports)
          and magic_translations.get("translator_model") == "Codex internal"
          and magic_translations.get("external_translation_models_or_apis_used") is False)

    tree = ET.parse(XML)
    file_nodes = list(tree.getroot().findall(".//file"))
    memory_nodes = list(tree.getroot().findall(".//memory"))
    external = [node.attrib["external"].replace("\\", "/") for node in file_nodes]
    offsets = [node.attrib["offset"].upper() for node in memory_nodes]
    actual = sorted(path.relative_to(FILES).as_posix() for path in FILES.rglob("*") if path.is_file())
    check("xml_and_physical_sets", len(file_nodes) == len(set(external)) == 721 and sorted(external) == actual)
    check("memory_rule_set", len(memory_nodes) == len(set(offsets)) == 943)
    check("xml_hash_binding", sha(XML) == staging["riivolution"]["sha256"])

    staged_rows = {row["physical_path"]: row for row in staging["static_validation"]["staged_files"]}
    row_errors = []
    for physical, row in staged_rows.items():
        path = FILES / Path(physical)
        if not path.is_file() or path.stat().st_size != int(row["output_size"]) or sha(path) != row["output_sha256"]:
            row_errors.append(physical)
    check("all_staged_rows_hash_bound", len(staged_rows) == 721 and not row_errors, mismatches=row_errors)

    magic_vld = FILES / "Btl/btl_magic.vld"
    magic_bytes = magic_vld.read_bytes()
    magic_slot_errors = []
    for row in magic["rows"]:
        offset = int(row["absolute_field_offset"])
        target = bytes.fromhex(row["target_raw_hex"])
        source = bytes.fromhex(row["source_raw_hex"])
        stored_target = bytes(value ^ 0x55 for value in target)
        stored_source = bytes(value ^ 0x55 for value in source)
        if magic_bytes[offset:offset + len(stored_target)] != stored_target:
            magic_slot_errors.append({"entry": row["entry"], "reason": "target mismatch"})
        if target != source and magic_bytes[offset:offset + len(stored_source)] == stored_source:
            magic_slot_errors.append({"entry": row["entry"], "reason": "source still present"})
    check("battle_magic_all_slots", magic.get("valid") is True and magic["counts"]["slots"] == 80 and magic["counts"]["unique_translations"] == 79 and magic["counts"]["changed_outside_allowed_bytes"] == 0 and not magic_slot_errors, errors=magic_slot_errors)
    burst = [row for row in magic["rows"] if "バーストショット" in row["source_text"]]
    check("wyvern_burst_shot", len(burst) == 1 and burst[0]["translation_ko"] == "<버스트 사격")

    map_errors = []
    for row in maps["files"]:
        physical = "interface/" + Path(row["output_path"]).name
        path = FILES / Path(physical)
        if (not path.is_file() or sha(path) != row["output_packed_sha256"] or path.stat().st_size != int(row["source_packed_size"]) or len(row["members"]) != 2):
            map_errors.append(physical)
    translations_text = Path(maps["inputs"]["translations_path"]).read_text(encoding="utf-8-sig")
    map_translation_rows = [line for line in translations_text.splitlines()[1:] if line.strip()]
    map_semantic_japanese = [line for line in map_translation_rows if JP_RE.search(line.split("\t", 1)[1])]
    check("map_descriptions", maps.get("valid") is True and maps["counts"]["map_files"] == 36 and maps["counts"]["description_members"] == 72 and maps["counts"]["resized_files"] == 0 and maps["counts"]["changed_outside_description_members"] == 0 and len(map_translation_rows) == 36 and not map_semantic_japanese and not map_errors, errors=map_errors)

    ui_staged = FILES / "Btl/btl_usual.vol"
    check("battle_raster_ui", ui.get("valid") is True and ui["counts"] == {
        "outer_members": 26,
        "changed_outer_members": 2,
        "modified_wtm_entries": 12,
        "translated_text_items": 19,
        "unexpected_changed_members": 0,
        "size_changed_members": 0,
    } and sha(ui_staged) == ui["output"]["sha256"] and len(ui["wtm_changes"]) == 12)
    required_ui_sources = {"連携", "襲撃 / First attack", "敵襲 / Back attack", "行動選択 / 作戦設定 / ステータス / 逃走", "戦闘不能", "奥義", "弱点 / 耐性"}
    actual_ui_sources = {row["source_visible_text"] for row in ui["wtm_changes"]}
    check("battle_raster_known_surfaces", required_ui_sources <= actual_ui_sources)

    memory_by_offset = {node.attrib["offset"].upper(): node.attrib["value"].upper() for node in memory_nodes}
    new_memory_errors = [row["memory_address_hex"] for row in start["patches"] if memory_by_offset.get(row["memory_address_hex"].upper()) != row["value"]]
    check("battle_start_residue", start.get("valid") is True and len(start["patches"]) == 2 and not new_memory_errors, errors=new_memory_errors)
    supplemental = staging["supplemental_runtime_patch"]["memory_patches"]
    supplemental_binding_errors = [
        row.get("memory_address_hex")
        for row in supplemental
        if memory_by_offset.get(str(row.get("memory_address_hex", "")).upper()) != str(row.get("value", "")).upper()
    ]
    check("all_manifest_memory_rules_bound", len(supplemental) == 943 and not supplemental_binding_errors, errors=supplemental_binding_errors)
    main_rows = [
        json.loads(line)
        for line in MAIN_DOL_TRANSLATIONS.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    known_sources = {row.get("source_text"): row.get("translation_ko") for row in main_rows}
    expected_runtime = {
        "ないよ〜〜ん": "없지롱~~",
        "タウン一覧を表示します": "마을 목록을 표시합니다",
        "ダンジョン一覧を表示します": "던전 목록을 표시합니다",
        "月影の宿一覧を表示します": "달그림자 여관 목록 표시",
    }
    check("previous_user_reported_runtime_strings", all(known_sources.get(source) == target for source, target in expected_runtime.items()), actual={source: known_sources.get(source) for source in expected_runtime})

    check("standard_enemy_and_skill_layer", enemy.get("valid") is True and enemy["counts"]["total_units"] == 1032 and enemy["counts"]["skill_names"] == 672 and enemy["counts"]["changed_outside_allowed_bytes"] == 0)
    check("system_database_residue", system.get("valid") is True and system["coverage"]["semantic_japanese_unmatched_after"] == 0 and system["counts"]["changed_outside_allowed_bytes"] == 0)
    check("fixed_table_geometry", geometry.get("valid") is True and geometry.get("summary", {}).get("protected_bytes_changed", 0) == 0)
    check("translation_memory", tm.get("translator_model", "Codex internal") in ("Codex internal", None) and tm["unit_count"] == 29777 and tm["translated_unit_count"] == 29777 and all(unit.get("translator") == "Codex internal model" for unit in tm["units"]))

    failed = [row for row in checks if not row["passed"]]
    report = {
        "schema": "arf-untranslated-surface-closure-v104",
        "game_id": "RPJJ99",
        "translator_model": "Codex internal",
        "external_translation_models_or_apis_used": False,
        "scope": {
            "standard_enemy_skill_occurrences": 672,
            "special_boss_skill_occurrences": 80,
            "special_boss_unique_skill_names": 79,
            "map_description_files": 36,
            "map_description_members": 72,
            "battle_raster_entries": 12,
            "battle_raster_text_items": 19,
            "staged_physical_files": 721,
            "memory_rules": 943,
        },
        "result": {
            "confirmed_user_visible_semantic_japanese_remaining": 0 if not failed else None,
            "intentionally_retained_original_japanese": [
                {"surface": "opening title logo baked into Movie/RAY_OP_02.sfd", "reason": "the translated re-encode froze; source movie is retained for runtime stability"}
            ],
            "not_counted_as_missing_translation": ["Japanese voice audio", "intentional decorative English interface art"],
        },
        "checks": checks,
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "errors": [row["name"] for row in failed],
        "error_count": len(failed),
        "valid": not failed,
        "artifacts": [artifact(path) for path in required],
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": report["valid"], "passed": report["passed_count"], "failed": report["failed_count"], "output": str(OUTPUT), "output_sha256": sha(OUTPUT)}, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
