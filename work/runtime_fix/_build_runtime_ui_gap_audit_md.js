const fs = require('fs');
const a = JSON.parse(fs.readFileSync('work/runtime_fix/runtime_ui_gap_audit.json', 'utf8'));
const L = [];
const add = (...x) => L.push(...x);
const q = (x) => '`' + String(x) + '`';
const cell = (x) => String(x ?? '').replaceAll('|', '\\|').replaceAll('\r\n', '<br>').replaceAll('\n', '<br>');

add('# Arc Rise Fantasia 한국어화 런타임 UI 경계 감사', '');
add('- 게임 ID: ' + q(a.game_id));
add('- 감사 시각: ' + q(a.generated_at));
add('- 판정: **' + a.verdict.status + '**');
add('- 본 문서는 감사 스냅샷이다. 원본 추출물, 게임 페이로드, 현재 655개 staging 파일은 변경하지 않았다.');
add('- 본 감사에서 번역을 수행하지 않았다. 후속 번역은 Codex 내부 모델만 사용한다.', '');

add('## 1. 결론', '');
add('초기 설정 화면의 일본어는 이미지가 아니라 ' + q('DATA/sys/main.dol') + '의 EUC-JP rodata에서 온다. ' +
  q('text_probe_10.json') + '은 이를 발견했지만 최종 텍스트 카탈로그가 ' + q('DATA/files') +
  '만 읽어서 ' + q('DATA/sys/main.dol') + '이 catalog, application, staging 경로에서 탈락했다.', '');
add('main.dol 밖에서도 다음 누락이 확정되었다.', '');
add('1. ' + q('DATA/files/Hbm/home.csv') + ', ' + q('home_nosave.csv') + ': Wii HOME 동적 일본어 문구.');
add('2. ' + q('DATA/files/Hbm/homeBtn.arc') + ': 일본어가 구워진 I4 TPL 18개와 한글 매핑이 0개인 BRFNT.');
add('3. ' + q('DATA/files/Event/endroll/EV09_18_0200C_00.wtm') + '부터 ' + q('_22.wtm') + ': 엔딩 대사 이미지 23개.', '');
add('현재 staging ' + a.coverage_delta.current_staged_physical_files + '개에 확정 누락 ' +
  a.coverage_delta.definite_new_physical_files + '개를 더하면 최소 ' +
  '**' + a.coverage_delta.projected_minimum_staged_physical_files_if_all_definite_gaps_are_added_without_overlap +
  '개**다. 영상과 배너 시각 전수 검사가 남아 있어 잠정치다.', '');

add('## 2. 런타임 및 파이프라인 증거', '');
add('| 증거 | 값 |', '|---|---|');
add('| 일본어 초기 설정 캡처 | ' + q(a.runtime_evidence.initial_settings_japanese.path) + ', SHA-256 ' +
  q(a.runtime_evidence.initial_settings_japanese.sha256) + ', 642×512 JPEG |');
add('| 한글 스트랩 대조 캡처 | ' + q(a.runtime_evidence.korean_strap_control.path) + ', SHA-256 ' +
  q(a.runtime_evidence.korean_strap_control.sha256) + ', 642×512 JPEG |');
add('| DOL probe | ' + a.main_dol.probe.candidate_count + '개 후보, EUC-JP, SHA-256 ' + q(a.main_dol.source_sha256) + ' |');
add('| 텍스트 카탈로그 | ' + a.current_pipeline_snapshot.catalog.record_count + ' occurrences / ' +
  a.current_pipeline_snapshot.catalog.physical_source_count + ' physical sources, main.dol=' +
  a.current_pipeline_snapshot.catalog.contains_main_dol + ', Hbm=' + a.current_pipeline_snapshot.catalog.contains_hbm + ' |');
add('| 최종 staging | ' + a.current_pipeline_snapshot.staging.staged_physical_files + '개, roots=' +
  q(JSON.stringify(a.current_pipeline_snapshot.staging.roots)) + ', main.dol=' +
  a.current_pipeline_snapshot.staging.contains_main_dol + ', Hbm=' + a.current_pipeline_snapshot.staging.contains_hbm +
  ', endroll=' + a.current_pipeline_snapshot.staging.contains_endroll_wtm + ' |');
add('| 이미지 lane | 수정 asset ' + a.current_pipeline_snapshot.image_lane.modified_asset_count + '개 / target ' +
  a.current_pipeline_snapshot.image_lane.replacement_target_count + '개, homeBtn=' +
  a.current_pipeline_snapshot.image_lane.contains_home_button_archive + ', endroll=' +
  a.current_pipeline_snapshot.image_lane.contains_endroll_dialogue_wtm + ' |', '');

add('### 원인 체인', '', '```text');
add('DATA/sys/main.dol --(probe 발견)--> 1,885 candidates');
add('        X');
add('DATA/files only --(catalog)--> application --> 655-file staging');
add('');
add('Hbm CSV/U8 + Event/endroll WTM');
add('        X  (텍스트/이미지 allowlist에 들어가지 못함)');
add('```', '');

add('## 3. main.dol 정확 오프셋', '');
add('- 물리 파일: ' + q(a.main_dol.physical_path));
add('- 크기: ' + a.main_dol.source_size + ' bytes');
add('- SHA-256: ' + q(a.main_dol.source_sha256));
add('- section: data[4], overall index 11, file ' + q(a.main_dol.containing_section.file_start_hex) + '..' +
  q(a.main_dol.containing_section.file_end_exclusive_hex) + ', RAM ' + q(a.main_dol.containing_section.ram_start_hex) + '..' +
  q(a.main_dol.containing_section.ram_end_exclusive_hex));
add('- 주소식: ' + q(a.main_dol.containing_section.mapping_formula));
add('- 직접 사용자 표시 확정 최소: ' + a.main_dol.confirmed_runtime_user_visible_minimum_count + '개');
add('- 초기 설정 lane: ' + a.main_dol.initial_settings_record_count + '개');
add('- casino/map/Copin 추가 deferred 사용자 표시 레코드: ' + a.main_dol.additional_deferred_player_facing_record_count + '개', '');

add('### 초기 설정 lane 40개', '');
add('| file offset | RAM | bytes/capacity | 일본어 원문 |', '|---:|---:|---:|---|');
for (const r of a.main_dol.initial_settings_records) {
  add('| ' + q(r.file_offset_hex) + ' | ' + q(r.ram_address_hex) + ' | ' + r.byte_length + '/' +
    r.capacity_to_nul + ' | ' + cell(r.source_text_jp) + ' |');
}
add('');
add('전체 146개 확정 레코드와 추가 129개 deferred 레코드의 raw_hex, 원문 SHA-256, file/RAM 주소는 동반 JSON에 수록했다. ' +
  'DOL의 나머지 probe 후보에는 false positive, debug, 추가 사용자 표시 문구가 섞여 있으므로 146개를 전수 완료로 해석하면 안 된다.', '');

add('## 4. main.dol 밖의 확정 누락', '');
add('### 4.1 Wii HOME 동적 문구', '');
add('| 물리 파일 | byte offset | bytes | 일본어 첫 열 |', '|---|---:|---:|---|');
for (const f of a.non_main_dol_definite_gaps.hbm_csv_text) {
  for (const r of f.records) {
    add('| ' + q('DATA/files/' + f.physical_path) + ' | ' + q(r.byte_offset_hex) + ' | ' + r.byte_length +
      ' | ' + cell(r.source_text_jp) + ' |');
  }
}
add('');
add('두 파일은 BOM FEFF, UTF-16BE, 탭 구분 다국어 열 구조다. 첫 번째 일본어 열만 바꾸고 BOM, CRLF, 따옴표, 탭, 행 수, 다른 언어 열을 보존해야 한다.', '');

const h = a.non_main_dol_definite_gaps.hbm_baked_ui_and_font;
add('### 4.2 Wii HOME 이미지와 폰트', '');
add('- 물리 파일: ' + q('DATA/files/' + h.physical_path));
add('- 크기: ' + h.source_size + ' bytes');
add('- SHA-256: ' + q(h.source_sha256));
add('- U8 nodes: ' + h.u8_node_count);
add('- 시각 증거: ' + q(h.visual_evidence.path) + ', SHA-256 ' + q(h.visual_evidence.sha256), '');
add('| U8 member | archive offset | size | TPL | 보이는 표기 | SHA-256 |', '|---|---:|---:|---:|---|---|');
for (const t of h.language_specific_textures) {
  add('| ' + q(t.member_path) + ' | ' + q(t.archive_offset_hex) + ' | ' + t.size_bytes + ' | ' +
    t.tpl_width + '×' + t.tpl_height + ' ' + t.tpl_gx_format_name + ' | ' + cell(t.visible_source_text_jp) +
    ' | ' + q(t.sha256) + ' |');
}
add('');
const fnt = h.dynamic_text_font;
add('동적 문구용 폰트 ' + q(fnt.member_path) + '는 archive ' + q(fnt.archive_offset_hex) + ', ' + fnt.size_bytes +
  ' bytes, SHA-256 ' + q(fnt.sha256) + '다. 고유 CMAP 매핑 ' + fnt.unique_mapped_codepoint_count +
  '개 중 **한글 음절 매핑은 ' + fnt.mapped_hangul_syllable_count + '개**다. CSV만 바꾸면 한글이 나오지 않으므로 BRFNT도 재구축해야 한다.', '');

const er = a.non_main_dol_definite_gaps.endroll_baked_dialogue;
add('### 4.3 엔딩 대사 이미지 23개', '');
add('- 시각 증거: ' + q(er.visual_evidence.path) + ', SHA-256 ' + q(er.visual_evidence.sha256), '');
add('| 물리 파일 | 크기 | 규격 | 일본어 시각 전사 | SHA-256 |', '|---|---:|---:|---|---|');
for (const f of er.files) {
  add('| ' + q('DATA/files/' + f.physical_path) + ' | ' + f.size_bytes + ' | ' + f.width + '×' + f.height +
    ' ' + f.gx_format + '/' + f.palette_format + ', data ' + q(f.image_data_offset_hex) + ' | ' +
    cell(f.visible_source_text_jp_visual_transcription) + ' | ' + q(f.sha256) + ' |');
}
add('');
add('이 파일들은 크레딧 장식이 아니라 엔딩 장면 대사를 표시하는 standalone WTM이다. fin.wtm은 라틴 FIN뿐이어서 제외했다.', '');

add('## 5. 확정 물리 파일 목록', '');
for (const p of a.coverage_delta.definite_gap_physical_paths) add('- ' + q(p));
add('');

add('## 6. 수정 권고', '');
for (const r of a.remediation_recommendations_without_translations) {
  add('### P' + r.priority + ' — ' + q(r.target), '', r.action, '');
  if (r.staging) add('Staging: ' + r.staging, '');
}

add('## 7. 남은 전수 검사', '');
for (const x of a.unresolved_visual_sweep) add('- ' + x);
add('');
add('opening.bnr의 IMET 일본어 슬롯은 ARC RISE FANTASIA이고, fin.wtm은 FIN, homeBtnIcon.wtm은 심볼이다. ' +
  '현재 확정 일본어 누락에서는 제외했지만 opening.bnr 압축 그래픽과 SFD 영상은 시각 검사가 남아 있다.', '');

add('## 8. 런타임 합격 기준', '');
for (const x of a.required_runtime_acceptance) add('- [ ] ' + x);
add('', '---', '', '기계 판독용 전체 목록: ' + q('work/runtime_fix/runtime_ui_gap_audit.json'), '');

fs.writeFileSync('work/runtime_fix/runtime_ui_gap_audit.md', L.join('\n') + '\n', 'utf8');
console.log(JSON.stringify({ output: 'work/runtime_fix/runtime_ui_gap_audit.md', lines: L.length }, null, 2));
