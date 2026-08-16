#!/usr/bin/env python3
"""Arc Rise Fantasia (RPJJ99) non-BSCR text-table parser/writer.

The game uses EUC-JP text plus low-byte runtime tokens.  This tool deliberately
accepts replacement *bytes* (`replacement_hex`) rather than trying to encode
Korean with a standard codec: the Korean font/code-point mapping is a separate
pipeline contract.  Fixed tables are rewritten in place; quest.bin is the one
supported pointer-pooled/resizable table.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


GAME_ID = "RPJJ99"
HEX_RE = re.compile(r"^[0-9A-Fa-f]*$")


@dataclass(frozen=True)
class Field:
    name: str
    offset: int
    capacity: int


@dataclass(frozen=True)
class FixedSchema:
    name: str
    record_size: int
    count: int
    fields: tuple[Field, ...]
    header_size: int = 0


FIXED: dict[str, FixedSchema] = {
    "item.bin": FixedSchema(
        "item", 255, 772,
        # The secondary C-string ends at relative byte 178. Bytes 179..180
        # are the big-endian item ID, not string padding.
        (Field("name", 0, 17), Field("description_primary", 17, 81), Field("description_secondary", 98, 81)),
    ),
    # Relative byte 20 is an opaque shop flag (0x02 for tailor entries).
    "shop.bin": FixedSchema("shop", 86, 47, (Field("name", 0, 20),)),
    "dragon.bin": FixedSchema(
        "dragon", 279, 13,
        (
            Field("name", 0, 24), Field("skill_name", 24, 48), Field("lore", 72, 97),
            Field("passive_description", 169, 49), Field("battle_description", 218, 49),
        ),
    ),
    "treasure.bin": FixedSchema("treasure", 49, 256, (Field("display_name", 23, 21),)),
    "magic.bin": FixedSchema(
        "magic", 164, 49,
        (Field("menu_name", 0, 20), Field("battle_name", 20, 40), Field("description", 60, 80)),
    ),
    "special.bin": FixedSchema(
        # Relative byte 105 (description-relative 83) is an effect flag.
        "special", 144, 76, (Field("name", 0, 22), Field("description", 22, 83)),
    ),
    "operation.bin": FixedSchema(
        "operation", 120, 8, (Field("name", 0, 24), Field("description", 24, 96)),
    ),
    "ability.bin": FixedSchema(
        "ability", 146, 250, (Field("name", 0, 21), Field("description", 21, 81)),
    ),
    "todo.dat": FixedSchema(
        "todo", 144, 208, (Field("lead", 16, 64), Field("objective", 80, 64)),
    ),
    "help.bin": FixedSchema(
        # Bytes 343..346 are a four-byte record metadata word.
        "help", 347, 380, (Field("title", 0, 21), Field("description", 21, 322)),
    ),
    "monster_book.bin": FixedSchema(
        # Relative byte 35 is the monster category, not name padding.
        "monster_book", 644, 274, (Field("name", 0, 35), Field("location", 260, 96)),
    ),
}


def validate_fixed_schema(schema: FixedSchema) -> None:
    """Reject overlapping or out-of-record fixed-string declarations."""
    previous_end = 0
    for spec in sorted(schema.fields, key=lambda value: value.offset):
        if spec.offset < previous_end:
            raise ValueError(f"{schema.name}: overlapping field {spec.name}")
        if spec.capacity <= 0 or spec.offset + spec.capacity > schema.record_size:
            raise ValueError(f"{schema.name}: invalid field geometry for {spec.name}")
        previous_end = spec.offset + spec.capacity


def validate_item_record_ids(data: bytes) -> None:
    """The item table stores its big-endian record ID at bytes 179..180."""
    schema = FIXED["item.bin"]
    expected_size = schema.record_size * schema.count
    if len(data) != expected_size:
        raise ValueError(f"item: size {len(data)} != expected {expected_size}")
    bad: list[tuple[int, int]] = []
    for index in range(schema.count):
        value = struct.unpack_from(">H", data, index * schema.record_size + 179)[0]
        if value != index:
            bad.append((index, value))
            if len(bad) == 8:
                break
    if bad:
        raise ValueError(f"item: record ID invariant failed: {bad}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def contains_japanese(text: str) -> bool:
    return any(
        0x3000 <= ord(c) <= 0x30FF
        or 0x3400 <= ord(c) <= 0x4DBF
        or 0x4E00 <= ord(c) <= 0x9FFF
        or 0xF900 <= ord(c) <= 0xFAFF
        or 0xFF01 <= ord(c) <= 0xFFEF
        for c in text
    )


def control_signature(raw: bytes) -> list[str]:
    """Return ordered runtime tokens, including their inline ASCII operands."""
    result: list[str] = []
    i = 0
    while i < len(raw):
        value = raw[i]
        if value in (0x09, 0x0A, 0x0D):
            i += 1
            continue
        if 0x01 <= value <= 0x1F or value == 0x7F:
            end = i + 1
            if value in (0x13, 0x15) and end + 2 <= len(raw) and all(
                chr(b) in "0123456789ABCDEFabcdef" for b in raw[end : end + 2]
            ):
                end += 2
            elif value == 0x1F:
                while end < len(raw) and 0x30 <= raw[end] <= 0x39:
                    end += 1
            result.append(raw[i:end].hex().upper())
            i = end
            continue
        # Skip one ASCII byte or one valid EUC-JP unit.
        if 0xA1 <= value <= 0xFE and i + 1 < len(raw) and 0xA1 <= raw[i + 1] <= 0xFE:
            i += 2
        elif value == 0x8E and i + 1 < len(raw):
            i += 2
        elif value == 0x8F and i + 2 < len(raw):
            i += 3
        else:
            i += 1
    return result


def render_mixed(raw: bytes) -> str:
    """Render EUC-JP text while making non-layout controls explicit."""
    out: list[str] = []
    i = 0
    while i < len(raw):
        b = raw[i]
        if b == 0x0A:
            out.append("\n")
            i += 1
            continue
        if b == 0x09:
            out.append("\t")
            i += 1
            continue
        if b == 0x0D:
            out.append("\r")
            i += 1
            continue
        if 0x01 <= b <= 0x1F or b == 0x7F:
            end = i + 1
            if b in (0x13, 0x15) and end + 2 <= len(raw) and all(
                chr(x) in "0123456789ABCDEFabcdef" for x in raw[end : end + 2]
            ):
                end += 2
            elif b == 0x1F:
                while end < len(raw) and 0x30 <= raw[end] <= 0x39:
                    end += 1
            token = raw[i:end].hex().upper()
            out.append(f"<${token}>")
            i = end
            continue
        if 0x20 <= b <= 0x7E:
            out.append(chr(b))
            i += 1
            continue
        length = 0
        if 0xA1 <= b <= 0xFE and i + 1 < len(raw) and 0xA1 <= raw[i + 1] <= 0xFE:
            length = 2
        elif b == 0x8E and i + 1 < len(raw):
            length = 2
        elif b == 0x8F and i + 2 < len(raw):
            length = 3
        if length:
            try:
                out.append(raw[i : i + length].decode("euc_jp"))
                i += length
                continue
            except UnicodeDecodeError:
                pass
        out.append(f"<#{b:02X}>")
        i += 1
    return "".join(out)


def field_raw(data: bytes, start: int, capacity: int) -> tuple[bytes, bool]:
    blob = data[start : start + capacity]
    end = blob.find(b"\0")
    if end < 0:
        return blob, False
    return blob[:end], True


def unit(
    schema: str,
    record: int | str,
    field_name: str,
    absolute_offset: int,
    capacity: int | None,
    raw: bytes,
    nul_terminated: bool,
    **extra: Any,
) -> dict[str, Any]:
    ident = f"{schema}:{record}:{field_name}"
    text = render_mixed(raw)
    result: dict[str, Any] = {
        "id": ident,
        "schema": schema,
        "record": record,
        "field": field_name,
        "offset": absolute_offset,
        "offset_hex": f"0x{absolute_offset:X}",
        "capacity": capacity,
        "byte_length": len(raw),
        "headroom": None if capacity is None else capacity - len(raw) - 1,
        "nul_terminated": nul_terminated,
        "raw_hex": raw.hex().upper(),
        "source_text": text,
        "has_japanese": contains_japanese(text),
        "control_signature": control_signature(raw),
        "replacement_hex": "",
    }
    result.update(extra)
    return result


def parse_fixed(data: bytes, schema: FixedSchema) -> list[dict[str, Any]]:
    validate_fixed_schema(schema)
    expected = schema.header_size + schema.record_size * schema.count
    if len(data) != expected:
        raise ValueError(f"{schema.name}: size {len(data)} != expected {expected}")
    if schema.name == "item":
        validate_item_record_ids(data)
    units: list[dict[str, Any]] = []
    for index in range(schema.count):
        base = schema.header_size + index * schema.record_size
        for spec in schema.fields:
            raw, terminated = field_raw(data, base + spec.offset, spec.capacity)
            units.append(unit(schema.name, index, spec.name, base + spec.offset, spec.capacity, raw, terminated))
    return units


def parse_copin(data: bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(data) < 4:
        raise ValueError("copin: truncated")
    count = struct.unpack_from(">I", data, 0)[0]
    if count == 0 or (len(data) - 4) % count:
        raise ValueError("copin: count/size mismatch")
    stride = (len(data) - 4) // count
    if (count, stride) != (30, 156):
        raise ValueError(f"copin: unexpected count/stride {count}/{stride}")
    schema = FixedSchema("copin", stride, count, (Field("name", 0, 16), Field("description", 16, 128)), 4)
    return parse_fixed(data, schema), {"record_count_header": count, "record_size": stride, "metadata_offset": 144}


def parse_btem(data: bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(data) < 0x1A4 or data[:4] != b"BTEM":
        raise ValueError("btem: bad/truncated magic")
    data_offset = struct.unpack_from(">I", data, 8)[0]
    if not (0x10 <= data_offset <= len(data) - 35):
        raise ValueError("btem: invalid data/name offset")
    raw, terminated = field_raw(data, data_offset, 35)
    return [unit("btem", 0, "display_name", data_offset, 35, raw, terminated)], {
        "header_size_word": struct.unpack_from(">I", data, 4)[0],
        "data_offset": data_offset,
        "name_capacity": 35,
    }


def tutorial_record_starts(data: bytes) -> list[int]:
    starts: list[int] = []
    for pos in range(0, len(data) - 0x154 + 1, 0x10):
        if data[pos + 0x0C : pos + 0x10] != b"\xFF\xFF\xFF\xFF":
            continue
        msg, mt = field_raw(data, pos + 0x14, 0x100)
        speaker, st = field_raw(data, pos + 0x114, 0x40)
        # Real records have a readable speaker and at least one Japanese unit.
        msg_text, speaker_text = render_mixed(msg), render_mixed(speaker)
        if mt and st and (contains_japanese(msg_text) or contains_japanese(speaker_text)):
            starts.append(pos)
    return starts


def parse_tutorial(data: bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(data) != 0x17000:
        raise ValueError(f"tutorial: size {len(data)} != 0x17000")
    starts = tutorial_record_starts(data)
    if len(starts) != 190:
        raise ValueError(f"tutorial: detected {len(starts)} records, expected 190")
    units: list[dict[str, Any]] = []
    for index, pos in enumerate(starts):
        msg, mt = field_raw(data, pos + 0x14, 0x100)
        speaker, st = field_raw(data, pos + 0x114, 0x40)
        key = f"0x{pos:X}"
        units.append(unit("btl_tutorial", key, "message", pos + 0x14, 0x100, msg, mt, ordinal=index))
        units.append(unit("btl_tutorial", key, "speaker", pos + 0x114, 0x40, speaker, st, ordinal=index))
    deltas = [b - a for a, b in zip(starts, starts[1:])]
    return units, {
        "active_record_count": len(starts),
        "message_offset": 0x14,
        "message_capacity": 0x100,
        "speaker_offset": 0x114,
        "speaker_capacity": 0x40,
        "common_record_stride": 0x170,
        "alternate_final_stride": 0x160,
        "observed_start_deltas": sorted(set(deltas)),
    }


def parse_sscr_header(data: bytes) -> dict[str, Any]:
    if len(data) < 0x10 or data[:4] != b"SSCR":
        raise ValueError("not SSCR")
    data_start, table_count, relocation_count, duplicate_start = struct.unpack_from(">IHHI", data, 4)
    if duplicate_start != data_start or table_count < 1:
        raise ValueError("invalid SSCR header")
    descriptor_words = 2 * table_count - 1
    descriptors = list(struct.unpack_from(f">{descriptor_words}I", data, 0x10))
    relocation_start = 0x10 + descriptor_words * 4
    relocation_end = relocation_start + relocation_count * 8
    if relocation_end > data_start:
        raise ValueError("SSCR relocation table overlaps data")
    relocations = [struct.unpack_from(">II", data, relocation_start + i * 8) for i in range(relocation_count)]
    name_offsets = descriptors[0::2]
    boundaries = descriptors[1::2]
    names = []
    for off in name_offsets:
        end = data.find(b"\0", off, data_start)
        if not (relocation_end <= off < end < data_start):
            raise ValueError("invalid SSCR table-name pointer")
        names.append(data[off:end].decode("ascii"))
    table_starts = [data_start] + boundaries
    table_ends = boundaries + [len(data)]
    return {
        "data_start": data_start,
        "table_count": table_count,
        "relocation_count": relocation_count,
        "descriptors": descriptors,
        "relocation_start": relocation_start,
        "relocation_end": relocation_end,
        "relocations": relocations,
        "table_names": names,
        "table_starts": table_starts,
        "table_ends": table_ends,
    }


QUEST_ROLES = ("title", "requester", "description", "objective_1", "objective_2", "objective_3")


def parse_quest(data: bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    h = parse_sscr_header(data)
    if h["table_names"] != ["_quest_tbl"] or h["relocation_count"] != 480:
        raise ValueError("quest: unexpected SSCR layout")
    pairs: list[tuple[int, int]] = h["relocations"]
    values = [v for _, v in pairs]
    targets = [t for t, _ in pairs]
    if values != sorted(values) or len(values) != len(set(values)):
        raise ValueError("quest: string pointers are not unique/monotonic")
    pool_start = values[0]
    if pool_start != 0x2D20:
        raise ValueError(f"quest: pool starts at 0x{pool_start:X}, expected 0x2D20")
    if len(pairs) % 6:
        raise ValueError("quest: relocation count is not divisible by six")
    record_count = len(pairs) // 6
    if record_count != 80:
        raise ValueError("quest: expected 80 records")
    units: list[dict[str, Any]] = []
    cursor_expected = pool_start
    pool_gaps: list[dict[str, int]] = []
    for index in range(record_count):
        record_base = h["data_start"] + index * 0x60
        for field_index, role in enumerate(QUEST_ROLES):
            relocation_index = index * 6 + field_index
            target, value = pairs[relocation_index]
            expected_target = record_base + 4 + field_index * 4
            if target != expected_target:
                raise ValueError(f"quest: relocation target 0x{target:X} != 0x{expected_target:X}")
            if value < cursor_expected:
                raise ValueError("quest: string pool pointers overlap or move backward")
            if value > cursor_expected:
                if any(data[cursor_expected:value]):
                    raise ValueError("quest: nonzero unreferenced bytes in string-pool gap")
                pool_gaps.append({"start": cursor_expected, "end": value, "size": value - cursor_expected})
            end = data.find(b"\0", value)
            if end < 0:
                raise ValueError("quest: unterminated pooled string")
            raw = data[value:end]
            units.append(
                unit(
                    "quest", index, role, value, None, raw, True,
                    relocation_index=relocation_index,
                    relocation_entry_offset=h["relocation_start"] + relocation_index * 8,
                    pointer_target=target,
                    in_place_capacity=(
                        (pairs[relocation_index + 1][1] if relocation_index + 1 < len(pairs) else len(data)) - value
                    ),
                )
            )
            cursor_expected = end + 1
    if cursor_expected < len(data):
        if any(data[cursor_expected:]):
            raise ValueError("quest: nonzero unreferenced tail after string pool")
        pool_gaps.append({"start": cursor_expected, "end": len(data), "size": len(data) - cursor_expected})
    elif cursor_expected > len(data):
        raise ValueError("quest: string pool extends beyond file")
    return units, {
        "sscr_table_name": "_quest_tbl",
        "record_count": record_count,
        "record_size": 0x60,
        "pointer_fields": [4, 8, 12, 16, 20, 24],
        "relocation_count": h["relocation_count"],
        "relocation_entry_size": 8,
        "pool_start": pool_start,
        "pool_end": len(data),
        "pool_gap_count": len(pool_gaps),
        "pool_gap_bytes": sum(g["size"] for g in pool_gaps),
        "pool_gaps": pool_gaps,
        "fixed_size_mode": "each replacement <= its original byte length; pointers and file size unchanged",
        "resizable_at_table_level": True,
    }


def parse_chat(data: bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    h = parse_sscr_header(data)
    if h["table_names"] != ["_msg_tbl", "_trigger"]:
        raise ValueError("chat: unexpected SSCR tables")
    start, end = h["table_starts"][0], h["table_ends"][0]
    if end - start != 400 * 44:
        raise ValueError("chat: _msg_tbl is not 400 x 44")
    units: list[dict[str, Any]] = []
    for index in range(400):
        pos = start + index * 44
        raw, terminated = field_raw(data, pos, 43)
        units.append(unit("chat", index, "title", pos, 43, raw, terminated))
    return units, {
        "sscr_tables": h["table_names"],
        "message_table_start": start,
        "message_table_end": end,
        "record_count": 400,
        "record_size": 44,
        "title_capacity": 43,
        "record_flag_offset": 43,
        "trigger_table_start": h["table_starts"][1],
        "relocation_count": h["relocation_count"],
    }


def detect_and_parse(path: Path, data: bytes, forced: str | None = None) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    name = path.name.lower()
    choice = forced.lower() if forced else ""
    if choice == "quest" or (not choice and name == "quest.bin"):
        units, meta = parse_quest(data); return "quest", units, meta
    if choice == "chat" or (not choice and name == "chat.bin"):
        units, meta = parse_chat(data); return "chat", units, meta
    if choice == "copin" or (not choice and name == "copin.dat"):
        units, meta = parse_copin(data); return "copin", units, meta
    if choice == "btl_tutorial" or (not choice and name == "btl_tutorial.vld"):
        units, meta = parse_tutorial(data); return "btl_tutorial", units, meta
    if choice == "btem" or (not choice and data[:4] == b"BTEM"):
        units, meta = parse_btem(data); return "btem", units, meta
    schema = FIXED.get(name)
    if choice:
        schema = next((s for s in FIXED.values() if s.name == choice), None)
    if schema:
        units = parse_fixed(data, schema)
        meta = {
            "record_count": schema.count,
            "record_size": schema.record_size,
            "header_size": schema.header_size,
            "fields": [{"name": f.name, "offset": f.offset, "capacity": f.capacity} for f in schema.fields],
        }
        if schema.name == "treasure":
            meta["internal_resource_key"] = {"offset": 0, "capacity": 23, "translatable": False}
        if schema.name == "help":
            meta["record_flag"] = {"offset": 346, "size": 1, "translatable": False}
        return schema.name, units, meta
    raise ValueError(f"unable to detect schema for {path.name}; use --schema")


def make_catalog(path: Path, data: bytes, forced: str | None = None) -> dict[str, Any]:
    schema, units, meta = detect_and_parse(path, data, forced)
    return {
        "format": "arf-rpjj99-non-bscr-table-v1",
        "game_id": GAME_ID,
        "source_path": str(path.resolve()),
        "source_size": len(data),
        "source_sha256": sha256(data),
        "schema": schema,
        "encoding_contract": "raw bytes; source renders as EUC-JP; Korean replacements use custom font-map bytes",
        "writer_contract": "set replacement_hex only; runtime controls and NUL are validated",
        "metadata": meta,
        "unit_count": len(units),
        "nonempty_count": sum(bool(u["raw_hex"]) for u in units),
        "japanese_unit_count": sum(bool(u["has_japanese"]) for u in units),
        "units": units,
    }


def decode_replacement(unit_data: dict[str, Any], use_original_when_blank: bool) -> bytes | None:
    text = str(unit_data.get("replacement_hex", "")).replace(" ", "").replace("_", "")
    exact_unterminated_noop = False
    if not text:
        if not use_original_when_blank:
            return None
        text = str(unit_data["raw_hex"])
        exact_unterminated_noop = not bool(unit_data.get("nul_terminated", True))
    if len(text) % 2 or not HEX_RE.fullmatch(text):
        raise ValueError(f"{unit_data['id']}: replacement_hex is not even-length hexadecimal")
    raw = bytes.fromhex(text)
    if b"\0" in raw:
        raise ValueError(f"{unit_data['id']}: replacement contains NUL")
    expected = list(unit_data.get("control_signature", []))
    actual = control_signature(raw)
    if actual != expected:
        raise ValueError(f"{unit_data['id']}: control signature changed {expected} -> {actual}")
    cap = unit_data.get("capacity")
    if cap is not None and len(raw) >= int(cap):
        # Preserve a malformed original full-width field byte-for-byte during
        # a no-op round trip. A real replacement must still leave room for NUL.
        if exact_unterminated_noop and len(raw) == int(cap):
            return raw
        raise ValueError(f"{unit_data['id']}: {len(raw)} bytes does not fit C-string capacity {cap}")
    return raw


def apply_fixed(data: bytes, units: Iterable[dict[str, Any]], rebuild_all: bool) -> bytes:
    out = bytearray(data)
    for item in units:
        raw = decode_replacement(item, rebuild_all)
        if raw is None:
            continue
        start, capacity = int(item["offset"]), int(item["capacity"])
        # Preserve padding/opaque bytes for exact no-op; only clear the former
        # string through its first NUL when a value actually changes.
        original = bytes.fromhex(str(item["raw_hex"]))
        if raw == original:
            out[start : start + len(raw)] = raw
            continue
        # Rewrite only the old/new C-string span. Bytes after the source's
        # first NUL are preserved because some records carry opaque metadata
        # near a string buffer boundary.
        clear_end = start + max(len(original), len(raw)) + 1
        if clear_end > start + capacity:
            raise ValueError(f"{item['id']}: C-string rewrite exceeds capacity")
        out[start:clear_end] = b"\0" * (clear_end - start)
        out[start : start + len(raw)] = raw
    return bytes(out)


def apply_quest(data: bytes, catalog: dict[str, Any], rebuild_all: bool, fixed_size: bool = False) -> bytes:
    parsed = parse_sscr_header(data)
    units = list(catalog["units"])
    if len(units) != parsed["relocation_count"]:
        raise ValueError("quest: catalog/relocation count mismatch")
    if fixed_size:
        out = bytearray(data)
        for item in units:
            raw = decode_replacement(item, rebuild_all)
            if raw is None:
                continue
            original = bytes.fromhex(str(item["raw_hex"]))
            if raw == original:
                continue
            capacity = int(item["in_place_capacity"])
            if len(raw) >= capacity:
                raise ValueError(
                    f"{item['id']}: {len(raw)} bytes does not fit fixed quest slot capacity {capacity}"
                )
            start = int(item["offset"])
            out[start : start + capacity] = b"\0" * capacity
            out[start : start + len(raw)] = raw
        return bytes(out)

    pool_start = int(catalog["metadata"]["pool_start"])
    prefix = bytearray(data[:pool_start])
    pool = bytearray()
    for index, item in enumerate(units):
        raw = decode_replacement(item, True if rebuild_all else False)
        if raw is None:
            raw = bytes.fromhex(str(item["raw_hex"]))
        pointer = pool_start + len(pool)
        relocation_entry = int(item["relocation_entry_offset"])
        struct.pack_into(">I", prefix, relocation_entry + 4, pointer)
        pool.extend(raw)
        pool.append(0)
    return bytes(prefix + pool)


def apply_catalog(
    data: bytes,
    catalog: dict[str, Any],
    rebuild_all: bool = False,
    quest_fixed_size: bool = False,
) -> bytes:
    if sha256(data) != catalog["source_sha256"]:
        raise ValueError("source SHA-256 does not match catalog")
    schema = str(catalog["schema"])
    _, baseline_units, _ = detect_and_parse(Path(f"source.{schema}"), data, schema)
    supplied_units = list(catalog.get("units", []))
    if len(supplied_units) != len(baseline_units):
        raise ValueError("catalog unit count does not match parsed source")
    immutable = (
        "id", "schema", "record", "field", "offset", "capacity", "raw_hex",
        "control_signature", "relocation_index", "relocation_entry_offset", "pointer_target",
        "in_place_capacity",
    )
    for expected, supplied in zip(baseline_units, supplied_units):
        for key in immutable:
            if key in expected and supplied.get(key) != expected.get(key):
                raise ValueError(f"{expected['id']}: immutable catalog field {key} changed")
    if catalog["schema"] == "quest":
        return apply_quest(data, catalog, rebuild_all, fixed_size=quest_fixed_size)
    output = apply_fixed(data, catalog["units"], rebuild_all)
    allowed = bytearray(len(data))
    for item in baseline_units:
        start = int(item["offset"])
        capacity = int(item["capacity"])
        allowed[start : start + capacity] = b"\1" * capacity
    outside = [
        index
        for index, (before, after) in enumerate(zip(data, output, strict=True))
        if before != after and not allowed[index]
    ]
    if outside:
        raise ValueError(f"{schema}: changes outside declared string buffers: {outside[:16]}")
    if schema == "item":
        validate_item_record_ids(output)
    return output


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    p_catalog = sub.add_parser("catalog")
    p_catalog.add_argument("input", type=Path)
    p_catalog.add_argument("output", type=Path)
    p_catalog.add_argument("--schema")
    p_apply = sub.add_parser("apply")
    p_apply.add_argument("input", type=Path)
    p_apply.add_argument("catalog", type=Path)
    p_apply.add_argument("output", type=Path)
    p_apply.add_argument(
        "--quest-fixed-size",
        action="store_true",
        help="for quest.bin, preserve pointers/file size and require each replacement to fit its original slot",
    )
    p_noop = sub.add_parser("noop")
    p_noop.add_argument("input", type=Path)
    p_noop.add_argument("output", type=Path)
    p_noop.add_argument("--catalog-output", type=Path)
    p_noop.add_argument("--schema")
    ns = ap.parse_args()

    if ns.command == "catalog":
        data = ns.input.read_bytes()
        catalog = make_catalog(ns.input, data, ns.schema)
        write_json(ns.output, catalog)
        print(json.dumps({"schema": catalog["schema"], "units": catalog["unit_count"], "output": str(ns.output)}, ensure_ascii=False))
        return 0
    if ns.command == "apply":
        data = ns.input.read_bytes()
        catalog = json.loads(ns.catalog.read_text(encoding="utf-8"))
        output = apply_catalog(data, catalog, rebuild_all=False, quest_fixed_size=ns.quest_fixed_size)
        ns.output.parent.mkdir(parents=True, exist_ok=True)
        ns.output.write_bytes(output)
        print(json.dumps({"size": len(output), "sha256": sha256(output), "output": str(ns.output)}, ensure_ascii=False))
        return 0
    if ns.command == "noop":
        data = ns.input.read_bytes()
        catalog = make_catalog(ns.input, data, ns.schema)
        output = apply_catalog(data, catalog, rebuild_all=True)
        ns.output.parent.mkdir(parents=True, exist_ok=True)
        ns.output.write_bytes(output)
        if ns.catalog_output:
            write_json(ns.catalog_output, catalog)
        exact = output == data
        print(json.dumps({"schema": catalog["schema"], "byte_exact": exact, "sha256": sha256(output)}, ensure_ascii=False))
        return 0 if exact else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
