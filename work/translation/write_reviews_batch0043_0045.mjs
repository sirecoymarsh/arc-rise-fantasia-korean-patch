import fs from "node:fs";
import path from "node:path";

const ROOT = path.join("work", "translation");
const SOURCE_ROOT = path.join(ROOT, "tm_v2", "batches", "source");
const DRAFT_ROOT = path.join(ROOT, "drafts");
const REVIEWED_ROOT = path.join(ROOT, "reviewed");
const REVIEWS_ROOT = path.join(ROOT, "reviews");

const CORRECTIONS = {
  batch_0043: {
    2: { after: "세상의 굴레에서 말이야", category: "naturalness", reason: "앞 문장의 해방 대상을 자연스러운 한국어 조사로 이었다." },
    33: { after: "……어?", category: "function", reason: "놀라 되묻는 짧은 반응을 자연스럽게 복원했다." },
    37: { after: "음, 음", category: "function", reason: "상대의 설명을 들으며 맞장구치는 반응으로 바로잡았다." },
    42: { after: "하지만 여자도 함께니까\n속도를 좀 맞춰 줘야지", category: "naturalness", reason: "동행자의 보행 속도를 배려한다는 뜻을 자연스럽게 표현했다." },
    45: { after: "그래.\n보수 받는 걸 잊는 용병은\n들어 본 적이 없거든", category: "meaning", reason: "보수 자체가 아니라 보수를 받는 일을 잊었다는 의미를 분명히 했다." },
    61: { after: "그래", category: "function", reason: "앞선 제안에 동의하는 짧은 맞장구로 다듬었다." },
    67: { after: "그 뒤에 그 숲에서 나를 만난 거구나", category: "meaning", reason: "이야기의 경위를 확인하며 납득하는 추론 어조로 바로잡았다." },
    84: { after: "아아, 그렇군……", category: "naturalness", reason: "같은 의미가 중복된 표현을 정리하고 절제된 어조를 살렸다." },
    88: { after: "……뭐, 확실히 이 녀석도\n막 쓰러졌었으니까", category: "meaning", reason: "원문에 없는 회복 동작을 덜어 내고 막 쓰러졌던 상태만 반영했다." },
    100: { after: "아니…… 설마\n시엘일 리 없어…… 나는\n１０００년의 세월을 헤맸을 텐데", category: "naturalness", reason: "시간을 헤맨다는 직역을 세월을 헤맸다는 자연스러운 표현으로 다듬었다." },
    108: { after: "난 라르크다.\n마슈가르, 너와 계약을 맺고 싶다", category: "speaker_voice", reason: "로그레스에게 자신을 밝히고 계약을 청하는 단정적인 어조로 맞췄다." },
    110: { after: "우리가 모르는 사이에\n몹시 긴장하고 있었던 모양이군.\n무거운 사명을 짊어진 아이인 만큼……", category: "naturalness", reason: "막중한 사명을 진 인물의 긴장을 자연스러운 한국어로 표현했다." },
    112: { after: "응?\n그럼 좋아하는 음식 얘기나 하자", category: "naturalness", reason: "화제를 즉석에서 정하는 구어체 문장으로 자연스럽게 완결했다." },
    113: { after: "결국 셰리의 기세에는\n못 당하겠구나……", category: "naturalness", reason: "상대의 강한 밀어붙임을 이기지 못한다는 뜻을 관용적으로 다듬었다." },
    116: { after: "이 녀석……\n코 고는 소리가 엄청나네", category: "speaker_voice", reason: "라르크의 거친 반말 어조와 감탄을 자연스럽게 맞췄다." },
    119: { after: "설마?\n아니, 그 설마일지도 모르지만……", category: "naturalness", reason: "같은 말을 되받아 가능성을 인정하는 자기 정정 어조로 다듬었다." },
    120: { after: "맞아, 바로 그거!", category: "function", reason: "상대가 제시한 표현을 반갑게 받아들이는 맞장구로 바로잡았다." },
    134: { after: "으으……\n이쪽으로 오면 안 됨다\n안 그러면 험한 꼴을……", category: "speaker_voice", reason: "니콜의 고유 말투와 뒤따를 위험을 경고하는 의미를 함께 살렸다." },
    153: { after: "다음은 나인가.\n소금에 절인 훈제 고기다", category: "speaker_voice", reason: "오이겐의 절제되고 격식 있는 서술 어조로 통일했다." },
    171: { after: "입 다물고 있어", category: "register", reason: "원문보다 과도하게 거친 욕설이 되지 않도록 명령의 강도를 맞췄다." },
    176: { after: "자자, 건배하죠", category: "speaker_voice", reason: "일행에게 건배를 권하는 정중한 청유형으로 다듬었다." },
    180: { after: "글쎄……\n뭐, 아델은\n여동생 같은 애니까", category: "function", reason: "질문에 답을 고르는 망설임을 동의 표현으로 잘못 옮긴 부분을 바로잡았다." },
    187: { after: "칭찬 참 고맙다.\n난 이제 슬슬 잘 건데?", category: "speaker_voice", reason: "라르크의 빈정대는 감사와 거친 반말 어조를 자연스럽게 살렸다." },
    191: { after: "뭐야? 왜 그렇게 진지한 표정이야", category: "naturalness", reason: "진지한 얼굴을 보고 가볍게 말을 거는 문장으로 자연스럽게 다듬었다." },
    196: { after: "난 스튜가 좋아", category: "meaning", reason: "주문을 고르는 말이 아니라 좋아하는 음식을 밝히는 답변으로 바로잡았다." },
    197: { after: "분명 어제는 새로운 생명이\n１２개의 고리에 의해 발견되고\n불길한 １３이……", category: "meaning", reason: "見いだされて를 근거 없이 선택받았다고 확장하지 않고 발견된다는 뜻으로 옮겼다." },
    199: { after: "그런 모양이군", category: "speaker_voice", reason: "격식 있고 절제된 화자의 짧은 동의 어조로 맞췄다." },
  },
  batch_0044: {
    1: { after: "편하게 있지 말고\n나가라고!!", category: "function", reason: "상대를 몰아내는 고함의 명령 강도와 느낌표를 복원했다." },
    3: { after: "어――", category: "function", reason: "갑작스러운 말에 놀라는 짧은 반응으로 바로잡았다." },
    4: { after: "에?", category: "function", reason: "잠결에 잘못 알아듣고 되묻는 반응을 자연스럽게 표현했다." },
    16: { after: "하아……?", category: "function", reason: "황당해하며 되묻는 감탄의 기능을 보존했다." },
    20: { after: "지난번 파티가 호평이었지.\n역시 이 의상 덕분이겠군.\n준비한 보람이 있었다", category: "speaker_voice", reason: "권위 있고 단정적인 화자의 어조로 세 문장을 통일했다." },
    23: { after: "그래서 공평하게 제비를 뽑아\n침대와 바닥으로 나눈 거잖슴까.\n참으셔야 함다", category: "speaker_voice", reason: "니콜의 고유 말투를 세 행에 일관되게 적용했다." },
    26: { after: "각오할 수밖에 없겠군.\n공화국 의장이\n손님을 즐겁게 하려는 여흥이라고 하지 않았나", category: "meaning", reason: "여흥을 근거로 각오해야 한다는 문장의 논리 관계를 완결했다." },
    29: { after: "그럼 우린 방으로 돌아갈게〜\n잘 자〜\n악몽을 꿀 수 있겠어〜", category: "naturalness", reason: "嫌な夢를 자연스러운 한국어인 악몽으로 옮기고 장난스러운 말투를 살렸다." },
    37: { after: "방으로 돌아가는 건 너 １명뿐이야?\n내 침대에서 자면 돼", category: "grammar", reason: "숫자를 보존하면서 혼자 방으로 돌아가는 대상을 자연스럽게 표현했다." },
    51: { after: "목소리……일까……", category: "grammar", reason: "명사 뒤에 어색하게 붙은 추측형을 자연스러운 서술 구조로 바로잡았다." },
    52: { after: "그러게", category: "function", reason: "앞선 판단에 동의하는 짧은 맞장구로 다듬었다." },
    54: { after: "불만 있어?", category: "naturalness", reason: "悪いかよ의 도전적인 반문을 자연스러운 한국어 구어로 옮겼다." },
    64: { after: "오이겐은……\n잠시 같이 있어 줄래?\n들어 줬으면 하는 이야기가 있어……", category: "meaning", reason: "付き合う를 교제 의미가 아니라 잠시 곁에 있어 달라는 뜻으로 분명히 했다." },
    68: { after: "정말, 어쩔 수 없네", category: "speaker_voice", reason: "라르크의 투덜거리는 반말 어조로 맞췄다." },
    69: { after: "자, 와 줬다고", category: "speaker_voice", reason: "일부러 와 주었다는 노련하고 자신만만한 화자의 뉘앙스를 살렸다." },
    71: { after: "으악……\n최악이야……\n사쥬랑 니콜이라니", category: "naturalness", reason: "두 사람을 보고 질색하는 감탄을 한국어 문장으로 자연스럽게 완결했다." },
    75: { after: "신경이 쓰여서……\n넌 어렵게\n만난 이사의 아이니까……", category: "meaning", reason: "せっかくめぐり会えた를 모처럼이 아니라 어렵게 만난 소중한 존재라는 뜻으로 옮겼다." },
    76: { after: "그래.\n힘내, 리피아", category: "function", reason: "앞선 말에 동의하고 응원하는 흐름을 자연스럽게 이었다." },
    83: { after: "가상하군.\n레슬리치고는 드문 모습이다", category: "speaker_voice", reason: "상대를 평하는 격식 있고 절제된 화자의 어조로 통일했다." },
    84: { after: "그러게", category: "naturalness", reason: "확실하다는 직역을 자연스러운 동의의 맞장구로 다듬었다." },
    86: { after: "벽의 꽃은 아니고……\n칼처럼 서 있는 사람도 있는 모양이지만.\n뭐, 상관없나", category: "meaning", reason: "壁の花ならぬ의 부정 대비와 이어지는 칼의 비유를 정확히 연결했다." },
    88: { after: "에에에에……!?", category: "function", reason: "내용을 되묻는 말이 아니라 길게 놀라는 감탄을 그대로 살렸다." },
    90: { after: "리피아도 니콜도\n거의 잠들었네.\n하핫", category: "speaker_voice", reason: "라르크의 자연스러운 반말 관찰 어조로 맞췄다." },
    96: { after: "질의응답.\n질문을 넘기는 건 받아 주지 않습니다", category: "naturalness", reason: "질문에 패스한다는 행위를 자연스러운 한국어로 풀었다." },
    107: { after: "악몽이라도 꿨어?", category: "naturalness", reason: "나쁜 꿈이라는 직역을 자연스러운 일상 표현으로 다듬었다." },
    109: { after: "이거 우연이네, 나도 얼굴이야", category: "naturalness", reason: "자신도 얼굴이 장점이라고 능글맞게 맞받는 농담을 자연스럽게 살렸다." },
    111: { after: "그, 그렇구나……", category: "speaker_voice", reason: "당황한 라르크의 부드러운 반말 반응으로 바로잡았다." },
    114: { after: "잠이 덜 깼냐.\n세실이잖아. 문 열어 줘", category: "meaning", reason: "寝ぼける를 잠꼬대가 아니라 잠이 덜 깬 상태라는 뜻으로 바로잡았다." },
    120: { after: "재미있는 일이 생길 기미가\n역력해서 그런 거 아니야?", category: "grammar", reason: "기색의 주체와 재미있는 사건의 관계를 자연스럽게 완결했다." },
    124: { after: "……큭큭……\n미안해. 네가\n너무 진지한 표정이라서", category: "naturalness", reason: "얼굴이라는 직역을 표정으로 다듬어 웃은 이유를 자연스럽게 표현했다." },
    133: { after: "네 몸에는 내 맹우들의\n로고스가 깃든 모양이군", category: "meaning", reason: "我が盟友를 화자 자신의 맹우들이라는 관계로 바로잡았다." },
    140: { after: "많이 기다렸지?", category: "naturalness", reason: "반복된 인사를 한국어의 친근하고 자연스러운 도착 인사로 다듬었다." },
    157: { after: "자, 슬슬 체념할 때다.\n해 줘야겠어――", category: "meaning", reason: "観念する를 각오하다가 아니라 저항을 포기하고 받아들인다는 뜻으로 바로잡았다." },
    162: { after: "아슬아슬하다기보다……\n리피아, 피부 예뻐", category: "speaker_voice", reason: "어린 화자의 직설적이고 자연스러운 반말 어조로 맞췄다." },
    170: { after: "돕는 거라면 해 줄게", category: "meaning", reason: "도움을 허락한다는 뜻이 아니라 직접 도와주겠다는 의사로 바로잡았다." },
    175: { after: "음식 시중도 부탁하고 싶지만\n오늘은 더 중요한 일이 있다.\n여흥을 부탁하고 싶군", category: "meaning", reason: "給仕를 일반 접대가 아니라 파티에서 음식 시중을 드는 일로 구체화했다." },
    183: { after: "부, 불길한 예감……", category: "naturalness", reason: "싫은 예감이라는 직역을 관용적인 불길한 예감으로 다듬고 말더듬을 보존했다." },
    188: { after: "……마음을 가다듬도록 하죠", category: "naturalness", reason: "気を取り直す의 관용적 의미를 자연스러운 한국어로 옮겼다." },
    191: { after: "당신은\n정말 신경 쓰인단 말이지……", category: "meaning", reason: "가정 표현이 아니라 상대의 경우가 특히 염려된다는 뜻으로 바로잡았다." },
    197: { after: "또 참\n의욕도 색기도\n없는 질문이네……", category: "meaning", reason: "色気를 낭만으로 바꾸지 않고 능글맞은 화자가 말하는 성적 매력의 뜻을 살렸다." },
  },
  batch_0045: {
    2: { after: "남자애 옷?", category: "naturalness", reason: "아이의 성별을 가리키는 구어를 자연스러운 한국어로 다듬었다." },
    9: { after: "여전히 딱딱하다고 해야 하나\n오이겐 씨는 참 성실하네", category: "meaning", reason: "真面目를 진지한 표정이 아니라 고지식할 만큼 성실한 성품이라는 뜻으로 옮겼다." },
    12: { after: "이렇게 함께 여행하는 것도\n어떤 인연이겠지――", category: "naturalness", reason: "무언가의 인연이라는 직역을 자연스러운 추측 표현으로 다듬었다." },
    18: { after: "뭐, 됐어. 첫 질문이니까.\n내가 좋아하는 건…… 빵이야.\n갓 구운 거", category: "speaker_voice", reason: "거친 반말 화자의 말투와 좋아하는 음식을 밝히는 흐름을 자연스럽게 맞췄다." },
    20: { after: "그렇지…… 잠깐, 왜!?\n여기서 약한 모습을 보이면\n계속 이용당할 거야", category: "meaning", reason: "つけこまれる를 약점이 잡힌다가 아니라 약한 틈을 이용당한다는 뜻으로 바로잡았다." },
    24: { after: "응?", category: "speaker_voice", reason: "부드러운 여성 화자가 부름에 답하는 자연스러운 반말로 맞췄다." },
    25: { after: "음?\n아, 그렇군", category: "speaker_voice", reason: "격식 있고 절제된 화자의 짧은 깨달음 어조로 맞췄다." },
    31: { after: "가령 말이야.\n리피아와 아델, 저 ２명 중\n누가 더 취향이야?", category: "grammar", reason: "숫자를 보존하면서 두 사람 중 선호를 묻는 문장 구조를 자연스럽게 정리했다." },
    33: { after: "아니, 그러니까…… 돕고 가라", category: "speaker_voice", reason: "상대를 붙잡아 도움을 명하는 단정적 어조로 완결했다." },
    53: { after: "함부로 내 이름 부르지 마!\n아무렇지도 않은 얼굴로\n라르크 옆에 붙어 있고!", category: "naturalness", reason: "당연하다는 듯 행동한다는 비난을 자연스러운 한국어 표정 묘사로 옮겼다." },
    56: { after: "변한 건\n아델의 마음이잖아.\n주변은 아무것도 안 변했어", category: "grammar", reason: "마음 쪽이라는 직역을 자연스러운 주어와 서술 구조로 바로잡았다." },
    58: { after: "아하하하핫! 당연하잖아.\n누나, 누나와 아버지 일행을\n두고 하는 말이야!", category: "meaning", reason: "父さんたち를 여러 아버지가 아니라 아버지와 그 일행을 가리키는 뜻으로 바로잡았다." },
    102: { after: "라르크의 말이 기뻤어.\n다들 내 눈치를 보며 조심스럽게\n대했지만 라르크는 달랐어", category: "meaning", reason: "腫れ物に触るように의 과도하게 조심스레 대한다는 관용적 의미를 자연스럽게 풀었다." },
    105: { after: "라르크. 가요", category: "speaker_voice", reason: "상대에게 함께 가자고 권하는 정중한 청유 어조를 복원했다." },
    113: { after: "……오이겐이……\n몰랐다고 해도, 다른\n아이온대 대원들은 알고 있었을까", category: "grammar", reason: "몰랐다는 조건의 주체와 다른 대원들을 명확히 구분했다." },
    118: { after: "내가 녀석의 주의를 끌겠다.\n그동안 너희는 비광정으로 서둘러라", category: "meaning", reason: "引きつける를 붙잡아 둔다는 뜻이 아니라 주의를 자신에게 돌린다는 뜻으로 바로잡았다." },
    119: { after: "잠깐.\n저 ２명, 대체 왜 저래?", category: "grammar", reason: "숫자를 보존하면서 두 사람을 화제로 삼는 조사와 어순을 자연스럽게 정리했다." },
    123: { after: "어?\n아니, 그냥 문득 생각났어", category: "speaker_voice", reason: "라르크의 놀란 반응을 부드러운 응답으로 잘못 옮긴 부분을 바로잡았다." },
    126: { after: "라르크가 가 버리겠어", category: "function", reason: "현재 상황을 경고하고 재촉하는 미래 어조로 완결했다." },
    128: { after: "도망치라고 할 때만큼은\n대답 하나는 잘한다니까\n니콜 녀석은 말이야", category: "meaning", reason: "返事がいい를 단순히 빠르다가 아니라 유난히 시원하게 응답한다는 뜻으로 다듬었다." },
    147: { after: "그린힐 의장의 지시가\n없으면 움직이지 않기로\n되어 있을 텐데", category: "grammar", reason: "조직의 행동 원칙을 나타내는 문장을 자연스러운 피동 구조로 완결했다." },
    151: { after: "그러니까 이런 곳에서\n생각에 빠지지 말라고\n전에 말했잖아", category: "meaning", reason: "考え事를 엉뚱한 생각이 아니라 주변을 잊고 생각에 잠기는 행위로 바로잡았다." },
    160: { after: "……미안해.\n하지만 나를 내버려 둬", category: "particle", reason: "放っておいて의 목적어에 맞는 목적격 조사를 사용했다." },
    188: { after: "……알스는 언제나\n그런 식으로 도망치는 거야!", category: "function", reason: "새삼 깨닫는 어조가 아니라 상대를 비난하는 단정적 감정 표현으로 바로잡았다." },
    191: { after: "뭐야! 너 따위가아!", category: "naturalness", reason: "분노로 길게 외치는 감탄을 어색한 철자 없이 자연스럽게 표현했다." },
    198: { after: "……내버려 둬. １명뿐이어도 난 괜찮으니까", category: "grammar", reason: "숫자를 보존하면서 혼자여도 괜찮다는 문장을 자연스러운 어순으로 다듬었다." },
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
    draft_translator: "/root/translate_batch_0009",
    draft_author: "/root/translate_batch_0009",
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
