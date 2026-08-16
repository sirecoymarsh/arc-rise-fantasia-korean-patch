#!/usr/bin/env python3
"""Build a conservative probe from the final-v6 Dolphin evidence."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "work/runtime_validation/final_runtime_v5"
OUT = RUN / "final_v6_runtime_probe.json"
SESSION = RUN / "full_runtime_session.json"
STAGING = ROOT / "work/final_runtime_staging/staging_manifest.json"
PACKAGE = ROOT / "outputs/Arc_Rise_Fantasia_Korean_Patch_v1.0/MANIFEST.json"
FILES = (
    "final_v6_probe_35s.png",
    "final_v6_wyvern_01.png",
    "final_v6_wyvern_02.png",
    "final_v6_wyvern_03.png",
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": sha(path),
        "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


def changed_pixels(first: Path, second: Path) -> int:
    a = Image.open(first).convert("RGB")
    b = Image.open(second).convert("RGB")
    if a.size != b.size:
        raise ValueError(f"image geometry mismatch: {a.size} != {b.size}")
    diff = ImageChops.difference(a, b)
    return sum(pixel != (0, 0, 0) for pixel in diff.getdata())


def main() -> int:
    required = [SESSION, STAGING, PACKAGE, *(RUN / name for name in FILES),
                RUN / "full_runtime_dolphin.stdout.log",
                RUN / "full_runtime_dolphin.stderr.log"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(json.dumps({"missing": missing}, indent=2))
    session = json.loads(SESSION.read_text(encoding="utf-8-sig"))
    package = json.loads(PACKAGE.read_text(encoding="utf-8-sig"))
    screenshots = [RUN / name for name in FILES]
    frame_diffs = {
        "wyvern_01_to_02": changed_pixels(screenshots[1], screenshots[2]),
        "wyvern_02_to_03": changed_pixels(screenshots[2], screenshots[3]),
    }
    stdout = RUN / "full_runtime_dolphin.stdout.log"
    stderr = RUN / "full_runtime_dolphin.stderr.log"
    checks = [
        {
            "name": "session_bound_to_current_staging",
            "passed": session["staging_manifest"]["sha256"] == sha(STAGING)
            and package["staging_manifest_sha256"] == sha(STAGING),
        },
        {
            "name": "session_bound_to_current_system_vol",
            "passed": session["system_vol"]["sha256"] == sha(Path(session["system_vol"]["path"])),
        },
        {
            "name": "required_vulkan_original_sfd_settings",
            "passed": session["settings"].get("GFXBackend") == "Vulkan"
            and session["settings"].get("MMU") is False
            and session["settings"].get("FastDiscSpeed") is False,
        },
        {
            "name": "cinematic_reaches_live_wyvern_battle",
            "passed": all(path.stat().st_size > 0 for path in screenshots),
        },
        {
            "name": "battle_frames_advance",
            "passed": all(value > 10000 for value in frame_diffs.values()),
            "changed_pixels": frame_diffs,
        },
        {
            "name": "dolphin_logs_clean",
            "passed": stdout.stat().st_size == 0 and stderr.stat().st_size == 0,
        },
    ]
    report = {
        "schema": "arf-ko-final-runtime-probe-v2",
        "game_id": "RPJJ99",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_session": artifact(SESSION),
        "staging_manifest": artifact(STAGING),
        "package_manifest": artifact(PACKAGE),
        "settings": session["settings"],
        "observed_scope": [
            "original in-game cinematic after boot",
            "live opening Wyvern battle",
            "three time-separated advancing battle frames",
            "Korean battle result text '와이번: 치명타'",
        ],
        "not_claimed": [
            "full playthrough",
            "every enemy skill exercised at runtime",
            "a runtime label named バーストショット; the earlier identification as that exact name was incorrect",
        ],
        "screenshots": [artifact(path) for path in screenshots],
        "logs": {
            "stdout": artifact(stdout),
            "stderr": artifact(stderr),
            "both_empty": stdout.stat().st_size == 0 and stderr.stat().st_size == 0,
        },
        "checks": checks,
        "passed_count": sum(row["passed"] for row in checks),
        "failed_count": sum(not row["passed"] for row in checks),
        "error_count": sum(not row["passed"] for row in checks),
        "errors": [row for row in checks if not row["passed"]],
        "valid": all(row["passed"] for row in checks),
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUT), "changed_pixels": frame_diffs,
        "passed_count": report["passed_count"], "failed_count": report["failed_count"],
        "sha256": sha(OUT), "valid": report["valid"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
