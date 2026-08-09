import fs from "node:fs";
import path from "node:path";

const ROOT = path.join("work", "translation");
const SOURCE_ROOT = path.join(ROOT, "tm_v2", "batches", "source");
const DRAFT_ROOT = path.join(ROOT, "drafts");
const REVIEWED_ROOT = path.join(ROOT, "reviewed");
const REVIEWS_ROOT = path.join(ROOT, "reviews");

const CORRECTIONS = {
  batch_0037: {
    1: { after: "기이한 사태가 아닌가?", category: "meaning", reason: "異様의 비정상적이고 기이한 뉘앙스를 분명히 했다." },
    2: { after: "수영하고 싶어〜", category: "speaker_voice", reason: "구어체 화자의 자연스러운 반말 종결로 맞췄다." },
    4: { after: "하지만 저는 자다와 제도를\n지키고 싶어서 병사가 됐슴다", category: "naturalness", reason: "열거 조사와 니콜의 말투를 자연스럽게 정리했다." },
    6: { after: "정말 다들, 어울리지도 않게\n신경이나 써 주고 말이야", category: "naturalness", reason: "신경 써 주는 동료들을 투덜대는 뜻으로 문장을 완결했다." },
    15: { after: "헤어졌다니, 그 뒤에는?", category: "meaning", reason: "はぐれた를 대상을 놓친 것이 아니라 일행과 헤어진 뜻으로 바로잡았다." },
    21: { after: "분개할 일은 아닙니다만", category: "speaker_voice", reason: "정중한 화자의 말투와 憤る의 의미를 반영했다." },
    27: { after: "설마 이그나츠가\n그런 수를 쓰다니……\n간파하지 못한 내 탓이다", category: "meaning", reason: "読み切れなかった를 글을 다 읽지 못했다가 아니라 계략을 간파하지 못했다는 뜻으로 바로잡았다." },
    31: { after: "지적인 안경과 동안, 그리고\n저 글래머러스한 몸매――", category: "naturalness", reason: "인물의 외형 요소를 자연스럽게 병렬했다." },
    41: { after: "여러분을 지키기 위해서라면\n저는 기꺼이 몬스터의 먹이로――", category: "particle", reason: "몬스터와 먹이의 소유 관계를 나타내는 조사를 보충했다." },
    43: { after: "네가 황자가 아니고\n라르크 일행도 병사가 아니었다면?", category: "grammar", reason: "가정 조건이 두 대상 전체에 걸리도록 시제를 바로잡았다." },
    44: { after: "날 즐겁게 해 주라고.\n여러 가지로 말이야", category: "naturalness", reason: "즐거움을 받는 대상을 보충해 한국어 문장을 자연스럽게 했다." },
    45: { after: "서글프네\n내일은 내 신세가 될지도――라니\n너, 정말 반성하는 거야?", category: "meaning", reason: "明日は我が身의 관용적 의미와 이어지는 핀잔을 자연스럽게 살렸다." },
    48: { after: "우엑…… 이걸로 조종하는 검까?\n영문 모를 기계뿐……", category: "function", reason: "うっへぇ의 질색하는 반응을 감탄의 반응으로 오해하지 않도록 바로잡았다." },
    50: { after: "마침 잘 왔네.\n너보다 훨씬 순진한 녀석이", category: "naturalness", reason: "いいとこに来た의 때맞춰 왔다는 뜻을 자연스럽게 반영했다." },
    53: { after: "그래. 그 시점의 기억은 희미하다.\n이미 기억을 잃기 시작했던\n것인지도 모르겠군", category: "speaker_voice", reason: "격식 있고 절제된 화자의 종결 어조로 통일했다." },
    58: { after: "끌려 들어갈 거다, 각오해――", category: "meaning", reason: "이어질 상황을 경고하는 미래 표현과 각오하라는 뜻을 복원했다." },
    62: { after: "무슨 일이야?\n그렇게 진지한 얼굴을 하고", category: "meaning", reason: "真剣な顔를 심각함보다 진지한 표정이라는 뜻으로 바로잡았다." },
    67: { after: "일이라……\n당신이 조사 중인 건\n잘돼 가고 있어?", category: "naturalness", reason: "仕事ねぇ의 화제 되받기와 조사 중인 건에 대한 질문을 자연스럽게 이었다." },
    73: { after: "그렇습니다.\n코핀도 광대가 되어 있습니다", category: "speaker_voice", reason: "코핀의 정중한 말투와 현재 상태를 일관되게 표현했다." },
    74: { after: "그건 너무 혹독했잖아?", category: "meaning", reason: "厳しい가 예절상 엄격함이 아니라 수련이 혹독했다는 뜻임을 살렸다." },
    78: { after: "너무 끈질기게 굴면\n저도 감정적으로 나올 겁니다", category: "naturalness", reason: "상대에게 경고하는 미래 표현을 자연스럽게 완결했다." },
    79: { after: "아니다.\n기본적으로는 전혀 닮지 않았다", category: "speaker_voice", reason: "격식 있고 단정적인 화자의 말투로 맞췄다." },
    84: { after: "기뻐〜\n약속이야〜", category: "naturalness", reason: "約束だからね의 친근한 확인을 자연스러운 반말로 고쳤다." },
    86: { after: "예이까지 나왔군요", category: "naturalness", reason: "いぇい라는 감탄까지 나왔다는 관찰을 자연스럽게 표현했다." },
    92: { after: "어머나, 청소년은\n자의식 과잉이네", category: "speaker_voice", reason: "능글맞은 여성 화자의 감탄사와 말투로 맞췄다." },
    98: { after: "오히려……\n이 라스카다 관리자들이\n특별한 것일지도 모르겠군", category: "speaker_voice", reason: "절제된 남성 화자의 종결 어조로 통일했다." },
    100: { after: "그 반대도 마찬가지다.\n리피아도 닮은 사람을\n본 적 있을지도 모른다", category: "speaker_voice", reason: "격식 있고 단정적인 화자의 서술 어조를 유지했다." },
    105: { after: "하하, 하지만 그 덕에\n라르크가 용병이 된\n셈이잖아", category: "naturalness", reason: "ようなもの를 가능성이 아니라 결과상 그런 셈이라는 뜻으로 다듬었다." },
    115: { after: "그리고 사쥬와 오이겐도 그래", category: "naturalness", reason: "앞 문장의 서술을 이어받는 생략 문장을 한국어로 완결했다." },
    134: { after: "저는 검도 못 쓰는데\n기억해 두면 되는 거다!!\n라고 혼났슴다", category: "speaker_voice", reason: "니콜의 말투를 복원하고 覚えときゃいい의 뜻을 바로잡았다." },
    136: { after: "역시 이 근처는\n용사도 ８단인 나도 힘드네", category: "terminology", reason: "勇者道를 기존 용어인 용사도로 통일하고 숫자를 보존했다." },
    142: { after: "됐어, 알았으니까!", category: "naturalness", reason: "もう의 제지하는 뉘앙스를 살려 자연스럽게 다듬었다." },
    145: { after: "그 두 분은 제 얼굴을\n위위아래아래좌우좌우로\n심하게 일그러뜨립니다", category: "meaning", reason: "上上下下左右左右의 방향 순서를 정확히 복원했다." },
    147: { after: "저는 솔직히 말씀드렸습니다.\n당신의 손가락은 저를 관통할 것 같습니다.\n하지만 정말 기분 좋습니다……라고", category: "particle", reason: "손가락의 소유 관계를 나타내는 조사를 보충했다." },
    152: { after: "다만\n이런 상황에 빠지지 않는 것이야말로\n중요한 일이지만 말이지", category: "speaker_voice", reason: "강조 표현과 고풍스러운 종결을 자연스럽게 살렸다." },
    156: { after: "그 아름다운 눈에 그늘이 지면\n둔감한 라르크가 아닌 이상\n고지식한 녀석이라도 알아채겠지", category: "meaning", reason: "ない限り의 조건을 이중 부정으로 잘못 옮긴 부분을 바로잡았다." },
    159: { after: "여기 있는 물이나 식량도\n필요했겠지.\n하지만 다른 이유도 있어", category: "naturalness", reason: "장소와 필요한 물자를 자연스러운 한국어 어순으로 정리했다." },
    172: { after: "소니아 박사의 연구 결과로는\n작은 결정을 무효화하는 데도\n시간이 걸린다고 했어", category: "grammar", reason: "관형격 조사와 무효화하는 행위의 목적 표현을 보완했다." },
    177: { after: "내가 뭐 어쨌어?", category: "function", reason: "私がどうかしたの를 자신에게 무슨 문제가 있는지 되묻는 말로 옮겼다." },
    179: { after: "그럼, 리피아, 가자〜", category: "meaning", reason: "行くよ를 혼자 간다는 선언이 아니라 동행을 재촉하는 말로 바로잡았다." },
    180: { after: "어머나, 용사님이\n우리에게 질려 버렸나 보네", category: "meaning", reason: "あきれた 주체와 대상이 뒤바뀐 부분을 바로잡았다." },
    181: { after: "미인임다, 기가 세 보이는", category: "speaker_voice", reason: "니콜 특유의 말투로 통일했다." },
    184: { after: "라르크 씨의 말씀대로\n아주 쿨하다고 생각합니다만\n코핀에게는 힘들 것 같습니다", category: "speaker_voice", reason: "코핀의 정중한 화법을 세 행에 일관되게 적용했다." },
    190: { after: "……니콜 녀석\n제대로 해 나갈 수 있으면\n좋겠는데", category: "naturalness", reason: "조건과 바람이 자연스럽게 이어지도록 문장을 다듬었다." },
  },
  batch_0038: {
    2: { after: "짙은 녹음으로 뒤덮인 땅이었지?\n결정화는 진행되고 있었나?", category: "speaker_voice", reason: "과거 상태를 확인하는 질문과 격식 있는 화자의 말투를 복원했다." },
    5: { after: "난 아직 아쉽게도\n키가 모자라니까〜", category: "naturalness", reason: "키가 부족하다는 직역을 자연스러운 구어로 다듬었다." },
    10: { after: "그래, 난 이상해", category: "speaker_voice", reason: "알스의 부드러운 자기 서술을 거친 표현에서 바로잡았다." },
    15: { after: "아〜, 드디어 돌아갈 수 있슴다!\n돌아가면 우선 목욕부터 하고\n맛있는 거라도 먹고 싶슴다〜!", category: "speaker_voice", reason: "니콜의 독특한 말투를 세 행에 일관되게 적용했다." },
    17: { after: "괜찮아, 고마워.\n가자.\n아버님과 그분들을 위해서라도――", category: "meaning", reason: "お父様たち를 여러 아버지가 아니라 아버지와 일행을 가리키는 뜻으로 풀었다." },
    19: { after: "후후후〜.\n둘 다 피부가 매끈하네\n품에 안는 느낌이 최고야……", category: "naturalness", reason: "抱き心地를 부자연스러운 안는 맛 대신 포옹감으로 다듬었다." },
    25: { after: "자, 조종 교대하자고.\n비켜, 비켜――", category: "naturalness", reason: "操縦代わる의 교대 의미를 자연스럽게 표현했다." },
    26: { after: "이런, 곱게 자라면\n반응도 솔직하군……", category: "naturalness", reason: "育ちがいい와 그에 따른 순진한 반응을 자연스럽게 옮겼다." },
    30: { after: "하지만 신체 일부를\n저렇게 변모시키고 있다.\n부담이 가벼울 리 없지", category: "speaker_voice", reason: "격식 있는 화자의 서술 어조로 맞췄다." },
    31: { after: "으음ー? 이 계기판 느낌 같은 게\n자장가로 잠들기 전을 떠올리게 해.\n난 그때 아직 어렸지만", category: "naturalness", reason: "자장가로 잠들기 전의 과거 시점을 분명하게 했다." },
    36: { after: "네 의상도\n무척 깔끔한 느낌이라\n잘 어울려", category: "naturalness", reason: "부자연스러운 관형 표현을 자연스럽게 다듬었다." },
    39: { after: "젊었을 때도 몇 번 지나갔다.\n이 근처 풍경은……\n변해 버렸지만 말이지", category: "speaker_voice", reason: "오이겐의 절제된 서술 어조로 통일했다." },
    45: { after: "게다가 당시 갓 알게 된\n나도 참가를 강요당했다", category: "speaker_voice", reason: "격식 있는 화자의 과거 서술 어조를 맞췄다." },
    46: { after: "뭐, 나도 처음엔 라르크를 보며\n참 무례한 녀석이라고\n생각했지만 말이야", category: "grammar", reason: "목적어와 인용절의 관계를 자연스럽게 바로잡았다." },
    48: { after: "아하하.\n확실히 좀처럼 없는 일이긴 하지ー", category: "naturalness", reason: "滅多にない의 의미를 자연스러운 문장으로 완결했다." },
    50: { after: "아니면 너희처럼\n수단을 선택해\n결과를 이루려 해야 할까", category: "naturalness", reason: "結果を目指す를 부자연스러운 지향 표현 대신 결과를 이루려 한다는 뜻으로 다듬었다." },
    59: { after: "그런 의미에서는 마녀가 실재한다고도\n실재하지 않는다고도 할 수 있다", category: "speaker_voice", reason: "격식 있는 화자의 단정적 서술 어조로 맞췄다." },
    63: { after: "아직 찾아오지 않았다", category: "speaker_voice", reason: "오이겐의 질문 답변을 격식 있는 종결로 통일했다." },
    65: { after: "당연하긴 뭐가 당연해\n모르겠다니까", category: "naturalness", reason: "決まってるじゃん에 대한 반박을 자연스러운 한국어로 다듬었다." },
    67: { after: "뭐, 뭐. 괜찮잖아.\n귀여운 동생 같은 녀석이잖아?", category: "meaning", reason: "弟分를 친동생이 아니라 동생처럼 아끼는 후배라는 뜻으로 풀었다." },
    68: { after: "네가\n활기차게 말하지 마〜!", category: "speaker_voice", reason: "あんた의 친근한 타박을 자연스러운 반말로 바꿨다." },
    70: { after: "토파지온으로 가자.\n보급 같은 것도 마칠\n필요가 있으니까", category: "naturalness", reason: "済ませる를 보급 절차를 마친다는 뜻으로 자연스럽게 옮겼다." },
    71: { after: "하지만 말이야ー, 세실\n왠지 불안하단 말이지", category: "meaning", reason: "セシルちゃん을 문장 주어가 아니라 말을 거는 호칭으로 바로잡았다." },
    73: { after: "아니, 이 구조로는\n통로 너머에 길이 이어지는지\n막다른 곳인지 분간할 수 없다", category: "speaker_voice", reason: "격식 있는 화자의 종결 어조로 통일했다." },
    77: { after: "아이치고는\n장난이 짓궂지만", category: "meaning", reason: "質が悪い를 품질이 나쁘다가 아니라 장난이 짓궂다는 뜻으로 풀었다." },
    84: { after: "응. 무슨 일이야?", category: "speaker_voice", reason: "리피아의 부드러운 반말 어조로 다듬었다." },
    95: { after: "오늘 지지만 않으면\n자기들이 이겼다고 떠벌려\n공적을 세우는 데 이용하자고", category: "meaning", reason: "功名를 모호한 한자어 대신 공적과 명성을 세운다는 뜻으로 풀었다." },
    97: { after: "그럴 생각은 없다.\n마음에 들기는 하니까", category: "speaker_voice", reason: "격식 있는 화자의 종결 어조로 통일했다." },
    101: { after: "제게는 절친한 친구가 있었습니다.\n그는 말이 없는 존재였지만\n아주 편리한 녀석이었습니다――", category: "speaker_voice", reason: "코핀의 정중한 회상체를 세 행에 일관되게 적용했다." },
    106: { after: "그게 마녀인지 자연인지는\n모르겠습니다만", category: "speaker_voice", reason: "정중한 화자의 말투를 복원했다." },
    108: { after: "이, 이건 어떤 의미에서는 신선하네……", category: "naturalness", reason: "ある意味의 관용적 표현을 자연스럽게 옮겼다." },
    109: { after: "용사 세실의 정도가 그녀에게 말을\n되찾아 준 것이었다――\n……라고 해 봤어", category: "function", reason: "なんちゃって를 진술이 아니라 장난스러운 덧붙임으로 바로잡았다." },
    117: { after: "코핀은 못 합니다\n돌아가고 싶은 고향은 있는데도 말입니다", category: "speaker_voice", reason: "코핀의 정중한 말투로 문장을 완결했다." },
    126: { after: "돈만 있으면 이사의 아이로서의 사명도\n어떻게든 된다는 거지?", category: "grammar", reason: "연속된 관형격 조사를 피하고 사명의 주체를 명확히 했다." },
    134: { after: "아니, 아니군…… 옛날부터 변하지 않았다.\n뜻을 굽히지 않는 녀석이었지", category: "speaker_voice", reason: "절제된 남성 화자의 과거 서술 어조로 맞췄다." },
    136: { after: "저도 진짜로 가겠슴다\n형님!!", category: "speaker_voice", reason: "니콜의 의지 표현과 고유 말투를 자연스럽게 맞췄다." },
    138: { after: "……하아.\n고맙다고.\n정말, 넌 못 당하겠어", category: "speaker_voice", reason: "거친 반말 화자의 감사와 투덜거림을 자연스럽게 살렸다." },
    140: { after: "한순간의 열기에 자신을 잊고\n냉정을 잃어 판단을 그르치는 건\n말도 안 돼. 죄악이야", category: "meaning", reason: "我を失う와 判断を見誤る의 의미를 자연스러운 한국어로 풀었다." },
    144: { after: "아아ー, 여성 요소가 부족하네ー", category: "terminology", reason: "女性成分를 여성 인원이 아니라 여성적 요소라는 기존 표현으로 통일했다." },
    145: { after: "……그렇습니다", category: "speaker_voice", reason: "디노스의 정중한 말투를 복원했다." },
    146: { after: "뭐, 뭐야!\n라르크가 알 바 아니잖아!", category: "meaning", reason: "ラルクには関係ない를 라르크와 관련 없다는 뜻이 아니라 참견하지 말라는 뜻으로 바로잡았다." },
    148: { after: "그 녀석한테는 안 어울리지만\n뭐, 어쩔 수 없지", category: "particle", reason: "似合う 대상에 맞는 조사를 사용했다." },
    149: { after: "사람 얼굴을 보고 할 말을 잃지 마.\n할 말이 있으면 해", category: "naturalness", reason: "絶句するな를 자연스러운 한국어 표현으로 다듬었다." },
    155: { after: "응, 입안이 조금 베였을 뿐……", category: "meaning", reason: "口の中が切れた를 입안이 찢어졌다가 아니라 조금 베였다는 뜻으로 바로잡았다." },
    161: { after: "이 도시에서 살아야\n했던 사람들……\n여기서 뭘 했던 걸까", category: "line_breaks", reason: "원문의 세 행 구조를 복원했다." },
    166: { after: "그 집을 찾아가면 된다.\n아니, 다르군――귀환이군", category: "speaker_voice", reason: "오이겐의 격식 있는 자기 정정 어조로 맞췄다." },
    168: { after: "나와 세실은\n리피아, 네 어머니를\n만난 적이 있었을지도 모른다", category: "speaker_voice", reason: "오이겐의 격식 있는 추측 어조로 통일했다." },
    169: { after: "한때 저곳은\n바싹 마른 삭막한 협곡이었다", category: "speaker_voice", reason: "격식 있는 화자의 과거 서술 종결을 복원했다." },
    171: { after: "언니의 이 차림은?\n어, 때?", category: "naturalness", reason: "자기 차림을 묻는 능글맞은 말투와 끊어 말하기를 자연스럽게 살렸다." },
    184: { after: "정말 눈이\n소리를 내는 건 아닌데\n그렇게 들린달까", category: "line_breaks", reason: "원문의 세 행 구조를 복원했다." },
    186: { after: "형님, 뭔가 불만스러워 보임다", category: "speaker_voice", reason: "니콜 특유의 말투로 통일했다." },
    192: { after: "라르크, 지도 표시를 봐라.\n움직이는 표식이 나타나 있다", category: "speaker_voice", reason: "오이겐의 지시와 관찰을 격식 있는 어조로 맞췄다." },
    194: { after: "그 녀석은 걱정 없어.\n저래 보여도 용기 있는 아이야", category: "meaning", reason: "あれでもな의 외견과 실제 성격이 다른 양보 의미를 자연스럽게 복원했다." },
    195: { after: "미니멈 레이디.\n당신답지 않게\n어찌 되셨나요?", category: "naturalness", reason: "あなたとしたことが의 상대답지 않다는 뉘앙스와 정중한 질문을 살렸다." },
  },
  batch_0039: {
    3: { after: "부탁한 기억은 없는데", category: "grammar", reason: "목적어를 꾸미는 관형 표현에 필요한 조사를 보충했다." },
    9: { after: "알스는 늘 말뿐이야!\n디노스. 가요", category: "speaker_voice", reason: "디노스에게 건네는 정중한 권유 어조를 복원했다." },
    28: { after: "리피아에게는 특별한 힘이 있으니까.\n그래서 우리와 함께\n행동해 주고 있는 거야", category: "meaning", reason: "行動してもらっている를 부탁한 과거가 아니라 현재 동행 중이라는 뜻으로 바로잡았다." },
    45: { after: "어른은 아이를 돌봐야\n하는 법이니까.\n나로서도 어쩔 수 없다", category: "speaker_voice", reason: "오이겐의 격식 있는 종결 어조로 통일했다." },
    46: { after: "그러고 보니 그럴지도.\n헤벌쭉 웃고 있는\n느낌이 나", category: "meaning", reason: "だらしなく笑う의 흐트러진 웃는 인상을 자연스럽게 풀었다." },
    50: { after: "푸석푸석해서 종잇조각 같고\n입에 넣으면 질척질척해져서\n식감이 완전 끔찍해!", category: "naturalness", reason: "식감에 대한 강한 혐오를 자연스러운 한국어로 다듬었다." },
    52: { after: "리피아, 신경 쓰지 마.\n우리 엄마는 걱정 안 해도 돼.\n나보다 훨씬 강한 사람이거든?", category: "speaker_voice", reason: "라르크가 어머니를 부르는 친근하고 거친 말투를 반영했다." },
    57: { after: "세상은 언제나 시끄럽습니다\n제 주변도 늘 그렇고\n수상한 움직임을 보이고 있습니다", category: "meaning", reason: "騒がしい를 활기찬 뜻의 시끌벅적이 아니라 시끄럽다는 뜻으로 바로잡았다." },
    87: { after: "그러네.\n언젠가 그녀에게 돌아갈 날이\n오기를 빌게", category: "naturalness", reason: "願っておく의 바람을 부자연스러운 보조 표현 없이 다듬었다." },
    90: { after: "자무엘 할아버지도\n얼른 은퇴하면 좋겠어", category: "proper_noun", reason: "라르크가 자무엘을 부르는 호칭을 기존 표기인 할아버지로 통일했다." },
    96: { after: "신제국 헌장 아래의 디아만트다\n그것도 상층이라면\n침입하기 어려웠을 것이다", category: "speaker_voice", reason: "격식 있는 화자의 추론 종결로 통일했다." },
    108: { after: "괜찮잖슴까.\n오팔루스에 머무는 동안엔\n역시 이 교복임다", category: "speaker_voice", reason: "니콜의 고유 말투를 세 행에 일관되게 적용했다." },
    113: { after: "괜찮잖슴까, 형님.\n전 꽤 마음에 든단 말임다.\n이런 학원에는 가 본 적도 없고", category: "speaker_voice", reason: "니콜의 고유 말투를 세 행에 일관되게 적용했다." },
    119: { after: "……아……. 그러고 보니 그렇네.\n지금 그 사람은 내……\n적이었지", category: "speaker_voice", reason: "라르크의 거친 반말과 뒤늦게 깨닫는 어조를 자연스럽게 맞췄다." },
    127: { after: "앞으로의 일을\n생각하게 되었다", category: "speaker_voice", reason: "오이겐의 격식 있는 회상 종결로 맞췄다." },
    128: { after: "어?\n아니…… 그럴지도 몰라.\n난 화가 나 있어", category: "speaker_voice", reason: "라르크의 거친 반말을 고풍스러운 어조에서 바로잡았다." },
    139: { after: "산호가 자라려면 시간이 걸릴 텐데\n공중 회랑 주변의 성장세는\n엄청나군", category: "naturalness", reason: "산호의 発育ぶり를 생물의 성장세라는 자연스러운 표현으로 다듬었다." },
    155: { after: "형님께는 감사함다……", category: "speaker_voice", reason: "니콜의 말투로 간결하고 자연스럽게 다듬었다." },
    171: { after: "탁룡의 꼬리를 잘라 내고\n주의를 자기 쪽으로 돌려\n저를 구해 줬슴다〜", category: "speaker_voice", reason: "니콜의 고유 말투와 동작의 연계를 자연스럽게 맞췄다." },
    177: { after: "할아버지는\n아델한테는 무르다고.\n우리한테는 엄격하면서", category: "proper_noun", reason: "자무엘을 가리키는 호칭을 기존 인물 말투에 맞게 할아버지로 통일했다." },
    178: { after: "어딘가의 학교에 다니는\n학생이었다면, 친구가\n될 수 있었을까?", category: "naturalness", reason: "学園을 학원이 아니라 학교로 옮기고 가정문을 자연스럽게 연결했다." },
    180: { after: "끈질기게 들러붙는 선배였는데\n정말 살았슴다!!\n형님께는 은혜를 입었슴다……", category: "meaning", reason: "恩義がある를 은혜가 존재한다가 아니라 은혜를 입어 빚진 뜻으로 바로잡았다." },
    184: { after: "정말 눈이\n소리를 내는 건 아닌데\n그렇게 들린달까", category: "line_breaks", reason: "원문의 세 행 구조를 복원했다." },
    186: { after: "형님, 뭔가 불만스러워 보임다", category: "speaker_voice", reason: "니콜 특유의 말투로 통일했다." },
    196: { after: "니콜, 형님은 나보다 연상이고\n나보다는 형님이\n황제에 더 어울린다고 생각해", category: "grammar", reason: "비교 대상과 주어의 관계를 자연스럽게 바로잡았다." },
  },
};

function readJsonl(filePath) {
  return fs.readFileSync(filePath, "utf8").split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
}

function toPosix(filePath) {
  return filePath.split(path.sep).join("/");
}

function writeBatch(batchId, corrections) {
  const sourcePath = path.join(SOURCE_ROOT, `${batchId}.jsonl`);
  const draftPath = path.join(DRAFT_ROOT, `${batchId}.jsonl`);
  const reviewedPath = path.join(REVIEWED_ROOT, `${batchId}.jsonl`);
  const reviewPath = path.join(REVIEWS_ROOT, `${batchId}_review.json`);
  const sourceRows = readJsonl(sourcePath);
  const draftRows = readJsonl(draftPath);
  const draftById = new Map(draftRows.map((row) => [row.tm_id, row]));
  const modifications = [];

  sourceRows.forEach((row, zeroBasedIndex) => {
    const correction = corrections[zeroBasedIndex + 1];
    const before = draftById.get(row.tm_id).translation_ko;
    const after = correction ? correction.after : before;
    row.translation_ko = after;
    if (correction) {
      modifications.push({
        tm_id: row.tm_id,
        source_text: row.source_text,
        before,
        after,
        category: correction.category,
        reason: correction.reason,
      });
    }
  });

  fs.mkdirSync(REVIEWED_ROOT, { recursive: true });
  fs.mkdirSync(REVIEWS_ROOT, { recursive: true });
  fs.writeFileSync(reviewedPath, `${sourceRows.map((row) => JSON.stringify(row)).join("\n")}\n`, "utf8");

  const report = {
    schema: "arf-translation-independent-review-v1",
    batch_id: batchId,
    reviewer: "/root/audit_boundary_integration",
    draft_translator: "/root/translate_batch_0008",
    draft_author: "/root/translate_batch_0008",
    independent_review: true,
    translation_engine_policy: "Codex internal models only",
    external_translation_services_used: [],
    external_translation_models_or_apis_used: [],
    source: toPosix(sourcePath),
    draft: toPosix(draftPath),
    reviewed_output: toPosix(reviewedPath),
    reviewed_units: sourceRows.length,
    modified_units: modifications.length,
    unchanged_units: sourceRows.length - modifications.length,
    review_dimensions: [
      "meaning",
      "function",
      "numeric fidelity",
      "proper nouns",
      "natural Korean",
      "particles",
      "control tokens",
      "line breaks",
    ],
    modifications,
    verification_execution: {
      status: "deferred_by_user_instruction",
      executed_tools: [],
      not_executed: ["validator", "fit", "encoding", "boundary_audit"],
      note: "사용자 지시에 따라 별도 validator, fit, encoding, boundary audit를 실행하지 않았다.",
    },
  };
  fs.writeFileSync(reviewPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  return modifications.length;
}

for (const [batchId, corrections] of Object.entries(CORRECTIONS)) {
  process.stdout.write(`${batchId}: ${writeBatch(batchId, corrections)}\n`);
}
