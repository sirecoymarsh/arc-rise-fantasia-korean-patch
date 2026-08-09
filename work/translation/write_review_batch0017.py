import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "translation" / "tm_v2" / "batches" / "source" / "batch_0017.jsonl"
DRAFT = ROOT / "translation" / "drafts" / "batch_0017.jsonl"
REVIEWED = ROOT / "translation" / "reviewed" / "batch_0017.jsonl"
REVIEW_LOG = ROOT / "translation" / "reviews" / "batch_0017_review.json"


corrections = {
    "ARF-TM-BDFA11E457222E71696C": {
        "after": "<$13>14<$1F>0000A1<$1F>01<$13>00 레벨 1의 <$13>14<$1F>000061<$1F>01<$13>00.\n아군 1명을 <$13>14<$1F>000037<$1F>01<$13>00\n상태로 만든다.\n<$13>14<$1F>0000B0<$1F>01<$13>00의\n샌드 커튼에서는\n<$13>14<$1F>000037<$1F>01<$13>00의 효과량이\n커진다",
        "category": "help_text_grammar",
        "reason": "「サンドカーテンでは」를 ‘샌드 커튼에서는’으로 바로잡아 해당 증폭기에서 효과량이 커진다는 기능을 명확히 했다.",
    },
    "ARF-TM-BE070D3FAD0F42F346A3": {
        "after": "범위 내 대상에게 바람 속성 피해\n추가 효과: SPD 하락",
        "category": "battle_function_terminology",
        "reason": "범위 공격의 적용 대상을 기존 전투 설명 템플릿에 맞게 명시했다.",
    },
    "ARF-TM-C036609AE9BFAF3366D1": {
        "after": "망고슈",
        "category": "weapon_name",
        "reason": "프랑스계 단검명 main-gauche의 통용 한국어 표기에 맞춰 고유 장비명을 교정했다.",
    },
    "ARF-TM-C0C9BCA59340884756EF": {
        "after": "척추를 떠올리게 하는 은백색 검.\n소지자는 때로 결정적인 일격을 날린다",
        "category": "natural_korean",
        "reason": "白銀의 색채 표현을 자연스러운 한국어 ‘은백색’으로 다듬었다.",
    },
    "ARF-TM-C10305AAD48523F34F42": {
        "after": "아주 커다란 뿔.\n집에 장식해 두면 자랑거리가 된다",
        "category": "natural_korean",
        "reason": "‘매우 거대한’의 중복감을 줄이고 장식물이 자랑거리가 된다는 뜻을 자연스럽게 옮겼다.",
    },
    "ARF-TM-C18696E13F074B2C14AC": {
        "after": "아다만그리브",
        "category": "item_series_consistency",
        "reason": "기존 승인 장비명 ‘아다만가드’, ‘아다만기아’와 같은 계열의 붙여쓰기 형식으로 통일했다.",
    },
    "ARF-TM-C269B113CA630D5F8A58": {
        "after": "나무 역할",
        "category": "meaning_naturalness",
        "reason": "의상 설명 문맥의 役을 역(驛)이 아닌 배역·역할의 뜻으로 명확히 옮겼다.",
    },
    "ARF-TM-C412CCF21CCCB7BEE4C5": {
        "after": "전체에게 물 속성 피해",
        "category": "battle_function_terminology",
        "reason": "전체 대상 피해 문구를 기존 전투 설명 표기와 통일했다.",
    },
    "ARF-TM-C4DE5566DFB0BD4A0229": {
        "after": "범위 내 대상에게 불 속성 피해",
        "category": "battle_function_terminology",
        "reason": "범위 공격의 적용 대상을 기존 전투 설명 템플릿에 맞게 명시했다.",
    },
    "ARF-TM-C52F620AD1DC7E296E7C": {
        "after": "<$13>14<$1F>0000A1<$1F>01<$13>00 레벨 2의 <$13>14<$1F>000061<$1F>01<$13>00.\n단일 적에게 <$13>14<$1F>0000A1<$1F>01<$13>00 피해를\n준다.\n<$13>14<$1F>0000B0<$1F>01<$13>00의\n어스 트랩에서는\n추가 효과로 대상을\n<$13>14<$1F>00001B<$1F>01<$13>00 상태로 만들 때가 있다",
        "category": "help_text_grammar",
        "reason": "「アーストラップでは」를 ‘어스 트랩에서는’으로 교정해 증폭기 고유 추가 효과임을 분명히 했다.",
    },
    "ARF-TM-C534751D184E12433473": {
        "after": "<$13>14<$1F>00009F<$1F>01<$13>00 레벨 3의 <$13>14<$1F>000061<$1F>01<$13>00.\n대상을 중심으로 한 범위 내\n아군의 <$13>14<$1F>000003<$1F>01<$13>00를 회복한다.\n<$13>14<$1F>0000B0<$1F>01<$13>00의\n힐 레인에서는 추가 효과로\n<$13>14<$1F>000017<$1F>01<$13>00 이외의\n<$13>14<$1F>000016<$1F>01<$13>00를 무작위로 하나,\n<$13>14<$1F>000021<$1F>01<$13>00로 인한\n능력치 하락을 회복한다",
        "category": "help_text_grammar",
        "reason": "「ヒールレインでは」를 ‘힐 레인에서는’으로 교정해 증폭기에서 발생하는 추가 효과임을 명확히 했다.",
    },
    "ARF-TM-C53D8D14C8DDAB5AE170": {
        "after": "광소술을 사용하는 행동을 하지 않습니다.\n그 외에는 『알아서』와 동일합니다",
        "category": "system_voice_consistency",
        "reason": "AI 작전 설명의 원문 존댓말과 인접 설명의 시스템 문체를 보존했다.",
    },
    "ARF-TM-C5413E23320E0954E9C4": {
        "after": "전체에게 어둠 속성 피해\n추가 효과: 모든 능력치 하락",
        "category": "battle_function_terminology",
        "reason": "전체 피해 대상 표기와 全能力의 능력치 범위를 전투 용어 규칙에 맞게 교정했다.",
    },
    "ARF-TM-C6CEA220B7CE7691CF9C": {
        "after": "비광정으로 현지로 향하는 라르크 일행",
        "category": "particle_naturalness",
        "reason": "방향을 나타내는 ‘현지에 향하는’을 자연스러운 조사 ‘현지로 향하는’으로 교정했다.",
    },
    "ARF-TM-C75B6A28642D36A9858B": {
        "after": "용사가 된 소녀가 애용하기에 알맞은 건틀릿.\n여정을 마친 용사는 자신이 있어야 할 곳으로 돌아간다",
        "category": "item_flavor_naturalness",
        "reason": "愛用すべき의 권장·적합 의미를 부자연스러운 의무 표현 없이 자연스럽게 옮겼다.",
    },
    "ARF-TM-C7903A02135134A7208C": {
        "after": "어둠 속에서 속삭이는 자",
        "category": "meaning_particle",
        "reason": "闇に가 속삭임의 대상이 아니라 장소를 나타내는 문맥임을 반영했다.",
    },
    "ARF-TM-C7DD7FA90F312E9918ED": {
        "after": "P-00",
        "category": "identifier_typography",
        "reason": "영문·숫자 식별자의 구분 기호를 기존 승인 형식인 ASCII 하이픈으로 통일했다.",
    },
    "ARF-TM-C7F395F42B50FB4F1167": {
        "after": "SP 획득량 상승",
        "category": "system_term_naturalness",
        "reason": "효과 설명의 SP 증가량과 대응하도록 取得アップ을 자연스러운 ‘획득량 상승’으로 명시했다.",
    },
    "ARF-TM-C86F2B2568E6AA25FC91": {
        "after": "음의 시대에 존재했다는 왕가의 유산.\n소지자의 방어력을 일시적으로 상승시킨다",
        "category": "lore_term_consistency",
        "reason": "세계관 시대명 負の時代를 기존 승인 표기 ‘음의 시대’와 일치시켰다.",
    },
    "ARF-TM-C8ED5F80B4C925BED71F": {
        "after": "캐릭터에게 어떤\n변화가 생긴 상태.\n능력치가 변하거나 자신에게\n유리한 효과가 나타나기도 한다.\n상태 변화에는 <$13>14<$1F>000022<$1F>01<$13>00와\n<$13>14<$1F>000023<$1F>01<$13>00가 있다.\n모든 상태 변화는\n전투 종료 시 효과가 사라진다",
        "category": "help_text_meaning_naturalness",
        "reason": "能力の変化를 능력치 변화로 명확히 하고 유리한 효과의 존재를 자연스러운 한국어로 다듬었다.",
    },
    "ARF-TM-C8F5F496835B3D0D711D": {
        "after": "세상의 모든 물질을\n구성하는 코드. 그 성질을\n올바르게 이해하는 동시에\n제어해 여러 효과를\n일으키는 <$13>14<$1F>000061<$1F>01<$13>00의 사용자를\n코더라고 부른다.\n군에 속한 자도 있고\n민간에서 살아가는 자도\n있다",
        "category": "meaning_naturalness",
        "reason": "市井를 시장이나 시중이 아니라 군에 속하지 않은 민간이라는 문맥에 맞게 교정했다.",
    },
    "ARF-TM-C915C2DE8B9D97F6434F": {
        "after": "은빛 양날에 빛이 흐르는 단정한 대검.\n소지자의 공격력을 항상 높여 준다",
        "category": "item_effect_naturalness",
        "reason": "장비가 소지자에게 상시 공격력 상승을 부여한다는 주체 관계를 자연스럽게 표현했다.",
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
    "batch_id": "batch_0017",
    "reviewer": "/root/translate_batch_0009",
    "draft_translator": "/root/translate_batch_0008",
    "independent_review": True,
    "translation_engine_policy": "Codex internal models only",
    "external_translation_services_used": [],
    "external_translation_models_or_apis_used": [],
    "source": "work/translation/tm_v2/batches/source/batch_0017.jsonl",
    "draft": "work/translation/drafts/batch_0017.jsonl",
    "reviewed_output": "work/translation/reviewed/batch_0017.jsonl",
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
    "verification_execution": {
        "status": "deferred_by_user_instruction",
        "executed_tools": [],
        "not_executed": ["validator", "fit", "encoding", "boundary_audit"],
        "note": "사용자 지시에 따라 별도 validator, fit, encoding, boundary audit를 실행하지 않았다.",
    },
}

REVIEW_LOG.parent.mkdir(parents=True, exist_ok=True)
REVIEW_LOG.write_text(json.dumps(review_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
