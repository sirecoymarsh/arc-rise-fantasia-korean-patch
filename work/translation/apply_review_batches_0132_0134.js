const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname);
const reviewer = '/root/translate_batch_0009';
const draftAuthor = '/root/audit_boundary_integration';

function replaceOnce(from, to) {
  return (text) => {
    if (!text.includes(from)) {
      throw new Error(`Expected text not found: ${JSON.stringify(from)}`);
    }
    return text.replace(from, to);
  };
}

function chain(...transforms) {
  return (text) => transforms.reduce((current, transform) => transform(current), text);
}

function fixed(after) {
  return () => after;
}

const edits = {
  '0132': [
    [3, fixed('우리 제국 병사들이\n너희의 나약해빠진 근성을\n다시 다잡아 주마'), 'meaning_natural_korean', '腑抜けた根性의 나약하고 해이한 상태를 자연스럽게 옮겼다.'],
    [4, fixed('저항군에 들어가게 해 주세요'), 'meaning_natural_korean', '조직에 가입시켜 달라는 의미를 자연스럽게 복원했다.'],
    [8, fixed('이렇게 비일상을 즐길 수 있는 건\n병사들이 적을 몰아내 준 덕분이야.\n정말 고개가 절로 숙여져……'), 'idiom_natural_korean', '非日常をはしゃげる와 頭が下がる의 의미를 자연스럽게 옮겼다.'],
    [13, replaceOnce('어쩌면 좋죠……', '이럴 수가……'), 'meaning', 'なんということでしょう의 놀라움과 탄식을 정확히 반영했다.'],
    [18, replaceOnce('이벤트 군 삭제', '이벤트군 삭제'), 'terminology', '디버그 용어의 합성어 표기를 통일했다.'],
    [19, fixed('난 처음이 아니야.\n내 동료는 처음이지――모든 게'), 'meaning_natural_korean', '처음인 주체가 동행인임을 명확히 하고 문장을 자연스럽게 다듬었다.'],
    [26, fixed('어머? 내가 성가시다고 하면\n데려가 줄 거야?\n――그렇다면 생각해 볼게'), 'meaning_natural_korean', '迷惑してる의 화자 관점과 인수해 간다는 의미를 바로잡았다.'],
    [33, fixed('일단 용박탑에도\n문화적 가치는 있습니다.\n아무도 눈치채지 못하지만……'), 'meaning_natural_korean', '気づいてない를 알아주지 않는다는 뜻이 아닌 인지하지 못한다는 뜻으로 바로잡았다.'],
    [44, fixed('설명하기를 좋아하는 청년'), 'natural_korean', '인물 라벨의 조사를 자연스럽게 보완했다.'],
    [45, fixed('퇴물더러 퇴물이라니……'), 'natural_korean', '호칭을 되받는 문장의 조사와 어감을 자연스럽게 다듬었다.'],
    [52, fixed('우리 집 메이드에게\n정말 폐를 끼치고 있어……\n참 한심한 당주지'), 'meaning_terminology', '当主를 가장이 아닌 집안의 주인인 당주로 정확히 옮겼다.'],
    [53, fixed('이 세상에는\n모든 이해를 초월한\n미지의 공간이 있다고 합니다<$0C>그것은 신의 변덕인가\n아니면 새로운 정리인가――'), 'meaning_setting_terminology', 'あらゆる理解와 定理를 각각 자연스럽고 설정에 맞게 복원했다.'],
    [66, fixed('새 출발을 하는 소녀'), 'meaning_natural_korean', '新たに踏みだす의 새롭게 나아가는 의미를 인물 라벨로 자연스럽게 옮겼다.'],
    [85, fixed('별로 가는 배? 그게 뭐야?'), 'meaning', '星へ行く船의 목적지를 정확히 옮겼다.'],
    [91, replaceOnce('기억에도 없는 죄로', '저지른 적도 없는 죄로'), 'meaning_natural_korean', '身に覚えの無い罪의 억울한 누명 의미를 자연스럽게 복원했다.'],
    [106, replaceOnce('그야말로 상승불패――', '그야말로 백전불패――'), 'idiom_natural_korean', '常勝無敗를 자연스러운 한국어 관용 표현으로 바로잡았다.'],
    [121, replaceOnce('헛소리하면 날려 버린다!', '헛소리하면 날려 버릴 거다!'), 'voice_natural_korean', '위협하는 미래 의도를 자연스러운 종결로 다듬었다.'],
    [148, replaceOnce('위기에 노출됨으로써\n생명은 자신의 존재라는 윤곽을\n모호하게 만들지 않게 되지', '위기에 노출됨으로써\n생명은 자신의 존재라는 윤곽을\n더는 흐리지 않게 돼'), 'meaning_natural_korean', '이중 부정의 직역투를 제거하면서 존재의 윤곽이 선명해진다는 의미를 보존했다.'],
    [191, fixed('다들 눈치채지 못하고 있지만\n전쟁의 발소리는 차츰\n다가오고 있는 것 아닐까?'), 'meaning_natural_korean', '着々との 진행 의미와 문장 주어를 자연스럽게 다듬었다.'],
  ],
  '0133': [
    [14, fixed('셰리 녀석이 틀림없이\n즐기는 순위 １등일걸'), 'numeric_fidelity_natural_korean', '원문의 전각 숫자 １을 보존하면서 가장 즐기고 있다는 뜻을 자연스럽게 다듬었다.'],
    [39, fixed('인류는 옷깃을 여미고 몸가짐을 바로잡아야 합니다.\n황제는 분별 있는 인간을 좋아합니다'), 'idiom_natural_korean', '襟を正す의 관용 의미를 자연스럽게 옮겼다.'],
    [49, fixed('내일 다시 오라―― 이건가.\n여기 있어 봤자 소용없어.\n무예관으로 돌아가자'), 'natural_korean', '명령을 되새기는 문장을 자연스러운 대화체로 다듬었다.'],
    [55, fixed('제국은 안트락스만으로는\n굶주림을 달래지 못했는지\n이젠 공화국과 전쟁 중이라더군……<$0C>더없이 탐욕스러워'), 'meaning_natural_korean', '굶주림을 채운다는 직역투와 전쟁 시제를 자연스럽게 바로잡았다.'],
    [58, fixed('……바이스 황태자는……\n……눈빛이 너무 차가워……<$0C>……난 그 사람이 어려워……'), 'meaning_natural_korean', '苦手의 상대가 부담스럽고 어렵다는 의미를 명확히 했다.'],
    [73, replaceOnce('인생은 １번뿐이라고?', '인생은 １번뿐이잖아?'), 'numeric_fidelity_voice', '전각 숫자 １을 보존하고 반문 어조를 바로잡았다.'],
    [82, replaceOnce('제국이 조용해져서 만만세!', '제국이 얌전해져서 만세지!'), 'meaning_natural_korean', '大人しくなって万々歳의 의미와 자연스러운 감탄을 복원했다.'],
    [84, fixed('저는 대성당의 안내인입니다.\n그 이상도\n그 이하도 아닙니다'), 'voice_natural_korean', '누락된 서술어를 보완하고 존대 문체를 일관되게 맞췄다.'],
    [86, replaceOnce('요즘 처음 목적을', '요즘 본래 목적을'), 'natural_korean', '当初の目的을 자연스러운 한국어로 다듬었다.'],
    [90, fixed('설명하기를 좋아하는 소녀'), 'natural_korean', '인물 라벨의 조사를 자연스럽게 보완했다.'],
    [91, replaceOnce('앞으로 단골이 될까', '앞으로 자주 와야겠어'), 'meaning_natural_korean', 'ひいきにしよう의 계속 이용하겠다는 의도를 자연스럽게 옮겼다.'],
    [103, fixed('알스 도련님이 당신을\n수배자로 삼았다던데……<$0C>알스가 아무 미련도 없는 사람을\n수배자로 삼지는 않아.\n그러니 희망을 가져도 돼'), 'meaning_natural_korean', '執着의 주체가 알스임을 명확히 해 관계 의미를 복원했다.'],
    [122, fixed('우리 주인님은\n뭘 드시고 싶은지 물어도\n항상 『아무거나』라고 하셔<$0C>요리하는 입장에서는\n『아무거나』란 대답이\n곤란함으로는 １등이야……'), 'numeric_fidelity_natural_korean', '원문의 전각 숫자 １을 보존하면서 요리하는 입장의 불만을 자연스럽게 다듬었다.'],
    [160, chain(replaceOnce('리얼 신은', '리얼신은'), replaceOnce('이사 신께', '이사신께')), 'setting_terminology', '신명 고정 표기인 리얼신과 이사신을 적용했다.'],
    [181, replaceOnce('제가 그 아이를 부르지만 않았다면', '제가 그 아이를 부르지 않았더라면'), 'grammar_natural_korean', '과거 반사실 조건문의 활용을 바로잡았다.'],
    [185, fixed('아아, 싫다 싫어.\n오른쪽을 보면 푸념.\n왼쪽을 보면 신에게 매달리기――<$0C>안트락스는 언제부터\n이렇게 나약한 자들의 도시가 됐어?'), 'parallelism_natural_korean', '좌우를 열거하는 문장의 병렬 구조를 자연스럽게 맞췄다.'],
    [189, fixed('아마 같은 소녀'), 'meaning', '亜麻를 아마포가 아닌 식물 섬유인 아마로 정확히 옮겼다.'],
    [192, replaceOnce('리얼 신이', '리얼신이'), 'setting_terminology', '신명 고정 표기인 리얼신을 적용했다.'],
    [194, fixed('기가 약한 병사'), 'natural_korean', '弱気의 인물 성향을 간결하고 자연스럽게 옮겼다.'],
  ],
  '0134': [
    [1, fixed('하지만――나는 언제나\n너를 지키는 게 기쁨이었어.\n그건 지금도 변하지 않았어'), 'voice_natural_korean', '회상 문장의 종결과 지킨다는 행위가 기쁨이었다는 의미를 자연스럽게 다듬었다.'],
    [11, replaceOnce('이제 이 무예관도\n큰 인기 틀림없어!', '이제 이 무예관도\n큰 인기를 끌 게 틀림없어!'), 'grammar_natural_korean', '누락된 서술 관계를 보완해 문장을 자연스럽게 완성했다.'],
    [12, replaceOnce('쥐는 감촉이 좋다는 거 알아?', '손에 쥐는 느낌이 좋다는 거 알아?'), 'natural_korean', '握り心地를 자연스러운 한국어 표현으로 다듬었다.'],
    [14, fixed('결국 아무리\n혹독한 환경이라도 인간은\n살아갈 수 있어요……<$0C>저는 답답한 생활에\n완전히 익숙해져 버렸습니다<$0C>인간의 뛰어난 적응력은\n어떤 의미에서는 무섭네요……'), 'voice_natural_korean', '화자의 존대 문체와 인칭을 일관되게 맞추고 표현을 자연스럽게 다듬었다.'],
    [20, fixed('둘째 딸과 셋째 딸을 찾음\n'), 'meaning', '次女와 三女가 딸을 가리킨다는 정보를 복원했다.'],
    [22, replaceOnce('사라진 가족의 몫까지', '잃은 가족의 몫까지'), 'meaning_natural_korean', '습격으로 잃은 가족이라는 문맥을 자연스럽게 반영했다.'],
    [35, fixed('솔직히 지금 상태에서 국민들이\n알스 폐하에 대한 불만을 늘어놓아도\n그걸 반박할 자신도 기개도 없어……'), 'meaning_natural_korean', '국민에게서 불만을 듣는 피동 관계를 자연스럽게 복원했다.'],
    [42, fixed('저는 몸이 약해서\n주인님께\n늘 꾸중만 들어요<$0C>――하지만, 하지만요\n꾸중을 듣는 건\n기대한다는 뜻이라고 생각해요'), 'voice_natural_korean', '화자의 존대 문체와 메이드가 주인을 부르는 표현을 자연스럽게 맞췄다.'],
    [47, replaceOnce('난 꼭\n거짓말은 아니라고 생각해.', '난 그게 꼭\n거짓말만은 아니라고 생각해.'), 'meaning_natural_korean', 'あながち嘘じゃない의 반드시 거짓만은 아니라는 의미를 자연스럽게 옮겼다.'],
    [53, fixed('오르키나의 가르침이\n파멸적이라고 보는 이들도 있습니다……<$0C>하지만 우리는 하늘의 물을 두고\n이기적으로 굴기를 그만두었을――\n뿐입니다'), 'grammar_meaning', '문법이 끊긴 직역을 바로잡고 이기적인 태도를 버렸다는 의미를 복원했다.'],
    [54, replaceOnce('나는 생각하게 되더라……', '나는 생각하게 되네……'), 'tense_voice', '현재의 사색을 나타내는 원문 시제와 말투를 맞췄다.'],
    [56, replaceOnce('이사 신과의', '이사신과의'), 'setting_terminology', '신명 고정 표기인 이사신을 적용했다.'],
    [66, replaceOnce('수도 방위를 위한 비장의 수인 건 변함없다.', '수도 방위를 위한 비장의 카드인 건 변함없다.'), 'idiom_natural_korean', '切り札를 자연스러운 한국어 관용 표현으로 옮겼다.'],
    [72, replaceOnce('이벤트 군 삭제', '이벤트군 삭제'), 'terminology', '디버그 용어의 합성어 표기를 통일했다.'],
    [77, fixed('벌써 찾은 거예요?\n오빠, 너무 빠른 거예요!<$0C>마지못해 아까 있던 곳으로 돌아가는 거예요'), 'voice', '캐릭터의 ですのよ 말버릇이 유지되도록 종결을 통일했다.'],
    [83, replaceOnce('――여긴 제도라고?', '――여긴 제도잖아?'), 'meaning_voice', '帝都임을 강조하는 반문 어조를 자연스럽게 복원했다.'],
    [84, replaceOnce('지금까지 고생은 대체……', '지금까지의 고생은 대체……'), 'grammar', '관형격 조사를 보완했다.'],
    [95, fixed('이 층은 위에서 １번째――\n높은 벽이 없어서\n햇빛이 밝아요<$0C>바람이 기분 좋지만\n조금 너무 강해서……\n모자가 날아가 버려요'), 'numeric_fidelity_natural_korean', '원문의 전각 숫자 １을 보존하면서 가장 위층이라는 의미를 자연스럽게 옮겼다.'],
    [99, replaceOnce('우리는 제국을 위한 말', '우리는 제국의 장기말'), 'meaning', '駒가 제국이 움직이는 장기말이라는 비유임을 명확히 했다.'],
    [117, fixed('에블로 가는 길에\n여기를 이용하고 있어.\n노숙할 필요가 없어져서 다행이야'), 'meaning_natural_korean', '使わせてもらってる를 사용 허락을 받아 이용 중이라는 뜻으로 바로잡았다.'],
    [121, replaceOnce('리더가 공화국\n원로원 의장이었다니 놀라워', '리더가 공화국의\n원로원 의장이었다니 놀라워'), 'grammar', '소속을 나타내는 관형격 조사를 보완했다.'],
    [126, fixed('첫째 딸과 둘째 딸을 찾음\n'), 'meaning', '長女와 次女가 딸을 가리킨다는 정보를 복원했다.'],
    [149, replaceOnce('페리스 마을보다도', '펠리스 마을보다도'), 'proper_noun', '지명 고정 표기인 펠리스를 적용했다.'],
    [151, fixed('일이 뜻대로 풀리지 않을 때\n자주 이곳을 찾습니다'), 'idiom_meaning', 'つまずいた를 물리적으로 넘어진다는 뜻이 아닌 난관에 부딪힌다는 비유로 옮겼다.'],
    [172, fixed('그렇다고 해맑게\n놀리지는 말라고'), 'meaning_natural_korean', '明るく馬鹿にする의 해맑게 놀리는 어감을 자연스럽게 옮겼다.'],
    [180, replaceOnce('우리의 신앙은 죄가 깊은 걸까?', '우리의 신앙은 그토록 죄 많은 걸까?'), 'natural_korean', '罪深い를 자연스러운 한국어 서술로 다듬었다.'],
    [196, fixed('이런 곳에 손님이라니\n그야말로 마계에 리얼신!\n……자랑할 만한 도구를 보세요!'), 'setting_terminology_natural_korean', '리얼신 고정 표기를 적용하고 自慢の道具를 자연스럽게 옮겼다.'],
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
