import fs from "node:fs";
import path from "node:path";

const ROOT = path.join("work", "translation");
const SOURCE_ROOT = path.join(ROOT, "tm_v2", "batches", "source");
const DRAFT_ROOT = path.join(ROOT, "drafts");
const REVIEWED_ROOT = path.join(ROOT, "reviewed");
const REVIEWS_ROOT = path.join(ROOT, "reviews");

const CORRECTIONS = {
  batch_0052: {
    5: { after: "모든 걸 가졌던 건\n당신이잖아!", category: "meaning", reason: "持ってた의 과거 시점을 살려 두 사람의 처지를 대비했다." },
    9: { after: "지하에 로그레스가 있을…… 리는 없겠지.\n이럴 땐", category: "naturalness", reason: "말줄임 뒤의 부정과 이어지는 미완 문장을 자연스러운 한국어 호흡으로 다듬었다." },
    12: { after: "싫어라♪ 사쥬도 참♪\n농담은 얼굴 하나로 충분하거든", category: "meaning", reason: "冗談は顔だけにしておきなさい의 외모를 빗댄 농담을 한국어에서 통하는 표현으로 옮겼다." },
    15: { after: "……역시 이곳은 아이온대가\n정식으로 접수한 시설이 아닐지도 모르겠군", category: "meaning", reason: "接収를 단순 접수가 아니라 시설을 공식적으로 넘겨받아 관리한다는 뜻으로 바로잡았다." },
    17: { after: "이사의 아이인가……\n내 로고스를 얻으러 왔나", category: "meaning", reason: "求めに来た를 구출이 아니라 로고스를 얻으러 왔다는 뜻으로 명확히 했다." },
    29: { after: "으〜. 설마 이 높은 곳을\n계단으로 올라갈 생각이야?", category: "naturalness", reason: "높이를 계단으로 간다는 직역을 높은 곳까지 올라간다는 자연스러운 표현으로 다듬었다." },
    31: { after: "왠지 엄청나네♪\n아까 밖에서 본 느낌으로는\n구름 위까지 닿아 있는 거 아냐?", category: "meaning", reason: "雲の上まで届いてたりして를 구름 위까지 닿았을 가능성을 떠올리는 추측으로 복원했다." },
    37: { after: "자료를 살펴본 바로는\n이제 인간으로 되돌릴 수 없어", category: "naturalness", reason: "자료를 본 바로는이라는 어색한 결합을 자연스럽게 다듬었다." },
    43: { after: "변환 과정의 실수로\n보석이 몸체에 융합돼 버림\n……이라고 쓰여 있어", category: "naturalness", reason: "실험 기록을 읽어 주는 상황에 맞춰 ボディ와 인용 종결을 자연스럽게 표현했다." },
    47: { after: "라르크!?\n설마 너도 이 살육에\n가담했다는 건가!?", category: "speaker_voice", reason: "알스의 격앙된 추궁을 단정적인 반문 어조로 맞췄다." },
    49: { after: "후〜. 어떻게든\n따돌린 것 같슴다!", category: "speaker_voice", reason: "니콜의 고유한 ~슴다 계열 말투를 복원했다." },
    50: { after: "아이온대의 누군가가\n사리사욕을 위해 시설을 차지하라고\n지시한 게 아닐까 하는 말이다", category: "meaning", reason: "接収를 행정적 시설 장악이라는 문맥에 맞춰 번역하고 행위 주체를 자연스럽게 밝혔다." },
    52: { after: "아니면 겁먹은 자기 자신을\n다독이는 거냐?", category: "naturalness", reason: "자기 자신에게 타이른다는 직역을 스스로를 다독인다는 자연스러운 표현으로 다듬었다." },
    54: { after: "리피아, 너도 마찬가지야.\n아무리 세상 물정 모르고 자랐다 해도\n이렇게 밖에 나온 이상은――", category: "meaning", reason: "箱入り를 단순히 곱게 자랐다는 뜻이 아니라 세상과 격리되어 자랐다는 의미로 풀었다." },
    59: { after: "그렇군요…… 그때의 일격으로\n목숨은 빼앗지 못했지만\n당신의 왼팔은 빼앗았군요", category: "function", reason: "ましたか를 실제 질문이 아니라 결과를 확인하고 깨닫는 악역의 어조로 바로잡았다." },
    61: { after: "여기엔 분명\n파피르사그가 있지?", category: "function", reason: "상대에게 기억을 확인하는 のよね의 질문 기능을 복원했다." },
    68: { after: "……비광정 건은 마리아에게 한 보답이니\n다시 갚아 줘도 곤란하다만", category: "meaning", reason: "マリアの礼를 마리아가 준 답례가 아니라 마리아에게 한 보답이라는 뜻으로 바로잡았다." },
    69: { after: "말다툼할 때가 아니야!\n아무튼 우리가\n무슨 일이 벌어지는지 보고 올게", category: "meaning", reason: "言い争ってる場合か를 말다툼할 때가 아니라는 반문으로 복원했다." },
    71: { after: "혀…… 형니임……\n죄, 죄송함다……", category: "speaker_voice", reason: "겁먹어 더듬는 니콜의 발화와 고유한 ~슴다 말투를 함께 살렸다." },
    72: { after: "아마 오르키나 교국이\n관련된 듯합니다", category: "naturalness", reason: "관련되어 있다고 생각합니다라는 일본어식 추측 표현을 간결한 한국어로 다듬었다." },
    73: { after: "아쉽네.\n내 장기말은 더 늘릴 수 없겠어", category: "meaning", reason: "手駒를 소유격 대명사로 오해할 수 있는 말이 아니라 조종하는 장기말이라는 뜻으로 명확히 했다." },
    74: { after: "리피아.\n그렇게 진지하게 답하면\n맥 빠짐다……", category: "speaker_voice", reason: "マジレス의 기능과 니콜의 고유 말투를 자연스럽게 살렸다." },
    76: { after: "부친 살해는 대역죄.\n황태자라 해도\n죄를 면할 수 없습니다", category: "naturalness", reason: "공적인 단죄 장면에 맞게 父殺し를 간결하고 격식 있게 표현했다." },
    79: { after: "이 사람……\n바이스 전하를\n닮았어……", category: "grammar", reason: "모습과 닮았다는 어색한 비교 구조를 사람을 직접 목적어로 삼는 표현으로 바로잡았다." },
    84: { after: "방금 그 비명……\n프레이아 장군의 비명 아닐까", category: "meaning", reason: "사람 자체가 아니라 들린 비명의 주인을 추측하는 문장임을 분명히 했다." },
    86: { after: "곤란하군요. 호제아에게\n이매지널 디바와 이사의 아이를\n지키라는 명령을 받았습니다", category: "terminology", reason: "고정 직위명 イマジナル・ディーバ를 이매지널 디바로 통일했다." },
    89: { after: "나는 그분을\n따르는 것밖에 할 수 없다.\n라군 상사. 알스 님을 부탁한다", category: "proper_noun", reason: "인물 이름과 존칭을 기존 표기에 맞춰 띄어 썼다." },
    92: { after: "그러네. 대폭발을 일으키는 적과\n지하에 있다니\n역시 생각만 해도 끔찍하잖아", category: "naturalness", reason: "ぞっとしない를 단순히 오싹한 감각이 아니라 생각하기도 싫은 위험한 상황으로 자연스럽게 표현했다." },
    97: { after: "어머, 장기말이라면 저기 와 있네", category: "meaning", reason: "手駒를 말이라는 중의적 표현 대신 조종하는 장기말로 명확히 했다." },
    98: { after: "……파피르사그는 우리가 차지하겠어", category: "naturalness", reason: "로그레스를 소유하겠다는 위협을 차지하겠다는 자연스러운 표현으로 다듬었다." },
    99: { after: "아, 형님!?\n왜 살아 있는 검까!?", category: "speaker_voice", reason: "あ를 잘못 옮긴 음절을 바로잡고 니콜의 놀란 ~슴까 계열 말투를 살렸다." },
    100: { after: "형님.\n아버님을 직접 죽이셨다는\n소문은 사실입니까", category: "meaning", reason: "手にかける를 막연히 해친 것이 아니라 직접 살해했다는 뜻으로 정확히 옮겼다." },
    109: { after: "너, 그래도 용병이잖아.\n이 녀석이 사람이든 뭐든\n적이면 쓰러뜨려. 안 그러면 죽는다", category: "meaning", reason: "でなけりゃ死ぬぞ를 죽으라는 명령이 아니라 그렇게 하지 않으면 죽는다는 경고로 바로잡았다." },
    110: { after: "그…… 그렇지.\n저 탁룡도 원래는 인간이었을지\n모르니까", category: "meaning", reason: "元は人間를 현재 인간일 가능성이 아니라 과거에 인간이었을 가능성으로 바로잡았다." },
    126: { after: "말씀드렸지요?\n저는 여러분을\n지켜야 합니다", category: "speaker_voice", reason: "정중하게 상대를 압박하는 화자의 말투에 맞춰 첫 문장을 다듬었다." },
    135: { after: "어머, 좋은 다이어트가 되겠네.\n사실 올라갈 때보다 내려갈 때가\n더 좋긴 하지만", category: "grammar", reason: "문장 끝의 양보 표현을 한국어에서 자연스럽게 완결했다." },
    140: { after: "응급 수리지만, 이걸로 엘리베이터가\n움직이게 됐을 거다", category: "meaning", reason: "はずだ의 판단을 단순 미래가 아니라 수리 결과에 대한 확신으로 살렸다." },
    144: { after: "실례지만, 이 회담에\n용병이 나설 자리는 없을 듯합니다만", category: "naturalness", reason: "없다고 생각합니다만이라는 직역투를 격식 있는 완곡 표현으로 다듬었다." },
    147: { after: "……뭔, 뭔가 나올 것 같네요.\n돌아가고 싶슴다", category: "speaker_voice", reason: "둘째 문장의 갑작스러운 반말을 니콜의 고유 말투로 바로잡았다." },
    163: { after: "치유의 비나 죽음의 비를……\n우리에게……", category: "meaning", reason: "癒シノ雨カ死ノ雨ヲ의 선택 관계를 자연스러운 한국어 조사로 표현했다." },
    175: { after: "죄도 없는\n그것도 여성을 습격하다니\n비열한 놈!", category: "naturalness", reason: "비난 대사의 마지막 명사구를 감정 강도에 맞는 완결된 호통으로 다듬었다." },
    177: { after: "이게 리얼 디바였다면\n일석이조였을 텐데요", category: "terminology", reason: "고정 직위명 リアル・ディーバ를 리얼 디바로 통일했다." },
    184: { after: "내가 더글러스 경의 처형이라는 걸 알고\n엔주의 목숨을 살리고 싶으면\n이걸 가져오라고 협박했어", category: "meaning", reason: "義理の姉를 더글러스 경의 아내인 엔주의 언니라는 관계에 맞춰 처형으로 바로잡았다." },
    186: { after: "……바네투도 기뻐하겠지……인가", category: "naturalness", reason: "앞서 들은 말을 되뇌며 의미를 짚는 독백으로 자연스럽게 다듬었다." },
    196: { after: "아무것도 모르는 외부인은 빠져 있어!", category: "naturalness", reason: "外野를 딱딱한 제삼자 대신 논쟁 밖의 외부인이라는 뜻으로 자연스럽게 옮겼다." },
    198: { after: "바네투도 기뻐하겠지……라는 말입니까.\n알스 님. 이건 바네투와의\n계약에 영향을 주는 것 아닙니까?", category: "function", reason: "앞선 문구를 인용해 계약 조건을 추론하는 질문임을 분명히 하고 존칭 표기를 통일했다." },
    199: { after: "지금 제국군이 위기에 처해 있다", category: "naturalness", reason: "위험한 상태라는 직역을 군이 위기에 놓였다는 자연스러운 표현으로 다듬었다." },
  },
  batch_0053: {
    5: { after: "……어…… 응.\n내 코드로 엘자 씨의 코드가\n침식해 들어온 것 같아……", category: "grammar", reason: "침식의 방향과 진행 상황이 자연스럽게 드러나도록 조사와 서술어를 바로잡았다." },
    10: { after: "열 수만 있다면, 이라고 했지.\n내용은 아직 확인하지 못했나", category: "meaning", reason: "開ければ의 조건과 아직 열어 보지 못한 상태를 정확히 복원했다." },
    12: { after: "２명 모두 위험해!", category: "naturalness", reason: "숫자를 보존하면서 ２人とも를 자연스러운 한국어로 표현했다." },
    13: { after: "１０００년이라고 했지.\n그럼 여기는 음의 시대의 도시\n……라는 걸까?", category: "particle", reason: "시대와 도시 사이의 소유·귀속 관계를 나타내는 조사를 보충했다." },
    24: { after: "야, 심마프 씨. 지금 여기로\n정신 나간 망자술사가 쳐들어오고 있어", category: "speaker_voice", reason: "さん의 빈정대는 호칭을 살리고 頭のおかしな를 자연스러운 구어로 다듬었다." },
    25: { after: "……흥이다.\n리피아가 귀엽다고 편애나 하고", category: "naturalness", reason: "투덜대는 미완 문장을 한국어의 보조사로 자연스럽게 살렸다." },
    26: { after: "아, 형님! 무슨 일임까?", category: "speaker_voice", reason: "あ를 잘못 옮긴 음절을 바로잡고 니콜의 고유 말투를 살렸다." },
    39: { after: "사쥬. 궁금한 게 있는데요,\n어떻게 이 반룡이\n미인인 줄 알았슴까?", category: "speaker_voice", reason: "素朴な質問을 자연스러운 질문 도입으로 바꾸고 니콜의 말투를 복원했다." },
    41: { after: "알스 님, 이대로는\n시간에 맞추지 못합니다", category: "proper_noun", reason: "존칭을 띄어 쓰고 間に合わない를 제시간에 도달하지 못한다는 뜻으로 정확히 옮겼다." },
    42: { after: "심마프.\n나는 이매지널 디바", category: "terminology", reason: "고정 직위명 イマジナル・ディーバ를 이매지널 디바로 통일했다." },
    43: { after: "유적은 당연히\n망한 곳이잖아", category: "naturalness", reason: "멸망해 있다는 어색한 상태 표현을 유적의 성격을 지적하는 농담으로 자연스럽게 다듬었다." },
    45: { after: "원로원은 공화국 귀류법에 따라\n권력을 보장받는 대신\n성황의 교시로 정치를 한다", category: "meaning", reason: "宣下를 형벌 선고가 아니라 성황이 내리는 정치적 교시라는 뜻으로 바로잡았다." },
    46: { after: "오…… 역시 디바.\n가소술 솜씨는 얕볼 수 없네.\n하지만――", category: "meaning", reason: "歌召術を使わせたら를 남에게 사용시키는 사역이 아니라 디바의 가소술 솜씨를 평가하는 말로 바로잡았다." },
    47: { after: "저는 원로원 의장의 대리인으로\n임명받은\n레슬리 플래허티라고 합니다", category: "naturalness", reason: "拝命致しました의 격식을 유지하면서 명받은이라는 어색한 직역을 다듬었다." },
    48: { after: "좋아. 어서 미인인 어머니와\n만나게 해 주자고", category: "naturalness", reason: "상대의 어머니를 가리키는 호칭을 한국어에서 자연스럽게 다듬었다." },
    54: { after: "세상 물정 모르는 디바와\n무슨 상관이야", category: "particle", reason: "関係ある의 대상을 나타내도록 주격 조사를 공동격 조사로 바로잡았다." },
    59: { after: "그나저나\n아버지가 죽었는데도\n전혀 상심한 기색이 없네", category: "meaning", reason: "堪えてない를 물리적 타격이 아니라 부친상에 상심한 기색이 없다는 뜻으로 바로잡았다." },
    77: { after: "당신을 만나면 제가 완수해야 할\n사명의 길을 알려 주신다고……", category: "naturalness", reason: "使命の道筋를 사명을 완수할 길이라는 자연스러운 한국어로 다듬었다." },
    82: { after: "뭐야, 영문 모를 소리만\n계속 해대고!\n이젠 정말 화가 난다고!", category: "speaker_voice", reason: "いい加減頭に来た의 누적된 분노를 강한 구어체로 복원했다." },
    84: { after: "이사의 아이를 올바른 방향으로 이끄는 것이\n이매지널 디바인 나의 사명", category: "terminology", reason: "고정 직위명 イマジナル・ディーバ를 이매지널 디바로 통일했다." },
    103: { after: "음의 시대 거라고?\n그럼 아주 오래된 유적이구나.\n있잖아, 라르크……", category: "naturalness", reason: "の가 대신하는 명사를 보충해 첫 문장을 자연스럽게 완결했다." },
    106: { after: "먼저 공격한 건 그쪽이잖아?", category: "meaning", reason: "手を出す를 중의적인 손을 대다가 아니라 먼저 공격했다는 뜻으로 명확히 했다." },
    107: { after: "쳇, 끝까지\n성가신 로그레스야!", category: "speaker_voice", reason: "라르크의 거친 반말 어조에 맞춰 문장 종결을 다듬었다." },
    109: { after: "적어도 그때까지\n니콜이 지원을 불러와 주면……", category: "naturalness", reason: "助けを呼ぶ를 도움 자체를 부른다는 직역 대신 지원을 불러온다는 뜻으로 다듬었다." },
    112: { after: "！ 무슨 말이야?\n어쩌다 그렇게 된 거야……", category: "meaning", reason: "どうしてそんなことに를 막연한 왜 그렇게가 아니라 사태의 경위를 묻는 말로 복원했다." },
    114: { after: "……나 １명만으로도 괜찮아.\n내 코드로 엘자 씨의 코드가\n침식해 들어온 것 같아……", category: "meaning", reason: "１人で大丈夫를 한 명이면 충분하다는 일반론이 아니라 화자 혼자서 괜찮다는 뜻으로 바로잡았다." },
    115: { after: "당신 힘으로 어떻게 좀 안 돼!?", category: "naturalness", reason: "상대의 힘으로 해결할 수 없는지 다급히 묻는 반문을 자연스럽게 다듬었다." },
    126: { after: "아니에요. 그보다\n공화국에 돌아가신 뒤에도 건강히 지내세요", category: "naturalness", reason: "돌아가셔도 건강하라는 어색한 양보 표현을 귀환 뒤의 안부 인사로 다듬었다." },
    127: { after: "이제야\n마음의 짐을 덜었구나", category: "naturalness", reason: "肩の荷が降りる의 관용적 의미를 자연스러운 한국어 관용 표현으로 옮겼다." },
    129: { after: "노스 노와레교는\n휴전 제안을 알지 못합니다.\n원로원 안에서만 결정한 일입니다", category: "naturalness", reason: "제안을 모른다는 어색한 목적어·서술어 결합을 바로잡았다." },
    138: { after: "젠장!\n이렇게 된 이상 디스크만이라도……", category: "speaker_voice", reason: "도주 직전의 분노를 나타내는 おのれ를 자연스러운 감탄사로 옮겼다." },
    141: { after: "그 정도 공격으로\n이겼다고 생각한 거야?\n난 그냥 놀아 준 것뿐인데", category: "meaning", reason: "こっちは가 가리키는 단일 화자를 복수 주어가 아니라 나로 바로잡았다." },
    142: { after: "힘으로라도 바이스 님이 계신 곳까지\n가라는 거군", category: "proper_noun", reason: "존칭 표기를 통일하고 元にたどりつく를 사람이 있는 곳에 도착한다는 뜻으로 자연스럽게 옮겼다." },
    143: { after: "하지만 지금 바이스 님을 설득하면\n제국은 황제 폐하의 붕어를 이유로\n휴전할 수도 있을 거야", category: "proper_noun", reason: "인물 이름과 존칭을 기존 표기에 맞춰 띄어 썼다." },
    148: { after: "노스 노와레교에도\n이매지널신에게도 개입은 허락하지 않겠습니다", category: "grammar", reason: "교도라는 중의성을 피하고 두 개입 주체에 알맞은 조사를 사용했다." },
    149: { after: "오팔루스를 구해 주신\n알스 전하와 함께 행동하고\n있었던 것 아니니?", category: "naturalness", reason: "지속 동작을 묻는 문장을 한국어의 자연스러운 회상형 반문으로 다듬었다." },
    150: { after: "이사의 아이 라르크.\n용케 힐베르트의 백성을\n삶과 죽음의 경계에서 해방해 주었구나", category: "speaker_voice", reason: "よくぞ의 칭찬과 신적 존재의 장중한 어조를 자연스럽게 살렸다." },
    153: { after: "목숨을 위협받을 우려가 있던\n아델을 남몰래 지키기 위해", category: "naturalness", reason: "노림당한다는 직역을 피하고 影から의 은밀한 보호라는 의미를 살렸다." },
    155: { after: "라이언?\n아까 들린 탁룡의 목소리 주인인가?", category: "grammar", reason: "소유 관계가 겹친 어색한 명사구를 자연스럽게 정리했다." },
    156: { after: "감히 방해하다니……", category: "speaker_voice", reason: "분노 섞인 원망을 미완의 서술보다 자연스러운 감탄형으로 다듬었다." },
    158: { after: "……읏…… 그렇군.\n엔주 님, 무례를 사과합니다.\n병사들을 시켜 댁까지 모셔다드리죠", category: "honorific", reason: "여성 민간인에게 어색한 공 호칭을 님으로 바꾸고 호송 제안을 자연스럽게 다듬었다." },
    163: { after: "역시 로그레스를\n손에 넣으려는 거구나", category: "particle", reason: "손에 넣는 대상인 로그레스에 목적격 조사를 사용했다." },
    164: { after: "……바네투도 기뻐하겠지…… 그렇지?\n알스. 이게 바네투와의\n계약에 영향을 주지 않을까?", category: "naturalness", reason: "그렇지라는 확인과 계약에 미칠 가능성을 묻는 문장을 자연스럽게 다듬었다." },
    176: { after: "엄마. 들은 대로야.\n앞으로의 생활은 걱정하지 마", category: "particle", reason: "앞으로 이어질 생활을 나타내는 관형격 조사를 보충했다." },
    183: { after: "그렇다면 그분을 도와다오.\n부탁한다", category: "speaker_voice", reason: "격식을 갖춘 군인의 간청에 맞춰 도와줘라는 가벼운 어조를 다듬었다." },
    184: { after: "자, 코드 디스크를\n내놓으시죠", category: "function", reason: "いただきましょうか를 허락을 구하는 요청이 아니라 위협적으로 물건을 내놓으라는 말로 복원했다." },
    187: { after: "정의라니 기가 막히는군,\n사신 라군", category: "meaning", reason: "正義が聞いて呆れる의 관용적 조롱을 정의가 어이없다는 직역 대신 자연스럽게 옮겼다." },
    190: { after: "그런 거 아닐까.\n학교 지리 시간에\n힐베르트라는 도시를 배웠는걸", category: "naturalness", reason: "도시 이름을 배웠다는 뜻이 분명하도록 고유명사와 보통명사의 관계를 다듬었다." },
    192: { after: "세실은 왜 저럴까……", category: "function", reason: "직전 행동을 보고 세실의 태도를 의아해하는 독백으로 자연스럽게 옮겼다." },
    196: { after: "한발 먼저…… 저세상에서 임무 완수의\n축배를 들고 있다고…… 말이다……", category: "naturalness", reason: "任務完了를 임무 완수라는 자연스러운 명사구로 다듬었다." },
    199: { after: "성황의 교시로 정치를 좌우하는 건\n잘못이라 하시며, ＱＥＤ의\n해산을 요구하려 하셨어", category: "meaning", reason: "宣下를 형벌 선고가 아니라 성황의 정치적 교시라는 뜻으로 바로잡고 화자의 회상 어조를 살렸다." },
  },
  batch_0054: {
    2: { after: "의료비 면제 외에\n매달 １０만 리코를 지원금으로\n지급하게 된다", category: "naturalness", reason: "지원금에 불필요하게 붙은 관형격 조사를 자연스러운 보어 구조로 다듬었다." },
    5: { after: "싸우겠다면\n때려눕혀 주겠어!", category: "meaning", reason: "やる를 막연히 무언가를 한다는 뜻이 아니라 싸우겠다는 도전으로 명확히 했다." },
    19: { after: "……아, 고마워. 하지만 괜찮아.\n내 코드로 엘자 씨의 코드가\n침식해 들어온 것 같아……", category: "grammar", reason: "침식의 방향과 진행 상황이 자연스럽게 드러나도록 조사와 서술어를 바로잡았다." },
    21: { after: "크윽, 리피아까지 ３명이면\n조금 벅찬가……!", category: "naturalness", reason: "파티 인원을 세는 상황에서 넣어도라는 기계적인 표현을 자연스럽게 다듬었다." },
    32: { after: "다행이야.\n고통받는 사람을 구할 수 있어서……", category: "meaning", reason: "구조에 성공해 다행이라는 가능·성취의 의미를 복원했다." },
    35: { after: "하지만 황제 폐하께서 살아 계시다면\n사절과의 알현 정도는\n허락하실 것이다", category: "meaning", reason: "使者를 사자라는 중의적 한자어 대신 외교 사절로 명확히 했다." },
    44: { after: "라르크…… 서둘러라.\n다음 로그레스는 반드시 네 손에 넣어라.\n그러면 섭리는 세계에 퍼질 것이다", category: "naturalness", reason: "次なるログレスこそ의 강조를 자연스러운 명령문으로 다듬었다." },
    56: { after: "알았다. 이 은혜는 잊지 않겠다", category: "meaning", reason: "恩に着る를 앞으로 신세를 지겠다는 뜻이 아니라 받은 은혜를 기억하겠다는 뜻으로 바로잡았다." },
    63: { after: "감사해 주셔야겠군요,\n레이디", category: "speaker_voice", reason: "상대를 비꼬며 감사를 요구하는 정중한 화자의 어조로 다듬었다." },
    64: { after: "이야기는 밖으로 나간 뒤에\n마저 하는 게 좋지 않을까?", category: "naturalness", reason: "이야기의 나머지라는 직역을 대화를 이어 한다는 자연스러운 표현으로 다듬었다." },
    66: { after: "라르크의 말이 기뻤어.\n다들 날 상처라도 건드리듯 조심했는데,\n라르크는 달랐어", category: "meaning", reason: "腫れ物に触るように를 상대를 지나치게 조심스럽게 대하는 관용적 의미로 자연스럽게 풀었다." },
    67: { after: "죽으면 어쩌려고!\n돌아가신 네 어머니도\n슬퍼할 거잖아!", category: "meaning", reason: "앞으로 죽는다면 어머니가 슬퍼할 것이라는 가정의 시제를 바로잡았다." },
    70: { after: "――리피아, 따라와!", category: "function", reason: "来い를 그 자리에 오라는 말이 아니라 화자를 따라오라는 다급한 명령으로 옮겼다." },
    75: { after: "음의 시대 거라고?\n그럼 꽤 오래된 유적이군", category: "naturalness", reason: "の가 대신하는 명사를 보충해 질문을 자연스럽게 완결했다." },
    77: { after: "당시 오르키나교의 디바는\n이그나츠라는 남자에게\n목숨을 위협받고 있었다", category: "naturalness", reason: "노림당한다는 직역을 자연스러운 피동 표현으로 다듬었다." },
    79: { after: "……라르크는\n무섭지만 다정하네", category: "speaker_voice", reason: "인물의 부드러운 반말에 맞춰 상냥하구나라는 직역투를 다듬었다." },
    84: { after: "라르크.\n세실도 함께\n데려가 주자", category: "naturalness", reason: "줄 끝에서 용언이 어색하게 갈라지지 않도록 의미 단위에 맞춰 다듬었다." },
    103: { after: "드디어 찾았어.\n이매지널 디바", category: "terminology", reason: "고정 직위명 イマジナル・ディーバ를 이매지널 디바로 통일했다." },
    111: { after: "알스 님을 지지하는 파벌이\n공화국과 결탁해 제국을\n내부에서 분열시키려 한다", category: "proper_noun", reason: "인물 이름과 존칭을 기존 표기에 맞춰 띄어 썼다." },
    119: { after: "리피아.\n사춘기 청소년에게\n그런 말은 너무하잖아", category: "meaning", reason: "年頃の青少年를 한창때의 청년이라는 모호한 말 대신 사춘기 또래라는 뜻으로 명확히 했다." },
    129: { after: "좋아. ２명 모두 가자", category: "naturalness", reason: "숫자를 보존하면서 ２人とも를 자연스러운 한국어로 표현했다." },
    137: { after: "성황 호제아 님으로부터 더글러스 경 부인\n엔주를 석방하라는\n명령서가 도착했습니다!", category: "particle", reason: "명령서를 보낸 주체인 호제아에 출발점을 나타내는 조사와 올바른 존칭 띄어쓰기를 적용했다." },
    140: { after: "디바는 딸이 휘말리지 않도록\n우리 로드 나이트에게\n딸의 호위를 부탁했다", category: "naturalness", reason: "말려들게 하지 않는다는 직역을 위험에 휘말리지 않게 한다는 자연스러운 표현으로 다듬었다." },
    144: { after: "나는 이 코드 디스크를\n받았기 때문에 ＱＥＤ의\n표적이 됐어", category: "naturalness", reason: "노림당하게 되었다는 직역을 표적이 되었다는 자연스러운 표현으로 다듬었다." },
    148: { after: "노스 노와레교 일이라면\n저와도 관련이 있을 겁니다", category: "grammar", reason: "저에게도 관계가 있다는 어색한 조사 결합을 바로잡았다." },
    154: { after: "라르크…… 괜찮겠어?\n저 어린아이 １명을 혼자 보내도……", category: "meaning", reason: "１人で를 아이 한 명만 있다는 뜻이 아니라 어린아이를 혼자 보내는 상황으로 바로잡았다." },
    156: { after: "왜, 왜? 무슨 말이야?", category: "function", reason: "설명을 듣고 뜻을 되묻는 どういうこと를 무슨 일인지 묻는 말과 구분했다." },
    160: { after: "겉으로는 원로원이\n주관하는 것처럼\n보이지만 말이다", category: "naturalness", reason: "정치를 운영하는 取り仕切る를 군사적 통솔이 아니라 주관한다는 뜻으로 다듬었다." },
    169: { after: "엄마……\n무슨 말이야……", category: "function", reason: "어머니의 설명을 듣고 의미를 되묻는 どういうこと를 무슨 일이냐는 질문과 구분했다." },
    172: { after: "쳇! 벌써 문을 뚫었나!", category: "naturalness", reason: "문을 돌파한다는 직역을 방어를 뚫었다는 자연스러운 전투 표현으로 다듬었다." },
    179: { after: "상관없거든. 세실은\n１명이서라도 자무엘 할아버지의 원수를\n갚고 말 거야!", category: "speaker_voice", reason: "숫자를 보존하면서 혼자서라도 복수하겠다는 세실의 허세와 결의를 살렸다." },
    180: { after: "엄마와 헤어진 채\n호존 때문에 이렇게\n되어 버린 거구나……", category: "meaning", reason: "뒤에서 아이의 어머니를 찾는 문맥에 맞춰 親를 엄마로 구체화했다." },
    185: { after: "……뭐, 됐어.\n이번 사건을\n설명해 주지 않겠어?", category: "naturalness", reason: "설명을 요구하는 정중한 반문을 한국어에서 자연스럽게 다듬었다." },
    200: { after: "……이그나츠가 보낸 사람이 왔어", category: "meaning", reason: "使い를 사자라는 중의적 한자어 대신 이그나츠가 보낸 사람으로 명확히 했다." },
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
