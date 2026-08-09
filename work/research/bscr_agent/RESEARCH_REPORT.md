# Arc Rise Fantasia (RPJJ99) BSCR 역분석 및 리빌더 보고서

## 범위와 안전 조건

- 대상: 추출된 RPJJ99 DATA 파티션의 `Event/*.vol` 및 `Map/*.cxd` 안쪽 BSCR.
- 원본 RVZ와 `work/disc_extracted`는 읽기만 했다.
- 번역은 수행하지 않았고 외부 번역 API/모델도 사용하지 않았다.
- 이 폴더의 도구는 inner BSCR만 담당한다. RTDP 재삽입과 LZ10 재압축은 별도 컨테이너 계층이다.

## 전수 검사 결과

`run_full_audit.py`로 전체 컨테이너 트리를 재귀 순회했다.

| 항목 | 결과 |
|---|---:|
| BSCR 총수 | 609 |
| Event BSCR | 380 |
| Map BSCR | 229 |
| BSCR 총 바이트 | 59,697,416 |
| descriptor | 23,371 |
| string-pool record | 212,342 |
| VM instruction | 3,315,159 |
| 선택지 호출 지점 | 585 |
| 전수 parse → no-op rebuild byte-exact | 609 / 609 |
| 구조 오류 | 0 |

전체 자산별 SHA-256, 섹션 경계, 개수, no-op SHA-256은 `full_audit.json`에 있다.

## 헤더

모든 정수는 big-endian이다.

| offset | 크기 | 확정된 의미 |
|---:|---:|---|
| `0x00` | 4 | magic `bscr` |
| `0x04` | 2 | opaque variant tag; 값은 `0x00AC` 603개, `0x00A9` 3개, `0x0090` 2개, `0x004D` 1개 |
| `0x06` | 30 | NUL-padded ASCII file name |
| `0x24` | 4 | file size |
| `0x28` | 4 | descriptor count |
| `0x2C` | 4 | descriptor start; 전부 `0x40` |
| `0x30` | 4 | string count |
| `0x34` | 4 | string-pool start; descriptor walk의 정확한 끝 |
| `0x38` | 4 | bytecode size |
| `0x3C` | 4 | bytecode start |

전수 성립 불변식:

```text
bytecode_start + bytecode_size == file_size == actual_length
descriptor_walk_end == string_pool_start
string_pool_start % 4 == 0
bytecode_start % 4 == 0
bytecode_size % 16 == 0
```

`0x38`과 `0x3C`는 각각 bytecode 크기와 시작 위치다. 기존의 단순 문자열 스캐너가 `0x38`을 pool end로 보았던 해석은 틀리며, pool end는 `0x3C`다.

## descriptor / 명령

descriptor는 `0x40`부터 연속 배치된다.

```text
u16 record_size
u16 type_code
char name[32]       # NUL-padded ASCII
byte opaque_tail[record_size - 36]
```

전수 type 분포:

| type | 수 | 이름에서 확인되는 역할 |
|---:|---:|---|
| `0xE0` | 21,403 | 일반 named command/function (`COM_*`, `FC_END` 등) |
| `0xE4` | 916 | `INIT_SCENE`, `INIT_PUT_*` |
| `0xE7` | 214 | `OPEN_EVENT` |
| `0xE8` | 229 | `CALLBACK_NPC` |
| `0xE9` | 229 | `CALLBACK_TRAP` |
| `0xEA` | 380 | Event episode entrypoint (`FC_EPISODE_*`, `EXP_FC_*`) |

opaque tail의 세부 필드는 번역 문자열 재배치에 필요하지 않아 의미를 단정하지 않았다. 원문 그대로 보존한다.

## 문자열 풀

`pool_start`에서 정확히 헤더의 `string_count`개를 읽는다.

```text
raw_string_0 00
raw_string_1 00
...
raw_string_n 00
00 padding          # 항상 1~4바이트, 다음 4바이트 경계까지
bytecode
```

- 문자열 포인터는 **pool-relative offset**이다.
- 문자열은 대부분 EUC-JP이나, 게임 전용/미정의 코드도 있으므로 리빌더는 텍스트가 아니라 raw bytes를 기준으로 동작한다.
- 모든 212,342개 레코드는 아래 두 포인터 opcode 중 하나 이상에서 참조되었다.
- 내부 command/function 이름은 번역 대상이 아니므로 기본적으로 변경을 거부한다.

## VM과 포인터

bytecode는 정확히 16바이트 셀의 배열이다.

```text
byte 0..3   opcode
byte 4..7   big-endian operand
byte 8..15  opcode-specific tail
```

문자열 포인터로 전수 확정한 opcode:

| opcode | 역할 | 고유 string 수 |
|---|---|---:|
| `1A F0 F1 5A` | 일반 literal string pointer | 165,722 |
| `81 00 F3 F2` | command/function call-target pointer | 46,620 |

두 집합은 전수에서 서로 겹치지 않았고 합집합이 전체 string pool과 정확히 일치했다. 총 참조 셀은 228,802개다. 리빌더는 두 opcode의 operand를 모두 새 pool-relative offset으로 갱신한다. 나머지 VM operand는 그대로 보존한다.

## 화자·메시지·치환 제어코드

BSCR pool 전수에서 나타난 제어코드:

| raw pattern | 측정 수 | 역할/처리 |
|---|---:|---|
| `0A` | 76,527 | line break; 번역 레이아웃에서 재배치 가능 |
| `0C` | 4,948 | page break; 순서와 개수 보존 |
| `14 hhhh` | 116 | item substitution ID, ASCII hex 4자리; 그대로 보존 |
| `15 hh` | 375 | controller/button glyph ID, ASCII hex 2자리; 그대로 보존 |
| `19 hh` | 40,207 | speaker slot/portrait slot, ASCII hex 2자리; 그대로 보존 |
| `1C hhhh` | 6,914 | message/window style ID, ASCII hex 4자리; 그대로 보존 |

`19` 값은 `00`~`08`이 주로 쓰이고 `0A`도 5회 있다. 같은 번호를 게임 전체의 한 고정 캐릭터로 단정할 증거는 없다. Event/호출 문맥의 speaker slot으로 취급하고 번역에서 숫자를 바꾸지 않는 것이 안전하다.

`1C` 뒤에는 다수의 네 자리 style 값이 온다. 예를 들어 `1C 30304134`는 raw `\x1C00A4`이며 다음 literal 대사의 메시지 표시 형식을 지정한다. 역시 내용 번역과 분리해 보존한다.

## 선택지

585개 선택지 호출에서 공통 구조를 전수 검출했다.

```text
1A F0 F1 5A <prompt_string_offset>
1A F0 F1 5A <options_string_offset>
82 BC F3 5A ...
82 BD F3 5A ...
82 BE F3 F2 ...
```

`options_string`은 LF(`0A`)로 항목을 구분한다. 예:

```text
prompt:  ワールドマップに移動しますか？
options: はい\nいいえ
```

또한 항목 자체가 `\x140001` 같은 item substitution이나 `\x1900` 같은 speaker slot일 수 있다. 번역 시 항목 순서와 의미 토큰을 보존해야 한다. 선택지 전문 예시는 `full_audit.json`의 `choice_examples`에 있다.

## variable-length rebuild 알고리즘

1. 헤더/descriptor/string count/bytecode 경계를 엄격히 검증한다.
2. 각 string record를 순서대로 재직렬화하며 old offset → new offset map을 만든다.
3. 마지막 NUL 뒤에 `4 - (content_size % 4)`바이트의 NUL padding을 붙인다. 즉 padding은 항상 1~4바이트다.
4. 두 포인터 opcode의 operand만 offset map으로 갱신한다.
5. `file_size`와 `bytecode_start`를 갱신한다.
6. `string_count`, `pool_start`, `bytecode_size`, descriptor와 비포인터 VM 셀은 그대로 보존한다.
7. 결과를 다시 strict parse하여 모든 포인터가 실제 string start를 가리키는지 확인한다.

기본 안전장치:

- embedded NUL 거부.
- call-target 변경 거부.
- `0C`, `14`, `15`, `19`, `1C` structural control signature 변경 거부.
- LF는 번역 레이아웃 조정을 위해 signature 비교에서 제외.

## no-op 및 길이 변경 증명

### Event 대표: `fc_00_001.bscr`

- 원본/no-op SHA-256: `84f9b5e301a916c2927c35c341eb55ee5526aa2f6eec745ee97237dc062fa6c2`
- parse → no-op rebuild: byte-exact.
- visible literal 하나를 30 → 32바이트로 늘림.
- file size: 4,028 → 4,032.
- bytecode start: 940 → 944.
- 포인터 셀 32개 검증, 그중 뒤쪽 string을 가리키는 28개 operand 변경.
- descriptor 전부 byte-exact, 비포인터 VM 셀 전부 동일.
- 원문 bytes로 역치환한 결과 원본 SHA-256과 byte-exact 일치.

### Map 대표: `map_t_jad_00.bscr`

- 원본/no-op SHA-256: `211c51ef804bcce28f9f9de459a93542353bfe553ac297d9cc4465586fd606a0`
- parse → no-op rebuild: byte-exact.
- literal 하나를 30 → 31바이트로 늘림.
- 기존 padding이 1바이트 줄어 총 file size와 bytecode start는 동일.
- 포인터 셀 1,771개 검증, 그중 1,724개 operand 변경.
- descriptor와 비포인터 VM 셀 동일.
- 역치환 결과 원본과 byte-exact 일치.

두 실험의 원본/no-op/변경/복원 fixture와 상세 필드값은 `fixtures/` 및 `full_audit.json`에 있다.

## 확정하지 않은 부분과 한계

- `0x04` variant tag의 의미는 미확정이다. 문자열 변경과 연동되는 checksum이라는 증거는 없고 값이 네 종류뿐이므로 opaque 상태로 보존한다.
- descriptor opaque tail과 문자열과 무관한 VM opcode의 의미는 단정하지 않았다.
- 구조 검증, byte-exact no-op, 포인터 전수 검증, 가역성은 완료했지만 이 하위 작업에서는 Dolphin 런타임 로드 테스트까지 수행하지 않았다.
- RTDP/LZ10 outer container 리빌드와 최종 디스크 패치는 별도 계층에서 검증해야 한다.
- 실제 한국어 glyph byte mapping은 폰트 작업 결과를 받아 raw replacement manifest로 공급해야 한다.
