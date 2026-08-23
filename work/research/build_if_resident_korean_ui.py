#!/usr/bin/env python3
"""Render Korean text into if_resident WTMD atlases and rebuild the CXD."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "image_ui_final" / "tools"))
from wtmd_pipeline import decode_wtmd, decompress_lz10, encode_wtmd, parse_wtmd  # noqa: E402


SOURCE_SHA256 = "09E6816C21AF70DDA1A7E474D0E25C50E0C3E9477E8313A8AFA922DE6172D359"
TRANSLATOR_MODEL = "Codex internal"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def parse_rtdp(data: bytes) -> list[dict[str, Any]]:
    require(data[:4] == b"RTDP" and len(data) >= 0x20, "not RTDP")
    eoh = int.from_bytes(data[4:8], "big")
    count = int.from_bytes(data[8:12], "big")
    rows: list[dict[str, Any]] = []
    for index in range(count):
        off = 0x20 + index * 40
        name = data[off : off + 32].split(b"\0", 1)[0].decode("latin1")
        size = int.from_bytes(data[off + 32 : off + 36], "big")
        rel = int.from_bytes(data[off + 36 : off + 40], "big")
        encoded = data[eoh + rel : eoh + rel + size]
        require(len(encoded) == size, f"RTDP entry {index} truncated")
        rows.append({"index": index, "name": name, "payload": bytes(v ^ 0x55 for v in encoded)})
    return rows


def font_path() -> Path:
    candidates = [
        Path(r"C:\Windows\Fonts\malgunbd.ttf"),
        Path(r"C:\Windows\Fonts\malgun.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("Malgun Gothic font not found")


class Renderer:
    def __init__(self, font_file: Path):
        self.font_file = font_file
        self.cache: dict[int, ImageFont.FreeTypeFont] = {}
        self.draw_log: list[dict[str, Any]] = []

    def font(self, size: int) -> ImageFont.FreeTypeFont:
        if size not in self.cache:
            self.cache[size] = ImageFont.truetype(str(self.font_file), size)
        return self.cache[size]

    def text_fit(
        self,
        image: Image.Image,
        box: tuple[int, int, int, int],
        text: str,
        *,
        fill: tuple[int, int, int, int],
        stroke_fill: tuple[int, int, int, int],
        max_size: int,
        min_size: int = 8,
        stroke_width: int = 1,
        align: str = "center",
        stable_id: str,
    ) -> None:
        draw = ImageDraw.Draw(image)
        left, top, right, bottom = box
        available_w, available_h = right - left, bottom - top
        chosen = None
        for size in range(max_size, min_size - 1, -1):
            font = self.font(size)
            bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
            width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            if width <= available_w and height <= available_h:
                chosen = (font, bbox, size, width, height)
                break
        require(chosen is not None, f"text does not fit: {stable_id} {text!r} in {box}")
        font, bbox, size, width, height = chosen
        if align == "right":
            x = right - width - bbox[0]
        elif align == "left":
            x = left - bbox[0]
        else:
            x = left + (available_w - width) // 2 - bbox[0]
        y = top + (available_h - height) // 2 - bbox[1]
        draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        actual = draw.textbbox((x, y), text, font=font, stroke_width=stroke_width)
        require(actual[0] >= left and actual[1] >= top and actual[2] <= right and actual[3] <= bottom,
                f"rendered text overflow: {stable_id} {actual} outside {box}")
        self.draw_log.append({
            "stable_id": stable_id,
            "target_ko": text,
            "box": list(box),
            "rendered_bbox": list(actual),
            "font_size": size,
            "stroke_width": stroke_width,
            "fit": True,
        })


WHITE = (255, 255, 255, 255)
BLUE = (0, 17, 136, 255)
CYAN = (49, 239, 239, 255)
LIGHT_CYAN = (205, 255, 255, 255)
NAVY = (0, 17, 51, 255)
GOLD = (255, 206, 74, 255)
BROWN = (49, 16, 0, 255)
RED = (255, 0, 0, 255)
DARK_RED = (66, 0, 0, 255)
ORANGE = (255, 174, 0, 255)
TRANSPARENT = (0, 0, 0, 0)


def blank_like(image: Image.Image) -> Image.Image:
    return Image.new("RGBA", image.size, TRANSPARENT)


def item(entry: dict[str, Any], index: int) -> dict[str, str]:
    value = entry["items"][index]
    return {"stable_id": str(value["stable_id"]), "text": str(value["target_ko"])}


def render_entry(renderer: Renderer, original: Image.Image, entry: dict[str, Any]) -> Image.Image:
    layout = str(entry["layout"])
    items = entry["items"]
    if layout == "shared_tab_atlas":
        image = original.copy().convert("RGBA")
        boxes = [
            (0, 16, 54, 40), (105, 16, 128, 40),
            (0, 40, 60, 64), (60, 40, 128, 64),
            (0, 64, 52, 88), (52, 64, 104, 88), (104, 64, 128, 88),
            (0, 88, 67, 112), (67, 88, 128, 112),
            (0, 112, 72, 136), (72, 112, 128, 136),
        ]
        draw = ImageDraw.Draw(image)
        for box in boxes:
            draw.rectangle((box[0], box[1], box[2] - 1, box[3] - 1), fill=TRANSPARENT)
        for i, box in enumerate(boxes):
            row = item(entry, i)
            renderer.text_fit(image, box, row["text"], fill=LIGHT_CYAN, stroke_fill=NAVY,
                              max_size=15 if i != 8 else 10, min_size=8, stroke_width=1,
                              align="center", stable_id=row["stable_id"])
        return image

    image = blank_like(original)
    if layout == "heading_rows_24_right":
        require(image.height == len(items) * 24, f"heading row count mismatch: {entry['entry_path']}")
        for i in range(len(items)):
            row = item(entry, i)
            renderer.text_fit(image, (1, i * 24, image.width, (i + 1) * 24), row["text"],
                              fill=WHITE, stroke_fill=BLUE, max_size=18, min_size=9,
                              stroke_width=1, align="right", stable_id=row["stable_id"])
    elif layout == "single_cyan_16":
        row = item(entry, 0)
        renderer.text_fit(image, (0, 0, image.width, image.height), row["text"], fill=CYAN,
                          stroke_fill=NAVY, max_size=13, min_size=8, stroke_width=1,
                          align="center", stable_id=row["stable_id"])
    elif layout == "single_cyan_24":
        row = item(entry, 0)
        renderer.text_fit(image, (0, 0, image.width, image.height), row["text"], fill=CYAN,
                          stroke_fill=NAVY, max_size=18, min_size=9, stroke_width=1,
                          align="center", stable_id=row["stable_id"])
    elif layout == "single_gold_24":
        row = item(entry, 0)
        renderer.text_fit(image, (0, 0, image.width, image.height), row["text"], fill=GOLD,
                          stroke_fill=BROWN, max_size=18, min_size=9, stroke_width=1,
                          align="center", stable_id=row["stable_id"])
    elif layout == "list_title_2rows":
        for i in range(2):
            row = item(entry, i)
            renderer.text_fit(image, (0, i * 16, image.width, (i + 1) * 16), row["text"],
                              fill=CYAN, stroke_fill=NAVY, max_size=13, min_size=8,
                              stroke_width=1, align="center", stable_id=row["stable_id"])
    elif layout == "equipment_logres_rows":
        boxes = [(0, 0, image.width, 27), (0, 27, image.width, 54), (0, 54, image.width, 80)]
        for i, box in enumerate(boxes):
            row = item(entry, i)
            renderer.text_fit(image, box, row["text"], fill=WHITE, stroke_fill=(0, 0, 0, 255),
                              max_size=17, min_size=9, stroke_width=1,
                              align="center", stable_id=row["stable_id"])
    elif layout == "shop_title_grid":
        boxes = [(0, 0, 42, 16), (42, 0, 82, 16), (82, 0, 110, 16), (110, 0, 136, 16),
                 (0, 16, 58, 32), (58, 16, 104, 32), (104, 16, 136, 32)]
        for i, box in enumerate(boxes):
            row = item(entry, i)
            renderer.text_fit(image, box, row["text"], fill=CYAN, stroke_fill=NAVY,
                              max_size=12, min_size=7, stroke_width=1,
                              align="center", stable_id=row["stable_id"])
    elif layout in {"cage_title_grid", "gem_title_grid", "clothes_title_grid", "tactics_title_grid"}:
        if layout == "cage_title_grid":
            boxes = [(0, 0, 40, 16), (40, 0, 80, 16), (80, 0, 104, 16)]
        elif layout == "gem_title_grid":
            boxes = [(0, 0, 40, 16), (40, 0, 80, 16), (80, 0, 104, 16), (104, 0, 128, 16)]
        else:
            boxes = [(0, 0, image.width // 2, 16), (image.width // 2, 0, image.width, 16)]
        for i, box in enumerate(boxes):
            row = item(entry, i)
            renderer.text_fit(image, box, row["text"], fill=CYAN, stroke_fill=NAVY,
                              max_size=12, min_size=7, stroke_width=1,
                              align="center", stable_id=row["stable_id"])
    elif layout == "single_weapon_custom":
        row = item(entry, 0)
        renderer.text_fit(image, (4, 4, image.width - 4, image.height - 4), row["text"],
                          fill=LIGHT_CYAN, stroke_fill=(0, 74, 180, 255), max_size=26,
                          min_size=12, stroke_width=2, align="center", stable_id=row["stable_id"])
    elif layout == "single_weapon_cyan_32":
        row = item(entry, 0)
        renderer.text_fit(image, (1, 1, image.width - 1, image.height - 1), row["text"],
                          fill=LIGHT_CYAN, stroke_fill=(0, 74, 180, 255), max_size=20,
                          min_size=10, stroke_width=2, align="center", stable_id=row["stable_id"])
    elif layout == "single_weapon_red_32":
        row = item(entry, 0)
        renderer.text_fit(image, (1, 1, image.width - 1, image.height - 1), row["text"],
                          fill=RED, stroke_fill=DARK_RED, max_size=21, min_size=10,
                          stroke_width=2, align="center", stable_id=row["stable_id"])
    elif layout == "dragons_effect_rows":
        for i in range(2):
            row = item(entry, i)
            renderer.text_fit(image, (0, i * 24, image.width, (i + 1) * 24), row["text"],
                              fill=LIGHT_CYAN, stroke_fill=(0, 50, 95, 255), max_size=17,
                              min_size=9, stroke_width=1, align="center", stable_id=row["stable_id"])
    elif layout == "single_category_gold_32":
        row = item(entry, 0)
        renderer.text_fit(image, (1, 1, image.width - 1, image.height - 1), row["text"],
                          fill=GOLD, stroke_fill=BROWN, max_size=20, min_size=9,
                          stroke_width=2, align="center", stable_id=row["stable_id"])
    elif layout == "monster_status_titles":
        boxes = [(0, 0, 32, 16), (32, 0, 64, 16), (64, 0, 96, 16),
                 (0, 16, 96, 32), (0, 32, 96, 48)]
        for i, box in enumerate(boxes):
            row = item(entry, i)
            renderer.text_fit(image, box, row["text"], fill=CYAN, stroke_fill=NAVY,
                              max_size=12, min_size=7, stroke_width=1,
                              align="center", stable_id=row["stable_id"])
    elif layout == "quest_level_grid":
        boxes = [(0, 0, 136, 24), (0, 24, 72, 48), (72, 24, 136, 48)]
        for i, box in enumerate(boxes):
            row = item(entry, i)
            color = LIGHT_CYAN if i == 0 else GOLD
            outline = NAVY if i == 0 else BROWN
            renderer.text_fit(image, box, row["text"], fill=color, stroke_fill=outline,
                              max_size=18, min_size=9, stroke_width=1,
                              align="center", stable_id=row["stable_id"])
    elif layout == "quest_main_rows_24":
        require(len(items) == 5 and image.height == 120, "quest main layout mismatch")
        for i in range(5):
            row = item(entry, i)
            renderer.text_fit(image, (0, i * 24, image.width, (i + 1) * 24), row["text"],
                              fill=CYAN, stroke_fill=NAVY, max_size=17, min_size=9,
                              stroke_width=1, align="center", stable_id=row["stable_id"])
    elif layout == "quest_type_rows_24":
        require(len(items) == 7 and image.height == 168, "quest type layout mismatch")
        for i in range(7):
            row = item(entry, i)
            renderer.text_fit(image, (0, i * 24, image.width, (i + 1) * 24), row["text"],
                              fill=ORANGE, stroke_fill=BROWN, max_size=18, min_size=9,
                              stroke_width=1, align="center", stable_id=row["stable_id"])
    else:
        raise RuntimeError(f"unknown layout: {layout}")
    return image


def encode_extended(original: bytes, image: Image.Image) -> tuple[bytes, dict[str, Any]]:
    header = parse_wtmd(original)
    if header["gx"] != 3:
        return encode_wtmd(original, image)
    width, height = header["width"], header["height"]
    require(image.size == (width, height), "IA8 image size changed")
    rgba = list(image.convert("RGBA").getdata())
    raw = bytearray()
    for by in range(0, height, 4):
        for bx in range(0, width, 4):
            for y in range(4):
                for x in range(4):
                    xx, yy = bx + x, by + y
                    if xx < width and yy < height:
                        r, g, b, a = rgba[yy * width + xx]
                        intensity = (r * 299 + g * 587 + b * 114 + 500) // 1000
                    else:
                        intensity, a = 0, 0
                    raw += struct.pack(">H", (a << 8) | intensity)
    require(len(raw) == header["base_bytes"], "IA8 encoded size mismatch")
    out = bytearray(original)
    pos = int(header["image_pos"])
    out[pos : pos + len(raw)] = raw
    return bytes(out), header


def contact_sheet(rows: list[dict[str, Any]], output: Path) -> None:
    cell_w, cell_h, columns = 360, 160, 3
    height = ((len(rows) + columns - 1) // columns) * cell_h
    sheet = Image.new("RGB", (cell_w * columns, height), (28, 32, 42))
    draw = ImageDraw.Draw(sheet)
    label_font = ImageFont.truetype(str(font_path()), 12)
    for i, row in enumerate(rows):
        image = Image.open(row["preview_png"]).convert("RGBA")
        scale = min(4.0, 330 / image.width, 110 / image.height)
        scale = max(1.0, scale)
        image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.NEAREST)
        x, y = (i % columns) * cell_w + 10, (i // columns) * cell_h + 8
        bg = Image.new("RGBA", image.size, (52, 57, 70, 255))
        bg.alpha_composite(image)
        sheet.paste(bg.convert("RGB"), (x, y))
        draw.text((x, y + image.height + 4), f"{row['entry_path']} {row['inner_name']}", font=label_font, fill=(240, 244, 255))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=ROOT / "work/disc_extracted/DATA/files/interface/if_resident_vol.cxd")
    ap.add_argument("--inventory", type=Path, default=ROOT / "work/research/ui_residue/inventory/manifest.json")
    ap.add_argument("--translations", type=Path, default=ROOT / "work/translation/ui_image_residue/ui_image_translations.json")
    ap.add_argument("--output", type=Path, default=ROOT / "work/ui_residue_application")
    args = ap.parse_args()

    source = args.source.read_bytes()
    require(sha256(source) == SOURCE_SHA256, "if_resident source hash mismatch")
    translations = json.loads(args.translations.read_text(encoding="utf-8"))
    require(translations.get("translator_model") == TRANSLATOR_MODEL, "translator provenance mismatch")
    require(not translations.get("external_translation_models_or_services_used"), "external translation provenance is not empty")
    require(str(translations.get("source_container_sha256", "")).upper() == SOURCE_SHA256,
            "translation/source hash mismatch")
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    require(str(inventory.get("source_sha256", "")).upper() == SOURCE_SHA256, "inventory/source hash mismatch")
    records = {tuple(row["entry_path"]): row for row in inventory["textures"]}
    entries = translations["entries"]
    require(len(entries) == len({tuple(e["entry_path"]) for e in entries}), "duplicate translated entry path")
    stable_ids = [item["stable_id"] for entry in entries for item in entry["items"]]
    require(len(stable_ids) == len(set(stable_ids)), "duplicate stable translation ID")

    if args.output.exists():
        shutil.rmtree(args.output)
    replacement_root = args.output / "replacements"
    preview_root = args.output / "previews"
    payload = args.output / "payloads/interface/if_resident_vol.cxd"
    replacement_root.mkdir(parents=True)
    preview_root.mkdir(parents=True)
    payload.parent.mkdir(parents=True)
    renderer = Renderer(font_path())
    edits: list[dict[str, Any]] = []
    applied: list[dict[str, Any]] = []

    for entry in entries:
        path_key = tuple(entry["entry_path"])
        require(path_key in records, f"translated WTMD not in inventory: {path_key}")
        record = records[path_key]
        raw_path = args.inventory.parent / record["raw"]
        original_raw = raw_path.read_bytes()
        require(sha256(original_raw) == str(record["sha256"]).upper(), f"inventory raw hash mismatch: {path_key}")
        original_image, header = decode_wtmd(original_raw)
        before_log = len(renderer.draw_log)
        edited_image = render_entry(renderer, original_image, entry)
        rendered_rows = renderer.draw_log[before_log:]
        rebuilt_raw, rebuilt_header = encode_extended(original_raw, edited_image)
        require(rebuilt_header["width"] == header["width"] and rebuilt_header["height"] == header["height"],
                f"WTMD geometry changed: {path_key}")
        require(len(rebuilt_raw) == len(original_raw), f"WTMD size changed: {path_key}")
        decoded_again, _ = decode_wtmd(rebuilt_raw)
        oi, ii = path_key
        stem = f"{oi:02d}_{ii:03d}"
        replacement_path = replacement_root / f"{stem}.wtm"
        preview_path = preview_root / f"{stem}.png"
        replacement_path.write_bytes(rebuilt_raw)
        decoded_again.save(preview_path)
        require(rebuilt_raw != original_raw, f"translated WTMD is byte-identical: {path_key}")
        edits.append({
            "entryPath": [oi, ii],
            "expectedSha256": sha256(original_raw).lower(),
            "replacementFile": f"replacements/{replacement_path.name}",
        })
        applied.append({
            "entry_path": [oi, ii],
            "outer_name": record["outer_name"],
            "inner_name": record["inner_name"],
            "layout": entry["layout"],
            "source_sha256": sha256(original_raw),
            "output_sha256": sha256(rebuilt_raw),
            "size_bytes": len(rebuilt_raw),
            "width": header["width"],
            "height": header["height"],
            "gx": header["gx_name"],
            "palette": header["pal_name"],
            "translation_count": len(entry["items"]),
            "stable_ids": [v["stable_id"] for v in entry["items"]],
            "preview_png": str(preview_path),
            "render_checks": rendered_rows,
        })

    edit_manifest = {"format": "arf-container-edits-v1", "edits": edits}
    edit_path = args.output / "container_edits.json"
    edit_path.write_text(json.dumps(edit_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    container_report_path = args.output / "container_rebuild_report.json"
    tool = ROOT / "work/research/container_agent/container_tool.js"
    subprocess.run(["node", str(tool), "rebuild", str(args.source), str(edit_path), str(payload), str(container_report_path)],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    container_report = json.loads(container_report_path.read_text(encoding="utf-8"))
    require(container_report.get("inputSha256", "").upper() == SOURCE_SHA256, "container report source mismatch")
    require(payload.is_file(), "rebuilt if_resident payload missing")

    original_outer = parse_rtdp(decompress_lz10(source))
    rebuilt_outer = parse_rtdp(decompress_lz10(payload.read_bytes()))
    require(len(original_outer) == len(rebuilt_outer), "outer RTDP entry count changed")
    edited_paths = {tuple(row["entry_path"]): row for row in applied}
    untouched_children = 0
    checked_edits = 0
    edited_outer_indices = {path[0] for path in edited_paths}
    for oi, (old_outer, new_outer) in enumerate(zip(original_outer, rebuilt_outer)):
        if oi not in edited_outer_indices:
            require(old_outer["payload"] == new_outer["payload"], f"untouched outer entry changed: {oi}")
            continue
        old_inner = parse_rtdp(old_outer["payload"])
        new_inner = parse_rtdp(new_outer["payload"])
        require(len(old_inner) == len(new_inner), f"inner RTDP entry count changed: {oi}")
        for ii, (old_child, new_child) in enumerate(zip(old_inner, new_inner)):
            key = (oi, ii)
            if key in edited_paths:
                require(sha256(new_child["payload"]) == edited_paths[key]["output_sha256"],
                        f"edited child hash mismatch: {key}")
                checked_edits += 1
            else:
                require(old_child["payload"] == new_child["payload"], f"untouched child changed: {key}")
                untouched_children += 1
    require(checked_edits == len(applied), "not every UI edit was verified in rebuilt container")

    contact_sheet(applied, args.output / "korean_ui_contact_sheet.png")
    for row in applied:
        row["preview_png"] = str(Path(row["preview_png"]).relative_to(args.output)).replace("\\", "/")
    report = {
        "schema": "arf-if-resident-korean-ui-application-v1",
        "game_id": "RPJJ99",
        "translator_model": TRANSLATOR_MODEL,
        "external_translation_models_or_services_used": [],
        "source": {"path": str(args.source), "size_bytes": len(source), "sha256": SOURCE_SHA256},
        "translation_manifest": {"path": str(args.translations), "sha256": sha256(args.translations.read_bytes())},
        "font": {"path": str(renderer.font_file), "sha256": sha256(renderer.font_file.read_bytes())},
        "output": {"path": str(payload), "size_bytes": payload.stat().st_size, "sha256": sha256(payload.read_bytes())},
        "counts": {
            "translated_wtmd_entries": len(applied),
            "translated_text_items": len(stable_ids),
            "verified_edited_entries": checked_edits,
            "verified_untouched_inner_entries": untouched_children,
            "render_fit_checks": len(renderer.draw_log),
            "render_overflows": 0,
        },
        "container_rebuild_report": {"path": str(container_report_path), "sha256": sha256(container_report_path.read_bytes())},
        "entries": applied,
        "valid": True,
        "errors": [],
    }
    (args.output / "application_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": True, "entries": len(applied), "texts": len(stable_ids),
                      "payload": str(payload), "sha256": report["output"]["sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
