#!/usr/bin/env python3
"""Final end-to-end proof for the reviewed addressee and scene-voice fixes."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
REPORT = W / "translation/addressee_audit/addressee_scene_voice_corrections.json"
QUEUE = W / "translation/addressee_audit/review_queue.json"
TM = W / "translation/final/translation_memory_draft.json"
CATALOG = W / "catalog/text_v2/text_catalog.json"
CODEBOOK = W / "font/final_v3/codebook.json"
STAGING = W / "final_runtime_staging"
STAGING_MANIFEST = STAGING / "staging_manifest.json"
STAGED_FILES = STAGING / "riivolution_sd/arc_rise_fantasia_ko_full/files"
SOURCE_FILES = W / "disc_extracted/DATA/files"
OCCURRENCE_MANIFEST = STAGING / "application/occurrence_application_manifest.jsonl"
BUILDER = W / "research/build_full_runtime_staging.py"
BSCR_TOOL = W / "research/bscr_agent/bscr_tool.py"
LZ10_TOOL = W / "research/arf_lz10.py"
ENCODER = W / "research/encode_custom_euc28.py"
OUTPUT = W / "validation/addressee_scene_voice_release_validation.json"

TOKEN_RE = re.compile(r"<\$[0-9A-Fa-f]{2}>|<#[0-9A-Fa-f]{2}>|\\[nfrt]")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    checks: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    def check(name: str, condition: bool, **evidence: Any) -> None:
        checks.append({"name": name, "passed": bool(condition), **evidence})
        if not condition:
            errors.append({"code": name, **evidence})

    required = (
        REPORT, QUEUE, TM, CATALOG, CODEBOOK, STAGING_MANIFEST,
        OCCURRENCE_MANIFEST, BUILDER, BSCR_TOOL, LZ10_TOOL, ENCODER,
    )
    missing = [str(path) for path in required if not path.is_file()]
    check("required_inputs_present", not missing, missing=missing)
    if missing:
        return write_report(checks, errors, 0, 0, 0)

    report = load(REPORT)
    queue = load(QUEUE)
    tm = load(TM)
    catalog = load(CATALOG)
    codebook = load(CODEBOOK)
    manifest = load(STAGING_MANIFEST)
    corrections = list(report.get("corrections", []))
    correction_by_id = {str(row.get("tm_id")): row for row in corrections}
    counts = dict(report.get("counts", {}))

    check(
        "correction_report_identity_and_policy",
        report.get("schema") == "arf-addressee-scene-voice-corrections-v1"
        and report.get("game_id") == "RPJJ99"
        and report.get("translation_engine_policy") == "Codex internal models only"
        and report.get("external_translation_models_or_apis_used") is False,
        report_sha256=sha256_file(REPORT),
    )
    check(
        "correction_counts_exact",
        int(counts.get("candidate_occurrences_reviewed", -1)) == 128
        and int(counts.get("unique_addressee_tm_ids_corrected", -1)) == 127
        and int(counts.get("speaker_voice_template_bleed_corrected", -1)) == 3
        and int(counts.get("unrelated_unit_semantic_copy_corrected", -1)) == 1
        and int(counts.get("total_unique_tm_ids_corrected", -1)) == 131
        and len(corrections) == 131
        and len(correction_by_id) == 131,
        counts=counts,
        correction_rows=len(corrections),
    )

    queue_rows = list(queue.get("all_dangsin_lines", []))
    queue_ids = {str(row.get("tm_id")) for row in queue_rows}
    scene_rows = [row for row in corrections if row.get("category") == "scene_addressee_and_story_phase_voice"]
    scene_ids = {str(row.get("tm_id")) for row in scene_rows}
    check(
        "review_queue_closed_exactly",
        len(queue_rows) == 128 and len(queue_ids) == 127 and scene_ids == queue_ids,
        queue_rows=len(queue_rows),
        queue_unique_tm_ids=len(queue_ids),
        corrected_scene_tm_ids=len(scene_ids),
    )
    residual_dangsin = [row["tm_id"] for row in scene_rows if "당신" in str(row.get("after", ""))]
    check("reviewed_dangsin_residue_zero", not residual_dangsin, residual_tm_ids=residual_dangsin)

    category_counts: dict[str, int] = defaultdict(int)
    for row in corrections:
        category_counts[str(row.get("category"))] += 1
    check(
        "scene_voice_and_semantic_categories_exact",
        category_counts == {
            "scene_addressee_and_story_phase_voice": 127,
            "speaker_voice_template_bleed": 3,
            "unrelated_unit_semantic_copy": 1,
        },
        category_counts=dict(category_counts),
    )

    token_errors = []
    for row in corrections:
        before_tokens = TOKEN_RE.findall(str(row.get("source_text", "")))
        after_tokens = TOKEN_RE.findall(str(row.get("after", "")))
        if before_tokens != after_tokens:
            token_errors.append({"tm_id": row.get("tm_id"), "source": before_tokens, "after": after_tokens})
    check("corrected_control_tokens_preserved", not token_errors, errors=token_errors[:20])

    tm_units = {str(row.get("tm_id")): row for row in tm.get("units", [])}
    tm_mismatches = []
    all_occurrence_ids: set[str] = set()
    for tm_id, correction in correction_by_id.items():
        unit = tm_units.get(tm_id)
        if unit is None or str(unit.get("translation_ko")) != str(correction.get("after")):
            tm_mismatches.append(tm_id)
            continue
        if unit.get("review_status") != "approved" or unit.get("translator") != "Codex internal model":
            tm_mismatches.append(tm_id)
        all_occurrence_ids.update(str(value) for value in unit.get("occurrence_ids", []))
    final_tm_hash = sha256_file(TM)
    check(
        "final_tm_contains_all_131_corrections",
        not tm_mismatches
        and str(report.get("outputs", {}).get("final_translation_memory_sha256", "")).upper() == final_tm_hash,
        final_tm_sha256=final_tm_hash,
        mismatch_tm_ids=tm_mismatches,
    )

    reviewed_mismatches = []
    for row in corrections:
        batch = str(row.get("batch"))
        path = W / f"translation/reviewed/{batch}.jsonl"
        matches = []
        if path.is_file():
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                if line.strip():
                    value = json.loads(line)
                    if str(value.get("tm_id")) == str(row.get("tm_id")):
                        matches.append(value)
        if len(matches) != 1 or str(matches[0].get("translation_ko", "")) != str(row.get("after", "")):
            reviewed_mismatches.append(str(row.get("tm_id")))
    check("reviewed_batches_match_final_corrections", not reviewed_mismatches, mismatches=reviewed_mismatches)

    staged_review = dict(manifest.get("addressee_scene_voice_review", {}))
    check(
        "staging_bound_to_correction_report_and_tm",
        str(manifest.get("inputs", {}).get("translation_memory", {}).get("sha256", "")).upper() == final_tm_hash
        and str(staged_review.get("correction_report_sha256", "")).upper() == sha256_file(REPORT)
        and str(staged_review.get("final_translation_memory_sha256", "")).upper() == final_tm_hash
        and staged_review.get("valid") is True,
        staging_manifest_sha256=sha256_file(STAGING_MANIFEST),
    )

    occurrence_rows: dict[str, dict[str, Any]] = {}
    duplicate_occurrences = []
    for line in OCCURRENCE_MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        occurrence_id = str(row.get("occurrence_id"))
        if occurrence_id in occurrence_rows:
            duplicate_occurrences.append(occurrence_id)
        occurrence_rows[occurrence_id] = row
    manifest_occurrence_hash = sha256_file(OCCURRENCE_MANIFEST)
    check(
        "occurrence_manifest_hash_and_uniqueness",
        not duplicate_occurrences
        and str(manifest.get("static_validation", {}).get("occurrence_manifest_sha256", "")).upper()
        == manifest_occurrence_hash,
        occurrence_manifest_sha256=manifest_occurrence_hash,
        duplicates=duplicate_occurrences[:20],
    )

    encoder = load_module("arf_addressee_encoder", ENCODER)
    builder = load_module("arf_addressee_builder", BUILDER)
    bscr = load_module("arf_addressee_bscr", BSCR_TOOL)
    lz10 = load_module("arf_addressee_lz10", LZ10_TOOL)

    expected_raw_by_tm: dict[str, bytes] = {}
    for tm_id, row in correction_by_id.items():
        expected_raw_by_tm[tm_id] = builder.encode_translation(str(row["after"]), codebook, encoder)
    occurrence_binding_errors = []
    for occurrence_id in sorted(all_occurrence_ids):
        row = occurrence_rows.get(occurrence_id)
        if row is None:
            occurrence_binding_errors.append({"occurrence_id": occurrence_id, "code": "missing"})
            continue
        tm_id = str(row.get("tm_id"))
        expected = expected_raw_by_tm.get(tm_id)
        if expected is None:
            occurrence_binding_errors.append({"occurrence_id": occurrence_id, "code": "wrong_tm", "tm_id": tm_id})
            continue
        if str(row.get("target_raw_sha256", "")).upper() != sha256_bytes(expected) or int(row.get("target_byte_length", -1)) != len(expected):
            occurrence_binding_errors.append({"occurrence_id": occurrence_id, "code": "target_hash_or_length"})
    check(
        "all_corrected_occurrences_bound_to_encoded_targets",
        not occurrence_binding_errors,
        corrected_occurrences=len(all_occurrence_ids),
        errors=occurrence_binding_errors[:30],
    )

    catalog_by_id = {str(row.get("id")): row for row in catalog.get("records", [])}
    grouped: dict[str, list[tuple[str, dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    non_bscr = []
    for occurrence_id in sorted(all_occurrence_ids):
        record = catalog_by_id.get(occurrence_id)
        app = occurrence_rows.get(occurrence_id)
        if record is None or app is None or record.get("extraction_mode") != "bscr_string_pool":
            non_bscr.append(occurrence_id)
            continue
        grouped[str(record["logical_locator"])].append((occurrence_id, record, app))
    check("all_corrected_occurrences_are_scene_bscr", not non_bscr, non_bscr_occurrences=non_bscr)

    staged_rows = {
        str(row.get("physical_path")): row
        for row in manifest.get("static_validation", {}).get("staged_files", [])
        if isinstance(row, dict)
    }
    physical_errors = []
    extracted_errors = []
    verified_occurrences = 0
    verified_files: set[str] = set()
    for logical_locator, rows in sorted(grouped.items()):
        physical_path = str(rows[0][1]["physical_path"])
        source_path = SOURCE_FILES / Path(physical_path)
        staged_path = STAGED_FILES / Path(physical_path)
        staged_row = staged_rows.get(physical_path)
        if (
            not source_path.is_file()
            or not staged_path.is_file()
            or staged_row is None
            or sha256_file(staged_path) != str(staged_row.get("output_sha256", "")).upper()
        ):
            physical_errors.append(physical_path)
            continue
        verified_files.add(physical_path)
        entry_path = builder.entry_path_from_locator(physical_path, logical_locator)
        source_leaf, _ = builder.extract_leaf(source_path.read_bytes(), physical_path, entry_path, lz10)
        staged_leaf, _ = builder.extract_leaf(staged_path.read_bytes(), physical_path, entry_path, lz10)
        source_bscr = bscr.parse_bscr(source_leaf)
        staged_bscr = bscr.parse_bscr(staged_leaf)
        source_index_by_relative = {
            item.relative_offset: index for index, item in enumerate(source_bscr.strings)
        }
        if len(source_bscr.strings) != len(staged_bscr.strings):
            extracted_errors.append({"locator": logical_locator, "code": "string_count"})
            continue
        for occurrence_id, record, app in rows:
            relative = int(record["offset"]) - int(source_bscr.pool_start)
            index = source_index_by_relative.get(relative)
            tm_id = str(app["tm_id"])
            expected = expected_raw_by_tm[tm_id]
            if index is None or staged_bscr.strings[index].raw != expected:
                extracted_errors.append({
                    "occurrence_id": occurrence_id,
                    "locator": logical_locator,
                    "code": "final_staged_raw_mismatch",
                })
            else:
                verified_occurrences += 1
    check(
        "final_staged_containers_embed_every_corrected_occurrence",
        not physical_errors and not extracted_errors and verified_occurrences == len(all_occurrence_ids),
        verified_occurrences=verified_occurrences,
        expected_occurrences=len(all_occurrence_ids),
        verified_physical_files=len(verified_files),
        physical_errors=physical_errors,
        extraction_errors=extracted_errors[:30],
    )

    return write_report(checks, errors, len(corrections), len(all_occurrence_ids), len(verified_files))


def write_report(
    checks: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    corrected_tm_ids: int,
    corrected_occurrences: int,
    verified_physical_files: int,
) -> int:
    report = {
        "schema": "arf-addressee-scene-voice-release-validation-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "scope": {
            "corrected_unique_tm_ids": corrected_tm_ids,
            "corrected_catalog_occurrences": corrected_occurrences,
            "verified_final_physical_files": verified_physical_files,
        },
        "checks": checks,
        "passed_count": sum(bool(row["passed"]) for row in checks),
        "failed_count": sum(not bool(row["passed"]) for row in checks),
        "error_count": len(errors),
        "errors": errors,
        "valid": not errors,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "valid": report["valid"],
        "checks": len(checks),
        "corrected_tm_ids": corrected_tm_ids,
        "corrected_occurrences": corrected_occurrences,
        "verified_physical_files": verified_physical_files,
        "error_count": len(errors),
        "report": str(OUTPUT),
        "report_sha256": sha256_file(OUTPUT),
    }, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
