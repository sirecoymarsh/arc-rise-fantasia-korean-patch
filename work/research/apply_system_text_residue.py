#!/usr/bin/env python3
"""Apply the independently discovered system-table Japanese residue safely."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import struct
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
TRANSLATIONS = W / "translation/system_residue/system_text_residue_translations.json"
CATALOGS = W / "final_system_table_application/replacement_catalogs"
BASE_PAYLOADS = W / "final_system_table_application/payloads"
CODEBOOK = W / "font/final_v3/codebook.json"
ENCODER = W / "research/encode_custom_euc28.py"
CONTAINER_TOOL = W / "research/container_agent/container_tool.js"
BASE_SYSTEM = W / "battle_enemy_application/system.vol"
OUT = W / "system_text_residue_application"
NODE = Path(r"C:\Program Files\nodejs\node.exe")

SEMANTIC_JAPANESE_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff]")
CONTROL_RE = re.compile(r"<\$[0-9A-Fa-f]+>|<#[0-9A-Fa-f]+>")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def semantic_japanese(text: str) -> bool:
    return bool(SEMANTIC_JAPANESE_RE.search(CONTROL_RE.sub("", text)))


def parse_rtdp(data: bytes) -> list[dict[str, object]]:
    if data[:4] != b"RTDP":
        raise ValueError("not RTDP")
    eoh, count = struct.unpack_from(">II", data, 4)
    rows = []
    for index in range(count):
        pos = 0x20 + index * 40
        name = data[pos:pos + 32].split(b"\0", 1)[0].decode("ascii")
        size, relative = struct.unpack_from(">II", data, pos + 32)
        stored = data[eoh + relative:eoh + relative + size]
        decoded = bytes(value ^ 0x55 for value in stored)
        rows.append({"index": index, "name": name, "decoded": decoded, "sha256": sha_bytes(decoded)})
    return rows


def main() -> int:
    for path in (TRANSLATIONS, CODEBOOK, ENCODER, CONTAINER_TOOL, BASE_SYSTEM, NODE):
        if not path.is_file():
            raise SystemExit(f"missing input: {path}")
    OUT.mkdir(parents=True, exist_ok=True)
    payload_out = OUT / "payloads"
    payload_out.mkdir(parents=True, exist_ok=True)
    doc = load(TRANSLATIONS)
    rows = doc["translations"]
    if len(rows) != 30 or len({row["table_unit_id"] for row in rows}) != 30:
        raise SystemExit("system residue map must contain 30 unique units")
    encoder = load_module("arf_system_residue_encoder", ENCODER)
    codebook = load(CODEBOOK)

    catalogs = {path.stem: load(path) for path in CATALOGS.glob("*.json")}
    units = {
        str(unit["id"]): (schema, unit)
        for schema, catalog in catalogs.items()
        for unit in catalog.get("units", [])
    }
    semantic_missing_before = []
    typography_only_unchanged = []
    for schema, catalog in catalogs.items():
        for unit in catalog.get("units", []):
            raw = str(unit.get("raw_hex", "")).upper()
            replacement = str(unit.get("replacement_hex", "")).upper()
            if semantic_japanese(str(unit.get("source_text", ""))) and (not replacement or replacement == raw):
                semantic_missing_before.append(str(unit["id"]))
            elif unit.get("has_japanese") and replacement == raw:
                typography_only_unchanged.append(str(unit["id"]))
    wanted = {str(row["table_unit_id"]) for row in rows}
    if set(semantic_missing_before) != wanted:
        raise SystemExit(json.dumps({"semantic_missing_before": semantic_missing_before, "wanted": sorted(wanted)}, ensure_ascii=False, indent=2))

    by_schema: dict[str, list[dict[str, object]]] = {}
    applied_rows = []
    for row in rows:
        unit_id = str(row["table_unit_id"])
        if unit_id not in units:
            raise SystemExit(f"missing table unit: {unit_id}")
        schema, unit = units[unit_id]
        if row["source_text"] != unit["source_text"]:
            raise SystemExit(f"source mismatch: {unit_id}")
        encoded = encoder.encode_text(str(row["translation_ko"]), codebook)
        capacity = int(unit["capacity"])
        if not encoded or b"\0" in encoded or len(encoded) >= capacity:
            raise SystemExit(f"target does not fit: {unit_id}: {len(encoded)}/{capacity}")
        by_schema.setdefault(schema, []).append({"translation": row, "unit": unit, "encoded": encoded})

    payload_reports = []
    for schema, edits in sorted(by_schema.items()):
        base_path = BASE_PAYLOADS / f"{schema}{Path(catalogs[schema]['source_path']).suffix}"
        if not base_path.is_file():
            raise SystemExit(f"missing base payload: {base_path}")
        before = base_path.read_bytes()
        after = bytearray(before)
        mask = bytearray(len(before))
        for edit in edits:
            unit = edit["unit"]
            encoded = edit["encoded"]
            offset, capacity = int(unit["offset"]), int(unit["capacity"])
            source_raw = bytes.fromhex(str(unit["raw_hex"]))
            if before[offset:offset + len(source_raw)] != source_raw:
                raise SystemExit(f"base payload source mismatch: {unit['id']}")
            after[offset:offset + capacity] = b"\0" * capacity
            after[offset:offset + len(encoded)] = encoded
            mask[offset:offset + capacity] = b"\1" * capacity
            if after[offset:offset + len(encoded)] != encoded or after[offset + len(encoded)] != 0:
                raise SystemExit(f"write verification failed: {unit['id']}")
            applied_rows.append({
                "table_unit_id": unit["id"], "schema": schema,
                "source_text": edit["translation"]["source_text"],
                "translation_ko": edit["translation"]["translation_ko"],
                "offset": offset, "capacity": capacity,
                "source_hex": source_raw.hex().upper(),
                "replacement_hex": encoded.hex().upper(),
                "encoded_bytes": len(encoded), "headroom": capacity - len(encoded) - 1,
            })
        outside = sum(a != b and not mask[index] for index, (a, b) in enumerate(zip(before, after)))
        if outside:
            raise SystemExit(f"outside-slot changes in {schema}: {outside}")
        output_path = payload_out / base_path.name
        output_path.write_bytes(after)
        payload_reports.append({
            "schema": schema, "source": str(base_path), "source_sha256": sha(base_path),
            "output": str(output_path), "output_sha256": sha(output_path),
            "size_bytes": len(after), "translated_fields": len(edits),
            "changed_outside_allowed_bytes": outside,
        })

    base_system = BASE_SYSTEM.read_bytes()
    base_entries = {str(row["name"]): row for row in parse_rtdp(base_system)}
    manifest = {"format": "arf-container-edits-v1", "edits": []}
    for payload in payload_reports:
        name = Path(str(payload["output"])).name
        entry = base_entries.get(name)
        if entry is None:
            raise SystemExit(f"system entry missing: {name}")
        if entry["decoded"] != Path(str(payload["source"])).read_bytes():
            raise SystemExit(f"system/base payload mismatch: {name}")
        manifest["edits"].append({
            "entryPath": [entry["index"]], "expectedSha256": entry["sha256"].lower(),
            "replacementFile": f"payloads/{name}", "name": name,
        })
    edits_path = OUT / "system_edits.json"
    edits_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    system_out = OUT / "system.vol"
    system_report = OUT / "system_rebuild_report.json"
    subprocess.run([
        str(NODE), str(CONTAINER_TOOL), "rebuild", str(BASE_SYSTEM), str(edits_path),
        str(system_out), str(system_report),
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    final_entries = {str(row["name"]): row for row in parse_rtdp(system_out.read_bytes())}
    for payload in payload_reports:
        name = Path(str(payload["output"])).name
        if final_entries[name]["decoded"] != Path(str(payload["output"])).read_bytes():
            raise SystemExit(f"rebuilt system leaf mismatch: {name}")

    report = {
        "schema": "arf-system-text-residue-application-v1", "game_id": "RPJJ99",
        "translation_engine_policy": doc["translation_engine_policy"],
        "external_translation_models_or_apis_used": False,
        "translation_map": {"path": str(TRANSLATIONS), "sha256": sha(TRANSLATIONS)},
        "codebook": {"path": str(CODEBOOK), "sha256": sha(CODEBOOK), "assigned_characters": codebook["assigned"]},
        "coverage": {
            "catalogs_audited": len(catalogs),
            "catalog_units_audited": sum(len(c["units"]) for c in catalogs.values()),
            "semantic_japanese_unmatched_before": len(semantic_missing_before),
            "semantic_japanese_unmatched_after": 0,
            "typography_only_source_bytes_intentionally_preserved": len(typography_only_unchanged),
        },
        "counts": {
            "translated_fields": len(applied_rows),
            "ability_names": sum(r["schema"] == "ability" for r in applied_rows),
            "chat_titles": sum(r["schema"] == "chat" for r in applied_rows),
            "shop_names": sum(r["schema"] == "shop" for r in applied_rows),
            "payloads_rebuilt": len(payload_reports),
            "changed_outside_allowed_bytes": sum(p["changed_outside_allowed_bytes"] for p in payload_reports),
        },
        "source_missing_unit_ids": semantic_missing_before,
        "typography_only_preserved_unit_ids": typography_only_unchanged,
        "translations": applied_rows,
        "payloads": payload_reports,
        "system": {
            "source": str(BASE_SYSTEM), "source_sha256": sha(BASE_SYSTEM),
            "output": str(system_out), "output_sha256": sha(system_out),
            "source_size": BASE_SYSTEM.stat().st_size, "output_size": system_out.stat().st_size,
            "rebuild_report": str(system_report), "rebuild_report_sha256": sha(system_report),
        },
        "valid": True, "error_count": 0, "errors": [],
    }
    report_path = OUT / "application_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validation = W / "validation/system_text_residue_audit.json"
    shutil.copy2(report_path, validation)
    print(json.dumps({"output": str(report_path), "counts": report["counts"], "coverage": report["coverage"], "system_sha256": report["system"]["output_sha256"], "valid": True}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
