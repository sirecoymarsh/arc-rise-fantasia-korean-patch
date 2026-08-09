#!/usr/bin/env python3
"""Verify the Korean runtime pilot at archive, payload, and glyph-code levels."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def differences(left: bytes, right: bytes) -> list[int]:
    if len(left) != len(right):
        raise ValueError("cannot produce same-size diff for differently sized files")
    return [index for index, (a, b) in enumerate(zip(left, right)) if a != b]


def rtdp_entry_range(data: bytes, index: int) -> tuple[int, int, int]:
    if data[:4] != b"RTDP":
        raise ValueError("not RTDP")
    eoh = struct.unpack_from(">I", data, 4)[0]
    count = struct.unpack_from(">I", data, 8)[0]
    if not (0 <= index < count):
        raise IndexError(index)
    pos = 0x20 + index * 40
    size, relative = struct.unpack_from(">II", data, pos + 32)
    start = eoh + relative
    return eoh, start, start + size


def compare_payload_trees(expected: Path, actual: Path) -> dict[str, object]:
    expected_files = sorted(p.relative_to(expected).as_posix() for p in expected.rglob("*") if p.is_file())
    actual_files = sorted(p.relative_to(actual).as_posix() for p in actual.rglob("*") if p.is_file())
    # Extraction manifests describe different parent archive paths/hashes and
    # are not decoded payloads.  Compare payload files and template.bin only.
    expected_core = [name for name in expected_files if name != "manifest.json"]
    actual_core = [name for name in actual_files if name != "manifest.json"]
    mismatches = []
    for name in sorted(set(expected_core) & set(actual_core)):
        left, right = expected / name, actual / name
        if sha256_file(left) != sha256_file(right):
            mismatches.append(name)
    return {
        "expected_files": len(expected_core),
        "actual_files": len(actual_core),
        "file_lists_equal": expected_core == actual_core,
        "mismatches": mismatches,
        "byte_exact": expected_core == actual_core and not mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-event", type=Path, required=True)
    parser.add_argument("--pilot-event", type=Path, required=True)
    parser.add_argument("--original-system", type=Path, required=True)
    parser.add_argument("--pilot-system", type=Path, required=True)
    parser.add_argument("--edited-event-fixture", type=Path, required=True)
    parser.add_argument("--edited-system-fixture", type=Path, required=True)
    parser.add_argument("--reextracted-event", type=Path, required=True)
    parser.add_argument("--reextracted-system", type=Path, required=True)
    parser.add_argument("--encoded-korean", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    original_event = args.original_event.read_bytes()
    pilot_event = args.pilot_event.read_bytes()
    event_diff = differences(original_event, pilot_event)
    event_eoh, event_start, event_end = rtdp_entry_range(original_event, 0)
    payload_offset = 0x12F
    expected_payload = (args.edited_event_fixture / "payloads" / "0000__fc_00_001.bscr").read_bytes()
    encoded = args.encoded_korean.read_bytes()
    encoded_recovered = expected_payload[payload_offset : payload_offset + len(encoded)] == encoded
    event_diff_confined = all(event_start + payload_offset <= pos < event_start + payload_offset + 30 for pos in event_diff)

    original_system = args.original_system.read_bytes()
    pilot_system = args.pilot_system.read_bytes()
    system_diff = differences(original_system, pilot_system)
    system_eoh, font0_start, font0_end = rtdp_entry_range(original_system, 0)
    system_diff_confined = bool(system_diff) and all(font0_start <= pos < font0_end for pos in system_diff)

    event_tree = compare_payload_trees(args.edited_event_fixture, args.reextracted_event)
    system_tree = compare_payload_trees(args.edited_system_fixture, args.reextracted_system)
    validation = {
        "schema": "arf-korean-runtime-pilot-validation-v1",
        "event_archive": {
            "original_sha256": sha256_bytes(original_event),
            "pilot_sha256": sha256_bytes(pilot_event),
            "size_preserved": len(original_event) == len(pilot_event),
            "header_table_preserved": original_event[:event_eoh] == pilot_event[:event_eoh],
            "different_byte_count": len(event_diff),
            "differences_confined_to_expected_30_byte_field": event_diff_confined,
            "encoded_korean_recovered": encoded_recovered,
            "reextracted_tree": event_tree,
        },
        "system_archive": {
            "original_sha256": sha256_bytes(original_system),
            "pilot_sha256": sha256_bytes(pilot_system),
            "size_preserved": len(original_system) == len(pilot_system),
            "header_table_preserved": original_system[:system_eoh] == pilot_system[:system_eoh],
            "different_byte_count": len(system_diff),
            "differences_confined_to_EUC28_0_payload": system_diff_confined,
            "reextracted_tree": system_tree,
        },
    }
    checks = [
        validation["event_archive"]["size_preserved"],
        validation["event_archive"]["header_table_preserved"],
        event_diff_confined,
        encoded_recovered,
        event_tree["byte_exact"],
        validation["system_archive"]["size_preserved"],
        validation["system_archive"]["header_table_preserved"],
        system_diff_confined,
        system_tree["byte_exact"],
    ]
    validation["all_static_checks_passed"] = all(checks)
    validation["runtime_dolphin_check"] = "pending"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_static_checks_passed": all(checks), "event_diffs": len(event_diff), "system_diffs": len(system_diff)}))
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
