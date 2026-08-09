#!/usr/bin/env python3
"""Build the complete RPJJ99 Korean Riivolution overlay from approved inputs.

This is the top-level application orchestrator.  It deliberately performs no
translation.  It binds an approved 29,777-unit TM to all 84,761 catalog
occurrences, rebuilds the 606 translated BSCR leaves and the 15 non-system
table leaves, delegates all RTDP/LZ10 writes to ``container_tool.js``, merges
the independently built Sys payload/font result plus the cumulative image-UI
``nowloading.wtm`` member, and adds the 43 image-UI physical replacements.  It
emits a hash-bound Riivolution tree containing exactly 655 physical files: the
612 text targets plus 43 non-overlapping direct image targets.

The original extracted disc tree and source RVZ are read-only inputs.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


GAME_ID = "RPJJ99"
TRANSLATION_POLICY = "Codex internal models only"
EXPECTED_TM_UNITS = 29_777
EXPECTED_OCCURRENCES = 84_761
EXPECTED_TEXT_PHYSICAL_FILES = 612
EXPECTED_IMAGE_REINSERTION_TARGETS = 44
EXPECTED_IMAGE_DIRECT_FILES = 43
EXPECTED_FINAL_PHYSICAL_FILES = 655
EXPECTED_BSCR_LEAVES = 606
EXPECTED_BSCR_OCCURRENCES = 79_076
EXPECTED_SYSTEM_OCCURRENCES = 5_236
# The canonical audit includes one table-specific whole-field binding for the
# scanner suffix occurrence inside ability:218:name, so all 5,236 catalog
# occurrences now have a structurally verified application field.
EXPECTED_SYSTEM_TABLE_FIELDS = 5_236
EXPECTED_SYSTEM_TM_UNITS = 4_343
EXPECTED_NON_SYSTEM_TABLE_PAYLOADS = 15
EXPECTED_NON_SYSTEM_TABLE_OCCURRENCES = 449
EXPECTED_LOCAL_CONTAINERS = 608  # Event 377 + Map 229 + Btl 1 + minigame 1

SYSTEM_CONTAINER_TABLES = (
    "item.bin",
    "shop.bin",
    "dragon.bin",
    "treasure.bin",
    "magic.bin",
    "special.bin",
    "operation.bin",
    "quest.bin",
    "ability.bin",
    "chat.bin",
    "todo.dat",
)
SYSTEM_DIRECT_TABLES = ("help.bin", "monster_book.bin")
SYSTEM_TABLES = SYSTEM_CONTAINER_TABLES + SYSTEM_DIRECT_TABLES
SYSTEM_FONTS = tuple(f"EUC28-{page}.wtm" for page in range(9))

SURFACE_OCCURRENCE_COUNTS = {
    "system_database": 5_236,
    "battle_text": 389,
    "misc_text": 60,
    "event_script": 4_786,
    "map_dialogue": 74_290,
}
PRIMARY_SURFACE_TM_COUNTS = {
    "system_database": 4_343,
    "battle_text": 172,
    "misc_text": 60,
    "event_script": 4_259,
    "map_dialogue": 20_943,
}

ENTRY_TOKEN_RE = re.compile(r"::(\d{4}):")


class BuildError(RuntimeError):
    """Raised when an input or rebuilt artifact violates the release contract."""


@dataclass(frozen=True)
class RtdpEntry:
    index: int
    name: str
    name_raw: bytes
    size: int
    relative_offset: int
    absolute_offset: int
    end_offset: int


@dataclass
class LeafBuild:
    kind: str
    physical_path: str
    logical_locator: str
    leaf_name: str
    entry_path: tuple[int, ...]
    source_sha256: str
    output_sha256: str
    source_size: int
    output_size: int
    occurrence_count: int
    tm_ids: set[str]
    output_path: Path
    replacement_manifest: Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise BuildError(f"cannot import tool: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BuildError(message)


def encode_translation(text: str, codebook: dict[str, Any], encoder_module) -> bytes:
    """Encode approved text exactly; every non-EUC-JP glyph must be in codebook."""
    return encoder_module.encode_text(text, codebook)


def rel_posix(path: Path, base: Path) -> str:
    return path.resolve().relative_to(base.resolve()).as_posix()


def validate_disc_relative_path(value: str, label: str) -> str:
    require("\\" not in value, f"{label}: disc path must use forward slashes: {value}")
    parsed = PurePosixPath(value)
    require(not parsed.is_absolute(), f"{label}: absolute disc path forbidden: {value}")
    require(value == parsed.as_posix(), f"{label}: non-canonical disc path: {value}")
    require(all(part not in {"", ".", ".."} for part in parsed.parts), f"{label}: unsafe disc path: {value}")
    return value


def validate_leaf_name(value: str, label: str) -> str:
    require(value == PurePosixPath(value).name and "\\" not in value, f"{label}: unsafe leaf name: {value}")
    return value


def parse_rtdp(data: bytes, label: str) -> tuple[list[RtdpEntry], list[bytes]]:
    require(len(data) >= 0x20, f"{label}: RTDP header truncated")
    require(data[:4] == b"RTDP", f"{label}: RTDP magic missing")
    eoh = int.from_bytes(data[4:8], "big")
    count = int.from_bytes(data[8:12], "big")
    table_end = 0x20 + count * 40
    require(table_end <= eoh <= len(data), f"{label}: invalid RTDP EOH")
    entries: list[RtdpEntry] = []
    payloads: list[bytes] = []
    for index in range(count):
        pos = 0x20 + index * 40
        name_raw = bytes(data[pos : pos + 32])
        name = name_raw.split(b"\0", 1)[0].decode("latin1")
        size = int.from_bytes(data[pos + 32 : pos + 36], "big")
        relative = int.from_bytes(data[pos + 36 : pos + 40], "big")
        start = eoh + relative
        end = start + size
        require(start <= end <= len(data), f"{label}: RTDP entry {index} out of range")
        entries.append(
            RtdpEntry(index, name, name_raw, size, relative, start, end)
        )
        payloads.append(bytes(value ^ 0x55 for value in data[start:end]))
    return entries, payloads


def extract_leaf(
    physical_data: bytes,
    physical_path: str,
    entry_path: tuple[int, ...],
    lz10_module,
) -> tuple[bytes, list[str]]:
    data = physical_data
    if physical_path.lower().endswith(".cxd"):
        require(data[:1] == b"\x10", f"{physical_path}: expected LZ10 wrapper")
        data = lz10_module.decompress_lz10(data)
    names: list[str] = []
    for depth, index in enumerate(entry_path):
        entries, payloads = parse_rtdp(data, f"{physical_path}:{'/'.join(map(str, entry_path[:depth]))}")
        require(0 <= index < len(entries), f"{physical_path}: entry path index {index} out of range")
        names.append(entries[index].name)
        data = payloads[index]
        if depth + 1 < len(entry_path):
            require(data[:4] == b"RTDP", f"{physical_path}: descendant {entry_path[:depth+1]} is not RTDP")
    return data, names


def entry_path_from_locator(physical_path: str, logical_locator: str) -> tuple[int, ...]:
    require(
        logical_locator == physical_path or logical_locator.startswith(physical_path + "::"),
        f"locator does not begin with physical path: {logical_locator}",
    )
    return tuple(int(value) for value in ENTRY_TOKEN_RE.findall(logical_locator))


def leaf_output_path(application_dir: Path, physical_path: str, entry_path: tuple[int, ...], leaf_name: str) -> Path:
    suffix = "direct" if not entry_path else "_".join(f"{value:04d}" for value in entry_path)
    return application_dir / "leaf_payloads" / (physical_path + ".d") / f"{suffix}__{leaf_name}"


def replacement_json_path(application_dir: Path, kind: str, physical_path: str, leaf_name: str) -> Path:
    return application_dir / f"{kind}_replacements" / (physical_path + ".d") / f"{leaf_name}.json"


def validate_and_index_inputs(args: argparse.Namespace) -> dict[str, Any]:
    memory = json.loads(args.translation_memory.read_text(encoding="utf-8"))
    catalog = json.loads(args.text_catalog.read_text(encoding="utf-8"))
    codebook = json.loads(args.codebook.read_text(encoding="utf-8"))
    physical_hashes = json.loads(args.physical_hashes.read_text(encoding="utf-8"))

    require(memory.get("game_id") == GAME_ID, "translation memory game_id mismatch")
    require(memory.get("translation_engine_policy") == TRANSLATION_POLICY, "TM translation policy mismatch")
    units = list(memory.get("units", []))
    require(len(units) == EXPECTED_TM_UNITS, f"expected {EXPECTED_TM_UNITS} TM units, got {len(units)}")
    require(catalog.get("game_id") == GAME_ID, "text catalog game_id mismatch")
    records = list(catalog.get("records", []))
    require(len(records) == EXPECTED_OCCURRENCES, f"expected {EXPECTED_OCCURRENCES} occurrences, got {len(records)}")
    require(codebook.get("format") == "arc-rise-fantasia-korean-codebook-v1", "unsupported codebook")

    tm_ids: set[str] = set()
    occurrence_to_tm: dict[str, dict[str, Any]] = {}
    primary_counts: Counter[str] = Counter()
    for unit in units:
        tm_id = str(unit.get("tm_id", ""))
        require(tm_id and tm_id not in tm_ids, f"duplicate or empty TM id: {tm_id}")
        tm_ids.add(tm_id)
        primary_counts[str(unit.get("primary_surface"))] += 1
        require(unit.get("review_status") == "approved", f"TM unit is not approved: {tm_id}")
        require(str(unit.get("translation_ko", "")).strip() != "", f"TM unit has blank translation: {tm_id}")
        occurrences = list(unit.get("occurrence_ids", []))
        require(len(occurrences) == int(unit.get("occurrence_count", -1)), f"TM occurrence count mismatch: {tm_id}")
        for occurrence_id in occurrences:
            occurrence_id = str(occurrence_id)
            require(occurrence_id not in occurrence_to_tm, f"occurrence assigned twice: {occurrence_id}")
            occurrence_to_tm[occurrence_id] = unit
    require(dict(primary_counts) == PRIMARY_SURFACE_TM_COUNTS, f"unexpected primary-surface TM counts: {dict(primary_counts)}")

    record_by_id: dict[str, dict[str, Any]] = {}
    surface_counts: Counter[str] = Counter()
    physical_paths: set[str] = set()
    for record in records:
        occurrence_id = str(record.get("id", ""))
        require(occurrence_id and occurrence_id not in record_by_id, f"duplicate catalog occurrence: {occurrence_id}")
        record_by_id[occurrence_id] = record
        surface_counts[str(record.get("surface"))] += 1
        physical_paths.add(validate_disc_relative_path(str(record.get("physical_path")), "text catalog"))
        validate_leaf_name(str(record.get("leaf_name")), "text catalog")
    require(dict(surface_counts) == SURFACE_OCCURRENCE_COUNTS, f"unexpected occurrence surface counts: {dict(surface_counts)}")
    require(len(physical_paths) == EXPECTED_TEXT_PHYSICAL_FILES, f"expected {EXPECTED_TEXT_PHYSICAL_FILES} text physical targets, got {len(physical_paths)}")
    require(set(record_by_id) == set(occurrence_to_tm), "TM occurrence IDs and catalog IDs are not an exact set match")

    missing_hashes = sorted(physical_paths - set(physical_hashes))
    require(not missing_hashes, f"physical hash inventory missing targets: {missing_hashes[:10]}")
    source_hash_errors: list[str] = []
    for ordinal, physical_path in enumerate(sorted(physical_paths, key=str.lower), 1):
        source = args.source_root / Path(physical_path)
        if not source.is_file():
            source_hash_errors.append(f"missing:{physical_path}")
            continue
        actual = sha256_file(source).lower()
        expected = str(physical_hashes[physical_path]).lower()
        if actual != expected:
            source_hash_errors.append(f"hash:{physical_path}:{expected}:{actual}")
        if ordinal % 100 == 0:
            print(f"[input hashes] {ordinal}/{len(physical_paths)}", flush=True)
    require(not source_hash_errors, "source physical validation failed: " + "; ".join(source_hash_errors[:10]))

    return {
        "memory": memory,
        "catalog": catalog,
        "codebook": codebook,
        "physical_hashes": physical_hashes,
        "units": units,
        "records": records,
        "occurrence_to_tm": occurrence_to_tm,
        "record_by_id": record_by_id,
        "physical_paths": physical_paths,
    }


def build_bscr_leaves(
    args: argparse.Namespace,
    indexed: dict[str, Any],
    application_dir: Path,
    bscr_module,
    encoder_module,
    lz10_module,
    occurrence_rows: dict[str, dict[str, Any]],
) -> list[LeafBuild]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in indexed["records"]:
        if record["extraction_mode"] == "bscr_string_pool":
            grouped[str(record["logical_locator"])].append(record)
    require(len(grouped) == EXPECTED_BSCR_LEAVES, f"expected {EXPECTED_BSCR_LEAVES} translated BSCR leaves, got {len(grouped)}")
    require(sum(map(len, grouped.values())) == EXPECTED_BSCR_OCCURRENCES, "BSCR occurrence total mismatch")

    results: list[LeafBuild] = []
    for ordinal, logical_locator in enumerate(sorted(grouped), 1):
        records = sorted(grouped[logical_locator], key=lambda item: int(item["offset"]))
        physical_path = str(records[0]["physical_path"])
        leaf_name = str(records[0]["leaf_name"])
        require(all(str(item["physical_path"]) == physical_path for item in records), f"mixed physical paths: {logical_locator}")
        entry_path = entry_path_from_locator(physical_path, logical_locator)
        require(entry_path, f"BSCR must be inside a container: {logical_locator}")
        source_physical = (args.source_root / Path(physical_path)).read_bytes()
        source_leaf, entry_names = extract_leaf(source_physical, physical_path, entry_path, lz10_module)
        require(entry_names[-1] == leaf_name, f"leaf name mismatch for {logical_locator}: {entry_names[-1]} != {leaf_name}")
        parsed = bscr_module.parse_bscr(source_leaf)
        require(parsed.file_name == leaf_name, f"BSCR header name mismatch: {logical_locator}")
        pool_hash = sha256_bytes(source_leaf[parsed.pool_start : parsed.bytecode_start])
        catalog_pool_hashes = {str(item["leaf_sha256"]).upper() for item in records}
        require(catalog_pool_hashes == {pool_hash}, f"catalog BSCR pool hash mismatch: {logical_locator}")

        replacements: dict[int, bytes] = {}
        replacement_rows: list[dict[str, Any]] = []
        tm_ids: set[str] = set()
        strings_by_relative = parsed.string_by_offset
        for record in records:
            absolute = int(record["offset"])
            relative = absolute - parsed.pool_start
            require(relative in strings_by_relative, f"catalog offset is not a BSCR string start: {logical_locator}@{absolute:#x}")
            source_string = strings_by_relative[relative]
            expected_raw = bytes.fromhex(str(record["raw_hex"]))
            require(source_string.raw == expected_raw, f"BSCR source raw mismatch: {logical_locator}@{absolute:#x}")
            tm_unit = indexed["occurrence_to_tm"][str(record["id"])]
            target = encode_translation(
                str(tm_unit["translation_ko"]), indexed["codebook"], encoder_module
            )
            require(b"\0" not in target, f"encoded NUL: {tm_unit['tm_id']}")
            require(relative not in replacements, f"duplicate BSCR replacement offset: {logical_locator}@{relative:#x}")
            replacements[relative] = target
            tm_ids.add(str(tm_unit["tm_id"]))
            replacement_rows.append(
                {
                    "offset": relative,
                    "absolute_source_offset": absolute,
                    "source_raw_hex": expected_raw.hex().upper(),
                    "raw_hex": target.hex().upper(),
                    "occurrence_id": record["id"],
                    "tm_id": tm_unit["tm_id"],
                }
            )
            occurrence_rows[str(record["id"])] = {
                "occurrence_id": record["id"],
                "tm_id": tm_unit["tm_id"],
                "surface": record["surface"],
                "physical_path": physical_path,
                "logical_locator": logical_locator,
                "leaf_name": leaf_name,
                "application_kind": "bscr_variable_pool",
                "catalog_offset": absolute,
                "leaf_replacement_offset": relative,
                "source_raw_sha256": sha256_bytes(expected_raw),
                "target_raw_sha256": sha256_bytes(target),
                "target_byte_length": len(target),
            }

        output_leaf = parsed.rebuild(replacements)
        verified = bscr_module.parse_bscr(output_leaf)
        require(len(verified.strings) == len(parsed.strings), f"BSCR string count changed: {logical_locator}")
        for old_record, new_record in zip(parsed.strings, verified.strings, strict=True):
            expected = replacements.get(old_record.relative_offset, old_record.raw)
            require(new_record.raw == expected, f"BSCR reparse mismatch: {logical_locator}@{old_record.relative_offset:#x}")
        require(output_leaf != source_leaf, f"translated BSCR is byte-exact source: {logical_locator}")

        output_path = leaf_output_path(application_dir, physical_path, entry_path, leaf_name)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(output_leaf)
        replacement_path = replacement_json_path(application_dir, "bscr", physical_path, leaf_name)
        write_json(
            replacement_path,
            {
                "format": "arf-bscr-replacements-v1",
                "game_id": GAME_ID,
                "logical_locator": logical_locator,
                "source_bscr_sha256": sha256_bytes(source_leaf),
                "output_bscr_sha256": sha256_bytes(output_leaf),
                "replacements": replacement_rows,
            },
        )
        results.append(
            LeafBuild(
                "bscr",
                physical_path,
                logical_locator,
                leaf_name,
                entry_path,
                sha256_bytes(source_leaf),
                sha256_bytes(output_leaf),
                len(source_leaf),
                len(output_leaf),
                len(records),
                tm_ids,
                output_path,
                replacement_path,
            )
        )
        if ordinal % 25 == 0 or ordinal == len(grouped):
            print(f"[BSCR leaves] {ordinal}/{len(grouped)}", flush=True)
    return results


def non_system_catalog_path(table_catalog_dir: Path, leaf_name: str) -> Path:
    lower = leaf_name.lower()
    if lower == "btl_tutorial.vld":
        return table_catalog_dir / "btl_tutorial.json"
    if lower == "copin.dat":
        return table_catalog_dir / "copin.json"
    if re.fullmatch(r"btl_stat_party\d{2}b?\.bin", lower):
        return table_catalog_dir / f"{Path(leaf_name).stem}.json"
    raise BuildError(f"unsupported non-system table leaf: {leaf_name}")


def match_table_unit(record: dict[str, Any], units: list[dict[str, Any]]) -> tuple[dict[str, Any], bytes, bytes]:
    record_offset = int(record["offset"])
    record_raw = bytes.fromhex(str(record["raw_hex"]))
    exact = [
        unit
        for unit in units
        if int(unit["offset"]) == record_offset
        and bytes.fromhex(str(unit["raw_hex"])) == record_raw
    ]
    if len(exact) == 1:
        return exact[0], b"", b""
    candidates: list[tuple[dict[str, Any], bytes, bytes]] = []
    for unit in units:
        unit_offset = int(unit["offset"])
        unit_raw = bytes.fromhex(str(unit["raw_hex"]))
        relative = unit_offset - record_offset
        if relative < 0 or relative + len(unit_raw) > len(record_raw):
            continue
        if record_raw[relative : relative + len(unit_raw)] != unit_raw:
            continue
        candidates.append(
            (unit, record_raw[:relative], record_raw[relative + len(unit_raw) :])
        )
    require(len(candidates) == 1, f"table occurrence has {len(candidates)} unit matches: {record['id']}")
    return candidates[0]


def strip_scanner_boundary(
    encoded_full_target: bytes,
    prefix: bytes,
    suffix: bytes,
    occurrence_id: str,
) -> bytes:
    require(encoded_full_target.startswith(prefix), f"translated scanner prefix changed: {occurrence_id}")
    require(encoded_full_target.endswith(suffix), f"translated scanner suffix changed: {occurrence_id}")
    start = len(prefix)
    end = len(encoded_full_target) - len(suffix) if suffix else len(encoded_full_target)
    require(end >= start, f"translated scanner boundary overlaps: {occurrence_id}")
    return encoded_full_target[start:end]


def build_non_system_table_leaves(
    args: argparse.Namespace,
    indexed: dict[str, Any],
    application_dir: Path,
    table_module,
    encoder_module,
    lz10_module,
    occurrence_rows: dict[str, dict[str, Any]],
) -> list[LeafBuild]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in indexed["records"]:
        if record["surface"] in {"battle_text", "misc_text"} and record["extraction_mode"] == "nul_eucjp_scan":
            grouped[str(record["logical_locator"])].append(record)
    require(len(grouped) == EXPECTED_NON_SYSTEM_TABLE_PAYLOADS, f"expected {EXPECTED_NON_SYSTEM_TABLE_PAYLOADS} non-system payloads, got {len(grouped)}")
    require(sum(map(len, grouped.values())) == EXPECTED_NON_SYSTEM_TABLE_OCCURRENCES, "non-system table occurrence total mismatch")

    results: list[LeafBuild] = []
    used_catalogs: set[Path] = set()
    for logical_locator in sorted(grouped):
        records = sorted(grouped[logical_locator], key=lambda item: int(item["offset"]))
        physical_path = str(records[0]["physical_path"])
        leaf_name = str(records[0]["leaf_name"])
        entry_path = entry_path_from_locator(physical_path, logical_locator)
        source_physical = (args.source_root / Path(physical_path)).read_bytes()
        if entry_path:
            source_leaf, entry_names = extract_leaf(source_physical, physical_path, entry_path, lz10_module)
            require(entry_names[-1] == leaf_name, f"table leaf name mismatch: {logical_locator}")
        else:
            source_leaf = source_physical
        catalog_path = non_system_catalog_path(args.table_catalog_dir, leaf_name)
        require(catalog_path.is_file(), f"missing table catalog: {catalog_path}")
        require(catalog_path not in used_catalogs, f"table catalog reused: {catalog_path}")
        used_catalogs.add(catalog_path)
        table_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        require(str(table_catalog.get("source_sha256", "")).upper() == sha256_bytes(source_leaf), f"table catalog source hash mismatch: {logical_locator}")
        catalog_leaf_hashes = {str(item["leaf_sha256"]).upper() for item in records}
        require(catalog_leaf_hashes == {sha256_bytes(source_leaf)}, f"text catalog leaf hash mismatch: {logical_locator}")

        modified_catalog = copy.deepcopy(table_catalog)
        units = list(modified_catalog["units"])
        used_unit_ids: set[str] = set()
        expected_targets: dict[str, bytes] = {}
        tm_ids: set[str] = set()
        mapping_rows: list[dict[str, Any]] = []
        for record in records:
            unit, prefix, suffix = match_table_unit(record, units)
            unit_id = str(unit["id"])
            require(unit_id not in used_unit_ids, f"table unit matched more than once: {logical_locator}:{unit_id}")
            used_unit_ids.add(unit_id)
            tm_unit = indexed["occurrence_to_tm"][str(record["id"])]
            encoded_full = encode_translation(
                str(tm_unit["translation_ko"]), indexed["codebook"], encoder_module
            )
            target = strip_scanner_boundary(encoded_full, prefix, suffix, str(record["id"]))
            require(b"\0" not in target, f"encoded NUL in table target: {record['id']}")
            unit["replacement_hex"] = target.hex().upper()
            unit["replacement_tm_id"] = tm_unit["tm_id"]
            unit["replacement_occurrence_id"] = record["id"]
            unit["scanner_prefix_hex"] = prefix.hex().upper()
            unit["scanner_suffix_hex"] = suffix.hex().upper()
            expected_targets[unit_id] = target
            tm_ids.add(str(tm_unit["tm_id"]))
            mapping_rows.append(
                {
                    "occurrence_id": record["id"],
                    "tm_id": tm_unit["tm_id"],
                    "table_unit_id": unit_id,
                    "scanner_prefix_hex": prefix.hex().upper(),
                    "scanner_suffix_hex": suffix.hex().upper(),
                    "replacement_hex": target.hex().upper(),
                }
            )
            occurrence_rows[str(record["id"])] = {
                "occurrence_id": record["id"],
                "tm_id": tm_unit["tm_id"],
                "surface": record["surface"],
                "physical_path": physical_path,
                "logical_locator": logical_locator,
                "leaf_name": leaf_name,
                "application_kind": "non_system_fixed_table",
                "catalog_offset": int(record["offset"]),
                "table_unit_id": unit_id,
                "source_raw_sha256": sha256_bytes(bytes.fromhex(str(record["raw_hex"]))),
                "target_raw_sha256": sha256_bytes(target),
                "target_byte_length": len(target),
                "scanner_prefix_bytes": len(prefix),
                "scanner_suffix_bytes": len(suffix),
            }

        output_leaf = table_module.apply_catalog(source_leaf, modified_catalog, rebuild_all=False)
        verified_catalog = table_module.make_catalog(Path(leaf_name), output_leaf, str(modified_catalog["schema"]))
        verified_by_id = {str(unit["id"]): unit for unit in verified_catalog["units"]}
        original_by_id = {str(unit["id"]): unit for unit in table_catalog["units"]}
        for unit_id, expected in expected_targets.items():
            actual = bytes.fromhex(str(verified_by_id[unit_id]["raw_hex"]))
            require(actual == expected, f"table replacement verification failed: {logical_locator}:{unit_id}")
        for unit_id, original in original_by_id.items():
            if unit_id in expected_targets:
                continue
            require(verified_by_id[unit_id]["raw_hex"] == original["raw_hex"], f"untargeted table unit changed: {logical_locator}:{unit_id}")
        require(output_leaf != source_leaf, f"translated table is byte-exact source: {logical_locator}")

        output_path = leaf_output_path(application_dir, physical_path, entry_path, leaf_name)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(output_leaf)
        replacement_path = replacement_json_path(application_dir, "table", physical_path, leaf_name)
        modified_catalog["application_mapping"] = mapping_rows
        modified_catalog["output_sha256"] = sha256_bytes(output_leaf)
        write_json(replacement_path, modified_catalog)
        verification_path = application_dir / "table_verification" / (physical_path + ".d") / f"{leaf_name}.json"
        write_json(verification_path, verified_catalog)
        results.append(
            LeafBuild(
                "table",
                physical_path,
                logical_locator,
                leaf_name,
                entry_path,
                sha256_bytes(source_leaf),
                sha256_bytes(output_leaf),
                len(source_leaf),
                len(output_leaf),
                len(records),
                tm_ids,
                output_path,
                replacement_path,
            )
        )
        print(f"[table leaf] {logical_locator}: {len(records)} occurrences", flush=True)
    return results


def container_manifest_path(application_dir: Path, physical_path: str) -> Path:
    return application_dir / "container_edits" / (physical_path + ".json")


def container_report_path(application_dir: Path, physical_path: str) -> Path:
    return application_dir / "container_reports" / (physical_path + ".json")


def make_container_manifest(application_dir: Path, physical_path: str, leaves: list[LeafBuild]) -> Path:
    manifest_path = container_manifest_path(application_dir, physical_path)
    edits = []
    for leaf in sorted(leaves, key=lambda item: item.entry_path):
        require(leaf.entry_path, f"direct leaf cannot be placed in container manifest: {leaf.logical_locator}")
        replacement_relative = os.path.relpath(leaf.output_path, manifest_path.parent).replace("\\", "/")
        edits.append(
            {
                "entryPath": list(leaf.entry_path),
                "expectedSha256": leaf.source_sha256.lower(),
                "replacementFile": replacement_relative,
                "logicalLocator": leaf.logical_locator,
            }
        )
    write_json(manifest_path, {"format": "arf-container-edits-v1", "edits": edits})
    return manifest_path


def run_one_container(
    node: Path,
    container_tool: Path,
    source: Path,
    edits: Path,
    output: Path,
    report: Path,
) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [str(node), str(container_tool), "rebuild", str(source), str(edits), str(output), str(report)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode:
        raise BuildError(
            f"container rebuild failed ({source}):\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return json.loads(report.read_text(encoding="utf-8"))


def rebuild_local_physical_files(
    args: argparse.Namespace,
    application_dir: Path,
    staging_files: Path,
    leaves: list[LeafBuild],
    lz10_module,
) -> tuple[list[dict[str, Any]], dict[str, list[LeafBuild]]]:
    grouped: dict[str, list[LeafBuild]] = defaultdict(list)
    direct: list[LeafBuild] = []
    for leaf in leaves:
        if leaf.entry_path:
            grouped[leaf.physical_path].append(leaf)
        else:
            direct.append(leaf)
    require(len(grouped) == EXPECTED_LOCAL_CONTAINERS, f"expected {EXPECTED_LOCAL_CONTAINERS} local containers, got {len(grouped)}")
    require(len(direct) == 1 and direct[0].physical_path == "Btl/btl_tutorial.vld", "unexpected direct non-system table set")

    jobs: list[tuple[str, Path, Path, Path, Path]] = []
    for physical_path in sorted(grouped, key=str.lower):
        manifest = make_container_manifest(application_dir, physical_path, grouped[physical_path])
        jobs.append(
            (
                physical_path,
                args.source_root / Path(physical_path),
                manifest,
                staging_files / Path(physical_path),
                container_report_path(application_dir, physical_path),
            )
        )

    reports_by_path: dict[str, dict[str, Any]] = {}
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        future_to_path = {
            executor.submit(
                run_one_container,
                args.node,
                args.container_tool,
                source,
                manifest,
                output,
                report,
            ): physical_path
            for physical_path, source, manifest, output, report in jobs
        }
        completed_count = 0
        for future in concurrent.futures.as_completed(future_to_path):
            physical_path = future_to_path[future]
            reports_by_path[physical_path] = future.result()
            completed_count += 1
            if completed_count % 25 == 0 or completed_count == len(jobs):
                print(f"[containers] {completed_count}/{len(jobs)}", flush=True)

    direct_leaf = direct[0]
    direct_output = staging_files / Path(direct_leaf.physical_path)
    direct_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(direct_leaf.output_path, direct_output)

    physical_reports: list[dict[str, Any]] = []
    for physical_path in sorted(grouped, key=str.lower):
        output = staging_files / Path(physical_path)
        report = reports_by_path[physical_path]
        expected_paths = {tuple(leaf.entry_path): leaf for leaf in grouped[physical_path]}
        audit = report.get("editAudit")
        if audit is None and "rtdpTree" in report:
            audit = report["rtdpTree"].get("editAudit")
        require(isinstance(audit, list), f"container report lacks edit audit: {physical_path}")
        actual_paths = {tuple(int(v) for v in item["entryPath"]): item for item in audit}
        require(set(actual_paths) == set(expected_paths), f"container edit path mismatch: {physical_path}")
        output_data = output.read_bytes()
        for entry_path, leaf in expected_paths.items():
            item = actual_paths[entry_path]
            require(str(item["oldSha256"]).upper() == leaf.source_sha256, f"container old leaf hash mismatch: {leaf.logical_locator}")
            require(str(item["newSha256"]).upper() == leaf.output_sha256, f"container new leaf hash mismatch: {leaf.logical_locator}")
            extracted, _ = extract_leaf(output_data, physical_path, entry_path, lz10_module)
            require(extracted == leaf.output_path.read_bytes(), f"re-extracted leaf mismatch: {leaf.logical_locator}")
        physical_reports.append(
            {
                "physical_path": physical_path,
                "source_sha256": sha256_file(args.source_root / Path(physical_path)),
                "output_sha256": sha256_file(output),
                "source_size": (args.source_root / Path(physical_path)).stat().st_size,
                "output_size": output.stat().st_size,
                "edited_leaf_count": len(expected_paths),
                "container_report": rel_posix(container_report_path(application_dir, physical_path), args.output_dir),
            }
        )
    physical_reports.append(
        {
            "physical_path": direct_leaf.physical_path,
            "source_sha256": direct_leaf.source_sha256,
            "output_sha256": direct_leaf.output_sha256,
            "source_size": direct_leaf.source_size,
            "output_size": direct_leaf.output_size,
            "edited_leaf_count": 1,
            "container_report": None,
        }
    )
    print(f"[containers] elapsed={time.monotonic()-started:.1f}s", flush=True)
    return physical_reports, grouped


def validate_system_inputs(args: argparse.Namespace) -> dict[str, Any]:
    proof = json.loads(args.system_proof.read_text(encoding="utf-8"))
    require(proof.get("game_id") == GAME_ID, "system proof game_id mismatch")
    require(proof.get("translation_engine_policy") == TRANSLATION_POLICY, "system proof translation policy mismatch")
    require(proof.get("external_translation_models_or_apis_used") is False, "system proof used an external model/API")
    require(proof.get("valid") is True, "system table application proof is not valid")
    require(str(proof.get("translation_memory_sha256", "")).upper() == sha256_file(args.translation_memory), "system proof TM hash mismatch")
    require(str(proof.get("codebook_sha256", "")).upper() == sha256_file(args.codebook), "system proof codebook hash mismatch")
    require(int(proof.get("approved_system_tm_units", -1)) == EXPECTED_SYSTEM_TM_UNITS, "system proof TM-unit count mismatch")
    require(int(proof.get("applied_unique_tm_units", -1)) == EXPECTED_SYSTEM_TM_UNITS, "system proof applied-unit count mismatch")
    require(int(proof.get("replacement_table_fields", -1)) == EXPECTED_SYSTEM_TABLE_FIELDS, "system proof structural-field count mismatch")
    require(int(proof.get("payloads_rebuilt", -1)) == len(SYSTEM_TABLES), "system proof payload count mismatch")

    payloads: dict[str, Path] = {}
    for name in SYSTEM_TABLES:
        path = args.system_payload_dir / name
        require(path.is_file(), f"missing final system payload: {path}")
        payloads[name] = path
    proof_by_name: dict[str, dict[str, Any]] = {}
    for report in proof.get("payloads", []):
        output_path = Path(str(report.get("output_path", "")))
        proof_by_name[output_path.name] = report
    require(set(proof_by_name) == set(SYSTEM_TABLES), f"system proof payload names mismatch: {sorted(proof_by_name)}")
    for name, path in payloads.items():
        require(str(proof_by_name[name].get("output_sha256", "")).upper() == sha256_file(path), f"system payload hash differs from proof: {name}")

    fonts: dict[str, Path] = {}
    for name in SYSTEM_FONTS:
        path = args.font_dir / name
        require(path.is_file(), f"missing final injected font: {path}")
        fonts[name] = path
    return {"proof": proof, "payloads": payloads, "fonts": fonts}


def project_path(project_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def validate_image_inputs(
    args: argparse.Namespace,
    indexed: dict[str, Any],
    project_root: Path,
) -> dict[str, Any]:
    manifest = json.loads(args.image_manifest.read_text(encoding="utf-8"))
    require(manifest.get("schema") == "arf-image-ui-reinsertion-manifest-v1", "unsupported image reinsertion manifest")
    require(manifest.get("original_rvz_modified") is False, "image lane reports original RVZ modification")
    targets = list(manifest.get("targets", []))
    require(len(targets) == EXPECTED_IMAGE_REINSERTION_TARGETS, f"expected {EXPECTED_IMAGE_REINSERTION_TARGETS} image reinsertion targets, got {len(targets)}")
    require(int(manifest.get("replacement_target_count", -1)) == len(targets), "image manifest target count mismatch")

    validation_path = project_path(project_root, str(manifest.get("validation", "")))
    require(validation_path.resolve() == args.image_validation.resolve(), "image validation path differs from manifest")
    validation = json.loads(args.image_validation.read_text(encoding="utf-8"))
    require(validation.get("schema") == "arf-image-ui-structural-validation-v1", "unsupported image validation schema")
    require(int(validation.get("asset_checks", -1)) == 48, "image structural asset-check count mismatch")
    require(int(validation.get("passed", -1)) == 48 and int(validation.get("failed", -1)) == 0, "image structural validation is not 48/48 PASS")
    require(not validation.get("failures"), "image structural validation contains failures")
    require(all(item.get("pass") is True for item in validation.get("checks", [])), "an image structural check did not pass")
    title_check = validation.get("title_archive_check", {})
    require(title_check.get("pass") is True, "title archive validation did not pass")

    image_root = args.image_manifest.resolve().parent
    payload_hashes = {str(key).replace("\\", "/"): str(value).upper() for key, value in manifest.get("payload_tree_sha256", {}).items()}
    require(len(payload_hashes) >= len(targets), "image payload hash tree is incomplete")
    for relative, expected_hash in sorted(payload_hashes.items()):
        payload = image_root / Path(relative)
        require(payload.is_file(), f"image payload tree member missing: {payload}")
        require(sha256_file(payload) == expected_hash, f"image payload tree hash mismatch: {relative}")

    checks_by_patched: dict[Path, dict[str, Any]] = {}
    for check in validation.get("checks", []):
        patched = project_path(project_root, str(check.get("patched", ""))).resolve()
        checks_by_patched[patched] = check

    direct: dict[str, Path] = {}
    system_leaf: Path | None = None
    target_rows: list[dict[str, Any]] = []
    target_names: set[str] = set()
    for target in targets:
        target_name = str(target.get("target", ""))
        require(target_name and target_name not in target_names, f"duplicate image reinsertion target: {target_name}")
        target_names.add(target_name)
        payload = project_path(project_root, str(target.get("payload", ""))).resolve()
        require(payload.is_file(), f"image target payload missing: {payload}")
        require(payload.is_relative_to(image_root), f"image target payload escapes image root: {payload}")
        payload_relative = payload.relative_to(image_root).as_posix()
        require(payload_hashes.get(payload_relative) == sha256_file(payload), f"image target payload is not hash-bound: {payload_relative}")

        if target_name == "Sys/system.vol::entry 53 nowloading.wtm":
            require(system_leaf is None, "duplicate cumulative system image leaf")
            system_leaf = payload
            target_rows.append({"target": target_name, "payload": str(payload), "kind": "cumulative_system_leaf", "entry_path": [53]})
            continue
        require("::" not in target_name, f"unsupported non-physical image target: {target_name}")
        validate_disc_relative_path(target_name, "image manifest")
        require(target_name not in direct, f"duplicate direct image physical target: {target_name}")
        source = args.source_root / Path(target_name)
        require(source.is_file(), f"image physical source missing: {source}")
        direct[target_name] = payload

        if target_name in {"Title/title.vol", "Sys/title.vol"}:
            require(sha256_file(source) == str(title_check.get("original_sha256", "")).upper(), f"title source hash mismatch: {target_name}")
            require(sha256_file(payload) == str(title_check.get("patched_sha256", "")).upper(), f"title payload hash mismatch: {target_name}")
        else:
            check = checks_by_patched.get(payload)
            require(check is not None, f"image structural check missing for payload: {payload}")
            require(sha256_file(source) == str(check.get("original_sha256", "")).upper(), f"image physical source hash mismatch: {target_name}")
            require(sha256_file(payload) == str(check.get("patched_sha256", "")).upper(), f"image physical payload hash mismatch: {target_name}")
        target_rows.append({"target": target_name, "payload": str(payload), "kind": "direct_physical"})

    require(len(direct) == EXPECTED_IMAGE_DIRECT_FILES, f"expected {EXPECTED_IMAGE_DIRECT_FILES} direct image files, got {len(direct)}")
    require(system_leaf is not None, "image manifest lacks cumulative system.vol entry 53")
    require(set(direct).isdisjoint(indexed["physical_paths"]), "direct image targets collide with text physical targets")
    require("Sys/system.vol" in indexed["physical_paths"], "text allowlist lacks cumulative Sys/system.vol")

    source_system = (args.source_root / "Sys/system.vol").read_bytes()
    entries, payloads = parse_rtdp(source_system, "Sys/system.vol image preflight")
    require(len(entries) > 53 and entries[53].name == "nowloading.wtm", "Sys/system.vol entry 53 identity mismatch")
    nowloading_check = checks_by_patched.get(system_leaf)
    require(nowloading_check is not None, "nowloading structural check missing")
    require(sha256_bytes(payloads[53]) == str(nowloading_check.get("original_sha256", "")).upper(), "source nowloading leaf hash mismatch")
    require(sha256_file(system_leaf) == str(nowloading_check.get("patched_sha256", "")).upper(), "patched nowloading leaf hash mismatch")

    full_physical_paths = set(indexed["physical_paths"]) | set(direct)
    require(len(full_physical_paths) == EXPECTED_FINAL_PHYSICAL_FILES, f"expected {EXPECTED_FINAL_PHYSICAL_FILES} final physical files, got {len(full_physical_paths)}")
    return {
        "manifest": manifest,
        "validation": validation,
        "direct": direct,
        "system_leaf": system_leaf,
        "physical_paths": full_physical_paths,
        "targets": target_rows,
    }


def stage_image_direct_files(
    args: argparse.Namespace,
    staging_files: Path,
    image_inputs: dict[str, Any],
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for physical_path, payload in sorted(image_inputs["direct"].items(), key=lambda item: item[0].lower()):
        destination = staging_files / Path(physical_path)
        require(not destination.exists(), f"image direct target collides with an existing staged file: {physical_path}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(payload, destination)
        require(sha256_file(destination) == sha256_file(payload), f"staged image payload copy mismatch: {physical_path}")
        reports.append(
            {
                "physical_path": physical_path,
                "source_sha256": sha256_file(args.source_root / Path(physical_path)),
                "output_sha256": sha256_file(destination),
                "source_size": (args.source_root / Path(physical_path)).stat().st_size,
                "output_size": destination.stat().st_size,
                "payload": str(payload),
            }
        )
    require(len(reports) == EXPECTED_IMAGE_DIRECT_FILES, "staged image direct-file count mismatch")
    return reports


def locate_supplied_system_file(base: Path, name: str) -> Path:
    direct = base / name
    nested = base / "Sys" / name
    if direct.is_file():
        return direct
    if nested.is_file():
        return nested
    raise BuildError(f"supplied system staging lacks {name}: {base}")


def merge_or_build_system(
    args: argparse.Namespace,
    application_dir: Path,
    staging_files: Path,
    system_inputs: dict[str, Any],
    image_inputs: dict[str, Any],
) -> dict[str, Any]:
    source_system = args.source_root / "Sys/system.vol"
    target_system = staging_files / "Sys/system.vol"
    target_system.parent.mkdir(parents=True, exist_ok=True)

    replacements = {
        **system_inputs["fonts"],
        **{name: system_inputs["payloads"][name] for name in SYSTEM_CONTAINER_TABLES},
        "nowloading.wtm": image_inputs["system_leaf"],
    }
    copied_dir = application_dir / "system_inputs"
    copied_dir.mkdir(parents=True, exist_ok=True)
    system_report_path = application_dir / "system_vol_rebuild_report.json"

    if args.system_files_dir:
        # A supplied cumulative text/font system.vol is accepted only when all
        # twenty non-image replacement hashes already match.  We then apply the
        # nowloading member as the final child edit, never overwriting it with a
        # separately built archive.
        base_system = locate_supplied_system_file(args.system_files_dir, "system.vol")
        base_data = base_system.read_bytes()
        entries, payloads = parse_rtdp(base_data, "supplied cumulative Sys/system.vol")
        by_name = {entry.name: entry for entry in entries}
        require(len(by_name) == len(entries), "supplied system.vol contains duplicate names")
        for name, source in replacements.items():
            if name == "nowloading.wtm":
                continue
            require(name in by_name, f"supplied system.vol missing expected entry: {name}")
            require(sha256_bytes(payloads[by_name[name].index]) == sha256_file(source), f"supplied system.vol is not cumulative for {name}")
        now_entry = by_name.get("nowloading.wtm")
        require(now_entry is not None and now_entry.index == 53, "supplied system.vol nowloading identity mismatch")
        copied = copied_dir / "nowloading.wtm"
        shutil.copy2(image_inputs["system_leaf"], copied)
        manifest_path = application_dir / "system_vol_edits.json"
        write_json(
            manifest_path,
            {
                "format": "arf-container-edits-v1",
                "edits": [
                    {
                        "entryPath": [53],
                        "expectedSha256": sha256_bytes(payloads[53]).lower(),
                        "replacementFile": os.path.relpath(copied, application_dir).replace("\\", "/"),
                        "name": "nowloading.wtm",
                    }
                ],
            },
        )
        run_one_container(args.node, args.container_tool, base_system, manifest_path, target_system, system_report_path)
        mode = "cumulative_nowloading_over_supplied_text_font_system"
    else:
        source_data = source_system.read_bytes()
        entries, payloads = parse_rtdp(source_data, "Sys/system.vol")
        by_name: dict[str, RtdpEntry] = {}
        for entry in entries:
            require(entry.name not in by_name, f"duplicate system.vol entry name: {entry.name}")
            by_name[entry.name] = entry
        edits = []
        for name, source in sorted(replacements.items()):
            require(name in by_name, f"system.vol missing expected entry: {name}")
            entry = by_name[name]
            if name == "nowloading.wtm":
                require(entry.index == 53, "source system.vol nowloading entry index changed")
            copied = copied_dir / name
            shutil.copy2(source, copied)
            edits.append(
                {
                    "entryPath": [entry.index],
                    "expectedSha256": sha256_bytes(payloads[entry.index]).lower(),
                    "replacementFile": os.path.relpath(copied, application_dir).replace("\\", "/"),
                    "name": name,
                }
            )
        manifest_path = application_dir / "system_vol_edits.json"
        write_json(manifest_path, {"format": "arf-container-edits-v1", "edits": sorted(edits, key=lambda item: item["entryPath"])})
        run_one_container(args.node, args.container_tool, source_system, manifest_path, target_system, system_report_path)
        mode = "rebuilt_cumulatively_from_final_tables_fonts_and_nowloading"

    for name in SYSTEM_DIRECT_TABLES:
        shutil.copy2(system_inputs["payloads"][name], staging_files / "Sys" / name)

    output_system_data = target_system.read_bytes()
    entries, payloads = parse_rtdp(output_system_data, "staged Sys/system.vol")
    by_name = {entry.name: (entry, payloads[entry.index]) for entry in entries}
    require(len(by_name) == len(entries), "staged system.vol contains duplicate names")
    target_inputs = replacements
    verified_entries = []
    for name, path in sorted(target_inputs.items()):
        require(name in by_name, f"staged system.vol missing replacement entry: {name}")
        actual = sha256_bytes(by_name[name][1])
        expected = sha256_file(path)
        require(actual == expected, f"staged system entry hash mismatch: {name}")
        verified_entries.append({"name": name, "index": by_name[name][0].index, "sha256": actual})
    for name in SYSTEM_DIRECT_TABLES:
        require(sha256_file(staging_files / "Sys" / name) == sha256_file(system_inputs["payloads"][name]), f"staged direct system payload mismatch: {name}")

    return {
        "mode": mode,
        "source_system_sha256": sha256_file(source_system),
        "output_system_sha256": sha256_file(target_system),
        "output_system_size": target_system.stat().st_size,
        "verified_internal_entries": verified_entries,
        "cumulative_nowloading_entry": 53,
        "direct_payloads": [
            {"name": name, "sha256": sha256_file(staging_files / "Sys" / name)}
            for name in SYSTEM_DIRECT_TABLES
        ],
        "rebuild_report": rel_posix(system_report_path, args.output_dir) if system_report_path else None,
    }


def add_system_occurrence_rows(indexed: dict[str, Any], occurrence_rows: dict[str, dict[str, Any]]) -> None:
    count = 0
    for record in indexed["records"]:
        if record["surface"] != "system_database":
            continue
        tm_unit = indexed["occurrence_to_tm"][str(record["id"])]
        occurrence_rows[str(record["id"])] = {
            "occurrence_id": record["id"],
            "tm_id": tm_unit["tm_id"],
            "surface": record["surface"],
            "physical_path": record["physical_path"],
            "logical_locator": record["logical_locator"],
            "leaf_name": record["leaf_name"],
            "application_kind": "verified_system_application_proof",
            "catalog_offset": int(record["offset"]),
            "source_raw_sha256": sha256_bytes(bytes.fromhex(str(record["raw_hex"]))),
            "system_proof_verified": True,
        }
        count += 1
    require(count == EXPECTED_SYSTEM_OCCURRENCES, "system occurrence audit count mismatch")


def build_riivolution_xml(xml_path: Path, physical_paths: set[str], source_root: Path, staging_files: Path) -> dict[str, Any]:
    root = ET.Element("wiidisc", {"version": "1"})
    game = ET.SubElement(root, "id", {"game": "RPJ", "developer": "99", "disc": "0", "version": "0"})
    ET.SubElement(game, "region", {"type": "J"})
    options = ET.SubElement(root, "options")
    section = ET.SubElement(options, "section", {"name": "Arc Rise Fantasia"})
    option = ET.SubElement(section, "option", {"id": "arf-ko-full-option", "name": "Korean Full Text Patch", "default": "1"})
    choice = ET.SubElement(option, "choice", {"name": "Enabled"})
    ET.SubElement(choice, "patch", {"id": "arf-ko-full"})
    patch = ET.SubElement(root, "patch", {"id": "arf-ko-full", "root": "/arc_rise_fantasia_ko_full/files"})
    resized = 0
    for physical_path in sorted(physical_paths, key=str.lower):
        source = source_root / Path(physical_path)
        staged = staging_files / Path(physical_path)
        resize = staged.stat().st_size != source.stat().st_size
        resized += int(resize)
        ET.SubElement(
            patch,
            "file",
            {
                "disc": "/" + physical_path,
                "external": physical_path,
                "resize": "true" if resize else "false",
            },
        )
    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    parsed = ET.parse(xml_path).getroot()
    listed = {
        item.attrib["disc"].removeprefix("/")
        for item in parsed.findall("./patch/file")
    }
    require(parsed.tag == "wiidisc", "Riivolution XML root invalid")
    require(listed == physical_paths, "Riivolution XML target set differs from allowlist")
    return {"file_count": len(listed), "resize_true_count": resized, "sha256": sha256_file(xml_path)}


def final_static_validation(
    args: argparse.Namespace,
    indexed: dict[str, Any],
    application_dir: Path,
    staging_files: Path,
    occurrence_rows: dict[str, dict[str, Any]],
    leaves: list[LeafBuild],
    local_physical_reports: list[dict[str, Any]],
    system_report: dict[str, Any],
    image_inputs: dict[str, Any],
    image_physical_reports: list[dict[str, Any]],
    xml_report: dict[str, Any],
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    expected = set(image_inputs["physical_paths"])
    actual = {
        path.relative_to(staging_files).as_posix()
        for path in staging_files.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        errors.append(
            {
                "code": "staged_allowlist_mismatch",
                "missing": sorted(expected - actual),
                "unexpected": sorted(actual - expected),
            }
        )
    if len(occurrence_rows) != EXPECTED_OCCURRENCES or set(occurrence_rows) != set(indexed["record_by_id"]):
        errors.append({"code": "occurrence_application_set_mismatch", "actual": len(occurrence_rows)})
    kind_counts = Counter(str(row["application_kind"]) for row in occurrence_rows.values())
    expected_kind_counts = {
        "bscr_variable_pool": EXPECTED_BSCR_OCCURRENCES,
        "non_system_fixed_table": EXPECTED_NON_SYSTEM_TABLE_OCCURRENCES,
        "verified_system_application_proof": EXPECTED_SYSTEM_OCCURRENCES,
    }
    if dict(kind_counts) != expected_kind_counts:
        errors.append({"code": "occurrence_kind_counts", "actual": dict(kind_counts), "expected": expected_kind_counts})
    if len([leaf for leaf in leaves if leaf.kind == "bscr"]) != EXPECTED_BSCR_LEAVES:
        errors.append({"code": "bscr_leaf_count"})
    if len([leaf for leaf in leaves if leaf.kind == "table"]) != EXPECTED_NON_SYSTEM_TABLE_PAYLOADS:
        errors.append({"code": "table_leaf_count"})
    if len(local_physical_reports) != EXPECTED_LOCAL_CONTAINERS + 1:
        errors.append({"code": "local_physical_report_count", "actual": len(local_physical_reports)})
    if len(image_physical_reports) != EXPECTED_IMAGE_DIRECT_FILES:
        errors.append({"code": "image_direct_physical_report_count", "actual": len(image_physical_reports)})
    if xml_report["file_count"] != EXPECTED_FINAL_PHYSICAL_FILES:
        errors.append({"code": "xml_file_count", "actual": xml_report["file_count"]})

    staged_files = []
    for physical_path in sorted(expected, key=str.lower):
        source = args.source_root / Path(physical_path)
        target = staging_files / Path(physical_path)
        if not target.is_file():
            continue
        source_hash = sha256_file(source)
        output_hash = sha256_file(target)
        if source_hash == output_hash:
            errors.append({"code": "staged_file_unchanged", "physical_path": physical_path})
        staged_files.append(
            {
                "physical_path": physical_path,
                "source_sha256": source_hash,
                "output_sha256": output_hash,
                "source_size": source.stat().st_size,
                "output_size": target.stat().st_size,
            }
        )

    occurrence_manifest = application_dir / "occurrence_application_manifest.jsonl"
    with occurrence_manifest.open("w", encoding="utf-8", newline="\n") as handle:
        for record in indexed["records"]:
            handle.write(json.dumps(occurrence_rows[str(record["id"])], ensure_ascii=False) + "\n")

    leaf_manifest = application_dir / "leaf_build_manifest.json"
    write_json(
        leaf_manifest,
        {
            "schema": "arf-full-leaf-build-manifest-v1",
            "game_id": GAME_ID,
            "leaf_count": len(leaves),
            "leaves": [
                {
                    "kind": leaf.kind,
                    "physical_path": leaf.physical_path,
                    "logical_locator": leaf.logical_locator,
                    "leaf_name": leaf.leaf_name,
                    "entry_path": list(leaf.entry_path),
                    "source_sha256": leaf.source_sha256,
                    "output_sha256": leaf.output_sha256,
                    "source_size": leaf.source_size,
                    "output_size": leaf.output_size,
                    "occurrence_count": leaf.occurrence_count,
                    "unique_tm_units": len(leaf.tm_ids),
                    "output": rel_posix(leaf.output_path, args.output_dir),
                    "replacement_manifest": rel_posix(leaf.replacement_manifest, args.output_dir),
                }
                for leaf in leaves
            ],
        },
    )
    return {
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "staged_file_count": len(staged_files),
        "staged_files": staged_files,
        "occurrence_application_counts": dict(kind_counts),
        "occurrence_manifest": rel_posix(occurrence_manifest, args.output_dir),
        "occurrence_manifest_sha256": sha256_file(occurrence_manifest),
        "leaf_manifest": rel_posix(leaf_manifest, args.output_dir),
        "leaf_manifest_sha256": sha256_file(leaf_manifest),
        "local_physical_reports": local_physical_reports,
        "system": system_report,
        "image_ui": {
            "reinsertion_targets": len(image_inputs["targets"]),
            "direct_physical_files": image_physical_reports,
            "cumulative_system_leaf": {
                "entry_path": [53],
                "payload": str(image_inputs["system_leaf"]),
                "sha256": sha256_file(image_inputs["system_leaf"]),
            },
        },
    }


def clean_output(output_dir: Path, project_root: Path, force: bool) -> None:
    resolved = output_dir.resolve()
    work_root = (project_root / "work").resolve()
    require(resolved.parent == work_root, f"output must be a direct child of {work_root}")
    require(resolved.name not in {"", ".", "..", "work"}, "unsafe output directory")
    if resolved.exists():
        require(force, f"output already exists; pass --force to replace it: {resolved}")
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[2]
    work = project_root / "work"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--translation-memory", type=Path, default=work / "translation/final/translation_memory_draft.json")
    parser.add_argument("--text-catalog", type=Path, default=work / "catalog/text_v2/text_catalog.json")
    parser.add_argument("--physical-hashes", type=Path, default=work / "catalog/text_v2/physical_source_hashes.json")
    parser.add_argument("--source-root", type=Path, default=work / "disc_extracted/DATA/files")
    parser.add_argument("--codebook", type=Path, default=work / "font/final_v1/codebook.json")
    parser.add_argument("--font-dir", type=Path, default=work / "font/final_v1/injected")
    parser.add_argument("--system-payload-dir", type=Path, default=work / "final_system_table_application/payloads")
    parser.add_argument("--system-proof", type=Path, default=work / "final_system_table_application/application_proof.json")
    parser.add_argument("--system-files-dir", type=Path, help="optional directory containing prebuilt system.vol/help.bin/monster_book.bin")
    parser.add_argument("--image-manifest", type=Path, default=work / "image_ui_final/reinsertion_manifest.json")
    parser.add_argument("--image-validation", type=Path, default=work / "image_ui_final/reports/structural_validation.json")
    parser.add_argument("--table-catalog-dir", type=Path, default=work / "research/table_agent/catalogs")
    parser.add_argument("--node", type=Path, default=Path(r"C:\Program Files\nodejs\node.exe"))
    parser.add_argument("--container-tool", type=Path, default=work / "research/container_agent/container_tool.js")
    parser.add_argument("--bscr-tool", type=Path, default=work / "research/bscr_agent/bscr_tool.py")
    parser.add_argument("--table-tool", type=Path, default=work / "research/table_agent/arf_table_tool.py")
    parser.add_argument("--encoder", type=Path, default=work / "research/encode_custom_euc28.py")
    parser.add_argument("--lz10-tool", type=Path, default=work / "research/arf_lz10.py")
    parser.add_argument("--output-dir", type=Path, default=work / "final_runtime_staging")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    require(1 <= args.jobs <= 16, "--jobs must be 1..16")
    required_paths = (
        args.translation_memory,
        args.text_catalog,
        args.physical_hashes,
        args.codebook,
        args.system_proof,
        args.image_manifest,
        args.image_validation,
        args.node,
        args.container_tool,
        args.bscr_tool,
        args.table_tool,
        args.encoder,
        args.lz10_tool,
    )
    missing = [str(path) for path in required_paths if not path.is_file()]
    require(not missing, "missing required inputs: " + ", ".join(missing))
    require(args.source_root.is_dir(), f"missing source root: {args.source_root}")
    require(args.table_catalog_dir.is_dir(), f"missing table catalog directory: {args.table_catalog_dir}")
    clean_output(args.output_dir, project_root, args.force)

    try:
        application_dir = args.output_dir / "application"
        staging_files = args.output_dir / "riivolution_sd/arc_rise_fantasia_ko_full/files"
        xml_path = args.output_dir / "riivolution_sd/riivolution/arc_rise_fantasia_ko_full.xml"
        application_dir.mkdir(parents=True)
        staging_files.mkdir(parents=True)

        print("[1/8] validating final TM/catalog/codebook, 612 text targets, and 44 image targets", flush=True)
        indexed = validate_and_index_inputs(args)
        system_inputs = validate_system_inputs(args)
        image_inputs = validate_image_inputs(args, indexed, project_root)
        bscr_module = load_module("arf_full_bscr_tool", args.bscr_tool)
        table_module = load_module("arf_full_table_tool", args.table_tool)
        encoder_module = load_module("arf_full_encoder", args.encoder)
        lz10_module = load_module("arf_full_lz10", args.lz10_tool)

        occurrence_rows: dict[str, dict[str, Any]] = {}
        print("[2/8] rebuilding 606 BSCR leaves", flush=True)
        bscr_leaves = build_bscr_leaves(
            args, indexed, application_dir, bscr_module, encoder_module, lz10_module, occurrence_rows
        )
        print("[3/8] rebuilding 15 non-system table leaves", flush=True)
        table_leaves = build_non_system_table_leaves(
            args, indexed, application_dir, table_module, encoder_module, lz10_module, occurrence_rows
        )
        leaves = bscr_leaves + table_leaves

        print("[4/8] rebuilding 608 Event/Map/Btl/minigame containers", flush=True)
        local_reports, _ = rebuild_local_physical_files(
            args, application_dir, staging_files, leaves, lz10_module
        )
        print("[5/8] cumulatively rebuilding Sys tables, fonts, and nowloading image", flush=True)
        system_report = merge_or_build_system(
            args, application_dir, staging_files, system_inputs, image_inputs
        )
        add_system_occurrence_rows(indexed, occurrence_rows)

        print("[6/8] staging 43 direct image-UI physical files", flush=True)
        image_physical_reports = stage_image_direct_files(
            args, staging_files, image_inputs
        )
        print("[7/8] generating 655-file Riivolution XML", flush=True)
        xml_report = build_riivolution_xml(
            xml_path, image_inputs["physical_paths"], args.source_root, staging_files
        )
        print("[8/8] running final static allowlist/hash/coverage validation", flush=True)
        validation = final_static_validation(
            args,
            indexed,
            application_dir,
            staging_files,
            occurrence_rows,
            leaves,
            local_reports,
            system_report,
            image_inputs,
            image_physical_reports,
            xml_report,
        )

        manifest = {
            "schema": "arf-full-runtime-staging-v1",
            "game_id": GAME_ID,
            "translation_engine_policy": TRANSLATION_POLICY,
            "external_translation_services_used": [],
            "external_translation_models_or_apis_used": [],
            "source_rvz_modified": False,
            "runtime_ready_release": False,
            "dolphin_screen_test": "pending",
            "inputs": {
                "translation_memory": {"path": str(args.translation_memory.resolve()), "sha256": sha256_file(args.translation_memory)},
                "text_catalog": {"path": str(args.text_catalog.resolve()), "sha256": sha256_file(args.text_catalog)},
                "codebook": {"path": str(args.codebook.resolve()), "sha256": sha256_file(args.codebook), "assigned_characters": indexed["codebook"].get("assigned")},
                "system_application_proof": {"path": str(args.system_proof.resolve()), "sha256": sha256_file(args.system_proof)},
                "image_reinsertion_manifest": {"path": str(args.image_manifest.resolve()), "sha256": sha256_file(args.image_manifest)},
                "image_structural_validation": {"path": str(args.image_validation.resolve()), "sha256": sha256_file(args.image_validation)},
                "source_files_root": str(args.source_root.resolve()),
            },
            "counts": {
                "tm_units": len(indexed["units"]),
                "catalog_occurrences": len(indexed["records"]),
                "bscr_leaves": len(bscr_leaves),
                "bscr_occurrences": sum(leaf.occurrence_count for leaf in bscr_leaves),
                "non_system_table_payloads": len(table_leaves),
                "non_system_table_occurrences": sum(leaf.occurrence_count for leaf in table_leaves),
                "system_occurrences": EXPECTED_SYSTEM_OCCURRENCES,
                "local_containers_rebuilt": EXPECTED_LOCAL_CONTAINERS,
                "image_reinsertion_targets": len(image_inputs["targets"]),
                "image_direct_physical_files": len(image_physical_reports),
                "image_cumulative_system_members": 1,
                "staged_physical_files": validation["staged_file_count"],
                "riivolution_file_rules": xml_report["file_count"],
            },
            "riivolution": {
                "xml": rel_posix(xml_path, args.output_dir),
                **xml_report,
                "patch_root": "riivolution_sd/arc_rise_fantasia_ko_full/files",
            },
            "static_validation": validation,
        }
        write_json(args.output_dir / "staging_manifest.json", manifest)
        summary = {
            "output": str(args.output_dir.resolve()),
            "tm_units": manifest["counts"]["tm_units"],
            "occurrences": manifest["counts"]["catalog_occurrences"],
            "bscr_leaves": manifest["counts"]["bscr_leaves"],
            "table_payloads": manifest["counts"]["non_system_table_payloads"],
            "staged_files": manifest["counts"]["staged_physical_files"],
            "static_errors": validation["error_count"],
            "valid": validation["valid"],
            "dolphin_screen_test": "pending",
        }
        print(json.dumps(summary, ensure_ascii=False), flush=True)
        return 0 if validation["valid"] else 1
    except Exception as exc:
        failure = {
            "schema": "arf-full-runtime-staging-failure-v1",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        write_json(args.output_dir / "BUILD_FAILED.json", failure)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
