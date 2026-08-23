# Arc Rise Fantasia (Japan) 한국어 패치

`RPJJ99` 일본판용 한국어 패치의 제작 소스, 번역 메모리, 빌드 도구 및 해시 결속 검증 자료입니다.

## 최신 배포본 v1.1.0 — 원클릭 ROM 패처

- 파일: `ArcRiseFantasia-Korean-ROM-Patcher-v1.1.0.zip`
- SHA-256: `A85B9F110EC72B3993F8092DCE9A15E31445BA2D4AC7C7677D66F122F115DC2A`
- 입력: 일본판 `RPJJ99` 원본 RVZ 또는 ISO
- 출력: 한국어가 내장된 별도의 RVZ 또는 ISO
- 델타 항목: 722개(게임 파일 721개 + `main.dol` 1개)
- 패치 매니페스트 SHA-256: `7CAEED6D8B6B7CAC0EE4C85AB9282154F4944F2A2A4C293818B5F2B62C6B09C2`
- 완전한 원본·패치 게임 이미지 포함: 없음

### 사용법

1. ZIP 파일의 압축을 완전히 풉니다.
2. `ArcRiseFantasiaKoreanRomPatcher.exe`를 더블클릭합니다.
3. 일본판 `RPJJ99` 원본 `.rvz` 또는 `.iso`를 선택합니다.
4. 한국어판을 저장할 위치와 RVZ/ISO 형식을 선택합니다.
5. **한국어판 만들기**를 누릅니다.

원본은 수정하지 않으며 출력 게임 ID도 `RPJJ99`로 유지되므로 기존 세이브를 그대로 사용합니다. 만들어진 파일은 Dolphin/Riivolution 패치 없이 바로 실행할 수 있습니다. ISO 출력은 사용하는 실기용 USB 로더의 방식에 맞춰 넣을 수 있습니다.

### v1.1.0 검증

- 원본 RVZ → 한국어 ISO: 성공, 722/722 출력 파일 해시 일치
- 원본 ISO → 한국어 RVZ: 성공, 722/722 출력 파일 해시 일치
- 한국어 RVZ 독립 Dolphin 부팅: 성공, 비정상 메모리 접근 로그 0건
- 최종 ZIP CRC·압축 해제·738개 파일 해시: 전부 일치
- 압축 해제본 GUI 실행: 성공
- Microsoft Defender 최종 EXE·스테이징·ZIP·압축 해제본 검사: 신규 탐지 0건

검증 자료는 `release_metadata/rom_patcher_v1.1.0/`에 있습니다.

## 이전 배포본 v1.0.5 — Riivolution 오버레이

- 파일: `outputs/Arc_Rise_Fantasia_Korean_Patch_v1.0.5.zip`
- SHA-256: `34A7681AC2DDAFC3EFB5CD13D85F922B7E2C2D5A8879187D655A221A2CAC3B0E`
- 원본 RVZ SHA-256: `4671E3E74EB664E441FA927FF6BE9FC06B7D4860782BC4CECCF7DBBB4108AAC5`
- 오버레이 파일: 722개(XML 포함, 게임 교체 파일 721개)
- 전달 방식: 원본 RVZ를 수정하지 않는 Riivolution/Dolphin 오버레이

대용량 ZIP과 원본·추출 게임 데이터는 Git에 넣지 않습니다. GitHub Release에는 ZIP과 체크섬을 첨부하고, 저장소에는 체크섬과 `release_metadata/`의 manifest/provenance를 기록합니다.

### v1.0.5 원클릭 설치

1. ZIP 파일의 압축을 완전히 풉니다.
2. Dolphin을 종료합니다.
3. `설치하기.cmd`를 더블클릭합니다.
4. Dolphin에서 게임을 우클릭하고 **Riivolution 패치로 시작**을 선택한 뒤 한국어 패치를 켭니다.

설치기는 Dolphin 사용자 폴더를 자동으로 찾고, 찾지 못한 경우에만 폴더 선택창을 표시합니다. PowerShell 명령이나 원본 RVZ 경로 입력은 필요하지 않습니다. 지속적인 백업·복원 상태를 만들지 않으며 우리 패치 전용 폴더와 XML만 설치·업데이트합니다.

직접 설치하려면 `payload\riivolution_sd` **안의** 두 폴더를 Dolphin 사용자 폴더의 `Load`에 복사합니다. `riivolution_sd` 폴더 자체를 복사하면 안 됩니다.

## 번역 및 구조 수정

- 전투 몬스터 기본 표시명: 270개
- 전투 몬스터 보조 표시명: 87회
- 보스 부위명: 3개
- 몬스터 기술명: 672회(고유 기술명 226개)
- 추가 어빌리티명: 14개
- 추가 채팅 제목: 15개
- 추가 상점명: 1개
- 그림형 UI: 68장, 155개 표기(메뉴·지도·무기 커스터마이즈·상점·퀘스트·몬스터 도감 등)
- 마을·필드 지도 아이콘 범례: 15개(세이브 포인트·보물·상점·시설·현재 위치 등)
- 특수·보스 기술명: 80회(고유 79종, 와이번의 `버스트 사격` 포함)
- 자동 이동 지도 지역 설명: 36곳(DAT/TXT 72개 표시 데이터)
- 전투 그림형 UI: 12장, 19개 표기(명령·작전·상태·도주·선제공격·기습·연계·오의·약점·내성 등)
- 3인 이상 대화 수신자 재검수: 후보 128회, 고유 대사 127개 교정
- 첫 장면 말투의 후속 장면 고정 전이 및 타 인물 전염: 3개 교정
- 무관한 문장 의미가 복사된 오역: 1개 교정(총 고유 교정 131개)
- 고정 길이 테이블 보호영역 변경: 0바이트
- `item.bin` ID: 772개 모두 유일

번역·교정·윤문·용어 통일에는 Codex 내부 모델만 사용했으며 외부 번역 API나 외부 생성 모델은 사용하지 않았습니다.

## 와이번 영상 정지 수정

정지 원인은 Dolphin 설정이 아니라 재인코딩된 `Movie/RAY_OP_02.sfd`였습니다. 릴리스에서는 해당 영상 오버레이를 제거하여 일본판 디스크의 원본 SFD를 그대로 읽습니다. 안정성을 위해 오프닝의 게임 제목 한 줄은 일본어로 남습니다.

## v1.0.5 검증

- 원클릭 신규 설치: 통과
- 동일 패치 재설치 및 다른 Riivolution XML 보존: 통과
- 변조된 패키지의 대상 쓰기 전 거부: 통과
- 설치 결과 722개 오버레이 파일의 매니페스트 해시 일치: 통과
- ZIP CRC·파일 집합·스테이징 트리 일치: 통과
- 최종 릴리스 검증 오류: 0건
- 수신자·장면 말투 교정 131개가 쓰이는 358개 위치를 최종 Event/Map 120개 파일에서 독립 재추출: 전부 일치
- v1.0.5: 3인 이상 대화 수신자·관계 재판정 및 장면 간 고정 말투 전이 교정
- 추가 장시간 실행·전투 전수 확인은 사용자 요청 시 진행

## 릴리스 생성

```powershell
python work/research/build_final_release.py `
  --root . `
  --staging work/final_runtime_staging/riivolution_sd `
  --staging-manifest work/final_runtime_staging/staging_manifest.json `
  --outputs outputs
```
