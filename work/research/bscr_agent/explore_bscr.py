#!/usr/bin/env python3
"""Read-only exploratory scanner for Arc Rise Fantasia BSCR assets."""

from __future__ import annotations

import hashlib
import json
import struct
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


RTDP_TABLE_OFFSET = 0x20
RTDP_RECORD_SIZE = 40
XOR_KEY = 0x55


def decompress_lz10(data: bytes) -> bytes:
    if len(data) < 4 or data[0] != 0x10:
        raise ValueError("not LZ10")
    expected = int.from_bytes(data[1:4], "little")
    if expected <= 0:
        raise ValueError("invalid LZ10 output size")
    pos = 4
    out = bytearray()
    while len(out) < expected:
        flags = data[pos]
        pos += 1
        for bit in range(7, -1, -1):
            if len(out) >= expected:
                break
            if flags & (1 << bit):
                first, second = data[pos], data[pos + 1]
                pos += 2
                length = (first >> 4) + 3
                distance = (((first & 0x0F) << 8) | second) + 1
                if distance > len(out):
                    raise ValueError("invalid LZ10 distance")
                for _ in range(length):
                    out.append(out[-distance])
                    if len(out) >= expected:
                        break
            else:
                out.append(data[pos])
                pos += 1
    return bytes(out)


@dataclass(frozen=True)
class Asset:
    locator: str
    physical_path: str
    data: bytes


def iter_logical(data: bytes, locator: str, physical_path: str, depth: int = 0) -> Iterator[Asset]:
    if depth > 8:
        raise ValueError(f"nesting too deep: {locator}")
    if data[:4] == b"RTDP":
        eoh, count, declared_size = struct.unpack_from(">III", data, 4)
        table_end = RTDP_TABLE_OFFSET + count * RTDP_RECORD_SIZE
        if not (table_end <= eoh <= len(data)):
            raise ValueError(f"bad RTDP header: {locator}")
        if declared_size not in (0, len(data)):
            raise ValueError(f"bad RTDP size: {locator}")
        for index in range(count):
            pos = RTDP_TABLE_OFFSET + index * RTDP_RECORD_SIZE
            raw_name, size, rel = struct.unpack_from(">32sII", data, pos)
            name = raw_name.split(b"\0", 1)[0].decode("ascii", errors="replace")
            start = eoh + rel
            end = start + size
            if end > len(data):
                raise ValueError(f"bad RTDP entry: {locator}::{index:04d}:{name}")
            decoded = bytes(value ^ XOR_KEY for value in data[start:end])
            child = f"{locator}::{index:04d}:{name or 'unnamed'}"
            yield from iter_logical(decoded, child, physical_path, depth + 1)
        return
    if data and data[0] == 0x10:
        expected = int.from_bytes(data[1:4], "little") if len(data) >= 4 else 0
        if 0 < expected <= 256 * 1024 * 1024:
            yield from iter_logical(decompress_lz10(data), locator + "::lz10", physical_path, depth + 1)
            return
    yield Asset(locator=locator, physical_path=physical_path, data=data)


def iter_bscr(root: Path) -> Iterator[Asset]:
    paths = sorted(
        (p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".vol", ".cxd"}),
        key=lambda p: p.relative_to(root).as_posix().lower(),
    )
    for path in paths:
        rel = path.relative_to(root).as_posix()
        for asset in iter_logical(path.read_bytes(), rel, rel):
            if asset.data[:4] == b"bscr":
                yield asset


def parse_header(asset: Asset) -> dict[str, object]:
    data = asset.data
    if len(data) < 0x40:
        raise ValueError("short BSCR")
    version = struct.unpack_from(">H", data, 4)[0]
    raw_name = data[6:0x24]
    name = raw_name.split(b"\0", 1)[0].decode("ascii", errors="replace")
    size, descriptor_count, descriptor_start, field_30, pool_start, bytecode_size, bytecode_start = struct.unpack_from(
        ">7I", data, 0x24
    )
    pos = descriptor_start
    descriptor_sizes: list[int] = []
    descriptor_types: list[int] = []
    descriptor_names: list[str] = []
    descriptor_parse_error = None
    try:
        for _ in range(descriptor_count):
            record_size, record_type = struct.unpack_from(">HH", data, pos)
            if record_size < 4 or pos + record_size > len(data):
                raise ValueError(f"bad descriptor size {record_size:#x} at {pos:#x}")
            descriptor_sizes.append(record_size)
            descriptor_types.append(record_type)
            descriptor_names.append(data[pos + 4 : pos + 36].split(b"\0", 1)[0].decode("ascii", errors="replace"))
            pos += record_size
    except Exception as exc:  # retained as evidence in the manifest
        descriptor_parse_error = str(exc)
    pool = data[pool_start:bytecode_start]
    # The pool is a dense sequence of NUL-terminated byte strings followed by
    # zero padding to a four-byte boundary.  Keep every non-padding record;
    # referenced empty constants, if any, are diagnosed below from VM cells.
    last_nonzero = len(pool) - 1
    while last_nonzero >= 0 and pool[last_nonzero] == 0:
        last_nonzero -= 1
    content_end = last_nonzero + 2 if last_nonzero >= 0 else 0
    pool_padding = pool[content_end:]
    string_records: list[dict[str, object]] = []
    cursor = 0
    while cursor < content_end:
        end = pool.find(b"\0", cursor, content_end)
        if end < 0:
            break
        raw = pool[cursor:end]
        try:
            decoded = raw.decode("euc_jp")
            decode_ok = True
        except UnicodeDecodeError:
            decoded = ""
            decode_ok = False
        string_records.append(
            {
                "relative_offset": cursor,
                "byte_length": len(raw),
                "raw_hex": raw.hex(),
                "decoded": decoded,
                "decode_ok": decode_ok,
            }
        )
        cursor = end + 1

    string_offsets = {int(record["relative_offset"]) for record in string_records}
    instruction_count = bytecode_size // 16 if bytecode_size % 16 == 0 else -1
    opcode_counts: Counter[str] = Counter()
    matching_operand_opcode_counts: Counter[str] = Counter()
    invalid_string_pointer_cells: list[dict[str, object]] = []
    referenced_offsets: Counter[int] = Counter()
    if instruction_count >= 0 and bytecode_start + bytecode_size <= len(data):
        for index in range(instruction_count):
            cell_pos = bytecode_start + index * 16
            opcode = data[cell_pos : cell_pos + 4]
            operand = struct.unpack_from(">I", data, cell_pos + 4)[0]
            opcode_hex = opcode.hex()
            opcode_counts[opcode_hex] += 1
            if operand in string_offsets:
                matching_operand_opcode_counts[opcode_hex] += 1
            if opcode == b"\x1a\xf0\xf1\x5a":
                if operand not in string_offsets:
                    invalid_string_pointer_cells.append(
                        {"instruction_index": index, "file_offset": cell_pos, "operand": operand}
                    )
                else:
                    referenced_offsets[operand] += 1

    return {
        "locator": asset.locator,
        "physical_path": asset.physical_path,
        "sha256": hashlib.sha256(data).hexdigest(),
        "length": len(data),
        "version": version,
        "name": name,
        "size": size,
        "descriptor_count": descriptor_count,
        "descriptor_start": descriptor_start,
        "field_30": field_30,
        "pool_start": pool_start,
        "bytecode_start": bytecode_start,
        "bytecode_size": bytecode_size,
        "instruction_count": instruction_count,
        "pool_size": bytecode_start - pool_start,
        "pool_content_end": content_end,
        "pool_padding_hex": pool_padding.hex(),
        "string_record_count": len(string_records),
        "string_records": string_records,
        "referenced_string_count": len(referenced_offsets),
        "string_pointer_reference_count": sum(referenced_offsets.values()),
        "unreferenced_string_offsets": sorted(string_offsets - set(referenced_offsets)),
        "invalid_string_pointer_cells": invalid_string_pointer_cells,
        "opcode_counts": dict(opcode_counts),
        "matching_operand_opcode_counts": dict(matching_operand_opcode_counts),
        "descriptor_walk_end": pos,
        "descriptor_sizes": descriptor_sizes,
        "descriptor_types": descriptor_types,
        "descriptor_names": descriptor_names,
        "descriptor_parse_error": descriptor_parse_error,
        "size_matches": size == len(data),
        "bytecode_bounds_match": bytecode_start + bytecode_size == len(data),
        "bytecode_size_multiple_16": bytecode_size % 16 == 0,
        "pool_strings_fill_section": cursor == content_end,
        "pool_padding_zero": not any(pool_padding),
        "descriptors_end_at_pool": pos == pool_start,
    }


def main() -> None:
    workspace = Path(__file__).resolve().parents[3]
    root = workspace / "work" / "disc_extracted" / "DATA" / "files"
    output = Path(__file__).resolve().parent / "bscr_manifest.json"
    records = [parse_header(asset) for asset in iter_bscr(root)]
    summary = {
        "asset_count": len(records),
        "version_counts": dict(Counter(str(r["version"]) for r in records)),
        "descriptor_start_counts": dict(Counter(str(r["descriptor_start"]) for r in records)),
        "descriptor_type_counts": dict(
            Counter(str(value) for record in records for value in record["descriptor_types"])
        ),
        "all_size_match": all(r["size_matches"] for r in records),
        "all_bytecode_bounds_match": all(r["bytecode_bounds_match"] for r in records),
        "all_bytecode_sizes_multiple_16": all(r["bytecode_size_multiple_16"] for r in records),
        "all_pool_strings_fill_section": all(r["pool_strings_fill_section"] for r in records),
        "all_pool_padding_zero": all(r["pool_padding_zero"] for r in records),
        "total_strings": sum(int(r["string_record_count"]) for r in records),
        "total_string_pointer_references": sum(int(r["string_pointer_reference_count"]) for r in records),
        "invalid_string_pointer_cells": [
            {"locator": r["locator"], "cells": r["invalid_string_pointer_cells"]}
            for r in records
            if r["invalid_string_pointer_cells"]
        ],
        "string_operand_opcode_counts": dict(
            Counter(
                {
                    opcode: sum(
                        int(record["matching_operand_opcode_counts"].get(opcode, 0))
                        for record in records
                    )
                    for opcode in {
                        opcode
                        for record in records
                        for opcode in record["matching_operand_opcode_counts"]
                    }
                }
            )
        ),
        "all_descriptors_end_at_pool": all(r["descriptors_end_at_pool"] for r in records),
        "parse_errors": [
            {"locator": r["locator"], "error": r["descriptor_parse_error"]}
            for r in records
            if r["descriptor_parse_error"]
        ],
    }
    output.write_text(json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
