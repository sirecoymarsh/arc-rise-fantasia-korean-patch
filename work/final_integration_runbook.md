# 《아크 라이즈 판타지아》 한국어화 최종 통합 실행서

> 이 문서는 **실행 준비용**이다. 작성 중에는 병합, 인코딩, 폰트 주입, 테이블 적용, 컨테이너 재빌드, RVZ 변환, 검증을 실행하지 않았다. 149개 독립 검수본이 모두 고정된 뒤 아래 순서를 한 번만 수행한다. 번역문 생성·교정에는 Codex 내부 모델만 사용하며, 외부 번역 서비스·모델·API는 사용하지 않는다.

작성 완료 시점의 입력 인벤토리에는 source 149개, draft 149개, reviewed 149개, review report 149개가 모두 존재한다. 특히 마지막 `batch_0149`는 177행이며, 0147~0149 보고서도 `Codex internal models only`와 빈 외부 서비스·모델/API 목록을 기록한다. 이 확인은 파일 목록과 보고서 메타데이터만 읽은 것이며 validator/fit/encoding/boundary audit를 실행한 결과가 아니다.

## 1. 최종 기준과 불변 조건

### 원본

- 게임 ID: `RPJJ99`
- 읽기 전용 원본: `F:\DOWN\Arc Rise Fantasia (Japan)\Arc Rise Fantasia (Japan).rvz`
- 원본 SHA-256: `4671E3E74EB664E441FA927FF6BE9FC06B7D4860782BC4CECCF7DBBB4108AAC5`
- 원본 RVZ를 직접 덮어쓰지 않는다.
- 기준 메타데이터: `work/project/baseline_manifest.json`, `work/project/language_contract.json`

### 텍스트 완성 기준

`work/translation/tm_v2/batch_manifest.json`이 선언한 값이 최종 기준이다.

| 항목 | 기대값 |
|---|---:|
| 검수 배치 | 149 |
| TM 단위 | 29,777 |
| 배치 0001~0148 | 각 200 |
| 배치 0149 | 177 |
| 원시 텍스트 발생 | 84,761 |
| `system_database` | 4,343 TM |
| `battle_text` | 172 TM |
| `misc_text` | 60 TM |
| `event_script` | 4,259 TM |
| `map_dialogue` | 20,943 TM |

`149 × 200`으로 계산하면 안 된다. 마지막 배치가 177개이므로 총합은 정확히 29,777개다.

### 실제 파일 적용 범위

`work/catalog/text_v2/text_catalog.json` 기준 사용자 표시 텍스트는 612개 물리 파일에 있다.

| 물리 파일군 | 파일 수 | 논리 자산/적용 방식 |
|---|---:|---|
| `Event/**/*.vol` | 377 | BSCR 377개, RTDP entry path `[0]` |
| `Map/*.cxd` | 229 | BSCR 229개, LZ10→RTDP entry path `[1]` |
| `Sys/*` | 3 | `system.vol`, `help.bin`, `monster_book.bin` |
| `Btl/*` | 2 | `btl_tutorial.vld`, `btl_usual.vol` |
| `minigame/*` | 1 | `mg_copin.vol` |
| **합계** | **612** | BSCR 606개 + 비-BSCR 테이블/폰트 |

BSCR 전수 609개 중 일본어 표시문이 없는 명령 전용 Event BSCR 3개는 수정 대상이 아니다. 최종 오버레이에는 원본과 실제로 달라진 물리 파일만 포함한다.

## 2. 고정 실행 환경

PowerShell에서 작업 루트를 고정한다.

```powershell
$Root = 'C:\Users\CadriacLord\Documents\Codex\2026-08-03\f-down-arc-rise-fantasia-japan'
Set-Location -LiteralPath $Root

$Python = 'P:\AI\forge\venv\Scripts\python.exe'       # Python 3.10.11, Pillow 9.5.0 확인됨
$Node = 'C:\Program Files\nodejs\node.exe'             # Node v24.15.0 확인됨
$DolphinTool = Join-Path $Root 'work\tools\dolphin-2603a\Dolphin-x64\DolphinTool.exe'
$SourceRvz = 'F:\DOWN\Arc Rise Fantasia (Japan)\Arc Rise Fantasia (Japan).rvz'
```

현재 PATH의 `python.exe`는 WindowsApps shim이며 이 환경에서 실행되지 않았다. 실행서에서는 반드시 위 `$Python`을 사용한다.

## 3. 현재 도구의 사용 가능 범위

| 단계 | 기존 도구 | 최종 통합 사용 여부 | 현재 제한 |
|---|---|---|---|
| 배치 검증 | `work/research/validate_translation_batch.py` | 사용 가능 | 149개를 최종 단계에서 일괄 실행 |
| 검수 체인 | `work/research/validate_review_chain.py` | **수정 후 사용** | 모든 배치를 200개로 가정하여 0149에서 실패 |
| TM 병합 | `work/research/merge_translation_batches.py` | 사용 가능 | 최종 boundary audit를 입력해야 함 |
| boundary 통합 | `work/research/build_canonical_boundary_audit.py` | **현재 그대로 사용 금지** | 배치 0001~0007만 해시 고정; 0008/0011 및 이후 최종 상태 미포함 |
| 승인 코퍼스 | `work/research/build_approved_corpus.py` | 사용 가능 | 최종 TM을 입력할 것 |
| 코드북/폰트 주입 | `work/research/font_agent/arf_euc28_mapping.py` | 사용 가능 | 기존 코드북을 append-only로 확장 |
| 폰트 검증 | `work/research/verify_injected_fonts.py` | 사용 가능 | 마지막 통합 검증 단계에서 1회 실행 |
| 테이블 fit | `work/research/check_translation_fit.py` | **수정 후 최종 검증에 사용** | `approved_tm_units`를 전체 TM으로 세면서 테이블 매칭 수와 같다고 가정한 과거 부분 상태용 의미가 남아 있음 |
| 시스템 테이블 적용 | `work/research/build_system_table_application_proof.py` | 시스템 13 payload에 사용 가능 | `primary_surface == system_database`만 적용 |
| 비시스템 테이블 적용 | `work/research/table_agent/arf_table_tool.py` | leaf writer로 사용 가능 | TM→15개 payload를 묶는 상위 스크립트 없음 |
| BSCR 적용 | `work/research/bscr_agent/bscr_tool.py` | leaf writer로 사용 가능 | TM→606개 BSCR manifest를 만드는 상위 스크립트 없음 |
| RTDP/LZ10 재빌드 | `work/research/container_agent/container_tool.js` | 사용 가능 | 608개 비-Sys 컨테이너를 묶는 상위 스크립트 없음 |
| Sys staging | `work/research/build_partial_runtime_staging.py` | Sys 부분에 사용 가능 | `system.vol` + 직접 파일 2개만 생성 |
| 최종 정적 검증 | `work/research/build_final_static_verification.py` | **현재 그대로 사용 금지** | 0149=177, 전체 surface, 전체 BSCR/컨테이너/RVZ를 모름 |
| RVZ 도구 | `DolphinTool.exe` | 기존 이미지의 변환/검증에 사용 가능 | 추출 트리나 오버레이를 Wii ISO/RVZ로 조립하지 못함 |

## 4. 정확한 최종 실행 순서

아래 단계는 순서를 바꾸지 않는다. 전용 출력 폴더를 쓰고, 원본 및 과거 증명 파일을 재사용 가능한 입력으로만 취급한다.

### 4.1 최종 입력 동결

다음 네 파일군이 `batch_0001`부터 `batch_0149`까지 모두 있어야 한다.

- 원본 패킷: `work/translation/tm_v2/batches/source/batch_####.jsonl`
- 초벌: `work/translation/drafts/batch_####.jsonl`
- 독립 검수본: `work/translation/reviewed/batch_####.jsonl`
- 검수 보고서: `work/translation/reviews/batch_####_review.json`

각 파일의 기대 행 수는 `batch_manifest.json`의 해당 `unit_count`를 따른다. 검수 보고서는 다음을 모두 만족해야 한다.

- `independent_review: true`
- 초벌 작성자와 검수자가 다름
- `translation_engine_policy: "Codex internal models only"`
- `external_translation_services_used: []`
- `external_translation_models_or_apis_used: []`

원본 RVZ 해시도 다시 고정한다.

```powershell
(Get-FileHash -LiteralPath $SourceRvz -Algorithm SHA256).Hash
```

결과가 기준 SHA-256과 다르면 즉시 중단한다.

### 4.2 최종 시스템 경계 감사 고정

TM 병합 전에 **최종판** `canonical_system_boundary_audit.json`이 필요하다. 이 파일은 4,343개 `system_database` TM 전체를 구조화 테이블 catalog와 대조하고, 실제 경계 이상만 포함해야 한다.

필수 판정:

- `ambiguous_tm_units == 0`
- `unmatched_tm_units == 0`
- 모든 `table_unit_ids`가 중복 없이 정확한 offset/raw hash 근거를 가짐
- boundary의 `clean_source_text`와 최종 검수 번역이 일치함
- 수정된 검수본과 검수 보고서의 provenance가 유지됨

현재 `work/research/build_canonical_boundary_audit.py`는 배치 0001~0007만 해시 고정하며, 이미 존재하는 `batch_0008.json`과 `batch_0011.json`도 포함하지 않는다. 따라서 현재 스크립트를 그대로 실행하면 안 된다. 먼저 최종 component를 전부 읽는 새 builder 또는 갱신본이 필요하다.

최종 경계 파일의 권장 위치는 그대로 유지한다.

```text
work/translation/boundary_audit/canonical_system_boundary_audit.json
```

### 4.3 149개 검수본을 최종 TM으로 병합

최종 경계 감사가 고정된 뒤 병합한다.

```powershell
& $Python 'work/research/merge_translation_batches.py' `
  'work/translation/tm_v2/translation_memory.json' `
  'work/translation/final' `
  'work/translation/reviewed' `
  --reviewed `
  --reviewer 'Codex independent reviewers' `
  --boundary-audit 'work/translation/boundary_audit/canonical_system_boundary_audit.json'
```

생성물:

- `work/translation/final/translation_memory_draft.json`
- `work/translation/final/translation_memory_draft.csv`
- `work/translation/final/coverage.json`

기대값:

- `translated_units == 29777`
- `reviewed_units == 29777`
- `coverage_percent == 100`
- `translated_occurrences == 84761`
- `batch_files`가 정확히 149개이며 중복 없음

과거 `work/translation/current/`를 자동으로 덮어쓰지 않는다. 최종 검증까지 통과한 뒤에만 `final/`을 canonical/current 위치로 승격한다.

### 4.4 최종 한글 코퍼스와 append-only 코드북 생성

```powershell
& $Python 'work/research/build_approved_corpus.py' `
  'work/translation/final/translation_memory_draft.json' `
  'work/font/final_v1'

& $Python 'work/research/font_agent/arf_euc28_mapping.py' codebook `
  'work/font/final_v1/approved_korean_corpus.txt' `
  -o 'work/font/final_v1/codebook.json' `
  --existing 'work/font/canonical_v1/codebook.json' `
  --reserve-hex 'work/font/original_reserved_pairs_v2.txt'
```

규칙:

- 기존 `work/font/canonical_v1/codebook.json`의 784개 배정을 한 글자도 이동하지 않는다.
- 원문 보존 pair 2,227개와 충돌하면 중단한다.
- 전체 배정 수는 예약 후 사용 가능한 4,259개 이하여야 한다.
- 표준 EUC-JP로 가능한 문자는 기존 인코딩을 쓰고, 한글만 커스텀 pair를 쓴다.

### 4.5 WTM 9장 재주입

```powershell
& $Python 'work/research/font_agent/arf_euc28_mapping.py' inject `
  --source-dir 'work/font/canonical_v1/source_original' `
  --output-dir 'work/font/final_v1/injected' `
  --codebook 'work/font/final_v1/codebook.json' `
  --font 'C:\Windows\Fonts\malgunbd.ttf' `
  --font-size 22 `
  --wtmd-tool 'work/research/font_agent/wtmd_font_tool.py' `
  --manifest 'work/font/final_v1/injection_manifest.json'
```

폰트 입력의 과거 증명 SHA-256은 `e8cbc0b2afcc14fb45dfb6086d5102c0b23a96e7b6e708f3122acde1b86c9082`이다. 다른 폰트 bytes를 쓰면 새로운 렌더링 기준으로 간주해야 한다.

정식 폰트 검증 명령은 4.11의 마지막 통합 검증에서 한 번만 실행한다. 주입 writer 자체의 재디코드 가드는 그대로 동작한다.

### 4.6 시스템 테이블 13개 payload 재빌드

기존 builder는 `system_database` 범위의 13개 payload를 처리한다.

```powershell
& $Python 'work/research/build_system_table_application_proof.py' `
  'work/translation/final/translation_memory_draft.json' `
  'work/font/final_v1/codebook.json' `
  'work/translation/boundary_audit/canonical_system_boundary_audit.json' `
  'work/research/table_agent/catalogs' `
  'work/final_system_table_application' `
  --table-tool 'work/research/table_agent/arf_table_tool.py' `
  --encoder 'work/research/encode_custom_euc28.py'
```

이 builder는 출력 폴더가 존재하면 지우므로 `work/` 바로 아래의 전용 폴더만 사용한다.

기대 payload:

- `system.vol` 내부 11개: `item.bin`, `shop.bin`, `dragon.bin`, `treasure.bin`, `magic.bin`, `special.bin`, `operation.bin`, `quest.bin`, `ability.bin`, `chat.bin`, `todo.dat`
- disc 직접 파일 2개: `help.bin`, `monster_book.bin`

`quest.bin`은 증명된 가변 문자열 풀 writer를 사용한다. `container_tool.js`의 `standard-resize` RTDP 경로가 있으므로 `--quest-fixed-size`를 붙이지 않는다.

### 4.7 비시스템 테이블 15개 payload 재빌드 — 상위 스크립트 필요

다음 catalog와 leaf writer는 이미 있다.

- catalog: `work/research/table_agent/catalogs/*.json`
- writer: `work/research/table_agent/arf_table_tool.py`
- encoder: `work/research/encode_custom_euc28.py`

그러나 현재 `build_system_table_application_proof.py`는 `primary_surface == system_database`만 선택하므로 아래 15개 payload는 적용하지 않는다.

- `Btl/btl_tutorial.vld` 1개
- `minigame/mg_copin.vol::0000:copin.dat` 1개
- `Btl/btl_usual.vol::0000:btl_status.vol` 내부 `btl_stat_party*.bin` 13개

필요한 새 상위 builder는 final TM을 구조화 catalog에 연결하여 `replacement_hex`를 채운 후 다음 기존 명령을 각 payload에 실행해야 한다.

```powershell
& $Python 'work/research/table_agent/arf_table_tool.py' apply `
  '<trusted-source-payload>' `
  '<replacement-catalog.json>' `
  '<rebuilt-payload>'
```

필수 출력은 replacement catalog, rebuilt payload, 재카탈로그 결과, source/output SHA-256, 선언된 필드 밖 diff 0 증명이다. 이 상위 builder는 현재 workspace에 없다.

### 4.8 Event/Map BSCR 606개 재빌드 — 상위 스크립트 필요

기존 leaf writer:

```text
work/research/bscr_agent/bscr_tool.py
```

개별 자산의 기존 실행 형식:

```powershell
& $Python 'work/research/bscr_agent/bscr_tool.py' rebuild `
  '<source.bscr>' `
  '<rebuilt.bscr>' `
  --replacements '<raw-byte-replacements.json>'
```

필요한 새 상위 builder는 다음을 수행해야 한다.

1. `work/catalog/text_v2/text_catalog.json`의 occurrence ID를 최종 TM ID에 연결한다.
2. `translation_ko`를 final codebook으로 인코딩한다.
3. catalog의 leaf SHA-256과 원본 raw bytes를 확인한다.
4. catalog의 절대 leaf offset을 BSCR의 원래 string-pool-relative offset으로 변환한다.
5. 같은 BSCR의 변경을 하나의 replacements manifest로 그룹화한다.
6. call target은 변경하지 않고, `0C/14/15/19/1C` 구조 제어 서명을 보존한다.
7. 377개 Event BSCR 및 229개 Map BSCR을 각각 한 번만 재빌드한다.
8. 결과를 다시 strict parse하여 pointer가 새 문자열 시작을 가리키는지 확인한다.

TM→BSCR manifest를 만드는 범용 스크립트는 현재 workspace에 없다. `build_runtime_pilot.py`는 한 문장/고정 offset 실험용이므로 전체 적용에 사용하면 안 된다.

### 4.9 물리 컨테이너를 bottom-up으로 재빌드

모든 leaf payload가 준비된 후 기존 컨테이너 writer를 사용한다.

```text
work/research/container_agent/container_tool.js
```

개별 물리 파일 명령:

```powershell
& $Node 'work/research/container_agent/container_tool.js' rebuild `
  '<source.vol-or-cxd>' `
  '<arf-container-edits-v1.json>' `
  '<rebuilt-output>' `
  '<rebuild-report.json>'
```

entry path는 이름이 아니라 다음 고정 index를 쓴다.

- Event: `[0]`
- Map `.cxd`: LZ10 해제 후 RTDP `[1]`
- `mg_copin.vol`의 `copin.dat`: `[0]`
- `btl_usual.vol` party BTEM: `[0,0]`부터 `[0,12]`
  - 실제 내부 순서는 party00~party10, party07B, party06B다.

각 edit에는 해당 decoded 원본 leaf의 `expectedSha256`를 넣는다. Event 377개와 Map 229개는 물리 파일별로 모든 leaf edit를 한 manifest에 묶는다. writer가 자동으로 RTDP child→parent와 LZ10을 bottom-up으로 재빌드하고 새 payload를 즉시 재해제해 확인한다.

Sys 부분은 기존 builder를 사용한다.

```powershell
& $Python 'work/research/build_partial_runtime_staging.py' `
  --node $Node `
  --container-tool 'work/research/container_agent/container_tool.js' `
  --source-system-vol 'work/disc_extracted/DATA/files/Sys/system.vol' `
  --table-payload-dir 'work/final_system_table_application/payloads' `
  --font-dir 'work/font/final_v1/injected' `
  --output-dir 'work/final_sys_staging'
```

이 결과는 `system.vol` 20개 entry(폰트 9 + 시스템 테이블 11)와 직접 Sys 파일 2개만 포함한다.

### 4.10 전체 Riivolution staging과 RVZ 경로

#### 4.10.1 권장/현재 가능한 결과: 전체 Riivolution 오버레이

최종 staging builder는 다음 612개 disc-relative 경로를 하나의 트리에 모아야 한다.

```text
work/final_runtime_staging/riivolution_sd/
  riivolution/arc_rise_fantasia_ko.xml
  arc_rise_fantasia_ko/files/<원래 DATA 파티션 상대 경로 612개>
```

XML의 대상은 `RPJ` / developer `99` / disc `0` / region `J`로 고정하고, 각 변경 파일을 정확한 disc path에 매핑한다. 현재 `build_partial_runtime_staging.py`는 Sys 3개 파일만 XML에 쓰므로 전체 612개 파일 manifest/XML을 만드는 새 staging builder가 필요하다.

이 오버레이가 `language_contract.json`의 기본 전달 방식이며, 원본 RVZ를 수정하지 않는다.

#### 4.10.2 직접 RVZ 산출: 현재 누락된 단계

`DolphinTool.exe`의 `convert`는 **이미 존재하는 disc image 형식 변환기**다. 추출 디렉터리 또는 Riivolution 오버레이를 원본 RVZ에 삽입하여 새 Wii image를 만들지 않는다. 따라서 다음 단계가 먼저 필요하다.

1. 원본 RPJJ99 partition/FST를 보존하면서 612개 파일을 교체하는 검증된 Wii ISO/WIA composer.
2. 교체 파일 크기 변화에 맞춘 FST offset/size, partition data/hash tree를 재구축한 patched ISO/WIA.
3. 원본과 별도 경로에 저장하고, 612개 allowlist 밖 semantic 변화가 없는지 검사.

이 ISO/WIA composer 및 자동 주입 스크립트는 현재 workspace에 없고, `wit`/`wwt`도 설치되어 있지 않다. 이 단계가 준비되기 전에는 “최종 RVZ 재빌드 완료”라고 표시하면 안 된다.

검증된 patched ISO가 생긴 뒤의 RVZ 변환 명령은 다음과 같다. 원본의 RVZ 설정을 재현하기 위해 Zstandard level 19와 block size 131072를 사용하며 scrub은 하지 않는다.

```powershell
& $DolphinTool convert `
  -u 'work/final_disc/dolphin_user' `
  -i 'work/final_disc/Arc Rise Fantasia (Japan) [Korean].iso' `
  -o 'work/final_disc/Arc Rise Fantasia (Japan) [Korean].rvz' `
  -f rvz `
  -b 131072 `
  -c zstd `
  -l 19
```

원본 RVZ를 위 명령의 input으로 그대로 넣으면 한국어 파일은 들어가지 않고 원본을 재압축할 뿐이다.

### 4.11 마지막 한 번의 통합 검증

모든 builder가 끝난 뒤 이 단계에서만 정식 validator/fit/font/application/disc 검증을 일괄 수행한다.

#### A. 149개 배치 validator

```powershell
$Manifest = Get-Content 'work/translation/tm_v2/batch_manifest.json' -Encoding UTF8 -Raw | ConvertFrom-Json
foreach ($Batch in $Manifest.batches) {
  $Name = 'batch_{0:d4}' -f [int]$Batch.batch
  & $Python 'work/research/validate_translation_batch.py' `
    "work/translation/tm_v2/batches/source/$Name.jsonl" `
    "work/translation/reviewed/$Name.jsonl" `
    "work/translation/final_validation/${Name}_reviewed.json" `
    --boundary-audit 'work/translation/boundary_audit/canonical_system_boundary_audit.json'
  if ($LASTEXITCODE -ne 0) { throw "translation validator failed: $Name" }
}
```

경고도 최종 0이어야 한다. 일본어 잔존 경고가 의도적 디버그/고유 표기라면 무시하지 말고 TM ID별 waiver를 최종 manifest에 기록한다.

#### B. 검수 체인 validator

`work/research/validate_review_chain.py`를 먼저 다음처럼 수정해야 한다.

- 기대 행 수를 고정 200이 아니라 `batch_manifest.json`의 `unit_count`에서 읽기
- validation report 경로를 `work/translation/final_validation/`로 받을 수 있게 하기
- 149개 합집합을 29,777로 검사

수정 후 149개 이름을 한 번에 넘기고 `--require-zero-warnings`를 사용한다.

#### C. 폰트/전역 인코딩 검증

```powershell
& $Python 'work/research/verify_injected_fonts.py' `
  --source-dir 'work/font/canonical_v1/source_original' `
  --injected-dir 'work/font/final_v1/injected' `
  --codebook 'work/font/final_v1/codebook.json' `
  --reserved-hex 'work/font/original_reserved_pairs_v2.txt' `
  --approved-units 'work/font/final_v1/approved_units.jsonl' `
  --manifest 'work/font/final_v1/injection_manifest.json' `
  --mapping-tool 'work/research/font_agent/arf_euc28_mapping.py' `
  --wtmd-tool 'work/research/font_agent/wtmd_font_tool.py' `
  --encoder 'work/research/encode_custom_euc28.py' `
  --output 'work/font/final_v1/injection_verification.json'
```

#### D. 테이블 fit 검증

```powershell
& $Python 'work/research/check_translation_fit.py' `
  'work/translation/final/translation_memory_draft.json' `
  'work/font/final_v1/codebook.json' `
  'work/research/table_agent/catalogs' `
  'work/font/final_v1/fit_preflight.json' `
  --boundary-audit 'work/translation/boundary_audit/canonical_system_boundary_audit.json'
```

실행 전 이 스크립트의 집계 의미를 전체 surface용으로 수정해야 한다. 전역 인코딩 대상 29,777과 구조화 table 매칭 대상은 서로 다른 수다. 최종 판정은 최소한 다음을 분리해야 한다.

- 전체 승인 TM 인코딩 오류: 0/29,777
- 시스템 TM 미매칭: 0/4,343
- 고정 table overflow: 0
- `quest.bin` 가변 경로 overflow는 오류가 아님
- battle/misc table 15 payload의 매칭/fit 결과 별도 포함

#### E. 전체 application/container 검증

현재 없는 최종 application validator가 다음을 한 번에 검사해야 한다.

- TM 29,777개가 승인 상태이며 비어 있지 않음
- occurrence 84,761개가 정확히 한 번씩 적용됨
- 물리 출력 파일 612개, allowlist 밖 출력 0
- BSCR 606개 strict parse, call target/구조 제어 보존, pointer 오류 0
- table catalog 28개 재카탈로그 결과와 target bytes 일치
- WTM 9개 주입 셀 밖 pixel 변경 0
- 모든 RTDP/LZ10 report의 source hash, edit hash, entry identity/order, bottom-up audit 정상
- 재추출한 leaf hash가 builder가 선언한 payload hash와 일치
- 원본에 일본어 표시문이 없던 BSCR 3개 및 allowlist 밖 파일이 원본과 동일

현재 `build_final_static_verification.py`는 과거 7배치/system-only 체크포인트용이다. 최소한 다음을 고친 새 final verifier가 필요하다.

- 배치별 기대 수를 manifest에서 읽고 0149=177 허용
- 전체 surface 합계와 84,761 occurrence 확인
- `approved_system_tm_units`를 전체 29,777과 비교하지 않고 `system_database` 4,343과 비교
- 비시스템 table, BSCR 606개, 물리 컨테이너 612개, 최종 staging 및 RVZ/ISO manifest 포함
- 경로를 `work/translation/final`, `work/font/final_v1`, 최종 application/staging으로 받도록 인자화

#### F. RVZ 검증(직접 RVZ를 만들었을 때만)

```powershell
& $DolphinTool header `
  -i 'work/final_disc/Arc Rise Fantasia (Japan) [Korean].rvz' `
  -j

& $DolphinTool verify `
  -i 'work/final_disc/Arc Rise Fantasia (Japan) [Korean].rvz' `
  -u 'work/final_disc/dolphin_user'
```

추가로 `extract -l`의 전체 file set이 원본과 같고, 612개 대상의 추출 hash가 staging과 같아야 한다. 과거 원본 검증에서는 `Error creating key`와 `MD5 not computed`가 함께 출력되었으므로 같은 현상이 나면 보고서에 그대로 남긴다.

#### G. Dolphin 런타임 한 세션

정적 검증이 통과한 동일 산출물로 한 번의 통합 화면 검사 세션을 수행한다.

- 타이틀/새 게임/로드
- 시스템 메뉴, 아이템·스킬·퀘스트·도감·도움말
- 필드 NPC/맵 대사, 이벤트 대사와 선택지
- 전투 튜토리얼과 파티 이름
- 코핀 미니게임
- 짧은/긴/다중행/숫자/제어코드 문자열
- missing glyph, 잘림, 겹침, 잘못된 줄바꿈, 포인터/로딩 회귀

Riivolution 오버레이와 직접 RVZ를 둘 다 배포한다면 둘은 별도 바이너리이므로 각각 같은 해시 결속 manifest와 런타임 증거가 필요하다.

## 5. 현재 누락 또는 갱신이 필요한 항목

1. **최종 boundary builder**: 현재 builder는 0001~0007만 고정하며 0008/0011도 누락한다.
2. **비시스템 table 상위 적용기**: battle tutorial, copin, party BTEM 13개를 final TM에서 적용하는 orchestration이 없다.
3. **TM→BSCR 상위 적용기**: 606개 BSCR의 occurrence를 raw replacement manifest로 변환하는 스크립트가 없다.
4. **전체 컨테이너 orchestration**: Event 377 + Map 229 + Btl/minigame을 물리 파일별로 그룹화하는 스크립트가 없다.
5. **전체 Riivolution staging builder**: 기존 스크립트는 Sys 3개 파일만 생성한다.
6. **Wii ISO composer**: overlay/추출 트리를 새 ISO/WIA로 조립하는 도구가 없다. 따라서 직접 RVZ 생성 단계가 막혀 있다.
7. **최종 validator 갱신**: `validate_review_chain.py`, `check_translation_fit.py`, `build_final_static_verification.py`는 7배치/system-only 시점의 가정을 포함한다.
8. **이미지 기반 UI**: 프로젝트 상태 문서가 지적한 메뉴·로고·일부 이미지 UI 한국어화는 별도 lane이며 현재 텍스트 TM 통합만으로 완료되지 않는다.
9. **최종 릴리스/복원 installer**: 원본 해시 결속, 설치/복원, 혼합 상태 거부를 구현한 release script는 아직 없다.

## 6. 중단 조건

다음 중 하나라도 발생하면 이후 단계로 진행하지 않는다.

- 원본 RVZ SHA-256 불일치
- 149개 입력 파일군 또는 review provenance 누락
- 최종 boundary ambiguous/unmatched가 1개 이상
- TM 단위가 29,777 또는 occurrence가 84,761이 아님
- 코드북 예약 pair 충돌 또는 4,259 슬롯 초과
- 전역 인코딩 오류, 고정 table overflow, BSCR control/pointer 오류
- application occurrence 누락/중복
- 612개 allowlist 밖 물리 파일 변경
- 컨테이너 decoded leaf hash 불일치
- patched ISO/RVZ가 원본 RPJJ99가 아니거나 staging hash와 불일치

이 중단 조건을 모두 통과하고 실제 Dolphin 화면 검사까지 완료한 산출물만 “최종 한국어화 빌드”로 승격한다.
