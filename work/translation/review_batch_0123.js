const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..');
const batchId = 'batch_0123';
const sourceRel = `work/translation/tm_v2/batches/source/${batchId}.jsonl`;
const draftRel = `work/translation/drafts/${batchId}.jsonl`;
const reviewedRel = `work/translation/reviewed/${batchId}.jsonl`;
const reportRel = `work/translation/reviews/${batchId}_review.json`;
const readJsonl = (rel) => fs.readFileSync(path.join(root, rel), 'utf8')
  .trimEnd().split(/\r?\n/).map(JSON.parse);

const source = readJsonl(sourceRel);
const draft = readJsonl(draftRel);

const corrections = new Map([
  [1, { after: `여기서 세계 각지로
메리디아 제품이
출하됩니다<$0C>메리디아의 공산품은
튼튼하고 쉽게 낡지 않는다고
전국 각지에서 호평이에요!`, category: 'natural_korean', reason: '열화라는 직역투 대신 공산품이 쉽게 낡지 않는다는 자연스러운 한국어로 다듬었다.' }],
  [3, { after: `옷차림을 갖춰 봤지만
그럴듯한 건 갓 꺼내 입은
순례자 복장뿐……<$0C>속사람은 그대로라
더워서 견딜 수가 없습니다.
사실 북쪽 출신이거든요`, category: 'meaning', reason: '中身はそのまま는 옷 속 사람이 바뀌지 않았다는 뜻이므로 의복 안쪽이라는 오해를 바로잡았다.' }],
  [6, { after: `흉벽 위로 펼쳐진 하늘을 보고 있으면
시간을 잊을 수 있을 것 같습니다……`, category: 'terminology', reason: '胸壁의 건축 용어 의미를 살려 성벽이 아닌 흉벽으로 교정했다.' }],
  [7, { after: `……리얼이니 이매지널이니
내 알 바냐`, category: 'proper_noun', reason: '고유 개념 リアル의 프로젝트 표기 리얼을 적용했다.' }],
  [18, { after: `알스 황제가 제창한
신제국 헌장이 곧 공포된다.
그때까지 마음 단단히 먹고 기다려라`, category: 'meaning', reason: '発布는 발포가 아니라 법령을 널리 알리는 공포이므로 의미를 바로잡았다.' }],
  [23, { after: `여기가 공중 회랑 라스카다……`, category: 'proper_noun', reason: '空中回廊ラスカーダ의 프로젝트 표기 공중 회랑 라스카다를 적용했다.' }],
  [26, { after: `무예관에 무슨 일이 생긴 듯해서
아가씨와 여기까지 왔습니다만……<$0C>다리가 굳어 이 이상
앞으로 나아갈 수 없을 것 같습니다……`, category: 'meaning', reason: 'お嬢様를 남성 호칭 도련님으로 옮긴 오류를 아가씨로 바로잡고 武芸塾 표기를 통일했다.' }],
  [28, { after: `여기는 『초승달 여관』이라는군.
동화 속 달의 이름을 붙이다니
옛사람은 멋진 감각을 가졌어`, category: 'proper_noun', reason: '반복 지명 眉月の宿의 기존 프로젝트 표기 초승달 여관을 적용했다.' }],
  [42, { after: `상사님이 부럽습니다.
바이스 황태자가 눈여겨보는 건
장군이나 당신 정도뿐입니다`, category: 'rank', reason: '군 계급 曹長의 고정 번역 상사를 적용했다.' }],
  [50, { after: `병사들 이야기를 엿들었는데
벌레도 못 죽일 알스 황자가
수배자가 됐대!<$0C>제국을 배신한 것도 모자라
오르키나교에 심취했다더군.
사실이면 위험한 이야기야!`, category: 'meaning', reason: '兵隊の話를 군대 자체가 아니라 병사들이 나눈 이야기라는 뜻으로 명확히 했다.' }],
  [51, { after: `단말기가 놓인 방은 바로 저기다!
하얀 창을――멈추겠어!`, category: 'meaning', reason: '止める는 상대에게 내리는 명령이 아니라 화자의 행동 의지이므로 1인칭 결의로 교정했다.' }],
  [59, { after: `변조되어 있었다고요?
하지만 이건 돌…… 맞죠?`, category: 'meaning', reason: '改ざん은 개조가 아니라 기록이나 내용을 변조했다는 뜻이다.' }],
  [63, { after: `묘전에 꽃을 바치고 왔습니다.
아내가 좋아하던 꽃이 예쁘게 피어서
보여 주고 싶어서요……`, category: 'voice', reason: '앞뒤 문맥의 정중한 남성 화법에 맞춰 반말로 바뀐 초안을 존댓말로 복원했다.' }],
  [64, { after: `사랑을 동경하는 후배`, category: 'idiom', reason: '恋に恋する를 한국어에서 부자연스러운 중복 표현 대신 사랑 자체를 동경한다는 뜻으로 옮겼다.' }],
  [65, { after: `지금의 디아만트는
애도에 잠긴 슬픈 도시――
당신도 기도하세요……`, category: 'natural_korean', reason: '도시가 상복을 입는다는 직역을 애도에 잠긴 도시라는 자연스러운 표현으로 다듬었다.' }],
  [70, { after: `구, 군인이십니까!?
갑자기 몬스터들이 나타나
눈 깜짝할 사이에 이렇게……<$0C>저는 위생병인데도
누구 １명 구하지 못해서……<$0C>싸우실 거라면
이걸 가져가십시오.
분명 도움이 될 겁니다`, category: 'numeric_fidelity', reason: '원문의 전각 숫자 １을 누락하지 않고 복원했다.' }],
  [76, { after: `아침에는 새 지저귐을 듣고
밤에는 도시의 소란을 등지고 잠들고……<$0C>이렇게 들으면 나이 드는 것도
나쁘지 않다고 생각되지 않나요?
――그 젊음으로는 아직 무리일까요`, category: 'voice', reason: '앞뒤 대사의 정중한 화법을 유지하고 새소리라는 포괄어 대신 지저귐의 뉘앙스를 살렸다.' }],
  [103, { after: `『고스로온대』라니
너희 용병들이 한판 뜨려는 거냐……<$0C>뭐 좋아, 그 승부
받아 주지`, category: 'proper_noun', reason: '기존 번역에서 확인되는 조직명 ゴスローン隊의 표기 고스로온대를 적용하고 대사의 의미를 자연스럽게 정리했다.' }],
  [107, { after: `마타타비 형제사의 열넷째 아들`, category: 'proper_noun', reason: '조직명 股旅兄弟舎의 프로젝트 표기 마타타비 형제사를 적용했다.' }],
  [113, { after: `……`, category: 'punctuation', reason: '일본식 중점과 마침표가 혼재된 초안을 한국어 말줄임표로 정리했다.' }],
  [114, { after: `잠깐. 마슈가르는
소아라도 그 이름을
말하지 않았나?`, category: 'proper_noun', reason: '로그레스 マシュガル의 프로젝트 표기 마슈가르를 적용했다.' }],
  [119, { after: `초승달 여관`, category: 'proper_noun', reason: '반복 지명 眉月の宿의 기존 프로젝트 표기 초승달 여관을 적용했다.' }],
  [124, { after: `나는 이 도시에서 태어나
계속 자다 경비직을 맡고 싶다고
병사장에게 요청해 왔어<$0C>염원이 이루어져 이곳에
배치됐지만……
보다시피 도시는 텅 비었어<$0C>정말 쓸쓸한 기분이야……`, category: 'natural_korean', reason: '병사장에게 경비직을 희망했다는 일본어식 결합을 자연스러운 한국어 문장으로 다듬었다.' }],
  [129, { after: `신경 쓰지 마.
자, 가자`, category: 'idiom', reason: 'こっちの話だ는 문자 그대로 이쪽 이야기라는 뜻이 아니라 상대가 신경 쓰지 않아도 된다는 관용 표현이다.' }],
  [130, { after: `제국으로 돌아가려면
갈루아 대열곡을 지나야
하니까……`, category: 'proper_noun', reason: '지명 ガロア大裂溝의 프로젝트 표기 갈루아 대열곡을 적용했다.' }],
  [139, { after: `우리 토파지온 마을 주민 일동은
알스 폐하의 새로운 제국을
지지하기로 결정했습니다<$0C>바이스 황태자도
존경할 만한 분이었지만
다소 피를 지나치게 탐했습니다……`, category: 'natural_korean', reason: '피를 너무 좋아했다는 직역을 호전성을 뜻하는 자연스러운 표현으로 다듬었다.' }],
  [141, { after: `그래
너무 많이 주지는 마`, category: 'meaning', reason: '먹이를 あげすぎない는 너무 많이 올리지 말라는 뜻이 아니라 너무 많이 주지 말라는 뜻이다.' }],
  [150, { after: `어서 제국에서 쿠데타라도
일어나면 좋겠어……<$0C>이런 생활을 계속하다간
정신이 이상해질 것 같아.
누구든 좋으니 구해 줘……`, category: 'grammar', reason: '언제까지 계속하면이라는 어색한 조건절을 자연스러운 한국어로 바로잡았다.' }],
  [165, { after: `일반 감방`, category: 'function', reason: '감옥 구역의 房은 일반실이 아니라 감방을 뜻하므로 화면 기능에 맞게 교정했다.' }],
  [170, { after: `그런 줄 몰랐어요……
생각해 봐야
하는 거군요……`, category: 'voice', reason: '한 문장 안에서 반말과 존댓말이 섞인 초안을 정중한 말투로 통일했다.' }],
  [172, { after: `연애<$15>00<$15>00<$15>00
일<$15>00
양동<$15>00<$15>00<$15>00<$0C>마음에 둔 이성 또는 동성의
관심을 끌지 않을 수 없는 １일.
잘 처신해 행복해집시다<$0C>행운을 부르는 물건은
페럿 인형.
가슴에 안고 큰 소리로 노래합시다`, category: 'numeric_fidelity', reason: '원문에 명시된 전각 숫자 １을 하루로 치환하지 않고 보존했다.' }],
  [174, { after: `각오를 다지는 병사`, category: 'natural_korean', reason: '기합이 들어간이라는 번역투를 인물 상태를 자연스럽게 드러내는 표현으로 다듬었다.' }],
  [175, { after: `아, 이건`, category: 'meaning', reason: '감탄사 ああ를 동의 표현 그래로 오역한 부분을 발견의 감탄으로 바로잡았다.' }]
]);

const reviewed = draft.map((row, i) => {
  const correction = corrections.get(i + 1);
  return correction ? { ...row, translation_ko: correction.after } : { ...row };
});

const modifications = [...corrections.entries()].map(([index, correction]) => ({
  index,
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
  review_dimensions: ['meaning', 'function', 'numeric fidelity', 'proper nouns', 'natural Korean', 'particles', 'control tokens', 'line breaks'],
  modifications,
  verification_execution: {
    status: 'deferred_by_user_instruction',
    executed_tools: [],
    not_executed: ['validator', 'fit', 'encoding', 'boundary_audit'],
    note: '사용자 지시에 따라 별도 validator, fit, encoding, boundary audit를 실행하지 않음.'
  }
};

fs.mkdirSync(path.dirname(path.join(root, reviewedRel)), { recursive: true });
fs.mkdirSync(path.dirname(path.join(root, reportRel)), { recursive: true });
fs.writeFileSync(path.join(root, reviewedRel), reviewed.map((row) => JSON.stringify(row)).join('\n') + '\n', 'utf8');
fs.writeFileSync(path.join(root, reportRel), JSON.stringify(report, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({ batch: batchId, reviewed: reviewed.length, modified: modifications.length, reviewed_output: reviewedRel, report: reportRel }));
