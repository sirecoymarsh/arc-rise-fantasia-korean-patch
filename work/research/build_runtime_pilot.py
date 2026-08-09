#!/usr/bin/env python3
"""Build copied RTDP fixtures for the first Korean glyph/runtime pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


EXPECTED_EVENT_RAW = bytes.fromhex(
    "A4AAA4A4A1A2CBDCC5F6A4CBA4B3A4ECA4C7B2E1A4B4A4B9A4CEA4ABA1A9"
)
EVENT_OFFSET = 0x12F


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_for_name(fixture: Path, name: str) -> Path:
    manifest = json.loads((fixture / "manifest.json").read_text(encoding="utf-8"))
    matches = [entry for entry in manifest["entries"] if entry["name"] == name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {name!r} in {fixture}, found {len(matches)}")
    return fixture / matches[0]["payloadFile"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-fixture", type=Path, required=True)
    parser.add_argument("--system-fixture", type=Path, required=True)
    parser.add_argument("--encoded-korean", type=Path, required=True)
    parser.add_argument("--injected-font-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing pilot directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True)
    event_out = args.output_dir / "event_fc_00_001"
    system_out = args.output_dir / "system"
    shutil.copytree(args.event_fixture, event_out)
    shutil.copytree(args.system_fixture, system_out)

    event_payload = payload_for_name(event_out, "fc_00_001.bscr")
    original_event_sha = sha256(event_payload)
    data = bytearray(event_payload.read_bytes())
    found = bytes(data[EVENT_OFFSET : EVENT_OFFSET + len(EXPECTED_EVENT_RAW)])
    if found != EXPECTED_EVENT_RAW:
        raise ValueError(
            f"pilot source guard failed at 0x{EVENT_OFFSET:X}: {found.hex().upper()}"
        )
    if data[EVENT_OFFSET + len(EXPECTED_EVENT_RAW)] != 0:
        raise ValueError("pilot source string is not NUL terminated at expected boundary")
    encoded = args.encoded_korean.read_bytes()
    if not encoded or b"\0" in encoded:
        raise ValueError("encoded Korean pilot must be non-empty and contain no NUL")
    if len(encoded) > len(EXPECTED_EVENT_RAW):
        raise ValueError(f"pilot translation {len(encoded)} exceeds {len(EXPECTED_EVENT_RAW)}-byte field")
    replacement = encoded + b"\0" * (len(EXPECTED_EVENT_RAW) - len(encoded))
    data[EVENT_OFFSET : EVENT_OFFSET + len(EXPECTED_EVENT_RAW)] = replacement
    event_payload.write_bytes(data)

    font_edits: list[dict[str, object]] = []
    for page in range(9):
        name = f"EUC28-{page}.wtm"
        target = payload_for_name(system_out, name)
        source_font = args.injected_font_dir / name
        if not source_font.is_file():
            raise FileNotFoundError(source_font)
        if source_font.stat().st_size != target.stat().st_size:
            raise ValueError(f"font size mismatch for {name}")
        before = sha256(target)
        shutil.copyfile(source_font, target)
        after = sha256(target)
        font_edits.append(
            {
                "name": name,
                "size": target.stat().st_size,
                "before_sha256": before,
                "after_sha256": after,
                "changed": before != after,
            }
        )

    manifest = {
        "schema": "arf-korean-runtime-pilot-v1",
        "source_text": "おい、本当にこれで過ごすのか？",
        "translation_ko": "야, 정말 이러고 지낼 거야?",
        "translation_policy": "Codex internal models only",
        "event": {
            "payload": str(event_payload),
            "offset": EVENT_OFFSET,
            "offset_hex": f"0x{EVENT_OFFSET:X}",
            "capacity": len(EXPECTED_EVENT_RAW),
            "encoded_length": len(encoded),
            "original_raw_hex": EXPECTED_EVENT_RAW.hex().upper(),
            "replacement_raw_hex": replacement.hex().upper(),
            "before_sha256": original_event_sha,
            "after_sha256": sha256(event_payload),
        },
        "fonts": font_edits,
    }
    (args.output_dir / "pilot_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(args.output_dir.resolve()), "event_bytes": len(encoded), "font_pages": 9}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
