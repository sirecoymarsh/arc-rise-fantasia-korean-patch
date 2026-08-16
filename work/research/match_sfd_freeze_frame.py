import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image


def decode_samples(ffmpeg: Path, movie: Path, fps: int = 2):
    command = [
        str(ffmpeg), "-v", "error", "-i", str(movie),
        "-vf", f"fps={fps},scale=64:48:flags=area,format=rgb24",
        "-f", "rawvideo", "pipe:1",
    ]
    data = subprocess.check_output(command)
    frame_size = 64 * 48 * 3
    if len(data) % frame_size:
        raise RuntimeError((len(data), frame_size))
    return np.frombuffer(data, dtype=np.uint8).reshape((-1, 48, 64, 3))


def image_info(image: np.ndarray):
    gray = image.mean(axis=2)
    row_mean = gray.mean(axis=1)
    col_mean = gray.mean(axis=0)
    return {
        "shape": list(image.shape),
        "row_mean_first_last_nonblack": [
            int(np.flatnonzero(row_mean > 3)[0]) if np.any(row_mean > 3) else None,
            int(np.flatnonzero(row_mean > 3)[-1]) if np.any(row_mean > 3) else None,
        ],
        "col_mean_first_last_nonblack": [
            int(np.flatnonzero(col_mean > 3)[0]) if np.any(col_mean > 3) else None,
            int(np.flatnonzero(col_mean > 3)[-1]) if np.any(col_mean > 3) else None,
        ],
        "mean_rgb": [float(x) for x in image.mean(axis=(0, 1))],
    }


def score(target: np.ndarray, candidate: np.ndarray):
    # Ignore the small emulator FPS overlay and compare normalized luminance.
    mask = np.ones((48, 64), dtype=bool)
    mask[:6, 50:] = False
    tg = target.mean(axis=2)[mask].astype(np.float64)
    cg = candidate.mean(axis=2)[mask].astype(np.float64)
    tg = (tg - tg.mean()) / (tg.std() + 1e-9)
    cg = (cg - cg.mean()) / (cg.std() + 1e-9)
    corr = float(np.mean(tg * cg))
    mse = float(np.mean((target[mask].astype(np.float64) - candidate[mask].astype(np.float64)) ** 2))
    return corr, mse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ffmpeg", type=Path, required=True)
    ap.add_argument("--screenshot", type=Path, required=True)
    ap.add_argument("--payload", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    full = np.asarray(Image.open(args.screenshot).convert("RGB"))
    target = np.asarray(Image.fromarray(full).resize((64, 48), Image.Resampling.BOX))
    report = {"screenshot": str(args.screenshot), "screenshot_info": image_info(full)}
    for label, movie in (("payload", args.payload), ("source", args.source)):
        frames = decode_samples(args.ffmpeg, movie)
        rows = []
        for index, frame in enumerate(frames):
            corr, mse = score(target, frame)
            rows.append({"sample_index": index, "seconds": index / 2, "correlation": corr, "mse": mse})
        rows.sort(key=lambda r: (-r["correlation"], r["mse"]))
        report[label] = {
            "path": str(movie),
            "sample_count": len(frames),
            "top_matches": rows[:20],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
