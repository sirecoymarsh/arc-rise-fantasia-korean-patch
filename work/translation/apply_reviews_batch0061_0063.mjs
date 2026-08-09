import fs from "node:fs";
import path from "node:path";

const root = path.resolve("work/translation");

const reviews = {
  batch_0061: [
    {
      index: 3,
      after: "그도 그럴 게 아델은\n나와 알스의 소꿉친구고……",
      category: "meaning",
      reason: "이유를 덧붙이는 'だって'의 연결 의미를 살렸다.",
    },
    {
      index: 4,
      after: "그렇게 매정한 소릴\n다 하네.\n라르크 군은 반항기인가?",
      category: "line_breaks",
      reason: "원문의 세 줄 구조를 복원하면서 능청스러운 말투를 자연스럽게 다듬었다.",
    },
    {
      index: 15,
      after: "분위기 파악 못 하면 미움받을걸?\n너희 상대는 우리다",
      category: "naturalness",
      reason: "상대에게 분위기를 읽으라고 경고하는 뜻이 자연스럽게 드러나도록 고쳤다.",
    },
    {
      index: 32,
      after: "그렇다면 내 수족에게 이사의 인자를\n심어 새로운 이사의 아이가\n이매지널의 섭리를 선택하게 하겠다!",
      category: "word_choice",
      reason: "'手駒'를 부자연스러운 '장기말' 대신 문맥에 맞는 '수족'으로 다듬었다.",
    },
    {
      index: 63,
      after: "저, 저기. 여기엔 오르키나교의\n디바 암살은 성황의 명령을 받은\nQED의 짓이라고 쓰여 있어",
      category: "proper_noun",
      reason: "용어집의 고정 표기인 ASCII 'QED'로 통일했다.",
    },
    {
      index: 74,
      after: "마하트 폐하께선 누가 독이라도 먹였는지\n몸이 편찮으셔서 말이야",
      category: "meaning",
      reason: "독살 시도를 당했을 가능성을 나타내는 '毒を盛られた'의 피동 의미를 명확히 했다.",
    },
    {
      index: 88,
      after: "……숨을…… 쉴 수 없어……\n괴……로워……",
      category: "spacing",
      reason: "말더듬 표현 안에 잘못 삽입된 공백을 제거했다.",
    },
    {
      index: 91,
      after: "아니. 성황의 선포 없이\n진행되는 일이야",
      category: "word_choice",
      reason: "공식적으로 뜻을 내리는 '宣下'를 문맥에 맞는 '선포'로 바로잡았다.",
    },
    {
      index: 96,
      after: "라르크. 속지 마.\n이 녀석도 필사적으로\n알스가 로그레스를 모으게 했어",
      category: "meaning",
      reason: "로그레스를 모은 주체가 알스이며 상대가 이를 시켰다는 사역 관계를 바로잡았다.",
    },
    {
      index: 106,
      after: "왜 놈들과 함께 있는 거지?\n역시 QED가 관련된 건가",
      category: "proper_noun",
      reason: "용어집의 고정 표기인 ASCII 'QED'로 통일했다.",
    },
    {
      index: 133,
      after: "공중 회랑이 어디 있는지도\n모르면 임무를 논할\n형편도 아니니까",
      category: "meaning",
      reason: "위치를 모르면 임무 자체를 논할 수 없다는 원문의 의미를 정확히 복원했다.",
    },
    {
      index: 173,
      after: "이런, 이런.\n이제야 눈치챘니,\n라르크 군",
      category: "naturalness",
      reason: "상대를 여유롭게 놀리는 의문형 어조를 자연스럽게 다듬었다.",
    },
    {
      index: 189,
      after: "……이 바보 녀석!\n적에게 자비를 베푸는 놈이 어디 있나!",
      category: "word_choice",
      reason: "적에게 연민을 베푼다는 '情けをかける'의 뜻을 명확히 했다.",
    },
  ],
  batch_0062: [
    {
      index: 1,
      after: "응? 모르는 거야?",
      category: "meaning",
      reason: "현재 상대가 알고 있는지를 묻는 원문의 시제를 바로잡았다.",
    },
    {
      index: 4,
      after: "결코 결정화로\n멸망시키려는 게 아니야",
      category: "fidelity",
      reason: "원문에 없는 '세계'를 덧붙이지 않고 의미 범위를 보존했다.",
    },
    {
      index: 69,
      after: "……알스 도련님,\n머리끝까지 화가 났겠지",
      category: "idiom",
      reason: "격분한 상태를 뜻하는 '頭に血が上る'를 자연스러운 한국어 관용 표현으로 옮겼다.",
    },
    {
      index: 83,
      after: "그저 닮은 사람일 뿐인 게 아니라면\n그녀는 셰리 그린힐.\n공화국 원로원 의장이야",
      category: "meaning",
      reason: "단순히 닮은 타인이 아니라면 본인이 셰리라는 조건문의 의미를 바로잡았다.",
    },
    {
      index: 100,
      after: "……어?\n그래, 괜찮지?",
      category: "naturalness",
      reason: "동의를 가볍게 구하는 말투가 자연스럽게 들리도록 다듬었다.",
    },
    {
      index: 120,
      after: "바이스 님!\n뭔가 알고 계시다면 알려 주세요!",
      category: "word_choice",
      reason: "정보를 말해 달라는 '教えて'를 문맥에 맞는 '알려 주세요'로 고쳤다.",
    },
    {
      index: 128,
      after: "형님! 어찌 그런 무례한 말씀을……",
      category: "line_breaks",
      reason: "원문에 없는 줄바꿈을 제거해 한 줄 구조를 복원했다.",
    },
    {
      index: 149,
      after: "유일하게 사랑스러운 미소녀는\n산원숭이 같은 용병만\n쫓아다니고 있으니 말이야",
      category: "word_choice",
      reason: "사랑스럽고 가녀린 인상을 뜻하는 '可憐'을 '가련한'으로 오해한 표현을 바로잡았다.",
    },
    {
      index: 180,
      after: "……난 군의 명령으로 움직여.\n알스가 명령을 철회한다면\n그래도 상관없어",
      category: "meaning",
      reason: "현재 명령을 취소한다는 '撤回命令'을 철수 명령으로 오해하지 않도록 바로잡았다.",
    },
  ],
  batch_0063: [
    {
      index: 20,
      after: "……나…… 당신을……\n좋아했더라면 좋았을 텐데……",
      category: "naturalness",
      reason: "상대를 사랑하지 못한 일을 후회하는 임종 대사를 자연스럽게 다듬었다.",
    },
    {
      index: 33,
      after: "그러려면 ９마리의 로그레스와\n계약해야 해……",
      category: "terminology",
      reason: "로그레스의 수량 표현을 기존 용례인 '마리'로 통일하고 전각 숫자 '９'를 보존했다.",
    },
    {
      index: 45,
      after: "그 말은 일대일 승부에서 이긴 뒤에\n다시 해 주시지",
      category: "meaning",
      reason: "승리한 뒤 같은 말을 다시 하라는 요구의 방향을 바로잡았다.",
    },
    {
      index: 60,
      after: "이매지널신이 어리석은 섭리를\n버릴 생각이 있다면\n대화의 가능성도 있다는 말일 뿐이야",
      category: "grammar",
      reason: "대화 자체의 가능성을 말하는 문장이 자연스럽게 이어지도록 다듬었다.",
    },
    {
      index: 61,
      after: "지적인 안경 미인 칼라일 씨〜♪",
      category: "speaker_voice",
      reason: "사쥬의 길게 늘이는 장난스러운 호칭을 자연스러운 물결표로 살렸다.",
    },
    {
      index: 78,
      after: "그렇겠지.\n극악무도한 제국에 복수를……\n한다는 얘기도 들려",
      category: "word_choice",
      reason: "'悪辣非道'를 자연스러운 한국어 합성 표현인 '극악무도한'으로 다듬었다.",
    },
    {
      index: 109,
      after: "아무것도 모른 채 이매지널을\n선택하도록 강요받았어……",
      category: "meaning",
      reason: "자발적 선택이 아니라 선택을 강요받았다는 '選ばされて'의 사역·피동 의미를 복원했다.",
    },
    {
      index: 111,
      after: "좋아, 에블로 가자",
      category: "proper_noun",
      reason: "용어집에 따라 지명 'エブル'을 '에블'로 바로잡았다.",
    },
    {
      index: 142,
      after: "……화산 활동은\n멈춰 준 모양이군.\n고맙다",
      category: "meaning",
      reason: "화산 자체가 아니라 화산 활동을 멈췄다는 의미를 명확히 했다.",
    },
    {
      index: 150,
      after: "공화국의 전신인 도시국가 연합에\n디바와 QED를 주고",
      category: "proper_noun",
      reason: "용어집의 고정 표기인 ASCII 'QED'로 통일했다.",
    },
    {
      index: 192,
      after: "하지만 QED라는 것에 대해선\n난 모른다",
      category: "proper_noun",
      reason: "용어집의 고정 표기인 ASCII 'QED'로 통일했다.",
    },
    {
      index: 197,
      after: "제국령에서 공화국으로 갈 수 있는 건\n제도에서 허가증을 받은 자뿐으로\n정해져 있다",
      category: "line_breaks",
      reason: "원문의 세 줄 구조를 복원하면서 통행 조건을 완결된 문장으로 다듬었다.",
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
    draft_translator: "/root/audit_boundary_integration",
    draft_author: "/root/audit_boundary_integration",
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
