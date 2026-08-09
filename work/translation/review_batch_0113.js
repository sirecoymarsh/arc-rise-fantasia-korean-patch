const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..');
const batchId = 'batch_0113';
const sourceRel = `work/translation/tm_v2/batches/source/${batchId}.jsonl`;
const draftRel = `work/translation/drafts/${batchId}.jsonl`;
const reviewedRel = `work/translation/reviewed/${batchId}.jsonl`;
const reportRel = `work/translation/reviews/${batchId}_review.json`;
const readJsonl = (rel) => fs.readFileSync(path.join(root, rel), 'utf8')
  .trimEnd().split(/\r?\n/).map(JSON.parse);

const source = readJsonl(sourceRel);
const draft = readJsonl(draftRel);

const corrections = new Map([
  [2, { after: "이곳 사령관은 내 선생님이었어<$0C>이렇게 공화국 의원으로\n선출된 뒤에도\n꼼짝을 못 하겠어……", category: 'idiom', reason: '「頭が上がらない」를 글자 그대로 머리를 들지 못한다는 뜻이 아니라 상대에게 꼼짝 못 한다는 관용 의미로 고쳤다.' }],
  [14, { after: "언제 세상을 떠나도 괜찮도록\n이번에는 내가 잘해 줘야 해.\n소중한 가족이니까……", category: 'meaning', reason: '「いつ逝っても」가 죽음을 완곡하게 가리키는 표현임을 분명히 했다.' }],
  [18, { after: "――네, 알고 있습니다!\n스승님 같은 일류 장인이\n되도록 노력하겠습니다!", category: 'terminology', reason: '장인 문맥의 「親方」를 범죄 조직처럼 들리는 ‘두목’이 아니라 기존 문맥 표기 ‘스승님’으로 고쳤다.' }],
  [21, { after: "슬프고 힘든 때이기에……\n곁에 있는 그녀에게 청혼했습니다.\n분별없다는 말을 들어도 괜찮습니다<$0C>슬픔에 빠진 저를\n말없이 받쳐 주는 그녀와\n영원히 함께하고 싶습니다", category: 'meaning', reason: '「不謹慎」를 종교적 불경이 아니라 상황에 맞지 않아 분별없다는 비판의 의미로 바로잡았다.' }],
  [29, { after: "인간은 혈통을 거스를 수 없어.\n학살자의 혈족은\n학살자가 되는 게 당연해――<$0C>그래서 난 알스에게\n티끌만큼도 기대하지 않아.\n메리디아는 사기꾼 가문이니까", category: 'idiom', reason: '「爪の垢ほども」를 자연스러운 한국어 극소량 표현으로 다듬었다.' }],
  [38, { after: "일단 길드에 얼굴을 비추고 갈까", category: 'natural_korean', reason: '「顔を出しておく」의 관용 의미가 자연스럽게 드러나도록 고쳤다.' }],
  [41, { after: "출입을 엄격히 하라는\n알스 폐하의 칙명을 받았다<$0C>――수상한 짓은 꾸미지 마라, 알겠나?", category: 'meaning', reason: '「妙なことを考える」를 단순한 생각이 아니라 수상한 일을 꾸미지 말라는 경고로 옮겼다.' }],
  [42, { after: "요즘은 뭘 해도\n전혀 의욕이 나지 않습니다.\n이젠 될 대로 되라……는 기분입니다", category: 'idiom', reason: '「もうどうにでもなれ」를 자연스러운 체념의 관용 표현으로 다듬었다.' }],
  [44, { after: "아끼고 사랑하는 딸", category: 'natural_korean', reason: 'NPC 성격표 「慈しみ愛する」를 자연스러운 한국어 수식으로 고쳤다.' }],
  [59, { after: "제 얼굴이 분노에 떨고 있지 않습니까?\n어떻게든 마음을 진정시키고 싶은데\n도무지 가라앉지 않습니다", category: 'grammar', reason: '분노의 원인을 나타내는 조사를 자연스럽게 고쳤다.' }],
  [71, { after: "정말! 이제 됐잖아\n그런 실랑이는!", category: 'natural_korean', reason: '「そういうやりとり」를 문맥의 반복되는 말다툼에 맞는 ‘실랑이’로 다듬었다.' }],
  [76, { after: "마하트 폐하의 적자가\n반기를 들었다는 말이 퍼져 봐라.\n제국의 체면은 완전히 구겨진다", category: 'meaning', reason: '「と言ってみろ」를 상대에게 반기를 들었다고 말해 보라는 명령으로 오해한 초안을 바로잡았다.' }],
  [81, { after: "이 나라는 군인의 천국입니다.\n무기와 병기…… 무엇이든 일급품.\n군비로 곤란할 일은 없습니다<$0C>바이스 황태자는 대단한 분입니다.\n그렇게 젊은데도\n국가의 근간이 무엇인지 아십니다", category: 'natural_korean', reason: '「国の礎が何たるか」를 어색한 물리적 주춧돌 표현 대신 국가의 근간으로 다듬었다.' }],
  [89, { after: "레이가 돌아와서 다행이야.\n레이 부족이 계속되면\n가장 먼저 피해를 보는 건 하층인걸<$0C>이제 물가가 안정되면\n우리도 살겠어", category: 'grammar', reason: '‘피해받다’의 어색한 결합을 ‘피해를 보다’로 고쳤다.' }],
  [96, { after: "상관없어.\n우릴 먹을 수 있으면\n먹어 보라지", category: 'meaning', reason: '「食えるもんなら食ってみろ」의 도발 대상과 거친 어조를 자연스럽게 복원했다.' }],
  [101, { after: "천성이로군요", category: 'meaning', reason: '「性」를 부정적인 성질이 아니라 타고난 천성이라는 문맥으로 고쳤다.' }],
  [105, { after: "다시 찾아오시길 기다리겠습니다……", category: 'natural_korean', reason: '상점 인사 「またのお越し」를 자연스러운 접객 표현으로 다듬었다.' }],
  [106, { after: "부탁을 받아 줄 사람은\n내가 아니라 라르크 쪽이야.\n――그렇지, 라르크 군?", category: 'meaning', reason: '「よろしくされる」의 말장난을 화자의 부탁을 받을 사람이 라르크라는 뜻으로 분명히 했다.' }],
  [108, { after: "알스 황제를 믿은 나는\n지나치게 순진한 사람이었나 봐……", category: 'natural_korean', reason: '「途方もないお人好し」의 자조를 어색한 한자어 ‘호인’ 대신 자연스럽게 다듬었다.' }],
  [109, { after: "장수풍뎅이와〜\n독설가 평론가의 공통점은〜\n정답은〜<$0C>투구를 벗으면 죽습니다", category: 'wordplay', reason: '수수께끼의 관용 도입부 「その心は」를 한국어의 ‘정답은’으로 고쳐 말장난 구조를 살렸다.' }],
  [110, { after: "사다리 06（위）\n", category: 'formatting', reason: '원문의 전각 괄호 형식을 복원했다.' }],
  [136, { after: "……무슨 일 있었나요?\n도시 사람들이……\n상당히…… 부산한 듯해요……", category: 'meaning', reason: '「街の人たち」를 거리 위 사람들로 오해하지 않도록 도시 주민이라는 뜻으로 바로잡았다.' }],
  [137, { after: "요즘 라르크 씨\n저한테 이상하게 차갑지 않아요?\n너무 귀여운 나머지 그런 건가요?", category: 'meaning', reason: '「可愛さあまって」를 ‘미운 정’으로 뒤집은 의미 오류를 바로잡고 화자의 능청스러운 자찬을 살렸다.' }],
  [140, { after: "눈을 뜨면\n제국군이 사라져 있다――<$0C>그런 꿈같은 일은 없으려나?", category: 'natural_korean', reason: '「都合のいいこと」를 어색한 ‘편리한 일’ 대신 바라는 꿈같은 상황으로 다듬었다.' }],
  [141, { after: "좋은 예감은 전혀 안 맞는데\n나쁜 예감만은 반드시 맞아……\n――참 손해 보는 체질 같지 않아?", category: 'natural_korean', reason: '「損な体質だと思わない？」의 질문을 자연스러운 구어체로 고쳤다.' }],
  [142, { after: "코핀은 비싸게\n팔리잖아요?<$0C>그래서 １마리 정도\n납치할까 하고\n나도 모르게 생각해서――", category: 'numeric_fidelity', reason: '원문의 전각 숫자 「１」을 번역문에 복원했다.' }],
  [149, { after: "그 뒤 떠나 버리셔서……\n그러니까……", category: 'meaning', reason: '「出奔」를 한국어에서 거의 쓰지 않는 직역 한자어 ‘출분’ 대신 자취를 감추듯 떠났다는 뜻으로 고쳤다.' }],
  [151, { after: "그래, 위험하다고 하려면\n가시 정도는 있어야지", category: 'meaning', reason: '가시가 있어야 위험한 상대답다는 「くらいじゃないと」의 조건을 반대로 옮긴 초안을 바로잡았다.' }],
  [152, { after: "알스 님의 신제국 헌장을\n나는 기꺼이 받아들일 생각입니다<$0C>새로 정한 이 엄격한 법은\n알스 폐하께서 오르키나의 가르침에\n따라 만든 법일 테니까요……<$0C>알스 님과 아델 님은\n우리 오르키나 백성의\n마지막 남은 유일한 희망입니다……", category: 'natural_korean', reason: '「唯一最後の希望」를 자연스러운 한국어 수식 순서로 다듬었다.' }],
  [153, { after: "무성의한 경비병", category: 'natural_korean', reason: 'NPC 성격표 「いい加減」를 어색한 ‘대충대충인’ 대신 자연스러운 성격 표현으로 고쳤다.' }],
  [159, { after: "우리 남편은 옛날부터 그래<$0C>저거라든가\n이거라든가\n그거라든가<$0C>애매하게 말할 때가 많아서 말이야.\n그런 말투에 맞춰 주느라\n나는 힘들었어", category: 'natural_korean', reason: '「そんな調子に付き合う」를 남편과 동행한다는 뜻이 아니라 애매한 말투에 맞춰 주느라 힘들었다는 뜻으로 다듬었다.' }],
  [165, { after: "솔직히 난 알스 폐하가\n아델에게 속고 있다고 생각해<$0C>아델은 오르키나의 복수를 위해\n알스 폐하를 이용하는 것뿐이야.\n――어서 정신 차리면 좋겠어", category: 'meaning', reason: '「騙されてる」의 현재 진행 상태를 과거형으로 바꾼 시제 오류를 바로잡았다.' }],
  [167, { after: "투레밀리아 공화국군이 자랑하는\n알콘대다!\n자, 출진!!", category: 'proper_noun', reason: '부대명 「アルコーン隊」의 프로젝트 표기 ‘알콘대’를 적용했다.' }],
  [178, { after: "그나저나\n이 공장 구역의 공기는\n여전히 더럽군<$0C>원로원 의원들은\n어떻게든 한다고 하지만\n……언제가 될지", category: 'line_breaks', reason: '「それにしても」의 의미를 바로잡고 초안에서 합쳐진 첫 문단의 원문 줄바꿈 수를 복원했다.' }],
  [186, { after: "음……<$0C>하고 끙끙거리면\n조금 똑똑해 보이지 않아?", category: 'meaning', reason: '생각하는 척 「음……」 하는 모습을 신음으로 오해한 초안을 바로잡았다.' }],
  [199, { after: "마하트 폐하께서 붕어하신 지\n얼마 지나지도 않아\n바이스 황태자의 죽음――<$0C>너무 숨 가쁘게 돌아가서\n뭐가 뭔지 모르겠어요", category: 'grammar', reason: '「崩御から時間がたたない内に」를 자연스러운 시간 경과 표현으로 고쳤다.' }],
  [200, { after: "모처럼 디아만트와\n통상할 수 있게 되나\n싶었던 찰나에 이 꼴이야<$0C>신제국 헌장인지 뭔지는 몰라도\n이제 와서 통제 경제를 지향하다니\n달력도 제대로 못 읽나?", category: 'natural_korean', reason: '「と思った矢先にこれだ」의 낙담과 비꼼을 자연스러운 한국어로 다듬었다.' }]
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
