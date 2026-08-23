#!/usr/bin/env python3
"""Patch the field-object Ray Stone name in the cumulative RPJJ99 btl_usual.vol.

The ordinary monster database already translates enemy entry 269.  The field
object used by battle targeting keeps a second copy in RTDP member 25
(`fld000.bin`) at BTEM offset 0x180.  This script patches that independent
consumer with the frozen Korean codebook, proves byte confinement, integrates
the cumulative container, and updates the staging manifest hash.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
STAGED = W / "final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Btl/btl_usual.vol"
REFERENCE_V110 = W / "battle_ui_raster_application/btl_usual.vol"
STAGING_MANIFEST = W / "final_runtime_staging/staging_manifest.json"
CODEBOOK = W / "font/final_v3/codebook.json"
APP = W / "ray_stone_field_application"
OUTPUT = APP / "btl_usual.vol"
REPORT = APP / "application_report.json"

GAME_ID = "RPJJ99"
SOURCE_CONTAINER_SHA256 = "C57249A61EA292B2AE1C2DD941804252543346E398B4B8E38275715B27AFDEA3"
ENTRY_INDEX = 25
ENTRY_NAME = "fld000.bin"
ENTRY_SIZE = 392_704
SOURCE_ENTRY_SHA256 = "81ACAEDD68D9831F46EC36484803091C5BC227338D9B01A7307EF9554157941E"
FIELD_OFFSET = 0x180
FIELD_CAPACITY = 35
METADATA_OFFSET = FIELD_OFFSET + FIELD_CAPACITY
METADATA_EXPECTED = 0x0A
SOURCE_TEXT = "レイストーン"
TARGET_TEXT = "레이 스톤"
SOURCE_HEX = "A5ECA5A4A5B9A5C8A1BCA5F3"
TARGET_HEX = "B6DEB0AB20BCF7C6D1"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    need(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def parse_rtdp(data: bytes) -> tuple[int, list[dict[str, Any]]]:
    need(data[:4] == b"RTDP", "btl_usual.vol is not RTDP")
    end_of_header, count = struct.unpack_from(">II", data, 4)
    need(end_of_header >= 0x20 + count * 40, "RTDP header is too small")
    need(end_of_header <= len(data), "RTDP header exceeds file")
    rows: list[dict[str, Any]] = []
    for index in range(count):
        position = 0x20 + index * 40
        name = data[position:position + 32].split(b"\0", 1)[0].decode("ascii")
        size, relative = struct.unpack_from(">II", data, position + 32)
        start = end_of_header + relative
        end = start + size
        need(start >= end_of_header and end <= len(data), f"RTDP member {index} exceeds file")
        rows.append({"index": index, "name": name, "size": size, "relative": relative, "start": start, "end": end})
    return end_of_header, rows


def decode_member(data: bytes, row: dict[str, Any]) -> bytes:
    return bytes(value ^ 0x55 for value in data[int(row["start"]):int(row["end"])])


def encode_target(codebook: dict[str, Any]) -> bytes:
    parts: list[bytes] = []
    characters = codebook["characters"]
    for character in TARGET_TEXT:
        if character in characters:
            parts.append(bytes.fromhex(characters[character]["bytes_hex"]))
        else:
            need(ord(character) <= 0x7F, f"target character missing from codebook: {character!r}")
            parts.append(character.encode("ascii"))
    result = b"".join(parts)
    need(result.hex().upper() == TARGET_HEX, "frozen target encoding changed")
    return result


def main() -> int:
    for path in (STAGED, REFERENCE_V110, STAGING_MANIFEST, CODEBOOK):
        need(path.is_file(), f"missing input: {path}")

    source = REFERENCE_V110.read_bytes()
    source_hash = sha256_bytes(source)
    _, rows = parse_rtdp(source)
    need(len(rows) == 26, f"unexpected btl_usual member count: {len(rows)}")
    row = rows[ENTRY_INDEX]
    need(row["name"] == ENTRY_NAME and row["size"] == ENTRY_SIZE, "fld000.bin identity/size changed")
    before_member = decode_member(source, row)
    current_raw = before_member[FIELD_OFFSET:FIELD_OFFSET + FIELD_CAPACITY].split(b"\0", 1)[0]
    target = encode_target(read_json(CODEBOOK))

    need(source_hash == SOURCE_CONTAINER_SHA256, f"unexpected v1.1.0 cumulative btl_usual source hash: {source_hash}")
    need(sha256_bytes(before_member) == SOURCE_ENTRY_SHA256, "fld000.bin trusted source hash changed")
    need(current_raw.hex().upper() == SOURCE_HEX, "Ray Stone source text bytes changed")
    need(current_raw.decode("euc_jp") == SOURCE_TEXT, "Ray Stone source text decode changed")
    need(before_member[METADATA_OFFSET] == METADATA_EXPECTED, "BTEM name metadata byte changed")
    need(len(target) < FIELD_CAPACITY, "Korean Ray Stone name does not fit the field")

    after_member = bytearray(before_member)
    after_member[FIELD_OFFSET:FIELD_OFFSET + FIELD_CAPACITY] = bytes(FIELD_CAPACITY)
    after_member[FIELD_OFFSET:FIELD_OFFSET + len(target)] = target
    need(after_member[METADATA_OFFSET] == METADATA_EXPECTED, "BTEM metadata was overwritten")

    changed_member_offsets = [index for index, pair in enumerate(zip(before_member, after_member)) if pair[0] != pair[1]]
    need(all(FIELD_OFFSET <= index < FIELD_OFFSET + FIELD_CAPACITY for index in changed_member_offsets), "member bytes changed outside name field")

    output = bytearray(source)
    encoded = bytes(value ^ 0x55 for value in after_member)
    output[int(row["start"]):int(row["end"])] = encoded
    output_bytes = bytes(output)
    need(len(output_bytes) == len(source), "outer container size changed")

    _, output_rows = parse_rtdp(output_bytes)
    for before_row, after_row in zip(rows, output_rows, strict=True):
        need((before_row["index"], before_row["name"], before_row["size"], before_row["relative"]) ==
             (after_row["index"], after_row["name"], after_row["size"], after_row["relative"]),
             "RTDP layout changed")
        if before_row["index"] != ENTRY_INDEX:
            need(decode_member(source, before_row) == decode_member(output_bytes, after_row),
                 f"unrelated RTDP member changed: {before_row['name']}")
    verified_member = decode_member(output_bytes, output_rows[ENTRY_INDEX])
    need(verified_member[FIELD_OFFSET:FIELD_OFFSET + len(target)] == target, "target bytes missing after rebuild")
    need(verified_member[FIELD_OFFSET + len(target):FIELD_OFFSET + FIELD_CAPACITY] ==
         bytes(FIELD_CAPACITY - len(target)), "target field padding is not zero")
    need(verified_member[METADATA_OFFSET] == METADATA_EXPECTED, "target metadata byte changed")

    current_staged = STAGED.read_bytes()
    already_applied = current_staged == output_bytes
    need(current_staged == source or already_applied,
         f"staged btl_usual is neither v1.1.0 source nor expected fixed output: {sha256_bytes(current_staged)}")

    APP.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(output_bytes)
    temporary = STAGED.with_suffix(STAGED.suffix + ".partial")
    temporary.write_bytes(output_bytes)
    os.replace(temporary, STAGED)
    need(STAGED.read_bytes() == output_bytes, "staging integration reread mismatch")

    manifest = read_json(STAGING_MANIFEST)
    need(manifest.get("game_id") == GAME_ID, "staging game ID changed")
    staged_rows = manifest["static_validation"]["staged_files"]
    matches = [item for item in staged_rows if item["physical_path"] == "Btl/btl_usual.vol"]
    need(len(matches) == 1, "staging manifest has no unique btl_usual row")
    staged_row = matches[0]
    need(staged_row["source_sha256"] == "D4DC0D5C73641AC5CA57ECB3EFCF654D6FE67F2AA2BBF6F6EB7FFEF9F6F8DA2C", "original btl_usual contract changed")
    staged_row["output_sha256"] = sha256_bytes(output_bytes)
    staged_row["output_size"] = len(output_bytes)
    manifest["counts"]["battle_field_object_name_residue_translations"] = 1
    manifest["ray_stone_field_patch"] = {
        "schema": "arf-ray-stone-field-name-patch-v1",
        "report": "work/ray_stone_field_application/application_report.json",
        "physical_path": "Btl/btl_usual.vol",
        "entry_index": ENTRY_INDEX,
        "member": ENTRY_NAME,
        "field_offset_hex": f"0x{FIELD_OFFSET:X}",
        "source_text": SOURCE_TEXT,
        "translation_ko": TARGET_TEXT,
        "output_sha256": sha256_bytes(output_bytes),
        "translator_model": "Codex internal",
    }
    write_json_atomic(STAGING_MANIFEST, manifest)

    report = {
        "schema": "arf-ray-stone-field-name-application-v1",
        "game_id": GAME_ID,
        "valid": True,
        "already_applied": already_applied,
        "physical_path": "Btl/btl_usual.vol",
        "source_container_sha256": source_hash,
        "output_container_sha256": sha256_bytes(output_bytes),
        "container_size": len(output_bytes),
        "member_index": ENTRY_INDEX,
        "member_name": ENTRY_NAME,
        "member_size": ENTRY_SIZE,
        "source_member_sha256": sha256_bytes(before_member),
        "output_member_sha256": sha256_bytes(verified_member),
        "field_offset_hex": f"0x{FIELD_OFFSET:X}",
        "field_capacity": FIELD_CAPACITY,
        "source_text": SOURCE_TEXT,
        "translation_ko": TARGET_TEXT,
        "source_hex": SOURCE_HEX,
        "target_hex": TARGET_HEX,
        "changed_member_bytes": len(changed_member_offsets),
        "changed_outside_allowlist": 0,
        "rtdp_layout_preserved": True,
        "unrelated_members_unchanged": True,
        "metadata_byte_preserved": True,
        "translator_model": "Codex internal",
        "external_translation_models_or_apis_used": False,
        "staging_manifest_sha256": sha256_bytes(STAGING_MANIFEST.read_bytes()),
    }
    write_json_atomic(REPORT, report)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
