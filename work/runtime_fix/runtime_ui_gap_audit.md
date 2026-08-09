# Arc Rise Fantasia 한국어화 런타임 UI 경계 감사

- 게임 ID: `RPJJ99`
- 감사 시각: `2026-08-03T21:51:17.942Z`
- 판정: **FAIL_INCOMPLETE_LOCALIZATION_BOUNDARY**
- 본 문서는 감사 스냅샷이다. 원본 추출물, 게임 페이로드, 현재 655개 staging 파일은 변경하지 않았다.
- 본 감사에서 번역을 수행하지 않았다. 후속 번역은 Codex 내부 모델만 사용한다.

## 1. 결론

초기 설정 화면의 일본어는 이미지가 아니라 `DATA/sys/main.dol`의 EUC-JP rodata에서 온다. `text_probe_10.json`은 이를 발견했지만 최종 텍스트 카탈로그가 `DATA/files`만 읽어서 `DATA/sys/main.dol`이 catalog, application, staging 경로에서 탈락했다.

main.dol 밖에서도 다음 누락이 확정되었다.

1. `DATA/files/Hbm/home.csv`, `home_nosave.csv`: Wii HOME 동적 일본어 문구.
2. `DATA/files/Hbm/homeBtn.arc`: 일본어가 구워진 I4 TPL 18개와 한글 매핑이 0개인 BRFNT.
3. `DATA/files/Event/endroll/EV09_18_0200C_00.wtm`부터 `_22.wtm`: 엔딩 대사 이미지 23개.

현재 staging 655개에 확정 누락 27개를 더하면 최소 **682개**다. 영상과 배너 시각 전수 검사가 남아 있어 잠정치다.

## 2. 런타임 및 파이프라인 증거

| 증거 | 값 |
|---|---|
| 일본어 초기 설정 캡처 | `work/runtime_validation/runtime_initial_settings_japanese_before_fix.png`, SHA-256 `69FFBAAB54DFB7D50ACE5265D6E358F63A79FD20E510328D3D848DABD33124AC`, 642×512 JPEG |
| 한글 스트랩 대조 캡처 | `work/runtime_validation/runtime_boot_korean.png`, SHA-256 `E3FBB193D9599E4F6DB5533CEFE09BAEB5F6269C3331B7716141BF512A2CD07D`, 642×512 JPEG |
| DOL probe | 1885개 후보, EUC-JP, SHA-256 `4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC` |
| 텍스트 카탈로그 | 84761 occurrences / 1751 physical sources, main.dol=false, Hbm=false |
| 최종 staging | 655개, roots=`{"Btl":2,"Event":377,"interface":39,"Map":229,"minigame":1,"Sys":6,"Title":1}`, main.dol=false, Hbm=false, endroll=false |
| 이미지 lane | 수정 asset 48개 / target 44개, homeBtn=false, endroll=false |

### 원인 체인

```text
DATA/sys/main.dol --(probe 발견)--> 1,885 candidates
        X
DATA/files only --(catalog)--> application --> 655-file staging

Hbm CSV/U8 + Event/endroll WTM
        X  (텍스트/이미지 allowlist에 들어가지 못함)
```

## 3. main.dol 정확 오프셋

- 물리 파일: `DATA/sys/main.dol`
- 크기: 4464672 bytes
- SHA-256: `4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC`
- section: data[4], overall index 11, file `0x3C5C00`..`0x3E50A0`, RAM `0x803C9B00`..`0x803E8FA0`
- 주소식: `RAM = 0x803C9B00 + (file_offset - 0x003C5C00)`
- 직접 사용자 표시 확정 최소: 146개
- 초기 설정 lane: 40개
- casino/map/Copin 추가 deferred 사용자 표시 레코드: 129개

### 초기 설정 lane 40개

| file offset | RAM | bytes/capacity | 일본어 원문 |
|---:|---:|---:|---|
| `0x003C9E01` | `0x803CDD01` | 87/87 | ゲームで使用する<br>コントローラを設定します。<br>コントローラのボタンを押せば<br>確定されます。 |
| `0x003C9E59` | `0x803CDD59` | 10/10 | ヌンチャク |
| `0x003C9E64` | `0x803CDD64` | 22/22 | クラシックコントローラ |
| `0x003C9E7B` | `0x803CDD7B` | 26/26 | ゲームキューブコントローラ |
| `0x003C9E96` | `0x803CDD96` | 37/37 | %sを<br>操作コントローラに設定しました。 |
| `0x003D10FA` | `0x803D4FFA` | 8/8 | 設定終了 |
| `0x003D1103` | `0x803D5003` | 8/8 | 初期設定 |
| `0x003D110C` | `0x803D500C` | 87/87 | ゲームで使用する<br>コントローラを設定します。<br>コントローラのボタンを押せば<br>確定されます。 |
| `0x003D1164` | `0x803D5064` | 37/37 | %sを<br>操作コントローラに設定しました。 |
| `0x003D118A` | `0x803D508A` | 12/12 | コントローラ |
| `0x003D1197` | `0x803D5097` | 4/4 | 振動 |
| `0x003D119C` | `0x803D509C` | 4/4 | 字幕 |
| `0x003D11A1` | `0x803D50A1` | 12/12 | カーソル記憶 |
| `0x003D11AE` | `0x803D50AE` | 10/10 | カメラ回転 |
| `0x003D11B9` | `0x803D50B9` | 8/8 | 文字速度 |
| `0x003D11C2` | `0x803D50C2` | 10/10 | ＢＧＭ音量 |
| `0x003D11CD` | `0x803D50CD` | 8/8 | ＳＥ音量 |
| `0x003D11D6` | `0x803D50D6` | 8/8 | 音声音量 |
| `0x003D11DF` | `0x803D50DF` | 16/16 | フリッカーレベル |
| `0x003D11F0` | `0x803D50F0` | 4/4 | ＯＮ |
| `0x003D11F5` | `0x803D50F5` | 6/6 | ＯＦＦ |
| `0x003D11FC` | `0x803D50FC` | 4/4 | 遅い |
| `0x003D1201` | `0x803D5101` | 4/4 | 普通 |
| `0x003D1206` | `0x803D5106` | 4/4 | 早い |
| `0x003D120B` | `0x803D510B` | 4/4 | 瞬間 |
| `0x003D1210` | `0x803D5110` | 4/4 | 無音 |
| `0x003D1215` | `0x803D5115` | 4/4 | 最大 |
| `0x003D121A` | `0x803D511A` | 4/4 | 最小 |
| `0x003D121F` | `0x803D511F` | 4/4 | 通常 |
| `0x003D1224` | `0x803D5124` | 4/4 | 反転 |
| `0x003D1229` | `0x803D5129` | 32/32 | 使用するコントローラを設定します |
| `0x003D124A` | `0x803D514A` | 30/30 | コントローラの振動を設定します |
| `0x003D1269` | `0x803D5169` | 43/43 | デモシーンの字幕の表示／非表示を<br>設定します |
| `0x003D1295` | `0x803D5195` | 59/59 | 戦闘中のメニューのカーソル位置の<br>保存／リセットを設定します |
| `0x003D12D1` | `0x803D51D1` | 41/41 | ワールドでのカメラの回転方向を<br>設定します |
| `0x003D12FB` | `0x803D51FB` | 32/32 | メッセージの表示速度を設定します |
| `0x003D131C` | `0x803D521C` | 24/24 | ＢＧＭの音量調整をします |
| `0x003D1335` | `0x803D5235` | 22/22 | ＳＥの音量調整をします |
| `0x003D134C` | `0x803D524C` | 22/22 | 音声の音量調整をします |
| `0x003D1363` | `0x803D5263` | 38/38 | フリッカーフィルタのレベルを設定します |

전체 146개 확정 레코드와 추가 129개 deferred 레코드의 raw_hex, 원문 SHA-256, file/RAM 주소는 동반 JSON에 수록했다. DOL의 나머지 probe 후보에는 false positive, debug, 추가 사용자 표시 문구가 섞여 있으므로 146개를 전수 완료로 해석하면 안 된다.

## 4. main.dol 밖의 확정 누락

### 4.1 Wii HOME 동적 문구

| 물리 파일 | byte offset | bytes | 일본어 첫 열 |
|---|---:|---:|---|
| `DATA/files/Hbm/home.csv` | `0x4` | 64 | 接続する順番に<br>①ボタンと②ボタンを<br>同時に押してください。 |
| `DATA/files/Hbm/home.csv` | `0x57E` | 12 | 切断中・・・ |
| `DATA/files/Hbm/home.csv` | `0x70E` | 68 | Wiiメニューにもどりますか？<br>（保存していない内容は失われます） |
| `DATA/files/Hbm/home.csv` | `0xAB4` | 56 | リセットしますか？<br>（保存していない内容は失われます） |
| `DATA/files/Hbm/home_nosave.csv` | `0x4` | 64 | 接続する順番に<br>①ボタンと②ボタンを<br>同時に押してください。 |
| `DATA/files/Hbm/home_nosave.csv` | `0x57E` | 12 | 切断中・・・ |
| `DATA/files/Hbm/home_nosave.csv` | `0x70E` | 30 | Wiiメニューにもどりますか？ |
| `DATA/files/Hbm/home_nosave.csv` | `0x89E` | 18 | リセットしますか？ |

두 파일은 BOM FEFF, UTF-16BE, 탭 구분 다국어 열 구조다. 첫 번째 일본어 열만 바꾸고 BOM, CRLF, 따옴표, 탭, 행 수, 다른 언어 열을 보존해야 한다.

### 4.2 Wii HOME 이미지와 폰트

- 물리 파일: `DATA/files/Hbm/homeBtn.arc`
- 크기: 432160 bytes
- SHA-256: `B0AF517B04C369A278B42C0147878E6C2ACB7EA6ACA4986D6243F93D760980BE`
- U8 nodes: 111
- 시각 증거: `work/runtime_fix/audit_renders/hbm/homebtn_jp_eng_contact_sheet.png`, SHA-256 `FF31755277183C5795440F53234C4AA3A4FE03A6BDA0E107018394461CC94BDE`

| U8 member | archive offset | size | TPL | 보이는 표기 | SHA-256 |
|---|---:|---:|---:|---|---|
| `arc/timg/tx_btn_00.tpl` | `0x56740` | 2784 | 136×40 I4 | とじる | `4F3DEED386E02D1DE6CCAB74E9050627555B731A5F7952A66E3A53968F954850` |
| `arc/timg/tx_btn_L_00.tpl` | `0x57220` | 7744 | 240×64 I4 | Wiiメニューへ | `9AD2DD0F112F634AF84B2FA5D0D91DA3DDC06357951AB5CBA2215CC31950C1A0` |
| `arc/timg/tx_btn_L_11.tpl` | `0x59060` | 7744 | 240×64 I4 | リセット | `21515137553DD9F5A2A945298B9160AD9CA5A3C1D1F2F74D970D366126705991` |
| `arc/timg/tx_cntrl_00.tpl` | `0x5AEA0` | 6848 | 424×32 I4 | Wiiリモコンの設定 | `13BAD8732900FD637B3285966CBCB9A66224EE55167988409C46F2039AE08D96` |
| `arc/timg/tx_cntrl_01.tpl` | `0x5C960` | 6848 | 424×32 I4 | Wiiリモコンの設定をとじる | `AB2525DB402FDBDA0173F76FD8B97F7920853AE3A46AE78AF14F2B9351406A2F` |
| `arc/timg/tx_msgBtn_00.tpl` | `0x5E420` | 3264 | 200×32 I4 | はい | `957BD3E4185BD0E0790BACAA88D7B71B5E28928B084E18942C970E015725EB9F` |
| `arc/timg/tx_msgBtn_01.tpl` | `0x5F0E0` | 3264 | 200×32 I4 | いいえ | `52D4E043DE9AF4BFB83EC6C1BE97235F9DC0FA0A946A9E9E9BDFDADE13F47003` |
| `arc/timg/tx_optnBtn_10.tpl` | `0x5FDA0` | 4160 | 128×64 I4 | ON | `964B8B6CEFFEE5A1F09EA8B2FD778ACDEEBDA2F91068E89A653189ED60E35328` |
| `arc/timg/tx_optnBtn_11.tpl` | `0x60DE0` | 4160 | 128×64 I4 | OFF | `48916D99B29DFCA76B69D85C46DE0ED5CF151B60DCEBB81CA54939E63647715C` |
| `arc/timg/tx_optnBtn_20.tpl` | `0x61E20` | 10304 | 320×64 I4 | つなぎなおす | `AB2195C2B841728EAC910363AA6A7AA5A1D4F3A5AC22F6BE11C7CA7DFEC9D5B1` |
| `arc/timg/tx_optn_00.tpl` | `0x64660` | 3648 | 112×64 I4 | 音量 | `5EBEE19824CDEF521DB53437787C9480AB3AD8AE865E9D6F44A6064853D6A62D` |
| `arc/timg/tx_optn_10.tpl` | `0x654A0` | 3648 | 112×64 I4 | 振動 | `C3B1357DD95B978F66DD0B78393DAC471681B4A7B455510EA4B9BB3CAA637B1F` |
| `arc/timg/tx_optn_20.tpl` | `0x662E0` | 3648 | 112×64 I4 | 接続 | `B25604B9D1D124C2038E28058B6C4D6D6D4CE0BE770AB583B74FBF474606375C` |
| `arc/timg/tx_plyr_00.tpl` | `0x67120` | 640 | 48×24 I4 | 1P | `5A8BDD9CDABBB8338956290E1B42E55955224B55C28D8109D5A57864495757E4` |
| `arc/timg/tx_plyr_01.tpl` | `0x673A0` | 640 | 48×24 I4 | 2P | `7320B7D2119962ECC9D0EB6EE2959C9592C51972CEDDC37C2531347F618F7ABE` |
| `arc/timg/tx_plyr_02.tpl` | `0x67620` | 640 | 48×24 I4 | 3P | `9A90D7E8420FB96FE798B176D0EB9822E2241A1833EBBEBAF7F7D6CA435DFBE3` |
| `arc/timg/tx_plyr_03.tpl` | `0x678A0` | 640 | 48×24 I4 | 4P | `01C5C977B8192360B9BD665CD75517465457421D75A2B547026653CCE771E3BD` |
| `arc/timg/tx_ttl_wrd_a.tpl` | `0x67B20` | 7424 | 368×40 I4 | HOMEボタンメニュー | `E6DC9A3338E953A4C7D87AAD05088398676ADEDB01D2EDC344ACF29ABFDCA4DD` |

동적 문구용 폰트 `arc/font/RevoIpl_UtrilloProGrecoStd_M_32_I4.brfnt`는 archive `0x1C020`, 58236 bytes, SHA-256 `FE2E0D0E83B588F01A682DEA0FA880934642712EC78823C98F49D07037ECE6CB`다. 고유 CMAP 매핑 108개 중 **한글 음절 매핑은 0개**다. CSV만 바꾸면 한글이 나오지 않으므로 BRFNT도 재구축해야 한다.

### 4.3 엔딩 대사 이미지 23개

- 시각 증거: `work/runtime_fix/audit_renders/endroll_contact_sheet.png`, SHA-256 `A50B5001811954497FBFFB423342C8C68D7257AFBD31801398E2E33D9C85A6D8`

| 물리 파일 | 크기 | 규격 | 일본어 시각 전사 | SHA-256 |
|---|---:|---:|---|---|
| `DATA/files/Event/endroll/EV09_18_0200C_00.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | やっほー!!<br>ラルク、起きる時間だよー!! | `53A0AA80D8A551A7FAEF55B8193ECB21826BB1BFD0F10EB305522FE0AB64826E` |
| `DATA/files/Event/endroll/EV09_18_0200C_01.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | 起きろってば、おきろー!! | `9C305503A3DCF7F376F084F0AA0611964C484EC6245A6D558C9885E10A271A6E` |
| `DATA/files/Event/endroll/EV09_18_0200C_02.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | ……ん | `C371F44089AFF73D5CDCD3AE1C6463D6231C6848A1029D01CB68EBFB3C453E1A` |
| `DATA/files/Event/endroll/EV09_18_0200C_03.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | お前が目覚める時に合わせて<br>我々のメッセージを残しておく | `F21635164052C671DC9241E6860ECC52779BF2B97A1A84CF63E6516A9FC6CC1C` |
| `DATA/files/Event/endroll/EV09_18_0200C_04.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | お前が寂しがるといけないんでな。<br>気の利いたモーニングコールだろ？ | `B63A91F9645A84E57CB88BD40AA9F26A0F80D4DE67287DD833F05C63891BD2AC` |
| `DATA/files/Event/endroll/EV09_18_0200C_05.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | ソニアの計算だと<br>あなたが目覚めるのはおよそ５００年後よ | `BD85D42A904CC00253ADEB4CE7CFAAC54FD3CB0BACEA701D84C1EA0928196DC7` |
| `DATA/files/Event/endroll/EV09_18_0200C_06.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | お前が眠ってから大変だったぜ。<br>ま、アルス坊やが頑張ってくれてな | `380FD44D8BB674FFF19584DCE966E2872813B76BA4B1E33F4655313791EBB0B8` |
| `DATA/files/Event/endroll/EV09_18_0200C_07.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | 今度はましな皇帝になれそうだぜ | `E547446BA8D186149D26AB85FB9FA0BC531931EB3142070C7D1DB58ADB90C8A9` |
| `DATA/files/Event/endroll/EV09_18_0200C_08.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | 我らも全力でサポートするつもりだ | `9AF3104489B27F56C72C51FBEE82BFC6C25AB88C8D9EDB6B1F72A7F6E64FB3CF` |
| `DATA/files/Event/endroll/EV09_18_0200C_09.wtm` | 7744 | 320×48 C4/RGB5A3, data `0x40` | 私は５年たったら<br>眠りについてちゃうけどね | `38C99B044CB45F4A7527AB94C0E065B5F5DE257B16BB9EC836C5A1CF4AFA94DD` |
| `DATA/files/Event/endroll/EV09_18_0200C_10.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | 希望がある限り、人は前に向かって<br>歩いて行くことが出来る | `EEF335E27713E711FD3D696BAA2F73B0CD4EC130DC89CD931934689E63E1C20A` |
| `DATA/files/Event/endroll/EV09_18_0200C_11.wtm` | 7584 | 312×48 C4/IA8, data `0x60` | あなたが目覚める約束の日まで<br>私たちは必死で生き抜いてみせる | `C3DC64BE922010803CB4C49BD482050603F63F795971382191A53C0E108751D1` |
| `DATA/files/Event/endroll/EV09_18_0200C_12.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | みんな…… | `EED589E0AEE439620C5F0A1C262E1667E6AA3D16834F3F8E34D08EAE1F7FC868` |
| `DATA/files/Event/endroll/EV09_18_0200C_13.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | だから、安心していいよ | `1A272A2717FB736B15150B4C48B643542D1E4705CCBAFB86968D6757E69613FF` |
| `DATA/files/Event/endroll/EV09_18_0200C_14.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | ラルクが目覚めたとき<br>ラルクは独りぼっちじゃないよ | `C4A207CB2130FFC5286E4AD5554174D00E79585BED23756D347793CC6E1AD711` |
| `DATA/files/Event/endroll/EV09_18_0200C_15.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | 私たちの心を受け継いだ誰かが<br>必ずラルクを迎えてくれるわ | `FE3FB69A87C46E7EEE9F539ECDCBCB3175578894A9AD15804236CA4BEB8154AD` |
| `DATA/files/Event/endroll/EV09_18_0200C_16.wtm` | 7584 | 312×48 C4/IA8, data `0x60` | 約束する。この人の世を<br>５００年後のお前に託すことを | `F67FFAFA739CDF418F665D21CD94F60EAFE7A66A1E62F52776AD7385E922DF50` |
| `DATA/files/Event/endroll/EV09_18_0200C_17.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | ――そろそろ時間だ | `917F157FD6EA14F6741DC914A517C31037B88C3487825E39C6C507284620A51D` |
| `DATA/files/Event/endroll/EV09_18_0200C_18.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | じゃあな、ラルク。<br>お前は最高の相棒だったぜ | `FC3A56BF46E998B54511421A9B1A264C12317C34B47D1CA42C2C920F08D90C1D` |
| `DATA/files/Event/endroll/EV09_18_0200C_19.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | ばいば～い！　また未来でね！ | `5F2518C4472779017F34768ECD9D642426FC5D6D60A6A966098A37BC67D78CDE` |
| `DATA/files/Event/endroll/EV09_18_0200C_20.wtm` | 7584 | 312×48 C4/IA8, data `0x60` | お姉さんのこと<br>忘れちゃダ・メ・ヨ | `4BDD7102774AE1521F9532C167C34CABC010AE1B2B8DF6CD2FAA5F8249121801` |
| `DATA/files/Event/endroll/EV09_18_0200C_21.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | さらばだ。<br>お前と共に在れたことを誇りに思う | `E77848C2BFE3AFBEBD5D9AC2812001063FAA120EAADD09F8738A6751D1BF96C8` |
| `DATA/files/Event/endroll/EV09_18_0200C_22.wtm` | 7552 | 312×48 C4/RGB5A3, data `0x40` | ……リフィアは……<br>リフィアはどうしたんだ…… | `C833C0271A8D74D3E5A0D19AE7003A5F3193FD24899B9820CB00ACC3ABCAF211` |

이 파일들은 크레딧 장식이 아니라 엔딩 장면 대사를 표시하는 standalone WTM이다. fin.wtm은 라틴 FIN뿐이어서 제외했다.

## 5. 확정 물리 파일 목록

- `DATA/sys/main.dol`
- `DATA/files/Hbm/home.csv`
- `DATA/files/Hbm/home_nosave.csv`
- `DATA/files/Hbm/homeBtn.arc`
- `DATA/files/Event/endroll/EV09_18_0200C_00.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_01.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_02.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_03.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_04.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_05.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_06.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_07.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_08.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_09.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_10.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_11.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_12.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_13.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_14.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_15.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_16.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_17.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_18.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_19.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_20.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_21.wtm`
- `DATA/files/Event/endroll/EV09_18_0200C_22.wtm`

## 6. 수정 권고

### P0 — `DATA/sys/main.dol`

Add an executable-string lane keyed to the exact source hash. Preserve printf tokens/control bytes. Verify each source byte span before patching. Where Korean codebook bytes exceed the NUL capacity, relocate rodata and patch validated pointers/callsites rather than overwriting adjacent data.

Staging: Add a hash-bound /sys/main.dol replacement rule (or the loader-specific equivalent) and validate actual runtime interception; DATA/files rules cannot cover it.

### P0 — `DATA/files/Hbm/home.csv and home_nosave.csv`

Translate only the Japanese first column with the Codex internal model; preserve UTF-16BE BOM, CRLF, quote/tab structure, row count and all other language columns. Re-run a TSV/CSV parse and HOME overlay runtime test.

### P0 — `DATA/files/Hbm/homeBtn.arc`

Rebuild the Nintendo U8 archive with Korean replacements for the 18 same-dimension I4 text textures. Inject/rebuild the BRFNT CMAP/glyph data for every Hangul character used by the CSV prompts; the original font maps zero Hangul syllables.

### P1 — `DATA/files/Event/endroll/EV09_18_0200C_00.wtm .. _22.wtm`

Translate and typeset all 23 ending-dialogue frames at the original canvas dimensions and GX/palette formats, then replace the physical WTM files and validate the complete ending playback sequence.

### P1 — `Inventory/staging generators`

Expand source roots from DATA/files-only to explicit files+sys+banner/media lanes. Fail the build when a known user-visible physical path has no catalog/reinsertion decision. Recompute manifest counts from the final allowlist rather than hand-maintaining 655.

## 7. 남은 전수 검사

- All Movie/*.sfd streams must be sampled at scene changes/end cards to prove that no Japanese text is burned into video frames.
- opening.bnr banner.bin/icon.bin compressed graphics should be rendered once; its IMET text alone is not a complete graphic proof.
- All remaining standalone/embedded TPL/WTM/BRRES text-bearing assets outside the 48-item image lane need contact-sheet review rather than extension-based exclusion.

opening.bnr의 IMET 일본어 슬롯은 ARC RISE FANTASIA이고, fin.wtm은 FIN, homeBtnIcon.wtm은 심볼이다. 현재 확정 일본어 누락에서는 제외했지만 opening.bnr 압축 그래픽과 SFD 영상은 시각 검사가 남아 있다.

## 8. 런타임 합격 기준

- [ ] Cold boot: strap/title/controller-selection/initial-settings screen show no Japanese.
- [ ] Every initial-settings row/value/help line and controller-change confirmation is Korean with no overflow or missing glyphs.
- [ ] Press HOME in a save-enabled and no-save context: all baked buttons/headings and all CSV prompts render Korean; reconnect flow and ①/② symbols remain intact.
- [ ] Trigger load/save/no-space/NAND-error flows and verify all executable-resident prompts.
- [ ] Play the ending through all 23 dialogue frames and verify Korean text, timing, alpha/palette and clipping.
- [ ] Re-run static hashes/structure checks and publish the updated physical-file manifest before any completion claim.

---

기계 판독용 전체 목록: `work/runtime_fix/runtime_ui_gap_audit.json`

