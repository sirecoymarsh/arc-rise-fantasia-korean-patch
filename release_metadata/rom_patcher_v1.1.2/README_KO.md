# v1.1.2 원클릭 ROM 패처 검증 자료

- `PATCH_MANIFEST.json`: 722개 VCDIFF 항목, 원본/출력 해시, 런타임 패치 계약
- `RELEASE_MANIFEST.json`: 최종 배포 스테이징 736개 매니페스트 대상 파일
- `BATTLE_FIELD_PLACEHOLDER_PATCH.json`: `btl_usual.vol`의 잔류 문자열 `名称未設定`을 `이름 미설정`으로 바꾼 바이트 제한 증거
- `ALL_BATTLE_TEXT_DUPLICATE_AUDIT.json`: 일반 전투, 적 DB, 특수·보스 기술, 전투 튜토리얼, `main.dol`, 전투 그림 UI의 중복 문자열 전수 검사
- `TARGETED_BATTLE_PROOF.json`: `레이 스톤`과 `이름 미설정`이 최종 이미지에 포함된 증거
- `VALIDATION.json`: 722/722 독립 출력 해시 검사, 독립 부팅, ZIP 추출, GUI 실행, Defender 검사 결과
- `ArcRiseFantasia-Korean-ROM-Patcher-v1.1.2.zip.sha256`: GitHub Release 첨부 ZIP 체크섬

릴리스에는 완전한 원본 또는 패치 게임 이미지가 없으며 VCDIFF 델타만 포함됩니다. 의미 번역·교정은 Codex 내부 모델만 사용했습니다. 전투 텍스트 중복 전수 검사에서 확인한 잔류 일본어는 0건이며 실제 표시 화면은 수동 검증 항목으로 별도 유지합니다.
