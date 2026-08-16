# Arc Rise Fantasia (Japan) 한국어 패치

`RPJJ99` 일본판용 Riivolution 한국어 패치의 제작 소스, 번역 메모리, 빌드 도구 및 해시 결속 검증 자료입니다.

## 최종 배포본

- 파일: `outputs/Arc_Rise_Fantasia_Korean_Patch_v1.0.zip`
- SHA-256: `C23EBE6779B403B4A71AB849A86AF436D71E936CB3A6CD35975F39025A2889BC`
- 원본 RVZ SHA-256: `4671E3E74EB664E441FA927FF6BE9FC06B7D4860782BC4CECCF7DBBB4108AAC5`
- 오버레이 파일: 684개(XML 포함, 게임 교체 파일 683개)
- 전달 방식: 원본 RVZ를 수정하지 않는 Riivolution/Dolphin 오버레이

대용량 ZIP과 원본·추출 게임 데이터는 Git에 넣지 않습니다. GitHub Release에는 ZIP과 체크섬을 첨부하고, 저장소에는 체크섬과 `release_metadata/`의 manifest/provenance를 기록합니다.

## 이번 수정 내용

### 전투 번역 보강

실제 전투 데이터가 들어 있는 `Btl/btl_enemy.vld`와 `Btl/btl_usual.vol`을 별도로 분석·재구성했습니다.

- 몬스터 표시명: 270개
- 보스 부위명: 3개
- 몬스터 기술명: 563회
- 고유 몬스터 기술명: 209개
- 허용된 문자열 영역 밖 변경: 0바이트

번역·교정·윤문·용어 통일에는 Codex 내부 모델만 사용했으며 외부 번역 API나 외부 생성 모델은 사용하지 않았습니다.

### 고정 길이 테이블 손상 수정

문자열 슬롯을 실제보다 크게 선언하여 후속 메타데이터를 0으로 덮던 문제를 수정했습니다.

- `item.description_secondary`: 82 → 81
- `shop.name`: 21 → 20
- `special.description`: 84 → 83
- `help.description`: 325 → 322
- `monster_book.name`: 36 → 35

수정 전에는 5개 테이블에서 메타데이터 1,231바이트가 훼손됐고 `item.bin`의 ID가 중복됐습니다. 원본에서 다시 빌드한 뒤 item ID 772개가 모두 유일하고 보호 메타데이터 변경이 0임을 확인했습니다.

### 와이번 영상 정지 수정

정지 원인은 Dolphin 설정이 아니라 재인코딩된 `Movie/RAY_OP_02.sfd`였습니다.

- 원본 영상: 프레임 타임스탬프 역행 0회
- 폐기한 재인코딩 영상: 타임스탬프 역행 143회, 중복 타임스탬프 97회
- 사용자 정지 화면은 재인코딩 영상의 48.5초 프레임과 일치

릴리스에서는 해당 영상 오버레이를 완전히 제거하여 일본판 디스크의 원본 SFD를 그대로 읽습니다. 안정성을 위해 오프닝의 게임 제목 한 줄은 일본어로 남습니다.

## 최종 런타임 검증

동일한 Dolphin 프로세스를 유지한 한 번의 연속 실행에서 다음을 확인했습니다.

1. 한국어 타이틀 진입
2. 와이번을 대검으로 올려치는 기존 정지 지점을 건너뛰지 않고 통과
3. 첫 전투 몬스터명 `와이번` 한국어 표시
4. 적 기술명 `와이번: 치명타` 한국어 표시
5. 전투 프레임 계속 진행 및 프로세스 정상 응답
6. `stdout`/`stderr` 오류 0바이트

검증 설정은 Vulkan, MMU 끔, Fast Disc Speed 끔입니다. 최종 통합 보고서는 `work/validation/battle_update_final_verification.json`이며 35/35 항목을 통과했습니다.

## 릴리스 생성

```powershell
python work/research/build_final_release.py `
  --root . `
  --staging work/final_runtime_staging/riivolution_sd `
  --staging-manifest work/final_runtime_staging/staging_manifest.json `
  --outputs outputs
```