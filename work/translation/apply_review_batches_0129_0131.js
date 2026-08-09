const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname);
const reviewer = '/root/translate_batch_0009';
const draftAuthor = '/root/translate_tail';

function replaceOnce(from, to) {
  return (text) => {
    if (!text.includes(from)) {
      throw new Error(`Expected text not found: ${JSON.stringify(from)}`);
    }
    return text.replace(from, to);
  };
}

function replaceEvery(from, to) {
  return (text) => {
    if (!text.includes(from)) {
      throw new Error(`Expected text not found: ${JSON.stringify(from)}`);
    }
    return text.replaceAll(from, to);
  };
}

function chain(...transforms) {
  return (text) => transforms.reduce((current, transform) => transform(current), text);
}

function fixed(after) {
  return () => after;
}

const edits = {
  '0129': [
    [7, replaceOnce('올키나', '오르키나'), 'proper_noun', '종교·지명 표기를 오르키나로 통일했다.'],
    [17, replaceOnce('마타타비 형제단', '마타타비 형제사'), 'proper_noun', '조직명 고정 표기를 적용했다.'],
    [30, replaceOnce('올키나', '오르키나'), 'proper_noun', '종교·지명 표기를 오르키나로 통일했다.'],
    [42, replaceOnce('이사 신께서', '이사신께서'), 'setting_terminology', '신명 고정 표기를 적용했다.'],
    [44, replaceOnce('볼일이 없다면\n돌아가 줄 뿐이야', '볼일이 없다면\n그냥 돌아가면 그만이야'), 'natural_korean', '일본어 직역투를 문맥에 맞는 자연스러운 한국어로 다듬었다.'],
    [50, replaceOnce('두 손이 있다면 모으십시오', '두 손이 있다면 모아 기도하십시오'), 'meaning_natural_korean', '합장하라는 원문의 종교적 행동 의미를 명확히 복원했다.'],
    [51, replaceOnce('랄, 랄, 랄', '란, 란, 란'), 'transliteration', '원문의 감탄성 음가 らん을 자연스럽게 옮겼다.'],
    [59, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [61, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [74, replaceOnce('이벤트 군 삭제', '이벤트군 삭제'), 'terminology', '디버그 용어의 합성어 표기를 통일했다.'],
    [76, replaceOnce('자랑스러워하는 남자', '우쭐해하는 남자'), 'meaning_natural_korean', '自慢げ의 태도를 자연스러운 인물 라벨로 옮겼다.'],
    [77, replaceOnce('올키나', '오르키나'), 'proper_noun', '종교·지명 표기를 오르키나로 통일했다.'],
    [79, replaceOnce('벌써 일주일이나', '벌써 １주일이나'), 'numeric_fidelity', '원문의 전각 숫자 １과 수치를 보존했다.'],
    [85, replaceOnce('알스 님을 한 번 더', '알스 님을 １번 더'), 'numeric_fidelity', '원문의 전각 숫자 １과 수치를 보존했다.'],
    [87, replaceOnce('대환영이지만', '대환영이야'), 'natural_korean', '종결이 어색하게 끊긴 문장을 자연스럽게 마무리했다.'],
    [95, replaceOnce('이벤트 군 삭제', '이벤트군 삭제'), 'terminology', '디버그 용어의 합성어 표기를 통일했다.'],
    [114, replaceOnce('동경하게 되네요', '동경하게 됩니다'), 'voice', '앞 문장과 존대 종결을 일관되게 맞췄다.'],
    [115, replaceOnce('가질 수 없는 모양이야', '들 수 없는 모양이야'), 'meaning', '아이템 소지 한도 문맥에 맞게 의미를 바로잡았다.'],
    [116, replaceOnce('무예 학당을', '무예관을'), 'terminology', '武芸塾의 시설명 표기를 무예관으로 통일했다.'],
    [119, chain(replaceOnce('디아만트 성', '디아만트성'), replaceOnce('만월의 숙소', '만월의 여관')), 'proper_noun', '장소명 고정 표기인 디아만트성과 만월의 여관을 적용했다.'],
    [122, replaceOnce('■■1번째 승리■■', '■■１번째 승리■■'), 'numeric_fidelity', '원문의 전각 숫자 １을 보존했다.'],
    [128, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [130, replaceOnce('출세로 가는 가장 빠른 길', '출세로 가는 １번 지름길'), 'numeric_fidelity', '원문의 전각 숫자 １과 최우선이라는 의미를 함께 보존했다.'],
    [131, replaceOnce('노스노와레 교회', '노스 노와레교회'), 'proper_noun', '종교 기관명 고정 표기를 적용했다.'],
    [137, replaceEvery('유인', '양동'), 'terminology', '운세 항목 陽動의 고정 번역인 양동을 적용했다.'],
    [145, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [147, replaceOnce('사흘도', '３일도'), 'numeric_fidelity', '원문의 전각 숫자 ３과 수치를 보존했다.'],
    [157, replaceOnce('이매지널 신', '이매지널신'), 'setting_terminology', '신명 고정 표기를 적용했다.'],
    [158, replaceOnce('올키나 교국', '오르키나 교국'), 'proper_noun', '국명 고정 표기를 적용했다.'],
    [159, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [166, replaceOnce('디아만트 성 D04로', '디아만트성 D04로'), 'proper_noun', '장소명 고정 표기를 적용했다.'],
    [168, replaceOnce('한 명씩', '１명씩'), 'numeric_fidelity', '원문의 전각 숫자 １과 수치를 보존했다.'],
    [170, replaceOnce('자랑스러운 물건들을', '자랑할 만한 물건들을'), 'natural_korean', '自慢の品々의 의미를 자연스러운 한국어로 다듬었다.'],
    [174, fixed('너무 우린 차를 두고〜\n오이겐 씨라 풉니다〜\n그 이유는〜<$0C>둘 다 떨떠름합니다'), 'meaning_wordplay', '수수께끼의 제시·풀이 구조와 떨떠름하다는 결론을 복원했다.'],
    [180, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [187, replaceOnce('라르크 브라이트 라군이라는 사람은\n형님 얘기인데', '라르크 브라이트 라군이란 사람이\n바로 형님인데'), 'meaning_natural_korean', '수배 인물과 형님이 동일인이라는 뜻을 자연스럽게 명확화했다.'],
    [191, replaceOnce('여자 친구 같은 사람이\n있으려나〜〜', '여자 친구라도\n있으려나〜〜'), 'natural_korean', '직역투를 대화체에 맞게 다듬었다.'],
  ],
  '0130': [
    [1, replaceOnce('이매지널 신 봉인', '이매지널신 봉인'), 'setting_terminology', '신명 고정 표기를 적용했다.'],
    [7, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [9, replaceOnce('……혼자 있게 해 줘', '……나 １명만 있게 해 줘'), 'numeric_fidelity', '원문의 전각 숫자 １과 혼자 있게 해 달라는 의미를 보존했다.'],
    [26, replaceOnce('천충탑 자이펠트', '천충탑 자이페르트'), 'proper_noun', '장소명 고정 표기를 적용했다.'],
    [50, replaceEvery('올키나', '오르키나'), 'proper_noun', '종교·지명 표기를 오르키나로 통일했다.'],
    [51, replaceOnce('변하지 않는 것은 없어요', '변하지 않는 것은 없습니다'), 'voice', '앞 문장과 존대 종결을 일관되게 맞췄다.'],
    [56, replaceOnce('이벤트 군 삭제', '이벤트군 삭제'), 'terminology', '디버그 용어의 합성어 표기를 통일했다.'],
    [60, replaceOnce('만월의 숙소·오두막', '만월의 여관·오두막'), 'proper_noun', '장소명 고정 표기를 적용했다.'],
    [73, replaceOnce('올키나교도가', '오르키나교도가'), 'proper_noun', '종교명 고정 표기를 적용했다.'],
    [75, replaceOnce('라군 상사님', '라르크 상사님'), 'proper_noun_rank', '원문의 인명 라르크와 계급 상사를 정확히 복원했다.'],
    [79, fixed('『붉은 달』의 신께서\n엄청 화나셨어<$0C>...'), 'voice_control_token', '神様의 높임과 원문의 제어 토큰 위치를 반영했다.'],
    [87, replaceOnce('이사 신께', '이사신께'), 'setting_terminology', '신명 고정 표기를 적용했다.'],
    [93, replaceOnce('배 한 척을', '배 １척을'), 'numeric_fidelity', '원문의 전각 숫자 １과 수치를 보존했다.'],
    [102, replaceOnce('계속 혼자……', '계속 １명뿐이야……'), 'numeric_fidelity_natural_korean', '원문의 전각 숫자 １을 보존하면서 독백을 자연스럽게 다듬었다.'],
    [105, replaceOnce('지금이 가장 행복하니까', '지금이 １번 행복하니까'), 'numeric_fidelity', '원문의 전각 숫자 １과 최상급 의미를 보존했다.'],
    [111, replaceOnce('하지만 나쁜 일은 아니야.', '하지만 나쁜 일은 아니다.'), 'voice', '독백의 문체와 종결을 일관되게 맞췄다.'],
    [118, fixed('오늘은 동경하던 선배와 데이트……<$0C>이렇게 기다리는 １분 １초가 행복해.\n벌써 １시간쯤 기다렸지만\n그것도 정말 행복해……'), 'numeric_fidelity_meaning', '원문의 １分１秒와 １時間 수치 및 기다리는 순간마다 행복하다는 뜻을 복원했다.'],
    [120, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [126, replaceOnce('한 명이라고 정해진 건 아니잖아', '１명이라고 정해진 건 아니잖아'), 'numeric_fidelity', '원문의 전각 숫자 １과 수치를 보존했다.'],
    [131, replaceOnce('곁에 붙어 있는 여자아이', '곁을 지키는 여자아이'), 'natural_korean', '인물 라벨을 자연스러운 한국어로 다듬었다.'],
    [139, replaceOnce('올키나교', '오르키나교'), 'proper_noun', '종교명 고정 표기를 적용했다.'],
    [149, replaceOnce('사죄의 말씀도 드릴 수 없습니다', '뭐라 사죄드려야 할지 모르겠습니다'), 'meaning_natural_korean', 'お詫びの言葉もございません의 사죄 관용 표현을 자연스럽게 옮겼다.'],
    [158, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [159, replaceOnce('불려 나온 지 한 시간이야', '불려 나온 지 １시간이야'), 'numeric_fidelity', '원문의 전각 숫자 １과 수치를 보존했다.'],
    [166, chain(replaceOnce('유인', '양동'), replaceOnce('그래도 하루는 끝나고', '그래도 １일은 끝나고')), 'terminology_numeric_fidelity', '陽動의 고정 번역과 원문의 전각 숫자 １을 적용했다.'],
    [167, replaceOnce('뭐, 꽤 괜찮은 선까지\n간 것 아니려나?', '뭐, 꽤 근접한 데까지\n간 것 아니려나?'), 'idiom_natural_korean', 'いい線行ってる의 관용 의미를 자연스럽게 옮겼다.'],
    [177, replaceOnce('올키나 교국', '오르키나 교국'), 'proper_noun', '국명 고정 표기를 적용했다.'],
    [192, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [196, replaceOnce('초승달의 숙소·오두막', '초승달 여관·오두막'), 'proper_noun', '장소명 고정 표기를 적용했다.'],
    [200, replaceOnce('올키나', '오르키나'), 'proper_noun', '종교·지명 표기를 오르키나로 통일했다.'],
  ],
  '0131': [
    [10, replaceOnce('마타타비 형제단', '마타타비 형제사'), 'proper_noun', '조직명 고정 표기를 적용했다.'],
    [30, replaceOnce('올키나교로', '오르키나교로'), 'proper_noun', '종교명 고정 표기를 적용했다.'],
    [34, chain(replaceEvery('올키나', '오르키나'), replaceOnce('아를 계약', '아를루 계약')), 'proper_noun', '메뉴 안의 지명과 인명 고정 표기를 적용했다.'],
    [70, replaceOnce('기도의 도시의 고양이', '기도 도시의 고양이'), 'natural_korean', '중복 조사를 제거해 인물 라벨을 자연스럽게 다듬었다.'],
    [73, replaceOnce('리피아 상태는 어때?', '리피아는 어때?'), 'natural_korean', '대화체에서 부자연스러운 명사 연결을 다듬었다.'],
    [85, replaceOnce('오늘도 술로 도망치자', '오늘도 술로 도피하자'), 'idiom', '酒に逃げる의 비유적 의미를 정확히 옮겼다.'],
    [88, replaceOnce('……영감답군', '……할아버지답군'), 'voice_meaning', '자무엘을 가리키는 가족 관계 호칭을 문맥에 맞게 복원했다.'],
    [98, fixed('술만이, 술만이\n나한테 다정하게 대해 줘'), 'meaning', '술만이 자신에게 다정하다는 원문의 주어 관계를 바로잡았다.'],
    [124, replaceOnce('밖에 있는 두 사람', '밖에 있는 ２명'), 'numeric_fidelity', '원문의 전각 숫자 ２와 수치를 보존했다.'],
    [136, replaceOnce('누군가 한 명을', '누군가 １명을'), 'numeric_fidelity', '원문의 전각 숫자 １과 수치를 보존했다.'],
    [140, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [147, replaceOnce('원로원이 노스노와레와', '원로원이 노스 노와레교와'), 'proper_noun', '종교 기관명 고정 표기를 적용했다.'],
    [148, replaceOnce('싫은 일이 있으면 술로 도망쳐.', '싫은 일이 있으면 술로 도피해.'), 'idiom', '酒に逃げる의 비유적 의미를 정확히 옮겼다.'],
    [153, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [158, fixed('아, 아무래도――\n이 정도로 큰 도시의 지도를\n만들려니 정말 고생스럽네……<$0C>조금쯤은\n쉬어도 되겠지……<$0C>――아, 거기 너.\n이 도시 지도의 사본을 줄 테니\n나 대신 검증해 주지 않을래?'), 'meaning_line_break', '누락된 머뭇거림을 복원하고 원문의 발화 흐름에 맞춰 줄바꿈을 다듬었다.'],
    [161, replaceOnce('카르분쿨루스', '카르분클루스'), 'proper_noun', '고유명사 고정 표기를 적용했다.'],
    [168, replaceOnce('마타타비 형제단', '마타타비 형제사'), 'proper_noun', '조직명 고정 표기를 적용했다.'],
    [192, fixed('여기는 오팔루스 사관학교다.\n――당신은 입학 희망자야?\n……그러기엔 꽤 나이가 많군'), 'natural_korean', '오탈자를 바로잡고 상대의 나이를 지적하는 문장을 자연스럽게 다듬었다.'],
    [199, replaceOnce('올키나교', '오르키나교'), 'proper_noun', '종교명 고정 표기를 적용했다.'],
  ],
};

function readJsonl(file) {
  return fs.readFileSync(file, 'utf8').trimEnd().split(/\r?\n/).map((line) => JSON.parse(line));
}

for (const [batchNo, batchEdits] of Object.entries(edits)) {
  const batchId = `batch_${batchNo}`;
  const sourceRel = `work/translation/tm_v2/batches/source/${batchId}.jsonl`;
  const draftRel = `work/translation/drafts/${batchId}.jsonl`;
  const reviewedRel = `work/translation/reviewed/${batchId}.jsonl`;
  const draftPath = path.join(root, 'drafts', `${batchId}.jsonl`);
  const reviewedPath = path.join(root, 'reviewed', `${batchId}.jsonl`);
  const reportPath = path.join(root, 'reviews', `${batchId}_review.json`);
  const rows = readJsonl(draftPath);
  const modifications = [];

  for (const [index, transform, category, reason] of batchEdits) {
    const row = rows[index - 1];
    const before = row.translation_ko;
    const after = transform(before);
    if (after === before) {
      throw new Error(`${batchId} row ${index}: review edit made no change`);
    }
    rows[index - 1] = { ...row, translation_ko: after };
    modifications.push({
      tm_id: row.tm_id,
      source_text: row.source_text,
      before,
      after,
      category,
      reason,
    });
  }

  fs.mkdirSync(path.dirname(reviewedPath), { recursive: true });
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });
  fs.writeFileSync(reviewedPath, `${rows.map((row) => JSON.stringify(row)).join('\n')}\n`, 'utf8');

  const report = {
    schema: 'arf-translation-independent-review-v1',
    batch_id: batchId,
    reviewer,
    draft_translator: draftAuthor,
    draft_author: draftAuthor,
    independent_review: true,
    translation_engine_policy: 'Codex internal models only',
    external_translation_services_used: [],
    external_translation_models_or_apis_used: [],
    source: sourceRel,
    draft: draftRel,
    reviewed_output: reviewedRel,
    reviewed_units: rows.length,
    modified_units: modifications.length,
    unchanged_units: rows.length - modifications.length,
    review_dimensions: [
      'meaning',
      'function',
      'numeric fidelity',
      'proper nouns',
      'natural Korean',
      'particles',
      'control tokens',
      'line breaks',
    ],
    modifications,
    verification_execution: {
      status: 'deferred_by_user_instruction',
      executed_tools: [],
      not_executed: ['validator', 'fit', 'encoding', 'boundary_audit'],
      note: '사용자 지시에 따라 별도 validator, fit, encoding, boundary audit를 실행하지 않았다.',
    },
  };
  fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  console.log(`${batchId}: ${rows.length} reviewed, ${modifications.length} modified`);
}
