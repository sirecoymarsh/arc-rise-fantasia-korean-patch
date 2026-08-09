#!/usr/bin/env python3
"""Apply every approved system-table translation and verify rebuilt payloads.

The generated binaries stay under ``work/``.  Only the source-free manifest is
intended for the development checkpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path


RAW_CONTROL_RE = re.compile(r"<\$([0-9A-Fa-f]{2,})>")
SYSTEM_CATALOG_FILENAMES = {
    "ability.json",
    "chat.json",
    "dragon.json",
    "help.json",
    "item.json",
    "magic.json",
    "monster_book.json",
    "operation.json",
    "quest.json",
    "shop.json",
    "special.json",
    "todo.json",
    "treasure.json",
}

# Independently audited text spans.  These deliberately do not come from the
# mutable catalogs: an earlier catalog boundary error classified record
# metadata as string padding and therefore made its own allowlist pass.
AUDITED_FIXED_LAYOUTS: dict[str, tuple[int, int, int, tuple[tuple[int, int], ...]]] = {
    # schema: (record_size, record_count, header_size, (relative_offset, capacity)*)
    "item": (255, 772, 0, ((0, 17), (17, 81), (98, 81))),
    "shop": (86, 47, 0, ((0, 20),)),
    "dragon": (279, 13, 0, ((0, 24), (24, 48), (72, 97), (169, 49), (218, 49))),
    "treasure": (49, 256, 0, ((23, 21),)),
    "magic": (164, 49, 0, ((0, 20), (20, 40), (60, 80))),
    "special": (144, 76, 0, ((0, 22), (22, 83))),
    "operation": (120, 8, 0, ((0, 24), (24, 96))),
    "ability": (146, 250, 0, ((0, 21), (21, 81))),
    "todo": (144, 208, 0, ((16, 64), (80, 64))),
    "help": (347, 380, 0, ((0, 21), (21, 322))),
    "monster_book": (644, 274, 0, ((0, 35), (260, 96))),
    # chat.bin is SSCR; its fixed 400x44 message table begins at 0x56A8 and
    # is followed by a separate trigger table that must remain opaque.
    "chat": (44, 400, 0x56A8, ((0, 43),)),
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def canonicalize_table_controls(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        raw = bytes.fromhex(match.group(1))
        if not raw:
            raise ValueError("empty raw control")
        return f"<${raw[0]:02X}>" + raw[1:].decode("ascii")

    return RAW_CONTROL_RE.sub(replace, text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("translation_memory", type=Path)
    parser.add_argument("codebook", type=Path)
    parser.add_argument("boundary_audit", type=Path)
    parser.add_argument("catalog_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--table-tool", type=Path, required=True)
    parser.add_argument("--encoder", type=Path, required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    resolved_output = args.output_dir.resolve()
    expected_parent = (root / "work").resolve()
    if resolved_output.parent != expected_parent:
        raise ValueError(f"output must be a direct child of {expected_parent}")
    if args.output_dir.exists():
        shutil.rmtree(args.output_dir)
    catalogs_out = args.output_dir / "replacement_catalogs"
    payloads_out = args.output_dir / "payloads"
    verification_out = args.output_dir / "verification_catalogs"
    for directory in (catalogs_out, payloads_out, verification_out):
        directory.mkdir(parents=True, exist_ok=True)

    memory = json.loads(args.translation_memory.read_text(encoding="utf-8"))
    codebook = json.loads(args.codebook.read_text(encoding="utf-8"))
    audit = json.loads(args.boundary_audit.read_text(encoding="utf-8"))
    encoder = load_module("arf_table_application_encoder", args.encoder)
    approved_by_source = {
        str(unit["source_text"]): unit
        for unit in memory["units"]
        if unit.get("review_status") == "approved"
        and str(unit.get("translation_ko", "")).strip()
        and unit.get("primary_surface") == "system_database"
    }
    approved_by_id = {str(unit["tm_id"]): unit for unit in approved_by_source.values()}
    system_database_scanner_occurrences = sum(
        int(unit.get("surface_counts", {}).get("system_database", 0))
        for unit in approved_by_id.values()
    )
    boundary_by_table: dict[str, dict[str, object]] = {}
    for item in audit["units"]:
        tm_unit = approved_by_id.get(str(item["tm_id"]))
        if tm_unit is None:
            continue
        application_mode = str(item.get("application_mode") or "tm_rewrite")
        table_target = str(tm_unit["translation_ko"])
        if application_mode == "table_specific_only":
            table_target = str(item.get("table_specific_translation_ko") or "")
            if not table_target:
                raise ValueError(
                    f"table-specific boundary target is empty: {item['tm_id']}"
                )
        for table_id in item["table_unit_ids"]:
            table_id = str(table_id)
            if table_id in boundary_by_table:
                raise ValueError(f"duplicate boundary table ID: {table_id}")
            boundary_by_table[table_id] = {
                "tm_unit": tm_unit,
                "target": table_target,
                "application_mode": application_mode,
            }

    payload_reports: list[dict[str, object]] = []
    matched_tm_ids: set[str] = set()
    total_replacements = 0
    fixed_outside_diff_errors = 0
    verification_errors: list[dict[str, object]] = []

    available_catalogs = {path.name for path in args.catalog_dir.glob("*.json")}
    missing_catalogs = sorted(SYSTEM_CATALOG_FILENAMES - available_catalogs)
    if missing_catalogs:
        raise ValueError(f"missing required system catalogs: {missing_catalogs}")
    for catalog_path in sorted(
        args.catalog_dir / name for name in SYSTEM_CATALOG_FILENAMES
    ):
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        replacements: list[tuple[dict[str, object], dict[str, object], bytes]] = []
        for table_unit in catalog.get("units", []):
            source = str(table_unit.get("source_text", ""))
            if not source:
                continue
            table_id = str(table_unit["id"])
            boundary_binding = boundary_by_table.get(table_id)
            matched_via_boundary = boundary_binding is not None
            if boundary_binding is not None:
                tm_unit = boundary_binding["tm_unit"]
                target = str(boundary_binding["target"])
                application_mode = str(boundary_binding["application_mode"])
            else:
                tm_unit = approved_by_source.get(canonicalize_table_controls(source))
                target = str(tm_unit["translation_ko"]) if tm_unit is not None else ""
                application_mode = "direct_source_match"
            if tm_unit is None:
                continue
            encoded = encoder.encode_text(target, codebook)
            if b"\0" in encoded:
                raise ValueError(f"encoded NUL for {tm_unit['tm_id']}")
            table_unit["replacement_hex"] = encoded.hex().upper()
            table_unit["replacement_tm_id"] = tm_unit["tm_id"]
            table_unit["matched_via_boundary_audit"] = matched_via_boundary
            table_unit["boundary_application_mode"] = application_mode
            replacements.append((table_unit, tm_unit, encoded))
            matched_tm_ids.add(str(tm_unit["tm_id"]))

        if not replacements:
            continue
        source_path = Path(str(catalog["source_path"]))
        if sha256(source_path).lower() != str(catalog["source_sha256"]).lower():
            raise ValueError(f"source hash mismatch: {source_path}")
        replacement_catalog_path = catalogs_out / catalog_path.name
        replacement_catalog_path.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        output_path = payloads_out / f"{catalog_path.stem}{source_path.suffix}"
        command = [
            sys.executable,
            str(args.table_tool),
            "apply",
            str(source_path),
            str(replacement_catalog_path),
            str(output_path),
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)

        verification_catalog_path = verification_out / catalog_path.name
        subprocess.run(
            [
                sys.executable,
                str(args.table_tool),
                "catalog",
                str(output_path),
                str(verification_catalog_path),
                "--schema",
                str(catalog["schema"]),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        verified = json.loads(
            verification_catalog_path.read_text(encoding="utf-8")
        )
        verified_by_id = {str(unit["id"]): unit for unit in verified["units"]}
        payload_verification_errors = []
        for table_unit, tm_unit, encoded in replacements:
            verified_unit = verified_by_id.get(str(table_unit["id"]))
            if verified_unit is None or str(verified_unit["raw_hex"]).upper() != encoded.hex().upper():
                payload_verification_errors.append(
                    {
                        "table_unit_id": table_unit["id"],
                        "tm_id": tm_unit["tm_id"],
                        "expected_hex": encoded.hex().upper(),
                        "actual_hex": (
                            verified_unit.get("raw_hex") if verified_unit else None
                        ),
                    }
                )

        resizable = bool(catalog.get("metadata", {}).get("resizable_at_table_level"))
        source_data = source_path.read_bytes()
        output_data = output_path.read_bytes()
        changes_outside_declared_slots = 0
        if not resizable:
            allowed: set[int] = set()
            schema_name = str(catalog["schema"])
            audited = AUDITED_FIXED_LAYOUTS.get(schema_name)
            if audited is None:
                raise ValueError(f"missing independently audited fixed layout: {schema_name}")
            record_size, record_count, header_size, spans = audited
            if len(source_data) < header_size + record_size * record_count:
                raise ValueError(f"audited fixed layout size mismatch: {schema_name}")
            for record in range(record_count):
                base = header_size + record * record_size
                for relative, capacity in spans:
                    allowed.update(range(base + relative, base + relative + capacity))
            changes_outside_declared_slots = sum(
                before != after and index not in allowed
                for index, (before, after) in enumerate(zip(source_data, output_data))
            )
            changes_outside_declared_slots += abs(len(source_data) - len(output_data))
            if changes_outside_declared_slots:
                fixed_outside_diff_errors += changes_outside_declared_slots
            if schema_name == "item":
                bad_item_ids = [
                    (record, int.from_bytes(output_data[record * 255 + 179 : record * 255 + 181], "big"))
                    for record in range(772)
                    if int.from_bytes(output_data[record * 255 + 179 : record * 255 + 181], "big") != record
                ]
                if bad_item_ids:
                    payload_verification_errors.append(
                        {
                            "code": "item_record_id_invariant_failed",
                            "count": len(bad_item_ids),
                            "sample": bad_item_ids[:16],
                        }
                    )

        if payload_verification_errors:
            verification_errors.extend(
                {
                    "catalog": catalog_path.name,
                    **item,
                }
                for item in payload_verification_errors
            )
        total_replacements += len(replacements)
        payload_reports.append(
            {
                "catalog": catalog_path.name,
                "schema": catalog["schema"],
                "source_path": str(source_path),
                "source_sha256": sha256(source_path),
                "output_path": str(output_path),
                "output_sha256": sha256(output_path),
                "source_size": len(source_data),
                "output_size": len(output_data),
                "table_resizable": resizable,
                "replacement_fields": len(replacements),
                "boundary_mapped_fields": sum(
                    bool(unit.get("matched_via_boundary_audit"))
                    for unit, _, _ in replacements
                ),
                "table_specific_boundary_fields": sum(
                    unit.get("boundary_application_mode") == "table_specific_only"
                    for unit, _, _ in replacements
                ),
                "verification_errors": len(payload_verification_errors),
                "changes_outside_declared_slots": changes_outside_declared_slots,
                "replacement_catalog_sha256": sha256(replacement_catalog_path),
                "verification_catalog_sha256": sha256(verification_catalog_path),
            }
        )

    missing_tm_ids = sorted(set(approved_by_id) - matched_tm_ids)
    if missing_tm_ids:
        verification_errors.append(
            {
                "code": "approved_system_tm_not_applied",
                "count": len(missing_tm_ids),
                "sample": missing_tm_ids[:20],
            }
        )
    structured_field_coverage_matches_scanner_occurrences = (
        total_replacements == system_database_scanner_occurrences
    )
    if not structured_field_coverage_matches_scanner_occurrences:
        verification_errors.append(
            {
                "code": "structured_field_scanner_occurrence_count_mismatch",
                "scanner_occurrences": system_database_scanner_occurrences,
                "structured_replacement_fields": total_replacements,
            }
        )
    table_specific_boundary_replacement_fields = sum(
        int(item.get("boundary_application_mode") == "table_specific_only")
        for path in catalogs_out.glob("*.json")
        for item in json.loads(path.read_text(encoding="utf-8")).get("units", [])
        if item.get("replacement_tm_id")
    )
    report = {
        "schema": "arf-approved-system-table-application-proof-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "translation_memory_sha256": sha256(args.translation_memory),
        "codebook_sha256": sha256(args.codebook),
        "boundary_audit_sha256": sha256(args.boundary_audit),
        "approved_system_tm_units": len(approved_by_id),
        "applied_unique_tm_units": len(matched_tm_ids),
        "replacement_table_fields": total_replacements,
        "system_database_scanner_occurrences": system_database_scanner_occurrences,
        "structured_field_coverage_matches_scanner_occurrences": (
            structured_field_coverage_matches_scanner_occurrences
        ),
        "table_specific_boundary_replacement_fields": (
            table_specific_boundary_replacement_fields
        ),
        "nested_scanner_occurrences_covered_by_structured_parent_field": (
            table_specific_boundary_replacement_fields
        ),
        "payloads_rebuilt": len(payload_reports),
        "payloads_by_schema": dict(
            Counter(str(item["schema"]) for item in payload_reports)
        ),
        "fixed_payload_changes_outside_declared_slots": fixed_outside_diff_errors,
        "verification_error_count": len(verification_errors),
        "verification_errors": verification_errors,
        "payloads": payload_reports,
        "valid": not verification_errors and fixed_outside_diff_errors == 0,
    }
    manifest_path = args.output_dir / "application_proof.json"
    manifest_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "approved_system_tm_units",
                    "applied_unique_tm_units",
                    "replacement_table_fields",
                    "payloads_rebuilt",
                    "fixed_payload_changes_outside_declared_slots",
                    "verification_error_count",
                    "valid",
                )
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
