#!/usr/bin/env python3
"""Combine pinned, applied component audits into the canonical ARF boundary map.

The canonical document is only emitted when every pinned component is resolved,
its application report still hashes the current reviewed batch, and the reviewed
text/metadata agree with the audited clean table-field boundary.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "work/translation/boundary_audit/canonical_system_boundary_audit.json"
SPECS = (
    (
        "work/translation/boundary_audit/batches_0001_0002.json",
        "E47BA47E1B2A33940EB08EFFFF1E313FD6ACC4F23D63C5219680D63DBAEE80C7",
        "work/translation/boundary_audit/application_report.json",
    ),
    (
        "work/translation/boundary_audit/batches_0003_0004.json",
        "8500248960597E9A7A656F14FD07010A923C0B60544B1D1478E8B497900BDB5C",
        "work/translation/boundary_audit/application_report_0003_0004.json",
    ),
    (
        "work/translation/boundary_audit/batch_0005.json",
        "4776B6BB8042A707C9A2E3ADDEE08520396BF52B54E88ED0D72989936BA7339E",
        "work/translation/boundary_audit/application_report_0005.json",
    ),
    (
        "work/translation/boundary_audit/batch_0006.json",
        "DE12AA2273139430E54DF9A7FE2024E4CF3C33ACA0FFE6D08CDC0684584B5E7F",
        "work/translation/boundary_audit/application_report_0006.json",
    ),
    (
        "work/translation/boundary_audit/batch_0007.json",
        "8A04559A15EFAC784BACDA52E2B68B3AE94B0C157BB956AD731D3D3DF502DD42",
        "work/translation/boundary_audit/application_report_0007.json",
    ),
    (
        "work/translation/boundary_audit/batch_0008.json",
        "19CEF06A3A04E3E74F6023D3C0D1528D7A6F916B7FB36C0C3BD6F7E1B4C7B511",
        "work/translation/boundary_audit/application_report_0008.json",
    ),
    (
        "work/translation/boundary_audit/batch_0011.json",
        "E52E112E8C285A41D68DEF26D5454A90480FC36AC449CD019D9844474620D3D1",
        "work/translation/boundary_audit/application_report_0011.json",
    ),
    (
        "work/translation/boundary_audit/final_remaining_system.json",
        "32BBCE13CFE1756FE0AF572228F75EFF946007CFB19CD0F9273E5BF18529A1A5",
        "work/translation/boundary_audit/application_report_final_remaining.json",
    ),
)
EXPECTED_AUDITED_TM_UNITS = 720
EXPECTED_LINKED_TABLE_UNITS = 727
EXPECTED_REVIEWED_BATCHES = 22


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    components = []
    units = []
    tm_ids: set[str] = set()
    table_unit_ids: set[str] = set()
    batches: list[str] = []
    seen_batches: set[str] = set()
    for relative, expected_hash, application_relative in SPECS:
        path = ROOT / relative
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"component audit hash mismatch for {relative}: "
                f"{actual_hash} != {expected_hash}"
            )
        audit = json.loads(path.read_text(encoding="utf-8"))
        if audit.get("translation_engine_policy") != "Codex internal models only":
            raise ValueError(f"component policy mismatch: {relative}")
        if audit.get("external_translation_models_or_apis_used") is not False:
            raise ValueError(f"external translation recorded in component: {relative}")
        summary = audit.get("summary", {})
        if int(summary.get("ambiguous_tm_units", -1)) != 0:
            raise ValueError(f"ambiguous TM units remain in {relative}")
        if int(summary.get("unmatched_tm_units", -1)) != 0:
            raise ValueError(f"unmatched TM units remain in {relative}")
        if int(summary.get("resolved_tm_units", -1)) != len(audit.get("units", [])):
            raise ValueError(f"resolved/unit count mismatch in {relative}")

        component_batches = [str(item) for item in audit["scope"]["reviewed_batches"]]
        duplicate_batches = sorted(set(component_batches) & seen_batches)
        if duplicate_batches:
            raise ValueError(
                f"reviewed batches repeated across components: {duplicate_batches}"
            )
        seen_batches.update(component_batches)

        application_path = ROOT / application_relative
        application = json.loads(application_path.read_text(encoding="utf-8"))
        if str(application.get("audit_sha256", "")).upper() != actual_hash:
            raise ValueError(f"application audit hash mismatch: {application_relative}")
        if int(application.get("audited_units", -1)) != len(audit["units"]):
            raise ValueError(f"application unit count mismatch: {application_relative}")
        if application.get("translation_engine_policy") != "Codex internal models only":
            raise ValueError(f"application policy mismatch: {application_relative}")
        if application.get("external_translation_models_or_apis_used") is not False:
            raise ValueError(f"external translation recorded: {application_relative}")

        reviewed_by_id: dict[str, tuple[str, dict[str, object]]] = {}
        reviewed_hashes: dict[str, str] = {}
        for batch_file in component_batches:
            batch_name = Path(batch_file).stem
            reviewed_path = ROOT / "work/translation/reviewed" / f"{batch_name}.jsonl"
            reviewed_hash = sha256(reviewed_path)
            application_batch = application.get("batches", {}).get(batch_name)
            if not isinstance(application_batch, dict):
                raise ValueError(
                    f"application missing reviewed batch {batch_name}: "
                    f"{application_relative}"
                )
            if str(application_batch.get("reviewed_sha256", "")).upper() != reviewed_hash:
                raise ValueError(
                    f"reviewed batch changed after boundary application: {batch_name}"
                )
            reviewed_hashes[batch_name] = reviewed_hash
            for record in read_jsonl(reviewed_path):
                tm_id = str(record["tm_id"])
                if tm_id in reviewed_by_id:
                    raise ValueError(
                        f"duplicate TM ID in component reviewed batches: {tm_id}"
                    )
                reviewed_by_id[tm_id] = (batch_name, record)

        adjustment_after = {
            str(item["tm_id"]): str(item["after"])
            for item in application.get("adjustments", [])
        }
        components.append(
            {
                "path": relative,
                "sha256": actual_hash,
                "application_report": application_relative,
                "application_report_sha256": sha256(application_path),
                "reviewed_batches": component_batches,
                "reviewed_batch_sha256": reviewed_hashes,
                "reviewed_state_verified": True,
                "audited_tm_units": summary["resolved_tm_units"],
                "linked_table_units": summary["linked_table_units"],
            }
        )
        batches.extend(component_batches)
        for unit in audit["units"]:
            tm_id = str(unit["tm_id"])
            if tm_id in tm_ids:
                raise ValueError(f"duplicate TM ID across component audits: {tm_id}")
            tm_ids.add(tm_id)
            if unit.get("status") != "resolved":
                raise ValueError(f"unresolved canonical boundary unit: {tm_id}")
            reviewed_pair = reviewed_by_id.get(tm_id)
            if reviewed_pair is None:
                raise ValueError(f"audited TM ID absent from reviewed batch: {tm_id}")
            reviewed_batch, reviewed = reviewed_pair
            if str(reviewed.get("source_text")) != str(
                unit.get("corrupt_scanner_source_text")
            ):
                raise ValueError(f"reviewed source differs from component: {tm_id}")
            reviewed_boundary = reviewed.get("boundary_audit")
            if not isinstance(reviewed_boundary, dict):
                raise ValueError(f"boundary metadata absent from reviewed unit: {tm_id}")
            for field in ("clean_source_text", "table_unit_ids", "anomaly_type"):
                if reviewed_boundary.get(field) != unit.get(field):
                    raise ValueError(
                        f"reviewed boundary metadata mismatch for {tm_id}: {field}"
                    )
            table_specific_only = (
                unit.get("application_mode") == "table_specific_only"
            )
            if table_specific_only:
                if reviewed_boundary.get("application_mode") != "table_specific_only":
                    raise ValueError(
                        f"table-specific application metadata missing for {tm_id}"
                    )
                if reviewed_boundary.get("table_specific_translation_ko") != unit.get(
                    "table_specific_translation_ko"
                ):
                    raise ValueError(
                        f"table-specific translation metadata mismatch for {tm_id}"
                    )
                expected_translation = str(
                    unit["approved_translation_before_boundary_audit"]
                )
            else:
                expected_translation = adjustment_after.get(
                    tm_id, str(unit["clean_translation_ko"])
                )
            reviewed_translation = str(reviewed.get("translation_ko") or "")
            if reviewed_translation != expected_translation:
                raise ValueError(
                    f"reviewed translation differs from applied audit for {tm_id}"
                )
            for table_id in unit["table_unit_ids"]:
                table_id = str(table_id)
                if table_id in table_unit_ids:
                    raise ValueError(
                        f"duplicate table unit across component audits: {table_id}"
                    )
                table_unit_ids.add(table_id)
            canonical_unit = dict(unit)
            component_translation = str(unit["clean_translation_ko"])
            if table_specific_only:
                canonical_unit["reviewed_override_applied"] = False
                canonical_unit["table_specific_only"] = True
                canonical_unit["reviewed_tm_translation_preserved"] = True
            elif component_translation != reviewed_translation:
                canonical_unit["component_clean_translation_ko"] = component_translation
                canonical_unit["clean_translation_ko"] = reviewed_translation
                canonical_unit["reviewed_override_applied"] = True
            else:
                canonical_unit["reviewed_override_applied"] = False
            canonical_unit["reviewed_translation_ko"] = reviewed_translation
            canonical_unit["reviewed_batch"] = f"{reviewed_batch}.jsonl"
            units.append(canonical_unit)

    if len(units) != EXPECTED_AUDITED_TM_UNITS:
        raise ValueError(
            f"expected {EXPECTED_AUDITED_TM_UNITS} audited TM units, found {len(units)}"
        )
    if len(table_unit_ids) != EXPECTED_LINKED_TABLE_UNITS:
        raise ValueError(
            f"expected {EXPECTED_LINKED_TABLE_UNITS} linked table units, "
            f"found {len(table_unit_ids)}"
        )
    if len(seen_batches) != EXPECTED_REVIEWED_BATCHES:
        raise ValueError(
            f"expected {EXPECTED_REVIEWED_BATCHES} reviewed batches, "
            f"found {len(seen_batches)}"
        )

    document = {
        "schema": "arf-system-table-boundary-audit-canonical-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "scope": {
            "reviewed_batches": sorted(batches),
            "audited_tm_units": len(units),
            "linked_table_units": len(table_unit_ids),
            "reviewed_state_verified": True,
        },
        "components": components,
        "summary": {
            "resolved_tm_units": len(units),
            "ambiguous_tm_units": 0,
            "unmatched_tm_units": 0,
            "linked_table_units": len(table_unit_ids),
            "reviewed_translation_mismatches": 0,
        },
        "units": sorted(units, key=lambda item: str(item["tm_id"])),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "sha256": sha256(OUTPUT),
                "audited_tm_units": len(units),
                "linked_table_units": len(table_unit_ids),
                "ambiguous_tm_units": 0,
                "unmatched_tm_units": 0,
                "reviewed_state_verified": True,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
