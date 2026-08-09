const fs = require('fs');
const path = require('path');

const root = path.join('work', 'translation');
const reviewer = '/root/translate_batch_0009';
const draftAuthor = '/root/review_batch_0058_0060';

const batches = {
  '0097': {
    changes: {
      4: {
        after: '저기 있는 언니가……\n１명뿐이던 나를\n거둬 줬어……<$0C>친하게 지내고 싶지만……\n아주 친해진 뒤에\n잃으면 또 괴로울 테니까……',
        category: 'numeric fidelity',
        reason: '원문의 전각 숫자 １을 유지하면서 １人ぼっち의 의미를 자연스럽게 옮겼다.'
      },
      28: {
        after: '힘의 바이스 님……\n정의의 알스 님……\n둘 다 우열을 가리기 어렵군……',
        category: 'meaning',
        reason: '義를 문맥에 맞는 정의로 바로잡아 의의라는 오역을 수정했다.'
      },
      40: {
        after: '길다브와 아부심……',
        category: 'proper nouns',
        reason: 'アブシム의 승인 표기인 아부심을 적용했다.'
      },
      61: {
        after: '누군가를 먼저 떠나보내는 건 괴롭습니다.\n하지만 １번 괴로운 건\n그 뒤에도 삶이 계속된다는 것입니다<$0C>우리는 이제부터\n매일 아침 눈을 뜰 때마다\n마하트 폐하의 부재를 슬퍼하겠지요',
        category: 'numeric fidelity',
        reason: '원문의 １番에 포함된 전각 숫자 １을 보존했다.'
      },
      66: {
        after: '너무 성급한 것도\n참으로 문제일 텐데……',
        category: 'meaning',
        reason: '短絡的를 문맥상 성급하다는 뜻으로 바로잡았다.'
      },
      73: {
        after: '조, 좋아……\n다음은 내 차례군……<$0C>온몸이 덜덜 떨리기 시작했어……\n이게 싸움을 앞둔 전율이라는 건가……\n덜덜덜덜……',
        category: 'natural Korean',
        reason: '武者震い를 직역한 무사 떨림 대신 싸움을 앞둔 전율이라는 관용적 표현으로 고쳤다.'
      },
      88: {
        after: '당신이 공화국에서 두려움의 대상인\n사신 라군인가……<$0C>설마 나보다 젊다니\n솔직히 충격이군',
        category: 'meaning',
        reason: '恐れられる의 피동 의미가 드러나도록 공화국에서 두려움의 대상인으로 고쳤다.'
      },
      95: {
        after: '난 예전부터 협상에 서툴러.\n어설프게나마 말이 통하는 만큼\n상인은 몬스터보다 더 질이 나빠……',
        category: 'natural Korean',
        reason: 'なまじ의 뉘앙스를 살리면서 한국어 문장을 자연스럽게 다듬었다.'
      },
      142: {
        after: '사람은 누구나 １명만으로는 살 수 없는 법입니다.\n타인의 환심을 사기 위해\n뜻하지 않게 어떤 행동을 선택하지요<$0C>제게 강한 호감을 품어 준 이가\n여기 있는 아가씨입니다.\n이런 저를 좋아해 주고 있어요<$0C>――죄송합니다.\n붙잡아 두고 말았군요.\n제 나쁜 버릇입니다<$0C>수다가\n지나칠 때가 있거든요',
        category: 'numeric fidelity',
        reason: '１人의 전각 숫자 １을 유지하면서 문장의 뜻을 보존했다.'
      },
      178: {
        after: '제…… 제법 담백하네',
        category: 'natural Korean',
        reason: 'ず……随分의 말더듬을 한국어 첫 음절 반복으로 자연스럽게 재현했다.'
      },
      182: {
        after: '）입니다.\n',
        category: 'formatting',
        reason: '원문에 있는 전각 닫는 괄호를 그대로 보존했다.'
      }
    }
  },
  '0098': {
    changes: {
      4: {
        after: '라르크 상사――\n알스 전하와 클라이드 장군께\n절대 무례를 범하지 않도록',
        category: 'proper nouns',
        reason: '원문의 ラルク를 라군이 아닌 라르크로 바로잡았다.'
      },
      75: {
        after: '……어, 어이, 저건……!?',
        category: 'natural Korean',
        reason: 'お、おい의 당황한 말더듬을 누락하지 않고 자연스럽게 살렸다.'
      },
      88: {
        after: '화를 참느라 필사적입니다.\n아니, 당신들과는 상관없어요<$0C>그분이 돌아가셨다는 사실에\n아무것도 하지 못한 제 자신에게도\n분노하지 않을 수 없습니다',
        category: 'particles',
        reason: '분노의 대상이 사망 사실과 아무것도 못 한 자신임을 조사와 서술어로 명확히 했다.'
      },
      93: {
        after: '요즘은 비상사태가 자주 일어나\n강아지 산책도\n제대로 못 하는 날뿐이야……<$0C>그래서 오늘은 귀중한 날이야.\n당신도 눈치껏\n오늘만큼은 ２명끼리 있게 해 줄래?',
        category: 'numeric fidelity',
        reason: '원문의 ２人에 포함된 전각 숫자 ２를 보존했다.'
      },
      146: {
        after: '알스 따윈 믿을 수 없어.\n엄마를 죽인 제국의\n１인자잖아?<$0C>오르키나교도라 해도\n제국이 엄마를 죽인 건 달라지지 않아<$0C>내가 알스를 죽이고\n아델 님을 구해 드릴 거야!',
        category: 'numeric fidelity',
        reason: '１番偉い의 뜻을 자연스럽게 옮기면서 전각 숫자 １을 유지했다.'
      },
      161: {
        after: '으음.\n용사도를 수련하는 사람으로서는\n제국병을 몰아내고 싶은데',
        category: 'proper nouns',
        reason: '勇者道의 승인 표기인 용사도를 적용했다.'
      },
      165: {
        after: '그렇다면……\n저보다 한참 어린 남동생일지도 모르겠군요',
        category: 'natural Korean',
        reason: '下の方の弟를 아래쪽 동생으로 직역한 부자연스러운 표현을 관계에 맞게 다듬었다.'
      },
      181: {
        after: '성전 메리디아스가 누군가에게\n변조되어 있다는 사실을',
        category: 'proper nouns',
        reason: '聖典メリディアス의 승인 표기인 성전 메리디아스를 적용했다.'
      },
      186: {
        after: '대성당에 １명 홀로 서서\n몰려든 관중 앞에서――<$0C>정말이지\n꿈 같은 이야기 아니야?',
        category: 'numeric fidelity',
        reason: '원문의 １人에 포함된 전각 숫자 １을 보존했다.'
      }
    }
  },
  '0099': {
    changes: {
      29: {
        after: '씁쓸한 표정의 병사',
        category: 'natural Korean',
        reason: '苦い顔를 직역한 쓴 표정 대신 자연스러운 씁쓸한 표정으로 다듬었다.'
      },
      32: {
        after: '나라에서 배급하는\n식사는 이제 지긋지긋해……<$0C>맛도 없는데다\n양도 아주 적다고!?\n우리 집에는 한창 클 아이가 있는데……',
        category: 'natural Korean',
        reason: 'マズイだけじゃなくって의 연결을 맛도 없는데다로 고쳐 문장을 자연스럽게 했다.'
      },
      43: {
        after: '전쟁의 기운을 재빨리 감지하는 것도\n행상인의 훌륭한 스킬 중 하나.\n저도 아직 미숙하다는 뜻이죠',
        category: 'terminology',
        reason: '원문의 スキル을 프로젝트 용어인 스킬로 통일했다.'
      },
      51: {
        after: '우리가 지키고 있으면서도\n도적의 침입을 허용하다니……\n정말 한심한 일이다',
        category: 'meaning',
        reason: '私たちがついていながら가 경비 중이었음에도 침입을 허용했다는 뜻임을 명확히 했다.'
      },
      60: {
        after: '원로원의 결정 때문에\n우리 경비병은 더욱\n긴장해야 합니다<$0C>그나저나――\n재건도 아직 끝나지 않았는데\n같은 편이 우리에게 칼을 겨누다니……',
        category: 'meaning',
        reason: '身内に刃を向けられる의 피동 관계를 같은 편이 우리에게 칼을 겨눈다는 뜻으로 바로잡았다.'
      },
      76: {
        after: '다들 저마다 다른 기분으로\n이 층에 오시는군요<$0C>뭐, 저도 비슷함다.\n그런 기세로 왔거든요\n――오늘 아침에도',
        category: 'natural Korean',
        reason: '色んなノリ를 온갖 기세로 직역한 표현을 자연스럽게 다듬고 니콜의 말투를 유지했다.'
      },
      78: {
        after: '이 대포…… 좀 봐.\n빛나는 칠흑의 몸체……\n내 정비 솜씨의 결정체야<$0C>이런! 탄을 쏘겠다는\n멋없는 소리는 하지 마.\n더러워지잖아',
        category: 'meaning',
        reason: '無粋를 몰상식함이 아니라 멋없고 운치 없다는 의미로 바로잡았다.'
      },
      79: {
        after: '바다가 정말 아름다워……<$0C>아무것도 하지 않는 １일이 있어도\n난 괜찮다고 생각해.\n당신은 어때?',
        category: 'numeric fidelity',
        reason: '원문의 １日에 포함된 전각 숫자 １을 보존했다.'
      },
      81: {
        after: '여기 있는 의장이라는 사람은\n이 도시의 １인자래.\n한 번만이라도 만나 보고 싶어!',
        category: 'numeric fidelity',
        reason: '１番偉い의 뜻을 자연스럽게 옮기면서 전각 숫자 １을 유지했다.'
      },
      84: {
        after: '의욕 넘치는 여자아이',
        category: 'natural Korean',
        reason: '気合十分을 기합이 충분하다고 직역한 표현을 자연스럽게 고쳤다.'
      },
      90: {
        after: '선택지는 싫어.\n고를 수 있는 미래가 정해져 있을 리 없잖아<$0C>둘 중 하나라면 세 번째 답을\n내 손으로 쟁취하겠어!',
        category: 'numeric fidelity',
        reason: '원문 第三을 번역하며 새로 생긴 전각 숫자 ３을 한글 표현으로 바로잡았다.'
      },
      115: {
        after: '순순히 포기해라!',
        category: 'natural Korean',
        reason: '観念するんだな를 관념해라로 직역한 표현을 자연스러운 위협 대사로 고쳤다.'
      },
      123: {
        after: '어머니를 구하려고 금기였던 이\n성전 메리디아스의 봉인을 풀고\n이사신과 계약을 맺으려 했다',
        category: 'proper nouns',
        reason: '聖典メリディアス의 승인 표기인 성전 메리디아스를 적용했다.'
      },
      138: {
        after: '여기는 펠리스.\n사막에 둘러싸인 불볕더위의 마을이다<$0C>지금은 우리 메리디아군이\n평화롭게 통치하고 있다',
        category: 'natural Korean',
        reason: '灼熱の村를 작열하는 마을로 직역한 표현을 자연스럽게 다듬었다.'
      },
      163: {
        after: '사우스 노와레교에 있어\n노와레교는 아버지 같은 존재입니다.\n이 여관에는 친근감을 느낍니다',
        category: 'particles',
        reason: 'サウスノワーレ教にとって의 관점을 자연스러운 조사와 서술로 표현했다.'
      },
      183: {
        after: '제국의 사신에게 의지하는 건 분하지만\n여기서는 디바를 믿고\n구원 부대를 보내고 싶다',
        category: 'meaning',
        reason: '癪だ를 단순히 싫다는 뜻이 아니라 분하고 못마땅하다는 뉘앙스로 바로잡았다.'
      },
      187: {
        after: '조금 긴장됩니다……\n공화국이 바트라키테스의 복수를 하러\n올지도 모르니까요……',
        category: 'meaning',
        reason: 'バトラキテスの報復가 바트라키테스를 위한 보복이라는 의미가 드러나도록 고쳤다.'
      },
      191: {
        after: '여기서 매일 일해 봐.\n지루함이야말로 １번 가는 지옥이야.\n아무 즐거움도 없으니까',
        category: 'numeric fidelity',
        reason: '원문의 １番에 포함된 전각 숫자 １을 보존했다.'
      },
      192: {
        after: '에블과 바트라키테스 사람들은\n원래 공화국의 영민<$0C>폭정에 시달리는 그들을\n구하려고 일어선다――\n언젠가 그날이 오겠지',
        category: 'meaning',
        reason: '圧政을 압정으로 옮긴 오타성 오역을 폭정으로 바로잡았다.'
      }
    }
  }
};

for (const [number, spec] of Object.entries(batches)) {
  const batchId = `batch_${number}`;
  const sourcePath = path.join(root, 'tm_v2', 'batches', 'source', `${batchId}.jsonl`);
  const draftPath = path.join(root, 'drafts', `${batchId}.jsonl`);
  const reviewedPath = path.join(root, 'reviewed', `${batchId}.jsonl`);
  const reviewPath = path.join(root, 'reviews', `${batchId}_review.json`);
  const sourceRows = fs.readFileSync(sourcePath, 'utf8').trim().split(/\r?\n/).map(JSON.parse);
  const draftRows = fs.readFileSync(draftPath, 'utf8').trim().split(/\r?\n/).map(JSON.parse);
  const reviewedRows = draftRows.map((row, index) => {
    const change = spec.changes[index];
    return change ? { ...row, translation_ko: change.after } : row;
  });
  const modifications = Object.entries(spec.changes).map(([indexText, change]) => {
    const index = Number(indexText);
    return {
      tm_id: sourceRows[index].tm_id,
      source_text: sourceRows[index].source_text,
      before: draftRows[index].translation_ko,
      after: change.after,
      category: change.category,
      reason: change.reason
    };
  });
  fs.writeFileSync(reviewedPath, reviewedRows.map(row => JSON.stringify(row)).join('\n') + '\n', 'utf8');
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
    source: sourcePath.replace(/\\/g, '/'),
    draft: draftPath.replace(/\\/g, '/'),
    reviewed_output: reviewedPath.replace(/\\/g, '/'),
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
      'line breaks'
    ],
    modifications,
    verification_execution: {
      status: 'deferred_by_user_instruction',
      executed_tools: [],
      not_executed: ['validator', 'fit', 'encoding', 'boundary_audit'],
      note: '사용자 지시에 따라 별도 validator, fit, encoding, boundary audit를 실행하지 않았다.'
    }
  };
  fs.writeFileSync(reviewPath, JSON.stringify(report, null, 2) + '\n', 'utf8');
}
