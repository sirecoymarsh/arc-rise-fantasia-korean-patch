import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "work" / "translation" / "drafts"
REVIEWED = ROOT / "work" / "translation" / "reviewed"
REPORTS = ROOT / "work" / "translation" / "reviews"
REVIEWER = "/root/review_batch_0058_0060"
DRAFT_AUTHOR = "/root/translate_batch_0009"

EDITS = {
    70: {
        2: ("오팔루스 방어 작전은 전부 알스 님과\n동료분들이 지시해서\n실행했다고 해", "terminology", "인명 존칭의 띄어쓰기를 프로젝트 표기에 맞췄다."),
        8: ("그나저나 엄청 큰 상대였어.\n뭐, 이 몸의 그릇 크기에\n비하면 소인배였지만", "naturalness", "크기와 인물의 그릇을 잇는 원문의 말장난을 자연스럽게 살렸다."),
        17: ("……이 녀석\n그저 곱게 자란 아가씨가 아니라\n아예 무지한 거 아냐?", "semantic_accuracy", "箱入り와 無知의 대비를 정확히 반영했다."),
        22: ("세계 곳곳의 가도변에\n띄엄띄엄 서 있잖아", "naturalness", "부자연스럽게 띄어진 합성어를 정리했다."),
        36: ("뭘 생각한다는 거야?\n이런 데서 １명이서 말이야!", "naturalness", "인원수 １을 보존하면서 조사를 자연스럽게 고쳤다."),
        37: ("현종!\n네놈들이 호제아 님을 해쳤나!\n우리 신종을 멸망시키려는 것이냐!", "terminology", "인명 존칭의 띄어쓰기를 통일했다."),
        38: ("원로원 의장에게 보내는 친서를\n맡아 왔습니다.\n전해 주시길 바랍니다", "semantic_accuracy", "取り次ぎ를 문서 전달 요청의 의미로 바로잡았다."),
        41: ("황제 폐하께\n알현을 주선해 주시겠습니까", "semantic_accuracy", "取り次ぎ를 황제 알현 주선이라는 문맥에 맞게 옮겼다."),
        49: ("아델을 어쩔 생각이지", "register", "추궁하는 남성 화자의 단정적 어조를 살렸다."),
        51: ("그럼 이사의 아이여, 그대에게 묻겠다.\n나의 힘, 『순결』의 로고스가\n필요한가", "register", "汝에 맞는 고전적 호칭과 장중한 어조를 적용했다."),
        53: ("있잖아! １명이서 가지 않으면\n정찰이 안 되잖아", "naturalness", "수치 보존 상태에서 조사를 자연스럽게 고쳤다."),
        64: ("저 문의 열쇠는 코드지?\n내가 잠금 코드를 다시 작성할게", "semantic_accuracy", "コードを書き換える를 코드 재작성의 의미로 명확히 했다."),
        66: ("야, 너희, 그만둬.\n그 녀석은 가투라라는\n고양이 요괴 여자라더군", "naturalness", "化け猫女의 수식 관계를 자연스럽게 옮겼다."),
        70: ("모르겠슴다.\n제국 병사들이 어디론가 끌고 간 뒤\n그걸로 소식이 끊겼슴다……", "semantic_accuracy", "それっきり를 이후 소식이 없다는 의미로 풀었다."),
        72: ("놈들이 덤벼든다.\n넌 물러나 있어", "semantic_accuracy", "襲ってくる의 공격 상황을 명확히 했다."),
        87: ("비슷하다고는 생각했지만, 다른 군인들과\n옷 입는 방식이 달라서……", "semantic_accuracy", "似ている를 외형 유사성으로 바로잡았다."),
        111: ("나는 말이야, 다시 한번 너와\n헤어져야 해.\n다시 １번 더 잃어야 한다고", "naturalness", "수치 １을 유지하면서 반복 상실의 표현을 자연스럽게 다듬었다."),
        117: ("그렇다면 섬뜩하긴 하지만\n딱히 호들갑 떨 일은\n아닌 것 같은데", "semantic_accuracy", "気味が悪い를 상황의 섬뜩함으로 정확히 옮겼다."),
        122: ("자의식을 지닌 것이에요〜", "naturalness", "분리된 서술격 조사를 바로잡았다."),
        128: ("전 불안해서 가슴이 두근거림다", "naturalness", "불안으로 인한 심박을 자연스러운 구어로 표현했다."),
        137: ("그 ２명……\n역시 한패였구나", "semantic_accuracy", "繋がっていた를 공모 관계라는 문맥에 맞게 옮겼다."),
        146: ("……그래, 내가 레온이다", "naturalness", "자기 확인에 맞지 않는 직역투를 제거했다."),
        151: ("리피아의 의사에 따라서는\n그녀를 어딘가로\n데려다줘야 할 수도 있잖아?", "terminology", "意向를 문맥에 맞는 '의사'로 옮겼다."),
        164: ("그리고 알스 님은 형님 일행을\n현상 수배했슴다", "terminology", "인명 존칭 띄어쓰기를 통일했다."),
        166: ("우연일 리 없어", "naturalness", "강한 부정 판단을 간결한 구어체로 다듬었다."),
        167: ("오, 난처한 표정이네\n라르크 군", "semantic_accuracy", "気まずそう를 난처하고 어색한 표정으로 바로잡았다."),
        189: ("이 앞에 푸른 달의 신이 머무는\n거처가 있습니다.\n안트락스는 그 너머입니다", "semantic_accuracy", "宿를 신의 거처라는 문맥으로 바로잡았다."),
        192: ("이사신과의 계약으로 보호받은\n이 몸도 이제\n쇠해 가고 있다", "semantic_accuracy", "朽ちる를 육체가 쇠하는 의미로 자연스럽게 옮겼다."),
    },
    71: {
        8: ("■■컷13-18■■\n", "formatting", "내부 컷 표식에 추가된 불필요한 공백을 제거했다."),
        14: ("저 상태라면 나보다 ３, ４년은\n먼저 깨어났을 거야", "naturalness", "추정형 시제와 구어체를 자연스럽게 다듬었다."),
        19: ("있다 해도\n군 소속 아니겠슴까?", "register", "니콜의 말버릇과 추정형 어조를 일치시켰다."),
        53: ("내가 아무것도…… 몰랐기\n……때……문이야", "formatting", "단어가 비정상적으로 네 줄로 분리된 번역을 원문의 두 줄과 말더듬에 맞게 복원했다."),
        61: ("이 땅에 쓰러진 용맹한 자여.\n깨어나라, 카오스의 이름으로!", "register", "의식문에 자연스러운 호격과 명령형을 적용했다."),
        69: ("……당신은 이사의 아이.\n심마프가 당신의 휘하에\n들어온 것이군요", "semantic_accuracy", "元に下る를 복종 관계라는 설정 문맥에 맞게 옮겼다."),
        82: ("그건 분명\n멸망 아니었슴까?", "register", "니콜의 일관된 말버릇을 적용했다."),
        85: ("가장 끔찍한 건 도시의 정원을\n정해 놓고, 그 수를 넘은 주민은……", "semantic_accuracy", "１番을 순번이 아닌 최상급으로 바로잡고 定員을 정원으로 옮겼다."),
        96: ("사쥬 감시는 안 해도 돼?", "semantic_accuracy", "見張りはいいの의 생략된 확인 의미를 분명히 했다."),
        100: ("있잖아, 리피아. 바다는 시간대에 따라\n해수면 높이가 달라져.\n그걸 밀물과 썰물이라고 해", "terminology", "潮를 자연 현상의 통용어로 풀어 썼다."),
        102: ("……지금은 조금\n사정이 다를지도 모르지♪", "naturalness", "원문의 줄 호흡과 장난스러운 종결을 살렸다."),
        118: ("리피아!?\n젠장, 그 녀석 왜 저렇게 초조해하지!", "semantic_accuracy", "焦る를 단순 이동이 아닌 초조함으로 옮겼다."),
        133: ("쓸데없는 짓을 한 건\n사쥬가 아니야.\n뻔히 그라를 넘겨주고 말이야", "naturalness", "비난하는 구어체의 연결을 자연스럽게 다듬었다."),
        137: ("이사신께 바칠 섭리를 고르는 건\n이사의 아이의 의지뿐이야", "semantic_accuracy", "イーサ神の元に의 목적 관계를 명확히 했다."),
        145: ("호존에 오염된 대지에서만\n살 수 있는 유사 인간이기에\n리얼의 섭리에 현혹되는 것이다", "semantic_accuracy", "人間もどきを 경멸적이면서도 의미가 분명한 표현으로 옮겼다."),
        152: ("지금도 이매지널신 곁에서는\n수십만 명이나 되는 사람들이\n잠들어 있어", "naturalness", "神の元의 위치 관계를 자연스럽게 다듬었다."),
        160: ("의장이라면 이미 이 세상에 없을 겁니다.\n그 디스크를 남긴 채로요", "naturalness", "문장 끝의 ね를 부드러운 설명조로 반영했다."),
        164: ("……길다브가\n당신의 휘하에 들어왔군요.\n그렇다면 저도 따르겠습니다", "semantic_accuracy", "복종 관계를 나타내는 元に下る를 정확히 옮겼다."),
        170: ("그럼 제가 라르크에게\n코드 제어로 세뇌를 걸겠습니다", "naturalness", "施す를 세뇌를 건다는 자연스러운 결합으로 고쳤다."),
        171: ("그럼이라니\n어디 가는 거야", "formatting", "인용된 접속 표현의 불필요한 띄어쓰기를 바로잡았다."),
        180: ("여전히 이상한 행보를\n보이시는군요, 교주 류즈 님", "semantic_accuracy", "動き方를 인물의 수상한 행보라는 문맥에 맞게 옮겼다."),
        186: ("……생각해 봐도 모르겠어", "naturalness", "화자의 독백형 결론을 자연스럽게 다듬었다."),
        191: ("전하…… 주둔군을 이끄는\n이 클라이드가 이런 사태를\n초래하고 말다니……", "semantic_accuracy", "자책하는 미완 문장의 생략 의미를 보충했다."),
        192: ("나도 어머니와 하인들이\n살해당했을 때 충격받았어.\n슬픔은 모두에게 똑같아", "naturalness", "보편적 슬픔을 나타내는 문장을 자연스럽게 다듬었다."),
    },
    72: {
        0: ("죄송하지만\n여러분은 자리를 비워 주세요", "naturalness", "席を外す의 통용 표현으로 바로잡았다."),
        6: ("이런, 빗나갔군.\n하지만 다음엔 빗맞히지 않아", "semantic_accuracy", "두 번의 外す를 동일한 사격 의미로 일관되게 옮겼다."),
        24: ("■■■■플래그 잠들어 있음■■■■\n", "naturalness", "개발용 표식의 일본어식 서술을 자연스럽게 다듬었다."),
        39: ("너희는 먼저 배에 올라 조타실을 점거해.\n바다로 나가면 우리 세상이야", "naturalness", "こっちのもんだ의 승산을 자신하는 관용 표현을 살렸다."),
        42: ("어느새라고 해야 하나\n바로 조금 전에 여기에 온\n것만 같은 느낌도 들고", "naturalness", "ばっかり의 시간상 뉘앙스를 자연스럽게 다듬었다."),
        46: ("오이겐이라는 떠돌이 용병의\n도움도 있어서\n피해를 최소화할 수 있었습니다", "semantic_accuracy", "旅の傭兵의 수식 관계와 力添え의 의미를 명확히 했다."),
        53: ("저…… 지금 저항군에 있슴다.\n그래서 돌아갈 수 없슴다", "terminology", "レジスタンス의 확정 표기 '저항군'을 적용했다."),
        60: ("제가 그런 말을 했던가요오?", "register", "소니아의 늘이는 말투를 일관되게 적용했다."),
        69: ("■■컷4-6■■\n", "formatting", "내부 컷 표식에 추가된 불필요한 공백을 제거했다."),
        70: ("신을 죽일지는 모릅니다.\n지킬 수 없는 약속은 하고 싶지 않습니다", "register", "한 대사 안에서 혼재한 존댓말 종결을 통일했다."),
        75: ("■■컷24-26■■\n", "formatting", "내부 컷 표식에 추가된 불필요한 공백을 제거했다."),
        76: ("아마 당신들과 마찬가지겠죠. 오르키나교도가\n아닌, 호기심으로 찾아온 여행자랄까", "semantic_accuracy", "교도 여부와 여행 동기의 문장 관계를 바로잡았다."),
        89: ("그건 무한하다고도 할 수 있는 변용\n패턴 중에서 하나의 해를 연산하는\n아득할 만큼 고된 작업입니다", "terminology", "解를 기술 문맥의 '해'로 옮기고 조사 관계를 정리했다."),
        105: ("극악무도한 라군이란\n그대를 말하는 것이겠지", "semantic_accuracy", "悪辣非道를 자연스러운 사자성어로 바로잡았다."),
        110: ("제２ 비광정단은 임무를 마치고 귀환했어.\n그래서 널 찾으려고 했는데……", "semantic_accuracy", "미완의 의도 표현을 한국어 문맥에 맞게 보충했다."),
        114: ("아델에게 디바 자리를\n물려주고 싶지 않았겠지", "semantic_accuracy", "ディーバを継がせる의 계승 의미를 명확히 했다."),
        120: ("난 말이지, 그런 식으로\n물건을 소중히 여기지 않는 녀석들이\n정말 싫어!! 나가!!", "naturalness", "목적어와 서술어의 결합을 자연스럽게 다듬었다."),
        123: ("■■컷7-10■■\n", "formatting", "내부 컷 표식에 추가된 불필요한 공백을 제거했다."),
        125: ("아, 알겠습니다", "naturalness", "일본어 음절을 그대로 옮긴 말더듬을 한국어로 자연스럽게 바꿨다."),
        152: ("호존 없이는 살 수 없는\n현종들은 호존이 정화된 뒤\n모조리 전멸한다", "semantic_accuracy", "ことごとく死滅する의 전멸 의미를 직접적으로 반영했다."),
        172: ("루훙가를 부르려면\n녀석의 이동 경로 근처에서\n호존 오염을 일으켜야 한다", "terminology", "回遊ルート를 생물의 이동 경로로 명확히 옮겼다."),
        178: ("이미 숨이 끊어졌어……", "naturalness", "사망 상태를 나타내는 관용 표현으로 다듬었다."),
        179: ("……구해…… 준 거지?\n미안, 고맙다", "semantic_accuracy", "助かった를 구조에 대한 감사의 의미로 옮겼다."),
        188: ("아마 처리 속도가 따라잡지 못할 거야", "semantic_accuracy", "処理が間に合わない를 처리 속도 부족이라는 의미로 명확히 했다."),
        198: ("물이 빠진다는 건\n해수면 높이가\n낮아진다는 뜻이야", "naturalness", "潮が引く의 통용 표현을 적용했다."),
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
        print(f"{batch_id} rows={len(rows)} modified={len(modifications)}")


if __name__ == "__main__":
    main()
