# 시스템 테이블 경계 이상 감사 — 번역 배치 0008

## 범위와 정책

- 대상: 독립 검수 완료 `batch_0008.jsonl`의 fit unmatched 34건
- 사전 substring 분석: 단일 후보 28건, 복수 후보 6건, 후보 없음 0건
- substring 후보는 참고만 했으며 **확정 근거로 사용하지 않음**
- 번역·교정 판단: **Codex 내부 모델만 사용**
- 외부 번역 모델/API: **사용하지 않음**
- reviewed 배치, 생산 TM, canonical 감사·코드북, 글꼴 및 table payload: 감사 중 읽기 전용, 수정하지 않음
- fit용 TM은 원본 base TM과 reviewed `batch_0008`만 임시 병합했으며 승인 단위는 200건
- 전체 결과: `batch_0008.json` (SHA-256 `19CEF06A3A04E3E74F6023D3C0D1528D7A6F916B7FB36C0C3BD6F7E1B4C7B511`)

## 엄격 검증 절차

1. 원본 TM의 모든 `occurrence_id`를 `text_v2/text_catalog.json`에서 역참조했다.
2. 각 logical locator에서 scanner `[offset, offset + byte_length)`와 동일 스키마 table field의 실제 byte span을 비교했다.
3. byte span이 **정확히 한 field와 겹친 경우만** table unit을 확정했다.
4. scanner/field raw slice를 원시 logical payload에서 다시 읽고, payload 전체 SHA-256을 text/table catalog 양쪽과 대조했다.
5. 구조 바이트 혼입과 실제 원문 선두 누락을 구분해 clean source/translation을 결정했다.
6. canonical v1 코드북을 `--existing`으로 append-only 확장한 임시 코드북으로 인코딩하고, NUL 포함 `required_with_nul <= capacity`를 검사했다.

## 결과

| 항목 | 수량 |
|---|---:|
| 감사한 TM | 34 |
| 정확히 해결 | 34 |
| 정확히 연결된 table unit | 34 |
| scanner 구조 접두부 혼입 | 31 |
| 실제 field 선두 누락 | 3 |
| clean 번역 변경 | 33 |
| ambiguous | 0 |
| unmatched | 0 |
| 감사 대상 overflow | 0 |
| 감사 대상 인코딩 오류 | 0 |
| 코드북·NUL 포함 capacity 적합 | 34 |

## 실제 선두 누락 3건

| TM | scanner/table offset | 누락 raw | 실제 원문 | clean 번역 |
|---|---|---|---|---|
| `ARF-TM-4CEE86567F1584CCB58E` | `0x6230` / `0x622C` | `A2A8A5AB` | `※カット　異国と故郷` | `※컷　타국과 고향` |
| `ARF-TM-4F755F9D2088CA02F818` | `0x630A` / `0x6308` | `B2F8` | `怪しいサージュ` | `수상한 사쥬` |
| `ARF-TM-52E38F3E0B5BCDA356D8` | `0x8C4E` / `0x8C4C` | `C1F5` | `装身具用５` | `장신구용 5` |

- `ARF-TM-4CEE86567F1584CCB58E`: scanner가 `※カ`를 잃어 `ット　異国と故郷`만 잡았다. clean 번역에서 `※컷` 의미를 복구했다.
- `ARF-TM-4F755F9D2088CA02F818`: 누락된 `怪` 때문에 초안이 `優しい`로 오판해 `다정한 사쥬`가 되었으나, raw field는 `怪しいサージュ`이므로 `수상한 사쥬`로 교정했다.
- `ARF-TM-52E38F3E0B5BCDA356D8`: 누락된 `装`의 의미는 승인 번역 `장신구용 5`에 이미 복구되어 있어 번역을 유지했다.

## 복수 substring 후보 6건의 offset 판정

| TM | 후보 수 | scanner offset | exact offset으로 확정 |
|---|---:|---:|---|
| `ARF-TM-4CF742B143200032C66C` | 2 | `0x14ECC` | `help:247:title` (`0x14ECD`) |
| `ARF-TM-4E7DFED11D34F0CC420B` | 2 | `0xEFE9` | `help:177:title` (`0xEFEB`) |
| `ARF-TM-4F23EAAE873BD8879739` | 2 | `0x72AB` | `chat:163:title` (`0x72AC`) |
| `ARF-TM-53017BCD4F3A7D930A47` | 2 | `0x15849` | `help:254:title` (`0x1584A`) |
| `ARF-TM-537E1D6FF3CE94F54EF4` | 2 | `0x115DD` | `help:205:title` (`0x115DF`) |
| `ARF-TM-54DF616263FF3DDB03E3` | 2 | `0xAAC8` | `help:126:title` (`0xAACA`) |


문자열 포함 관계만으로 짧은 후보를 선택하지 않았으며, 6건 모두 scanner raw 범위가 정확히 한 field와 겹친 결과만 채택했다.

## 구조 접두부 혼입 대표 사례

- `chat:83:title`: scanner `0x64EB`, field `0x64EC`; 구조 raw `24`가 `$アデールはどこに？`의 선두로 붙었다.
- `help:366:title`: scanner `0x1F016`, field `0x1F01A`; 구조 raw `5C784420`가 `\xD マシュガル`의 선두로 붙었다.
- `help:280:title`: scanner `0x17B84`, field `0x17B88`; 구조 raw `5C2E0C20`가 `\.<$0C> 裏ギルド`의 선두로 붙었다.
- `help:308:title`: scanner `0x1A178`, field `0x1A17C`; 구조 raw `0F6A7C20`가 `<$0F>j| トパジオン`의 선두로 붙었다.


34건 전체의 exact table unit, clean source/translation, raw offset·hex, logical payload SHA-256, encoded hex와 NUL 포함 capacity 판정은 JSON에 기록했다.

## 코드북 검증

- canonical v1 코드북: 784자, SHA-256 `C2B3EFD964B88FB58B166AEE72EC655DCBBE0E6245A7B69AFFA22F96EF55851A`
- batch 0008 임시 코드북: 805자, SHA-256 `095D664326A3DFC14A167679CE1D2839C073DC2A7D0F5AD58104D8BBC44D9853`
- 새 한글 21자 append-only 추가
- 기존 784자 mapping 전부 불변
- 원문 보존 예약 pair 2,227개 유지

## 경계 감사 범위 밖 초기 fit 발견 사항

초기 fit에서 exact source로 이미 매칭된 별도 항목 중 고정 field overflow 7건, resizable in-place overflow 3건, `·` 인코딩 오류 3건이 있었다. 이들은 34개 boundary-unmatched 감사 대상이 아니며, 본 감사에서는 reviewed 번역이나 payload를 수정하지 않았다. 상세 ID는 JSON의 `out_of_boundary_scope_fit_findings`와 `batch_0008_fit_only.json`에 남겼다.

## 별도 조치 목록

- **Ambiguous:** 없음. 발생 시 raw 구조 증거 확보 전까지 반영 제외.
- **Unmatched:** 없음. substring만으로 추정하지 말고 포맷/offset 추가 조사.
- **Boundary overflow:** 없음. 발생 시 의미 보존 축약 재승인 또는 검증된 resizable 경로 사용.
- **Boundary encoding error:** 없음. 발생 시 append-only 코드북 확장과 글꼴 재렌더링 후 재검증.
