# 시스템 테이블 경계 이상 감사 — 번역 배치 0006

## 범위와 정책

- 대상: 독립 검수 완료 `batch_0006.jsonl`의 구조 카탈로그 unmatched 37건
- 전체 fit과 batch-only 임시 fit의 unmatched ID 집합: **37건 모두 동일**
- 번역·축약 판단: **Codex 내부 모델만 사용**
- 외부 번역 모델/API: **사용하지 않음**
- reviewed 배치와 생산 `translation_memory_draft.json`: 감사 중 **읽기 전용**, 수정하지 않음
- 전체 결과: `batch_0006.json`

## 검증 방법

1. 각 TM의 모든 `occurrence_id`를 `text_v2/text_catalog.json`에서 역참조했다.
2. scanner의 `[offset, offset + byte_length)`와 동일 스키마의 구조화 table field 범위를 비교했다.
3. 범위가 **정확히 한 field와 겹치는 경우만** 연결했다. substring 유사성만으로는 확정하지 않았다.
4. scanner와 field raw slice를 원시 payload에서 재독출하고 payload 전체 SHA-256도 table catalog와 대조했다.
5. 실제 필드 앞 구조 바이트 혼입과 실제 원문 선두 누락을 구분했다.
6. 정리된 번역을 batch 0006 append-only 코드북으로 인코딩하고, NUL 1바이트를 포함한 `required_with_nul <= capacity`를 검사했다.

## 코드북 및 fit 입력 검증

- 이전 코드북: 746자, SHA-256 `284CA42BE7F27AB8861593B1D9B72399903DCC006876C405A58624973818A313`
- batch 0006 코드북: 768자, SHA-256 `33A628293AE061B8A7BB075DF8FB03A869A41B706B9AE6C921E7963772272F5B`
- 새 글자: 22자 append-only 추가
- 기존 746자 byte/code 위치: 전부 불변
- 검수용 임시 코드북과 현행 canonical 코드북: byte-identical
- 전체 fit SHA-256: `83163FAD06583AE8B7FF942D1476545B5A91C6F3FB24A0E1EF5568F2F61F352C`
- batch-only fit SHA-256: `F1B0FE860F6FC255D123297F46861C151E171E06A5557431DB0E7889509FECB7`

## 결과

| 항목 | 수량 |
|---|---:|
| 감사한 TM | 37 |
| 정확히 해결 | 37 |
| 정확히 연결된 table unit | 37 |
| scanner 구조 접두부 혼입 | 33 |
| 실제 필드 선두 누락 | 4 |
| ambiguous | 0 |
| unmatched | 0 |
| overflow | 0 |
| 인코딩 오류 | 0 |
| 코드북·NUL 포함 capacity 적합 | 37 |

## 실제 선두 누락 4건

| TM | scanner 원문 | 구조화 원문 | 정리 번역 | raw/offset 근거 |
|---|---|---|---|---|
| `ARF-TM-33A74C2E25B95348E3D1` | `身具用１` | `装身具用１` | `장신구용 1` | `ability:242:name` `0x8A04`; scanner `0x8A06`; 누락 `C1F5`=`装` |
| `ARF-TM-3763C62816EC1EED56DA` | `身具用８` | `装身具用８` | `장신구용 8` | `ability:249:name` `0x8E02`; scanner `0x8E04`; 누락 `C1F5`=`装` |
| `ARF-TM-3A150DC3799C616082D6` | `らないリフィア` | `わからないリフィア` | `이해하지 못하는 리피아` | `chat:76:title` `0x63B8`; scanner `0x63BC`; 누락 `A4EFA4AB`=`わか` |
| `ARF-TM-3CFB213E3A0103861239` | `の間` | `束の間` | `한순간` | `chat:289:title` `0x8854`; scanner `0x8856`; 누락 `C2AB`=`束` |

앞의 두 승인 번역은 이미 누락 의미를 복구하고 있었다. 뒤의 두 건은 손상된 scanner 원문에 맞춰 불완전하게 번역되어 있어 구조화 원문 전체 의미로 정리했다.

## 구조 접두부 혼입 대표 사례

- `help:40:title`: scanner `0x3637`, 실제 field `0x3638`; `01`이 `<$01>`로 붙었다.
- `help:362:title`: scanner `0x1EAAA`, 실제 field `0x1EAAE`; `4D366820`이 `M6h `로 붙었다.
- `chat:148:title`: scanner `0x7016`, 실제 field `0x7018`; `0119`가 `<$01><$19>`로 붙었다.
- `magic:37:menu_name`: scanner `0x17B3`, 실제 field `0x17B4`; `47`이 `G`로 붙었다.

37건 전체의 table unit ID, clean source/translation, raw offsets·hex, 겹친 바이트 수, payload SHA 검증, encoded hex와 NUL 포함 capacity 판정은 JSON에 기록했다.

## 별도 조치 목록

- **Ambiguous:** 없음. 발생 시 raw 구조 증거가 확보될 때까지 반영 제외.
- **Unmatched:** 없음. substring만으로 추정 확정하지 않고 포맷/offset 추가 조사.
- **Overflow:** 없음. 발생 시 의미 보존 축약을 재승인하거나 검증된 resizable 경로만 사용.
- **Encoding error:** 없음. 발생 시 append-only 코드북 확장과 글꼴 재렌더링 후 재검증.
