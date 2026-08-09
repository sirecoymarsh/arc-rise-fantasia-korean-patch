const fs = require("fs");
const path = require("path");

const reviewer = "/root/translate_batch_0008";
const draftAuthor = "/root/translate_batch_0009";

const reviews = {
  batch_0049: {
    6: {
      text: "애초에 여긴\n공화국이 아니야.\n아무도 널 떠받들 필요 없어",
      category: "meaning",
      reason: "공화국도 아니라는 추가 의미가 생기지 않도록 원문의 단정 표현을 바로잡았다.",
    },
    19: {
      text: "오이겐은 그런 녀석이 아니라고오",
      category: "speaker_voice",
      reason: "부정문의 필수 조사와 늘여 말하는 어조를 자연스럽게 복원했다.",
    },
    45: {
      text: "아니, 근데, 있잖아\n나는 후방 지원에 맞는 편이랄까……",
      category: "naturalness",
      reason: "후방 지원에 적합하다는 뜻을 한국어 구어체로 자연스럽게 다듬었다.",
    },
    54: {
      text: "너희 이교도들은\n무서〜운 황태자 전하께\n꼬챙이에 꿰일지도 몰라",
      category: "grammar",
      reason: "꼬챙이에 꿰인다는 원문의 위협이 자연스럽게 성립하도록 서술어를 보완했다.",
    },
    65: {
      text: "아무튼 형님\n당장 구하러 가 주세요!",
      category: "meaning",
      reason: "습격당한 이들을 구조하러 가라는 뜻이 드러나도록 동사를 바로잡았다.",
    },
    67: {
      text: "라르크 일행은\n이미 이 앞쪽으로 가고 있다\n너희도……",
      category: "naturalness",
      reason: "앞으로 향하고 있다는 진행 의미를 자연스러운 한국어로 정리했다.",
    },
    82: {
      text: "좋아, 잠깐 보고 올까",
      category: "meaning",
      reason: "직접 가서 상황을 살펴본다는 의미를 살렸다.",
    },
    106: {
      text: "――이해하고 있어, 디노스",
      category: "naturalness",
      reason: "직역투인 자기 인식 표현을 간결하고 자연스러운 대사로 다듬었다.",
    },
    108: {
      text: "그럼.\n엄마한테 얘기하고 올까",
      category: "naturalness",
      reason: "어머니에게 말을 건네러 간다는 뜻을 문맥에 맞는 구어체로 옮겼다.",
    },
    111: {
      text: "뭐…… 뭐……!\n차, 차분하게\n쉴 수가 없잖아!",
      category: "speaker_voice",
      reason: "당황해 말을 더듬는 감탄이 일인칭 대명사로 오해되지 않도록 고쳤다.",
    },
    122: {
      text: "미안해. 내 힘이 부족해서\n라르크를 끔찍한 일에 휘말리게 했어……",
      category: "grammar",
      reason: "라르크가 피해를 입게 했다는 사역 관계가 올바르게 드러나도록 고쳤다.",
    },
    127: {
      text: "매라고!? 또\n믿을 만한지 아닌지도\n모를 방법을 쓰자고……",
      category: "naturalness",
      reason: "매를 이용한 연락 수단의 신뢰성을 의심하는 대사를 자연스럽게 다듬었다.",
    },
    139: {
      text: "호에…… 방금 게 계약……!",
      category: "grammar",
      reason: "'지금 게'라는 어색한 결합을 문맥에 맞는 '방금 게'로 바로잡았다.",
    },
    140: {
      text: "오르키나교는 현세의 기도와 순교로\n내세의 번영을 약속하는 가르침이기에\n배척당하는 거겠지요",
      category: "meaning",
      reason: "교리가 사람들에게 기피되고 배척된다는 원문의 의미와 문장 흐름을 살렸다.",
    },
    152: {
      text: "뭐, 딱히\n이사의 아이니 뭐니 하는 데\n관심은 없으니 상관없지만",
      category: "terminology",
      reason: "설정 용어 '이사의 아이'를 성별이 한정되는 '아들'과 구분했다.",
    },
    175: {
      text: "나머지 １개 조를 이끌 사람은……\n오이겐, 당신이 적임자라고 생각해",
      category: "naturalness",
      reason: "두 번째 조를 가리키는 표현을 자연스럽게 다듬고 전각 숫자를 보존했다.",
    },
    188: {
      text: "둘 중 누구를 데려가시겠습니까?",
      category: "meaning",
      reason: "제시된 두 사람 가운데 한 명을 고르는 선택문임을 분명히 했다.",
    },
    190: {
      text: "위기에 빠진 소녀를 구하는 건\n멋지게 등장한 용사님 몫이지!",
      category: "grammar",
      reason: "수식 관계가 어색했던 문장을 자연스러운 한국어 대사로 바로잡았다.",
    },
    200: {
      text: "남을 돕는 건 용사의 길에서 기본!\n나도 사람을 돕고 싶고\n레온도 만나고 싶어",
      category: "grammar",
      reason: "'용사의 길의 기본'이라는 중복 조사를 자연스럽게 다듬었다.",
    },
  },
  batch_0050: {
    18: {
      text: "이 자식……!\n내가 좋게 대해 줬더니\n기어오르네!",
      category: "naturalness",
      reason: "직역투인 주어 표현을 화자의 거친 구어체에 맞게 다듬었다.",
    },
    33: {
      text: "마리아는 어디에 있는 걸까……",
      category: "grammar",
      reason: "마리아의 소재를 묻는 문장이 호격으로 읽히지 않도록 조사를 보완했다.",
    },
    35: {
      text: "이사의 아이를 찾는 건\n좀 더 나중이어야 했어",
      category: "naturalness",
      reason: "원래 예정 시점이 더 뒤였다는 뜻을 간결하고 자연스럽게 다듬었다.",
    },
    54: {
      text: "……한 건 해 주셨군, 바이스 님.\n난 버림패라는 거냐",
      category: "meaning",
      reason: "상대의 계략을 비꼬는 어조와 '버림패'의 의미를 정확히 살렸다.",
    },
    75: {
      text: "다음에 식사가 들어오면\n감방을 부수고 간수를 인질로 잡는다",
      category: "word_choice",
      reason: "탈옥 문맥에서 '牢'를 건물 전체가 아닌 감방으로 구체화했다.",
    },
    78: {
      text: "오르키나 때도 그렇고\n우린 이런 곳만\n걷게 되는군요",
      category: "meaning",
      reason: "이유를 깨달았다는 뜻의 '어쩐지'를 제거해 반복 경험을 나열하는 원문을 살렸다.",
    },
    88: {
      text: "의장님! 이토록 무법한 메리디아\n제국을 내버려 둬도 되는 겁니까!",
      category: "meaning",
      reason: "제국을 용서하는 것이 아니라 횡포를 용인하는 상황임을 분명히 했다.",
    },
    97: {
      text: "라르크에겐 비광정 일로\n빚이 있으니까.\n그리고 남을 돕는 건 용사의 길에서 기본이잖아",
      category: "grammar",
      reason: "'용사의 길의 기본'이라는 중복 조사를 자연스럽게 다듬었다.",
    },
    99: {
      text: "몇 번이나 말해야 하나. 나는 오이겐이다",
      category: "naturalness",
      reason: "일본어식 사역 표현을 위엄 있는 한국어 대사로 바로잡았다.",
    },
    107: {
      text: "이그나츠는 ＱＥＤ라 불리는\n암살 집단을 조종해 공화국 정치에\n개입하고 있다",
      category: "format_fidelity",
      reason: "원문의 전각 표기 'ＱＥＤ'를 그대로 복원했다.",
    },
    111: {
      text: "제정신인가? 정면 돌파는 무리다.\n비밀 통로를 이용하자",
      category: "function",
      reason: "행동 방침을 제안하는 대사에 맞게 종결 표현을 바로잡았다.",
    },
    115: {
      text: "라르크! 뒤에도 있어!",
      category: "naturalness",
      reason: "후방의 적을 경고하는 짧은 외침을 자연스럽게 다듬었다.",
    },
    118: {
      text: "그래.\n２명 모두 고마워",
      category: "numeric_fidelity",
      reason: "두 사람을 가리키는 전각 숫자 '２'를 보존했다.",
    },
    126: {
      text: "역시 출구 경비는 철통같군.\n여길 돌파하기는 어렵겠다",
      category: "grammar",
      reason: "출구가 스스로 지키는 것처럼 읽히던 주술 관계를 바로잡았다.",
    },
    127: {
      text: "……얼굴에 안 어울리는 말을\n하는 녀석이네",
      category: "grammar",
      reason: "한국어 관용 표현에 맞게 조사를 바로잡았다.",
    },
    136: {
      text: "달리 갈 만한 곳도 없으니까",
      category: "naturalness",
      reason: "갈 곳이 달리 없다는 뜻을 중복 없이 자연스럽게 다듬었다.",
    },
    139: {
      text: "어떻게든 도망쳐 나왔군.\n아직 도시 안까지는\n수색이 미치지 않은 건가……",
      category: "meaning",
      reason: "추격대의 수색 범위가 아직 시내에 닿지 않았다는 의미를 명확히 했다.",
    },
    142: {
      text: "라르크. 그렇게 하자.\n그 많은 사람과 싸워서\n쓸데없이 부상자를 내는 건 좋지 않아",
      category: "meaning",
      reason: "불필요한 부상자를 내는 것이 바람직하지 않다는 판단을 정확히 살렸다.",
    },
    143: {
      text: "음의 시대에 쓰던 엘리베이터의 일종이다.\n이걸 쓰면 단숨에 꼭대기 층까지\n갈 수 있을 것이다",
      category: "terminology",
      reason: "고정 설정어 '負の時代'를 '음의 시대'로 바로잡았다.",
    },
    157: {
      text: "하아? 기껏해야 １００층이 될까\n말까겠지.\n구름 위라니, 또 과장이 심하네",
      category: "meaning",
      reason: "100층을 넘는다는 뜻이 아니라 많아야 100층 안팎이라는 의미로 바로잡고 전각 숫자를 보존했다.",
    },
    163: {
      text: "으음. 그래도\n기껏해야 １００층이 될까\n말까잖아",
      category: "meaning",
      reason: "높이가 많아야 100층 안팎이라는 의미로 바로잡고 전각 숫자를 보존했다.",
    },
    166: {
      text: "근데 아이온대가 왜\n이런 교회를 접수한 걸까요",
      category: "word_choice",
      reason: "조직이 시설을 넘겨받아 관리한다는 '接収'의 의미를 살렸다.",
    },
    170: {
      text: "……하지만 뒤에서는 딴짓을 했잖아?",
      category: "naturalness",
      reason: "조직의 겉과 다른 이면을 지적하는 거친 대사로 자연스럽게 다듬었다.",
    },
    173: {
      text: "뭔지는 모르겠지만 넌\n이 시설에 상당히 마음 쓰는\n모양이니까",
      category: "meaning",
      reason: "시설에 특별한 사정과 관심이 있다는 의미가 과도하게 부정적으로 읽히지 않도록 했다.",
    },
    185: {
      text: "마…… 멋대로 죽은 사람 취급하지 마!",
      category: "meaning",
      reason: "실제로 죽이지 말라는 뜻이 아니라 생존자를 죽었다고 단정하지 말라는 문맥을 살렸다.",
    },
    198: {
      text: "……이게 무슨 일인지\n밖에 나가면 차근차근\n설명해 줘야겠어, 오이겐 나리",
      category: "meaning",
      reason: "화자가 오이겐에게 설명을 요구한다는 방향을 올바르게 바로잡았다.",
    },
  },
  batch_0051: {
    10: {
      text: "그렇구나. 너희가 이런 탑을\n많이 봤다면 여긴\n음의 시대 건축물일지도 모르겠네",
      category: "terminology",
      reason: "고정 설정어 '負の時代'를 '음의 시대'로 바로잡았다.",
    },
    16: {
      text: "모두를 도우려고",
      category: "grammar",
      reason: "도움의 대상을 나타내는 목적격 관계를 자연스럽게 보완했다.",
    },
    28: {
      text: "라르크……\n파피르사그는 우리가 차지했어",
      category: "meaning",
      reason: "경쟁 끝에 파피르사그와 먼저 계약했다는 문맥을 살렸다.",
    },
    29: {
      text: "자무엘 할아버지도\n엄마도, 라르크도!",
      category: "speaker_voice",
      reason: "감정적으로 자신의 어머니를 열거하는 장면에 맞춰 호칭을 자연스럽게 다듬었다.",
    },
    37: {
      text: "……당신의 목을 내놔!",
      category: "function",
      reason: "목숨을 요구하는 위협이 한국어 대사로 강하게 전달되도록 다듬었다.",
    },
    39: {
      text: "어라. 이 엘리베이터\n레이 에너지가 공급되지 않는 것 같아",
      category: "meaning",
      reason: "엘리베이터에 에너지가 공급되지 않는 상태임을 분명히 했다.",
    },
    40: {
      text: "사쥬 말대로\n여기서 살려 보내 봐야 해가 될 뿐이야",
      category: "meaning",
      reason: "적을 놓아주는 행위가 해만 낳는다는 원문의 판단을 정확히 살렸다.",
    },
    82: {
      text: "음의 시대에 쓰던 엘리베이터의 일종이다.\n저걸 쓰면 단숨에 꼭대기 층까지\n갈 수 있을 것이다",
      category: "terminology",
      reason: "고정 설정어 '負の時代'를 '음의 시대'로 바로잡았다.",
    },
    87: {
      text: "공화국 귀류법에 기록된 특수 공작대\n『끝나지 않는 어둠의 여왕』――ＱＥＤ",
      category: "terminology",
      reason: "고정 용어 '공화국 귀류법'과 원문의 전각 표기 'ＱＥＤ'를 복원했다.",
    },
    101: {
      text: "이 문을 열면 침입이 있었다는 사실을\n아이온대에 알리게 된다",
      category: "meaning",
      reason: "문을 여는 순간 과거의 침입 사실이 통보된다는 의미를 분명히 했다.",
    },
    121: {
      text: "하지만 사쥬도 내려갔으니까\n그게 １순위라고 생각했어",
      category: "naturalness",
      reason: "가장 나은 선택이라는 뜻을 자연스럽게 다듬고 전각 숫자 '１'을 보존했다.",
    },
    127: {
      text: "그게 １순위겠지, 오이겐",
      category: "naturalness",
      reason: "최선의 선택이라는 뜻을 자연스럽게 다듬고 전각 숫자 '１'을 보존했다.",
    },
    135: {
      text: "그러게. 노스 노와레교에서\n중요한 교회라면",
      category: "grammar",
      reason: "해당 종교에서 중요한 교회라는 관계가 자연스럽게 드러나도록 조사를 바로잡았다.",
    },
    138: {
      text: "탁룡을 상대로 １명이서 싸울 셈이야!?",
      category: "grammar",
      reason: "혼자 싸운다는 뜻을 중복 없이 다듬고 전각 숫자 '１'을 보존했다.",
    },
    144: {
      text: "라르크.\n파피르사그와의 계약은 마쳤어",
      category: "grammar",
      reason: "계약 상대와의 관계를 나타내는 조사를 자연스럽게 보완했다.",
    },
    147: {
      text: "어떻게 해야 하는지는 간단해",
      category: "naturalness",
      reason: "행동 방침이 명확하다는 뜻을 자연스러운 한국어로 다듬었다.",
    },
    154: {
      text: "그렇다면――나를 죽이러 와라.\n또 １명의 어리석은 이사의 아이\n알폰스 제나 메리디아",
      category: "numeric_fidelity",
      reason: "또 한 명을 가리키는 원문의 전각 숫자 '１'을 보존했다.",
    },
    157: {
      text: "으으, 열받아!\n화려하게 퇴장해 버렸어!\n분해!",
      category: "meaning",
      reason: "화자 자신이 퇴장당한 것이 아니라 상대가 떠나 버린 상황과 분한 감정을 살렸다.",
    },
    169: {
      text: "……정식 절차를 밟은\n접수가 아닐지도 모른다",
      category: "word_choice",
      reason: "시설을 정식으로 넘겨받는 '接収'의 의미를 '점거'와 구분했다.",
    },
    174: {
      text: "호존을 투여한\n인체 실험 논문이야",
      category: "naturalness",
      reason: "일본어식 명사 연결을 자연스러운 한국어 관형 구조로 다듬었다.",
    },
    183: {
      text: "라르크……\n당신의 목을 내놔!",
      category: "function",
      reason: "목숨을 요구하는 위협이 한국어 대사로 강하게 전달되도록 다듬었다.",
    },
  },
};

for (const [batchId, changes] of Object.entries(reviews)) {
  const sourcePath = `work/translation/tm_v2/batches/source/${batchId}.jsonl`;
  const draftPath = `work/translation/drafts/${batchId}.jsonl`;
  const reviewedPath = `work/translation/reviewed/${batchId}.jsonl`;
  const reviewPath = `work/translation/reviews/${batchId}_review.json`;
  const readJsonl = (file) => fs.readFileSync(file, "utf8")
    .split(/\r?\n/)
    .filter(Boolean)
    .map(JSON.parse);

  const sourceRows = readJsonl(sourcePath);
  const draftRows = readJsonl(draftPath);
  const modifications = [];
  const reviewedRows = sourceRows.map((sourceRow, zeroIndex) => {
    const index = zeroIndex + 1;
    const before = draftRows[zeroIndex].translation_ko;
    const change = changes[index];
    const after = change ? change.text : before;
    if (change) {
      modifications.push({
        tm_id: sourceRow.tm_id,
        source_text: sourceRow.source_text,
        before,
        after,
        category: change.category,
        reason: change.reason,
      });
    }
    return { ...sourceRow, translation_ko: after };
  });

  fs.mkdirSync(path.dirname(reviewedPath), { recursive: true });
  fs.mkdirSync(path.dirname(reviewPath), { recursive: true });
  fs.writeFileSync(reviewedPath, `${reviewedRows.map((row) => JSON.stringify(row)).join("\n")}\n`, "utf8");

  const report = {
    schema: "arf-translation-independent-review-v1",
    batch_id: batchId,
    reviewer,
    draft_translator: draftAuthor,
    draft_author: draftAuthor,
    independent_review: true,
    translation_engine_policy: "Codex internal models only",
    external_translation_services_used: [],
    external_translation_models_or_apis_used: [],
    source: sourcePath,
    draft: draftPath,
    reviewed_output: reviewedPath,
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
  process.stdout.write(`${batchId}\t${modifications.length}\n`);
}
