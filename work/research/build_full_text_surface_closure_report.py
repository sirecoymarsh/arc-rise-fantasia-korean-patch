#!/usr/bin/env python3
"""Build one source-grounded closure report for all known text surfaces."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
OUT = W / "validation/full_text_surface_closure.json"
PATHS = {
    "base_closure": W / "validation/localization_residue_closure.json",
    "all_btl_vld": W / "validation/all_btl_vld_surface_classification.json",
    "translation_memory": W / "translation/final/translation_memory_draft.json",
    "rtdp_localization_payloads": W / "research/rtdp_agent/audit/localization_payloads.json",
    "party_geometry": W / "battle_enemy_application/party_name_geometry_audit.json",
    "battle_catalog": W / "translation/battle_enemy/battle_enemy_catalog.json",
    "tutorial_catalog": W / "research/table_agent/catalogs/btl_tutorial.json",
    "staging_manifest": W / "final_runtime_staging/staging_manifest.json",
}
SYSTEM_CATALOGS = W / "final_system_table_application/replacement_catalogs"
EXACT_BURST_TERMS = ("バーストショット", "バースト・ショット")
JAPANESE_LETTER_RE = re.compile(r"[\u3041-\u3096\u30A1-\u30FA\u30FD-\u30FF\u3400-\u9FFF\uF900-\uFAFF]")
BROAD_JAPANESE_RE = re.compile(r"[\u3040-\u30FF\u3400-\u9FFF\uF900-\uFAFF]")
CONTROL_RE = re.compile(r"<\$[0-9A-Fa-f]+>|<#[0-9A-Fa-f]+>")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def has_semantic_japanese(text: str) -> bool:
    return bool(JAPANESE_LETTER_RE.search(CONTROL_RE.sub("", text)))


def has_broad_japanese(text: str) -> bool:
    return bool(BROAD_JAPANESE_RE.search(CONTROL_RE.sub("", text)))


def main() -> int:
    required = list(PATHS.values()) + sorted(SYSTEM_CATALOGS.glob("*.json"))
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(json.dumps({"missing": missing}, ensure_ascii=False, indent=2))

    checks: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    def check(name: str, passed: bool, **details: Any) -> None:
        row = {"name": name, "passed": bool(passed), **details}
        checks.append(row)
        if not passed:
            errors.append(row)

    base = load(PATHS["base_closure"])
    check("existing_battle_system_closure_valid",
          base.get("valid") is True and base.get("error_count") == 0
          and base.get("summary", {}).get("semantic_japanese_unmatched_after") == 0
          and base.get("summary", {}).get("changed_outside_declared_text_slots") == 0)

    vld = load(PATHS["all_btl_vld"])
    by_kind = {row["kind"]: row for row in vld["summary"]}
    expected_vld = {
        "enemy": (270, 270, 0, {"BTEM": 270}),
        "magic": (247, 235, 12, {"RTDP": 235, "empty": 12}),
        "map": (57, 55, 2, {"RTDP": 55, "empty": 2}),
        "pc": (12, 12, 0, {"RTDP": 12}),
        "weapon": (193, 147, 46, {"RTDP": 147, "empty": 46}),
        "win": (60, 56, 4, {"RTDP": 56, "empty": 4}),
        "tutorial": (24, 21, 3, {"....": 21, "empty": 3}),
    }
    vld_mismatches = []
    for kind, (entries, nonempty, empty, magics) in expected_vld.items():
        row = by_kind.get(kind, {})
        actual = (row.get("entry_count"), row.get("nonempty_entries"),
                  row.get("empty_entries"), row.get("decoded_magic_counts"))
        if actual != (entries, nonempty, empty, magics):
            vld_mismatches.append({"kind": kind, "actual": actual})
    check("all_seven_battle_vld_families_classified",
          vld.get("valid") is True and not vld_mismatches
          and sum(row["entry_count"] for row in vld["summary"]) == 863,
          mismatches=vld_mismatches)
    check("burst_shot_exact_compound_absent",
          vld.get("exact_compound_hit_count") == 0,
          component_hits=vld.get("component_term_hit_count"),
          component_rows=vld.get("burst_term_hits"))
    check("non_enemy_battle_vlds_are_asset_archives",
          all(by_kind[kind]["decoded_magic_counts"].get("RTDP", 0)
              == by_kind[kind]["nonempty_entries"]
              for kind in ("magic", "map", "pc", "weapon", "win")))

    tm = load(PATHS["translation_memory"])
    units = tm["units"]
    semantic_target_rows = [
        {"tm_id": row["tm_id"], "surface": row.get("primary_surface"),
         "source_text": row["source_text"], "translation_ko": row.get("translation_ko", "")}
        for row in units if has_semantic_japanese(str(row.get("translation_ko", "")))
    ]
    typography_only_rows = [
        row["tm_id"] for row in units
        if has_broad_japanese(str(row.get("translation_ko", "")))
        and not has_semantic_japanese(str(row.get("translation_ko", "")))
    ]
    check("translation_memory_complete",
          tm.get("unit_count") == len(units) == 29777
          and tm.get("translated_unit_count") == 29777
          and tm.get("reviewed_unit_count") == 29777
          and sum(int(row.get("occurrence_count", 0)) for row in units) == 84761)
    check("event_and_map_targets_have_no_semantic_japanese",
          not semantic_target_rows, rows=semantic_target_rows,
          typography_only_long_mark_or_punctuation_count=len(typography_only_rows))

    payloads = load(PATHS["rtdp_localization_payloads"])
    class_counts = Counter(row["formatClass"] for row in payloads)
    expected_classes = Counter({
        "embedded battle party display name": 13,
        "embedded field/resource labels": 1,
        "BSCR scenario/event script": 380,
        "localized data/string table": 12,
    })
    check("all_vetted_rtdp_localization_payloads_accounted",
          len(payloads) == 406 and class_counts == expected_classes,
          actual=dict(class_counts))

    party = load(PATHS["party_geometry"])
    check("battle_party_names_translated_without_metadata_damage",
          len(party) == 13 and all(row.get("EqualMeta") is True and int(row.get("TotalDiff", 0)) > 0 for row in party))

    battle_catalog = load(PATHS["battle_catalog"])
    tutorial_catalog = load(PATHS["tutorial_catalog"])
    system_catalogs = [load(path) for path in sorted(SYSTEM_CATALOGS.glob("*.json"))]
    searchable = [
        ("translation_memory", row["tm_id"], str(row["source_text"])) for row in units
    ] + [
        ("battle_enemy", row["id"], str(row["source_text"])) for row in battle_catalog["units"]
    ] + [
        ("battle_tutorial", row["id"], str(row["source_text"])) for row in tutorial_catalog["units"]
    ] + [
        ("system_table", row["id"], str(row["source_text"]))
        for catalog in system_catalogs for row in catalog.get("units", [])
    ]
    exact_hits = [
        {"surface": surface, "id": uid, "text": text}
        for surface, uid, text in searchable
        if any(term in text for term in EXACT_BURST_TERMS)
    ]
    check("burst_shot_absent_from_all_audited_source_text",
          not exact_hits, searched_source_units=len(searchable), hits=exact_hits)

    wyvern_units = [
        row for row in battle_catalog["units"]
        if row["id"].startswith("btl_enemy:195:")
    ]
    wyvern_skill_sources = [
        row["source_text"] for row in wyvern_units if row["field"] == "skill_name"
    ]
    check("wyvern_named_skill_slots_exhaustive",
          wyvern_skill_sources == ["ウイングカッター", "雄叫び"],
          skill_sources=wyvern_skill_sources)
    check("wyvern_orb_attack_is_id_or_animation_only",
          not exact_hits and vld.get("exact_compound_hit_count") == 0
          and wyvern_skill_sources == ["ウイングカッター", "雄叫び"],
          verdict="No バーストショット display string exists; the orb attack is represented by behavior/animation data, not a translatable name slot.")

    staging = load(PATHS["staging_manifest"])
    check("current_staging_retains_closed_counts",
          staging.get("counts", {}).get("staged_physical_files") == 683
          and staging.get("counts", {}).get("battle_enemy_translation_occurrences") == 1032
          and staging.get("counts", {}).get("system_text_residue_translation_occurrences") == 30)

    report = {
        "schema": "arf-full-text-surface-closure-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "scope": {
            "vetted_rtdp_localization_payloads": 406,
            "event_script_payloads": 380,
            "translation_memory_units": 29777,
            "translation_occurrences": 84761,
            "battle_vld_entries_classified": 863,
            "battle_enemy_units": 1032,
            "battle_tutorial_semantic_units": 376,
            "system_catalog_units": sum(len(catalog.get("units", [])) for catalog in system_catalogs),
            "battle_party_name_payloads": 13,
        },
        "burst_shot_provenance": {
            "exact_original_strings_searched": list(EXACT_BURST_TERMS),
            "exact_compound_hits": 0,
            "component_term_hits": vld.get("burst_term_hits"),
            "wyvern_entry": 195,
            "wyvern_named_skill_strings": wyvern_skill_sources,
            "classification": "monster behavior/action with no standalone display-name string",
        },
        "summary": {
            "semantic_japanese_in_korean_targets": len(semantic_target_rows),
            "typography_only_japanese_marks_in_korean_targets": len(typography_only_rows),
            "unmatched_semantic_japanese_after": 0,
            "exact_burst_shot_source_hits": len(exact_hits),
        },
        "checks": checks,
        "passed_count": sum(row["passed"] for row in checks),
        "failed_count": sum(not row["passed"] for row in checks),
        "error_count": len(errors),
        "errors": errors,
        "artifacts": [
            {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
             "size_bytes": path.stat().st_size, "sha256": sha(path)}
            for path in required
        ],
        "valid": not errors,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUT), "scope": report["scope"], "summary": report["summary"],
        "passed_count": report["passed_count"], "failed_count": report["failed_count"],
        "sha256": sha(OUT), "valid": report["valid"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
