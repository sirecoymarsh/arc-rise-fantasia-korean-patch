#!/usr/bin/env python3
"""Validate every reviewed main.dol memory write in staging and release."""
from __future__ import annotations
import hashlib, json, re, struct
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
SOURCE = W / "disc_extracted/DATA/sys/main.dol"
TRANSLATIONS = W / "runtime_fix/main_dol_translations.jsonl"
PATCH_REPORT = W / "runtime_fix/main_dol_patch_report_v2.json"
CROSSREVIEW = W / "runtime_fix/main_dol_crossreview.json"
INTEGRATION = W / "runtime_fix/runtime_supplement_integration.json"
STAGING_MANIFEST = W / "final_runtime_staging/staging_manifest.json"
STAGING_XML = W / "final_runtime_staging/riivolution_sd/riivolution/arc_rise_fantasia_ko_full.xml"
PACKAGE = ROOT / "outputs/Arc_Rise_Fantasia_Korean_Patch_v1.0.3"
PACKAGE_XML = PACKAGE / "payload/riivolution_sd/riivolution/arc_rise_fantasia_ko_full.xml"
PACKAGE_MANIFEST = PACKAGE / "MANIFEST.json"
OUTPUT = W / "validation/main_dol_runtime_residue_release_validation.json"
SOURCE_SHA256 = "4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC"
TARGET_OFFSET = 0x003CF241
TARGET_SOURCE = "ないよ〜〜ん"
TARGET_KOREAN = "없지롱~~"
EXPECTED_REVIEWED = 926
EXPECTED_FINAL_MEMORY = 941


def h(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def need(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dol_sections(data: bytes):
    be32 = lambda off: struct.unpack_from(">I", data, off)[0]
    rows = []
    for i in range(7):
        rows.append((f"text{i}", be32(4*i), be32(0x48+4*i), be32(0x90+4*i)))
    for i in range(11):
        rows.append((f"data{i}", be32(0x1C+4*i), be32(0x64+4*i), be32(0xAC+4*i)))
    return [r for r in rows if r[3]]


def address_for(offset: int, length: int, sections):
    found = [(name, addr + offset - start) for name, start, addr, size in sections
             if start <= offset and offset + length <= start + size]
    need(len(found) == 1, f"DOL section mapping failed at 0x{offset:X}")
    return found[0]


def main() -> int:
    required = [SOURCE, TRANSLATIONS, PATCH_REPORT, CROSSREVIEW, INTEGRATION,
                STAGING_MANIFEST, STAGING_XML, PACKAGE_XML, PACKAGE_MANIFEST]
    for path in required:
        need(path.is_file(), f"missing input: {path}")
    source = SOURCE.read_bytes()
    need(h(SOURCE) == SOURCE_SHA256, "source main.dol hash mismatch")
    rows = [json.loads(line) for line in TRANSLATIONS.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    need(len(rows) == EXPECTED_REVIEWED, "translation row count mismatch")
    need(len({int(r["offset"]) for r in rows}) == EXPECTED_REVIEWED, "duplicate translation offset")
    need(all(r.get("provenance") == "Codex internal model" and r.get("external_translation_used") is False for r in rows),
         "translation provenance mismatch")
    residue = [r for r in rows if int(r["offset"]) == TARGET_OFFSET]
    need(len(residue) == 1, "runtime residue target missing")
    target = residue[0]
    need(target.get("source_text") == TARGET_SOURCE and target.get("translation_ko") == TARGET_KOREAN,
         "runtime residue translation mismatch")
    need(not re.search(r"[\u3041-\u30FA\u3400-\u9FFF\uF900-\uFAFF]", str(target["translation_ko"])),
         "Japanese remains in runtime residue target")
    raw = bytes.fromhex(str(target["source_raw_hex"]))
    need(source[TARGET_OFFSET:TARGET_OFFSET+len(raw)] == raw and source[TARGET_OFFSET+len(raw)] == 0,
         "runtime residue source bytes/NUL mismatch")

    patch = load(PATCH_REPORT)
    cross = load(CROSSREVIEW)
    integ = load(INTEGRATION)
    need(patch.get("valid") is True and int(patch["summary"]["patch_rows"]) == EXPECTED_REVIEWED,
         "main.dol patch report invalid")
    need(patch["inputs"]["translations_jsonl"]["sha256"] == h(TRANSLATIONS), "patch/translation hash mismatch")
    need(cross.get("valid") is True and int(cross["result"]["reviewed_rows"]) == EXPECTED_REVIEWED,
         "cross-review invalid")
    need(int(cross["coverage"]["excluded_debug_internal"]) == 399, "cross-review exclusion count mismatch")
    need(int(integ.get("memory_patch_count", -1)) == EXPECTED_REVIEWED, "runtime integration count mismatch")

    root = ET.parse(STAGING_XML).getroot()
    memory_nodes = list(root.findall(".//memory"))
    need(len(memory_nodes) == EXPECTED_FINAL_MEMORY, "final XML memory count mismatch")
    memory = {}
    for node in memory_nodes:
        key = str(node.attrib["offset"]).upper()
        need(key not in memory, f"duplicate memory address: {key}")
        memory[key] = str(node.attrib["value"]).upper()
    sections = dol_sections(source)
    verified = []
    for item in patch["patches"]:
        offset = int(item["offset"]); length = int(item["byte_length"])
        section, address = address_for(offset, length, sections)
        key = f"0x{address:08X}".upper()
        expected = str(item["encoded_hex"]).upper() + "00" * int(item["zero_padding_bytes"])
        need(memory.get(key) == expected, f"staging memory mismatch at {key}")
        verified.append({"file_offset": offset, "memory_address_hex": key, "section": section,
                         "byte_length": length, "value_sha256": hashlib.sha256(bytes.fromhex(expected)).hexdigest().upper()})

    staging = load(STAGING_MANIFEST)
    need(staging["riivolution"]["memory_count"] == EXPECTED_FINAL_MEMORY, "staging manifest memory count mismatch")
    need(staging["riivolution"]["sha256"] == h(STAGING_XML), "staging XML hash mismatch")
    need(staging["town_map_legend_patch"]["base_memory_rules"] == EXPECTED_REVIEWED, "town-map base count mismatch")
    need(staging["town_map_legend_patch"]["final_memory_rules"] == EXPECTED_FINAL_MEMORY, "town-map final count mismatch")
    need(h(PACKAGE_XML) == h(STAGING_XML), "release/staging XML mismatch")
    package_manifest = load(PACKAGE_MANIFEST)
    need(package_manifest.get("staging_manifest_sha256") == h(STAGING_MANIFEST), "release/staging manifest binding mismatch")

    report = {
        "schema": "arf-main-dol-runtime-residue-release-validation-v1",
        "game_id": "RPJJ99",
        "translator_model": "Codex internal",
        "external_translation_models_or_apis_used": False,
        "target": {"offset": TARGET_OFFSET, "offset_hex": f"0x{TARGET_OFFSET:08X}",
                   "source_text": TARGET_SOURCE, "translation_ko": TARGET_KOREAN,
                   "slot_bytes": len(raw), "source_raw_sha256": hashlib.sha256(raw).hexdigest().upper()},
        "counts": {"reviewed_main_dol_rows": len(rows), "verified_main_dol_memory_writes": len(verified),
                   "final_xml_memory_rules": len(memory_nodes), "town_map_delta_rules": EXPECTED_FINAL_MEMORY-EXPECTED_REVIEWED},
        "inputs": {"translations_sha256": h(TRANSLATIONS), "patch_report_sha256": h(PATCH_REPORT),
                   "crossreview_sha256": h(CROSSREVIEW), "runtime_integration_sha256": h(INTEGRATION),
                   "staging_manifest_sha256": h(STAGING_MANIFEST), "staging_xml_sha256": h(STAGING_XML),
                   "package_manifest_sha256": h(PACKAGE_MANIFEST), "package_xml_sha256": h(PACKAGE_XML)},
        "checks": {"source_bytes_and_nul_verified": True, "codex_only_provenance": True,
                   "target_has_no_japanese_residue": True, "all_926_memory_values_match": True,
                   "crossreview_valid": True, "release_staging_binding_matches": True},
        "error_count": 0, "errors": [], "valid": True,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"valid": True, "target": TARGET_KOREAN, "reviewed": len(rows),
                      "memory_rules": len(memory_nodes), "report": str(OUTPUT), "report_sha256": h(OUTPUT)}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
