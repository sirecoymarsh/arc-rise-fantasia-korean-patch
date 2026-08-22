#!/usr/bin/env python3
"""Independently validate the packaged Korean town-map legend delta."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
SOURCE = W / "disc_extracted" / "DATA" / "sys" / "main.dol"
CODEBOOK = W / "font" / "final_v3" / "codebook.json"
ENCODER = W / "research" / "encode_custom_euc28.py"
TRANSLATIONS = W / "translation" / "town_map_legend" / "main_dol_town_map_legend.jsonl"
PATCH_REPORT = W / "runtime_fix" / "town_map_legend_patch_report.json"
INTEGRATION_REPORT = W / "runtime_fix" / "town_map_legend_integration_report.json"
STAGING_MANIFEST = W / "final_runtime_staging" / "staging_manifest.json"
STAGING_XML = W / "final_runtime_staging" / "riivolution_sd" / "riivolution" / "arc_rise_fantasia_ko_full.xml"
PACKAGE = ROOT / "outputs" / "Arc_Rise_Fantasia_Korean_Patch_v1.0.3"
PACKAGE_XML = PACKAGE / "payload" / "riivolution_sd" / "riivolution" / "arc_rise_fantasia_ko_full.xml"
PACKAGE_PROVENANCE = PACKAGE / "PROVENANCE.json"
PACKAGE_MANIFEST = PACKAGE / "MANIFEST.json"
OUTPUT = W / "validation" / "town_map_legend_release_validation.json"
SOURCE_SHA256 = "4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC"


def h(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def need(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sections(data: bytes) -> list[tuple[str, int, int, int]]:
    be32 = lambda offset: struct.unpack_from(">I", data, offset)[0]
    rows = []
    for index in range(7):
        rows.append((f"text{index}", be32(4 * index), be32(0x48 + 4 * index), be32(0x90 + 4 * index)))
    for index in range(11):
        rows.append((f"data{index}", be32(0x1C + 4 * index), be32(0x64 + 4 * index), be32(0xAC + 4 * index)))
    return [row for row in rows if row[3] > 0]


def address_for(offset: int, length: int, rows: list[tuple[str, int, int, int]]) -> tuple[str, int]:
    found = [(name, memory + offset - start) for name, start, memory, size in rows if start <= offset and offset + length <= start + size]
    need(len(found) == 1, f"bad DOL section mapping at 0x{offset:X}")
    return found[0]


def main() -> int:
    required = [
        SOURCE, CODEBOOK, ENCODER, TRANSLATIONS, PATCH_REPORT, INTEGRATION_REPORT,
        STAGING_MANIFEST, STAGING_XML, PACKAGE_XML, PACKAGE_PROVENANCE, PACKAGE_MANIFEST,
    ]
    for path in required:
        need(path.is_file(), f"missing validation input: {path}")
    source = SOURCE.read_bytes()
    need(h(SOURCE) == SOURCE_SHA256, "source DOL hash mismatch")
    codebook = json.loads(CODEBOOK.read_text(encoding="utf-8-sig"))
    encoder = load_module("arf_town_map_release_encoder", ENCODER)
    translations = [json.loads(line) for line in TRANSLATIONS.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    need(len(translations) == 15, "town-map translation count mismatch")
    need(len({row["offset"] for row in translations}) == 15, "duplicate town-map file offset")
    need(all(row.get("translator_model") == "Codex internal" for row in translations), "translator provenance mismatch")
    need(all(row.get("external_translation_used") is False for row in translations), "external translation flag mismatch")

    xml_root = ET.parse(STAGING_XML).getroot()
    memory_nodes = list(xml_root.findall(".//memory"))
    file_nodes = list(xml_root.findall(".//file"))
    need(len(memory_nodes) == 940 and len(file_nodes) == 684, "staging XML count mismatch")
    memory = {}
    for node in memory_nodes:
        key = str(node.attrib["offset"]).upper()
        need(key not in memory, f"duplicate XML memory address: {key}")
        memory[key] = str(node.attrib["value"]).upper()

    mapped = sections(source)
    checks: list[dict[str, Any]] = []
    for row in translations:
        offset = int(row["offset"])
        raw = bytes.fromhex(str(row["source_raw_hex"]))
        need(source[offset : offset + len(raw)] == raw, f"source bytes mismatch at 0x{offset:X}")
        need(source[offset + len(raw)] == 0, f"source NUL mismatch at 0x{offset:X}")
        need(str(row["source_text"])[:2] == str(row["translation_ko"])[:2], f"icon prefix mismatch at 0x{offset:X}")
        encoded = encoder.encode_text(str(row["translation_ko"]), codebook)
        need(len(encoded) <= len(raw), f"encoded target overflow at 0x{offset:X}")
        section, address = address_for(offset, len(raw), mapped)
        key = f"0x{address:08X}".upper()
        expected = (encoded + b"\0" * (len(raw) - len(encoded))).hex().upper()
        need(memory.get(key) == expected, f"packaged memory value mismatch at {key}")
        checks.append({
            "offset": offset,
            "offset_hex": f"0x{offset:08X}",
            "memory_address_hex": key,
            "section": section,
            "source_text": row["source_text"],
            "translation_ko": row["translation_ko"],
            "slot_bytes": len(raw),
            "encoded_bytes": len(encoded),
            "prefix_preserved": True,
            "nul_preserved_outside_write": True,
            "memory_value_matches": True,
        })

    staging = json.loads(STAGING_MANIFEST.read_text(encoding="utf-8-sig"))
    town = staging.get("town_map_legend_patch", {})
    need(staging["counts"]["town_map_legend_translations"] == 15, "staging legend count mismatch")
    need(staging["riivolution"]["memory_count"] == 940, "staging memory count mismatch")
    need(staging["riivolution"]["sha256"] == h(STAGING_XML), "staging XML hash mismatch")
    need(town.get("valid") is True and town.get("translated_labels") == 15, "staging town-map proof invalid")
    need(town.get("base_memory_rules") == 925 and town.get("final_memory_rules") == 940, "staging memory proof mismatch")
    need(town.get("icon_identifier_prefixes_preserved") is True, "staging prefix proof missing")
    need(town.get("terminating_nuls_preserved") is True, "staging NUL proof missing")
    need(h(PACKAGE_XML) == h(STAGING_XML), "release/staging XML mismatch")
    provenance = json.loads(PACKAGE_PROVENANCE.read_text(encoding="utf-8-sig"))
    public_town = provenance.get("town_map_legend", {})
    need(public_town.get("translated_labels") == 15, "public legend count mismatch")
    need(public_town.get("base_memory_rules") == 925 and public_town.get("final_memory_rules") == 940, "public memory proof mismatch")
    need(public_town.get("translator_model") == "Codex internal", "public translator provenance mismatch")
    need(public_town.get("external_translation_models_or_apis_used") is False, "public external model flag mismatch")
    release_manifest = json.loads(PACKAGE_MANIFEST.read_text(encoding="utf-8-sig"))
    need(release_manifest.get("package") == "Arc_Rise_Fantasia_Korean_Patch_v1.0.3", "release package name mismatch")
    need(release_manifest.get("staging_manifest_sha256") == h(STAGING_MANIFEST), "release staging-manifest binding mismatch")

    result = {
        "schema": "arf-town-map-legend-release-validation-v1",
        "game_id": "RPJJ99",
        "translator_model": "Codex internal",
        "external_translation_models_or_apis_used": False,
        "inputs": {
            "source_main_dol_sha256": h(SOURCE),
            "codebook_sha256": h(CODEBOOK),
            "translations_sha256": h(TRANSLATIONS),
            "patch_report_sha256": h(PATCH_REPORT),
            "integration_report_sha256": h(INTEGRATION_REPORT),
            "staging_manifest_sha256": h(STAGING_MANIFEST),
            "staging_xml_sha256": h(STAGING_XML),
            "package_manifest_sha256": h(PACKAGE_MANIFEST),
            "package_xml_sha256": h(PACKAGE_XML),
        },
        "counts": {
            "translated_labels": len(translations),
            "source_slots_verified": len(checks),
            "xml_file_rules": len(file_nodes),
            "xml_memory_rules": len(memory_nodes),
        },
        "checks": checks,
        "summary": {
            "all_source_bytes_verified": True,
            "all_targets_fit": True,
            "all_icon_prefixes_preserved": True,
            "all_terminating_nuls_preserved": True,
            "all_packaged_memory_values_match": True,
            "release_staging_binding_matches": True,
        },
        "error_count": 0,
        "errors": [],
        "valid": True,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": True, "translated_labels": 15, "memory_rules": 940, "report": str(OUTPUT), "report_sha256": h(OUTPUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

