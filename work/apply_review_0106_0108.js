const fs = require('fs');
const path = require('path');

const root = path.join('work', 'translation');
const reviewer = '/root/translate_batch_0009';
const draftAuthor = '/root/review_batch_0058_0060';

const batches = {
  '0106': [
    {
      tm_id: 'ARF-TM-76C13F6003B19D4A115C',
      after: '나 봤어.\n자다가 습격당했을 때\n검을 들고 싸워 준 사람들――<$0C>쌍검으로 적을 쓸어버린 남자와\n큰 검을 든 젊은이……\n――２명 모두 훌륭한 솜씨였지',
      category: 'numeric_fidelity',
      reason: '원문의 전각 숫자 「２」를 복원하면서 문장 의미와 줄바꿈을 유지했다.',
    },
    {
      tm_id: 'ARF-TM-77345C31F484133AB875',
      after: '이제 안 그럴게!\n짐이 되지 않을 테니까!',
      category: 'meaning',
      reason: '「足手まとい」를 단순한 방해가 아니라 동료에게 짐이 되는 의미로 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-77D59CDEFD7DC12BE79C',
      after: '이 앞은 초소입니다.\n공화국을 타도하기 위해\n병사들이 기력을 보충하고 있습니다',
      category: 'natural_korean',
      reason: '「英気を養う」의 뜻을 자연스러운 한국어 관용 표현으로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-78256E20893EF2824A73',
      after: '설마 메리디아 가문의 사람이\n이 오팔루스 도시를\n구해 줄 줄은 몰랐어<$0C>인간은 피에\n얽매이는 존재가 아니다――인가<$0C>알폰스 메리디아가 아니라\n그저 『알스 님』이라면\n나도 전력을 다해 응원할게',
      category: 'grammar',
      reason: '「メリディア家」를 ‘메리디아 가문’으로 옮겨 잘못된 조사 결합을 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-78ABAD5B99AD21A33A56',
      after: '오늘은 동경하던 선배에게 고백할 거야.\n아아…… 가슴 두근거림이 멈추지 않아!\n신이시여――제게 용기를 주세요!',
      category: 'natural_korean',
      reason: '가슴과 두근거림의 서술 관계를 자연스럽게 정리했다.',
    },
    {
      tm_id: 'ARF-TM-78BA7C234FA626D51317',
      after: '분명 까다로운 상대였던 거 아니야?',
      category: 'grammar',
      reason: '부정 의문문의 잘못된 시제 결합을 자연스럽게 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-78E362EAE4F842BBEF97',
      after: '역사적인 관점에서 봐도\n지금 제국 같은 통제 경제가\n잘된 사례는 없습니다<$0C>……제 개인적인 의견입니다만\n알스 황제의 신제국 헌장은\n미숙한 졸책이라고 생각합니다',
      category: 'natural_korean',
      reason: '「稚拙な愚策」의 중복 직역을 피하면서 미숙한 정책이라는 평가를 살렸다.',
    },
    {
      tm_id: 'ARF-TM-7912C49FB24C450DA180',
      after: '알스 황자였나?<$0C>연설은 훌륭했지만\n구체적인 건\n하나도 말하지 않았잖아?<$0C>어른들은 바보라니까.\n그런 말에 쉽게\n신봉자가 되어 주잖아',
      category: 'grammar',
      reason: '「何ひとつ言ってなくない？」의 반문을 자연스러운 한국어 부정 의문문으로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-7912C720861B853D73EF',
      after: '위기를 기회로 바꾸는 게\n일류 행상인――<$0C>사막에서 길을 잃었다면\n여기서만 나는 특산품을\n잔뜩 챙겨서 돌아가겠습니다',
      category: 'voice',
      reason: '원문의 정중한 상인 말투를 끝까지 유지하고 마지막 동작을 자연스럽게 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-792BA4A097635DF39E6B',
      after: '……역시 여기도\n제국에 제압돼 있슴다',
      category: 'character_voice',
      reason: '니콜의 「～ッス」 말투를 프로젝트 표기인 ‘~슴다’로 통일했다.',
    },
    {
      tm_id: 'ARF-TM-7A1E82156CAF9EBE8012',
      after: '요즘 삼각관계에 빠졌습니다.\n이쪽을 세우면 저쪽이 서지 않고\n양쪽 사이에 끼어 고생한다는 그거<$0C>상당히 복잡한 상황이지만\n그걸 즐길 여유가 필요하다고 봅니다<$0C>이 상황만 벗어나면\n코핀은 한층 성장해 있을 겁니다',
      category: 'idiom',
      reason: '「一皮むける」를 문자 그대로 옮기지 않고 한층 성장한다는 관용 의미로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-7A84AF348EE0D5676EA1',
      after: '알스 황제에게 실망했어.\n뭐야, 신제국 헌장이라니……\n……바보 같아!<$0C>１명이라도 더 많은 사람을\n처형하기 위한 법으로밖에\n보이지 않아',
      category: 'numeric_fidelity',
      reason: '원문의 전각 숫자 「１」을 번역문에 복원했다.',
    },
  ],
  '0107': [
    {
      tm_id: 'ARF-TM-7ADB47A357B6B25A7923',
      after: '알스를 칭찬하는 놈들은\n제국의 반역자로 간주한다<$0C>화풀이로 죽기보다 더한 고통을\n맛보게 해 주자……!',
      category: 'meaning',
      reason: '「死ぬより辛い目」를 ‘죽는 것보다 더한 고통’이라는 의미로 명확히 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-7B530BB6C73F34D72388',
      after: '기막혀하실지도 모르지만\n사람의 약한 마음을 파고드는 건\n장사의 기본 중 기본이니까요',
      category: 'meaning',
      reason: '「呆れられる」를 ‘질리다’가 아닌 상대가 기막혀하는 반응으로 옮겼다.',
    },
    {
      tm_id: 'ARF-TM-7B7ECF6A4CE4376AA7A7',
      after: '너도 리얼신이\n세계를 구할 거라 믿고\n알스와 여행하는 건가',
      category: 'proper_noun',
      reason: '「リアル神」의 승인 표기를 ‘리얼신’으로 통일했다.',
    },
    {
      tm_id: 'ARF-TM-7B9A6530F3088D402EF1',
      after: '그것이 이매지널과 리얼의 섭리',
      category: 'proper_noun',
      reason: '세계관 고유명 「リアル」의 승인 표기를 ‘리얼’로 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-7C0E73AFED929320346F',
      after: '이렇게 깨끗하게 닦인\n바닥을 밟기만 해도\n마음이 충만해져',
      category: 'natural_korean',
      reason: '「満たされた気分」을 직역투가 아닌 자연스러운 심정 표현으로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-7C1552187AF4A0F1231A',
      after: '이 노인……\n왠지 사람을 끌어당기는 힘이 있어.\n자기 안을 바라본다……인가',
      category: 'meaning',
      reason: '「求心力」를 문맥상 사람을 끌어당기는 힘이라는 뜻으로 풀어 자연스럽게 옮겼다.',
    },
    {
      tm_id: 'ARF-TM-7CAB63C11843A5E75283',
      after: '군을 떠난 녀석의 마음도 알아.\n사람들에게 두려움과 외면을 받고……<$0C>사실은 사람들을 구하려고\n군대에 들어왔는데……',
      category: 'meaning',
      reason: '「軍を投げ出した」와 수동형 「恐れられ、避けられる」의 관계를 정확하게 복원했다.',
    },
    {
      tm_id: 'ARF-TM-7CE50D12BEBC7CB7302E',
      after: '저는 바다에 들어가지 않습니다.\n소금물과 궁합이 좋지 않습니다<$0C>유감스럽지만……',
      category: 'voice',
      reason: '한 대사 안에서 혼재하던 주어와 종결 어미를 정중체로 통일했다.',
    },
    {
      tm_id: 'ARF-TM-7D0FF3B371ED099D469C',
      after: '라필 님은…… 내게\n가장 존경하고 사랑한 분이었어……<$0C>그 목소리를 이제 접할 수\n없다고 생각하면 나는……',
      category: 'natural_korean',
      reason: '「敬愛すべきお方」의 존경과 애정이 함께 담긴 의미를 자연스럽게 풀었다.',
    },
    {
      tm_id: 'ARF-TM-7D4F46967957039321C8',
      after: '（하아…… 이 녀석들과 있으면\n　정말 지루할 틈은 없어）',
      category: 'formatting',
      reason: '원문의 전각 괄호와 행 머리 전각 공백을 그대로 복원했다.',
    },
    {
      tm_id: 'ARF-TM-7DB83D414EBDE1C704BA',
      after: '근엄한 표정의 병사',
      category: 'natural_korean',
      reason: '「厳格な顔つき」를 인물 라벨에 자연스러운 ‘근엄한 표정’으로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-7DEFFBBE252984859A3A',
      after: '……평화로운 건 좋지만\n너무 평화로우면 조금 지루하지.\n어디서 용재해라도 안 일어나나?',
      category: 'terminology',
      reason: '「竜災害」의 승인 용어를 ‘용재해’로 통일했다.',
    },
    {
      tm_id: 'ARF-TM-7E327DA40EC8DB18DD9C',
      after: '국교인 노스 노와레교회와\n공화국 수도 카르분클루스<$0C>……이 둘이 싸우면\n공화국은 어떻게 되는 거지?',
      category: 'proper_noun',
      reason: '교회 고유명의 프로젝트 표기 규칙에 맞춰 ‘노스 노와레교회’로 통일했다.',
    },
    {
      tm_id: 'ARF-TM-7E3FB1CDAD870FE0C521',
      after: '오늘도 밖은 좋은 날씨……\n느긋한 １일은\n이 마을의 소중한 재산이야',
      category: 'numeric_fidelity',
      reason: '원문의 전각 숫자 「１」을 번역문에 복원했다.',
    },
  ],
  '0108': [
    {
      tm_id: 'ARF-TM-7E80429DB89D2C9D1F20',
      after: '정원을 손질할 때도\n병사들을 무서워해야 하다니\n정말 웃기지도 않는 세상이야',
      category: 'grammar',
      reason: '「兵士に怯える」의 대상 관계가 드러나도록 조사를 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-7EC2F1F34E99B647D7D8',
      after: '추운 지방에서 자랐는데도\n이 기후는 너무 힘들어……',
      category: 'meaning',
      reason: '「寒冷地育ち」를 화자의 성장 배경으로 자연스럽게 옮겼다.',
    },
    {
      tm_id: 'ARF-TM-7EEAA65DAD09AEE9085F',
      after: '공화국은 지금 당장\n폭정에 시달리는 에블과 바트라키테스의\n백성을 제국에서 되찾아야 합니다',
      category: 'natural_korean',
      reason: '「悪政」의 어색한 한자 직역을 문맥에 맞는 ‘폭정’으로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-7EFB1802A36A58A5BA99',
      after: '여기는 코핀 마을.\n어서 와, 코핀의 영웅.\n느긋하게 쉬다 갔으면 해<$0C>……그렇게 말하라고\n저기 있는 코핀이 말했어.\n고을에 들면……이라는 거지',
      category: 'idiom',
      reason: '「郷に入れば」가 가리키는 속담을 알아보기 쉬운 한국어 관용 표현으로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-7F18443352C475492A18',
      after: '이 앞은 이사의 영역.\n나의 『지배』 로고스와――',
      category: 'grammar',
      reason: '명사 수식에서 겹친 조사를 제거해 자연스럽게 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-7F43A10422FCB86DD698',
      after: '후우…… 숨이 차 버렸습니다.\n１０살만 젊었다면……\n좀 더 여러 가지로 놀아 줬을 텐데',
      category: 'numeric_fidelity',
      reason: '원문의 전각 숫자 「１０」을 번역문에 복원했다.',
    },
    {
      tm_id: 'ARF-TM-80268478EC2363A37CDB',
      after: '당분간 이 도시에\n자리를 잡고\n장사에 힘쓸 생각입니다<$0C>매입과 판매를\n동시에 할 수 있는 도시는\n상인에게는 더없이 고마운 일입니다',
      category: 'grammar',
      reason: '도시 자체가 상인에게 고맙다는 직역을 ‘고마운 일’이라는 자연스러운 서술로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-8035309714842924B28E',
      after: '흥. 난 마슈가르의 정보가\n필요했을 뿐이다.\n난 에블로 돌아가겠다!',
      category: 'proper_noun',
      reason: '「マシュガル」의 승인 표기를 ‘마슈가르’로 통일했다.',
    },
    {
      tm_id: 'ARF-TM-805FBB81CA8BD0120EC6',
      after: '이상한 데 쓰면 안 돼, 알겠지?\n안 그러면……',
      category: 'meaning',
      reason: '경고형 의문과 「さもないと」의 조건 의미가 자연스럽게 이어지도록 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-807D66D54DE9183D95D9',
      after: '도구점 『실크햇당』',
      category: 'proper_noun',
      reason: '시스템 상점명에서 확립된 「山高帽堂」의 승인 표기 ‘실크햇당’을 적용했다.',
    },
    {
      tm_id: 'ARF-TM-80C4818300DE7330448B',
      after: '제국에서는 알스 폐하의\n폭정에 대한 불만이 높아져\n언제 반란이 일어나도 이상하지 않아<$0C>클라이드 장군 덕분에\n어떻게든 현 상황을 유지하지만\n그것도 언제까지 갈지……',
      category: 'meaning',
      reason: '「現状」를 현상(現象)이 아니라 현재 상황이라는 뜻으로 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-80E8D08B170E96740B36',
      after: '제국군이 바트라키테스까지……\n남은 건 카르분클루스와\n이 도시――베네트나슈지',
      category: 'grammar',
      reason: '도시명 뒤에 잘못 붙은 ‘군’을 제거하고 원문의 확인 어조를 살렸다.',
    },
    {
      tm_id: 'ARF-TM-81145FD2BAC2DE7F8663',
      after: '무, 무슨 일 있었나요?<$0C>도시 사람들에게서\n침울한 분위기가\n물씬 느껴지는데요……',
      category: 'natural_korean',
      reason: '「ダウナーな雰囲気」와 「ひしひし」를 자연스러운 한국어 분위기 묘사로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-81209F29DEE3C5D5FA41',
      after: '설국에서 자랐는데도\n추위에는 약해<$0C>이렇게 매일 거리 경비\n일을 떠넘기는 상관에게\n살의에 가까운 감정이 들어',
      category: 'natural_korean',
      reason: '「雪国育ち」를 자연스러운 한국어 ‘설국에서 자라다’로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-814CE31A567336B3C25E',
      after: '내 뒤에 포커를 한 녀석이\n눈앞에서 스트레이트 플러시를\n내 버렸어……<$0C>１번만, 딱 １번만 더\n버텼다면 나도……',
      category: 'numeric_fidelity',
      reason: '원문에 두 번 나오는 전각 숫자 「１」을 모두 복원했다.',
    },
    {
      tm_id: 'ARF-TM-8162C00083FAC12C8636',
      after: '자다에 도적을 들인 탓에\n수비대 병사들은 빠짐없이\n클라이드 장군의 호통을 들어야 합니다<$0C>다음은 제 차례입니다……\n차라리 빨리 끝났으면……',
      category: 'natural_korean',
      reason: '호통을 ‘기다린다’는 직역을 피하고 병사들이 질책받게 된 상황을 자연스럽게 표현했다.',
    },
    {
      tm_id: 'ARF-TM-8169E43EBA25141BC6D0',
      after: '（차이를 모르겠어……）',
      category: 'formatting',
      reason: '원문의 전각 괄호를 번역문에 복원했다.',
    },
    {
      tm_id: 'ARF-TM-8184339487362647EACE',
      after: '매일 주민 수를 세고\n외출 허가증 발급을 승인하며\n순찰병의 보고를 받는다――<$0C>매일 똑같은 반복 업무.\n아무리 해도\n나라에 공헌한다는 생각이 안 들어',
      category: 'meaning',
      reason: '「外出許可証の公布許可」를 허가증 발급 승인 업무라는 뜻으로 자연스럽게 고쳤다.',
    },
  ],
};

for (const [number, modifications] of Object.entries(batches)) {
  const batchId = `batch_${number}`;
  const sourceRel = `work/translation/tm_v2/batches/source/${batchId}.jsonl`;
  const draftRel = `work/translation/drafts/${batchId}.jsonl`;
  const reviewedRel = `work/translation/reviewed/${batchId}.jsonl`;
  const reviewRel = `work/translation/reviews/${batchId}_review.json`;
  const rows = fs.readFileSync(draftRel, 'utf8').split(/\r?\n/).filter(Boolean).map(JSON.parse);
  const byId = new Map(modifications.map((item) => [item.tm_id, item]));
  const reportMods = [];

  for (const row of rows) {
    const mod = byId.get(row.tm_id);
    if (!mod) continue;
    const before = row.translation_ko;
    row.translation_ko = mod.after;
    reportMods.push({
      tm_id: row.tm_id,
      source_text: row.source_text,
      before,
      after: mod.after,
      category: mod.category,
      reason: mod.reason,
    });
  }

  fs.mkdirSync(path.dirname(reviewedRel), { recursive: true });
  fs.mkdirSync(path.dirname(reviewRel), { recursive: true });
  fs.writeFileSync(reviewedRel, rows.map((row) => JSON.stringify(row)).join('\n') + '\n', 'utf8');

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
    modified_units: reportMods.length,
    unchanged_units: rows.length - reportMods.length,
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
    modifications: reportMods,
    verification_execution: {
      status: 'deferred_by_user_instruction',
      executed_tools: [],
      not_executed: ['validator', 'fit', 'encoding', 'boundary_audit'],
      note: '사용자 지시에 따라 별도 validator, fit, encoding, boundary audit를 실행하지 않았다.',
    },
  };
  fs.writeFileSync(reviewRel, JSON.stringify(report, null, 2) + '\n', 'utf8');
}
