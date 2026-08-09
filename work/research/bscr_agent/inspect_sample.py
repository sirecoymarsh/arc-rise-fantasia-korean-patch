#!/usr/bin/env python3
from __future__ import annotations

import struct
from pathlib import Path


path = Path("work/research/rtdp_agent/fixtures/fc_00_001/payloads/0000__fc_00_001.bscr")
data = path.read_bytes()
pool_start, code_start = struct.unpack_from(">II", data, 0x34)

pos = pool_start
index = 0
while pos < 0x3AC:
    end = data.find(b"\0", pos, 0x3AC)
    if end < 0:
        break
    raw = data[pos:end]
    if raw:
        try:
            text = raw.decode("euc_jp")
        except UnicodeDecodeError:
            text = repr(raw)
        print(index, hex(pos), hex(pos - pool_start), len(raw), text)
    index += 1
    pos = end + 1

print("\nPOINTER CANDIDATES FOR STRING STARTS")
pos = pool_start
while pos < 0x3AC:
    end = data.find(b"\0", pos, 0x3AC)
    if end < 0:
        break
    raw = data[pos:end]
    if raw:
        for label, value in (("abs", pos), ("rel", pos - pool_start)):
            needle = struct.pack(">I", value)
            hits = []
            cursor = 0
            while True:
                hit = data.find(needle, cursor)
                if hit < 0:
                    break
                if hit < pool_start or hit >= 0x3AC:
                    hits.append(hit)
                cursor = hit + 1
            if hits:
                print(hex(pos), raw[:24], label, hex(value), [hex(x) for x in hits])
    pos = end + 1
