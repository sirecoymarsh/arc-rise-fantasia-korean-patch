# 시스템 테이블 경계 이상 감사 — 번역 배치 0007

## 범위와 정책

- 대상: 독립 검수 완료 `batch_0007.jsonl`의 fit unmatched 29건
- 사전 substring 분석: 단일 후보 27건, 복수 후보 2건
- substring 후보는 참고만 했으며 **확정 근거로 사용하지 않음**
- 번역·축약 판단: **Codex 내부 모델만 사용**
- 외부 번역 모델/API: **사용하지 않음**
- reviewed 배치 및 생산 TM: 감사 중 읽기 전용, 수정하지 않음
- 전체 결과: `batch_0007.json`

## 엄격 검증 절차

1. TM의 모든 `occurrence_id`를 `text_v2/text_catalog.json`에서 역참조했다.
2. scanner `[offset, offset + byte_length)`와 동일 스키마 table field의 실제 바이트 범위를 비교했다.
3. 범위가 **정확히 한 field와 겹친 경우만** table unit을 확정했다.
4. scanner/field raw slice를 원시 payload에서 다시 읽고 payload 전체 SHA-256도 table catalog와 대조했다.
5. 구조 바이트 혼입과 실제 원문 선두 누락을 구분하고 clean source/translation을 결정했다.
6. batch 0007 append-only 임시 코드북으로 인코딩한 뒤 NUL 포함 `required_with_nul <= capacity`를 검사했다.

## 결과

| 항목 | 수량 |
|---|---:|
| 감사한 TM | 29 |
| 정확히 해결 | 29 |
| 정확히 연결된 table unit | 29 |
| scanner 구조 접두부 혼입 | 28 |
| 실제 field 선두 누락 | 1 |
| ambiguous | 0 |
| unmatched | 0 |
| overflow | 0 |
| 인코딩 오류 | 0 |
| 코드북·NUL 포함 capacity 적합 | 29 |

## 실제 선두 누락 1건

- TM: `ARF-TM-3F5CF01DF2981D97DA7A`
- scanner: `召術師範`, offset `0x5F42`
- 구조화 field: `chat:50:title`, offset `0x5F40`
- 실제 원문: `光召術師範`
- 누락 raw: `B8F7` = `光`
- clean 번역: `광소술 사범`
- capacity: 43바이트, 인코딩 11바이트 + NUL 1바이트 — 적합

승인 번역은 손실된 `光`의 의미를 이미 `광소술`로 복구하고 있었다.

## 복수 substring 후보 2건의 offset 판정

| TM | substring 후보 | exact offset으로 확정 |
|---|---|---|
| `ARF-TM-422E6D2B4497B51D9B8E` | `help:146:title`=`生命の奇跡`, `help:156:title`=`生命` | scanner `0xC5E4`가 field `0xC5E6`과 겹쳐 `help:146:title` 확정 |
| `ARF-TM-483B4FAEF7494ED5A3A7` | `help:11:title`=`ＤＥＦ`, `help:122:title`=`ＤＥＦストック` | scanner `0xA55C`가 field `0xA55E`과 겹쳐 `help:122:title` 확정 |

문자열 포함 관계만으로 짧은 후보를 선택하지 않았으며, 두 건 모두 raw 범위가 한 field에만 정확히 겹쳤다.

## 구조 접두부 혼입 대표 사례

- `help:195:title`: scanner `0x1084F`, 실제 field `0x10851`; `7F08`이 `<$7F><$08>`로 붙었다.
- `chat:139:title`: scanner `0x6E8A`, 실제 field `0x6E8C`; `011B`가 `<$01><$1B>`로 붙었다.
- `magic:22:menu_name`: scanner `0xE17`, 실제 field `0xE18`; `3A`가 `:`로 붙었다.
- `dragon:3:name`: scanner `0x344`, 실제 field `0x345`; `01`이 `<$01>`로 붙었다.

29건 전체의 exact table unit, clean source/translation, raw offset·hex, payload hash, encoded hex와 NUL 포함 capacity 판정은 JSON에 기록했다.

## 코드북 검증

- 이전 batch 0006 코드북: 768자, SHA-256 `33A628293AE061B8A7BB075DF8FB03A869A41B706B9AE6C921E7963772272F5B`
- batch 0007 임시 코드북: 784자, SHA-256 `C2B3EFD964B88FB58B166AEE72EC655DCBBE0E6245A7B69AFFA22F96EF55851A`
- 새 글자 16자 append-only 추가
- 기존 768자 mapping 전부 불변

## 별도 조치 목록

- **Ambiguous:** 없음. 발생 시 raw 구조 증거 확보 전까지 반영 제외.
- **Unmatched:** 없음. substring만으로 추정하지 말고 포맷/offset 추가 조사.
- **Overflow:** 없음. 발생 시 의미 보존 축약 재승인 또는 검증된 resizable 경로 사용.
- **Encoding error:** 없음. 발생 시 append-only 코드북 확장과 글꼴 재렌더링 후 재검증.
