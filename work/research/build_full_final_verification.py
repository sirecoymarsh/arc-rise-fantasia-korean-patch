#!/usr/bin/env python3
"""Build the whole-project final static verification report for RPJJ99 Korean.

This verifier performs no translation and calls no network service.  It binds
the reviewed translation/font/system/image evidence to the final Riivolution
staging tree by exact identifier sets, exact relative-path sets, sizes, and
SHA-256 digests.  The optional release package is a separate lane: when it has
not been built yet, static runtime staging may still pass while release remains
PENDING.  A Dolphin runtime report can be supplied separately; if absent it is
reported as NOT_SUPPLIED and does not weaken or block the static/release result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work"
GAME_ID = "RPJJ99"
TRANSLATION_POLICY = "Codex internal models only"
REVIEW_POLICY_LABELS = {
    TRANSLATION_POLICY,
    "Codex internal model only",
    "Codex 내부 모델 전용",
}
SOURCE_RVZ_SHA256 = (
    "4671E3E74EB664E441FA927FF6BE9FC06B7D4860782BC4CECCF7DBBB4108AAC5"
)
SOURCE_RVZ_SIZE = 3_589_772_720

EXPECTED_TM_UNITS = 29_777
EXPECTED_OCCURRENCES = 84_761
EXPECTED_REVIEW_BATCHES = 149
EXPECTED_TEXT_PHYSICAL = 612
EXPECTED_IMAGE_TARGETS = 44
EXPECTED_IMAGE_PHYSICAL = 43
EXPECTED_SUPPLEMENTAL_PHYSICAL = 28
EXPECTED_MAIN_DOL_MEMORY_PATCHES = 926
EXPECTED_FINAL_MEMORY_PATCHES = 941
EXPECTED_OVERLAY_PHYSICAL = 684
EXPECTED_RELEASE_OVERLAY_FILES = 685  # 684 game replacements + Riivolution XML
EXPECTED_BSCR_LEAVES = 606
EXPECTED_BSCR_OCCURRENCES = 79_076
EXPECTED_TABLE_LEAVES = 15
EXPECTED_TABLE_OCCURRENCES = 449
EXPECTED_SYSTEM_TM_UNITS = 4_343
EXPECTED_SYSTEM_FIELDS = 5_236
EXPECTED_LOCAL_CONTAINERS = 608
EXPECTED_LOCAL_PHYSICAL = 609
EXPECTED_FONT_PAGES = 9
EXPECTED_FONT_ENCODED_UNITS = 30_703
EXPECTED_INSTALLER_FIXTURE_CHECKS = {
    "pristine_install",
    "installed_hash_verification",
    "byte_exact_restore",
    "restored_target_has_no_added_files",
    "tampered_payload_rejected_before_target_write",
}
DEFAULT_DOLPHIN_RUNTIME_REPORT = WORK / "validation/dolphin_runtime_validation.json"
DOLPHIN_RUNTIME_SCHEMA = "arf-ko-dolphin-runtime-validation-v1"

EXPECTED_SURFACE_OCCURRENCES = {
    "system_database": 5_236,
    "battle_text": 389,
    "misc_text": 60,
    "event_script": 4_786,
    "map_dialogue": 74_290,
}
EXPECTED_PRIMARY_SURFACES = {
    "system_database": 4_343,
    "battle_text": 172,
    "misc_text": 60,
    "event_script": 4_259,
    "map_dialogue": 20_943,
}
EXPECTED_APPLICATION_KINDS = {
    "bscr_variable_pool": EXPECTED_BSCR_OCCURRENCES,
    "non_system_fixed_table": EXPECTED_TABLE_OCCURRENCES,
    "verified_system_application_proof": EXPECTED_SYSTEM_FIELDS,
}

SYSTEM_CONTAINER_TABLES = (
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
SYSTEM_DIRECT_TABLES = ("help.bin", "monster_book.bin")
SYSTEM_TABLES = SYSTEM_CONTAINER_TABLES + SYSTEM_DIRECT_TABLES
EXPECTED_SYSTEM_CATALOGS = {f"{Path(name).stem}.json" for name in SYSTEM_TABLES}
SYSTEM_FONTS = tuple(f"EUC28-{page}.wtm" for page in range(EXPECTED_FONT_PAGES))
EXPECTED_FINAL_INVARIANTS = {
    "internal_model_only",
    "original_rvz_unchanged",
    "review_chain_149_batches_29777_units",
    "heuristic_warnings_148_classified_unwaived_zero",
    "batch_0149_has_177_units",
    "canonical_boundary_720_tm_727_fields_zero_ambiguity",
    "translation_memory_29777_units_84761_occurrences_100_percent",
    "append_only_codebook_1369_characters_zero_collisions",
    "font_pages_9_zero_encoding_errors",
    "system_tables_13_payloads_5236_fields_zero_errors",
}

# Frozen final-QA anchors.  These are deliberately independent of mutable
# staging manifests so a self-consistent but stale/replaced evidence chain is
# rejected before runtime packaging.
FINAL_ANCHOR_HASHES = {
    "work/final_text_font_integration_report.json": "44BDD1661CDF103CB3C0C0FA30E6A2BE2DC83D6A4F458359EE947CF869439962",
    "work/translation/final/translation_memory_draft.json": "CF46C82FBD9A201938B5001985015FBE4D3147E718BE1101253BF9D0DC3775B1",
    "work/translation/final_validation/review_chain.json": "1CD0B00CBBC0C6F04F7B63AABDEB5B6533C27FF68A36F42AE0D847B7936634F2",
    "work/translation/final_validation/heuristic_warning_waivers.json": "0BEBDFADE1C1AF8112760881466326C522F1B19851C80317DFC521550E2AC4D1",
    "work/translation/final_validation/heuristic_warning_waiver_verification.json": "AE4DF0D66171FDC0912ACECCDDBF38C8458225B8486E546EDCFE5872D1C81785",
    "work/translation/boundary_audit/canonical_system_boundary_audit.json": "F1D312C5F70CECA06AF3B070B39A21ECD364F391ED52E6D999FFAE88DDBAED77",
    "work/final_system_table_application/application_proof.json": "D8136357A8FF902462E4A16AF9F171E7DBFF01B8E1968CBB698D3C32C1A4A6D1",
    "work/font/final_v2/codebook.json": "620EA1A432EF411DF6D394371B415F637322B55B333ACE5562A44A7A134331EF",
    "work/font/final_v2/injection_verification.json": "449AF99168784CCC70BE50FF43C77D5CEA3CC4AF5978C59287ECE4662EA5D435",
    "work/font/final_v2/fit_preflight.json": "3E7B375E57FAC40B0C8300802EDFCA1109CF6DE6208EE174B211B9C968B10C3D",
    "work/image_ui_final/reinsertion_manifest.json": "C4D18E426A267D3F0D3C7EF65CB3BBEEC4DF109A7040D184685F6EE724974665",
    "work/image_ui_final/reports/structural_validation.json": "667E2AA9865CFB635A3F6F3A48FF22BFA5393278FFB904ACDEB226BAF309E8AB",
}

ENTRY_TOKEN_RE = re.compile(r"::(\d{4}):")
HEX64_RE = re.compile(r"^[0-9A-Fa-f]{64}$")
BATCH_RE = re.compile(r"^batch_(\d{4})$")


_SHA_CACHE: dict[tuple[str, int, int], str] = {}


def sha256_file(path: Path) -> str:
    stat = path.stat()
    key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns)
    cached = _SHA_CACHE.get(key)
    if cached is not None:
        return cached
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    value = digest.hexdigest().upper()
    _SHA_CACHE[key] = value
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_json(path: Path) -> dict[str, Any]:
    # PowerShell 5.1 fixture reports are UTF-8 with BOM; utf-8-sig is also
    # byte-for-byte compatible with ordinary UTF-8 JSON inputs.
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row is not an object: {path}:{line_number}")
            rows.append(value)
    return rows


def project_path(value: str | os.PathLike[str]) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def staging_path(staging_root: Path, value: str | os.PathLike[str]) -> Path:
    path = Path(value)
    return path if path.is_absolute() else staging_root / path


def rel_posix(path: Path, base: Path) -> str:
    return path.resolve().relative_to(base.resolve()).as_posix()


def actual_file_set(root: Path) -> set[str]:
    if not root.is_dir():
        return set()
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


def canonical_disc_path(value: str) -> bool:
    if not value or "\\" in value:
        return False
    pure = PurePosixPath(value)
    return (
        not pure.is_absolute()
        and pure.as_posix() == value
        and all(part not in {"", ".", ".."} for part in pure.parts)
    )


def tree_digest(paths: Iterable[Path], base: Path) -> str:
    digest = hashlib.sha256()
    rows = sorted(
        ((rel_posix(path, base), sha256_file(path)) for path in paths),
        key=lambda item: item[0].casefold(),
    )
    for relative, file_hash in rows:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest().upper()


def sample(values: Iterable[Any], limit: int = 30) -> list[Any]:
    ordered = sorted(values, key=lambda item: str(item).casefold())
    return ordered[:limit]


@dataclass
class Lane:
    name: str
    errors: list[dict[str, Any]] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def fail(self, code: str, **details: Any) -> None:
        self.errors.append({"code": code, **details})

    def require(self, condition: bool, code: str, **details: Any) -> bool:
        if not condition:
            self.fail(code, **details)
            return False
        return True

    def exact_set(
        self,
        actual: Iterable[Any],
        expected: Iterable[Any],
        code: str,
    ) -> bool:
        actual_set = set(actual)
        expected_set = set(expected)
        if actual_set != expected_set:
            missing = expected_set - actual_set
            unexpected = actual_set - expected_set
            self.fail(
                code,
                actual_count=len(actual_set),
                expected_count=len(expected_set),
                missing_count=len(missing),
                unexpected_count=len(unexpected),
                missing=sample(missing),
                unexpected=sample(unexpected),
            )
            return False
        return True

    def result(self) -> dict[str, Any]:
        return {
            "status": "PASS" if not self.errors else "FAIL",
            "valid": not self.errors,
            "error_count": len(self.errors),
            "errors": self.errors,
            "evidence": self.evidence,
        }


def run_lane(name: str, function, context: dict[str, Any]) -> Lane:
    lane = Lane(name)
    try:
        function(lane, context)
    except Exception as exc:  # keep the final report writable on malformed input
        lane.fail(
            "unhandled_verification_exception",
            error_type=type(exc).__name__,
            error=str(exc),
        )
    return lane


def validate_hash(path: Path, expected: str) -> bool:
    return path.is_file() and HEX64_RE.fullmatch(str(expected)) is not None and sha256_file(path) == str(expected).upper()


def require_final_anchor(lane: Lane, path: Path, code: str) -> None:
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    expected = FINAL_ANCHOR_HASHES.get(relative)
    lane.require(
        expected is not None and validate_hash(path, expected),
        code,
        path=relative,
        expected_sha256=expected,
        actual_sha256=sha256_file(path) if path.is_file() else None,
    )


def iter_artifact_records(value: Any, location: str = "$") -> Iterator[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        if {"path", "size_bytes", "sha256"}.issubset(value):
            yield location, value
        for key, child in value.items():
            yield from iter_artifact_records(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_artifact_records(child, f"{location}[{index}]")


def verify_text_translation(lane: Lane, context: dict[str, Any]) -> None:
    report_path = WORK / "final_text_font_integration_report.json"
    contract_path = WORK / "project/language_contract.json"
    batch_manifest_path = WORK / "translation/tm_v2/batch_manifest.json"
    review_chain_path = WORK / "translation/final_validation/review_chain.json"
    tm_path = WORK / "translation/final/translation_memory_draft.json"
    coverage_path = WORK / "translation/final/coverage.json"
    catalog_path = WORK / "catalog/text_v2/text_catalog.json"
    physical_hashes_path = WORK / "catalog/text_v2/physical_source_hashes.json"
    source_root = WORK / "disc_extracted/DATA/files"

    required = (
        report_path,
        contract_path,
        batch_manifest_path,
        review_chain_path,
        tm_path,
        coverage_path,
        catalog_path,
        physical_hashes_path,
    )
    missing = [str(path) for path in required if not path.is_file()]
    lane.require(not missing, "missing_text_translation_inputs", files=missing)
    if missing:
        return

    report = read_json(report_path)
    contract = read_json(contract_path)
    batch_manifest = read_json(batch_manifest_path)
    review_chain = read_json(review_chain_path)
    memory = read_json(tm_path)
    coverage = read_json(coverage_path)
    catalog = read_json(catalog_path)
    physical_hashes = read_json(physical_hashes_path)
    canonical_boundary_path = WORK / "translation/boundary_audit/canonical_system_boundary_audit.json"
    canonical_boundary = read_json(canonical_boundary_path)

    for anchored in (
        report_path,
        tm_path,
        review_chain_path,
        canonical_boundary_path,
    ):
        require_final_anchor(lane, anchored, "final_text_translation_anchor_hash")

    lane.require(report.get("schema") == "arf-final-text-font-integration-report-v2", "text_report_schema")
    lane.require(report.get("game_id") == GAME_ID, "text_report_game_id")
    lane.require(report.get("translation_engine_policy") == TRANSLATION_POLICY, "text_report_policy")
    lane.require(report.get("external_translation_models_or_apis_used") is False, "text_report_external_model_flag")
    lane.require(report.get("valid") is True and int(report.get("error_count", -1)) == 0, "text_report_invalid")
    invariants = report.get("final_invariants", {})
    lane.exact_set(invariants, EXPECTED_FINAL_INVARIANTS, "text_report_invariant_key_set")
    lane.require(all(invariants.get(key) is True for key in EXPECTED_FINAL_INVARIANTS), "text_report_invariant_false")
    boundary_summary = dict(canonical_boundary.get("summary", {}))
    boundary_scope = dict(canonical_boundary.get("scope", {}))
    lane.require(int(boundary_scope.get("audited_tm_units", -1)) == 720, "canonical_boundary_tm_scope")
    lane.require(int(boundary_scope.get("linked_table_units", -1)) == 727, "canonical_boundary_field_scope")
    lane.require(int(boundary_summary.get("resolved_tm_units", -1)) == 720, "canonical_boundary_tm_resolved")
    lane.require(int(boundary_summary.get("linked_table_units", -1)) == 727, "canonical_boundary_fields_resolved")
    lane.require(int(boundary_summary.get("ambiguous_tm_units", -1)) == 0, "canonical_boundary_ambiguous")
    lane.require(int(boundary_summary.get("unmatched_tm_units", -1)) == 0, "canonical_boundary_unmatched")
    lane.require(boundary_scope.get("reviewed_state_verified") is True, "canonical_boundary_review_state")
    lane.require(canonical_boundary.get("translation_engine_policy") == TRANSLATION_POLICY, "canonical_boundary_policy")
    lane.require(canonical_boundary.get("external_translation_models_or_apis_used") is False, "canonical_boundary_external_flag")
    components = list(canonical_boundary.get("components", []))
    component_paths: set[str] = set()
    component_hash_errors: list[str] = []
    for component in components:
        relative = str(component.get("path", "")).replace("\\", "/")
        if relative in component_paths:
            component_hash_errors.append(relative + ":duplicate")
            continue
        component_paths.add(relative)
        path = project_path(relative)
        if not validate_hash(path, str(component.get("sha256", ""))):
            component_hash_errors.append(relative + ":hash")
    lane.require(len(components) == 8 and len(component_paths) == 8, "canonical_boundary_component_set")
    lane.require(not component_hash_errors, "canonical_boundary_component_hashes", mismatches=component_hash_errors)
    lane.require(sum(int(row.get("audited_tm_units", 0)) for row in components) == 720, "canonical_boundary_component_tm_sum")
    lane.require(sum(int(row.get("linked_table_units", 0)) for row in components) == 727, "canonical_boundary_component_field_sum")
    lane.require(len(set(boundary_scope.get("reviewed_batches", []))) == 22, "canonical_boundary_reviewed_batch_set")

    translation_policy = contract.get("translation_policy", {})
    lane.require(translation_policy.get("codex_internal_models_only") is True, "language_contract_internal_only")
    prohibited = set(translation_policy.get("prohibited", []))
    lane.require(
        {"external translation APIs", "external generative AI models"}.issubset(prohibited),
        "language_contract_external_not_prohibited",
    )

    artifact_errors: list[dict[str, Any]] = []
    artifact_expectations: dict[str, tuple[int, str]] = {}
    for location, artifact in iter_artifact_records(report):
        value = str(artifact.get("path", ""))
        path = project_path(value)
        expected_size = int(artifact.get("size_bytes", -1))
        expected_hash = str(artifact.get("sha256", "")).upper()
        key = str(path.resolve())
        prior = artifact_expectations.get(key)
        if prior is not None and prior != (expected_size, expected_hash):
            artifact_errors.append({"location": location, "path": value, "reason": "conflicting_reference"})
            continue
        artifact_expectations[key] = (expected_size, expected_hash)
        if not path.is_file():
            artifact_errors.append({"location": location, "path": value, "reason": "missing"})
        elif path.stat().st_size != expected_size or sha256_file(path) != expected_hash:
            artifact_errors.append({"location": location, "path": value, "reason": "size_or_hash"})
    lane.require(
        not artifact_errors,
        "text_report_artifact_hashes",
        mismatch_count=len(artifact_errors),
        mismatches=artifact_errors[:30],
    )

    expected_batches = {f"batch_{index:04d}" for index in range(1, EXPECTED_REVIEW_BATCHES + 1)}
    manifest_rows = list(batch_manifest.get("batches", []))
    manifest_names = {f"batch_{int(row.get('batch', -1)):04d}" for row in manifest_rows}
    lane.require(int(batch_manifest.get("batch_count", -1)) == EXPECTED_REVIEW_BATCHES, "batch_manifest_count")
    lane.require(int(batch_manifest.get("unit_count", -1)) == EXPECTED_TM_UNITS, "batch_manifest_units")
    lane.exact_set(manifest_names, expected_batches, "batch_manifest_exact_set")
    manifest_units = {f"batch_{int(row['batch']):04d}": int(row.get("unit_count", -1)) for row in manifest_rows}
    lane.require(sum(manifest_units.values()) == EXPECTED_TM_UNITS, "batch_manifest_unit_sum")
    lane.require(
        all(manifest_units.get(name) == (177 if name == "batch_0149" else 200) for name in expected_batches),
        "batch_manifest_batch_sizes",
    )
    lane.require(
        all(row.get("translator_policy") == TRANSLATION_POLICY for row in manifest_rows),
        "batch_manifest_policy",
    )

    chain_rows = list(review_chain.get("batches", []))
    chain_by_name = {str(row.get("batch")): row for row in chain_rows}
    lane.require(len(chain_by_name) == len(chain_rows), "review_chain_duplicate_batch")
    lane.exact_set(chain_by_name, expected_batches, "review_chain_exact_set")
    lane.require(int(review_chain.get("batch_count", -1)) == EXPECTED_REVIEW_BATCHES, "review_chain_count")
    lane.require(int(review_chain.get("reviewed_units", -1)) == EXPECTED_TM_UNITS, "review_chain_units")
    lane.require(review_chain.get("valid") is True and int(review_chain.get("error_count", -1)) == 0, "review_chain_invalid")
    lane.require(review_chain.get("all_manifest_batches_supplied") is True, "review_chain_incomplete")
    lane.require(review_chain.get("translation_engine_policy") == TRANSLATION_POLICY, "review_chain_policy")
    lane.require(review_chain.get("external_translation_models_or_apis_used") is False, "review_chain_external_flag")
    lane.require(
        str(review_chain.get("batch_manifest_sha256", "")).upper() == sha256_file(batch_manifest_path),
        "review_chain_manifest_hash",
    )

    drafts_dir = WORK / "translation/drafts"
    reviewed_dir = WORK / "translation/reviewed"
    reviews_dir = WORK / "translation/reviews"
    validations_dir = WORK / "translation/final_validation"
    draft_files = {path.stem: path for path in drafts_dir.glob("batch_[0-9][0-9][0-9][0-9].jsonl")}
    reviewed_files = {path.stem: path for path in reviewed_dir.glob("batch_[0-9][0-9][0-9][0-9].jsonl")}
    review_files = {
        path.name.removesuffix("_review.json"): path
        for path in reviews_dir.glob("batch_[0-9][0-9][0-9][0-9]_review.json")
    }
    validation_files = {
        path.name.removesuffix("_reviewed.json"): path
        for path in validations_dir.glob("batch_[0-9][0-9][0-9][0-9]_reviewed.json")
    }
    lane.exact_set(draft_files, expected_batches, "draft_batch_file_set")
    lane.exact_set(reviewed_files, expected_batches, "reviewed_batch_file_set")
    lane.exact_set(review_files, expected_batches, "review_report_file_set")
    lane.exact_set(validation_files, expected_batches, "review_validation_file_set")

    reviewed_by_tm: dict[str, dict[str, Any]] = {}
    validator_warning_count = 0
    batch_hash_mismatches: list[dict[str, str]] = []
    batch_count_mismatches: list[dict[str, Any]] = []
    for batch in sorted(expected_batches):
        row = chain_by_name.get(batch)
        paths = (
            draft_files.get(batch),
            reviewed_files.get(batch),
            review_files.get(batch),
            validation_files.get(batch),
        )
        if row is None or any(path is None for path in paths):
            continue
        draft_path, reviewed_path, review_path, validation_path = paths
        assert draft_path and reviewed_path and review_path and validation_path
        expected_hashes = {
            "draft_sha256": draft_path,
            "reviewed_sha256": reviewed_path,
            "review_report_sha256": review_path,
            "validation_sha256": validation_path,
        }
        for field_name, path in expected_hashes.items():
            if str(row.get(field_name, "")).upper() != sha256_file(path):
                batch_hash_mismatches.append({"batch": batch, "field": field_name})
        reviewed_rows = read_jsonl(reviewed_path)
        expected_units = manifest_units.get(batch, -1)
        if len(reviewed_rows) != expected_units or int(row.get("units", -1)) != expected_units:
            batch_count_mismatches.append(
                {"batch": batch, "manifest": expected_units, "reviewed": len(reviewed_rows), "chain": row.get("units")}
            )
        for unit in reviewed_rows:
            tm_id = str(unit.get("tm_id", ""))
            if not tm_id or tm_id in reviewed_by_tm:
                lane.fail("duplicate_or_empty_reviewed_tm_id", batch=batch, tm_id=tm_id)
            else:
                reviewed_by_tm[tm_id] = unit
        validation = read_json(validation_path)
        if validation.get("valid") is not True or int(validation.get("error_count", -1)) != 0:
            lane.fail("invalid_batch_validation", batch=batch)
        warnings = list(validation.get("warnings", []))
        validator_warning_count += len(warnings)
        if int(row.get("validator_warnings", -1)) != len(warnings):
            batch_count_mismatches.append(
                {"batch": batch, "chain_warnings": row.get("validator_warnings"), "current_warnings": len(warnings)}
            )
        # Early review batches used two equivalent singular/Korean labels before
        # the chain-level wording was normalized.  All three labels state the
        # same closed, internal-only policy; the chain-level external-service
        # flag and frozen review hashes above remain independently enforced.
        lane.require(row.get("review_policy_label") in REVIEW_POLICY_LABELS, "review_batch_policy", batch=batch)
    lane.require(
        not batch_hash_mismatches,
        "review_chain_batch_hashes",
        mismatch_count=len(batch_hash_mismatches),
        mismatches=batch_hash_mismatches[:30],
    )
    lane.require(
        not batch_count_mismatches,
        "review_chain_batch_counts",
        mismatch_count=len(batch_count_mismatches),
        mismatches=batch_count_mismatches[:30],
    )

    units = list(memory.get("units", []))
    tm_by_id: dict[str, dict[str, Any]] = {}
    occurrence_to_tm: dict[str, str] = {}
    duplicate_occurrences: list[str] = []
    primary_counts: Counter[str] = Counter()
    for unit in units:
        tm_id = str(unit.get("tm_id", ""))
        if not tm_id or tm_id in tm_by_id:
            lane.fail("duplicate_or_empty_final_tm_id", tm_id=tm_id)
            continue
        tm_by_id[tm_id] = unit
        primary_counts[str(unit.get("primary_surface"))] += 1
        lane.require(unit.get("status") == "translated", "tm_status", tm_id=tm_id)
        lane.require(unit.get("review_status") == "approved", "tm_review_status", tm_id=tm_id)
        lane.require(bool(str(unit.get("translation_ko", "")).strip()), "tm_blank_translation", tm_id=tm_id)
        occurrence_ids = [str(value) for value in unit.get("occurrence_ids", [])]
        if len(occurrence_ids) != int(unit.get("occurrence_count", -1)):
            lane.fail("tm_occurrence_count", tm_id=tm_id)
        for occurrence_id in occurrence_ids:
            if occurrence_id in occurrence_to_tm:
                duplicate_occurrences.append(occurrence_id)
            else:
                occurrence_to_tm[occurrence_id] = tm_id
    lane.require(memory.get("game_id") == GAME_ID, "tm_game_id")
    lane.require(memory.get("translation_engine_policy") == TRANSLATION_POLICY, "tm_policy")
    lane.require(len(units) == EXPECTED_TM_UNITS and len(tm_by_id) == EXPECTED_TM_UNITS, "tm_unit_count")
    lane.require(not duplicate_occurrences, "tm_duplicate_occurrences", count=len(duplicate_occurrences), sample=sample(duplicate_occurrences))
    lane.require(len(occurrence_to_tm) == EXPECTED_OCCURRENCES, "tm_occurrence_total", actual=len(occurrence_to_tm))
    lane.require(dict(primary_counts) == EXPECTED_PRIMARY_SURFACES, "tm_primary_surface_counts", actual=dict(primary_counts))
    lane.exact_set(reviewed_by_tm, tm_by_id, "reviewed_tm_exact_set")
    reviewed_mismatches: list[str] = []
    for tm_id in set(reviewed_by_tm) & set(tm_by_id):
        reviewed = reviewed_by_tm[tm_id]
        final = tm_by_id[tm_id]
        if (
            reviewed.get("source_text") != final.get("source_text")
            or reviewed.get("translation_ko") != final.get("translation_ko")
            or reviewed.get("primary_surface") != final.get("primary_surface")
            or int(reviewed.get("occurrence_count", -1)) != int(final.get("occurrence_count", -2))
        ):
            reviewed_mismatches.append(tm_id)
    lane.require(
        not reviewed_mismatches,
        "reviewed_to_final_tm_mismatch",
        mismatch_count=len(reviewed_mismatches),
        sample=sample(reviewed_mismatches),
    )

    records = list(catalog.get("records", []))
    catalog_by_id: dict[str, dict[str, Any]] = {}
    catalog_by_locator: dict[str, list[dict[str, Any]]] = defaultdict(list)
    surface_counts: Counter[str] = Counter()
    text_physical_paths: set[str] = set()
    unsafe_paths: list[str] = []
    for record in records:
        occurrence_id = str(record.get("id", ""))
        if not occurrence_id or occurrence_id in catalog_by_id:
            lane.fail("duplicate_or_empty_catalog_occurrence", occurrence_id=occurrence_id)
            continue
        catalog_by_id[occurrence_id] = record
        catalog_by_locator[str(record.get("logical_locator", ""))].append(record)
        surface_counts[str(record.get("surface"))] += 1
        physical = str(record.get("physical_path", ""))
        if not canonical_disc_path(physical):
            unsafe_paths.append(physical)
        text_physical_paths.add(physical)
    lane.require(catalog.get("game_id") == GAME_ID, "catalog_game_id")
    lane.require(catalog.get("translation_engine_policy") == TRANSLATION_POLICY, "catalog_policy")
    lane.require(len(records) == EXPECTED_OCCURRENCES and len(catalog_by_id) == EXPECTED_OCCURRENCES, "catalog_occurrence_count")
    lane.require(dict(surface_counts) == EXPECTED_SURFACE_OCCURRENCES, "catalog_surface_counts", actual=dict(surface_counts))
    lane.require(not unsafe_paths, "unsafe_catalog_physical_paths", count=len(unsafe_paths), sample=sample(unsafe_paths))
    lane.require(len(text_physical_paths) == EXPECTED_TEXT_PHYSICAL, "text_physical_count", actual=len(text_physical_paths))
    lane.exact_set(catalog_by_id, occurrence_to_tm, "tm_catalog_occurrence_exact_set")

    source_hash_errors: list[dict[str, str]] = []
    for physical in sorted(text_physical_paths, key=str.casefold):
        source = source_root / Path(physical)
        expected_hash = str(physical_hashes.get(physical, "")).upper()
        if not source.is_file():
            source_hash_errors.append({"path": physical, "reason": "missing"})
        elif not HEX64_RE.fullmatch(expected_hash) or sha256_file(source) != expected_hash:
            source_hash_errors.append({"path": physical, "reason": "hash"})
    lane.require(
        not source_hash_errors,
        "text_physical_source_hashes",
        mismatch_count=len(source_hash_errors),
        mismatches=source_hash_errors[:30],
    )

    lane.require(int(coverage.get("total_units", -1)) == EXPECTED_TM_UNITS, "coverage_units")
    lane.require(int(coverage.get("translated_units", -1)) == EXPECTED_TM_UNITS, "coverage_translated")
    lane.require(int(coverage.get("reviewed_units", -1)) == EXPECTED_TM_UNITS, "coverage_reviewed")
    lane.require(int(coverage.get("total_occurrences", -1)) == EXPECTED_OCCURRENCES, "coverage_occurrences")
    lane.require(float(coverage.get("coverage_percent", -1)) == 100.0, "coverage_percent")

    context.update(
        {
            "text_report": report,
            "text_report_path": report_path,
            "batch_manifest": batch_manifest,
            "review_chain": review_chain,
            "review_chain_path": review_chain_path,
            "expected_batches": expected_batches,
            "reviewed_files": reviewed_files,
            "validation_files": validation_files,
            "reviewed_by_tm": reviewed_by_tm,
            "validator_warning_count": validator_warning_count,
            "memory": memory,
            "tm_path": tm_path,
            "tm_by_id": tm_by_id,
            "occurrence_to_tm": occurrence_to_tm,
            "catalog": catalog,
            "catalog_path": catalog_path,
            "catalog_by_id": catalog_by_id,
            "catalog_by_locator": catalog_by_locator,
            "text_physical_paths": text_physical_paths,
            "physical_hashes": physical_hashes,
            "physical_hashes_path": physical_hashes_path,
            "source_root": source_root,
        }
    )
    lane.evidence.update(
        {
            "final_text_font_report": str(report_path.relative_to(ROOT)).replace("\\", "/"),
            "final_text_font_report_sha256": sha256_file(report_path),
            "hash_bound_report_artifacts": len(artifact_expectations),
            "review_batches": len(chain_by_name),
            "reviewed_units": len(reviewed_by_tm),
            "validator_warnings": validator_warning_count,
            "tm_units": len(tm_by_id),
            "catalog_occurrences": len(catalog_by_id),
            "text_physical_sources": len(text_physical_paths),
            "text_source_tree_sha256": tree_digest(
                (source_root / Path(path) for path in text_physical_paths), source_root
            ),
        }
    )


def warning_key(batch: str, tm_id: str, warning: dict[str, Any]) -> tuple[Any, ...]:
    return (
        batch,
        tm_id,
        str(warning.get("code")),
        str(warning.get("characters", "")),
        int(warning.get("source_count", -1)),
        int(warning.get("translation_count", -1)),
    )


def verify_heuristic_waivers(lane: Lane, context: dict[str, Any]) -> None:
    waivers_path = WORK / "translation/final_validation/heuristic_warning_waivers.json"
    application_path = WORK / "translation/final_validation/heuristic_warning_qa_application.json"
    verification_path = WORK / "translation/final_validation/heuristic_warning_waiver_verification.json"
    review_chain_path = WORK / "translation/final_validation/review_chain.json"
    missing = [str(path) for path in (waivers_path, application_path, verification_path, review_chain_path) if not path.is_file()]
    lane.require(not missing, "missing_waiver_inputs", files=missing)
    if missing:
        return
    waivers = read_json(waivers_path)
    application = read_json(application_path)
    verification = read_json(verification_path)
    review_chain = read_json(review_chain_path)
    require_final_anchor(lane, waivers_path, "final_waiver_anchor_hash")
    require_final_anchor(lane, verification_path, "final_waiver_verification_anchor_hash")

    lane.require(waivers.get("translation_engine_policy") == TRANSLATION_POLICY, "waiver_policy")
    lane.require(waivers.get("external_translation_models_or_apis_used") is False, "waiver_external_flag")
    lane.require(waivers.get("valid") is True, "waiver_document_invalid")
    lane.require(application.get("translation_engine_policy") == TRANSLATION_POLICY, "waiver_application_policy")
    lane.require(application.get("external_translation_models_or_apis_used") is False, "waiver_application_external_flag")
    lane.require(application.get("valid") is True, "waiver_application_invalid")
    lane.require(verification.get("translation_engine_policy") == TRANSLATION_POLICY, "waiver_verification_policy")
    lane.require(verification.get("external_translation_models_or_apis_used") is False, "waiver_verification_external_flag")
    lane.require(verification.get("valid") is True and int(verification.get("error_count", -1)) == 0, "waiver_verification_invalid")
    references = {
        "waiver_artifact_sha256": waivers_path,
        "application_artifact_sha256": application_path,
        "review_chain_sha256": review_chain_path,
    }
    hash_mismatches = [field_name for field_name, path in references.items() if str(verification.get(field_name, "")).upper() != sha256_file(path)]
    lane.require(not hash_mismatches, "waiver_verification_reference_hashes", fields=hash_mismatches)

    waiver_rows = list(waivers.get("waivers", []))
    waiver_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in waiver_rows:
        key = warning_key(str(row.get("batch")), str(row.get("tm_id")), dict(row.get("warning", {})))
        if key in waiver_by_key:
            lane.fail("duplicate_waiver_key", key=list(key))
        else:
            waiver_by_key[key] = row

    expected_batches = context.get("expected_batches") or {f"batch_{index:04d}" for index in range(1, 150)}
    validation_files: dict[str, Path] = context.get("validation_files", {})
    reviewed_files: dict[str, Path] = context.get("reviewed_files", {})
    if not validation_files:
        validation_files = {
            path.name.removesuffix("_reviewed.json"): path
            for path in (WORK / "translation/final_validation").glob("batch_[0-9][0-9][0-9][0-9]_reviewed.json")
        }
    if not reviewed_files:
        reviewed_files = {path.stem: path for path in (WORK / "translation/reviewed").glob("batch_[0-9][0-9][0-9][0-9].jsonl")}
    lane.exact_set(validation_files, expected_batches, "waiver_validation_batch_set")
    lane.exact_set(reviewed_files, expected_batches, "waiver_reviewed_batch_set")

    current_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for batch in sorted(expected_batches):
        validation_path = validation_files.get(batch)
        reviewed_path = reviewed_files.get(batch)
        if validation_path is None or reviewed_path is None:
            continue
        validation = read_json(validation_path)
        reviewed = {str(row.get("tm_id")): row for row in read_jsonl(reviewed_path)}
        reviewed_hash = sha256_file(reviewed_path)
        for warning in validation.get("warnings", []):
            tm_id = str(warning.get("tm_id", ""))
            key = warning_key(batch, tm_id, warning)
            if key in current_by_key:
                lane.fail("duplicate_current_warning", key=list(key))
            else:
                current_by_key[key] = {
                    "translation_ko": reviewed.get(tm_id, {}).get("translation_ko"),
                    "reviewed_batch_sha256": reviewed_hash,
                }
    lane.exact_set(current_by_key, waiver_by_key, "waiver_current_warning_exact_set")
    target_mismatches: list[tuple[Any, ...]] = []
    batch_hash_mismatches: list[tuple[Any, ...]] = []
    for key in set(current_by_key) & set(waiver_by_key):
        current = current_by_key[key]
        waiver = waiver_by_key[key]
        if current["translation_ko"] != waiver.get("translation_ko"):
            target_mismatches.append(key)
        if current["reviewed_batch_sha256"] != str(waiver.get("reviewed_batch_sha256", "")).upper():
            batch_hash_mismatches.append(key)
    lane.require(not target_mismatches, "waived_target_mismatch", count=len(target_mismatches), sample=[list(key) for key in sample(target_mismatches)])
    lane.require(not batch_hash_mismatches, "waived_batch_hash_mismatch", count=len(batch_hash_mismatches), sample=[list(key) for key in sample(batch_hash_mismatches)])

    corrected_warning_ids = {
        str(row.get("tm_id"))
        for row in application.get("corrections", [])
        if row.get("warning_code") is not None
    }
    still_present = corrected_warning_ids & {str(key[1]) for key in current_by_key}
    lane.require(not still_present, "corrected_warnings_still_present", count=len(still_present), sample=sample(still_present))
    categories = Counter(str(row.get("category")) for row in waiver_rows)
    expected_categories = {
        "intentional_vocal_lengthening_acting_mark": 62,
        "verified_korean_line_reflow": 24,
        "intentional_middle_dot_delimiter_or_emphasis": 55,
    }
    lane.require(dict(categories) == expected_categories, "waiver_category_counts", actual=dict(categories))
    scalar_expectations = {
        "original_warning_events": 148,
        "corrected_warning_events": 7,
        "remaining_warning_events": 141,
        "waiver_entries": 141,
        "unwaived_warning_events": 0,
        "stale_waiver_entries": 0,
        "waived_target_mismatches": 0,
        "waived_batch_hash_mismatches": 0,
        "corrected_warnings_still_present": 0,
    }
    for field_name, expected in scalar_expectations.items():
        lane.require(int(verification.get(field_name, -1)) == expected, "waiver_verification_count", field=field_name, expected=expected, actual=verification.get(field_name))
    lane.require(len(current_by_key) == 141 and len(waiver_by_key) == 141, "waiver_runtime_counts")
    lane.require(int(application.get("warning_events_corrected", -1)) == 7, "warning_application_corrected")
    lane.require(int(application.get("warning_events_waived", -1)) == 141, "warning_application_waived")
    lane.require(int(application.get("adjacent_contamination_corrections", -1)) == 1, "warning_application_adjacent")
    lane.require(int(application.get("total_target_corrections", -1)) == 8, "warning_application_total")
    lane.require(review_chain.get("valid") is True and int(review_chain.get("reviewed_units", -1)) == EXPECTED_TM_UNITS, "waiver_review_chain_invalid")

    context.update({"waivers": waivers, "waiver_verification": verification})
    lane.evidence.update(
        {
            "waivers_sha256": sha256_file(waivers_path),
            "waiver_verification_sha256": sha256_file(verification_path),
            "initial_warning_events": 148,
            "corrected_warning_events": 7,
            "remaining_warning_events": len(current_by_key),
            "exact_waiver_entries": len(waiver_by_key),
            "unwaived_warning_events": len(set(current_by_key) - set(waiver_by_key)),
            "stale_waiver_entries": len(set(waiver_by_key) - set(current_by_key)),
        }
    )


def verify_system_fonts(lane: Lane, context: dict[str, Any]) -> None:
    proof_path = WORK / "final_system_table_application/application_proof.json"
    codebook_path = WORK / "font/final_v2/codebook.json"
    approved_units_path = WORK / "font/final_v2/approved_units.jsonl"
    supplemental_corpus_path = WORK / "font/final_v2/supplemental_corpus.txt"
    codebook_verification_path = WORK / "font/final_v2/codebook_append_only_verification.json"
    injection_manifest_path = WORK / "font/final_v2/injection_manifest.json"
    injection_verification_path = WORK / "font/final_v2/injection_verification.json"
    fit_path = WORK / "font/final_v2/fit_preflight.json"
    required = (
        proof_path,
        codebook_path,
        approved_units_path,
        supplemental_corpus_path,
        codebook_verification_path,
        injection_manifest_path,
        injection_verification_path,
        fit_path,
    )
    missing = [str(path) for path in required if not path.is_file()]
    lane.require(not missing, "missing_system_font_inputs", files=missing)
    if missing:
        return
    proof = read_json(proof_path)
    codebook = read_json(codebook_path)
    codebook_verification = read_json(codebook_verification_path)
    injection_manifest = read_json(injection_manifest_path)
    injection_verification = read_json(injection_verification_path)
    fit = read_json(fit_path)

    for anchored in (proof_path, codebook_path, injection_verification_path, fit_path):
        require_final_anchor(lane, anchored, "final_system_font_anchor_hash")

    lane.require(proof.get("schema") == "arf-approved-system-table-application-proof-v1", "system_proof_schema")
    lane.require(proof.get("game_id") == GAME_ID, "system_proof_game_id")
    lane.require(proof.get("translation_engine_policy") == TRANSLATION_POLICY, "system_proof_policy")
    lane.require(proof.get("external_translation_models_or_apis_used") is False, "system_proof_external_flag")
    lane.require(proof.get("valid") is True and int(proof.get("verification_error_count", -1)) == 0, "system_proof_invalid")
    expected_counts = {
        "approved_system_tm_units": EXPECTED_SYSTEM_TM_UNITS,
        "applied_unique_tm_units": EXPECTED_SYSTEM_TM_UNITS,
        "replacement_table_fields": EXPECTED_SYSTEM_FIELDS,
        "system_database_scanner_occurrences": EXPECTED_SYSTEM_FIELDS,
        "payloads_rebuilt": len(SYSTEM_TABLES),
        "fixed_payload_changes_outside_declared_slots": 0,
    }
    for field_name, expected in expected_counts.items():
        lane.require(int(proof.get(field_name, -1)) == expected, "system_proof_count", field=field_name, expected=expected, actual=proof.get(field_name))
    lane.require(proof.get("structured_field_coverage_matches_scanner_occurrences") is True, "system_structured_scanner_delta")
    if "tm_path" in context:
        lane.require(str(proof.get("translation_memory_sha256", "")).upper() == sha256_file(context["tm_path"]), "system_proof_tm_hash")
    lane.require(str(proof.get("codebook_sha256", "")).upper() == sha256_file(codebook_path), "system_proof_codebook_hash")
    canonical_boundary_path = WORK / "translation/boundary_audit/canonical_system_boundary_audit.json"
    lane.require(
        str(proof.get("boundary_audit_sha256", "")).upper()
        == sha256_file(canonical_boundary_path),
        "system_proof_boundary_hash",
    )

    payload_dir = WORK / "final_system_table_application/payloads"
    replacement_dir = WORK / "final_system_table_application/replacement_catalogs"
    verification_dir = WORK / "final_system_table_application/verification_catalogs"
    payload_files = {path.name: path for path in payload_dir.glob("*") if path.is_file()}
    replacement_files = {path.name: path for path in replacement_dir.glob("*.json")}
    verification_files = {path.name: path for path in verification_dir.glob("*.json")}
    expected_payloads = set(SYSTEM_TABLES)
    expected_catalogs = {f"{Path(name).stem}.json" for name in SYSTEM_TABLES}
    lane.exact_set(payload_files, expected_payloads, "system_payload_file_set")
    lane.exact_set(replacement_files, expected_catalogs, "system_replacement_catalog_set")
    lane.exact_set(verification_files, expected_catalogs, "system_verification_catalog_set")

    proof_rows = list(proof.get("payloads", []))
    proof_by_payload: dict[str, dict[str, Any]] = {}
    for row in proof_rows:
        output_name = Path(str(row.get("output_path", ""))).name
        if output_name in proof_by_payload:
            lane.fail("duplicate_system_proof_payload", payload=output_name)
        else:
            proof_by_payload[output_name] = row
    lane.exact_set(proof_by_payload, expected_payloads, "system_proof_payload_exact_set")
    payload_hashes: dict[str, str] = {}
    system_hash_errors: list[dict[str, str]] = []
    field_sum = 0
    for name in SYSTEM_TABLES:
        row = proof_by_payload.get(name)
        payload = payload_files.get(name)
        if row is None or payload is None:
            continue
        payload_hash = sha256_file(payload)
        payload_hashes[name] = payload_hash
        catalog_name = str(row.get("catalog", ""))
        source = project_path(str(row.get("source_path", "")))
        replacement = replacement_files.get(catalog_name)
        verification = verification_files.get(catalog_name)
        checks = (
            (payload_hash == str(row.get("output_sha256", "")).upper(), "payload_output_hash"),
            (payload.stat().st_size == int(row.get("output_size", -1)), "payload_output_size"),
            (source.is_file() and sha256_file(source) == str(row.get("source_sha256", "")).upper(), "payload_source_hash"),
            (replacement is not None and sha256_file(replacement) == str(row.get("replacement_catalog_sha256", "")).upper(), "replacement_catalog_hash"),
            (verification is not None and sha256_file(verification) == str(row.get("verification_catalog_sha256", "")).upper(), "verification_catalog_hash"),
            (int(row.get("verification_errors", -1)) == 0, "payload_verification_errors"),
            (int(row.get("changes_outside_declared_slots", -1)) == 0, "payload_outside_slot_changes"),
        )
        for condition, reason in checks:
            if not condition:
                system_hash_errors.append({"payload": name, "reason": reason})
        field_sum += int(row.get("replacement_fields", 0))
    lane.require(not system_hash_errors, "system_payload_hash_or_proof_mismatch", mismatch_count=len(system_hash_errors), mismatches=system_hash_errors[:30])
    lane.require(field_sum == EXPECTED_SYSTEM_FIELDS, "system_payload_field_sum", actual=field_sum)

    lane.require(codebook_verification.get("translation_engine_policy") == TRANSLATION_POLICY, "codebook_policy")
    lane.require(codebook_verification.get("valid") is True and int(codebook_verification.get("error_count", -1)) == 0, "codebook_invalid")
    for field_name, expected in {
        "existing_assigned": 1_368,
        "extended_assigned": 1_369,
        "appended_characters": 1,
        "required_hangul": 504,
        "required_custom_glyphs": 504,
        "existing_assignments_changed": 0,
        "reserved_pair_collisions": 0,
    }.items():
        lane.require(int(codebook_verification.get(field_name, -1)) == expected, "codebook_count", field=field_name, expected=expected, actual=codebook_verification.get(field_name))
    lane.require(str(codebook_verification.get("extended_codebook_sha256", "")).upper() == sha256_file(codebook_path), "codebook_verification_hash")
    lane.require(
        str(codebook_verification.get("corpus_sha256", "")).upper()
        == sha256_file(supplemental_corpus_path),
        "codebook_verification_corpus_hash",
    )
    lane.require(int(codebook.get("assigned", -1)) == 1_369, "codebook_assigned")

    manifest_rows = list(injection_manifest.get("files", []))
    manifest_by_page = {int(row.get("page", -1)): row for row in manifest_rows}
    verification_rows = list(injection_verification.get("pages", []))
    verification_by_page = {int(row.get("page", -1)): row for row in verification_rows}
    expected_pages = set(range(EXPECTED_FONT_PAGES))
    lane.require(len(manifest_by_page) == len(manifest_rows), "font_manifest_duplicate_pages")
    lane.require(len(verification_by_page) == len(verification_rows), "font_verification_duplicate_pages")
    lane.exact_set(manifest_by_page, expected_pages, "font_manifest_page_set")
    lane.exact_set(verification_by_page, expected_pages, "font_verification_page_set")
    injected_dir = WORK / "font/final_v2/injected"
    injected_files = {path.name: path for path in injected_dir.glob("*") if path.is_file()}
    lane.exact_set(injected_files, set(SYSTEM_FONTS), "injected_font_file_set")
    font_hashes: dict[str, str] = {}
    font_errors: list[dict[str, Any]] = []
    for page in sorted(expected_pages):
        manifest_row = manifest_by_page.get(page)
        verification_row = verification_by_page.get(page)
        name = f"EUC28-{page}.wtm"
        output = injected_files.get(name)
        if manifest_row is None or verification_row is None or output is None:
            continue
        source = project_path(str(manifest_row.get("source", "")))
        expected_output = project_path(str(manifest_row.get("output", "")))
        conditions = (
            expected_output.resolve() == output.resolve(),
            source.is_file() and sha256_file(source) == str(manifest_row.get("source_sha256", "")).upper(),
            sha256_file(output) == str(manifest_row.get("output_sha256", "")).upper(),
            manifest_row.get("size_preserved") is True,
            manifest_row.get("header_palette_preserved") is True,
            manifest_row.get("redecode_indices_exact") is True,
            verification_row.get("size_preserved") is True,
            verification_row.get("header_palette_preserved") is True,
            verification_row.get("redecode_reencode_exact") is True,
            verification_row.get("manifest_hashes_match") is True,
            int(verification_row.get("changes_outside_assigned_cells", -1)) == 0,
        )
        if not all(conditions):
            font_errors.append({"page": page})
        font_hashes[name] = sha256_file(output)
    lane.require(not font_errors, "font_page_hash_or_structure", mismatches=font_errors)
    lane.require(injection_verification.get("translation_engine_policy") == TRANSLATION_POLICY, "font_verification_policy")
    lane.require(injection_verification.get("valid") is True and int(injection_verification.get("error_count", -1)) == 0, "font_verification_invalid")
    lane.require(int(injection_verification.get("approved_units_encoded", -1)) == EXPECTED_FONT_ENCODED_UNITS, "font_approved_units")
    lane.require(int(injection_verification.get("approved_unit_encoding_errors", -1)) == 0, "font_encoding_errors")
    lane.require(int(injection_verification.get("assigned_characters", -1)) == 1_369, "font_assigned_characters")
    lane.require(str(injection_verification.get("codebook_sha256", "")).upper() == sha256_file(codebook_path), "font_codebook_hash")
    lane.require(str(injection_verification.get("injection_manifest_sha256", "")).upper() == sha256_file(injection_manifest_path), "font_manifest_hash")
    lane.require(
        str(injection_verification.get("approved_units_sha256", "")).upper()
        == sha256_file(approved_units_path),
        "font_approved_units_hash",
    )

    fit_expectations = {
        "approved_tm_units": EXPECTED_TM_UNITS,
        "matched_unique_tm_units": EXPECTED_SYSTEM_TM_UNITS,
        "matched_table_fields": EXPECTED_SYSTEM_FIELDS,
        "fixed_overflow_count": 0,
        "unmatched_system_tm_count": 0,
        "encoding_error_count": 0,
        "global_encoding_error_count": 0,
    }
    for field_name, expected in fit_expectations.items():
        lane.require(int(fit.get(field_name, -1)) == expected, "fit_preflight_count", field=field_name, expected=expected, actual=fit.get(field_name))
    lane.require(fit.get("safe_for_fixed_table_insertion") is True, "fit_preflight_not_safe")
    if "tm_path" in context:
        lane.require(
            str(fit.get("translation_memory_sha256", "")).upper()
            == sha256_file(context["tm_path"]),
            "fit_preflight_tm_hash",
        )
    lane.require(
        str(fit.get("codebook_sha256", "")).upper() == sha256_file(codebook_path),
        "fit_preflight_codebook_hash",
    )
    lane.require(
        str(fit.get("boundary_audit_sha256", "")).upper()
        == sha256_file(canonical_boundary_path),
        "fit_preflight_boundary_hash",
    )
    fit_catalog_dir = project_path(str(fit.get("catalog_dir", "")))
    fit_catalog_rows = list(fit.get("catalog_artifacts", []))
    fit_catalog_names = {str(row.get("name", "")) for row in fit_catalog_rows}
    lane.exact_set(
        fit_catalog_names,
        EXPECTED_SYSTEM_CATALOGS,
        "fit_preflight_catalog_set",
    )
    fit_catalog_errors: list[str] = []
    for row in fit_catalog_rows:
        name = str(row.get("name", ""))
        path = fit_catalog_dir / name
        if (
            not path.is_file()
            or path.stat().st_size != int(row.get("size_bytes", -1))
            or sha256_file(path) != str(row.get("sha256", "")).upper()
        ):
            fit_catalog_errors.append(name)
    lane.require(
        not fit_catalog_errors,
        "fit_preflight_catalog_hashes",
        mismatches=fit_catalog_errors,
    )

    context.update(
        {
            "system_proof": proof,
            "system_proof_path": proof_path,
            "system_payload_hashes": payload_hashes,
            "font_hashes": font_hashes,
            "codebook_path": codebook_path,
        }
    )
    lane.evidence.update(
        {
            "system_application_proof_sha256": sha256_file(proof_path),
            "system_payloads": len(payload_hashes),
            "system_fields": field_sum,
            "system_payload_tree_sha256": tree_digest(payload_files.values(), payload_dir),
            "font_pages": len(font_hashes),
            "font_tree_sha256": tree_digest(injected_files.values(), injected_dir),
            "codebook_sha256": sha256_file(codebook_path),
            "font_injection_verification_sha256": sha256_file(injection_verification_path),
        }
    )


def verify_image_ui(lane: Lane, context: dict[str, Any]) -> None:
    manifest_path = WORK / "image_ui_final/reinsertion_manifest.json"
    validation_path = WORK / "image_ui_final/reports/structural_validation.json"
    if not manifest_path.is_file() or not validation_path.is_file():
        lane.fail("missing_image_evidence")
        return
    manifest = read_json(manifest_path)
    validation = read_json(validation_path)
    require_final_anchor(lane, manifest_path, "final_image_manifest_anchor_hash")
    require_final_anchor(lane, validation_path, "final_image_validation_anchor_hash")
    image_root = manifest_path.parent
    source_root: Path = context.get("source_root", WORK / "disc_extracted/DATA/files")
    text_paths: set[str] = set(context.get("text_physical_paths", set()))

    lane.require(manifest.get("schema") == "arf-image-ui-reinsertion-manifest-v1", "image_manifest_schema")
    lane.require(manifest.get("original_rvz_modified") is False, "image_manifest_source_modified")
    targets = list(manifest.get("targets", []))
    lane.require(len(targets) == EXPECTED_IMAGE_TARGETS, "image_target_count", actual=len(targets))
    lane.require(int(manifest.get("replacement_target_count", -1)) == EXPECTED_IMAGE_TARGETS, "image_manifest_declared_count")
    declared_validation = project_path(str(manifest.get("validation", "")))
    lane.require(declared_validation.resolve() == validation_path.resolve(), "image_validation_path")
    lane.require(validation.get("schema") == "arf-image-ui-structural-validation-v1", "image_validation_schema")
    lane.require(int(validation.get("asset_checks", -1)) == 48, "image_asset_checks")
    lane.require(int(validation.get("passed", -1)) == 48 and int(validation.get("failed", -1)) == 0, "image_structural_counts")
    lane.require(not validation.get("failures"), "image_structural_failures")
    checks = list(validation.get("checks", []))
    lane.require(len(checks) == 48 and all(row.get("pass") is True for row in checks), "image_check_exact_pass_set")
    title_check = dict(validation.get("title_archive_check", {}))
    lane.require(title_check.get("pass") is True, "image_title_archive_check")

    declared_payload_hashes = {
        str(relative).replace("\\", "/"): str(value).upper()
        for relative, value in dict(manifest.get("payload_tree_sha256", {})).items()
    }
    payload_hash_errors: list[dict[str, str]] = []
    for relative, expected_hash in sorted(declared_payload_hashes.items()):
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts or not relative.startswith("payloads/"):
            payload_hash_errors.append({"path": relative, "reason": "unsafe"})
            continue
        path = image_root / Path(relative)
        if not validate_hash(path, expected_hash):
            payload_hash_errors.append({"path": relative, "reason": "missing_or_hash"})
    lane.require(not payload_hash_errors, "image_declared_payload_hashes", mismatch_count=len(payload_hash_errors), mismatches=payload_hash_errors[:30])

    checks_by_patched: dict[Path, dict[str, Any]] = {}
    structural_errors: list[dict[str, str]] = []
    for row in checks:
        original = project_path(str(row.get("original", ""))).resolve()
        patched = project_path(str(row.get("patched", ""))).resolve()
        if patched in checks_by_patched:
            structural_errors.append({"path": str(patched), "reason": "duplicate_patched_check"})
        checks_by_patched[patched] = row
        if not original.is_file() or sha256_file(original) != str(row.get("original_sha256", "")).upper():
            structural_errors.append({"path": str(original), "reason": "original_hash"})
        if not patched.is_file() or sha256_file(patched) != str(row.get("patched_sha256", "")).upper():
            structural_errors.append({"path": str(patched), "reason": "patched_hash"})
        # Raw WTM checks record ``*_bytes`` while the CXD/WTMD checks record
        # ``*_compressed_bytes``.  Both forms bind the exact physical payload
        # size in the frozen structural report.
        original_size = row.get("original_bytes", row.get("original_compressed_bytes", -1))
        patched_size = row.get("patched_bytes", row.get("patched_compressed_bytes", -1))
        if original.is_file() and original.stat().st_size != int(original_size):
            structural_errors.append({"path": str(original), "reason": "original_size"})
        if patched.is_file() and patched.stat().st_size != int(patched_size):
            structural_errors.append({"path": str(patched), "reason": "patched_size"})
    lane.require(not structural_errors, "image_structural_hashes", mismatch_count=len(structural_errors), mismatches=structural_errors[:30])

    target_names: set[str] = set()
    direct: dict[str, Path] = {}
    original_hashes: dict[str, str] = {}
    system_leaf: Path | None = None
    target_errors: list[dict[str, str]] = []
    for target in targets:
        name = str(target.get("target", ""))
        if not name or name in target_names:
            target_errors.append({"target": name, "reason": "duplicate_or_empty"})
            continue
        target_names.add(name)
        payload = project_path(str(target.get("payload", ""))).resolve()
        if not payload.is_file() or not payload.is_relative_to(image_root.resolve()):
            target_errors.append({"target": name, "reason": "missing_or_escaped_payload"})
            continue
        relative = payload.relative_to(image_root.resolve()).as_posix()
        if declared_payload_hashes.get(relative) != sha256_file(payload):
            target_errors.append({"target": name, "reason": "unbound_payload_hash"})
        if name == "Sys/system.vol::entry 53 nowloading.wtm":
            if system_leaf is not None:
                target_errors.append({"target": name, "reason": "duplicate_system_leaf"})
            system_leaf = payload
            check = checks_by_patched.get(payload)
            if check is None:
                target_errors.append({"target": name, "reason": "missing_structural_check"})
            continue
        if not canonical_disc_path(name) or "::" in name:
            target_errors.append({"target": name, "reason": "unsafe_physical_path"})
            continue
        direct[name] = payload
        source = source_root / Path(name)
        if name in {"Title/title.vol", "Sys/title.vol"}:
            expected_original = str(title_check.get("original_sha256", "")).upper()
            expected_patched = str(title_check.get("patched_sha256", "")).upper()
        else:
            check = checks_by_patched.get(payload)
            if check is None:
                target_errors.append({"target": name, "reason": "missing_structural_check"})
                continue
            expected_original = str(check.get("original_sha256", "")).upper()
            expected_patched = str(check.get("patched_sha256", "")).upper()
        original_hashes[name] = expected_original
        if not source.is_file() or sha256_file(source) != expected_original:
            target_errors.append({"target": name, "reason": "source_hash"})
        if sha256_file(payload) != expected_patched:
            target_errors.append({"target": name, "reason": "payload_hash"})
    lane.require(not target_errors, "image_target_proofs", mismatch_count=len(target_errors), mismatches=target_errors[:30])
    lane.require(len(direct) == EXPECTED_IMAGE_PHYSICAL, "image_direct_count", actual=len(direct))
    lane.require(system_leaf is not None, "image_nowloading_missing")
    if system_leaf is not None:
        try:
            source_entries = parse_rtdp(source_root / "Sys/system.vol")
            source_entry = source_entries.get("nowloading.wtm")
            structural_row = checks_by_patched.get(system_leaf)
            lane.require(
                source_entry is not None
                and source_entry[0] == 53
                and structural_row is not None
                and sha256_bytes(source_entry[1])
                == str(structural_row.get("original_sha256", "")).upper(),
                "image_nowloading_source_leaf_hash",
            )
        except Exception as exc:
            lane.fail(
                "image_nowloading_source_parse",
                error_type=type(exc).__name__,
                error=str(exc),
            )
    if text_paths:
        collisions = {name for name in direct if name.casefold() in {value.casefold() for value in text_paths}}
        lane.require(not collisions, "image_text_physical_collision", paths=sample(collisions))
        union = text_paths | set(direct)
        lane.require(len(union) == EXPECTED_OVERLAY_PHYSICAL, "image_text_union_count", actual=len(union))

    context.update(
        {
            "image_manifest": manifest,
            "image_manifest_path": manifest_path,
            "image_validation": validation,
            "image_validation_path": validation_path,
            "image_direct": direct,
            "image_original_hashes": original_hashes,
            "image_system_leaf": system_leaf,
            "overlay_allowlist": text_paths | set(direct),
        }
    )
    target_payloads = [path for path in direct.values()]
    if system_leaf is not None:
        target_payloads.append(system_leaf)
    lane.evidence.update(
        {
            "reinsertion_manifest_sha256": sha256_file(manifest_path),
            "structural_validation_sha256": sha256_file(validation_path),
            "structural_checks_passed": int(validation.get("passed", -1)),
            "reinsertion_targets": len(target_names),
            "direct_physical_targets": len(direct),
            "cumulative_system_targets": int(system_leaf is not None),
            "target_payload_tree_sha256": tree_digest(target_payloads, image_root),
        }
    )


def verify_immutable_source(lane: Lane, context: dict[str, Any]) -> None:
    report = context.get("text_report")
    if not isinstance(report, dict):
        report_path = WORK / "final_text_font_integration_report.json"
        if not report_path.is_file():
            lane.fail("missing_text_report_for_rvz")
            return
        report = read_json(report_path)
    rvz = dict(report.get("immutable_source_rvz", {}))
    rvz_path = Path(str(rvz.get("path", "")))
    lane.require(rvz_path.is_file(), "source_rvz_missing", path=str(rvz_path))
    if not rvz_path.is_file():
        return
    current_hash = sha256_file(rvz_path)
    current_size = rvz_path.stat().st_size
    lane.require(current_hash == SOURCE_RVZ_SHA256, "source_rvz_hash", actual=current_hash)
    lane.require(current_size == SOURCE_RVZ_SIZE, "source_rvz_size", actual=current_size)
    lane.require(str(rvz.get("baseline_sha256", "")).upper() == SOURCE_RVZ_SHA256, "text_report_rvz_baseline")
    lane.require(str(rvz.get("current_sha256", "")).upper() == current_hash, "text_report_rvz_current")
    lane.require(int(rvz.get("size_bytes", -1)) == current_size, "text_report_rvz_size")
    lane.require(rvz.get("hash_matches_immutable_baseline") is True, "text_report_rvz_match_flag")
    lane.require(rvz.get("modified") is False and int(rvz.get("write_operations_performed_by_this_stage", -1)) == 0, "text_report_rvz_write_flag")
    context["source_rvz_path"] = rvz_path
    lane.evidence.update(
        {
            "path": str(rvz_path),
            "size_bytes": current_size,
            "sha256": current_hash,
            "modified": False,
        }
    )


def parse_rtdp(path: Path) -> dict[str, tuple[int, bytes]]:
    data = path.read_bytes()
    if len(data) < 0x20 or data[:4] != b"RTDP":
        raise ValueError(f"RTDP header missing: {path}")
    eoh = int.from_bytes(data[4:8], "big")
    count = int.from_bytes(data[8:12], "big")
    if not (0x20 + count * 40 <= eoh <= len(data)):
        raise ValueError(f"invalid RTDP table: {path}")
    result: dict[str, tuple[int, bytes]] = {}
    for index in range(count):
        pos = 0x20 + index * 40
        name = data[pos : pos + 32].split(b"\0", 1)[0].decode("latin1")
        size = int.from_bytes(data[pos + 32 : pos + 36], "big")
        relative = int.from_bytes(data[pos + 36 : pos + 40], "big")
        start = eoh + relative
        end = start + size
        if not (start <= end <= len(data)):
            raise ValueError(f"RTDP entry out of range: {path}:{index}")
        if name in result:
            raise ValueError(f"duplicate RTDP name: {path}:{name}")
        result[name] = (index, bytes(value ^ 0x55 for value in data[start:end]))
    return result


def audit_list(report: dict[str, Any]) -> list[dict[str, Any]]:
    value = report.get("editAudit")
    if value is None and isinstance(report.get("rtdpTree"), dict):
        value = report["rtdpTree"].get("editAudit")
    return list(value or [])


def verify_runtime_supplement(lane: Lane, context: dict[str, Any]) -> None:
    runtime = WORK / "runtime_fix"
    staging_manifest_path = WORK / "final_runtime_staging/staging_manifest.json"
    paths = {
        "integration": runtime / "runtime_supplement_integration.json",
        "main_translations": runtime / "main_dol_translations.jsonl",
        "main_crossreview": runtime / "main_dol_crossreview.json",
        "main_patch_report": runtime / "main_dol_patch_report_v2.json",
        "hbm": runtime / "hbm_ko/hbm_korean_payload_manifest.json",
        "endroll": runtime / "endroll_ui/manifest.json",
        "endroll_verification": runtime / "endroll_ui/verification_summary.json",
        "opening": runtime / "opening_bnr_ko/opening_bnr_korean_payload_manifest.json",
        "sfd": runtime / "sfd_ko/sfd_final_validation.json",
        "sfd_replacement": runtime / "sfd_ko/sfd_video_replacement_report.json",
        "visual": runtime / "visual_sweep/final_visual_surface_audit.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    lane.require(not missing, "supplemental_artifacts_missing", artifacts=missing)
    lane.require(staging_manifest_path.is_file(), "supplemental_staging_manifest_missing")
    if missing or not staging_manifest_path.is_file():
        return
    docs = {name: read_json(path) for name, path in paths.items() if path.suffix == ".json"}
    integration = docs["integration"]
    crossreview = docs["main_crossreview"]
    patch_report = docs["main_patch_report"]
    hbm = docs["hbm"]
    endroll = docs["endroll"]
    endroll_verification = docs["endroll_verification"]
    opening = docs["opening"]
    sfd = docs["sfd"]
    sfd_replacement = docs["sfd_replacement"]
    visual = docs["visual"]

    lane.require(integration.get("schema") == "arf-runtime-supplement-integration-v1" and integration.get("valid") is True,
                 "supplemental_integration_invalid")
    lane.require(int(integration.get("base_physical_count", -1)) == 655, "supplemental_base_count")
    lane.require(int(integration.get("supplemental_physical_count", -1)) == EXPECTED_SUPPLEMENTAL_PHYSICAL,
                 "supplemental_physical_count")
    lane.require(int(integration.get("final_physical_count", -1)) == EXPECTED_OVERLAY_PHYSICAL,
                 "supplemental_final_count")
    lane.require(int(integration.get("memory_patch_count", -1)) == EXPECTED_MAIN_DOL_MEMORY_PATCHES,
                 "supplemental_memory_count")
    lane.require(integration.get("main_dol_staged_physically") is False, "main_dol_physical_staging_forbidden")
    lane.require(str(integration.get("staging_manifest_sha256", "")).upper() == sha256_file(staging_manifest_path),
                 "supplemental_staging_manifest_hash")

    translations = read_jsonl(paths["main_translations"])
    lane.require(len(translations) == EXPECTED_MAIN_DOL_MEMORY_PATCHES, "main_dol_translation_count")
    lane.require(crossreview.get("valid") is True and crossreview.get("verdict") == "PASS", "main_dol_crossreview_invalid")
    lane.require(int(crossreview.get("result", {}).get("reviewed_rows", -1)) == EXPECTED_MAIN_DOL_MEMORY_PATCHES,
                 "main_dol_crossreview_count")
    lane.require(str(crossreview.get("result", {}).get("translations_sha256", "")).upper() == sha256_file(paths["main_translations"]),
                 "main_dol_crossreview_translation_hash")
    lane.require(patch_report.get("valid") is True, "main_dol_patch_report_invalid")
    lane.require(int(patch_report.get("summary", {}).get("patch_rows", -1)) == EXPECTED_MAIN_DOL_MEMORY_PATCHES,
                 "main_dol_patch_report_count")
    lane.require(str(patch_report.get("source", {}).get("sha256", "")).upper() == "4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC",
                 "main_dol_source_hash")
    lane.require(str(patch_report.get("inputs", {}).get("translations_jsonl", {}).get("sha256", "")).upper() == sha256_file(paths["main_translations"]),
                 "main_dol_patch_translation_hash")
    lane.require(str(patch_report.get("inputs", {}).get("codebook", {}).get("sha256", "")).upper() == sha256_file(WORK / "font/final_v2/codebook.json"),
                 "main_dol_patch_codebook_hash")

    lane.require(hbm.get("static_validation", {}).get("valid") is True and int(hbm.get("physical_payload_count", -1)) == 3,
                 "hbm_supplement_invalid")
    lane.require(int(endroll.get("file_count", -1)) == 23, "endroll_manifest_count")
    lane.require(endroll_verification.get("valid") is True and int(endroll_verification.get("checked_file_count", -1)) == 23,
                 "endroll_verification_invalid")
    lane.require(str(endroll.get("payload_aggregate_sha256", "")).upper() == str(endroll_verification.get("payload_aggregate_sha256", "")).upper(),
                 "endroll_aggregate_hash")
    lane.require(opening.get("valid") is True and opening.get("static_validation", {}).get("valid") is True,
                 "opening_bnr_invalid")
    lane.require(sfd.get("valid") is True and sfd.get("visual_evidence", {}).get("manual_verdict") == "PASS",
                 "opening_sfd_invalid")
    lane.require(sfd.get("decoded_audio_framemd5", {}).get("byte_exact") is True,
                 "opening_sfd_audio_not_exact")
    lane.require(sfd_replacement.get("valid") is True and sfd_replacement.get("audio_pes_packets_byte_exact") is True,
                 "opening_sfd_container_invalid")
    lane.require(visual.get("valid") is True and visual.get("manual_visual_review_complete") is True,
                 "visual_surface_audit_invalid")
    lane.require(int(visual.get("remaining_japanese_user_visible_visual_surfaces", -1)) == 0,
                 "visual_japanese_residue")

    supplemental_rows = list(integration.get("physical_files", []))
    supplemental_by_path = {str(row.get("physical_path", "")): row for row in supplemental_rows}
    expected_paths = {
        "Hbm/home.csv", "Hbm/home_nosave.csv", "Hbm/homeBtn.arc",
        "opening.bnr", "Movie/RAY_OP_02.sfd",
        *(f"Event/endroll/EV09_18_0200C_{index:02d}.wtm" for index in range(23)),
    }
    lane.require(len(supplemental_by_path) == len(supplemental_rows), "supplemental_duplicate_paths")
    lane.exact_set(supplemental_by_path, expected_paths, "supplemental_physical_exact_set")
    source_root: Path = context.get("source_root", WORK / "disc_extracted/DATA/files")
    supplemental_hash_errors: list[str] = []
    supplemental_original_hashes: dict[str, str] = {}
    supplemental_resize: dict[str, bool] = {}
    for physical in expected_paths:
        row = supplemental_by_path.get(physical, {})
        source = source_root / Path(physical)
        if not source.is_file():
            supplemental_hash_errors.append(physical + ":source_missing")
            continue
        source_hash = sha256_file(source)
        supplemental_original_hashes[physical] = source_hash
        supplemental_resize[physical] = bool(row.get("resize"))
        if (
            str(row.get("source_sha256", "")).upper() != source_hash
            or int(row.get("source_size", -1)) != source.stat().st_size
            or not HEX64_RE.fullmatch(str(row.get("output_sha256", "")))
            or str(row.get("output_sha256", "")).upper() == source_hash
        ):
            supplemental_hash_errors.append(physical + ":hash_or_size")
    lane.require(not supplemental_hash_errors, "supplemental_source_payload_hashes",
                 mismatch_count=len(supplemental_hash_errors), mismatches=supplemental_hash_errors[:30])

    context.update({
        "supplemental_paths": expected_paths,
        "supplemental_rows": supplemental_by_path,
        "supplemental_original_hashes": supplemental_original_hashes,
        "supplemental_resize": supplemental_resize,
    })
    lane.evidence.update({
        "supplemental_physical_files": len(expected_paths),
        "main_dol_memory_patches": EXPECTED_MAIN_DOL_MEMORY_PATCHES,
        "main_dol_translations_sha256": sha256_file(paths["main_translations"]),
        "visual_surface_audit_sha256": sha256_file(paths["visual"]),
        "opening_sfd_validation_sha256": sha256_file(paths["sfd"]),
    })


def verify_runtime_staging(lane: Lane, context: dict[str, Any]) -> None:
    staging_root = WORK / "final_runtime_staging"
    manifest_path = staging_root / "staging_manifest.json"
    failure_path = staging_root / "BUILD_FAILED.json"
    lane.require(not failure_path.exists(), "staging_build_failure_sentinel", path=str(failure_path))
    lane.require(manifest_path.is_file(), "staging_manifest_missing", path=str(manifest_path))
    if not manifest_path.is_file():
        return
    manifest = read_json(manifest_path)
    static = dict(manifest.get("static_validation", {}))
    text_paths: set[str] = set(context.get("text_physical_paths", set()))
    image_direct: dict[str, Path] = dict(context.get("image_direct", {}))
    supplemental_paths: set[str] = set(context.get("supplemental_paths", set()))
    overlay_allowlist = text_paths | set(image_direct) | supplemental_paths
    source_root: Path = context.get("source_root", WORK / "disc_extracted/DATA/files")
    catalog_by_id: dict[str, dict[str, Any]] = context.get("catalog_by_id", {})
    occurrence_to_tm: dict[str, str] = context.get("occurrence_to_tm", {})
    catalog_by_locator: dict[str, list[dict[str, Any]]] = context.get("catalog_by_locator", {})
    physical_hashes: dict[str, Any] = context.get("physical_hashes", {})

    lane.require(manifest.get("schema") == "arf-full-runtime-staging-v2", "staging_manifest_schema")
    lane.require(manifest.get("game_id") == GAME_ID, "staging_game_id")
    lane.require(manifest.get("translation_engine_policy") == TRANSLATION_POLICY, "staging_policy")
    lane.require(manifest.get("external_translation_services_used") == [], "staging_external_services")
    lane.require(manifest.get("external_translation_models_or_apis_used") == [], "staging_external_models")
    lane.require(manifest.get("source_rvz_modified") is False, "staging_source_modified")
    lane.require(manifest.get("runtime_ready_release") is False, "staging_runtime_release_flag")
    lane.require(manifest.get("dolphin_screen_test") == "pending", "staging_dolphin_status")
    lane.require(static.get("valid") is True and int(static.get("error_count", -1)) == 0 and not static.get("errors"), "staging_embedded_validation_invalid")
    lane.require(len(text_paths) == EXPECTED_TEXT_PHYSICAL, "staging_dependency_text_set", actual=len(text_paths))
    lane.require(len(image_direct) == EXPECTED_IMAGE_PHYSICAL, "staging_dependency_image_set", actual=len(image_direct))
    lane.require(len(supplemental_paths) == EXPECTED_SUPPLEMENTAL_PHYSICAL, "staging_dependency_supplemental_set", actual=len(supplemental_paths))
    lane.require(len(overlay_allowlist) == EXPECTED_OVERLAY_PHYSICAL, "overlay_allowlist_count", actual=len(overlay_allowlist))
    lane.require(len({path.casefold() for path in overlay_allowlist}) == len(overlay_allowlist), "overlay_case_collision")

    inputs = dict(manifest.get("inputs", {}))
    expected_inputs = {
        "translation_memory": context.get("tm_path"),
        "text_catalog": context.get("catalog_path"),
        "codebook": context.get("codebook_path"),
        "system_application_proof": context.get("system_proof_path"),
        "image_reinsertion_manifest": context.get("image_manifest_path"),
        "image_structural_validation": context.get("image_validation_path"),
    }
    input_errors: list[str] = []
    for key, expected_path in expected_inputs.items():
        record = inputs.get(key)
        if expected_path is None or not isinstance(record, dict):
            input_errors.append(key + ":missing")
            continue
        declared_path = Path(str(record.get("path", "")))
        if declared_path.resolve() != Path(expected_path).resolve() or str(record.get("sha256", "")).upper() != sha256_file(Path(expected_path)):
            input_errors.append(key + ":path_or_hash")
    lane.require(not input_errors, "staging_input_hashes", mismatches=input_errors)
    declared_source_root = Path(str(inputs.get("source_files_root", "")))
    lane.require(declared_source_root.resolve() == source_root.resolve(), "staging_source_root")

    counts = dict(manifest.get("counts", {}))
    expected_counts = {
        "tm_units": EXPECTED_TM_UNITS,
        "catalog_occurrences": EXPECTED_OCCURRENCES,
        "bscr_leaves": EXPECTED_BSCR_LEAVES,
        "bscr_occurrences": EXPECTED_BSCR_OCCURRENCES,
        "non_system_table_payloads": EXPECTED_TABLE_LEAVES,
        "non_system_table_occurrences": EXPECTED_TABLE_OCCURRENCES,
        "system_occurrences": EXPECTED_SYSTEM_FIELDS,
        "local_containers_rebuilt": EXPECTED_LOCAL_CONTAINERS,
        "image_reinsertion_targets": EXPECTED_IMAGE_TARGETS,
        "image_direct_physical_files": EXPECTED_IMAGE_PHYSICAL,
        "image_cumulative_system_members": 1,
        "supplemental_physical_files": EXPECTED_SUPPLEMENTAL_PHYSICAL,
        "staged_physical_files": EXPECTED_OVERLAY_PHYSICAL,
        "riivolution_file_rules": EXPECTED_OVERLAY_PHYSICAL,
        "riivolution_memory_rules": EXPECTED_FINAL_MEMORY_PATCHES,
    }
    for field_name, expected in expected_counts.items():
        lane.require(int(counts.get(field_name, -1)) == expected, "staging_manifest_count", field=field_name, expected=expected, actual=counts.get(field_name))

    patch_root_relative = str(manifest.get("riivolution", {}).get("patch_root", ""))
    patch_root = staging_path(staging_root, patch_root_relative)
    actual_overlay = actual_file_set(patch_root)
    lane.exact_set(actual_overlay, overlay_allowlist, "overlay_physical_exact_set")
    overlay_unexpected = actual_overlay - overlay_allowlist
    overlay_missing = overlay_allowlist - actual_overlay

    staged_rows = list(static.get("staged_files", []))
    staged_by_path: dict[str, dict[str, Any]] = {}
    for row in staged_rows:
        physical = str(row.get("physical_path", ""))
        if physical in staged_by_path:
            lane.fail("duplicate_staged_manifest_path", path=physical)
        else:
            staged_by_path[physical] = row
    lane.exact_set(staged_by_path, overlay_allowlist, "staged_file_manifest_exact_set")
    lane.require(int(static.get("staged_file_count", -1)) == EXPECTED_OVERLAY_PHYSICAL, "embedded_staged_file_count")
    staged_hash_errors: list[dict[str, str]] = []
    for physical in sorted(overlay_allowlist, key=str.casefold):
        row = staged_by_path.get(physical)
        source = source_root / Path(physical)
        output = patch_root / Path(physical)
        if row is None or not source.is_file() or not output.is_file():
            staged_hash_errors.append({"path": physical, "reason": "missing"})
            continue
        if physical in text_paths:
            expected_source = str(physical_hashes.get(physical, "")).upper()
        elif physical in image_direct:
            expected_source = str(context.get("image_original_hashes", {}).get(physical, "")).upper()
        else:
            expected_source = str(context.get("supplemental_original_hashes", {}).get(physical, "")).upper()
        source_hash = sha256_file(source)
        output_hash = sha256_file(output)
        conditions = (
            source_hash == expected_source,
            str(row.get("source_sha256", "")).upper() == source_hash,
            str(row.get("output_sha256", "")).upper() == output_hash,
            int(row.get("source_size", -1)) == source.stat().st_size,
            int(row.get("output_size", -1)) == output.stat().st_size,
            source_hash != output_hash,
        )
        if not all(conditions):
            staged_hash_errors.append({"path": physical, "reason": "source_output_hash_or_size"})
    lane.require(not staged_hash_errors, "staged_physical_hashes", mismatch_count=len(staged_hash_errors), mismatches=staged_hash_errors[:30])

    riivolution = dict(manifest.get("riivolution", {}))
    xml_path = staging_path(staging_root, str(riivolution.get("xml", "")))
    xml_errors: list[str] = []
    xml_rules: dict[str, dict[str, str]] = {}
    xml_memory: dict[str, str] = {}
    if not xml_path.is_file():
        xml_errors.append("missing")
    else:
        if sha256_file(xml_path) != str(riivolution.get("sha256", "")).upper():
            xml_errors.append("hash")
        parsed = ET.parse(xml_path).getroot()
        if parsed.tag != "wiidisc":
            xml_errors.append("root")
        patch_nodes = parsed.findall("./patch")
        if len(patch_nodes) != 1 or patch_nodes[0].attrib.get("root") != "/arc_rise_fantasia_ko_full/files":
            xml_errors.append("patch_root")
        for node in parsed.findall("./patch/file"):
            physical = node.attrib.get("disc", "").removeprefix("/")
            if physical in xml_rules:
                xml_errors.append("duplicate:" + physical)
            xml_rules[physical] = dict(node.attrib)
        for node in parsed.findall("./patch/memory"):
            offset = str(node.attrib.get("offset", ""))
            if offset in xml_memory:
                xml_errors.append("duplicate_memory:" + offset)
            xml_memory[offset] = str(node.attrib.get("value", "")).upper()
        if set(xml_rules) != overlay_allowlist:
            xml_errors.append("target_set")
        for physical, attrs in xml_rules.items():
            if physical in supplemental_paths:
                expected_resize = "true" if context.get("supplemental_resize", {}).get(physical) else "false"
            else:
                expected_resize = "true" if (patch_root / Path(physical)).stat().st_size != (source_root / Path(physical)).stat().st_size else "false"
            if attrs.get("external") != physical or attrs.get("resize") != expected_resize:
                xml_errors.append("attributes:" + physical)
        supplemental = dict(manifest.get("supplemental_runtime_patch", {}))
        memory_rows = list(supplemental.get("memory_patches", []))
        expected_memory = {str(row.get("memory_address_hex", "")): str(row.get("value", "")).upper() for row in memory_rows}
        if len(expected_memory) != len(memory_rows) or len(memory_rows) != EXPECTED_FINAL_MEMORY_PATCHES:
            xml_errors.append("memory_manifest_count")
        if xml_memory != expected_memory:
            xml_errors.append("memory_exact_set_or_value")
        if supplemental.get("main_dol_staged_physically") is not False:
            xml_errors.append("main_dol_physical_flag")
    lane.require(not xml_errors, "riivolution_xml", mismatch_count=len(xml_errors), mismatches=xml_errors[:30])
    lane.require(int(riivolution.get("file_count", -1)) == EXPECTED_OVERLAY_PHYSICAL, "riivolution_declared_count")
    lane.require(int(riivolution.get("memory_count", -1)) == EXPECTED_FINAL_MEMORY_PATCHES, "riivolution_declared_memory_count")

    occurrence_manifest_path = staging_path(staging_root, str(static.get("occurrence_manifest", "")))
    leaf_manifest_path = staging_path(staging_root, str(static.get("leaf_manifest", "")))
    lane.require(validate_hash(occurrence_manifest_path, str(static.get("occurrence_manifest_sha256", ""))), "occurrence_manifest_hash")
    lane.require(validate_hash(leaf_manifest_path, str(static.get("leaf_manifest_sha256", ""))), "leaf_manifest_hash")
    occurrence_rows = read_jsonl(occurrence_manifest_path) if occurrence_manifest_path.is_file() else []
    occurrence_application: dict[str, dict[str, Any]] = {}
    duplicate_application_ids: list[str] = []
    kind_counts: Counter[str] = Counter()
    occurrence_mismatches: list[str] = []
    for row in occurrence_rows:
        occurrence_id = str(row.get("occurrence_id", ""))
        if occurrence_id in occurrence_application:
            duplicate_application_ids.append(occurrence_id)
            continue
        occurrence_application[occurrence_id] = row
        kind_counts[str(row.get("application_kind"))] += 1
        catalog_record = catalog_by_id.get(occurrence_id)
        if catalog_record is None:
            continue
        expected_raw_hash = sha256_bytes(bytes.fromhex(str(catalog_record.get("raw_hex", ""))))
        if (
            str(row.get("tm_id", "")) != occurrence_to_tm.get(occurrence_id)
            or row.get("physical_path") != catalog_record.get("physical_path")
            or row.get("logical_locator") != catalog_record.get("logical_locator")
            or row.get("leaf_name") != catalog_record.get("leaf_name")
            or int(row.get("catalog_offset", -1)) != int(catalog_record.get("offset", -2))
            or str(row.get("source_raw_sha256", "")).upper() != expected_raw_hash
        ):
            occurrence_mismatches.append(occurrence_id)
    lane.require(not duplicate_application_ids, "duplicate_occurrence_application", count=len(duplicate_application_ids), sample=sample(duplicate_application_ids))
    lane.exact_set(occurrence_application, catalog_by_id, "occurrence_application_exact_set")
    lane.require(dict(kind_counts) == EXPECTED_APPLICATION_KINDS, "occurrence_application_kind_counts", actual=dict(kind_counts))
    lane.require(not occurrence_mismatches, "occurrence_application_mapping", mismatch_count=len(occurrence_mismatches), sample=sample(occurrence_mismatches))

    leaf_manifest = read_json(leaf_manifest_path) if leaf_manifest_path.is_file() else {}
    lane.require(leaf_manifest.get("schema") == "arf-full-leaf-build-manifest-v1", "leaf_manifest_schema")
    leaves = list(leaf_manifest.get("leaves", []))
    lane.require(int(leaf_manifest.get("leaf_count", -1)) == len(leaves) == EXPECTED_BSCR_LEAVES + EXPECTED_TABLE_LEAVES, "leaf_manifest_count", actual=len(leaves))
    leaf_by_locator: dict[str, dict[str, Any]] = {}
    output_paths: set[str] = set()
    replacement_paths: set[str] = set()
    bscr_report_paths: set[str] = set()
    table_report_paths: set[str] = set()
    table_verification_paths: set[str] = set()
    expected_application_files: set[str] = set()
    leaf_hash_errors: list[dict[str, str]] = []
    replacement_occurrence_ids: set[str] = set()
    replacement_duplicates: list[str] = []
    kind_leaf_counts: Counter[str] = Counter()
    kind_occurrence_counts: Counter[str] = Counter()
    nested_by_physical: dict[str, list[dict[str, Any]]] = defaultdict(list)
    direct_leaves: list[dict[str, Any]] = []
    for leaf in leaves:
        locator = str(leaf.get("logical_locator", ""))
        physical = str(leaf.get("physical_path", ""))
        kind = str(leaf.get("kind", ""))
        if locator in leaf_by_locator:
            lane.fail("duplicate_leaf_locator", locator=locator)
            continue
        leaf_by_locator[locator] = leaf
        kind_leaf_counts[kind] += 1
        kind_occurrence_counts[kind] += int(leaf.get("occurrence_count", 0))
        output_relative = str(leaf.get("output", "")).replace("\\", "/")
        replacement_relative = str(leaf.get("replacement_manifest", "")).replace("\\", "/")
        output_paths.add(output_relative)
        replacement_paths.add(replacement_relative)
        expected_application_files.update({output_relative, replacement_relative})
        output_path = staging_path(staging_root, output_relative)
        replacement_path = staging_path(staging_root, replacement_relative)
        expected_entry_path = tuple(int(value) for value in ENTRY_TOKEN_RE.findall(locator))
        actual_entry_path = tuple(int(value) for value in leaf.get("entry_path", []))
        if expected_entry_path != actual_entry_path:
            leaf_hash_errors.append({"locator": locator, "reason": "entry_path"})
        if actual_entry_path:
            nested_by_physical[physical].append(leaf)
        else:
            direct_leaves.append(leaf)
        if (
            not output_path.is_file()
            or sha256_file(output_path) != str(leaf.get("output_sha256", "")).upper()
            or output_path.stat().st_size != int(leaf.get("output_size", -1))
            or not replacement_path.is_file()
            or str(leaf.get("source_sha256", "")).upper() == str(leaf.get("output_sha256", "")).upper()
        ):
            leaf_hash_errors.append({"locator": locator, "reason": "output_or_report_hash"})
            continue
        expected_record_ids = {str(row.get("id")) for row in catalog_by_locator.get(locator, [])}
        if len(expected_record_ids) != int(leaf.get("occurrence_count", -1)):
            leaf_hash_errors.append({"locator": locator, "reason": "catalog_occurrence_count"})
        report = read_json(replacement_path)
        if kind == "bscr":
            bscr_report_paths.add(replacement_relative)
            rows = list(report.get("replacements", []))
            report_ids = {str(row.get("occurrence_id", "")) for row in rows}
            if (
                report.get("format") != "arf-bscr-replacements-v1"
                or report.get("logical_locator") != locator
                or str(report.get("source_bscr_sha256", "")).upper() != str(leaf.get("source_sha256", "")).upper()
                or str(report.get("output_bscr_sha256", "")).upper() != str(leaf.get("output_sha256", "")).upper()
                or len(report_ids) != len(rows)
                or report_ids != expected_record_ids
            ):
                leaf_hash_errors.append({"locator": locator, "reason": "bscr_report"})
            for row in rows:
                occurrence_id = str(row.get("occurrence_id", ""))
                application_row = occurrence_application.get(occurrence_id, {})
                if (
                    str(row.get("tm_id", "")) != str(application_row.get("tm_id", ""))
                    or sha256_bytes(bytes.fromhex(str(row.get("source_raw_hex", "")))) != str(application_row.get("source_raw_sha256", "")).upper()
                    or sha256_bytes(bytes.fromhex(str(row.get("raw_hex", "")))) != str(application_row.get("target_raw_sha256", "")).upper()
                ):
                    leaf_hash_errors.append({"locator": locator, "reason": "bscr_occurrence_row"})
        elif kind == "table":
            table_report_paths.add(replacement_relative)
            verification_relative = replacement_relative.replace("/table_replacements/", "/table_verification/")
            table_verification_paths.add(verification_relative)
            expected_application_files.add(verification_relative)
            verification_path = staging_path(staging_root, verification_relative)
            mappings = list(report.get("application_mapping", []))
            report_ids = {str(row.get("occurrence_id", "")) for row in mappings}
            units_by_id = {str(row.get("id")): row for row in report.get("units", [])}
            verified = read_json(verification_path) if verification_path.is_file() else {}
            verified_by_id = {str(row.get("id")): row for row in verified.get("units", [])}
            if (
                str(report.get("source_sha256", "")).upper() != str(leaf.get("source_sha256", "")).upper()
                or str(report.get("output_sha256", "")).upper() != str(leaf.get("output_sha256", "")).upper()
                or not verification_path.is_file()
                or str(verified.get("source_sha256", "")).upper() != str(leaf.get("output_sha256", "")).upper()
                or len(report_ids) != len(mappings)
                or report_ids != expected_record_ids
            ):
                leaf_hash_errors.append({"locator": locator, "reason": "table_report"})
            for mapping in mappings:
                occurrence_id = str(mapping.get("occurrence_id", ""))
                unit_id = str(mapping.get("table_unit_id", ""))
                application_row = occurrence_application.get(occurrence_id, {})
                replacement_unit = units_by_id.get(unit_id, {})
                verified_unit = verified_by_id.get(unit_id, {})
                if (
                    str(mapping.get("tm_id", "")) != str(application_row.get("tm_id", ""))
                    or str(mapping.get("replacement_hex", "")).upper() != str(replacement_unit.get("replacement_hex", "")).upper()
                    or str(mapping.get("replacement_hex", "")).upper() != str(verified_unit.get("raw_hex", "")).upper()
                    or sha256_bytes(bytes.fromhex(str(mapping.get("replacement_hex", ""))))
                    != str(application_row.get("target_raw_sha256", "")).upper()
                    or unit_id != str(application_row.get("table_unit_id", ""))
                ):
                    leaf_hash_errors.append({"locator": locator, "reason": "table_occurrence_row"})
        else:
            leaf_hash_errors.append({"locator": locator, "reason": "unknown_kind"})
            report_ids = set()
        for occurrence_id in report_ids:
            if occurrence_id in replacement_occurrence_ids:
                replacement_duplicates.append(occurrence_id)
            replacement_occurrence_ids.add(occurrence_id)
    lane.require(not leaf_hash_errors, "individual_leaf_reports", mismatch_count=len(leaf_hash_errors), mismatches=leaf_hash_errors[:30])
    lane.require(not replacement_duplicates, "duplicate_leaf_replacement_occurrence", count=len(replacement_duplicates), sample=sample(replacement_duplicates))
    lane.require(kind_leaf_counts == Counter({"bscr": EXPECTED_BSCR_LEAVES, "table": EXPECTED_TABLE_LEAVES}), "leaf_kind_counts", actual=dict(kind_leaf_counts))
    lane.require(kind_occurrence_counts == Counter({"bscr": EXPECTED_BSCR_OCCURRENCES, "table": EXPECTED_TABLE_OCCURRENCES}), "leaf_occurrence_counts", actual=dict(kind_occurrence_counts))
    lane.require(len(output_paths) == len(leaves) and len(replacement_paths) == len(leaves), "leaf_output_or_report_path_duplicates")
    lane.require(len(direct_leaves) == 1 and str(direct_leaves[0].get("physical_path")) == "Btl/btl_tutorial.vld", "direct_leaf_exact_set")
    lane.require(len(nested_by_physical) == EXPECTED_LOCAL_CONTAINERS, "nested_container_count", actual=len(nested_by_physical))
    system_occurrence_ids = {occurrence_id for occurrence_id, row in occurrence_application.items() if row.get("application_kind") == "verified_system_application_proof"}
    lane.exact_set(replacement_occurrence_ids | system_occurrence_ids, occurrence_application, "leaf_plus_system_occurrence_exact_set")

    actual_bscr_reports = {
        rel_posix(path, staging_root)
        for path in (staging_root / "application/bscr_replacements").rglob("*.json")
    }
    actual_table_reports = {
        rel_posix(path, staging_root)
        for path in (staging_root / "application/table_replacements").rglob("*.json")
    }
    actual_table_verification = {
        rel_posix(path, staging_root)
        for path in (staging_root / "application/table_verification").rglob("*.json")
    }
    actual_leaf_payloads = {
        rel_posix(path, staging_root)
        for path in (staging_root / "application/leaf_payloads").rglob("*")
        if path.is_file()
    }
    lane.exact_set(actual_bscr_reports, bscr_report_paths, "bscr_report_file_exact_set")
    lane.exact_set(actual_table_reports, table_report_paths, "table_report_file_exact_set")
    lane.exact_set(actual_table_verification, table_verification_paths, "table_verification_file_exact_set")
    lane.exact_set(actual_leaf_payloads, output_paths, "leaf_payload_file_exact_set")

    local_rows = list(static.get("local_physical_reports", []))
    local_by_physical: dict[str, dict[str, Any]] = {}
    for row in local_rows:
        physical = str(row.get("physical_path", ""))
        if physical in local_by_physical:
            lane.fail("duplicate_local_physical_report", path=physical)
        local_by_physical[physical] = row
    expected_local_paths = text_paths - {"Sys/system.vol", "Sys/help.bin", "Sys/monster_book.bin"}
    lane.exact_set(local_by_physical, expected_local_paths, "local_physical_report_exact_set")
    lane.require(len(local_rows) == EXPECTED_LOCAL_PHYSICAL, "local_physical_report_count", actual=len(local_rows))
    container_report_paths: set[str] = set()
    container_edit_paths: set[str] = set()
    container_errors: list[dict[str, str]] = []
    for physical, row in sorted(local_by_physical.items()):
        source = source_root / Path(physical)
        output = patch_root / Path(physical)
        expected_leaves = nested_by_physical.get(physical, [])
        if (
            not source.is_file()
            or not output.is_file()
            or sha256_file(source) != str(row.get("source_sha256", "")).upper()
            or sha256_file(output) != str(row.get("output_sha256", "")).upper()
            or source.stat().st_size != int(row.get("source_size", -1))
            or output.stat().st_size != int(row.get("output_size", -1))
            or int(row.get("edited_leaf_count", -1)) != (len(expected_leaves) if expected_leaves else 1)
        ):
            container_errors.append({"path": physical, "reason": "physical_summary"})
        report_relative = row.get("container_report")
        if not expected_leaves:
            if report_relative is not None:
                container_errors.append({"path": physical, "reason": "direct_has_container_report"})
            continue
        expected_report_relative = f"application/container_reports/{physical}.json"
        expected_edit_relative = f"application/container_edits/{physical}.json"
        container_report_paths.add(expected_report_relative)
        container_edit_paths.add(expected_edit_relative)
        expected_application_files.update({expected_report_relative, expected_edit_relative})
        if str(report_relative).replace("\\", "/") != expected_report_relative:
            container_errors.append({"path": physical, "reason": "container_report_path"})
            continue
        report_path = staging_root / Path(expected_report_relative)
        edit_path = staging_root / Path(expected_edit_relative)
        if not report_path.is_file() or not edit_path.is_file():
            container_errors.append({"path": physical, "reason": "missing_container_evidence"})
            continue
        report = read_json(report_path)
        edit_doc = read_json(edit_path)
        audits = audit_list(report)
        audit_by_path = {tuple(int(value) for value in item.get("entryPath", [])): item for item in audits}
        edits = list(edit_doc.get("edits", []))
        edit_by_path = {tuple(int(value) for value in item.get("entryPath", [])): item for item in edits}
        leaf_by_entry = {tuple(int(value) for value in leaf.get("entry_path", [])): leaf for leaf in expected_leaves}
        if len(audit_by_path) != len(audits) or len(edit_by_path) != len(edits) or set(audit_by_path) != set(leaf_by_entry) or set(edit_by_path) != set(leaf_by_entry):
            container_errors.append({"path": physical, "reason": "container_edit_exact_set"})
            continue
        if (
            str(report.get("inputSha256", "")).upper() != sha256_file(source)
            or str(report.get("outputSha256", "")).upper() != sha256_file(output)
            or int(report.get("inputSize", -1)) != source.stat().st_size
            or int(report.get("outputSize", -1)) != output.stat().st_size
            or report.get("byteExact") is not False
        ):
            container_errors.append({"path": physical, "reason": "container_input_output_hash"})
        for entry_path, leaf in leaf_by_entry.items():
            audit = audit_by_path[entry_path]
            edit = edit_by_path[entry_path]
            replacement = (edit_path.parent / Path(str(edit.get("replacementFile", "")))).resolve()
            leaf_output = staging_path(staging_root, str(leaf.get("output", ""))).resolve()
            if (
                str(audit.get("oldSha256", "")).upper() != str(leaf.get("source_sha256", "")).upper()
                or str(audit.get("newSha256", "")).upper() != str(leaf.get("output_sha256", "")).upper()
                or str(edit.get("expectedSha256", "")).upper() != str(leaf.get("source_sha256", "")).upper()
                or replacement != leaf_output
                or not replacement.is_file()
                or sha256_file(replacement) != str(leaf.get("output_sha256", "")).upper()
            ):
                container_errors.append({"path": physical, "reason": "container_leaf_audit"})
    lane.require(not container_errors, "individual_container_reports", mismatch_count=len(container_errors), mismatches=container_errors[:30])
    actual_container_reports = {
        rel_posix(path, staging_root)
        for path in (staging_root / "application/container_reports").rglob("*.json")
    }
    actual_container_edits = {
        rel_posix(path, staging_root)
        for path in (staging_root / "application/container_edits").rglob("*.json")
    }
    lane.exact_set(actual_container_reports, container_report_paths, "container_report_file_exact_set")
    lane.exact_set(actual_container_edits, container_edit_paths, "container_edit_file_exact_set")

    system_summary = dict(static.get("system", {}))
    system_output = patch_root / "Sys/system.vol"
    system_report_relative = str(system_summary.get("rebuild_report", "")).replace("\\", "/")
    system_report_path = staging_path(staging_root, system_report_relative)
    system_edit_relative = "application/system_vol_edits.json"
    system_edit_path = staging_root / system_edit_relative
    expected_application_files.update({system_report_relative, system_edit_relative})
    system_errors: list[str] = []
    if not system_output.is_file() or not system_report_path.is_file() or not system_edit_path.is_file():
        system_errors.append("missing")
    else:
        system_entries = parse_rtdp(system_output)
        source_system = source_root / "Sys/system.vol"
        source_system_entries = parse_rtdp(source_system)
        expected_internal_hashes = {
            **dict(context.get("font_hashes", {})),
            **{name: context.get("system_payload_hashes", {}).get(name) for name in SYSTEM_CONTAINER_TABLES},
            "nowloading.wtm": sha256_file(context["image_system_leaf"]) if context.get("image_system_leaf") else None,
        }
        lane.exact_set({name for name, value in expected_internal_hashes.items() if value}, set(SYSTEM_FONTS) | set(SYSTEM_CONTAINER_TABLES) | {"nowloading.wtm"}, "system_expected_internal_set")
        if set(system_entries) != set(source_system_entries):
            system_errors.append("system_entry_name_exact_set")
        else:
            for name, (source_index, source_payload) in source_system_entries.items():
                output_index, output_payload = system_entries[name]
                if output_index != source_index:
                    system_errors.append("system_entry_index:" + name)
                if name not in expected_internal_hashes and output_payload != source_payload:
                    system_errors.append("unexpected_system_entry_change:" + name)
        verified_rows = list(system_summary.get("verified_internal_entries", []))
        verified_by_name = {str(row.get("name")): row for row in verified_rows}
        if len(verified_by_name) != len(verified_rows) or set(verified_by_name) != set(expected_internal_hashes):
            system_errors.append("verified_internal_exact_set")
        for name, expected_hash in expected_internal_hashes.items():
            entry = system_entries.get(name)
            row = verified_by_name.get(name)
            if entry is None or row is None or expected_hash is None:
                system_errors.append("internal_missing:" + name)
                continue
            index, payload = entry
            if sha256_bytes(payload) != expected_hash or int(row.get("index", -1)) != index or str(row.get("sha256", "")).upper() != expected_hash:
                system_errors.append("internal_hash:" + name)
        if system_entries.get("nowloading.wtm", (-1, b""))[0] != 53 or int(system_summary.get("cumulative_nowloading_entry", -1)) != 53:
            system_errors.append("nowloading_index")
        if str(system_summary.get("output_system_sha256", "")).upper() != sha256_file(system_output):
            system_errors.append("system_output_hash")
        if str(system_summary.get("source_system_sha256", "")).upper() != sha256_file(source_system):
            system_errors.append("system_source_hash")
        direct_rows = {str(row.get("name")): row for row in system_summary.get("direct_payloads", [])}
        if set(direct_rows) != set(SYSTEM_DIRECT_TABLES):
            system_errors.append("direct_payload_set")
        for name in SYSTEM_DIRECT_TABLES:
            staged = patch_root / "Sys" / name
            expected_hash = context.get("system_payload_hashes", {}).get(name)
            if not staged.is_file() or expected_hash is None or sha256_file(staged) != expected_hash or str(direct_rows.get(name, {}).get("sha256", "")).upper() != expected_hash:
                system_errors.append("direct_payload_hash:" + name)
        rebuild_report = read_json(system_report_path)
        if str(rebuild_report.get("outputSha256", "")).upper() != sha256_file(system_output):
            system_errors.append("rebuild_report_output_hash")
        edits_doc = read_json(system_edit_path)
        edits = list(edits_doc.get("edits", []))
        edit_by_path = {tuple(int(value) for value in item.get("entryPath", [])): item for item in edits}
        audits = audit_list(rebuild_report)
        audit_by_path = {tuple(int(value) for value in item.get("entryPath", [])): item for item in audits}
        mode = str(system_summary.get("mode", ""))
        if mode == "rebuilt_cumulatively_from_final_tables_fonts_and_nowloading":
            expected_edit_paths = {(system_entries[name][0],) for name in expected_internal_hashes}
        elif mode == "cumulative_nowloading_over_supplied_text_font_system":
            expected_edit_paths = {(53,)}
        else:
            expected_edit_paths = set()
            system_errors.append("system_mode")
        if len(edit_by_path) != len(edits) or len(audit_by_path) != len(audits) or set(edit_by_path) != expected_edit_paths or set(audit_by_path) != expected_edit_paths:
            system_errors.append("system_edit_exact_set")
        for entry_path, edit in edit_by_path.items():
            replacement = (system_edit_path.parent / Path(str(edit.get("replacementFile", "")))).resolve()
            try:
                replacement_relative = rel_posix(replacement, staging_root)
                expected_application_files.add(replacement_relative)
            except ValueError:
                system_errors.append("system_replacement_escape")
                continue
            if not replacement.is_file():
                system_errors.append("system_replacement_missing")
                continue
            name = str(edit.get("name", ""))
            if name in expected_internal_hashes and expected_internal_hashes[name] is not None and sha256_file(replacement) != expected_internal_hashes[name]:
                system_errors.append("system_replacement_hash:" + name)
            audit = audit_by_path.get(entry_path, {})
            if (
                str(edit.get("expectedSha256", "")).upper()
                != str(audit.get("oldSha256", "")).upper()
                or str(audit.get("newSha256", "")).upper() != sha256_file(replacement)
            ):
                system_errors.append("system_edit_audit_hash:" + name)
    lane.require(not system_errors, "staged_system_reports", mismatch_count=len(system_errors), mismatches=system_errors[:30])

    image_static = dict(static.get("image_ui", {}))
    image_rows = list(image_static.get("direct_physical_files", []))
    image_by_path = {str(row.get("physical_path", "")): row for row in image_rows}
    lane.require(len(image_by_path) == len(image_rows), "duplicate_image_physical_report")
    lane.exact_set(image_by_path, image_direct, "staged_image_report_exact_set")
    image_report_errors: list[str] = []
    for physical, payload in image_direct.items():
        row = image_by_path.get(physical, {})
        staged = patch_root / Path(physical)
        source = source_root / Path(physical)
        if (
            not staged.is_file()
            or sha256_file(staged) != sha256_file(payload)
            or str(row.get("output_sha256", "")).upper() != sha256_file(payload)
            or str(row.get("source_sha256", "")).upper() != sha256_file(source)
            or Path(str(row.get("payload", ""))).resolve() != payload.resolve()
        ):
            image_report_errors.append(physical)
    cumulative = dict(image_static.get("cumulative_system_leaf", {}))
    if cumulative.get("entry_path") != [53] or not context.get("image_system_leaf") or str(cumulative.get("sha256", "")).upper() != sha256_file(context["image_system_leaf"]):
        image_report_errors.append("nowloading")
    lane.require(int(image_static.get("reinsertion_targets", -1)) == EXPECTED_IMAGE_TARGETS, "staged_image_target_count")
    lane.require(not image_report_errors, "staged_image_reports", mismatch_count=len(image_report_errors), mismatches=image_report_errors[:30])

    occurrence_relative = rel_posix(occurrence_manifest_path, staging_root) if occurrence_manifest_path.is_file() else str(static.get("occurrence_manifest", ""))
    leaf_relative = rel_posix(leaf_manifest_path, staging_root) if leaf_manifest_path.is_file() else str(static.get("leaf_manifest", ""))
    expected_application_files.update({occurrence_relative, leaf_relative})
    application_root = staging_root / "application"
    actual_application_files = {f"application/{relative}" for relative in actual_file_set(application_root)}
    lane.exact_set(actual_application_files, expected_application_files, "application_artifact_exact_set")
    application_unexpected = actual_application_files - expected_application_files
    application_missing = expected_application_files - actual_application_files

    expected_staging_files = (
        expected_application_files
        | {f"{patch_root_relative.rstrip('/')}/{physical}" for physical in overlay_allowlist}
        | {rel_posix(xml_path, staging_root) if xml_path.is_file() else str(riivolution.get("xml", "")), "staging_manifest.json"}
    )
    actual_staging_files = actual_file_set(staging_root)
    lane.exact_set(actual_staging_files, expected_staging_files, "full_staging_tree_exact_set")
    staging_unexpected = actual_staging_files - expected_staging_files
    staging_missing = expected_staging_files - actual_staging_files

    report_paths = [staging_root / Path(path) for path in bscr_report_paths | table_report_paths | table_verification_paths | container_report_paths]
    if system_report_path.is_file():
        report_paths.append(system_report_path)
    lane.evidence.update(
        {
            "staging_manifest_sha256": sha256_file(manifest_path),
            "text_physical_files": len(text_paths),
            "image_physical_files": len(image_direct),
            "supplemental_physical_files": len(supplemental_paths),
            "main_dol_memory_patches": len(xml_memory),
            "overlay_allowlist_files": len(overlay_allowlist),
            "overlay_actual_files": len(actual_overlay),
            "overlay_tree_sha256": tree_digest((patch_root / Path(path) for path in overlay_allowlist if (patch_root / Path(path)).is_file()), patch_root),
            "occurrence_application_rows": len(occurrence_application),
            "occurrence_application_manifest_sha256": sha256_file(occurrence_manifest_path) if occurrence_manifest_path.is_file() else None,
            "leaf_manifest_sha256": sha256_file(leaf_manifest_path) if leaf_manifest_path.is_file() else None,
            "bscr_reports": len(bscr_report_paths),
            "table_replacement_reports": len(table_report_paths),
            "table_verification_reports": len(table_verification_paths),
            "container_reports": len(container_report_paths),
            "individual_report_tree_sha256": tree_digest(report_paths, staging_root) if report_paths else None,
            "application_files": len(actual_application_files),
            "application_tree_sha256": tree_digest((staging_root / Path(path) for path in actual_application_files), staging_root),
            "unexpected_overlay_files": len(overlay_unexpected),
            "missing_overlay_files": len(overlay_missing),
            "unexpected_application_files": len(application_unexpected),
            "missing_application_files": len(application_missing),
            "unexpected_staging_files": len(staging_unexpected),
            "missing_staging_files": len(staging_missing),
            "unexpected_files": len(staging_unexpected),
        }
    )
    context.update(
        {
            "staging_root": staging_root,
            "staging_manifest": manifest,
            "staging_manifest_path": manifest_path,
            "patch_root": patch_root,
            "xml_path": xml_path,
            "overlay_allowlist": overlay_allowlist,
        }
    )


def safe_zip_name(name: str, package_name: str) -> bool:
    pure = PurePosixPath(name)
    return (
        not pure.is_absolute()
        and bool(pure.parts)
        and pure.parts[0] == package_name
        and ".." not in pure.parts
        and "" not in pure.parts
    )


def verify_release(lane: Lane, context: dict[str, Any]) -> None:
    outputs = ROOT / "outputs"
    package_name = "Arc_Rise_Fantasia_Korean_Patch_v1.0.2"
    package = outputs / package_name
    zip_path = outputs / f"{package_name}.zip"
    checksum_path = outputs / f"{package_name}.zip.sha256"
    presence = {"package": package.exists(), "zip": zip_path.exists(), "checksum": checksum_path.exists()}
    if not any(presence.values()):
        lane.evidence.update(
            {
                "status": "PENDING",
                "reason": "final release package has not been built",
                "expected_package_dir": str(package),
                "expected_zip": str(zip_path),
            }
        )
        return
    if not all(presence.values()):
        lane.fail("partial_release_artifacts", presence=presence)
        return
    if not package.is_dir() or not zip_path.is_file() or not checksum_path.is_file():
        lane.fail("invalid_release_artifact_types")
        return
    manifest_path = package / "MANIFEST.json"
    release_validation_path = WORK / "validation/final_release_validation.json"
    installer_fixture_path = WORK / "validation/installer_fixture.json"
    lane.require(manifest_path.is_file(), "release_manifest_missing")
    if not manifest_path.is_file():
        return
    manifest = read_json(manifest_path)
    expected_fields = {
        "schema": "arf-ko-riivolution-release-v1",
        "package": package_name,
        "game_id": GAME_ID,
        "source_rvz_sha256": SOURCE_RVZ_SHA256,
        "source_media_included": False,
        "source_media_write_policy": "read-only; never overwrite",
        "translation_engine_policy": TRANSLATION_POLICY,
        "external_translation_models_or_apis_used": False,
        "runtime_ready_release": True,
    }
    for field_name, expected in expected_fields.items():
        lane.require(manifest.get(field_name) == expected, "release_manifest_field", field=field_name, expected=expected, actual=manifest.get(field_name))
    actual_files = {
        path.relative_to(package).as_posix(): path
        for path in package.rglob("*")
        if path.is_file() and path.name != "MANIFEST.json"
    }
    declared_rows = list(manifest.get("files", []))
    declared = {str(row.get("path", "")): row for row in declared_rows}
    lane.require(len(declared) == len(declared_rows), "release_duplicate_manifest_path")
    lane.exact_set(actual_files, declared, "release_manifest_file_exact_set")
    release_hash_errors: list[str] = []
    for relative, path in actual_files.items():
        row = declared.get(relative)
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts or row is None:
            release_hash_errors.append(relative)
            continue
        if path.stat().st_size != int(row.get("size_bytes", -1)) or sha256_file(path) != str(row.get("sha256", "")).upper():
            release_hash_errors.append(relative)
    lane.require(not release_hash_errors, "release_file_hashes", mismatch_count=len(release_hash_errors), mismatches=release_hash_errors[:30])

    overlay_allowlist: set[str] = context.get("overlay_allowlist", set())
    patch_root: Path | None = context.get("patch_root")
    xml_path: Path | None = context.get("xml_path")
    package_files_root = package / "payload/riivolution_sd/arc_rise_fantasia_ko_full/files"
    package_physical = actual_file_set(package_files_root)
    lane.exact_set(package_physical, overlay_allowlist, "release_overlay_physical_exact_set")
    package_overlay_errors: list[str] = []
    if patch_root is not None:
        for physical in overlay_allowlist:
            packaged = package_files_root / Path(physical)
            staged = patch_root / Path(physical)
            if not packaged.is_file() or not staged.is_file() or sha256_file(packaged) != sha256_file(staged):
                package_overlay_errors.append(physical)
    packaged_xml = package / "payload/riivolution_sd/riivolution/arc_rise_fantasia_ko_full.xml"
    if xml_path is None or not packaged_xml.is_file() or sha256_file(packaged_xml) != sha256_file(xml_path):
        package_overlay_errors.append("riivolution_xml")
    lane.require(not package_overlay_errors, "release_staging_hash_binding", mismatch_count=len(package_overlay_errors), mismatches=package_overlay_errors[:30])

    overlay_role_paths = {str(row.get("path")) for row in declared_rows if row.get("role") == "riivolution_overlay"}
    actual_overlay_paths = {relative for relative in actual_files if relative.startswith("payload/riivolution_sd/")}
    lane.exact_set(overlay_role_paths, actual_overlay_paths, "release_overlay_role_exact_set")
    lane.require(int(manifest.get("overlay_file_count", -1)) == len(actual_overlay_paths), "release_overlay_count")
    lane.require(len(actual_overlay_paths) == EXPECTED_RELEASE_OVERLAY_FILES, "release_overlay_total_count")
    lane.require(
        int(manifest.get("game_replacement_file_count", -1)) == EXPECTED_OVERLAY_PHYSICAL,
        "release_game_replacement_count",
    )
    lane.require(len(package_physical) == EXPECTED_OVERLAY_PHYSICAL, "release_physical_count")

    zip_hash = sha256_file(zip_path)
    checksum_tokens = checksum_path.read_text(encoding="ascii").split()
    lane.require(bool(checksum_tokens) and checksum_tokens[0].upper() == zip_hash, "release_zip_checksum")
    with zipfile.ZipFile(zip_path) as archive:
        bad = archive.testzip()
        lane.require(bad is None, "release_zip_crc", member=bad)
        names = {info.filename for info in archive.infolist() if not info.is_dir()}
        unsafe = {name for name in names if not safe_zip_name(name, package_name)}
        lane.require(not unsafe, "release_zip_unsafe_names", names=sample(unsafe))
        expected_zip_names = {
            (PurePosixPath(package_name) / path.relative_to(package).as_posix()).as_posix()
            for path in package.rglob("*")
            if path.is_file()
        }
        lane.exact_set(names, expected_zip_names, "release_zip_file_exact_set")

    # Bind the independent post-build validator to the exact package, ZIP and
    # manifest that were checked above.  A stale green report cannot satisfy
    # this lane after any release artifact changes.
    lane.require(release_validation_path.is_file(), "release_validation_missing")
    release_validation: dict[str, Any] = {}
    if release_validation_path.is_file():
        release_validation = read_json(release_validation_path)
        lane.require(
            release_validation.get("schema") == "arf-ko-final-release-validation-v1",
            "release_validation_schema",
        )
        declared_package = project_path(str(release_validation.get("package_dir", "")))
        declared_zip = project_path(str(release_validation.get("zip_path", "")))
        lane.require(declared_package.resolve() == package.resolve(), "release_validation_package_path")
        lane.require(declared_zip.resolve() == zip_path.resolve(), "release_validation_zip_path")
        lane.require(
            int(release_validation.get("zip_size_bytes", -1)) == zip_path.stat().st_size,
            "release_validation_zip_size",
        )
        lane.require(
            str(release_validation.get("zip_sha256", "")).upper() == zip_hash,
            "release_validation_zip_hash",
        )
        lane.require(
            str(release_validation.get("manifest_sha256", "")).upper() == sha256_file(manifest_path),
            "release_validation_manifest_hash",
        )
        lane.require(
            int(release_validation.get("overlay_file_count", -1)) == EXPECTED_RELEASE_OVERLAY_FILES,
            "release_validation_overlay_count",
        )
        lane.require(
            int(release_validation.get("game_replacement_file_count", -1)) == EXPECTED_OVERLAY_PHYSICAL,
            "release_validation_game_replacement_count",
        )
        lane.require(
            release_validation.get("translation_engine_policy") == TRANSLATION_POLICY,
            "release_validation_translation_policy",
        )
        lane.require(
            release_validation.get("external_translation_models_or_apis_used") is False,
            "release_validation_external_translation_flag",
        )
        lane.require(
            release_validation.get("valid") is True
            and int(release_validation.get("error_count", -1)) == 0
            and not release_validation.get("errors"),
            "release_validation_invalid",
        )

    # The installer fixture proves pristine install, installed-file hash
    # verification, byte-exact restore, no leftovers and fail-before-write on
    # payload tamper.  Require the exact five named checks rather than trusting
    # only the aggregate `valid` flag.
    lane.require(installer_fixture_path.is_file(), "installer_fixture_missing")
    installer_fixture: dict[str, Any] = {}
    installer_checks: dict[str, dict[str, Any]] = {}
    if installer_fixture_path.is_file():
        installer_fixture = read_json(installer_fixture_path)
        lane.require(
            installer_fixture.get("schema") == "arf-ko-installer-fixture-v1",
            "installer_fixture_schema",
        )
        declared_package = project_path(str(installer_fixture.get("package_root", "")))
        lane.require(declared_package.resolve() == package.resolve(), "installer_fixture_package_path")
        lane.require(
            str(installer_fixture.get("source_rvz_sha256", "")).upper() == SOURCE_RVZ_SHA256,
            "installer_fixture_source_hash",
        )
        lane.require(
            str(installer_fixture.get("package_manifest_sha256", "")).upper()
            == sha256_file(manifest_path),
            "installer_fixture_package_manifest_hash",
        )
        lane.require(
            int(installer_fixture.get("package_manifest_size_bytes", -1))
            == manifest_path.stat().st_size,
            "installer_fixture_package_manifest_size",
        )
        check_rows = list(installer_fixture.get("checks", []))
        installer_checks = {str(row.get("name", "")): row for row in check_rows}
        lane.require(len(installer_checks) == len(check_rows), "installer_fixture_duplicate_check")
        lane.exact_set(installer_checks, EXPECTED_INSTALLER_FIXTURE_CHECKS, "installer_fixture_exact_check_set")
        failed_names = sorted(name for name, row in installer_checks.items() if row.get("passed") is not True)
        lane.require(not failed_names, "installer_fixture_failed_checks", checks=failed_names)
        lane.require(
            int(installer_fixture.get("passed_count", -1)) == len(EXPECTED_INSTALLER_FIXTURE_CHECKS)
            and int(installer_fixture.get("failed_count", -1)) == 0
            and installer_fixture.get("valid") is True,
            "installer_fixture_invalid",
        )

    lane.evidence.update(
        {
            "status": "PASS" if not lane.errors else "FAIL",
            "package_dir": str(package),
            "manifest_sha256": sha256_file(manifest_path),
            "package_physical_files": len(package_physical),
            "zip_path": str(zip_path),
            "zip_size_bytes": zip_path.stat().st_size,
            "zip_sha256": zip_hash,
            "release_validation_path": str(release_validation_path),
            "release_validation_sha256": sha256_file(release_validation_path) if release_validation_path.is_file() else None,
            "release_validation_overlay_files": release_validation.get("overlay_file_count"),
            "release_validation_game_replacements": release_validation.get("game_replacement_file_count"),
            "installer_fixture_path": str(installer_fixture_path),
            "installer_fixture_sha256": sha256_file(installer_fixture_path) if installer_fixture_path.is_file() else None,
            "installer_fixture_passed": installer_fixture.get("passed_count"),
        }
    )
    context.update(
        {
            "release_package_dir": package,
            "release_manifest_path": manifest_path,
            "release_manifest": manifest,
            "release_zip_path": zip_path,
            "release_zip_sha256": zip_hash,
            "release_validation_path": release_validation_path,
            "installer_fixture_path": installer_fixture_path,
        }
    )


def verify_dolphin_runtime(lane: Lane, context: dict[str, Any]) -> None:
    """Validate an optional, artifact-bound Dolphin runtime report.

    The runtime check is intentionally outside the deterministic static lane.
    When supplied, however, it must identify the exact staging and release
    artifacts already accepted above, so a report from an older build cannot be
    combined with the current package.
    """

    report_path: Path | None = context.get("dolphin_runtime_report_path")
    if report_path is None:
        lane.evidence.update(
            {
                "status": "NOT_SUPPLIED",
                "default_path": str(DEFAULT_DOLPHIN_RUNTIME_REPORT),
                "reason": "optional Dolphin runtime report was not supplied",
            }
        )
        return
    lane.require(report_path.is_file(), "dolphin_runtime_report_missing", path=str(report_path))
    if not report_path.is_file():
        return
    report = read_json(report_path)
    lane.require(report.get("schema") == DOLPHIN_RUNTIME_SCHEMA, "dolphin_runtime_schema")
    lane.require(report.get("game_id") == GAME_ID, "dolphin_runtime_game_id")

    staging_manifest_path: Path | None = context.get("staging_manifest_path")
    release_manifest_path: Path | None = context.get("release_manifest_path")
    xml_path: Path | None = context.get("xml_path")
    required_bindings = (
        ("staging_manifest_sha256", staging_manifest_path),
        ("package_manifest_sha256", release_manifest_path),
        ("riivolution_xml_sha256", xml_path),
    )
    binding_evidence: dict[str, str | None] = {}
    for field_name, artifact_path in required_bindings:
        actual_hash = sha256_file(artifact_path) if artifact_path is not None and artifact_path.is_file() else None
        binding_evidence[field_name] = actual_hash
        lane.require(
            actual_hash is not None and str(report.get(field_name, "")).upper() == actual_hash,
            "dolphin_runtime_artifact_binding",
            field=field_name,
            expected_sha256=actual_hash,
            actual_sha256=report.get(field_name),
        )

    check_rows = list(report.get("checks", []))
    checks = {str(row.get("name", "")): row for row in check_rows}
    lane.require(bool(check_rows), "dolphin_runtime_no_checks")
    lane.require(len(checks) == len(check_rows) and "" not in checks, "dolphin_runtime_duplicate_or_empty_check")
    failed_checks = sorted(name for name, row in checks.items() if row.get("passed") is not True)
    lane.require(not failed_checks, "dolphin_runtime_failed_checks", checks=failed_checks)
    lane.require(
        int(report.get("passed_count", -1)) == len(check_rows)
        and int(report.get("failed_count", -1)) == 0,
        "dolphin_runtime_check_counts",
    )
    lane.require(
        report.get("valid") is True
        and int(report.get("error_count", 0)) == 0
        and not report.get("errors", []),
        "dolphin_runtime_invalid",
    )

    # Hash-bind any screenshot/log artifacts declared in the same standard
    # path/size/hash record form used throughout this verifier.
    artifact_errors: list[dict[str, Any]] = []
    artifact_count = 0
    for location, record in iter_artifact_records(report.get("artifacts", []), "$.artifacts"):
        artifact_count += 1
        path = project_path(str(record.get("path", "")))
        expected_hash = str(record.get("sha256", ""))
        expected_size = int(record.get("size_bytes", -1))
        if (
            not path.is_file()
            or expected_size < 0
            or path.stat().st_size != expected_size
            or not validate_hash(path, expected_hash)
        ):
            artifact_errors.append({"location": location, "path": str(path)})
    lane.require(
        not artifact_errors,
        "dolphin_runtime_artifact_hashes",
        mismatch_count=len(artifact_errors),
        mismatches=artifact_errors[:30],
    )
    lane.evidence.update(
        {
            "status": "PASS" if not lane.errors else "FAIL",
            "report_path": str(report_path),
            "report_sha256": sha256_file(report_path),
            "checks": len(check_rows),
            "artifacts": artifact_count,
            "artifact_bindings": binding_evidence,
        }
    )


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=WORK / "validation/full_final_static_verification.json",
    )
    parser.add_argument(
        "--runtime-report",
        type=Path,
        default=None,
        help=(
            "optional Dolphin report using schema "
            f"{DOLPHIN_RUNTIME_SCHEMA}; if omitted, "
            f"{DEFAULT_DOLPHIN_RUNTIME_REPORT} is auto-detected when present"
        ),
    )
    args = parser.parse_args()
    context: dict[str, Any] = {}

    lane_specs = (
        ("text_translation_and_report", verify_text_translation),
        ("heuristic_warning_waivers", verify_heuristic_waivers),
        ("system_tables_and_fonts", verify_system_fonts),
        ("image_ui", verify_image_ui),
        ("runtime_supplement", verify_runtime_supplement),
        ("immutable_source_rvz", verify_immutable_source),
        ("runtime_staging", verify_runtime_staging),
    )
    lanes: dict[str, Lane] = {}
    for name, function in lane_specs:
        print(f"[verify] {name}", flush=True)
        lanes[name] = run_lane(name, function, context)

    static_valid = all(not lane.errors for lane in lanes.values())
    print("[verify] release_package", flush=True)
    release_lane = run_lane("release_package", verify_release, context)
    release_pending = not release_lane.errors and release_lane.evidence.get("status") == "PENDING"
    if release_pending:
        release_status = "PENDING"
    else:
        release_status = "PASS" if not release_lane.errors else "FAIL"

    if args.runtime_report is not None:
        runtime_report_path = args.runtime_report if args.runtime_report.is_absolute() else ROOT / args.runtime_report
    elif DEFAULT_DOLPHIN_RUNTIME_REPORT.is_file():
        runtime_report_path = DEFAULT_DOLPHIN_RUNTIME_REPORT
    else:
        runtime_report_path = None
    context["dolphin_runtime_report_path"] = runtime_report_path
    print("[verify] dolphin_runtime", flush=True)
    dolphin_lane = run_lane("dolphin_runtime", verify_dolphin_runtime, context)
    runtime_not_supplied = not dolphin_lane.errors and dolphin_lane.evidence.get("status") == "NOT_SUPPLIED"
    if runtime_not_supplied:
        dolphin_status = "NOT_SUPPLIED"
    else:
        dolphin_status = "PASS" if not dolphin_lane.errors else "FAIL"

    lane_results = {name: lane.result() for name, lane in lanes.items()}
    release_result = release_lane.result()
    release_result["status"] = release_status
    release_result["valid"] = None if release_pending else not release_lane.errors
    lane_results["release_package"] = release_result
    dolphin_result = dolphin_lane.result()
    dolphin_result["status"] = dolphin_status
    dolphin_result["valid"] = None if runtime_not_supplied else not dolphin_lane.errors
    lane_results["dolphin_runtime"] = dolphin_result

    static_errors = [
        {"lane": name, **error}
        for name, lane in lanes.items()
        for error in lane.errors
    ]
    if not static_valid or release_status == "FAIL" or dolphin_status == "FAIL":
        overall_status = "FAIL"
    elif release_status == "PENDING":
        overall_status = "STATIC_PASS_RELEASE_PENDING"
    elif release_status == "PASS":
        overall_status = "PASS"
    else:
        overall_status = "FAIL"
    runtime_evidence = lanes["runtime_staging"].evidence
    report = {
        "schema": "arf-full-final-static-verification-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "game_id": GAME_ID,
        "translation_engine_policy": TRANSLATION_POLICY,
        "external_translation_services_used": [],
        "external_translation_models_or_apis_used": [],
        "static_runtime_staging_status": "PASS" if static_valid else "FAIL",
        "static_valid": static_valid,
        "release_lane_status": release_status,
        "dolphin_runtime_status": dolphin_status,
        "runtime_ready_release": release_status == "PASS" and dolphin_status != "FAIL",
        "overall_status": overall_status,
        "summary": {
            "tm_units": len(context.get("tm_by_id", {})),
            "catalog_occurrences": len(context.get("catalog_by_id", {})),
            "review_batches": len(context.get("review_chain", {}).get("batches", [])),
            "remaining_heuristic_warnings": context.get("validator_warning_count"),
            "unwaived_heuristic_warnings": lanes["heuristic_warning_waivers"].evidence.get("unwaived_warning_events"),
            "system_payloads": len(context.get("system_payload_hashes", {})),
            "system_fields": context.get("system_proof", {}).get("replacement_table_fields"),
            "font_pages": len(context.get("font_hashes", {})),
            "image_reinsertion_targets": lanes["image_ui"].evidence.get("reinsertion_targets"),
            "text_physical_sources": len(context.get("text_physical_paths", set())),
            "image_physical_sources": len(context.get("image_direct", {})),
            "overlay_allowlist_files": len(context.get("overlay_allowlist", set())),
            "unexpected_files": runtime_evidence.get("unexpected_files"),
            "source_rvz_sha256": lanes["immutable_source_rvz"].evidence.get("sha256"),
            "release_overlay_files": release_lane.evidence.get("release_validation_overlay_files"),
            "release_game_replacements": release_lane.evidence.get("release_validation_game_replacements"),
            "installer_fixture_passed": release_lane.evidence.get("installer_fixture_passed"),
            "dolphin_runtime_checks": dolphin_lane.evidence.get("checks"),
        },
        "lanes": lane_results,
        "static_error_count": len(static_errors),
        "static_errors": static_errors,
        "release_error_count": len(release_lane.errors),
        "release_errors": release_lane.errors,
        "dolphin_runtime_error_count": len(dolphin_lane.errors),
        "dolphin_runtime_errors": dolphin_lane.errors,
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    atomic_write_json(output, report)
    output_hash = sha256_file(output)
    print(
        json.dumps(
            {
                "output": str(output),
                "sha256": output_hash,
                "static_runtime_staging_status": report["static_runtime_staging_status"],
                "release_lane_status": release_status,
                "dolphin_runtime_status": dolphin_status,
                "overall_status": overall_status,
                "static_error_count": len(static_errors),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0 if static_valid and release_status != "FAIL" and dolphin_status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
