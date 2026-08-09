#!/usr/bin/env python3
"""Regression checks for the Arc Rise Fantasia EUC28 font pipeline."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--wtmd-tool", type=Path, required=True)
    p.add_argument("--mapping-tool", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    wtmd = load_module("arf_wtmd_verify", args.wtmd_tool)
    mapping = load_module("arf_mapping_verify", args.mapping_tool)
    result = {"noop_roundtrip": [], "mapping_landmarks": []}

    for page in range(9):
        path = args.source_dir / f"EUC28-{page}.wtm"
        data = path.read_bytes()
        rebuilt, info = wtmd.exact_noop(data, str(path))
        h = wtmd.parse_header(data, str(path))
        info.update(
            {
                "file": path.name,
                "width": h.width,
                "height": h.height,
                "format": h.gx_format_name,
                "palette": h.palette_format_name,
                "image_offset": h.image_offset,
            }
        )
        result["noop_roundtrip"].append(info)

    landmarks = {
        "A1A2": ("、", 2, 0, 2, 44, 0),
        "A3B0": ("０", 208, 0, 208, 22, 252),
        "A4A1": ("ぁ", 289, 0, 289, 286, 336),
        "A5A1": ("ァ", 385, 0, 385, 374, 448),
        "A6A1": ("Α", 481, 0, 481, 462, 560),
        "A7A1": ("А", 577, 0, 577, 44, 700),
        "A8A1": ("─", 673, 0, 673, 132, 812),
        "B0A1": ("亜", 721, 0, 721, 176, 868),
        "B1A1": ("院", 817, 0, 817, 264, 980),
        "B1AC": ("卯", 828, 1, 0, 0, 0),
        "F4A6": ("熙", 7254, 8, 630, 198, 756),
    }
    for hex_pair, (char, expected_slot, page, local, x, y) in landmarks.items():
        encoded = bytes.fromhex(hex_pair)
        slot = mapping.pair_to_global_slot(encoded[0], encoded[1])
        loc = mapping.global_slot_to_location(slot)
        ok = (
            encoded.decode("euc_jp") == char
            and slot == expected_slot
            and loc["page"] == page
            and loc["local_slot"] == local
            and loc["x"] == x
            and loc["y"] == y
        )
        result["mapping_landmarks"].append(
            {"bytes_hex": hex_pair, "character": char, **loc, "pass": ok}
        )

    result["summary"] = {
        "noop_files": len(result["noop_roundtrip"]),
        "noop_exact": all(r["exact_match"] for r in result["noop_roundtrip"]),
        "landmarks": len(result["mapping_landmarks"]),
        "landmarks_pass": all(r["pass"] for r in result["mapping_landmarks"]),
    }
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not all(result["summary"].values()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
