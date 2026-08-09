# -*- coding: utf-8 -*-
"""Apply the independent batch 0006 review with an explicit UTF-8 writer."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = Path("work/translation/tm_v2/batches/source/batch_0006.jsonl")
DRAFT = Path("work/translation/drafts/batch_0006.jsonl")
OUTPUT = Path("work/translation/reviewed/batch_0006.jsonl")


CHANGES = {
    "ARF-TM-325FAEE50CA3F412DE0A": (
        "<$13>14<$1F>000098<$1F>01<$13>00 방식 중 하나.\n"
        "자신의 시야에 들어오는 범위의\n"
        "적에게 반응한다.\n"
        "시야 밖, 즉\n"
        "뒤를 노리면 반응하지 않는다"
    ),
    "ARF-TM-32D1CA3C8220D71A23BF": "RES 하락",
    "ARF-TM-334214F2C356E9118021": (
        "<$13>14<$1F>0000A4<$1F>01<$13>00 레벨 4의 <$13>14<$1F>000061<$1F>01<$13>00.\n"
        "대상을 중심으로 한 범위 내의\n"
        "적에게 물과 바람의 <$13>14<$1F>0000A2<$1F>01<$13>00\n"
        "피해를 준다.\n"
        "<$13>14<$1F>0000B0<$1F>01<$13>00의\n"
        "토르 해머에서는\n"
        "추가 효과로 대상을\n"
        "<$13>14<$1F>00001D<$1F>01<$13>00 상태로 만들기도 한다"
    ),
    "ARF-TM-3343DCA46796947A85D0": (
        "땅의 코드가 새겨진 장신구.\n육체의 석화를 막도록 작용한다"
    ),
    "ARF-TM-34518E656C2B9FC05389": (
        "단일 대상 HP 소량 회복\n자신 외 대상에게 발동 가능"
    ),
    "ARF-TM-345B5EC239691C153C04": (
        "일기당천의 코더 사냥꾼이 애용한 지팡이.\n"
        "소지자를 지키며 때로 광소술을 무효화한다"
    ),
    "ARF-TM-34B22DDAF70C38FD78BD": (
        "<$15>01물리 공격 시 날개 달린 생물에게 주는\n"
        "피해가 크게 증가한다"
    ),
    "ARF-TM-34F6BF9FCE2AE67F7EDC": (
        "메리디아 황제가 된\n"
        "알스가 공포한\n"
        "새로운 헌법 조항.\n"
        "<$13>14<$1F>000138<$1F>01<$13>00에 의해\n"
        "건국 때부터 이어져 온\n"
        "구법에 비해\n"
        "훨씬 가혹한 이 법은\n"
        "사람이 사람을 잉여 존재로\n"
        "여겨 배척하는 법이었다"
    ),
    "ARF-TM-3521F2F9CB31DC6114DD": (
        "보기 드문 꽃이 선명하게 핀 휘장.\n"
        "발밑에서 행운을 찾을 듯한 기분이 든다……"
    ),
    "ARF-TM-364FDC37BCDF81E4FDE6": "레벨 2 MP 완전 회복",
    "ARF-TM-364AE0F702E20DEA38C0": "의문의 간호복",
    "ARF-TM-373C31B9539E2B8F6F57": (
        "<$13>14<$1F>0000A5<$1F>01<$13>00 레벨 1의 <$13>14<$1F>000061<$1F>01<$13>00.\n"
        "적 단일 대상에게 불과 바람의 <$13>14<$1F>0000A2<$1F>01<$13>00\n"
        "피해를 준다.\n"
        "<$13>14<$1F>0000B0<$1F>01<$13>00의\n"
        "샤인 불릿에서는\n"
        "추가 효과로\n"
        "대상을 <$13>14<$1F>000020<$1F>01<$13>00 상태로\n"
        "만들기도 한다"
    ),
    "ARF-TM-375CFA3B661F431A2B6B": (
        "<$13>14<$1F>0000A1<$1F>01<$13>00 레벨 4의 <$13>14<$1F>000061<$1F>01<$13>00.\n"
        "대상을 중심으로 한 범위 내\n"
        "적에게 <$13>14<$1F>0000A1<$1F>01<$13>00 피해를\n"
        "준다.\n"
        "<$13>14<$1F>0000B0<$1F>01<$13>00의\n"
        "가이아 브리드에서는\n"
        "추가 효과로 대상을\n"
        "<$13>14<$1F>000036<$1F>01<$13>00 상태로\n"
        "만들기도 한다"
    ),
    "ARF-TM-382B1220143304D3EC82": "G선더볼트",
    "ARF-TM-386768A1EA571E36700C": (
        "물리 공격 시 수생 생물에게 주는\n피해가 증가한다"
    ),
    "ARF-TM-386BB7193FF058B24CC1": (
        "<$13>14<$1F>00014B<$1F>01<$13>00 서쪽\n"
        "푸른 언덕이 이어진 사이에\n"
        "자리 잡은 작은 마을.\n"
        "한때는 독자적인 색채가 짙은\n"
        "문화로 알려졌으나\n"
        "지금은 <$13>14<$1F>000148<$1F>01<$13>00와\n"
        "다른 도시의 영향을\n"
        "피하지 못하고 있다"
    ),
    "ARF-TM-391A739C3A358546845C": (
        "레테아 숲에 새가 이상할 만큼 불어났네.\n"
        "원인을 밝혀 해결해 주지 않겠나?\n"
        "낯선 새도 있었던 듯하네만……"
    ),
    "ARF-TM-3903C64837C93CD29802": (
        "제도에 전해지는 용사상을 본뜬 의상\n"
        "초대 메리디아 왕의 모습이라는 설도 있지만……"
    ),
    "ARF-TM-39C1821CBF56DC7A890E": (
        "밤을 닮은 칠흑의 드레스 가슴께를\n"
        "얼어붙은 별 같은 펜던트가 장식한다"
    ),
    "ARF-TM-3A13C08F93F275ACBE90": "수생 생물 특공",
    "ARF-TM-3B2AC3F87D60F0DF4FAB": (
        "빠르게 내지르는 철의 손끝.\n승리 후 행운이 따르기 쉬워진다"
    ),
    "ARF-TM-3B2BC778DC7B5423DCB4": (
        "혼자서 <$13>14<$1F>000000<$1F>01<$13>00을 조합해\n"
        "발생하는 연계를\n"
        "나타낸다.\n"
        "<$13>14<$1F>000060<$1F>01<$13>00, <$13>14<$1F>00004B<$1F>01<$13>00을\n"
        "조합하면\n"
        "발생하기도 한다"
    ),
    "ARF-TM-3C0DBE3765380F4368E5": (
        "어느 나라와도 다른 학사 차림\n"
        "햇빛 받은 유리 너머의 눈동자는 수수께끼를 안다"
    ),
    "ARF-TM-3B3830DC2BFD9A6358C6": (
        "<$13>14<$1F>000021<$1F>01<$13>00 중 하나.\n"
        "캐릭터의 <$13>14<$1F>000046<$1F>01<$13>00으로\n"
        "주는 피해가 증가한다.\n"
        "<$13>14<$1F>000029<$1F>01<$13>00 상태일 때\n"
        "MGC 상승 효과를 중첩하면\n"
        "<$13>14<$1F>000029<$1F>01<$13>00의 효과를\n"
        "약화시키거나 덮어쓸\n"
        "수 있다. 이 <$13>14<$1F>000021<$1F>01<$13>00은\n"
        "<$13>14<$1F>000022<$1F>01<$13>00이다"
    ),
    "ARF-TM-3CD2B8EE90FA5A874CC0": (
        "<$13>14<$1F>000016<$1F>01<$13>00 중 하나.\n"
        "<$13>14<$1F>000003<$1F>01<$13>00 회복을 전혀 받을 수\n"
        "없는 상태.\n"
        "<$13>14<$1F>000064<$1F>01<$13>00이나 <$13>14<$1F>000061<$1F>01<$13>00뿐\n"
        "아니라 <$13>14<$1F>000039<$1F>01<$13>00의 영향도\n"
        "받지 못한다.\n"
        "이 <$13>14<$1F>000016<$1F>01<$13>00은 전투가\n"
        "끝나도 회복되지 않는다"
    ),
    "ARF-TM-3D2C466FAD9E7AC84B2B": (
        "경건한 소녀는 신의 가르침을 설파할까?\n"
        "아니면 그 미소 속에 계략을 숨기고 있을까?"
    ),
    "ARF-TM-3D5D563C549BB8B1DE7A": (
        "광소술전에 특화된 충격 완화 장비.\n방어력과 저항력을 높인다"
    ),
    "ARF-TM-3D69577BA80C3D0C12A7": (
        "단일 대상에게 무속성 피해\n추가 효과: DEF 하락"
    ),
    "ARF-TM-3E29CFE95FD277A612E0": "메이드 기행〜대도시 편 2",
    "ARF-TM-3E3CEB48CC3D7E287709": (
        "오르키나교 신도에게 아델이 납치됐다!"
    ),
}


def load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main() -> None:
    source = load_jsonl(SOURCE)
    draft = load_jsonl(DRAFT)
    assert len(source) == len(draft) == 200
    assert set(CHANGES).issubset({str(unit["tm_id"]) for unit in draft})
    for src_unit, draft_unit in zip(source, draft):
        assert src_unit["tm_id"] == draft_unit["tm_id"]
        assert src_unit["source_text"] == draft_unit["source_text"]
        replacement = CHANGES.get(str(draft_unit["tm_id"]))
        if replacement is not None:
            draft_unit["translation_ko"] = replacement
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "".join(
            json.dumps(unit, ensure_ascii=False, separators=(",", ":")) + "\n"
            for unit in draft
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"units": len(draft), "modified": len(CHANGES)}))


if __name__ == "__main__":
    main()
