# v1.1.2 원클릭 ROM 패처 검증 자료

- `PATCH_MANIFEST.json`: 722개 VCDIFF 항목, 원본/출력 해시, 런타임 패치 계약
- `RELEASE_MANIFEST.json`: 최종 배포 스테이징 736개 매니페스트 대상 파일
- `BATTLE_FIELD_PLACEHOLDER_PATCH.json`: `btl_usual.vol`의 잔류 문자열 `名称未設定`을 `이름 미설정`으로 바꾼 바이트 제한 증거
- `ALL_BATTLE_TEXT_DUPLICATE_AUDIT.json`: 일반 전투, 적 DB, 특수·보스 기술, 전투 튜토리얼, `main.dol`, 전투 그림 UI의 중복 문자열 전수 검사
- `TARGETED_BATTLE_PROOF.json`: `레이 스톤`과 `이름 미설정`이 최종 이미지에 포함된 증거
- `SFD_DIALOGUE_CLOSURE.json`: 21개 SFD 음성 전수 분류와 `RAY_OP_02.sfd`의 한국어 엔진 자막 29개 결속 증거
- `UNTRANSLATED_COMPLETION_AUDIT.json`: 전체 텍스트·전투·지도·UI·영상 자막 표면의 최종 미번역 완료 감사
- `VALIDATION.json`: 722/722 독립 출력 해시 검사, 독립 부팅, ZIP 추출, GUI 실행, Defender 검사 결과
- `ArcRiseFantasia-Korean-ROM-Patcher-v1.1.2.zip.sha256`: GitHub Release 첨부 ZIP 체크섬

릴리스에는 완전한 원본 또는 패치 게임 이미지가 없으며 VCDIFF 델타만 포함됩니다. 의미 번역·교정은 Codex 내부 모델만 사용했습니다. 전투 텍스트 중복 전수 검사에서 확인한 잔류 일본어는 0건이며 실제 표시 화면은 수동 검증 항목으로 별도 유지합니다.

`RAY_OP_02.sfd`는 원본 영상과 일본어 음성을 유지하지만, 스토리 대사 구간은 활성 `Map/map_d_hnk_00.cxd`의 BSCR 29개가 한국어 자막으로 표시됩니다. 오프닝 제목 로고의 작은 일본어 부제 한 줄은 사용자 요청과 런타임 안정성 때문에 원본 그대로 유지합니다. 검토용 MP4는 게임 패치에 포함되지 않습니다.
