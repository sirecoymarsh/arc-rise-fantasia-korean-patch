import fs from "node:fs";
import path from "node:path";

const root = path.resolve("work/translation");

const reviews = {
  batch_0082: [
    {
      index: 15,
      after: "그늘에서 ２일이나 두면\n먹기 좋게 익는대요……<$0C>오늘 저녁 식사에는\n늦잖아!",
      category: "naturalness",
      reason: "저녁 식사 때까지 익지 않는다는 뜻의 '間に合わない'를 자연스러운 한국어로 다듬었다.",
    },
    {
      index: 27,
      after: "푸른 눈의 노와레교도",
      category: "terminology",
      reason: "종교 소속을 나타내는 'ノワーレ教徒'를 프로젝트의 기존 표기인 '노와레교도'로 통일했다.",
    },
    {
      index: 58,
      after: "내 생각엔 네 신앙심은\n별로 상관없는 것 같은데",
      category: "naturalness",
      reason: "화자의 견해를 덧붙이는 '俺は'이 자연스럽게 연결되도록 어순을 다듬었다.",
    },
    {
      index: 85,
      after: "레벨１MP　　\n레벨２MP　　\n레벨３MP　　\n레벨４MP　　\n마법 위력: 불 속성\n마법 위력: 물 속성\n마법 위력: 바람 속성\n마법 위력: 땅 속성\n슬롯 수　　　\n최강　　　　　\n초기화　　　　\n그만두기　　　",
      category: "orthography",
      reason: "전각 숫자는 보존하고 문체 가이드에 따라 전각 영문 약어 'ＭＰ'를 반각 ASCII 'MP'로 정규화했다.",
    },
    {
      index: 98,
      after: "에블 유적 D00으로\n",
      category: "proper_noun",
      reason: "용어집의 고정 지명 'エブル'을 '에블'로 바로잡았다.",
    },
    {
      index: 109,
      after: "당신이 레지스탕스의\n새 지도자인가<$0C>카자프에게 자세한 이야기는 들었다.\n――앞으로도 잘 부탁한다",
      category: "terminology",
      reason: "조직명 'レジスタンス'를 프로젝트에서 사용하는 음역 표기 '레지스탕스'로 통일했다.",
    },
    {
      index: 116,
      after: "B랭크 이벤트 샘플을 재생하시겠습니까?",
      category: "orthography",
      reason: "문체 가이드에 따라 전각 영문 'Ｂ'를 반각 ASCII 'B'로 정규화했다.",
    },
    {
      index: 135,
      after: "어머, 도련님……\n누나한테 무슨 볼일이야?<$0C>나도 심심했으니까\n잠깐이라면\n놀아 줄 수도 있어♪",
      category: "meaning",
      reason: "화자가 상대와 놀아 주겠다는 '遊んであげる'의 행위 방향을 바로잡았다.",
    },
    {
      index: 147,
      after: "아까는 덕분에 살았어.\n과연 전설의 용병이라\n불릴 만하군",
      category: "naturalness",
      reason: "상대의 도움으로 위기를 넘겼다는 '助かった'를 자연스러운 감사 표현으로 다듬었다.",
    },
    {
      index: 159,
      after: "화평 회담을 핑계로 한 기습……\n바이스 황태자는 악랄한 분이군요.\n혈육의 손에 죽은 것도 무리는 아닙니다",
      category: "word_choice",
      reason: "가족에게 죽임을 당했다는 '肉親に討たれる'를 자연스럽고 정확하게 옮겼다.",
    },
    {
      index: 165,
      after: "그 바이스 전하가\n바닷속으로 사라졌다니……\n도저히 믿을 수 없어",
      category: "idiom",
      reason: "바다에서 죽거나 사라진다는 '海の藻屑に消える'를 자연스러운 관용 표현으로 다듬었다.",
    },
    {
      index: 172,
      after: "에블이 더럽혀지고\n바트라키테스가 유린당했습니다.\n다음은 카르분클루스일까요?",
      category: "proper_noun",
      reason: "용어집의 고정 지명 'エブル'을 '에블'로 바로잡았다.",
    },
    {
      index: 193,
      after: "천충탑 자이페르트・라운드 플로어０６",
      category: "proper_noun",
      reason: "용어집의 고정 지명 '天衝塔ザイフェルト'를 '천충탑 자이페르트'로 바로잡고 전각 숫자를 보존했다.",
    },
  ],
  batch_0083: [
    {
      index: 11,
      after: "로그레스 탐색 시작　　　\n천충탑 자이페르트 클리어\n엘고드 화산 클리어　　　\n솔리톤 종유동 클리어　　\n폐도 힐베르트 클리어　　\n돌아간다　　　　　　　",
      category: "proper_noun",
      reason: "용어집의 고정 지명 '天衝塔ザイフェルト'를 '천충탑 자이페르트'로 바로잡았다.",
    },
    {
      index: 13,
      after: "교단 병사를 쓰러뜨리다니\n너희는 제국 사람이냐?\n이 도시를 습격하러 왔나!",
      category: "grammar",
      reason: "복수 상대를 지칭하는 문장의 주어와 서술어 호응을 자연스럽게 고쳤다.",
    },
    {
      index: 22,
      after: "에블 유적 D03 오이겐에서 브라이트로\n",
      category: "proper_noun",
      reason: "용어집의 고정 지명 'エブル'을 '에블'로 바로잡았다.",
    },
    {
      index: 59,
      after: "이 도시에 있던 많은\n노스 노와레교도는\n베네트나슈로 돌아갔습니다<$0C>역시 원로원은\n노스 노와레교를\n배척할 생각이군요",
      category: "terminology",
      reason: "종교 소속을 나타내는 'ノースノワーレ教徒'를 '노스 노와레교도'로 통일했다.",
    },
    {
      index: 66,
      after: "알스 황제든 누구든 좋으니까\n빨리 에블을\n제국에서 해방해 줘……",
      category: "proper_noun",
      reason: "용어집의 고정 지명 'エブル'을 '에블'로 바로잡았다.",
    },
    {
      index: 73,
      after: "제국의 습격 이후로는\n전보다 매일이 더 충실해졌어<$0C>언제 죽어도 후회하지 않도록\n１일 １일을 온 힘을 다해 살자고\n생각하게 됐거든――<$0C>그 습격이 잃게 한 것만\n있는 건 아니었다고\n지금은 그렇게 생각해……",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 '１' 두 개를 복원하면서 자연스러운 문장으로 다듬었다.",
    },
    {
      index: 96,
      after: "알스 폐하가\n오르키나교도라고\n우쭐대지 마라!",
      category: "terminology",
      reason: "종교 소속을 나타내는 'オルキナ教徒'를 '오르키나교도'로 통일했다.",
    },
    {
      index: 110,
      after: "전쟁 중이야! 전쟁!",
      category: "speaker_voice",
      reason: "전쟁 중임을 강하게 상기시키는 원문의 강조 어조를 자연스럽게 살렸다.",
    },
    {
      index: 128,
      after: "기하 회랑 알비스・희망을 품은 기억  제１층",
      category: "naturalness",
      reason: "기억이 희망을 품는다는 제목의 의미가 자연스럽게 전달되도록 다듬었다.",
    },
    {
      index: 135,
      after: "어머, 도련님……\n누나한테 무슨 볼일이야?<$0C>나도 심심했으니까\n잠깐이라면\n놀아 줄 수도 있어♪",
      category: "meaning",
      reason: "화자가 상대와 놀아 주겠다는 '遊んであげる'의 행위 방향을 바로잡았다.",
    },
    {
      index: 138,
      after: "이 마을 북서쪽에는\n에블 유적이 있어<$0C>마을 사람조차 가까이 가지 않는\n아주 위험한 유적이야.\n당신도 가까이 가지 마",
      category: "proper_noun",
      reason: "용어집의 고정 지명 'エブル'을 '에블'로 바로잡았다.",
    },
    {
      index: 146,
      after: "우리가 할 수 있는 건\n알스 황자의 말씀을 믿고\n희망을 잃지 않은 채 살아가는 것뿐<$0C>그 총명한 분이라면\n반드시 미친 황제인 형을 쓰러뜨리고\n풀헤임에 평화를 가져올 겁니다",
      category: "grammar",
      reason: "'兄皇'의 가족 관계와 황제 지위를 자연스러운 한국어 어순으로 다듬었다.",
    },
    {
      index: 150,
      after: "에블에 사는\n친구가 제국 병사들에게\n투옥됐다고 들었습니다<$0C>신제국 헌장인가를\n위반했다는데……\n대체 뭘 한 걸까요",
      category: "proper_noun",
      reason: "용어집의 고정 지명 'エブル'을 '에블'로 바로잡았다.",
    },
    {
      index: 153,
      after: "테스트 맵・NPC 배치 초기화\n",
      category: "orthography",
      reason: "문체 가이드에 따라 전각 영문 약어 'ＮＰＣ'를 반각 ASCII 'NPC'로 정규화했다.",
    },
    {
      index: 177,
      after: "이게 『멸망』이라는 거라면\n나는 신앙을 품은 이 영혼째\n바다에 몸을 던지고 싶어……",
      category: "naturalness",
      reason: "신앙을 간직한 영혼까지 함께 던지겠다는 비장한 대사를 자연스럽게 다듬었다.",
    },
  ],
  batch_0084: [
    {
      index: 31,
      after: "아내가 쌀쌀맞게 굴고\n딸이 험한 말을 배워도\n역시 인생은 살 만해<$0C>다음에는 아내와 딸을\n여기에 데려오겠습니다",
      category: "grammar",
      reason: "아내가 화자에게 냉담하게 군다는 의미를 자연스러운 능동문으로 고쳤다.",
    },
    {
      index: 49,
      after: "……혼자면 돼.\n이젠 소중한 사람을 만들거나\n잃는 건 싫으니까……",
      category: "numeric_fidelity",
      reason: "원문에 숫자가 없는 '１명' 표기를 제거하고 혼자 지내겠다는 의미를 정확히 복원했다.",
    },
    {
      index: 53,
      after: "이 마을 １번 안쪽에\n그란츠 씨라는 사람이 살아<$0C>무서운 사람이지만 기계에 밝아서\n못 고치는 게 없다고 했어",
      category: "numeric_fidelity",
      reason: "원문의 전각 숫자 '１'을 복원했다.",
    },
    {
      index: 61,
      after: "이런, 이런.\n완전히 머리끝까지 화가 났군",
      category: "idiom",
      reason: "격분한 상태를 뜻하는 '頭に血が上る'를 자연스러운 한국어 관용 표현으로 옮겼다.",
    },
    {
      index: 65,
      after: "이 나이가 돼서도\n내 발로 걸을 수 있는 건<$0C>오랫동안 밀물과 썰물의 길을 지나\n신전에 참배한 덕분이야",
      category: "word_choice",
      reason: "밀물과 썰물에 따라 열리는 길이라는 '満ち干の道'의 의미를 명확히 했다.",
    },
    {
      index: 69,
      after: "네가 화평 사자라니……\n고약한 농담이군<$0C>너는 선전포고\n친서를 가져온 남자잖아?",
      category: "naturalness",
      reason: "'趣味の悪い冗談'을 자연스러운 한국어 표현으로 다듬었다.",
    },
    {
      index: 89,
      after: "여기서 샘을 계속 바라보면\n가끔 떠 있는 나뭇잎 뒤에\n이상한 생물이 보이는――<$0C>것 같아.\n기분 탓일까……",
      category: "naturalness",
      reason: "생물이 보이는 듯하다는 문장이 제어 토큰 전후로 자연스럽게 이어지도록 다듬었다.",
    },
    {
      index: 100,
      after: "여기서 배웅하는 분은\n고귀한 분이 많습니다<$0C>……차림새를 단정히 해야겠어요",
      category: "word_choice",
      reason: "외모와 복장을 단정히 한다는 '身だしなみ'의 의미를 정확히 옮겼다.",
    },
    {
      index: 107,
      after: "……어머. 셰리 그린힐\n의장 암살 미수 사건에 연루됐는지도\n의심해 보는 게 좋겠군요",
      category: "grammar",
      reason: "사건 관여 여부를 의심한다는 문장의 호응을 자연스럽게 고쳤다.",
    },
    {
      index: 134,
      after: "있지, 너도 １명 홀로야?\n그렇다면 나와 같네.\n불쌍해라……",
      category: "grammar",
      reason: "전각 숫자 '１'을 보존하면서 홀로인지 묻는 문장을 자연스럽게 다듬었다.",
    },
    {
      index: 151,
      after: "지금은 제국보다\n공화국 경제를 재건하는 것이\n무엇보다 최우선 과제다<$0C>에블과 바트라키테스를\n빼앗긴 데다 많은 도시가\n피해를 입었으니까……",
      category: "proper_noun",
      reason: "용어집의 고정 지명 'エブル'을 '에블'로 바로잡았다.",
    },
    {
      index: 152,
      after: "……좋은 아침입니다<$0C>…………\n……그게 다입니다만…… 뭔가요?",
      category: "meaning",
      reason: "아침 인사인 'おはようございます'를 정확히 옮겼다.",
    },
    {
      index: 160,
      after: "아름다운 도시가 파괴되는 걸\n보는 건 견딜 수 없어……\n이렇게나 아름다우니까",
      category: "grammar",
      reason: "이유를 나타내는 마지막 문장의 어미와 띄어쓰기를 자연스럽게 고쳤다.",
    },
    {
      index: 163,
      after: "저기 있는 예쁜 여자――\n진짜 가족은 아니지만\n내 엄마야……<$0C>지난 습격으로\n１명 홀로 남은 나를\n거둬 줬어……",
      category: "grammar",
      reason: "전각 숫자 '１'을 보존하면서 홀로 남았다는 의미를 자연스럽게 다듬었다.",
    },
    {
      index: 197,
      after: "공화국에 영원한 충성을 맹세하는 것보다\n특정 숙녀에게 영원한 사랑을 맹세하는 게\n남자로서는 성공한 인생이지?",
      category: "naturalness",
      reason: "연애에서 성공한 사람을 뜻하는 '勝ち組'을 자연스러운 한국어로 다듬었다.",
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
  fs.writeFileSync(path.join(root, reviewedRel), reviewedRows.map((row) => JSON.stringify(row)).join("\n") + "\n", "utf8");

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
    review_dimensions: ["meaning", "function", "numeric fidelity", "proper nouns", "natural Korean", "particles", "control tokens", "line breaks"],
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
