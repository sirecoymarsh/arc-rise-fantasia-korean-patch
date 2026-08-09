"""Apply the audited shop-name compaction caused by corrected table geometry."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TM_ID = "ARF-TM-7983B232461623CDF50F"
EXPECTED_SOURCE = "▼ ペネロペの仕立屋"
BEFORE = "▼ 페넬로페의 양장점"
AFTER = "▼ 페넬로페 양장점"
CAPACITY = 20
MARKER = (
    "[fixed-field-geometry] Internal-model compact rewrite after independent "
    "audit corrected shop.name capacity from 21 to 20 bytes."
)
REVIEWED = ROOT / "work" / "translation" / "reviewed" / "batch_0001.jsonl"
DRAFT = ROOT / "work" / "translation" / "drafts" / "batch_0001.jsonl"
REVIEW = ROOT / "work" / "translation" / "reviews" / "batch_0001_review.json"
FINAL_JSON = ROOT / "work" / "translation" / "final" / "translation_memory_draft.json"
FINAL_CSV = ROOT / "work" / "translation" / "final" / "translation_memory_draft.csv"
CODEBOOK = ROOT / "work" / "font" / "final_v2" / "codebook.json"
ENCODER = ROOT / "work" / "research" / "encode_custom_euc28.py"
AUDITS = (
    ROOT / "work" / "runtime_validation" / "fixed_schema_boundary_audit.json",
    ROOT / "work" / "runtime_validation" / "fixed_table_geometry_audit.json",
)
OUTPUT = ROOT / "work" / "translation" / "fixed_field_fit" / "geometry_regression_correction.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def update_unit(unit: dict[str, object]) -> None:
    if str(unit.get("source_text")) != EXPECTED_SOURCE:
        raise ValueError(f"source mismatch for {TM_ID}")
    current = str(unit.get("translation_ko") or "")
    if current not in {BEFORE, AFTER}:
        raise ValueError(f"unexpected target for {TM_ID}: {current!r}")
    unit["translation_ko"] = AFTER
    notes = str(unit.get("notes") or "")
    if MARKER not in notes:
        unit["notes"] = (notes + (" " if notes else "") + MARKER).strip()


def load_encoder():
    spec = importlib.util.spec_from_file_location("arf_geometry_encoder", ENCODER)
    if spec is None or spec.loader is None:
        raise RuntimeError(ENCODER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    encoder = load_encoder()
    codebook = json.loads(CODEBOOK.read_text(encoding="utf-8"))
    before_bytes = encoder.encode_text(BEFORE, codebook)
    after_bytes = encoder.encode_text(AFTER, codebook)
    if len(before_bytes) + 1 <= CAPACITY or len(after_bytes) + 1 > CAPACITY:
        raise ValueError("shop compaction precondition failed")

    reviewed = load_jsonl(REVIEWED)
    matched = [row for row in reviewed if str(row.get("tm_id")) == TM_ID]
    if len(matched) != 1:
        raise ValueError(f"reviewed unit cardinality: {len(matched)}")
    update_unit(matched[0])
    write_jsonl(REVIEWED, reviewed)

    draft_by_id = {str(row["tm_id"]): row for row in load_jsonl(DRAFT)}
    modified = sum(
        str(row.get("translation_ko") or "")
        != str(draft_by_id[str(row["tm_id"])].get("translation_ko") or "")
        for row in reviewed
    )
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    review["modified_units"] = modified
    review["unchanged_units"] = len(reviewed) - modified
    review["fixed_field_geometry_correction"] = {
        "status": "applied",
        "tm_id": TM_ID,
        "before": BEFORE,
        "after": AFTER,
        "capacity": CAPACITY,
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
    }
    if isinstance(review.get("final_change_summary"), dict):
        review["final_change_summary"]["final_modified_units_against_original_draft"] = modified
        review["final_change_summary"]["final_unchanged_units_against_original_draft"] = len(reviewed) - modified
    review.setdefault("hashes", {})["reviewed_sha256"] = sha256(REVIEWED)
    REVIEW.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    final_tm = json.loads(FINAL_JSON.read_text(encoding="utf-8"))
    final_matches = [row for row in final_tm["units"] if str(row.get("tm_id")) == TM_ID]
    if len(final_matches) != 1:
        raise ValueError(f"final TM unit cardinality: {len(final_matches)}")
    update_unit(final_matches[0])
    FINAL_JSON.write_text(json.dumps(final_tm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with FINAL_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    csv_matches = [row for row in rows if row.get("tm_id") == TM_ID]
    if len(csv_matches) != 1:
        raise ValueError(f"final CSV unit cardinality: {len(csv_matches)}")
    csv_matches[0]["translation_ko"] = AFTER
    csv_matches[0]["notes"] = str(final_matches[0].get("notes") or "")
    with FINAL_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    audit_records = []
    for path in AUDITS:
        if path.exists():
            audit_records.append(
                {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path)}
            )
    report = {
        "schema": "arf-fixed-field-geometry-correction-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "audits": audit_records,
        "correction": {
            "tm_id": TM_ID,
            "source_text": EXPECTED_SOURCE,
            "before": BEFORE,
            "after": AFTER,
            "before_bytes": len(before_bytes),
            "after_bytes": len(after_bytes),
            "capacity_including_nul": CAPACITY,
            "fits_after": len(after_bytes) + 1 <= CAPACITY,
        },
        "artifacts": {
            "reviewed_batch_sha256": sha256(REVIEWED),
            "review_report_sha256": sha256(REVIEW),
            "final_tm_sha256": sha256(FINAL_JSON),
            "final_tm_csv_sha256": sha256(FINAL_CSV),
        },
        "valid": True,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
