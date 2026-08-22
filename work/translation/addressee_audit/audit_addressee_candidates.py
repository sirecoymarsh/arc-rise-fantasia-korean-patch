#!/usr/bin/env python3
"""Build a read-only, occurrence-bound audit corpus for multi-party BSCR dialogue.

This utility does not translate or modify the translation memory.  It joins the
original BSCR string order, per-line speaker-slot controls, catalog occurrence
IDs, and the current Korean TM so a Codex reviewer can judge addressees from a
whole scene instead of isolated source strings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


JA_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
TARGET_RE = re.compile(
    r"(?<![가-힣])(?:너는|너를|너에게|너한테|너도|너와|너랑|너희(?:들)?|넌|널|"
    r"네가|네게|네겐|니가|당신(?:은|을|에게|한테|도|들)?|"
    r"너|자네|그대|네놈|얘들아|여러분)(?![가-힣])"
)

SOURCE_RE = re.compile(
    r"(?:お前たち|おまえたち|君たち|キミたち|あなたたち|"
    r"お前|おまえ|おめー|君|きみ|キミ|あなた|貴方|あんた|貴様|そなた|てめえ)"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm_locator(value: str) -> str:
    return value.replace("\\", "/")


def is_speaker_token(raw: bytes) -> str | None:
    if len(raw) == 3 and raw[0] == 0x19:
        try:
            payload = raw[1:].decode("ascii")
        except UnicodeDecodeError:
            return None
        if re.fullmatch(r"[0-9A-Fa-f]{2}", payload):
            return payload.upper()
    return None


def looks_like_dialogue(text: str) -> bool:
    if not JA_RE.search(text):
        return False
    if re.fullmatch(r"[A-Za-z0-9_./\\:-]+", text):
        return False
    return True


def load_tm(tm_path: Path) -> tuple[dict[str, str], dict[str, str], dict[str, dict]]:
    document = json.loads(tm_path.read_text(encoding="utf-8"))
    by_occurrence: dict[str, str] = {}
    tm_id_by_occurrence: dict[str, str] = {}
    by_id: dict[str, dict] = {}
    for unit in document["units"]:
        tm_id = unit["tm_id"]
        by_id[tm_id] = unit
        ko = unit.get("translation_ko", "")
        for occurrence_id in unit.get("occurrence_ids", []):
            by_occurrence[occurrence_id] = ko
            tm_id_by_occurrence[occurrence_id] = tm_id
    return by_occurrence, tm_id_by_occurrence, by_id


def load_catalog(catalog_path: Path) -> tuple[dict[tuple[str, int], dict], dict[str, dict]]:
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    by_location: dict[tuple[str, int], dict] = {}
    by_id: dict[str, dict] = {}
    for record in document["records"]:
        rid = record["id"]
        by_id[rid] = record
        if record.get("extraction_mode") == "bscr_string_pool":
            key = (norm_locator(record["logical_locator"]), int(record["offset"]))
            by_location[key] = record
    return by_location, by_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    source_root = root / "work/disc_extracted/DATA/files"
    audit_path = root / "work/research/bscr_agent/full_audit.json"
    catalog_path = root / "work/catalog/text_v2/text_catalog.json"
    tm_path = root / "work/translation/final/translation_memory_draft.json"

    sys.path.insert(0, str(root / "work/research/bscr_agent"))
    from bscr_tool import parse_bscr  # pylint: disable=import-error,import-outside-toplevel
    from explore_bscr import iter_logical  # pylint: disable=import-error,import-outside-toplevel

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    catalog_by_location, catalog_by_id = load_catalog(catalog_path)
    tm_by_occurrence, tm_id_by_occurrence, tm_by_id = load_tm(tm_path)

    wanted_locators = {norm_locator(row["locator"]) for row in audit["records"]}
    physical_paths = sorted({norm_locator(row["physical_path"]) for row in audit["records"]})
    assets: dict[str, bytes] = {}
    errors: list[dict] = []
    for index, physical_path in enumerate(physical_paths, 1):
        path = source_root / Path(physical_path)
        try:
            data = path.read_bytes()
            for asset in iter_logical(data, physical_path, physical_path):
                locator = norm_locator(asset.locator)
                if locator in wanted_locators and asset.data[:4] == b"bscr":
                    assets[locator] = asset.data
        except Exception as exc:  # retain complete extraction evidence
            errors.append({"physical_path": physical_path, "error": str(exc)})
        if index % 100 == 0:
            print(f"loaded {index}/{len(physical_paths)} containers", flush=True)

    scenes: list[dict] = []
    unmatched_locations: list[dict] = []
    for locator in sorted(assets):
        parsed = parse_bscr(assets[locator])
        strings = list(parsed.strings)
        utterances: list[dict] = []
        for i, speaker_record in enumerate(strings[:-1]):
            slot = is_speaker_token(speaker_record.raw)
            if slot is None:
                continue
            dialogue_record = strings[i + 1]
            source_text = dialogue_record.raw.decode("euc_jp", errors="backslashreplace")
            if not looks_like_dialogue(source_text):
                continue
            key = (locator, dialogue_record.absolute_offset)
            catalog = catalog_by_location.get(key)
            if catalog is None:
                unmatched_locations.append(
                    {
                        "locator": locator,
                        "absolute_offset": dialogue_record.absolute_offset,
                        "source_text": source_text,
                    }
                )
                occurrence_id = None
                translation_ko = ""
                tm_id = None
            else:
                occurrence_id = catalog["id"]
                translation_ko = tm_by_occurrence.get(occurrence_id, "")
                tm_id = tm_id_by_occurrence.get(occurrence_id)

            voice_asset = ""
            if i > 0:
                preceding = strings[i - 1].raw.decode("ascii", errors="ignore")
                if "/" in preceding and not JA_RE.search(preceding):
                    voice_asset = preceding
            flags = []
            if SOURCE_RE.search(source_text):
                flags.append("explicit_ja_addressee")
            if TARGET_RE.search(translation_ko):
                flags.append("explicit_ko_addressee")
            if source_text.count("、") + source_text.count("？") + source_text.count("！") > 0:
                flags.append("responsive_or_direct_address_possible")
            utterances.append(
                {
                    "line_index": len(utterances),
                    "string_index": dialogue_record.index,
                    "speaker_slot": slot,
                    "source_text": source_text,
                    "translation_ko": translation_ko,
                    "tm_id": tm_id,
                    "occurrence_id": occurrence_id,
                    "absolute_offset": dialogue_record.absolute_offset,
                    "voice_asset": voice_asset,
                    "flags": flags,
                }
            )

        distinct_slots = sorted({row["speaker_slot"] for row in utterances})
        if len(distinct_slots) < 3:
            continue
        signature_material = json.dumps(
            [(row["speaker_slot"], row["source_text"]) for row in utterances],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        candidate_lines = [row["line_index"] for row in utterances if row["flags"]]
        scenes.append(
            {
                "locator": locator,
                "physical_path": next(
                    (norm_locator(r["physical_path"]) for r in audit["records"] if norm_locator(r["locator"]) == locator),
                    "",
                ),
                "source_bscr_sha256": sha256_bytes(assets[locator]),
                "dialogue_signature_sha256": sha256_bytes(signature_material),
                "surface": "event_script" if locator.startswith("Event/") else "map_dialogue",
                "utterance_count": len(utterances),
                "speaker_slots": distinct_slots,
                "speaker_slot_counts": dict(Counter(row["speaker_slot"] for row in utterances)),
                "candidate_line_indices": candidate_lines,
                "utterances": utterances,
            }
        )

    # Preserve every locator, but nominate one canonical copy per identical dialogue sequence.
    by_signature: dict[str, list[dict]] = defaultdict(list)
    for scene in scenes:
        by_signature[scene["dialogue_signature_sha256"]].append(scene)
    canonical_scenes: list[dict] = []
    for signature, copies in sorted(by_signature.items()):
        copies.sort(key=lambda row: (0 if row["surface"] == "event_script" else 1, row["locator"]))
        canonical = copies[0]
        canonical_scenes.append(
            {
                **canonical,
                "duplicate_locators": [row["locator"] for row in copies[1:]],
                "copy_count": len(copies),
            }
        )

    canonical_scenes.sort(
        key=lambda row: (
            0 if row["surface"] == "event_script" else 1,
            -len(row["candidate_line_indices"]),
            -row["utterance_count"],
            row["locator"],
        )
    )
    report = {
        "schema": "arf-ko-multiparty-addressee-audit-corpus-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "purpose": "Read-only scene corpus for per-line speaker-to-addressee review in scenes with 3+ speaker slots.",
        "inputs": {
            "bscr_full_audit": str(audit_path),
            "text_catalog": str(catalog_path),
            "translation_memory": str(tm_path),
        },
        "counts": {
            "expected_bscr_assets": len(wanted_locators),
            "loaded_bscr_assets": len(assets),
            "multiparty_scene_copies": len(scenes),
            "unique_multiparty_scenes": len(canonical_scenes),
            "unique_event_scenes": sum(row["surface"] == "event_script" for row in canonical_scenes),
            "unique_map_scenes": sum(row["surface"] == "map_dialogue" for row in canonical_scenes),
            "utterances": sum(row["utterance_count"] for row in canonical_scenes),
            "candidate_utterances": sum(len(row["candidate_line_indices"]) for row in canonical_scenes),
            "unmatched_catalog_locations": len(unmatched_locations),
            "container_errors": len(errors),
        },
        "errors": errors,
        "unmatched_catalog_locations": unmatched_locations,
        "scenes": canonical_scenes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], ensure_ascii=False, indent=2))
    return 0 if not errors and not unmatched_locations and len(assets) == len(wanted_locators) else 1


if __name__ == "__main__":
    raise SystemExit(main())

