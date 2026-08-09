#!/usr/bin/env python3
"""Apply pinned Korean compactions for the final fixed-width table fields.

The replacements below were individually rewritten by the internal model to
preserve meaning and required line breaks while fitting the original slot.
There is deliberately no automatic shortening or external translation call.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = (
    ROOT / "work/translation/fixed_field_fit/preflight_before_corrections.json"
)
EXPECTED_PREFLIGHT_SHA256 = (
    "8D24170F71010E405B10ECBDB6487349798F4615DFC4DDAAB2A793BD45CE35F5"
)
CODEBOOK = ROOT / "work/font/final_v1/codebook.json"
ENCODER = ROOT / "work/research/encode_custom_euc28.py"
OUTPUT = ROOT / "work/translation/fixed_field_fit/application_report.json"

REPLACEMENTS = {
    "ARF-TM-D5D54ECF1368478E6260": "능력치와 기본AP가 상승하고\n불과 땅 내성을 얻는다",
    "ARF-TM-87918AF462B59604075C": "공격 능력치가 상승하고\n방어 능력치가 하락한다",
    "ARF-TM-A71A0E143CB0B3BE05C3": "운명의네잎클로버",
    "ARF-TM-E4E8B6ADC4BA7AB522D6": "물결치는 칼날이 타오르는 불꽃을 닮은 검.\n그 일격은 대상에게 불꽃의 고통을 안긴다",
    "ARF-TM-DB8BEECF2CBF79AEB2FA": "강철칼날에 송곳니 같은 말뚝이 늘어선 이형의 검.\n참격은 때로 적의 자유를 빼앗는다",
    "ARF-TM-ADDDB1FD6BE11ADADB55": "뒤로 휜 칼날이 용의 이빨을 닮은 검.\n그 칼날은 죽음 직전의 자에게 힘을 보탠다",
    "ARF-TM-94FED430601B3C3926E6": "때려도, 외워도 좋은 만능 지팡이.\n그 일격은 마법 생물에게 치명상을 입힌다",
    "ARF-TM-C6B0496679795DCC1B47": "이세계 출신 『새벽빛의 마녀』 지팡이.\n소지자의 광소술을 늘 증폭하는 금단의 무기",
    "ARF-TM-8B21BBD0B296633040E9": "다른 곳으로 시선을 돌려 『슬쩍』하기 위한 단검.\n부자가 될 듯한 기분이 든다",
    "ARF-TM-E25E394099962B3A5B5F": "이름 없는 대장장이가 평생을 바쳐 만든 검.\n소지자에게 세상의 모든 악의를 모은다",
    "ARF-TM-9F174893AB22C77B01D9": "불/물/바람/땅의 4대 원소가 조화를 이루는 명검.\n속성 공격을 강화하는 힘을 품는다",
    "ARF-TM-C7903A02135134A7208C": "어둠의 속삭임",
    "ARF-TM-E5415A375B8682518880": "눈부신 빛에 주인의 얼굴이 비치는 고운 건틀릿.\n선을 긋듯 부드럽고 느긋이 움직인다",
    "ARF-TM-C75B6A28642D36A9858B": "용사가 된 소녀에게 어울리는 건틀릿.\n여정을 마친 용사는 제자리로 돌아간다",
    "ARF-TM-8E200117A3F18E2FA220": "지닌 기술을 모두 조준에 쏟은 한 자루 총.\n그 한 발은 때로 상대의 민첩성을 낮춘다",
    "ARF-TM-86F88899F67EC92856DD": "우직하게 충의를 끝까지 지키는 성스런 도끼\n거침없는 일격엔 어떤 망설임도 없다",
    "ARF-TM-EA6EA9BA8EE980640534": "바람에 날리는 깃털장식이 특징인 가벼운 신발.\n민첩성 등을 높이고 추격 효과를 낸다",
    "ARF-TM-EBBB00FDE4FEC019F20E": "인공생물의 모피로 만든 귀중한 망토\n방어력과 저항력이 상승하고 모든 내성을 높인다",
    "ARF-TM-AF1443E8F809CCEA79FF": "배달을 극한까지 익힌 자가 받는 새 시련?\n체력을 대가로 의욕이 마구 떨어진다……",
    "ARF-TM-878F084235B64A1F9C12": "해바라기 압화",
    "ARF-TM-996CD4C867926D0592C0": "외눈가면을 쓴 여왕을 본뜬 목걸이.\n소리 없이 다가오는 어둠 같은 몸놀림을 선사한다",
    "ARF-TM-E6138372D498A2D679ED": "제국 레지스탕스 구성원의 증표.\n가지고 있기만 해도 제국령에서 물건을 살 수 있다",
    "ARF-TM-850B8167D277D12EFA8A": "라스카다 신종에게 건네진 용옥석.\n지니기만 해도 레이와 호존으로부터 몸을 지킨다",
    "ARF-TM-F43A948073999FA39DCD": "공화국 서신",
    "ARF-TM-FF23438EB0A2F7C908A5": "나라를 다스리는 자의 뜻에 따라 원래 오페라 극장\n배경이던 것이 인형탈이 된 물건",
    "ARF-TM-5A51AF2B0D0080DD8F79": "백색·연두색 옷",
    "ARF-TM-D4846A09531C0F85878A": "여름의 해방을 기다린 남자가 입는\n흰 해변과 푸른 바다, 사랑에 빠지기 위한 의상",
    "ARF-TM-90DC50A12C19C0EE71FD": "의문의 학사복",
    "ARF-TM-BEAA4E15583B09947E71": "처진귀 강아지옷",
    "ARF-TM-D22D05EE2864927E8175": "활기찬 수도의 돌길을 힘차게 걷기 위해서는\n세월에도 사랑받는 의상이 필요하다",
    "ARF-TM-BE171C569A3FA6A7679D": "소매와 타이를 꾸민 붉은 장미는 카르분클루스의\n전통 문양을 더 날카롭게 다듬은 것",
    "ARF-TM-820A33D7A50A8909B3D6": "혹독한 겨울의 흰빛에 맞선 검정은\n얼어붙는 바람을 막고 온기를 놓치지 않는다",
    "ARF-TM-D2E9B7D94B02A6FC95A5": "의문의 태도술사",
    "ARF-TM-8B9438146E47C2026FD3": "부두 일꾼들은 외모에 신경 쓰지 않는다.\n드러나는 건 개성과 거친 면모뿐",
    "ARF-TM-BA875BBBCC9AF5EE30DB": "고목색 기모노",
    "ARF-TM-ED33E9BA49AFE56F9DF1": "엉덩이 뒤로 소용돌이치는 큰 꼬리가 달린\n인형탈은 의외로 과감하게 살결을 드러낸다",
    "ARF-TM-E44477CD9F0C819C9EF5": "어느 나라 공주의 것인지는 단언 못하지만\n어디서 어떻게 봐도……인 신비한 드레스",
    "ARF-TM-FAEC2359BB9E7CBFEEBA": "검은고양이 슈트",
    "ARF-TM-BD868E030097FA88F50E": "정열적인 색채로 완성한 무희의 옷\n춤꾼의 움직임에 맞춰 요염한 기운을 흩뿌린다",
    "ARF-TM-5D8DC26C3F356777DCAC": "다른 디아만트 소녀들의 옷과는\n확연히 다른 디자인에 이국적 감각이 묻어난다",
    "ARF-TM-CFB0DDE82F0A19C977BE": "고풍 수영복",
    "ARF-TM-C49502AADEDFFE134014": "의문의 인형옷",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_encoder(path: Path):
    spec = importlib.util.spec_from_file_location("arf_fixed_fit_encoder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records),
        encoding="utf-8",
    )


def main() -> int:
    if sha256(PREFLIGHT) != EXPECTED_PREFLIGHT_SHA256:
        raise ValueError("fixed-field discovery preflight hash mismatch")
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    fixed = [
        item
        for item in preflight.get("overflow_fields", [])
        if not bool(item.get("table_resizable"))
    ]
    fixed_by_id = {str(item["tm_id"]): item for item in fixed}
    if len(fixed) != 42 or len(fixed_by_id) != 42:
        raise ValueError(f"expected 42 unique fixed overflows, found {len(fixed)}")
    if set(REPLACEMENTS) != set(fixed_by_id):
        raise ValueError(
            "replacement ID set differs from fixed-overflow discovery: "
            f"missing={sorted(set(fixed_by_id) - set(REPLACEMENTS))}, "
            f"extra={sorted(set(REPLACEMENTS) - set(fixed_by_id))}"
        )

    encoder = load_encoder(ENCODER)
    codebook = json.loads(CODEBOOK.read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []
    for tm_id, target in REPLACEMENTS.items():
        item = fixed_by_id[tm_id]
        encoded = encoder.encode_text(target, codebook)
        capacity = int(item["capacity"])
        required = len(encoded) + 1
        if b"\0" in encoded:
            raise ValueError(f"encoded NUL in replacement: {tm_id}")
        if required > capacity:
            raise ValueError(
                f"replacement still overflows {tm_id}: {required}>{capacity}"
            )
        if target.count("\n") != str(item["source_text"]).count("\n"):
            raise ValueError(f"line-break count changed for {tm_id}")
        checks.append(
            {
                "tm_id": tm_id,
                "table_unit_id": item["table_unit_id"],
                "before": item["translation_ko"],
                "after": target,
                "before_required_with_nul": item["required_with_nul"],
                "after_required_with_nul": required,
                "capacity": capacity,
                "headroom_after_nul": capacity - required,
                "encoded_hex": encoded.hex().upper(),
            }
        )

    reviewed_dir = ROOT / "work/translation/reviewed"
    found: dict[str, tuple[Path, dict[str, object]]] = {}
    records_by_path: dict[Path, list[dict[str, object]]] = {}
    for path in sorted(reviewed_dir.glob("batch_*.jsonl")):
        records = read_jsonl(path)
        records_by_path[path] = records
        for record in records:
            tm_id = str(record["tm_id"])
            if tm_id in REPLACEMENTS:
                if tm_id in found:
                    raise ValueError(f"duplicate reviewed TM ID: {tm_id}")
                found[tm_id] = (path, record)
    if set(found) != set(REPLACEMENTS):
        raise ValueError(f"reviewed units missing: {sorted(set(REPLACEMENTS) - set(found))}")

    changed_by_batch: dict[Path, int] = defaultdict(int)
    marker = (
        "[fixed-field-fit] Internal-model compact rewrite verified against "
        "the original structured-table byte capacity."
    )
    for tm_id, target in REPLACEMENTS.items():
        path, record = found[tm_id]
        if str(record.get("translation_ko")) != str(fixed_by_id[tm_id]["translation_ko"]):
            raise ValueError(f"reviewed target changed since discovery: {tm_id}")
        record["translation_ko"] = target
        notes = str(record.get("notes") or "")
        if marker not in notes:
            record["notes"] = (notes + (" " if notes else "") + marker).strip()
        changed_by_batch[path] += 1

    batch_results: dict[str, dict[str, object]] = {}
    for path, changed in sorted(changed_by_batch.items(), key=lambda pair: pair[0].name):
        records = records_by_path[path]
        write_jsonl(path, records)
        batch_name = path.stem
        draft_path = ROOT / "work/translation/drafts" / path.name
        draft_by_id = {str(item["tm_id"]): item for item in read_jsonl(draft_path)}
        modified = sum(
            str(item.get("translation_ko") or "")
            != str(draft_by_id[str(item["tm_id"])].get("translation_ko") or "")
            for item in records
        )
        review_path = ROOT / "work/translation/reviews" / f"{batch_name}_review.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))
        review["modified_units"] = modified
        review["unchanged_units"] = len(records) - modified
        review["fixed_field_fit_application"] = {
            "status": "applied",
            "source": str(PREFLIGHT.relative_to(ROOT)).replace("\\", "/"),
            "source_sha256": EXPECTED_PREFLIGHT_SHA256,
            "corrected_units_in_batch": changed,
            "translation_engine_policy": "Codex internal models only",
            "external_translation_models_or_apis_used": False,
        }
        if isinstance(review.get("final_change_summary"), dict):
            review["final_change_summary"][
                "final_modified_units_against_original_draft"
            ] = modified
            review["final_change_summary"][
                "final_unchanged_units_against_original_draft"
            ] = len(records) - modified
        review.setdefault("hashes", {})["reviewed_sha256"] = sha256(path)
        review_path.write_text(
            json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        batch_results[batch_name] = {
            "corrected_units": changed,
            "modified_against_draft": modified,
            "reviewed_sha256": sha256(path),
            "review_report_sha256": sha256(review_path),
        }

    report = {
        "schema": "arf-fixed-table-fit-application-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "source_preflight": str(PREFLIGHT.relative_to(ROOT)).replace("\\", "/"),
        "source_preflight_sha256": EXPECTED_PREFLIGHT_SHA256,
        "codebook_sha256": sha256(CODEBOOK),
        "fixed_overflows_discovered": len(fixed),
        "fixed_fields_corrected": len(checks),
        "fixed_fields_fit_after_correction": sum(
            int(item["after_required_with_nul"]) <= int(item["capacity"])
            for item in checks
        ),
        "batches": batch_results,
        "corrections": checks,
        "error_count": 0,
        "valid": True,
    }
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "fixed_fields_corrected": len(checks),
                "fixed_fields_fit_after_correction": report[
                    "fixed_fields_fit_after_correction"
                ],
                "affected_batches": len(batch_results),
                "application_report": str(OUTPUT),
                "valid": True,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
