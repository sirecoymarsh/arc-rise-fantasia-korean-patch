# Arc Rise Fantasia 이미지 UI 한국어화 최종 보고서

## 결과

- 실제 수정 이미지: **48개**
- 재삽입 대상: **44개** (동일 타이틀 아카이브의 두 배치 경로 포함)
- 구조 검사: **48/48 PASS**
- 타이틀 RTDP 변경 엔트리: `[0, 1, 2, 3, 4, 5]` / 예상 `[0, 1, 2, 3, 4, 5]`
- 100% 재렌더 시각 확인: **PASS**
- 원본 RVZ 수정: **없음**
- 외부 번역/API/생성 모델 사용: **없음**

## 처리 범위

- `Sys/strapA_jp.wtm`, `Sys/strapB_jp.wtm`: 일본어 안전 문구 전체를 한국어로 교체.
- `Title/title.vol`, `Sys/title.vol`: PRESS ANY BUTTON, New Game 2상태, Continue 2상태, 로고 하단 일본어 부제를 한국어로 교체.
- `Sys/system.vol::0053:nowloading.wtm`: 두 상태의 Now Loading을 `불러오는 중…`으로 교체.
- `interface/tex_loc_title_*_wtm.cxd` 37개: 일본어 장소명을 프로젝트 고정 표기의 한국어로 교체하고 기존 영어 부제는 장식 요소로 유지.
- 카지노 소개 2개: 블랙잭/포커의 안내문, 조작 라벨, 상태 라벨 및 포커 족보를 한국어로 교체.

## 보존 사항

- 모든 WTMD의 캔버스, GX 형식, 팔레트 형식, 헤더와 팔레트 바이트를 유지했다.
- 팔레트 텍스처는 기존 팔레트 안에서만 재양자화했고 RGBA32 텍스처는 원래 타일 배열로 재인코드했다.
- 타이틀 VOL은 원본 크기·11개 엔트리·순서·정렬을 유지하며 엔트리 0~5만 변경했다.
- 장소명/카지노 CXD는 동일 크기의 WTMD leaf를 deterministic LZ10으로 다시 감쌌다.

## 제외 자산

- `interface/tex_casino_intro_race_wtm.cxd`: No Japanese text detected; race scene art only.
- `interface/tex_casino_intro_slot_wtm.cxd`: No Japanese text detected; slot symbols and English BET COIN label retained as art/UI convention.
- `Sys/criware.wtm`: CRIWARE middleware logo; no Japanese text and not a game-localization surface.
- `Hbm/homeBtnIcon.wtm`: Wii Home Button icon; symbolic art with no Japanese text.
- `Title/title.vol::title_flear.tpl`: Title flare/effect texture; no identified display text.
- `Title/title.vol::title.brres`: Title scene model/layout resources; baked labels are stored in the separately edited WTMD members.
- `Title/title.vol::light.brres`: Lighting effect resource; no display text.
- `Title/title.vol::rain.brres`: Rain effect resource; no display text.

## 산출물

- 원본 디코드: `work/image_ui_final/original/`
- 조판 PNG: `work/image_ui_final/edited/`
- 재인코드 payload: `work/image_ui_final/payloads/`
- 한국어 문자열 맵: `work/image_ui_final/korean_string_map.json`
- 재삽입 매니페스트: `work/image_ui_final/reinsertion_manifest.json`
- 구조 검사: `work/image_ui_final/reports/structural_validation.json`
- 100% 재렌더: `work/image_ui_final/reports/reencoded_render/`
- 콘택트시트: `work/image_ui_final/reports/contact_reencoded_100pct/`

## 남은 통합 단계

- `nowloading.wtm`은 다른 lane의 누적 `system.vol`에 엔트리 53으로 병합해야 한다.
- CXD는 압축 크기가 달라질 수 있으므로 최종 디스크 파일시스템 재구성 단계에서 교체한다.
- 실제 게임 런타임 확인은 이 lane에서 실행하지 않았다. 최종 통합 빌드에서 부팅 경고, 타이틀 상태 전환, 장소 입장, 카지노 안내, 로딩 화면을 확인해야 한다.
