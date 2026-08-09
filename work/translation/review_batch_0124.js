const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..');
const batchId = 'batch_0124';
const sourceRel = `work/translation/tm_v2/batches/source/${batchId}.jsonl`;
const draftRel = `work/translation/drafts/${batchId}.jsonl`;
const reviewedRel = `work/translation/reviewed/${batchId}.jsonl`;
const reportRel = `work/translation/reviews/${batchId}_review.json`;
const readJsonl = (rel) => fs.readFileSync(path.join(root, rel), 'utf8')
  .trimEnd().split(/\r?\n/).map(JSON.parse);

const source = readJsonl(sourceRel);
const draft = readJsonl(draftRel);

const corrections = new Map([
  [7, { after: `『여기까지 도달하다니
　근성 있는 녀석이로다!』<$0C>『그 근성을 높이 사
　자무엘 무예관에
　입문하는 것을 허락하노라!』<$0C>라고 적혀 있다……`, category: 'proper_noun', reason: '반복 시설명 ザムエル武芸塾의 프로젝트 표기 자무엘 무예관을 적용했다.' }],
  [10, { after: `그렇군. 이 땅은
이사 신의 정원이자
벗의 묘비이기도 하다는 건가`, category: 'proper_noun', reason: '신명 イーサ神을 이름과 호칭이 구분되도록 이사 신으로 표기했다.' }],
  [15, { after: `파피르사그와
우르그라와
스쿠일이네`, category: 'proper_noun', reason: '로그레스 고유명 パピルサグ와 ウルグラ의 프로젝트 표기 파피르사그, 우르그라를 적용했다.' }],
  [17, { after: `알스 폐하를 공공연히 비판하는
병사들을 이해할 수 없다<$0C>제국을 위해 섬기겠다고 맹세한
그때의 충성 서약은
거짓이었다는 건가?`, category: 'natural_korean', reason: '兵士たちの気がしれない를 뜻이 분명한 자연스러운 한국어로 다듬었다.' }],
  [23, { after: `방금 그 말투, 들으셨어요?`, category: 'natural_korean', reason: '평서형으로 끝난 초안을 원문의 질문 의도와 한국어 어순에 맞게 바로잡았다.' }],
  [25, { after: `그린힐 의장이
암살당했다며 원로원은
발칵 뒤집혔어<$0C>시신도 못 찾았는데
어떻게 『암살』이라고 아는 걸까?`, category: 'idiom', reason: '大わらわだ를 벌집을 쑤신 듯하다는 직역 대신 발칵 뒤집혔다는 자연스러운 표현으로 옮겼다.' }],
  [31, { after: `운 좋게 폭격을
피할 수 있었지만
마음고생 탓에 몸이 상했습니다`, category: 'natural_korean', reason: '心労から体を壊す를 심로라는 번역투 대신 자연스러운 한국어로 다듬었다.' }],
  [35, { after: `■■４번째 승리■■
`, category: 'numeric_fidelity', reason: '원문의 전각 숫자 ４를 반각 숫자로 바꾸지 않고 복원했다.' }],
  [38, { after: `아, 미안……`, category: 'meaning', reason: '감탄사 ああ를 동의 표현 그래로 옮긴 오류를 사과에 앞선 감탄으로 바로잡았다.' }],
  [47, { after: `알스 황제의 즉위는
우리에게 더없는 기쁨입니다.
하지만 희생이 너무 컸습니다<$0C>앞날이 창창한 많은 젊은이가
이번 일로 목숨을 잃었습니다.
……지금은 애도할 때입니다`, category: 'idiom', reason: '喪に服する는 반드시 상복을 입는 행위가 아니라 애도한다는 뜻이므로 문맥에 맞게 교정했다.' }],
  [48, { after: `에블의 그란츠가
마슈가르를 연구했었지.
이야기를 들어보는 게 어때`, category: 'proper_noun', reason: '로그레스 マシュガル의 프로젝트 표기 마슈가르를 적용했다.' }],
  [63, { after: `아, 형님〜!
다들 절 괴롭힌단 말임다!`, category: 'voice', reason: '원문에 없는 말더듬을 제거하고 っスよ의 거친 후배 말투를 자연스럽게 살렸다.' }],
  [71, { after: `언제까지고 이곳에
매달려 있으면 제 아내는
편히 떠나지 못하겠지요……<$0C>저는 과거에 사로잡히지 않고
미래를 살기로 결심했습니다`, category: 'natural_korean', reason: '天に召されない를 특정 종교의 천국 표현으로 한정하지 않고 문맥에 맞는 한국어로 다듬었다.' }],
  [73, { after: `오늘은 그이와 데이트야……
몇 번이나 데이트했는데도
늘 가슴이 두근거려<$0C>오늘은 어떤 １일이 될까……
아아…… 가슴이 두근거려 멈추질 않아!`, category: 'numeric_fidelity', reason: '원문에 명시된 전각 숫자 １을 하루로 치환하지 않고 보존했다.' }],
  [84, { after: `섬세한 메이드`, category: 'terminology', reason: '직업명 メイド를 프로젝트에서 사용하는 메이드 표기로 통일했다.' }],
  [104, { after: `……꼬맹이가 아니야. 라르크다`, category: 'meaning', reason: '坊や는 도련님이라는 신분 호칭이 아니라 어린 남자아이를 낮춰 부르는 말이므로 의미를 바로잡았다.' }],
  [105, { after: `친척 집에 놀러 가는 데도
외출 허가증이 필요하다니……
제정신이 아니야!<$0C>알스 황제는 우리가 처한
이 곤경을 알고 계신 걸까?
……대체 왜 이렇게 변한 거지`, category: 'meaning', reason: '窮状는 경제적 궁핍에 한정되지 않고 현재 처한 곤경을 뜻하므로 의미를 바로잡았다.' }],
  [120, { after: `욕설을 내뱉는 병사`, category: 'meaning', reason: '悪態をつく는 남을 험담한다기보다 불평과 욕설을 내뱉는다는 뜻이므로 인물 라벨을 교정했다.' }],
  [134, { after: `앞길도 멀 것 같아.
조심해, <$19>04`, category: 'natural_korean', reason: 'この先も長そうだ를 앞으로도 길겠네라는 번역투 대신 문맥에 맞는 자연스러운 표현으로 다듬었다.' }],
  [136, { after: `풀이 죽은 병사`, category: 'meaning', reason: '萎えている는 신체적으로 시들었다는 뜻이 아니라 기세가 꺾인 상태이므로 인물 라벨을 교정했다.' }],
  [154, { after: `자, 잠깐 놀라게 하지 마!
지금 바쁘단 말이야!`, category: 'meaning', reason: '脅かさないで는 이 문맥에서 협박하지 말라는 뜻이 아니라 갑자기 놀라게 하지 말라는 뜻이다.' }],
  [163, { after: `병사에게도 계절마다 옷을 바꾸는
관습이 필요하지 않아?<$0C>아무리 그래도 이 차림으로
이런 일을 하는 건 아니잖아.
언젠가 탈수 증상으로 쓰러질 거야`, category: 'meaning', reason: '兵隊를 군대라는 조직으로 옮긴 오류를 병사로 바로잡고 衣替え의 계절별 옷 갈아입기 의미를 살렸다.' }],
  [176, { after: `회의장에는 볼일 없어!
지하 형장으로 서두르자!`, category: 'meaning', reason: '議場는 의회라는 기관이 아니라 회의가 열리는 장소이므로 회의장으로 교정했다.' }],
  [180, { after: `『평화 회담』이 뭐야?`, category: 'terminology', reason: '어린아이의 발음 わへーかいだん이 가리키는 和平会談을 프로젝트 표기 평화 회담으로 통일했다.' }],
  [184, { after: `행상인/메이드/합창단 １　표시
합창단 ２/코더 상급-하급/의사　표시
비둘기/갈매기/고양이/개　표시
셉텐트리오 병사　표시
map_get 명령`, category: 'terminology', reason: '직업명 メイド를 같은 배치와 프로젝트의 메이드 표기로 통일했다.' }],
  [197, { after: `계속 대립하던
장사 경쟁자가 다른 도시로 옮겼는지
요즘 통 보이지 않아<$0C>……뭐지, 이 기분.
외로운 건 아니지만
조금 허전해`, category: 'meaning', reason: '商売敵를 거래 상대라는 뜻의 장사 상대로 옮긴 오류를 경쟁 관계가 드러나도록 바로잡았다.' }]
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
