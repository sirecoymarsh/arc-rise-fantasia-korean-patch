#!/usr/bin/env python3
"""Read-only audit of ARF fixed-table text spans and protected record bytes.

This diagnostic intentionally does not rebuild any release artifact.  It compares
the trusted source payloads with the current final table payloads using a
separately declared, audited record layout.  The declaration is deliberately
independent of ``arf_table_tool.FIXED`` so a bad writer schema cannot approve its
own damage.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class TextSpan:
    name: str
    offset: int
    size: int


@dataclass(frozen=True)
class Layout:
    stem: str
    record_size: int
    record_count: int
    spans: tuple[TextSpan, ...]


# Audited minimal writable spans.  Everything else in a record is protected.
# In particular, these do not repeat the five over-wide spans in the current
# table tool (item/shop/special/help/monster_book).
LAYOUTS = (
    Layout("item", 255, 772, (
        TextSpan("name", 0, 17),
        TextSpan("description_primary", 17, 81),
        TextSpan("description_secondary", 98, 81),
    )),
    Layout("shop", 86, 47, (TextSpan("name", 0, 20),)),
    Layout("dragon", 279, 13, (
        TextSpan("name", 0, 24), TextSpan("skill_name", 24, 48),
        TextSpan("lore", 72, 97), TextSpan("passive_description", 169, 49),
        TextSpan("battle_description", 218, 49),
    )),
    Layout("treasure", 49, 256, (TextSpan("display_name", 23, 21),)),
    Layout("magic", 164, 49, (
        TextSpan("menu_name", 0, 20), TextSpan("battle_name", 20, 40),
        TextSpan("description", 60, 80),
    )),
    Layout("special", 144, 76, (
        TextSpan("name", 0, 22), TextSpan("description", 22, 83),
    )),
    Layout("operation", 120, 8, (
        TextSpan("name", 0, 24), TextSpan("description", 24, 96),
    )),
    Layout("ability", 146, 250, (
        TextSpan("name", 0, 21), TextSpan("description", 21, 81),
    )),
    Layout("todo", 144, 208, (
        TextSpan("lead", 16, 64), TextSpan("objective", 80, 64),
    )),
    Layout("help", 347, 380, (
        TextSpan("title", 0, 21), TextSpan("description", 21, 322),
    )),
    Layout("monster_book", 644, 274, (
        TextSpan("name", 0, 35), TextSpan("location", 260, 96),
    )),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def protected_mask(layout: Layout) -> list[bool]:
    mask = [True] * layout.record_size
    for span in layout.spans:
        if not (0 <= span.offset < span.offset + span.size <= layout.record_size):
            raise ValueError(f"invalid span: {layout.stem}:{span}")
        for pos in range(span.offset, span.offset + span.size):
            if not mask[pos]:
                raise ValueError(f"overlapping span: {layout.stem}:{span}")
            mask[pos] = False
    return mask


def contiguous_ranges(mask: list[bool]) -> list[list[int]]:
    out: list[list[int]] = []
    start: int | None = None
    for index, value in enumerate(mask + [False]):
        if value and start is None:
            start = index
        elif not value and start is not None:
            out.append([start, index])
            start = None
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "work/runtime_validation/fixed_table_geometry_audit.json",
    )
    args = parser.parse_args()

    table_tool = load_module(
        "arf_table_tool_geometry_audit",
        ROOT / "work/research/table_agent/arf_table_tool.py",
    )
    catalogs_dir = ROOT / "work/research/table_agent/catalogs"
    replacement_dir = ROOT / "work/final_system_table_application/replacement_catalogs"
    payload_dir = ROOT / "work/final_system_table_application/payloads"

    layout_reports: list[dict[str, Any]] = []
    total_protected_changed_bytes = 0
    total_protected_changed_records = 0
    for layout in LAYOUTS:
        catalog_path = catalogs_dir / f"{layout.stem}.json"
        replacement_path = replacement_dir / f"{layout.stem}.json"
        payload_path = payload_dir / (
            "todo.dat" if layout.stem == "todo" else f"{layout.stem}.bin"
        )
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        replacement_catalog = json.loads(replacement_path.read_text(encoding="utf-8"))
        source_path = Path(str(catalog["source_path"]))
        source = source_path.read_bytes()
        payload = payload_path.read_bytes()
        expected_size = layout.record_size * layout.record_count
        if len(source) != expected_size or len(payload) != expected_size:
            raise ValueError(f"size mismatch: {layout.stem}")

        mask = protected_mask(layout)
        changed_positions: Counter[int] = Counter()
        changed_records: set[int] = set()
        samples: list[dict[str, int]] = []
        for record in range(layout.record_count):
            base = record * layout.record_size
            for pos, protected in enumerate(mask):
                if protected and source[base + pos] != payload[base + pos]:
                    changed_positions[pos] += 1
                    changed_records.add(record)
                    if len(samples) < 40:
                        samples.append({
                            "record": record,
                            "record_offset": pos,
                            "source": source[base + pos],
                            "payload": payload[base + pos],
                        })

        replacement_by_field: dict[str, list[dict[str, Any]]] = {}
        for unit in replacement_catalog["units"]:
            if unit.get("replacement_tm_id"):
                replacement_by_field.setdefault(str(unit["field"]), []).append(unit)

        span_reports: list[dict[str, Any]] = []
        current_schema = table_tool.FIXED[
            "todo.dat" if layout.stem == "todo" else f"{layout.stem}.bin"
        ]
        current_by_name = {field.name: field for field in current_schema.fields}
        for span in layout.spans:
            source_lengths: list[int] = []
            unterminated: list[int] = []
            nonzero_after_nul_records: list[int] = []
            for record in range(layout.record_count):
                base = record * layout.record_size + span.offset
                blob = source[base : base + span.size]
                end = blob.find(b"\0")
                if end < 0:
                    end = span.size
                    unterminated.append(record)
                elif any(blob[end + 1 :]):
                    nonzero_after_nul_records.append(record)
                source_lengths.append(end)
            replacements = replacement_by_field.get(span.name, [])
            replacement_lengths = [
                len(bytes.fromhex(str(unit["replacement_hex"])))
                for unit in replacements
            ]
            current = current_by_name[span.name]
            span_reports.append({
                "field": span.name,
                "offset": span.offset,
                "audited_size": span.size,
                "audited_end_exclusive": span.offset + span.size,
                "current_tool_size": current.capacity,
                "schema_size_delta": int(current.capacity) - span.size,
                "source_max_bytes": max(source_lengths),
                "source_unterminated_records": unterminated,
                "source_nonzero_after_first_nul_within_audited_span_records": (
                    nonzero_after_nul_records
                ),
                "replacement_fields": len(replacements),
                "replacement_max_bytes": max(replacement_lengths) if replacement_lengths else 0,
                "replacement_exact_span_count": sum(
                    size == span.size for size in replacement_lengths
                ),
                "replacement_c_string_overflow_count": sum(
                    size >= span.size for size in replacement_lengths
                ),
            })

        protected_changed_bytes = sum(changed_positions.values())
        total_protected_changed_bytes += protected_changed_bytes
        total_protected_changed_records += len(changed_records)
        layout_reports.append({
            "schema": layout.stem,
            "record_size": layout.record_size,
            "record_count": layout.record_count,
            "source_path": str(source_path),
            "source_sha256": sha256_bytes(source),
            "payload_path": str(payload_path),
            "payload_sha256": sha256_bytes(payload),
            "audited_text_spans": span_reports,
            "protected_ranges_half_open": contiguous_ranges(mask),
            "protected_changed_bytes": protected_changed_bytes,
            "protected_changed_records": len(changed_records),
            "protected_changed_positions": {
                str(key): value for key, value in sorted(changed_positions.items())
            },
            "protected_change_samples": samples,
            "protected_bytes_preserved": protected_changed_bytes == 0,
        })

    item_source = Path(
        json.loads((catalogs_dir / "item.json").read_text(encoding="utf-8"))["source_path"]
    ).read_bytes()
    item_payload = (payload_dir / "item.bin").read_bytes()
    source_ids = [
        int.from_bytes(item_source[index * 255 + 179 : index * 255 + 181], "big")
        for index in range(772)
    ]
    payload_ids = [
        int.from_bytes(item_payload[index * 255 + 179 : index * 255 + 181], "big")
        for index in range(772)
    ]
    source_id_mismatches = [index for index, value in enumerate(source_ids) if index != value]
    payload_id_mismatches = [index for index, value in enumerate(payload_ids) if index != value]
    payload_id_counts = Counter(payload_ids)

    item_catalog = json.loads((replacement_dir / "item.json").read_text(encoding="utf-8"))
    item_replacements = [unit for unit in item_catalog["units"] if unit.get("replacement_tm_id")]
    source_render_mismatches = [
        str(unit["id"])
        for unit in item_catalog["units"]
        if table_tool.render_mixed(bytes.fromhex(str(unit["raw_hex"])))
        != str(unit["source_text"])
    ]
    source_decode_marker_units = [
        str(unit["id"])
        for unit in item_catalog["units"]
        if "<#" in str(unit["source_text"])
    ]
    control_mismatches: list[dict[str, Any]] = []
    for unit in item_replacements:
        actual = table_tool.control_signature(bytes.fromhex(unit["replacement_hex"]))
        expected = list(unit["control_signature"])
        if actual != expected:
            control_mismatches.append({"id": unit["id"], "expected": expected, "actual": actual})

    codebook = json.loads((ROOT / "work/font/final_v2/codebook.json").read_text(encoding="utf-8"))
    pairs = [str(value["bytes_hex"]).upper() for value in codebook["characters"].values()]
    reserved = {
        line.strip().upper()
        for line in (ROOT / "work/font/original_reserved_pairs_v2.txt").read_text(
            encoding="ascii"
        ).splitlines()
        if line.strip()
    }
    invalid_pairs = [
        pair for pair in pairs
        if len(pair) != 4
        or not (0xB0 <= int(pair[:2], 16) <= 0xF4)
        or not (0xA1 <= int(pair[2:], 16) <= 0xFE)
    ]

    proof = json.loads(
        (ROOT / "work/final_system_table_application/application_proof.json").read_text(
            encoding="utf-8"
        )
    )
    item_proof = next(item for item in proof["payloads"] if item["catalog"] == "item.json")
    report = {
        "schema": "arf-fixed-table-geometry-audit-v1",
        "read_only": True,
        "valid": total_protected_changed_bytes == 0,
        "summary": {
            "schemas_audited": len(layout_reports),
            "schemas_with_protected_changes": sum(
                not item["protected_bytes_preserved"] for item in layout_reports
            ),
            "protected_changed_bytes_sum": total_protected_changed_bytes,
            "protected_changed_record_counts_sum_non_deduplicated": (
                total_protected_changed_records
            ),
        },
        "item_record_id_invariant": {
            "offset": 179,
            "width": 2,
            "endianness": "big",
            "expected": "record index",
            "source_mismatch_count": len(source_id_mismatches),
            "source_mismatch_sample": source_id_mismatches[:20],
            "payload_mismatch_count": len(payload_id_mismatches),
            "payload_mismatch_sample": [
                {"record": index, "payload_id": payload_ids[index]}
                for index in payload_id_mismatches[:40]
            ],
            "payload_duplicate_id_groups": sum(count > 1 for count in payload_id_counts.values()),
            "payload_duplicate_id_excess": sum(
                count - 1 for count in payload_id_counts.values() if count > 1
            ),
            "payload_missing_ids": [index for index in range(772) if index not in payload_id_counts],
        },
        "item_encoding_checks": {
            "replacement_fields": len(item_replacements),
            "source_catalog_render_mismatches": source_render_mismatches,
            "source_catalog_decode_marker_units": source_decode_marker_units,
            "control_signature_mismatches": control_mismatches,
            "codebook_assigned": len(pairs),
            "codebook_duplicate_pairs": len(pairs) - len(set(pairs)),
            "codebook_invalid_custom_pairs": invalid_pairs,
            "codebook_reserved_v2_collisions": sorted(set(pairs) & reserved),
        },
        "proof_self_schema_false_negative": {
            "proof_valid": proof["valid"],
            "item_claimed_changes_outside_declared_slots": item_proof[
                "changes_outside_declared_slots"
            ],
            "independent_item_protected_changed_bytes": next(
                item["protected_changed_bytes"]
                for item in layout_reports
                if item["schema"] == "item"
            ),
        },
        "layouts": layout_reports,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"item payload ID mismatches: {len(payload_id_mismatches)}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
