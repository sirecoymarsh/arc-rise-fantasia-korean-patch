import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "translation" / "tm_v2" / "batches" / "source" / "batch_0012.jsonl"
DRAFT = ROOT / "translation" / "drafts" / "batch_0012.jsonl"
REVIEWED = ROOT / "translation" / "reviewed" / "batch_0012.jsonl"
REVIEW_LOG = ROOT / "translation" / "reviews" / "batch_0012_review.json"


corrections = {
    "ARF-TM-7E22CFB9B9330EC78893": {
        "after": "자양강장에 효과적인 약을 만들고 싶다.\n이걸로 지친 백성들을 구하는 거야.\n커다란 눈알이 달린 식물과 애벌레에게서\n채취할 수 있다고 들었다",
        "category": "meaning/naturalness",
        "reason": "‘큰 눈알을 지닌 식물’이라는 수식 관계가 분명하도록 다듬었다.",
    },
    "ARF-TM-7E91E75CE31B6244742D": {
        "after": "하나의 <$13>14<$1F>0000E4<$1F>01<$13>00을 얼마나\n사용해 왔는지를 보여 주는 지표.\n<$13>14<$1F>0000E4<$1F>01<$13>00마다 있으며, 무기 LV를\n높이면\n<$13>14<$1F>00004F<$1F>01<$13>00의 슬롯이 확장되거나\n<$13>14<$1F>00004E<$1F>01<$13>00의 잠금이\n해제되는 등의 현상이\n발생한다",
        "category": "meaning/naturalness",
        "reason": "使い込む의 지속적인 사용 의미와 目安의 지표 의미를 자연스럽게 반영했다.",
    },
    "ARF-TM-7F16BAD6F5FE3AF55213": {
        "after": "<$13>14<$1F>00009D<$1F>01<$13>00 중 하나.\n여러 적에게 효과가 있는\n공격 계열 <$13>14<$1F>000061<$1F>01<$13>00이 많은\n속성이다.\n이 속성은 <$13>14<$1F>0000A1<$1F>01<$13>00과\n<$13>14<$1F>0000AD<$1F>01<$13>00한다",
        "category": "terminology",
        "reason": "동일한 시스템 설명에서 쓰는 ‘공격 계열’ 표기로 통일했다.",
    },
    "ARF-TM-7FAD5032CAA433BEE3BF": {
        "after": "메리디아 가문의 문장이 새겨진 브로치.\n착용자가 쓰러지는 것을 용납하지 않는다",
        "category": "naturalness",
        "reason": "장비 설명의 주체와 착용 대상이 자연스럽게 드러나도록 다듬었다.",
    },
    "ARF-TM-80F11EF1A907CB06E1F2": {
        "after": "범위 내 대상의 DEF/RES 상승\n자신 주변에 발동",
        "category": "battle-function/naturalness",
        "reason": "범위 효과의 대상이 분명하도록 전투 설명 템플릿에 맞췄다.",
    },
    "ARF-TM-811D571E5B31ABB9AE2F": {
        "after": "<$13>14<$1F>0000E8<$1F>01<$13>00의 대지――\n그 이면을 종횡무진\n누비며 다량의 <$13>14<$1F>0000EC<$1F>01<$13>00를\n머금은 것이 지맥이다.\n오늘날에는 땅속 깊은 곳까지\n탐사의 손길이 닿아\n오르키나에서 메리디아로\n이어지는 본류의 존재가\n확인되었다",
        "category": "meaning/naturalness",
        "reason": "대지의 이면을 흐르며 에너지를 머금은 주체가 지맥임을 명확히 했다.",
    },
    "ARF-TM-85120AC1D6834B687271": {
        "after": "<$13>14<$1F>000131<$1F>01<$13>00의 수도.\n아름다운 분수 광장 주변에는\n수많은 상점과 노점이\n늘어서고, 항만 지구에서는 선박의\n흰 돛이 펄럭이며\n공업 지구에서는 조업 소리가\n끊이지 않으며, 상층 지구는\n활기가 넘치고 성은\n압도적인 아름다움을 자랑한다",
        "category": "naturalness",
        "reason": "상층 지구의 활기를 묘사하는 문장을 자연스러운 한국어로 교정했다.",
    },
    "ARF-TM-85AB0BC1448D87655B2B": {
        "after": "노와레교도가 지닌 성석",
        "category": "proper-noun/orthography",
        "reason": "종교명과 ‘교도’를 하나의 복합어로 붙여 썼다.",
    },
    "ARF-TM-87F4B242BB7716E7AFD1": {
        "after": "<$13>14<$1F>000093<$1F>01<$13>00가 적을 발견하는\n수단. <$13>14<$1F>000099<$1F>01<$13>00, <$13>14<$1F>00009A<$1F>01<$13>00, <$13>14<$1F>00009B<$1F>01<$13>00\n<$13>14<$1F>00009C<$1F>01<$13>00의 4가지 수단이 있다.\n둘 이상의 감지 방식을\n함께 지닌 경우도 있다.\n또한, 자신보다 명백히\n강한 적은 감지하지\n않는다. 이길 수 없는 적에게\n도전하지 않는다는 뜻이다",
        "category": "naturalness/line-break",
        "reason": "마지막 설명을 자연스럽게 연결하고 조사가 줄 끝에 고립되지 않도록 재배치했다.",
    },
    "ARF-TM-8AD936792569B790CE96": {
        "after": "<$13>14<$1F>000021<$1F>01<$13>00 중 하나.\n<$13>14<$1F>000003<$1F>01<$13>00가 최대치의 25% 이하로\n떨어지면 자동으로\n발생한다. 고유 효과는\n없지만 <$13>14<$1F>00004B<$1F>01<$13>00의\n발동 조건이 되는\n경우가 있다. 이 <$13>14<$1F>000021<$1F>01<$13>00는\n<$13>14<$1F>000023<$1F>01<$13>00이다.",
        "category": "grammar/line-break",
        "reason": "조사 ‘는’이 다음 줄에 홀로 남지 않도록 보호 토큰 뒤로 옮겼다.",
    },
    "ARF-TM-8AF3B4CF818538FDED1B": {
        "after": "범위 내 대상에게 빛+어둠 속성 피해\n추가 효과: 혼란/맹독",
        "category": "battle-function/naturalness",
        "reason": "범위 공격의 적용 대상을 전투 설명 템플릿에 맞게 명시했다.",
    },
}


source_rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines()]
draft_rows = [json.loads(line) for line in DRAFT.read_text(encoding="utf-8").splitlines()]
draft_by_id = {row["tm_id"]: row for row in draft_rows}

reviewed_rows = []
modifications = []
for source_row in source_rows:
    tm_id = source_row["tm_id"]
    before = draft_by_id[tm_id]["translation_ko"]
    correction = corrections.get(tm_id)
    after = correction["after"] if correction else before
    source_row["translation_ko"] = after
    reviewed_rows.append(source_row)
    if correction:
        modifications.append(
            {
                "tm_id": tm_id,
                "source_text": source_row["source_text"],
                "before": before,
                "after": after,
                "category": correction["category"],
                "reason": correction["reason"],
            }
        )

REVIEWED.parent.mkdir(parents=True, exist_ok=True)
REVIEWED.write_text(
    "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in reviewed_rows),
    encoding="utf-8",
)

review_record = {
    "schema": "arf-translation-independent-review-v1",
    "batch_id": "batch_0012",
    "reviewer": "/root/translate_batch_0009",
    "draft_translator": "/root/translate_batch_0008",
    "translation_engine_policy": "Codex internal models only",
    "external_translation_services_used": [],
    "source": "work/translation/tm_v2/batches/source/batch_0012.jsonl",
    "draft": "work/translation/drafts/batch_0012.jsonl",
    "reviewed_output": "work/translation/reviewed/batch_0012.jsonl",
    "reviewed_units": 200,
    "modified_units": len(modifications),
    "unchanged_units": 200 - len(modifications),
    "review_dimensions": [
        "meaning",
        "function",
        "numeric fidelity",
        "proper nouns",
        "natural Korean",
        "particles",
        "control tokens",
        "line breaks",
    ],
    "modifications": modifications,
}
REVIEW_LOG.parent.mkdir(parents=True, exist_ok=True)
REVIEW_LOG.write_text(json.dumps(review_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
