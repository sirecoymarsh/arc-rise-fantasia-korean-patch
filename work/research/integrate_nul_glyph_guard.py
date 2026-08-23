#!/usr/bin/env python3
"""Install the RPJJ99 animated-text NUL guard into final Riivolution staging.

The game's normal text loop rejects the terminating NUL before glyph lookup,
but the animated single-character path at 0x800F5780 does not.  A NUL byte is
therefore interpreted as a multibyte character.  Its page calculation yields
-18 and reads four bytes before the font-page table; those bytes are ``_sys``
from the allocator header's ``font_sys.c`` source-name field (0x5F737973),
which exactly matches the first invalid-read address reported by Dolphin.

This script adds a narrow entry trampoline only to the faulty animation
routine.  A second runtime observation proved that filtering NUL alone merely
exposed the following newline byte (page -17, ``.c\0\0``).  The guard therefore
validates the complete supported lead-byte set: printable ASCII 0x20..0x7E,
EUC-JP half-width lead 0x8E, or multibyte leads 0xA1..0xFE.  Invalid/control
bytes return without lookup; valid input executes the displaced prologue and
resumes the original body.
"""

from __future__ import annotations

import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
SOURCE_DOL = W / "disc_extracted/DATA/sys/main.dol"
STAGING = W / "final_runtime_staging"
XML = STAGING / "riivolution_sd/riivolution/arc_rise_fantasia_ko_full.xml"
STAGING_MANIFEST = STAGING / "staging_manifest.json"
PATCH_MANIFEST = W / "runtime_fix/nul_glyph_guard_patch.json"
INTEGRATION_REPORT = W / "runtime_validation/invalid_read_800e59a0_20260823/nul_glyph_guard_integration.json"
FORENSIC_REPORT = W / "runtime_validation/invalid_read_800e59a0_20260823/static_map_audit/nul_glyph_root_cause.json"

GAME_ID = "RPJJ99"
SOURCE_DOL_SHA256 = "4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC"
BASE_MEMORY_RULES = 943
FINAL_MEMORY_RULES = 945

ANIMATED_GLYPH_ENTRY = 0x800F5780
ANIMATED_GLYPH_BODY = 0x800F5784
CODE_CAVE = 0x80021A14
CODE_CAVE_SECTION_END = 0x80021A40
DISPLACED_PROLOGUE = 0x9421FEF0  # stwu r1,-0x110(r1)


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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    need(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


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


def memory_span_to_file(address: int, length: int, sections: list[dict[str, int | str]]) -> tuple[str, int]:
    matches: list[tuple[str, int]] = []
    for section in sections:
        start = int(section["memory_address"])
        end = start + int(section["size"])
        if start <= address and address + length <= end:
            matches.append((str(section["name"]), int(section["file_offset"]) + address - start))
    need(len(matches) == 1, f"memory span 0x{address:08X}+0x{length:X} maps to {len(matches)} DOL sections")
    return matches[0]


def branch(source: int, target: int) -> int:
    displacement = target - source
    need(displacement % 4 == 0, "unaligned PowerPC branch")
    need(-(1 << 25) <= displacement < (1 << 25), "PowerPC branch is out of range")
    return 0x48000000 | (displacement & 0x03FFFFFC)


def build_patch_rows(source: bytes, sections: list[dict[str, int | str]]) -> list[dict[str, Any]]:
    # Compact range test. Subtracting 0x20 lets one unsigned comparison cover
    # printable ASCII; subtracting another 0x81 maps 0xA1..0xFE to 0..0x5D.
    # Reuse the existing blr at 0x80021A40 as the reject path so that the
    # complete validator fits the audited 44-byte data1 tail exactly.
    cave_words = [
        0x89830000,  # lbz r12,0(r3)
        0x398CFFE0,  # addi r12,r12,-0x20
        0x280C005E,  # cmplwi r12,0x5e (original 0x20..0x7e)
        0x40810018,  # ble cave+0x24 (draw)
        0x280C006E,  # cmplwi r12,0x6e (original 0x8e)
        0x41820010,  # beq cave+0x24 (draw)
        0x398CFF7F,  # addi r12,r12,-0x81 (original minus 0xa1)
        0x280C005D,  # cmplwi r12,0x5d (original 0xa1..0xfe)
        0x4181000C,  # bgt 0x80021a40 (existing blr)
        DISPLACED_PROLOGUE,
        branch(CODE_CAVE + 0x28, ANIMATED_GLYPH_BODY),
    ]
    definitions = [
        {
            "stable_id": "ARF-RUNTIME-NUL-GLYPH-ENTRY",
            "purpose": "redirect animated glyph routine through NUL guard",
            "address": ANIMATED_GLYPH_ENTRY,
            "value": struct.pack(">I", branch(ANIMATED_GLYPH_ENTRY, CODE_CAVE)),
            "expected_original": struct.pack(">I", DISPLACED_PROLOGUE),
        },
        {
            "stable_id": "ARF-RUNTIME-NUL-GLYPH-CAVE",
            "purpose": "reject control/invalid lead bytes; otherwise execute displaced prologue and resume original routine",
            "address": CODE_CAVE,
            "value": b"".join(struct.pack(">I", word) for word in cave_words),
            "expected_original": bytes(4 * len(cave_words)),
        },
    ]
    rows: list[dict[str, Any]] = []
    for definition in definitions:
        address = int(definition["address"])
        value = bytes(definition["value"])
        expected = bytes(definition["expected_original"])
        section, file_offset = memory_span_to_file(address, len(value), sections)
        actual = source[file_offset:file_offset + len(value)]
        need(actual == expected, f"original DOL bytes mismatch at 0x{address:08X}: {actual.hex().upper()}")
        rows.append({
            "stable_id": definition["stable_id"],
            "purpose": definition["purpose"],
            "file_offset": file_offset,
            "file_offset_hex": f"0x{file_offset:08X}",
            "memory_address": address,
            "memory_address_hex": f"0x{address:08X}",
            "section": section,
            "byte_length": len(value),
            "original_hex": expected.hex().upper(),
            "value": value.hex().upper(),
            "value_sha256": sha256_bytes(value),
        })
    return rows


def spans_overlap(a: int, alen: int, b: int, blen: int) -> bool:
    return a < b + blen and b < a + alen


def main() -> int:
    for path in (SOURCE_DOL, XML, STAGING_MANIFEST):
        need(path.is_file(), f"missing input: {path}")
    source = SOURCE_DOL.read_bytes()
    need(sha256_bytes(source) == SOURCE_DOL_SHA256, "source main.dol SHA-256 mismatch")
    sections = dol_sections(source)
    patch_rows = build_patch_rows(source, sections)

    # The chosen cave is the zero-filled tail of data1 immediately before text1.
    cave_section, cave_file_offset = memory_span_to_file(CODE_CAVE, CODE_CAVE_SECTION_END - CODE_CAVE, sections)
    cave_original = source[cave_file_offset:cave_file_offset + CODE_CAVE_SECTION_END - CODE_CAVE]
    need(cave_section == "data1" and cave_original == bytes(len(cave_original)), "code cave is not the audited zero-filled data1 tail")
    raw_pointer_refs = []
    for offset in range(0, len(source) - 3, 4):
        value = struct.unpack_from(">I", source, offset)[0]
        if CODE_CAVE <= value < CODE_CAVE_SECTION_END:
            raw_pointer_refs.append({"file_offset_hex": f"0x{offset:08X}", "value_hex": f"0x{value:08X}"})
    need(not raw_pointer_refs, "chosen code cave has raw aligned DOL pointer references")

    tree = ET.parse(XML)
    patch_nodes = [node for node in tree.getroot().findall(".//patch") if node.findall("file") or node.findall("memory")]
    if not patch_nodes and tree.getroot().tag == "patch":
        patch_nodes = [tree.getroot()]
    need(len(patch_nodes) == 1, f"expected one populated patch node, got {len(patch_nodes)}")
    patch_node = patch_nodes[0]
    new_by_address = {int(row["memory_address"]): row for row in patch_rows}

    retained: list[dict[str, str]] = []
    existing_new: dict[int, dict[str, str]] = {}
    for node in patch_node.findall("memory"):
        attrs = dict(node.attrib)
        address = int(attrs["offset"], 16)
        value = bytes.fromhex(attrs["value"])
        if address in new_by_address:
            existing_new[address] = attrs
            previous_nul_only_cave = "880300002C0000004182000C9421FEF0480D3D604E800020"
            previous_faulty_r0_cave = "880300003800FFE02800005E408100182800006E418200103800FF7F2800005D4181000C9421FEF0480D3D48"
            allowed_values = {str(new_by_address[address]["value"])}
            if address == CODE_CAVE:
                allowed_values.add(previous_nul_only_cave)
                allowed_values.add(previous_faulty_r0_cave)
            need(attrs["value"].upper() in allowed_values, f"unknown stale code patch at 0x{address:08X}")
            continue
        for row in patch_rows:
            need(not spans_overlap(address, len(value), int(row["memory_address"]), int(row["byte_length"])),
                 f"existing memory rule overlaps {row['stable_id']}: 0x{address:08X}")
        retained.append(attrs)
    need(len(retained) == BASE_MEMORY_RULES, f"expected {BASE_MEMORY_RULES} base memory rules, got {len(retained)}")

    for node in list(patch_node.findall("memory")):
        patch_node.remove(node)
    final_memory = retained + [
        {"offset": str(row["memory_address_hex"]), "value": str(row["value"])}
        for row in patch_rows
    ]
    final_memory.sort(key=lambda attrs: int(attrs["offset"], 16))
    need(len({attrs["offset"].upper() for attrs in final_memory}) == FINAL_MEMORY_RULES, "final memory-rule address set is not unique")
    for attrs in final_memory:
        ET.SubElement(patch_node, "memory", attrs)
    ET.indent(tree, space="  ")
    tree.write(XML, encoding="utf-8", xml_declaration=True)
    need(len(ET.parse(XML).getroot().findall(".//memory")) == FINAL_MEMORY_RULES, "written XML memory-rule count mismatch")

    root_cause = {
        "symptom": {
            "first_invalid_read": "0x5F737973",
            "first_pc": "0x800E68FC",
            "subsequent_warning_addresses": ["0x00000008", "0x0000000A", "0x0000000C", "0x5F737977"],
            "classification": "one root fault with cascading invalid reads",
        },
        "mechanism": {
            "faulty_path": "animated single-character renderer 0x800F5780 -> glyph renderer 0x800E65F8",
            "trigger": "terminating NUL and newline/control bytes passed as glyphs",
            "observed_invalid_page_quotients": [-18, -17],
            "font_manager_lookup": "font_manager + 8 + (-18 * 4) = allocation_header + 0x20",
            "allocation_header_bytes": "_sys from font_sys.c",
            "allocation_header_u32_hex": ["0x5F737973", "0x2E630000"],
            "why_only_some_lines": "the normal text loop checks NUL; the animated per-character path did not",
        },
        "scope": {
            "independent_root_causes_confirmed": 1,
            "direct_glyph_renderer_callers": 2,
            "already_guarded_callers": 1,
            "unguarded_callers_fixed": 1,
        },
    }
    patch_manifest = {
        "schema": "arf-runtime-code-patch-v1",
        "game_id": GAME_ID,
        "source_main_dol": {"path": str(SOURCE_DOL), "sha256": SOURCE_DOL_SHA256},
        "root_cause": root_cause,
        "strategy": "complete lead-byte range guard on the sole unguarded animated-glyph routine",
        "warning_suppression_used": False,
        "mmu_required": False,
        "code_cave": {
            "memory_start_hex": f"0x{CODE_CAVE:08X}",
            "memory_end_hex": f"0x{CODE_CAVE_SECTION_END:08X}",
            "section": cave_section,
            "available_zero_bytes": len(cave_original),
            "used_bytes": int(patch_rows[1]["byte_length"]),
            "raw_aligned_pointer_reference_count": len(raw_pointer_refs),
        },
        "patches": patch_rows,
        "checks": {
            "source_hash_verified": True,
            "original_instruction_verified": True,
            "code_cave_zero_fill_verified": True,
            "code_cave_has_no_raw_aligned_pointer_references": True,
            "branch_alignment_and_range_verified": True,
            "supported_lead_ranges_enforced": ["0x20..0x7E", "0x8E", "0xA1..0xFE"],
            "patch_spans_do_not_overlap_existing_rules": True,
        },
        "valid": True,
    }
    write_json(PATCH_MANIFEST, patch_manifest)
    write_json(FORENSIC_REPORT, patch_manifest)

    staging = load_json(STAGING_MANIFEST)
    need(staging.get("game_id") == GAME_ID, "staging game ID mismatch")
    supplemental = staging.get("supplemental_runtime_patch", {})
    memory_rows = list(supplemental.get("memory_patches", []))
    new_addresses = set(new_by_address)
    memory_rows = [row for row in memory_rows if int(row.get("memory_address", int(str(row.get("memory_address_hex", "0")), 16))) not in new_addresses]
    need(len(memory_rows) == BASE_MEMORY_RULES, f"staging manifest has {len(memory_rows)} base memory rows")
    memory_rows.extend(patch_rows)
    memory_rows.sort(key=lambda row: int(row["memory_address"]))
    supplemental["memory_patches"] = memory_rows
    supplemental["memory_patch_count"] = FINAL_MEMORY_RULES
    supplemental["runtime_code_patch_count"] = len(patch_rows)
    supplemental["valid"] = True
    staging["supplemental_runtime_patch"] = supplemental
    staging.setdefault("counts", {})["riivolution_memory_rules"] = FINAL_MEMORY_RULES
    staging["counts"]["runtime_code_patch_memory_rules"] = len(patch_rows)
    staging.setdefault("riivolution", {})["memory_count"] = FINAL_MEMORY_RULES
    staging["riivolution"]["sha256"] = sha256_file(XML)
    staging.setdefault("inputs", {})["nul_glyph_guard_patch"] = {
        "path": str(PATCH_MANIFEST),
        "sha256": sha256_file(PATCH_MANIFEST),
    }
    staging["runtime_code_patch"] = {
        "schema": patch_manifest["schema"],
        "patch_manifest": str(PATCH_MANIFEST),
        "patch_manifest_sha256": sha256_file(PATCH_MANIFEST),
        "memory_rules": len(patch_rows),
        "base_memory_rules": BASE_MEMORY_RULES,
        "final_memory_rules": FINAL_MEMORY_RULES,
        "mmu_required": False,
        "warning_suppression_used": False,
        "root_cause_confirmed": True,
        "valid": True,
    }
    staging["runtime_ready_release"] = False
    staging["dolphin_screen_test"] = "pending_final_single_validation"
    write_json(STAGING_MANIFEST, staging)

    report = {
        "schema": "arf-nul-glyph-guard-integration-v1",
        "game_id": GAME_ID,
        "base_memory_rules": BASE_MEMORY_RULES,
        "added_memory_rules": len(patch_rows),
        "final_memory_rules": FINAL_MEMORY_RULES,
        "patch_manifest": {"path": str(PATCH_MANIFEST), "sha256": sha256_file(PATCH_MANIFEST)},
        "staging_xml": {"path": str(XML), "sha256": sha256_file(XML)},
        "staging_manifest": {"path": str(STAGING_MANIFEST), "sha256": sha256_file(STAGING_MANIFEST)},
        "runtime_validation": "pending final single Dolphin validation",
        "valid": True,
    }
    write_json(INTEGRATION_REPORT, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
