#!/usr/bin/env python3
"""Patch the nested boss/special skill labels in Btl/btl_magic.vld.

Every selected VLD entry is an uncompressed, fixed-size RTDP archive.  RTDP
member payloads are stored XOR 0x55.  This writer changes only the original
NUL-terminated label span and proves that every byte outside those spans is
source-identical.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


CONTROL_RE = re.compile(r"<\$([0-9A-Fa-f]{2})>")
XOR_KEY = 0x55


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def encode_text(text: str, codebook: dict) -> bytes:
    mapping = {
        char: bytes.fromhex(record["bytes_hex"])
        for char, record in codebook["characters"].items()
    }
    out = bytearray()
    cursor = 0
    for match in CONTROL_RE.finditer(text):
        out.extend(encode_plain(text[cursor : match.start()], mapping))
        out.append(int(match.group(1), 16))
        cursor = match.end()
    out.extend(encode_plain(text[cursor:], mapping))
    return bytes(out)


def encode_plain(text: str, mapping: dict[str, bytes]) -> bytes:
    out = bytearray()
    for char in text:
        if char in mapping:
            out.extend(mapping[char])
        elif ord(char) <= 0x7F:
            out.append(ord(char))
        else:
            out.extend(char.encode("euc_jp"))
    return bytes(out)


def parse_rtdp(data: bytes, label: str):
    if data[:4] != b"RTDP" or len(data) < 0x20:
        raise ValueError(f"{label}: not an RTDP archive")
    eoh, count, declared = struct.unpack_from(">III", data, 4)
    if declared > len(data) or 0x20 + count * 40 > eoh:
        raise ValueError(f"{label}: invalid RTDP geometry")
    rows = []
    for index in range(count):
        rec = 0x20 + index * 40
        raw_name = data[rec : rec + 32]
        name = raw_name.split(b"\0", 1)[0].decode("ascii")
        size, relative = struct.unpack_from(">II", data, rec + 32)
        absolute = eoh + relative
        if absolute + size > declared:
            raise ValueError(f"{label}: member {index} exceeds archive")
        rows.append({
            "index": index,
            "name": name,
            "size": size,
            "absolute": absolute,
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--output-dir", type=Path)
    ns = ap.parse_args()
    root = ns.root.resolve()
    output_dir = (ns.output_dir or root / "work/battle_magic_application").resolve()
    source_vld_path = root / "work/disc_extracted/DATA/files/Btl/btl_magic.vld"
    source_vlh_path = root / "work/research/table_agent/btl_usual_entries/btl_magic.vlh"
    translations_path = root / "work/translation/battle_magic/battle_magic_skill_translations.json"
    codebook_path = root / "work/font/final_v3/codebook.json"
    for required in (source_vld_path, source_vlh_path, translations_path, codebook_path):
        if not required.is_file():
            raise FileNotFoundError(required)

    source = source_vld_path.read_bytes()
    header = source_vlh_path.read_bytes()
    doc = load_json(translations_path)
    codebook = load_json(codebook_path)
    if doc.get("translator_model") != "Codex internal":
        raise ValueError("translation provenance must be Codex internal")
    rows = doc["translations"]
    if len(rows) != 80 or len({(r["entry"], r["member"], r["offset"]) for r in rows}) != 80:
        raise ValueError("expected 80 unique battle-magic slots")

    count = struct.unpack_from(">I", header, 8)[0]
    output = bytearray(source)
    allowed = bytearray(len(source))
    report_rows = []

    for row in rows:
        entry = int(row["entry"])
        if not 0 <= entry < count:
            raise ValueError(f"entry out of range: {entry}")
        packed_size, entry_offset = struct.unpack_from(">II", header, 0x20 + entry * 8)
        entry_data = bytes(output[entry_offset : entry_offset + packed_size])
        if entry_data[:4] != b"RTDP":
            raise ValueError(f"entry {entry}: expected uncompressed RTDP")
        members = parse_rtdp(entry_data, f"btl_magic[{entry}]")
        member = next((m for m in members if m["name"] == row["member"]), None)
        if member is None:
            raise ValueError(f"entry {entry}: member not found: {row['member']}")
        stored_start = member["absolute"]
        stored_end = stored_start + member["size"]
        decoded = bytearray(value ^ XOR_KEY for value in entry_data[stored_start:stored_end])
        field_offset = int(row["offset"])
        source_raw = encode_text(row["source_text"], codebook)
        target_raw = encode_text(row["translation_ko"], codebook)
        if decoded[field_offset : field_offset + len(source_raw)] != source_raw:
            actual = bytes(decoded[field_offset : field_offset + len(source_raw)])
            raise ValueError(
                f"entry {entry}/{row['member']}: source mismatch at 0x{field_offset:X}: "
                f"expected {source_raw.hex().upper()} got {actual.hex().upper()}"
            )
        if field_offset + len(source_raw) >= len(decoded) or decoded[field_offset + len(source_raw)] != 0:
            raise ValueError(f"entry {entry}/{row['member']}: source is not NUL terminated")
        if len(target_raw) > len(source_raw):
            raise ValueError(
                f"entry {entry}/{row['member']}: target {len(target_raw)} exceeds source slot {len(source_raw)}"
            )
        prefix_len = 4 if len(source_raw) >= 4 and source_raw[0] == 0x3C and source_raw[1] == 0x15 else 1
        if target_raw[:prefix_len] != source_raw[:prefix_len]:
            raise ValueError(f"entry {entry}/{row['member']}: control/style prefix changed")

        decoded[field_offset : field_offset + len(source_raw)] = b"\0" * len(source_raw)
        decoded[field_offset : field_offset + len(target_raw)] = target_raw
        encoded_member = bytes(value ^ XOR_KEY for value in decoded)
        entry_mut = bytearray(entry_data)
        entry_mut[stored_start:stored_end] = encoded_member
        output[entry_offset : entry_offset + packed_size] = entry_mut

        absolute_field = entry_offset + stored_start + field_offset
        allowed[absolute_field : absolute_field + len(source_raw)] = b"\1" * len(source_raw)
        report_rows.append({
            **row,
            "source_bytes": len(source_raw),
            "target_bytes": len(target_raw),
            "headroom_bytes": len(source_raw) - len(target_raw),
            "entry_offset": entry_offset,
            "member_stored_offset": stored_start,
            "absolute_field_offset": absolute_field,
            "source_raw_hex": source_raw.hex().upper(),
            "target_raw_hex": target_raw.hex().upper(),
        })

    changed = [index for index, (a, b) in enumerate(zip(source, output)) if a != b]
    outside = [index for index in changed if not allowed[index]]
    if outside:
        raise ValueError(f"{len(outside)} bytes changed outside approved label spans")
    if len(output) != len(source) or bytes(output[:0]) != source[:0]:
        raise ValueError("output size changed")

    # Re-read every target from the rebuilt file before emitting it.
    for row in report_rows:
        start = row["absolute_field_offset"]
        stored = output[start : start + row["source_bytes"]]
        decoded = bytes(value ^ XOR_KEY for value in stored)
        target = bytes.fromhex(row["target_raw_hex"])
        if decoded[: len(target)] != target or any(decoded[len(target) :]):
            raise ValueError(f"post-build verification failed: entry {row['entry']}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_vld_path = output_dir / "btl_magic.vld"
    report_path = output_dir / "application_report.json"
    output_vld_path.write_bytes(output)
    report = {
        "schema": "arf-btl-magic-application-v1",
        "game_id": "RPJJ99",
        "translator_model": "Codex internal",
        "source": {
            "vld_path": str(source_vld_path),
            "vld_size": len(source),
            "vld_sha256": sha256(source),
            "vlh_path": str(source_vlh_path),
            "vlh_sha256": sha256(header),
        },
        "inputs": {
            "translations_path": str(translations_path),
            "translations_sha256": sha256(translations_path.read_bytes()),
            "codebook_path": str(codebook_path),
            "codebook_sha256": sha256(codebook_path.read_bytes()),
        },
        "output": {
            "vld_path": str(output_vld_path),
            "vld_size": len(output),
            "vld_sha256": sha256(output),
        },
        "counts": {
            "slots": len(report_rows),
            "unique_source_texts": len({r["source_text"] for r in report_rows}),
            "unique_translations": len({r["translation_ko"] for r in report_rows}),
            "changed_bytes": len(changed),
            "changed_outside_allowed_bytes": len(outside),
        },
        "invariants": {
            "file_size_preserved": len(output) == len(source),
            "vld_header_external_and_unchanged": True,
            "all_entries_uncompressed_rtdp": True,
            "all_targets_fit_original_slots": True,
            "all_control_style_prefixes_preserved": True,
            "all_bytes_outside_label_spans_source_identical": not outside,
            "all_targets_reread_exact": True,
        },
        "rows": report_rows,
        "valid": True,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output_vld_path), **report["counts"], "valid": True}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
