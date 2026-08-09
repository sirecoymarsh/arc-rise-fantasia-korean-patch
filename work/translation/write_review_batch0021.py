import json
from pathlib import Path


BATCH_ID = "batch_0021"
SOURCE_PATH = Path("work/translation/tm_v2/batches/source/batch_0021.jsonl")
DRAFT_PATH = Path("work/translation/drafts/batch_0021.jsonl")
REVIEWED_PATH = Path("work/translation/reviewed/batch_0021.jsonl")
REPORT_PATH = Path("work/translation/reviews/batch_0021_review.json")


REVISIONS = {
    "ARF-TM-EE3ED8C73D1C4E2425C9": {
        "after": "카르분클루스에 있는\n하모니 홀 관장의 의뢰다.\n마지막 멤버가 있는 곳을 알아낸 모양이다.\n자세한 이야기는 관장에게 들어 봐.\n　\n※진행 중 포기할 수 없는 퀘스트입니다",
        "category": "quest_text_naturalness",
        "reason": "「聞いてくれ」를 앞선 연속 퀘스트와 같은 자연스러운 요청형인 ‘들어 봐’로 바로잡았다.",
    },
    "ARF-TM-EEC33739EAC9E1082416": {
        "after": "전투 중 화면 오른쪽 아래에\n표시되는 카드.\n왼쪽부터 <$13>14<$1F>000000<$1F>01<$13>00 순서가\n빠른 순으로 나열되어 있다.\n턴 카드에서는\n<$13>14<$1F>000000<$1F>01<$13>00 순서뿐만 아니라\n깜빡이는 아이콘을 통해\n적의 <$13>14<$1F>000000<$1F>01<$13>00도 어느 정도\n예측할 수 있다",
        "category": "help_text_naturalness_and_line_breaks",
        "reason": "조사와 용언이 어색하게 갈라진 줄바꿈 및 ‘빠른 순서대로’의 중복을 고치고, 아이콘으로 적의 행동을 예측하는 기능을 자연스럽게 정리했다.",
    },
    "ARF-TM-EF58353838B9B4768DAA": {
        "after": "물리 공격 시 곤충계에게 주는\n피해가 증가한다",
        "category": "battle_function_terminology",
        "reason": "동일한 곤충계 특공 설명의 검수 용어와 효과 문장인 ‘피해가 증가한다’에 맞췄다.",
    },
    "ARF-TM-EF86E1B281E01F93995B": {
        "after": "<$15>01물리 공격 시 곤충계에게 주는\n피해가 크게 증가한다",
        "category": "battle_function_terminology",
        "reason": "동일한 곤충계 특공 설명의 검수 용어를 적용하고 ‘大きく’의 강도를 유지한 채 자연스러운 효과 문장으로 고쳤다.",
    },
    "ARF-TM-EFC566AC5DA4513BA95A": {
        "after": "하늘을 뒤덮을 만큼 거대한 얼음벽은\n어떻게 이 세계에 나타난\n것일까? 사람들은 그곳에 신비가\n개입했다고 여겨 설희의 전설을\n만들어 냈다고도 할 수 있다.\n지금도 대빙벽 탄생의 수수께끼는\n풀리지 않은 채 남아 있으며\n옛 신비 또한 사라지지 않은 채\n고스란히 남아 있다",
        "category": "lore_text_naturalness",
        "reason": "‘사라지지 않고 현존하고 있다’의 중복 표현을 자연스럽게 다듬으면서 옛 신비가 지금도 남아 있다는 뜻을 보존했다.",
    },
    "ARF-TM-EFCF680E0F5A38B36E83": {
        "after": "<$13>14<$1F>0000E8<$1F>01<$13>00의 물질은\n복잡하게 얽힌 코드로\n짜인 존재라 할 수 있다.\n이는 <$13>14<$1F>0000EF<$1F>01<$13>00라는\n특별한 존재도 마찬가지\n이며, 그들 또한\n몸에 새겨진 코드가\n개변되면 심신에\n이상이 생기고 만다",
        "category": "lore_text_grammar",
        "reason": "수동 표현 ‘개변당하면’을 ‘코드가 개변되면’으로 고쳐 문장 구조를 자연스럽게 했다.",
    },
    "ARF-TM-EFE49034EBA623A35FB4": {
        "after": "라르크는 다음 임무를 위해 움직이기 시작한다",
        "category": "story_summary_naturalness",
        "reason": "「次の任務に向けて」의 목적 관계를 한국어의 자연스러운 ‘다음 임무를 위해’로 옮겼다.",
    },
    "ARF-TM-F14DA290A5576E153F27": {
        "after": "자신의 ATK/SPD 상승",
        "category": "system_term_consistency",
        "reason": "복수 능력치 표기를 프로젝트의 슬래시 형식으로 통일했다.",
    },
    "ARF-TM-F1C4C4636046EAA6479E": {
        "after": "<$13>14<$1F>00009E<$1F>01<$13>00 레벨 1의 <$13>14<$1F>000061<$1F>01<$13>00.\n단일 대상에게 <$13>14<$1F>00009E<$1F>01<$13>00 피해를\n준다.\n<$13>14<$1F>0000B0<$1F>01<$13>00의\n플레임 디토네이터에서는\n주는 피해가\n크게 증가한다",
        "category": "battle_target_terminology",
        "reason": "「敵単体」를 전투 설명의 고정 범위 용어인 ‘단일 대상’으로 통일했다.",
    },
    "ARF-TM-F25E359359C51B0DC236": {
        "after": "메리디아군 하급 병사에게 지급되는 군복\n흐트러진 차림은 애초에 고려 대상이 아니다",
        "category": "item_flavor_naturalness",
        "reason": "「想定外となっている」를 직역한 어색한 과거형을 현재의 설정 설명에 맞게 자연스럽게 다듬었다.",
    },
    "ARF-TM-F34C90CB70D6D721BBE1": {
        "after": "자신의 ATK/DEF 상승",
        "category": "system_term_consistency",
        "reason": "복수 능력치 표기를 프로젝트의 슬래시 형식으로 통일했다.",
    },
    "ARF-TM-F3BDB552C494F2ADA6BC": {
        "after": "장군에게 지급되는 두려움과 경의의 상의.\n방어력과 저항력을 높인다",
        "category": "item_flavor_meaning",
        "reason": "「畏怖と敬意」의 서로 다른 의미를 ‘두려움과 경의’로 분명히 구분했다.",
    },
    "ARF-TM-F45A64DBFD2ADB3C59B5": {
        "after": "적에게서 얻는 리코가 증가한다",
        "category": "battle_function_grammar",
        "reason": "획득 리코가 증가한다는 효과의 주어와 서술어를 명확히 했다.",
    },
    "ARF-TM-F46511B55CE6D65C1C96": {
        "after": "지나치게 묵직한 구조 탓에\n착용자의 움직임을 둔하게 만드는 인형탈",
        "category": "item_series_consistency",
        "reason": "「きぐるみ」를 기존 검수 장비명 표기인 ‘인형탈’로 통일했다.",
    },
    "ARF-TM-F48B79E3B5D9C04FF331": {
        "after": "상태 이상과 상태 변화를 양도한다\n자신을 제외한 대상에게 발동",
        "category": "battle_function_naturalness",
        "reason": "「自分以外」를 자연스러운 제외 대상 표현으로 고쳐 적용 범위를 명확히 했다.",
    },
    "ARF-TM-F4ABF7FD6A743A6D5277": {
        "after": "※이식　잠옷 05",
        "category": "developer_label_consistency",
        "reason": "같은 ‘寝間着 01~04’ 계열과 숫자 앞 띄어쓰기를 통일했다.",
    },
    "ARF-TM-F7318AA58236C5949EBE": {
        "after": "<$13>14<$1F>000021<$1F>01<$13>00 중 하나.\n캐릭터의 불 <$13>14<$1F>000014<$1F>01<$13>00를\n상승시킨다.\n<$13>14<$1F>000032<$1F>01<$13>00 상태일 때\n불 내성 상승 효과를 중첩하면\n<$13>14<$1F>000032<$1F>01<$13>00의 효과를\n약화하거나 덮어쓸 수\n있다. 이 <$13>14<$1F>000021<$1F>01<$13>00는\n<$13>14<$1F>000022<$1F>01<$13>00이다",
        "category": "help_text_line_breaks",
        "reason": "‘덮어쓸 수 있다’의 용언 덩어리가 부자연스럽게 갈라지지 않도록 원래 줄 수 안에서 재배치했다.",
    },
    "ARF-TM-F7E4213CEC2B65CF086E": {
        "after": "다람쥐 인형탈",
        "category": "item_series_consistency",
        "reason": "「きぐるみ」 장비명의 기존 검수 표기인 ‘인형탈’을 적용했다.",
    },
    "ARF-TM-F892613465621E9AEBC9": {
        "after": "기쁨을 노래하는 아이들이 목에 두른 스카프.\n착용하면 몸에 힘을 불어넣어 준다",
        "category": "item_flavor_grammar",
        "reason": "스카프를 두른 주체가 아이들이 되도록 관형절의 잘못된 조사를 바로잡았다.",
    },
    "ARF-TM-F89AF5043C4BFC92C07C": {
        "after": "슬림한 외투",
        "category": "item_name_meaning",
        "reason": "「細身」가 외투의 가늘고 슬림한 형태를 가리키도록 의미를 바로잡았다.",
    },
    "ARF-TM-F9181A921A5996AC5D5D": {
        "after": "물리 공격 시 불사 계열에게 주는\n피해가 증가한다",
        "category": "battle_function_terminology",
        "reason": "동일한 불사 계열 특공 용어를 유지하면서 효과 서술을 자연스러운 ‘피해가 증가한다’로 고쳤다.",
    },
}


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


source_rows = read_jsonl(SOURCE_PATH)
draft_rows = read_jsonl(DRAFT_PATH)
draft_by_id = {row["tm_id"]: row for row in draft_rows}

if len(source_rows) != 200 or len(draft_rows) != 200:
    raise RuntimeError("batch_0021 must contain exactly 200 units")
if [row["tm_id"] for row in source_rows] != [row["tm_id"] for row in draft_rows]:
    raise RuntimeError("source/draft ID order mismatch")
if set(REVISIONS) - set(draft_by_id):
    raise RuntimeError("revision ID missing from draft")

reviewed_rows = []
modifications = []
for draft_row in draft_rows:
    reviewed_row = dict(draft_row)
    revision = REVISIONS.get(draft_row["tm_id"])
    if revision is not None:
        before = draft_row["translation_ko"]
        after = revision["after"]
        reviewed_row["translation_ko"] = after
        modifications.append(
            {
                "tm_id": draft_row["tm_id"],
                "source_text": draft_row["source_text"],
                "before": before,
                "after": after,
                "category": revision["category"],
                "reason": revision["reason"],
            }
        )
    reviewed_rows.append(reviewed_row)

REVIEWED_PATH.parent.mkdir(parents=True, exist_ok=True)
REVIEWED_PATH.write_text(
    "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in reviewed_rows)
    + "\n",
    encoding="utf-8",
)

report = {
    "schema": "arf-translation-independent-review-v1",
    "batch_id": BATCH_ID,
    "reviewer": "/root/translate_batch_0008",
    "draft_translator": "/root/translate_batch_0009",
    "independent_review": True,
    "translation_engine_policy": "Codex internal models only",
    "external_translation_services_used": [],
    "external_translation_models_or_apis_used": [],
    "source": SOURCE_PATH.as_posix(),
    "draft": DRAFT_PATH.as_posix(),
    "reviewed_output": REVIEWED_PATH.as_posix(),
    "reviewed_units": len(reviewed_rows),
    "modified_units": len(modifications),
    "unchanged_units": len(reviewed_rows) - len(modifications),
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
    "verification_execution": {
        "status": "deferred_by_parent_instruction",
        "executed_tools": [],
        "not_executed": ["validator", "fit", "encoding", "boundary_audit"],
        "note": "상위 작업 지시에 따라 별도 validator, fit, encoding, boundary audit를 실행하지 않았다.",
    },
    "modifications": modifications,
}

REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
REPORT_PATH.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps({"reviewed_units": len(reviewed_rows), "modified_units": len(modifications)}))
