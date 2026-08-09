# opening.bnr 한국어 현지화 보고서

- 대상: Arc Rise Fantasia (RPJJ99)
- 번역: Codex 내부 모델 판단만 사용
- 원본 추출물: 변경하지 않음
- 정적 검증: **PASS**

## 처리 내용

- 배너 `title_base.tpl`: `アークライズファンタジア`를 `아크 라이즈 판타지아`로 교체했다.
- 아이콘 `title.tpl`: 높이가 3~4픽셀뿐이라 한글을 넣지 않고 일본어 작은 부제만 제거했다.
- 영문 메인 로고, 애니메이션 BRLAN/BRLYT, 나머지 텍스처와 `sound.bin`은 그대로 보존했다.

## 산출물

- payload: `work/runtime_fix/opening_bnr_ko/payloads/opening.bnr`
- SHA-256: `63C06073023FE8AEA760AC8AB763A281E531355E1B12B883CF6F64D15D1BB778`
- 크기: 506,240 bytes (원본 505,696 bytes)
- 전후 비교: `work/runtime_fix/opening_bnr_ko/audit/opening_bnr_original_vs_korean.png`
- manifest: `work/runtime_fix/opening_bnr_ko/opening_bnr_korean_payload_manifest.json`

## 검증

- PASS — `source_sha256_anchor_valid`
- PASS — `source_baseline_unmodified`
- PASS — `deterministic_rebuild_byte_identical`
- PASS — `imet_header_byte_identical`
- PASS — `imet_md5_valid`
- PASS — `outer_u8_file_set_order_and_structure_preserved`
- PASS — `outer_u8_only_banner_and_icon_changed`
- PASS — `banner_inner_u8_only_title_base_changed`
- PASS — `icon_inner_u8_only_title_changed`
- PASS — `banner_inner_u8_offsets_and_sizes_preserved`
- PASS — `icon_inner_u8_offsets_and_sizes_preserved`
- PASS — `same_target_tpl_sizes_formats_and_geometry`
- PASS — `all_imd5_hashes_valid`
- PASS — `all_lz77_roundtrips_valid`
- PASS — `animation_layout_and_unrelated_textures_preserved`
- PASS — `sound_byte_identical`
- PASS — `sound_imd5_valid`
- PASS — `banner_pixel_diff_scoped_to_subtitle`
- PASS — `icon_pixel_diff_scoped_to_expected_blocks`

IMET 헤더/MD5, 양쪽 IMD5, LZ77 왕복, outer/inner U8 파일 집합과 노드 구조, TPL 크기·GX 포맷·캔버스를 모두 검증했다. 동일 입력을 두 번 빌드한 결과도 바이트 단위로 일치했다.
