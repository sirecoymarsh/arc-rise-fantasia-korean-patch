import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "work/translation/tm_v2/batches/source/batch_0005.jsonl"
DRAFT = ROOT / "work/translation/drafts/batch_0005.jsonl"
REVIEWED = ROOT / "work/translation/reviewed/batch_0005.jsonl"
CHANGES = ROOT / "work/translation/reviews/batch_0005_changes.json"


edits = {
    "ARF-TM-27128F4825E6D3F8D7F0": {
        "translation_ko": "<$13>14<$1F>000021<$1F>01<$13>00 중 하나.\n캐릭터가 <$13>14<$1F>000046<$1F>01<$13>00로\n받는 피해가 증가한다.\n<$13>14<$1F>00002A<$1F>01<$13>00 상태일 때\nRES 하락 효과를 중첩하면\n<$13>14<$1F>00002A<$1F>01<$13>00의 효과를\n약화시키거나 덮어쓸 수\n있다. 이 <$13>14<$1F>000021<$1F>01<$13>00은\n<$13>14<$1F>000022<$1F>01<$13>00이다",
        "category": "system_template_naturalness",
        "reason": "상태 변화 도움말의 반복 템플릿을 앞선 검수본과 맞추고, 타동 표현을 자연스럽게 다듬었다.",
    },
    "ARF-TM-2864BD55239C7263831C": {
        "translation_ko": "희귀한 휘석에 레이 결정을 융합한 것.\n소지자는 석화에 걸리지 않게 된다",
        "category": "meaning_naturalness",
        "reason": "신체가 석화를 ‘막아 낸다’는 어색한 의역을 석화 면역의 실제 의미가 분명한 문장으로 바로잡았다.",
    },
    "ARF-TM-27CFA1039F83ACF9A217": {
        "translation_ko": "세레나 붉은 보석",
        "category": "fixed_field_capacity",
        "reason": "색과 보석 의미를 유지하면서 아이템명 고정 필드의 NUL 포함 17바이트 한도에 맞췄다.",
    },
    "ARF-TM-28B276C7BA61227DC078": {
        "translation_ko": "세실이 자신을 소개할 때 하는 말.\n용사의 길을 설파하는 것치고는\n<$13>14<$1F>00013D<$1F>01<$13>00에 숨어들거나\n탈옥을 돕는 등\n거리낌 없는 짓을 거듭하고\n있지만, 이 한마디만 있으면\n왠지 용서받는다는 점이\n미소를 자아내기도 하고\n두렵기도 하다",
        "category": "meaning_naturalness",
        "reason": "「えげつない行為」를 단순한 막무가내가 아니라 거리낌 없이 선을 넘는 행위라는 문맥으로 복원했다.",
    },
    "ARF-TM-28D5F4F9A536933E3263": {
        "translation_ko": "우리 집으로 돌아가기",
        "category": "title_naturalness",
        "reason": "채팅 제목에서 어색한 명사구 ‘우리 집으로의 귀환’을 자연스러운 한국어 제목으로 다듬었다.",
    },
    "ARF-TM-2A3C4940C525EC9DAF66": {
        "translation_ko": "<$0F>紅 용옥석",
        "category": "source_structure_marker",
        "reason": "<$0F> 직후의 EUC-JP 문자 紅은 도움말 제어 명령의 매개변수일 가능성이 높으므로 번역하지 않고 원바이트열 의미를 보존했다.",
    },
    "ARF-TM-2A3FC351253095AC3EC0": {
        "translation_ko": "어둠의 코드가 새겨진 장신구.\n깊은 잠의 나락에서 착용자를 끌어낸다",
        "category": "naturalness",
        "reason": "「淵から引き戻す」의 방향과 의미가 자연스럽게 드러나도록 ‘끌어올린다’를 ‘끌어낸다’로 고쳤다.",
    },
    "ARF-TM-2AD8BF9F8DD7A44636CC": {
        "translation_ko": "근육질 형님이 그려진 책",
        "category": "tone_nuance",
        "reason": "익살스러운 「ムキムキのお兄さん」의 친근한 호칭 뉘앙스를 건조한 ‘남성’ 대신 살렸다.",
    },
    "ARF-TM-2B17FF268C8EA75555CB": {
        "translation_ko": "지정한 아군을 응원해\n<$13>14<$1F>00002E<$1F>01<$13>00 상태로\n만드는 <$13>14<$1F>00004B<$1F>01<$13>00.\n한 번 응원한 정도로는 효과가\n미미하지만, 거듭\n응원하면\n그 힘은 막강해질\n것이다",
        "category": "naturalness",
        "reason": "‘거듭 응원을 계속하면’의 의미 중복을 제거하면서 원문의 반복 응원 조건을 유지했다.",
    },
    "ARF-TM-2B4DB392741518069150": {
        "translation_ko": "라르크 일행을 위기에서 구하는 오이겐.",
        "category": "grammar_meaning",
        "reason": "「危機を救う」를 한국어에서 목적 관계가 분명한 ‘일행을 위기에서 구하다’로 바로잡았다.",
    },
    "ARF-TM-2B93B9B7B3B281E3E6AE": {
        "translation_ko": "『뜨거운 모래에 둘러싸인 마을의 벽면을 조사하라』고\n적혀 있다",
        "category": "lexical_clarity",
        "reason": "「熱砂」를 순국자를 뜻하는 동음어로 오해할 수 있는 ‘열사’ 대신 명확한 ‘뜨거운 모래’로 옮겼다.",
    },
    "ARF-TM-2B98F8A3A4C3A37D7E8D": {
        "translation_ko": "<$13>14<$1F>0000A3<$1F>01<$13>00 레벨 4의 <$13>14<$1F>000061<$1F>01<$13>00.\n대상을 중심으로 한 범위 내\n적에게 물과 땅의 <$13>14<$1F>0000A2<$1F>01<$13>00\n피해를 준다.\n<$13>14<$1F>0000B0<$1F>01<$13>00의\n프리징 케이지에서는\n추가 효과로 대상을\n<$13>14<$1F>000029<$1F>01<$13>00 상태로\n만들기도 한다",
        "category": "system_naturalness",
        "reason": "확률성 추가 효과의 「することがある」를 자연스러운 시스템 문장 ‘만들기도 한다’로 다듬었다.",
    },
    "ARF-TM-2C728786C53E26BEF349": {
        "translation_ko": "대죄를 짊어진 자를 붙잡아 두는 구속복.\n온갖 재앙에 맞서는 힘을 지녔다",
        "category": "meaning_accuracy",
        "reason": "「大罪を負う」의 ‘죄를 짊어지다’라는 표현을 살리고 원문에 없는 범행 확정을 피했다.",
    },
    "ARF-TM-2CD336C5FEDF2A9078F4": {
        "translation_ko": "과거 <$13>14<$1F>0000E8<$1F>01<$13>00에서\n가장 깊은 신앙을 모은 것은\n<$13>14<$1F>00011D<$1F>01<$13>00이었다.\n교단은 세계 각지에서\n순례하러 오는 이들을\n위해 길을 정비하고 그곳에\n때로는 비바람을 피하고\n때로는 다른 순례자들과\n쉴 수 있는 숙소를 마련했다",
        "category": "grammar_naturalness",
        "reason": "「信仰を集めていたのは」의 주어·서술 관계를 복원하고 불필요하게 덧붙인 ‘대상’을 제거했다.",
    },
    "ARF-TM-2D5AC3B0DCEE3B664CF1": {
        "translation_ko": "<$13>14<$1F>0000A4<$1F>01<$13>00 레벨 2의 <$13>14<$1F>000061<$1F>01<$13>00.\n단일 대상에게 물과 바람의 <$13>14<$1F>0000A2<$1F>01<$13>00\n피해를 준다.\n<$13>14<$1F>0000B0<$1F>01<$13>00의\n블래스트 임팩트에서는\n추가 효과로\n대상을 <$13>14<$1F>000020<$1F>01<$13>00 상태로\n만들기도 한다",
        "category": "system_naturalness",
        "reason": "확률성 추가 효과의 「することがある」를 자연스러운 시스템 문장 ‘만들기도 한다’로 다듬었다.",
    },
    "ARF-TM-2D833458BE0F59CF1193": {
        "translation_ko": "낮은 확률로 한 번의 물리 공격 행동이\n모두 치명타가 된다",
        "category": "system_meaning_naturalness",
        "reason": "「１行動全て」가 한 차례의 물리 공격 행동 전체를 가리킨다는 점이 분명하도록 어순을 바로잡았다.",
    },
    "ARF-TM-2E296584A59379382E99": {
        "translation_ko": "『무한』의 이름을 받은 이형의 건틀릿.\n때로 주인의 한계를 뛰어넘는 힘을 끌어낸다",
        "category": "meaning_grammar_fixed_field",
        "reason": "「主に自らの限界を超越させる」의 주체·대상 관계를 복원하고 아이템 설명 고정 필드의 NUL 포함 81바이트 한도에도 맞췄다.",
    },
    "ARF-TM-2E3370D252B28929B43F": {
        "translation_ko": "방어 능력치가 상승하고\n공격 능력치가 감소한다",
        "category": "fixed_field_capacity",
        "reason": "공격계·방어계 능력치의 대비를 유지하면서 로그레스 설명 고정 필드의 NUL 포함 49바이트 한도에 맞췄다.",
    },
    "ARF-TM-30291AF4620F85AD2520": {
        "translation_ko": "<$13>14<$1F>00014C<$1F>01<$13>00의 동쪽, 고요한 숲에\n있던 <$13>14<$1F>000150<$1F>01<$13>00\n교회.\n의지할 곳 없는 아이들이\n공동생활을 하던\n곳이었으나 유행병으로\n많은 이가 쓰러진 결과\n시설은 폐쇄되고 생존자들은\n<$13>14<$1F>00014C<$1F>01<$13>00에 거두어졌다",
        "category": "meaning_naturalness",
        "reason": "「引き取られた」를 시설 폐쇄 뒤 생존자들이 다른 곳에 거두어진 문맥에 맞게 옮겼다.",
    },
    "ARF-TM-31330044C28BC69AA7FD": {
        "translation_ko": "날개 달린 생물 특공+",
        "category": "terminology_naturalness",
        "reason": "「有翼生物」를 어색한 ‘날개 생물’ 대신 의미가 즉시 드러나는 ‘날개 달린 생물’로 옮겼다.",
    },
    "ARF-TM-3163C988C91C2AA58CEE": {
        "translation_ko": "하늘에서 대지로 왔다고 전해지는 지팡이.\n소지자에게 내성을 줘 광소술을 막아 준다",
        "category": "fixed_field_capacity",
        "reason": "천상에서 대지로 온 지팡이와 광소술 방호의 의미를 유지하면서 NUL 포함 81바이트 고정 필드에 맞췄다.",
    },
    "ARF-TM-3154C8F29D5584D8FAFE": {
        "translation_ko": "대상을 매도해\n<$13>14<$1F>00002F<$1F>01<$13>00 상태로 만드는\n<$13>14<$1F>00004B<$1F>01<$13>00.\n한 번 매도한 정도로는\n꿈쩍하지 않지만, 거듭\n매도하면\n당신에 대한 공포가 진짜가\n될 것이다",
        "category": "naturalness_meaning",
        "reason": "‘거듭 매도를 계속하면’의 중복을 없애고 「貴方への恐怖」를 의미가 분명한 ‘당신에 대한 공포’로 고쳤다.",
    },
    "ARF-TM-31B3D94227FDE67655F0": {
        "translation_ko": "콘서트를 열고 싶다 3",
        "category": "quest_title_style",
        "reason": "퀘스트 제목의 문체를 구어형 ‘싶어’보다 목록 제목에 자연스러운 평서형 ‘싶다’로 정리했다.",
    },
}


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


source_rows = read_jsonl(SOURCE)
draft_rows = read_jsonl(DRAFT)
assert len(source_rows) == len(draft_rows) == 200
assert [row["tm_id"] for row in source_rows] == [row["tm_id"] for row in draft_rows]
assert all(src["source_text"] == drf["source_text"] for src, drf in zip(source_rows, draft_rows))
assert set(edits) <= {row["tm_id"] for row in draft_rows}

modifications = []
reviewed_rows = []
for src, draft in zip(source_rows, draft_rows):
    reviewed = dict(draft)
    if draft["tm_id"] in edits:
        edit = edits[draft["tm_id"]]
        before = draft["translation_ko"]
        after = edit["translation_ko"]
        assert before != after
        reviewed["translation_ko"] = after
        modifications.append(
            {
                "tm_id": draft["tm_id"],
                "source_text": draft["source_text"],
                "before": before,
                "after": after,
                "category": edit["category"],
                "reason": edit["reason"],
            }
        )
    reviewed_rows.append(reviewed)

assert len(modifications) == len(edits)
REVIEWED.parent.mkdir(parents=True, exist_ok=True)
REVIEWED.write_text(
    "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in reviewed_rows),
    encoding="utf-8",
    newline="\n",
)

change_payload = {
    "schema": "arf-translation-review-changes-v1",
    "batch_id": "batch_0005",
    "reviewer": "/root/review_batch_0005",
    "translation_engine_policy": "Codex internal models only",
    "external_translation_services_used": [],
    "modified_units": len(modifications),
    "modifications": modifications,
    "reviewed_sha256": hashlib.sha256(REVIEWED.read_bytes()).hexdigest().upper(),
}
CHANGES.parent.mkdir(parents=True, exist_ok=True)
CHANGES.write_text(json.dumps(change_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"reviewed_units": len(reviewed_rows), "modified_units": len(modifications), "reviewed_sha256": change_payload["reviewed_sha256"]}, ensure_ascii=False))
