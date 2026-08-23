#!/usr/bin/env python3
"""Audit every known runtime battle-text lane for undeclared or residual Japanese.

This closes the gap that allowed the separate field-object copy of Ray Stone to
survive earlier database-only checks.  It independently covers enemy BTEM
records, the 14 BTEM leaves in btl_usual.vol, special/boss labels embedded in
btl_magic.vld, battle tutorial records, main.dol runtime strings, and raster UI
application reports.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any


def need(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    need(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_scan_module(root: Path):
    path = root / "work/research/audit_battle_text_coverage.py"
    spec = importlib.util.spec_from_file_location("arf_battle_scan", path)
    need(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["arf_battle_scan"] = module
    spec.loader.exec_module(module)
    return module


def parse_rtdp(data: bytes) -> list[tuple[int, str, bytes]]:
    need(data[:4] == b"RTDP", "not RTDP")
    end_of_header, count = struct.unpack_from(">II", data, 4)
    need(0x20 + count * 40 <= end_of_header <= len(data), "invalid RTDP header")
    result = []
    for index in range(count):
        pos = 0x20 + index * 40
        name = data[pos:pos + 32].split(b"\0", 1)[0].decode("ascii")
        size, relative = struct.unpack_from(">II", data, pos + 32)
        start = end_of_header + relative
        end = start + size
        need(end <= len(data), f"RTDP member exceeds file: {name}")
        result.append((index, name, bytes(value ^ 0x55 for value in data[start:end])))
    return result


def extract_leaf(container: Path, wanted: str) -> bytes:
    for _, name, data in parse_rtdp(container.read_bytes()):
        if name == wanted:
            return data
    raise RuntimeError(f"missing RTDP leaf: {wanted}")


def collect_btem(container: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for outer_index, outer_name, outer in parse_rtdp(container.read_bytes()):
        outer_id = f"{outer_index}:{outer_name}"
        if outer[:4] == b"BTEM":
            result[outer_id] = outer
        elif outer[:4] == b"RTDP":
            for inner_index, inner_name, inner in parse_rtdp(outer):
                if inner[:4] == b"BTEM":
                    result[f"{outer_id}/{inner_index}:{inner_name}"] = inner
    return result


def japanese_letters(text: str) -> bool:
    return any(
        0x3040 <= ord(char) <= 0x30FF
        or 0x3400 <= ord(char) <= 0x9FFF
        or 0xF900 <= ord(char) <= 0xFAFF
        for char in text
    )


def audit_btem(root: Path, scanner) -> dict[str, Any]:
    source_path = root / "work/disc_extracted/DATA/files/Btl/btl_usual.vol"
    final_path = root / "work/final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Btl/btl_usual.vol"
    source = collect_btem(source_path)
    final = collect_btem(final_path)
    need(source.keys() == final.keys(), "BTEM identity set changed")
    rows = []
    residue = []
    for identity, before in source.items():
        after = final[identity]
        first_rtdp = before.find(b"RTDP")
        limit = len(before) if first_rtdp < 0 else first_rtdp
        source_runs = [row for row in scanner.scan_euc_jp_runs(before[:limit], max_bytes=256)
                       if japanese_letters(str(row["text"]))]
        unchanged = []
        for row in source_runs:
            start, end = int(row["offset"]), int(row["end"])
            if after[start:end] == before[start:end]:
                item = {"identity": identity, **row}
                unchanged.append(item)
                residue.append(item)
        rows.append({
            "identity": identity,
            "source_semantic_runs": len(source_runs),
            "unchanged_semantic_runs": len(unchanged),
            "unchanged": unchanged,
        })
    return {
        "source_sha256": sha(source_path),
        "final_sha256": sha(final_path),
        "btem_count": len(rows),
        "source_semantic_runs": sum(row["source_semantic_runs"] for row in rows),
        "residue_count": len(residue),
        "residue": residue,
        "rows": rows,
    }


def parse_vlh(header: bytes, vld_size: int) -> list[tuple[int, int]]:
    need(header[:4] == b"RVLX", "not RVLX")
    header_size, count, declared = struct.unpack_from(">III", header, 4)
    need(header_size == len(header) and declared == len(header) + vld_size, "RVLX geometry mismatch")
    return [struct.unpack_from(">II", header, 0x20 + index * 8) for index in range(count)]


def magic_members(vld: Path, header: bytes):
    rows = parse_vlh(header, vld.stat().st_size)
    with vld.open("rb") as handle:
        for entry, (size, offset) in enumerate(rows):
            if not size:
                continue
            handle.seek(offset)
            data = handle.read(size)
            need(data[:4] == b"RTDP", f"magic entry {entry} is not RTDP")
            for member_index, name, decoded in parse_rtdp(data):
                yield entry, member_index, name, decoded


def audit_magic(root: Path) -> dict[str, Any]:
    report = load(root / "work/battle_magic_application/application_report.json")
    patterns = {bytes.fromhex(row["source_raw_hex"]): row["source_text"] for row in report["rows"]}
    regex = re.compile(b"|".join(re.escape(pattern) for pattern in sorted(patterns, key=len, reverse=True)))
    source_path = root / "work/disc_extracted/DATA/files/Btl/btl_magic.vld"
    final_path = root / "work/final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Btl/btl_magic.vld"
    header = (root / "work/research/table_agent/btl_usual_entries/btl_magic.vlh").read_bytes()

    def scan(path: Path) -> list[dict[str, Any]]:
        hits = []
        for entry, member_index, member, data in magic_members(path, header):
            for match in regex.finditer(data):
                hits.append({
                    "entry": entry, "member_index": member_index, "member": member,
                    "offset": match.start(), "source_text": patterns[match.group()],
                })
        return hits

    source_hits = scan(source_path)
    final_hits = scan(final_path)
    expected = {(row["entry"], row["member"], row["offset"], row["source_text"]) for row in report["rows"]}
    observed = {(row["entry"], row["member"], row["offset"], row["source_text"]) for row in source_hits}
    undeclared = [row for row in source_hits
                  if (row["entry"], row["member"], row["offset"], row["source_text"]) not in expected]
    return {
        "source_sha256": sha(source_path), "final_sha256": sha(final_path),
        "unique_source_patterns": len(patterns), "declared_slots": len(report["rows"]),
        "source_hits": len(source_hits), "undeclared_source_hits": undeclared,
        "declared_missing_count": len(expected - observed),
        "final_residue_hits": final_hits,
    }


def audit_tutorial(root: Path) -> dict[str, Any]:
    catalog = load(root / "work/research/table_agent/catalogs/btl_tutorial.json")
    source_path = root / "work/disc_extracted/DATA/files/Btl/btl_tutorial.vld"
    final_path = root / "work/final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Btl/btl_tutorial.vld"
    source, final = source_path.read_bytes(), final_path.read_bytes()
    rows = [row for row in catalog["units"] if row.get("has_japanese") and japanese_letters(str(row["source_text"]))]
    source_mismatch = []
    residue = []
    for row in rows:
        offset = int(row["offset"])
        raw = bytes.fromhex(row["raw_hex"])
        if source[offset:offset + len(raw)] != raw:
            source_mismatch.append(row["id"])
        if final[offset:offset + len(raw)] == raw:
            residue.append({"id": row["id"], "offset": offset, "source_text": row["source_text"]})
    return {
        "source_sha256": sha(source_path), "final_sha256": sha(final_path),
        "semantic_japanese_slots": len(rows), "source_mismatch_count": len(source_mismatch),
        "source_mismatches": source_mismatch, "final_residue_count": len(residue), "final_residue": residue,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "work/validation/all_battle_text_duplicate_audit.json"
    scanner = load_scan_module(root)

    enemy = load(root / "work/validation/battle_text_independent_coverage_audit.json")
    main_dol = load(root / "work/validation/main_dol_runtime_residue_release_validation.json")
    battle_ui = load(root / "work/battle_ui_raster_application/application_report.json")
    system_residue = load(root / "work/validation/localization_residue_closure.json")
    btem = audit_btem(root, scanner)
    magic = audit_magic(root)
    tutorial = audit_tutorial(root)

    errors = []
    if enemy.get("counts", {}).get("uncovered_before_first_rtdp") != 0 or enemy.get("counts", {}).get("unchanged_before_first_rtdp") != 0:
        errors.append("enemy BTEM coverage/residue failed")
    if btem["residue_count"]:
        errors.append("btl_usual BTEM residue remains")
    if magic["undeclared_source_hits"] or magic["declared_missing_count"] or magic["final_residue_hits"]:
        errors.append("btl_magic duplicate/residue audit failed")
    if tutorial["source_mismatch_count"] or tutorial["final_residue_count"]:
        errors.append("battle tutorial residue audit failed")
    if main_dol.get("valid") is not True or main_dol.get("checks", {}).get("target_has_no_japanese_residue") is not True:
        errors.append("main.dol runtime string validation failed")
    if battle_ui.get("valid") is not True or battle_ui.get("counts", {}).get("unexpected_changed_members") != 0:
        errors.append("battle raster UI validation failed")
    if system_residue.get("valid") is not True or system_residue.get("summary", {}).get("semantic_japanese_unmatched_after") != 0:
        errors.append("system text residue validation failed")

    report = {
        "schema": "arf-all-battle-text-duplicate-audit-v1", "game_id": "RPJJ99",
        "translator_model": "Codex internal", "external_translation_models_or_apis_used": False,
        "enemy_btem": {
            "entries": enemy.get("counts", {}).get("entries"),
            "catalog_units": enemy.get("catalog", {}).get("unit_count"),
            "uncovered_before_first_rtdp": enemy.get("counts", {}).get("uncovered_before_first_rtdp"),
            "unchanged_before_first_rtdp": enemy.get("counts", {}).get("unchanged_before_first_rtdp"),
        },
        "btl_usual_btem": btem, "battle_magic": magic, "battle_tutorial": tutorial,
        "main_dol_runtime": {
            "valid": main_dol.get("valid"),
            "verified_memory_writes": main_dol.get("counts", {}).get("verified_main_dol_memory_writes"),
            "target_has_no_japanese_residue": main_dol.get("checks", {}).get("target_has_no_japanese_residue"),
        },
        "battle_raster_ui": {
            "valid": battle_ui.get("valid"),
            "modified_wtm_entries": battle_ui.get("counts", {}).get("modified_wtm_entries"),
            "translated_text_items": battle_ui.get("counts", {}).get("translated_text_items"),
            "unexpected_changed_members": battle_ui.get("counts", {}).get("unexpected_changed_members"),
        },
        "system_text_residue": {
            "valid": system_residue.get("valid"),
            "semantic_japanese_unmatched_after": system_residue.get("summary", {}).get("semantic_japanese_unmatched_after"),
        },
        "error_count": len(errors), "errors": errors, "valid": not errors,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output), "valid": report["valid"], "error_count": len(errors),
        "btl_usual_residue": btem["residue"], "magic_final_residue_count": len(magic["final_residue_hits"]),
        "tutorial_final_residue_count": tutorial["final_residue_count"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
