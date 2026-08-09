const fs = require("fs");
const path = require("path");

const reviewer = "/root/translate_batch_0008";
const draftAuthor = "/root/translate_batch_0009";

const reviews = {
  batch_0055: {
    9: {
      text: "……그래. 이걸 열 수 있다면\nＱＥＤ의 정체와 성황과 내통하는\n현직 원로원 의원의 정체",
      category: "format_fidelity",
      reason: "원문의 전각 표기 'ＱＥＤ'를 그대로 복원했다.",
    },
    10: {
      text: "부디 내게 힘을 빌려 줘",
      category: "grammar",
      reason: "보조 용언의 띄어쓰기를 바로잡았다.",
    },
    28: {
      text: "돈으로 샀어.\n난 아버지 죽음의 진상을 알기 위해\nＱＥＤ와 접촉하고 싶었거든",
      category: "format_fidelity",
      reason: "원문의 전각 표기 'ＱＥＤ'를 그대로 복원했다.",
    },
    29: {
      text: "대찬성이야. 사람 돕기――\n아니, 미라 돕기는\n용사의 길에서 기본이지",
      category: "grammar",
      reason: "'용사의 길의 기본'이라는 중복 조사를 자연스럽게 다듬었다.",
    },
    32: {
      text: "……라군 상사.\n넌 알스 님의 신하이자\n친구이기도 하지 않나",
      category: "function",
      reason: "상대가 알스의 친구임을 확인하는 수사 의문문의 기능을 살렸다.",
    },
    36: {
      text: "너 따위는 형님이 나설\n필요도 없어!",
      category: "naturalness",
      reason: "형님을 번거롭게 할 가치도 없다는 도발을 자연스러운 한국어로 다듬었다.",
    },
    41: {
      text: "알 것 같기도 하고\n아닌 것 같기도 하고……",
      category: "grammar",
      reason: "이해한 듯하면서도 확신하지 못하는 양면적인 반응을 자연스럽게 정리했다.",
    },
    53: {
      text: "이제 됐어…… 그만해.\n당장 여기서 사라지고 싶어져",
      category: "naturalness",
      reason: "당혹감 때문에 자리를 피하고 싶어진다는 대사를 자연스러운 구어체로 다듬었다.",
    },
    63: {
      text: "……그럴지도. 아아, 아쉽네.\n여긴 망자들이 많을 것 같아서\n내 말도 늘릴 수 있었는데",
      category: "meaning",
      reason: "망자를 자신의 말로 늘릴 수 있었을 것이라는 가능 의미를 정확히 살렸다.",
    },
    64: {
      text: "힐베르트는 지상에 남겨진 백성의\n탄식이 남은 도시",
      category: "word_choice",
      reason: "버려진 백성의 슬픔과 탄식을 뜻하는 '嘆き'를 문맥에 맞게 바로잡았다.",
    },
    69: {
      text: "모른다 이거지. 그렇겠지.\n아무것도 모르는 꼭두각시가\n놈들에게는 편할 테니까",
      category: "naturalness",
      reason: "상대의 무지를 비꼬는 어조가 자연스럽게 이어지도록 다듬었다.",
    },
    82: {
      text: "심마프가 부른다느니\n뭐라느니 하면서 멋대로\n용박탑 쪽으로 가 버려서……",
      category: "meaning",
      reason: "비틀거렸다는 뜻이 아니라 목적 없이 제멋대로 가 버렸다는 의미를 살렸다.",
    },
    99: {
      text: "차…… 창피하니까\n통신…… 끊겠슴다!",
      category: "speaker_voice",
      reason: "겁먹은 모습을 보이는 것이 창피하다는 뜻과 니콜의 말투를 자연스럽게 살렸다.",
    },
    108: {
      text: "물어보고 싶었어.\n나 자신을 믿게 해 보라는\n그 말에 답할 수 있었는지",
      category: "meaning",
      reason: "상대의 요구에 자신이 부응했는지를 묻는 의미를 보완했다.",
    },
    119: {
      text: "강 건너편으로 향하는\n산길을 알고 있다.\n상당히 위험한 길이지만",
      category: "meaning",
      reason: "목적지가 단순한 맞은편이 아니라 강의 대안임을 문맥에 맞게 명확히 했다.",
    },
    120: {
      text: "한 발짝 모자랐군.\n미안하다, 라르크",
      category: "naturalness",
      reason: "승부에서 아주 조금 미치지 못했다는 관용 표현을 자연스럽게 다듬었다.",
    },
    121: {
      text: "그…… 그건 그렇지만……\n그래도…… 있잖슴까\n저는 후방 지원에 맞는 편이랄까……",
      category: "naturalness",
      reason: "후방 지원에 적합하다는 뜻을 니콜의 말투에 맞는 자연스러운 표현으로 고쳤다.",
    },
    135: {
      text: "레슬리가 １순위라는 녀석도 있어",
      category: "naturalness",
      reason: "가장 좋아한다는 뜻을 자연스럽게 다듬고 전각 숫자 '１'을 보존했다.",
    },
    137: {
      text: "사쥬, 나를 아버지에 대한\n신뢰로 대한다고 했었지",
      category: "meaning",
      reason: "사쥬가 라르크를 대하는 근거가 렉스에 대한 신뢰라는 관계를 바로잡았다.",
    },
    142: {
      text: "！ 아……\n고맙다, 사쥬",
      category: "meaning",
      reason: "놀람 뒤에 이어지는 감탄을 동의 표현으로 오해하지 않도록 바로잡았다.",
    },
    161: {
      text: "눈치 없는 목석이라 미안하네",
      category: "word_choice",
      reason: "연애 감정에 둔감한 사람을 뜻하는 '朴念仁'의 의미를 살렸다.",
    },
    177: {
      text: "적전 도주와 반역죄 혐의를 받고 있다.\n자, 너희는 어서 가라!",
      category: "meaning",
      reason: "화자가 두 죄목으로 문책받는 상태라는 피동 관계를 바로잡았다.",
    },
    195: {
      text: "모두를 괴롭게 했는데……\n나, 행복하다는 생각이 들어",
      category: "naturalness",
      reason: "죄책감 속에서도 행복을 느끼고 만다는 고백을 자연스럽게 다듬었다.",
    },
  },
  batch_0056: {
    11: {
      text: "걱정할 필요 없어.\n그 녀석은 틀림없이 레온이야",
      category: "grammar",
      reason: "레온임이 틀림없다는 단정이 자연스럽게 성립하도록 문장을 바로잡았다.",
    },
    51: {
      text: "그렇군\n신종도 결국 신의 버림패인가",
      category: "word_choice",
      reason: "희생시키고 버리는 말이라는 뜻의 '捨てゴマ'를 자연스러운 한국어로 고쳤다.",
    },
    66: {
      text: "자, 라르크.\n이제 슬슬 모두를 모으자",
      category: "grammar",
      reason: "사람들을 불러 모은다는 목적격 관계를 바로잡았다.",
    },
    79: {
      text: "사람의 미래를 사람의 손으로 되찾는다는 건\n그런 거잖아",
      category: "grammar",
      reason: "미래를 되찾는 수단을 나타내는 조사를 자연스럽게 바로잡았다.",
    },
    95: {
      text: "나를 신경 쓰지 마라",
      category: "grammar",
      reason: "신경 쓰는 대상을 나타내는 목적격 조사를 바로잡았다.",
    },
    98: {
      text: "……그런가.\n신종과 접촉했군.\n그렇군……",
      category: "meaning",
      reason: "새 사실을 납득하는 'なるほど'를 조건·결론 표현과 구분했다.",
    },
    99: {
      text: "……그럼\n그런 걸로 해 두죠",
      category: "speaker_voice",
      reason: "상대와 거리를 두는 공손한 어조를 종결 표현에 반영했다.",
    },
    108: {
      text: "아, 알겠습니다!",
      category: "meaning",
      reason: "명령을 이해하고 수락하는 '了解'의 기능을 정확히 살렸다.",
    },
    123: {
      text: "미안해.\n내 멋대로 말해서",
      category: "grammar",
      reason: "제멋대로 말한 행동을 사과하는 구어체가 자연스럽게 이어지도록 다듬었다.",
    },
    141: {
      text: "스쿠일도 이렇게\n아름다운 로그레스일까……",
      category: "naturalness",
      reason: "눈앞의 풍경처럼 아름다운지 묻는 비교 표현을 자연스럽게 다듬었다.",
    },
    177: {
      text: "방심해서 선수를 빼앗기면\n용사라는 이름이 울겠다.\n서두르자!!",
      category: "naturalness",
      reason: "남에게 뒤처지면 용사의 명예가 손상된다는 관용적 의미를 살렸다.",
    },
    195: {
      text: "지금 라르크가 계약한\n로그레스는 ３마리.\n이 기세로 계속 가고 싶군",
      category: "naturalness",
      reason: "현재의 좋은 흐름을 유지하고 싶다는 뜻을 자연스럽게 다듬고 전각 숫자를 보존했다.",
    },
  },
  batch_0057: {
    11: {
      text: "그도 그럴 게…… 이사의 아이인 당신이\n정말로 존재했으니까",
      category: "grammar",
      reason: "당신이 실제 이사의 아이라는 주술 관계가 자연스럽게 드러나도록 바로잡았다.",
    },
    27: {
      text: "９마리의 로그레스를 거느렸을 때\n이사신이 계신\n성지 노와레에 이르게 된다",
      category: "grammar",
      reason: "수량 표현과 목적어의 관계를 자연스럽게 다듬고 전각 숫자 '９'를 보존했다.",
    },
    31: {
      text: "그러니까 １순위니\n뭐니 하는 게 아니라니까!",
      category: "naturalness",
      reason: "가장 좋아하는 사람의 순위를 부정하는 문맥에 맞게 다듬고 전각 숫자를 보존했다.",
    },
    39: {
      text: "이 앞은 신성한 곳이므로\n디바께서 필요하다고 생각하는 분만\n데려가 주십시오",
      category: "meaning",
      reason: "동행자의 필요 여부를 판단하는 주체가 디바임을 명확히 했다.",
    },
    46: {
      text: "뭐라고!?\n이 자식, １번만 더 말해 봐!!",
      category: "numeric_fidelity",
      reason: "한 번 더 말하라는 원문의 전각 숫자 '１'을 보존했다.",
    },
    54: {
      text: "자신 있는 검 솜씨만으로는\n어쩌지 못할 일이\n있을지도 모르니까",
      category: "naturalness",
      reason: "자랑으로 삼는 검술 실력을 뜻하는 표현을 자연스럽게 다듬었다.",
    },
    56: {
      text: "그걸로 기운을 채웠으면\n신을 자칭하는 돌인가 뭔가를\n숭배하러 가자<$15>00",
      category: "meaning",
      reason: "신을 자칭하는 돌을 보러 가는 것이 아니라 숭배하러 간다는 비꼬는 어조를 살렸다.",
    },
    86: {
      text: "이번 싸움이 끝나고\n여러 가지에 매듭을 지으면……\n내 마음속 １순위도 바뀌려나.",
      category: "naturalness",
      reason: "마음속에서 가장 중요한 사람의 순위를 뜻하도록 다듬고 전각 숫자를 보존했다.",
    },
    90: {
      text: "지금 라르크가 계약한\n로그레스는 ４마리.\n이 기세로 계속 가고 싶군",
      category: "naturalness",
      reason: "현재의 좋은 흐름을 유지하고 싶다는 뜻을 자연스럽게 다듬고 전각 숫자를 보존했다.",
    },
    92: {
      text: "시엘, 리피아를 부탁한다.\n우리의 단 １명인 딸이니까……",
      category: "grammar",
      reason: "외동딸을 나타내는 수량 표현의 중복을 줄이면서 전각 숫자를 보존했다.",
    },
    96: {
      text: "그 펜던트를\n넘겨주시겠나",
      category: "speaker_voice",
      reason: "상대를 압박하며 물건을 요구하는 공손하면서도 위협적인 어조를 살렸다.",
    },
    108: {
      text: "정말, 그러다간\n알스에게 선수를 빼앗길걸?",
      category: "meaning",
      reason: "단순 추월이 아니라 알스가 먼저 목적을 달성할 수 있다는 의미를 살렸다.",
    },
    115: {
      text: "당신이 말한 『확증』이\n되지는 않을지도 모르지만\n한 가지 확실한 게 있어",
      category: "grammar",
      reason: "확증이 되지 않을 수도 있다는 서술 관계가 자연스럽게 이어지도록 바로잡았다.",
    },
    135: {
      text: "뭐…… 뭐야…… 방금 건……",
      category: "meaning",
      reason: "방금 본 현상에 놀라 묻는 대사를 회상 표현으로 오해하지 않도록 바로잡았다.",
    },
    140: {
      text: "오늘은 그겁니까? 알스 전하를 모시고\n사령관께 승전 보고라도 하러 왔슴까?",
      category: "word_choice",
      reason: "전투 승리를 보고한다는 뜻의 '戦勝報告'를 '승전 보고'로 바로잡았다.",
    },
    150: {
      text: "아니, 나도 군에 몸담은 사람이야.\n민간인을 죽게 내버려 둘 수는 없어",
      category: "grammar",
      reason: "화자가 군인이라는 첫 문장을 완결된 자연스러운 한국어로 다듬었다.",
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
