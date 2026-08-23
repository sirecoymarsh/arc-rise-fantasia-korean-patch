#!/usr/bin/env python3
"""Build a user-review package for all Arc Rise Fantasia SFD audio surfaces."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work"
OUT = WORK / "runtime_validation" / "sfd_dialogue_review_v112"
CLIP_START = 145.0

CLASSIFICATION = {
    "EV01_05_0800B.sfd": ("audio_music_effects_only", "ADX contains music/effects; speech VAD found 0.000 s."),
    "EV07_09_0100A.sfd": ("audio_music_effects_only", "ADX contains music/effects; speech VAD found 0.000 s."),
    "EV07_09_0700A.sfd": ("silent_video", "No audio stream."),
    "EV09_06_0600B_04.sfd": ("silent_video", "No audio stream."),
    "EV09_06_0600B_06.sfd": ("silent_video", "No audio stream."),
    "EV09_06_0600B_08.sfd": ("silent_video", "No audio stream."),
    "EV09_06_0600B_12-13.sfd": ("silent_video", "No audio stream."),
    "EV09_06_0600B_15.sfd": ("silent_video", "No audio stream."),
    "EV99_I_07B.sfd": ("audio_music_effects_only", "ADX contains music/effects; speech VAD found 0.000 s."),
    "EV99_I_11B.sfd": ("audio_music_effects_only", "ADX contains music/effects; speech VAD found 0.000 s."),
    "EV99_I_12B.sfd": ("audio_music_effects_only", "ADX contains music/effects; speech VAD found 0.000 s."),
    "EV99_I_13B.sfd": ("audio_music_effects_only", "ADX contains music/effects; speech VAD found 0.000 s."),
    "EV99_I_14B.sfd": ("audio_music_effects_only", "ADX contains music/effects; speech VAD found 0.000 s."),
    "EV99_I_15B.sfd": ("audio_music_effects_only", "ADX contains music/effects; speech VAD found 0.000 s."),
    "EV99_I_16B.sfd": ("audio_music_effects_only", "ADX contains music/effects; speech VAD found 0.000 s."),
    "ie_logo.sfd": ("silent_video", "No audio stream."),
    "mmv.sfd": ("spoken_brand_ident", "Voice says Marvelous Entertainment; not story dialogue."),
    "RAY_ED_ROLL.sfd": ("music_or_song_no_story_dialogue", "Ending credits music; no story dialogue detected."),
    "RAY_ED.sfd": ("music_or_song_no_story_dialogue", "Ending music/song; no story dialogue detected."),
    "RAY_OP_01.sfd": ("music_or_song_no_story_dialogue", "Opening music/song; no story dialogue detected."),
    "RAY_OP_02.sfd": ("story_dialogue_with_music", "Japanese story dialogue detected from 152.368 s through 283.088 s."),
}

# Timings are bound to the original SFD timeline. Lines are the active
# Map/map_d_hnk_00.cxd BSCR sequence 112..140.
TIMINGS = [
    (112, 152.20, 157.90), (113, 157.90, 165.45), (114, 165.45, 166.75),
    (115, 166.75, 168.70), (116, 174.70, 176.40), (117, 182.70, 184.00),
    (118, 186.20, 191.55), (119, 192.85, 196.10), (120, 196.10, 201.65),
    (121, 201.65, 203.60), (122, 203.60, 206.55), (123, 208.10, 209.35),
    (124, 209.35, 214.75), (125, 214.75, 216.55), (126, 217.45, 219.60),
    (127, 220.30, 224.55), (128, 229.00, 230.75), (129, 230.75, 234.55),
    (130, 234.55, 238.95), (131, 238.95, 241.05), (132, 241.05, 243.20),
    (133, 244.45, 246.00), (134, 246.00, 251.10), (135, 251.10, 253.25),
    (136, 253.25, 255.10), (137, 255.60, 260.50), (138, 260.55, 265.15),
    (139, 268.45, 274.05), (140, 280.15, 283.10),
]

CANDIDATE = {
    112: "……네가…… 구해 준 거지?\n고마워. 덕분에 살았어.",
    113: "그나저나 방금 그건……\n광소술……은 아니었지. 가소술인가?",
    114: "설마……",
    115: "너, 코더야?",
    116: "이봐, 너!",
    117: "……미안해.",
    118: "……상처투성이잖아.\n너, 왜 이런 곳에……",
    119: "『너』……라는 게 나를 말하는 거야?",
    120: "그래. 이름을 모르니까.\n기분 나빴다면 미안해.",
    121: "난 라르크야. 그러니까――",
    122: "기분 나빠? 뭐가?",
    123: "뭐가라니……",
    124: "밖에서는 나를 『너』라고\n부르는 줄 알았어.",
    125: "아니면 됐어.",
    126: "무, 무슨 소리야?",
    127: "나는 디바. 개체명은 리피아.",
    128: "대체 넌 뭐야?",
    129: "『너』는 알아.\n하인을 부르는 말이잖아?",
    130: "아, 정말!\n대체 뭐냐고!?",
    131: "혹시 화났어?",
    132: "짜증 난 거야!",
    133: "――뭐, 됐어.",
    134: "리피아……라고 했지.\n일단 안전한 곳까지 피하자.",
    135: "아직 탁룡이 나타날지도 몰라.",
    136: "안전한 곳?",
    137: "분명 여기서 남동쪽에\n토파지온 마을이 있을 거야.",
    138: "거기까지 데려다줄게.\n날 구해 준 답례야.",
    139: "그래, 알았어. 잘 부탁해.",
    140: "하아……\n대체 뭐냐고, 정말……",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def srt_time(value: float) -> str:
    ms = int(round(value * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    streams = json.loads((WORK / "runtime_validation/sfd_stream_inventory_v112.json").read_text(encoding="utf-8-sig"))
    stt = json.loads((WORK / "runtime_validation/sfd_audio_stt_small_v112.json").read_text(encoding="utf-8"))
    bscr = json.loads((WORK / "research/bscr_agent/bscr_manifest.json").read_text(encoding="utf-8"))
    tm = json.loads((WORK / "translation/final/translation_memory_draft.json").read_text(encoding="utf-8"))["units"]
    rec = next(r for r in bscr["records"] if r["locator"] == "Map/map_d_hnk_00.cxd::lz10::0001:map_d_hnk_00.bscr")
    tm_by_source = {u["source_text"]: u for u in tm if u.get("status") == "translated"}
    movie_names = {m["name"] for m in streams["movies"]}
    if movie_names != set(CLASSIFICATION):
        raise ValueError(f"movie set mismatch: {sorted(movie_names ^ set(CLASSIFICATION))}")
    stt_by_name = {Path(f["wav"]).with_suffix(".sfd").name: f for f in stt["files"]}

    classification_rows = []
    for movie in sorted(streams["movies"], key=lambda x: x["name"].lower()):
        kind, note = CLASSIFICATION[movie["name"]]
        audio = next((s for s in movie["streams"] if s.get("codec_type") == "audio"), None)
        stt_row = stt_by_name.get(movie["name"])
        classification_rows.append({
            "file": movie["name"],
            "duration_seconds": movie["duration"],
            "audio_codec": audio.get("codec_name") if audio else "",
            "classification": kind,
            "stt_segment_count": stt_row.get("segment_count", 0) if stt_row else 0,
            "speech_vad_seconds": stt_row.get("duration_after_vad", 0) if stt_row else 0,
            "note": note,
        })

    dialogue = []
    for index, start, end in TIMINGS:
        source = rec["string_records"][index]["decoded"]
        unit = tm_by_source[source]
        dialogue.append({
            "bscr_index": index,
            "start_seconds": start,
            "end_seconds": end,
            "source_ja": source,
            "current_runtime_ko": unit["translation_ko"],
            "candidate_ko": CANDIDATE[index],
            "tm_id": unit["tm_id"],
            "translator_model": "Codex internal",
            "candidate_status": "user_review_required_not_applied",
        })

    with (OUT / "SFD_21_AUDIO_CLASSIFICATION.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=classification_rows[0].keys())
        w.writeheader(); w.writerows(classification_rows)
    with (OUT / "RAY_OP_02_DIALOGUE_CANDIDATE.tsv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=dialogue[0].keys(), delimiter="\t")
        w.writeheader(); w.writerows(dialogue)

    full_srt = []
    clip_srt = []
    for n, row in enumerate(dialogue, 1):
        full_srt += [str(n), f"{srt_time(row['start_seconds'])} --> {srt_time(row['end_seconds'])}", row["candidate_ko"], ""]
        clip_srt += [str(n), f"{srt_time(row['start_seconds']-CLIP_START)} --> {srt_time(row['end_seconds']-CLIP_START)}", row["candidate_ko"], ""]
    (OUT / "RAY_OP_02_DIALOGUE_CANDIDATE_FULL.srt").write_text("\n".join(full_srt), encoding="utf-8-sig")
    (OUT / "RAY_OP_02_DIALOGUE_CANDIDATE_CLIP.srt").write_text("\n".join(clip_srt), encoding="utf-8-sig")

    staged_map = WORK / "final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Map/map_d_hnk_00.cxd"
    report = {
        "schema": "arf-sfd-audio-dialogue-review-v1",
        "game_id": "RPJJ99",
        "movie_count": 21,
        "movies_without_audio": sum(r["classification"] == "silent_video" for r in classification_rows),
        "movies_with_audio": sum(bool(r["audio_codec"]) for r in classification_rows),
        "movies_with_story_dialogue": 1,
        "story_dialogue_movie": "Movie/RAY_OP_02.sfd",
        "story_dialogue_range_seconds": [152.368, 283.088],
        "active_subtitle_script": "Map/map_d_hnk_00.cxd::lz10::0001:map_d_hnk_00.bscr",
        "active_subtitle_line_range": [112, 140],
        "active_subtitle_line_count": len(dialogue),
        "active_map_is_in_v112_staging": staged_map.is_file(),
        "active_map_staged_sha256": sha256(staged_map),
        "current_runtime_subtitles_already_korean": True,
        "burn_in_sfd_required": False,
        "reason": "The story dialogue has a separate active BSCR subtitle lane already included in v1.1.2; modifying the SFD is unnecessary and previously broke Sofdec timestamps.",
        "candidate_changes_applied": False,
        "candidate_requires_user_review": True,
        "translation_provenance": "Codex internal",
        "external_translation_service_used_for_korean": False,
        "stt_role": "speech presence and timing evidence only; not translation",
        "classification": classification_rows,
        "dialogue": dialogue,
        "valid": True,
    }
    report_path = OUT / "SFD_AUDIO_DIALOGUE_REVIEW.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = f"""# SFD 동영상 음성·자막 검토 패키지

- 전체 SFD: **21개**
- 오디오 스트림 있음: **{report['movies_with_audio']}개**
- 오디오 스트림 없음: **{report['movies_without_audio']}개**
- 실제 스토리 대사 포함: **1개 (`RAY_OP_02.sfd`)**
- 대사 구간: **152.368~283.088초**
- 자막 원고: 활성 `Map/map_d_hnk_00.cxd`의 112~140번, 총 **29개**

## 중요한 결론

`RAY_OP_02.sfd`의 일본어 음성 대사는 게임의 별도 BSCR 메시지로 이미 한국어가
표시되도록 v1.1.2에 들어 있습니다. 따라서 SFD에 글자를 직접 구워 넣을 필요가
없습니다. 이전 영상 정지는 SFD 재인코딩에서 타임스탬프가 역행했기 때문에 생겼고,
원본 SFD + 한국어 BSCR 자막이 가장 안전한 구조입니다.

`RAY_OP_02_DIALOGUE_CANDIDATE.tsv`에는 현재 게임 문구와 자연스럽게 다듬은 후보를
나란히 넣었습니다. 후보는 아직 게임 패치에 적용하지 않았습니다.
`RAY_OP_02_Korean_Subtitle_Review.mp4`는 후보 문구를 확인하는 검토용 영상이며,
게임에 넣을 SFD가 아닙니다.
"""
    (OUT / "README_KO.md").write_text(readme, encoding="utf-8-sig")
    print(json.dumps({"output": str(OUT), "report": str(report_path), "report_sha256": sha256(report_path), "dialogue_lines": len(dialogue)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
