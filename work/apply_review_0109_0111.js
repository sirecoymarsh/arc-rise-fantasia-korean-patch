const fs = require('fs');
const path = require('path');

const reviewer = '/root/translate_batch_0009';
const draftAuthor = '/root/audit_boundary_integration';

const batches = {
  '0109': [
    {
      tm_id: 'ARF-TM-829591FD6B52AC0B7A33',
      after: '조금 전 성 안이\n어수선한 것 같던데\n――무슨 일이라도 있었을까?<$0C>여기는 성이니까\n도적이 침입했을 리는\n없었을 것 같긴 하지만……',
      category: 'character_voice',
      reason: '「かしら」의 여성 화자 어조를 살리고 뒤 문장을 자연스러운 추측 표현으로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-82D8B61F87A68A668183',
      after: '임무를 잊는 일은 없습니다.\n단 한순간도요',
      category: 'natural_korean',
      reason: '「片時たりとも」를 어색한 직역 대신 자연스러운 강조 표현으로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-82E2FB4D8FCA3EEBE53F',
      after: '라르크인가, 오랜만이군.\n나도 아버지의 이름에 부끄럽지 않은\n훌륭한 병사가 되려고 한다<$0C>방금 그걸 자무엘 님의\n무덤 앞에서 맹세한 참이다',
      category: 'natural_korean',
      reason: '「墓前」의 한자 직역 ‘묘전’을 일상적인 한국어 ‘무덤 앞’으로 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-834DE12CF89BEB59B6D1',
      after: '우리 디아만트 백성은\n소중한 사람을 잃었습니다……<$0C>여기 피어 있는 꽃을\n마하트 폐하의 영전에\n바치려 합니다……',
      category: 'meaning',
      reason: '실제 꽃을 바치는 「手向け」를 인조 꽃을 뜻할 수 있는 ‘조화’로 옮긴 오류를 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-83977D5D46072E876BB8',
      after: '공구 일체를\n들고 다니며 여행하는 건\n제법 고된 일이야<$0C>여기서 에블까지는\n거리가 상당히 머니까……',
      category: 'natural_korean',
      reason: '「工具用品を一式」와 「骨が折れる」를 자연스러운 한국어 표현으로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-83CEFFB75108D2BB1BDF',
      after: '딱히 남을 돕는 일은\n아닌 것 같다만……',
      category: 'grammar',
      reason: '조사와 서술부의 어색한 결합을 바로잡아 원문의 유보적 판단을 살렸다.',
    },
    {
      tm_id: 'ARF-TM-842957DDFB929C18D5A2',
      after: '알스 폐하……라.\n말하기도 듣기도 낯설군<$0C>나는 바이스 전하를\n제１의 의지처로 여겼는데……',
      category: 'natural_korean',
      reason: '원문의 전각 숫자 「１」을 유지하면서 어색한 ‘１순위로 의지하다’를 자연스러운 명사구로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-843D2366D5802E48F2F3',
      after: '겁먹은 붉은 머리\n병사를 봤는데\n분명 당했겠지',
      category: 'meaning',
      reason: '이미 목격한 병사의 이후 상황을 추측하는 문맥에 맞춰 진행형을 완료 추측으로 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-847283A447DCD3AFCFD7',
      after: '미안하지만 근무 중에는\n사담이 금지되어 있다<$0C>나도 경비에 집중하고 싶으니\n날 좀 내버려 두겠나?',
      category: 'grammar',
      reason: '「放っておいてくれないか」의 목적어와 요청 의미가 자연스럽게 드러나도록 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-8475F6E80BA03DED96E2',
      after: '진정해, 꼬마야.\n그럼 바다에 나가면\n디아만트로 향하자',
      category: 'function',
      reason: '「向かうぞ」의 동행 제안을 평서형이 아닌 자연스러운 청유형으로 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-84D79E1B72C0C3A6120E',
      after: '눈은 잔뜩 충혈돼 있고……\n역시 그 사람――무서워',
      category: 'formatting',
      reason: '원문에 없는 대시 뒤 공백을 제거해 문장부호 형식을 맞췄다.',
    },
    {
      tm_id: 'ARF-TM-8563A26FC04CF68FEA7D',
      after: '그래, 이게 그거야.\n문장은 정중한데 글씨는 엉망이야.\n그렇다고 아이가 쓴 것 같지도 않지만……',
      category: 'meaning',
      reason: '「文面」과 편지를 쓴 사람에 대한 추측을 각각 ‘문장’과 ‘아이가 쓴 것’으로 명확히 옮겼다.',
    },
    {
      tm_id: 'ARF-TM-8575133DC7016A657A38',
      after: '어느 날의 일이야.<$0C>일이 일단락되어\n배달 본부로 돌아갔을 때였어……<$0C>접수대 동료가 자리를 비웠다가\n돌아와 보니――<$0C>이 상자와 편지, 그리고\n의뢰 보수가\n카운터에 놓여 있었어',
      category: 'meaning',
      reason: '화자가 직접 겪은 일을 전하는 대사이므로 마지막의 잘못된 전언형을 직접 경험형으로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-8589A3B5B1C11170C75D',
      after: '특사님\n부디 이해해 주십시오<$0C>도시 주민과 의회의 바람은 하나.\n전쟁 없는 평화로운 세계.\n의장님도 그렇게 생각하십니다',
      category: 'natural_korean',
      reason: '「街の民」를 자연스러운 ‘도시 주민’으로 옮기고 중복된 조사 표현을 간결하게 다듬었다.',
    },
  ],
  '0110': [
    {
      tm_id: 'ARF-TM-85CC20E12D8C35FF00A4',
      after: '여전히 제국은\n전쟁에만 매달려 지내는데――\n이대로 괜찮은 걸까요?',
      category: 'natural_korean',
      reason: '「戦争に明け暮れる日々」의 중복 직역을 자연스러운 서술문으로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-8610E2543A60C2071982',
      after: '물론 이론 수업만 있는 게 아니야.\n혹독한 전투 훈련과 실습을 거듭해야\n비로소 １인분은 해낼 수 있어<$0C>입학해서 제대로 졸업할 수 있는 건\n전체의 １할이 고작이야',
      category: 'natural_korean',
      reason: '전각 숫자 「１」을 보존하면서 중복된 ‘１인분 몫’을 자연스러운 구어 표현으로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-86262976EED03569B36F',
      after: '이건 정말\n돈 계산할 생각에 손이 근질근질해서――<$0C>도무지 진정되지 않는\n이야기군요',
      category: 'idiom',
      reason: '「腕が鳴る」를 능력을 발휘하고 싶어 근질거린다는 관용 의미로 자연스럽게 옮겼다.',
    },
    {
      tm_id: 'ARF-TM-8633EDADE31013040E05',
      after: '여기 늘어선 상장을 보셨습니까?\n이야, 훌륭한 공적이군요<$0C>듣자 하니 알스 황자도\n이곳 문하생 １명이라더군요.\n점점 더 흥미가 생기는군요',
      category: 'natural_korean',
      reason: '「興味が尽きない」의 뜻을 어색한 ‘흥미가 끝이 없다’ 대신 자연스러운 감탄으로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-86C15B61EF813E86D951',
      after: '아, 나른해.\n몸이 늘어져 죽을 것 같아……<$0C>왜 엘리트인 내가\n이런 변방 경비를 하는 거지?',
      category: 'meaning',
      reason: '「だるい」를 단순히 귀찮다는 뜻이 아니라 몸이 나른하고 늘어지는 상태로 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-86C778F47C2CC07B24F5',
      after: '오늘은 바다까지\n엄마와 함께 산책하는 날이야.\n빨리 바다에 가고 싶어〜',
      category: 'character_voice',
      reason: '아이의 구어체에 맞지 않는 평서형 종결을 자연스러운 반말로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-8779C65C3C6067EA88CA',
      after: '기운 내……<$0C>제국 사람들에게\n우리의 불굴의 의지를\n보여 주자고요!',
      category: 'function',
      reason: '「見せつけてやりましょうよ」의 격려와 권유를 어색한 의문형이 아닌 힘 있는 청유형으로 옮겼다.',
    },
    {
      tm_id: 'ARF-TM-879DE33F30BB42963E85',
      after: '메리디아 제국이\n이 이상 전쟁의 불길을 넓히는 건\n이제 무리가 아닐까<$0C>여기서 보면\n병사들이 지친 게 분명해.\n나라 재정도 매우 빠듯하다더군',
      category: 'idiom',
      reason: '재정난을 뜻하는 「火の車」를 실제 화재로 오해할 수 있는 표현 대신 의미에 맞게 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-87B2D92DF02EF1A05990',
      after: '우리는 알스 황제를 믿는다<$0C>폭정에 관한 소문이 사실이라 해도\n그럴 수밖에 없는\n사정이 분명 있을 것이다',
      category: 'natural_korean',
      reason: '「悪政」의 어색한 한자 직역 ‘악정’을 문맥에 맞는 ‘폭정’으로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-87DD33FDD05D64DBD14B',
      after: '……이거 참.\n골치 아픈 일이 됐군',
      category: 'natural_korean',
      reason: '「やれやれ」를 한국어에서 자연스러운 난감함의 감탄사로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-88050DA13CE87C684CB3',
      after: '소피아의 양장점에 어서 오세요.\n멋내기는 여행의 기본 중 기본!\n꼭 구경하고 가 주세요',
      category: 'grammar',
      reason: '도착점 조사가 문장 끝에 남은 어색한 도치문을 자연스러운 환영 인사로 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-88084AB155CBC8C6D375',
      after: '이 여관은 무척 편안해.\n제도의 요란한 번잡함과는\n완전히 동떨어진 고요함이 있으니 말일세',
      category: 'natural_korean',
      reason: '「全く無縁」의 직역투를 자연스럽게 풀고 노년 화자의 어조를 살렸다.',
    },
    {
      tm_id: 'ARF-TM-88BE069D8CCA578F5517',
      after: '여기 있으면\n하늘에 떠 있는 비광정을\n매일 볼 수 있다니까?',
      category: 'character_voice',
      reason: '자랑하듯 알려 주는 「見れるんだぜ？」를 단순 확인 질문이 아닌 구어적 강조로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-898B4FF01EB50744D95E',
      after: '자네, 꽤\n피곤해 보이는 얼굴이군<$0C>그럴 때는 한 모금이면 기운이 완전 회복!\n도시 노동자의 필수품을\n선물해 주지!',
      category: 'terminology',
      reason: '「マストアイテム」를 프로젝트의 자연스러운 번역 원칙에 맞춰 ‘필수품’으로 통일했다.',
    },
    {
      tm_id: 'ARF-TM-898CE41D27C2A27FBAC5',
      after: '자, 그럼\n우리도 좀 쉬자고',
      category: 'natural_korean',
      reason: '일본어 장음 기호가 남은 감탄사를 자연스러운 한국어 전환 표현으로 고쳤다.',
    },
  ],
  '0111': [
    {
      tm_id: 'ARF-TM-89D887FBC4CD1E9DFD95',
      after: '연애<$15>00\n일<$15>00\n양동<$15>00<$0C>모두가 질색할 만한 １일입니다.\n옛날엔 나도 좀 놀았다――는 이야기는 금지\n돌이킬 수 없게 됩니다<$0C>행운을 부르는 물건은 여행기입니다.\n가 본 적 없는 땅에\n마음을 두는 정도로만 합시다',
      category: 'numeric_fidelity',
      reason: '원문의 전각 숫자 「１」을 번역문에 복원했다.',
    },
    {
      tm_id: 'ARF-TM-89DEE13F8149234283BA',
      after: '투기장도 카지노도\n보고 있자니 질려 버렸어.\n어째서 어른들은 질리지 않는 거야?<$0C>투기장이나 카지노보다\n밖에서 친구들과 노는 게\n１등으로 즐거워',
      category: 'numeric_fidelity',
      reason: '「１番」의 전각 숫자 「１」을 유지하면서 아이의 말투에 맞게 옮겼다.',
    },
    {
      tm_id: 'ARF-TM-89E9868E6CAE7AC56825',
      after: '오팔루스를 구해 주신\n알스 폐하께서 저토록\n불합리한 법을 만드시다니――<$0C>이건 무언가 오해임이 틀림없어',
      category: 'grammar',
      reason: '‘오해가 틀림없다’의 잘못된 조사 결합을 ‘오해임이 틀림없다’로 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-8A00DDE01F57A8A4839C',
      after: '여행 중이신 일행인가요?\n괜찮으시다면 저희 여관\n『푸른 하늘 무지개다리 여관』을 이용해 주세요',
      category: 'proper_noun',
      reason: '다른 검수본에서 확립된 「青空の虹橋亭」의 표기 ‘푸른 하늘 무지개다리 여관’으로 통일했다.',
    },
    {
      tm_id: 'ARF-TM-8A73F67E02FB0E73F577',
      after: '엄마한테 말했어.\n『나는 테너 가수가 될 거야』라고<$0C>역시 소프라노보다\n테너로 노래하고 싶으니까……',
      category: 'grammar',
      reason: '성부를 목적어로 ‘부르다’라고 한 어색한 표현을 ‘테너로 노래하다’로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-8AEF2666A0CAA00F7EF9',
      after: '제국군 VS 방어 스크린\n엘리엇 중장에게 보고　　\n돌아간다　　　　　　　　　',
      category: 'formatting',
      reason: '문체 가이드에 따라 전각 영문 「ＶＳ」를 반각 ASCII ‘VS’로 정규화했다.',
    },
    {
      tm_id: 'ARF-TM-8AFA34AC808F6D0CDC09',
      after: '어쨌든 옛날이야기야.\n지금은 항구에서 온종일 멍하니\n지난날에 잠기는 게 고작이지……',
      category: 'natural_korean',
      reason: '「過去に浸る」를 직역투 ‘과거에 잠기다’ 대신 자연스러운 회상 표현으로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-8B32BB94F422D8849418',
      after: '거기 있는 젊은이가 아까부터\n시끄럽게 떠들고 있는데\n네가 좀 한마디 해 줘',
      category: 'natural_korean',
      reason: '「注意しといてくれ」를 어색한 ‘주의를 주다’ 대신 자연스러운 구어 표현으로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-8B47C70C78432A6445E5',
      after: '여기에 있으면 언제나 이\n묘한 감각에 시달리게 돼',
      category: 'meaning',
      reason: '「つきまとわれる」의 계속 따라붙어 괴롭히는 뉘앙스를 자연스럽게 복원했다.',
    },
    {
      tm_id: 'ARF-TM-8B5594E1DFCDB2A41269',
      after: '이 나라는 어떻게 되는 걸까요……<$0C>행방불명이었던\n그린힐 의장이 돌아왔나 했더니\n터무니없는 결의를 강요하고 있습니다<$0C>성황 호제아에게 국가 반역죄 적용――\n이는 국교인 노스 노와레교를\n부정하는 것과 다름없는 어리석은 정책입니다',
      category: 'natural_korean',
      reason: '첫 문장의 어색한 직역을 자연스러운 우려로 고치고 「愚策」를 문맥에 맞는 정책 표현으로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-8B747577333188C6259B',
      after: '뭐야? 그 반항적인 눈빛은?\n우리 지금 잔뜩 날이 서 있으니\n몸 성하려면 자극하지 않는 게 좋을걸',
      category: 'idiom',
      reason: '「身のため」를 어색한 ‘신상에 좋다’가 아닌 위협 상황에 자연스러운 관용 표현으로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-8B818620E67851CCA288',
      after: '권세에 취한 형님과\n나라에 칼을 겨눈 아우님――<$0C>마하트 폐하께서는 어떤 심정으로\n다투고 시기하는 ２명의 아들을\n바라보셨을까……',
      category: 'numeric_fidelity',
      reason: '원문의 전각 숫자 「２」를 번역문에 복원했다.',
    },
    {
      tm_id: 'ARF-TM-8BAE693F46E54FCD9A09',
      after: '장사의 비결 제１칙.\n『공짜보다 비싼 것은 없다』<$0C>공공 급수장에\n사용료를 매겨 봤습니다.\n솔직히 떼돈을 벌고 있죠',
      category: 'numeric_fidelity',
      reason: '순번의 뜻을 유지하면서 원문의 전각 숫자 「１」을 번역문에 복원했다.',
    },
    {
      tm_id: 'ARF-TM-8BB3AB364B36D501C527',
      after: '부럽구나, 라르크.\n황제 폐하의 친구라면\n너도 덕 좀 보지 않았나?',
      category: 'idiom',
      reason: '이득을 보았다는 「いい目を見る」를 부정적 뉘앙스의 ‘좋은 꼴’이 아닌 ‘덕을 보다’로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-8BC63A73C6F133C7E9C8',
      after: '또 세계 정세가\n불안정해지고 있다……<$0C>전쟁, 평화, 종교, 인종――\n우리 인간은 너무나도\n어리석은 존재인지도 모르겠군<$0C>이제 너희 젊은이들에게 맡기마.\n노병은 죽지 않고, 다만 사라질 뿐이지',
      category: 'natural_korean',
      reason: '사람을 가리키는 「生き物」를 어색한 ‘생물’ 대신 문맥에 맞는 ‘존재’로 다듬었다.',
    },
    {
      tm_id: 'ARF-TM-8C25F02B73CA32174CE1',
      after: '자다는 꽤 좋은 곳이지\n잘 정리된 구획 같은 건\n정말 마음에 들어<$0C>뭐, 난 내 방을 아주 좋아해서\n바깥 거리에는 그다지\n나가지 않기도 하지만……',
      category: 'natural_korean',
      reason: '긍정적 의미의 「たまらない」를 어색한 ‘참을 수 없이 좋다’ 대신 자연스러운 호감 표현으로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-8C720514BF0D9979B12C',
      after: '오프닝 １　　　\n오프닝 ２　　　\n엔딩　　　　　　\n오르키나 습격　　　　\n비광정 발진　　　　　\n비광정 VS 마슈가르\n오팔루스 배리어　　\n제국 기함의 최후　　　\n니콜 특공　　　　　\n적월 부상　　　　　　\n창월 부상　　　　　　\n스태프 롤　　　　　\nMMV 새 로고　　　　\n돌아간다　　　　　　　',
      category: 'formatting',
      reason: '문체 가이드에 따라 전각 영문 「ＶＳ」와 「ＭＭＶ」를 반각 ASCII로 정규화하고 숫자는 유지했다.',
    },
    {
      tm_id: 'ARF-TM-8C96731E4293DAEC4499',
      after: '어쨌든\n우선 그린힐 의장의\n안위 확인이 최우선이다',
      category: 'meaning',
      reason: '생사와 안전을 함께 뜻하는 「安否」를 단순 ‘안전’보다 정확한 ‘안위’로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-8CA869EB0CA769B00F5B',
      after: '오늘은 정말 멋진 꽃을\n들여올 수 있었어<$0C>이런 날에는 틀림없이\n좋은 일이 생길 거야……\n１일이 기대되네',
      category: 'numeric_fidelity',
      reason: '원문의 전각 숫자 「１」을 번역문에 복원했다.',
    },
    {
      tm_id: 'ARF-TM-8CAD820ADC3920C54E92',
      after: '２명 다 힘내〜\n끝나면 오빠랑\n간식 먹자!',
      category: 'numeric_fidelity',
      reason: '원문의 전각 숫자 「２」를 번역문에 복원했다.',
    },
    {
      tm_id: 'ARF-TM-8CFDF1FA9CBAB9F639D8',
      after: '그 바이스 전하께서\n이토록 허무하게 쓰러지시다니……\n――세상은 헤아릴 수 없는 일투성이로군<$0C>게다가 알스 신황제는\n오르키나교로 타락했다고 한다.\n……메리디아 제국은 어떻게 되는 거지?',
      category: 'meaning',
      reason: '비하와 경멸이 담긴 「身を落とす」를 중립적인 ‘몸을 담다’가 아니라 ‘타락하다’로 복원했다.',
    },
    {
      tm_id: 'ARF-TM-8D1D01BE117A5671FC5A',
      after: '조사해 보는 게――',
      category: 'grammar',
      reason: '뒤에서 말이 끊기는 문장에 자연스럽도록 의존 명사 구성을 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-8D2D0EC59416AE45F59D',
      after: '내가 아직 신병이던 시절에는\n황제 폐하께서 탑 발코니에서\n귀한 말씀을 내려 주시곤 했지<$0C>광장에…… 그래\n１００명이나 되는 병사가 모였던가.\n전하들께서도 아직 어리셨지――',
      category: 'meaning',
      reason: '「ありがたいお言葉」를 화자가 감사한다는 뜻이 아니라 은혜롭고 귀한 말씀이라는 의미로 바로잡았다.',
    },
    {
      tm_id: 'ARF-TM-8D50951C7A72C2ADD5AD',
      after: '신제국 헌장의 소문은\n이런 북쪽 지방까지 들려오고 있어<$0C>이야기를 들어 보면 믿을 수가 없어.\n자유를 중시하는 알스 님께서\n그런 법을 만드시다니――',
      category: 'natural_korean',
      reason: '「北国」를 별개의 나라로 오해할 수 있는 ‘북쪽 나라’ 대신 북방 지방이라는 뜻으로 고쳤다.',
    },
    {
      tm_id: 'ARF-TM-8D899FC56EE56DB50526',
      after: '무역상인인 남편에게\n들은 이야기인데――<$0C>오르키나 방면으로 가는 배가\n전 노선 멈췄대요.\n……왜 그런지 알아요?',
      category: 'grammar',
      reason: '직업 명사와 가족 관계 명사의 수식 관계가 드러나도록 서술격 조사를 보완했다.',
    },
    {
      tm_id: 'ARF-TM-8D934A6833FC8FC71224',
      after: '바이스 전하와 알스 전하\n２분이 손을 맞잡고\n이 제국을 지탱해 주신다면……<$0C>우리나라는 풀헤임의\n패자가 될 수도 있을 텐데',
      category: 'numeric_fidelity',
      reason: '원문의 전각 숫자 「２」를 번역문에 복원했다.',
    },
    {
      tm_id: 'ARF-TM-8DABFFE71F7D2BFC878B',
      after: '외출 금지 포고는\n아무리 그래도 너무 심하지 않나 하고\n처음에는 생각했지만……<$0C>곰곰이 생각해 보니\n운영이나 관리 측면에서는\n굉장히 효율적이지 않아?',
      category: 'grammar',
      reason: '인용절 뒤에 빠진 ‘하고’를 보완해 첫 문단의 문장 구조를 자연스럽게 고쳤다.',
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
