#!/usr/bin/env python3
"""Build a stable, read-only Japanese text catalog for Arc Rise Fantasia (RPJJ99).

The game stores most visible text as EUC-JP.  Physical `.vol` files and many
LZ10-compressed `.cxd` files contain XOR-0x55 RTDP archives.  This scanner walks
those containers in memory, recognizes BSCR string pools, and scans conservative
binary leaf types for NUL-terminated EUC-JP units.  It never writes beside the
extracted disc tree and never mutates the source RVZ or extracted files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import struct
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


TEXT_LEAF_EXTENSIONS = {
    ".bscr",
    ".bin",
    ".dat",
    ".vld",
    ".cli",
    ".lit",
    ".b",
    ".txt",
    ".csv",
}
DIRECT_TEXT_ASSETS = {
    "Btl/btl_tutorial.vld",
    "Sys/help.bin",
    "Sys/monster_book.bin",
}
SKIP_MAGICS = {b"WTMD", b"bres", b"RSTM", b"SFD\0"}
RTDP_TABLE_OFFSET = 0x20
RTDP_RECORD_SIZE = 40
XOR_KEY = 0x55


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_id(locator: str, offset: int, raw: bytes) -> str:
    identity = locator.encode("utf-8") + b"\0" + offset.to_bytes(8, "big") + b"\0" + raw
    return "ARF-" + hashlib.sha1(identity).hexdigest()[:20].upper()


def align_up(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def decompress_lz10(data: bytes) -> bytes:
    if len(data) < 4 or data[0] != 0x10:
        raise ValueError("not an LZ10 stream")
    expected = int.from_bytes(data[1:4], "little")
    if expected <= 0:
        raise ValueError("unsupported zero-sized/extended LZ10 header")
    source = 4
    output = bytearray()
    while len(output) < expected:
        if source >= len(data):
            raise ValueError(f"truncated LZ10 flags at {len(output)}/{expected}")
        flags = data[source]
        source += 1
        for bit in range(7, -1, -1):
            if len(output) >= expected:
                break
            if flags & (1 << bit):
                if source + 2 > len(data):
                    raise ValueError("truncated LZ10 back-reference")
                first, second = data[source], data[source + 1]
                source += 2
                length = (first >> 4) + 3
                distance = (((first & 0x0F) << 8) | second) + 1
                if distance > len(output):
                    raise ValueError(f"invalid LZ10 distance {distance}")
                for _ in range(length):
                    output.append(output[-distance])
                    if len(output) >= expected:
                        break
            else:
                if source >= len(data):
                    raise ValueError("truncated LZ10 literal")
                output.append(data[source])
                source += 1
    return bytes(output)


@dataclass(frozen=True)
class RtdpEntry:
    index: int
    name: str
    size: int
    relative_offset: int
    absolute_offset: int
    decoded: bytes


def parse_rtdp(data: bytes, locator: str) -> list[RtdpEntry]:
    if len(data) < RTDP_TABLE_OFFSET or data[:4] != b"RTDP":
        raise ValueError(f"{locator}: not RTDP")
    end_of_header, count, declared_size = struct.unpack_from(">III", data, 4)
    table_end = RTDP_TABLE_OFFSET + count * RTDP_RECORD_SIZE
    if table_end > len(data) or not (table_end <= end_of_header <= len(data)):
        raise ValueError(f"{locator}: invalid RTDP header/table bounds")
    if declared_size not in (0, len(data)):
        raise ValueError(f"{locator}: RTDP size {declared_size} != {len(data)}")
    entries: list[RtdpEntry] = []
    for index in range(count):
        pos = RTDP_TABLE_OFFSET + index * RTDP_RECORD_SIZE
        raw_name, size, relative_offset = struct.unpack_from(">32sII", data, pos)
        name = raw_name.split(b"\0", 1)[0].decode("ascii", errors="replace")
        start = end_of_header + relative_offset
        end = start + size
        if start < end_of_header or end > len(data):
            raise ValueError(f"{locator}: RTDP entry {index} out of range")
        stored = data[start:end]
        decoded = bytes(value ^ XOR_KEY for value in stored)
        entries.append(RtdpEntry(index, name, size, relative_offset, start, decoded))
    return entries


def is_japanese_char(char: str) -> bool:
    code = ord(char)
    return (
        0x3000 <= code <= 0x303F
        or 0x3040 <= code <= 0x30FF
        or 0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0xFF01 <= code <= 0xFFEF
    )


def euc_jp_unit(data: bytes, pos: int) -> tuple[int, str] | None:
    value = data[pos]
    if value in (0x09, 0x0A, 0x0D):
        return 1, {0x09: "\t", 0x0A: "\n", 0x0D: "\r"}[value]
    if 0x20 <= value <= 0x7E:
        return 1, chr(value)
    length = 0
    if 0xA1 <= value <= 0xFE and pos + 1 < len(data) and 0xA1 <= data[pos + 1] <= 0xFE:
        length = 2
    elif value == 0x8E and pos + 1 < len(data) and 0xA1 <= data[pos + 1] <= 0xDF:
        length = 2
    elif (
        value == 0x8F
        and pos + 2 < len(data)
        and 0xA1 <= data[pos + 1] <= 0xFE
        and 0xA1 <= data[pos + 2] <= 0xFE
    ):
        length = 3
    if not length:
        return None
    raw = data[pos : pos + length]
    try:
        return length, raw.decode("euc_jp")
    except UnicodeDecodeError:
        return None


def split_tokenized_segments(chunk: bytes, chunk_offset: int) -> Iterator[dict[str, object]]:
    """Yield EUC-JP/control segments, splitting on invalid high binary bytes.

    Low control bytes are retained as `<$XX>` tokens.  Arc Rise Fantasia uses
    values such as 0x13/0x19/0x1f inside otherwise textual fields.
    """
    start = 0
    cursor = 0
    parts: list[str] = []
    japanese = 0
    control_count = 0

    def emit(end: int) -> dict[str, object] | None:
        nonlocal start, parts, japanese, control_count
        raw = chunk[start:end]
        text = "".join(parts)
        visible = sum(1 for char in text if not (char == "<" or char == ">"))
        result = None
        if raw and japanese >= 1 and visible >= 1 and len(raw) <= 8192:
            result = {
                "offset": chunk_offset + start,
                "raw": raw,
                "source_text": text,
                "japanese_chars": japanese,
                "control_count": control_count,
            }
        parts = []
        japanese = 0
        control_count = 0
        return result

    while cursor < len(chunk):
        unit = euc_jp_unit(chunk, cursor)
        if unit is not None:
            length, text = unit
            parts.append(text)
            japanese += sum(1 for char in text if is_japanese_char(char))
            cursor += length
            continue
        value = chunk[cursor]
        if 0x01 <= value <= 0x1F or value == 0x7F:
            parts.append(f"<$%02X>" % value)
            control_count += 1
            cursor += 1
            continue
        result = emit(cursor)
        if result is not None:
            yield result
        cursor += 1
        start = cursor
    result = emit(cursor)
    if result is not None:
        yield result


def scan_nul_strings(data: bytes, base_offset: int = 0) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    cursor = 0
    while cursor < len(data):
        end = data.find(b"\0", cursor)
        terminated = end >= 0
        if not terminated:
            end = len(data)
        chunk = data[cursor:end]
        for segment in split_tokenized_segments(chunk, base_offset + cursor):
            segment_start = int(segment["offset"]) - base_offset
            raw = segment["raw"]
            assert isinstance(raw, bytes)
            # The capacity is exact only when the segment reaches the NUL.
            reaches_nul = terminated and segment_start + len(raw) == end
            segment["capacity_to_nul"] = len(raw) if reaches_nul else None
            segment["nul_terminated"] = reaches_nul
            records.append(segment)
        if not terminated:
            break
        cursor = end + 1
    return records


def bscr_string_bounds(data: bytes) -> tuple[int, int] | None:
    if len(data) < 0x40 or data[:4] != b"bscr":
        return None
    file_size = int.from_bytes(data[0x24:0x28], "big")
    pool_start = int.from_bytes(data[0x34:0x38], "big")
    bytecode_size = int.from_bytes(data[0x38:0x3C], "big")
    pool_end = int.from_bytes(data[0x3C:0x40], "big")
    if file_size not in (0, len(data)):
        return None
    if not (0x40 <= pool_start <= pool_end <= len(data)):
        return None
    if pool_end + bytecode_size != len(data) or bytecode_size % 16:
        return None
    return pool_start, pool_end


def surface_for(locator: str, leaf_name: str) -> str:
    normalized = locator.replace("\\", "/").lower()
    if leaf_name.lower().endswith(".bscr"):
        if "/event/" in "/" + normalized:
            return "event_script"
        if "/map/" in "/" + normalized:
            return "map_dialogue"
        return "script"
    if "/sys/" in "/" + normalized:
        return "system_database"
    if "/btl/" in "/" + normalized:
        return "battle_text"
    if "/interface/" in "/" + normalized or "/title/" in "/" + normalized:
        return "interface_text"
    return "misc_text"


class CatalogBuilder:
    def __init__(self, root: Path, vetted_payloads: Path | None = None) -> None:
        self.root = root
        self.records: list[dict[str, object]] = []
        self.errors: list[dict[str, str]] = []
        self.stats: Counter[str] = Counter()
        self.physical_hashes: dict[str, str] = {}
        self._seen_logical: set[tuple[str, str]] = set()
        self.vetted_identities: set[str] = set()
        self.vetted_metadata: dict[str, dict[str, object]] = {}
        if vetted_payloads and vetted_payloads.is_file():
            parsed = json.loads(vetted_payloads.read_text(encoding="utf-8"))
            for item in parsed:
                identity = str(item["entryIdentity"]).replace("\\", "/")
                # The mixed fld000 resource produced hundreds of known false
                # positives.  Keep it in the surface inventory, but do not
                # promote its raw heuristic hits to translation units until its
                # BTEM schema is mapped.
                if item.get("formatClass") == "embedded field/resource labels":
                    continue
                self.vetted_identities.add(identity)
                self.vetted_metadata[identity] = item

    def add_records(
        self,
        data: bytes,
        locator: str,
        physical_path: str,
        leaf_name: str,
        mode: str,
        base_offset: int = 0,
    ) -> None:
        candidates = scan_nul_strings(data, base_offset=base_offset)
        leaf_hash = sha256(data if base_offset == 0 else data)
        surface = surface_for(locator, leaf_name)
        for candidate in candidates:
            # Translation units must be complete NUL-terminated fields.  The
            # more permissive tokenizer is useful for forensic discovery, but
            # partial binary fragments are not safe inputs for translation.
            if not candidate["nul_terminated"] or int(candidate["japanese_chars"]) < 2:
                continue
            raw = candidate.pop("raw")
            assert isinstance(raw, bytes)
            offset = int(candidate["offset"])
            record = {
                "id": stable_id(locator, offset, raw),
                "surface": surface,
                "physical_path": physical_path,
                "logical_locator": locator,
                "leaf_name": leaf_name,
                "extraction_mode": mode,
                "leaf_sha256": leaf_hash,
                "offset": offset,
                "offset_hex": f"0x{offset:X}",
                "byte_length": len(raw),
                "raw_hex": raw.hex().upper(),
                "source_text": candidate["source_text"],
                "japanese_chars": candidate["japanese_chars"],
                "control_count": candidate["control_count"],
                "capacity_to_nul": candidate["capacity_to_nul"],
                "nul_terminated": candidate["nul_terminated"],
                "translation_ko": "",
                "status": "untranslated",
                "review_status": "pending",
            }
            self.records.append(record)
            self.stats[f"surface:{surface}"] += 1
        self.stats["logical_text_assets"] += 1

    def process_logical(self, data: bytes, locator: str, physical_path: str, leaf_name: str, depth: int = 0) -> None:
        if depth > 8:
            self.errors.append({"locator": locator, "error": "container recursion exceeds 8"})
            return
        digest = sha256(data)
        seen_key = (locator, digest)
        if seen_key in self._seen_logical:
            return
        self._seen_logical.add(seen_key)

        try:
            if len(data) >= 4 and data[:4] == b"RTDP":
                self.stats["rtdp_archives"] += 1
                for entry in parse_rtdp(data, locator):
                    name = entry.name or f"unnamed_{entry.index:04d}"
                    child = f"{locator}::{entry.index:04d}:{name}"
                    if entry.size:
                        self.process_logical(entry.decoded, child, physical_path, name, depth + 1)
                return
            if len(data) >= 4 and data[0] == 0x10:
                expected = int.from_bytes(data[1:4], "little")
                # Plausibility bound prevents random binary leaves from being
                # interpreted as giant compressed streams.
                if 0 < expected <= 256 * 1024 * 1024:
                    unpacked = decompress_lz10(data)
                    self.stats["lz10_streams"] += 1
                    self.process_logical(unpacked, locator + "::lz10", physical_path, leaf_name, depth + 1)
                    return
        except (ValueError, struct.error) as exc:
            self.errors.append({"locator": locator, "error": str(exc)})
            return

        if data[:4] in SKIP_MAGICS:
            self.stats["skipped_graphic_or_media"] += 1
            return
        bounds = bscr_string_bounds(data)
        if bounds is not None:
            pool_start, pool_end = bounds
            self.stats["bscr_assets"] += 1
            self.add_records(
                data[pool_start:pool_end],
                locator,
                physical_path,
                leaf_name,
                "bscr_string_pool",
                base_offset=pool_start,
            )
            return
        normalized_locator = locator.replace("\\", "/")
        normalized_physical = physical_path.replace("\\", "/")
        if (
            Path(leaf_name).suffix.lower() in TEXT_LEAF_EXTENSIONS
            and (
                normalized_locator in self.vetted_identities
                or normalized_physical in DIRECT_TEXT_ASSETS
            )
        ):
            self.add_records(data, locator, physical_path, leaf_name, "nul_eucjp_scan")

    def run(self) -> None:
        candidates: list[Path] = []
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(self.root).as_posix()
            ext = path.suffix.lower()
            if ext in {".vol", ".cxd"} or relative in DIRECT_TEXT_ASSETS:
                candidates.append(path)
        candidates.sort(key=lambda item: item.relative_to(self.root).as_posix().lower())
        self.stats["physical_candidates"] = len(candidates)
        for index, path in enumerate(candidates, 1):
            relative = path.relative_to(self.root).as_posix()
            try:
                data = path.read_bytes()
                self.physical_hashes[relative] = sha256(data)
                self.process_logical(data, relative, relative, path.name)
            except (OSError, ValueError) as exc:
                self.errors.append({"locator": relative, "error": str(exc)})
            if index % 100 == 0:
                print(f"[{index}/{len(candidates)}] strings={len(self.records)}", file=sys.stderr)

        # Context is attached only after collection so neighboring semantic
        # units are stable and independent of traversal implementation details.
        by_locator: dict[str, list[dict[str, object]]] = defaultdict(list)
        for record in self.records:
            by_locator[str(record["logical_locator"])].append(record)
        for locator_records in by_locator.values():
            locator_records.sort(key=lambda item: int(item["offset"]))
            for index, record in enumerate(locator_records):
                record["previous_source"] = locator_records[index - 1]["source_text"] if index else None
                record["next_source"] = locator_records[index + 1]["source_text"] if index + 1 < len(locator_records) else None
        self.records.sort(key=lambda item: (str(item["physical_path"]).lower(), str(item["logical_locator"]), int(item["offset"])))


def write_outputs(builder: CatalogBuilder, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog = {
        "schema": "arf-korean-localization-catalog-v1",
        "game_id": "RPJJ99",
        "source_language": "ja-JP",
        "target_language": "ko-KR",
        "encoding": "EUC-JP with embedded control bytes",
        "translation_engine_policy": "Codex internal models only",
        "source_root": str(builder.root.resolve()),
        "record_count": len(builder.records),
        "records": builder.records,
    }
    (output_dir / "text_catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    columns = [
        "id",
        "surface",
        "physical_path",
        "logical_locator",
        "leaf_name",
        "extraction_mode",
        "offset_hex",
        "byte_length",
        "capacity_to_nul",
        "source_text",
        "previous_source",
        "next_source",
        "translation_ko",
        "status",
        "review_status",
    ]
    with (output_dir / "text_catalog.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(builder.records)

    summary = {
        "schema": "arf-text-inventory-summary-v1",
        "source_root": str(builder.root.resolve()),
        "statistics": dict(sorted(builder.stats.items())),
        "record_count": len(builder.records),
        "unique_source_text_count": len({str(record["source_text"]) for record in builder.records}),
        "physical_source_count": len(builder.physical_hashes),
        "error_count": len(builder.errors),
        "errors": builder.errors,
    }
    (output_dir / "text_catalog_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "physical_source_hashes.json").write_text(
        json.dumps(builder.physical_hashes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--vetted-payloads",
        type=Path,
        default=Path(__file__).with_name("rtdp_agent") / "audit" / "localization_payloads.json",
    )
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"not a directory: {args.root}")
    builder = CatalogBuilder(args.root, args.vetted_payloads)
    builder.run()
    write_outputs(builder, args.output_dir)
    print(
        json.dumps(
            {
                "records": len(builder.records),
                "errors": len(builder.errors),
                "output": str(args.output_dir.resolve()),
            },
            ensure_ascii=False,
        )
    )
    return 0 if not builder.errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
