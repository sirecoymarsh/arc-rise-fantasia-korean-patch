"""Launch the rebuilt full patch in a clean, collision-free Dolphin profile."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "work" / "runtime_validation"
DOLPHIN = ROOT / "work" / "tools" / "dolphin-2603a" / "Dolphin-x64" / "Dolphin.exe"
BASE_USER = RUNTIME / "dolphin_user"
USER = RUNTIME / "dolphin_user_final_validation"
DESCRIPTOR = RUNTIME / "arc_rise_fantasia_ko_full.json"
XML = (
    ROOT
    / "work"
    / "final_runtime_staging"
    / "riivolution_sd"
    / "riivolution"
    / "arc_rise_fantasia_ko_full.xml"
)
SYSTEM_VOL = (
    ROOT
    / "work"
    / "final_runtime_staging"
    / "riivolution_sd"
    / "arc_rise_fantasia_ko_full"
    / "files"
    / "Sys"
    / "system.vol"
)
MANIFEST = ROOT / "work" / "final_runtime_staging" / "staging_manifest.json"
SESSION = RUNTIME / "final_runtime" / "full_runtime_session.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def set_ini_value(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(key)}\s*=.*$")
    if not pattern.search(text):
        raise ValueError(f"missing Dolphin.ini key: {key}")
    return pattern.sub(f"{key} = {value}", text)


def set_ini_section_value(text: str, section: str, key: str, value: str) -> str:
    """Set or add a key inside one INI section without reformatting the file."""
    section_pattern = re.compile(
        rf"(?ms)^\[{re.escape(section)}\]\s*$.*?(?=^\[|\Z)"
    )
    match = section_pattern.search(text)
    if not match:
        suffix = "" if text.endswith("\n") else "\n"
        return f"{text}{suffix}[{section}]\n{key} = {value}\n"
    block = match.group(0)
    key_pattern = re.compile(rf"(?m)^{re.escape(key)}\s*=.*$")
    if key_pattern.search(block):
        replacement = key_pattern.sub(f"{key} = {value}", block)
    else:
        replacement = block.rstrip("\n") + f"\n{key} = {value}\n"
    return text[: match.start()] + replacement + text[match.end() :]


def main() -> int:
    for path in (DOLPHIN, BASE_USER, DESCRIPTOR, XML, SYSTEM_VOL, MANIFEST):
        if not path.exists():
            raise SystemExit(f"missing final runtime input: {path}")
    if USER.exists():
        shutil.rmtree(USER)
    shutil.copytree(
        BASE_USER,
        USER,
        ignore=shutil.ignore_patterns(
            "Cache", "Logs", "play_rec.dat", "*.uidcache", "*.lock"
        ),
    )
    ini = USER / "Config" / "Dolphin.ini"
    text = ini.read_text(encoding="utf-8-sig")
    text = set_ini_value(text, "UsePanicHandlers", "True")
    text = set_ini_value(text, "EmulationSpeed", "1.0")
    # Prove the corrected patch works with Dolphin's fast/default non-MMU path;
    # the broken build previously raised an invalid-read warning here.
    text = set_ini_value(text, "MMU", "False")
    # Only one emulated controller should share the keyboard during the
    # evidence run.  Otherwise the same physical key can simultaneously act
    # as GameCube Start and Wii Remote HOME, making controller attribution
    # ambiguous in menus.
    text = set_ini_section_value(text, "Core", "SIDevice0", "0")
    ini.write_text(text, encoding="utf-8")

    wiimote_ini = USER / "Config" / "WiimoteNew.ini"
    wiimote_text = wiimote_ini.read_text(encoding="utf-8-sig")
    wiimote_text = set_ini_value(wiimote_text, "Buttons/Home", "F8")
    wiimote_ini.write_text(wiimote_text, encoding="utf-8")
    gc_pad_ini = USER / "Config" / "GCPadNew.ini"
    gc_pad_text = gc_pad_ini.read_text(encoding="utf-8-sig")
    gc_pad_text = set_ini_value(gc_pad_text, "Device", "")
    gc_pad_ini.write_text(gc_pad_text, encoding="utf-8")

    SESSION.parent.mkdir(parents=True, exist_ok=True)
    stdout_path = SESSION.parent / "full_runtime_dolphin.stdout.log"
    stderr_path = SESSION.parent / "full_runtime_dolphin.stderr.log"
    stdout = stdout_path.open("wb")
    stderr = stderr_path.open("wb")
    process = subprocess.Popen(
        [str(DOLPHIN), "-u", str(USER), "-b", "-e", str(DESCRIPTOR)],
        cwd=str(DOLPHIN.parent),
        stdout=stdout,
        stderr=stderr,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    stdout.close()
    stderr.close()
    time.sleep(3)
    if process.poll() is not None:
        raise SystemExit(f"Dolphin exited early: {process.returncode}")
    session = {
        "schema": "arf-ko-dolphin-runtime-session-v1",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "pid": process.pid,
        "dolphin": {"path": str(DOLPHIN.resolve()), "sha256": sha256(DOLPHIN)},
        "user": str(USER.resolve()),
        "dolphin_ini": {"path": str(ini.resolve()), "sha256": sha256(ini)},
        "wiimote_ini": {
            "path": str(wiimote_ini.resolve()),
            "sha256": sha256(wiimote_ini),
        },
        "gc_pad_ini": {"path": str(gc_pad_ini.resolve()), "sha256": sha256(gc_pad_ini)},
        "settings": {"EmulationSpeed": 1.0, "MMU": False, "UsePanicHandlers": True},
        "descriptor": {"path": str(DESCRIPTOR.resolve()), "sha256": sha256(DESCRIPTOR)},
        "xml": {"path": str(XML.resolve()), "sha256": sha256(XML)},
        "system_vol": {"path": str(SYSTEM_VOL.resolve()), "sha256": sha256(SYSTEM_VOL)},
        "staging_manifest": {"path": str(MANIFEST.resolve()), "sha256": sha256(MANIFEST)},
        "stdout": str(stdout_path.resolve()),
        "stderr": str(stderr_path.resolve()),
    }
    SESSION.write_text(json.dumps(session, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(session, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
