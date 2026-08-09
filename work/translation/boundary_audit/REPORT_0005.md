# 시스템 테이블 경계 이상 감사 — 번역 배치 0005

## 범위와 정책

- 대상: 승인 `batch_0005.jsonl`에 속한 `unmatched_system_units` 28건
- 번역·축약 판단: **Codex 내부 모델만 사용**
- 외부 번역 모델/API: **사용하지 않음**
- 기존 reviewed 배치 및 `translation_memory_draft.json`: **수정하지 않음**
- 전체 결과: `batch_0005.json`

## 검증 방법

1. 각 TM의 `occurrence_id`를 `work/catalog/text_v2/text_catalog.json`에서 역참조했다.
2. scanner의 `[offset, offset + byte_length)`와 같은 스키마의 구조화 table field 범위를 비교했다.
3. **정확히 한 field와 offset 범위가 겹친 경우만** 연결했다. substring 일치는 확정 근거로 사용하지 않았다.
4. scanner 및 field raw slice를 원시 payload에서 다시 읽고, payload 전체 SHA-256도 table catalog 값과 대조했다.
5. 가짜 구조 접두부는 번역에서도 제거하고, 실제 원문 선두가 누락된 건은 구조화 원문을 기준으로 뜻을 복구했다.
6. 현행 canonical codebook으로 인코딩한 뒤 NUL 종단 1바이트를 예약한 `capacity - 1`과 비교했다.

## 결과

| 항목 | 수량 |
|---|---:|
| 감사한 TM | 28 |
| 정확히 해결 | 28 |
| 정확히 연결된 table unit | 28 |
| scanner 구조 접두부 혼입 | 27 |
| 실제 필드 선두 누락 | 1 |
| ambiguous | 0 |
| unmatched | 0 |
| overflow | 0 |
| 인코딩 오류 | 0 |
| 코드북·NUL 포함 capacity 적합 | 28 |

검증에 사용한 canonical codebook은 746자를 배정한 파일이며 SHA-256은 `284CA42BE7F27AB8861593B1D9B72399903DCC006876C405A58624973818A313`이다.

## 실제 선두 누락 1건

- TM: `ARF-TM-26154CC088EA9858A295`
- scanner 원문/offset: `防具９` / `0x872E`
- 구조화 field: `ability:237:name` / `0x872A`
- 실제 원문: `属性防具９`
- 누락 raw: `C2B0C0AD` = `属性`
- 정리 번역: `속성 방어구 9`
- capacity: 21바이트, NUL 제외 최대 20바이트
- 인코딩 길이: 13바이트 — 적합

## 구조 접두부 혼입 대표 사례

- `help:36:title`: scanner `0x30CB`, 실제 field `0x30CC`; `01`이 `<$01>`로 잘못 붙었다.
- `help:270:title`: scanner `0x16DF6`, 실제 field `0x16DFA`; `0FB9C820`이 `<$0F>紅 `로 잘못 붙었다.
- `chat:161:title`: scanner `0x7252`, 실제 field `0x7254`; `0110`이 `<$01><$10>`으로 잘못 붙었다.
- `chat:327:title`: scanner `0x8EDB`, 실제 field `0x8EDC`; `37`이 `7`로 잘못 붙었다.

28건 전체의 table unit ID, clean source/translation, raw offsets와 hex, 겹친 바이트 수, payload 경로·SHA 검증, encoded hex와 capacity 판정은 JSON에 기록했다.

## 별도 조치 목록

### Ambiguous

- 없음. 향후 발생하면 구조 증거가 추가될 때까지 반영 대상에서 제외한다.

### Unmatched

- 없음. 향후 발생하면 substring으로 추정 확정하지 않고 정확한 포맷/offset을 추가 조사한다.

### Overflow

- 없음. 28건 모두 NUL을 포함한 field capacity 안에 들어간다.
- 향후 고정 field overflow는 의미 보존 축약안을 재승인하거나 별도 검증된 resizable 경로를 사용한다.

### Encoding error

- 없음. 향후 발생하면 canonical codebook과 글꼴 아틀라스를 확장·재렌더링한 뒤 재검증한다.
