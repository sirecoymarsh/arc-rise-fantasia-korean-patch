const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..');

const batches = {
  '0091': [
    [2, '이 늙은이는 언제나 생각하지……\n자신이 대신 죽어 줄 수 있다면 좋겠다고.\n그럴 수 있을 리 없는데도……', 'speaker_voice', '화자가 자신을 가리키는 노년의 자조적인 말투가 자연스럽게 드러나도록 다듬었다.'],
    [11, '초조한 게 아니야', 'grammar', '부정 구문의 의존 명사와 조사를 자연스럽게 바로잡았다.'],
    [21, '그렇게 음식점에 물었더니\n나를 보고 웃었어……', 'meaning', '단순히 웃음의 대상이 되었다는 원문의 뜻을 과도한 적의 없이 복원했다.'],
    [24, '정신 세계에서는 ELV 효과를 내지 않습니다\n', 'orthography', '일반 명사 결합의 띄어쓰기를 바로잡았다.'],
    [27, '어라?\n너도 일하다\n몰래 빠져나온 참이야?<$0C>……응?\n아, 아니구나. 미안해.\n공범이 필요했거든', 'naturalness', '일에서 물리적으로 빠져나온다는 직역을 몰래 자리를 비운 상황에 맞게 다듬었다.'],
    [31, '투기장에 카지노――\n이 도시는 지루할 틈이 없어서\n오래 머물러도 질리지 않네', 'naturalness', '오래 체류하는 것이 부담스럽지 않다는 뜻을 자연스러운 한국어로 옮겼다.'],
    [32, '난 최강……\n난 무적……\n누구에게든 이길 수 있어――아마도', 'meaning', '자신을 다독이면서도 확신하지 못하는 문말의 뉘앙스를 복원했다.'],
    [51, '멋진 여자란\n언제나 사랑에 빠져 있는 법이야.\n동행분도 그렇게 생각하지?', 'honorifics', '함께 온 사람을 가리키는 호칭을 자연스럽고 예의 있게 다듬었다.'],
    [55, '자무엘 무예관으로\n', 'proper_noun', '용어집의 고정 지명인 자무엘 무예관을 적용했다.'],
    [56, '아름다운 알스 님을\n만날 수 있다길래\n무예관에 들어왔는데……', 'terminology', '자무엘 무예관과 연결되는 시설 명칭을 일관되게 통일했다.'],
    [60, '밤늦게까지 깨어 있으니까\n좀처럼 감기가 낫지 않잖아!\n――알겠어?', 'naturalness', '시간이 지나도 낫지 않는다는 표현을 자연스러운 관용으로 다듬었다.'],
    [61, '이 공간의……\n맨 끝까지 가 주지 않을래', 'meaning', '공간의 가장 먼 끝을 향한다는 의미를 분명하게 복원했다.'],
    [64, '여기는 코핀 마을.\n코핀의 영웅, 오랜만이야.\n즐겁게 지내다 가면 좋겠어', 'naturalness', '방문객에게 즐겁게 머물다 가길 바라는 인사를 자연스럽게 다듬었다.'],
    [74, '상실을 겪은 아가씨', 'meaning', '무언가를 잃은 여성을 가리키는 수식 구조를 딸을 잃어버렸다는 뜻으로 오해한 번역을 바로잡았다.'],
    [78, '여기서는 일단 따르자――', 'meaning', '당장은 상대의 지시에 따르기로 한다는 판단을 분명하게 옮겼다.'],
    [83, '비용은 들겠지만\n길드에서 용병을 구해\n육로로 갈 수밖에 없겠네요……', 'word_choice', '용병을 수배한다는 뜻에 맞도록 동사를 자연스럽게 교체했다.'],
    [96, '뭐, 동료들은 모〜두\n그 이상한 여자들에게\n죽었지만 말이야', 'speaker_voice', '거친 화자의 말투와 완결된 문말을 살려 자연스럽게 다듬었다.'],
    [97, '정말 믿을 수 없는 나라야.\n메리디아는 말이지', 'naturalness', '뒤늦게 화제를 덧붙이는 원문의 도치 어감을 한국어 문말로 살렸다.'],
    [119, '엄청난 전개네……\n지금쯤 성 쪽은 큰 소동이겠어!', 'word_choice', '사건 전개가 격렬하고 대단하다는 뜻을 장렬하다는 부자연스러운 표현에서 바로잡았다.'],
    [120, '배가 흔들리지 않는 걸 보면\n어딘가에 떠밀려 닿은 걸까', 'meaning', '배가 표류 끝에 어딘가에 닿았다는 의미를 자연스럽게 풀어 옮겼다.'],
    [130, '좀처럼 없는 일이잖아?\n우리 같은 장인이\n이렇게 성 근처로 불려 오다니', 'grammar', '반문형 종결을 자연스럽게 바로잡았다.'],
    [131, '정직하게 벌어서는\n언제까지나 하류 생활을\n벗어나지 못해<$0C>범죄에 가까운 짓을 하지 않으면\n상층 구역에 사는 건 꿈도 못 꿀 일.\n……난 위로 올라가겠어', 'idiom', '실현 가능성이 극히 낮다는 관용 표현을 자연스러운 한국어로 교체했다.'],
    [135, '아차, 깜빡할 뻔했네<$0C>자무엘 할아버지에게\n앞으로의 일을\n상의하기로 했었지', 'meaning', '위험을 알리는 말이 아니라 약속을 잊을 뻔했다는 상황임을 복원했다.'],
    [136, '그러고 보니 지금 나――\n차인 거야?', 'idiom', '문득 자신의 처지를 깨닫는 도입부를 자연스러운 한국어 관용으로 다듬었다.'],
    [141, '받겠다니, 용사의 길을 걷는 녀석이\n할 말이냐', 'naturalness', '용사의 도를 닦는다는 표현을 자연스러운 한국어로 다듬었다.'],
    [149, '라르크 형님께.\n여러모로 생각해 봤지만, 역시 저는\n용병 체질이 아닌 모양입니다', 'naturalness', '편지 문체와 용병 일이 맞지 않는다는 뜻을 간결하고 자연스럽게 다듬었다.'],
    [155, '……그러고 보니 너――\n그 얼굴…… 어디선가 본 것 같은\n느낌이 드는데……', 'grammar', '어디선가 본 듯하다는 추측 구문을 자연스럽게 완성했다.'],
    [178, '무구점 『이어지는 별』', 'terminology', '무기와 방어구를 함께 취급하는 시설 명칭을 무구점으로 바로잡았다.'],
    [193, '한사코 지키는 경비병', 'naturalness', '완고한 태도로 지키는 상태를 NPC 표제에 어울리는 간결한 표현으로 다듬었다.']
  ],
  '0092': [
    [12, '당신들 관광객 덕분에\n우리도 먹고사는 거니까.\n무슨 일 있으면 언제든 얘기해<$0C>이런 오락은\n세상이 흉흉할 때일수록 돈이 돼.\n그러니 제국에 감사해야겠군!', 'naturalness', '상담에 응하겠다는 호의를 화자의 말투에 맞는 자연스러운 표현으로 다듬었다.'],
    [27, '음식점은 왜\n리코와 음식을 바꿔 주는 거야?\n음식점은 리코를 먹는 거야?', 'meaning', '화폐 리코와 음식을 교환한다는 아이의 질문에서 교환 의미가 누락된 부분을 복원했다.'],
    [32, '이런 날에는 대성당에 가서\n손이 까질 만큼\n계속 기도하면 불안하지 않을 텐데', 'naturalness', '손의 피부가 벗겨질 만큼 기도한다는 과장을 자연스러운 한국어로 다듬었다.'],
    [33, '침착해야 한다는 건\n알고 있지만\n아무래도 안 되겠어……', 'grammar', '부자연스러운 침착하다 활용을 자연스러운 의무 표현으로 바로잡았다.'],
    [41, '아까 마을 남자가\n시비를 걸어오길래\n도리어 혼내 줬지<$0C>그 녀석 소지품에\n이런 게 들어 있길래\n너한테 주마', 'naturalness', '시비를 건 상대를 되받아친 상황과 소지품 표현을 자연스럽게 다듬었다.'],
    [42, '요즘 도시 사람들이\n『붉은 달』이라는 말을 자주 하던데\n대체 무슨 이야기야?<$0C>달이라면 어릴 때 자주 듣던\n동화에 나온 것 같기도 한데……', 'naturalness', '옛날이라는 말의 반복을 없애고 어린 시절 들은 동화라는 의미를 자연스럽게 옮겼다.'],
    [54, '알스 님은 노력파시지.\n……그래서 공감할 수 있어.\n세상은 재능이 전부가 아니야', 'word_choice', '재능형이 아닌 노력형 인물이라는 뜻을 간결한 고정 표현으로 옮겼다.'],
    [67, '분명 안트락스는\n다시 살아날 거야<$0C>이곳 사람들은 목숨을 내놓은 건가?\n싶을 정도로\n열심히 일하거든', 'meaning', '사람들이 몸을 사리지 않고 일한다는 의미를 분명하게 복원했다.'],
    [86, '숲의 결정화, 이제 막을 수 없어.\n코핀의 영웅, 이 마을을\n구해 주지 않겠습니까?', 'honorifics', '도움을 청하는 원문의 정중한 종결을 반영했다.'],
    [98, '이 마을 서쪽에\n그라 자혜교회라는\n건물이 있는 건 알고 있나?<$0C>사쥬와 마리아를 비롯해\n마을의 많은 젊은이가\n그곳에서 자랐지', 'proper_noun', '용어집과 기존 지명 표기에 맞춰 그라 자혜교회의 띄어쓰기를 통일했다.'],
    [118, '옛날에는…… 친구들과 함께\n바다 어디에서 파도가 시작되는지\n『보인다』『거짓말이야』 하며<$0C>바라보곤 했지요', 'naturalness', '친구들과 파도의 시작점을 두고 주고받던 말을 자연스러운 직접화법으로 다듬었다.'],
    [126, '머지않아 이 세상에서\n좋은 술과 맛있는 음식도 사라지겠지<$0C>그게 법이니 어쩔 수 없지만\n그건 그것대로 따분한 세상이군……', 'meaning', '그러한 금지가 법이기 때문에 어쩔 수 없다는 인과관계를 복원했다.'],
    [143, '바이스가 죽은 덕분에\n회의 횟수가 눈에 띄게 줄어서\n난 정말 살 것 같아……<$0C>비좁은 의회에서 계속\n논의를 이어 가다 보면\n숨이 막힐 지경이거든……', 'meaning', '줄어든 대상이 의원 수가 아니라 의회 회의 횟수라는 문맥을 바로잡았다.'],
    [147, '큰맘 먹고 창으로 바꾼다든가……\n하지만 창은 멋도 없고\n다들 놀려 대니까 말이야', 'meaning', '창을 쓰면 주변 사람들에게 놀림받는다는 뜻을 바보 취급이라는 과한 해석에서 바로잡았다.'],
    [165, '어느 섭리도 선택하지 않은 이사의 아이여\n신에게 맞서고 싶다면\n신을 낳은 나를 당당히 쓰러뜨려 보아라', 'terminology', '세계관 용어 定理를 용어집의 고정 번역인 섭리로 통일하고 문장을 다듬었다.'],
    [191, '로그레스는 어쩔 거야?', 'meaning', '로그레스 수집을 어떻게 할 것인지 묻는 문맥을 상태 확인으로 오해하지 않도록 바로잡았다.'],
    [198, '에블로 돌아간다 해도\n지금은 신제국 헌장 때문에\n마음 놓고 외출할 수도 없어', 'idiom', '거리낌 없이 외출할 수 없다는 뜻을 뻔뻔하다는 부정확한 표현에서 바로잡았다.']
  ],
  '0093': [
    [15, '저는 결심했습니다<$0C>만약 이사의 아이가 신의 섭리를 고르기 위해\n로그레스를 모으려 한다면\n이사의 아이를 죽이겠다고', 'terminology', '세계관 용어 定理를 용어집의 고정 번역인 섭리로 통일했다.'],
    [21, '나는 좋은 뜻으로 한 일이\n언제나 나쁜 결과로 돌아오는 타입이야.\n있지? 그런 불행한 사람……', 'naturalness', '선의로 한 일이 늘 역효과를 낸다는 뜻을 자연스러운 한국어로 다듬었다.'],
    [33, '라르크는 나를 선택한 게 아니야――\n이매지널의 섭리를 고르도록\n강요당한 거야!', 'meaning', '라르크가 자의로 화자이자 이매지널의 섭리를 택한 것이 아니라 강요받았다는 관계를 명확히 하고 고정 용어를 적용했다.'],
    [39, '너무 빈둥거리지만 말고\n가끔은 무예관으로\n돌아와 줘!<$0C>무예관 아이들도\n라르크와 대련하기를\n기대하고 있으니까!', 'terminology', '자무엘 무예관과 연결되는 시설 명칭을 일관되게 통일했다.'],
    [41, '얼마 전에 제도에서 인사 발령이 내려왔어.\n아무래도 디아만트 발령이\n정식으로 결정된 모양이야<$0C>영전이라고 생각하지만\n이 녀석들을 생각하면\n별로 내키지 않아', 'meaning', '인사 명령을 뜻하는 辞令를 사령장으로 오해한 번역을 바로잡았다.'],
    [45, '엉뚱한 청년', 'meaning', '꾸밈없고 다소 엉뚱한 성격을 가리키는 天然을 천연덕스럽다는 다른 의미에서 바로잡았다.'],
    [67, '차분한 개', 'meaning', '개가 차분한 상태임을 사람의 마음을 편안하게 해 준다는 사역 의미로 오해한 번역을 바로잡았다.'],
    [84, '나도 당신과 같아……\n이 순간을 그대로 담아\n액자에 넣어 장식하고 싶을 만큼……', 'idiom', '행복한 순간을 사진처럼 간직하고 싶다는 비유를 자연스러운 한국어로 다듬었다.'],
    [97, '마하트 폐하의 사인에 관해\n병으로 숨졌다고 발표할 모양이지만\n그걸 믿는 녀석은 아무도 없어', 'word_choice', '병사를 군인으로 오해할 여지가 없도록 병으로 숨졌다는 의미를 명확히 했다.'],
    [99, '저는 귀족들을\n별로 좋게 보지 않습니다<$0C>잘난 듯이 거들먹거리는 게\n취미인 것 같은 사람들이니까요……', 'naturalness', '좋은 인상을 품는다는 부자연스러운 결합을 자연스러운 평가 표현으로 다듬었다.'],
    [100, '마침내 바트라키테스마저\n제국의 손에 넘어갔다……<$0C>제국이 그 송곳니를 북쪽으로 돌리는 건\n시간문제 아닌가……\n딸아…… 부디 무사하기를……', 'word_choice', '침략 의지를 비유하는 牙를 이빨보다 문맥에 맞는 송곳니로 다듬었다.'],
    [106, '보기와는 다른 병사', 'naturalness', '겉보기와 실제 인상이 다르다는 NPC 표제를 간결하고 자연스럽게 다듬었다.'],
    [110, '우리는 오팔루스 주둔 부대 사령관\n엘리엇 중장의 사절이다!', 'meaning', '중장의 명을 받고 온 사절을 하수인으로 오해한 번역을 바로잡았다.'],
    [136, '에블과 바트라키테스를 거쳤으니\n다음 표적은 어디일까요?<$0C>단숨에 수도를 함락시킬지\n정신적 지주인 성도를 함락시킬지\n……공화국의 전황은 좋지 않군요', 'naturalness', '노림을 받는다는 부자연스러운 피동 표현을 다음 공격 표적이라는 자연스러운 말로 다듬었다.'],
    [146, '라르크 씨는 형님과\n정말 많이 닮았네요<$0C>형님이 인류의 미래를 맡긴 것도\n조금은 이해할 것 같아요', 'meaning', '형이 라르크에게 인류의 미래를 맡긴 까닭을 이해한다는 주체와 대상을 명확히 했다.'],
    [163, '무예관 같은\n수상쩍은 장사를 하니까\n이런 일을 당하는 거다<$0C>『유유상종』이라는 말도 있지.\n아무리 배움이 짧은 자네라도\n속담의 뜻은 알겠지?', 'terminology', '자무엘 무예관과 연결되는 시설 명칭을 일관되게 통일했다.'],
    [166, '이 사관학교 졸업생 대부분이\n공화국 전역의 주둔군에\n신병으로 파견되고 있어<$0C>말하자면 이곳은\n공화국의 무기고――\n그렇게 말해도 과장은 아니야', 'grammar', '파견 신분을 나타내는 조사와 서술을 자연스럽게 바로잡았다.'],
    [193, '귀여운 여자애라도\n입문해 주면 좋을 텐데……<$0C>『선배』라고\n불러 주기도 하고……', 'terminology', '무예관에 들어오는 일을 학교 입학이 아닌 입문으로 옮기고 호칭을 직접적으로 다듬었다.']
  ]
};

for (const [num, modifications] of Object.entries(batches)) {
  const batchId = `batch_${num}`;
  const draftRel = `work/translation/drafts/${batchId}.jsonl`;
  const sourceRel = `work/translation/tm_v2/batches/source/${batchId}.jsonl`;
  const reviewedRel = `work/translation/reviewed/${batchId}.jsonl`;
  const reviewRel = `work/translation/reviews/${batchId}_review.json`;
  const draftPath = path.join(root, draftRel);
  const rows = fs.readFileSync(draftPath, 'utf8').trimEnd().split(/\r?\n/).map(JSON.parse);
  const reportMods = [];

  for (const [rowIndex, after, category, reason] of modifications) {
    const row = rows[rowIndex];
    const before = row.translation_ko;
    row.translation_ko = after;
    reportMods.push({
      row_index: rowIndex,
      tm_id: row.tm_id,
      source_text: row.source_text,
      before,
      after,
      category,
      reason
    });
  }

  fs.mkdirSync(path.dirname(path.join(root, reviewedRel)), { recursive: true });
  fs.mkdirSync(path.dirname(path.join(root, reviewRel)), { recursive: true });
  fs.writeFileSync(path.join(root, reviewedRel), rows.map((row) => JSON.stringify(row)).join('\n') + '\n', 'utf8');

  const report = {
    schema: 'arf-translation-independent-review-v1',
    batch_id: batchId,
    reviewer: '/root/audit_boundary_integration',
    draft_translator: '/root/translate_batch_0009',
    draft_author: '/root/translate_batch_0009',
    independent_review: true,
    translation_engine_policy: 'Codex internal models only',
    external_translation_services_used: [],
    external_translation_models_or_apis_used: [],
    sources: {
      draft: draftRel,
      source: sourceRel,
      rules: 'work/translation/tm_v2/TRANSLATION_RULES.md',
      style_guide: 'work/translation/glossary_agent/style_guide.md',
      glossary: 'work/translation/glossary_agent/glossary.csv'
    },
    output: reviewedRel,
    row_count: rows.length,
    reviewed_row_count: rows.length,
    modified_row_count: reportMods.length,
    unchanged_row_count: rows.length - reportMods.length,
    modifications: reportMods,
    verification_execution: {
      status: 'deferred_by_user_instruction',
      executed_tools: [],
      not_executed: ['validator', 'fit', 'encoding', 'boundary_audit'],
      note: '사용자 지시에 따라 별도 validator, fit, encoding, boundary audit를 실행하지 않았다.'
    }
  };

  fs.writeFileSync(path.join(root, reviewRel), JSON.stringify(report, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify({
    batch: batchId,
    reviewed: rows.length,
    modified: reportMods.length,
    output: reviewedRel,
    review: reviewRel
  }));
}
