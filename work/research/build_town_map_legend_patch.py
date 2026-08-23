#!/usr/bin/env python3
"""Build and optionally integrate Korean town-map legend strings.

The two leading ASCII characters in each source string are icon identifiers
used by the game. They are preserved verbatim while only the visible label is
localized.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work"
SOURCE_DOL = WORK / "disc_extracted" / "DATA" / "sys" / "main.dol"
CODEBOOK = WORK / "font" / "final_v3" / "codebook.json"
ENCODER = WORK / "research" / "encode_custom_euc28.py"
PATCHER = WORK / "research" / "patch_main_dol_strings.py"
TRANSLATIONS = WORK / "translation" / "town_map_legend" / "main_dol_town_map_legend.jsonl"
PATCHED_DOL = WORK / "runtime_fix" / "main.dol.town_map_legend_candidate"
PATCH_REPORT = WORK / "runtime_fix" / "town_map_legend_patch_report.json"
STAGING = WORK / "final_runtime_staging"
STAGING_MANIFEST = STAGING / "staging_manifest.json"
XML = STAGING / "riivolution_sd" / "riivolution" / "arc_rise_fantasia_ko_full.xml"
INTEGRATION_REPORT = WORK / "runtime_fix" / "town_map_legend_integration_report.json"

GAME_ID = "RPJJ99"
SOURCE_SHA256 = "4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC"
BASE_MEMORY_RULES = 926
LEGEND_ROWS = [
    (0x003CF564, "50セーブポイント", "50세이브 포인트"),
    (0x003CF576, "51宝箱", "51보물"),
    (0x003CF57E, "52次のマップ", "52다음 지도"),
    (0x003CF58C, "53ワールドマップ", "53세계 지도"),
    (0x003CF59E, "54はしご", "54사다리"),
    (0x003CF5A8, "55宿屋", "55여관"),
    (0x003CF5B0, "56道具屋", "56도구점"),
    (0x003CF5BA, "57武具屋", "57무구점"),
    (0x003CF5C4, "58工房", "58공방"),
    (0x003CF5CC, "59仕立屋", "59양장점"),
    (0x003CF5D6, "5aギルド", "5a길드"),
    (0x003CF5E0, "5bカジノ", "5b카지노"),
    (0x003CF5EA, "5c闘技場", "5c투기장"),
    (0x003CF5F4, "5dハーモニーホール", "5d하모니 홀"),
    (0x003CF608, "5e現在位置", "5e현재위치"),
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


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    matches: list[tuple[str, int]] = []
    for section in sections:
        start = int(section["file_offset"])
        end = start + int(section["size"])
        if start <= offset and offset + length <= end:
            matches.append((str(section["name"]), int(section["memory_address"]) + offset - start))
    need(len(matches) == 1, f"DOL span 0x{offset:X}+0x{length:X} maps to {len(matches)} sections")
    return matches[0]


def build_candidate() -> dict[str, Any]:
    need(SOURCE_DOL.is_file(), f"missing source DOL: {SOURCE_DOL}")
    need(CODEBOOK.is_file(), f"missing codebook: {CODEBOOK}")
    source = SOURCE_DOL.read_bytes()
    need(sha256_bytes(source) == SOURCE_SHA256, "source main.dol SHA-256 mismatch")
    codebook = json.loads(CODEBOOK.read_text(encoding="utf-8-sig"))
    encoder = load_module("arf_town_map_encoder", ENCODER)

    manifest_rows: list[dict[str, Any]] = []
    for offset, source_text, target_text in LEGEND_ROWS:
        source_raw = source_text.encode("euc_jp")
        need(source[offset : offset + len(source_raw)] == source_raw, f"source bytes mismatch at 0x{offset:X}")
        need(source[offset + len(source_raw)] == 0, f"terminating NUL missing at 0x{offset:X}")
        encoded = encoder.encode_text(target_text, codebook)
        need(len(encoded) <= len(source_raw), f"target overflow at 0x{offset:X}: {target_text!r}")
        need(target_text[:2] == source_text[:2], f"icon identifier changed at 0x{offset:X}")
        manifest_rows.append({
            "schema": "arf-main-dol-translation-v1",
            "file": "DATA/sys/main.dol",
            "file_sha256": SOURCE_SHA256,
            "offset": offset,
            "offset_hex": f"0x{offset:08X}",
            "byte_length": len(source_raw),
            "capacity_to_nul": len(source_raw),
            "source_encoding": "EUC-JP",
            "source_text": source_text,
            "source_raw_hex": source_raw.hex().upper(),
            "translation_ko": target_text,
            "estimated_target_bytes": len(encoded),
            "context": "마을·필드 지도 아이콘 범례(앞 2바이트 아이콘 식별자 보존)",
            "lane": "town_map_legend",
            "visibility": "runtime_user_visible",
            "provenance": "Codex internal model",
            "translator_model": "Codex internal",
            "external_translation_used": False,
        })

    TRANSLATIONS.parent.mkdir(parents=True, exist_ok=True)
    TRANSLATIONS.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in manifest_rows),
        encoding="utf-8",
    )

    patcher = load_module("arf_town_map_patcher", PATCHER)
    report = patcher.patch_file(
        SOURCE_DOL,
        TRANSLATIONS,
        CODEBOOK,
        PATCHED_DOL,
        PATCH_REPORT,
        SOURCE_SHA256,
        ENCODER,
    )
    need(report.get("valid") is True, "town-map DOL patch report is invalid")
    need(int(report["summary"]["patch_rows"]) == len(LEGEND_ROWS), "unexpected patch-row count")
    need(report["summary"]["changes_confined_to_allowlisted_spans"] is True, "DOL diff escaped allowlist")
    return report


def integrate(report: dict[str, Any]) -> dict[str, Any]:
    need(STAGING_MANIFEST.is_file() and XML.is_file(), "final staging inputs are missing")
    manifest = json.loads(STAGING_MANIFEST.read_text(encoding="utf-8-sig"))
    need(manifest.get("schema") == "arf-full-runtime-staging-v2", "unexpected staging schema")
    need(manifest.get("game_id") == GAME_ID, "staging game ID mismatch")
    need(manifest.get("static_validation", {}).get("valid") is True, "staging static validation is not green")
    need(sha256_file(XML) == str(manifest["riivolution"]["sha256"]).upper(), "staging XML hash mismatch")

    source = SOURCE_DOL.read_bytes()
    sections = dol_sections(source)
    new_rows: list[dict[str, Any]] = []
    for patch in report["patches"]:
        file_offset = int(patch["offset"])
        byte_length = int(patch["byte_length"])
        section_name, address = file_span_to_memory(file_offset, byte_length, sections)
        value = str(patch["encoded_hex"]).upper() + ("00" * int(patch["zero_padding_bytes"]))
        need(len(value) == byte_length * 2, f"memory value length mismatch at 0x{file_offset:X}")
        new_rows.append({
            "file_offset": file_offset,
            "memory_address": address,
            "memory_address_hex": f"0x{address:08X}",
            "section": section_name,
            "byte_length": byte_length,
            "value": value,
            "value_sha256": sha256_bytes(bytes.fromhex(value)),
            "stable_id": f"ARF-MAP-LEGEND-{str(patch['source_text'])[:2].upper()}",
            "source_text": patch["source_text"],
            "translation_ko": patch["translation_ko"],
        })
    new_rows.sort(key=lambda row: int(row["memory_address"]))
    new_addresses = {str(row["memory_address_hex"]).upper() for row in new_rows}
    need(len(new_addresses) == len(LEGEND_ROWS), "duplicate town-map memory address")

    tree = ET.parse(XML)
    patch_nodes = [
        node for node in tree.getroot().findall(".//patch")
        if node.findall("file") or node.findall("memory")
    ]
    if not patch_nodes and tree.getroot().tag == "patch":
        patch_nodes = [tree.getroot()]
    need(len(patch_nodes) == 1, f"expected one populated Riivolution patch node, got {len(patch_nodes)}")
    patch_node = patch_nodes[0]
    memory_nodes = list(patch_node.findall("memory"))
    for node in list(memory_nodes):
        if str(node.attrib.get("offset", "")).upper() in new_addresses:
            patch_node.remove(node)
    base_nodes = list(patch_node.findall("memory"))
    need(len(base_nodes) == BASE_MEMORY_RULES, f"unexpected base memory-rule count: {len(base_nodes)}")
    base_addresses = {str(node.attrib.get("offset", "")).upper() for node in base_nodes}
    need(not (base_addresses & new_addresses), "town-map memory address overlaps existing patch")

    combined = [
        {"offset": str(node.attrib["offset"]).upper(), "value": str(node.attrib["value"]).upper()}
        for node in base_nodes
    ] + [
        {"offset": str(row["memory_address_hex"]).upper(), "value": str(row["value"]).upper()}
        for row in new_rows
    ]
    for node in list(patch_node.findall("memory")):
        patch_node.remove(node)
    for row in sorted(combined, key=lambda item: int(item["offset"], 16)):
        ET.SubElement(patch_node, "memory", {"offset": row["offset"], "value": row["value"]})
    ET.indent(tree, space="  ")
    tree.write(XML, encoding="utf-8", xml_declaration=True)

    reparsed = ET.parse(XML)
    file_count = len(reparsed.getroot().findall(".//file"))
    memory_count = len(reparsed.getroot().findall(".//memory"))
    need(file_count == int(manifest["riivolution"]["file_count"]) == 684, "Riivolution file-rule count changed")
    need(memory_count == BASE_MEMORY_RULES + len(LEGEND_ROWS), "Riivolution memory-rule count mismatch")
    physical_root = STAGING / "riivolution_sd" / "arc_rise_fantasia_ko_full" / "files"
    need(sum(path.is_file() for path in physical_root.rglob("*")) == 684, "physical staging file count changed")

    manifest["counts"]["riivolution_memory_rules"] = memory_count
    manifest["counts"]["town_map_legend_translations"] = len(LEGEND_ROWS)
    manifest["riivolution"]["memory_count"] = memory_count
    manifest["riivolution"]["sha256"] = sha256_file(XML)
    supplemental = manifest["supplemental_runtime_patch"]
    supplemental["base_memory_patch_count"] = BASE_MEMORY_RULES
    supplemental["memory_patch_count"] = memory_count
    old_rows = [
        row for row in supplemental.get("memory_patches", [])
        if int(row.get("file_offset", -1)) not in {int(item["file_offset"]) for item in new_rows}
    ]
    need(len(old_rows) == BASE_MEMORY_RULES, "staging manifest base memory rows are incomplete")
    supplemental["memory_patches"] = sorted(old_rows + new_rows, key=lambda row: int(row["memory_address"]))
    supplemental["valid"] = True

    manifest["inputs"]["town_map_legend_translations"] = {
        "path": str(TRANSLATIONS),
        "sha256": sha256_file(TRANSLATIONS),
        "count": len(LEGEND_ROWS),
        "translator_model": "Codex internal",
        "translation_engine_policy": "Codex internal model only",
        "external_translation_models_or_apis_used": False,
    }
    manifest["inputs"]["town_map_legend_patch_report"] = {
        "path": str(PATCH_REPORT),
        "sha256": sha256_file(PATCH_REPORT),
    }
    manifest["town_map_legend_patch"] = {
        "source_main_dol_sha256": SOURCE_SHA256,
        "translation_manifest_sha256": sha256_file(TRANSLATIONS),
        "patch_report_sha256": sha256_file(PATCH_REPORT),
        "codebook_sha256": sha256_file(CODEBOOK),
        "translated_labels": len(LEGEND_ROWS),
        "base_memory_rules": BASE_MEMORY_RULES,
        "final_memory_rules": memory_count,
        "icon_identifier_prefixes_preserved": True,
        "terminating_nuls_preserved": True,
        "changes_confined_to_allowlisted_spans": True,
        "translator_model": "Codex internal",
        "external_translation_models_or_apis_used": False,
        "valid": True,
    }
    manifest["runtime_ready_release"] = True
    manifest["dolphin_screen_test"] = "not_requested_for_town_map_legend_delta"
    write_json(STAGING_MANIFEST, manifest)

    result = {
        "schema": "arf-town-map-legend-integration-v1",
        "game_id": GAME_ID,
        "translation_engine_policy": "Codex internal model only",
        "translator_model": "Codex internal",
        "external_translation_models_or_apis_used": False,
        "source_main_dol": {"path": str(SOURCE_DOL), "sha256": sha256_file(SOURCE_DOL)},
        "translations": {"path": str(TRANSLATIONS), "sha256": sha256_file(TRANSLATIONS), "count": len(LEGEND_ROWS)},
        "patch_report": {"path": str(PATCH_REPORT), "sha256": sha256_file(PATCH_REPORT)},
        "staging_manifest": {"path": str(STAGING_MANIFEST), "sha256": sha256_file(STAGING_MANIFEST)},
        "xml": {
            "path": str(XML),
            "sha256": sha256_file(XML),
            "file_count": file_count,
            "memory_count": memory_count,
        },
        "memory_patches": new_rows,
        "checks": {
            "source_hash_verified": True,
            "source_bytes_verified": True,
            "icon_identifier_prefixes_preserved": True,
            "terminating_nuls_preserved": True,
            "targets_fit_fixed_slots": True,
            "existing_memory_rules_preserved": True,
            "new_memory_addresses_unique": True,
            "physical_staging_unchanged": True,
        },
        "error_count": 0,
        "errors": [],
        "valid": True,
    }
    write_json(INTEGRATION_REPORT, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--integrate", action="store_true", help="append the validated writes to final staging")
    args = parser.parse_args()
    report = build_candidate()
    summary: dict[str, Any] = {
        "candidate_valid": True,
        "translated_labels": len(LEGEND_ROWS),
        "translations_sha256": sha256_file(TRANSLATIONS),
        "patch_report_sha256": sha256_file(PATCH_REPORT),
        "candidate_dol_sha256": sha256_file(PATCHED_DOL),
    }
    if args.integrate:
        result = integrate(report)
        summary.update({
            "integrated": True,
            "final_memory_rules": result["xml"]["memory_count"],
            "xml_sha256": result["xml"]["sha256"],
            "staging_manifest_sha256": result["staging_manifest"]["sha256"],
        })
    else:
        summary["integrated"] = False
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


