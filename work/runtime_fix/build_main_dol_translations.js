const fs = require('fs');
const crypto = require('crypto');

const probePath = 'work/catalog/text_probe_10.json';
const dolPath = 'work/disc_extracted/DATA/sys/main.dol';
const outPath = 'work/runtime_fix/main_dol_priority_fragment.jsonl';
const reportPath = 'work/runtime_fix/main_dol_priority_fragment_report.json';

const probe = JSON.parse(fs.readFileSync(probePath, 'utf8'));
const byOffset = new Map(probe.records.map((r) => [r.offset, r]));

// [file offset, Korean, runtime context, lane]
// Only strings with a direct player-facing callsite/surface are included.
const selected = [
  [0x3c651c, 'ARC RISE FANTASIA 디스크를\n넣어 주세요.', '디스크 미삽입 오류 화면', 'title_system'],
  [0x3c6550, '디스크를 읽을 수 없습니다.\nWii 본체 사용설명서를 확인해 주세요.', '디스크 읽기 오류 화면', 'title_system'],

  [0x3c905e, 'Wii 리모컨 연결이 끊겼습니다.', '컨트롤러 연결 끊김 안내', 'controller_prompt'],
  [0x3c907e, 'Wii 리모컨에 눈차크 또는\n클래식 컨트롤러를 연결해 주세요.', '필수 확장 컨트롤러 연결 안내', 'controller_prompt'],
  [0x3c92f8, '「전투 튜토리얼」을 보시겠습니까?', '전투 튜토리얼 확인', 'tutorial_prompt'],
  [0x3c93b8, '행동하시겠습니까?', '전투 행동 시작 확인', 'common_prompt'],
  [0x3c93cd, '예', '공통 긍정 선택지', 'common_choice'],
  [0x3c93d2, '아니요', '공통 부정 선택지', 'common_choice'],
  [0x3c98a2, '세이브 포인트', '세이브 포인트 명칭', 'title_system'],

  [0x3c9e01, '사용할 컨트롤러를\n설정합니다.\n컨트롤러의 버튼을 누르면\n확정됩니다.', '최초 실행 컨트롤러 선택 안내', 'initial_setup'],
  [0x3c9e59, '눈차크', '최초 실행 컨트롤러 종류', 'initial_setup'],
  [0x3c9e64, '클래식 컨트롤러', '최초 실행 컨트롤러 종류', 'initial_setup'],
  [0x3c9e7b, '게임큐브 컨트롤러', '최초 실행 컨트롤러 종류', 'initial_setup'],
  [0x3c9e96, '%s\n조작 컨트롤러로 설정했습니다.', '최초 실행 컨트롤러 확정 안내', 'initial_setup'],
  [0x3c9f5f, 'Wii 본체 저장 메모리의 여유 공간이 부족합니다.\nWii 메뉴의 데이터 관리 화면에서 데이터를 SD 카드로\n옮기거나 삭제하여 %s블록의\n여유 공간을 확보해 주세요.', '저장 메모리 용량 부족 오류', 'save_system'],
  [0x3ca05e, 'Wii 본체 저장 메모리의 여유 파일 수가\n부족합니다.\nWii 메뉴의 데이터 관리 화면에서 데이터를\nSD 카드로 옮기거나 삭제해 주세요.', '저장 메모리 파일 수 부족 오류', 'save_system'],
  [0x3ca163, '이대로 시작하면 저장할 수 없습니다', '저장 불가 상태 경고', 'save_system'],
  [0x3ca18a, '저장하지 않고 시작', '저장 없이 시작 선택지', 'save_system'],
  [0x3ca19d, 'Wii 데이터 관리 화면으로', 'Wii 데이터 관리 이동 선택지', 'save_system'],
  [0x3ca1bb, '게임 시작\n', '게임 시작 선택지', 'title_system'],
  [0x3ca1cb, 'Wii 메뉴로\n', 'Wii 메뉴 이동 선택지', 'title_system'],
  [0x3ca1da, 'Wii 본체 저장 메모리를 확인하고 있습니다...', '최초 저장 메모리 확인 안내', 'save_system'],

  [0x3cb70c, '시스템', '용병 안내서 분류 탭', 'common_ui'],
  [0x3cb715, '커맨드', '용병 안내서 분류 탭', 'common_ui'],
  [0x3cb71e, '몬스터', '용병 안내서 분류 탭', 'common_ui'],
  [0x3cb729, '광소술', '용병 안내서 분류 탭', 'common_ui'],
  [0x3cb730, '아이템', '용병 안내서 분류 탭', 'common_ui'],
  [0x3cb739, '용어', '용병 안내서 분류 탭', 'common_ui'],
  [0x3cb73e, '안내서 『%s』에 항목 추가', '용병 안내서 갱신 알림', 'system_notification'],
  [0x3cb75b, '%s의 최대 HP가 %d 상승', '능력치 상승 알림', 'system_notification'],
  [0x3cb78a, '암 포스 『%s』 잠금 해제', '암 포스 잠금 해제 알림', 'system_notification'],
  [0x3cb7ab, '암 포스 프레임 확장', '암 포스 프레임 확장 알림', 'system_notification'],
  [0x3cb7cb, '「%s」 습득', '기술 습득 알림', 'system_notification'],

  [0x3cf6cd, '누구에게?', '아이템 대상 선택 안내', 'common_prompt'],
  [0x3cf6de, '전체 사용', '아이템 전체 대상 안내', 'common_prompt'],
  [0x3cf718, '설정을 초기화하시겠습니까?', '설정 초기화 확인', 'common_prompt'],
  [0x3cf87d, '이 게임 데이터를 불러옵니다.\n계속하시겠습니까?', '불러오기 확인', 'save_system'],
  [0x3cf8af, '불러오면 현재 게임 데이터는\n사라집니다. 계속하시겠습니까?', '불러오기 데이터 유실 경고', 'save_system'],
  [0x3cf8ef, '게임 데이터를 저장하시겠습니까?', '저장 확인', 'save_system'],
  [0x3cf91c, '이미 게임 데이터가 저장되어 있습니다.\n덮어쓰시겠습니까?', '저장 덮어쓰기 확인', 'save_system'],
  [0x3cfc6c, '예', '공통 긍정 선택지', 'common_choice'],
  [0x3cfc71, '아니요', '공통 부정 선택지', 'common_choice'],
  [0x3cfca3, '불러올 파일을 선택해 주세요', '불러오기 슬롯 선택 안내', 'save_system'],
  [0x3cfcc6, '저장할 파일을 선택해 주세요', '저장 슬롯 선택 안내', 'save_system'],

  [0x3cfd81, '아이템을 확인하거나 사용할 수 있습니다', '메인 메뉴 아이템 설명', 'system_menu'],
  [0x3cfda8, '광소술을 사용하거나\n케이지의 젬을 교체할 수 있습니다', '메인 메뉴 광소술 설명', 'system_menu'],
  [0x3cfde4, '무기를 바꾸거나\n암 포스를 설정할 수 있습니다', '메인 메뉴 장비 설명', 'system_menu'],
  [0x3cfe18, '방어구 장비', '메인 메뉴 방어구 설명', 'system_menu'],
  [0x3cfe2b, '전투 설정을 변경할 수 있습니다', '메인 메뉴 전투 설정 설명', 'system_menu'],
  [0x3cfe4c, '지도를 볼 수 있습니다', '메인 메뉴 지도 설명', 'system_menu'],
  [0x3cfe65, '여러 정보를 확인할 수 있습니다', '메인 메뉴 정보 설명', 'system_menu'],
  [0x3cfe88, '설정 변경, 저장/불러오기 가능', '메인 메뉴 시스템 설명', 'system_menu'],
  [0x3cfead, '『대열 변경』으로 전투 멤버를 교체하고\n『결정』으로 상태를 확인합니다', '파티 메뉴 조작 안내', 'system_menu'],
  [0x3cfef3, '게스트 멤버는 대열을\n바꿀 수 없습니다', '파티 대열 변경 제한', 'system_menu'],
  [0x3cff25, '%s와 교체할 멤버를\n선택해 주세요', '파티 교체 대상 선택', 'system_menu'],
  [0x3cff51, '광소술 사용', '광소술 메뉴 설명', 'system_menu'],
  [0x3cff64, '케이지를 설정합니다', '케이지 메뉴 설명', 'system_menu'],
  [0x3cff7b, '무기의 암 포스 프레임에\n피스를 설정할 수 있습니다', '암 포스 설정 설명', 'system_menu'],
  [0x3cffbb, '장비할 무기를 선택합니다', '무기 장비 메뉴 설명', 'system_menu'],
  [0x3cffd4, '작전을 설정합니다', '작전 메뉴 설명', 'system_menu'],
  [0x3cffe9, '파티를 편성합니다', '파티 편성 메뉴 설명', 'system_menu'],
  [0x3d0000, '로그레스 확인 및 동조가 가능합니다', '로그레스 메뉴 설명', 'system_menu'],
  [0x3d002b, '주변 지도를 확인할 수 있습니다', '지역 지도 설명', 'system_menu'],
  [0x3d004c, '세계 지도를 확인할 수 있습니다', '세계 지도 설명', 'system_menu'],
  [0x3d006d, '길드 수첩을 확인합니다', '길드 수첩 설명', 'system_menu'],
  [0x3d0084, '전투한 몬스터 정보를\n확인할 수 있습니다', '몬스터 도감 설명', 'system_menu'],
  [0x3d00b0, '게임 용어를 확인할 수 있습니다', '용어집 설명', 'system_menu'],
  [0x3d00d5, '데이터를 저장할 수 있습니다', '저장 메뉴 설명', 'system_menu'],
  [0x3d00f6, '데이터를 불러올 수 있습니다', '불러오기 메뉴 설명', 'system_menu'],
  [0x3d0117, '게임 설정을 변경합니다', '설정 메뉴 설명', 'system_menu'],

  [0x3d1007, '항목선택', '공통 조작 도움말', 'common_ui'],
  [0x3d1010, '결정', '공통 조작 도움말', 'common_ui'],
  [0x3d1015, '뒤로', '공통 조작 도움말', 'common_ui'],
  [0x3d101a, '상태', '공통 조작 도움말', 'common_ui'],
  [0x3d1025, '닫기', '공통 조작 도움말', 'common_ui'],
  [0x3d102c, '버리기', '공통 조작 도움말', 'common_ui'],
  [0x3d1033, '정산', '공통 조작 도움말', 'common_ui'],
  [0x3d1038, '상세정보', '공통 조작 도움말', 'common_ui'],
  [0x3d1041, '줌', '공통 조작 도움말', 'common_ui'],
  [0x3d1048, '프레임 조작', '공통 조작 도움말', 'common_ui'],
  [0x3d1055, '모델', '공통 조작 도움말', 'common_ui'],
  [0x3d105c, '회전', '공통 조작 도움말', 'common_ui'],
  [0x3d1061, '전환', '공통 조작 도움말', 'common_ui'],
  [0x3d1066, '좌우회전', '공통 조작 도움말', 'common_ui'],
  [0x3d106f, '상하회전', '공통 조작 도움말', 'common_ui'],
  [0x3d1078, '목록', '공통 조작 도움말', 'common_ui'],
  [0x3d107f, '수락', '공통 조작 도움말', 'common_ui'],
  [0x3d1086, '달성', '공통 조작 도움말', 'common_ui'],
  [0x3d108b, '포기', '공통 조작 도움말', 'common_ui'],
  [0x3d1090, '참가', '공통 조작 도움말', 'common_ui'],
  [0x3d1095, '자릿수', '공통 조작 도움말', 'common_ui'],
  [0x3d109c, '카드 선택', '공통 조작 도움말', 'common_ui'],
  [0x3d10a7, '색선택', '공통 조작 도움말', 'common_ui'],
  [0x3d10ae, '끝내기', '공통 조작 도움말', 'common_ui'],
  [0x3d10b5, '릴 정지', '공통 조작 도움말', 'common_ui'],
  [0x3d10c0, '다음', '공통 조작 도움말', 'common_ui'],
  [0x3d10c5, '카드 교환', '공통 조작 도움말', 'common_ui'],
  [0x3d10d0, '단어검색', '공통 조작 도움말', 'common_ui'],
  [0x3d10d9, '기록', '공통 조작 도움말', 'common_ui'],
  [0x3d10de, '이동', '공통 조작 도움말', 'common_ui'],
  [0x3d10e3, '정보', '공통 조작 도움말', 'common_ui'],
  [0x3d10e8, '프레임', '공통 조작 도움말', 'common_ui'],
  [0x3d10f1, '대열변경', '공통 조작 도움말', 'common_ui'],
  [0x3d10fa, '설정완료', '초기 설정 완료 버튼', 'initial_setup'],
  [0x3d1103, '초기설정', '최초 실행 설정 화면 제목', 'initial_setup'],
  [0x3d110c, '사용할 컨트롤러를\n설정합니다.\n컨트롤러의 버튼을 누르면\n확정됩니다.', '초기 설정 컨트롤러 선택 안내', 'initial_setup'],
  [0x3d1164, '%s\n조작 컨트롤러로 설정했습니다.', '초기 설정 컨트롤러 확정 안내', 'initial_setup'],
  [0x3d118a, '컨트롤러', '초기 설정 항목', 'initial_setup'],
  [0x3d1197, '진동', '초기 설정 항목', 'initial_setup'],
  [0x3d119c, '자막', '초기 설정 항목', 'initial_setup'],
  [0x3d11a1, '커서 기억', '초기 설정 항목', 'initial_setup'],
  [0x3d11ae, '카메라회전', '초기 설정 항목', 'initial_setup'],
  [0x3d11b9, '글자속도', '초기 설정 항목', 'initial_setup'],
  [0x3d11c2, 'BGM 음량', '초기 설정 항목', 'initial_setup'],
  [0x3d11cd, 'SE 음량', '초기 설정 항목', 'initial_setup'],
  [0x3d11d6, '음성음량', '초기 설정 항목', 'initial_setup'],
  [0x3d11df, '플리커 레벨', '초기 설정 항목', 'initial_setup'],
  [0x3d11f0, 'ON', '설정값', 'initial_setup'],
  [0x3d11f5, '끔', '설정값', 'initial_setup'],
  [0x3d11fc, '느림', '문자 속도 설정값', 'initial_setup'],
  [0x3d1201, '보통', '문자 속도 설정값', 'initial_setup'],
  [0x3d1206, '빠름', '문자 속도 설정값', 'initial_setup'],
  [0x3d120b, '즉시', '문자 속도 설정값', 'initial_setup'],
  [0x3d1210, '무음', '음량 설정값', 'initial_setup'],
  [0x3d1215, '최대', '음량 설정값', 'initial_setup'],
  [0x3d121a, '최소', '음량 설정값', 'initial_setup'],
  [0x3d121f, '일반', '카메라 회전 설정값', 'initial_setup'],
  [0x3d1224, '반전', '카메라 회전 설정값', 'initial_setup'],
  [0x3d1229, '사용할 컨트롤러를 설정합니다', '초기 설정 항목 설명', 'initial_setup'],
  [0x3d124a, '컨트롤러 진동을 설정합니다', '초기 설정 항목 설명', 'initial_setup'],
  [0x3d1269, '데모 장면의 자막 표시 여부를\n설정합니다', '초기 설정 항목 설명', 'initial_setup'],
  [0x3d1295, '전투 메뉴의 커서 위치\n저장 여부를 설정합니다', '초기 설정 항목 설명', 'initial_setup'],
  [0x3d12d1, '월드에서 카메라 회전 방향을\n설정합니다', '초기 설정 항목 설명', 'initial_setup'],
  [0x3d12fb, '메시지 표시 속도를 설정합니다', '초기 설정 항목 설명', 'initial_setup'],
  [0x3d131c, 'BGM 음량을 조절합니다', '초기 설정 항목 설명', 'initial_setup'],
  [0x3d1335, 'SE 음량을 조절합니다', '초기 설정 항목 설명', 'initial_setup'],
  [0x3d134c, '음성 음량을 조절합니다', '초기 설정 항목 설명', 'initial_setup'],
  [0x3d1363, '플리커 필터 레벨을 설정합니다', '초기 설정 항목 설명', 'initial_setup'],
  [0x3d138a, '불러오는 중', '불러오기 진행 안내', 'save_system'],
  [0x3d139b, '불러오기 완료', '불러오기 완료 안내', 'save_system'],
  [0x3d13b0, '저장 중입니다.\n전원 버튼(또는 리셋 버튼)을\n누르지 마세요.', '저장 진행 및 전원 경고', 'save_system'],
  [0x3d13f7, '저장 완료', '저장 완료 안내', 'save_system'],
  [0x3d143a, 'Wii 본체 저장 메모리의 여유 공간이\n부족합니다.\nWii 메뉴의 데이터 관리 화면에서\n데이터를 SD 카드로 옮기거나\n삭제하여 4블록의 여유 공간을\n확보해 주세요.', '저장 공간 부족 오류', 'save_system'],
  [0x3d14e4, 'Wii 본체 저장 메모리를\n읽거나 쓸 수 없습니다.\nWii 본체 사용설명서를 확인해 주세요.', '저장 메모리 입출력 오류', 'save_system'],
  [0x3d156b, '데이터가 없습니다', '빈 저장 슬롯 안내', 'save_system'],
  [0x3d157e, '월드 맵', '월드 맵 화면명', 'common_ui'],
];

function estimatedEncodedLength(s) {
  let n = 0;
  for (const ch of s) n += ch.codePointAt(0) <= 0x7f ? 1 : 2;
  return n;
}

const dol = fs.readFileSync(dolPath);
const records = [];
const errors = [];
for (const [offset, translation, context, lane] of selected) {
  const src = byOffset.get(offset);
  if (!src) {
    errors.push({ offset_hex: `0x${offset.toString(16).toUpperCase()}`, error: 'probe_record_missing' });
    continue;
  }
  const actual = dol.subarray(offset, offset + src.byte_length).toString('hex').toUpperCase();
  if (actual !== src.raw_hex.toUpperCase()) {
    errors.push({ offset_hex: `0x${offset.toString(16).toUpperCase()}`, error: 'source_bytes_mismatch' });
    continue;
  }
  const targetLength = estimatedEncodedLength(translation);
  if (targetLength > src.capacity_to_nul) {
    errors.push({
      offset_hex: `0x${offset.toString(16).toUpperCase()}`,
      error: 'estimated_target_over_capacity',
      capacity: src.capacity_to_nul,
      estimated_target_bytes: targetLength,
      translation_ko: translation,
    });
    continue;
  }
  records.push({
    schema: 'arf-main-dol-translation-v1',
    file: 'DATA/sys/main.dol',
    file_sha256: probe.source_sha256.toUpperCase(),
    offset,
    offset_hex: `0x${offset.toString(16).toUpperCase().padStart(8, '0')}`,
    byte_length: src.byte_length,
    capacity_to_nul: src.capacity_to_nul,
    source_encoding: 'EUC-JP',
    source_text: src.text,
    source_raw_hex: src.raw_hex.toUpperCase(),
    translation_ko: translation,
    estimated_target_bytes: targetLength,
    context,
    lane,
    visibility: 'runtime_user_visible',
    provenance: 'Codex internal model',
    external_translation_used: false,
  });
}

records.sort((a, b) => a.offset - b.offset);
fs.writeFileSync(outPath, records.map((r) => JSON.stringify(r)).join('\n') + '\n', 'utf8');

const counts = {};
for (const r of records) counts[r.lane] = (counts[r.lane] || 0) + 1;
const report = {
  schema: 'arf-main-dol-translation-report-v1',
  source: dolPath,
  source_sha256: crypto.createHash('sha256').update(dol).digest('hex').toUpperCase(),
  probe_candidate_count: probe.records.length,
  selected_runtime_user_visible_count: records.length,
  excluded_or_deferred_candidate_count: probe.records.length - records.length,
  counts_by_lane: counts,
  validation: {
    all_offsets_present_in_probe: !errors.some((e) => e.error === 'probe_record_missing'),
    all_source_bytes_match_main_dol: !errors.some((e) => e.error === 'source_bytes_mismatch'),
    all_estimated_targets_fit_capacity: !errors.some((e) => e.error === 'estimated_target_over_capacity'),
    placeholder_policy: 'printf placeholders preserved verbatim',
  },
  errors,
  exclusions: {
    debug_only: 'developer menus, printf/assert/log strings, task init/finalize traces, test maps and internal identifiers excluded',
    deferred_user_content: 'battle/casino/quest and map-specific main.dol strings outside initial/title/system-common priority remain for the next runtime-fix pass',
  },
  unresolved: errors,
};
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n', 'utf8');
console.log(JSON.stringify(report, null, 2));
