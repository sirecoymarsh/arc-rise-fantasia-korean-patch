"""Build small system.vol subset variants for Dolphin runtime isolation.

This is a research-only helper.  It never edits the release manifest/XML.  The
selected variant is copied to a deliberately unmanifested ``__runtime_debug__``
path and is referenced only by a diagnostic Riivolution descriptor.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "work" / "runtime_validation"
VARIANTS = RUNTIME / "systemvol_variants"
APPLICATION = ROOT / "work" / "final_runtime_staging" / "application"
SOURCE = ROOT / "work" / "disc_extracted" / "DATA" / "files" / "Sys" / "system.vol"
MANIFEST = APPLICATION / "system_vol_edits.json"
NODE = Path(r"C:\Program Files\nodejs\node.exe")
CONTAINER_TOOL = ROOT / "work" / "research" / "container_agent" / "container_tool.js"
BASE_XML = RUNTIME / "arc_rise_fantasia_ko_base655_no_dol_no_systemvol.xml"
BASE_JSON = RUNTIME / "arc_rise_fantasia_ko_base655_no_dol_no_systemvol.json"
DIAG_XML = RUNTIME / "arc_rise_fantasia_ko_systemvol_variant.xml"
DIAG_JSON = RUNTIME / "arc_rise_fantasia_ko_systemvol_variant.json"
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
ITEM_SOURCE = ROOT / "work" / "pristine" / "Sys" / "system.vol" / "item.bin"
ITEM_FINAL = APPLICATION / "system_inputs" / "item.bin"
ITEM_RECORD_SIZE = 255
ITEM_RECORD_COUNT = 772
ITEM_FIELDS = {
    "name": (0, 17),
    "description_primary": (17, 81),
    # Bytes 179..180 are the big-endian record ID, so the secondary string
    # buffer is 81 bytes (relative 98..178), not 82.
    "description_secondary": (98, 81),
}
CODEBOOK = ROOT / "work" / "font" / "final_v2" / "codebook.json"
ITEM_771_SAFE_TRANSLATION = "라필 사후 아델에게 계승된\n단아한 무녀의 자태"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_variant(name: str, edits: list[dict]) -> dict:
    variant_dir = VARIANTS / name
    variant_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = variant_dir / "manifest.json"
    output_path = variant_dir / "system.vol"
    report_path = variant_dir / "rebuild_report.json"

    normalized = []
    for edit in edits:
        item = dict(edit)
        replacement = (APPLICATION / item["replacementFile"]).resolve()
        item["replacementFile"] = str(replacement)
        normalized.append(item)
    write_json(manifest_path, {"format": "arf-container-edits-v1", "edits": normalized})

    completed = subprocess.run(
        [str(NODE), str(CONTAINER_TOOL), "rebuild", str(SOURCE), str(manifest_path), str(output_path), str(report_path)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"{name}: container rebuild failed ({completed.returncode})\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return {
        "name": name,
        "edit_count": len(edits),
        "entry_names": [str(edit.get("name", "")) for edit in edits],
        "path": str(output_path),
        "size_bytes": output_path.stat().st_size,
        "sha256": sha256(output_path),
        "report": str(report_path),
    }


def build_item_payload(name: str, field_names: tuple[str, ...], records: range | None = None) -> Path:
    source = ITEM_SOURCE.read_bytes()
    final = ITEM_FINAL.read_bytes()
    expected_size = ITEM_RECORD_SIZE * ITEM_RECORD_COUNT
    if len(source) != expected_size or len(final) != expected_size:
        raise SystemExit("item.bin size/record geometry mismatch")
    out = bytearray(source)
    selected_records = records if records is not None else range(ITEM_RECORD_COUNT)
    for record in selected_records:
        base = record * ITEM_RECORD_SIZE
        for field_name in field_names:
            offset, capacity = ITEM_FIELDS[field_name]
            start = base + offset
            out[start : start + capacity] = final[start : start + capacity]
    output = VARIANTS / "item_payloads" / f"{name}.bin"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(out)
    return output


def build_item_variant(name: str, item_edit: dict, field_names: tuple[str, ...], records: range | None = None) -> dict:
    payload = build_item_payload(name, field_names, records)
    edit = dict(item_edit)
    edit["replacementFile"] = str(payload.resolve())
    result = build_variant(name, [edit])
    result["item_fields"] = list(field_names)
    result["item_records"] = (
        [records.start, records.stop] if records is not None else [0, ITEM_RECORD_COUNT]
    )
    result["item_payload_sha256"] = sha256(payload)
    return result


def encode_custom(text: str) -> bytes:
    codebook = json.loads(CODEBOOK.read_text(encoding="utf-8"))
    mapping = {
        char: bytes.fromhex(entry["bytes_hex"])
        for char, entry in codebook["characters"].items()
    }
    out = bytearray()
    for char in text:
        out.extend(mapping[char] if char in mapping else char.encode("euc_jp"))
    return bytes(out)


def build_item_override_variant(name: str, item_edit: dict, record: int, field_name: str, text: str) -> dict:
    source = bytearray(ITEM_SOURCE.read_bytes())
    offset, capacity = ITEM_FIELDS[field_name]
    encoded = encode_custom(text)
    if len(encoded) >= capacity or b"\0" in encoded:
        raise SystemExit(f"{name}: override does not fit item field")
    start = record * ITEM_RECORD_SIZE + offset
    source[start : start + capacity] = b"\0" * capacity
    source[start : start + len(encoded)] = encoded
    payload = VARIANTS / "item_payloads" / f"{name}.bin"
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_bytes(source)
    edit = dict(item_edit)
    edit["replacementFile"] = str(payload.resolve())
    result = build_variant(name, [edit])
    result.update(
        {
            "item_record": record,
            "item_field": field_name,
            "override_text": text,
            "override_hex": encoded.hex().upper(),
            "override_size": len(encoded),
            "item_payload_sha256": sha256(payload),
        }
    )
    return result


def build_descriptor() -> None:
    tree = ET.parse(BASE_XML)
    patch = tree.getroot().find("patch")
    if patch is None:
        raise SystemExit("diagnostic base XML has no <patch>")
    patch.append(
        ET.Element(
            "file",
            {
                "disc": "/Sys/system.vol",
                "external": "__runtime_debug__/system.vol",
                "resize": "true",
            },
        )
    )
    ET.indent(tree, space="  ")
    tree.write(DIAG_XML, encoding="utf-8", xml_declaration=True)

    descriptor = json.loads(BASE_JSON.read_text(encoding="utf-8-sig"))
    descriptor["display-name"] = "Arc Rise Fantasia Korean system.vol subset diagnostic"
    descriptor["riivolution"]["patches"][0]["xml"] = str(DIAG_XML.resolve())
    write_json(DIAG_JSON, descriptor)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    changed = []
    for edit in manifest["edits"]:
        replacement = APPLICATION / edit["replacementFile"]
        if sha256(replacement).lower() != edit["expectedSha256"].lower():
            changed.append(edit)

    fonts = [edit for edit in changed if str(edit["name"]).startswith("EUC28-")]
    data = [edit for edit in changed if edit not in fonts]
    item_edit = next(edit for edit in changed if edit["name"] == "item.bin")
    variants = [
        build_variant("fonts_only", fonts),
        build_variant("data_only", data),
        build_variant("data_a", data[:6]),
        build_variant("data_b", data[6:]),
        build_variant("data_a1", data[:3]),
        build_variant("data_a2", data[3:6]),
        build_variant("item_only", data[:1]),
        build_variant("shop_dragon", data[1:3]),
        build_item_variant("item_names_only", item_edit, ("name",)),
        build_item_variant("item_primary_only", item_edit, ("description_primary",)),
        build_item_variant("item_secondary_only", item_edit, ("description_secondary",)),
        build_item_variant(
            "item_primary_records_000_385",
            item_edit,
            ("description_primary",),
            range(0, 386),
        ),
        build_item_variant(
            "item_primary_records_386_771",
            item_edit,
            ("description_primary",),
            range(386, 772),
        ),
        build_item_variant(
            "item_primary_records_386_579",
            item_edit,
            ("description_primary",),
            range(386, 580),
        ),
        build_item_variant(
            "item_primary_records_580_771",
            item_edit,
            ("description_primary",),
            range(580, 772),
        ),
        build_item_variant(
            "item_primary_records_580_675",
            item_edit,
            ("description_primary",),
            range(580, 676),
        ),
        build_item_variant(
            "item_primary_records_676_771",
            item_edit,
            ("description_primary",),
            range(676, 772),
        ),
        build_item_variant(
            "item_primary_records_676_723",
            item_edit,
            ("description_primary",),
            range(676, 724),
        ),
        build_item_variant(
            "item_primary_records_724_771",
            item_edit,
            ("description_primary",),
            range(724, 772),
        ),
        build_item_variant(
            "item_primary_records_724_747",
            item_edit,
            ("description_primary",),
            range(724, 748),
        ),
        build_item_variant(
            "item_primary_records_748_771",
            item_edit,
            ("description_primary",),
            range(748, 772),
        ),
        build_item_variant(
            "item_primary_records_748_759",
            item_edit,
            ("description_primary",),
            range(748, 760),
        ),
        build_item_variant(
            "item_primary_records_760_771",
            item_edit,
            ("description_primary",),
            range(760, 772),
        ),
        build_item_variant(
            "item_primary_records_760_765",
            item_edit,
            ("description_primary",),
            range(760, 766),
        ),
        build_item_variant(
            "item_primary_records_766_771",
            item_edit,
            ("description_primary",),
            range(766, 772),
        ),
        build_item_variant(
            "item_primary_records_766_768",
            item_edit,
            ("description_primary",),
            range(766, 769),
        ),
        build_item_variant(
            "item_primary_records_769_771",
            item_edit,
            ("description_primary",),
            range(769, 772),
        ),
        build_item_variant(
            "item_primary_record_769",
            item_edit,
            ("description_primary",),
            range(769, 770),
        ),
        build_item_variant(
            "item_primary_records_770_771",
            item_edit,
            ("description_primary",),
            range(770, 772),
        ),
        build_item_variant(
            "item_primary_record_770",
            item_edit,
            ("description_primary",),
            range(770, 771),
        ),
        build_item_variant(
            "item_primary_record_771",
            item_edit,
            ("description_primary",),
            range(771, 772),
        ),
        build_item_override_variant(
            "item_primary_record_771_safe",
            item_edit,
            771,
            "description_primary",
            ITEM_771_SAFE_TRANSLATION,
        ),
    ]
    build_descriptor()
    DEBUG_FILE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(variants[0]["path"]), DEBUG_FILE)
    report = {
        "format": "arf-systemvol-diagnostic-variants-v1",
        "source": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "changed_entry_count": len(changed),
        "variants": variants,
        "descriptor": str(DIAG_JSON),
        "debug_file": str(DEBUG_FILE),
        "selected": "fonts_only",
    }
    write_json(VARIANTS / "index.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
