#!/usr/bin/env python3
"""Extract every nested WTMD texture from if_resident_vol.cxd for UI residue review."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "image_ui_final" / "tools"))
from wtmd_pipeline import decode_wtmd, decompress_lz10  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_rtdp(data: bytes) -> list[dict[str, object]]:
    if data[:4] != b"RTDP" or len(data) < 0x20:
        raise ValueError("not RTDP")
    eoh = int.from_bytes(data[4:8], "big")
    count = int.from_bytes(data[8:12], "big")
    out: list[dict[str, object]] = []
    for index in range(count):
        off = 0x20 + index * 40
        name_raw = data[off : off + 32]
        name = name_raw.split(b"\0", 1)[0].decode("latin1")
        size = int.from_bytes(data[off + 32 : off + 36], "big")
        rel = int.from_bytes(data[off + 36 : off + 40], "big")
        encoded = data[eoh + rel : eoh + rel + size]
        if len(encoded) != size:
            raise ValueError(f"entry {index} truncated")
        payload = bytes(value ^ 0x55 for value in encoded)
        out.append({"index": index, "name": name, "payload": payload})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    packed = args.source.read_bytes()
    unpacked = decompress_lz10(packed)
    outer = parse_rtdp(unpacked)
    raw_root = args.output / "raw"
    png_root = args.output / "png"
    raw_root.mkdir(parents=True, exist_ok=True)
    png_root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []

    for outer_entry in outer:
        outer_payload = outer_entry["payload"]
        if not isinstance(outer_payload, bytes) or outer_payload[:4] != b"RTDP":
            continue
        for inner_entry in parse_rtdp(outer_payload):
            payload = inner_entry["payload"]
            if not isinstance(payload, bytes) or payload[:4] != b"WTMD":
                continue
            oi = int(outer_entry["index"])
            ii = int(inner_entry["index"])
            stem = f"{oi:02d}_{ii:03d}_{inner_entry['name']}"
            raw_path = raw_root / f"{stem}.wtm"
            png_path = png_root / f"{stem}.png"
            raw_path.write_bytes(payload)
            image, header = decode_wtmd(payload)
            image.save(png_path)
            alpha = image.getchannel("A")
            bbox = alpha.getbbox()
            manifest.append({
                "entry_path": [oi, ii],
                "outer_name": outer_entry["name"],
                "inner_name": inner_entry["name"],
                "sha256": sha256(payload),
                "size_bytes": len(payload),
                "width": image.width,
                "height": image.height,
                "gx": header["gx_name"],
                "palette": header["pal_name"],
                "alpha_bbox": list(bbox) if bbox else None,
                "raw": str(raw_path.relative_to(args.output)).replace("\\", "/"),
                "png": str(png_path.relative_to(args.output)).replace("\\", "/"),
            })

    report = {
        "schema": "arf-if-resident-wtmd-inventory-v1",
        "source": str(args.source),
        "source_sha256": sha256(packed),
        "unpacked_sha256": sha256(unpacked),
        "outer_entry_count": len(outer),
        "texture_count": len(manifest),
        "textures": manifest,
    }
    (args.output / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "textures": len(manifest)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
