# Arc Rise Fantasia (RPJJ99) 비-BSCR 텍스트 테이블 역분석

## 1. 범위와 원칙

- 대상: 일본판 `RPJJ99`, 표시 문자열 인코딩은 EUC-JP 기반이다.
- 원본 RVZ 및 `work/disc_extracted` 입력은 읽기 전용으로 다뤘다.
- 외부 번역 API/외부 언어 모델은 사용하지 않았다. 이 작업은 로컬 바이트 구조 분석과 무변경 재구성 검증만 수행한다.
- 한국어 문자열은 표준 EUC-JP로 인코딩할 수 없으므로 writer는 번역문 자체가 아니라, 별도의 한글 폰트/코드포인트 맵이 만든 `replacement_hex`를 입력으로 받는다.

핵심 구현:

- `arf_table_tool.py`: 안정 semantic-unit catalog + 고정 길이 writer + `quest.bin` 포인터 풀 writer
- `run_roundtrip_suite.py`: 전 대상 자동 no-op/경계 검증
- `roundtrip_proof.json`: SHA-256을 포함한 28건 검증 증거
- `catalogs/*.json`: 파일별 안정 ID, 원문 바이트, 표시문, 용량, 제어코드 서명

## 2. 공통 고정 레코드 스키마

아래의 `capacity`는 NUL 종단자를 포함하는 C 문자열 슬롯 전체 크기다. 따라서 실제 교체 바이트는 항상 `capacity - 1` 이하여야 한다.

| 파일 | 레코드 수 × 크기 | 표시 문자열 필드 `(레코드 상대 오프셋, capacity)` | 비문자 영역/특기 |
|---|---:|---|---|
| `item.bin` | 772 × `0xFF` | `name (0x00,17)`, `description_primary (0x11,81)`, `description_secondary (0x62,81)` | `0xB4..0xFE` 메타데이터 |
| `shop.bin` | 47 × `0x56` | `name (0x00,20)` | `0x15..0x55` 상품/플래그 데이터 |
| `dragon.bin` | 13 × `0x117` | `name (0x00,24)`, `skill_name (0x18,48)`, `lore (0x48,97)`, `passive_description (0xA9,49)`, `battle_description (0xDA,49)` | `0x10B..0x116` 메타데이터 |
| `treasure.bin` | 256 × `0x31` | `display_name (0x17,21)` | `0x00..0x16` ASCII 내부 리소스 키, `0x2C..0x30` 메타데이터. 키는 번역 금지 |
| `magic.bin` | 49 × `0xA4` | `menu_name (0x00,20)`, `battle_name (0x14,40)`, `description (0x3C,80)` | `0x8C..0xA3` 메타데이터 |
| `special.bin` | 76 × `0x90` | `name (0x00,22)`, `description (0x16,83)` | `0x6A..0x8F` 메타데이터 |
| `operation.bin` | 8 × `0x78` | `name (0x00,24)`, `description (0x18,96)` | 레코드 전체가 두 문자열 슬롯 |
| `ability.bin` | 250 × `0x92` | `name (0x00,21)`, `description (0x15,81)` | `0x66..0x91` 메타데이터 |
| `todo.dat` | 208 × `0x90` | `lead (0x10,64)`, `objective (0x50,64)` | `0x00..0x0F` 진행 조건/ID |
| `help.bin` | 380 × `0x15B` | `title (0x00,21)`, `description (0x15,322)` | 마지막 `+0x15A` 1바이트 분류 플래그 |
| `monster_book.bin` | 274 × `0x284` | `name (0x00,35)`, `location (0x104,96)` | 이름 뒤 전투 스탯, `0x164` 이후 드롭/기타 데이터 |

고정 필드 중 특히 여유가 적은 곳:

- `item.name`: 최대 16/17바이트, NUL을 제외하면 여유 0바이트
- `shop.name`: 최대 20/21바이트, 여유 0바이트
- `dragon.passive_description`: 최대 47/49바이트, 여유 1바이트
- `ability.name`, `help.title`: 최소 여유 2바이트

한글 코드가 글자당 2바이트인 매핑이라면 이 제한은 사실상 표시 글자 수 제한이기도 하므로, 번역 단계에서 짧은 용어를 우선해야 한다.

## 3. `copin.dat`

`minigame/mg_copin.vol::0000:copin.dat`의 구조:

- `+0x00`: BE `u32` 레코드 수 = 30
- 파일 헤더: 4바이트
- 레코드: 30 × `0x9C` (156바이트)
- 레코드 내:
  - `name`: `+0x00`, capacity 16
  - `description`: `+0x10`, capacity 128
  - 메타데이터: `+0x90..+0x9B`, 12바이트

총 60개 필드가 모두 실제 일본어 표시 문자열이다. 레코드 크기는 파일 크기 `(4684 - 4) / 30`과 정확히 일치한다.

## 4. `quest.bin`: SSCR relocation + 가변 문자열 풀

### SSCR 공통 헤더

확인된 SSCR 헤더 의미:

- `0x00`: `SSCR`
- `0x04`: 데이터 시작 오프셋
- `0x08`: BE `u16 table_count`, BE `u16 relocation_count`
- `0x0C`: 데이터 시작 오프셋 복제본
- `0x10`: `(2 × table_count - 1)`개의 descriptor word
  - 테이블 이름 포인터와 다음 테이블 시작 경계가 교차 배치된다.
- 그 뒤: relocation 항목 `relocation_count × 8`
  - BE `u32 pointer_target`, BE `u32 pointed_value`
- 이어서 ASCII 테이블 이름, 정렬 패딩, 실제 데이터

### quest 전용 레이아웃

- 테이블: `_quest_tbl` 1개
- 데이터 시작: `0x0F20`
- relocation 수: 480
- relocation 표: `0x14..0x0F13`
- 테이블 이름: `0x0F14`, `_quest_tbl`
- 퀘스트 레코드: 80 × `0x60`, `0x0F20..0x2D1F`
- 문자열 풀: `0x2D20..EOF`
- 각 레코드에는 6개의 포인터 대상 슬롯이 있다.
  - `+0x04 title`
  - `+0x08 requester`
  - `+0x0C description`
  - `+0x10 objective_1`
  - `+0x14 objective_2`
  - `+0x18 objective_3`
- 파일의 대상 슬롯 값은 전부 0이고, 로더가 relocation 표를 통해 실제 주소를 연결하는 구조다.
- 480개 pointed value는 모두 유일하고 오름차순이다.
- 원본 풀은 480개의 `문자열 + NUL`이 빈틈·alias 없이 EOF까지 정확히 이어진다.
- 80개 레코드 중 실제 일본어가 있는 필드는 272개다. 나머지는 예약/빈 필드다.

Writer는 두 모드를 제공한다.

1. 기본 가변 풀 재빌드
   - 모든 문자열을 다시 연속 배치하고 480개 relocation value를 갱신한다.
   - 개별 문자열 길이 제한이 없고 파일 크기가 달라질 수 있다.
   - 제어코드만 보존되면 테이블 수준에서 길이 변경 가능하다.
   - 상위 `system.vol`의 entry 크기도 바뀌므로 가변 RTDP writer가 필요하다.
2. `--quest-fixed-size`
   - 각 번역은 해당 원문 슬롯 길이 이하여야 한다.
   - 짧아진 부분을 0으로 채우고 포인터와 파일 크기를 그대로 유지한다.
   - 현재의 고정 레이아웃 RTDP writer와 바로 결합할 수 있다.

## 5. `chat.bin`: SSCR 고정 메시지 표

- SSCR 테이블 두 개: `_msg_tbl`, `_trigger`
- 데이터 시작: `0x56A8`
- `_msg_tbl`: `0x56A8..0x9B67`, 정확히 400 × `0x2C`
- 각 메시지 레코드:
  - `title`: `+0x00`, capacity 43
  - 플래그: `+0x2B`, 1바이트, 번역 금지
- `_trigger`: `0x9B68..EOF`, 바이너리 트리거/스크립트 데이터, 번역 대상에서 제외
- relocation 수: 2767. 제목 문자열 자체는 레코드 고정 슬롯이므로 개별 포인터 재작성은 필요 없다.
- 400개 슬롯 중 318개가 실제 일본어 표시 제목이다.

기존 단순 NUL 스캐너가 플래그 바이트를 다음 제목 앞 제어문자로 오인했지만, 43+1 레코드 분리로 이를 제거했다.

## 6. `btl_tutorial.vld`

- 파일 크기: `0x17000`
- 활성 대사 레코드: 190개
- 레코드 시작은 16바이트 정렬이며 `+0x0C == FFFFFFFF` 표식으로 안정 검출된다.
- 일반 활성 레코드 크기/간격: `0x170`; 마지막 구간은 `0x160`; 튜토리얼 묶음 사이에는 패딩/빈 공간이 있다.
- 공통 표시 필드:
  - 헤더: `+0x00..+0x13`, 20바이트
  - `message`: `+0x14`, capacity `0x100` (256)
  - `speaker`: `+0x114`, capacity `0x40` (64)
  - 일반 trailer: `+0x154`, 28바이트
  - 마지막 `0x160` 레코드 trailer: 12바이트
- 190개 메시지 중 189개는 일본어, 한 개는 원문 ASCII `!?`; 화자 190개는 모두 일본어다.
- 총 380개 semantic unit, 메시지 25개에 런타임 제어코드가 있다.

파일 전체를 단순 `0x170` 배열로 해석하면 중간 패딩 이후 레코드 상대 오프셋이 틀어진다. 구현은 실제 헤더 표식을 탐색해 절대 위치 기반 ID를 만든다.

## 7. party BTEM 표시 이름

`Btl/btl_usual.vol::0000:btl_status.vol` 안의 13개 `BTEM` payload를 확인했다.

공통 구조:

- `0x00`: `BTEM`
- `0x08`: BE `u32` 데이터/표시 이름 오프셋 = `0x180`
- `display_name`: `0x180`, capacity 36
- 실제 이름 뒤 `0x1A4`부터 BTEM 전투/상태 데이터

확인된 13개 표시 이름:

| payload | 원문 |
|---|---|
| `party00` | ラルク |
| `party01` | リフィア |
| `party02` | サージュ |
| `party03` | オイゲン |
| `party04` | セシル |
| `party05` | レスリー |
| `party06`, `party06B` | アルス |
| `party07`, `party07B` | アデール |
| `party08` | ニコル |
| `party09` | クライド |
| `party10` | ディノス |

같은 BTEM 규칙은 첫 `btl_enemy.vld` LZ10 payload의 `帝国兵` 이름에도 성립한다. 다만 거대한 VLD 전체의 concatenation/index 구조는 본 writer 범위 밖이며, 이 보고서에서는 RTDP 안의 13개 party BTEM만 편집 가능 대상으로 확정했다.

## 8. 런타임 제어코드

실제 텍스트에서 확인된 주요 패턴:

- `13 xx`: 예 `13 14`, `13 03`, `13 02`, `13 00`
- `15 xx`: 예 `15 D4`, `15 90`, `15 D2`, `15 2A`
- `1F <ASCII digits>`: 예 `1F 000004`, `1F 01`
- `0A`: 수동 줄바꿈

예를 들어 help 문자열에는 다음과 같은 연속 토큰이 존재한다.

`13 14 / 1F 000004 / 1F 01 / 13 00`

Catalog는 각 필드에 ordered `control_signature`를 기록한다. Writer는 번역 바이트의 서명이 원문과 정확히 같지 않으면 실패한다. 줄바꿈 `0A`는 레이아웃 조정을 위해 서명에서 제외하지만, 다른 저수준 토큰과 ASCII operand는 그대로 보존한다. NUL은 writer가 붙이므로 `replacement_hex` 안에 직접 넣을 수 없다.

제어코드 포함 unit 수:

- `help`: 354
- `item`: 318
- `ability`: 55
- `quest`: 43
- `btl_tutorial`: 25

## 9. no-op 및 경계 검증

`roundtrip_proof.json` 결과:

- 총 28개 payload
  - 15개 핵심 테이블/직접 파일
  - 13개 party BTEM
- 전부 `parse → rebuild → write` 결과가 원본과 byte-for-byte 동일
- 각 결과 SHA-256도 원본과 동일
- `suite_passed = true`

추가 양성/음성 검증:

1. quest 가변 재빌드
   - 첫 40바이트 문자열을 `TEST` 4바이트로 교체
   - 파일 크기 `22990 → 22954` (`-36`)
   - 나머지 479개 문자열 동일
   - 재파싱 후 80레코드/480포인터 정상, 풀 gap 0
2. quest 고정 크기 모드
   - 동일 교체 후 파일 크기 22990 유지
   - relocation 표 전체 불변
   - 원래 슬롯의 남은 36바이트만 0 패딩
3. 고정 테이블 edit confinement
   - `operation[0].name`을 `TEST`로 바꾼 fixture는 원본과 같은 960바이트
   - 차이 8바이트가 전부 선언된 name 슬롯 안에만 존재
4. 음성 가드
   - 슬롯과 같은 24바이트를 넣어 NUL 공간을 없애는 overflow는 거부
   - quest 제어코드가 있는 필드를 제어코드 없는 바이트로 교체하면 거부

## 10. 원본 데이터의 특이점

정규화하거나 자동 수정하면 안 되는 원본 이상치:

- `shop.bin` record 28의 21바이트 name 슬롯은 마지막에 불완전한 EUC-JP lead byte `B2`를 포함한다. 원문 게임 데이터 그대로 보존되며, 한국어 번역 시 해당 슬롯 전체를 정상 매핑 바이트로 덮어써야 한다.
- `magic.bin` record 0의 `battle_name`/`description` 슬롯은 텍스트 대신 `FFFE` sentinel을 가진다.
- `special.bin` record 72의 description 슬롯은 `30FE` 비문자 sentinel을 가진다.
- 이 값들은 catalog에는 남지만 `has_japanese=false`이므로 번역 대상에서 제외해야 한다.

## 11. 적용 경계

- 고정 테이블, copin, chat, tutorial, party BTEM: payload 크기 불변으로 완전 편집 가능.
- quest:
  - 현재 RTDP 고정 writer를 쓸 때는 `--quest-fixed-size` 사용.
  - 가변 RTDP writer가 준비되면 기본 가변 풀 writer 사용 가능.
- 한국어화 실제 입력은 반드시 최종 한글 glyph map이 산출한 바이트여야 한다.
- `chat._trigger`, BTEM 전투 데이터, 각 레코드 메타데이터, treasure ASCII 리소스 키는 번역/수정 금지다.

