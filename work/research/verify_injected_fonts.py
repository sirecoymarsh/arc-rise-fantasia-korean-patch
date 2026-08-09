#!/usr/bin/env python3
"""Verify canonical ARF Korean codebook and injected WTMD font copies."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--injected-dir", type=Path, required=True)
    parser.add_argument("--codebook", type=Path, required=True)
    parser.add_argument("--reserved-hex", type=Path, required=True)
    parser.add_argument("--approved-units", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--mapping-tool", type=Path, required=True)
    parser.add_argument("--wtmd-tool", type=Path, required=True)
    parser.add_argument("--encoder", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    mapping_tool = load_module("arf_mapping_verify", args.mapping_tool)
    wtmd = load_module("arf_wtmd_verify", args.wtmd_tool)
    encoder = load_module("arf_encoder_verify", args.encoder)
    codebook = json.loads(args.codebook.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    reserved = {
        token.strip().upper()
        for token in args.reserved_hex.read_text(encoding="utf-8").split()
        if token.strip()
    }
    characters = codebook["characters"]
    errors: list[dict[str, object]] = []

    byte_pairs = [str(entry["bytes_hex"]).upper() for entry in characters.values()]
    if len(characters) != int(codebook["assigned"]):
        errors.append({"code": "assigned_count_mismatch"})
    if len(byte_pairs) != len(set(byte_pairs)):
        errors.append({"code": "duplicate_codebook_pair"})
    collisions = sorted(set(byte_pairs) & reserved)
    if collisions:
        errors.append({"code": "reserved_pair_collision", "sample": collisions[:20]})

    manifest_by_page = {int(item["page"]): item for item in manifest["files"]}
    assigned_by_page: dict[int, list[tuple[str, dict[str, object]]]] = {}
    for char, entry in characters.items():
        pair = bytes.fromhex(str(entry["bytes_hex"]))
        expected_slot = mapping_tool.pair_to_global_slot(pair[0], pair[1])
        expected = mapping_tool.global_slot_to_location(expected_slot)
        for key in ("global_slot", "page", "local_slot", "column", "row", "x", "y"):
            if int(entry[key]) != int(expected[key]):
                errors.append(
                    {
                        "code": "mapping_coordinate_mismatch",
                        "character": char,
                        "field": key,
                    }
                )
        assigned_by_page.setdefault(int(entry["page"]), []).append((char, entry))

    page_results: list[dict[str, object]] = []
    total_changed_pixels = 0
    assigned_cells_without_change: list[str] = []
    for page in range(9):
        source_path = args.source_dir / f"EUC28-{page}.wtm"
        output_path = args.injected_dir / f"EUC28-{page}.wtm"
        source_data = source_path.read_bytes()
        output_data = output_path.read_bytes()
        source_header, source_palette, source_indices = wtmd.decode_wtmd(
            source_data, str(source_path)
        )
        output_header, output_palette, output_indices = wtmd.decode_wtmd(
            output_data, str(output_path)
        )
        header_palette_preserved = (
            source_data[: source_header.image_offset]
            == output_data[: output_header.image_offset]
        )
        size_preserved = len(source_data) == len(output_data)
        if not header_palette_preserved:
            errors.append({"code": "header_or_palette_changed", "page": page})
        if not size_preserved:
            errors.append({"code": "font_size_changed", "page": page})
        if source_palette != output_palette:
            errors.append({"code": "decoded_palette_changed", "page": page})

        allowed_pixels: set[int] = set()
        cell_changes: dict[str, int] = {}
        for char, entry in assigned_by_page.get(page, []):
            x0, y0 = int(entry["x"]), int(entry["y"])
            pixels = {
                (y0 + y) * source_header.width + (x0 + x)
                for y in range(mapping_tool.CELL_HEIGHT)
                for x in range(mapping_tool.CELL_WIDTH)
            }
            allowed_pixels.update(pixels)
            changed = sum(source_indices[i] != output_indices[i] for i in pixels)
            cell_changes[char] = changed
            if changed == 0:
                assigned_cells_without_change.append(char)

        changed_pixels = {
            i
            for i, (before, after) in enumerate(zip(source_indices, output_indices))
            if before != after
        }
        outside = changed_pixels - allowed_pixels
        if outside:
            errors.append(
                {
                    "code": "pixels_changed_outside_assigned_cells",
                    "page": page,
                    "count": len(outside),
                    "sample": sorted(outside)[:20],
                }
            )
        total_changed_pixels += len(changed_pixels)
        rebuilt_payload = wtmd.encode_c4_indices(
            output_indices, output_header.width, output_header.height
        )
        expected_payload = output_data[
            output_header.image_offset : output_header.image_offset
            + output_header.width * output_header.height // 2
        ]
        redecode_reencode_exact = rebuilt_payload == expected_payload
        if not redecode_reencode_exact:
            errors.append({"code": "output_reencode_mismatch", "page": page})

        manifest_item = manifest_by_page.get(page, {})
        manifest_hashes_match = (
            manifest_item.get("source_sha256") == sha256(source_path)
            and manifest_item.get("output_sha256") == sha256(output_path)
        )
        if not manifest_hashes_match:
            errors.append({"code": "injection_manifest_hash_mismatch", "page": page})
        page_results.append(
            {
                "page": page,
                "assigned_cells": len(assigned_by_page.get(page, [])),
                "changed_pixels": len(changed_pixels),
                "changes_outside_assigned_cells": len(outside),
                "size_preserved": size_preserved,
                "header_palette_preserved": header_palette_preserved,
                "redecode_reencode_exact": redecode_reencode_exact,
                "manifest_hashes_match": manifest_hashes_match,
            }
        )

    if assigned_cells_without_change:
        errors.append(
            {
                "code": "assigned_cells_without_pixel_change",
                "count": len(assigned_cells_without_change),
                "sample": assigned_cells_without_change[:20],
            }
        )

    encoding_errors: list[dict[str, str]] = []
    encoded_units = 0
    for line in args.approved_units.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        unit = json.loads(line)
        try:
            encoded = encoder.encode_text(str(unit["translation_ko"]), codebook)
            if b"\0" in encoded:
                raise ValueError("encoded payload contains NUL")
            encoded_units += 1
        except Exception as exc:
            encoding_errors.append({"tm_id": str(unit["tm_id"]), "error": str(exc)})
    if encoding_errors:
        errors.append(
            {
                "code": "approved_translation_encoding_errors",
                "count": len(encoding_errors),
                "sample": encoding_errors[:20],
            }
        )

    report = {
        "schema": "arf-canonical-korean-font-injection-verification-v1",
        "translation_engine_policy": "Codex internal models only",
        "codebook_sha256": sha256(args.codebook),
        "injection_manifest_sha256": sha256(args.manifest),
        "reserved_hex_sha256": sha256(args.reserved_hex),
        "approved_units_sha256": sha256(args.approved_units),
        "mapping_tool_sha256": sha256(args.mapping_tool),
        "wtmd_tool_sha256": sha256(args.wtmd_tool),
        "encoder_sha256": sha256(args.encoder),
        "assigned_characters": len(characters),
        "reserved_source_pairs": len(reserved),
        "reserved_pair_collisions": len(collisions),
        "approved_units_encoded": encoded_units,
        "approved_unit_encoding_errors": len(encoding_errors),
        "assigned_cells_without_pixel_change": len(assigned_cells_without_change),
        "total_changed_pixels": total_changed_pixels,
        "pages": page_results,
        "error_count": len(errors),
        "errors": errors,
        "valid": not errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "assigned_characters",
                    "reserved_source_pairs",
                    "approved_units_encoded",
                    "assigned_cells_without_pixel_change",
                    "total_changed_pixels",
                    "error_count",
                    "valid",
                )
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
