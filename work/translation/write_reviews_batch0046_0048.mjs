import fs from "node:fs";
import path from "node:path";

const ROOT = path.join("work", "translation");
const SOURCE_ROOT = path.join(ROOT, "tm_v2", "batches", "source");
const DRAFT_ROOT = path.join(ROOT, "drafts");
const REVIEWED_ROOT = path.join(ROOT, "reviewed");
const REVIEWS_ROOT = path.join(ROOT, "reviews");

const CORRECTIONS = {
  batch_0046: {
    3: { after: "당연하지.\n여자라는 이유만으로 모두 아름다운 거야", category: "naturalness", reason: "여성이라는 사실 자체를 찬미하는 문장을 자연스러운 한국어로 다듬었다." },
    5: { after: "……아델이 왔었지", category: "speaker_voice", reason: "라르크의 거친 반말 회상 어조로 맞췄다." },
    11: { after: "코어를 대신할 존재가 필요해", category: "naturalness", reason: "코어의 역할을 맡을 대상을 자연스러운 명사로 표현했다." },
    12: { after: "큰일이야! 적의 습격을 받고 있어!", category: "naturalness", reason: "습격당하는 상황을 자연스러운 한국어 피동 표현으로 다듬었다." },
    16: { after: "……알스. 제국을 부탁한다.\n거기엔 우리 엄마가 살고 있어", category: "speaker_voice", reason: "라르크가 어머니를 부르는 친근하고 거친 말투를 반영했다." },
    19: { after: "소용없습니다. 이곳은 제 영역입니다", category: "speaker_voice", reason: "정중한 화자의 단정적인 두 문장을 완결했다." },
    24: { after: "――알았어.\n훗날 내가 남긴 성과를 지켜봐 줘", category: "naturalness", reason: "미래에서라는 직역을 훗날 성과를 확인한다는 자연스러운 표현으로 다듬었다." },
    27: { after: "그런 거야.\n그러니 모두와는 여기서 작별이야", category: "speaker_voice", reason: "라르크의 반말 어조로 두 행의 종결을 통일했다." },
    31: { after: "사람들이 인간의 힘만으로 살아가려 한 결과\n전란과 파괴에 절망했기 때문입니다", category: "naturalness", reason: "人が人だけで의 뜻을 신에게 의존하지 않고 인간만의 힘으로 산다는 의미로 풀었다." },
    39: { after: "미안해, 리피아", category: "speaker_voice", reason: "감정적인 이별 장면의 라르크 반말 어조로 맞췄다." },
    42: { after: "그리고 미인 용사로 자란\n모습을 보여 줄 거니까", category: "function", reason: "앞선 결심의 이유로 이어지는 から의 문장 기능을 복원했다." },
    50: { after: "그래.\n어서 다른 사람들과 합류하자", category: "naturalness", reason: "다른 모두라는 어색한 표현을 일행을 가리키는 자연스러운 말로 다듬었다." },
    53: { after: "시끄러워, 바이올런스 레이디", category: "terminology", reason: "사쥬가 붙인 고정 별명을 기존 표기인 바이올런스 레이디로 통일했다." },
    68: { after: "한 번은 제게 졌는데도요?", category: "naturalness", reason: "정중한 반문 어조를 중복 표현 없이 자연스럽게 다듬었다." },
    70: { after: "내 존재는 역사 속에\n묻혀 버릴 거야", category: "meaning", reason: "俺のこと를 자신의 이야기가 아니라 인물 자신이 역사에 묻힌다는 뜻으로 바로잡았다." },
    75: { after: "라르크! 위험해! 뒤를 봐!", category: "function", reason: "등 뒤의 위협을 즉시 경고하는 자연스러운 명령으로 다듬었다." },
    80: { after: "나…… 나는 이제 잠들게 돼", category: "speaker_voice", reason: "감정에 막혀 자신을 반복하는 어린 화자의 말더듬을 복원했다." },
    82: { after: "그렇습니다.\n저는 더는 이해할 수 없었습니다", category: "naturalness", reason: "알 수 없게 되었다는 직역을 판단을 이해하지 못하게 된 뜻으로 자연스럽게 다듬었다." },
    86: { after: "왜 그래?\n갑자기 그렇게 새삼스럽게 굴고", category: "meaning", reason: "改まる를 표정만 정색한 것이 아니라 갑자기 격식을 차리는 태도라는 뜻으로 옮겼다." },
    90: { after: "사쥬가 없네", category: "particle", reason: "사쥬를 부르는 호칭이 아니라 부재한 주어임을 나타내는 조사를 보충했다." },
    102: { after: "메리디아 왕이란\n우리나라의 초대 황제를 말하는 것이군요", category: "proper_noun", reason: "인명과 직위를 구분해 메리디아 왕으로 띄어 썼다." },
    109: { after: "그렇다면 난 공화국을 반드시 바꾸겠어.\n셰리와 함께 말이야", category: "meaning", reason: "変えてみせる의 강한 결의를 반드시 바꾸겠다는 표현으로 살렸다." },
    110: { after: "아, 시끄러우니까\n그것도 괜찮을지도 몰라", category: "grammar", reason: "가능성을 나타내는 문장의 서술어를 자연스럽게 완결했다." },
    111: { after: "표식이라니, 로그레스의 표식 말이야?", category: "naturalness", reason: "생략된 대상을 보충해 어떤 표식을 묻는지 자연스럽게 밝혔다." },
    117: { after: "라르크. 갑시다.\n사람의 미래를 사람의 손으로 되찾기 위해", category: "particle", reason: "미래를 되찾는 주체의 수단을 나타내는 조사로 바로잡았다." },
    127: { after: "……저는 저 자신이면서 이사이기도 합니다.\n성지 노와레 중심에서 잠든 코어의 반쪽입니다", category: "naturalness", reason: "저는 저라는 직역을 자기 정체성을 밝히는 자연스러운 표현으로 다듬었다." },
    131: { after: "당신 안에 살아 숨 쉬는 제 인자가\n그렇게 느끼게 했겠지요", category: "meaning", reason: "인자가 만남의 예감을 느끼게 했다는 인과 관계를 분명히 했다." },
    142: { after: "그건 아닙니다.\n여러분이 바라는 미래에는 신이 있어서는 안 됩니다", category: "naturalness", reason: "지향한다는 딱딱한 직역을 미래를 바란다는 자연스러운 표현으로 다듬었다." },
    146: { after: "그렇다면 우리도 온 힘을 다할게.\n이번엔 지지 않을 테니까", category: "meaning", reason: "本気で行く를 실제로 간다는 뜻이 아니라 전력을 다해 맞선다는 뜻으로 바로잡았다." },
    148: { after: "메리디아의 인자?\n무슨 소리를 하는 거야, 이 녀석은……", category: "naturalness", reason: "소리를 꺼낸다는 직역을 자연스러운 반문으로 다듬었다." },
    150: { after: "역시.\n다시 만날 것 같은 예감이 들었어", category: "naturalness", reason: "그랬군이라는 불필요한 추론을 덜고 재회 예감을 자연스럽게 표현했다." },
    155: { after: "그저 수십 년이나 수백 년 잠들 뿐이야.\n잠든 신종과 마찬가지야", category: "meaning", reason: "眠れる神種를 잠들 수 있는 종족이 아니라 잠들어 있는 신종이라는 뜻으로 바로잡았다." },
    165: { after: "한 편의 모험 소설을\n읽는 기분이네", category: "meaning", reason: "ちょっとした를 작은 크기가 아니라 제법 그럴듯한 한 편이라는 뜻으로 자연스럽게 옮겼다." },
    188: { after: "당신은 메리디아의 인자를\n물려받지 않았는데도", category: "meaning", reason: "因子を継ぐ를 이어 간다가 아니라 혈통의 인자를 물려받는다는 뜻으로 바로잡았다." },
    192: { after: "메리디아의 인자에서 본\n세 번째 섭리가 이것이라면……", category: "particle", reason: "인자를 생물처럼 취급한 조사 대신 판단의 근거 장소를 나타내는 조사를 사용했다." },
    198: { after: "악운 하나는 질기니까", category: "naturalness", reason: "悪運が強い의 좀처럼 죽지 않는 질긴 운이라는 관용적 의미를 살렸다." },
    199: { after: "라르크의 섭리로도 희생은 생깁니다.\n호존은 존재 자체가 뒤틀립니다", category: "grammar", reason: "호존과 뒤틀리는 존재의 관계를 자연스러운 주어와 서술 구조로 정리했다." },
  },
  batch_0047: {
    14: { after: "코어를 파괴한다는 건\n저를 죽인다는 뜻입니다", category: "speaker_voice", reason: "정중한 신적 존재의 서술 어조로 문장을 완결했다." },
    18: { after: "다른 사람들은 어디 있을까", category: "naturalness", reason: "다른 모두라는 직역을 일행을 가리키는 자연스러운 표현으로 다듬었다." },
    20: { after: "뭐, 그 ２명이라\n걱정은 안 하지만\n빨리 합류해야겠어", category: "meaning", reason: "상대가 합류해 주기를 바라는 뜻이 아니라 화자가 서둘러 합류해야 한다는 뜻으로 바로잡았다." },
    22: { after: "응. 용사 세실의 상대가 못 되지.\n……라고 해도\n아까는 져 버렸지만", category: "naturalness", reason: "상대가 아니라는 표현을 세실에게 적수가 되지 못한다는 자연스러운 뜻으로 다듬었다." },
    23: { after: "소니아와 얘기했다는 게\n이걸 말한 거였나……", category: "naturalness", reason: "소니아와 나눈 사전 협의의 내용을 되짚는 문장으로 자연스럽게 다듬었다." },
    31: { after: "류즈가 노래하는 돌이라고……?", category: "grammar", reason: "류즈가 돌을 노래한다는 중의성을 피하고 정체를 되묻는 서술 구조로 바로잡았다." },
    39: { after: "자, 라르크. 상대도 진심으로 덤비네.\n이쪽도 마무리로 가자고", category: "naturalness", reason: "상대의 전력과 최종전을 맞는 능글맞은 화자의 어조를 자연스럽게 살렸다." },
    44: { after: "그것은 저를 거짓 신이라 여기고 반란을 일으킨\n메리디아 왕의 짓입니다", category: "proper_noun", reason: "인명과 직위를 구분해 메리디아 왕으로 띄어 썼다." },
    49: { after: "이사 시스템은 이미 붕괴해 있었습니다.\n제가 제 존재에 의문을 품은 순간에", category: "grammar", reason: "자기 자신에 대한 의문이라는 재귀 관계를 자연스럽게 표현했다." },
    63: { after: "라르크.\n섭리를 짜고 세상에 제시하는 건 우리의 역할", category: "meaning", reason: "定理を組む와 示す를 섭리를 구성해 세상에 제시한다는 뜻으로 정확히 옮겼다." },
    65: { after: "미안하다. 신세를 끼쳤군", category: "meaning", reason: "世話をかけた를 신세를 졌다가 아니라 상대에게 수고를 끼쳤다는 뜻으로 바로잡았다." },
    77: { after: "리피아구나. 잘 부탁해", category: "function", reason: "리피아를 부르는 말이 아니라 이름을 확인하고 인사하는 문장으로 바로잡았다." },
    89: { after: "알스 님\n사쥬가 동행하고 있다 해도\n라군 상사 일행을 쫓으시려면――", category: "proper_noun", reason: "인물 이름과 존칭의 띄어쓰기를 기존 표기에 맞췄다." },
    91: { after: "넌 아델 님을 위해\n모든 로그레스를――", category: "proper_noun", reason: "인물 이름과 존칭의 띄어쓰기를 기존 표기에 맞췄다." },
    107: { after: "아, 맞다. 알스, 용 토벌\n계약금 말인데, 의사에게\n한꺼번에 전해지도록 마련해 줘", category: "naturalness", reason: "손써 달라는 직역을 계약금 전달을 주선해 달라는 자연스러운 요청으로 다듬었다." },
    115: { after: "……알스……\n몬스터의 기척이 느껴져.\n그것도 엄청난 무리야", category: "meaning", reason: "大群을 군대가 아니라 몬스터가 이룬 거대한 무리라는 뜻으로 바로잡았다." },
    126: { after: "난 마리아를 에블까지 데려다주고 올게", category: "speaker_voice", reason: "라르크의 자연스러운 반말 의지 표현으로 맞췄다." },
    129: { after: "무슨 뜻이지? 말해!", category: "speaker_voice", reason: "사정을 추궁하는 단정적이고 강한 반문 어조로 다듬었다." },
    136: { after: "하지만 알스 님.\n이 앞부터는 길이 셋으로 나뉘어 있습니다", category: "proper_noun", reason: "인물 이름과 존칭의 띄어쓰기를 기존 표기에 맞췄다." },
    143: { after: "……그럼 이 몸은 오이겐 조에\n넣어 달라고 하지", category: "speaker_voice", reason: "俺様를 사용하는 사쥬의 과장되고 능글맞은 자기 호칭을 살렸다." },
    149: { after: "아, 알았어! 지금 갈게!", category: "function", reason: "부름에 당황해 응답하는 말더듬과 행동 의사를 자연스럽게 표현했다." },
    152: { after: "그게 바로 용사도라는 겁니다", category: "terminology", reason: "勇者道를 승인된 시스템 용어인 용사도로 통일했다." },
    153: { after: "하지만 아델, 라르크는 임무를\n명령받은 거야. 그래서――", category: "grammar", reason: "명령을 받은 대상과 변명의 인과 관계를 자연스럽게 완결했다." },
    166: { after: "전언을 받았습니다", category: "naturalness", reason: "메시지를 맡았다는 직역을 전달할 전언을 받았다는 자연스러운 표현으로 다듬었다." },
    188: { after: "그래. 미안해, 아델", category: "function", reason: "앞선 말을 받아들이는 동의 표현을 자연스럽게 바로잡았다." },
    198: { after: "여관에서 오르키나교 신자로 오해받아\n숙박을 거절당한 데다\n여관 측에서 병사까지 불렀습니다", category: "meaning", reason: "화자가 불려 왔다는 뜻이 아니라 여관이 병사를 호출했다는 행위 관계로 바로잡았다." },
  },
  batch_0048: {
    2: { after: "뭐, 뭐임까?\n설마 여기에 그라가 있는 검까?", category: "speaker_voice", reason: "니콜의 말더듬과 고유한 ~슴까 계열 말투를 복원했다." },
    5: { after: "……당신,\n그들을 믿고 있구나", category: "grammar", reason: "믿는 대상이 뒤에 어색하게 남지 않도록 목적어와 서술어의 어순을 정리했다." },
    7: { after: "소아라. 가요", category: "speaker_voice", reason: "상대에게 함께 가자고 권하는 정중한 청유형을 복원했다." },
    11: { after: "모, 모르겠슴다〜.\n제가 왔을 땐 인상 험악한\n남자들이 여길 습격하고 있었을 뿐임다……", category: "speaker_voice", reason: "니콜의 고유 말투를 세 행에 일관되게 적용했다." },
    13: { after: "저기…… 위험한 순간에\n도와주셔서 감사합니다", category: "naturalness", reason: "위험한 때라는 직역을 위기에서 구조받은 상황에 맞게 다듬었다." },
    16: { after: "형님…… 저, 불안함다……", category: "speaker_voice", reason: "니콜의 불안한 감정과 고유 말투를 함께 살렸다." },
    18: { after: "눈치 없는 건 묻지 마라", category: "meaning", reason: "野暮를 단순히 쓸데없다가 아니라 남의 사정을 눈치 없이 캐묻는다는 뜻으로 풀었다." },
    24: { after: "후후.\n막 잠에서 깬 라르크는 웃긴 얼굴이야", category: "naturalness", reason: "変な顔를 얼굴이 이상하다는 직역이 아니라 장난스럽게 웃긴 표정이라는 뜻으로 다듬었다." },
    25: { after: "……어쩔 수 없지.\n알스와 상의해 볼까", category: "speaker_voice", reason: "라르크의 자연스러운 반말 어조로 맞췄다." },
    29: { after: "그렇지.\n알스는 겁쟁이니까", category: "function", reason: "앞선 말을 받아 동의하는 짧은 맞장구로 바로잡았다." },
    34: { after: "아니.\n한데 뭉쳐…… 뒤엉킨\n그 불쾌한 느낌은 없어", category: "naturalness", reason: "まとまってぐちゃぐちゃした를 한데 뭉쳐 뒤엉킨 기척이라는 자연스러운 표현으로 다듬었다." },
    49: { after: "허허허!\n노스 노와레교의 디바에게\n칭찬받다니 영광입니다", category: "speaker_voice", reason: "디바에게 예를 갖추는 노인의 정중한 말투로 종결을 바로잡았다." },
    50: { after: "……그래. 그렇게 하렴.\n나도 그 ２명이 걱정돼.\n라르크, 부탁할게", category: "speaker_voice", reason: "숫자를 보존하면서 성인 여성의 부드럽고 자연스러운 당부 어조로 다듬었다." },
    64: { after: "난 빼놓는 거야?\n그럼 라르크 조에\n넣어 줘", category: "grammar", reason: "자신만 제외되는지 묻고 편성시켜 달라는 문장 구조를 자연스럽게 바로잡았다." },
    67: { after: "다녀왔어, 아델.\n우리 엄마는 별일 없었어?", category: "meaning", reason: "어머니에게 직접 말을 거는 것이 아니라 아델에게 어머니의 안부를 묻는 관계로 바로잡았다." },
    68: { after: "이사의 아이를 찾은 뒤\n어떻게 해야 할지는\n앞으로 배울 예정이었으니까", category: "naturalness", reason: "목적어와 후속 행동의 시간 관계를 자연스러운 한국어로 정리했다." },
    74: { after: "그라와는 내가 계약했어", category: "speaker_voice", reason: "라르크의 거친 반말 어조로 통일했다." },
    76: { after: "왜 멍하니 있어,\n니콜!", category: "grammar", reason: "멍하니 있다와 자연스럽게 결합하는 의문 부사로 바로잡았다." },
    86: { after: "그래. 위험한 조직의 분위기라고\n하면 되려나", category: "function", reason: "앞선 질문을 받아 설명하는 동의 표현으로 바로잡았다." },
    94: { after: "어? 무슨 일이야, 아델", category: "speaker_voice", reason: "라르크의 놀란 반말 반응을 자연스럽게 맞췄다." },
    98: { after: "아, 알겠슴다! 감다!\n가면 되는 거잖슴까ー!", category: "speaker_voice", reason: "니콜의 짜증 섞인 말더듬과 고유 말투를 두 행에 일관되게 적용했다." },
    103: { after: "역시 형님!\n보는 눈이 높으심다! 이 니콜 님이\n대활약해 보이겠슴다――", category: "speaker_voice", reason: "니콜의 허세와 고유한 ~슴다 말투를 일관되게 살렸다." },
    113: { after: "아, 그것보다 마침 잘 오셨슴다!\n저, 형님을 찾고 있었슴다!", category: "speaker_voice", reason: "니콜의 반가운 보고를 고유 말투로 통일했다." },
    115: { after: "이런, 이런. 저 일행은\n여전하네", category: "naturalness", reason: "주어가 다음 행에 어색하게 남지 않도록 문장 어순을 자연스럽게 정리했다." },
    117: { after: "뭐, 가장 빠른 방법은\n오르키나교 신자인 척하고\n순례선에 섞여 드는 것이지", category: "meaning", reason: "なりすます를 옷만 변장하는 것이 아니라 신자인 척 신분을 위장한다는 뜻으로 바로잡았다." },
    125: { after: "설령 제국의 황자라 해도\n이사의 아이인 이상\n아델 님의 뜻을 따르는 게 당연하다", category: "proper_noun", reason: "인물 이름과 존칭의 띄어쓰기를 기존 표기에 맞췄다." },
    132: { after: "이걸로 빚도 다 청산되겠네", category: "speaker_voice", reason: "라르크의 자연스러운 반말과 빚을 모두 갚는다는 의미를 살렸다." },
    136: { after: "이사의 아이와 이매지널 디바여……\n그리고 나의 사랑스러운 아이들아", category: "terminology", reason: "고정 직위명 イマジナル・ディーバ를 기존 표기인 이매지널 디바로 통일했다." },
    140: { after: "레온은 로드 나이트를\n해산한 뒤 행방불명임다!?", category: "speaker_voice", reason: "니콜의 놀란 보고에 고유한 말투를 복원했다." },
    149: { after: "마하트 폐하께서 병상에 쓰러지시고\n바이스 전하가 실권을 잡은 뒤로\n군의 수준은 계속 떨어지고 있구나", category: "naturalness", reason: "군 녀석들의 질이라는 직역을 조직의 수준이 저하된다는 자연스러운 표현으로 다듬었다." },
    158: { after: "왠지 묘한 분이네.\n하지만 저한테 신경 쓰실 필요 없어요,\n리피아 씨", category: "naturalness", reason: "사람을 신기하다고 하는 직역과 딱딱한 걱정 표현을 자연스럽게 다듬었다." },
    160: { after: "자무엘 씨라는 할아버지에게서\n이걸 받아 왔습니다", category: "meaning", reason: "물건을 맡겼다는 뜻이 아니라 전달을 위해 받아 왔다는 관계로 바로잡았다." },
    166: { after: "오르키나에 가려면\n반드시 배가 필요하네", category: "meaning", reason: "どうしても의 반드시 필요하다는 강한 필수성을 복원했다." },
    183: { after: "뭐?\n왜 그래, 할아버지답지 않게", category: "speaker_voice", reason: "라르크의 놀란 반응을 응답형이 아니라 거친 반문으로 바로잡았다." },
    188: { after: "자세한 건 모름다", category: "speaker_voice", reason: "니콜의 고유 말투를 간결하게 복원했다." },
    196: { after: "리얼 디바의 증표인\n그 펜던트를 도적이?", category: "terminology", reason: "고정 직위명 リアル・ディーバ를 기존 표기인 리얼 디바로 통일하고 펜던트와 증표의 관계를 바로잡았다." },
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
