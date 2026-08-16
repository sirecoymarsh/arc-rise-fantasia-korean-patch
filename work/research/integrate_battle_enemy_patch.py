#!/usr/bin/env python3
"""Integrate translated battle enemy data and the append-only v3 font into final staging."""

from __future__ import annotations
import hashlib, json, shutil
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
ST = W / "final_runtime_staging"
FILES = ST / "riivolution_sd" / "arc_rise_fantasia_ko_full" / "files"
XML = ST / "riivolution_sd" / "riivolution" / "arc_rise_fantasia_ko_full.xml"
MANIFEST = ST / "staging_manifest.json"
APP = W / "battle_enemy_application"
FONT = W / "font" / "final_v3"
CATALOG = W / "translation" / "battle_enemy" / "battle_enemy_catalog.json"
SKILLS = W / "translation" / "battle_enemy" / "battle_enemy_skill_translations.json"
OLD_ROOT = r"C:\Users\CadriacLord\Documents\Codex\2026-08-03\f-down-arc-rise-fantasia-japan"


def h(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def need(ok, message):
    if not ok:
        raise SystemExit(message)


def rebind(value):
    if isinstance(value, str):
        return value.replace(OLD_ROOT, str(ROOT))
    if isinstance(value, list):
        return [rebind(v) for v in value]
    if isinstance(value, dict):
        return {k: rebind(v) for k, v in value.items()}
    return value


def staged_row(rows, relative):
    matches = [row for row in rows if row["physical_path"] == relative]
    need(len(matches) == 1, f"expected one staged row: {relative}")
    return matches[0]


def main():
    report_path = APP / "application_report.json"
    system_report_path = APP / "system_font_v3_rebuild_report.json"
    codebook_path = FONT / "codebook.json"
    append_path = FONT / "codebook_append_only_verification.json"
    inject_manifest_path = FONT / "injection_manifest.json"
    inject_verify_path = FONT / "injection_verification.json"
    required = [
        XML, MANIFEST, report_path, system_report_path, CATALOG, SKILLS,
        codebook_path, append_path, inject_manifest_path, inject_verify_path,
        APP / "btl_enemy.vld", APP / "btl_usual.vol", APP / "system.vol",
        W / "runtime_validation" / "sfd_frame_timestamp_audit.json",
        W / "runtime_validation" / "sfd_freeze_frame_match.json",
    ]
    for path in required:
        need(path.is_file(), f"missing input: {path}")

    rejected_sfd = FILES / "Movie" / "RAY_OP_02.sfd"
    rejected_sfd_was_present = rejected_sfd.is_file()
    if rejected_sfd_was_present:
        rejected_sfd.unlink()

    app = load(report_path)
    expected_counts = {
        "entries": 270, "display_names": 270, "part_names": 3, "skill_names": 563,
        "total_units": 836, "entries_fitting_source_slots": 270,
        "changed_outside_allowed_bytes": 0,
    }
    need(app.get("valid") is True and app["counts"] == expected_counts, "battle application invalid")
    need(h(APP / "btl_enemy.vld") == app["output"]["vld_sha256"], "VLD hash mismatch")
    need(h(APP / "btl_usual.vol") == app["output"]["btl_usual_sha256"], "usual hash mismatch")
    system_report = load(system_report_path)
    need(h(APP / "system.vol") == system_report["outputSha256"].upper(), "system hash mismatch")

    append = load(append_path)
    inject_verify = load(inject_verify_path)
    inject_manifest = load(inject_manifest_path)
    codebook = load(codebook_path)
    need(append.get("valid") is True and inject_verify.get("valid") is True, "font verification invalid")
    need(append["existing_assignments_changed"] == 0 and append["appended_characters"] == 1, "font is not append-only")
    need(codebook["assigned"] == 1370, "unexpected v3 codebook size")

    copies = {
        "Btl/btl_enemy.vld": APP / "btl_enemy.vld",
        "Btl/btl_usual.vol": APP / "btl_usual.vol",
        "Sys/system.vol": APP / "system.vol",
    }
    for relative, source in copies.items():
        target = FILES / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        need(h(target) == h(source), f"copy mismatch: {relative}")

    text = XML.read_text(encoding="utf-8-sig")
    text = "\n".join(
        line for line in text.splitlines()
        if 'disc="/Movie/RAY_OP_02.sfd"' not in line
    ) + "\n"
    rule = '    <file disc="/Btl/btl_enemy.vld" external="Btl/btl_enemy.vld" resize="false" />'
    if rule not in text:
        anchor = '    <file disc="/Btl/btl_usual.vol" external="Btl/btl_usual.vol" resize="false" />'
        need(anchor in text, "XML anchor missing")
        text = text.replace(anchor, anchor + "\n" + rule, 1)
    XML.write_text(text, encoding="utf-8")
    need(XML.read_text(encoding="utf-8").count(rule) == 1, "bad enemy XML rule count")

    root = ET.parse(XML).getroot()
    file_nodes = list(root.iter("file"))
    memory_nodes = list(root.iter("memory"))
    file_count = len(file_nodes)
    memory_count = len(memory_nodes)
    resize_true = sum(n.attrib.get("resize", "false").lower() == "true" for n in file_nodes)
    need((file_count, memory_count, resize_true) == (683, 925, 559), "unexpected XML counts")

    doc = rebind(load(MANIFEST))
    supplemental = doc["supplemental_runtime_patch"]
    supplemental["physical_files"] = [
        row for row in supplemental.get("physical_files", [])
        if row.get("physical_path") != "Movie/RAY_OP_02.sfd"
    ]
    supplemental["physical_count"] = 27
    artifacts = supplemental.get("artifacts", {})
    artifacts.pop("sfd_video_replacement_report_sha256", None)
    artifacts.pop("sfd_final_validation_sha256", None)
    doc["sfd_runtime_compatibility"] = {
        "physical_path": "Movie/RAY_OP_02.sfd",
        "overlay_present": False,
        "source_disc_file_used": True,
        "source_sha256": "8653907F6F4DE206E57FE108EC2D050135E4DB68306AC8CAE7D2BEBCA46DC4A0",
        "rejected_payload_sha256": "A6095E7E5DB15012AA914AF41958F4BF5947DD5029C199605C66FCB6577BD2A3",
        "source_timestamp_regressions": 0,
        "rejected_payload_timestamp_regressions": 143,
        "rejected_payload_duplicate_timestamps": 97,
        "freeze_frame_seconds": 48.5,
        "edited_interval_seconds": [48.1, 54.5],
        "timestamp_audit_sha256": h(W / "runtime_validation" / "sfd_frame_timestamp_audit.json"),
        "freeze_match_sha256": h(W / "runtime_validation" / "sfd_freeze_frame_match.json"),
        "valid": True,
    }
    need(doc["schema"] == "arf-full-runtime-staging-v2" and doc["game_id"] == "RPJJ99", "bad manifest identity")
    inputs = doc["inputs"]
    inputs["codebook"] = {"path": str(codebook_path), "sha256": h(codebook_path), "assigned_characters": 1370}
    inputs["battle_enemy_catalog"] = {"path": str(CATALOG), "sha256": h(CATALOG)}
    inputs["battle_enemy_skill_translations"] = {
        "path": str(SKILLS), "sha256": h(SKILLS),
        "translation_engine_policy": "Codex internal model only",
        "external_translation_models_or_apis_used": False,
    }
    inputs["battle_enemy_application_report"] = {"path": str(report_path), "sha256": h(report_path)}
    inputs["font_v3_append_only_verification"] = {"path": str(append_path), "sha256": h(append_path)}
    inputs["font_v3_injection_verification"] = {"path": str(inject_verify_path), "sha256": h(inject_verify_path)}

    doc["counts"].update({
        "supplemental_physical_files": 27,
        "staged_physical_files": 683, "riivolution_file_rules": 683,
        "battle_enemy_entries": 270, "battle_enemy_display_name_occurrences": 270,
        "battle_enemy_part_name_occurrences": 3,
        "battle_enemy_skill_name_occurrences": 563,
        "battle_enemy_translation_occurrences": 836,
        "battle_enemy_unique_skill_names": 209,
        "battle_enemy_unique_part_names": 3,
    })
    doc["riivolution"].update({
        "file_count": file_count, "resize_true_count": resize_true,
        "sha256": h(XML), "memory_count": memory_count,
    })

    static = doc["static_validation"]
    rows = [row for row in static["staged_files"] if row["physical_path"] != "Movie/RAY_OP_02.sfd"]
    static["staged_files"] = rows
    staged_row(rows, "Btl/btl_usual.vol").update({
        "output_sha256": app["output"]["btl_usual_sha256"],
        "output_size": app["output"]["btl_usual_size"],
    })
    staged_row(rows, "Sys/system.vol").update({
        "output_sha256": h(APP / "system.vol"),
        "output_size": (APP / "system.vol").stat().st_size,
    })
    vld_row = next((r for r in rows if r["physical_path"] == "Btl/btl_enemy.vld"), None)
    if vld_row is None:
        vld_row = {"physical_path": "Btl/btl_enemy.vld"}
        rows.append(vld_row)
    vld_row.update({
        "source_sha256": app["source"]["vld_sha256"],
        "output_sha256": app["output"]["vld_sha256"],
        "source_size": app["source"]["vld_size"],
        "output_size": app["output"]["vld_size"],
    })
    rows.sort(key=lambda r: r["physical_path"].lower())
    static["staged_file_count"] = 683

    local = static["local_physical_reports"]
    usual = staged_row(local, "Btl/btl_usual.vol")
    usual.update({
        "output_sha256": app["output"]["btl_usual_sha256"],
        "output_size": app["output"]["btl_usual_size"],
        "edited_leaf_count": 14,
        "container_report": "work/battle_enemy_application/application_report.json",
    })
    local_vld = next((r for r in local if r["physical_path"] == "Btl/btl_enemy.vld"), None)
    if local_vld is None:
        local_vld = {"physical_path": "Btl/btl_enemy.vld"}
        local.append(local_vld)
    local_vld.update({
        "source_sha256": app["source"]["vld_sha256"],
        "output_sha256": app["output"]["vld_sha256"],
        "source_size": app["source"]["vld_size"],
        "output_size": app["output"]["vld_size"],
        "edited_leaf_count": 270, "translated_unit_count": 836,
        "container_report": "work/battle_enemy_application/application_report.json",
    })
    local.sort(key=lambda r: r["physical_path"].lower())

    system = static["system"]
    system.update({
        "mode": "rebuilt_cumulatively_from_final_tables_fonts_v3_and_nowloading",
        "output_system_sha256": h(APP / "system.vol"),
        "output_system_size": (APP / "system.vol").stat().st_size,
        "rebuild_report": "work/battle_enemy_application/system_font_v3_rebuild_report.json",
    })
    pages = {row["page"]: row for row in inject_manifest["files"]}
    for entry in system["verified_internal_entries"]:
        if entry["name"].startswith("EUC28-") and entry["name"].endswith(".wtm"):
            page = int(entry["name"][6:-4])
            entry["sha256"] = pages[page]["output_sha256"].upper()

    doc["battle_enemy_application"] = {
        "report": str(report_path), "report_sha256": h(report_path), "valid": True,
        **expected_counts, "layout_policy": app["layout_policy"],
    }
    doc["font_v3"] = {
        "codebook_sha256": h(codebook_path), "assigned_characters": 1370,
        "appended_characters": 1, "existing_assignments_changed": 0,
        "injection_verification_sha256": h(inject_verify_path), "valid": True,
    }
    doc["supplemental_runtime_patch"]["codebook_sha256"] = h(codebook_path)
    doc["runtime_ready_release"] = False
    doc["dolphin_screen_test"] = "pending_final_single_run"

    physical = sorted(path for path in FILES.rglob("*") if path.is_file())
    rules = {n.attrib["external"].replace("\\", "/") for n in file_nodes}
    actual = {path.relative_to(FILES).as_posix() for path in physical}
    need(len(physical) == 683 and rules == actual, "physical/XML file set mismatch")
    for row in rows:
        path = FILES / Path(row["physical_path"])
        need(path.is_file(), f"missing staged file: {row['physical_path']}")
        need(h(path) == row["output_sha256"] and path.stat().st_size == row["output_size"], f"staged row mismatch: {row['physical_path']}")

    static.update({"valid": True, "error_count": 0, "errors": []})
    MANIFEST.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    integration = {
        "schema": "arf-battle-enemy-staging-integration-v1", "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal model only",
        "external_translation_models_or_apis_used": False,
        "staging_manifest": {"path": str(MANIFEST), "sha256": h(MANIFEST)},
        "xml": {"path": str(XML), "sha256": h(XML), "file_count": file_count,
                "memory_count": memory_count, "resize_true_count": resize_true},
        "physical_file_count": len(physical),
        "removed_unsafe_sfd_overlay": {
            "physical_path": "Movie/RAY_OP_02.sfd",
            "was_present_before_repair": rejected_sfd_was_present,
            "present_after_repair": rejected_sfd.is_file(),
            "source_disc_file_used": True,
        },
        "outputs": {rel: {"path": str(FILES / Path(rel)), "size": (FILES / Path(rel)).stat().st_size,
                          "sha256": h(FILES / Path(rel))} for rel in copies},
        "battle_counts": expected_counts,
        "font": {"codebook_sha256": h(codebook_path), "assigned_characters": 1370,
                 "appended_characters": 1, "existing_assignments_changed": 0},
        "error_count": 0, "errors": [], "valid": True,
    }
    out = APP / "staging_integration_report.json"
    out.write_text(json.dumps(integration, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(integration, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
