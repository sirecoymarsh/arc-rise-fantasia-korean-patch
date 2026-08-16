#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import mmap
from pathlib import Path
import struct
import unicodedata


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def lz10_decompress(packed: bytes) -> bytes:
    if len(packed) < 4 or packed[0] != 0x10:
        raise ValueError("not Nintendo LZ10")
    wanted = int.from_bytes(packed[1:4], "little")
    out = bytearray()
    pos = 4
    while len(out) < wanted:
        flags = packed[pos]
        pos += 1
        for bit in range(7, -1, -1):
            if len(out) >= wanted:
                break
            if flags & (1 << bit):
                a, b = packed[pos], packed[pos + 1]
                pos += 2
                length = (a >> 4) + 3
                distance = ((a & 0x0F) << 8 | b) + 1
                for _ in range(length):
                    out.append(out[-distance])
                    if len(out) >= wanted:
                        break
            else:
                out.append(packed[pos])
                pos += 1
    return bytes(out)


def parse_header(data: bytes, vld_size: int) -> list[dict[str, int]]:
    if data[:4] != b"RVLX":
        raise ValueError("bad RVLX header")
    size, count, declared = struct.unpack_from(">III", data, 4)
    if size != len(data) or declared != size + vld_size:
        raise ValueError("RVLX geometry mismatch")
    rows = []
    for index in range(count):
        packed_size, offset = struct.unpack_from(">II", data, 0x20 + index * 8)
        rows.append({"index": index, "offset": offset, "packed_size": packed_size})
    return rows


def extract_rtdp_leaf(path: Path, wanted_name: str) -> bytes:
    data = path.read_bytes()
    if data[:4] != b"RTDP":
        raise ValueError(f"not RTDP: {path}")
    eoh = int.from_bytes(data[4:8], "big")
    count = int.from_bytes(data[8:12], "big")
    for index in range(count):
        pos = 0x20 + index * 40
        name = data[pos:pos + 32].split(b"\0", 1)[0].decode("latin1")
        size = int.from_bytes(data[pos + 32:pos + 36], "big")
        relative = int.from_bytes(data[pos + 36:pos + 40], "big")
        if name == wanted_name:
            return bytes(value ^ 0x55 for value in data[eoh + relative:eoh + relative + size])
    raise ValueError(f"missing RTDP leaf: {wanted_name}")


def is_japanese_char(char: str) -> bool:
    cp = ord(char)
    return (
        0x3040 <= cp <= 0x30FF
        or 0x3400 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF
    )


def is_allowed_ascii(value: int) -> bool:
    return value == 0x15 or value in (0x09, 0x0A, 0x0D) or 0x20 <= value <= 0x7E


def scan_euc_jp_runs(data: bytes, max_bytes: int = 128) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    occupied_until = -1
    pos = 0
    while pos + 1 < len(data):
        if pos < occupied_until:
            pos += 1
            continue
        a, b = data[pos], data[pos + 1]
        if not (0xA1 <= a <= 0xFE and 0xA1 <= b <= 0xFE):
            pos += 1
            continue
        try:
            first = data[pos:pos + 2].decode("euc_jp")
        except UnicodeDecodeError:
            pos += 1
            continue
        if not first or not is_japanese_char(first):
            pos += 1
            continue
        end = pos
        japanese = 0
        while end < len(data) and end - pos < max_bytes:
            value = data[end]
            if value == 0:
                break
            if is_allowed_ascii(value):
                end += 1
                continue
            if end + 1 < len(data) and 0xA1 <= value <= 0xFE and 0xA1 <= data[end + 1] <= 0xFE:
                try:
                    char = data[end:end + 2].decode("euc_jp")
                except UnicodeDecodeError:
                    break
                if not is_japanese_char(char) and not unicodedata.category(char).startswith(("P", "S")):
                    break
                japanese += int(is_japanese_char(char))
                end += 2
                continue
            break
        if end >= len(data) or data[end] != 0 or japanese < 2:
            pos += 1
            continue
        raw = data[pos:end]
        try:
            text = raw.decode("euc_jp")
        except UnicodeDecodeError:
            pos += 1
            continue
        rows.append({
            "offset": pos,
            "end": end,
            "byte_length": len(raw),
            "text": text,
            "raw_hex": raw.hex().upper(),
        })
        occupied_until = end
        pos = end + 1
    return rows


def worker(task: tuple[str, int, int, str, int, int]) -> dict[str, object]:
    source_path, source_offset, source_size, final_path, final_offset, final_size = task
    with open(source_path, "rb") as handle:
        handle.seek(source_offset)
        source = lz10_decompress(handle.read(source_size))
    with open(final_path, "rb") as handle:
        handle.seek(final_offset)
        final = lz10_decompress(handle.read(final_size))
    if len(source) != len(final):
        raise ValueError("unpacked size mismatch")
    first_rtdp = source.find(b"RTDP")
    strings = []
    for row in scan_euc_jp_runs(source):
        offset = int(row["offset"])
        end = int(row["end"])
        final_raw = final[offset:end]
        strings.append({
            **row,
            "section": "before_first_rtdp" if first_rtdp < 0 or offset < first_rtdp else "after_first_rtdp",
            "unchanged_in_final": final_raw == source[offset:end],
            "final_hex": final_raw.hex().upper(),
            "preceding_32_hex": source[max(0, offset - 32):offset].hex().upper(),
            "following_32_hex": source[end:min(len(source), end + 32)].hex().upper(),
        })
    return {
        "unpacked_size": len(source),
        "source_unpacked_sha256": sha256_bytes(source),
        "final_unpacked_sha256": sha256_bytes(final),
        "first_rtdp_offset": first_rtdp,
        "strings": strings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    ns = parser.parse_args()
    root = ns.root.resolve()
    source_vld = root / "work/disc_extracted/DATA/files/Btl/btl_enemy.vld"
    final_vld = root / "work/final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Btl/btl_enemy.vld"
    source_header_path = root / "work/research/table_agent/btl_usual_entries/btl_enemy.vlh"
    final_usual = root / "work/final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Btl/btl_usual.vol"
    catalog_path = root / "work/translation/battle_enemy/battle_enemy_catalog.json"

    source_header = source_header_path.read_bytes()
    final_header = extract_rtdp_leaf(final_usual, "btl_enemy.vlh")
    source_entries = parse_header(source_header, source_vld.stat().st_size)
    final_entries = parse_header(final_header, final_vld.stat().st_size)
    if len(source_entries) != len(final_entries):
        raise ValueError("entry count mismatch")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    covered: dict[int, list[dict[str, object]]] = {}
    for unit in catalog["units"]:
        index = int(unit["id"].split(":")[1])
        covered.setdefault(index, []).append({
            "id": unit["id"],
            "offset": int(unit["offset"]),
            "end": int(unit["offset"]) + int(unit["capacity"]),
            "source_text": unit["source_text"],
            "field": unit["field"],
        })

    tasks = []
    for source_entry, final_entry in zip(source_entries, final_entries):
        tasks.append((
            str(source_vld), source_entry["offset"], source_entry["packed_size"],
            str(final_vld), final_entry["offset"], final_entry["packed_size"],
        ))
    with ProcessPoolExecutor(max_workers=ns.workers) as pool:
        scanned = list(pool.map(worker, tasks, chunksize=1))

    all_strings = []
    uncovered = []
    unchanged = []
    for index, result in enumerate(scanned):
        for string in result["strings"]:
            offset = int(string["offset"])
            end = int(string["end"])
            owners = [
                unit for unit in covered.get(index, [])
                if int(unit["offset"]) <= offset and end <= int(unit["end"])
            ]
            row = {
                "entry": index,
                **string,
                "catalog_covered": bool(owners),
                "catalog_units": [unit["id"] for unit in owners],
            }
            all_strings.append(row)
            if not owners and string["section"] == "before_first_rtdp":
                uncovered.append(row)
            if bool(string["unchanged_in_final"]) and string["section"] == "before_first_rtdp":
                unchanged.append(row)

    catalog_offset_mismatches = []
    by_entry_offset = {(row["entry"], row["offset"]): row for row in all_strings}
    for index, units in covered.items():
        for unit in units:
            source_offset = int(unit["offset"])
            source_text = str(unit["source_text"])
            prefix = 0
            while prefix < len(source_text) and not is_japanese_char(source_text[prefix]):
                prefix += 1
            raw_prefix = source_text[:prefix].encode("euc_jp")
            key = (index, source_offset + len(raw_prefix))
            if key not in by_entry_offset:
                catalog_offset_mismatches.append({"entry": index, "unit": unit["id"], "expected_japanese_offset": key[1]})

    report = {
        "schema": "arf-battle-text-independent-coverage-audit-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal model only",
        "source": {
            "vld": str(source_vld),
            "vld_sha256": sha256_bytes(source_vld.read_bytes()),
            "header_sha256": sha256_bytes(source_header),
        },
        "final": {
            "vld": str(final_vld),
            "vld_sha256": sha256_bytes(final_vld.read_bytes()),
            "header_sha256": sha256_bytes(final_header),
        },
        "catalog": {
            "path": str(catalog_path),
            "sha256": sha256_bytes(catalog_path.read_bytes()),
            "unit_count": len(catalog["units"]),
        },
        "counts": {
            "entries": len(scanned),
            "independent_japanese_runs": len(all_strings),
            "before_first_rtdp": sum(row["section"] == "before_first_rtdp" for row in all_strings),
            "after_first_rtdp": sum(row["section"] == "after_first_rtdp" for row in all_strings),
            "uncovered_before_first_rtdp": len(uncovered),
            "unchanged_before_first_rtdp": len(unchanged),
            "catalog_offset_mismatches": len(catalog_offset_mismatches),
        },
        "uncovered_before_first_rtdp": uncovered,
        "unchanged_before_first_rtdp": unchanged,
        "catalog_offset_mismatches": catalog_offset_mismatches,
        "all_independent_strings_digest": {
            "count": len(all_strings),
            "canonical_json_sha256": sha256_bytes(json.dumps(
                all_strings, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")),
            "sample_first_20": all_strings[:20],
        },
    }
    ns.output.parent.mkdir(parents=True, exist_ok=True)
    ns.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(ns.output), "counts": report["counts"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
