# Arc Rise Fantasia 한국어화 최종 통합 감사

## 판정

**PASS — 정적 통합 검증 완료 / Dolphin 런타임 화면 검증 대기**

- 감사 체크: **134/134 통과**, 실패 0
- 번역 정책: **Codex 내부 모델만 사용**
- 외부 번역 모델/API 사용: **없음**
- 이번 감사의 변경 범위: 이 Markdown 보고서와 `final_integration_audit.json` 생성뿐이며 생산 파일은 수정하지 않음
- 런타임 릴리스 판정: **아직 아님** (`dolphin_screen_test: pending`)

## 핵심 교차 확인

| 항목 | 기대값 | 실제값 | 판정 |
|---|---:|---:|---|
| canonical boundary SHA-256 | `131DBA...71920` | `131DBA...71920` | PASS |
| boundary TM → table links | 235 → 242 | 235 → 242 | PASS |
| boundary ambiguous / unmatched | 0 / 0 | 0 / 0 | PASS |
| 승인·검수 번역 / 원문 발생 수 | 1,400 / 1,921 | 1,400 / 1,921 | PASS |
| 검수 배치 | 7 × 200 | 각 200, error 0, warning 0 | PASS |
| fit TM / table fields | 1,400 / 1,935 | 1,400 / 1,935 | PASS |
| fixed overflow / unmatched / encoding / global encoding | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | PASS |
| 고정 테이블 삽입 안전성 | `true` | `true` | PASS |
| 폰트 배정 / 원본 예약 충돌 / 오류 | 784 / 0 / 0 | 784 / 0 / 0 | PASS |
| 테이블 적용 TM → fields / payloads | 1,400 → 1,935 / 13 | 1,400 → 1,935 / 13 | PASS |
| staging system.vol edits + direct files | 20 + 2 | 20 + 2 | PASS |
| staging 정적 오류 / XML | 0 / valid | 0 / valid | PASS |
| final static 오류 | 0 | 0 | PASS |

## Canonical component 해시 감사

canonical 보고서가 선언한 5개 component의 SHA-256을 실제 파일과 다시 계산해 비교했다. 모두 일치했다.

| Component | TM | Table links | SHA-256 | 실제 일치 |
|---|---:|---:|---|---|
| `batches_0001_0002.json` | 61 | 68 | `E47BA47E...E80C7` | 예 |
| `batches_0003_0004.json` | 80 | 80 | `85002489...DB5C` | 예 |
| `batch_0005.json` | 28 | 28 | `4776B6BB...339E` | 예 |
| `batch_0006.json` | 37 | 37 | `DE12AA22...5E7F` | 예 |
| `batch_0007.json` | 29 | 29 | `8A04559A...DD42` | 예 |

- 합계: TM 235, table links 242
- component TM ID 합집합: 중복 없이 235개
- component table link 합집합: 중복 없이 242개
- canonical의 unit 본문은 component 합집합과 일치
- 모든 235개 매핑은 exact offset overlap이며 원본 SHA/field bytes/scanner bytes 재검증 플래그가 참

## 과거 용량 초과 1건의 최종 해소 확인

canonical component는 감사 당시 `ARF-TM-019ABE60D53A27F0D5E8`에 대해 1건의 용량 초과를 정직하게 보존한다.

- 당시 문안: `코핀에게 전해 내려오는 진실` — 27 bytes, 최대 20 bytes
- 최종 승인 문안: `코핀에게 전해진 진실`
- 적용 필드: `help:295:title`
- 최종 replacement: 20 bytes / 최대 20 bytes
- replacement catalog의 TM ID와 canonical ID 일치
- verification catalog의 실제 raw hex가 replacement hex와 일치
- 최종 fit의 `fixed_overflow_count`: 0

따라서 이는 미해결 결함이 아니라 **canonical 이력 이후 최종 TM에서 축약되어 실제 적용까지 검증된 항목**이다.

## 번역·검수 체인

- TM 전체 29,777개 중 1,400개가 `translated`이면서 `approved`
- 비어 있지 않은 한국어 target도 정확히 1,400개
- 번역된 발생 수 합계 1,921
- reviewed JSONL 7개를 합친 1,400개 TM ID는 모두 고유하며 merged TM target과 일치
- boundary 235개 TM ID 모두 최종 TM에 존재하고 승인 상태
- 7개 validator 모두 `source/translation/completed = 200/200/200`, error 0, warning 0, valid true
- `final_static_verification.json`에 기록된 7개 validator SHA-256은 실제 파일 해시와 모두 일치

## Fit·폰트·테이블 적용

### Fit

- 승인 TM 1,400개 전부 매칭
- 13개 schema의 table field 1,935개 매칭
- fixed overflow 0, unmatched 0, encoding error 0, global encoding error 0
- 66건은 증명된 resizable-table 경로이며 fixed-field 오류로 분류되지 않음
- `known_fixed_fields_fit = true`, `safe_for_fixed_table_insertion = true`

### 폰트

- Hangul glyph 784개 배정, 원본 예약 pair 2,227개, 충돌 0
- 승인 TM 1,400개 인코딩 오류 0
- 9개 페이지의 source/output 해시 18개를 실제 파일과 비교해 모두 일치
- 페이지별 크기·헤더/팔레트·재인코딩·변경 셀 경계 검사가 모두 통과

### 시스템 테이블 적용

- TM 1,400개를 table field 1,935개에 적용
- 13개 payload 재빌드, 검증 오류 0, 선언 슬롯 밖 변경 0
- proof의 TM/codebook/boundary SHA-256이 실제 파일과 일치
- 각 payload의 source/output/replacement catalog/verification catalog 해시 총 **52개**를 실제 파일과 비교해 불일치 0
- canonical boundary link 242개 모두 올바른 replacement TM ID와 `matched_via_boundary_audit`를 가지며 verification raw hex까지 일치

## Partial runtime staging

- `system.vol` 편집 entry 20개
- direct file 2개: `help.bin`, `monster_book.bin`
- source/output/direct/XML 등 staging 파일 해시 5개 실제 비교, 불일치 0
- Riivolution XML은 manifest 검증뿐 아니라 실제 XML 파서로도 읽혔고 root는 `wiidisc`
- 정적 오류 0, `static_valid = true`
- `runtime_ready_release = false`
- Dolphin 화면 테스트는 `pending`

## 결론

요청된 정적 통합 기준과 해시 체인은 모두 충족한다. 다만 이 판정은 **정적 체크포인트 감사**이며, 실제 Dolphin 부팅·글꼴 표시·화면 레이아웃 테스트가 완료되기 전에는 런타임 검증 완료나 최종 릴리스로 표시하면 안 된다.

