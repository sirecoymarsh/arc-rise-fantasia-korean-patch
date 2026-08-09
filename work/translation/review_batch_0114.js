const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..');
const batchId = 'batch_0114';
const sourceRel = `work/translation/tm_v2/batches/source/${batchId}.jsonl`;
const draftRel = `work/translation/drafts/${batchId}.jsonl`;
const reviewedRel = `work/translation/reviewed/${batchId}.jsonl`;
const reportRel = `work/translation/reviews/${batchId}_review.json`;
const readJsonl = (rel) => fs.readFileSync(path.join(root, rel), 'utf8')
  .trimEnd().split(/\r?\n/).map(JSON.parse);

const source = readJsonl(sourceRel);
const draft = readJsonl(draftRel);

const corrections = new Map([
  [5, { after: "그래…… 그렇구나……\n냄새를 없애 버리다니\n왠지 굉장하네……", category: 'meaning', reason: '앞 문맥의 채소가 고기 냄새를 없앤다는 뜻이 드러나도록 「消しちゃう」의 목적어를 복원했다.' }],
  [8, { after: "아무리 그래도 이제 질리기 시작했어……", category: 'natural_korean', reason: '「さすがにもう」의 누적된 지겨움을 자연스러운 구어체로 다듬었다.' }],
  [10, { after: "도시 어디에 가도\n험상궂은 병사뿐이라\n기분이 가라앉슴다……<$0C>지금 디아만트에는\n촉촉함이 부족함다……", category: 'meaning', reason: '「街中」를 한 거리로 한정하지 않고 도시 전체라는 뜻으로 바로잡았다.' }],
  [13, { after: "코핀도 살이 찌는구나……", category: 'natural_korean', reason: '「肥満がある」를 어색한 명사 결합 대신 자연스러운 한국어로 다듬었다.' }],
  [17, { after: "검 휘두르기 １００번 뒤에는\n달리기 ２００번!", category: 'meaning', reason: '「素振り」에 원문에 없는 목검 재질을 덧붙이지 않고 검을 휘두르는 훈련으로 고쳤다.' }],
  [38, { after: "알스 황제는 불쌍해<$0C>우리에게는 칭송받고\n자국민에게는 헐뜯기고 있잖아?\n――보통 반대라고 생각하지 않아?", category: 'grammar', reason: '「貶められている」의 피동·진행 의미가 빠진 문장을 완성했다.' }],
  [44, { after: "이게 사랑이라는 걸까요……\n지금까지 잿빛이던 제 세상에\n온갖 색의 꽃이 핀 듯한 충격입니다", category: 'natural_korean', reason: '「万色」를 한국어에서 낯선 직역 한자어 ‘만색’ 대신 자연스러운 표현으로 다듬었다.' }],
  [45, { after: "난 기다리는 게 서툴러……\n나쁜 상상만 하게 돼<$0C>아아, 빨리 돌아오면 좋겠는데……", category: 'meaning', reason: '「早く帰ってこないかな」를 귀환을 예측하는 말이 아니라 빨리 돌아오기를 바라는 독백으로 고쳤다.' }],
  [47, { after: "알스 폐하의 즉위는\n우리도 대환영이지만……\n지금은 축하할 기분이 아니야<$0C>바이스 황태자와 함께\n기함 파르세발이\n바다의 물거품이 됐잖아?<$0C>그건 우리 비광정\n정비사들에게\n특별한 비광정이었으니까……", category: 'proper_noun', reason: '기함 「パーセヴァル」의 승인 표기 ‘파르세발’을 적용했다.' }],
  [48, { after: "안목 있는 경비병", category: 'idiom', reason: '「違いのわかる」를 차이를 문자 그대로 안다는 뜻이 아니라 안목이 있다는 인물 성향으로 고쳤다.' }],
  [51, { after: "마슈가르와 계약 완료\n", category: 'proper_noun', reason: '로그레스 「マシュガル」의 프로젝트 표기 ‘마슈가르’를 적용했다.' }],
  [54, { after: "――암살당했다는 이야기인데\n유, 유령 같은 건 아니지……<$0C>발도 제대로 땅에 붙어 있고……", category: 'meaning', reason: '유령인지 확인하는 「足、ついてる」의 관용 상황이 드러나도록 고쳤다.' }],
  [57, { after: "군인들이 비광정을 쓴다면\n배 １척쯤 떼어 줬으면 해.\n정말 소중히 할게?", category: 'numeric_fidelity', reason: '원문의 전각 숫자 「１」을 복원하고 함선 한 척을 나눠 달라는 표현을 자연스럽게 다듬었다.' }],
  [60, { after: "바이스 황태자 때가 좋았어.\n모든 군인이 같은 방향을 봤지.\n――하지만 앞으로는 달라<$0C>군인들은 싸움 말고도\n자신들이 있을 곳을 찾아야 해", category: 'meaning', reason: '「居場所」를 주거지가 아니라 전투 외에 군인이 자리할 역할과 소속감의 의미로 바로잡았다.' }],
  [61, { after: "제도에서 멀어질수록\n제도의 영향력은 약해지고\n병사들을 제대로 관리할 수 없게 된다<$0C>그걸 막기 위해서라도\n병사를 감시할 자가 필요해.\n――바로 나처럼", category: 'natural_korean', reason: '「管理が行き届かなくなる」를 한국어의 자연스러운 관리 문장으로 다듬었다.' }],
  [64, { after: "노스 노와레교회와\n카르분클루스 원로원――\n두 곳 사이에 끼었어……<$0C>대체 그린힐 의장은\n왜 그런 고발을 한 걸까……", category: 'proper_noun', reason: '고유 조직명 「ノースノワーレ教会」를 프로젝트 표기 ‘노스 노와레교회’로 통일했다.' }],
  [72, { after: "못마땅해하는 병사", category: 'meaning', reason: '「苦々しい」를 단순히 씁쓸한 감정이 아니라 못마땅하고 불쾌한 태도로 다듬었다.' }],
  [73, { after: "도시 분위기가 바뀌었습니다.\n이제 마음껏\n일과인 산책을 계속할 수 있습니다", category: 'meaning', reason: '「街の雰囲気」를 거리 한 곳이 아니라 도시 전체의 분위기로 바로잡았다.' }],
  [78, { after: "지하 감옥의 죄인에 대해서는\n함구 명령을 받았으므로\n아무것도 말할 수 없다――", category: 'natural_korean', reason: '「口止めされている」를 어색한 ‘입단속을 당하다’ 대신 함구 명령을 받았다는 표현으로 고쳤다.' }],
  [82, { after: "싸움이 끝나면\n너희도 결판을 내야겠네.\n……여러 의미로<$15>00", category: 'natural_korean', reason: '「決着をつける」의 일본어식 한자 결합 ‘결착을 내다’를 자연스러운 ‘결판을 내다’로 고쳤다.' }],
  [83, { after: "신종과 현종은\n완전히 다른 생물……\n서로 이해할 필요조차 느끼지 못합니다", category: 'grammar', reason: '‘필요를 못 느끼다’의 부정 서술을 자연스러운 어순으로 고쳤다.' }],
  [84, { after: "요즘 교관이 엄격해<$0C>얼마 전 제국이 습격했을 때\n방어 스크린을 써서\n제국을 철수시켰잖아?<$0C>그 뒤로 교관이 의욕에 넘쳐서\n우리는 성가셔 죽겠어<$0C>그건 거의 알스 황제\n덕분인데 말이야……", category: 'meaning', reason: '「こっちはいい迷惑」를 화자 일행이 민폐라는 뜻으로 뒤집은 초안을, 그들이 성가신 피해를 보고 있다는 뜻으로 바로잡았다.' }],
  [86, { after: "……더워서 죽을 것 같아<$0C>그보다 주민도 거의\n없는데 일부러\n경비할 필요가 있나?", category: 'natural_korean', reason: '「ロクにいない」와 「っていうか」를 자연스러운 한국어 구어체로 다듬었다.' }],
  [97, { after: "칼라일 박사에게 연락이 왔는데\n그 일로 네게 묻고 싶은 게\n있다는군", category: 'natural_korean', reason: '「その件」를 어색한 ‘그 건’ 대신 자연스러운 ‘그 일’로 고쳤다.' }],
  [104, { after: "뭐, 그렇게 딱딱하게 굴지 마<$0C>나도 여러모로 조사했는데\n마슈가르는 ＊＊ 상공에서\n목격되는 일이 많은 듯해<$0C>그 근처를 날아보면\n만날 수 있지 않을까\n생각하는데……", category: 'proper_noun', reason: '「マシュガル」의 프로젝트 표기 ‘마슈가르’를 적용했다.' }],
  [110, { after: "전 대장이 있어 주면\n알콘대도 무적인데……<$0C>전 대장은 여자였지만\n남자도 놀랄 완력으로\n훌륭한 분이었습니다", category: 'proper_noun', reason: '부대명 「アルコーン隊」의 프로젝트 표기 ‘알콘대’를 적용했다.' }],
  [113, { after: "우리 집은 피해를 면했지만――\n다른 사람들의 피해는 끔찍해.\n대체 누가 이런 짓을……<$0C>호제아 성하께서 계신\n대성당이 무사했던 게\n불행 중 다행이야……", category: 'grammar', reason: '‘피해를 피하다’의 중복 표현과 피해자가 끔찍하다는 잘못된 서술 대상을 바로잡았다.' }],
  [118, { after: "친구를 죽이는 그 고통――\n이 내가 이어받겠다", category: 'meaning', reason: '「友を殺める」를 단순히 해치는 수준으로 약화하지 않고 친구를 죽이는 고통으로 옮겼다.' }],
  [121, { after: "알스 폐하의 신법이 어떻든\n우리는 황제 개인이 아니라\n메리디아 제국에 충성을 맹세한 몸――<$0C>여기까지 왔다면\n저도 사념을 전부 떨치고\n나라를 위해 목숨을 바칠 생각입니다", category: 'natural_korean', reason: '「忠誠を誓った身」를 자연스러운 한국어 관용 결합으로 다듬었다.' }],
  [129, { after: "명가의 맏이", category: 'meaning', reason: '성별이 명시되지 않은 「長子」를 ‘장남’으로 단정하지 않고 중립적인 ‘맏이’로 고쳤다.' }],
  [130, { after: "그게 무슨 쓸모가 있지?", category: 'natural_korean', reason: '「何の役に立つ」를 자연스러운 한국어 질문으로 다듬었다.' }],
  [136, { after: "나의 『노도』 로고스가 그대를 인도하리라", category: 'grammar', reason: '명사 수식에서 겹친 조사 ‘의’를 제거했다.' }],
  [140, { after: "바이스 황태자 휘하라면\n어떤 전쟁에서도 질 것 같지 않습니다", category: 'natural_korean', reason: '군 지휘 관계의 「元なら」를 자연스러운 ‘휘하라면’으로 다듬었다.' }],
  [153, { after: "가족과 나, 어느 쪽이 소중해?\n……같은 눈치 없는 말을 할 만큼\n나는 오만한 여자가 아니지만", category: 'meaning', reason: '「野暮なこと」를 단순히 촌스럽다는 뜻이 아니라 상대 사정을 헤아리지 못하는 눈치 없는 말로 고쳤다.' }],
  [158, { after: "모두 착하게 지내면\n제국의 나쁜 사람들도\n분명 없어질 거야……", category: 'natural_korean', reason: '「いい子にしていれば」를 어색한 ‘착한 아이로 있다’ 대신 자연스러운 표현으로 다듬었다.' }],
  [160, { after: "부흥에 힘쓰는 사람들을 보면\n도시의 본질은 건물이나 정치가 아니라\n그곳에 사는 사람임을 절감하게 돼<$0C>우리는 아무리 빼앗겨도\n몇 번이고 일어날 거야. 일어설 수 있어<$0C>――그들이 그런 기분이 들게 해 줘", category: 'meaning', reason: '복구에 힘쓰는 사람들이 화자에게 다시 일어설 수 있다는 기분을 준다는 인과와 주체를 분명히 했다.' }],
  [166, { after: "나도 디노스에게 말을\n전해 줬으면 하는데.\n어서 집에 돌아오라고", category: 'natural_korean', reason: '「伝言して欲しい」를 딱딱한 ‘전언’ 대신 자연스러운 대화체로 다듬었다.' }],
  [169, { after: "이사의 아이가 잠든 이사신을\n깨우면 사신 리얼에 의한\n결정화를 막을 수 있어", category: 'proper_noun', reason: '신명 「リアル」의 승인 표기 ‘리얼’을 적용했다.' }],
  [178, { after: "코핀은 귀엽지만\n너무 비싸서 귀족만 살 수 있어<$0C>그래서 １마리 정도\n가져갈까 하고\n나도 모르게 생각해서――", category: 'numeric_fidelity', reason: '원문의 전각 숫자 「１」을 번역문에 복원했다.' }],
  [192, { after: "알스 황제는 권력에 물든 건지\n아니면 형을 죽인 죄에 물든 건지\n고결한 영웅에서 폭군으로 전락했습니다<$0C>이 모든 건 제 신앙이\n부족한 탓이 분명합니다……\n오늘은 밤새 기도하겠습니다", category: 'voice', reason: '「毒された」를 문맥에 맞는 ‘물들다’로 다듬고 한 대사 안에서 섞인 반말과 존댓말을 정중체로 통일했다.' }],
  [196, { after: "바이스 황태자는\n아주 거하게\n일을 벌여 놨군……<$0C>이래서는 반감을 사도\n당연했을지 몰라……", category: 'natural_korean', reason: '「派手にやった」를 어색한 ‘화려하게 저지르다’ 대신 큰 피해를 벌여 놓았다는 구어체로 다듬었다.' }],
  [198, { after: "바이스 황태자처럼\n나라를 하나로 모을 통솔력이\n알스 님에게 있다면……", category: 'natural_korean', reason: '‘통솔력으로 모을 힘’이라는 중복 표현을 자연스럽고 간결하게 고쳤다.' }]
]);

const reviewed = draft.map((row, i) => {
  const correction = corrections.get(i + 1);
  return correction ? { ...row, translation_ko: correction.after } : { ...row };
});

const modifications = [...corrections.entries()].map(([index, correction]) => ({
  tm_id: source[index - 1].tm_id,
  source_text: source[index - 1].source_text,
  before: draft[index - 1].translation_ko,
  after: correction.after,
  category: correction.category,
  reason: correction.reason
}));

const report = {
  schema: 'arf-translation-independent-review-v1',
  batch_id: batchId,
  reviewer: '/root/audit_boundary_integration',
  draft_translator: '/root/review_batch_0058_0060',
  draft_author: '/root/review_batch_0058_0060',
  independent_review: true,
  translation_engine_policy: 'Codex internal models only',
  external_translation_services_used: [],
  external_translation_models_or_apis_used: [],
  source: sourceRel,
  draft: draftRel,
  reviewed_output: reviewedRel,
  reviewed_units: reviewed.length,
  modified_units: modifications.length,
  unchanged_units: reviewed.length - modifications.length,
  review_dimensions: [
    'meaning', 'function', 'numeric fidelity', 'proper nouns',
    'natural Korean', 'particles', 'control tokens', 'line breaks'
  ],
  modifications,
  verification_execution: {
    status: 'deferred_by_user_instruction',
    executed_tools: [],
    not_executed: ['validator', 'fit', 'encoding', 'boundary_audit'],
    note: '사용자 지시에 따라 별도 validator, fit, encoding, boundary audit를 실행하지 않았다.'
  }
};

fs.mkdirSync(path.dirname(path.join(root, reviewedRel)), { recursive: true });
fs.mkdirSync(path.dirname(path.join(root, reportRel)), { recursive: true });
fs.writeFileSync(path.join(root, reviewedRel), reviewed.map((row) => JSON.stringify(row)).join('\n') + '\n', 'utf8');
fs.writeFileSync(path.join(root, reportRel), JSON.stringify(report, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({ batch: batchId, reviewed: reviewed.length, modified: modifications.length, reviewed_output: reviewedRel, report: reportRel }));
