#!/usr/bin/env python3
"""Diagnose source-boundary mismatches between the TM and table catalogs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


RAW_CONTROL_RE = re.compile(r"<\$([0-9A-Fa-f]{2,})>")


def canonicalize(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        raw = bytes.fromhex(match.group(1))
        return f"<${raw[0]:02X}>" + raw[1:].decode("ascii")

    return RAW_CONTROL_RE.sub(replace, text)


def schema_from_locator(locator: str) -> str:
    leaf = locator.rsplit(":", 1)[-1]
    return Path(leaf).stem


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fit_report", type=Path)
    parser.add_argument("catalog_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = json.loads(args.fit_report.read_text(encoding="utf-8"))
    catalogs: dict[str, list[dict[str, object]]] = {}
    for path in args.catalog_dir.glob("*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        catalogs[path.stem] = [
            {
                "table_unit_id": unit.get("id"),
                "source_text": canonicalize(str(unit.get("source_text", ""))),
                "capacity": unit.get("capacity"),
                "in_place_capacity": unit.get("in_place_capacity"),
            }
            for unit in document.get("units", [])
            if unit.get("source_text")
        ]
    results = []
    for unmatched in report["unmatched_system_units"]:
        locator = str(unmatched["sample_contexts"][0]["logical_locator"])
        schema = schema_from_locator(locator)
        source = str(unmatched["source_text"])
        candidates = []
        for unit in catalogs.get(schema, []):
            table_source = str(unit["source_text"])
            if source in table_source or table_source in source:
                candidates.append(unit)
        results.append(
            {
                "tm_id": unmatched["tm_id"],
                "locator": locator,
                "schema": schema,
                "source_text": source,
                "translation_ko": unmatched["translation_ko"],
                "substring_candidate_count": len(candidates),
                "substring_candidates": candidates[:20],
            }
        )
    output = {
        "schema": "arf-unmatched-table-boundary-analysis-v1",
        "input_unmatched_count": len(results),
        "with_single_substring_candidate": sum(
            item["substring_candidate_count"] == 1 for item in results
        ),
        "with_multiple_substring_candidates": sum(
            item["substring_candidate_count"] > 1 for item in results
        ),
        "with_no_substring_candidate": sum(
            item["substring_candidate_count"] == 0 for item in results
        ),
        "units": results,
    }
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {key: output[key] for key in output if key != "units"}, ensure_ascii=False
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
