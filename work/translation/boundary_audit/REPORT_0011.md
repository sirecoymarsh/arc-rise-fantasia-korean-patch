# 시스템 테이블 경계 이상 감사 — 번역 배치 0011

## 범위와 정책

- 대상: 독립 검수 완료 `batch_0011.jsonl`의 fit unmatched 33건
- 임시 병합: 생산 TM 1,400건 + batch 0011 검수본 200건 = 승인 1,600건
- 사전 substring 분석: 단일 후보 30건, 복수 후보 3건, 후보 없음 0건
- substring 후보는 참고만 했으며 **확정 근거로 사용하지 않음**
- 번역·교정 판단: **Codex 내부 모델만 사용**
- 외부 번역 모델/API: **사용하지 않음**
- reviewed 배치·생산 TM·canonical codebook·글꼴·payload: 감사 중 읽기 전용, 수정하지 않음
- 전체 결과: `batch_0011.json` (SHA-256 `E52E112E8C285A41D68DEF26D5454A90480FC36AC449CD019D9844474620D3D1`)

## 엄격 검증 절차

1. 생산 TM에 batch 0011 검수본을 읽기 전용 입력으로 임시 병합했다.
2. 승인 코퍼스로 canonical_v1 코드북을 append-only 임시 확장했다.
3. `check_translation_fit.py`와 `analyze_unmatched_fit.py`로 신규 unmatched 33건 전부를 산출했다.
4. TM의 모든 occurrence ID를 `text_v2/text_catalog.json`에서 역참조했다.
5. scanner `[offset, offset + byte_length)`와 같은 logical locator의 구조화 table field 실제 바이트 범위를 비교했다.
6. 범위가 **정확히 한 field와 겹친 경우만** table unit을 확정했다.
7. scanner/field raw slice를 원시 payload에서 다시 읽고 payload 전체 SHA-256도 table catalog 및 scanner leaf SHA와 대조했다.
8. 구조 바이트 혼입과 실제 원문 선두 누락을 구분하고 clean source/translation을 결정했다.
9. append-only 임시 코드북으로 인코딩한 뒤 NUL 포함 `required_with_nul <= capacity`를 검사했다.

## 결과

| 항목 | 수량 |
|---|---:|
| 감사한 TM | 33 |
| 정확히 해결 | 33 |
| 정확히 연결된 table unit | 33 |
| scanner 구조 접두부 혼입 | 31 |
| 실제 field 선두 누락 | 2 |
| ambiguous | 0 |
| unmatched | 0 |
| 감사 범위 내 overflow | 0 |
| 감사 범위 내 인코딩 오류 | 0 |
| 코드북·NUL 포함 capacity 적합 | 33 |

## 실제 선두 누락 2건

| TM | scanner 원문 | 구조화 field 원문 | scanner / field offset | 누락 raw | clean 번역 |
|---|---|---|---|---|---|
| `ARF-TM-72828725BCE29713BB66` | `防具１３` | `属性防具１３` | `0x8976` / `0x8972` | `C2B0C0AD` | `속성 방어구 13` |
| `ARF-TM-7C3174BF24D161835E83` | `防具１１` | `属性防具１１` | `0x8852` / `0x884E` | `C2B0C0AD` | `속성 방어구 11` |

두 건 모두 scanner가 `属性`의 raw `C2B0C0AD`를 건너뛰었다. 승인 번역의 `방어구 13/11`에 누락 의미를 복구해 `속성 방어구 13/11`로 확정했으며 각각 21바이트 고정 필드에 들어간다.

## `<$0F>座<$01>` 구조 접두부 판정

- TM: `ARF-TM-7CD4CC8553B43C2C978E`
- scanner: `<$0F>座<$01>作戦設定`, offset `0x6F22`, raw `0FBAC201BAEEC0EFC0DFC4EA`
- 구조화 field: `help:82:title`, offset `0x6F26`, raw `BAEEC0EFC0DFC4EA`
- 정확한 overlap: 8바이트; field 앞 `0FBAC201` = `<$0F>座<$01>`는 구조 접두부
- clean source/translation: `作戦設定` / `작전 설정`

따라서 `座`를 표시 문자열로 보아 음역한 `좌`는 제거했다. 이는 substring 추정이 아니라 원시 payload의 table field 시작점으로 판정한 결과다.

## 복수 substring 후보 3건의 offset 판정

| TM | substring 후보 | exact offset으로 확정 |
|---|---|---|
| `ARF-TM-732A78E7D681BF59765C` | `help:236:title`=`レイ`, `help:237:title`=`レイスコール` | `help:237:title` |
| `ARF-TM-7997FAEEC44DB49163E1` | `help:13:title`=`ＲＥＳ`, `help:123:title`=`ＲＥＳストック`, `help:130:title`=`全力ＲＥＳストック` | `help:130:title` |
| `ARF-TM-7BECC1D0372FAD196C33` | `help:171:title`=`ジェム`, `help:175:title`=`ジェムの破片` | `help:175:title` |

문자열 포함 관계만으로 짧은 후보를 선택하지 않았으며, 세 건 모두 raw 범위가 한 field에만 정확히 겹쳤다.

## 구조 접두부 혼입 대표 사례

- `help:237:title`: scanner `0x1413B`, field `0x1413F`; `0F6A7C20` (`<$0F>j| `) 제거.
- `dragon:12:name`: scanner `0xD10`, field `0xD14`; `01010101` (`<$01>`×4) 제거.
- `help:98:title`: scanner `0x84D5`, field `0x84D6`; 선두 `0A` 개행 제거.
- `magic:17:menu_name`: scanner `0xAE3`, field `0xAE4`; 선두 `32` (`2`) 제거.
- `chat:255:title`: scanner `0x827B`, field `0x827C`; 선두 `38` (`8`) 제거.

33건 전체의 exact table unit, clean source/translation, raw offset·hex, payload hash, encoded hex와 NUL 포함 capacity 판정은 JSON에 기록했다.

## 임시 코드북 검증

- canonical_v1 코드북: 784자, SHA-256 `C2B3EFD964B88FB58B166AEE72EC655DCBBE0E6245A7B69AFFA22F96EF55851A`
- batch 0011 임시 코드북: 805자, SHA-256 `8FEE8348945F09C0937317EA5C180BD366E257049851E6895E68ADCB86110B24`
- 새 글자 21자 append-only 추가
- 기존 784자 mapping 전부 불변
- 생산 canonical codebook과 글꼴은 수정하지 않음

## preflight의 별도 범위 외 적합성 항목

초기 전체 fit에는 exact-source로 이미 매칭된 고정 필드 overflow 3건(`ARF-TM-76E49C6A0E93976F891E`, `ARF-TM-7092E11C1F16690A719C`, `ARF-TM-77F216B015A6123828EF`)과 resizable table의 기존 자리 초과 69건이 있다. 이들은 **신규 unmatched 경계 감사 33건 밖**이므로 본 JSON에서 번역을 바꾸지 않았다. 이번에 해결한 33건 자체는 모두 NUL 포함 capacity에 적합하다.

## 별도 조치 목록

- **Ambiguous:** 없음. 발생 시 raw 구조 증거 확보 전까지 반영 제외.
- **Unmatched:** 없음. substring만으로 추정하지 말고 포맷/offset 추가 조사.
- **감사 범위 내 overflow:** 없음. 발생 시 의미 보존 축약 재승인 또는 검증된 resizable 경로 사용.
- **Encoding error:** 없음. 발생 시 append-only 코드북 확장과 글꼴 재렌더링 후 재검증.
