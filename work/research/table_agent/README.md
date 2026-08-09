# ARF non-BSCR table tool

## Catalog

```powershell
python arf_table_tool.py catalog <input> <catalog.json>
```

`catalog.json`에서 번역 대상 unit의 `replacement_hex`만 채운다. 한글 문자열을 직접 넣지 않고, 프로젝트의 한글 폰트/코드포인트 맵으로 인코딩된 바이트를 16진수로 넣는다.

## Apply

```powershell
python arf_table_tool.py apply <input> <catalog.json> <output>
```

현재 고정 크기 RTDP 부모 안의 `quest.bin`을 만들 때:

```powershell
python arf_table_tool.py apply <quest.bin> <quest.json> <output> --quest-fixed-size
```

## Byte-exact no-op

```powershell
python arf_table_tool.py noop <input> <output> --catalog-output <catalog.json>
python run_roundtrip_suite.py
```

전체 스키마와 검증 결과는 `RESEARCH_REPORT.md`, `roundtrip_proof.json`에 있다.
