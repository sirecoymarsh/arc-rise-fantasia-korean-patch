#!/usr/bin/env python3
"""Integrate late-discovered user-visible assets into the full overlay.

The base staging builder owns the 655 translated game files.  This script
adds only the separately reviewed runtime surfaces: HOME Button resources,
ending-card WTMs, opening.bnr, the localized opening movie, and fixed-width
main.dol strings expressed as Riivolution memory writes.  main.dol itself is
never copied into the overlay.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import struct
import sys
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


GAME_ID = "RPJJ99"
BASE_PHYSICAL_COUNT = 655
SUPPLEMENTAL_PHYSICAL_COUNT = 28
EXPECTED_MEMORY_PATCHES = 925
MAIN_DOL_SHA256 = "4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC"


class IntegrationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise IntegrationError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def dol_sections(data: bytes) -> list[dict[str, int | str]]:
    require(len(data) >= 0x100, "main.dol is too small")
    be32 = lambda offset: struct.unpack_from(">I", data, offset)[0]
    sections: list[dict[str, int | str]] = []
    for index in range(7):
        sections.append({
            "name": f"text{index}",
            "file_offset": be32(0x00 + 4 * index),
            "memory_address": be32(0x48 + 4 * index),
            "size": be32(0x90 + 4 * index),
        })
    for index in range(11):
        sections.append({
            "name": f"data{index}",
            "file_offset": be32(0x1C + 4 * index),
            "memory_address": be32(0x64 + 4 * index),
            "size": be32(0xAC + 4 * index),
        })
    return [section for section in sections if int(section["size"]) > 0]


def file_span_to_memory(offset: int, length: int, sections: list[dict[str, int | str]]) -> tuple[str, int]:
    matches = []
    for section in sections:
        start = int(section["file_offset"])
        end = start + int(section["size"])
        if start <= offset and offset + length <= end:
            matches.append((str(section["name"]), int(section["memory_address"]) + offset - start))
    require(len(matches) == 1, f"DOL span 0x{offset:X}+0x{length:X} maps to {len(matches)} sections")
    return matches[0]


def supplemental_payloads(runtime_fix: Path) -> list[tuple[str, Path, bool, str]]:
    rows: list[tuple[str, Path, bool, str]] = [
        ("Hbm/home.csv", runtime_fix / "hbm_ko/payloads/Hbm/home.csv", True, "hbm"),
        ("Hbm/home_nosave.csv", runtime_fix / "hbm_ko/payloads/Hbm/home_nosave.csv", True, "hbm"),
        ("Hbm/homeBtn.arc", runtime_fix / "hbm_ko/payloads/Hbm/homeBtn.arc", False, "hbm"),
    ]
    for index in range(23):
        name = f"EV09_18_0200C_{index:02d}.wtm"
        rows.append((f"Event/endroll/{name}", runtime_fix / f"endroll_ui/payloads/Event/endroll/{name}", False, "endroll"))
    rows.extend([
        ("opening.bnr", runtime_fix / "opening_bnr_ko/payloads/opening.bnr", True, "opening_bnr"),
        ("Movie/RAY_OP_02.sfd", runtime_fix / "sfd_ko/payloads/Movie/RAY_OP_02.sfd", False, "opening_movie"),
    ])
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging", type=Path, default=Path("work/final_runtime_staging"))
    parser.add_argument("--source-files", type=Path, default=Path("work/disc_extracted/DATA/files"))
    parser.add_argument("--source-main-dol", type=Path, default=Path("work/disc_extracted/DATA/sys/main.dol"))
    parser.add_argument("--runtime-fix", type=Path, default=Path("work/runtime_fix"))
    parser.add_argument("--translations", type=Path, default=Path("work/runtime_fix/main_dol_translations.jsonl"))
    parser.add_argument("--codebook", type=Path, default=Path("work/font/final_v2/codebook.json"))
    parser.add_argument("--encoder", type=Path, default=Path("work/research/encode_custom_euc28.py"))
    parser.add_argument("--patcher", type=Path, default=Path("work/research/patch_main_dol_strings.py"))
    parser.add_argument("--dol-output", type=Path, default=Path("work/runtime_fix/main.dol.patched_v2"))
    parser.add_argument("--dol-report", type=Path, default=Path("work/runtime_fix/main_dol_patch_report_v2.json"))
    parser.add_argument("--report", type=Path, default=Path("work/runtime_fix/runtime_supplement_integration.json"))
    args = parser.parse_args()

    manifest_path = args.staging / "staging_manifest.json"
    manifest = load_json(manifest_path)
    require(manifest.get("game_id") == GAME_ID, "staging game ID mismatch")
    require(manifest.get("schema") == "arf-full-runtime-staging-v1", "staging is not a clean base build")
    require(manifest.get("static_validation", {}).get("valid") is True, "base staging is not valid")
    require(manifest.get("counts", {}).get("staged_physical_files") == BASE_PHYSICAL_COUNT,
            "base staging physical count mismatch (already integrated or incomplete)")

    xml_rel = Path(str(manifest["riivolution"]["xml"]))
    xml_path = args.staging / xml_rel
    require(xml_path.is_file(), f"missing Riivolution XML: {xml_path}")
    require(sha256_file(xml_path) == str(manifest["riivolution"]["sha256"]).upper(), "base XML hash mismatch")
    patch_root = args.staging / Path(str(manifest["riivolution"]["patch_root"]))
    require(patch_root.is_dir(), f"missing patch root: {patch_root}")

    # Bind all separately reviewed manifests before copying bytes.
    hbm = load_json(args.runtime_fix / "hbm_ko/hbm_korean_payload_manifest.json")
    endroll = load_json(args.runtime_fix / "endroll_ui/manifest.json")
    endroll_verification = load_json(args.runtime_fix / "endroll_ui/verification_summary.json")
    opening = load_json(args.runtime_fix / "opening_bnr_ko/opening_bnr_korean_payload_manifest.json")
    sfd_remux = load_json(args.runtime_fix / "sfd_ko/sfd_video_replacement_report.json")
    sfd_final = load_json(args.runtime_fix / "sfd_ko/sfd_final_validation.json")
    crossreview = load_json(args.runtime_fix / "main_dol_crossreview.json")
    visual_audit = load_json(args.runtime_fix / "visual_sweep/final_visual_surface_audit.json")
    require(hbm.get("static_validation", {}).get("valid") is True, "HBM manifest is not valid")
    require(endroll.get("file_count") == 23, "endroll manifest file count is not 23")
    require(endroll.get("payload_aggregate_sha256") == endroll_verification.get("payload_aggregate_sha256"),
            "endroll manifest/verification payload aggregate mismatch")
    require(endroll_verification.get("valid") is True, "endroll verification is not valid")
    require(opening.get("static_validation", {}).get("valid") is True or opening.get("valid") is True,
            "opening.bnr manifest is not valid")
    require(sfd_remux.get("valid") is True, "SFD remux report is not valid")
    require(sfd_final.get("valid") is True, "SFD final validation is not valid")
    require(crossreview.get("valid") is True, "main.dol cross-review is not valid")
    require(visual_audit.get("valid") is True, "final visual surface audit is not valid")

    payload_rows = supplemental_payloads(args.runtime_fix)
    require(len(payload_rows) == SUPPLEMENTAL_PHYSICAL_COUNT, "internal supplemental payload count mismatch")
    require(len({row[0] for row in payload_rows}) == len(payload_rows), "duplicate supplemental physical paths")

    staged_rows = manifest["static_validation"]["staged_files"]
    require(isinstance(staged_rows, list) and len(staged_rows) == BASE_PHYSICAL_COUNT,
            "base staged-file manifest mismatch")
    existing = {str(row["physical_path"]) for row in staged_rows}
    require(not (existing & {row[0] for row in payload_rows}), "supplemental path overlaps base staging")

    added: list[dict[str, Any]] = []
    for physical_path, payload_path, resize, lane in payload_rows:
        source_path = args.source_files / Path(physical_path)
        target_path = patch_root / Path(physical_path)
        require(source_path.is_file(), f"missing trusted source: {source_path}")
        require(payload_path.is_file(), f"missing supplemental payload: {payload_path}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(payload_path, target_path)
        require(sha256_file(target_path) == sha256_file(payload_path), f"copy hash mismatch: {physical_path}")
        row = {
            "physical_path": physical_path,
            "source_sha256": sha256_file(source_path),
            "output_sha256": sha256_file(target_path),
            "source_size": source_path.stat().st_size,
            "output_size": target_path.stat().st_size,
            "resize": resize,
            "supplemental_lane": lane,
        }
        if not resize:
            require(row["source_size"] == row["output_size"], f"resize=false size mismatch: {physical_path}")
        added.append(row)

    # Build a semantic patched DOL only as validation material, then translate
    # its exact fixed-width writes into load-addressed Riivolution memory rules.
    patcher = load_module("arf_main_dol_patcher", args.patcher)
    dol_report = patcher.patch_file(
        args.source_main_dol, args.translations, args.codebook, args.dol_output,
        args.dol_report, MAIN_DOL_SHA256, args.encoder,
    )
    require(dol_report.get("valid") is True, "main.dol patcher did not return valid")
    patches = dol_report.get("patches", [])
    require(len(patches) == EXPECTED_MEMORY_PATCHES, f"main.dol patch count is {len(patches)}")
    original_dol = args.source_main_dol.read_bytes()
    sections = dol_sections(original_dol)
    memory_rows: list[dict[str, Any]] = []
    seen_addresses: set[int] = set()
    for patch in patches:
        file_offset = int(patch["offset"])
        byte_length = int(patch["byte_length"])
        section_name, address = file_span_to_memory(file_offset, byte_length, sections)
        value = str(patch["encoded_hex"]).upper() + ("00" * int(patch["zero_padding_bytes"]))
        require(len(value) == byte_length * 2, f"memory value size mismatch at 0x{file_offset:X}")
        require(address not in seen_addresses, f"duplicate memory address 0x{address:08X}")
        seen_addresses.add(address)
        memory_rows.append({
            "file_offset": file_offset,
            "memory_address": address,
            "memory_address_hex": f"0x{address:08X}",
            "section": section_name,
            "byte_length": byte_length,
            "value": value,
            "value_sha256": hashlib.sha256(bytes.fromhex(value)).hexdigest().upper(),
        })
    memory_rows.sort(key=lambda row: int(row["memory_address"]))

    tree = ET.parse(xml_path)
    root = tree.getroot()
    patch_nodes = root.findall("patch")
    require(len(patch_nodes) == 1, "expected exactly one Riivolution patch node")
    patch_node = patch_nodes[0]
    require(not patch_node.findall("memory"), "base XML unexpectedly already contains memory rules")
    file_nodes = patch_node.findall("file")
    require(len(file_nodes) == BASE_PHYSICAL_COUNT, "base XML file-rule count mismatch")
    by_disc = {str(node.get("disc")): node for node in file_nodes}
    for row in added:
        disc = "/" + str(row["physical_path"])
        require(disc not in by_disc, f"duplicate XML disc path: {disc}")
        by_disc[disc] = ET.Element("file", {
            "disc": disc,
            "external": str(row["physical_path"]),
            "resize": "true" if row["resize"] else "false",
        })
    for child in list(patch_node):
        patch_node.remove(child)
    for disc in sorted(by_disc, key=lambda value: value.casefold()):
        patch_node.append(by_disc[disc])
    for row in memory_rows:
        patch_node.append(ET.Element("memory", {
            "offset": str(row["memory_address_hex"]),
            "value": str(row["value"]),
        }))
    ET.indent(tree, space="  ")
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    all_staged = sorted(staged_rows + added, key=lambda row: str(row["physical_path"]).casefold())
    actual_files = sorted(path.relative_to(patch_root).as_posix() for path in patch_root.rglob("*") if path.is_file())
    expected_files = sorted(str(row["physical_path"]) for row in all_staged)
    require(actual_files == expected_files, "post-integration staged file set mismatch")
    for row in all_staged:
        path = patch_root / Path(str(row["physical_path"]))
        require(sha256_file(path) == str(row["output_sha256"]).upper(), f"staged hash mismatch: {path}")

    xml_tree = ET.parse(xml_path)
    xml_patch = xml_tree.getroot().find("patch")
    require(xml_patch is not None, "missing patch node after XML write")
    require(len(xml_patch.findall("file")) == BASE_PHYSICAL_COUNT + SUPPLEMENTAL_PHYSICAL_COUNT,
            "final XML file-rule count mismatch")
    require(len(xml_patch.findall("memory")) == EXPECTED_MEMORY_PATCHES,
            "final XML memory-rule count mismatch")

    manifest["schema"] = "arf-full-runtime-staging-v2"
    manifest["counts"]["supplemental_physical_files"] = SUPPLEMENTAL_PHYSICAL_COUNT
    manifest["counts"]["staged_physical_files"] = len(all_staged)
    manifest["counts"]["riivolution_file_rules"] = len(all_staged)
    manifest["counts"]["riivolution_memory_rules"] = len(memory_rows)
    manifest["riivolution"]["file_count"] = len(all_staged)
    manifest["riivolution"]["memory_count"] = len(memory_rows)
    manifest["riivolution"]["resize_true_count"] = sum(bool(row.get("resize", row["source_size"] != row["output_size"])) for row in all_staged)
    manifest["riivolution"]["sha256"] = sha256_file(xml_path)
    manifest["static_validation"]["staged_file_count"] = len(all_staged)
    manifest["static_validation"]["staged_files"] = all_staged
    manifest["supplemental_runtime_patch"] = {
        "physical_count": len(added),
        "memory_patch_count": len(memory_rows),
        "main_dol_source_sha256": MAIN_DOL_SHA256,
        "main_dol_translations_sha256": sha256_file(args.translations),
        "main_dol_crossreview_sha256": sha256_file(args.runtime_fix / "main_dol_crossreview.json"),
        "main_dol_patched_semantic_sha256": dol_report["output"]["sha256"],
        "main_dol_patch_report_sha256": sha256_file(args.dol_report),
        "codebook_sha256": sha256_file(args.codebook),
        "memory_patches": memory_rows,
        "artifacts": {
            "hbm_manifest_sha256": sha256_file(args.runtime_fix / "hbm_ko/hbm_korean_payload_manifest.json"),
            "endroll_manifest_sha256": sha256_file(args.runtime_fix / "endroll_ui/manifest.json"),
            "endroll_verification_sha256": sha256_file(args.runtime_fix / "endroll_ui/verification_summary.json"),
            "opening_bnr_manifest_sha256": sha256_file(args.runtime_fix / "opening_bnr_ko/opening_bnr_korean_payload_manifest.json"),
            "sfd_video_replacement_report_sha256": sha256_file(args.runtime_fix / "sfd_ko/sfd_video_replacement_report.json"),
            "sfd_final_validation_sha256": sha256_file(args.runtime_fix / "sfd_ko/sfd_final_validation.json"),
            "final_visual_surface_audit_sha256": sha256_file(args.runtime_fix / "visual_sweep/final_visual_surface_audit.json"),
        },
        "physical_files": added,
        "main_dol_staged_physically": False,
        "valid": True,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    report = {
        "schema": "arf-runtime-supplement-integration-v1",
        "game_id": GAME_ID,
        "translation_engine_policy": "Codex internal model only",
        "external_translation_models_or_apis_used": False,
        "base_physical_count": BASE_PHYSICAL_COUNT,
        "supplemental_physical_count": len(added),
        "final_physical_count": len(all_staged),
        "memory_patch_count": len(memory_rows),
        "main_dol_staged_physically": False,
        "xml_sha256": sha256_file(xml_path),
        "staging_manifest_sha256": sha256_file(manifest_path),
        "physical_files": added,
        "valid": True,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({
        "valid": True,
        "physical_files": len(all_staged),
        "supplemental_files": len(added),
        "memory_patches": len(memory_rows),
        "xml_sha256": report["xml_sha256"],
        "manifest_sha256": report["staging_manifest_sha256"],
    }))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IntegrationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
