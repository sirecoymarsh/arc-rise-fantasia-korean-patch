const fs = require('fs');
const crypto = require('crypto');

const path = 'work/runtime_fix/main_dol_translations.jsonl';
const changeLogPath = 'work/runtime_fix/main_dol_crossreview_changes.json';

// Independent Codex-only cross-review corrections. Keys are immutable DOL
// source offsets, so no source/raw/capacity identity field can be changed.
const corrections = new Map(Object.entries({
  '0x003C8A79': ['광소무효', 'locked term: 光召術 is 광소술; compact form required by 8-byte capacity'],

  '0x003C8C4A': [': 공격', 'particle-neutral battle-log fragment'],
  '0x003C8C51': [': 엑셀 액트', 'particle-neutral battle-log fragment'],
  '0x003C8C62': [': 광소술', 'particle-neutral battle-log fragment'],
  '0x003C8C76': [': 방어', 'particle-neutral battle-log fragment'],
  '0x003C8C7D': [': 훔침', 'particle-neutral battle-log fragment'],
  '0x003C8C91': [': 격파', 'particle-neutral battle-log fragment'],
  '0x003C8CA7': [': 치명타', 'locked battle term: クリティカル is 치명타'],
  '0x003C8CB6': [' 훔침 실패', 'natural spacing in battle-log fragment'],
  '0x003C8CC1': [': 아이템 없음', 'remove unsafe topic-particle allomorph after a runtime name'],
  '0x003C8CDA': [': 파괴', 'particle-neutral battle-log fragment'],
  '0x003C8CE1': [': 훔쳤으나 소지 불가', 'remove unsafe object particle and retain inventory-full meaning'],
  '0x003C8D71': ['신중 훔침', 'distinguish 盗む from the separate 強奪 skill'],
  '0x003C8E14': ['상태변화 흡수+', 'restore readable spacing within the 14-byte capacity'],
  '0x003CB73E': ['용병 지침 『%s』에 항목 추가', 'restore omitted 傭兵 meaning within the exact capacity'],

  '0x003CF451': ['원로원사절', '使者 means envoy; avoid the lion homograph 사자'],
  '0x003CF46F': ['노스 노와레교도', 'locked religion name: 노스 노와레교'],
  '0x003CF6CD': ['누구에게 씁니까?', 'restore omitted use action in the target prompt'],
  '0x003CF6DE': ['전체에 씁니다', 'restore omitted use action in the target prompt'],
  '0x003CF73D': ['%s 1개를 구매합니다.\n구매할까요?', 'remove unsafe 을/를 allomorph after runtime item name'],
  '0x003CF79B': ['%s 1개를 판매합니다.\n판매할까요?', 'remove unsafe 을/를 allomorph after runtime item name'],
  '0x003CF7C0': ['%s의 케이지에\n%s 작업을 합니다.\n계속할까요?', 'remove unsafe 을/를 allomorph after runtime operation name'],
  '0x003CF85B': ['%s 구매를 진행합니다.\n계속할까요?', 'remove unsafe 을/를 allomorph after runtime item name'],
  '0x003CFAD3': ['코인 %d개로\n%s 교환\n계속하시겠습니까?', 'remove unsafe 을/를 allomorph after runtime prize name'],
  '0x003CFB5C': ['%s행 이동\n계속할까요?', 'remove unsafe 로/으로 allomorph after runtime destination name'],
  '0x003CFF25': ['%s 대신 넣을 멤버를\n선택해 주세요', 'remove unsafe 와/과 allomorph after runtime member name'],

  '0x003D036E': ['복합 속성 『%s』\n발생!', 'locked compound spacing'],
  '0x003D038C': ['복합 속성 『%s』・『%s』\n발생!', 'locked compound spacing'],
  '0x003D077C': ['시크릿 피스 해방: 『%s』\n완료되었습니다\n\n효과\n%s', 'remove unsafe 이/가 allomorph after runtime piece name'],
  '0x003D0C7C': ['96 부족합니다', 'particle-neutral text after a runtime control/icon token'],
  '0x003D0F2B': ['불 속성 광소술 성능 1단계 강화', 'locked elemental term: 불 속성'],
  '0x003D0F50': ['물 속성 광소술 성능 1단계 강화', 'locked elemental term: 물 속성'],
  '0x003D0F75': ['바람 속성 광소술 성능 1단계 강화', 'locked elemental term: 바람 속성'],
  '0x003D0F9A': ['땅 속성 광소술 성능 1단계 강화', 'locked elemental term: 땅 속성'],
  '0x003D11F0': ['켬', 'pair ON/OFF consistently as 켬/끔'],

  '0x003D18B5': ['아쉽네요! 노 페어', 'match the casino attendant/system polite register'],
  '0x003D1C25': ['달그림자 여관 목록 표시', 'locked place term: 月影の宿 is 달그림자 여관'],
  '0x003D1C7A': ['『뒤로』로 목록으로 돌아갑니다', 'correct destination particle while staying within capacity'],
  '0x003D1CA4': ['재개', 'ポーズ解除 is resume, not an abstract stop release'],
  '0x003D1EBF': ['수도 카르분클루스', 'locked place spelling: カルブンクルス is 카르분클루스'],
  '0x003D1F2B': ['오팔루스', 'locked place spelling'],

  '0x003D51AF': ['승리했습니다', 'natural result message'],
  '0x003D51C0': ['패배했습니다', 'natural result message'],

  '0x003E7F78': ['제도 디아만트', 'restore natural place-name spacing'],
  '0x003E7FC4': ['교도 안트락스', 'restore natural place-name spacing'],
  '0x003E8010': ['교도 안트락스', 'restore natural place-name spacing'],
  '0x003E805C': ['코핀 숨은 마을', 'restore natural place-name spacing'],
  '0x003E80A8': ['코핀 마을', 'restore natural place-name spacing'],
  '0x003E80F4': ['수도 카르분클루스', 'locked spelling and natural spacing'],
  '0x003E8140': ['성도 베네트나슈', 'restore natural place-name spacing'],
  '0x003E8224': ['오팔루스', 'locked place spelling'],
  '0x003E82BC': ['레테아 숲', 'locked place spelling and spacing'],
  '0x003E8308': ['레테아 숲', 'locked place spelling and spacing'],
  '0x003E8354': ['만델로 해안', 'locked place spacing'],
  '0x003E8438': ['에블 유적', 'locked place spacing'],
  '0x003E8484': ['그라 자혜교회 터', 'locked place spacing'],
  '0x003E851C': ['천충탑 자이페르트', 'locked place spacing'],
  '0x003E8568': ['폐도 힐베르트', 'locked place spacing'],
  '0x003E85B4': ['엘고드 화산', 'locked place spacing'],
  '0x003E8600': ['솔리톤 종유동', 'locked place spacing'],
  '0x003E864C': ['레졸벤트 대빙벽', 'locked place spacing'],
  '0x003E8698': ['공중 회랑 라스카다', 'locked place spacing'],
  '0x003E8730': ['성지 노와레', 'locked place spacing'],
  '0x003E877C': ['기하 회랑 알비스', 'locked place spacing'],
  '0x003E8B0C': ['해명의 길', 'locked place spelling'],
  '0x003E8B58': ['기함 파르세발', 'locked place spacing'],
  '0x003E8CD4': ['토파지온 여관 로비', 'natural compound spacing'],
  '0x003E8D20': ['자다 제국군 초소', 'natural compound spacing'],
  '0x003E8D6C': ['자무엘 무예관: 1F', 'locked facility name and spacing'],
  '0x003E8DB8': ['자무엘 무예관: 2F', 'locked facility name and spacing'],
  '0x003E8E04': ['자무엘 무예관: 별관', 'locked facility name and spacing'],
  '0x003E8E50': ['베네트나슈 밤', 'natural state suffix spacing'],
  '0x003E9018': ['리피아(린다)의 집', 'natural possessive spacing'],
  '0x003E90B0': ['바트라키테스: 회의실', 'natural colon spacing'],
  '0x003E9148': ['오팔루스: 사령관실', 'locked place spelling and natural colon spacing'],
  '0x003E91E0': ['도적선: 선실', 'natural colon spacing'],
  '0x003E922C': ['백월: 회의실', 'natural colon spacing'],
  '0x003E9278': ['백월: 통신실', 'natural colon spacing'],
  '0x003E9310': ['노와레 오두막 안', 'natural compound spacing'],

  '0x003F072A': ['코핀 큰 나무', '大樹 means a great tree; avoid opaque 대수'],
  '0x003F0742': ['코핀 돌무대', 'natural compound spacing'],
  '0x003F0801': ['\r굽잇길', 'correct Korean 사이시옷 spelling'],
  '0x003F08AA': ['한적한 거리', 'natural spacing'],
  '0x003F08DA': ['예술로', '芸術街 means an arts street; 예술가 means artist'],
  '0x003F090A': ['오락로', '娯楽街 means an entertainment street'],
  '0x003F0922': ['가극장길', 'retain 歌劇場 (opera house) within the hard capacity'],
  '0x003F096A': ['열사 마을', 'natural rendering of 熱砂の集落'],
  '0x003F0B19': ['0극채색 미궁', 'natural compound spacing'],
  '0x003F0CB1': ['A메아리 암로', 'natural compound spacing within hard capacity'],
  '0x003F0CC9': ['B침묵 놀이터', 'natural compound spacing'],
  '0x003F0CF9': ['D지하 저장고', 'natural compound spacing'],
  '0x003F0DD1': ['O엘리베이터 홀', 'restore the full エレベータ meaning within capacity'],
  '0x003F0DE9': ['P콘솔 플로어', 'natural loanword spacing'],
  '0x003F0E01': ['Q라운드 플로어 01', 'natural loanword/number spacing'],
  '0x003F0E1A': ['라운드 플로어 02', 'natural loanword/number spacing'],
  '0x003F0E32': ['라운드 플로어 03', 'natural loanword/number spacing'],
  '0x003F0E4A': ['라운드 플로어 04', 'natural loanword/number spacing'],
  '0x003F0E62': ['라운드 플로어 05', 'natural loanword/number spacing'],
  '0x003F0E7A': ['라운드 플로어 06', 'natural loanword/number spacing'],
  '0x003F0E92': ['라운드 플로어 07', 'natural loanword/number spacing'],
  '0x003F0EAA': ['라운드 플로어 08', 'natural loanword/number spacing'],
  '0x003F0EC2': ['라운드 플로어 09', 'natural loanword/number spacing'],
  '0x003F0EDA': ['라운드 플로어 10', 'natural loanword/number spacing'],
  '0x003F0EF1': ['R헤븐즈 래더', 'natural loanword spacing'],
  '0x003F0F21': ['T헤븐즈 래더', 'natural loanword spacing'],
  '0x003F0F69': ['W용암가장자리', 'ほとり means edge/bank; 용암가 is unnatural'],
  '0x003F10A1': ['j귀인로', '貴人街 means a street/district, not a person suffix'],
  '0x003F1221': ['|의회앞', '議場 means assembly hall; avoid chairman homograph 의장'],
  '0x003F1239': ['}의회입구', '議場 means assembly hall; avoid chairman homograph 의장'],
  '0x003F1342': ['섭리의방', 'locked world term: 定理 is 섭리'],
  '0x003F138A': ['섭리의방', 'locked world term: 定理 is 섭리'],
  '0x003F13A1': ['질서회랑', 'contextual correction: anomalous 柅緒 label is paired against 混沌'],
  '0x003F1762': ['대성당 앞길', 'natural place-name spacing'],
  '0x003F17F2': ['돌길과 눈사람 길', 'natural place-name spacing'],
  '0x003F180A': ['배움터', 'locked TM rendering of 学び舎'],
  '0x003F1822': ['깨어난 자들의 방', 'natural place-name spacing'],
  '0x003F186A': ['토파지온 여관 로비', 'natural compound spacing'],
  '0x003F1882': ['자다 제국군 초소', 'natural compound spacing'],
  '0x003F189A': ['자무엘 무예관: 1F', 'locked facility name and spacing'],
  '0x003F18B2': ['자무엘 무예관: 2F', 'locked facility name and spacing'],
  '0x003F18CA': ['자무엘 무예관: 별관', 'locked facility name and spacing'],
  '0x003F18E2': ['베네트나슈 밤', 'natural state suffix spacing'],
  '0x003F18FA': ['용박탑 이벤트 비공정', 'distinguish 飛空艇/挺 from locked 飛光艇=비광정'],
  '0x003F1912': ['루훙가용 이벤트', 'locked character/logres spelling: ルフンガ is 루훙가'],
  '0x003F1972': ['리피아(린다)의 집', 'natural possessive spacing'],
  '0x003F19A2': ['바트라키테스: 회의실', 'natural colon spacing'],
  '0x003F19D2': ['오팔루스: 사령관실', 'locked place spelling and natural colon spacing'],
  '0x003F19EA': ['PC용 비공정 함교', 'distinguish 飛空艇 from locked 飛光艇=비광정'],
  '0x003F1A02': ['도적선: 선실', 'natural colon spacing'],
  '0x003F1A1A': ['백월: 회의실', 'natural colon spacing'],
  '0x003F1A32': ['백월: 통신실', 'natural colon spacing'],
  '0x003F1A4A': ['백월: 심마프 회상용', 'natural colon/compound spacing'],
  '0x003F1A62': ['노와레 오두막 안', 'natural compound spacing'],
  '0x003F1A7A': ['자다 전장', 'natural Korean for バトルフィール'],
  '0x003F1A92': ['신룡 전장', 'natural Korean for バトルフィールド'],
  '0x003F1AAA': ['백월 거주구00 세피아', 'natural compound spacing'],
  '0x003F1AC2': ['바트라 광장 B 이벤트', 'natural compound spacing'],
  '0x003F1ADA': ['오리엔스 이벤트', 'natural compound spacing'],
  '0x003F1B0A': ['이벤트 영상용 29B', 'natural compound/number spacing'],
  '0x003F1B22': ['이벤트 영상용 30B', 'natural compound/number spacing'],
  '0x003F1D1A': ['열린 땅', 'natural place-name spacing'],
  '0x003F1D32': ['잊힌 땅', 'natural place-name spacing'],
  '0x003F1D4A': ['달아오른 땅', 'natural place-name spacing'],
  '0x003F1D62': ['감싸인 땅', 'natural place-name spacing'],
  '0x003F1D7A': ['열린 땅', 'natural place-name spacing'],
  '0x003F1DAA': ['닫힌 땅', 'natural place-name spacing'],
  '0x003F1DD9': ['\n기하 회랑 알비스', 'locked place spacing'],
}));

function est(s) {
  let n = 0;
  for (const ch of s) n += ch.codePointAt(0) <= 0x7f ? 1 : 2;
  return n;
}

function printfTokens(s) {
  return s.match(/%(?:[-+ #0]*\d*(?:\.\d+)?[hlLzjt]*[diuoxXfFeEgGaAcspn%])/g) || [];
}

function sha256(data) {
  return crypto.createHash('sha256').update(data).digest('hex').toUpperCase();
}

const beforeBytes = fs.readFileSync(path);
const rows = beforeBytes.toString('utf8').trim().split(/\r?\n/).map(JSON.parse);
const byOffset = new Map(rows.map((r, i) => [r.offset_hex, { r, i }]));
const changes = [];

for (const [offsetHex, [target, reason]] of corrections) {
  const found = byOffset.get(offsetHex);
  if (!found) throw new Error(`missing correction target ${offsetHex}`);
  const { r } = found;
  const old = r.translation_ko;
  if (old === target) continue;
  const targetBytes = est(target);
  if (targetBytes > r.capacity_to_nul) {
    throw new Error(`${offsetHex}: ${targetBytes} > capacity ${r.capacity_to_nul}: ${JSON.stringify(target)}`);
  }
  const oldTokens = printfTokens(r.source_text);
  const newTokens = printfTokens(target);
  if (JSON.stringify(oldTokens) !== JSON.stringify(newTokens)) {
    throw new Error(`${offsetHex}: printf tokens differ: ${JSON.stringify(oldTokens)} != ${JSON.stringify(newTokens)}`);
  }
  const oldNl = (r.source_text.match(/\n/g) || []).length;
  const newNl = (target.match(/\n/g) || []).length;
  if (oldNl !== newNl) throw new Error(`${offsetHex}: newline count differs ${oldNl} != ${newNl}`);
  r.translation_ko = target;
  r.estimated_target_bytes = targetBytes;
  changes.push({
    offset: r.offset,
    offset_hex: offsetHex,
    lane: r.lane,
    source_text: r.source_text,
    old_translation_ko: old,
    new_translation_ko: target,
    capacity_to_nul: r.capacity_to_nul,
    encoded_length_estimate: targetBytes,
    reason,
  });
}

const afterText = rows.map((r) => JSON.stringify(r)).join('\n') + '\n';
fs.writeFileSync(path, afterText, 'utf8');
const log = {
  schema: 'arf-main-dol-crossreview-change-log-v1',
  reviewer: 'independent Codex internal model',
  external_translation_used: false,
  reviewed_rows: rows.length,
  corrected_rows: changes.length,
  before_sha256: sha256(beforeBytes),
  after_sha256: sha256(Buffer.from(afterText, 'utf8')),
  changes,
};
fs.writeFileSync(changeLogPath, JSON.stringify(log, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({ corrected: changes.length, before_sha256: log.before_sha256, after_sha256: log.after_sha256 }, null, 2));
