const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', '..');
const probe = JSON.parse(fs.readFileSync(path.join(root, 'work/catalog/text_probe_10.json'), 'utf8'));
const candidates = probe.records.filter((r) => r.offset >= 0x003C64F7 && r.offset <= 0x003CFFFF);
const mainDolPath = path.join(root, 'work/disc_extracted/DATA/sys/main.dol');
const mainDol = fs.readFileSync(mainDolPath);
const crypto = require('crypto');
const mainDolSha256 = crypto.createHash('sha256').update(mainDol).digest('hex').toUpperCase();
const sourceByteMismatches = candidates.filter((r) =>
  mainDol.subarray(r.offset, r.offset + r.byte_length).toString('hex').toUpperCase() !== r.raw_hex.toUpperCase()
);

// This map is deliberately keyed by file offset: repeated Japanese fragments can
// have different runtime roles, and offsets are the stable patch identity.
const translations = new Map();
const add = (offset, translation_ko, context, lane) => {
  if (translations.has(offset)) throw new Error(`duplicate offset 0x${offset.toString(16)}`);
  translations.set(offset, { translation_ko, context, lane });
};

// Disc/runtime system prompts.
add(0x003C651C, 'ARC RISE FANTASIA 디스크를\n넣어 주세요.', '게임 디스크 삽입 요구 화면', 'title_system');
add(0x003C6550, '디스크를 읽을 수 없습니다.\nWii 본체 사용설명서를 확인해 주세요.', '게임 디스크 읽기 오류 화면', 'title_system');

// Battle status, parameter and result vocabulary actually emitted by the battle UI.
[
  [0x003C89F0, '석화'], [0x003C89F5, '맹독'], [0x003C89FA, '혼란'],
  [0x003C89FF, '침묵'], [0x003C8A04, '속박'], [0x003C8A0B, '마비'],
  [0x003C8A10, '질병'], [0x003C8A15, '수면'], [0x003C8A2E, '레벨'],
  [0x003C8A35, '적대심'], [0x003C8A3C, '최대 HP'], [0x003C8A45, '화내성'],
  [0x003C8A4C, '수내성'], [0x003C8A53, '풍내성'], [0x003C8A5A, '토내성'],
  [0x003C8A61, '신속'], [0x003C8A66, '재생'], [0x003C8A6B, '축복'],
  [0x003C8A70, '물리무효'], [0x003C8A79, '광술무효'], [0x003C8A82, '전부무효'],
  [0x003C8A8B, '피해 반사'], [0x003C8A98, '부유'], [0x003C8AA0, '%s 엄호'],
  [0x003C8AAB, '로그레스개방'],
].forEach(([o, t]) => add(o, t, '전투 상태·능력 표시', 'battle_status'));

[
  [0x003C8C4A, ' 공격'], [0x003C8C51, ' 엑셀 액트'], [0x003C8C62, ' 광소술'],
  [0x003C8C6B, '의 아이템'], [0x003C8C76, ' 방어'], [0x003C8C7D, ' 훔침'],
  [0x003C8C86, ' 전투 불능'], [0x003C8C91, ' 격파'], [0x003C8C98, ' 로그레스 개방'],
  [0x003C8CA7, ' 크리티컬'], [0x003C8CB6, ' 훔침실패'], [0x003C8CC1, '은 아이템이 없다'],
  [0x003C8CDA, ' 파괴'], [0x003C8CE1, '을 훔쳤지만 더 못 든다'],
].forEach(([o, t]) => add(o, t, '전투 결과 로그에 이름 뒤로 결합되는 문구', 'battle_log'));

[
  [0x003C8D48, '싱글 커넥트'], [0x003C8D59, '엑셀 액트 습득'],
  [0x003C8D6C, '강탈'], [0x003C8D71, '신중강탈'], [0x003C8D7C, '전력공격'],
  [0x003C8D85, '전력방어'], [0x003C8D8E, '파괴일격'], [0x003C8D99, '전력 충전'],
  [0x003C8DA6, '전력 변환'], [0x003C8DB1, '힘껏 응원'], [0x003C8DBE, '치유의 격려'],
  [0x003C8DCB, '심한욕설'], [0x003C8DD4, '전력 엄호'], [0x003C8DE3, '버티기'],
  [0x003C8DEA, '생명기적'], [0x003C8DF5, '흡수공격'], [0x003C8DFE, '상태변화흡수'],
  [0x003C8E0B, 'SP 흡수'], [0x003C8E14, '상태변화흡수+'], [0x003C8E23, '모두에게 강탈'],
  [0x003C8E32, '모두에게 흡수'], [0x003C8E41, '전력 DEF 비축'], [0x003C8E54, '철벽'],
  [0x003C8E59, '전력 RES 비축'], [0x003C8E6C, '연속공격'], [0x003C8E75, '협력공격'],
  [0x003C8E7E, '%s 엄호'], [0x003C8F1F, '가소술'], [0x003C8F26, '엑셀 액트'],
  [0x003C8F35, '플래시 드라이브'], [0x003C8F48, '트리니티 액트'],
  [0x003C8F59, '엑셀 트리니티'],
].forEach(([o, t]) => add(o, t, '전투 기술·연계 명칭', 'battle_action'));

add(0x003C905E, 'Wii 리모컨 연결이 끊겼습니다.', '컨트롤러 연결 끊김 안내', 'controller_prompt');
add(0x003C907E, 'Wii 리모컨에 눈차크 또는\n클래식 컨트롤러를 연결해 주세요.', '필수 확장 컨트롤러 연결 안내', 'controller_prompt');
add(0x003C92E8, '도주', '전투 도주 결과', 'battle_notice');
add(0x003C92ED, '도주 실패', '전투 도주 실패 결과', 'battle_notice');
add(0x003C92F8, '「전투 튜토리얼」을 보시겠습니까?', '전투 튜토리얼 확인', 'tutorial_prompt');
add(0x003C93B8, '행동하시겠습니까?', '전투 행동 확정', 'common_prompt');
add(0x003C93CD, '예', '긍정 선택지', 'common_choice');
add(0x003C93D2, '아니요', '부정 선택지', 'common_choice');
add(0x003C98A2, '세이브 포인트', '세이브 포인트 화면 제목', 'save_system');
add(0x003C9A05, '더는 못 드나……', '소지 한도 도달 시 짧은 알림', 'inventory_notice');

add(0x003C9E01, '사용할 컨트롤러를\n설정합니다.\n컨트롤러의 버튼을 누르면\n확정됩니다.', '최초 실행 컨트롤러 설정 안내', 'initial_setup');
add(0x003C9E59, '눈차크', '컨트롤러 종류', 'initial_setup');
add(0x003C9E64, '클래식 컨트롤러', '컨트롤러 종류', 'initial_setup');
add(0x003C9E7B, '게임큐브 컨트롤러', '컨트롤러 종류', 'initial_setup');
add(0x003C9E96, '%s을\n조작 컨트롤러로 설정했습니다.', '컨트롤러 설정 완료 안내', 'initial_setup');
add(0x003C9F5F, 'Wii 본체 저장 메모리의 여유 공간이 부족합니다.\nWii 메뉴의 데이터 관리 화면에서 데이터를 SD 카드로\n옮기거나 삭제하여 %s블록의\n여유 공간을 확보해 주세요.', '저장 공간 부족 안내', 'save_system');
add(0x003CA05E, 'Wii 본체 저장 메모리의 여유 파일 수가\n부족합니다.\nWii 메뉴의 데이터 관리 화면에서 데이터를\nSD 카드로 옮기거나 삭제해 주세요.', '저장 파일 수 부족 안내', 'save_system');
add(0x003CA163, '이대로 시작하면 저장할 수 없습니다', '저장 불가 경고', 'save_system');
add(0x003CA18A, '저장하지 않고 시작', '저장 없이 시작 선택지', 'save_system');
add(0x003CA19D, 'Wii 데이터 관리 화면으로', 'Wii 데이터 관리 이동 선택지', 'save_system');
add(0x003CA1BB, '게임 시작\n', '타이틀 선택지', 'title_system');
add(0x003CA1CB, 'Wii 메뉴로\n', '타이틀 선택지', 'title_system');
add(0x003CA1DA, 'Wii 본체 저장 메모리를 확인하고 있습니다...', '타이틀 저장 메모리 검사 안내', 'save_system');

[
  [0x003CA558, '공격'], [0x003CA561, '물리 공격'], [0x003CA56E, '광소술'],
  [0x003CA575, 'MP를 소비하는 행동'], [0x003CA588, '엑셀 액트'], [0x003CA597, 'SP를 소비하는 행동'],
  [0x003CA5AA, '암 포스'], [0x003CA5B9, 'AP를 소비하는 행동'], [0x003CA5CC, '아이템'],
  [0x003CA5D5, '아이템 사용'], [0x003CA5E4, '로그레스'], [0x003CA5ED, '로그레스 능력 사용'],
  [0x003CA602, '방어'], [0x003CA60B, '피해 감소'], [0x003CA61A, '대기/이동'],
  [0x003CA625, '대기 및 이동'],
].forEach(([o, t]) => add(o, t, '전투 커맨드와 도움말', 'battle_command'));

add(0x003CB2F3, '%s 지도', '지도 항목의 동적 명칭', 'map_ui');
[
  [0x003CB70C, '시스템'], [0x003CB715, '커맨드'], [0x003CB71E, '몬스터'],
  [0x003CB729, '광소술'], [0x003CB730, '아이템'], [0x003CB739, '용어'],
].forEach(([o, t]) => add(o, t, '용병 안내서 분류 탭', 'guide_ui'));
add(0x003CB73E, '안내서 『%s』에 항목 추가', '용병 안내서 새 항목 알림', 'system_notification');
add(0x003CB75B, '%s의 최대 HP가 %d 상승', '캐릭터 성장 알림', 'system_notification');
add(0x003CB78A, '암 포스 『%s』 잠금 해제', '암 포스 해금 알림', 'system_notification');
add(0x003CB7AB, '암 포스 프레임 확장', '암 포스 프레임 확장 알림', 'system_notification');
add(0x003CB7CB, '「%s」 습득', '기술 습득 알림', 'system_notification');

// Runtime speaker/name lookup table. Compact role labels are used where the fixed
// C-string slot cannot hold a spaced Korean form.
const nameRows = [
  [0x003CF1C8, '라르크'], [0x003CF1CF, '리피아'], [0x003CF1D8, '사쥬'],
  [0x003CF1E1, '오이겐'], [0x003CF1EA, '세실'], [0x003CF1F1, '레슬리'],
  [0x003CF1FA, '알스'], [0x003CF201, '아델'], [0x003CF20A, '니콜'],
  [0x003CF211, '클라이드'], [0x003CF21A, '디노스'], [0x003CF24E, '???'],
  [0x003CF255, '바이스'], [0x003CF25E, '이그나츠'], [0x003CF269, '호제아'],
  [0x003CF270, '폴랴'], [0x003CF279, '루냐'], [0x003CF282, '류즈'],
  [0x003CF28B, '소아라'], [0x003CF292, '프레이아'], [0x003CF29B, '엘레나'],
  [0x003CF2A2, '자무엘'], [0x003CF2AB, '마리아'], [0x003CF2B2, '엔주'],
  [0x003CF2BB, '셰리'], [0x003CF2C4, '엘리엇'], [0x003CF2CF, '하델'],
  [0x003CF2D8, '시엘'], [0x003CF2DF, '그란츠'], [0x003CF2E8, '소니아'],
  [0x003CF2EF, '코핀'], [0x003CF2F6, '코핀 장로'], [0x003CF301, '아브리스'],
  [0x003CF30C, '카자프'], [0x003CF313, '마크'], [0x003CF31A, '미키'],
  [0x003CF323, '료'], [0x003CF32A, '촌장'], [0x003CF32F, '제국재상'],
  [0x003CF338, '함장'], [0x003CF33D, '도적두목'], [0x003CF346, '의사'],
  [0x003CF34B, '제국병'], [0x003CF352, '교단병'], [0x003CF359, '공화국병'],
  [0x003CF362, '아이온대 병사'], [0x003CF371, '순례자'], [0x003CF378, '원로원의원'],
  [0x003CF383, '건달'], [0x003CF388, '오르키나교도'], [0x003CF395, '상인'],
  [0x003CF39A, '아가씨'], [0x003CF3A1, '청년'], [0x003CF3A8, '노인'],
  [0x003CF3AD, '중년녀'], [0x003CF3B4, '학생'], [0x003CF3B9, '여관 주인'],
  [0x003CF3C4, '소년'], [0x003CF3CB, '제어 시스템'], [0x003CF3D8, '신종'],
  [0x003CF3DD, '루샤'], [0x003CF3E6, '바네사'], [0x003CF3F1, '사키'],
  [0x003CF3F6, '소녀'], [0x003CF3FD, '아저씨'], [0x003CF404, '노파'],
  [0x003CF409, '사제'], [0x003CF40E, '경비'], [0x003CF413, '전령병'],
  [0x003CF41A, '월터'], [0x003CF425, '엘자'], [0x003CF42C, '라이언'],
  [0x003CF435, '루이스'], [0x003CF43C, '엄마'], [0x003CF441, '톰'],
  [0x003CF446, '가투라'], [0x003CF451, '원로원사자'], [0x003CF45C, '접수원'],
  [0x003CF463, '대장'], [0x003CF468, '경비병'], [0x003CF46F, '노스노와레 교도'],
];
nameRows.forEach(([o, t]) => add(o, t, '대화창 화자·NPC 표시명', 'speaker_name'));

[
  [0x003CF4C1, '심마프'], [0x003CF4CA, '길다브'], [0x003CF4D3, '파피르사그'],
  [0x003CF4DE, '아를루'], [0x003CF4E5, '아부심'], [0x003CF4EE, '그라'],
  [0x003CF4F3, '스쿠일'], [0x003CF4FC, '쿠도안느'], [0x003CF507, '우르그라'],
  [0x003CF510, '바네투'], [0x003CF519, '루훙가'], [0x003CF522, '마슈가르'],
  [0x003CF52D, '사령사'], [0x003CF534, '여관 코핀'], [0x003CF53F, '카지노 접수원'],
].forEach(([o, t]) => add(o, t, '대화·전투에서 표시되는 특수 개체명', 'speaker_name'));
add(0x003CF54E, '작전1', '작전 프리셋 명칭', 'strategy_ui');
add(0x003CF555, '작전2', '작전 프리셋 명칭', 'strategy_ui');
add(0x003CF55C, '작전3', '작전 프리셋 명칭', 'strategy_ui');

[
  [0x003CF6B8, '맹독'], [0x003CF6BD, '석화'], [0x003CF6C2, '침묵'], [0x003CF6C7, '질병'],
].forEach(([o, t]) => add(o, t, '아이템 대상의 상태 표시', 'status_ui'));
add(0x003CF6CD, '누구에게?', '아이템 사용 대상 선택', 'common_prompt');
add(0x003CF6DE, '전체 사용', '전체 대상 사용 안내', 'common_prompt');
add(0x003CF6ED, '%s\n      개를 버립니다.\n계속할까요?', '아이템 버리기 확인', 'inventory_prompt');
add(0x003CF718, '설정을 초기화하시겠습니까?', '설정 초기화 확인', 'common_prompt');
add(0x003CF73D, '%s을 1개 구매합니다.\n구매할까요?', '아이템 1개 구매 확인', 'shop_prompt');
add(0x003CF79B, '%s을 1개 판매합니다.\n판매할까요?', '아이템 1개 판매 확인', 'shop_prompt');
add(0x003CF7C0, '%s의 케이지에\n%s을 적용합니다.\n계속할까요?', '케이지 가공 확인', 'cage_prompt');
add(0x003CF7ED, '%s의 케이지 가공을\n모두 초기화합니다.\n계속할까요?', '케이지 가공 초기화 확인', 'cage_prompt');
add(0x003CF826, '%s 5개를 사용해\n%s 1개를 생성합니다.\n계속할까요?', '아이템 합성 확인', 'craft_prompt');
add(0x003CF85B, '%s을 구매합니다.\n구매할까요?', '아이템 구매 확인', 'shop_prompt');
add(0x003CF87D, '이 게임 데이터를 불러옵니다.\n계속하시겠습니까?', '게임 데이터 불러오기 확인', 'save_system');
add(0x003CF8AF, '불러오면 현재 게임 데이터는\n사라집니다. 계속하시겠습니까?', '불러오기 시 현재 데이터 손실 경고', 'save_system');
add(0x003CF8EF, '게임 데이터를 저장하시겠습니까?', '게임 데이터 저장 확인', 'save_system');
add(0x003CF91C, '이미 게임 데이터가 저장되어 있습니다.\n덮어쓰시겠습니까?', '게임 데이터 덮어쓰기 확인', 'save_system');
add(0x003CF960, '이 퀘스트를 수락합니다.\n계속하시겠습니까?', '퀘스트 수락 확인', 'quest_prompt');
add(0x003CF98A, '이 퀘스트는 도중에 포기할 수 없습니다.\n계속할까요?', '포기 불가 퀘스트 수락 경고', 'quest_prompt');
add(0x003CF9C0, '완료 조건을 충족한 퀘스트는\n포기할 수 없습니다.\n완료하시겠습니까?', '완료 조건 충족 퀘스트 처리 확인', 'quest_prompt');
add(0x003CFA0D, '이 퀘스트를 완료합니다.\n계속하시겠습니까?', '퀘스트 완료 확인', 'quest_prompt');
add(0x003CFA39, '이 퀘스트를 포기합니다.\n계속하시겠습니까?', '퀘스트 포기 확인', 'quest_prompt');
add(0x003CFA65, '선택한 전투를 시작합니다.\n계속하시겠습니까?', '선택 전투 시작 확인', 'battle_prompt');
add(0x003CFAD3, '코인 %d개와\n%s을 교환합니다.\n계속하시겠습니까?', '카지노 코인 교환 확인', 'casino_prompt');
add(0x003CFB15, '%x%s에서\n이 무기로 옮깁니다. 계속하시겠습니까?', '무기 간 피스 이동 확인', 'equipment_prompt');
add(0x003CFB45, '더블 업하시겠습니까?', '카지노 더블 업 확인', 'casino_prompt');
add(0x003CFB5C, '%s로 이동합니다.\n계속할까요?', '목적지 이동 확인', 'travel_prompt');
add(0x003CFB7E, '성공 보상 아이템이나 돈을\n한도까지 보유 중입니다. 지금 완료하면\n보상을 잃습니다. 계속하시겠습니까?', '보상 소지 한도 초과 퀘스트 완료 경고', 'quest_prompt');
add(0x003CFBF5, '성공 보상 아이템이나 돈을\n한도까지 보유 중입니다. 지금 승리하면\n보상을 잃습니다. 계속하시겠습니까?', '보상 소지 한도 초과 전투 승리 경고', 'battle_prompt');
add(0x003CFC6C, '예', '긍정 선택지', 'common_choice');
add(0x003CFC71, '아니요', '부정 선택지', 'common_choice');
add(0x003CFC78, '장비', '장비 선택지', 'equipment_ui');
add(0x003CFC7D, '해제', '장비 해제 선택지', 'equipment_ui');
add(0x003CFC82, '암 포스', '암 포스 메뉴', 'equipment_ui');
add(0x003CFC91, '호출', '대상 불러오기 선택지', 'common_ui');
add(0x003CFC9A, '자동항해', '자동 항해 선택지', 'travel_ui');
add(0x003CFCA3, '불러올 파일을 선택해 주세요', '불러오기 파일 선택 안내', 'save_system');
add(0x003CFCC6, '저장할 파일을 선택해 주세요', '저장 파일 선택 안내', 'save_system');
add(0x003CFCE9, '『결정』으로 각 엑셀 액트를\n확인할 수 있습니다', '엑셀 액트 확인 조작 도움말', 'system_menu');
add(0x003CFD1D, '『결정』으로 %s의 의상을\n선택할 수 있습니다', '의상 선택 조작 도움말', 'system_menu');
add(0x003CFD4B, '엑셀 액트를 습득하지 않았습니다', '엑셀 액트 미습득 안내', 'system_menu');
add(0x003CFD6C, '의상이 없습니다', '의상 미보유 안내', 'system_menu');
add(0x003CFD81, '아이템을 확인하거나 사용할 수 있습니다', '아이템 메뉴 설명', 'system_menu');
add(0x003CFDA8, '광소술을 사용하거나\n케이지의 젬을 교체할 수 있습니다', '광소술·케이지 메뉴 설명', 'system_menu');
add(0x003CFDE4, '무기를 바꾸거나\n암 포스를 설정할 수 있습니다', '무기·암 포스 메뉴 설명', 'system_menu');
add(0x003CFE18, '방어구 장비', '방어구 메뉴 설명', 'system_menu');
add(0x003CFE2B, '전투 설정을 변경할 수 있습니다', '작전 메뉴 설명', 'system_menu');
add(0x003CFE4C, '지도를 볼 수 있습니다', '지도 메뉴 설명', 'system_menu');
add(0x003CFE65, '여러 정보를 확인할 수 있습니다', '정보 메뉴 설명', 'system_menu');
add(0x003CFE88, '설정 변경, 저장/불러오기 가능', '시스템 메뉴 설명', 'system_menu');
add(0x003CFEAD, '『대열 변경』으로 전투 멤버를 교체하고\n『결정』으로 상태를 확인합니다', '파티 대열 변경 조작 도움말', 'system_menu');
add(0x003CFEF3, '게스트 멤버는 대열을\n바꿀 수 없습니다', '게스트 멤버 대열 변경 제한', 'system_menu');
add(0x003CFF25, '%s와 교체할 멤버를\n선택해 주세요', '파티 교체 대상 선택', 'system_menu');
add(0x003CFF51, '광소술 사용', '광소술 메뉴 설명', 'system_menu');
add(0x003CFF64, '케이지를 설정합니다', '케이지 메뉴 설명', 'system_menu');
add(0x003CFF7B, '무기의 암 포스 프레임에\n피스를 설정할 수 있습니다', '암 포스 피스 메뉴 설명', 'system_menu');
add(0x003CFFBB, '장비할 무기를 선택합니다', '무기 장비 메뉴 설명', 'system_menu');
add(0x003CFFD4, '작전을 설정합니다', '작전 메뉴 설명', 'system_menu');
add(0x003CFFE9, '파티를 편성합니다', '파티 편성 메뉴 설명', 'system_menu');

const byOffset = new Map(candidates.map((r) => [r.offset, r]));
const estimate = (s) => [...s].reduce((n, ch) => n + (ch.codePointAt(0) <= 0x7f ? 1 : 2), 0);
const printfTokens = (s) => s.match(/%(?:[-+0 #]*\d*(?:\.\d+)?[diuoxXfFeEgGaAcspn%])/g) || [];

const included = [];
const validationErrors = [];
if (mainDolSha256 !== probe.source_sha256.toUpperCase()) {
  validationErrors.push({ error: 'source_main_dol_sha256_mismatch', expected: probe.source_sha256.toUpperCase(), actual: mainDolSha256 });
}
if (sourceByteMismatches.length) {
  validationErrors.push({ error: 'source_candidate_raw_byte_mismatch', offsets: sourceByteMismatches.map((r) => r.offset) });
}
for (const [offset, t] of [...translations].sort((a, b) => a[0] - b[0])) {
  const src = byOffset.get(offset);
  if (!src) {
    validationErrors.push({ offset, error: 'offset_not_in_assigned_range' });
    continue;
  }
  const targetBytes = estimate(t.translation_ko);
  const sourceTokens = printfTokens(src.text);
  const targetTokens = printfTokens(t.translation_ko);
  if (targetBytes > src.capacity_to_nul) validationErrors.push({ offset, error: 'capacity_overflow', targetBytes, capacity: src.capacity_to_nul });
  if (JSON.stringify(sourceTokens) !== JSON.stringify(targetTokens)) validationErrors.push({ offset, error: 'printf_token_mismatch', sourceTokens, targetTokens });
  if ((src.text.match(/\n/g) || []).length !== (t.translation_ko.match(/\n/g) || []).length) validationErrors.push({ offset, error: 'newline_mismatch' });
  included.push({
    offset,
    source_text: src.text,
    translation_ko: t.translation_ko,
    context: t.context,
    lane: t.lane,
    capacity_to_nul: src.capacity_to_nul,
  });
}

const exclusionReason = (r) => {
  const s = r.text;
  if (/ダミー[３-９]|^[0-9a-f]{2}(?:セーブポイント|宝箱|次のマップ|ワールドマップ|はしご|宿屋|道具屋|武具屋|工房|仕立屋|ギルド|カジノ|闘技場|ハーモニーホール|現在位置)$/.test(s)) return 'internal_identifier_or_dummy_label';
  if (/テスト|デバッグ|ボス用|サンプル|（仮）|戦闘背景/.test(s) || (r.offset >= 0x003C73DF && r.offset <= 0x003C8592)) return 'unavailable_test_or_debug_menu';
  if (/^(E[0-7])/.test(s) || s === '96盗まれた' || s.startsWith('96になります')) return 'internal_or_invalid_placeholder_literal';
  if (s === 'ないよ〜〜ん' || s === '停止中だよもん' || s === 'あれ？？\n') return 'unreachable_developer_placeholder';
  if (/^>>|warning|ERROR|err |scr err|info :|alloc|cache|タスク|初期化|後始末|読み込み|ロード時|チェックディジット|スタック|overflow|オーバー|NAND|ワークバッファ|ユーザー定義|構造体|アイコン番号|作成に失敗|データがありません|マップがありません|ファイル名がありません|解除\n|起動\n|フラグ値|グループ指定|コマ落ち|デコードスキップ|表示スキップ|エンプティBスキップ|コール|バッチ|フレーム変更|セピア化|未接続\n|リモコン\n|ヌンチャク\n|クラコン\n|ＧＣパッド\n/.test(s)) return 'developer_log_assert_or_runtime_diagnostic';
  if (r.offset >= 0x003C931B && r.offset <= 0x003C939C) return 'unavailable_tutorial_test_choice';
  return 'internal_non_display_string_or_unproven_visibility';
};

const includedOffsets = new Set(included.map((r) => r.offset));
const excluded = candidates.filter((r) => !includedOffsets.has(r.offset)).map((r) => ({
  offset: r.offset,
  source_text: r.text,
  reason: exclusionReason(r),
}));

const outDir = path.join(root, 'work/runtime_fix');
fs.writeFileSync(path.join(outDir, 'main_dol_lower_fragment.jsonl'), included.map((r) => JSON.stringify(r)).join('\n') + '\n', 'utf8');
const byReason = {};
for (const e of excluded) byReason[e.reason] = (byReason[e.reason] || 0) + 1;
const report = {
  schema: 'arf-main-dol-lower-fragment-audit-v1',
  source_file: 'DATA/sys/main.dol',
  source_sha256: probe.source_sha256.toUpperCase(),
  source_verification: {
    actual_file: 'work/disc_extracted/DATA/sys/main.dol',
    actual_size: mainDol.length,
    actual_sha256: mainDolSha256,
    expected_sha256_match: mainDolSha256 === probe.source_sha256.toUpperCase(),
    candidate_raw_byte_match_count: candidates.length - sourceByteMismatches.length,
    candidate_raw_byte_mismatch_count: sourceByteMismatches.length,
  },
  assigned_offset_start: 0x003C64F7,
  assigned_offset_end: 0x003CFFFF,
  candidate_count: candidates.length,
  included_count: included.length,
  excluded_count: excluded.length,
  unresolved_count: 0,
  validation: {
    custom_euc28_estimator: 'ASCII=1 byte, non-ASCII=2 bytes',
    capacity_overflow_count: validationErrors.filter((e) => e.error === 'capacity_overflow').length,
    printf_token_mismatch_count: validationErrors.filter((e) => e.error === 'printf_token_mismatch').length,
    newline_mismatch_count: validationErrors.filter((e) => e.error === 'newline_mismatch').length,
    errors: validationErrors,
  },
  exclusion_counts_by_reason: byReason,
  exclusions: excluded,
  provenance: {
    translation_engine: 'Codex internal model only',
    external_translation_used: false,
    terminology_sources: [
      'work/translation/glossary_agent/glossary.csv',
      'work/translation/final/translation_memory_draft.json',
    ],
  },
};
fs.writeFileSync(path.join(outDir, 'main_dol_lower_fragment_report.json'), JSON.stringify(report, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({ included: included.length, excluded: excluded.length, validationErrors }, null, 2));
if (validationErrors.length) process.exitCode = 1;
