#!/usr/bin/env python3
"""Preflight approved Korean translations against Arc Rise fixed table fields."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path


RAW_CONTROL_RE = re.compile(r"<\$([0-9A-Fa-f]{2,})>")
TM_CONTROL_RE = re.compile(r"<\$[0-9A-Fa-f]{2}>")
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def catalog_tree_sha256(paths: list[Path]) -> str:
    """Bind a fit report to both catalog names and exact catalog bytes."""

    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda value: value.name):
        name = path.name.encode("utf-8")
        digest.update(len(name).to_bytes(4, "big"))
        digest.update(name)
        digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest().upper()


def load_encoder(path: Path):
    spec = importlib.util.spec_from_file_location("arf_custom_encoder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load encoder: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonicalize_table_controls(text: str) -> str:
    """Convert table-tool raw control chunks to the TM token representation.

    The table catalogs represent raw bytes as e.g. ``<$154432>`` while the
    text catalog represents the same bytes as ``<$15>D2``.  Control payloads
    in the audited schemas are ASCII, so this conversion is lossless.
    """

    def replace(match: re.Match[str]) -> str:
        raw_hex = match.group(1)
        if len(raw_hex) % 2:
            raise ValueError(f"odd raw control token: {match.group(0)!r}")
        raw = bytes.fromhex(raw_hex)
        if not raw:
            raise ValueError("empty raw control token")
        try:
            suffix = raw[1:].decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError(f"non-ASCII control payload: {match.group(0)!r}") from exc
        return f"<${raw[0]:02X}>" + suffix

    return RAW_CONTROL_RE.sub(replace, text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("translation_memory", type=Path)
    parser.add_argument("codebook", type=Path)
    parser.add_argument("catalog_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--encoder",
        type=Path,
        default=Path(__file__).with_name("encode_custom_euc28.py"),
    )
    parser.add_argument(
        "--boundary-audit",
        type=Path,
        help=(
            "Optional verified boundary-audit JSON mapping scanner-corrupt TM IDs "
            "to exact structured table unit IDs."
        ),
    )
    args = parser.parse_args()

    memory = json.loads(args.translation_memory.read_text(encoding="utf-8"))
    codebook = json.loads(args.codebook.read_text(encoding="utf-8"))
    encoder = load_encoder(args.encoder)
    approved_units = [
        unit
        for unit in memory["units"]
        if str(unit.get("translation_ko", "")).strip()
        and unit.get("review_status") == "approved"
    ]
    translated = {
        str(unit["source_text"]): unit
        for unit in approved_units
        if unit.get("primary_surface") == "system_database"
    }
    translated_by_id = {
        str(unit["tm_id"]): unit
        for unit in approved_units
        if unit.get("primary_surface") == "system_database"
    }
    boundary_table_bindings: dict[str, dict[str, object]] = {}
    boundary_tm_ids: set[str] = set()
    if args.boundary_audit:
        boundary = json.loads(args.boundary_audit.read_text(encoding="utf-8"))
        for item in boundary.get("units", []):
            tm_id = str(item["tm_id"])
            tm_unit = translated_by_id.get(tm_id)
            if tm_unit is None:
                continue
            boundary_tm_ids.add(tm_id)
            application_mode = str(item.get("application_mode") or "tm_rewrite")
            table_target = str(tm_unit["translation_ko"])
            if application_mode == "table_specific_only":
                table_target = str(item.get("table_specific_translation_ko") or "")
                if not table_target:
                    raise ValueError(
                        f"table-specific boundary target is empty: {tm_id}"
                    )
            for table_unit_id in item.get("table_unit_ids", []):
                table_unit_id = str(table_unit_id)
                if table_unit_id in boundary_table_bindings:
                    raise ValueError(f"duplicate boundary table mapping: {table_unit_id}")
                boundary_table_bindings[table_unit_id] = {
                    "tm_unit": tm_unit,
                    "target": table_target,
                    "application_mode": application_mode,
                }

    global_encoding_errors: list[dict[str, object]] = []
    for tm_unit in approved_units:
        try:
            encoded_target = encoder.encode_text(str(tm_unit["translation_ko"]), codebook)
            if b"\0" in encoded_target:
                raise ValueError("encoded translation contains NUL")
        except Exception as exc:
            global_encoding_errors.append(
                {
                    "tm_id": tm_unit["tm_id"],
                    "primary_surface": tm_unit.get("primary_surface"),
                    "source_text": tm_unit["source_text"],
                    "translation_ko": tm_unit["translation_ko"],
                    "error": str(exc),
                }
            )

    results: list[dict[str, object]] = []
    unmatched: list[dict[str, object]] = []
    encoding_errors: list[dict[str, object]] = []
    matched_tm_ids: set[str] = set()
    fixed_overflows = 0
    resizable_in_place_overflows = 0

    available_catalogs = {path.name for path in args.catalog_dir.glob("*.json")}
    missing_catalogs = sorted(SYSTEM_CATALOG_FILENAMES - available_catalogs)
    if missing_catalogs:
        raise ValueError(f"missing required system catalogs: {missing_catalogs}")
    catalog_paths = sorted(
        (args.catalog_dir / name for name in SYSTEM_CATALOG_FILENAMES),
        key=lambda path: path.name,
    )
    for catalog_path in catalog_paths:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        schema = str(catalog.get("schema", catalog_path.stem))
        resizable = bool(catalog.get("metadata", {}).get("resizable_at_table_level"))
        for table_unit in catalog.get("units", []):
            source = str(table_unit.get("source_text", ""))
            if not source:
                continue
            canonical_source = canonicalize_table_controls(source)
            table_unit_id = str(table_unit.get("id"))
            boundary_binding = boundary_table_bindings.get(table_unit_id)
            matched_via_boundary_audit = boundary_binding is not None
            if boundary_binding is not None:
                tm_unit = boundary_binding["tm_unit"]
                target = str(boundary_binding["target"])
                application_mode = str(boundary_binding["application_mode"])
            else:
                tm_unit = translated.get(canonical_source)
                target = str(tm_unit["translation_ko"]) if tm_unit is not None else ""
                application_mode = "direct_source_match"
            if tm_unit is None:
                continue
            tm_id = str(tm_unit["tm_id"])
            matched_tm_ids.add(tm_id)
            try:
                encoded = encoder.encode_text(target, codebook)
            except Exception as exc:  # keep a complete preflight report
                encoding_errors.append(
                    {
                        "tm_id": tm_id,
                        "schema": schema,
                        "table_unit_id": table_unit.get("id"),
                        "error": str(exc),
                    }
                )
                continue

            if b"\0" in encoded:
                encoding_errors.append(
                    {
                        "tm_id": tm_id,
                        "schema": schema,
                        "table_unit_id": table_unit.get("id"),
                        "error": "encoded translation contains NUL",
                    }
                )
                continue

            raw_capacity = table_unit.get("capacity")
            if raw_capacity is None:
                raw_capacity = table_unit.get("in_place_capacity", 0)
            capacity = int(raw_capacity)
            required_with_nul = len(encoded) + 1
            fits_in_place = required_with_nul <= capacity
            if not fits_in_place:
                if resizable:
                    resizable_in_place_overflows += 1
                else:
                    fixed_overflows += 1
            results.append(
                {
                    "tm_id": tm_id,
                    "schema": schema,
                    "catalog": catalog_path.name,
                    "table_unit_id": table_unit.get("id"),
                    "source_text": canonical_source,
                    "translation_ko": target,
                    "encoded_bytes": len(encoded),
                    "required_with_nul": required_with_nul,
                    "capacity": capacity,
                    "headroom_after_nul": capacity - required_with_nul,
                    "fits_in_place": fits_in_place,
                    "table_resizable": resizable,
                    "matched_via_boundary_audit": matched_via_boundary_audit,
                    "boundary_application_mode": application_mode,
                }
            )

    # Approved units that occur on system_database but were not mapped to a
    # schema catalog need manual locator analysis rather than being silently
    # treated as fitting.
    for unit in memory["units"]:
        if (
            unit.get("review_status") == "approved"
            and unit.get("primary_surface") == "system_database"
            and str(unit["tm_id"]) not in matched_tm_ids
        ):
            unmatched.append(
                {
                    "tm_id": unit["tm_id"],
                    "source_text": unit["source_text"],
                    "translation_ko": unit["translation_ko"],
                    "sample_contexts": unit.get("sample_contexts", [])[:3],
                }
            )

    by_schema = Counter(str(item["schema"]) for item in results)
    overflow_items = [item for item in results if not item["fits_in_place"]]
    report = {
        "schema": "arf-approved-translation-fit-preflight-v1",
        "translation_memory": str(args.translation_memory.resolve()),
        "translation_memory_sha256": sha256(args.translation_memory),
        "codebook": str(args.codebook.resolve()),
        "codebook_sha256": sha256(args.codebook),
        "catalog_dir": str(args.catalog_dir.resolve()),
        "catalog_tree_sha256": catalog_tree_sha256(catalog_paths),
        "catalog_artifacts": [
            {
                "name": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in catalog_paths
        ],
        "encoder": str(args.encoder.resolve()),
        "encoder_sha256": sha256(args.encoder),
        "approved_tm_units": len(approved_units),
        "matched_unique_tm_units": len(matched_tm_ids),
        "matched_table_fields": len(results),
        "matched_fields_by_schema": dict(sorted(by_schema.items())),
        "fixed_overflow_count": fixed_overflows,
        "resizable_table_in_place_overflow_count": resizable_in_place_overflows,
        "unmatched_system_tm_count": len(unmatched),
        "encoding_error_count": len(encoding_errors),
        "global_encoding_error_count": len(global_encoding_errors),
        "known_fixed_fields_fit": (
            fixed_overflows == 0 and not encoding_errors and not global_encoding_errors
        ),
        "safe_for_fixed_table_insertion": (
            fixed_overflows == 0
            and not encoding_errors
            and not global_encoding_errors
            and not unmatched
        ),
        "overflow_fields": overflow_items,
        "unmatched_system_units": unmatched,
        "encoding_errors": encoding_errors,
        "global_encoding_errors": global_encoding_errors,
        "translation_engine_policy": "Codex internal models only",
        "boundary_audit": str(args.boundary_audit.resolve()) if args.boundary_audit else None,
        "boundary_audit_sha256": sha256(args.boundary_audit)
        if args.boundary_audit
        else None,
        "boundary_audit_tm_units_matched": len(boundary_tm_ids & matched_tm_ids),
        "boundary_audit_table_fields_matched": sum(
            bool(item.get("matched_via_boundary_audit")) for item in results
        ),
        "table_specific_boundary_fields_matched": sum(
            item.get("boundary_application_mode") == "table_specific_only"
            for item in results
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "approved_tm_units",
                    "matched_unique_tm_units",
                    "matched_table_fields",
                    "fixed_overflow_count",
                    "resizable_table_in_place_overflow_count",
                    "unmatched_system_tm_count",
                    "encoding_error_count",
                    "global_encoding_error_count",
                    "known_fixed_fields_fit",
                    "safe_for_fixed_table_insertion",
                )
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["safe_for_fixed_table_insertion"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
