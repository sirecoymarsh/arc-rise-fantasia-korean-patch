import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "work/translation/drafts"
REVIEWED = ROOT / "work/translation/reviewed"
REPORTS = ROOT / "work/translation/reviews"
REVIEWER = "/root/review_batch_0058_0060"
DRAFT_AUTHOR = "/root/translate_batch_0009"


# row: (reviewed Korean, category, reason)
SETS = {
    79: {
        18: ("우리는 또다시 배신당했습니다.\n알스 같은 건\n이제 믿을 수 없습니다", "register", "한 대사 안에서 반말과 존댓말이 섞이지 않도록 공식적인 말투로 통일했다."),
        31: ("성지 노와레・곤혹의 회랑", "formatting", "프로젝트 지명 표기의 고유명사 구분점으로 통일했다."),
        45: ("이의, 있음~!\n이의이의, 있음~!", "wordplay", "異議あり를 흉내 내는 아이의 말장난이 한국어에서도 드러나도록 옮겼다."),
        54: ("군인으로 남든 용병이 되든\n떳떳한 일을 하면 되잖아?<$0C>……그러고 보니\n너희는 모르고 있었지?", "semantic_accuracy", "まともな仕事를 과거의 일을 추궁하는 뜻이 아니라 떳떳한 일을 하면 된다는 의미로 바로잡았다."),
        72: ("라르크.\n너에게 나와 저항군의\n가교 역할을 맡기겠다", "terminology", "レジスタンス의 확정 표기 '저항군'을 적용했다."),
        78: ("……그런가요오?<$0C>전 당연히 그린힐 의장은\n죽은 줄 알았어요.\n미인은 박명이라잖아요?", "character_voice", "そうなんですかぁ의 늘어지는 말투를 살리고 문장 호흡을 자연스럽게 다듬었다."),
        98: ("제도 디아만트・자무엘 무예관  １Ｆ", "terminology", "ザムエル武芸塾의 확정 표기와 원문의 전각 층 표기 및 구분점을 적용했다."),
        102: ("지도자 라르크.\n그때는 신세 많이 졌습니다<$0C>당신 덕분에\n저희도 한동안 활동을\n계속할 수 있을 것 같습니다", "terminology", "조직 직책 リーダー를 확정 표기 '지도자'로 통일했다."),
        108: ("cop020:스켈레톤\ncop021:리빙 데드\ncop022:골드 본\ncop023:킹 본\n그만두기", "ui", "디버그 메뉴의 やめる를 취소가 아닌 동작 종료 항목으로 정확히 옮겼다."),
        114: ("카르분클루스의 해초를\n반죽에 듬뿍 넣은\n『그린힐 만주』를 개발했어<$0C>이걸로 관광객의 마음을 단번에 사로잡겠어!\n이 신상품을 카르분클루스의\n대표 기념품으로 만들 거야", "semantic_accuracy", "饅頭를 고기소 음식인 만두가 아니라 일본식 과자 '만주'로 바로잡았다."),
        164: ("곤란한 일이 있으면\n저희 저항군에\n뭐든지 말씀해 주세요……", "terminology", "レジスタンス의 확정 표기 '저항군'을 적용했다."),
        167: ("알스 폐하라면\n그 알스 형 말이지?\n……역시 무예관은 대단해!", "terminology", "武芸塾의 확정 표기 '무예관'을 적용했다."),
        173: ("안트락스 로케타이　　　　　\n오르키나교 대신전 로케타이　　　\n오르키나교 대신전 지하 로케타이　\n레이 제어 장치 파괴　　　　　　　\n아델 유괴　　　　　　　　　　　\n해명의 길 로케타이　　　　　　　\n해명의 길 보스 등장　　　　　　　\n리얼의 무녀 계승 의식 전반　　　　\n리얼의 무녀 계승 의식 후반　　　　\n점령 후 안트락스　　　　　　　　\n비공정을 타고 디아만트로　　　　　\n돌아간다　　　　　　　　　　　", "ui", "이동 항목의 목적지 표현과 디버그 메뉴의 もどる 표기를 자연스럽게 다듬었다."),
        180: ("아이들이 자유분방하게\n자라 주는 건\n부모에게 더없는 기쁨이야<$0C>당신도 아이가 생기면\n내 마음을 알게 될 거야", "semantic_accuracy", "子どもを持つ를 출산으로 한정하지 않고 아이가 생긴다는 뜻으로 정확히 옮겼다."),
        198: ("우린 디바의 의뢰를 받아\n그 계획을 저지하고 디바의 딸을\n――아델을 구했어", "semantic_accuracy", "それ가 디바의 의뢰가 아니라 앞서 언급된 계획을 가리키도록 지시 관계를 명확히 했다."),
    },
    80: {
        7: ("풀이 죽은 노인", "naturalness", "肩を落とす를 한국어의 자연스러운 상태 묘사로 옮겼다."),
        18: ("응……?\n라르크다<$0C>너는?", "semantic_accuracy", "자기소개인 ラルクだ를 상대를 부르는 표현으로 오역한 부분을 바로잡았다."),
        22: ("이젠 메리디아 황가를\n믿을 수가 없구먼……<$0C>오르키나, 바트라키테스――\n우리가 몇 번이나 속아 왔던가.\n메리디아는 악마의 가문인 게야", "character_voice", "노인의 말투가 마지막 문장까지 이어지도록 종결 어미를 통일했다."),
        25: ("금액? 웃기지 마.\n우린 돈 액수에 연연하는 게 아니야.\n같은 국민으로서의 성의를 보고 싶어", "semantic_accuracy", "金額に拘る를 금액 자체에 집착한다는 뜻보다 액수에 연연한다는 문맥으로 다듬었다."),
        26: ("어디를 조작할까?", "ui", "디버그 문맥의 弄る를 물리적으로 만진다가 아니라 조작한다는 뜻으로 옮겼다."),
        44: ("세간의 소문에 따르면 기괴한 대륙이\n바다에 떠 있다고 한다.\n……도저히 믿을 수 없는 이야기지만", "naturalness", "異形の大陸를 직역투인 '이형의 대륙' 대신 자연스러운 묘사로 옮겼다."),
        47: ("라르크, 너무 무리하지 마<$0C>당신은 이제야 만난\n이사의 아이니까……", "naturalness", "やっと出会えた의 화자 관점을 살려 자연스러운 한국어로 다듬었다."),
        51: ("무예관의 아이들은\n언제나 열심히 하네……\n라르크도 옛날엔 저랬어?", "terminology", "武芸塾의 확정 표기 '무예관'을 적용했다."),
        55: ("지난 습격으로 많은 목숨이\n희생되었습니다……\n마음의 병을 얻은 주민도 많다고 합니다", "semantic_accuracy", "생명을 잃은 주체가 화자가 아니라 희생자들이라는 의미를 명확히 했다."),
        59: ("자제하는 남자아이", "naturalness", "自重する를 한자어 직역 대신 행동을 삼가는 상태로 옮겼다."),
        67: ("이 앞은 장군님의 저택이야.\n장군님의 따님이라면\n무예관 앞에서 놀고 있어", "terminology", "武芸塾의 확정 표기 '무예관'을 적용했다."),
        73: ("이제 나도 피부가 예전 같지 않은 나이……\n괜찮은 남자라도 적당히 골라\n군을 그만둬 버릴까……", "naturalness", "お肌の曲がり角이라는 노화 관용 표현을 자연스러운 한국어로 옮겼다."),
        79: ("사신 라군에게\n감쪽같이 도망친 뒤로\n시민들의 압박이 심해져서……<$0C>매일 밖에서 근무하는 경비병들은\n평소보다 더 따가운\n눈총을 받게 됐다고", "naturalness", "밖에서 근무하는 경비병을 수동형으로 표현한 직역투를 바로잡았다."),
        85: ("나는 여러 가지를 하며\n노는 걸 좋아하는데――\n지금은 소재가 떨어졌어……<$0C>오빠는 어릴 때\n어떤 놀이를 했어?", "register", "소녀가 젊은 남성에게 쓰는 お兄さん을 상황에 맞게 '오빠'로 옮겼다."),
        93: ("붉은 대륙이라니……\n대체 뭘까?\n신식 병기라는 걸까!?", "naturalness", "近代兵器를 세계관 대사에 어울리는 '신식 병기'로 다듬었다."),
        95: ("■■■되돌리기■■■\n", "ui", "디버그 메뉴 항목 戻すよ를 기능명 형태로 통일했다."),
        116: ("눈을 뜨고 있어도\n건조해서 아프기만 하니까……<$0C>마음도 열어 봤자\n역시 아픈 꼴을\n당할 것 같잖아?", "naturalness", "마음을 연다는 비유가 한국어에서 자연스럽게 이어지도록 문장을 재구성했다."),
        118: ("처음 보는 얼굴이군…… 여행자인가?\n여행하는 건 좋다만\n여긴 이제 제국령이다――<$0C>신제국 헌장의 영향 아래\n있다는 걸 잊지 마라", "naturalness", "大いに結構를 부자연스러운 '실컷 해도 좋다' 대신 허용의 어조로 옮겼다."),
        121: ("지도자 라르크.\n이런 곳까지\n와 주셔서 송구합니다<$0C>여기는 저항군의 거점.\n당신의 방문을 진심으로\n환영합니다……", "terminology", "リーダー와 レジスタンス의 확정 표기를 적용하고 アジト를 자연스럽게 옮겼다."),
        132: ("아, 맞다. 하나 잊고 있었군요.\n니콜 베넥스 군이라는 청년을\n아십니까?", "naturalness", "そうそう의 회상 어감을 살려 대화 도입부를 자연스럽게 다듬었다."),
        156: ("더글러스 경 부인에게\n누명을 씌워 처형했다면\n원로원은 신뢰를 잃을 것이다", "semantic_accuracy", "冤罪で処刑した를 단순히 억울한 죄가 아니라 누명을 씌운 처형으로 명확히 했다."),
        172: ("EV02_03_0200B\n이벤트 캐릭터 삭제\n그만두기", "ui", "디버그 메뉴의 やめる를 동작 종료 항목으로 정확히 옮겼다."),
        182: ("……형은 １명뿐이야?", "semantic_accuracy", "１人가 인원수를 묻는 말이 아니라 혼자인지를 묻는 표현임을 살리면서 원문의 숫자를 유지했다."),
    },
    81: {
        10: ("승패를 가르는 건 신념의 강함.\n이번에는 너희의 마음이\n내 충의를 뛰어넘었다<$0C>……알스 님은 이 앞에 있다.\n라르크…… 그분의\n슬픔에 결착을 지어 다오", "naturalness", "悲しみにケリをつける를 부자연스러운 '슬픔에 결판' 대신 결착을 짓는다는 표현으로 다듬었다."),
        12: ("무너진 집들 사이로\n햇살이 비칩니다.\n이게 부흥의 빛일까요……", "naturalness", "木漏れ日를 중복 수식 없이 자연스러운 '햇살'로 옮겼다."),
        29: ("아빠가 『밖에 나가면 안 돼』라고\n해서 오늘은 집에서\n소꿉놀이하고 있어……<$0C>１인 놀이는 재미없어.\n……형도 같이 놀래?", "naturalness", "１人で遊ぶ의 숫자를 유지하면서 중복된 '１명 혼자' 표현을 자연스럽게 고쳤다."),
        40: ("EV09_12_1100B\nEV09_12_1300B\n이벤트 캐릭터 삭제\n실험\n그만두기", "ui", "디버그 메뉴의 やめる를 동작 종료 항목으로 정확히 옮겼다."),
        41: ("리피아 일은\n저한테 전부\n맡겨 주십쇼!<$0C>조금이라도 위험이 닥치면\n제 목숨과 바꿔서라도\n끝까지 지킬 각오임다!", "character_voice", "自分に를 자연스러운 1인칭으로 옮기면서 니콜의 말버릇을 유지했다."),
        45: ("평소처럼 생활하려\n노력하는 게 중요합니다.\n그러면 마음도 차분해질 겁니다……", "semantic_accuracy", "いつも通りの暮らしを心がける를 '생활을 마음에 새기다'가 아닌 일상을 유지하려 노력한다는 뜻으로 바로잡았다."),
        66: ("인형　　　: cop002~cop003\n미니 리치: cop010~cop013\n스켈레톤: cop020~cop023\n리치　　: cop030~cop033\n그만두기", "ui", "디버그 메뉴의 やめる를 동작 종료 항목으로 정확히 옮겼다."),
        70: ("알스 황제라면\n바트라키테스를 해방해 주실 거야――\n……그렇게 믿습니다<$0C>바트라키테스는 제 고향입니다.\n１일이라도 빨리 돌아가고 싶습니다……", "register", "대사 후반부의 공식적인 말투에 맞춰 소유격과 종결 어미를 정리했다."),
        93: ("분명 곧\n장터도 상중에 들어갈 테니\n지금 미리 사 둬야……", "naturalness", "市が喪に服する를 시장이 장례를 치른다는 직역 대신 장터가 상중에 들어간다는 뜻으로 다듬었다."),
        108: ("의회 정치로 바뀐 뒤\n국내 빈부 격차가 줄어들고 있다.\n다른 어디에서도 볼 수 없는 징조다<$0C>전쟁 같은 야만적인 행위보다\n새로운 정치 체제가\n백성을 풍요롭게 한다는 게 증명됐다", "word_choice", "긍정적인 변화인 兆候를 부정적 뉘앙스가 강한 '징후' 대신 '징조'로 옮겼다."),
        116: ("아무튼 황제의 붕어 소식도\n카르분클루스 의장에게\n알려야 해", "naturalness", "붕어에 관한 소식을 전한다는 의미가 자연스럽게 드러나도록 다듬었다."),
        117: ("변경의 땅 02・NPC 배치 초기화\n", "formatting", "원문의 고유명사 구분점과 행 끝 형식을 반영했다."),
        128: ("고맙……다고 하고 싶지만\n어느새 나도\n더 들 수 없게 된 모양이야<$0C>이번에는 사양할게\n모처럼인데 미안해", "naturalness", "말을 꺼냈다가 소지 한도를 깨닫는 화자의 자기 정정이 자연스럽게 드러나도록 옮겼다."),
        131: ("그래, 육로는 위험하니까\n１명으로는 무리겠지.", "naturalness", "１人じゃ의 숫자를 유지하면서 중복된 '１명 혼자' 표현을 바로잡았다."),
        155: ("안트락스와\n바트라키테스 일을 잊었어?<$0C>피로 물든 메리디아 일족은\n속여서 기습하는 데 능한 가문이야", "semantic_accuracy", "だまし討ち의 속임수와 기습 의미를 모두 반영했다."),
        176: ("가자!", "naturalness", "동료를 독려하는 行くぞ를 선언형보다 자연스러운 권유형으로 옮겼다."),
        182: ("고집 센 남자", "naturalness", "こだわる의 관형 표현을 자연스러운 인물 묘사로 다듬었다."),
    },
}


# Minimal substitutions preserve all otherwise significant spacing in long debug menus.
REPLACEMENTS = {
    80: {
        190: ([
            ("자무엘 무예 학원", "자무엘 무예관"),
            ("돌아가기", "돌아간다"),
        ], "terminology", "긴 디버그 메뉴의 간격을 보존하면서 武芸塾과 もどる의 확정 표기를 적용했다."),
    },
    81: {
        136: ([
            ("무예 학원", "무예관"),
        ], "terminology", "대사 전체의 武芸塾을 확정 표기 '무예관'으로 통일했다."),
    },
}


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


for number in (79, 80, 81):
    batch_id = f"batch_{number:04d}"
    draft_path = DRAFTS / f"{batch_id}.jsonl"
    output_path = REVIEWED / f"{batch_id}.jsonl"
    report_path = REPORTS / f"{batch_id}_review.json"
    rows = load_jsonl(draft_path)
    modifications = []

    operations = []
    for row_index, (after, category, reason) in SETS.get(number, {}).items():
        operations.append((row_index, after, category, reason))
    for row_index, (pairs, category, reason) in REPLACEMENTS.get(number, {}).items():
        after = rows[row_index]["translation_ko"]
        for old, new in pairs:
            after = after.replace(old, new)
        operations.append((row_index, after, category, reason))

    for row_index, after, category, reason in sorted(operations):
        row = rows[row_index]
        before = row["translation_ko"]
        row["translation_ko"] = after
        if before != after:
            modifications.append({
                "row_index": row_index,
                "tm_id": row["tm_id"],
                "source_text": row["source_text"],
                "before": before,
                "after": after,
                "category": category,
                "reason": reason,
            })

    write_jsonl(output_path, rows)
    report = {
        "schema": "arf-translation-independent-review-v1",
        "batch_id": batch_id,
        "reviewer": REVIEWER,
        "draft_translator": DRAFT_AUTHOR,
        "draft_author": DRAFT_AUTHOR,
        "independent_review": True,
        "translation_engine_policy": "Codex internal models only",
        "external_translation_services_used": [],
        "external_translation_models_or_apis_used": [],
        "sources": {
            "draft": f"work/translation/drafts/{batch_id}.jsonl",
            "source": f"work/translation/tm_v2/batches/source/{batch_id}.jsonl",
            "rules": "work/translation/tm_v2/TRANSLATION_RULES.md",
            "style_guide": "work/translation/glossary_agent/style_guide.md",
            "glossary": "work/translation/glossary_agent/glossary.csv",
        },
        "output": f"work/translation/reviewed/{batch_id}.jsonl",
        "row_count": len(rows),
        "reviewed_row_count": len(rows),
        "modified_row_count": len(modifications),
        "unchanged_row_count": len(rows) - len(modifications),
        "modifications": modifications,
        "verification_execution": {
            "status": "deferred_by_user_instruction",
            "executed_tools": [],
            "not_executed": ["validator", "fit", "encoding", "boundary_audit"],
            "reason": "사용자 지시에 따라 기술 검증은 전체 번역 완료 후 마지막에 한 번만 수행한다.",
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{batch_id} rows={len(rows)} modified={len(modifications)}")
