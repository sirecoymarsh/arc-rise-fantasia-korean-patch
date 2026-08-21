#!/usr/bin/env python3
"""Build labeled contact sheets for likely text-bearing if_resident WTMD textures."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


TEXT_NAME = re.compile(
    r"(moji|title|name|stats|lv|wp|time|money|soldout|guest|ready|mihatu|file|clear|"
    r"pause|help|custom|list|category|formation|action|total|current|ability|caption|"
    r"quest|dictionary|dragons|element|equipment|shop|save|arena|heading|choices)",
    re.IGNORECASE,
)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        Path(r"C:\Windows\Fonts\malgun.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ):
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("inventory", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    data = json.loads(args.inventory.read_text(encoding="utf-8"))
    base = args.inventory.parent
    groups: dict[tuple[int, str], list[dict[str, object]]] = defaultdict(list)
    for record in data["textures"]:
        if TEXT_NAME.search(str(record["inner_name"])):
            groups[(int(record["entry_path"][0]), str(record["outer_name"]))].append(record)
    args.output.mkdir(parents=True, exist_ok=True)
    font = load_font(13)
    title_font = load_font(18)
    index: list[dict[str, object]] = []
    sheet_width = 1280
    cell_width = 400
    columns = 3

    for (outer_index, outer_name), records in sorted(groups.items()):
        rows: list[list[tuple[dict[str, object], Image.Image, int, int]]] = []
        current: list[tuple[dict[str, object], Image.Image, int, int]] = []
        for record in sorted(records, key=lambda r: int(r["entry_path"][1])):
            image = Image.open(base / str(record["png"])).convert("RGBA")
            scale = min(4.0, 360 / max(1, image.width), 220 / max(1, image.height))
            scale = max(1.0, scale)
            width = max(1, round(image.width * scale))
            height = max(1, round(image.height * scale))
            if scale != 1:
                image = image.resize((width, height), Image.Resampling.NEAREST)
            current.append((record, image, width, height))
            if len(current) == columns:
                rows.append(current)
                current = []
        if current:
            rows.append(current)

        row_heights = [max(item[3] for item in row) + 62 for row in rows]
        sheet = Image.new("RGB", (sheet_width, 44 + sum(row_heights)), (31, 35, 46))
        draw = ImageDraw.Draw(sheet)
        draw.text((12, 10), f"{outer_index:02d} {outer_name} — {len(records)} candidate textures", font=title_font, fill=(255, 255, 255))
        y = 44
        for row, row_height in zip(rows, row_heights):
            for column, (record, image, width, height) in enumerate(row):
                x = column * cell_width + 12
                draw.rectangle((x - 4, y - 4, x + 372, y + row_height - 8), fill=(17, 19, 26), outline=(73, 83, 105))
                checker = Image.new("RGBA", (width, height), (45, 50, 62, 255))
                block = 8
                cd = ImageDraw.Draw(checker)
                for yy in range(0, height, block):
                    for xx in range(0, width, block):
                        if (xx // block + yy // block) % 2:
                            cd.rectangle((xx, yy, min(width - 1, xx + block - 1), min(height - 1, yy + block - 1)), fill=(65, 70, 84, 255))
                checker.alpha_composite(image)
                sheet.paste(checker.convert("RGB"), (x, y))
                label_y = y + height + 5
                inner_index = int(record["entry_path"][1])
                draw.text((x, label_y), f"[{outer_index},{inner_index}] {record['inner_name']}", font=font, fill=(230, 235, 245))
                draw.text((x, label_y + 19), f"{record['width']}×{record['height']} {record['gx']} / {record['palette']}", font=font, fill=(151, 181, 216))
            y += row_height
        output = args.output / f"{outer_index:02d}_{outer_name}.png"
        sheet.save(output)
        index.append({"outer_index": outer_index, "outer_name": outer_name, "candidates": len(records), "sheet": output.name})

    (args.output / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sheets": len(index), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
