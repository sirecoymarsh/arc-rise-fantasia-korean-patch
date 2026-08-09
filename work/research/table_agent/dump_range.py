#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

ap=argparse.ArgumentParser(); ap.add_argument('path',type=Path); ap.add_argument('start',type=lambda x:int(x,0)); ap.add_argument('length',type=lambda x:int(x,0)); ns=ap.parse_args()
d=ns.path.read_bytes(); end=min(len(d),ns.start+ns.length)
for p in range(ns.start,end,16):
    r=d[p:min(p+16,end)]
    a=''.join(chr(x) if 32<=x<127 else '.' for x in r)
    print(f'{p:08X}: {r.hex(" "):<47}  {a}')
