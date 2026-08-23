#!/usr/bin/env python3
"""Audit whether final ARF reports and release artifacts need refreshing.

This is intentionally a read-only dependency audit.  Apart from the JSON file
selected with ``--output``, it does not rebuild translations, fonts, staging,
the public release, the ZIP, or installer fixtures.  Its purpose is to catch a
green-but-stale evidence chain after a late translation or payload correction.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


PACKAGE_NAME = "Arc_Rise_Fantasia_Korean_Patch_v1.0.2"
EXPECTED_TM_UNITS = 29_777
EXPECTED_MAIN_DOL_UNITS = 926
EXPECTED_SYSTEM_FIELDS = 5_236
EXPECTED_SYSTEM_PAYLOADS = 13
EXPECTED_STAGED_PHYSICAL = 684
GEOMETRY_TM_ID = "ARF-TM-7983B232461623CDF50F"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def artifact(path: Path, root: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": path.resolve().relative_to(root.resolve()).as_posix()
        if path.resolve().is_relative_to(root.resolve())
        else str(path.resolve()),
        "exists": path.is_file(),
    }
    if path.is_file():
        record.update(size_bytes=path.stat().st_size, sha256=sha256(path))
    return record


def resolve_project_path(root: Path, value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else root / path


def iter_artifact_records(
    value: Any, location: str = "$"
) -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        if {"path", "size_bytes", "sha256"}.issubset(value):
            yield location, value
        for key, child in value.items():
            yield from iter_artifact_records(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_artifact_records(child, f"{location}[{index}]")


def tree(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file()
    }


def compare_trees(left: Path, right: Path) -> dict[str, Any]:
    left_files = tree(left)
    right_files = tree(right)
    shared = left_files.keys() & right_files.keys()
    changed = [
        relative
        for relative in sorted(shared)
        if sha256(left_files[relative]) != sha256(right_files[relative])
    ]
    return {
        "left": str(left.resolve()),
        "right": str(right.resolve()),
        "left_file_count": len(left_files),
        "right_file_count": len(right_files),
        "missing_from_right": sorted(left_files.keys() - right_files.keys()),
        "extra_in_right": sorted(right_files.keys() - left_files.keys()),
        "changed_count": len(changed),
        "changed": [
            {
                "path": relative,
                "right_sha256": sha256(right_files[relative]),
                "left_sha256": sha256(left_files[relative]),
            }
            for relative in changed
        ],
        "equal": (
            left_files.keys() == right_files.keys() and not changed
        ),
    }


def compact_approved_units(units: list[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(
            {"tm_id": str(unit["tm_id"]), "translation_ko": str(unit["translation_ko"])},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
        for unit in units
    ).encode("utf-8")


def compare_tm_rows(
    expected: dict[str, str], actual: dict[str, str]
) -> dict[str, Any]:
    missing = sorted(expected.keys() - actual.keys())
    extra = sorted(actual.keys() - expected.keys())
    mismatched = sorted(
        tm_id
        for tm_id in expected.keys() & actual.keys()
        if expected[tm_id] != actual[tm_id]
    )
    return {
        "expected_count": len(expected),
        "actual_count": len(actual),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "translation_mismatch_count": len(mismatched),
        "missing_sample": missing[:20],
        "extra_sample": extra[:20],
        "translation_mismatch_sample": [
            {
                "tm_id": tm_id,
                "actual": actual[tm_id],
                "expected": expected[tm_id],
            }
            for tm_id in mismatched[:20]
        ],
        "exact": not missing and not extra and not mismatched,
    }


def hash_binding(
    report: dict[str, Any], field: str, path: Path
) -> dict[str, Any]:
    declared = str(report.get(field, "")).upper()
    actual = sha256(path) if path.is_file() else None
    return {
        "field": field,
        "path": str(path.resolve()),
        "declared_sha256": declared or None,
        "actual_sha256": actual,
        "present": bool(declared),
        "matches": bool(actual and declared == actual),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Return status 1 when the refresh chain is not ready.",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    output = (
        args.output
        or root / "work/validation/final_release_refresh_preflight.json"
    ).resolve()

    p = {
        "tm": root / "work/translation/final/translation_memory_draft.json",
        "tm_csv": root / "work/translation/final/translation_memory_draft.csv",
        "review_chain": root / "work/translation/final_validation/review_chain.json",
        "approved_v1": root / "work/font/final_v1/approved_units.jsonl",
        "corpus_v1": root / "work/font/final_v1/approved_korean_corpus.txt",
        "corpus_manifest": root / "work/font/final_v1/corpus_manifest.json",
        "approved_v2": root / "work/font/final_v2/approved_units.jsonl",
        "main_dol": root / "work/runtime_fix/main_dol_translations.jsonl",
        "codebook": root / "work/font/final_v2/codebook.json",
        "codebook_verification": root
        / "work/font/final_v2/codebook_append_only_verification.json",
        "injection_verification": root
        / "work/font/final_v2/injection_verification.json",
        "fit": root / "work/font/final_v2/fit_preflight.json",
        "post_geometry_fit": root
        / "work/translation/fixed_field_fit/preflight_after_geometry_corrections.json",
        "geometry_correction": root
        / "work/translation/fixed_field_fit/geometry_regression_correction.json",
        "geometry_repair": root
        / "work/runtime_validation/fixed_table_geometry_repair_validation.json",
        "proof": root / "work/final_system_table_application/application_proof.json",
        "staging_manifest": root
        / "work/final_runtime_staging/staging_manifest.json",
        "staging_tree": root / "work/final_runtime_staging/riivolution_sd",
        "integration": root / "work/final_text_font_integration_report.json",
        "package": root / "outputs" / PACKAGE_NAME,
        "package_tree": root
        / "outputs"
        / PACKAGE_NAME
        / "payload/riivolution_sd",
        "zip": root / "outputs" / f"{PACKAGE_NAME}.zip",
        "checksum": root / "outputs" / f"{PACKAGE_NAME}.zip.sha256",
        "release_validation": root
        / "work/validation/final_release_validation.json",
        "installer_fixture": root / "work/validation/installer_fixture.json",
    }
    missing_required = [name for name, path in p.items() if name not in {"package", "package_tree", "zip", "checksum", "release_validation", "installer_fixture"} and not path.exists()]
    if missing_required:
        raise FileNotFoundError(f"missing required artifacts: {missing_required}")

    memory = read_json(p["tm"])
    approved_tm_units = [
        unit
        for unit in memory.get("units", [])
        if unit.get("review_status") == "approved"
        and str(unit.get("translation_ko", "")).strip()
    ]
    tm_by_id = {
        str(unit["tm_id"]): str(unit["translation_ko"])
        for unit in approved_tm_units
    }
    geometry_tm = next(
        (unit for unit in approved_tm_units if unit.get("tm_id") == GEOMETRY_TM_ID),
        None,
    )

    with p["tm_csv"].open("r", encoding="utf-8-sig", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    csv_by_id = {
        str(row["tm_id"]): str(row["translation_ko"])
        for row in csv_rows
        if str(row.get("review_status", "")) == "approved"
        and str(row.get("translation_ko", "")).strip()
    }
    csv_comparison = compare_tm_rows(tm_by_id, csv_by_id)

    reviewed_by_id: dict[str, str] = {}
    for path in sorted((root / "work/translation/reviewed").glob("batch_*.jsonl")):
        for row in read_jsonl(path):
            reviewed_by_id[str(row["tm_id"])] = str(row.get("translation_ko", ""))
    reviewed_comparison = compare_tm_rows(tm_by_id, reviewed_by_id)

    review_chain = read_json(p["review_chain"])
    review_hash_mismatches: list[dict[str, Any]] = []
    for row in review_chain.get("batches", []):
        batch = str(row["batch"])
        references = {
            "source_sha256": root
            / f"work/translation/tm_v2/batches/source/{batch}.jsonl",
            "draft_sha256": root / f"work/translation/drafts/{batch}.jsonl",
            "reviewed_sha256": root / f"work/translation/reviewed/{batch}.jsonl",
            "review_report_sha256": root
            / f"work/translation/reviews/{batch}_review.json",
            "validation_sha256": root
            / f"work/translation/final_validation/{batch}_reviewed.json",
        }
        for field, path in references.items():
            actual = sha256(path) if path.is_file() else None
            declared = str(row.get(field, "")).upper()
            if actual != declared:
                review_hash_mismatches.append(
                    {
                        "batch": batch,
                        "field": field,
                        "path": str(path.resolve()),
                        "declared_sha256": declared or None,
                        "actual_sha256": actual,
                    }
                )

    approved_reports: dict[str, Any] = {}
    for name in ("approved_v1", "approved_v2"):
        rows = read_jsonl(p[name])
        tm_rows = {
            str(row["tm_id"]): str(row["translation_ko"])
            for row in rows
            if "tm_id" in row
        }
        comparison = compare_tm_rows(tm_by_id, tm_rows)
        approved_reports[name] = {
            "artifact": artifact(p[name], root),
            "line_count": len(rows),
            "tm_row_count": len(tm_rows),
            "non_tm_row_count": len(rows) - len(tm_rows),
            "tm_comparison": comparison,
        }

    expected_v1_lf = compact_approved_units(approved_tm_units)
    expected_corpus_lf = (
        "\n".join(str(unit["translation_ko"]) for unit in approved_tm_units) + "\n"
    ).encode("utf-8")
    expected_v1_bytes = expected_v1_lf.replace(b"\n", os.linesep.encode("ascii"))
    expected_corpus_bytes = expected_corpus_lf.replace(
        b"\n", os.linesep.encode("ascii")
    )
    approved_reports["approved_v1"].update(
        expected_sha256=sha256_bytes(expected_v1_bytes),
        exact_expected_bytes=p["approved_v1"].read_bytes() == expected_v1_bytes,
    )
    approved_reports["corpus_v1"] = {
        "artifact": artifact(p["corpus_v1"], root),
        "expected_sha256": sha256_bytes(expected_corpus_bytes),
        "exact_expected_bytes": p["corpus_v1"].read_bytes() == expected_corpus_bytes,
    }

    main_dol_rows = read_jsonl(p["main_dol"])
    v2_rows = read_jsonl(p["approved_v2"])
    v2_extra_rows = [row for row in v2_rows if "tm_id" not in row]
    approved_reports["approved_v2"].update(
        main_dol_expected_count=EXPECTED_MAIN_DOL_UNITS,
        main_dol_actual_count=len(main_dol_rows),
        main_dol_rows_exact=v2_extra_rows == main_dol_rows,
    )

    corpus_manifest = read_json(p["corpus_manifest"])
    corpus_bindings = [
        hash_binding(corpus_manifest, "approved_units_jsonl_sha256", p["approved_v1"]),
        hash_binding(corpus_manifest, "corpus_sha256", p["corpus_v1"]),
        hash_binding(corpus_manifest, "translation_memory_sha256", p["tm"]),
    ]

    codebook = read_json(p["codebook"])
    codebook_chars = set(codebook.get("characters", {}))
    current_font_text = [str(unit["translation_ko"]) for unit in approved_tm_units]
    current_font_text.extend(str(row.get("translation_ko", "")) for row in main_dol_rows)
    required_custom: set[str] = set()
    for char in "".join(current_font_text):
        try:
            char.encode("euc_jp")
        except UnicodeEncodeError:
            required_custom.add(char)
    missing_custom = sorted(required_custom - codebook_chars, key=ord)
    unused_codebook = sorted(codebook_chars - required_custom, key=ord)

    fit = read_json(p["fit"])
    post_geometry_fit = read_json(p["post_geometry_fit"])
    fit_bindings = [
        hash_binding(fit, "translation_memory_sha256", p["tm"]),
        hash_binding(fit, "codebook_sha256", p["codebook"]),
    ]
    fit_ready = (
        fit.get("safe_for_fixed_table_insertion") is True
        and int(fit.get("matched_table_fields", -1)) == EXPECTED_SYSTEM_FIELDS
        and int(fit.get("fixed_overflow_count", -1)) == 0
        and all(binding["matches"] for binding in fit_bindings)
    )

    geometry_correction = read_json(p["geometry_correction"])
    geometry_repair = read_json(p["geometry_repair"])
    geometry_audit_bindings: list[dict[str, Any]] = []
    for row in geometry_correction.get("audits", []):
        path = resolve_project_path(root, row.get("path", ""))
        actual = sha256(path) if path.is_file() else None
        geometry_audit_bindings.append(
            {
                "path": str(path.resolve()),
                "declared_sha256": str(row.get("sha256", "")).upper(),
                "actual_sha256": actual,
                "matches": actual == str(row.get("sha256", "")).upper(),
            }
        )
    correction_artifacts = dict(geometry_correction.get("artifacts", {}))
    geometry_current = (
        geometry_correction.get("valid") is True
        and geometry_tm is not None
        and str(geometry_tm.get("translation_ko"))
        == str(geometry_correction.get("correction", {}).get("after"))
        and correction_artifacts.get("final_tm_sha256") == sha256(p["tm"])
        and correction_artifacts.get("final_tm_csv_sha256") == sha256(p["tm_csv"])
        and all(row["matches"] for row in geometry_audit_bindings)
        and geometry_repair.get("valid") is True
        and int(
            geometry_repair.get("summary", {}).get(
                "protected_changed_bytes_sum", -1
            )
        )
        == 0
    )

    proof = read_json(p["proof"])
    proof_payload_mismatches: list[dict[str, Any]] = []
    for row in proof.get("payloads", []):
        path = resolve_project_path(root, row.get("output_path", ""))
        actual = sha256(path) if path.is_file() else None
        declared = str(row.get("output_sha256", "")).upper()
        if actual != declared:
            proof_payload_mismatches.append(
                {
                    "catalog": row.get("catalog"),
                    "path": str(path.resolve()),
                    "declared_sha256": declared,
                    "actual_sha256": actual,
                }
            )
    proof_current = (
        proof.get("valid") is True
        and str(proof.get("translation_memory_sha256", "")).upper() == sha256(p["tm"])
        and str(proof.get("codebook_sha256", "")).upper() == sha256(p["codebook"])
        and int(proof.get("payloads_rebuilt", -1)) == EXPECTED_SYSTEM_PAYLOADS
        and int(proof.get("replacement_table_fields", -1)) == EXPECTED_SYSTEM_FIELDS
        and int(proof.get("fixed_payload_changes_outside_declared_slots", -1)) == 0
        and not proof_payload_mismatches
    )

    staging = read_json(p["staging_manifest"])
    staging_inputs = dict(staging.get("inputs", {}))
    staging_bindings = []
    for key, path in (
        ("translation_memory", p["tm"]),
        ("codebook", p["codebook"]),
        ("system_application_proof", p["proof"]),
    ):
        record = dict(staging_inputs.get(key, {}))
        actual = sha256(path)
        staging_bindings.append(
            {
                "input": key,
                "declared_sha256": str(record.get("sha256", "")).upper(),
                "actual_sha256": actual,
                "matches": str(record.get("sha256", "")).upper() == actual,
            }
        )
    staging_current = (
        int(staging.get("counts", {}).get("staged_physical_files", -1))
        == EXPECTED_STAGED_PHYSICAL
        and staging.get("static_validation", {}).get("valid") is True
        and int(staging.get("static_validation", {}).get("error_count", -1)) == 0
        and all(row["matches"] for row in staging_bindings)
    )

    integration = read_json(p["integration"])
    integration_artifact_mismatches: list[dict[str, Any]] = []
    for location, row in iter_artifact_records(integration):
        path = resolve_project_path(root, row.get("path", ""))
        actual_hash = sha256(path) if path.is_file() else None
        actual_size = path.stat().st_size if path.is_file() else None
        if (
            actual_hash != str(row.get("sha256", "")).upper()
            or actual_size != int(row.get("size_bytes", -1))
        ):
            integration_artifact_mismatches.append(
                {
                    "location": location,
                    "path": str(path.resolve()),
                    "declared_sha256": str(row.get("sha256", "")).upper(),
                    "actual_sha256": actual_hash,
                    "declared_size": row.get("size_bytes"),
                    "actual_size": actual_size,
                }
            )
    integration_current = (
        integration.get("valid") is True
        and not integration_artifact_mismatches
        and str(
            integration.get("frozen_translation_memory", {})
            .get("json", {})
            .get("sha256", "")
        ).upper()
        == sha256(p["tm"])
        and str(
            integration.get("system_table_application", {})
            .get("proof", {})
            .get("sha256", "")
        ).upper()
        == sha256(p["proof"])
    )

    release_tree_comparison = compare_trees(p["staging_tree"], p["package_tree"])
    release_exists = (
        p["package"].is_dir() and p["zip"].is_file() and p["checksum"].is_file()
    )
    release_manifest = p["package"] / "MANIFEST.json"
    release_validation_binding: dict[str, Any] = {"exists": False}
    if p["release_validation"].is_file() and release_manifest.is_file() and p["zip"].is_file():
        validation = read_json(p["release_validation"])
        release_validation_binding = {
            "exists": True,
            "valid_flag": validation.get("valid"),
            "manifest_declared_sha256": validation.get("manifest_sha256"),
            "manifest_actual_sha256": sha256(release_manifest),
            "manifest_matches": str(validation.get("manifest_sha256", "")).upper()
            == sha256(release_manifest),
            "zip_declared_sha256": validation.get("zip_sha256"),
            "zip_actual_sha256": sha256(p["zip"]),
            "zip_matches": str(validation.get("zip_sha256", "")).upper()
            == sha256(p["zip"]),
        }

    installer_binding: dict[str, Any] = {"exists": False}
    if p["installer_fixture"].is_file():
        fixture = read_json(p["installer_fixture"])
        installer_binding = {
            "exists": True,
            "valid_flag": fixture.get("valid"),
            "package_root": fixture.get("package_root"),
            "package_manifest_sha256": fixture.get("package_manifest_sha256"),
            "package_manifest_hash_present": bool(
                fixture.get("package_manifest_sha256")
            ),
            "package_manifest_hash_matches": bool(
                release_manifest.is_file()
                and str(fixture.get("package_manifest_sha256", "")).upper()
                == sha256(release_manifest)
            ),
            "passed_count": fixture.get("passed_count"),
            "failed_count": fixture.get("failed_count"),
        }

    corpus_current = (
        approved_reports["approved_v1"]["tm_comparison"]["exact"]
        and approved_reports["approved_v1"]["exact_expected_bytes"]
        and approved_reports["corpus_v1"]["exact_expected_bytes"]
        and all(binding["matches"] for binding in corpus_bindings)
    )
    font_approved_current = (
        approved_reports["approved_v2"]["tm_comparison"]["exact"]
        and approved_reports["approved_v2"]["main_dol_rows_exact"]
        and len(v2_extra_rows) == EXPECTED_MAIN_DOL_UNITS
    )
    codebook_closure_current = not missing_custom
    review_current = (
        reviewed_comparison["exact"]
        and not review_hash_mismatches
        and review_chain.get("valid") is True
        and int(review_chain.get("reviewed_units", -1)) == EXPECTED_TM_UNITS
    )
    ready_for_integration = all(
        (
            len(tm_by_id) == EXPECTED_TM_UNITS,
            csv_comparison["exact"],
            review_current,
            corpus_current,
            font_approved_current,
            codebook_closure_current,
            fit_ready,
            geometry_current,
            proof_current,
        )
    )
    ready_for_release = ready_for_integration and integration_current and staging_current

    required_refreshes: list[dict[str, Any]] = []
    for identifier, current, action in (
        (
            "review_chain",
            review_current,
            "Regenerate review_chain.json so batch_0001 reviewed/review-report hashes bind the geometry correction.",
        ),
        (
            "approved_corpus",
            corpus_current,
            "Run build_approved_corpus.py against the current final TM.",
        ),
        (
            "final_v2_approved_units",
            font_approved_current,
            "Recompose final_v2 approved_units from refreshed TM units plus the reviewed 926 main.dol rows.",
        ),
        (
            "fit_preflight_hash_binding",
            fit_ready,
            "Regenerate fit_preflight.json with explicit TM/codebook/catalog/boundary hashes.",
        ),
        (
            "text_font_integration_report",
            integration_current and ready_for_integration,
            "Regenerate the text/font integration report only after all upstream evidence is current.",
        ),
        (
            "public_release",
            release_exists and release_tree_comparison["equal"] and ready_for_release,
            "Rebuild package, ZIP and checksum from current staging.",
        ),
        (
            "release_validation",
            bool(
                release_tree_comparison["equal"]
                and release_validation_binding.get("valid_flag") is True
                and release_validation_binding.get("manifest_matches")
                and release_validation_binding.get("zip_matches")
            ),
            "Run validate_final_release.py against the rebuilt package/ZIP/checksum.",
        ),
        (
            "installer_fixture",
            bool(
                release_tree_comparison["equal"]
                and installer_binding.get("valid_flag") is True
                and installer_binding.get("package_manifest_hash_matches")
            ),
            "Run the installer fixture against the rebuilt package and record package_manifest_sha256.",
        ),
    ):
        if not current:
            required_refreshes.append({"id": identifier, "action": action})

    report = {
        "schema": "arf-final-release-refresh-dependency-audit-v1",
        "read_only_except_output_report": True,
        "root": str(root),
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "current_artifacts": {
            name: artifact(path, root)
            for name, path in p.items()
            if path.is_file()
        },
        "translation_memory": {
            "approved_units": len(tm_by_id),
            "json_csv": csv_comparison,
            "reviewed_batches_semantic_comparison": reviewed_comparison,
            "geometry_tm_id": GEOMETRY_TM_ID,
            "geometry_translation_ko": geometry_tm.get("translation_ko")
            if geometry_tm
            else None,
        },
        "review_chain": {
            "declared_valid": review_chain.get("valid"),
            "hash_mismatch_count": len(review_hash_mismatches),
            "hash_mismatches": review_hash_mismatches,
            "current": review_current,
        },
        "approved_font_inputs": approved_reports,
        "corpus_manifest_bindings": corpus_bindings,
        "font_codebook_closure": {
            "assigned_characters": len(codebook_chars),
            "required_custom_characters": len(required_custom),
            "missing_required_count": len(missing_custom),
            "missing_required": missing_custom,
            "unused_assigned_count": len(unused_codebook),
            "current_text_encodable_without_font_rebuild": not missing_custom,
        },
        "fit_preflight": {
            "artifact": artifact(p["fit"], root),
            "post_geometry_artifact": artifact(p["post_geometry_fit"], root),
            "byte_identical": p["fit"].read_bytes()
            == p["post_geometry_fit"].read_bytes(),
            "declared_safe": fit.get("safe_for_fixed_table_insertion"),
            "matched_table_fields": fit.get("matched_table_fields"),
            "hash_bindings": fit_bindings,
            "current": fit_ready,
        },
        "geometry_regression": {
            "correction_artifact": artifact(p["geometry_correction"], root),
            "repair_validation_artifact": artifact(p["geometry_repair"], root),
            "audit_bindings": geometry_audit_bindings,
            "current": geometry_current,
        },
        "system_application": {
            "artifact": artifact(p["proof"], root),
            "payload_hash_mismatch_count": len(proof_payload_mismatches),
            "payload_hash_mismatches": proof_payload_mismatches,
            "current": proof_current,
        },
        "staging": {
            "manifest": artifact(p["staging_manifest"], root),
            "input_bindings": staging_bindings,
            "current": staging_current,
        },
        "text_font_integration_report": {
            "artifact": artifact(p["integration"], root),
            "artifact_mismatch_count": len(integration_artifact_mismatches),
            "artifact_mismatches": integration_artifact_mismatches,
            "current": integration_current,
        },
        "existing_release": {
            "release_artifacts_exist": release_exists,
            "staging_tree_comparison": release_tree_comparison,
            "release_validation_binding": release_validation_binding,
            "installer_fixture_binding": installer_binding,
        },
        "readiness": {
            "ready_for_text_font_integration_report": ready_for_integration,
            "ready_for_public_release_build": ready_for_release,
            "existing_public_release_matches_current_staging": release_tree_comparison[
                "equal"
            ],
            "required_refresh_count": len(required_refreshes),
            "required_refreshes": required_refreshes,
        },
        "valid": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "sha256": sha256(output),
                "ready_for_text_font_integration_report": ready_for_integration,
                "ready_for_public_release_build": ready_for_release,
                "required_refresh_count": len(required_refreshes),
            },
            ensure_ascii=False,
        )
    )
    return 1 if args.require_ready and not ready_for_release else 0


if __name__ == "__main__":
    raise SystemExit(main())
