#!/usr/bin/env python3
"""Build the final deterministic scanner/table boundary audit.

The generic NUL scanner occasionally starts inside a structured table field or
includes bytes from the preceding record structure.  This tool consumes the
preserved fit-preflight discovery list, proves every mapping by exact byte-range
overlap against the structured catalogs, and emits the clean field text and
reviewed Korean text to use for insertion.

No translation service is called.  Most target repairs remove an identical
scanner-only prefix already copied into the reviewed target.  The small set of
missing-source-prefix repairs is explicitly pinned below after internal-model
review.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEMORY_PATH = ROOT / "work/translation/final/translation_memory_draft.json"
DISCOVERY_PATH = (
    ROOT
    / "work/translation/boundary_audit/remaining_system_discovery_preflight.json"
)
TEXT_CATALOG_PATH = ROOT / "work/catalog/text_v2/text_catalog.json"
CATALOG_DIR = ROOT / "work/research/table_agent/catalogs"
CODEBOOK_PATH = ROOT / "work/font/final_v1/codebook.json"
ENCODER_PATH = ROOT / "work/research/encode_custom_euc28.py"
OUTPUT_PATH = ROOT / "work/translation/boundary_audit/final_remaining_system.json"

EXPECTED_DISCOVERY_TM_UNITS = 417
EXPECTED_TM_UNITS = 418
EXPECTED_TABLE_UNITS = 418
NESTED_TM_ID = "ARF-TM-B9E4C48F9B1EA3670863"
NESTED_OCCURRENCE_ID = "ARF-9436C9070C3E005687B8"
NESTED_TABLE_UNIT_ID = "ability:218:name"
NESTED_CLEAN_TRANSLATION = "최속 행동"
EXPECTED_BATCHES = (
    "batch_0009.jsonl",
    "batch_0010.jsonl",
    "batch_0012.jsonl",
    "batch_0013.jsonl",
    "batch_0014.jsonl",
    "batch_0015.jsonl",
    "batch_0016.jsonl",
    "batch_0017.jsonl",
    "batch_0018.jsonl",
    "batch_0019.jsonl",
    "batch_0020.jsonl",
    "batch_0021.jsonl",
    "batch_0022.jsonl",
)

# These are semantic boundary recoveries, not automatic retranslations.  Four
# scanner records began inside their actual title/name; the fifth copied a
# scanner-only control/garbage prefix whose visible middle byte was translated.
TRANSLATION_OVERRIDES = {
    "ARF-TM-5F37310207C0E9DA664E": "처음 만났을 무렵",
    "ARF-TM-6595BF8415F3C13A8EEB": "속성 방어구 10",
    "ARF-TM-94B7760C24DCD8A0FF2D": "속성 내성",
    "ARF-TM-AB4CCCC12089626CCB9D": "내게 부족한 것",
    "ARF-TM-C6FD81B3BD766D8D400A": "가련한 전사",
}

RAW_CONTROL_RE = re.compile(r"<\$([0-9A-Fa-f]{2,})>")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_encoder(path: Path):
    spec = importlib.util.spec_from_file_location("arf_remaining_boundary_encoder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load encoder: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonicalize_table_controls(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        raw_hex = match.group(1)
        if len(raw_hex) % 2:
            raise ValueError(f"odd raw control token: {match.group(0)!r}")
        raw = bytes.fromhex(raw_hex)
        if not raw:
            raise ValueError("empty raw control token")
        return f"<${raw[0]:02X}>" + raw[1:].decode("ascii")

    return RAW_CONTROL_RE.sub(replace, text)


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    memory = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
    discovery = json.loads(DISCOVERY_PATH.read_text(encoding="utf-8"))
    text_catalog = json.loads(TEXT_CATALOG_PATH.read_text(encoding="utf-8"))
    codebook = json.loads(CODEBOOK_PATH.read_text(encoding="utf-8"))
    encoder = load_encoder(ENCODER_PATH)

    discovery_units = discovery.get("unmatched_system_units", [])
    if (
        int(discovery.get("unmatched_system_tm_count", -1))
        != EXPECTED_DISCOVERY_TM_UNITS
    ):
        raise ValueError("preserved discovery count is not 417")
    discovery_by_id = {
        str(item["tm_id"]): item for item in discovery_units
    }
    discovery_ids = set(discovery_by_id)
    if len(discovery_ids) != EXPECTED_DISCOVERY_TM_UNITS:
        raise ValueError("duplicate or missing IDs in preserved discovery")

    tm_by_id = {str(item["tm_id"]): item for item in memory["units"]}
    occurrence_by_id = {
        str(item["id"]): item for item in text_catalog.get("records", [])
    }

    reviewed_by_id: dict[str, tuple[str, dict[str, object]]] = {}
    reviewed_hashes: dict[str, str] = {}
    for filename in EXPECTED_BATCHES:
        path = ROOT / "work/translation/reviewed" / filename
        reviewed_hashes[filename] = sha256(path)
        for record in read_jsonl(path):
            tm_id = str(record["tm_id"])
            if tm_id in reviewed_by_id:
                raise ValueError(f"duplicate reviewed TM ID: {tm_id}")
            reviewed_by_id[tm_id] = (filename, record)

    catalogs_by_basename: dict[str, list[tuple[Path, dict[str, object]]]] = (
        defaultdict(list)
    )
    for catalog_path in sorted(CATALOG_DIR.glob("*.json")):
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        source_path = Path(str(catalog["source_path"]))
        catalogs_by_basename[source_path.name].append((catalog_path, catalog))

    units: list[dict[str, object]] = []
    table_refs: set[str] = set()
    anomaly_counts: Counter[str] = Counter()
    repair_counts: Counter[str] = Counter()
    batch_counts: Counter[str] = Counter()
    fit_counts: Counter[str] = Counter()

    for tm_id in sorted(discovery_ids):
        tm = tm_by_id.get(tm_id)
        if tm is None:
            raise ValueError(f"discovery TM absent from merged memory: {tm_id}")
        if tm.get("review_status") != "approved":
            raise ValueError(f"discovery TM is not approved: {tm_id}")
        if tm.get("primary_surface") != "system_database":
            raise ValueError(f"discovery TM is not system_database: {tm_id}")
        reviewed_pair = reviewed_by_id.get(tm_id)
        if reviewed_pair is None:
            raise ValueError(f"discovery TM absent from expected reviewed batches: {tm_id}")
        batch_name, reviewed = reviewed_pair
        if str(reviewed.get("source_text")) != str(tm["source_text"]):
            raise ValueError(f"reviewed/merged source mismatch: {tm_id}")
        if str(reviewed.get("translation_ko")) != str(tm["translation_ko"]):
            raise ValueError(f"reviewed/merged target mismatch: {tm_id}")
        batch_counts[batch_name] += 1

        occurrence_ids = [str(value) for value in tm.get("occurrence_ids", [])]
        if len(occurrence_ids) != 1:
            raise ValueError(f"expected one occurrence for boundary TM {tm_id}")
        occurrence = occurrence_by_id.get(occurrence_ids[0])
        if occurrence is None:
            raise ValueError(f"missing occurrence {occurrence_ids[0]} for {tm_id}")
        basename = str(occurrence.get("leaf_name") or "")
        scanner_start = int(occurrence["offset"])
        scanner_raw = bytes.fromhex(str(occurrence["raw_hex"]))
        scanner_end = scanner_start + len(scanner_raw)
        if int(occurrence["byte_length"]) != len(scanner_raw):
            raise ValueError(f"scanner byte length mismatch: {tm_id}")

        candidates: list[
            tuple[Path, dict[str, object], dict[str, object], int]
        ] = []
        for catalog_path, catalog in catalogs_by_basename.get(basename, []):
            for table_unit in catalog.get("units", []):
                table_start = int(table_unit["offset"])
                table_raw = bytes.fromhex(str(table_unit["raw_hex"]))
                table_end = table_start + len(table_raw)
                overlap = max(
                    0,
                    min(scanner_end, table_end) - max(scanner_start, table_start),
                )
                if overlap:
                    candidates.append((catalog_path, catalog, table_unit, overlap))
        if len(candidates) != 1:
            raise ValueError(
                f"expected exactly one overlap for {tm_id}, got {len(candidates)}"
            )
        catalog_path, catalog, table_unit, overlap = candidates[0]
        table_id = str(table_unit["id"])
        if table_id in table_refs:
            raise ValueError(f"duplicate table mapping: {table_id}")
        table_refs.add(table_id)

        source_path = Path(str(catalog["source_path"]))
        source_data = source_path.read_bytes()
        source_hash = sha256(source_path)
        if source_hash.lower() != str(catalog["source_sha256"]).lower():
            raise ValueError(f"catalog source hash mismatch: {catalog_path}")
        if source_hash.lower() != str(occurrence["leaf_sha256"]).lower():
            raise ValueError(f"scanner/catalog leaf hash mismatch: {tm_id}")
        table_start = int(table_unit["offset"])
        table_raw = bytes.fromhex(str(table_unit["raw_hex"]))
        table_end = table_start + len(table_raw)
        if source_data[scanner_start:scanner_end] != scanner_raw:
            raise ValueError(f"scanner raw slice mismatch: {tm_id}")
        if source_data[table_start:table_end] != table_raw:
            raise ValueError(f"table raw slice mismatch: {tm_id}")

        discovery_unit = discovery_by_id[tm_id]
        corrupt_source = str(tm["source_text"])
        if str(discovery_unit.get("source_text")) != corrupt_source:
            raise ValueError(f"preserved discovery source changed: {tm_id}")
        clean_source = canonicalize_table_controls(str(table_unit["source_text"]))
        # The preserved discovery is the immutable pre-application state.  The
        # reviewed batch and merged memory may already contain the clean target
        # when this builder is rerun to refresh provenance hashes, so derive the
        # repair from the preserved target rather than from the mutable current
        # reviewed state.
        approved_before = str(discovery_unit["translation_ko"])
        current_target = str(tm["translation_ko"])
        pre_len = max(0, table_start - scanner_start)
        missing_prefix_len = max(0, scanner_start - table_start)
        if pre_len and scanner_end == table_end:
            anomaly_type = "scanner_included_pre_field_structure_bytes"
            if not corrupt_source.endswith(clean_source):
                raise ValueError(f"source suffix relation failed: {tm_id}")
            corrupt_prefix = (
                corrupt_source[: -len(clean_source)] if clean_source else corrupt_source
            )
            if tm_id in TRANSLATION_OVERRIDES:
                clean_target = TRANSLATION_OVERRIDES[tm_id]
                translation_repair = "internal_review_semantic_prefix_removal"
            else:
                if not approved_before.startswith(corrupt_prefix):
                    raise ValueError(f"reviewed target did not copy corrupt prefix: {tm_id}")
                clean_target = approved_before[len(corrupt_prefix) :]
                translation_repair = "remove_copied_structural_prefix"
        elif missing_prefix_len and scanner_end == table_end:
            anomaly_type = "scanner_skipped_field_prefix"
            if not clean_source.endswith(corrupt_source):
                raise ValueError(f"clean source suffix relation failed: {tm_id}")
            clean_target = TRANSLATION_OVERRIDES.get(tm_id, approved_before)
            translation_repair = (
                "internal_review_semantic_prefix_recovery"
                if tm_id in TRANSLATION_OVERRIDES
                else "reviewed_target_already_recovers_missing_prefix"
            )
        else:
            raise ValueError(
                f"unsupported overlap geometry for {tm_id}: "
                f"scanner={scanner_start}:{scanner_end}, table={table_start}:{table_end}"
            )
        if not clean_target:
            raise ValueError(f"empty clean target after boundary repair: {tm_id}")
        if current_target not in {approved_before, clean_target}:
            raise ValueError(
                f"current reviewed target is neither preserved nor repaired: {tm_id}"
            )

        capacity = int(
            table_unit.get("capacity", table_unit.get("in_place_capacity", 0))
        )
        encoded = encoder.encode_text(clean_target, codebook)
        required_with_nul = len(encoded) + 1
        if b"\0" in encoded:
            raise ValueError(f"encoded NUL in clean target: {tm_id}")
        fit_status = (
            "verified_fit" if required_with_nul <= capacity else "fixed_overflow"
        )
        fit_counts[fit_status] += 1
        if fit_status != "verified_fit":
            raise ValueError(
                f"boundary repair does not fit fixed field {table_id}: "
                f"{required_with_nul}>{capacity}"
            )

        anomaly_counts[anomaly_type] += 1
        repair_counts[translation_repair] += 1
        units.append(
            {
                "tm_id": tm_id,
                "status": "resolved",
                "schema": str(catalog["schema"]),
                "logical_locator": str(occurrence["logical_locator"]),
                "corrupt_scanner_source_text": corrupt_source,
                "approved_translation_before_boundary_audit": approved_before,
                "table_unit_ids": [table_id],
                "clean_source_text": clean_source,
                "clean_translation_ko": clean_target,
                "translation_repair": translation_repair,
                "translation_changed": approved_before != clean_target,
                "capacity": capacity,
                "encoded_fit": {
                    "review_required": False,
                    "status": fit_status,
                    "encoded_bytes": len(encoded),
                    "encoded_hex": encoded.hex().upper(),
                    "required_with_nul": required_with_nul,
                    "max_payload_bytes": capacity - 1,
                    "nul_terminator_reserved": True,
                },
                "anomaly_type": anomaly_type,
                "evidence": [
                    {
                        "occurrence_id": str(occurrence["id"]),
                        "logical_locator": str(occurrence["logical_locator"]),
                        "scanner_offset": scanner_start,
                        "scanner_offset_hex": f"0x{scanner_start:X}",
                        "scanner_byte_length": len(scanner_raw),
                        "scanner_raw_hex": scanner_raw.hex().upper(),
                        "table_unit_id": table_id,
                        "table_offset": table_start,
                        "table_offset_hex": f"0x{table_start:X}",
                        "table_byte_length": len(table_raw),
                        "table_raw_hex": table_raw.hex().upper(),
                        "offset_delta_scanner_minus_table": scanner_start
                        - table_start,
                        "overlap_bytes": overlap,
                        "pre_field_structure_hex_in_scanner": (
                            scanner_raw[:pre_len].hex().upper() if pre_len else ""
                        ),
                        "missing_real_field_prefix_hex": (
                            table_raw[:missing_prefix_len].hex().upper()
                            if missing_prefix_len
                            else ""
                        ),
                        "raw_source_path": str(source_path),
                        "raw_source_sha256": source_hash.lower(),
                        "raw_source_sha256_verified": True,
                        "raw_field_bytes_verified": True,
                        "raw_scanner_bytes_verified": True,
                        "mapping_status": "exact_by_offset_overlap",
                    }
                ],
            }
        )

    # One source unit has two system occurrences with different structural
    # boundaries.  ``行動`` is an exact help-title field, but its second scanner
    # occurrence begins four bytes into the ability name ``最速行動``.  The
    # reviewed TM target must remain ``행동`` for help:0:title, so this entry is
    # an insertion-only table-specific override rather than a TM rewrite.
    nested_tm = tm_by_id[NESTED_TM_ID]
    nested_batch, nested_reviewed = reviewed_by_id[NESTED_TM_ID]
    if nested_batch != "batch_0022.jsonl":
        raise ValueError(f"unexpected nested-occurrence batch: {nested_batch}")
    if str(nested_tm["source_text"]) != "行動":
        raise ValueError("nested-occurrence source changed")
    if str(nested_tm["translation_ko"]) != "행동":
        raise ValueError("nested-occurrence reviewed translation changed")
    if str(nested_reviewed["translation_ko"]) != "행동":
        raise ValueError("nested-occurrence reviewed batch target changed")
    nested_occurrence = occurrence_by_id[NESTED_OCCURRENCE_ID]
    ability_candidates = [
        pair
        for pair in catalogs_by_basename["ability.bin"]
        if pair[0].name == "ability.json"
    ]
    if len(ability_candidates) != 1:
        raise ValueError("ability catalog is not unique")
    nested_catalog_path, nested_catalog = ability_candidates[0]
    nested_table = next(
        item
        for item in nested_catalog["units"]
        if str(item["id"]) == NESTED_TABLE_UNIT_ID
    )
    nested_source_path = Path(str(nested_catalog["source_path"]))
    nested_source_data = nested_source_path.read_bytes()
    nested_source_hash = sha256(nested_source_path)
    nested_scanner_start = int(nested_occurrence["offset"])
    nested_scanner_raw = bytes.fromhex(str(nested_occurrence["raw_hex"]))
    nested_scanner_end = nested_scanner_start + len(nested_scanner_raw)
    nested_table_start = int(nested_table["offset"])
    nested_table_raw = bytes.fromhex(str(nested_table["raw_hex"]))
    nested_table_end = nested_table_start + len(nested_table_raw)
    nested_overlap = max(
        0,
        min(nested_scanner_end, nested_table_end)
        - max(nested_scanner_start, nested_table_start),
    )
    if nested_overlap != len(nested_scanner_raw):
        raise ValueError("nested scanner suffix is not fully inside ability:218:name")
    if nested_source_data[nested_scanner_start:nested_scanner_end] != nested_scanner_raw:
        raise ValueError("nested scanner raw slice mismatch")
    if nested_source_data[nested_table_start:nested_table_end] != nested_table_raw:
        raise ValueError("nested table raw slice mismatch")
    if nested_source_hash.lower() != str(nested_catalog["source_sha256"]).lower():
        raise ValueError("nested ability source hash mismatch")
    if nested_source_hash.lower() != str(nested_occurrence["leaf_sha256"]).lower():
        raise ValueError("nested scanner/catalog leaf hash mismatch")
    nested_clean_source = canonicalize_table_controls(str(nested_table["source_text"]))
    if nested_clean_source != "最速行動" or not nested_clean_source.endswith(
        str(nested_tm["source_text"])
    ):
        raise ValueError("nested clean-source suffix relation failed")
    nested_capacity = int(nested_table["capacity"])
    nested_encoded = encoder.encode_text(NESTED_CLEAN_TRANSLATION, codebook)
    nested_required = len(nested_encoded) + 1
    if nested_required > nested_capacity or b"\0" in nested_encoded:
        raise ValueError("nested table-specific target does not fit")
    if NESTED_TABLE_UNIT_ID in table_refs:
        raise ValueError("nested table unit already mapped")
    table_refs.add(NESTED_TABLE_UNIT_ID)
    batch_counts[nested_batch] += 1
    anomaly_counts["scanner_skipped_field_prefix"] += 1
    repair_counts["table_specific_semantic_prefix_recovery"] += 1
    fit_counts["verified_fit"] += 1
    units.append(
        {
            "tm_id": NESTED_TM_ID,
            "status": "resolved",
            "schema": "ability",
            "logical_locator": str(nested_occurrence["logical_locator"]),
            "corrupt_scanner_source_text": str(nested_tm["source_text"]),
            "approved_translation_before_boundary_audit": str(
                nested_tm["translation_ko"]
            ),
            "table_unit_ids": [NESTED_TABLE_UNIT_ID],
            "clean_source_text": nested_clean_source,
            "clean_translation_ko": NESTED_CLEAN_TRANSLATION,
            "table_specific_translation_ko": NESTED_CLEAN_TRANSLATION,
            "application_mode": "table_specific_only",
            "translation_repair": "table_specific_semantic_prefix_recovery",
            "translation_changed": False,
            "table_specific_translation_differs_from_reviewed_tm": True,
            "capacity": nested_capacity,
            "encoded_fit": {
                "review_required": False,
                "status": "verified_fit",
                "encoded_bytes": len(nested_encoded),
                "encoded_hex": nested_encoded.hex().upper(),
                "required_with_nul": nested_required,
                "max_payload_bytes": nested_capacity - 1,
                "nul_terminator_reserved": True,
            },
            "anomaly_type": "scanner_skipped_field_prefix",
            "evidence": [
                {
                    "occurrence_id": NESTED_OCCURRENCE_ID,
                    "logical_locator": str(nested_occurrence["logical_locator"]),
                    "scanner_offset": nested_scanner_start,
                    "scanner_offset_hex": f"0x{nested_scanner_start:X}",
                    "scanner_byte_length": len(nested_scanner_raw),
                    "scanner_raw_hex": nested_scanner_raw.hex().upper(),
                    "table_unit_id": NESTED_TABLE_UNIT_ID,
                    "table_offset": nested_table_start,
                    "table_offset_hex": f"0x{nested_table_start:X}",
                    "table_byte_length": len(nested_table_raw),
                    "table_raw_hex": nested_table_raw.hex().upper(),
                    "offset_delta_scanner_minus_table": nested_scanner_start
                    - nested_table_start,
                    "overlap_bytes": nested_overlap,
                    "pre_field_structure_hex_in_scanner": "",
                    "missing_real_field_prefix_hex": nested_table_raw[
                        : nested_scanner_start - nested_table_start
                    ].hex().upper(),
                    "raw_source_path": str(nested_source_path),
                    "raw_source_sha256": nested_source_hash.lower(),
                    "raw_source_sha256_verified": True,
                    "raw_field_bytes_verified": True,
                    "raw_scanner_bytes_verified": True,
                    "mapping_status": "exact_nested_suffix_by_offset_overlap",
                    "coexisting_exact_occurrence": {
                        "occurrence_id": "ARF-037BE37E9EFFA460870B",
                        "logical_locator": "Sys/help.bin",
                        "table_unit_id": "help:0:title",
                        "uses_reviewed_tm_translation": True,
                    },
                }
            ],
        }
    )

    if len(units) != EXPECTED_TM_UNITS:
        raise ValueError(f"expected {EXPECTED_TM_UNITS} units, found {len(units)}")
    if len(table_refs) != EXPECTED_TABLE_UNITS:
        raise ValueError(
            f"expected {EXPECTED_TABLE_UNITS} table units, found {len(table_refs)}"
        )
    if set(batch_counts) != set(EXPECTED_BATCHES):
        raise ValueError(f"unexpected reviewed-batch set: {sorted(batch_counts)}")

    document = {
        "schema": "arf-system-table-boundary-audit-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "scope": {
            "reviewed_batches": list(EXPECTED_BATCHES),
            "expected_tm_units": EXPECTED_TM_UNITS,
            "audited_tm_units": len(units),
            "reviewed_batch_unit_counts": dict(sorted(batch_counts.items())),
            "reviewed_batch_sha256_before_application": reviewed_hashes,
        },
        "inputs": {
            "translation_memory": str(MEMORY_PATH.relative_to(ROOT)).replace("\\", "/"),
            "translation_memory_sha256": sha256(MEMORY_PATH),
            "discovery_preflight": str(DISCOVERY_PATH.relative_to(ROOT)).replace("\\", "/"),
            "discovery_preflight_sha256": sha256(DISCOVERY_PATH),
            "text_catalog": str(TEXT_CATALOG_PATH.relative_to(ROOT)).replace("\\", "/"),
            "text_catalog_sha256": sha256(TEXT_CATALOG_PATH),
            "table_catalog_dir": str(CATALOG_DIR.relative_to(ROOT)).replace("\\", "/"),
            "codebook": str(CODEBOOK_PATH.relative_to(ROOT)).replace("\\", "/"),
            "codebook_sha256": sha256(CODEBOOK_PATH),
        },
        "method": (
            "Each occurrence was linked only when its scanner byte range had "
            "exactly one offset overlap with a structured table field; the raw "
            "scanner slice, table slice, and whole source SHA-256 were verified. "
            "Substring candidates were never deciding evidence."
        ),
        "summary": {
            "resolved_tm_units": len(units),
            "ambiguous_tm_units": 0,
            "unmatched_tm_units": 0,
            "linked_table_units": len(table_refs),
            "anomaly_types": dict(sorted(anomaly_counts.items())),
            "translation_repairs": dict(sorted(repair_counts.items())),
            "translation_changes": sum(bool(item["translation_changed"]) for item in units),
            "encoded_fit_statuses": dict(sorted(fit_counts.items())),
            "encoded_fit_review_required": 0,
        },
        "action_lists": {
            "ambiguous_tm_ids": [],
            "unmatched_tm_ids": [],
            "overflow_tm_ids": [],
            "encoding_error_tm_ids": [],
        },
        "units": units,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(OUTPUT_PATH),
                "sha256": sha256(OUTPUT_PATH),
                "resolved_tm_units": len(units),
                "linked_table_units": len(table_refs),
                "ambiguous_tm_units": 0,
                "unmatched_tm_units": 0,
                "translation_changes": document["summary"]["translation_changes"],
                "encoded_fit_statuses": document["summary"]["encoded_fit_statuses"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
