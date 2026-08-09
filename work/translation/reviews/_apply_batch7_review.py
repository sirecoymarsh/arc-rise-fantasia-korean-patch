import hashlib
import json
from pathlib import Path


SOURCE = Path("work/translation/tm_v2/batches/source/batch_0007.jsonl")
DRAFT = Path("work/translation/drafts/batch_0007.jsonl")
OUTPUT = Path("work/translation/reviewed/batch_0007.jsonl")
CHANGES = Path("work/translation/reviews/batch_0007_changes.json")


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


edits = {
    "ARF-TM-3F5CF01DF2981D97DA7A": {
        "after": "광소술 사범",
        "category": "source_catalog_boundary_recovery",
        "reason": "NUL 스캐너 원문은 선두 「光」을 잃어 ‘召術師範’으로 잘렸지만 구조화된 chat:50:title은 ‘光召術師範’으로 확인되어 화면 의미를 ‘광소술 사범’으로 복원했다.",
    },
    "ARF-TM-3E995063593504059CF2": {
        "after": "<$13>14<$1F>0000EC<$1F>01<$13>00의 힘을 이용해\n다양한 현상을 일으키는\n광소 기술.\n광소술을 사용할 때는\n<$13>14<$1F>000008<$1F>01<$13>00를 1포인트 소모한다",
        "category": "linked_term_particle",
        "reason": "제어 토큰으로 치환될 자원명 뒤 목적격 조사를 보완해 ‘자원을 1포인트 소모한다’는 문장 구조를 복원했다.",
    },
    "ARF-TM-3EA37727C9F91A5AA549": {
        "after": "바람의 코드가 새겨진 장신구.\n그 바람의 울림은 억압의 침묵을 깨뜨린다",
        "category": "item_flavor_naturalness",
        "reason": "「風鳴り」를 어색한 ‘바람 소리’보다 장신구의 시적인 설명에 맞는 ‘바람의 울림’으로 다듬었다.",
    },
    "ARF-TM-4292FF72037D819C5E06": {
        "after": "자신의 <$13>14<$1F>000007<$1F>01<$13>00를 지정한\n아군에게 양도하는 <$13>14<$1F>00004B<$1F>01<$13>00.\n다른 캐릭터가 쓰고 싶은\n<$13>14<$1F>00004B<$1F>01<$13>00가 있는데\n<$13>14<$1F>000007<$1F>01<$13>00가 부족하다.\n하지만 자신은 남아돈다.\n그럴 때를 위한\n<$13>14<$1F>00004B<$1F>01<$13>00이다",
        "category": "help_text_grammar",
        "reason": "‘다른 캐릭터로 사용하고 싶은’의 어색한 주체 관계를 바로잡고, 지정한 아군에게 자원을 양도한다는 기능을 자연스럽게 재구성했다.",
    },
    "ARF-TM-42AFA6BB5C04CAF0D529": {
        "after": "선명한 파랑과 흘러내릴 듯한 빨강이 돋보이는\n사람들에게 웃음을 선사하기 위한 의상",
        "category": "item_flavor_naturalness",
        "reason": "일본어 수식 관계를 분명히 하고 ‘웃음을 주다’를 의상 설명에 자연스러운 ‘웃음을 선사하다’로 다듬었다.",
    },
    "ARF-TM-42B1F05B7A28F4AFDCB5": {
        "after": "마수의 피에 10년간 담갔다고 하는 검.\n그 일격은 마수에게 막대한 위력을 발휘한다",
        "category": "item_flavor_naturalness",
        "reason": "「絶大なる効果」를 공격용 검의 문맥에 맞게 ‘막대한 위력’으로 옮겨 자연스러움과 효과의 강도를 함께 살렸다.",
    },
    "ARF-TM-42E4C817A258C9D1DFD2": {
        "after": "평범한 수영복\n강한 햇빛에서 눈을 보호하는 검은 유리 안경이 딸려 있다",
        "category": "meaning_omission",
        "reason": "초벌에서 빠진 보호 대상 「目」를 복원해 안경이 강한 햇빛으로부터 눈을 보호한다는 뜻을 명확히 했다.",
    },
    "ARF-TM-45E1FC7F11C8B2B0DD5C": {
        "after": "짐을 배달하고 있습니다만\n저로서는 어려울 것 같아\n대신 배달해 주셨으면 합니다.\n바트라키테스 광장에서 기다리겠습니다.\n　\n※도중에 포기할 수 없는 퀘스트입니다",
        "category": "quest_register_naturalness",
        "reason": "「荷物」를 과도하게 상업적인 ‘화물’ 대신 일반적인 ‘짐’으로 옮기고 의뢰인의 정중한 말투를 정리했다.",
    },
    "ARF-TM-46105CD2453198DE0969": {
        "after": "<$13>14<$1F>0000F9<$1F>01<$13>00와 같은 이름이\n붙은 코드.\n이사의 코드를 지닌 자는\n<$13>14<$1F>0000FB<$1F>01<$13>00라 불린다.\n이 코드가 대체\n어떤 힘을 지녔는지는\n알 수 없지만\n<$13>14<$1F>0000EF<$1F>01<$13>00와의 계약에는\n없어서는 안 될 것으로 보인다",
        "category": "linked_term_particle_meaning",
        "reason": "「〜との契約」를 ‘사이의 계약’이 아니라 제어 토큰 대상과 맺는 ‘〜와의 계약’으로 바로잡았다.",
    },
    "ARF-TM-468B4F41CA2FC098ED41": {
        "after": "<$15>01피해를 받을 때\n반드시 『방어』 상태가 된다",
        "category": "system_term_typography",
        "reason": "앞선 검수본의 전투 명령 표기와 맞춰 원문의 『』를 유지하고 비표준 곡선 따옴표를 제거했다.",
    },
    "ARF-TM-473A4A1E8F39DEEC88A5": {
        "after": "비율로 받는 피해량을\n크게 줄인다",
        "category": "system_meaning_naturalness",
        "reason": "‘비율 피해로 받는 피해’라는 중복·비문을 고쳐 비율 기반 피해량을 크게 줄이는 기능을 명확히 했다.",
    },
    "ARF-TM-496FC041025A5312D522": {
        "after": "<$13>14<$1F>0000A0<$1F>01<$13>00 레벨 4의 <$13>14<$1F>000061<$1F>01<$13>00.\n아군 1명을 <$13>14<$1F>00003B<$1F>01<$13>00\n상태로 만든다.\n<$13>14<$1F>0000B0<$1F>01<$13>00의\n퀵 워드에서는\n효과 지속 턴이 늘어난다",
        "category": "system_naturalness",
        "reason": "‘효과 턴’이라는 불명확한 표현을 효과의 지속 턴 수가 늘어난다는 의미로 명료화했다.",
    },
    "ARF-TM-4AD436B36BAD7345B714": {
        "after": "보타이 전투복",
        "category": "fixed_field_capacity",
        "reason": "나비넥타이라는 의미를 유지하는 의류 용어 ‘보타이’를 사용해 아이템명 고정 필드의 NUL 포함 17바이트 한도에 맞췄다.",
    },
    "ARF-TM-4BC5F10B70B8F690E72A": {
        "after": "이매지널신으로 이어지는 문을 봉인하기 위해",
        "category": "glossary_consistency",
        "reason": "고정 용어집의 합성 신명 표기 ‘이매지널신’을 적용했다.",
    },
}


source = read_jsonl(SOURCE)
draft = read_jsonl(DRAFT)
assert len(source) == len(draft) == 200
source_by_id = {item["tm_id"]: item for item in source}
assert [item["tm_id"] for item in source] == [item["tm_id"] for item in draft]
assert set(edits).issubset(source_by_id)

changes = []
for src_item, item in zip(source, draft):
    assert item["source_text"] == src_item["source_text"]
    edit = edits.get(item["tm_id"])
    if not edit:
        continue
    before = item["translation_ko"]
    after = edit["after"]
    assert before != after
    assert before.count("\n") == after.count("\n"), item["tm_id"]
    item["translation_ko"] = after
    changes.append(
        {
            "tm_id": item["tm_id"],
            "source_text": item["source_text"],
            "before": before,
            "after": after,
            "category": edit["category"],
            "reason": edit["reason"],
        }
    )

assert len(changes) == len(edits)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(
    "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in draft),
    encoding="utf-8",
)
CHANGES.write_text(
    json.dumps(
        {
            "schema": "arf-translation-review-changes-v1",
            "batch_id": "batch_0007",
            "reviewer": "/root/review_batch_0007",
            "translation_engine_policy": "Codex internal models only",
            "external_translation_services_used": [],
            "modified_units": len(changes),
            "modifications": changes,
            "reviewed_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest().upper(),
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
print(json.dumps({"modified_units": len(changes), "reviewed_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest().upper()}))
