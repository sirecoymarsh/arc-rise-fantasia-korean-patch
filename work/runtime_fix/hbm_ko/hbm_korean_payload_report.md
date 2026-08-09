# Wii HOME 메뉴 한국어 payload 보고서

- 대상: Arc Rise Fantasia `RPJJ99`
- 번역: Codex 내부 모델만 사용
- 외부 번역 서비스/API: 사용하지 않음
- 원본 추출물: 변경하지 않음
- 정적 검증: **PASS**

## 산출물

| 물리 경로 | 출력 경로 | 크기 | SHA-256 |
|---|---|---:|---|
| `Hbm/home.csv` | `work/runtime_fix/hbm_ko/payloads/Hbm/home.csv` | 3640 | `BCBE430B52BD0D44036737FD1775CB96C9731BC026D0C7210EC9ECEDA520E12A` |
| `Hbm/home_nosave.csv` | `work/runtime_fix/hbm_ko/payloads/Hbm/home_nosave.csv` | 2558 | `BF527E3B5F79FC936F723256932F06790979825FFDBF0F4EEACB930CD0D910EF` |
| `Hbm/homeBtn.arc` | `work/runtime_fix/hbm_ko/payloads/Hbm/homeBtn.arc` | 432160 | `A583578077CB3EC808532719BFD9835462B2AFE66327343F266EA4A895277CC8` |

## CSV 번역

| 파일 | 일본어 | 한국어 |
|---|---|---|
| `Hbm/home.csv` | 接続する順番に<br>①ボタンと②ボタンを<br>同時に押してください。 | 연결할 순서대로<br>① 버튼과 ② 버튼을<br>동시에 눌러 주세요. |
| `Hbm/home.csv` | 切断中・・・ | 연결을 끊는 중... |
| `Hbm/home.csv` | Wiiメニューにもどりますか？<br>（保存していない内容は失われます） | Wii 메뉴로 돌아가시겠습니까?<br>(저장하지 않은 내용은 사라집니다.) |
| `Hbm/home.csv` | リセットしますか？<br>（保存していない内容は失われます） | 리셋하시겠습니까?<br>(저장하지 않은 내용은 사라집니다.) |
| `Hbm/home_nosave.csv` | 接続する順番に<br>①ボタンと②ボタンを<br>同時に押してください。 | 연결할 순서대로<br>① 버튼과 ② 버튼을<br>동시에 눌러 주세요. |
| `Hbm/home_nosave.csv` | 切断中・・・ | 연결을 끊는 중... |
| `Hbm/home_nosave.csv` | Wiiメニューにもどりますか？ | Wii 메뉴로 돌아가시겠습니까? |
| `Hbm/home_nosave.csv` | リセットしますか？ | 리셋하시겠습니까? |

## homeBtn.arc 이미지

- Nintendo U8 크기와 111개 node table/모든 member offset을 보존했다.
- 일본어 I4 TPL 12개를 같은 크기·같은 헤더·같은 캔버스로 교체했다.
- ON/OFF, 1P~4P 중립 표기 6개는 원본을 유지했다.
- 비교 이미지: `work/runtime_fix/hbm_ko/audit/homebtn_original_vs_korean.png`

| member | 원문 | 한국어 | 규격 |
|---|---|---|---|
| `arc/timg/tx_btn_00.tpl` | とじる | 닫기 | 136×40 I4 |
| `arc/timg/tx_btn_L_00.tpl` | Wiiメニューへ | Wii 메뉴로 | 240×64 I4 |
| `arc/timg/tx_btn_L_11.tpl` | リセット | 리셋 | 240×64 I4 |
| `arc/timg/tx_cntrl_00.tpl` | Wiiリモコンの設定 | Wii 리모컨 설정 | 424×32 I4 |
| `arc/timg/tx_cntrl_01.tpl` | Wiiリモコンの設定をとじる | Wii 리모컨 설정 닫기 | 424×32 I4 |
| `arc/timg/tx_msgBtn_00.tpl` | はい | 예 | 200×32 I4 |
| `arc/timg/tx_msgBtn_01.tpl` | いいえ | 아니요 | 200×32 I4 |
| `arc/timg/tx_optnBtn_20.tpl` | つなぎなおす | 다시 연결 | 320×64 I4 |
| `arc/timg/tx_optn_00.tpl` | 音量 | 음량 | 112×64 I4 |
| `arc/timg/tx_optn_10.tpl` | 振動 | 진동 | 112×64 I4 |
| `arc/timg/tx_optn_20.tpl` | 接続 | 연결 | 112×64 I4 |
| `arc/timg/tx_ttl_wrd_a.tpl` | HOMEボタンメニュー | HOME 버튼 메뉴 | 368×40 I4 |

## BRFNT 한글 주입

- member: `arc/font/RevoIpl_UtrilloProGrecoStd_M_32_I4.brfnt` @ `0x1C020`
- 크기 보존: 58236 bytes
- 필요한 고유 한글 45자를 기존 일본어 glyph slot 57~101에 주입했다.
- CMAP 용량 61개 중 55개 사용.
- ASCII, 유럽어 악센트, 공백, ①, ② 매핑은 보존했다.
- 모든 CSV 코드포인트 매핑 확인: PASS
- glyph 시트: `work/runtime_fix/hbm_ko/audit/brfnt_korean_glyphs.png`
- 실제 BRFNT 렌더 미리보기: `work/runtime_fix/hbm_ko/audit/brfnt_dynamic_text_preview.png`

## 구조 검증

- `valid`: `True`
- `csv_bom_preserved`: `True`
- `csv_other_language_columns_unchanged`: `True`
- `u8_size_preserved`: `True`
- `u8_node_table_preserved`: `True`
- `all_target_tpl_sizes_and_headers_preserved`: `True`
- `brfnt_size_and_header_preserved`: `True`
- `all_required_dynamic_codepoints_mapped`: `True`
- `unexpected_changed_u8_members`: `[]`

## 통합

- payload root: `work/runtime_fix/hbm_ko/payloads/Hbm`
- Riivolution fragment: `work/runtime_fix/hbm_ko/riivolution_hbm_rules.xml.fragment`
- CSV 두 파일은 크기가 바뀌므로 `resize=true`, homeBtn.arc는 같은 크기이므로 `resize=false`다.

## 남은 런타임 검증

- [ ] 저장 가능한 장면에서 HOME을 열어 모든 버튼/설정/확인 문구 확인
- [ ] 저장 불가 장면에서 home_nosave.csv 경로 확인
- [ ] 재연결/연결 해제 흐름에서 ①/②, 한글 glyph, 줄바꿈, clipping 확인
