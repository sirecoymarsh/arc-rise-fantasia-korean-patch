import fs from "node:fs";
import path from "node:path";


const ROOT = path.join("work", "translation");
const SOURCE_ROOT = path.join(ROOT, "tm_v2", "batches", "source");
const DRAFT_ROOT = path.join(ROOT, "drafts");
const REVIEWED_ROOT = path.join(ROOT, "reviewed");
const REVIEWS_ROOT = path.join(ROOT, "reviews");

const CORRECTIONS = {
  batch_0031: {
    "ARF-TM-60EF56EF682098F0B33D": {
      after: "할 수 있을 리 없슴다.\n꽃 １００송이의 목을 벨 수 있으면\n그걸로 수련이 끝이라니",
      category: "meaning",
      reason: "できるわけない를 불가능을 단정하는 뜻으로 바로잡고 수련 종료 조건을 자연스럽게 연결했다.",
    },
    "ARF-TM-6102F29E2C5FC445B32C": {
      after: "아니, 군이 아니라 집으로 돌아가겠지",
      category: "naturalness",
      reason: "생략된 이동 동사를 보충해 한국어 문장을 완결했다.",
    },
    "ARF-TM-619FA48F9346B9C87732": {
      after: "알았다면 됐다.\n설령 사신이라 불리더라도\n넌 변할 필요가 없다는 거지",
      category: "grammar",
      reason: "조사와 인용 종결을 자연스럽게 바로잡았다.",
    },
    "ARF-TM-61D8B9A43C42B14F84E6": {
      after: "고마워〜, 반하지 마〜",
      category: "speaker_voice",
      reason: "장난스러운 반말 어조에 맞게 명령형을 다듬었다.",
    },
    "ARF-TM-61EC914C4EB118BC7AA9": {
      after: "지금은 여기 들를\n여유 같은 건 없어.\n앞길을 서두르자",
      category: "line_breaks",
      reason: "원문의 세 행 구조를 복원하면서 의미를 자연스럽게 정리했다.",
    },
    "ARF-TM-63B63A2C66175ADD7A9B": {
      after: "이런 통로까지……\n잘 아시네요",
      category: "naturalness",
      reason: "목적어가 어색하게 남지 않도록 한국어 어순을 바로잡았다.",
    },
    "ARF-TM-63F3B99A57F2963E2054": {
      after: "……신속의 레온은 죽었어.\n사쥬라고 불러 달라고\n전에도 말했잖아",
      category: "naturalness",
      reason: "호칭 요청과 앞선 발언의 관계가 분명해지도록 어순을 다듬었다.",
    },
    "ARF-TM-64782FAABFA7461B22DA": {
      after: "깊은 한숨〜\n그러다 늙어, 오이겐",
      category: "naturalness",
      reason: "상대에게 건네는 가벼운 핀잔으로 자연스럽게 다듬었다.",
    },
    "ARF-TM-64BC1DDF816C7DB507BF": {
      after: "밤에는\n희귀한 광석을 찾았다며\n자취를 감추고……",
      category: "line_breaks",
      reason: "원문의 세 행 구조를 복원하고 서술을 자연스럽게 연결했다.",
    },
    "ARF-TM-652012CA7CB595DAFBD3": {
      after: "알겠어.\n라르크는 공인 용병이구나",
      category: "terminology",
      reason: "認可傭兵을 용어집 표기인 공인 용병으로 통일했다.",
    },
    "ARF-TM-66CCA129B5B066CE2D7A": {
      after: "처음으로 대련을\n했었잖아?\n그 뒤부터였지",
      category: "line_breaks",
      reason: "원문의 세 행 구조를 복원했다.",
    },
    "ARF-TM-6AA4F2AEAE0A4950943D": {
      after: "메리디아 가문의 피가 빚은 결과인가……",
      category: "meaning",
      reason: "血のなせる業를 혈통이 빚은 결과라는 문맥으로 바로잡았다.",
    },
    "ARF-TM-6B3D705676760628BA19": {
      after: "과거의 유산인가……",
      category: "naturalness",
      reason: "직역투 조사를 자연스러운 한국어 관형 표현으로 다듬었다.",
    },
    "ARF-TM-6B4A9A16ED67DB8C4207": {
      after: "누구 때문이라고 생각해?\n그 건방진 입,\n막아 줄 수도 있어",
      category: "meaning",
      reason: "減らず口의 건방지게 말대꾸하는 뉘앙스와 위협성 농담을 살렸다.",
    },
    "ARF-TM-6BB862D8AF67D80369DB": {
      after: "이 치마 길이야말로\n여자의 숙원, 용기의 증표다!",
      category: "meaning",
      reason: "本懐를 본분이 아니라 간절히 바라던 숙원이라는 뜻으로 바로잡았다.",
    },
    "ARF-TM-6BFF07EB7AE97108AF90": {
      after: "하지만 하마터면\n참지 못할 만큼\n자극을 받을 때도 있습니다",
      category: "meaning",
      reason: "危ういところで의 아슬아슬하게 참는 뉘앙스를 복원했다.",
    },
    "ARF-TM-6C551057A8346302CA0A": {
      after: "생각하지 않으면 된다, 이건가.\n뭐, 모르면 무섭지도 않겠지",
      category: "naturalness",
      reason: "생략된 결론을 보충해 독백의 흐름을 자연스럽게 만들었다.",
    },
    "ARF-TM-6D346B7FE18865FAB555": {
      after: "에!?",
      category: "function",
      reason: "놀람의 감탄사를 대답으로 오해하지 않도록 바로잡았다.",
    },
    "ARF-TM-6DD8B55935AD9D57237A": {
      after: "입으로 배에서 나는 소리 내지 마.\n알았어, 뭐라도 생각할게.\n기대하, 고, 있어!",
      category: "meaning",
      reason: "楽しみにしてろ의 기대하라는 뜻과 의도적인 끊어 말하기를 살렸다.",
    },
    "ARF-TM-6E4D89E078CDE62F758F": {
      after: "전직……이긴 하지만",
      category: "meaning",
      reason: "元가 현재가 아닌 전직 신분을 가리킨다는 점을 분명히 했다.",
    },
    "ARF-TM-6EA4D8AD092C6E759406": {
      after: "내 아름다운 추억을 깎아내리다니.\n……왠지 좀 충격이네……",
      category: "naturalness",
      reason: "けなされた의 의미를 일상적인 한국어 표현으로 다듬었다.",
    },
  },
  batch_0032: {
    "ARF-TM-6F34EA6F780CAEA96EDB": {
      after: "……안쪽에서 냉기가 느껴지는군.\n상당히 깊은 종유동굴일지도 모르겠군",
      category: "speaker_voice",
      reason: "고풍스럽고 단정적인 화자의 말투를 일관되게 맞췄다.",
    },
    "ARF-TM-70A9F703990668CBCED4": {
      after: "나는 기억해.\n자무엘 선생님과 다 같이\n수련하러 산에 올랐던 일을",
      category: "naturalness",
      reason: "皆で의 함께했다는 뜻과 목적 표현을 자연스럽게 다듬었다.",
    },
    "ARF-TM-70C1F7C3ACCCEFC4A687": {
      after: "덜……덜?",
      category: "meaning",
      reason: "앞 문장의 ガクブル를 되묻는 말장난을 한국어 의태어로 살렸다.",
    },
    "ARF-TM-72D01B97EC3E4E62A902": {
      after: "아버지인가…… 그렇다면 괜찮겠군.\n나도 경험이 있으니까 말이지",
      category: "speaker_voice",
      reason: "고풍스러운 화자의 종결 어조와 설명의 완결성을 맞췄다.",
    },
    "ARF-TM-738AA8729D6B57387361": {
      after: "언제까지나 헤매는가 싶더니\n의외로 순간만 생각하기도 하고",
      category: "meaning",
      reason: "刹那的을 생소한 직역어 대신 순간만 중시한다는 뜻으로 풀었다.",
    },
    "ARF-TM-73A238AE0215A2BEAA8B": {
      after: "사쥬\n너도 참 태평하네……",
      category: "speaker_voice",
      reason: "あんた의 친근하고 타박하는 반말 어조를 반영했다.",
    },
    "ARF-TM-74AC02BDD7672E23D16D": {
      after: "알 것 같습니다.\n지금은 제대로 이해하지 못하지만\n당신이 하신 말이……",
      category: "speaker_voice",
      reason: "원문의 정중한 화법을 세 행 전체에 일관되게 적용했다.",
    },
    "ARF-TM-753851C6639F67A5EDC4": {
      after: "바트라키테스만을 위해서가 아니야.\n메리디아를 위해서도 그래",
      category: "naturalness",
      reason: "대조되는 두 대상을 자연스러운 한국어로 연결했다.",
    },
    "ARF-TM-7594C96485F4B9F6DA69": {
      after: "난 어떻게 하면 돼?",
      category: "naturalness",
      reason: "행동 지침을 묻는 질문으로 자연스럽게 다듬었다.",
    },
    "ARF-TM-7620FD96E3A979596662": {
      after: "너라면 분명 될 수 있어.\n모두에게 사랑받는 용사님으로",
      category: "particle",
      reason: "될 수 있다는 서술과 이어지도록 보격 표현을 바로잡았다.",
    },
    "ARF-TM-762AF9F23F423BA4B425": {
      after: "뭐, 미간을 험악하게 찌푸리는 건\n닮았다면 닮았으려나",
      category: "naturalness",
      reason: "표정을 가리키는 문장을 자연스러운 한국어로 다듬었다.",
    },
    "ARF-TM-766B52E0E3DDD3633E23": {
      after: "아니ー, 세실은 그렇다 치고\n리피아가 억지로 하는 듯한 느낌이\n참을 수 없이 좋슴다ー",
      category: "meaning",
      reason: "たまんない가 불쾌함이 아니라 너무 좋아 견딜 수 없다는 뜻임을 복원했다.",
    },
    "ARF-TM-7728287A11A18D6DB21B": {
      after: "게다가 다 같이 노는 편이 더 즐거우니까",
      category: "meaning",
      reason: "方が의 비교 의미와 しね의 이유 제시를 반영했다.",
    },
    "ARF-TM-7A06231DCAF3EEFB50FD": {
      after: "짱까지 붙여 부르냐.\n뭐, 그렇지.\n언제까지 불평만 할 순 없고",
      category: "meaning",
      reason: "ちゃんづけかよ를 호칭을 금지하는 말이 아니라 놀라며 지적하는 말로 바로잡았다.",
    },
    "ARF-TM-7A2BF0A50EC311D279B8": {
      after: "근데 말이야…… 김빠진다니까.\n예쁜 언니가\n민망한 모습을 보여 주는데",
      category: "meaning",
      reason: "あられもない姿를 꼴사납다가 아니라 민망하게 드러난 모습으로 바로잡았다.",
    },
    "ARF-TM-7BEA3A806E881CE43FFF": {
      after: "그가 잃은 목숨――",
      category: "naturalness",
      reason: "목숨을 분실물처럼 표현하지 않도록 자연스럽게 다듬었다.",
    },
  },
  batch_0033: {
    "ARF-TM-7F7828AA7FBED5ACFC79": {
      after: "진짜 마음은 어느 쪽이야?",
      category: "meaning",
      reason: "本命이 둘 중 진심으로 좋아하는 상대를 뜻한다는 점을 분명히 했다.",
    },
    "ARF-TM-8065AEC81E7D7FD9DC78": {
      after: "전에는 해변에서 코핀에게\n사랑 고백을 받았다〜\n하고 푸념하더라",
      category: "naturalness",
      reason: "부자연스러운 피동 표현을 자연스러운 한국어로 다듬었다.",
    },
    "ARF-TM-8193986335E1E010E721": {
      after: "그렇군, 그렇다면 걱정할 것 없겠군.\n아르콘대도\n무능하지는 않을 테니 말이지",
      category: "speaker_voice",
      reason: "격식 있고 고풍스러운 화자의 종결 어조를 일관되게 맞췄다.",
    },
    "ARF-TM-81F1F4489CF900746B40": {
      after: "나랑 같네.\n라르크를 어디까지나\n따라가고 싶거든",
      category: "naturalness",
      reason: "이유를 덧붙이는 もの의 말끝을 자연스럽게 완결했다.",
    },
    "ARF-TM-82197128644E1FB29118": {
      after: "디바를 계승했을 때\n역대 디바의 코드가\n몸에 새겨진 것 같아",
      category: "meaning",
      reason: "코드가 화자의 몸에 새겨진 피동 관계를 복원했다.",
    },
    "ARF-TM-83246BC3704AC8E04E84": {
      after: "안트락스 남서쪽이야.\n우리를 따라오는\n저 녀석의 고향이지",
      category: "particle",
      reason: "저 녀석과 고향의 소유 관계를 분명히 했다.",
    },
    "ARF-TM-8337D606A8698F14FD44": {
      after: "정신을 못 차리네, 당신들은.\n그러니까 여자 때문에 고생할 팔자가\n훤히 보이는 거 아니야?",
      category: "meaning",
      reason: "こりない와 女難の相의 관용적 의미를 문맥에 맞게 풀었다.",
    },
    "ARF-TM-83ED9BA2D6B14FB813AF": {
      after: "어이쿠, 아가씨.\n나한테 반하면 위험할걸?",
      category: "function",
      reason: "실제 여부를 묻는 질문이 아니라 능글맞은 경고가 되도록 다듬었다.",
    },
    "ARF-TM-83FFD43DDB8AAE8A5261": {
      after: "클라이드라는 남자에게도\n사명이 있겠지.\n스스로 세운 맹세다",
      category: "naturalness",
      reason: "중복된 부사를 덜고 세 행의 논리를 자연스럽게 연결했다.",
    },
    "ARF-TM-841E9BCBB0CCB232FEA2": {
      after: "대단하네…… 대체 여긴 뭐야……\n밖에서 봤을 땐\n아무것도 알 수 없었는데",
      category: "naturalness",
      reason: "놀라움과 외관만으로 알 수 없었다는 의미를 자연스럽게 다듬었다.",
    },
    "ARF-TM-8435C92D234930390354": {
      after: "미안해…… 레슬리.\n너한테 늘 고생만 시키네",
      category: "speaker_voice",
      reason: "여성 화자의 부드러운 반말 어조로 바로잡았다.",
    },
    "ARF-TM-84502AC1D0116F608AD4": {
      after: "위태로울 정도의 사명감과\n자신에게 부과된 완전함의 추구\n그리고――",
      category: "meaning",
      reason: "자신에게 요구가 부과된 피동 관계를 복원했다.",
    },
    "ARF-TM-86C14A9186678B804FBE": {
      after: "코핀은 나날이 변하고 있습니다.\n같은 날은 두 번 다시 오지 않듯\n코핀이 똑같은 날은 단 １일도 없습니다",
      category: "naturalness",
      reason: "매일 달라지는 코핀이라는 비유를 자연스럽게 다듬고 원문의 숫자를 보존했다.",
    },
    "ARF-TM-87D77CF2B94740FA5220": {
      after: "너와 라르크에 관한 이야기를 들을 수 있어서\n늘 즐거우니까",
      category: "meaning",
      reason: "두 사람에 관한 이야기를 들을 수 있어 즐겁다는 인과를 복원했다.",
    },
    "ARF-TM-8814ECFF15D14B7BC3DC": {
      after: "그보다 세실 녀석은\n재미있어하는 것뿐이잖아?",
      category: "meaning",
      reason: "っていうか의 화제 전환과 面白がる의 의미를 자연스럽게 반영했다.",
    },
    "ARF-TM-8819B94E163087EA024E": {
      after: "응, 그런 것 같아.\n또 오자. 새들을\n놀라게 하지 않도록 조용히",
      category: "naturalness",
      reason: "こっそりとの 조용히 다가가는 뉘앙스를 문맥에 맞게 살렸다.",
    },
    "ARF-TM-88BC73FB7A96E537BDD4": {
      after: "뭐야! 늘 날 어떻게 대해야 할지 모르겠다는\n표정으로 쳐다보면서!",
      category: "meaning",
      reason: "扱いに困る가 상대를 어떻게 대할지 몰라 한다는 뜻임을 복원했다.",
    },
    "ARF-TM-896263655E9A20255F6D": {
      after: "『좋아하니까』라니",
      category: "function",
      reason: "인용되는 발화와 이를 되받는 표현의 경계를 분명히 했다.",
    },
    "ARF-TM-8A580A7EC07758606AA7": {
      after: "소니아 씨가 말씀하신\n바이스의……\n네 형의 말이네",
      category: "speaker_voice",
      reason: "おっしゃっていた의 높임을 반영했다.",
    },
  },
};

function readJsonl(filePath) {
  return fs
    .readFileSync(filePath, "utf8")
    .split(/\r?\n/)
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line));
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

  for (const row of sourceRows) {
    const tmId = row.tm_id;
    const before = draftById.get(tmId).translation_ko;
    const correction = corrections[tmId];
    const after = correction ? correction.after : before;
    row.translation_ko = after;
    if (correction) {
      modifications.push({
        tm_id: tmId,
        source_text: row.source_text,
        before,
        after,
        category: correction.category,
        reason: correction.reason,
      });
    }
  }

  fs.mkdirSync(REVIEWED_ROOT, { recursive: true });
  fs.mkdirSync(REVIEWS_ROOT, { recursive: true });
  fs.writeFileSync(reviewedPath, `${sourceRows.map((row) => JSON.stringify(row)).join("\n")}\n`, "utf8");

  const report = {
    schema: "arf-translation-independent-review-v1",
    batch_id: batchId,
    reviewer: "/root/translate_batch_0009",
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
  const count = writeBatch(batchId, corrections);
  process.stdout.write(`${batchId}: ${count}\n`);
}
