#!/usr/bin/env python3
"""Create deterministic contact sheets for every Arc Rise Fantasia SFD movie.

The audit samples at a fixed interval and also captures detected hard cuts.  It is
read-only with respect to the extracted disc and writes a hash-bound index for
manual visual review.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def run(cmd: list[str], *, allow_empty: bool = False) -> str:
    p = subprocess.run(cmd, check=not allow_empty, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True, encoding="utf-8",
                       errors="replace")
    if p.returncode and not allow_empty:
        raise RuntimeError(p.stderr)
    return p.stdout


def probe(ffprobe: Path, movie: Path) -> dict:
    raw = run([
        str(ffprobe), "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate:format=duration",
        "-of", "json", str(movie),
    ])
    data = json.loads(raw)
    stream = data["streams"][0]
    return {
        "duration": float(data["format"]["duration"]),
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "avg_frame_rate": stream.get("avg_frame_rate", ""),
    }


def safe_stem(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", path.stem)


def capture_one(ffmpeg: Path, ffprobe: Path, movie: Path, out_root: Path,
                interval: float) -> dict:
    meta = probe(ffprobe, movie)
    movie_dir = out_root / "frames" / safe_stem(movie)
    if movie_dir.exists():
        shutil.rmtree(movie_dir)
    movie_dir.mkdir(parents=True)

    # Fixed interval samples cover fades, scrolling credits, and long static shots.
    run([
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-i", str(movie),
        "-vf", f"fps=1/{interval:.6f},scale=640:-2",
        "-q:v", "2", str(movie_dir / "interval_%05d.jpg"),
    ])
    # A second lane catches brief hard-cut title cards between fixed samples.
    run([
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-i", str(movie),
        "-vf", "select='gt(scene,0.22)',scale=640:-2",
        "-fps_mode", "vfr", "-strict", "unofficial", "-q:v", "2",
        str(movie_dir / "scene_%05d.jpg"),
    ], allow_empty=True)
    frames = sorted(movie_dir.glob("*.jpg"))
    return {
        "relative_path": f"Movie/{movie.name}",
        "source_sha256": sha256(movie),
        "source_size": movie.stat().st_size,
        **meta,
        "interval_seconds": interval,
        "interval_frame_count": len(list(movie_dir.glob("interval_*.jpg"))),
        "scene_frame_count": len(list(movie_dir.glob("scene_*.jpg"))),
        "frame_count": len(frames),
        "frame_dir": movie_dir.as_posix(),
    }


def font(size: int) -> ImageFont.ImageFont:
    for p in (Path("C:/Windows/Fonts/malgun.ttf"),
              Path("C:/Windows/Fonts/arial.ttf")):
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def build_sheets(movie_row: dict, out_root: Path, cols: int = 4,
                 rows: int = 4) -> list[dict]:
    frame_dir = Path(movie_row["frame_dir"])
    frames = sorted(frame_dir.glob("*.jpg"))
    sheet_dir = out_root / "contact_sheets"
    sheet_dir.mkdir(parents=True, exist_ok=True)
    label_font = font(15)
    title_font = font(19)
    thumb_w, thumb_h, label_h, title_h = 320, 180, 24, 34
    per_page = cols * rows
    pages = []
    for page_i in range(math.ceil(len(frames) / per_page)):
        group = frames[page_i * per_page:(page_i + 1) * per_page]
        canvas = Image.new("RGB", (cols * thumb_w, title_h + rows * (thumb_h + label_h)), "white")
        draw = ImageDraw.Draw(canvas)
        draw.text((8, 5), f"{movie_row['relative_path']}  page {page_i + 1}/{math.ceil(len(frames)/per_page)}",
                  fill="black", font=title_font)
        for i, frame in enumerate(group):
            with Image.open(frame) as im:
                im = im.convert("RGB")
                im.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                x = (i % cols) * thumb_w + (thumb_w - im.width) // 2
                y = title_h + (i // cols) * (thumb_h + label_h) + (thumb_h - im.height) // 2
                canvas.paste(im, (x, y))
            lx = (i % cols) * thumb_w + 5
            ly = title_h + (i // cols) * (thumb_h + label_h) + thumb_h + 2
            draw.text((lx, ly), frame.name, fill="black", font=label_font)
        out = sheet_dir / f"{safe_stem(Path(movie_row['relative_path']))}_p{page_i+1:02d}.png"
        canvas.save(out, optimize=True)
        pages.append({"path": out.as_posix(), "sha256": sha256(out), "frames": len(group)})
    return pages


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--movie-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--ffmpeg", type=Path, required=True)
    ap.add_argument("--ffprobe", type=Path, required=True)
    ap.add_argument("--interval", type=float, default=3.0)
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()
    movies = sorted(args.movie_dir.glob("*.sfd"), key=lambda p: p.name.lower())
    args.output.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(capture_one, args.ffmpeg, args.ffprobe, m,
                          args.output, args.interval) for m in movies]
        rows = [f.result() for f in futs]
    rows.sort(key=lambda r: r["relative_path"].lower())
    for row in rows:
        row["contact_sheets"] = build_sheets(row, args.output)
    report = {
        "schema": "arf-ko-sfd-visual-audit-v1",
        "movie_count": len(rows),
        "sampling_contract": {
            "fixed_interval_seconds": args.interval,
            "scene_threshold": 0.22,
            "includes_all_movies": True,
            "manual_review_required": True,
        },
        "movies": rows,
    }
    out = args.output / "sfd_visual_audit_index.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"movie_count": len(rows),
                      "frame_count": sum(r["frame_count"] for r in rows),
                      "sheet_count": sum(len(r["contact_sheets"]) for r in rows),
                      "report": str(out), "report_sha256": sha256(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
