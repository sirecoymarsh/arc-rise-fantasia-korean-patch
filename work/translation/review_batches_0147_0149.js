const fs = require('fs');
const path = require('path');

const ROOT = 'work/translation';
const REVIEWER = '/root/audit_boundary_integration';
const DRAFT_AUTHOR = '/root/translate_final';

const expectedCounts = {
  batch_0147: 200,
  batch_0148: 200,
  batch_0149: 177,
};

const corrections = {
  batch_0147: [
    {
      index: 15,
      category: 'typo_voice',
      reason: 'あ의 머뭇거림이 「혀」로 잘못 옮겨진 오타를 화자의 실제 발화에 맞게 바로잡았다.',
      after: '아…… 형님……',
    },
    {
      index: 27,
      category: 'voice',
      reason: '니콜의 ～ッス 말투를 프로젝트의 「~슴다/~임다」 계열로 살렸다.',
      after: '유난히 조용함다',
    },
    {
      index: 37,
      category: 'natural_korean',
      reason: 'ホールの女主人의 소유 관계가 자연스럽게 드러나도록 조사를 보완했다.',
      after: '홀의 여주인',
    },
    {
      index: 49,
      category: 'meaning_terminology',
      reason: '仕立屋는 재단사 개인이 아니라 상점인 양장점을 가리키므로 기존 상점 표기에 맞췄다.',
      after: '『페넬로페』의 양장점',
    },
    {
      index: 64,
      category: 'grammar',
      reason: '기계가 작동했다는 起動した의 뜻이 자연스럽도록 피동 표현 「가동되다」를 사용했다.',
      after: `……오이겐.
호제아 님께선 어떻게 되신 건가.
어째서 갑자기 하얀 창이 가동된 거지?`,
    },
    {
      index: 79,
      category: 'natural_korean',
      reason: '소지 한도 때문에 더 들 수 없다는 持ちきれない의 뜻을 자연스럽게 다듬었다.',
      after: '미안, 더는 들 수 없는 모양이야',
    },
    {
      index: 114,
      category: 'natural_korean_voice',
      reason: '짧은 경고 대사가 자연스러운 구어체로 들리도록 종결을 다듬었다.',
      after: '탄막이 얇아!',
    },
    {
      index: 119,
      category: 'numeric_fidelity',
      reason: '혼자 남겨 둔 인원수 １과 전각 숫자 형태를 보존했다.',
      after: `……１명만 남겨 둬서 미안해.
푹 쉬어`,
    },
  ],
  batch_0148: [
    {
      index: 22,
      category: 'natural_korean_voice',
      reason: '놀라서 되묻는 짧은 대사가 자연스럽게 들리도록 의문 종결을 보완했다.',
      after: '뭐! 거짓말이지!?',
    },
    {
      index: 62,
      category: 'typo_voice',
      reason: 'あ의 머뭇거림이 「혀」로 잘못 옮겨진 오타를 「아」로 바로잡았다.',
      after: '아, 형니임~!',
    },
    {
      index: 80,
      category: 'natural_korean',
      reason: '소지 한도 때문에 더 들 수 없다는 持ちきれない의 뜻을 자연스럽게 다듬었다.',
      after: `미안, 그건 더는
들 수 없는 모양이야`,
    },
    {
      index: 114,
      category: 'meaning_natural_korean',
      reason: '鼻を高くする의 관용적 의미인 우쭐대는 모습을 인물 라벨에 반영했다.',
      after: '우쭐대는 노인',
    },
    {
      index: 118,
      category: 'natural_korean',
      reason: 'ずっとお留守番してる를 자연스러운 한국어인 「계속 집을 지키고 있어」로 다듬었다.',
      after: `엄마……
낮에는 일하고 있어……
그래서 계속 집을 지키고 있어`,
    },
    {
      index: 132,
      category: 'meaning',
      reason: '取り違える를 단순히 헷갈리게 한다는 뜻이 아니라 잘못 판단한다는 뜻으로 옮겼다.',
      after: '착각하는 여자',
    },
    {
      index: 151,
      category: 'natural_korean_voice',
      reason: '비명을 알아차리고 놀라는 대사가 자연스럽게 들리도록 종결을 다듬었다.',
      after: '비명이야!?',
    },
    {
      index: 163,
      category: 'voice',
      reason: '니콜의 ～ッス 말투를 프로젝트의 「~슴다/~임다」 계열로 살렸다.',
      after: `또 에블로
되돌아가게 됐슴다……`,
    },
    {
      index: 200,
      category: 'meaning',
      reason: '送る를 단순히 보내다가 아니라 비광정으로 목적지까지 데려다준다는 문맥으로 옮겼다.',
      after: '내가 데려다주게 해 줘!',
    },
  ],
  batch_0149: [
    {
      index: 43,
      category: 'voice',
      reason: '니콜의 ～ッス 말투를 프로젝트의 「~슴다/~임다」 계열로 살렸다.',
      after: '드디어임다',
    },
    {
      index: 60,
      category: 'natural_korean',
      reason: '무슨 일이 생긴 뒤에는 이미 늦는다는 경고가 자연스럽게 이어지도록 다듬었다.',
      after: `우리도 서둘러야 한다
마리아에게 무슨 일이 생긴 뒤에는
――이미 늦는다`,
    },
    {
      index: 80,
      category: 'voice',
      reason: 'よ、よく의 말더듬을 한국어 발화의 「자, 잘」로 자연스럽게 재현했다.',
      after: '자, 잘 먹는 개구나…',
    },
    {
      index: 90,
      category: 'meaning',
      reason: 'もてなす의 손님을 환대하고 대접한다는 뜻을 인물 라벨에 반영했다.',
      after: '손님을 대접하는 코핀',
    },
    {
      index: 96,
      category: 'voice',
      reason: '방법을 찾겠다는 探すぞ를 서술문이 아니라 일행을 이끄는 의지형 대사로 옮겼다.',
      after: `――아래로 돌아가도 소용없다
지상으로 돌아갈 방법을 찾자`,
    },
    {
      index: 98,
      category: 'natural_korean',
      reason: '보고를 잊지 말라는 안내 문장의 목적격 조사를 자연스럽게 다듬었다.',
      after: `길드에 보고하는 걸
잊지 마세요~`,
    },
    {
      index: 117,
      category: 'meaning',
      reason: '이름 뒤의 （仮）를 임시 상태가 아니라 임시로 붙인 명칭이라는 뜻의 「가칭」으로 옮겼다.',
      after: '린다(가칭)',
    },
    {
      index: 131,
      category: 'natural_korean',
      reason: '두 시설 중 마음에 드는 곳을 고르라는 안내가 완결된 한국어 문장으로 들리도록 다듬었다.',
      after: `여기는 카르분클루스가 자랑하는
풀헤임 최고의 유흥가야!!<$0C>쭉 직진하면 『카지노』
막다른 곳에서 꺾으면 『투기장』
어느 쪽이든 마음에 드는 곳으로 가세요!`,
    },
    {
      index: 148,
      category: 'natural_korean',
      reason: '宿の看板娘의 소속 관계가 자연스럽게 드러나도록 조사를 보완했다.',
      after: '여관의 간판 아가씨',
    },
    {
      index: 158,
      category: 'natural_korean',
      reason: '의장이 언제라도 돌아올 수 있게 저택을 지킨다는 문장 구조를 자연스럽게 다듬었다.',
      after: `그린힐 의장께서
언제라도 돌아오실 수 있도록
저택을 경비하고 있습니다<$0C>대단히 죄송하지만
이 앞은 누구도
통과시킬 수 없습니다`,
    },
    {
      index: 160,
      category: 'meaning',
      reason: '行かせない를 보내지 않겠다는 뜻이 아니라 상대가 떠나도록 두지 않겠다는 뜻으로 바로잡았다.',
      after: '가게 두지 않겠어!',
    },
    {
      index: 177,
      category: 'natural_korean',
      reason: '얼마 전에 열이 났기 때문에 외출하지 못한다는 아이의 설명을 자연스럽게 다듬었다.',
      after: `이젠 멀쩡한데
오늘도 놀러
나가면 안 된대……<$0C>얼마 전에 열이 난 지
얼마 안 됐다고……
모처럼 새로운 놀이도 생겼는데`,
    },
  ],
};

function readJsonl(filePath) {
  const text = fs.readFileSync(filePath, 'utf8');
  const lines = text.split(/\r?\n/).filter((line) => line.length > 0);
  return lines.map((line, i) => {
    try {
      return JSON.parse(line);
    } catch (error) {
      throw new Error(`${filePath}:${i + 1}: ${error.message}`);
    }
  });
}

function withoutTranslation(row) {
  const clone = { ...row };
  delete clone.translation_ko;
  return clone;
}

for (const [batchId, edits] of Object.entries(corrections)) {
  const sourcePath = path.join(ROOT, 'tm_v2', 'batches', 'source', `${batchId}.jsonl`);
  const draftPath = path.join(ROOT, 'drafts', `${batchId}.jsonl`);
  const reviewedPath = path.join(ROOT, 'reviewed', `${batchId}.jsonl`);
  const reportPath = path.join(ROOT, 'reviews', `${batchId}_review.json`);

  const sourceRows = readJsonl(sourcePath);
  const draftRows = readJsonl(draftPath);
  const expected = expectedCounts[batchId];
  if (sourceRows.length !== expected || draftRows.length !== expected) {
    throw new Error(`${batchId}: expected ${expected} rows, got source=${sourceRows.length}, draft=${draftRows.length}`);
  }

  for (let i = 0; i < expected; i += 1) {
    if (sourceRows[i].tm_id !== draftRows[i].tm_id) {
      throw new Error(`${batchId}:${i + 1}: source/draft tm_id mismatch`);
    }
  }

  const reviewedRows = draftRows.map((row) => ({ ...row }));
  const modifications = [];
  const seenIndexes = new Set();

  for (const edit of edits) {
    const rowIndex = edit.index - 1;
    if (seenIndexes.has(edit.index)) {
      throw new Error(`${batchId}:${edit.index}: duplicate correction index`);
    }
    seenIndexes.add(edit.index);
    if (rowIndex < 0 || rowIndex >= reviewedRows.length) {
      throw new Error(`${batchId}:${edit.index}: correction index out of range`);
    }

    const before = reviewedRows[rowIndex].translation_ko;
    if (before === edit.after) {
      throw new Error(`${batchId}:${edit.index}: correction does not change translation_ko`);
    }

    reviewedRows[rowIndex].translation_ko = edit.after;
    modifications.push({
      index: edit.index,
      tm_id: reviewedRows[rowIndex].tm_id,
      source_text: reviewedRows[rowIndex].source_text,
      before,
      after: edit.after,
      category: edit.category,
      reason: edit.reason,
    });
  }

  for (let i = 0; i < expected; i += 1) {
    const beforeMetadata = JSON.stringify(withoutTranslation(draftRows[i]));
    const afterMetadata = JSON.stringify(withoutTranslation(reviewedRows[i]));
    if (beforeMetadata !== afterMetadata) {
      throw new Error(`${batchId}:${i + 1}: a field other than translation_ko changed`);
    }
  }

  fs.mkdirSync(path.dirname(reviewedPath), { recursive: true });
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });
  fs.writeFileSync(reviewedPath, `${reviewedRows.map((row) => JSON.stringify(row)).join('\n')}\n`, 'utf8');

  const report = {
    schema: 'arf-translation-independent-review-v1',
    batch_id: batchId,
    reviewer: REVIEWER,
    draft_translator: DRAFT_AUTHOR,
    draft_author: DRAFT_AUTHOR,
    independent_review: true,
    translation_engine_policy: 'Codex internal models only',
    external_translation_services_used: [],
    external_translation_models_or_apis_used: [],
    source: sourcePath.replaceAll('\\', '/'),
    draft: draftPath.replaceAll('\\', '/'),
    reviewed_output: reviewedPath.replaceAll('\\', '/'),
    reviewed_units: expected,
    modified_units: modifications.length,
    unchanged_units: expected - modifications.length,
    correction_count: modifications.length,
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
    corrections: modifications,
    verification_execution: {
      status: 'deferred_by_user_instruction',
      executed_tools: [],
      not_executed: ['validator', 'fit', 'encoding', 'boundary_audit'],
      note: '사용자 지시에 따라 별도 validator, fit, encoding, boundary audit를 실행하지 않았다.',
    },
  };

  fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  console.log(`${batchId}: reviewed=${expected}, corrections=${modifications.length}`);
}
