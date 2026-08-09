# Arc Rise Fantasia (Japan) 한국어 패치

`RPJJ99`용 Riivolution 한국어 패치의 제작 소스, 번역 메모리, 빌드 도구와 해시 결속 보고서입니다.

## 최종 산출물

- 패치: `outputs/Arc_Rise_Fantasia_Korean_Patch_v1.0.zip`
- SHA-256: `D0A830B2A4DDE999A8D03F77191FBCD59FAA062B4B2F99467EBB023692213D33`
- 원본 RVZ 요구 SHA-256: `4671E3E74EB664E441FA927FF6BE9FC06B7D4860782BC4CECCF7DBBB4108AAC5`
- 오버레이 파일: 684개

512 MB 릴리스 ZIP과 원본/추출 게임 데이터는 Git에 넣지 않습니다. ZIP은 위 경로에 보존하며, Git에는 체크섬과 `release_metadata/`의 manifest/provenance를 기록합니다.

## 회귀 수정

고정 길이 문자열 슬롯을 실제보다 크게 선언해 후속 메타데이터를 0으로 덮던 문제를 수정했습니다.

- `item.description_secondary`: 82 → 81
- `shop.name`: 21 → 20
- `special.description`: 84 → 83
- `help.description`: 325 → 322
- `monster_book.name`: 36 → 35

수정 전에는 5개 테이블에서 메타데이터 1,231바이트가 훼손됐고, `item.bin`의 ID가 중복됐습니다. 원본에서 다시 빌드한 뒤 item ID 772개가 모두 유일하고 보호 메타데이터 변경이 0임을 확인했습니다.

## 런타임 결과

최종 전체 패치는 Dolphin에서 MMU를 켜지 않은 상태로 한국어 초기설정, 타이틀, 불러오기 및 본편 전투까지 진입했습니다. 기존 무한 재시작은 재현되지 않았습니다.

번역과 검토는 Codex 내부 모델만 사용했습니다.

## 릴리스 생성

```powershell
python work/research/build_final_release.py `
  --root . `
  --staging work/final_runtime_staging/riivolution_sd `
  --staging-manifest work/final_runtime_staging/staging_manifest.json `
  --outputs outputs
```

