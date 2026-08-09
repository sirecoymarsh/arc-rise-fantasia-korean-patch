"""Launch one isolated system.vol diagnostic and capture timed runtime frames.

The runner owns only the Dolphin process that it starts.  It copies a selected
research variant into the unmanifested ``__runtime_debug__`` path referenced by
the diagnostic game-mod descriptor, captures the render HWND at each requested
wall-clock time, records image statistics, and then closes that exact PID.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "work" / "runtime_validation"
DOLPHIN = ROOT / "work" / "tools" / "dolphin-2603a" / "Dolphin-x64" / "Dolphin.exe"
USER = RUNTIME / "dolphin_user"
RUN_USERS = RUNTIME / "dolphin_user_runs"
DESCRIPTOR = RUNTIME / "arc_rise_fantasia_ko_systemvol_variant.json"
INDEX = RUNTIME / "systemvol_variants" / "index.json"
DEBUG_FILE = (
    ROOT
    / "work"
    / "final_runtime_staging"
    / "riivolution_sd"
    / "arc_rise_fantasia_ko_full"
    / "files"
    / "__runtime_debug__"
    / "system.vol"
)
OUTPUT_ROOT = RUNTIME / "final_runtime"

sys.path.insert(0, str(RUNTIME))
from windows_dolphin_control import (  # noqa: E402
    EnumWindowsProc,
    capture,
    enumerate_windows,
    title_for,
    user32,
)


BM_CLICK = 0x00F5
user32.EnumChildWindows.argtypes = [ctypes.c_void_p, EnumWindowsProc, ctypes.c_void_p]
user32.EnumChildWindows.restype = ctypes.c_bool
user32.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
user32.SendMessageW.restype = ctypes.c_void_p


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def image_stats(path: Path) -> dict[str, object]:
    image = Image.open(path).convert("RGB")
    pixels = list(image.getdata())
    count = len(pixels)
    nonblack = sum(max(pixel) > 8 for pixel in pixels)
    mean = [round(sum(pixel[channel] for pixel in pixels) / count, 4) for channel in range(3)]
    return {
        "width": image.width,
        "height": image.height,
        "sha256": sha256(path),
        "nonblack_pixel_ratio": round(nonblack / count, 8),
        "rgb_mean": mean,
    }


def dismiss_panic_warning(pid: int, windows: list[dict[str, object]]) -> bool:
    """Click Dolphin's per-session ignore button when a panic dialog appears."""
    warning_handles = [
        int(row["hwnd"])
        for row in windows
        if row.get("visible") and str(row.get("title", "")) in {"경고", "Warning"}
    ]
    for warning in warning_handles:
        children: list[tuple[int, str]] = []

        @EnumWindowsProc
        def callback(hwnd: int, _lparam: int) -> bool:
            children.append((int(hwnd), title_for(hwnd)))
            return True

        user32.EnumChildWindows(warning, callback, 0)
        preferred = [
            hwnd
            for hwnd, text in children
            if "세션" in text and "무시" in text
            or "ignore" in text.casefold() and "session" in text.casefold()
        ]
        if preferred:
            user32.SendMessageW(preferred[0], BM_CLICK, 0, 0)
            return True
    return False


def wait_for_render_window(pid: int, deadline: float) -> dict[str, object]:
    last: list[dict[str, object]] = []
    while time.monotonic() < deadline:
        last = enumerate_windows(pid)
        if dismiss_panic_warning(pid, last):
            time.sleep(0.5)
            continue
        visible = [
            row
            for row in last
            if row.get("visible") and "RPJJ99" in str(row.get("title", ""))
        ]
        if len(visible) == 1:
            return visible[0]
        # Dolphin 2603a leaves this render HWND titled simply ``Dolphin``
        # while a panic handler is disabled or before the game title suffix is
        # assigned.  In batch mode it is the only remaining visible non-dialog
        # window and still owns the 640x480 Direct3D client surface.
        fallback = [
            row
            for row in last
            if row.get("visible") and str(row.get("title", "")) == "Dolphin"
        ]
        if len(fallback) == 1 and not any(
            row.get("visible") and str(row.get("title", "")) in {"경고", "Warning"}
            for row in last
        ):
            return fallback[0]
        time.sleep(0.5)
    raise RuntimeError(f"Dolphin render window did not appear: {last}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("variant")
    parser.add_argument("--times", nargs="+", type=float, default=[60.0, 90.0])
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    if any(value <= 0 for value in args.times) or args.times != sorted(set(args.times)):
        raise SystemExit("--times must be unique positive values in ascending order")

    index = json.loads(INDEX.read_text(encoding="utf-8"))
    variants = {str(row["name"]): row for row in index["variants"]}
    if args.variant not in variants:
        raise SystemExit(f"unknown variant: {args.variant}")
    source = Path(str(variants[args.variant]["path"]))
    if sha256(source) != str(variants[args.variant]["sha256"]).upper():
        raise SystemExit(f"variant hash mismatch: {source}")
    for required in (DOLPHIN, DESCRIPTOR, USER):
        if not required.exists():
            raise SystemExit(f"missing runtime input: {required}")

    DEBUG_FILE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, DEBUG_FILE)
    if sha256(DEBUG_FILE) != sha256(source):
        raise SystemExit("debug system.vol copy hash mismatch")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_user = RUN_USERS / f"{args.variant}_{int(time.time())}_{os.getpid()}"
    run_user.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        USER,
        run_user,
        ignore=shutil.ignore_patterns(
            "Cache", "Logs", "play_rec.dat", "*.uidcache", "*.lock"
        ),
    )
    stdout_path = args.output_dir / f"{args.variant}_runner.stdout.log"
    stderr_path = args.output_dir / f"{args.variant}_runner.stderr.log"
    result_path = args.output_dir / f"{args.variant}_runtime_result.json"
    stdout = stdout_path.open("wb")
    stderr = stderr_path.open("wb")
    process: subprocess.Popen[bytes] | None = None
    started = time.monotonic()
    frames: list[dict[str, object]] = []
    try:
        process = subprocess.Popen(
            [str(DOLPHIN), "-u", str(run_user), "-b", "-e", str(DESCRIPTOR)],
            cwd=str(DOLPHIN.parent),
            stdout=stdout,
            stderr=stderr,
        )
        window = wait_for_render_window(process.pid, time.monotonic() + 30.0)
        for target in args.times:
            remaining = started + target - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
            if process.poll() is not None:
                raise RuntimeError(f"Dolphin exited early with {process.returncode}")
            label = str(target).replace(".", "p")
            output = args.output_dir / f"retest_{args.variant}_{label}s.png"
            captured = capture(int(window["hwnd"]), output)
            frames.append(
                {
                    "target_seconds": target,
                    "actual_seconds": round(time.monotonic() - started, 3),
                    "capture": captured,
                    "image": image_stats(output),
                }
            )
        result = {
            "format": "arf-systemvol-runtime-diagnostic-v1",
            "variant": args.variant,
            "variant_path": str(source.resolve()),
            "variant_sha256": sha256(source),
            "debug_path": str(DEBUG_FILE.resolve()),
            "dolphin_path": str(DOLPHIN.resolve()),
            "dolphin_pid": process.pid,
            "dolphin_user": str(run_user.resolve()),
            "descriptor": str(DESCRIPTOR.resolve()),
            "window": window,
            "frames": frames,
        }
        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        stdout.close()
        stderr.close()


if __name__ == "__main__":
    main()
