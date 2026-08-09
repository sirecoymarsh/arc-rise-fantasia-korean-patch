#!/usr/bin/env python3
"""Render and inventory every standalone WTMD texture in the extracted disc."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def font(size: int):
    p = Path("C:/Windows/Fonts/malgun.ttf")
    return ImageFont.truetype(str(p), size) if p.exists() else ImageFont.load_default()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    sys.path.insert(0, str((Path(__file__).resolve().parents[1] / "image_ui_final" / "tools")))
    from wtmd_pipeline import decode_wtmd
    args.output.mkdir(parents=True, exist_ok=True)
    render_dir = args.output / "renders"
    render_dir.mkdir(exist_ok=True)
    rows = []
    for i, path in enumerate(sorted(args.root.rglob("*.wtm"), key=lambda p: str(p).lower())):
        image, meta = decode_wtmd(path.read_bytes())
        rel = path.relative_to(args.root).as_posix()
        out = render_dir / f"{i:03d}_{path.stem}.png"
        image.save(out)
        rows.append({"relative_path": rel, "source_size": path.stat().st_size,
                     "source_sha256": digest(path), **meta,
                     "render": str(out), "render_sha256": digest(out),
                     "review_verdict": None, "review_notes": None})
    cols, grid_rows, cell_w, cell_h, label_h = 4, 3, 360, 260, 48
    pages = []
    for page in range(math.ceil(len(rows)/(cols*grid_rows))):
        group = rows[page*cols*grid_rows:(page+1)*cols*grid_rows]
        sheet = Image.new("RGB", (cols*cell_w, grid_rows*(cell_h+label_h)), "white")
        draw = ImageDraw.Draw(sheet)
        for i, row in enumerate(group):
            x, y = i % cols * cell_w, i // cols * (cell_h+label_h)
            bg = Image.new("RGBA", (cell_w, cell_h), (230,230,230,255))
            bd = ImageDraw.Draw(bg)
            for yy in range(0, cell_h, 16):
                for xx in range(0, cell_w, 16):
                    if (xx//16+yy//16)&1:
                        bd.rectangle((xx,yy,xx+15,yy+15), fill=(190,190,190,255))
            with Image.open(row["render"]) as im:
                im = im.convert("RGBA")
                im.thumbnail((cell_w,cell_h), Image.Resampling.NEAREST)
                bg.alpha_composite(im, ((cell_w-im.width)//2,(cell_h-im.height)//2))
            sheet.paste(bg.convert("RGB"),(x,y))
            draw.text((x+4,y+cell_h+2), row["relative_path"], fill="black", font=font(13))
            draw.text((x+4,y+cell_h+24), f"{row['width']}x{row['height']} {row['gx_name']}/{row['pal_name']}", fill="black", font=font(12))
        sp=args.output/f"standalone_wtm_contact_p{page+1:02d}.png"
        sheet.save(sp,optimize=True)
        pages.append({"path":str(sp),"sha256":digest(sp),"items":len(group)})
    report={"schema":"arf-ko-standalone-wtm-visual-audit-v1","valid":False,
            "manual_review_complete":False,"asset_count":len(rows),
            "assets":rows,"contact_sheets":pages}
    rp=args.output/"standalone_wtm_visual_audit.json"
    rp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"assets":len(rows),"sheets":len(pages),"report":str(rp),"sha256":digest(rp)},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
