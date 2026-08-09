import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "translation" / "tm_v2" / "batches" / "source" / "batch_0019.jsonl"
DRAFT = ROOT / "translation" / "drafts" / "batch_0019.jsonl"
REVIEWED = ROOT / "translation" / "reviewed" / "batch_0019.jsonl"
REVIEW_LOG = ROOT / "translation" / "reviews" / "batch_0019_review.json"


corrections = {
    "ARF-TM-D698E453F5B4EE105CB7": {
        "after": "<$13>14<$1F>000021<$1F>01<$13>00 중 하나.\n캐릭터의 물 <$13>14<$1F>000014<$1F>01<$13>00을\n상승시킨다.\n<$13>14<$1F>000034<$1F>01<$13>00 상태일 때\n물 내성 상승 효과를 겹치면\n<$13>14<$1F>000034<$1F>01<$13>00의 효과를\n약화하거나 덮어쓸 수\n있다. 이 <$13>14<$1F>000021<$1F>01<$13>00는\n<$13>14<$1F>000022<$1F>01<$13>00이다",
        "category": "help_text_grammar_consistency",
        "reason": "내성 효과를 중첩하는 기능과 소유 관계를 자연스럽고 명확하게 다듬었다.",
    },
    "ARF-TM-D6A0ABB146FA8238B1DE": {
        "after": "물리 공격 시 수생 생물에게 주는\n피해가 크게 상승한다",
        "category": "enemy_type_terminology",
        "reason": "수생 생물 적용 대상을 기존 승인 전투 표기와 통일했다.",
    },
    "ARF-TM-D79919AB8B87238812A5": {
        "after": "<$13>14<$1F>0000F9<$1F>01<$13>00의 남동생인 신.\n『번영』과 『기술 혁신』을\n상징한다고 여겨진다.\n<$13>14<$1F>000147<$1F>01<$13>00의\n<$13>14<$1F>000150<$1F>01<$13>00에서는\n신앙의 대상이 되어\n수많은 사람이\n그 신성에 매료되어 있다",
        "category": "lore_grammar",
        "reason": "弟神을 설명하는 첫 문장의 관형구조를 자연스럽게 고쳤다.",
    },
    "ARF-TM-D7ACEBEE2C4145D567DD": {
        "after": ",가까이에 있어……",
        "category": "meaning_grammar",
        "reason": "「ありて」를 양보의 뜻이 아닌 존재·위치를 나타내는 연용 표현으로 바로잡았다.",
    },
    "ARF-TM-D7B6D3C4C313B085621B": {
        "after": "온갖 무기를 장식하는 진홍빛 술.\n승리를 거두면 더 큰 성과를 얻는다",
        "category": "item_name_consistency",
        "reason": "緋色을 기존 승인 아이템명 '진홍빛 무기 장식'과 맞추고 승리 시의 효과를 자연스럽게 다듬었다.",
    },
    "ARF-TM-D7EF40D3E8A5BBD07895": {
        "after": "고독한 늑대",
        "category": "idiom_naturalness",
        "reason": "一匹狼의 독립적인 인물상을 '고독한 늑대'로 정확하게 옮겼다.",
    },
    "ARF-TM-D7FE1EC96CC49D195394": {
        "after": "캐릭터의 체력을\n수치로 나타낸 것.\n피해를 받는 등의 이유로\n감소하며, 수치가 0이 되면\n<$13>14<$1F>000017<$1F>01<$13>00 상태가 된다.\n여관이나 레벨 업 등\n여러 회복 수단이 존재한다",
        "category": "system_term_naturalness",
        "reason": "레벨 상승이 아닌 레벨 업 행위로 HP가 회복된다는 뜻을 명확히 했다.",
    },
    "ARF-TM-D84F04C6E763812B4A65": {
        "after": "플레임 디토네이터",
        "category": "magic_name_glossary",
        "reason": "고유 마법명을 고정 용어 '플레임 디토네이터'와 일치시켰다.",
    },
    "ARF-TM-D97422F61B0226FB9659": {
        "after": "도적선을 타고 바다로 달아난 라르크 일행은",
        "category": "meaning_particle",
        "reason": "도적선이 이동 수단임을 밝히고 방향 조사를 자연스럽게 고쳤다.",
    },
    "ARF-TM-D9D9A9079E827EAB5FD7": {
        "after": "『<$13>14<$1F>000065<$1F>01<$13>00』와 『<$13>14<$1F>000060<$1F>01<$13>00』을\n차례로 실행하면 발생하는\n<$13>14<$1F>000059<$1F>01<$13>00.\n대상에게 피해를 주면서\n동시에 <$13>14<$1F>000064<$1F>01<$13>00에 <$13>14<$1F>000065<$1F>01<$13>00를\n사용할 수 있다. 주는 피해도\n평소보다 조금\n커진다는 것이 장점\n중 하나다",
        "category": "combo_function_grammar",
        "reason": "제어 토큰을 보존하면서 피해와 훔치기가 동시에 발생하는 연계 기능을 문장으로 완결했다.",
    },
    "ARF-TM-D9E72B184B87E25DE927": {
        "after": "운을 끌어들여\n<$13>14<$1F>00004B<$1F>01<$13>00의 발동 확률을\n높일 수 있는\n<$13>14<$1F>00004B<$1F>01<$13>00.\n일정 확률로 발동하는\n암 포스 이외에는 효과가\n나타나지 않으므로\n주의해야 한다",
        "category": "help_text_lineflow",
        "reason": "고정 용어 '암 포스'가 줄 경계에서 갈라지지 않도록 문장을 재배치했다.",
    },
    "ARF-TM-DA25226CF17B2398C1BA": {
        "after": "조류 피해 때문에 곤란합니다",
        "category": "quest_title_consistency",
        "reason": "후속 퀘스트 제목과 맞춰 鳥害를 '조류 피해'로 통일했다.",
    },
    "ARF-TM-DAA480C84137CE3548CA": {
        "after": "용재해 후 남겨지는 검은 파편.\n착용자에게 성과와 불모함을 동시에 안겨 준다",
        "category": "item_flavor_naturalness",
        "reason": "不毛의 추상적 성질을 자연스러운 명사형 '불모함'으로 표현했다.",
    },
    "ARF-TM-DADEB3086280655C4077": {
        "after": "<$13>14<$1F>00009D<$1F>01<$13>00 중 하나.\n단일 대상에게 효과가 높은\n공격 계열 <$13>14<$1F>000061<$1F>01<$13>00이 많은\n속성이다.\n이 속성은 <$13>14<$1F>00009F<$1F>01<$13>00와\n<$13>14<$1F>0000AD<$1F>01<$13>00한다",
        "category": "battle_term_consistency",
        "reason": "攻撃系를 기존 헬프 문구의 '공격 계열'과 통일했다.",
    },
    "ARF-TM-DBEB0238B1E587D6B5F1": {
        "after": "공화국을 남북으로 가르는\n대하는 밀레그리스다.\n공화국 건국 초기에는\n밀레그리스를 중심으로 문명이\n발달했다고 전해진다.\n공화국의 젖줄인 대하 밀레그리스는\n여러 지류로 갈라져\n지금도 공화국을 풍요롭게\n하고 있다",
        "category": "lore_naturalness",
        "reason": "공화국의 성립 시기와 모체와 같은 대하의 역할을 자연스러운 한국어로 다듬었다.",
    },
    "ARF-TM-DCC795E2FA1A9A70B55E": {
        "after": "공들인 장난을 떠올리게 하는 슈트\n묘한 색감과 마름모 조합이 독특하다",
        "category": "item_flavor_naturalness",
        "reason": "의상 디자인이 연상시키는 冗談을 문맥에 맞는 '장난'으로 옮겼다.",
    },
    "ARF-TM-DD50AA633F137EE0DB57": {
        "after": "<$13>14<$1F>000141<$1F>01<$13>00의 수도이자\n모든 오르키나교도의\n성지인 곳, 바로\n교도 안트락스다.\n<$13>14<$1F>000145<$1F>01<$13>00은 3대 종교\n중 신자가 가장 적다.\n하지만 신자 대부분은 독실하며\n오직 가르침에 목숨을 바치고자\n살아가는 것으로 알려져 있다",
        "category": "lore_meaning_naturalness",
        "reason": "오르키나교도와 성지의 소유 관계를 바로잡고 教えに殉ずる의 헌신적 의미를 자연스럽게 옮겼다.",
    },
    "ARF-TM-DD658BB4B72CFB0C302B": {
        "after": "보기에는 사랑스러운 드레스지만 사실은\n싸우는 소녀를 위해 만든 특별 제작품",
        "category": "item_flavor_naturalness",
        "reason": "'특별품'의 어색한 압축을 의상 설명에 맞는 '특별 제작품'으로 다듬었다.",
    },
    "ARF-TM-DEB4B7492788EF35E2FA": {
        "after": "오이겐 관련 이벤트?\n아니면 마리아 관련?",
        "category": "developer_text_naturalness",
        "reason": "반복되는 関む·がらみ를 간결한 개발용 확인 문구로 다듬었다.",
    },
    "ARF-TM-DF72FD629B2E556011C4": {
        "after": "은빛 칼날이 아름다운 단정한 대검.\n소지자의 공격력을 항상 높여 준다",
        "category": "item_effect_naturalness",
        "reason": "장비가 소지자에게 상시 공격력 상승을 부여한다는 주체 관계를 명확히 했다.",
    },
    "ARF-TM-E0D3E2B4901DD960CED0": {
        "after": "<$13>14<$1F>000131<$1F>01<$13>00군은\n정식으로 채용된 장병과\n군비 절감을 위해\n황실 소속으로 채용된\n<$13>14<$1F>00013E<$1F>01<$13>00로\n편성되어 있다.\n주력 공정단은 <$13>14<$1F>0000EA<$1F>01<$13>00와의\n전투에서 제도의 요새\n역할을 하는 부대다",
        "category": "lore_grammar",
        "reason": "황실 소속 채용 형식과 대적 전투 관계를 자연스러운 조사로 정리했다.",
    },
    "ARF-TM-E1484A3C4CFD488D620D": {
        "after": "범위 내 대상의 ATK/MGC 상승\n자신 주변에 발동",
        "category": "battle_phrase_consistency",
        "reason": "동일한 범위형 특수기 설명의 '자신 주변에 발동' 표기와 통일했다.",
    },
    "ARF-TM-E1B50EA96B8E402695EA": {
        "after": "<$19>필연",
        "category": "title_naturalness",
        "reason": "必定의 의미를 현대 한국어에서 자연스러운 '필연'으로 옮겼다.",
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
    "batch_id": "batch_0019",
    "reviewer": "/root/translate_batch_0009",
    "draft_translator": "/root/audit_boundary_integration",
    "independent_review": True,
    "translation_engine_policy": "Codex internal models only",
    "external_translation_services_used": [],
    "external_translation_models_or_apis_used": [],
    "source": "work/translation/tm_v2/batches/source/batch_0019.jsonl",
    "draft": "work/translation/drafts/batch_0019.jsonl",
    "reviewed_output": "work/translation/reviewed/batch_0019.jsonl",
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
