# Wii 실기 설치 — Riivolution 파일 로딩 방식

이 방식은 ISO/RVZ를 새로 만들지 않습니다. 일본판 정품 디스크에서 읽는 파일을 SD 카드의 한국어 파일로 실시간 대체합니다.

## 준비물

- 홈브류 채널과 Riivolution이 설치된 Wii
- FAT32 SD 카드
- 일본판 정품 디스크 `RPJJ99`
- 최신 `Arc_Rise_Fantasia_Korean_Riivolution_v1.1.3.zip`

## 설치

1. ZIP의 압축을 완전히 풉니다.
2. `payload/riivolution_sd` **안의** 다음 두 폴더를 SD 카드 최상위에 복사합니다.
   - `arc_rise_fantasia_ko_full`
   - `riivolution`
3. 복사 후 다음 경로가 존재하는지 확인합니다.
   - `SD:/arc_rise_fantasia_ko_full/files/...`
   - `SD:/riivolution/arc_rise_fantasia_ko_full.xml`
4. SD 카드를 Wii에 넣고 일본판 정품 디스크를 삽입합니다.
5. 홈브류 채널에서 Riivolution을 실행합니다.
6. `Arc Rise Fantasia` 항목의 `Korean Full Text Patch`를 `Enabled`로 설정합니다.
7. `Launch`를 눌러 실행합니다.

## 흔한 실수

- `SD:/riivolution_sd/...`처럼 **중간 `riivolution_sd` 폴더를 만들면 안 됩니다.** 그 안의 두 폴더가 SD 카드 루트에 바로 와야 합니다.
- `SD:/riivolution/` 전체를 삭제하면 다른 게임의 Riivolution 패치도 사라질 수 있습니다.
- USB 로더가 Riivolution XML 파일 로딩을 지원하지 않으면 이 방식을 사용할 수 없습니다. 그 경우 원클릭 ROM 패처에서 ISO를 만든 뒤 해당 USB 로더의 통상적인 방식으로 넣습니다.

## 제거

다음 두 항목만 삭제합니다.

- `SD:/arc_rise_fantasia_ko_full`
- `SD:/riivolution/arc_rise_fantasia_ko_full.xml`
