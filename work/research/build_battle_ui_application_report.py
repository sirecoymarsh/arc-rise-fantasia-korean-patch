#!/usr/bin/env python3
"""Prove the exact battle raster UI delta before final staging integration."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
BASE = W / "final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Btl/btl_usual.vol"
OUTPUT = W / "battle_ui_raster_application/btl_usual.vol"
APP = W / "battle_ui_raster_application"
REPORT = APP / "application_report.json"

EXPECTED = {
    "btl_tex_wtm.vol": {
        27: ("btl_comandlist_moji.wtm", ["コマンド", "명령"]),
        32: ("btl_renkei_moji_renkei.wtm", ["連携", "연계"]),
        33: ("btl_renkei_moji_renkei_enemy.wtm", ["連携", "연계"]),
        34: ("btl_renkei_moji_excelact_pc.wtm", ["奥義", "오의"]),
        35: ("btl_renkei_moji_excelact_enemy.w", ["奥義", "오의"]),
        48: ("btl_renkei_moji_syugeki.wtm", ["襲撃 / First attack", "선제공격"]),
        49: ("btl_renkei_moji_tekisyu.wtm", ["敵襲 / Back attack", "기습"]),
        75: ("btl_tactics_moji.wtm", ["作戦 1 / 作戦 2 / 作戦 3", "작전 1 / 작전 2 / 작전 3"]),
    },
    "btl_tex_shared.vol": {
        16: ("btl_status_dead.wtm", ["戦闘不能", "전투불능"]),
        50: ("btl_comandselect_moji.wtm", ["行動選択 / 作戦設定 / ステータス / 逃走", "행동 선택 / 작전 설정 / 상태 / 도주"]),
        71: ("btl_hit_moji.wtm", ["連携レート / Total damage / Hit", "연계율 / 총 피해량 / HIT"]),
        99: ("moji.wtm", ["弱点 / 耐性", "약점 / 내성"]),
    },
}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha(path: Path) -> str:
    return digest(path.read_bytes())


def parse_rtdp(data: bytes) -> list[dict[str, Any]]:
    need(data[:4] == b"RTDP", "not RTDP")
    eoh, count = struct.unpack_from(">II", data, 4)
    rows = []
    for index in range(count):
        pos = 0x20 + index * 40
        name = data[pos:pos + 32].split(b"\0", 1)[0].decode("ascii")
        size, relative = struct.unpack_from(">II", data, pos + 32)
        stored = data[eoh + relative:eoh + relative + size]
        decoded = bytes(value ^ 0x55 for value in stored)
        rows.append({"index": index, "name": name, "size": size, "decoded": decoded})
    return rows


def main() -> int:
    for path in (BASE, OUTPUT):
        need(path.is_file(), f"missing input: {path}")
    need(BASE.stat().st_size == OUTPUT.stat().st_size, "outer size changed")
    base_top = parse_rtdp(BASE.read_bytes())
    out_top = parse_rtdp(OUTPUT.read_bytes())
    need(len(base_top) == len(out_top), "outer member count changed")
    top_changed = []
    nested_rows = []
    for before, after in zip(base_top, out_top):
        need((before["index"], before["name"], before["size"]) == (after["index"], after["name"], after["size"]), "outer layout changed")
        if before["decoded"] == after["decoded"]:
            continue
        name = str(before["name"])
        need(name in EXPECTED, f"unexpected changed outer member: {name}")
        top_changed.append({
            "index": before["index"], "name": name, "size": before["size"],
            "source_sha256": digest(before["decoded"]), "output_sha256": digest(after["decoded"]),
        })
        b_rows = parse_rtdp(before["decoded"])
        a_rows = parse_rtdp(after["decoded"])
        need(len(b_rows) == len(a_rows), f"nested member count changed: {name}")
        seen = set()
        for b_row, a_row in zip(b_rows, a_rows):
            need((b_row["index"], b_row["name"], b_row["size"]) == (a_row["index"], a_row["name"], a_row["size"]), f"nested layout changed: {name}")
            if b_row["decoded"] == a_row["decoded"]:
                continue
            index = int(b_row["index"])
            need(index in EXPECTED[name], f"unexpected changed nested member: {name}::{index}")
            expected_name, texts = EXPECTED[name][index]
            need(b_row["name"] == expected_name, f"unexpected nested name: {name}::{index}")
            seen.add(index)
            nested_rows.append({
                "container": name,
                "entry_index": index,
                "member": expected_name,
                "size": b_row["size"],
                "source_sha256": digest(b_row["decoded"]),
                "output_sha256": digest(a_row["decoded"]),
                "source_visible_text": texts[0],
                "translation_ko": texts[1],
                "translator_model": "Codex internal",
            })
        need(seen == set(EXPECTED[name]), f"missing expected nested edits in {name}")
    need({row["name"] for row in top_changed} == set(EXPECTED), "outer changed set mismatch")
    need(len(nested_rows) == 12, "expected 12 changed WTM entries")

    preview_files = sorted(path for path in (APP / "preview_png").glob("*.png") if path.is_file())
    report = {
        "schema": "arf-battle-raster-ui-application-v1",
        "game_id": "RPJJ99",
        "translator_model": "Codex internal",
        "translation_engine_policy": "Codex internal model only",
        "external_translation_models_or_apis_used": False,
        "source": {"path": str(BASE), "size": BASE.stat().st_size, "sha256": sha(BASE)},
        "output": {"path": str(OUTPUT), "size": OUTPUT.stat().st_size, "sha256": sha(OUTPUT)},
        "counts": {
            "outer_members": len(base_top),
            "changed_outer_members": len(top_changed),
            "modified_wtm_entries": len(nested_rows),
            "translated_text_items": 19,
            "unexpected_changed_members": 0,
            "size_changed_members": 0,
        },
        "outer_changes": top_changed,
        "wtm_changes": nested_rows,
        "preview_artifacts": [
            {"path": str(path), "size": path.stat().st_size, "sha256": sha(path)} for path in preview_files
        ],
        "checks": {
            "outer_size_preserved": True,
            "outer_member_layout_preserved": True,
            "only_two_allowlisted_nested_volumes_changed": True,
            "nested_member_layouts_preserved": True,
            "only_twelve_allowlisted_wtm_entries_changed": True,
            "all_wtm_entry_sizes_preserved": True,
        },
        "valid": True,
        "error_count": 0,
        "errors": [],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "output_sha256": report["output"]["sha256"], "counts": report["counts"], "valid": True}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
