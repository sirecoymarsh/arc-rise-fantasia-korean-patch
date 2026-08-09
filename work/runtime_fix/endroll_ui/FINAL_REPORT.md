# Arc Rise Fantasia 엔딩 대사 WTM 한국어화 보고서

## 결과

- 대상: `Event/endroll/EV09_18_0200C_00.wtm` ~ `_22.wtm`
- 완료: **23/23**
- 번역: **Codex 내부 모델만 사용**
- 외부 번역 서비스: **사용하지 않음**
- staging/release 반영: **하지 않음**

## 구조 검증

- GX 형식: C4 유지
- 팔레트: 원본 RGB5A3/IA8 및 헤더·팔레트 바이트 보존
- 크기: 원본과 출력 파일의 크기 동일
- 캔버스: 312x48 또는 320x48 유지
- 독립 2회 인코딩: 23/23 byte-exact
- decode/re-encode: 23/23 byte-exact
- 텍스트 경계 여백: 23/23 PASS
- 구조 검증 오류: 0

## 결정론 및 해시

- 23개 payload 집합 SHA-256: `3AD4024E673672EDAA5E9DD2101CFBA9043B11A408B5410757F5B441A5FD9FCE`
- `translation_map.json`: `B59710387DE9A8D6C36223212B07CBCF3A63D7D8A63697927F60606FC95B20B6`
- `structural_validation.json`: `20B665CB35F9B49BB521BD41C3283955B06A788115B090351C4866B76171FFC1`
- `manifest.json`: `33850936302940B2A2069C5E9C436F35C84EBC676E2612C99976457EB028CB4F`
- 전 contact sheet: `D222B890D46EDE8D7F0AE0FEC86C0191D095C00281185E0D4EAB18AB41A1955F`
- 후 contact sheet: `E7E57860E5D6D376CFA47552E90FE8AF9E6F5C01EA9748872E5F088A306152E6`

## 시각 검증

- 23개 프레임 모두 한국어 표시
- 눈에 보이는 일본어 잔류 0
- 잘림·겹침 0
- 1~2행 제한 준수
- 원본과 유사한 흰색 본문 및 어두운 외곽선 유지

자세한 행별 증거는 `translation_map.json`, `structural_validation.json`, `visual_validation.json`, `manifest.json`에 기록했다.
