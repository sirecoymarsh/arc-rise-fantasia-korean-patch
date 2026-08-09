const fs = require("fs");
const path = require("path");

const revisions = {
  batch_0028: {
    17: ["월드 스크립트５５", "원문의 전각 수치 표기를 보존"],
    21: [
      "<$15>28와<$15>29로 비행 중에도\n배 주변을 살펴볼 수 있어.\n움직인 화면을 원래대로 돌리는 건<$15>1B야",
      "제어 토큰의 원문 인접 관계를 복원",
    ],
    41: ["월드 스크립트６１", "원문의 전각 수치 표기를 보존"],
    57: [
      "성지 노와레의 노래하는 돌……인가.\n다른 녀석들에게 들었다면\n내 귀를 의심했겠지만",
      "가정 표현과 역접 관계를 자연스럽게 교정",
    ],
    70: ["투기장 설명２４", "원문의 전각 수치 표기를 보존"],
    75: ["투기장 설명２３", "원문의 전각 수치 표기를 보존"],
    96: [
      "왜 사과해?\n그저 그립다고 느끼는 건지\n몰랐을 뿐이야",
      "회상 감정의 의미와 원문 줄바꿈을 교정",
    ],
    97: [
      "나한테\n정말 소중한 거구나 하고\n느꼈어……",
      "원문의 3행 구조를 복원하고 문장을 자연스럽게 교정",
    ],
    113: [
      "레온…… 사쥬가 스스로\n로드 나이트 단장의 허상을\n무너뜨리고 말았군",
      "조직명 표기를 용어집에 맞춤",
    ],
    124: [
      "그녀…… 적대 조직에게\n목숨을 노려졌던 모양이야",
      "피동 관계와 조사를 교정",
    ],
    140: ["투기장 설명１５", "원문의 전각 수치 표기를 보존"],
    183: [
      "무례한 녀석이네〜\n청렴결백 그 자체잖아",
      "말끝과 문장부호를 화자 어조에 맞게 교정",
    ],
    195: ["엥?", "놀람을 나타내는 감탄사의 의미를 교정"],
  },
  batch_0029: {
    32: [
      "아침에는\n너무 앞서가다가 일행과 떨어지고……",
      "はぐれる의 의미를 추락이 아닌 일행 이탈로 교정",
    ],
    61: [
      "아유〜\n그 정도는 아니〜――랄까\n입대 같은 건 간단함다",
      "겸양 뒤에 이어지는 입대 설명의 의미와 말투를 교정",
    ],
    73: [
      "탁룡 강하――아니, 공중 회랑 베르쿠트의\n추락으로 인한 호존 범람은\n아직도 세계를 괴롭히고 있다",
      "고유명사와 추락의 수식 관계를 자연스럽게 교정",
    ],
    87: [
      "바이스와 힘이 향하는 방향은 달라도\n백성에게 가혹한 처사를\n강요한다는 점은 다르지 않다",
      "力の向き와 처사의 의미 및 조사를 교정",
    ],
    94: [
      "먼저 달그림자 여관에 들를까……\n안트락스에 들어가려면\n뭔가 방도가 필요하기도 하고",
      "手立て를 문맥에 맞는 방도로 교정",
    ],
    95: [
      "아마 저거야, 거대한 새!\n전에 비광정이\n에블에서 격추당했을 때 그 녀석!",
      "비광정이 격추당한 사건의 의미를 복원",
    ],
    116: ["전투식량이 있다면 말이지", "조건 표현 あれば의 의미를 교정"],
    129: [
      "아니야……\n하지만 왠지 그리운 느낌이 들어서\n끝까지 미워할 수가 없어",
      "중복 문장부호를 제거",
    ],
    134: [
      "그러니까 꽃잎은 １장도\n흩뜨리지 않는 게 중요해",
      "원문의 수치 표기를 보존",
    ],
    162: ["(나에게만 주어진…… 사명)", "사명이 주어진 대상의 의미를 교정"],
    197: [
      "자랑스럽게 말하지 마……\n뭐, 한동안 걷다 보면\n차차 익숙해지겠지",
      "중복 문장부호를 제거",
    ],
  },
  batch_0030: {
    4: [
      "토벌 퀘스트에서\n목표 몬스터를 몇 마리 쓰러뜨렸는지<$0C>수집 퀘스트에서\n목표 아이템을 몇 개 얻었는지<$0C>그런 걸\n일일이 기억할 수는 없잖아?<$0C>그럴 때는\n메뉴에서 길드 수첩을 확인해 줘<$0C>현재 수락한 퀘스트 내용을\n확인할 수 있어<$0C>완료했는지, 미달성인지\n한눈에 알 수 있어 편리해",
      "퀘스트 수락 용어와 종결 문장을 자연스럽게 교정",
    ],
    12: ["도움?", "원문 단문 질문의 범위를 복원"],
    14: [
      "그거 써먹어야지.\n좋아, 전설의 용사가 되겠어!",
      "화자 단독 목표의 의미를 교정",
    ],
    42: [
      "후우……\n그 아이도 참……\n너무 꽉 끼잖아……",
      "후속 의상 대화에 맞게 きつい의 의미를 교정",
    ],
    48: [
      "과감하게,<$15>22를 누르고\n<$15>10으로 결정하면\n재빨리 데리러 와 줍니다!",
      "제어 토큰 인접 관계와 조작 설명을 교정",
    ],
    54: [
      "디노스는 적들 사이에 언니가 있어도\n날 위해 싸워 준댔어.\n어느 위선자님과는 딴판이지",
      "적 진영 관계와 비꼬는 대상 표현을 자연스럽게 교정",
    ],
    76: ["평범?", "되묻는 단어의 품사와 어조를 원문에 맞춤"],
    89: ["엑!! 아니, 그건……", "놀람 감탄사를 문맥에 맞게 교정"],
    96: ["뭐, 뭐야, 갑자기……\n그렇게 닮았어?", "중복 문장부호를 제거"],
    100: [
      "저기〜, 리피아.\n실제로 딱딱해진 게 아니라\n제 엉덩이는 머리처럼 부드럽슴다",
      "カチコチ를 결빙이 아닌 딱딱함으로 교정",
    ],
    101: [
      "자, 거기서 삐치지 마.\n그런 반응을 하고 있으면\n어린애 티를 못 벗는다고?",
      "子どもを卒業의 관용 의미를 자연스럽게 교정",
    ],
    113: [
      "모르는구나……\n식사는 오감으로 맛보는 거야!\n다 함께 즐겁고 맛있게 먹어야지",
      "중복 문장부호를 제거",
    ],
    132: [
      "(리피아……\n　저도 그렇슴다…… 즐겁슴다……\n　하지만…… 저는……)",
      "니콜 말투의 오탈자를 교정",
    ],
    136: [
      "그렇슴다, ２, ３개월 뒤쯤?\n그 정도 지나면 귀여운 새끼 고양이들한테\n둘러싸여 있지 않겠슴까?",
      "원문의 수치를 보존",
    ],
    144: [
      "너는 스스로를\n풀헤임의 보물!\n이라고 단언하잖아",
      "세계명 표기를 용어집에 맞춤",
    ],
    158: [
      "거의 타고난 것이지만\n끊임없는 노력의 결실로\n조금 더 부드러워집니다",
      "努力の結晶의 관용 의미를 자연스럽게 교정",
    ],
    160: ["오이겐이 날 보고 웃었어〜", "笑われた의 어감이 과도하게 적대적이지 않도록 교정"],
    173: ["정말 닮았네", "似ている를 동일함이 아닌 닮음으로 교정"],
    174: [
      "하지만……\n응. 제법 잘 어울리잖아?",
      "중복 문장부호를 제거",
    ],
  },
};

for (const [batch, batchRevisions] of Object.entries(revisions)) {
  const sourcePath = path.join("work", "translation", "tm_v2", "batches", "source", `${batch}.jsonl`);
  const draftPath = path.join("work", "translation", "drafts", `${batch}.jsonl`);
  const reviewedPath = path.join("work", "translation", "reviewed", `${batch}.jsonl`);
  const reviewPath = path.join("work", "translation", "reviews", `${batch}_review.json`);
  const readRows = (file) =>
    fs.readFileSync(file, "utf8").split(/\r?\n/).filter(Boolean).map(JSON.parse);
  const sources = readRows(sourcePath);
  const drafts = readRows(draftPath);
  const modificationList = [];
  const reviewed = sources.map((source, offset) => {
    const index = offset + 1;
    const revision = batchRevisions[index];
    const before = drafts[offset].translation_ko;
    const after = revision ? revision[0] : before;
    if (revision) {
      modificationList.push({
        index,
        tm_id: source.tm_id,
        before,
        after,
        reason: revision[1],
      });
    }
    return { ...source, translation_ko: after };
  });

  fs.mkdirSync(path.dirname(reviewedPath), { recursive: true });
  fs.mkdirSync(path.dirname(reviewPath), { recursive: true });
  fs.writeFileSync(reviewedPath, `${reviewed.map((row) => JSON.stringify(row)).join("\n")}\n`, "utf8");
  fs.writeFileSync(
    reviewPath,
    `${JSON.stringify(
      {
        batch,
        draft_author: "/root/audit_boundary_integration",
        reviewer: "/root/translate_batch_0008",
        translation_method: "Codex 내부 모델 전용",
        external_services_used: false,
        reviewed_record_count: reviewed.length,
        modified_count: modificationList.length,
        modifications: modificationList,
      },
      null,
      2,
    )}\n`,
    "utf8",
  );
  process.stdout.write(`${batch} ${modificationList.length}\n`);
}
