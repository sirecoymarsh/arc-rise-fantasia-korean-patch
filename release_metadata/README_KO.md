# 아크 라이즈 판타지아 한국어 패치 v1.0

## 대상

- 게임 ID: `RPJJ99`
- 일본판 원본 RVZ SHA-256: `4671E3E74EB664E441FA927FF6BE9FC06B7D4860782BC4CECCF7DBBB4108AAC5`
- 일본어 음성 유지
- 원본 RVZ는 수정하지 않는 Riivolution/Dolphin 오버레이 방식

## 설치

1. Dolphin을 종료합니다.
2. PowerShell에서 다음을 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-ARF-KO.ps1 `
  -SourceRvz 'D:\Games\Arc Rise Fantasia (Japan).rvz' `
  -TargetRoot 'D:\DolphinUser\Load'
```

`TargetRoot`에는 Riivolution SD 구조를 둘 폴더를 지정합니다. 설치기는 패키지와
원본 해시를 확인한 뒤 `riivolution` 및 `arc_rise_fantasia_ko` 폴더를 복사합니다.

## 복원

```powershell
powershell -ExecutionPolicy Bypass -File .\Restore-ARF-KO.ps1
```

설치 전에 같은 경로에 있던 파일은 외부 백업에서 복구되고, 새로 추가된 파일은
제거됩니다. 설치 상태는 `%LOCALAPPDATA%\ArcRiseFantasiaKO`에 기록됩니다.

## 무결성 확인

```powershell
powershell -ExecutionPolicy Bypass -File .\Verify-ARF-KO.ps1
```

번역·교정·윤문·용어 통일에는 Codex 내부 모델만 사용했습니다. 외부 번역
서비스나 외부 생성 모델은 사용하지 않았습니다.
