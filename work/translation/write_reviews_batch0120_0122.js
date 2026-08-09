const fs = require("fs");
const path = require("path");

const ROOT = "work/translation";
const REVIEWER = "/root/translate_batch_0009";
const DRAFT_AUTHOR = "/root/audit_boundary_integration";

const direct = (after) => () => after;
const swap = (from, to) => (before) => {
  if (!before.includes(from)) {
    throw new Error(`Expected text not found: ${JSON.stringify(from)}`);
  }
  return before.replace(from, to);
};

const batches = {
  batch_0120: [
    [9, "natural_korean", "일본어 장음 부호가 남은 기합을 한국어 발음으로 다듬음", direct("티! 투!\n티야아!")],
    [12, "proper_noun", "ラルク를 라군으로 잘못 옮긴 인명 오역을 수정함", swap("라군 상사", "라르크 상사")],
    [15, "numeric_fidelity", "１番의 수치 정보를 보존하면서 최상급 의미가 자연스럽게 드러나도록 수정함", swap("……공화국이 １번 안전하겠지?", "……공화국이 안전도 １등이겠지?")],
    [33, "meaning", "원문에 없는 보조사 '도'를 제거해 대상을 정확히 지칭함", swap("당신들도 제국 사람이지!?", "당신들은 제국 사람이지!?")],
    [57, "natural_korean", "'하나같이 전부'의 중복 표현을 정리함", swap("여기 경비병들은 하나같이\n전부 허수아비야!", "여기 경비병들은 하나같이\n허수아비야!")],
    [58, "voice", "あんた의 반말 어조에 맞게 호칭을 조정함", swap("당신이 이거 맡아 둬", "네가 이거 맡아 둬")],
    [62, "numeric_fidelity", "１番을 보존하면서 부자연스러운 '１번 가까운'을 자연스럽게 다듬음", direct("고작 옷이라고 생각하겠지만\n옷은 우리에게 가장 가까운\n１순위 동반자라고 생각해")],
    [68, "terminology", "仕立屋를 프로젝트 내 점포 용어인 양장점으로 통일함", direct("『안나』의 양장점")],
    [105, "meaning", "不謹慎을 종교적 불경이 아니라 상황에 맞지 않는 경솔함으로 수정함", direct("도시가 복구되는 마당에\n이런 걸 신경 쓰고 있다니……\n나도 참 경솔하네")],
    [122, "natural_korean", "어색한 조사 결합을 자연스러운 한국어 문장으로 다듬음", direct("마을 주민이 멋대로 밖에 나가면\n당신들 입장에서도\n곤란하지 않을까?")],
    [136, "meaning", "고백하지 않으면 거절할 수도 없다는 인과를 명확하게 복원함", direct("눈앞의 남자 좀 봐.\n벌써 １시간이나 우물쭈물하고 있어<$0C>고백할 거면\n빨리 좀 하라는 거지.\n고백 안 하면 거절도 못 하잖아")],
    [138, "voice", "군인 어조가 마지막 줄까지 일관되도록 종결을 수정함", direct("먼 곳에 계속 있다 보니\n제국이 그리워지는군……\n어서 돌아가고 싶군")],
    [146, "voice", "한 대사 안의 존댓말 종결을 통일하고 とことん의 의미를 살림", direct("이제 내 목소리는\n그에게 닿을 것 같지 않습니다.\n할 거라면 끝까지 해 줬으면 합니다")],
    [158, "meaning", "血の繋がりは薄い를 자연스러운 혈연 관계 표현으로 수정함", direct("집을 지으려고 합니다.\n이 아이와 함께 살 집을요<$0C>우리의 혈연은 가깝지 않지만\n이 도시에서 고난을 함께 이겨 낸\n무엇보다 강한 유대가 있으니까요……")],
    [164, "voice", "정중한 화자의 종결과 1인칭을 문장 전체에서 통일함", direct("디아만트에도\n졸부 귀족이 늘어나서\n귀족의 품격은 계속 떨어지고 있습니다――<$0C>작위는 돈으로 사는 게 아니라\n수여받는 것――\n……저는 그렇게 생각합니다")],
    [166, "meaning", "乱心을 '난심을 품다'가 아니라 이성을 잃는 의미로 바로잡음", direct("새로 왕좌에 오른\n알스 황제마저 이성을 잃고\n나라를 어지럽힌다고 들었습니다<$0C>이쯤 되니\n역시 메리디아의 혈통은\n저주받았을지도 모르겠군요")],
    [169, "numeric_fidelity", "１番の夢의 서열 의미를 수치를 유지한 채 자연스럽게 표현함", direct("용박탑 위에서\n풀헤임을 내려다보는 게\n내 꿈 중 １순위야!")],
    [170, "meaning", "教えに殉じる를 문맥에 맞는 신앙적 헌신 표현으로 수정함", direct("불온한 세상이기에 더욱\n가르침에 몸을 바쳐야 한다고 생각합니다<$0C>괜찮으시다면\n함께 성도의 대성당까지\n기도를 올리러 가시죠……")],
    [172, "natural_korean", "끝나지 않은 연결형 종결을 완결된 구어체로 다듬음", direct("길드에 먼저 들어갈지\n아니면 의상점으로 갈지――<$0C>내 고민은――\n사라질 것 같지 않네")],
    [174, "punctuation", "문장 중간에 잘못 들어간 마침표를 제거함", swap("현재 원로원에서는.", "현재 원로원에서는")],
    [175, "voice", "거친 반말 화자의 あんた를 자연스러운 반말 호칭으로 수정함", direct("미안, 더는 못 들 것 같아\n네게 돌려줄게")],
    [184, "meaning", "ぶっちぎって를 '따돌리고 붙잡다'라는 모순된 표현 대신 단숨에 제압한 의미로 수정함", direct("어이, 라르크.\n난 알겠어……네가\n그런 얼굴을 하고 있으니 말이야!<$0C>드디어 해냈구나?\n마슈가르 자식을 단숨에 제압해서\n붙잡은 거지!<$0C>아니야?")],
    [190, "grammar", "생략으로 불완전해진 마지막 문장을 자연스럽게 완결함", direct("움직이지 말라고 해도 말이야\n뭐 어때.\n고양이 정도는 도망쳐도 되잖아")],
  ],
  batch_0121: [
    [5, "meaning", "後ろ向き의 성격·방향 중의성을 한국어 말장난으로 살림", direct("내 성격이 너무 뒤만 본다고\n친구에게 자주 지적받는다\n하지만 걸을 때는 앞을 본다<$0C>무슨 점이 뒤만 본다는 건지\n밤늦게까지 그를 추궁하고 싶다")],
    [8, "grammar", "誰１人의 부정 호응을 자연스러운 한국어로 수정함", swap("누구 １명 남을 생각하지 않아", "단 １명도 남을 생각하지 않아")],
    [16, "numeric_fidelity", "１人でも의 '혼자서도' 의미를 수치를 유지해 자연스럽게 표현함", swap("……나는 １명이어도 살아갈 수 있어.", "……나는 １명만으로도 살아갈 수 있어.")],
    [30, "meaning", "乱心을 '난심을 품다'가 아니라 이성을 잃는 의미로 바로잡음", swap("알스 폐하께서는 난심을 품으셨다……", "알스 폐하께서는 이성을 잃으셨다……")],
    [40, "natural_korean", "일본어 물결표가 남은 응시 의태어를 한국어 표기로 다듬음", swap("지〜〜긋", "지이이긋")],
    [65, "meaning", "元首를 군 계급이나 원수로 오해하지 않도록 국가원수로 명확히 함", swap("메리디아 제국의 원수가", "메리디아 제국의 국가원수가")],
    [68, "meaning", "後日을 먼 훗날이 아니라 추후 일정이라는 의미로 수정함", swap("훗날 집무실에서", "추후 집무실에서")],
    [109, "meaning", "害された의 피격·피해 의미를 모호한 '당했다' 대신 명확히 표현함", swap("제국 병사가 황자에게 당했다는 건", "제국 병사가 황자에게 해를 입었다는 건")],
    [112, "natural_korean", "중복된 설명형 종결을 간결하고 자연스럽게 다듬음", direct("평화로운 건 좋은 일이죠……\n그래야 자다답죠")],
    [115, "numeric_fidelity", "１人で의 혼자 남은 상황을 수치를 유지해 자연스럽게 표현함", direct("우리 가족이 새까맣게 타서\n움직이지 않게 됐으니까……\n나, 계속 １명만 남아 울고 있었어<$0C>그랬더니 언니가 와서\n나한테 말을 걸어 줬어")],
    [127, "meaning", "可憐을 가련함이 아니라 사랑스러운 모습이라는 의미로 수정함", swap("가련해……", "사랑스러워……")],
    [130, "natural_korean", "手間をかけさせた의 관용적 의미를 자연스럽게 옮김", direct("아, 고마워\n번거롭게 했네")],
    [131, "meaning", "질문의 대상이 자기 자신임을 명확히 하고 자연스러운 표현으로 다듬음", direct("자기 자신에게서 １번 마음에 드는 점은?\n――자, 말해 봐")],
    [134, "natural_korean", "喪失した를 어색한 관형 표현 대신 자연스러운 인물 라벨로 수정함", direct("상실을 겪은 소녀")],
    [155, "proper_noun", "설정 고유명 イーサ神을 이사신으로 통일함", swap("이사 신이 조금 불쌍해……", "이사신이 조금 불쌍해……")],
    [157, "punctuation", "대사에 남은 일본어 물결표를 한국어 표기로 바꿈", swap("잠깐만〜!", "잠깐만~!")],
    [166, "meaning", "세계 변화가 낳는 軋み를 문자 그대로 삐걱임이 아닌 마찰로 다듬음", swap("변하는 세계가 낳는 삐걱임입니다", "변하는 세계가 낳는 마찰입니다")],
    [172, "meaning", "それにしても를 역접이 아닌 화제 전환 표현으로 수정함", swap("그래도 정말 굉장한 신기루였어.", "그나저나 정말 굉장한 신기루였어.")],
    [184, "natural_korean", "酒に呑まれる의 관용적 의미를 자연스럽게 표현함", swap("예전에는 술에 먹히는", "예전에는 술에 휘둘리는")],
    [189, "meaning", "ねぇ의 부름말을 동의 표현으로 오역한 부분을 수정함", direct("제가 도움이 된다면……\n있잖아, 라르크")],
    [190, "meaning", "금속이 熱を帯びる 상황을 화가 난다는 뜻이 아니라 달아오르는 의미로 수정함", swap("열을 받으면", "달아오르면")],
  ],
  batch_0122: [
    [5, "terminology", "積み荷主를 자연스러운 물류 용어인 화주로 수정함", direct("젊은 화주")],
    [7, "meaning", "숨은 상태가 앞으로 들킬 수 있다는 인과와 시제를 바로잡음", swap("숨어 있는 게 들키니까", "숨어 있는 게 들킬 테니까")],
    [32, "natural_korean", "명사형으로 끊긴 감사 문장을 자연스럽게 연결함", direct("그를 구해 준 데 대해\n진심으로 감사한다")],
    [39, "natural_korean", "방향 조사 '별로'의 중의성을 피하도록 표현을 다듬음", swap("별로 가는 배", "별로 향하는 배")],
    [47, "natural_korean", "일본어 물결표가 남은 하품 의성어를 한국어 표기로 다듬음", swap("하아〜암……", "하아암……")],
    [48, "punctuation", "노랫소리와 말끝에 남은 일본어 장음·물결표를 한국어 표기로 바꿈", direct("루루루루~♪\n……이 노래?\n투레밀리아의 전통 창가야<$0C>나도 어릴 때 카르분클루스의\n가극장에서 친구들과 불렀어~")],
    [49, "punctuation", "일본어식 점 세 개와 마침표를 프로젝트 말줄임표로 통일함", direct("이제 당신과는 함께할 수 없어……")],
    [61, "meaning", "喪に服する를 문자 그대로 상복을 입는 것이 아니라 상중에 드는 관용 표현으로 수정함", direct("황족에게 불행한 일이 생기면\n제도 전체가 상중에 들어\n며칠 동안 가게가 영업하지 않아<$0C>그래서 오늘은 사재기하러 왔어.\n굶어 죽어서 마하트 폐하의\n뒤를 따르는 건 사양이거든")],
    [64, "terminology", "救援要請를 문맥에 맞는 지원 요청으로 수정함", swap("구원 요청", "지원 요청")],
    [67, "natural_korean", "직역투 인물 라벨을 자연스러운 동작 표현으로 수정함", direct("살짝 미소 짓는 병사")],
    [76, "meaning", "モンスターよけ를 퇴치가 아니라 접근 방지 장치로 수정함", swap("몬스터 퇴치 장치", "몬스터 방지 장치")],
    [77, "punctuation", "대사에 남은 일본어 물결표를 한국어 표기로 바꿈", swap("형님〜", "형님~")],
    [91, "natural_korean", "바닷바람 때문에 몸에 소금기가 밴다는 뜻을 자연스럽게 표현함", direct("여기서 경비하면\n온몸에 소금기가 배어서\n조금 싫단 말이죠……")],
    [119, "meaning", "景気悪そうな顔의 말장난성 표현을 문맥에 맞는 침울한 표정으로 다듬음", direct("경기도 나빠졌으니\n오늘은 화끈하게\n카지노에서 즐기고 올까……<$0C>오락은 마음에 잘 듣는 약이야.\n싫은 일은 전부 잊고\n내일을 향해 재충전할 수 있지<$0C>……너도 꽤나\n죽상을 하고 있잖아.\n유흥가에라도 다녀와")],
    [121, "meaning", "働き者를 직업인 일꾼이 아니라 부지런한 성격의 인물 라벨로 수정함", direct("부지런한 사람")],
    [127, "punctuation", "늘인 말끝에 남은 일본어 장음 부호를 한국어 표기로 바꿈", swap("나, 재미없어ー", "나, 재미없어~")],
    [137, "natural_korean", "단어 내부에 남은 일본어 물결표를 제거해 자연스럽게 다듬음", swap("느긋〜하게", "느긋하게")],
    [146, "terminology", "トゥレミリア魚가 언어명처럼 보이지 않도록 물고기 이름임을 명확히 함", swap("투레밀리아어는", "투레밀리아 물고기는")],
    [149, "punctuation", "늘인 말끝에 남은 일본어 물결표를 한국어 표기로 바꿈", swap("아직인가, 아직인가〜", "아직인가, 아직인가~")],
    [152, "natural_korean", "ざまあみろ의 인용과 종결을 자연스러운 구어체로 다듬음", direct("솔직히 제국 사람들이\n알스의 법 때문에 고통받든\n우리와는 상관없어<$0C>――아니, 오히려\n『꼴좋다』고 할 정도지")],
    [162, "punctuation", "늘인 말끝에 남은 일본어 물결표를 한국어 표기로 바꿈", swap("알스 님을 만나 보고 싶어〜", "알스 님을 만나 보고 싶어~")],
    [165, "natural_korean", "じゃあ死ねば의 도발적인 구어체를 자연스럽게 다듬음", direct("그럼 죽지 그래?")],
    [169, "grammar", "인용 조사와 대시의 위치를 바로잡음", direct("암살당했다느니――\n흉흉한 이야기도 오가니\n뭐가 진실인지……")],
    [180, "meaning", "邪神을 死神과 혼동한 '사신' 오역을 수정함", direct("어이, 그럼 이렇게\n나무가 돌이 된 게\n사악한 신의 저주라는 거야?")],
    [185, "meaning", "議会를 기관 자체가 아니라 반복되는 회의 일정이라는 문맥으로 수정함", swap("요즘은 아침부터 밤까지\n의회뿐이야……", "요즘은 아침부터 밤까지\n회의뿐이야……")],
    [193, "punctuation", "늘인 말끝에 남은 일본어 물결표를 한국어 표기로 바꿈", direct("크면\n아빠 배에 태워 달라고 할 거야~\n……부럽지?")],
    [195, "terminology", "仕立屋를 프로젝트 내 점포 용어인 양장점으로 통일함", direct("『모니카』의 양장점")],
  ],
};

function readJsonl(file) {
  return fs.readFileSync(file, "utf8").split(/\r?\n/).filter(Boolean).map(JSON.parse);
}

for (const [batchId, edits] of Object.entries(batches)) {
  const sourcePath = `${ROOT}/tm_v2/batches/source/${batchId}.jsonl`;
  const draftPath = `${ROOT}/drafts/${batchId}.jsonl`;
  const reviewedPath = `${ROOT}/reviewed/${batchId}.jsonl`;
  const reportPath = `${ROOT}/reviews/${batchId}_review.json`;
  const sourceRows = readJsonl(sourcePath);
  const draftRows = readJsonl(draftPath);
  const modifications = [];

  for (const [index, category, reason, transform] of edits) {
    const sourceRow = sourceRows[index - 1];
    const draftRow = draftRows[index - 1];
    const before = draftRow.translation_ko;
    const after = transform(before);
    if (before === after) {
      throw new Error(`${batchId} index ${index}: edit produced no change`);
    }
    draftRow.translation_ko = after;
    modifications.push({
      tm_id: sourceRow.tm_id,
      source_text: sourceRow.source_text,
      before,
      after,
      category,
      reason,
    });
  }

  fs.mkdirSync(path.dirname(reviewedPath), { recursive: true });
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });
  fs.writeFileSync(reviewedPath, `${draftRows.map((row) => JSON.stringify(row)).join("\n")}\n`, "utf8");

  const report = {
    schema: "arf-translation-independent-review-v1",
    batch_id: batchId,
    reviewer: REVIEWER,
    draft_translator: DRAFT_AUTHOR,
    draft_author: DRAFT_AUTHOR,
    independent_review: true,
    translation_engine_policy: "Codex internal models only",
    external_translation_services_used: [],
    external_translation_models_or_apis_used: [],
    source: sourcePath,
    draft: draftPath,
    reviewed_output: reviewedPath,
    reviewed_units: draftRows.length,
    modified_units: modifications.length,
    unchanged_units: draftRows.length - modifications.length,
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
  fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  process.stdout.write(`${batchId}: ${modifications.length} modified, ${draftRows.length} reviewed\n`);
}
