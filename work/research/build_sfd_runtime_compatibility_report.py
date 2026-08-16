#!/usr/bin/env python3
"""Prove that the rejected localized SFD is absent and the trusted disc movie is used."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path


SOURCE_SHA256 = "8653907F6F4DE206E57FE108EC2D050135E4DB68306AC8CAE7D2BEBCA46DC4A0"
REJECTED_SHA256 = "A6095E7E5DB15012AA914AF41958F4BF5947DD5029C199605C66FCB6577BD2A3"
PHYSICAL_PATH = "Movie/RAY_OP_02.sfd"
EDITED_INTERVAL = (48.1, 54.5)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return value


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    work = root / "work"
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=work / "disc_extracted/DATA/files/Movie/RAY_OP_02.sfd")
    parser.add_argument("--rejected", type=Path, default=work / "runtime_fix/sfd_ko/payloads/Movie/RAY_OP_02.sfd")
    parser.add_argument("--timestamp-audit", type=Path, default=work / "runtime_validation/sfd_frame_timestamp_audit.json")
    parser.add_argument("--freeze-match", type=Path, default=work / "runtime_validation/sfd_freeze_frame_match.json")
    parser.add_argument("--staging-manifest", type=Path, default=work / "final_runtime_staging/staging_manifest.json")
    parser.add_argument("--xml", type=Path, default=work / "final_runtime_staging/riivolution_sd/riivolution/arc_rise_fantasia_ko_full.xml")
    parser.add_argument("--staged-files", type=Path, default=work / "final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files")
    parser.add_argument("--output", type=Path, default=work / "runtime_validation/sfd_runtime_compatibility_repair.json")
    args = parser.parse_args()

    timestamp = load(args.timestamp_audit)
    freeze = load(args.freeze_match)
    manifest = load(args.staging_manifest)
    source = timestamp.get("source", {})
    rejected = timestamp.get("payload", {})
    top = list(freeze.get("payload", {}).get("top_matches", []))
    best_seconds = float(top[0].get("seconds")) if top else None
    staged_rows = {
        str(row.get("physical_path"))
        for row in manifest.get("static_validation", {}).get("staged_files", [])
        if isinstance(row, dict)
    }
    xml_rules = {
        str(node.get("disc", "")).lstrip("/")
        for node in ET.parse(args.xml).getroot().iter("file")
    }
    compatibility = manifest.get("sfd_runtime_compatibility", {})
    checks = [
        {"name": "trusted_source_hash", "passed": args.source.is_file() and sha256(args.source) == SOURCE_SHA256},
        {"name": "rejected_payload_hash", "passed": args.rejected.is_file() and sha256(args.rejected) == REJECTED_SHA256},
        {"name": "source_has_no_timestamp_regressions", "passed": source.get("regression_count") == 0},
        {"name": "rejected_payload_has_143_timestamp_regressions", "passed": rejected.get("regression_count") == 143},
        {"name": "rejected_payload_has_97_duplicate_timestamps", "passed": rejected.get("duplicate_count") == 97},
        {"name": "frame_count_changed_by_reencode", "passed": source.get("frame_count") == 8596 and rejected.get("frame_count") == 8597},
        {"name": "freeze_frame_inside_edited_interval", "passed": best_seconds is not None and EDITED_INTERVAL[0] <= best_seconds <= EDITED_INTERVAL[1]},
        {"name": "unsafe_sfd_absent_from_staging", "passed": not (args.staged_files / PHYSICAL_PATH).exists()},
        {"name": "unsafe_sfd_absent_from_manifest", "passed": PHYSICAL_PATH not in staged_rows},
        {"name": "unsafe_sfd_absent_from_xml", "passed": PHYSICAL_PATH not in xml_rules},
        {"name": "manifest_records_original_disc_fallback", "passed": compatibility.get("overlay_present") is False and compatibility.get("source_disc_file_used") is True and compatibility.get("valid") is True},
    ]
    errors = [row["name"] for row in checks if not row["passed"]]
    report = {
        "schema": "arf-ko-sfd-runtime-compatibility-repair-v1",
        "game_id": "RPJJ99",
        "physical_path": PHYSICAL_PATH,
        "decision": "use_trusted_original_disc_sfd",
        "translation_engine_policy": "Codex internal model only",
        "external_translation_models_or_apis_used": False,
        "edited_interval_seconds": list(EDITED_INTERVAL),
        "matched_freeze_frame_seconds": best_seconds,
        "source": {"path": str(args.source), "sha256": sha256(args.source), **source},
        "rejected_payload": {"path": str(args.rejected), "sha256": sha256(args.rejected), **rejected},
        "timestamp_audit": {"path": str(args.timestamp_audit), "sha256": sha256(args.timestamp_audit)},
        "freeze_match": {"path": str(args.freeze_match), "sha256": sha256(args.freeze_match)},
        "staging_manifest": {"path": str(args.staging_manifest), "sha256": sha256(args.staging_manifest)},
        "riivolution_xml": {"path": str(args.xml), "sha256": sha256(args.xml)},
        "checks": checks,
        "passed_count": sum(bool(row["passed"]) for row in checks),
        "failed_count": len(errors),
        "error_count": len(errors),
        "errors": errors,
        "valid": not errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": report["valid"], "passed": report["passed_count"], "errors": errors, "output": str(args.output)}, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
