#!/usr/bin/env python3
"""Build a statically verified partial RPJJ99 Riivolution staging tree.

The staging binaries remain in ``work/`` and are not included in the
source-free development checkpoint.  A Dolphin screen test is still required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


SYSTEM_TABLE_NAMES = (
    "item.bin",
    "shop.bin",
    "dragon.bin",
    "treasure.bin",
    "magic.bin",
    "special.bin",
    "operation.bin",
    "quest.bin",
    "ability.bin",
    "chat.bin",
    "todo.dat",
)
DIRECT_TABLE_NAMES = ("help.bin", "monster_book.bin")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def run_json(command: list[str]) -> dict:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", type=Path, required=True)
    parser.add_argument("--container-tool", type=Path, required=True)
    parser.add_argument("--source-system-vol", type=Path, required=True)
    parser.add_argument("--table-payload-dir", type=Path, required=True)
    parser.add_argument("--font-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    resolved_output = args.output_dir.resolve()
    expected_parent = (root / "work").resolve()
    if resolved_output.parent != expected_parent:
        raise ValueError(f"output must be a direct child of {expected_parent}")
    if args.output_dir.exists():
        shutil.rmtree(args.output_dir)
    inputs = args.output_dir / "inputs"
    staging_root = args.output_dir / "riivolution_sd/arc_rise_fantasia_ko_dev/files/Sys"
    xml_dir = args.output_dir / "riivolution_sd/riivolution"
    for directory in (inputs, staging_root, xml_dir):
        directory.mkdir(parents=True, exist_ok=True)

    source_inspection = run_json(
        [
            str(args.node),
            str(args.container_tool),
            "inspect",
            str(args.source_system_vol),
        ]
    )
    if source_inspection.get("wrapper") != "RTDP":
        raise ValueError("source system.vol is not RTDP")
    entries = source_inspection["entries"]
    entries_by_name = {str(entry["name"]): entry for entry in entries}
    if len(entries_by_name) != len(entries):
        raise ValueError("system.vol contains duplicate names; explicit map required")

    replacements: dict[str, Path] = {}
    for page in range(9):
        name = f"EUC28-{page}.wtm"
        replacements[name] = args.font_dir / name
    for name in SYSTEM_TABLE_NAMES:
        replacements[name] = args.table_payload_dir / name
    for name, path in replacements.items():
        if name not in entries_by_name:
            raise ValueError(f"missing system.vol entry: {name}")
        if not path.is_file():
            raise ValueError(f"missing replacement: {path}")

    edit_items = []
    copied_by_name: dict[str, Path] = {}
    for name, replacement in replacements.items():
        copied = inputs / name
        shutil.copy2(replacement, copied)
        copied_by_name[name] = copied
        source_entry = entries_by_name[name]
        edit_items.append(
            {
                "entryPath": [int(source_entry["index"])],
                "expectedSha256": str(source_entry["decodedSha256"]),
                "replacementFile": f"inputs/{name}",
            }
        )
    edit_items.sort(key=lambda item: item["entryPath"])
    edits = {"format": "arf-container-edits-v1", "edits": edit_items}
    edits_path = args.output_dir / "system_vol_edits.json"
    edits_path.write_text(
        json.dumps(edits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    output_system_vol = staging_root / "system.vol"
    rebuild_report_path = args.output_dir / "system_vol_rebuild_report.json"
    subprocess.run(
        [
            str(args.node),
            str(args.container_tool),
            "rebuild",
            str(args.source_system_vol),
            str(edits_path),
            str(output_system_vol),
            str(rebuild_report_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    output_inspection = run_json(
        [
            str(args.node),
            str(args.container_tool),
            "inspect",
            str(output_system_vol),
        ]
    )

    errors: list[dict[str, object]] = []
    output_entries = output_inspection["entries"]
    if len(output_entries) != len(entries):
        errors.append({"code": "entry_count_changed"})
    for source_entry, output_entry in zip(entries, output_entries):
        if source_entry["index"] != output_entry["index"] or source_entry["name"] != output_entry["name"]:
            errors.append(
                {
                    "code": "entry_identity_changed",
                    "index": source_entry["index"],
                }
            )
            continue
        name = str(source_entry["name"])
        expected_hash = (
            sha256(copied_by_name[name]).lower()
            if name in copied_by_name
            else str(source_entry["decodedSha256"])
        )
        if str(output_entry["decodedSha256"]) != expected_hash:
            errors.append(
                {
                    "code": "decoded_entry_hash_mismatch",
                    "index": source_entry["index"],
                    "name": name,
                    "expected": expected_hash,
                    "actual": output_entry["decodedSha256"],
                }
            )

    direct_files = []
    for name in DIRECT_TABLE_NAMES:
        source = args.table_payload_dir / name
        if not source.is_file():
            raise ValueError(f"missing direct replacement: {source}")
        destination = staging_root / name
        shutil.copy2(source, destination)
        direct_files.append(
            {
                "disc_path": f"/Sys/{name}",
                "staged_path": str(destination),
                "size_bytes": destination.stat().st_size,
                "sha256": sha256(destination),
            }
        )

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<wiidisc version="1">
  <id game="RPJ" developer="99" disc="0" version="0">
    <region type="J" />
  </id>
  <options>
    <section name="Arc Rise Fantasia">
      <option id="arf-ko-dev-option" name="Korean Development Checkpoint" default="1">
        <choice name="Enabled"><patch id="arf-ko-dev" /></choice>
      </option>
    </section>
  </options>
  <patch id="arf-ko-dev" root="/arc_rise_fantasia_ko_dev/files">
    <file disc="/Sys/system.vol" external="Sys/system.vol" resize="true" />
    <file disc="/Sys/help.bin" external="Sys/help.bin" resize="false" />
    <file disc="/Sys/monster_book.bin" external="Sys/monster_book.bin" resize="false" />
  </patch>
</wiidisc>
"""
    xml_path = xml_dir / "arc_rise_fantasia_ko_dev.xml"
    xml_path.write_text(xml, encoding="utf-8")
    try:
        xml_root = ET.parse(xml_path).getroot()
        game_id = xml_root.find("id")
        xml_valid = (
            xml_root.tag == "wiidisc"
            and game_id is not None
            and game_id.attrib.get("game") == "RPJ"
            and game_id.attrib.get("developer") == "99"
        )
    except ET.ParseError:
        xml_valid = False
    if not xml_valid:
        errors.append({"code": "riivolution_xml_invalid"})

    rebuild_report = json.loads(rebuild_report_path.read_text(encoding="utf-8"))
    audits = rebuild_report.get("containerAuditBottomUp", [])
    rebuild_policy = audits[-1].get("policy") if audits else None
    manifest = {
        "schema": "arf-partial-runtime-staging-static-validation-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "runtime_ready_release": False,
        "dolphin_screen_test": "pending",
        "source_system_vol": {
            "path": str(args.source_system_vol.resolve()),
            "size_bytes": args.source_system_vol.stat().st_size,
            "sha256": sha256(args.source_system_vol),
        },
        "output_system_vol": {
            "path": str(output_system_vol),
            "size_bytes": output_system_vol.stat().st_size,
            "sha256": sha256(output_system_vol),
            "edited_entries": len(edit_items),
            "entry_count": len(output_entries),
            "rebuild_policy": rebuild_policy,
        },
        "direct_files": direct_files,
        "riivolution_xml": {
            "path": str(xml_path),
            "sha256": sha256(xml_path),
        },
        "static_validation": {
            "edited_decoded_hashes_match": not any(
                item["code"] == "decoded_entry_hash_mismatch" for item in errors
            ),
            "untouched_entries_preserved": not any(
                item["code"] in {"decoded_entry_hash_mismatch", "entry_identity_changed"}
                for item in errors
            ),
            "entry_identity_preserved": not any(
                item["code"] == "entry_identity_changed" for item in errors
            ),
            "riivolution_xml_valid": xml_valid,
            "error_count": len(errors),
            "errors": errors,
            "valid": not errors,
        },
    }
    manifest_path = args.output_dir / "staging_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "system_vol_edits": len(edit_items),
                "source_size": args.source_system_vol.stat().st_size,
                "output_size": output_system_vol.stat().st_size,
                "direct_files": len(direct_files),
                "static_error_count": len(errors),
                "valid": not errors,
                "dolphin_screen_test": "pending",
            },
            ensure_ascii=False,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
