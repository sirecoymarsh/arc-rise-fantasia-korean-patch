#!/usr/bin/env python3
"""Bind the reviewed addressee/scene-voice correction set to final staging."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
REPORT = W / "translation/addressee_audit/addressee_scene_voice_corrections.json"
TM = W / "translation/final/translation_memory_draft.json"
MANIFEST = W / "final_runtime_staging/staging_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    need(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def main() -> int:
    for path in (REPORT, TM, MANIFEST):
        need(path.is_file(), f"missing input: {path}")
    report = load(REPORT)
    manifest = load(MANIFEST)
    counts = dict(report.get("counts", {}))
    need(report.get("schema") == "arf-addressee-scene-voice-corrections-v1", "bad correction schema")
    need(report.get("game_id") == "RPJJ99", "bad correction game ID")
    need(report.get("translation_engine_policy") == "Codex internal models only", "bad translator policy")
    need(report.get("external_translation_models_or_apis_used") is False, "external translator recorded")
    need(int(counts.get("candidate_occurrences_reviewed", -1)) == 128, "candidate count mismatch")
    need(int(counts.get("unique_addressee_tm_ids_corrected", -1)) == 127, "addressee count mismatch")
    need(int(counts.get("speaker_voice_template_bleed_corrected", -1)) == 3, "voice-bleed count mismatch")
    need(int(counts.get("unrelated_unit_semantic_copy_corrected", -1)) == 1, "semantic-copy count mismatch")
    need(int(counts.get("total_unique_tm_ids_corrected", -1)) == 131, "total correction count mismatch")
    tm_hash = sha256(TM)
    need(str(report.get("outputs", {}).get("final_translation_memory_sha256", "")).upper() == tm_hash,
         "correction report is not bound to current final TM")
    need(str(manifest.get("inputs", {}).get("translation_memory", {}).get("sha256", "")).upper() == tm_hash,
         "staging is not built from the corrected final TM")
    need(manifest.get("static_validation", {}).get("valid") is True, "staging static validation is not green")

    report_hash = sha256(REPORT)
    manifest.setdefault("inputs", {})["addressee_scene_voice_corrections"] = {
        "path": str(REPORT),
        "sha256": report_hash,
        "translator_model": "Codex internal",
        "external_translation_models_or_apis_used": False,
    }
    manifest.setdefault("counts", {}).update({
        "addressee_candidate_occurrences_reviewed": 128,
        "addressee_unique_tm_ids_corrected": 127,
        "speaker_voice_template_bleed_corrected": 3,
        "semantic_copy_errors_corrected": 1,
        "addressee_scene_voice_total_unique_tm_ids_corrected": 131,
    })
    manifest["addressee_scene_voice_review"] = {
        "decision_unit": report["decision_unit"],
        "candidate_occurrences_reviewed": 128,
        "unique_addressee_tm_ids_corrected": 127,
        "speaker_voice_template_bleed_corrected": 3,
        "unrelated_unit_semantic_copy_corrected": 1,
        "total_unique_tm_ids_corrected": 131,
        "correction_report_sha256": report_hash,
        "final_translation_memory_sha256": tm_hash,
        "translator_model": "Codex internal",
        "external_translation_models_or_apis_used": False,
        "valid": True,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "manifest": str(MANIFEST),
        "manifest_sha256": sha256(MANIFEST),
        "correction_report_sha256": report_hash,
        "final_tm_sha256": tm_hash,
        "corrected_tm_ids": 131,
        "valid": True,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
