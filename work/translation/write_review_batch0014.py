import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "translation" / "tm_v2" / "batches" / "source" / "batch_0014.jsonl"
DRAFT = ROOT / "translation" / "drafts" / "batch_0014.jsonl"
REVIEWED = ROOT / "translation" / "reviewed" / "batch_0014.jsonl"
REVIEW_LOG = ROOT / "translation" / "reviews" / "batch_0014_review.json"


corrections = {
    "ARF-TM-996CD4C867926D0592C0": {
        "after": "외눈 가면을 쓴 여왕을 본뜬 목걸이.\n소리 없이 다가오는 어둠 같은 몸놀림을 선사한다",
        "category": "naturalness",
        "reason": "목걸이가 착용자에게 몸놀림을 부여한다는 주체 관계를 자연스럽게 다듬었다.",
    },
    "ARF-TM-999ED3492D24122BDFFE": {
        "after": "고탑 꼭대기에서 1000년간 바람을 맞은 검.\n손에 든 자에게 바람의 가호가 깃든다",
        "category": "meaning/naturalness",
        "reason": "手にした者를 검을 손에 든 사람이라는 문맥에 맞게 교정했다.",
    },
    "ARF-TM-9A94E7BF6FB177E05880": {
        "after": "범위 내 대상에게 물 속성 피해",
        "category": "battle-function/terminology",
        "reason": "범위 공격의 적용 대상을 전투 설명 템플릿에 맞게 명시했다.",
    },
    "ARF-TM-9B9544CB61E931C6D527": {
        "after": "사용하면\n<$13>14<$1F>000043<$1F>01<$13>00에 대해\n<$13>14<$1F>000049<$1F>01<$13>00 효과를\n얻을 수 있게 된다.\n<$13>14<$1F>000026<$1F>01<$13>00와 달리\n공격받기 전까지는\n효과가 절대 줄어들지 않는\n안심하고 쓸 수 있는\n<$13>14<$1F>00004B<$1F>01<$13>00이다",
        "category": "naturalness/line-break",
        "reason": "서술어가 마지막 줄에 홀로 남지 않도록 문장과 줄바꿈을 자연스럽게 재배치했다.",
    },
    "ARF-TM-9BA8783789FF1AF09C17": {
        "after": "『<$13>14<$1F>000076<$1F>01<$13>00』와 『<$13>14<$1F>00006A<$1F>01<$13>00』를\n연속으로 실행하면 발생하는\n<$13>14<$1F>000059<$1F>01<$13>00.\n대상이 가진 <$13>14<$1F>000007<$1F>01<$13>00에 <$13>14<$1F>000076<$1F>01<$13>00를 사용해\n자신의 것으로 만들 수\n있다. 단, <$13>14<$1F>000064<$1F>01<$13>00은\n훔칠 수 없게 된다. 상대에게서\n빼앗은 힘으로 쓰러뜨린다.\n이보다 더한 굴욕은 없다",
        "category": "meaning/grammar",
        "reason": "명령 이름을 억지로 용언화한 표현을 풀고 ‘아이템’ 토큰에 맞는 조사를 적용했다.",
    },
    "ARF-TM-9CCB0AAD8DC0448E1087": {
        "after": "<$13>14<$1F>000016<$1F>01<$13>00 중 하나.\n<$13>14<$1F>000003<$1F>01<$13>00가 0이 되었을 때\n자동으로 발생한다.\n어떠한 <$13>14<$1F>000000<$1F>01<$13>00도 할 수 없고\n전투 참가자 슬롯에서도 제외되어\n<$13>14<$1F>000004<$1F>01<$13>00가 감소한다.\n이 <$13>14<$1F>000016<$1F>01<$13>00은\n전투 종료 시 회복된다",
        "category": "battle-function/grammar/line-break",
        "reason": "전투 불능 시 행동 불가·참가 슬롯 제외 효과를 명확히 하고 상태 이상 토큰의 조사와 줄바꿈을 교정했다.",
    },
    "ARF-TM-9DA86C925E96F599F7F2": {
        "after": "범위 내 대상에게 땅 속성 피해\n추가 효과: 바람 내성 하락",
        "category": "battle-function/terminology",
        "reason": "범위 공격의 적용 대상을 전투 설명 템플릿에 맞게 명시했다.",
    },
    "ARF-TM-9E8BC1E235EC8DDB7E2D": {
        "after": "레이를 띤 특수 금속이 쓰인 부품",
        "category": "meaning/naturalness",
        "reason": "부품에 특수 금속이 사용되었다는 원문의 관계를 더 정확하고 자연스럽게 표현했다.",
    },
    "ARF-TM-9E8EBEBDE7A47CD062FF": {
        "after": "지정한 아군이 받는\n모든 피해를 대신\n받는 <$13>14<$1F>00004B<$1F>01<$13>00.\n캐릭터를 반드시\n지키고 싶을 때 쓰면\n좋을 것이다.\n이 <$13>14<$1F>00004B<$1F>01<$13>00은\n사용한 턴에만\n유효하다",
        "category": "grammar",
        "reason": "‘암 포스’ 토큰 뒤의 조사를 받침에 맞게 교정했다.",
    },
    "ARF-TM-9F174893AB22C77B01D9": {
        "after": "불/물/바람/땅의 4대 원소가 조화를 이루는 명검.\n속성 공격을 강화하는 힘을 품고 있다",
        "category": "meaning/naturalness",
        "reason": "四大元素が奏でる의 비유와 장비 성능을 자연스러운 한국어로 다듬었다.",
    },
    "ARF-TM-A0284FB7B5FCB6FE9D41": {
        "after": "짙고 차분하게 물들인 옷에는 풀헤임에서\n좀처럼 보기 드문 품격이 서려 있다",
        "category": "naturalness",
        "reason": "‘보기 드문 종류의 품격’이라는 번역투 표현을 자연스럽게 교정했다.",
    },
    "ARF-TM-A11A6AFABBF951BED98C": {
        "after": "전체에게 바람 속성 피해\n추가 효과: 땅 내성 하락",
        "category": "battle-function/terminology",
        "reason": "전체 대상 피해 문구를 기존 전투 설명 표기와 통일했다.",
    },
    "ARF-TM-A16C1A6444D6297C0EB4": {
        "after": "<$13>14<$1F>000021<$1F>01<$13>00 중 하나.\n캐릭터의 <$13>14<$1F>000003<$1F>01<$13>00\n최대치를 2배로 만든다.\n이 <$13>14<$1F>000021<$1F>01<$13>00는\n<$13>14<$1F>000023<$1F>01<$13>00이다",
        "category": "naturalness/line-break",
        "reason": "HP 최대치 설명의 어순을 다듬고 서술어가 마지막 줄에 홀로 남지 않도록 재배치했다.",
    },
    "ARF-TM-A17A08E9ED185340E7F5": {
        "after": "『<$13>14<$1F>00007A<$1F>01<$13>00』를\n2회 연속 실행하면 발생\n하는 <$13>14<$1F>000059<$1F>01<$13>00.\n『<$13>14<$1F>00007A<$1F>01<$13>00』의\n효과를 높일 수 있다.\n이것만 있으면 어떤 맹공에도\n안심……할 수 있을지도 모른다",
        "category": "grammar/line-break",
        "reason": "조사 ‘에도’가 다음 줄에 홀로 남은 문제와 어색한 서술을 함께 교정했다.",
    },
    "ARF-TM-A1D15979D58625510DA4": {
        "after": "홀로 제국병을 맞아 싸우러 간 오이겐.",
        "category": "meaning/naturalness",
        "reason": "迎え撃つ가 적을 맞아 싸운다는 의미임을 반영하고 ‘단 1명이서’를 자연스럽게 다듬었다.",
    },
    "ARF-TM-A2ACE32BFB947EE29B91": {
        "after": "몸을 여유롭게 감싸는 잠옷은\n편안함과 약간의 그리움을 안겨 준다",
        "category": "naturalness",
        "reason": "잠옷의 헐렁하고 편안한 착용감을 자연스러운 한국어로 표현했다.",
    },
    "ARF-TM-A2EDEDC1A37B619FA5C5": {
        "after": "<$13>14<$1F>00009F<$1F>01<$13>00 레벨 2의 <$13>14<$1F>000061<$1F>01<$13>00.\n단일 적에게 <$13>14<$1F>00009F<$1F>01<$13>00 피해를\n준다.\n<$13>14<$1F>0000B0<$1F>01<$13>00의\n레인 애로에서는\n추가 효과로 대상을\n<$13>14<$1F>000019<$1F>01<$13>00 상태로 만들기도 한다",
        "category": "battle-function/naturalness",
        "reason": "敵単体의 대상을 ‘단일 적’으로 자연스럽고 명확하게 표현했다.",
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
    "batch_id": "batch_0014",
    "reviewer": "/root/translate_batch_0009",
    "draft_translator": "/root/translate_batch_0008",
    "translation_engine_policy": "Codex internal models only",
    "external_translation_services_used": [],
    "source": "work/translation/tm_v2/batches/source/batch_0014.jsonl",
    "draft": "work/translation/drafts/batch_0014.jsonl",
    "reviewed_output": "work/translation/reviewed/batch_0014.jsonl",
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
