import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "work/translation/drafts"
REVIEWED = ROOT / "work/translation/reviewed"
REPORTS = ROOT / "work/translation/reviews"
REVIEWER = "/root/review_batch_0058_0060"
DRAFT_AUTHOR = "/root/audit_boundary_integration"


EDITS = {
    85: {
        38: ("새로 제정된 법 아래\n제국의 폭정이 시작됐다고 들었습니다.\n에블에 사는 친구가 걱정됩니다……", "terminology", "エブル의 확정 지명 표기 '에블'을 적용했다."),
        43: ("호제아 님은 판단을 그르쳤어.\n너희 같은 야만적인 현종을\n이곳에 들이다니……!<$0C>이 무슨 실책! 이 무슨 어리석음!\n――분통이 터질 지경이다", "semantic_accuracy", "失態를 상태를 뜻하는 '실태'가 아니라 잘못을 뜻하는 '실책'으로 바로잡았다."),
        46: ("안트락스를 함락시키고\n그다음은 에블, 바트라키테스……\n혹사당한 병사들은 죽을 맛이지<$0C>군대에 들어왔으니 전쟁은 각오했어.\n하지만 이렇게 사람을 막 부리면\n병사들도 피폐해지는 법이야", "terminology", "エブル의 확정 지명 표기 '에블'을 적용했다."),
        73: ("오르키나교는\n많은 나라와 사람들에게\n사교라 불리며 멸시받고 있습니다<$0C>하지만 그것은\n가르침의 일부가 확대 해석되어\n악의적인 인상 조작을 당한 탓입니다<$0C>……확실히 우리는 멸망을\n부정할 수 없습니다<$0C>하지만 그 멸망은\n단순한 생명의 멸망이 아니라\n신생을 위한 위대한 포석입니다", "naturalness", "印象操作をされている를 직역투인 '인상이 조작되다' 대신 인상 조작을 당한다는 뜻으로 옮겼다."),
        89: ("알고 있습니다.\n하지만 제국군은 만만하게\n볼 상대가 아닙니다<$0C>이 증표를 가지고 있으면\n제국 영내 가게에 있는 협력자가\n물건을 팔아 줄 겁니다<$0C>빈틈없이 준비해서\n부디 우리 지도자를\n구해 주세요!", "terminology", "조직 직책 リーダー를 확정 표기 '지도자'로 통일했다."),
        91: ("나도 경비만 하지 말고\n카지노에 가고 싶다고……<$0C>정말 손해 보는 역할이야.\n옆 녀석은 보기만 해도 답답하고, 일은 재미없고\n군인 따위 그만둘까", "naturalness", "暑苦しい를 단순히 부담스럽다가 아니라 보기만 해도 덥고 답답한 인상을 준다는 뜻으로 다듬었다."),
        99: ("저보다는\n아내를 닮았겠죠.\n특히 볼의 보조개가요……", "naturalness", "마지막 명사구의 조사와 어순을 자연스럽게 다듬었다."),
        103: ("스스로 생각해야 하고\n도움이 되어야 한다고 생각했는데\n전혀 잘 안 됐어!", "grammar", "병렬되는 두 생각을 연결해 한국어 문장을 완성했다."),
        106: ("완전히 회복했습니다", "semantic_accuracy", "全回復를 여러 대상을 모두 회복했다는 뜻이 아니라 완전 회복으로 정확히 옮겼다."),
        119: ("궁극의 몬스터를 목표로 하는\n우리에게는\n미지의 힘이 있습니다<$0C>자, 동포여\n덤비는 겁니다", "naturalness", "目指す를 부자연스러운 '지향하다' 대신 목표로 한다는 뜻으로 옮겼다."),
        125: ("……이제 충분하다. 라르크.\n넌 내가 손을 잡아 줄 가치도 없어", "semantic_accuracy", "手を組むには値しない의 가치 판단 주체가 알스임을 분명히 했다."),
        144: ("지나치게 활기찬 아가씨", "word_choice", "やたら元気를 불필요하다는 뜻의 '쓸데없이'가 아니라 유난히 활기차다는 인상으로 옮겼다."),
        155: ("싸우는 건 야만적이라고…… 생각해", "semantic_accuracy", "화자의 견해를 청자에게 되묻는 문장으로 바꾸지 않고 원문의 망설이는 진술로 복원했다."),
        157: ("그 상냥했던 마하트 폐하께서\n서거하시다니 믿을 수 없군<$0C>지금 아내에게 꽃을 따게 하고 있어.\n가장 아름다운 꽃을 장식해서\n폐하께 바칠 수 있도록……<$0C>괜찮다면 우리 아내를\n도와주지 않겠나", "register", "왕의 죽음을 자연스러운 높임 표현으로 다듬고 주격 높임을 보완했다."),
    },
    86: {
        9: ("……흥. 공인 용병 따위가\n황태자 전하의 위광을 등에 업고", "terminology", "認可傭兵의 확정 표기 '공인 용병'을 적용했다."),
        38: ("오르키나의 달\n이야기에 겁먹은 녀석이\n몇 명 있는 모양인데――<$0C>이렇게 멀리 떨어진 곳에서\n겁먹고 있다니 한심하군", "semantic_accuracy", "世話ない를 돌봐 줄 수 없다는 뜻이 아니라 한심하다는 비꼼으로 옮겼다."),
        48: ("변경의 숲 D01에서\n", "formatting", "지명과 맵 식별자의 띄어쓰기를 통일했다."),
        50: ("디아만트 T05로\n", "formatting", "지명과 맵 식별자의 띄어쓰기를 통일했다."),
        52: ("카르분클루스 T01 왼쪽으로\n", "formatting", "지명과 맵 식별자의 띄어쓰기를 통일했다."),
        54: ("순조로운 여행길의 동반자로\n『마타타비 형제사』가 정성껏\n만든 지도는 어떠십니까?<$0C>다가올 장사를 위해\n여행자에게 무료 제공 중입니다.\n자, 당신도 사양하지 마시고……", "naturalness", "健やかなる旅를 사람의 건강이 아니라 순조로운 여행을 기원하는 홍보 문구로 다듬었다."),
        85: ("노와레 오두막 ７로\n", "formatting", "지명과 맵 식별 숫자의 띄어쓰기를 통일했다."),
        86: ("그린힐 의장님!\n돌아오셨습니까――<$0C>부디 이 앞의 의사당까지\n등원해 주십시오", "semantic_accuracy", "議場를 직책인 '의장'이 아니라 회의 장소인 '의사당'으로 바로잡았다."),
        88: ("내 일은\n내 손으로 끝내도록 하지", "naturalness", "自分の始末をつける를 부자연스러운 '내 처리' 대신 스스로 결말을 낸다는 뜻으로 옮겼다."),
        91: ("다음에 또 유흥가에 가면\n아빠한테 이를 거예요!\n아이가 갈 곳이 아니라고요!", "semantic_accuracy", "상대를 타이르는 경고를 질문처럼 옮긴 부분을 바로잡았다."),
        110: ("디아만트 T05　기타에서\n", "formatting", "지명과 맵 식별자의 띄어쓰기를 통일했다."),
        113: ("쉰 덕분에 몸은 절호조!\n다음 안트락스 시가지\n경비 임무도 문제없어!", "naturalness", "次の任務までにはバッチリ를 다음 임무를 수행할 준비가 됐다는 뜻으로 자연스럽게 옮겼다."),
        120: ("조국에 반역의 칼날을 겨누고\n친형을 자기 손으로 죽이고\n마침내 왕좌를 손에 넣은 남자……<$0C>알스 님의 삶은 연극 같아.\n게다가 그 근심 가득한\n존안은 솔직히 반칙이라고 생각해", "naturalness", "半生을 한국어 대사에서 낯선 한자어 대신 한 사람의 삶이라는 뜻으로 풀었다."),
        131: ("충분하다.\n새로운 미래를 선택한 인간의 아이여\n나와 계약하기를 바란다", "character_voice", "신적 존재의 계약 요청을 장중한 어조로 다듬었다."),
        132: ("한번 메리디아 병사들에게\n몹쓸 일을 당하고 나서\n아버지는 완전히 소심해졌어<$0C>그래서 내가 이렇게 나선 거야", "naturalness", "だから。わたしがこうして의 생략된 행동 관계를 문맥에 맞는 완성 문장으로 옮겼다."),
        135: ("너무 고집만 부리면\n잡을 수 있는 기회도 놓치게 돼", "naturalness", "충고문을 어색한 의문형으로 끝낸 부분을 자연스럽게 다듬었다."),
        142: ("디아만트성 D02(왼쪽)으로\n", "formatting", "확정 지명과 맵 식별자를 구분하고 방향 괄호를 한국어 표기로 정리했다."),
        149: ("이 대성당은 습격을 피했다……\n다들 그렇게 말하지만\n저는 그렇게 생각하지 않습니다<$0C>호제아 성하의 높은 신격이\n닥쳐오는 사기를 물리쳤다……\n그렇게 생각하지 않을 수 없습니다", "semantic_accuracy", "そう思えてなりません를 다른 가능성을 배제한다는 뜻이 아니라 그렇게 생각하지 않을 수 없다는 의미로 옮겼다."),
        152: ("그럴 리가 있겠냐!<$0C>짐이 가득해서 못 들고 가니\n에블까지 가져가 달라는\n부탁을 받은 거야!", "terminology", "エブル의 확정 지명 표기 '에블'을 적용했다."),
        170: ("미안해요.\n말을 많이 해서는 안 돼요", "naturalness", "あまり話してはいけない를 '별로 이야기하다'라는 직역투 없이 자연스럽게 옮겼다."),
        173: ("높은 탑 D01로\n", "formatting", "지명과 맵 식별자의 띄어쓰기를 통일했다."),
        181: ("내 친척 중에는\n나의 엄격한 교육 방침이\n잘못됐다는 사람도 있습니다<$0C>그래도 나는 １인의 부모로서\n아이가 올바르게 자라길\n바라요", "naturalness", "１人の親를 중복된 '한 명의 부모' 대신 자연스러운 자격 표현으로 다듬으면서 숫자를 보존했다."),
        184: ("알스 폐하는 이제\n황제의 그릇이 아니다――<$0C>우리 양식 있는 제국 신민들이\n무익하게 백성을 괴롭히는 황제를\n왕좌에서 끌어내릴 때다", "word_choice", "いたずらに를 구어적인 '괜히'보다 공식 대사에 맞는 '무익하게'로 옮겼다."),
    },
    87: {
        3: ("의사당에 들어가는 건 자유지만\n조금이라도 수상한 행동을 하면\n우리 칼의 녹으로 만들어 주마", "semantic_accuracy", "議場를 직책인 '의장'이 아니라 회의 장소인 '의사당'으로 바로잡았다."),
        25: ("지도를 그려 온 지도 어언 수년――<$0C>형제 사이에서 전설로 불리던\n코핀 마을에 도착하다니……\n꿈만 같잖아!<$0C>――여행자여.\n당신에게도 내 행복을\n나눠 주지!", "grammar", "겹쳐 쓰인 '지도를 그린 지도'를 자연스러운 관용 표현으로 바로잡았다."),
        28: ("뭐, 여기서 생각만 해 봐야\n아무 소용없지", "naturalness", "始まらない를 직역하지 않고 행동하지 않으면 소용없다는 뜻으로 옮겼다."),
        36: ("효도는 할 수 있을 때 해.\n안 그러면 후회할 거야", "semantic_accuracy", "충고를 청자에게 묻는 의문형으로 바꾸지 않고 단정적인 경고로 복원했다."),
        47: ("인간은……\n언젠가 기억해 내는 것조차\n못하게 되는 법입니다", "naturalness", "思いだすことすらできない의 중복 용언을 간결하고 자연스럽게 다듬었다."),
        50: ("……큰일을 해내겠다는 생각으로\n나왔어, 이 교도에 말이야.\n더운 것도 참고……<$0C>하지만 그 슬픈 사건이 있었잖아……<$0C>도시에서 １번가는 대로에\n내 가게를 갖겠다는 꿈도\n이래선 당분간 미뤄야겠네", "naturalness", "街で１番の大通り를 서수 직역 대신 '１번가는 대로'로 자연스럽게 옮기면서 숫자를 보존했다."),
        51: ("카르분클루스 T00 왼쪽으로\n", "formatting", "지명과 맵 식별자의 띄어쓰기를 통일했다."),
        65: ("……처음 뵙겠습니다\n저는 『마타타비 형제사』의 열일곱째 아들.\n이 펠리스 마을의 측량 담당이죠<$0C>당신들 여행자지?\n나이도 옷차림도 제각각이고\n――틀림없이 그렇지?<$0C>그렇다면 이야기는 간단해.\n이 마을 지도는 공짜로 줄 테니\n검증을 부탁할게", "terminology", "フェリス의 확정 지명 표기 '펠리스'를 적용했다."),
        67: ("뭐어!? 가 본 적도 있어?\n그렇구나, 아는 게 당연하겠네.\n공인 용병이니까~~", "terminology", "認可傭兵의 확정 표기 '공인 용병'을 적용했다."),
        69: ("(저쪽으로 가는 건 그만둘까――)", "formatting", "한국어 문장에 맞는 괄호 표기로 통일했다."),
        72: ("사쥬네……\n우리를 도와준\n도적단 녀석을 감시하고 있어", "semantic_accuracy", "サージュ가 감시 주체인 것처럼 잘못 옮긴 부분을 바로잡아 니콜이 사쥬의 도적단원을 감시한다는 문맥을 복원했다."),
        83: ("샘에 퍼지는 물결을……\n제 눈은 이제……\n제대로 포착하지 못합니다<$0C>하지만 제 마음에는\n분명히 퍼지는 파문이\n비치고 있습니다……", "register", "한 대사 안에서 1인칭 높임말을 '제'로 통일했다."),
        92: ("이 앞은 원로원 의사당이다.\n용건이 있다면 막지 않겠지만\n놀러 온 거라면 등 뒤를 조심해라", "terminology", "議会를 장소 문맥에 맞게 원로원 의사당으로 다듬었다."),
        97: ("제국에서 알스 황제가\n비판받고 있다는\n참으로 안타까운 소문을 들었네<$0C>어떤 시대든 위정자는\n나라의 모든 업을 짊어지고\n규탄받는 것이 운명……<$0C>내가 걱정하는 건\n이 일로 알스 황제의\n숭고한 뜻이 꺾이는 것이야<$0C>뭐, 형조차\n그 손으로 죽일 각오다.\n강인한 정신력을 지녔겠지만", "semantic_accuracy", "糾弾을 법률 절차인 탄핵이 아니라 비난과 규탄을 받는다는 뜻으로 바로잡았다."),
        100: ("(……뭐랄까……\n　뭐, 적국 사람이라는 것만\n　안 들키면 어떻게든 되겠지)<$0C>(……다음은 자다로군……)", "naturalness", "목적지 자다와 호칭처럼 읽히는 '자다 군'을 구분하고 괄호 표기를 통일했다."),
        103: ("저항군을 소탕하려고\n여기까지 파견됐지만\n혹독한 기후 때문에 뜻대로 되지 않는다<$0C>이 지형의 이점이 있기에\n저항군이\n잘 움직이는 걸지도 모르겠군", "terminology", "レジスタンス의 확정 표기 '저항군'을 적용했다."),
        107: ("마하트 폐하의 붕어――\n그런 소문을 믿을 만큼\n정신이 흐리진 않았어", "naturalness", "전날 한숨도 못 잔 화자의 농담이 이중 부정 없이 자연스럽게 드러나도록 옮겼다."),
        115: ("고향 바트라키테스 사람들이\n걱정되어 견딜 수 없습니다", "grammar", "걱정돼와 격식체가 충돌한 부분을 자연스러운 문장으로 다듬었다."),
        117: ("이 도시에 남길 잘했어.\n제국과 공화국의 통상이 성립하면\n항구에서 한몫 더 벌 수 있을 테니까", "naturalness", "正解だった를 직역한 '정답이었다' 대신 선택을 잘했다는 뜻으로 옮겼다."),
        132: ("…………<$0C>그렇다는 건\n난 사유물과 쓰레기를 나른 셈인가?", "naturalness", "억지로 운반했다는 문맥이 드러나도록 사역 수동의 결과를 자연스럽게 다듬었다."),
        139: ("세계 각지에 있는\n달그림자 여관을 찾으면\n마치 마음이 씻기는 듯해<$0C>어떤 여행자도 받아들이는\n노와레교의 관용을\n느낄 수 있지", "naturalness", "세계 각지에 있는 여관이라는 수식 관계를 자연스럽게 바로잡았다."),
        141: ("그건 허가증인가.\n물론 지나가도 좋아.\n난 하던 생각을 마저 하지――<$0C>우리는 언제부터 여기 있었나……\n이 의문이 문득 떠오르면\n나는 자문자답을 멈출 수 없게 된다……", "naturalness", "考え事の続きを를 불완전한 명사구가 아니라 하던 생각을 계속한다는 말로 완성했다."),
        145: ("(미동도 하지 않아……\n　소중한 사람이었겠지\n　이 무덤에 잠든 누군가는……)", "formatting", "한국어 문장에 맞는 괄호 표기로 통일했다."),
        146: ("여기서 계속 기다리겠습니다.\n여동생은 단 １명뿐인\n피가 이어진 가족이니까요……", "formatting", "たった１人의 수치를 빠뜨리지 않고 자연스러운 인원 표현으로 복원했다."),
        148: ("왠지 도시가 시끄럽네.\n……무슨 일이 있었을까?", "character_voice", "かしら의 여성 화자 어감을 자연스러운 의문형으로 반영했다."),
        156: ("기하 회랑 알비스・혼탁한 기억  제３층", "terminology", "混濁する記憶의 프로젝트 내 확정 제목 표기 '혼탁한 기억'을 적용했다."),
        164: ("너무 많은 걸 잃었습니다.\n이제 지쳐 버렸습니다.\n아무것도 생각하고 싶지 않습니다……", "register", "한 대사 안에서 격식체 종결을 통일했다."),
        187: ("에블 유적 D05로\n", "terminology", "エブル遺跡의 확정 지명 표기와 맵 식별자 띄어쓰기를 적용했다."),
        190: ("EV01_04_0500B\n이벤트 캐릭터 삭제\n그만두기", "ui", "イベント君을 개발용 이벤트 캐릭터를 가리키는 통용 표기로 옮겼다."),
    },
}


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


for number in (85, 86, 87):
    batch_id = f"batch_{number:04d}"
    draft_path = DRAFTS / f"{batch_id}.jsonl"
    reviewed_path = REVIEWED / f"{batch_id}.jsonl"
    report_path = REPORTS / f"{batch_id}_review.json"
    rows = read_jsonl(draft_path)
    modifications = []
    for row_index, (after, category, reason) in sorted(EDITS[number].items()):
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
