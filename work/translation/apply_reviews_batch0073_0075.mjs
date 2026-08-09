import fs from "node:fs";
import path from "node:path";

const root = path.resolve("work/translation");

const reviews = {
  batch_0073: [
    {
      index: 2,
      after: "……모략으로 사람을 함정에 빠뜨리는 건\n어머니를 닮았나",
      category: "naturalness",
      reason: "성향이 어머니에게서 이어졌다는 '母親譲り'를 자연스러운 한국어 표현으로 다듬었다.",
    },
    {
      index: 9,
      after: "침입자다!\n지하 감옥에 도적이 침입했다!",
      category: "word_choice",
      reason: "침입자를 가리키는 '賊'을 문맥에 맞는 '도적'으로 바로잡았다.",
    },
    {
      index: 13,
      after: "다들 용옥석을 차고 있지 않아?",
      category: "naturalness",
      reason: "신체에 착용하는 용옥석의 동사를 자연스러운 '차다'로 다듬었다.",
    },
    {
      index: 37,
      after: "쫓아가지 않아도 괜찮슴까, 형님",
      category: "speaker_voice",
      reason: "니콜의 말투를 유지하면서도 오타처럼 보이던 종결 표현을 자연스럽게 고쳤다.",
    },
    {
      index: 83,
      after: "메리디아 제국군과는 아무 인연도 없다는\n표정을 지어 두는 게 안전해",
      category: "grammar",
      reason: "부자연스러운 '아무 연도'를 '아무 인연도'로 바로잡았다.",
    },
    {
      index: 89,
      after: "그런 식으로 말하지 마.\n투레밀리아에서 우리 제국까지\n여자 １명 혼자서는 힘들었을 거야",
      category: "grammar",
      reason: "전각 숫자 '１'을 보존하면서 '１명이서는'의 잘못된 조사를 자연스럽게 고쳤다.",
    },
    {
      index: 93,
      after: "오늘 저녁, 더글러스 경 부인의\n처형이 집행되기로\n결정됐습니다",
      category: "meaning",
      reason: "처형이 오늘 저녁부터 지속된다는 뜻이 아니라 그 시각에 집행된다는 의미를 명확히 했다.",
    },
    {
      index: 115,
      after: "OK〜!\n브레이브 세실호라면\n금방이야!",
      category: "orthography",
      reason: "문체 가이드에 따라 전각 영문 약어 'ＯＫ'를 반각 ASCII 'OK'로 정규화했다.",
    },
    {
      index: 137,
      after: "그래. 게다가 이건\n진실을 알 기회일지도 몰라",
      category: "line_breaks",
      reason: "조사와 의미 덩어리가 어색하게 끊기지 않도록 두 줄 구조 안에서 줄바꿈을 조정했다.",
    },
    {
      index: 160,
      after: "그보다 리피아의 아빠가 심마프라면\n앞뒤가 안 맞지 않아?",
      category: "idiom",
      reason: "나이와 시간 관계가 맞지 않는다는 뜻의 '計算が合わない'를 자연스러운 관용 표현으로 옮겼다.",
    },
    {
      index: 171,
      after: "용옥석?\n탁룡에게서 채취되는 돌멩이 말이야?",
      category: "word_choice",
      reason: "자원이나 광물을 얻는다는 '採れる'의 뜻을 '채취되다'로 명확히 했다.",
    },
    {
      index: 175,
      after: "자, 가자. 너희 ２명 다",
      category: "grammar",
      reason: "전각 숫자 '２'를 보존하면서 호격 표현을 자연스럽게 고쳤다.",
    },
    {
      index: 178,
      after: "카메라 보간 전환　OFF\n",
      category: "terminology",
      reason: "카메라 처리 용어 '補完'을 문맥에 맞는 '보간'으로 바로잡았다.",
    },
    {
      index: 184,
      after: "아직 명령서가 도착하지 않은\n것이라 해도 이대로는\n시간에 맞출 수 있을지 모르겠군",
      category: "naturalness",
      reason: "기한에 맞출 수 있는지를 뜻하는 '間に合う'를 자연스럽게 다듬었다.",
    },
  ],
  batch_0074: [
    {
      index: 12,
      after: "으헤…… 기다려 주세요.\n그럼 적어도 세수라도 하고\n기분 전환 좀 하게 해 주세요",
      category: "meaning",
      reason: "화자 자신이 기분을 전환하겠다는 의미가 드러나도록 사역 관계를 바로잡았다.",
    },
    {
      index: 17,
      after: "니콜. 힘내자.\n아델은 １명 혼자라 마음이\n불안할 거야",
      category: "grammar",
      reason: "전각 숫자 '１'을 보존하면서 '１명이서'의 잘못된 조사를 자연스럽게 고쳤다.",
    },
    {
      index: 25,
      after: "난 왜 지금 이렇게\n누나와 이야기하고 있는 걸까?",
      category: "naturalness",
      reason: "스스로 대화의 목적을 되묻는 독백을 자연스러운 한국어 어순으로 다듬었다.",
    },
    {
      index: 30,
      after: "어머, 사쥬.\n그렇게 큰 그릇은 대체\n어디에 숨겨 둔 거야?",
      category: "idiom",
      reason: "도량을 뜻하는 비유적 '器'가 한국어에서도 자연스럽게 읽히도록 표현을 다듬었다.",
    },
    {
      index: 36,
      after: "형님. 옥좌를 찬탈하겠습니다",
      category: "terminology",
      reason: "황제의 자리인 '玉座'를 프로젝트의 기존 표기인 '옥좌'로 통일했다.",
    },
    {
      index: 70,
      after: "으아아――――!",
      category: "speaker_voice",
      reason: "거친 비명인 'ぎゃああ'의 강도를 성별을 불필요하게 특정하지 않는 감탄사로 살렸다.",
    },
    {
      index: 75,
      after: "대단해!\n『조수』가 빠졌구나?",
      category: "word_choice",
      reason: "직전에 배운 해수면 변화 개념인 '潮'를 설정 설명과 일치하는 '조수'로 옮겼다.",
    },
    {
      index: 80,
      after: "이벤트\n이벤트 캐릭터 삭제",
      category: "terminology",
      reason: "개발용 객체명 'イベント君'을 같은 계열 문자열과 일치하도록 '이벤트 캐릭터'로 통일했다.",
    },
    {
      index: 105,
      after: "라군 공께서는 당분간\n여관에서 기다려 주십시오.\n숙박 절차는 이쪽에서 처리하겠습니다",
      category: "honorifics",
      reason: "높임 조사와 명령형을 공식 안내 장면에 맞게 일관되게 다듬었다.",
    },
    {
      index: 110,
      after: "어머님은 심마프라면\n그것을 위한 길을\n알려 줄 거라고 하셨어",
      category: "meaning",
      reason: "물리적인 특정 장소가 아니라 목적을 이루는 방도를 뜻하는 원문의 범위를 복원했다.",
    },
    {
      index: 116,
      after: "이매지널의 섭리를 이사신에게\n제시해야 하는 거지?",
      category: "word_choice",
      reason: "섭리를 신에게 내보인다는 '出す'를 설정 문맥에 맞는 '제시하다'로 명확히 했다.",
    },
    {
      index: 130,
      after: "저쪽이니 이쪽이니 하지 말고\n좀 더 제대로\n설명할 수는 없어!?",
      category: "line_breaks",
      reason: "원문의 세 줄 수를 지키면서 한국어 의미 덩어리에 맞게 줄바꿈과 어순을 다듬었다.",
    },
    {
      index: 162,
      after: "……동생?\n형이라고 해야 하는 거 아니야?",
      category: "naturalness",
      reason: "동생과 형을 정정하는 반문이 자연스럽게 전달되도록 고쳤다.",
    },
    {
      index: 167,
      after: "내버려 두면 비광정을 움직여서\n１명 혼자 가 버릴 것 같아.\n빨리 쫓아가자",
      category: "grammar",
      reason: "전각 숫자 '１'을 보존하면서 '１명이서'의 잘못된 조사를 바로잡았다.",
    },
  ],
  batch_0075: [
    {
      index: 0,
      after: "밀림이라면 분명 벌레 같은 것도\n잔뜩 있을 검다.\n싫은데……",
      category: "speaker_voice",
      reason: "니콜의 말투를 살리고 '싫다'로 끊긴 독백을 자연스럽게 다듬었다.",
    },
    {
      index: 22,
      after: "그건 리피아도\n마찬가지 아니야?\n２명이나 짜증 내서 어쩌자는 거야",
      category: "grammar",
      reason: "전각 숫자 '２'를 보존하면서 '２명이서'의 어색한 조사를 자연스럽게 고쳤다.",
    },
    {
      index: 31,
      after: "웃기지 마! 비겁한 수단으로\n옥좌를 손에 넣어도\n알스 님은 기뻐하지 않으신다!",
      category: "terminology",
      reason: "황제의 자리인 '玉座'를 프로젝트의 기존 표기인 '옥좌'로 통일했다.",
    },
    {
      index: 35,
      after: "그러고 보니\n리피아도 용옥석을 차고 있었지.\n그럼 너도 신종이야?",
      category: "naturalness",
      reason: "신체에 착용하는 용옥석의 동사를 자연스러운 '차다'로 다듬었다.",
    },
    {
      index: 39,
      after: "그나저나 투레밀리아에는\n이상한 풍습이 있네.\n용옥석을 몸에 붙이다니",
      category: "word_choice",
      reason: "용옥석이 신체에 부착된다는 설정이 드러나도록 착용 동사를 바로잡았다.",
    },
    {
      index: 43,
      after: "형님까지 너무하심다.\n전 임무를 제대로 수행했슴다",
      category: "speaker_voice",
      reason: "니콜 특유의 말투를 유지하면서 문법적으로 어색한 종결을 다듬었다.",
    },
    {
      index: 51,
      after: "……어, 어쨌든\n이제 앞으로 갈 수 있을 것 같네",
      category: "speaker_voice",
      reason: "말을 더듬는 원문의 호흡을 한국어 감탄사와 자연스럽게 맞췄다.",
    },
    {
      index: 73,
      after: "절친한 친구의 위기를 모른 척할 수는\n없지",
      category: "meaning",
      reason: "'親友'의 가까운 관계를 단순한 친구보다 명확하게 살렸다.",
    },
    {
      index: 96,
      after: "아항. 알겠어.\n라르크는 신을 살려 둔 채\n죽일 생각이구나",
      category: "speaker_voice",
      reason: "능글맞게 깨달음을 나타내는 'あはん'의 억양을 자연스럽게 살렸다.",
    },
    {
      index: 120,
      after: "여기가 가우스 지하도야?\n딱 봐도 분위기 있네.\n두근거리기 시작했어♪",
      category: "naturalness",
      reason: "탐험 장소다운 분위기에 들뜬 화자의 감정이 이어지도록 다듬었다.",
    },
    {
      index: 121,
      after: "이제 누구에게도 아무것도 빼앗기지 않을 거야!",
      category: "naturalness",
      reason: "더는 자신의 것을 빼앗기지 않겠다는 결의를 자연스러운 피동 표현으로 다듬었다.",
    },
    {
      index: 127,
      after: "초록빛이 굉장해…… 가학성 정원과는\n풍경이 완전히 달라. 멋져……",
      category: "naturalness",
      reason: "풍부한 녹음을 보고 감탄하는 대사를 자연스러운 한국어로 다듬었다.",
    },
    {
      index: 149,
      after: "프레이아 장군……\n어떻게 하시겠습니까",
      category: "honorifics",
      reason: "장군에게 방침을 묻는 공식 장면의 높임말을 바로잡았다.",
    },
    {
      index: 164,
      after: "……우린 다친 몸이야.\n일단 토파지온에서 쉬자",
      category: "naturalness",
      reason: "부상당한 상태를 뜻하는 '手負い'를 자연스러운 대사로 다듬었다.",
    },
    {
      index: 183,
      after: "저도 그 소름 끼치는 현종입니다",
      category: "honorifics",
      reason: "정중한 종결과 어울리도록 화자의 일인칭을 '저'로 통일했다.",
    },
    {
      index: 184,
      after: "넌 결함품이 아니야.\n아빠도 늘 널\n눈여겨보고……",
      category: "terminology",
      reason: "설정상 실패작을 비하하는 '出来損ない'를 기존 문맥의 '결함품'으로 통일했다.",
    },
    {
      index: 192,
      after: "……라르크. 이 세계는 신을\n자처하는 녀석들의 모형 정원이야",
      category: "meaning",
      reason: "신들이 통제하는 축소 세계를 뜻하는 '箱庭'의 비유를 복원했다.",
    },
    {
      index: 196,
      after: "……군에 있으면 이런 말은\n듣는 데 익숙해져",
      category: "naturalness",
      reason: "반복해서 같은 말을 들어 익숙하다는 의미를 자연스럽게 다듬었다.",
    },
    {
      index: 199,
      after: "어머님께 함구하라는 말을 들었어",
      category: "word_choice",
      reason: "비밀을 말하지 말라는 당부인 '口止め'를 과도하게 강압적이지 않은 표현으로 바로잡았다.",
    },
  ],
};

for (const [batchId, changes] of Object.entries(reviews)) {
  const sourceRel = `tm_v2/batches/source/${batchId}.jsonl`;
  const draftRel = `drafts/${batchId}.jsonl`;
  const reviewedRel = `reviewed/${batchId}.jsonl`;
  const reviewRel = `reviews/${batchId}_review.json`;
  const draftRows = fs.readFileSync(path.join(root, draftRel), "utf8").trim().split(/\r?\n/).map(JSON.parse);
  const reviewedRows = draftRows.map((row) => ({ ...row }));
  const modifications = changes.map((change) => {
    const row = reviewedRows[change.index];
    const before = row.translation_ko;
    row.translation_ko = change.after;
    return {
      tm_id: row.tm_id,
      source_text: row.source_text,
      before,
      after: change.after,
      category: change.category,
      reason: change.reason,
    };
  });

  fs.mkdirSync(path.join(root, "reviewed"), { recursive: true });
  fs.mkdirSync(path.join(root, "reviews"), { recursive: true });
  fs.writeFileSync(
    path.join(root, reviewedRel),
    reviewedRows.map((row) => JSON.stringify(row)).join("\n") + "\n",
    "utf8",
  );

  const report = {
    schema: "arf-translation-independent-review-v1",
    batch_id: batchId,
    reviewer: "/root/translate_batch_0009",
    draft_translator: "/root/review_batch_0058_0060",
    draft_author: "/root/review_batch_0058_0060",
    independent_review: true,
    translation_engine_policy: "Codex internal models only",
    external_translation_services_used: [],
    external_translation_models_or_apis_used: [],
    source: `work/translation/${sourceRel}`,
    draft: `work/translation/${draftRel}`,
    reviewed_output: `work/translation/${reviewedRel}`,
    reviewed_units: reviewedRows.length,
    modified_units: modifications.length,
    unchanged_units: reviewedRows.length - modifications.length,
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
  fs.writeFileSync(path.join(root, reviewRel), JSON.stringify(report, null, 2) + "\n", "utf8");
  console.log(`${batchId} reviewed=${reviewedRows.length} modified=${modifications.length}`);
}
