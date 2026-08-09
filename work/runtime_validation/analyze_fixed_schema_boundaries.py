#!/usr/bin/env python3
"""Read-only boundary audit for every fixed non-BSCR table schema.

The existing catalogs are treated as evidence, not as ground truth: this audit
checks whether a declared text capacity overlaps bytes that behave as record
metadata and whether the localized payload actually changed those bytes.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / "work/final_system_table_application/application_proof.json"
CATALOG_DIR = ROOT / "work/final_system_table_application/replacement_catalogs"
OUTPUT = ROOT / "work/runtime_validation/fixed_schema_boundary_audit.json"

# Capacities independently established from the first dense binary field, not
# from the old catalog. All unlisted field capacities remain unchanged.
CORRECTED_CAPACITIES = {
    ("item", "description_secondary"): 81,
    ("shop", "name"): 20,
    ("special", "description"): 83,
    ("help", "description"): 322,
    ("monster_book", "name"): 35,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def nul_position(blob: bytes) -> int | None:
    pos = blob.find(b"\0")
    return None if pos < 0 else pos


def byte_distribution(data: bytes, record_size: int, count: int, offset: int, header: int = 0) -> dict[str, int]:
    values = Counter(data[header + record * record_size + offset] for record in range(count))
    return {f"0x{value:02X}": amount for value, amount in sorted(values.items())}


def main() -> int:
    proof = json.loads(PROOF.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    total_outside_bytes = 0
    total_outside_records = 0

    for payload in proof["payloads"]:
        catalog = json.loads((CATALOG_DIR / payload["catalog"]).read_text(encoding="utf-8"))
        metadata = catalog.get("metadata", {})
        if "fields" not in metadata:
            continue
        schema = payload["schema"]
        source_path = Path(payload["source_path"])
        output_path = ROOT / Path(payload["output_path"])
        source = source_path.read_bytes()
        output = output_path.read_bytes()
        record_size = int(metadata["record_size"])
        record_count = int(metadata["record_count"])
        header = int(metadata.get("header_size", 0))
        assert len(source) == header + record_size * record_count
        assert len(output) == len(source)
        units = {unit["id"]: unit for unit in catalog["units"]}

        field_results: list[dict[str, Any]] = []
        safe_ranges: list[tuple[int, int]] = []
        for field in metadata["fields"]:
            name = field["name"]
            offset = int(field["offset"])
            declared = int(field["capacity"])
            corrected = CORRECTED_CAPACITIES.get((schema, name), declared)
            safe_ranges.append((offset, offset + corrected))
            source_nuls: list[int | None] = []
            output_nuls: list[int | None] = []
            changed_fields = 0
            erased_after_nul: list[dict[str, Any]] = []
            overlap_changes: list[dict[str, Any]] = []
            fit_violations: list[dict[str, Any]] = []
            corrected_unterminated_source: list[dict[str, Any]] = []
            max_effective_length = 0

            for record in range(record_count):
                base = header + record * record_size
                source_blob = source[base + offset : base + offset + declared]
                output_blob = output[base + offset : base + offset + declared]
                source_nul = nul_position(source_blob)
                output_nul = nul_position(output_blob)
                source_nuls.append(source_nul)
                output_nuls.append(output_nul)
                changed_fields += source_blob != output_blob
                source_logical_end = declared if source_nul is None else source_nul
                if source_nul is not None:
                    erased = [
                        {
                            "relative_offset": pos,
                            "absolute_offset": base + offset + pos,
                            "source_hex": f"{source_blob[pos]:02X}",
                            "output_hex": f"{output_blob[pos]:02X}",
                        }
                        for pos in range(source_nul + 1, declared)
                        if source_blob[pos] and source_blob[pos] != output_blob[pos]
                    ]
                    if erased:
                        erased_after_nul.append({"record": record, "bytes": erased})

                overlap = [
                    {
                        "relative_offset": pos,
                        "record_offset": offset + pos,
                        "absolute_offset": base + offset + pos,
                        "source_hex": f"{source_blob[pos]:02X}",
                        "output_hex": f"{output_blob[pos]:02X}",
                    }
                    for pos in range(corrected, declared)
                    if source_blob[pos] != output_blob[pos]
                ]
                if overlap:
                    overlap_changes.append({"record": record, "bytes": overlap})

                unit = units[f"{schema}:{record}:{name}"]
                effective = bytes.fromhex(unit["replacement_hex"]) if unit.get("replacement_hex") else bytes.fromhex(unit["raw_hex"])
                max_effective_length = max(max_effective_length, len(effective))
                if len(effective) >= corrected:
                    fit_violations.append({
                        "record": record,
                        "id": unit["id"],
                        "effective_byte_length": len(effective),
                        "corrected_capacity": corrected,
                        "source_text": unit["source_text"],
                        "replacement_tm_id": unit.get("replacement_tm_id"),
                        "replacement_hex": unit.get("replacement_hex", ""),
                    })
                corrected_source_blob = source[base + offset : base + offset + corrected]
                if b"\0" not in corrected_source_blob:
                    corrected_unterminated_source.append({
                        "record": record,
                        "id": unit["id"],
                        "raw_hex": corrected_source_blob.hex().upper(),
                        "source_text": unit["source_text"],
                    })

            field_results.append({
                "field": name,
                "offset": offset,
                "declared_capacity": declared,
                "corrected_safe_capacity": corrected,
                "metadata_overlap": None if corrected == declared else {
                    "record_offset_start": offset + corrected,
                    "record_offset_end_exclusive": offset + declared,
                    "size": declared - corrected,
                    "source_byte_distributions": [
                        {
                            "record_offset": offset + pos,
                            "distribution": byte_distribution(source, record_size, record_count, offset + pos, header),
                        }
                        for pos in range(corrected, declared)
                    ],
                },
                "source_nul_min": min(pos for pos in source_nuls if pos is not None),
                "source_nul_max": max(pos for pos in source_nuls if pos is not None),
                "source_unterminated_under_declared_capacity": sum(pos is None for pos in source_nuls),
                "output_nul_min": min(pos for pos in output_nuls if pos is not None),
                "output_nul_max": max(pos for pos in output_nuls if pos is not None),
                "output_unterminated_under_declared_capacity": sum(pos is None for pos in output_nuls),
                "changed_field_count": changed_fields,
                "max_effective_payload_length": max_effective_length,
                "erased_nonzero_after_source_nul_record_count": len(erased_after_nul),
                "erased_nonzero_after_source_nul_byte_count": sum(len(item["bytes"]) for item in erased_after_nul),
                "erased_nonzero_after_source_nul": erased_after_nul,
                "metadata_overlap_changed_record_count": len(overlap_changes),
                "metadata_overlap_changed_byte_count": sum(len(item["bytes"]) for item in overlap_changes),
                "metadata_overlap_changes": overlap_changes,
                "corrected_capacity_fit_violation_count": len(fit_violations),
                "corrected_capacity_fit_violations": fit_violations,
                "source_unterminated_under_corrected_capacity_count": len(corrected_unterminated_source),
                "source_unterminated_under_corrected_capacity": corrected_unterminated_source,
            })

        # Every payload edit outside the corrected text ranges is unexpected.
        outside: list[dict[str, Any]] = []
        for record in range(record_count):
            base = header + record * record_size
            record_changes = []
            for relative in range(record_size):
                in_text = any(start <= relative < end for start, end in safe_ranges)
                absolute = base + relative
                if not in_text and source[absolute] != output[absolute]:
                    record_changes.append({
                        "record_offset": relative,
                        "absolute_offset": absolute,
                        "source_hex": f"{source[absolute]:02X}",
                        "output_hex": f"{output[absolute]:02X}",
                    })
            if record_changes:
                outside.append({"record": record, "bytes": record_changes})
        outside_byte_count = sum(len(item["bytes"]) for item in outside)
        total_outside_bytes += outside_byte_count
        total_outside_records += len(outside)

        results.append({
            "schema": schema,
            "source_path": str(source_path),
            "source_sha256": sha(source),
            "output_path": str(output_path.relative_to(ROOT)),
            "output_sha256": sha(output),
            "record_size": record_size,
            "record_count": record_count,
            "fields": field_results,
            "changes_outside_corrected_text_ranges_record_count": len(outside),
            "changes_outside_corrected_text_ranges_byte_count": outside_byte_count,
            "changes_outside_corrected_text_ranges": outside,
        })

    by_schema = {result["schema"]: result for result in results}
    # Compact, human-checkable boundary witnesses.
    item_source = Path(next(p for p in proof["payloads"] if p["schema"] == "item")["source_path"]).read_bytes()
    shop_source = Path(next(p for p in proof["payloads"] if p["schema"] == "shop")["source_path"]).read_bytes()
    special_source = Path(next(p for p in proof["payloads"] if p["schema"] == "special")["source_path"]).read_bytes()
    help_source = Path(next(p for p in proof["payloads"] if p["schema"] == "help")["source_path"]).read_bytes()
    monster_source = Path(next(p for p in proof["payloads"] if p["schema"] == "monster_book")["source_path"]).read_bytes()
    witnesses = {
        "item": {
            "interpretation": "record offsets 179..180 are a unique big-endian item ID; high byte groups are 256x0, 256x1, 256x2, 4x3",
            "source_high_byte_distribution": byte_distribution(item_source, 255, 772, 179),
            "source_unique_u16_ids": len({int.from_bytes(item_source[r * 255 + 179 : r * 255 + 181], "big") for r in range(772)}),
            "samples": {str(r): item_source[r * 255 + 179 : r * 255 + 183].hex().upper() for r in (0, 255, 256, 511, 512, 767, 768, 771)},
        },
        "shop": {
            "interpretation": "record offset 20 begins a big-endian u16 merchandise-ID array",
            "samples": {str(r): shop_source[r * 86 + 20 : r * 86 + 32].hex().upper() for r in (5, 8, 11, 14, 19, 22, 42, 43)},
        },
        "special": {
            "interpretation": "record offset 105 is the first byte of the dense 39-byte battle metadata tail",
            "samples": {str(r): special_source[r * 144 + 100 : r * 144 + 116].hex().upper() for r in (9, 15, 56)},
        },
        "help": {
            "interpretation": "record offsets 343..346 form a 4-byte display/classification metadata word; only offset 346 was previously recognized",
            "samples": {str(r): help_source[r * 347 + 343 : r * 347 + 347].hex().upper() for r in (0, 7, 9, 18, 19, 49, 100, 200, 300, 379)},
        },
        "monster_book": {
            "interpretation": "record offset 35 is a group/level byte immediately followed by dense monster statistics beginning at offset 36",
            "samples": {str(r): monster_source[r * 644 + 35 : r * 644 + 44].hex().upper() for r in (0, 28, 29, 36, 37, 100, 200, 273)},
        },
    }

    report = {
        "schema": "arf-fixed-schema-boundary-audit-v1",
        "proof_input": str(PROOF.relative_to(ROOT)),
        "proof_sha256": sha(PROOF.read_bytes()),
        "corrected_capacities": [
            {"schema": schema, "field": field, "capacity": capacity}
            for (schema, field), capacity in sorted(CORRECTED_CAPACITIES.items())
        ],
        "summary": {
            "fixed_schema_count": len(results),
            "schemas_with_changes_outside_corrected_text_ranges": [
                result["schema"] for result in results if result["changes_outside_corrected_text_ranges_byte_count"]
            ],
            "total_changes_outside_corrected_text_ranges_record_count_across_files": total_outside_records,
            "total_changes_outside_corrected_text_ranges_byte_count": total_outside_bytes,
            "schemas_without_detected_metadata_corruption": [
                result["schema"] for result in results if not result["changes_outside_corrected_text_ranges_byte_count"]
            ],
        },
        "boundary_witnesses": witnesses,
        "schemas": results,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "summary": report["summary"],
        "corrected_fields": [
            {
                "schema": schema,
                "field": field,
                "declared": next(f for f in by_schema[schema]["fields"] if f["field"] == field)["declared_capacity"],
                "corrected": capacity,
                "corrupted_records": next(f for f in by_schema[schema]["fields"] if f["field"] == field)["metadata_overlap_changed_record_count"],
                "corrupted_bytes": next(f for f in by_schema[schema]["fields"] if f["field"] == field)["metadata_overlap_changed_byte_count"],
                "fit_violations": next(f for f in by_schema[schema]["fields"] if f["field"] == field)["corrected_capacity_fit_violation_count"],
            }
            for (schema, field), capacity in sorted(CORRECTED_CAPACITIES.items())
        ],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
