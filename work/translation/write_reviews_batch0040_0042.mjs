import fs from "node:fs";
import path from "node:path";

const ROOT = path.join("work", "translation");
const SOURCE_ROOT = path.join(ROOT, "tm_v2", "batches", "source");
const DRAFT_ROOT = path.join(ROOT, "drafts");
const REVIEWED_ROOT = path.join(ROOT, "reviewed");
const REVIEWS_ROOT = path.join(ROOT, "reviews");

const CORRECTIONS = {
  batch_0040: {
    "ARF-TM-E43C73ADB8023532B356": {
      after: "라르크의 반응이 기대되네☆!",
      category: "function",
      reason: "상대에게 기대하라고 권하는 말이 아니라 라르크의 반응을 기대한다는 발화 의도를 복원했다.",
    },
    "ARF-TM-E49A71E7E01E65A3ABD1": {
      after: "그렇게 나쁜 녀석은\n아닌 것 같슴다",
      category: "naturalness",
      reason: "부정 추측 표현이 자연스럽게 이어지도록 다듬었다.",
    },
    "ARF-TM-E59AD972F9219EBB1526": {
      after: "그만두라니까\n징그럽잖아!",
      category: "meaning",
      reason: "상대의 행동을 불쾌하고 섬뜩하게 여기는 뉘앙스를 살렸다.",
    },
    "ARF-TM-E763FE21A95F7CA10277": {
      after: "어디를 봐야 할지 곤란할 때도\n있었지만\n이젠 익숙해졌슴다",
      category: "naturalness",
      reason: "시선을 어디에 둘지 곤란하다는 관용적 의미를 자연스럽게 옮겼다.",
    },
    "ARF-TM-E8EEDD8DB0DA1AF6F6B2": {
      after: "무리일 것이다.\n알스가 어렸을 때와는\n그들의 관계도 달라졌으니",
      category: "speaker_voice",
      reason: "오이겐의 절제된 문어체 어조와 문장 간 인과관계를 살렸다.",
    },
    "ARF-TM-E94BF46BE6F8CD5432F5": {
      after: "본 적이 있는 곳인가",
      category: "meaning",
      reason: "장소에 낯이 익은지를 묻는 뜻이 분명하게 드러나도록 고쳤다.",
    },
    "ARF-TM-E99321563BDE6974B69B": {
      after: "헤에〜, 그렇구나.\n뭐든 잘 아네.\n조금 존경하게 될지도 모르겠네",
      category: "naturalness",
      reason: "마지막 추측 표현을 빠짐없이 완결된 한국어 문장으로 다듬었다.",
    },
    "ARF-TM-EA177286485D0A5E6A86": {
      after: "어딘가 좁고 어두운 구석에서\n가만히 몸을 웅크린 채\n지내게 해 주시고……",
      category: "grammar",
      reason: "화자가 몸을 작게 웅크리고 지낸다는 의미와 겸양 표현을 자연스럽게 연결했다.",
    },
    "ARF-TM-EA73743667B9E2E17546": {
      after: "네, 네……",
      category: "naturalness",
      reason: "마지못해 대답하는 말투를 한국어 관용 표현으로 옮겼다.",
    },
    "ARF-TM-EAAB955BFBF03A814A29": {
      after: "용병이라는 이유만으로\n툭하면 죽으라는 명령을 받으면\n못 참으니까",
      category: "meaning",
      reason: "쉽게 목숨을 버리라는 명령을 내리는 부당함이 드러나도록 고쳤다.",
    },
    "ARF-TM-EB059BF132A1700CD1B3": {
      after: "……뭐, 계속 고민하고 있을\n때가 아닌가.\n기운 차리고 가자",
      category: "meaning",
      reason: "くよくよ를 우물쭈물하는 행동이 아니라 계속 고민하며 침울해하는 상태로 바로잡았다.",
    },
    "ARF-TM-EBE24B8AB5CD789E50D5": {
      after: "뭔 일임까, 형님\n안 어울리게 심각한 표정이나 짓고",
      category: "speaker_voice",
      reason: "니콜 특유의 가벼운 말투를 유지하면서 자연스러운 질문으로 다듬었다.",
    },
    "ARF-TM-ECF9F3E2B3B1A8191029": {
      after: "맞아.\n５살 정도씩 차이 나나?",
      category: "grammar",
      reason: "나이 차이를 묻는 한국어 어순으로 자연스럽게 고쳤다.",
    },
    "ARF-TM-EDFF102057B882589B5C": {
      after: "이제 곧이네",
      category: "meaning",
      reason: "도착 여부를 단정하지 않고 때가 가까워졌다는 원문의 뜻을 유지했다.",
    },
    "ARF-TM-EE7D215B24FBCB0536B3": {
      after: "그렇다잖아. 결정됐군",
      category: "function",
      reason: "앞선 말을 받아 결론을 확정하는 발화 기능이 드러나도록 고쳤다.",
    },
    "ARF-TM-EF86F5B8A82FD4FF1DA2": {
      after: "그 녀석을 못 믿는구나……",
      category: "meaning",
      reason: "신뢰가 없는 사람이 그 녀석이라는 주체 관계를 분명히 했다.",
    },
    "ARF-TM-EFEE71DA4F8A42C6512A": {
      after: "틀림없어――우리 동포\n『고고의 마슈가르』다.\n혼란을 겪고 있어",
      category: "terminology",
      reason: "고유 칭호 『孤高のマシュガル』를 용어집 표기인 『고고의 마슈가르』로 통일했다.",
    },
    "ARF-TM-F06FC5E42EB87AE2BBBF": {
      after: "아아〜, 정말, 아까 건 봐줍쇼!\n네가 노련한 전사라는 건\n자〜알 알았슴다!",
      category: "meaning",
      reason: "歴戦을 단순한 역전이 아니라 수많은 전투를 겪은 노련함으로 옮겼다.",
    },
  },
  batch_0041: {
    "ARF-TM-F2039E1C2C208BE1D865": {
      after: "저게 뭡니까",
      category: "speaker_voice",
      reason: "니콜의 말투를 유지하면서 오타처럼 보이는 축약을 자연스럽게 풀었다.",
    },
    "ARF-TM-F3352E6424E08E3592AB": {
      after: "아르콘대 대장이던 시절에\n조금 말이지",
      category: "terminology",
      reason: "アルコーン을 기존 확정 표기인 아르콘대로 통일했다.",
    },
    "ARF-TM-F496F49DE0EDD674D2E7": {
      after: "네, 네. 알았어",
      category: "naturalness",
      reason: "마지못해 승낙하는 대답을 한국어 관용 표현으로 옮겼다.",
    },
    "ARF-TM-F59416885DB42F797546": {
      after: "이쯤 화면 오른쪽 위에\n정보가 표시되게 되어 있으니까\n착륙할 수 있다면<$0C><$15>13을 누르면\n나머지는 비광정이 알아서\n착륙 시퀀스에 들어갈 거야",
      category: "grammar",
      reason: "중복된 조건 표현을 정리하고 화면 안내 문장을 자연스럽게 다듬었다.",
    },
    "ARF-TM-F5D666555DA0901CEFC4": {
      after: "그럴지도…… 모르겠네.\n고마워, 리피아",
      category: "grammar",
      reason: "추측 표현의 활용을 자연스러운 한국어 형태로 바로잡았다.",
    },
    "ARF-TM-F602EC99EA81D24E45CB": {
      after: "아니…… 아, 그래도\n그럴지도 모르겠네",
      category: "speaker_voice",
      reason: "라르크의 평소 반말 어조에 맞게 종결 표현을 조정했다.",
    },
    "ARF-TM-F63389E8EF6C58896135": {
      after: "응? 이 더러운 글씨는\n혹시 코핀이 쓴 건가?<$0C>『우리 계곡에 구세주 나타나다!』\n그게 나라는 거야……",
      category: "naturalness",
      reason: "인용문의 구세주가 자신을 가리킨다는 반응을 자연스럽게 표현했다.",
    },
    "ARF-TM-F649C3AB7DDF6E6B89FD": {
      after: "아이한테까지 한심하다는 소릴 듣는 우리라니……",
      category: "meaning",
      reason: "아이에게 어이없다는 평가를 받는 상황이라는 의미를 복원했다.",
    },
    "ARF-TM-F6751A90EC96351BB3AC": {
      after: "알겠다고 해 놓고 결국\n１명 혼자 먼저 가는 거냐",
      category: "meaning",
      reason: "상대가 혼자 앞서 가 버린다는 원문의 주체와 행동을 분명히 했다.",
    },
    "ARF-TM-F6992404766856C90874": {
      after: "세상에선 돈이 힘이야",
      category: "naturalness",
      reason: "돈이 영향력을 발휘한다는 관용적 의미를 자연스러운 한국어로 옮겼다.",
    },
    "ARF-TM-F9C583A2995A39728550": {
      after: "하지만 영양가도 높다.\n배도 든든해지지",
      category: "speaker_voice",
      reason: "오이겐의 절제된 단정형 어조에 맞추고 포만감을 자연스럽게 표현했다.",
    },
    "ARF-TM-FA0B70A54F39AD476216": {
      after: "그런 걸까……\n저들의 말이야말로\n진정한 백성의 목소리일지도……",
      category: "punctuation",
      reason: "말줄임표 뒤에 불필요하게 덧붙은 마침표를 제거했다.",
    },
    "ARF-TM-FA868E81B8052D7FD935": {
      after: "자기 자신에게서 가장 마음에 드는 점은?\n――자, 어때",
      category: "meaning",
      reason: "신체 부위가 아니라 자기 자신에게서 좋아하는 점을 묻는 질문으로 바로잡았다.",
    },
    "ARF-TM-FAC3D8F05936326DAA74": {
      after: "그러니까 시종도 아니라니까!",
      category: "meaning",
      reason: "しもべ를 문맥에 맞는 시종으로 옮겼다.",
    },
    "ARF-TM-FC0F5B7E536BC9D6EF5B": {
      after: "저번 일로 생각하는 바도\n생긴 모양이다. 조금은\n변했을지도 모르겠군",
      category: "speaker_voice",
      reason: "오이겐의 절제된 단정형 어조와 문장 연결을 자연스럽게 다듬었다.",
    },
    "ARF-TM-FC801854119E8B358D21": {
      after: "나한테 널 돌보게 하고 있잖아",
      category: "meaning",
      reason: "화자가 보호자라는 신분이 아니라 상대를 돌보는 역할을 맡았다는 뜻을 살렸다.",
    },
    "ARF-TM-FCBFFACAB4EC9B824197": {
      after: "틀림없어……\n아군끼리 싸운 거야……",
      category: "meaning",
      reason: "同士討ち를 단순한 상호 전투가 아니라 같은 편끼리 벌인 싸움으로 명확히 했다.",
    },
    "ARF-TM-FD675122D43EF88B3F41": {
      after: "뭐, 그때는\n리피아가 표적이었으니까……",
      category: "naturalness",
      reason: "수동태 직역을 피하고 노림을 받은 상황을 자연스럽게 표현했다.",
    },
    "ARF-TM-FDED140965237B326465": {
      after: "니콜은 아직 젊다.\n나름의 결론을 찾는 데\n필요한 시간은 충분하겠지",
      category: "speaker_voice",
      reason: "오이겐의 절제된 단정형 어조로 통일했다.",
    },
    "ARF-TM-FFBA4E388DD4570F1002": {
      after: "그러게.\n또 오자.\n이 비밀의 샘에――",
      category: "particle",
      reason: "고유하게 지칭하는 샘의 이름이 자연스럽게 이어지도록 관형격 조사를 보완했다.",
    },
  },
  batch_0042: {
    "ARF-TM-046A843BAC74F4899133": {
      after: "……못 봤구나, 라르크",
      category: "meaning",
      reason: "화자가 보지 못했다는 뜻이 아니라 라르크가 보지 않았음을 확인하는 문장으로 바로잡았다.",
    },
    "ARF-TM-2F66C1A4EEA0772F8246": {
      after: "레이디, 손을 내주시죠",
      category: "speaker_voice",
      reason: "여성에게 손을 청하는 세련되고 공손한 어조를 살렸다.",
    },
    "ARF-TM-684A9E5022A55D14E953": {
      after: "교회는 아이온대에\n점거당했고, 마리아 말고는\n죽었다는 보고를 받았어",
      category: "meaning",
      reason: "接収를 단순 접수가 아니라 무력 조직에 의한 점거로 명확히 옮겼다.",
    },
    "ARF-TM-78779BBB88C017FDE3E6": {
      after: "난 １명 혼자서도\n제대로 해낼 수 있으니까!",
      category: "naturalness",
      reason: "혼자서도 일을 해낼 수 있다는 자신감을 자연스럽게 표현했다.",
    },
    "ARF-TM-7A185B01838A30D275AB": {
      after: "그러고 보니 전설의 용병치고\n젊어 보이네요. 몇 살임까?",
      category: "meaning",
      reason: "실제 나이를 단정하지 않고 겉보기에 젊다는 관찰로 바로잡았다.",
    },
    "ARF-TM-821F5D6849486294909A": {
      after: "형니〜임",
      category: "naturalness",
      reason: "일본어 장음 기호가 한국어 단어에 섞이지 않도록 늘여 부르는 말투로 다듬었다.",
    },
    "ARF-TM-B3A35B5B2BC0C5E42EA4": {
      after: "『싫은걸』이라니…… 전설의 용병이라\n불리던 녀석이 그런 어린애\n같은 말투 쓰지 마",
      category: "function",
      reason: "상대가 방금 한 말을 직접 인용해 타박하는 발화 구조를 분명히 했다.",
    },
    "ARF-TM-B948FD5412E0A8FCD8E2": {
      after: "딱히 초조해하지 않습니다",
      category: "meaning",
      reason: "현재 초조하지 않다고 부정하는 발화를 과거형에서 현재형으로 바로잡았다.",
    },
    "ARF-TM-D46EBB9D1BAC2BB98A0B": {
      after: "……내가 사쥬의 미래를\n짓밟은 것이다",
      category: "speaker_voice",
      reason: "오이겐의 절제된 단정형 어조로 통일했다.",
    },
    "ARF-TM-DD7EEA4BCDF29C98B486": {
      after: "그랬던 거야!?",
      category: "meaning",
      reason: "새로 알게 된 과거의 사실에 놀라는 반응이 드러나도록 시제를 바로잡았다.",
    },
    "ARF-TM-EDEABAA8324997651F1F": {
      after: "……라르크.\n눈치 좀 챙겨",
      category: "naturalness",
      reason: "空気を読む의 관용적 의미를 자연스러운 한국어 대사로 옮겼다.",
    },
    "ARF-TM-F5F4901CAC7CB4162673": {
      after: "다행히 예전의 나는\n그 녀석 동료가 아니었으니 말이지",
      category: "speaker_voice",
      reason: "오이겐의 설명조 어투와 과거 시점을 자연스럽게 살렸다.",
    },
    "ARF-TM-42D099D813F61B3E3E81": {
      after: "아무렇지도 않게 말하네……",
      category: "line_breaks",
      reason: "다음 번역 단위의 문장이 잘못 붙은 초과 번역을 제거하고 원문의 단일 행 구조를 복원했다.",
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
