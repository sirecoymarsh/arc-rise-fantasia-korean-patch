const fs = require('fs');
const path = require('path');

const ROOT = path.join('work', 'translation');
const REVIEWER = '/root/translate_batch_0009';

const batches = {
  batch_0141: {
    draftAuthor: '/root/translate_tail',
    edits: [
      [20, 'natural_korean', '거친 남성 화자의 말투와 소지 한도 의미가 자연스럽게 드러나도록 다듬었다.', `괜찮겠어? 미안하군.\n고맙다, 받아 둘게<$0C>……아니, 안 되겠네.\n설마 했지만 틀림없어.\n다 들 수 없는 모양이야……`],
      [38, 'terminology', '프로젝트의 반복 디버그 명칭인 ロケ鯛君을 기존 표기인 로케타이 군으로 통일했다.', `로케타이 군`],
      [40, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 1-2\n`],
      [41, 'debug_format', '영문 식별자와 한국어 기능명 사이를 띄어 썼다.', `PLACE24 처리\n`],
      [42, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 1-4\n`],
      [43, 'terminology', '반복 디버그 명칭 ロケ鯛를 기존 표기인 로케타이로 통일했다.', `로케타이를 재생할까?`],
      [44, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 4-5\n`],
      [48, 'natural_korean', '마지막 판단문이 자연스러운 한국어가 되도록 부사를 보완했다.', `그렇기에 알스 님께서\n상처받으시는 게 아닐까\n나는 그렇게 생각한다`],
      [59, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 1-3\n`],
      [62, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 18-19\n`],
      [64, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 12-13\n`],
      [65, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 16-18\n`],
      [69, 'natural_korean', 'よしみ를 직역한 어색한 연결을 자연스러운 관계 표현으로 고쳤다.', `얼마 전까지 함께 여행한\n정을 생각해서 여기서는\n물러나 주지 않을래?`],
      [72, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 10-12\n`],
      [73, 'natural_korean', '마지막 명사구가 앞 문장에 자연스럽게 이어지도록 조사와 종결을 보완했다.', `소용없어. 라르크는 리피아에게\n속고 있잖아.\n이매지널의 충실한 인형에게 말이야`],
      [74, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 13-15\n`],
      [80, 'voice', '격식 있는 군인 화자의 부탁이 가벼운 구어체로 흐르지 않도록 조정했다.', `너는 알스 님의 신하이자\n친구일 테지. 그렇다면 그분을\n도와다오. 부탁한다`],
      [81, 'terminology', '曹長의 고정 계급 표기인 상사를 적용했다.', `……라군 상사`],
      [82, 'terminology', '디버그 객체명 ロケタイ君을 로케타이 군으로 통일했다.', `로케타이 군에게 불린 듯하니 페이드 인합니다.\n`],
      [85, 'terminology', 'イベント君의 고정 디버그 표기인 이벤트군을 적용했다.', `이벤트군`],
      [91, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 3-4\n`],
      [92, 'debug_format', '영문 식별자와 한국어 기능명 사이를 띄어 썼다.', `PLACE16 처리\n`],
      [93, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 24-26\n`],
      [94, 'debug_format', '영문 식별자와 한국어 기능명 사이를 띄어 썼다.', `START_05 도착\n`],
      [95, 'debug_format', '영문 식별자와 한국어 기능명 사이를 띄어 썼다.', `PLACE00 처리\n`],
      [98, 'voice', '주저하는 대답의 더듬는 느낌이 자연스럽게 들리도록 다듬었다.', `네, 네에……`],
      [99, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 7\n`],
      [105, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 10-11\n`],
      [106, 'debug_format', '복합 디버그 기능명 내부의 누락된 공백을 복원했다.', `더미・오브젝트 배치 초기화\n`],
      [108, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 10\n`],
      [109, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 6-9\n`],
      [112, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 16-19\n`],
      [117, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 16-17\n`],
      [118, 'grammar', '定理와 契約을 병렬로 나열하는 문맥에 맞게 조사를 고쳤다.', `섭리와 계약……인가`],
      [119, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 20-23\n`],
      [120, 'debug_format', '컷 번호 앞의 구분 공백을 복원하되 선행 0을 유지했다.', `컷 03\n`],
      [122, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 27-30\n`],
      [125, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 15-17\n`],
      [127, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 5-6\n`],
      [128, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 22-24\n`],
      [135, 'debug_format', '영문 식별자와 한국어 기능명 사이를 띄어 썼다.', `PLACE27 처리\n`],
      [137, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 14\n`],
      [138, 'natural_korean', '자책의 의미가 분명하고 자연스럽게 들리도록 고쳤다.', `……역시 내가 문제인 거야`],
      [139, 'japanese_residue', '번역문에 남은 일본어 디버그 용어를 한국어로 옮기고 영문 플래그는 유지했다.', `카메라 오프셋 OFF(초깃값)\n`],
      [143, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 31-33\n`],
      [146, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 34-35\n`],
      [147, 'debug_format', '컷 번호 앞의 구분 공백을 복원하되 원문의 선행 0을 유지했다.', `컷 04-6\n`],
      [148, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 9b\n`],
      [150, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 36-38\n`],
      [151, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 7-8\n`],
      [158, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 26.5\n`],
      [159, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 5-9\n`],
      [161, 'japanese_residue', '번역문에 남은 일본어 디버그 용어를 한국어로 옮기고 수치와 영문 플래그를 유지했다.', `카메라 오프셋 ON(+150)\n`],
      [162, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 39\n`],
      [163, 'voice', '니콜의 반복 말투에 맞게 マジ를 진짜로 통일했다.', `진짜임까!?`],
      [165, 'meaning', '인물명 グラ를 일반 명사 그래픽으로 오역한 부분을 바로잡았다.', `그라와 같아?`],
      [166, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 6-8\n`],
      [180, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 9-11\n`],
      [181, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 14-15\n`],
      [182, 'voice', '주저하면서도 힘차게 답하는 말투가 자연스럽게 들리도록 다듬었다.', `……네, 넵!`],
      [183, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 9\n`],
      [185, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 1\n`],
      [189, 'debug_format', '복합 디버그 기능명 내부의 누락된 공백을 복원했다.', `더미・NPC 배치 초기화\n`],
      [190, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 15\n`],
      [192, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 3-6\n`],
      [193, 'natural_korean', '부자연스러운 이중 부정을 자연스러운 추측 표현으로 고쳤다.', `아닌 것 같은데?\n밖에서 봤을 때는\n더 높았을 텐데`],
      [196, 'debug_format', '컷 번호 앞의 구분 공백을 복원하되 선행 0을 유지했다.', `컷 08-10\n`],
      [199, 'debug_format', '컷 번호 앞의 구분 공백을 복원했다.', `컷 19-21\n`],
      [200, 'debug_format', '컷 번호 앞의 구분 공백을 복원하되 선행 0을 유지했다.', `컷 01-04\n`],
    ],
  },
  batch_0142: {
    draftAuthor: '/root/translate_final',
    edits: [
      [11, 'terminology', 'ロゴス를 로그레스로 오역한 부분을 고정 용어 로고스로 바로잡았다.', `어쩔 수 없군.\n나의 『천위』 로고스를 주마`],
      [27, 'terminology', 'イベント君의 고정 디버그 표기인 이벤트군을 적용했다.', `■■이벤트군 삭제■■\n`],
      [49, 'terminology_numeric_fidelity', '競合을 경합으로 통일하고 원문의 전각 숫자 ２를 복원했다.', `경합 ２회차\n`],
      [54, 'terminology', 'オブジェ君의 디버그 객체명을 오브젝트군으로 통일했다.', `오브젝트군`],
      [57, 'meaning', '理想像가 이상형이 아니라 상상해 온 이상적인 모습이라는 뜻이 되도록 고쳤다.', `레온의 이상상이……`],
      [58, 'meaning', '仲間를 단순한 사람들로 옮긴 부분을 동료 관계가 드러나도록 바로잡았다.', `어릴 적부터\n우리 그라 자혜교회 동료들은\n그라와 친하게 지냈다`],
      [60, 'meaning', '서명할 물건을 가리키는 コレ를 사람을 가리키는 이쪽으로 오해하지 않도록 고쳤다.', `이걸로 부탁할게`],
      [71, 'terminology_numeric_fidelity', '競合을 경합으로 통일하고 원문의 전각 숫자 ３을 복원했다.', `경합 ３회차\n`],
      [79, 'terminology', 'イベント君의 고정 디버그 표기인 이벤트군을 적용했다.', `이벤트군 G`],
      [81, 'terminology_numeric_fidelity', '競合을 경합으로 통일하고 원문의 전각 숫자 １을 복원했다.', `경합 １회차\n`],
      [88, 'terminology', '측정 결과를 말하는 디버그 문맥에 맞게 タイム를 타임으로 유지했다.', `타임은……`],
      [103, 'terminology', '競合君을 일반 캐릭터가 아닌 경합 디버그 객체명으로 옮겼다.', `경합군`],
      [108, 'natural_korean', '격식 있는 짧은 동의문을 자연스럽게 다듬었다.', `나는 이의 없다`],
      [116, 'voice', '俺さま의 과장된 자칭이 드러나도록 화자 어조를 복원했다.', `이 몸도 찬성.\n요즘 허리랑 다리가 쑤시거든`],
      [124, 'voice', '딸이 아버지를 부르는 말로 부자연스러운 아버님을 아버지로 고쳤다.', `아버지……`],
      [141, 'punctuation', '원문의 장음 물결표를 동일한 문자로 복원했다.', `언제든 들러 주세요〜`],
      [159, 'natural_korean', '소유 관계가 빠진 명사구를 자연스럽게 보완했다.', `도구점 주인의 딸`],
      [170, 'meaning', '조건문이 아니라 자신의 상태를 말하는 문장으로 바로잡았다.', `나는 괜찮아`],
      [177, 'terminology', '디버그 명칭의 君을 프로젝트 표기인 군으로 옮겼다.', `어느 오두막에서 왔는지 답하는 군`],
      [195, 'meaning', '白々しい의 능청스럽게 모르는 체한다는 의미를 살렸다.', `시치미 떼기는……`],
    ],
  },
  batch_0143: {
    draftAuthor: '/root/translate_final',
    edits: [
      [3, 'natural_korean', '구어체 어순이 자연스럽도록 다듬었다.', `이제 벽은 없어\n`],
      [4, 'title', '황자라는 직함 뒤에 불필요하게 붙은 존칭을 덜어 기존 직함 표기에 맞췄다.', `역시 황자 일행도\n로그레스와 계약하러 온 걸까요?`],
      [36, 'terminology', '競合의 고정 표기인 경합을 적용했다.', `■■경합으로■■\n`],
      [76, 'title', '고정 군 직함 표기에 맞춰 장군 뒤의 중복 존칭을 덜었다.', `프레이아 장군!`],
      [81, 'meaning', '관용적인 비유가 마계의 신이라는 정의문으로 오해되지 않도록 의미를 복원했다.', `형님! 마계에서 이사신을 만난 격이\n바로 이런 거예요.\n빨리 도망쳐요!`],
      [89, 'natural_korean', '문장이 미완성된 듯 끝나는 표현을 자연스러운 핀잔으로 완결했다.', `……정말, 무모한 짓이나 하고`],
      [97, 'natural_korean', '명령문이 자연스럽게 들리도록 관용적인 표현으로 고쳤다.', `넌 입 다물고 있어`],
      [101, 'meaning', '장비를 되찾아 준 상황의 助かる를 감사가 아니라 안도 표현으로 옮겼다.', `살았군`],
      [110, 'grammar', '우리나라의 띄어쓰기를 바로잡고 문장 호응을 다듬었다.', `그런 미래를 인간에게 강요하는\n신과 신도들에게, 어째서 우리나라가\n따라야 한단 말이냐`],
      [114, 'natural_korean', '자신이 악역에 가까운 처지라는 구어체 의미가 자연스럽게 드러나도록 다듬었다.', `굳이 말하자면\n지금은 선전포고 문서를 가져온\n내가 나쁜 놈이지만……`],
      [129, 'natural_korean', '호격 명사구가 어색하게 끊기지 않도록 복수형을 보완했다.', `바보냐, 너희들`],
      [130, 'meaning', '敵を飼う의 비유를 적을 곁에 두지 않는다는 의미로 자연스럽게 옮겼다.', `섭리를 택하는 자는 내 적이다.\n난 적을 곁에 두는 취미는 없으니까`],
      [137, 'meaning_voice', 'きめぇ의 강한 혐오감을 살리면서 더듬는 말투를 유지했다.', `여…… 역겨워……`],
      [144, 'natural_korean', 'おっと의 제지 뉘앙스가 자연스럽게 들리도록 고쳤다.', `이런, 움직이지 마`],
      [162, 'natural_korean', '방향을 가리키는 짧은 외침이 자연스럽도록 보완했다.', `위쪽이다!`],
      [163, 'natural_korean', '출신지를 나타내는 인물 라벨을 자연스러운 한국어 명사로 고쳤다.', `오리엔스인`],
      [169, 'terminology', 'イベント君의 고정 디버그 표기인 이벤트군을 적용했다.', `B 이벤트군 G`],
      [170, 'voice', '공식 석상에서 화내는 화자의 격식 있는 종결을 살렸다.', `무슨 뜻이냐!`],
      [183, 'terminology', '작중 시스템 용어 コア를 기존 표기인 코어로 통일했다.', `네.\n당신이 코어가 되어, 전 세계의\n호존을 무효화하는 겁니다`],
      [200, 'spacing', '복합 명사의 띄어쓰기를 바로잡았다.', `젠장! 지하 시설을 봉쇄해라!`],
    ],
  },
};

const readJsonl = (file) => fs.readFileSync(file, 'utf8')
  .split(/\r?\n/).filter(Boolean).map(JSON.parse);

for (const [batchId, config] of Object.entries(batches)) {
  const sourcePath = `${ROOT}/tm_v2/batches/source/${batchId}.jsonl`;
  const draftPath = `${ROOT}/drafts/${batchId}.jsonl`;
  const reviewedPath = `${ROOT}/reviewed/${batchId}.jsonl`;
  const reportPath = `${ROOT}/reviews/${batchId}_review.json`;
  const sourceRows = readJsonl(sourcePath);
  const reviewedRows = readJsonl(draftPath).map((row) => ({ ...row }));
  const modifications = [];

  for (const [index, category, reason, after] of config.edits) {
    const sourceRow = sourceRows[index - 1];
    const reviewedRow = reviewedRows[index - 1];
    const before = reviewedRow.translation_ko;
    reviewedRow.translation_ko = after;
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
  fs.writeFileSync(reviewedPath, `${reviewedRows.map((row) => JSON.stringify(row)).join('\n')}\n`, 'utf8');

  const report = {
    schema: 'arf-translation-independent-review-v1',
    batch_id: batchId,
    reviewer: REVIEWER,
    draft_translator: config.draftAuthor,
    draft_author: config.draftAuthor,
    independent_review: true,
    translation_engine_policy: 'Codex internal models only',
    external_translation_services_used: [],
    external_translation_models_or_apis_used: [],
    source: sourcePath,
    draft: draftPath,
    reviewed_output: reviewedPath,
    reviewed_units: reviewedRows.length,
    modified_units: modifications.length,
    unchanged_units: reviewedRows.length - modifications.length,
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
  process.stdout.write(`${batchId}: ${modifications.length} modified, ${reviewedRows.length} reviewed\n`);
}
