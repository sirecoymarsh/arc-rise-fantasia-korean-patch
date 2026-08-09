const fs = require("fs");
const path = require("path");

const reviewSets = {
  batch_0034: {
    13: {
      after: "이것이 바다 위에서 보는 광경인가――\n참으로 엄청난 결정화군",
      category: "meaning_tone",
      reason: "すさまじい를 공포로 단정한 표현 대신 결정화의 엄청난 규모를 나타내도록 바로잡았다.",
    },
    19: {
      after: "정말, ２명 모두 변함없네",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 ２를 그대로 보존했다.",
    },
    26: {
      after: "뭐야?　악필이네.\n『남쪽에 있는 겁니다』……라고\n이것만으론 모르겠잖아……",
      category: "naturalness",
      reason: "汚い字를 글씨가 물리적으로 더럽다는 뜻이 아니라 읽기 힘든 악필로 자연스럽게 옮겼다.",
    },
    47: {
      after: "나는 왜\n신종이라는 사실을 알지 못했던 걸까……",
      category: "meaning",
      reason: "정체를 고지받지 못한 상태였다는 의미가 자연스럽게 드러나도록 다듬었다.",
    },
    57: {
      after: "월반했어",
      category: "terminology",
      reason: "飛び級의 일반적인 한국어 표현인 월반으로 교정했다.",
    },
    59: {
      after: "멋진 문장이네요",
      category: "context_naturalness",
      reason: "직전의 사랑 고백 대사를 가리키는 フレーズ를 문맥에 맞는 문장으로 옮겼다.",
    },
    74: {
      after: "뭐, 가 주도록 하자고",
      category: "speaker_voice",
      reason: "거친 남성 화자의 권유형을 불필요한 높임말 없이 자연스럽게 복원했다.",
    },
    78: {
      after: "아아, 그런 뱀의 눈총을 받으며\n꽉 조여지고 싶어!",
      category: "meaning_naturalness",
      reason: "수동형 睨まれてシメあげられたい의 피학적 농담이 자연스럽게 전달되도록 교정했다.",
    },
    82: {
      after: "코핀 레이스는\n출전하는 코핀에게 코인을 걸고――<$0C>１위를 차지할 코핀을\n맞혀서\n배당을 받는 게임입니다<$0C>코핀 레이스 중에는\nWii 리모컨을 흔들어\n코핀을 응원할 수 있습니다<$0C>응원받은 코핀은\n빠르게 달리려 합니다<$0C>하지만 코핀에게는 스태미나가 있어\n스태미나가 떨어지면\n앉아서 쉬려고 합니다<$0C>이때는\n응원해도 효과가 없으니\n주의해 주세요<$0C>코핀 레이스 설명은 여기까지입니다",
      category: "numeric_fidelity_terminology",
      reason: "원문의 전각 숫자 １을 복원하고 출주를 자연스러운 게임 용어인 출전으로 교정했다.",
    },
    88: {
      after: "하지만 서로 적과 아군으로 갈리면\n나라면 슬플 것 같아서……",
      category: "meaning_naturalness",
      reason: "敵と味方になってしまって가 양측으로 갈라진다는 의미임을 명확히 했다.",
    },
    93: {
      after: "아니, 뭐 그 정도까지야",
      category: "speaker_voice",
      reason: "겸연쩍게 받아치는 남성 화자의 어조를 자연스럽게 다듬었다.",
    },
    101: {
      after: "여기에는 분명\n복잡하게 굽이진 후미가 있었을 텐데.\n지금은 볼일 없어",
      category: "lexical_accuracy",
      reason: "入り組んだ入り江를 지형 문맥에 맞는 복잡하게 굽이진 후미로 구체화했다.",
    },
    102: {
      after: "투기장 설명２",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 ２를 보존했다.",
    },
    104: {
      after: "여자애라면\n여기 제대로 있잖아.\n신비로운 미소녀가 ２명이나",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 ２를 보존했다.",
    },
    115: {
      after: "여긴 마치 거대한 계단 같네.\n산호층과 산호층이 이어져 있으니까",
      category: "lexical_naturalness",
      reason: "珊瑚の棚를 직역한 선반 대신 지형을 나타내는 산호층으로 교정했다.",
    },
    118: {
      after: "그건 성지 노와레를\n여는 열쇠인 ９체의 로그레스다",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 ９를 보존했다.",
    },
    120: {
      after: "여기 화면 오른쪽 위에\n정보 표시가 뜨게 되어 있으니\n착륙할 수 있을 것 같으면<$0C><$15>10을 누르면\n나머지는 비광정이 알아서\n착륙 절차에 들어가 줄 거야",
      category: "meaning_ui",
      reason: "ここんとこの를 시간 부사인 요즘으로 오역한 부분을 화면상의 위치를 가리키도록 바로잡았다.",
    },
    130: {
      after: "투기장 설명２２",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 ２２를 보존했다.",
    },
    144: {
      after: "절로 고개가 숙여지는 마음임다",
      category: "spelling",
      reason: "오타가 난 종결형을 니콜의 말투를 유지한 채 교정했다.",
    },
    168: {
      after: "우리나라 군대를 지휘하는\n장군 중 １명이야",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 １을 보존했다.",
    },
    183: {
      after: "이렇게 된 이상……\n형님～～～\n형님도 같이 당해 주십쇼!",
      category: "context_meaning",
      reason: "의상 소동 문맥의 道連れ를 실제 죽음이 아니라 같은 곤경에 끌어들이는 농담으로 바로잡았다.",
    },
    191: {
      after: "고양이? 고양이 정도야\n어디에나 있잖아?\n드문 거야?",
      category: "lexical_accuracy",
      reason: "珍しい를 신기하다는 감상보다 희귀 여부를 묻는 말로 정확히 옮겼다.",
    },
    199: {
      after: "요충지?　천연인 거야?",
      category: "wordplay",
      reason: "ヨウショウ을 무의미한 음사로 두지 않고 직전의 要衝과 天然을 잇는 말장난이 보이도록 교정했다.",
    },
  },
  batch_0035: {
    3: {
      after: "투기장 설명１２",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 １２를 보존했다.",
    },
    7: {
      after: "자, 사쥬 군",
      category: "context_naturalness",
      reason: "발언 순서를 넘겨주는 どうぞ를 과도하게 풀어 쓰지 않고 장면에 맞는 짧은 호명으로 다듬었다.",
    },
    43: {
      after: "모른다.\n동료들 사이를 흐트러뜨리지 말고 입어라――\n라며 ２명에게 협박당해서 말이지",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 ２를 보존했다.",
    },
    47: {
      after: "월드 스크립트６０",
      category: "numeric_fidelity_terminology",
      reason: "고정 용어 월드 스크립트를 유지하면서 원문의 전각 숫자 ６０을 복원했다.",
    },
    58: {
      after: "레슬리, 세실――고마워.\n２명에게는 언제나 도움만 받고 있어",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 ２를 보존했다.",
    },
    74: {
      after: "어떤 ２명 남자의 관계에 관해.\n그들의 정체는 과연?",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 ２를 보존했다.",
    },
    76: {
      after: "１명이서, ３명 몫은 걸었어",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 １과 ３을 모두 보존했다.",
    },
    83: {
      after: "왜?\n한번 들어 보고 싶은데.\n대답에 따라서는――",
      category: "naturalness",
      reason: "聞かせてもらいたい의 요청을 자연스러운 한국어 구어체로 다듬었다.",
    },
    89: {
      after: "아델이 디바였다니 말이야!\n확실히 신비로운 느낌은\n있었으려나〜? 그렇지! 리피아!",
      category: "line_breaks_naturalness",
      reason: "원문의 3행 구조는 유지하면서 한국어 단어가 행 사이에서 끊긴 문제를 해소했다.",
    },
    101: {
      after: "응.\n다른 사람의 마음을 받아들여야\n진정한 용사님이니까",
      category: "glossary_terminology",
      reason: "勇者의 고정 번역을 용자로 쓰지 않고 용사로 통일했다.",
    },
    121: {
      after: "그런가.\n하지만 １명이서 끙끙 앓을 바에는\n이야기해라. 언제든 괜찮다",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 １을 보존했다.",
    },
    143: {
      after: "에〜!　진짜임까!?",
      category: "speaker_voice",
      reason: "ニコル의 っス체를 반영하되 잘못 축약된 표현을 자연스러운 캐릭터 말투로 교정했다.",
    },
    148: {
      after: "기본적으로는…… 아니다.\n소속돼 있던 적도\n있기는 하지만",
      category: "naturalness",
      reason: "재적이라는 문어적 직역을 대화에 자연스러운 소속 표현으로 바꿨다.",
    },
    158: {
      after: "이 녀석이 사신이면 난 어떤 신이지?\n미와 사랑의 화신으로\n떠받들어져야 하잖아?",
      category: "naturalness",
      reason: "何神様의 익살스러운 질문을 부자연스러운 신님 직역 없이 자연스럽게 다듬었다.",
    },
    180: {
      after: "그러니까 상대와\n대등해지라는 거야?",
      category: "naturalness",
      reason: "互角になれ를 한국어 대화에 자연스러운 대등해지다로 교정했다.",
    },
    200: {
      after: "투기장 설명１８",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 １８을 보존했다.",
    },
  },
  batch_0036: {
    5: {
      after: "소니아 씨는 매력적이야.\n１명으로 두기에는 아까워――",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 １을 보존했다.",
    },
    19: {
      after: "２분 모두 잘 어울립니다",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 ２를 보존했다.",
    },
    20: {
      after: "당신은 정말 강운의 소유자네.\nQED에게 습격당했다 싶더니\n그 바이스 덕분에 목숨을 건지고――",
      category: "grammar_naturalness",
      reason: "목숨을 구원받는다는 부자연스러운 결합을 목숨을 건지다로 교정했다.",
    },
    32: {
      after: "아름다운 아침이기도 했습니다",
      category: "naturalness",
      reason: "朝の綺麗な日의 수식 관계를 자연스러운 한국어 어순으로 정리했다.",
    },
    40: {
      after: "전사에게도 휴식은 필요하다, 이건가",
      category: "naturalness",
      reason: "인용된 말을 되새기는 か의 어감을 자연스러운 독백으로 다듬었다.",
    },
    44: {
      after: "나는 너도\n충분히 신뢰하고 있는데?",
      category: "speaker_voice_naturalness",
      reason: "つもりだが의 반문을 부자연스러운 생각한다만 대신 자연스러운 대화체로 교정했다.",
    },
    48: {
      after: "제멋대로 굴\n생각은 아니었는데",
      category: "meaning",
      reason: "わがまま를 단순한 고집보다 제멋대로 구는 행동으로 정확히 옮겼다.",
    },
    64: {
      after: "뭐, 내 경우에는\n상사 대우일 뿐이지만 말이야",
      category: "line_breaks_naturalness",
      reason: "원문의 2행 구조는 유지하면서 한국어 조사가 행 끝에서 어색하게 분리된 문제를 바로잡았다.",
    },
    69: {
      after: "그런 거 아냐, 아냐.\n오해하지 마, 리피아",
      category: "meaning",
      reason: "ならない를 금지 표현으로 오역한 부분을 앞선 추측을 부정하는 말로 복원했다.",
    },
    71: {
      after: "흐〜응\n나쁘진 않지?",
      category: "naturalness",
      reason: "이중 부정으로 어색해진 문장을 자연스러운 반문형으로 다듬었다.",
    },
    81: {
      after: "이건 왠지 아주 오래된 시대의\n옷 같네.\n그런 느낌 안 들어?",
      category: "naturalness",
      reason: "옛날 시대라는 중복 표현을 자연스럽게 다듬었다.",
    },
    89: {
      after: "구전 문학이라고 해야 할까요\n사람의 입에서 입으로 전해진\n옛날이야기라고 합니다",
      category: "terminology",
      reason: "口承文学의 통용 한국어 용어를 구전 문학으로 교정했다.",
    },
    102: {
      after: "후후, 그건 좋군.\n훌륭한 병사는 온갖 상황에 몸담고\n적응하는 법이다",
      category: "naturalness",
      reason: "あらゆる状況に身を置き를 한국어 관용에 맞게 다듬었다.",
    },
    119: {
      after: "전에 １명만 따로 따돌림당했으니\n그만큼 되찾으려는 거겠지",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 １을 보존했다.",
    },
    134: {
      after: "라르크, 너도 그래?\n지금 리피아의 이런 느낌이\n마니아한테는 못 견디게 좋은 거야?",
      category: "naturalness",
      reason: "たまらない를 참을 수 없다는 직역 대신 너무 좋다는 문맥의 반문으로 다듬었다.",
    },
    135: {
      after: "투기장 설명１７",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 １７을 보존했다.",
    },
    156: {
      after: "그건 사관학교\n제복 같진 않네",
      category: "naturalness",
      reason: "조사가 어색하게 중복된 문장을 원문의 2행 구조 안에서 자연스럽게 다듬었다.",
    },
    198: {
      after: "그건 말이지, 눈 위에서는\n사람은 외모의 귀여움이\n３할 늘기 때문입니다",
      category: "grammar_numeric_fidelity",
      reason: "원문의 전각 숫자 ３은 유지하면서 주어가 중복된 비문을 교정했다.",
    },
  },
};

for (const [batch, changes] of Object.entries(reviewSets)) {
  const sourcePath = path.join(__dirname, "tm_v2", "batches", "source", `${batch}.jsonl`);
  const draftPath = path.join(__dirname, "drafts", `${batch}.jsonl`);
  const reviewedPath = path.join(__dirname, "reviewed", `${batch}.jsonl`);
  const reviewPath = path.join(__dirname, "reviews", `${batch}_review.json`);
  const readRows = (file) => fs.readFileSync(file, "utf8").split(/\r?\n/).filter(Boolean).map(JSON.parse);
  const sourceRows = readRows(sourcePath);
  const draftRows = readRows(draftPath);
  const modifications = [];

  for (const [indexText, change] of Object.entries(changes)) {
    const index = Number(indexText);
    const sourceRow = sourceRows[index - 1];
    const draftRow = draftRows[index - 1];
    modifications.push({
      index,
      tm_id: sourceRow.tm_id,
      source_text: sourceRow.source_text,
      before: draftRow.translation_ko,
      after: change.after,
      category: change.category,
      reason: change.reason,
    });
    draftRow.translation_ko = change.after;
  }

  fs.mkdirSync(path.dirname(reviewedPath), { recursive: true });
  fs.mkdirSync(path.dirname(reviewPath), { recursive: true });
  fs.writeFileSync(reviewedPath, `${draftRows.map((row) => JSON.stringify(row)).join("\n")}\n`, "utf8");
  const report = {
    schema: "arf-translation-independent-review-v1",
    batch_id: batch,
    reviewer: "/root/translate_batch_0008",
    draft_translator: "/root/audit_boundary_integration",
    draft_author: "/root/audit_boundary_integration",
    independent_review: true,
    translation_engine_policy: "Codex internal models only",
    external_translation_services_used: [],
    external_translation_models_or_apis_used: [],
    source: `work/translation/tm_v2/batches/source/${batch}.jsonl`,
    draft: `work/translation/drafts/${batch}.jsonl`,
    reviewed_output: `work/translation/reviewed/${batch}.jsonl`,
    reviewed_units: draftRows.length,
    modified_units: modifications.length,
    unchanged_units: draftRows.length - modifications.length,
    review_dimensions: [
      "meaning",
      "function",
      "numeric fidelity",
      "proper nouns",
      "natural Korean",
      "speaker voice",
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
  process.stdout.write(`${JSON.stringify({ batch, reviewed: draftRows.length, modified: modifications.length })}\n`);
}
