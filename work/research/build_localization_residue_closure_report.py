#!/usr/bin/env python3
"""Consolidate independent battle and system Japanese-residue closure evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
OUT = W / "validation/localization_residue_closure.json"
SEMANTIC_JAPANESE_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff]")
CONTROL_RE = re.compile(r"<\$[0-9A-Fa-f]+>|<#[0-9A-Fa-f]+>")

NEW_SKILL_SOURCES = {
    "クロスカッター", "グラム", "ビフレスト", "フロッティ", "ペネトレイトフィスト",
    "ラグナロク", "乱射", "嫉妬の吐息", "強欲の腕", "憤怒の腕", "暴食の吐息",
    "瘴気", "砲撃", "神斬", "神雷", "鎮められし怨嗟", "雷撃",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def h(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def semantic_japanese(text: str) -> bool:
    return bool(SEMANTIC_JAPANESE_RE.search(CONTROL_RE.sub("", text)))


def parse_rtdp(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"RTDP":
        raise ValueError(f"not RTDP: {path}")
    eoh, count = struct.unpack_from(">II", data, 4)
    leaves = {}
    for index in range(count):
        pos = 0x20 + index * 40
        name = data[pos:pos + 32].split(b"\0", 1)[0].decode("ascii")
        size, relative = struct.unpack_from(">II", data, pos + 32)
        stored = data[eoh + relative:eoh + relative + size]
        leaves[name] = bytes(value ^ 0x55 for value in stored)
    return leaves


def main() -> int:
    battle_audit_path = W / "validation/battle_text_independent_coverage_audit.json"
    battle_app_path = W / "battle_enemy_application/application_report.json"
    battle_catalog_path = W / "translation/battle_enemy/battle_enemy_catalog.json"
    battle_map_path = W / "translation/battle_enemy/battle_enemy_skill_translations.json"
    system_path = W / "system_text_residue_application/application_report.json"
    system_core_path = W / "final_system_table_application/application_proof.json"
    tutorial_catalog_path = W / "research/table_agent/catalogs/btl_tutorial.json"
    tutorial_source_path = W / "disc_extracted/DATA/files/Btl/btl_tutorial.vld"
    tutorial_final_path = W / "final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Btl/btl_tutorial.vld"
    staged_system_path = W / "final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Sys/system.vol"
    staging_path = W / "final_runtime_staging/staging_manifest.json"
    scan_module_path = W / "research/audit_battle_text_coverage.py"
    required = [
        battle_audit_path, battle_app_path, battle_catalog_path, battle_map_path,
        system_path, system_core_path, tutorial_catalog_path, tutorial_source_path,
        tutorial_final_path, staged_system_path, staging_path, scan_module_path,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(json.dumps({"missing": missing}, ensure_ascii=False))

    checks = []
    errors = []

    def check(name: str, passed: bool, **details) -> None:
        row = {"name": name, "passed": bool(passed), **details}
        checks.append(row)
        if not passed:
            errors.append(row)

    battle = load(battle_audit_path)
    battle_app = load(battle_app_path)
    battle_catalog = load(battle_catalog_path)
    battle_map = load(battle_map_path)
    bc = battle["counts"]
    expected_battle_counts = {
        "entries": 270, "display_names": 270, "alternate_display_names": 87,
        "part_names": 3, "skill_names": 672, "total_units": 1032,
        "entries_fitting_source_slots": 270, "changed_outside_allowed_bytes": 0,
    }
    check("battle_application_counts", battle_app.get("valid") is True and battle_app.get("counts") == expected_battle_counts,
          actual=battle_app.get("counts"))
    check("battle_independent_generic_coverage",
          bc.get("uncovered_before_first_rtdp") == 0 and bc.get("unchanged_before_first_rtdp") == 0,
          uncovered=bc.get("uncovered_before_first_rtdp"), unchanged=bc.get("unchanged_before_first_rtdp"))
    check("battle_catalog_complete", battle_catalog.get("unit_count") == 1032
          and battle_catalog.get("alternate_display_name_count") == 87
          and battle_catalog.get("skill_name_count") == 672)
    marker = "<" + "$" + "15>"
    mapped_sources = {str(row["source_text"]).replace(marker, "\x15") for row in battle_map["translations"]}
    required_sources = {
        str(unit["source_text"])
        for unit in battle_catalog["units"]
        if unit["field"] in {"skill_name", "part_name"}
    }
    check("battle_skill_map_complete", len(battle_map["translations"]) == 229
          and required_sources == mapped_sources,
          required_unique=len(required_sources), mapped_unique=len(mapped_sources),
          missing=sorted(required_sources - mapped_sources))
    new_rows = [row for row in battle_map["translations"] if row["source_text"] in NEW_SKILL_SOURCES]
    check("new_nonstandard_action_skill_sources_closed", len(new_rows) == 17,
          translations=new_rows)

    system = load(system_path)
    core = load(system_core_path)
    check("core_system_application_valid", core.get("valid") is True
          and core.get("verification_error_count") == 0
          and core.get("fixed_payload_changes_outside_declared_slots") == 0)
    check("system_residue_application_valid", system.get("valid") is True
          and system.get("error_count") == 0
          and system.get("counts", {}).get("translated_fields") == 30
          and system.get("counts", {}).get("changed_outside_allowed_bytes") == 0)
    check("system_semantic_residue_closed",
          system.get("coverage", {}).get("catalogs_audited") == 13
          and system.get("coverage", {}).get("catalog_units_audited") == 6103
          and system.get("coverage", {}).get("semantic_japanese_unmatched_before") == 30
          and system.get("coverage", {}).get("semantic_japanese_unmatched_after") == 0)
    staged_leaves = parse_rtdp(staged_system_path)
    leaf_errors = []
    for payload in system["payloads"]:
        name = Path(payload["output"]).name
        expected = Path(payload["output"]).read_bytes()
        if staged_leaves.get(name) != expected:
            leaf_errors.append(name)
    check("system_residue_payloads_bound_to_staged_system", not leaf_errors, mismatches=leaf_errors)

    tutorial_catalog = load(tutorial_catalog_path)
    tutorial_source = tutorial_source_path.read_bytes()
    tutorial_final = tutorial_final_path.read_bytes()
    scanner = load_module("arf_battle_coverage_scanner", scan_module_path)
    runs = scanner.scan_euc_jp_runs(tutorial_source)
    uncovered = []
    for run in runs:
        owners = [
            unit for unit in tutorial_catalog["units"]
            if int(unit["offset"]) <= int(run["offset"])
            and int(run["end"]) <= int(unit["offset"]) + int(unit["capacity"])
        ]
        if not owners:
            uncovered.append(run)
    semantic_units = [unit for unit in tutorial_catalog["units"] if semantic_japanese(str(unit["source_text"]))]
    punctuation_units = [
        unit for unit in tutorial_catalog["units"]
        if unit.get("has_japanese") and not semantic_japanese(str(unit["source_text"]))
    ]
    source_mismatches = []
    unchanged_semantic = []
    for unit in tutorial_catalog["units"]:
        raw = bytes.fromhex(str(unit["raw_hex"]))
        offset = int(unit["offset"])
        if tutorial_source[offset:offset + len(raw)] != raw:
            source_mismatches.append(unit["id"])
        if unit in semantic_units and tutorial_final[offset:offset + len(raw)] == raw:
            unchanged_semantic.append(unit["id"])
    check("battle_tutorial_source_catalog_exact", not source_mismatches, mismatches=source_mismatches)
    check("battle_tutorial_independent_coverage", len(runs) == 376 and not uncovered
          and len(semantic_units) == 376 and not unchanged_semantic,
          independent_runs=len(runs), semantic_units=len(semantic_units),
          uncovered=len(uncovered), unchanged_semantic=unchanged_semantic,
          punctuation_only_preserved=[unit["id"] for unit in punctuation_units])

    staging = load(staging_path)
    staged_row = next(row for row in staging["static_validation"]["staged_files"] if row["physical_path"] == "Sys/system.vol")
    check("staged_system_manifest_binding", staged_row["output_sha256"] == h(staged_system_path)
          and staging.get("system_text_residue_application", {}).get("report_sha256") == h(system_path)
          and staging.get("counts", {}).get("system_text_residue_translation_occurrences") == 30)

    report = {
        "schema": "arf-localization-residue-closure-v1", "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal model only",
        "external_translation_models_or_apis_used": False,
        "scope": {
            "battle_enemy_entries": "270 decompressed BTEM payloads before their first nested RTDP asset region",
            "battle_tutorial": "all structured tutorial message/speaker fields plus an independent EUC-JP source scan",
            "system_tables": "13 system display catalogs and the final staged system.vol leaves",
            "excluded_as_non_text": "33,746 Japanese-looking EUC byte runs after BTEM nested RTDP boundaries; these are textures/models/binary assets, not string fields",
        },
        "summary": {
            "battle_enemy_text_occurrences": 1032,
            "battle_enemy_unique_skill_and_part_sources": 229,
            "newly_closed_nonstandard_skill_sources": 17,
            "newly_closed_nonstandard_skill_occurrences": 33,
            "newly_closed_alternate_monster_name_occurrences": 87,
            "battle_tutorial_semantic_japanese_occurrences": 376,
            "system_catalog_units_audited": 6103,
            "newly_closed_system_semantic_japanese_occurrences": 30,
            "newly_closed_ability_names": 14,
            "semantic_japanese_unmatched_after": 0,
            "changed_outside_declared_text_slots": 0,
        },
        "informational": {
            "battle_generic_scanner_catalog_units_below_detection_threshold": bc.get("catalog_offset_mismatches"),
            "reason": "single-character/control-prefixed catalog strings are intentionally below the independent scanner's minimum two-Japanese-character heuristic; application source hashes and catalog counts still verify them",
            "system_typography_only_original_byte_fields": system.get("coverage", {}).get("typography_only_source_bytes_intentionally_preserved"),
            "tutorial_punctuation_only_original_fields": len(punctuation_units),
        },
        "new_skill_translations": new_rows,
        "system_residue_translations": system["translations"],
        "checks": checks,
        "passed_count": sum(row["passed"] for row in checks),
        "failed_count": sum(not row["passed"] for row in checks),
        "errors": errors, "error_count": len(errors), "valid": not errors,
        "artifacts": [
            {"path": str(path), "size_bytes": path.stat().st_size, "sha256": h(path)}
            for path in required
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "summary": report["summary"], "passed_count": report["passed_count"], "failed_count": report["failed_count"], "valid": report["valid"]}, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
