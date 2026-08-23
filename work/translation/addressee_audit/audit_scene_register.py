#!/usr/bin/env python3
"""Build an all-scene register audit for ARF dialogue.

This is a candidate generator only.  It never translates and never edits TM.
Accepted Korean corrections are written separately by the active Codex model
after whole-scene review.
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
CONTROL_RE = re.compile(r"<\$[0-9A-Fa-f]{2}>")

JP_POLITE_RE = re.compile(
    r"(?:です(?:ね|よ|か|わ|の)?|ます(?:ね|よ|か)?|ません|ましょう|"
    r"ください|下さい|ございます|ございません|でしょう|でしょうか|"
    r"いただけ|頂け|なさいます|致します|申します)"
)
JP_ROUGH_RE = re.compile(
    r"(?:お前|おまえ|おめー|てめえ|貴様|あんた|じゃね[ぇえ]|ねーよ|"
    r"だぜ|だぞ|だろ(?:う)?[！!？?]|しろ(?:よ)?[！!。]?|するな|"
    r"くれよ|かよ[！!？?。]?|やがれ|ちまえ|野郎)"
)

KO_POLITE_RE = re.compile(
    r"(?:습니다|습니까|슴다|임다|세요|십시오|시겠어요|주시겠|해요|예요|이에요|"
    r"군요|네요|나요|까요|겠어요|거예요|거죠|잖아요|말이에요|답니다|랍니다|죠)"
    r"(?:[.!?…~♪\n]|$)"
)
KO_CASUAL_RE = re.compile(
    r"(?:거야|잖아|말이야|거든|해라|하라|해 줘|해줘|하지 마|하지마|"
    r"할까|하자|겠어|했어|였어|됐어|할래|해 볼래|해볼래|냐|니|군|네|지|다|마)"
    r"(?:[.!?…~♪\n]|$)"
)

NAME_MAP = {
    "ラルク": "라르크",
    "リフィア": "리피아",
    "アルス": "알스",
    "アデール": "아델",
    "ニコル": "니콜",
    "セシル": "세실",
    "サージュ": "사쥬",
    "レスリー": "레슬리",
    "オイゲン": "오이겐",
    "ヴァイス": "바이스",
    "ホゼア": "호제아",
    "レオン": "레온",
    "シェリィ": "셰리",
    "カーライル": "칼라일",
    "クドアンヌ": "쿠도안느",
    "グランツ": "그란츠",
}


def norm_locator(value: str) -> str:
    return value.replace("\\", "/")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_speaker_token(raw: bytes) -> str | None:
    if len(raw) != 3 or raw[0] != 0x19:
        return None
    try:
        payload = raw[1:].decode("ascii")
    except UnicodeDecodeError:
        return None
    return payload.upper() if re.fullmatch(r"[0-9A-Fa-f]{2}", payload) else None


def looks_like_dialogue(text: str) -> bool:
    return bool(JA_RE.search(text)) and not bool(re.fullmatch(r"[A-Za-z0-9_./\\:-]+", text))


def register(text: str, polite_re: re.Pattern[str], casual_re: re.Pattern[str]) -> str:
    clean = CONTROL_RE.sub("", text)
    polite = bool(polite_re.search(clean))
    casual = bool(casual_re.search(clean))
    if polite and casual:
        return "mixed"
    if polite:
        return "polite"
    if casual:
        return "casual"
    return "unknown"


def natural_key(locator: str) -> tuple:
    parts = re.split(r"(\d+)", locator.lower())
    return tuple(int(part) if part.isdigit() else part for part in parts)


def load_catalog(path: Path) -> dict[tuple[str, int], dict]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {
        (norm_locator(row["logical_locator"]), int(row["offset"])): row
        for row in doc["records"]
        if row.get("extraction_mode") == "bscr_string_pool"
    }


def load_tm(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    ko_by_occ: dict[str, str] = {}
    tm_by_occ: dict[str, str] = {}
    for unit in doc["units"]:
        for occ in unit.get("occurrence_ids", []):
            ko_by_occ[str(occ)] = str(unit.get("translation_ko") or "")
            tm_by_occ[str(occ)] = str(unit["tm_id"])
    return ko_by_occ, tm_by_occ


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()

    source_root = root / "work/disc_extracted/DATA/files"
    audit_path = root / "work/research/bscr_agent/full_audit.json"
    catalog_path = root / "work/catalog/text_v2/text_catalog.json"
    tm_path = root / "work/translation/final/translation_memory_draft.json"

    sys.path.insert(0, str(root / "work/research/bscr_agent"))
    from bscr_tool import parse_bscr  # pylint: disable=import-error,import-outside-toplevel
    from explore_bscr import iter_logical  # pylint: disable=import-error,import-outside-toplevel

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    catalog = load_catalog(catalog_path)
    ko_by_occ, tm_by_occ = load_tm(tm_path)
    wanted = {norm_locator(row["locator"]) for row in audit["records"]}
    physical_paths = sorted({norm_locator(row["physical_path"]) for row in audit["records"]})

    assets: dict[str, bytes] = {}
    errors: list[dict] = []
    for physical in physical_paths:
        try:
            data = (source_root / Path(physical)).read_bytes()
            for asset in iter_logical(data, physical, physical):
                locator = norm_locator(asset.locator)
                if locator in wanted and asset.data[:4] == b"bscr":
                    assets[locator] = asset.data
        except Exception as exc:  # pragma: no cover - evidence path
            errors.append({"physical_path": physical, "error": str(exc)})

    scenes: list[dict] = []
    unmatched: list[dict] = []
    for locator in sorted(assets, key=natural_key):
        parsed = parse_bscr(assets[locator])
        utterances: list[dict] = []
        strings = list(parsed.strings)
        for idx, token in enumerate(strings[:-1]):
            slot = is_speaker_token(token.raw)
            if slot is None:
                continue
            dialogue = strings[idx + 1]
            source = dialogue.raw.decode("euc_jp", errors="backslashreplace")
            if not looks_like_dialogue(source):
                continue
            record = catalog.get((locator, dialogue.absolute_offset))
            if record is None:
                unmatched.append(
                    {"locator": locator, "offset": dialogue.absolute_offset, "source_text": source}
                )
                occ_id = None
                tm_id = None
                ko = ""
            else:
                occ_id = str(record["id"])
                tm_id = tm_by_occ.get(occ_id)
                ko = ko_by_occ.get(occ_id, "")
            jp_reg = register(source, JP_POLITE_RE, JP_ROUGH_RE)
            ko_reg = register(ko, KO_POLITE_RE, KO_CASUAL_RE)
            names = [ko_name for jp_name, ko_name in NAME_MAP.items() if jp_name in source]
            mismatch = (
                (jp_reg == "polite" and ko_reg == "casual")
                or (jp_reg == "casual" and ko_reg == "polite")
            )
            utterances.append(
                {
                    "line_index": len(utterances),
                    "speaker_slot": slot,
                    "source_text": source,
                    "translation_ko": ko,
                    "tm_id": tm_id,
                    "occurrence_id": occ_id,
                    "absolute_offset": dialogue.absolute_offset,
                    "jp_register": jp_reg,
                    "ko_register": ko_reg,
                    "direct_names": names,
                    "register_mismatch_candidate": mismatch,
                }
            )
        if not utterances:
            continue
        material = json.dumps(
            [(row["speaker_slot"], row["source_text"]) for row in utterances],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        scenes.append(
            {
                "locator": locator,
                "surface": "event_script" if locator.startswith("Event/") else "map_dialogue",
                "source_bscr_sha256": sha256_bytes(assets[locator]),
                "dialogue_signature_sha256": sha256_bytes(material),
                "utterance_count": len(utterances),
                "speaker_slots": sorted({row["speaker_slot"] for row in utterances}),
                "utterances": utterances,
            }
        )

    # Canonicalize byte-identical dialogue sequences, preferring Event copies.
    by_sig: dict[str, list[dict]] = defaultdict(list)
    for scene in scenes:
        by_sig[scene["dialogue_signature_sha256"]].append(scene)
    canonical: list[dict] = []
    for copies in by_sig.values():
        copies.sort(key=lambda row: (0 if row["surface"] == "event_script" else 1, natural_key(row["locator"])))
        chosen = copies[0]
        chosen["duplicate_locators"] = [row["locator"] for row in copies[1:]]
        chosen["copy_count"] = len(copies)
        canonical.append(chosen)
    canonical.sort(key=lambda row: (0 if row["surface"] == "event_script" else 1, natural_key(row["locator"])))

    # Build a conservative first-scene-baseline candidate list.  Filename order
    # is only a locator-order proxy; every hit still requires full-scene review.
    first_scene: dict[str, dict] = {}
    for scene in canonical:
        for slot in scene["speaker_slots"]:
            if slot in first_scene:
                continue
            rows = [row for row in scene["utterances"] if row["speaker_slot"] == slot]
            jp = Counter(row["jp_register"] for row in rows if row["jp_register"] in {"polite", "casual"})
            ko = Counter(row["ko_register"] for row in rows if row["ko_register"] in {"polite", "casual"})
            if rows:
                first_scene[slot] = {
                    "locator": scene["locator"],
                    "jp_dominant": jp.most_common(1)[0][0] if jp else "unknown",
                    "ko_dominant": ko.most_common(1)[0][0] if ko else "unknown",
                    "utterance_count": len(rows),
                }

    candidates: list[dict] = []
    for scene in canonical:
        for row in scene["utterances"]:
            if not row["register_mismatch_candidate"] or not row["tm_id"]:
                continue
            baseline = first_scene.get(row["speaker_slot"], {})
            matches_first_ko = row["ko_register"] == baseline.get("ko_dominant")
            differs_first_jp = (
                baseline.get("jp_dominant") in {"polite", "casual"}
                and row["jp_register"] != baseline.get("jp_dominant")
            )
            candidates.append(
                {
                    "locator": scene["locator"],
                    "line_index": row["line_index"],
                    "speaker_slot": row["speaker_slot"],
                    "tm_id": row["tm_id"],
                    "source_text": row["source_text"],
                    "translation_ko": row["translation_ko"],
                    "jp_register": row["jp_register"],
                    "ko_register": row["ko_register"],
                    "direct_names": row["direct_names"],
                    "first_scene_baseline": baseline,
                    "matches_first_ko": matches_first_ko,
                    "differs_first_jp": differs_first_jp,
                    "first_scene_carryover_candidate": matches_first_ko and differs_first_jp,
                }
            )

    report = {
        "schema": "arf-ko-scene-register-audit-corpus-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "purpose": (
            "Read-only candidates for dialogue whose Korean register may have been inherited "
            "from a character baseline instead of being re-evaluated per scene/addressee."
        ),
        "limitations": [
            "Japanese/Korean register labels are regex candidates, not semantic verdicts.",
            "Natural locator order is only a story-order proxy.",
            "Every accepted correction requires whole-scene Codex review.",
        ],
        "inputs": {
            "bscr_full_audit": str(audit_path),
            "text_catalog": str(catalog_path),
            "translation_memory": str(tm_path),
        },
        "counts": {
            "expected_bscr_assets": len(wanted),
            "loaded_bscr_assets": len(assets),
            "scene_copies": len(scenes),
            "unique_scenes": len(canonical),
            "utterances": sum(scene["utterance_count"] for scene in canonical),
            "register_mismatch_candidates": len(candidates),
            "first_scene_carryover_candidates": sum(row["first_scene_carryover_candidate"] for row in candidates),
            "unmatched_catalog_locations": len(unmatched),
            "container_errors": len(errors),
        },
        "first_scene_by_speaker_slot": first_scene,
        "errors": errors,
        "unmatched_catalog_locations": unmatched,
        "candidates": candidates,
        "scenes": canonical,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], ensure_ascii=False, indent=2))
    return 0 if not errors and len(assets) == len(wanted) else 1


if __name__ == "__main__":
    raise SystemExit(main())
