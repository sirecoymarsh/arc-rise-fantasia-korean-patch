import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "work" / "translation" / "drafts"
REVIEWED = ROOT / "work" / "translation" / "reviewed"
REPORTS = ROOT / "work" / "translation" / "reviews"
REVIEWER = "/root/review_batch_0058_0060"
DRAFT_AUTHOR = "/root/audit_boundary_integration"

# index: (replacement, category, reason)
EDITS = {
    67: {
        3: ("아델은 라군 상사――네놈만\n바라본다고 생각했다.\n나도 알스 님도 말이다", "terminology", "曹長의 확정 계급 표기인 '상사'를 적용했다."),
        9: ("일단 두들겨 봐야겠군.\n너희도 쓸 수 있는 광소술을 모조리\n퍼부어 봐", "semantic_accuracy", "사용 가능한 광소술을 전부 쏟으라는 의미를 명확히 했다."),
        16: ("류즈……\n넌 대체 누구지.\n그리고 당신도 마찬가지야, 소아라", "naturalness", "병렬 호명의 의미와 한국어 어순을 자연스럽게 다듬었다."),
        20: ("이매지널은 인간을 구해.\n……그래야 할 텐데", "semantic_accuracy", "화자의 불확실한 기대를 나타내는 원문의 뉘앙스를 복원했다."),
        25: ("그래서 엔주 씨에게\n돌아가지 않는 건가!", "naturalness", "반문형 대사를 자연스럽게 다듬었다."),
        30: ("리피아는 정말\n어딘가 엇나가 있네", "semantic_accuracy", "ピントがずれている의 비유적 의미를 반영했다."),
        35: ("당신들과 아는 사이였다고\n해도 기억나지 않아", "semantic_accuracy", "기억 상실을 전제로 한 원문의 조건 관계를 바로잡았다."),
        43: ("그러기 위해 로그레스가 필요하다면 찾겠어.\n하지만 그건 내가 이사의 아이라서\n그러는 게 아니야", "naturalness", "문장 연결과 강조 대상을 자연스럽게 정리했다."),
        46: ("바, 바보야!\n괜히 소란을 일으키면\n아부심에 관해 물어볼 수 없잖아!", "terminology", "アブシム의 확정 표기 '아부심'을 적용했다."),
        52: ("장소는 말할 수 없습니다.\n니콜은 지금 저항군으로\n활동 중입니다. 건강했어요", "terminology", "レジスタンス의 확정 표기 '저항군'을 적용했다."),
        58: ("이제 탁룡화는 막을 수 없다.\n그 전에……", "semantic_accuracy", "임박한 상태를 나타내는 시제를 바로잡았다."),
        63: ("서민들의 고통 따윈\n모르겠지", "semantic_accuracy", "下々の人間을 문맥에 맞게 '서민들'로 옮겼다."),
        77: ("당신은 이런 데서\n뭐 하는 검까? 분명 황자\n감시를 하고 있던 거 아니었……", "naturalness", "중단된 반문을 자연스럽게 복원했다."),
        78: ("이쪽은 어리바리한 남자 １명을\n잃어도\n눈 하나 깜짝 안 해", "semantic_accuracy", "이미 사람을 잃는 상황을 가정하는 원문의 의미를 반영했다."),
        89: ("인사 발령장은 내가 직접 전해 주겠다.\n나중에 집무실로 와라", "terminology", "辞令를 군 인사 문맥의 '인사 발령장'으로 바로잡았다."),
        92: ("니콜, １명이서 도망친 걸\n상당히 신경 쓰는 걸까", "formatting", "원문의 인원수 １을 보존했다."),
        106: ("저항군의 지도자를\n돌려받겠다", "terminology", "조직명과 직책을 확정 용어로 통일했다."),
        116: ("허가증 없는 외출은\n신제국 헌장 제３조 위반이다!\n즉시 체포해 처형한다!", "formatting", "조항 번호의 전각 숫자 표기를 보존했다."),
        128: ("네? 그게 뭡니까", "naturalness", "부자연스러운 축약형을 화자의 정중한 질문으로 다듬었다."),
        132: ("그런 걸 멋대로 정해도\n저항군 녀석들도……", "terminology", "レジスタンス의 확정 표기를 적용했다."),
        142: ("예전엔 모두가 따르고\n사랑했을 만큼 아주 다정한\n사람이었는데……", "naturalness", "줄바꿈으로 끊긴 서술을 자연스럽게 정리했다."),
        149: ("바, 방금 건 뭐였슴까……", "naturalness", "화자의 말버릇을 유지하면서 어순을 자연스럽게 바꿨다."),
        158: ("어? 아, 아아…… 왜?", "semantic_accuracy", "머뭇거리는 감탄과 반문을 원문대로 복원했다."),
        166: ("디바도 뭣도 아닌\n그저 『리피아』여도\n라르크와 일행에게 도움이 될 수 있어?", "naturalness", "みんな를 해당 일행 전체로 자연스럽게 표현했다."),
        168: ("다시 만나게 된다면\n프레이아가 사과하고 싶다고\n전해 줘", "semantic_accuracy", "현재의 전달 의뢰를 불필요한 과거 시제 없이 옮겼다."),
        179: ("그 긍지 높은 피가 흐르는\n자신을 소중히 여기세요", "naturalness", "한국어 목적어 구조를 자연스럽게 다듬었다."),
        185: ("그야 당연하지.\n네가 나를 고문했으니까", "semantic_accuracy", "고문 행위의 주체와 대상을 명확히 했다."),
        189: ("뭐, 그렇게 자기들 행동을\n정당화하는 건 자유지만 우리를\n따라다니는 건 민폐야", "naturalness", "구어 대사의 호흡과 목적어를 자연스럽게 정리했다."),
        194: ("그래. 적어도 난 이매지널의\n섭리가 전부 옳다고 말할 근거를\n내 안에 갖고 있지 않았어", "semantic_accuracy", "正しいと言える根拠의 의미를 정확히 반영했다."),
        199: ("바이스도 무슨 생각인지\n모르겠다 싶었는데\n알스는 또 왜 저러는 걸까", "naturalness", "두 인물에 대한 화자의 의문을 자연스럽게 연결했다."),
    },
    68: {
        0: ("부탁해.\n이게 사령부에서 온 서신이야", "terminology", "書状을 문맥에 맞는 '서신'으로 옮기고 출처 관계를 분명히 했다."),
        10: ("그러면 네게\n알스 황자의 감시역을 맡길 수 있다", "register", "군 상관의 단정적인 말투를 유지했다."),
        17: ("우리한텐\n과장이 아니라니까.\n이런 걸 어떻게 만든 거야?", "naturalness", "강조와 의문문의 한국어 어순을 다듬었다."),
        21: ("아까부터 완전히 딴생각만\n하고 있잖아", "semantic_accuracy", "上の空의 의미를 자연스러운 관용 표현으로 옮겼다."),
        31: ("마지막으로 뵌 건 １８년 전.\n당시에는 아직 대령이셨지요", "naturalness", "부자연스러운 줄바꿈과 서술어 결합을 정리했다."),
        45: ("난 아버지에 의해\n깨어난 거야.\n라필 님을 죽이기 위해서 말이야", "semantic_accuracy", "수동 관계와 각성 목적을 명확히 했다."),
        57: ("조원 선발은\n라군 상사에게 일임한다", "terminology", "曹長의 확정 계급 표기 '상사'를 적용했다."),
        65: ("무슨 뜻이야……\n그렇게 하면\n신종은 죽어 버리는데", "naturalness", "조건 관계가 자연스럽게 드러나도록 다듬었다."),
        68: ("세계에 퍼지기 전에\n철저히 박멸해야 한다", "semantic_accuracy", "대상을 제거한다는 滅ぼす의 의미를 '박멸'로 정확히 표현했다."),
        72: ("하지만…… 역시…… 말이야.\n갑자기 헤어지려니까……", "naturalness", "중단된 구어체의 호흡을 자연스럽게 다듬었다."),
        74: ("하지만 전원이 리피아 안으로\n들어가면 의식을 잃은 몸이\n습격당할 위험이 있어", "semantic_accuracy", "이동 방향과 위험의 대상을 명확히 했다."),
        82: ("그래…… 아부심은\n알스에게 빼앗겼으니까", "terminology", "アブシム의 확정 표기 '아부심'을 적용했다."),
        84: ("하지만 우리 의도와 상관없이\n알스는 리얼의 섭리를 도출하려고\n로그레스를 손에 넣으려 해", "semantic_accuracy", "導く를 설정 문맥의 '도출하다'로 바로잡았다."),
        91: ("투레밀리아 원로원 경비부\n알콘대 대장\n레슬리 플래허티 대위", "formatting", "소속과 직책의 줄별 구조를 유지하며 표기를 정리했다."),
        103: ("너희가 순순히 날\n도적으로 착각해 줘서 다행이었어", "naturalness", "助かった의 안도 뉘앙스를 자연스럽게 옮겼다."),
        110: ("이 앞이\n저 탑 같은 신전인가……<$0C>저 바보가 눈에 띄어 버린\n탓도 있으니까<$0C>독실한 오르키나교 사람들이\n많아 보이는 곳은 피해 두는 게\n좋겠어<$0C>도시에서 정보를 모아 볼까", "naturalness", "제어 코드를 유지하면서 인과 표현과 줄 호흡을 다듬었다."),
        118: ("그때는 아직 １４, ５살짜리\n애송이였으니까요", "naturalness", "나이를 나타내는 수치와 구어체를 자연스럽게 결합했다."),
        125: ("이런, 이런. 전 알콘대 소속의\n고문이 특기인 숙녀분\n아닙니까", "naturalness", "수식 관계를 명확히 했다."),
        131: ("설마…… 나한테\n조금은 마음이 있었던 거야?", "semantic_accuracy", "意識されてた의 연애 감정 뉘앙스를 반영했다."),
        133: ("그래. 그러니 그렇게 되기 전에\n카르분클루스에서\n지원 부대를 부르는 거야", "terminology", "救援部隊를 군사 문맥의 '지원 부대'로 통일했다."),
        137: ("어~라~?\n알스 폐하 아니십니까", "register", "늘여 말하는 도발적 호칭의 어조를 살렸다."),
        151: ("여기서는 코드 해석과 변환\n실험이 진행됐던 모양이야", "naturalness", "명사구의 중복 조사를 제거했다."),
        153: ("리피아가 이사의 아이라는 말을 들어도\n무슨 소린지 모르니, 시키는 대로\n하면 되겠지 하고……", "semantic_accuracy", "발언을 들은 주체와 이어지는 판단을 분명히 했다."),
        166: ("그런 표정 짓지 마.\n유혹해 버릴 거야<$15>00", "register", "장난스러운 경고의 미래 뉘앙스를 살렸다."),
        168: ("네…… 모두와\n오이겐 씨를\n믿고 있어요", "naturalness", "신뢰 대상에 맞도록 조사를 바로잡았다."),
        172: ("그래. 저항군의\n새 지도자♪로서도", "terminology", "조직명과 직책을 확정 용어로 통일했다."),
        173: ("２명이 제시하는 섭리를 선택해\n멸망의 노래를 없애고 혼돈에서\n낙원 노와레를 만들어 냈다", "naturalness", "불필요한 번역투를 줄이고 문장 연결을 다듬었다."),
        187: ("그래? 난……\n이상하게도 그리운 느낌이 들어", "naturalness", "不思議と의 부사적 뉘앙스를 자연스럽게 반영했다."),
    },
    69: {
        5: ("나도 미니멈 레이디의 의견에는\n찬성이지만, 그렇게 『해야 하는지』는\n모르겠어", "semantic_accuracy", "べき의 당위 의미를 자연스러운 문장으로 복원했다."),
        6: ("그걸 말하면 니콜이 너희\n곁을 떠난 의미가 없어", "semantic_accuracy", "생략된 목적어를 보충해 문맥을 명확히 했다."),
        14: ("니콜은 괜찮겠지?", "punctuation", "확인을 구하는 의문문의 종결을 반영했다."),
        18: ("로그레스 길다브를 봉인하면\n이 나라에 쳐들어가기는 쉽다.\n공중 회랑 정지 따위는 구실일 뿐이다", "naturalness", "조사와 군사적 서술을 자연스럽게 정리했다."),
        30: ("나…… 역시 아무것도 모르는\n어린애였을 뿐이야.\n한심해……", "semantic_accuracy", "ただの의 자조적 한정 의미를 반영했다."),
        38: ("길다브…… 죽여!", "register", "殺って의 거친 명령 어조를 직접적으로 살렸다."),
        46: ("뭔가…… 유적……인 검까?", "naturalness", "화자의 말버릇을 유지하면서 서술형 결합을 바로잡았다."),
        57: ("얼른 당신 자신을\n믿을 수 있게 해 달라고", "naturalness", "신뢰의 대상을 자연스러운 한국어로 정리했다."),
        62: ("게다가 그 코드 디스크의 정밀 조사가\n끝나면 원로원과 성황의 관계에도\n종지부를 찍게 되겠지", "semantic_accuracy", "精査와 귀결 관계를 정확히 반영했다."),
        75: ("우선 도시 안에서\n탐문해 보자", "terminology", "聞き込み를 조사 문맥의 '탐문'으로 옮겼다."),
        78: ("하지만 이사신에게 리얼의 섭리를\n아뢰지 않는 한 세계는 결정화되지\n않는 게 아니었나?", "naturalness", "부정 의문문의 문법을 자연스럽게 다듬었다."),
        82: ("바이스의 명령이다\n성황의 부탁이다 하며 이리저리 휘둘려\n눈앞의 목적에만 집중해 버려", "semantic_accuracy", "右往左往의 피동적 혼란을 문맥에 맞게 표현했다."),
        84: ("부디\n들여보내 주시기를――", "semantic_accuracy", "통행 허가를 청하는 お通し의 의미를 바로잡았다."),
        91: ("그 사람은 날 죽일 생각으로\n카르분클루스로 가는 사자로\n임명한 거야", "semantic_accuracy", "사자로 명한 행위를 자연스럽고 정확하게 옮겼다."),
        100: ("사과할 것 없어. 난 그 사람을\n……더글러스 경을 눈앞에서\n죽게 하고 말았어", "semantic_accuracy", "의도적 방치로 오해되지 않도록 원문의 결과 표현을 살렸다."),
        102: ("……그럼 네 눈을\n뜨게 해 주지", "semantic_accuracy", "目を覚まさせる의 비유를 원문의 표현에 가깝게 복원했다."),
        110: ("나는 노와레 １２용사의 수장\n『심려의 아를루』.\n성지 노와레를 이끄는 자", "formatting", "호칭과 고유명사의 확정 표기를 유지하며 첫 줄을 정리했다."),
        129: ("그건 성지 노와레에서 들어라", "naturalness", "지시형으로 생략된 문장을 자연스럽게 완성했다."),
        149: ("글쎄, 좋지는 않겠지.\n본인은 납득하고 있어", "semantic_accuracy", "현재 상태를 나타내는 시제로 바로잡았다."),
        154: ("웬만한 비광정보다 훨씬 빨라.\n카르분클루스로 가자고", "register", "동행을 권하는 거친 구어체로 자연스럽게 다듬었다."),
        169: ("여자와 아이를 포함해 ４명인가……\n상대하기엔 좀 모자라지만, 뭐 좋다", "semantic_accuracy", "ハンデ를 전투 상대의 수적 열세라는 문맥으로 자연스럽게 풀었다."),
        178: ("이렇게 경비를 느슨하게 하고\n맞이해 준 것이다.\n고맙게 여겨라", "naturalness", "부자연스러운 사동 표현을 고치고 호흡을 정리했다."),
        182: ("새로 너를 고용할 테니\n용병으로서 저항군을\n도와줘라", "terminology", "レジスタンス의 확정 표기 '저항군'을 적용했다."),
        186: ("네. 지적인 안경 미인인지는\n모르겠지만〜\n안경 미인 소니아 칼라일입니다〜", "naturalness", "수식 관계가 어색한 표현을 바로잡았다."),
        192: ("제게는 들립니다.\n성지 노와레에 잠든 이사신의\n각성을 기다리는 고동이", "semantic_accuracy", "기다림의 대상이 이사신의 각성임을 명확히 했다."),
        195: ("제국군도 진압을 위해\n전력을 크게 할애하고 있어", "naturalness", "주어와 군사 용어의 결합을 자연스럽게 정리했다."),
    },
}


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def main():
    REVIEWED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    summary = []
    for batch_no, edits in EDITS.items():
        batch_id = f"batch_{batch_no:04d}"
        draft_path = DRAFTS / f"{batch_id}.jsonl"
        reviewed_path = REVIEWED / f"{batch_id}.jsonl"
        report_path = REPORTS / f"{batch_id}_review.json"
        rows = load_jsonl(draft_path)
        modifications = []
        for idx, (after, category, reason) in sorted(edits.items()):
            before = rows[idx]["translation_ko"]
            if before == after:
                continue
            rows[idx]["translation_ko"] = after
            modifications.append({
                "row_index": idx,
                "tm_id": rows[idx]["tm_id"],
                "source_text": rows[idx]["source_text"],
                "before": before,
                "after": after,
                "category": category,
                "reason": reason,
            })
        write_jsonl(reviewed_path, rows)
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
                "draft": str(draft_path.relative_to(ROOT)).replace("\\", "/"),
                "source": f"work/translation/tm_v2/batches/source/{batch_id}.jsonl",
                "rules": "work/translation/tm_v2/TRANSLATION_RULES.md",
                "style_guide": "work/translation/glossary_agent/style_guide.md",
                "glossary": "work/translation/glossary_agent/glossary.csv",
            },
            "output": str(reviewed_path.relative_to(ROOT)).replace("\\", "/"),
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
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary.append((batch_id, len(rows), len(modifications)))
    for item in summary:
        print(f"{item[0]} rows={item[1]} modified={item[2]}")


if __name__ == "__main__":
    main()
