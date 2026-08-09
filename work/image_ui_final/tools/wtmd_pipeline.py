#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Iterable

from PIL import Image


GX_NAMES = {0: "I4", 1: "I8", 2: "IA4", 3: "IA8", 4: "RGB565", 5: "RGB5A3", 6: "RGBA32", 8: "C4", 9: "C8", 10: "C14X2", 14: "CMPR"}
PAL_NAMES = {0: "none", 1: "RGB565", 2: "RGB5A3", 3: "IA8"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expand(v: int, bits: int) -> int:
    return (v * 255 + ((1 << bits) - 1) // 2) // ((1 << bits) - 1)


def rgb565(v: int):
    return expand((v >> 11) & 31, 5), expand((v >> 5) & 63, 6), expand(v & 31, 5), 255


def rgb5a3(v: int):
    if v & 0x8000:
        return expand((v >> 10) & 31, 5), expand((v >> 5) & 31, 5), expand(v & 31, 5), 255
    return expand((v >> 8) & 15, 4), expand((v >> 4) & 15, 4), expand(v & 15, 4), expand((v >> 12) & 7, 3)


def ia8(v: int):
    return v & 255, v & 255, v & 255, (v >> 8) & 255


def parse_wtmd(data: bytes):
    if len(data) < 0x20 or data[:4] != b"WTMD":
        raise ValueError("not WTMD")
    width, height = struct.unpack_from(">HH", data, 8)
    gx, pal = data[12], data[13]
    palette_pos = struct.unpack_from("<H", data, 18)[0]
    palette_bytes = struct.unpack_from("<H", data, 16)[0]
    if gx in (8, 9, 10):
        if palette_bytes == 0:
            palette_bytes = {8: 0x20, 9: 0x200, 10: 0x8000}.get(gx, 0)
        image_pos = palette_pos + palette_bytes
    else:
        palette_bytes = 0
        image_pos = palette_pos
    bpp = {0: .5, 1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 4, 8: .5, 9: 1, 10: 2, 14: .5}[gx]
    base_bytes = int(width * height * bpp)
    if image_pos + base_bytes > len(data):
        inferred = len(data) - base_bytes
        if inferred >= 0x20:
            image_pos = inferred
            if gx in (8, 9, 10):
                palette_pos = 0x20
                palette_bytes = image_pos - palette_pos
        else:
            raise ValueError(f"bad WTMD offsets: {image_pos}+{base_bytes}>{len(data)}")
    return {"width": width, "height": height, "gx": gx, "gx_name": GX_NAMES.get(gx, f"unknown_{gx}"), "pal": pal,
            "pal_name": PAL_NAMES.get(pal, f"unknown_{pal}"), "palette_pos": palette_pos, "palette_bytes": palette_bytes,
            "image_pos": image_pos, "base_bytes": base_bytes, "size": len(data)}


def palette_rgba(data: bytes, h):
    out = []
    if h["gx"] not in (8, 9, 10):
        return out
    raw = data[h["palette_pos"]:h["image_pos"]]
    conv = {1: rgb565, 2: rgb5a3, 3: ia8}[h["pal"]]
    for i in range(0, len(raw), 2):
        if i + 2 <= len(raw):
            out.append(conv(struct.unpack_from(">H", raw, i)[0]))
    limit = {8: 16, 9: 256, 10: 16384}[h["gx"]]
    return out[:limit]


def tile_iter(width, height, tw, th):
    for by in range(0, height, th):
        for bx in range(0, width, tw):
            yield bx, by


def decode_indices(raw: bytes, w: int, h: int, gx: int):
    idx = [0] * (w * h); p = 0
    tw, th = {8: (8, 8), 9: (8, 4), 10: (4, 4)}[gx]
    for bx, by in tile_iter(w, h, tw, th):
        for y in range(th):
            for x in range(tw):
                xx, yy = bx + x, by + y
                if gx == 8:
                    if x % 2 == 0:
                        v = raw[p]; p += 1
                    q = (v >> 4) if x % 2 == 0 else (v & 15)
                elif gx == 9:
                    q = raw[p]; p += 1
                else:
                    q = struct.unpack_from(">H", raw, p)[0] & 0x3FFF; p += 2
                if xx < w and yy < h: idx[yy*w+xx] = q
    return idx


def decode_wtmd(data: bytes):
    h = parse_wtmd(data); w, ht, gx = h["width"], h["height"], h["gx"]
    raw = data[h["image_pos"]:h["image_pos"]+h["base_bytes"]]
    px = [(0,0,0,0)] * (w*ht)
    if gx in (8,9,10):
        pal = palette_rgba(data, h); idx = decode_indices(raw,w,ht,gx)
        px = [pal[i] if i < len(pal) else (255,0,255,255) for i in idx]
    elif gx == 6:
        p = 0
        for bx, by in tile_iter(w,ht,4,4):
            ar = raw[p:p+32]; gb = raw[p+32:p+64]; p += 64
            for i in range(16):
                x,y=i%4,i//4; xx,yy=bx+x,by+y
                if xx<w and yy<ht: px[yy*w+xx]=(ar[i*2+1],gb[i*2],gb[i*2+1],ar[i*2])
    elif gx == 14:
        p = 0
        for bx, by in tile_iter(w, ht, 8, 8):
            for sy in (0, 4):
                for sx in (0, 4):
                    c0v, c1v = struct.unpack_from(">HH", raw, p)
                    bits = struct.unpack_from(">I", raw, p + 4)[0]
                    p += 8
                    c0, c1 = rgb565(c0v), rgb565(c1v)
                    if c0v > c1v:
                        c2 = tuple((2*c0[i]+c1[i])//3 for i in range(3)) + (255,)
                        c3 = tuple((c0[i]+2*c1[i])//3 for i in range(3)) + (255,)
                    else:
                        c2 = tuple((c0[i]+c1[i])//2 for i in range(3)) + (255,)
                        c3 = (0, 0, 0, 0)
                    colors = (c0, c1, c2, c3)
                    for i in range(16):
                        xx, yy = bx + sx + i % 4, by + sy + i // 4
                        if xx < w and yy < ht:
                            px[yy*w+xx] = colors[(bits >> (30-2*i)) & 3]
    else:
        specs={0:(8,8),1:(8,4),2:(8,4),3:(4,4),4:(4,4),5:(4,4)}
        if gx not in specs: raise NotImplementedError(h["gx_name"])
        tw,th=specs[gx]; p=0
        for bx,by in tile_iter(w,ht,tw,th):
            for y in range(th):
                for x in range(tw):
                    if gx==0:
                        if x%2==0: v=raw[p];p+=1
                        i=((v>>4) if x%2==0 else (v&15))*17; c=(i,i,i,255)
                    elif gx==1: i=raw[p];p+=1;c=(i,i,i,255)
                    elif gx==2: v=raw[p];p+=1;i=(v&15)*17;a=(v>>4)*17;c=(i,i,i,a)
                    else:
                        v=struct.unpack_from(">H",raw,p)[0];p+=2;c=ia8(v) if gx==3 else rgb565(v) if gx==4 else rgb5a3(v)
                    xx,yy=bx+x,by+y
                    if xx<w and yy<ht:px[yy*w+xx]=c
    im=Image.new("RGBA",(w,ht));im.putdata(px);return im,h


def nearest_index(color, palette):
    r,g,b,a=color
    if a <= 8:
        amin = min(p[3] for p in palette)
        candidates = [i for i, p in enumerate(palette) if p[3] == amin]
    else:
        candidates = range(len(palette))
    return min(candidates, key=lambda i: (palette[i][0]-r)**2+(palette[i][1]-g)**2+(palette[i][2]-b)**2+4*(palette[i][3]-a)**2)


def encode_indices(indices, w, h, gx):
    out=bytearray();tw,th={8:(8,8),9:(8,4),10:(4,4)}[gx]
    for bx,by in tile_iter(w,h,tw,th):
        for y in range(th):
            x=0
            while x<tw:
                def val(xx):
                    px,py=bx+xx,by+y
                    return indices[py*w+px] if px<w and py<h else 0
                if gx==8: out.append(((val(x)&15)<<4)|(val(x+1)&15));x+=2
                elif gx==9: out.append(val(x)&255);x+=1
                else: out += struct.pack(">H", val(x)&0x3FFF);x+=1
    return bytes(out)


def encode_wtmd(original: bytes, image: Image.Image):
    h=parse_wtmd(original);w,ht,gx=h["width"],h["height"],h["gx"]
    if image.size!=(w,ht): raise ValueError(f"size changed {image.size}!={(w,ht)}")
    rgba=list(image.convert("RGBA").getdata())
    if gx in (8,9,10):
        pal=palette_rgba(original,h); cache={}; idx=[]
        for c in rgba:
            if c not in cache: cache[c]=nearest_index(c,pal)
            idx.append(cache[c])
        raw=encode_indices(idx,w,ht,gx)
    elif gx==6:
        raw=bytearray()
        for bx,by in tile_iter(w,ht,4,4):
            tile=[]
            for y in range(4):
                for x in range(4):
                    xx,yy=bx+x,by+y;tile.append(rgba[yy*w+xx] if xx<w and yy<ht else (0,0,0,0))
            for r,g,b,a in tile: raw += bytes((a,r))
            for r,g,b,a in tile: raw += bytes((g,b))
        raw=bytes(raw)
    else: raise NotImplementedError(f"encoding {h['gx_name']}")
    if len(raw)!=h["base_bytes"]: raise AssertionError((len(raw),h["base_bytes"]))
    out=bytearray(original);out[h["image_pos"]:h["image_pos"]+len(raw)]=raw
    return bytes(out),h


def decompress_lz10(data: bytes):
    if data[:1]!=b"\x10": raise ValueError("not LZ10")
    expected=int.from_bytes(data[1:4],"little");src=4;out=bytearray()
    while len(out)<expected:
        flags=data[src];src+=1
        for bit in range(7,-1,-1):
            if len(out)>=expected: break
            if flags&(1<<bit):
                a,b=data[src],data[src+1];src+=2;ln=(a>>4)+3;dist=(((a&15)<<8)|b)+1
                for _ in range(ln):out.append(out[-dist])
            else:out.append(data[src]);src+=1
    return bytes(out[:expected])


def compress_lz10(data: bytes):
    out=bytearray(b"\x10"+len(data).to_bytes(3,"little"));positions={};i=0
    while i<len(data):
        flag_pos=len(out);out.append(0);flags=0;group=bytearray()
        for bit in range(7,-1,-1):
            if i>=len(data):break
            best_len=0;best_dist=0
            if i+3<=len(data):
                key=bytes(data[i:i+3]);cand=positions.get(key,[])
                while cand and i-cand[0]>4096:cand.pop(0)
                for p in reversed(cand[-128:]):
                    maxlen=min(18,len(data)-i);ln=3
                    while ln<maxlen and data[p+ln]==data[i+ln]:ln+=1
                    if ln>best_len:best_len=ln;best_dist=i-p
                    if ln==18:break
            if best_len>=3:
                flags|=1<<bit;v=((best_len-3)<<12)|(best_dist-1);group+=bytes((v>>8,v&255));step=best_len
            else:group.append(data[i]);step=1
            for q in range(i,i+step):
                if q+3<=len(data): positions.setdefault(bytes(data[q:q+3]),[]).append(q)
            i+=step
        out[flag_pos]=flags;out+=group
    while len(out)%4:out.append(0)
    return bytes(out)


def cmd_decode(args):
    raw=args.input.read_bytes();payload=decompress_lz10(raw) if args.input.suffix.lower()==".cxd" else raw
    if args.payload: args.payload.write_bytes(payload)
    im,h=decode_wtmd(payload);args.output.parent.mkdir(parents=True,exist_ok=True);im.save(args.output)
    print(json.dumps({"input":str(args.input),"output":str(args.output),"input_sha256":sha256(raw),"payload_sha256":sha256(payload),**h},indent=2))


def cmd_encode(args):
    raw=args.original.read_bytes();payload=decompress_lz10(raw) if args.original.suffix.lower()==".cxd" else raw
    edited=Image.open(args.png).convert("RGBA");rebuilt,h=encode_wtmd(payload,edited)
    out=compress_lz10(rebuilt) if args.original.suffix.lower()==".cxd" else rebuilt
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(out)
    if args.payload: args.payload.write_bytes(rebuilt)
    print(json.dumps({"output":str(args.output),"original_sha256":sha256(raw),"payload_sha256":sha256(rebuilt),"output_sha256":sha256(out),"output_bytes":len(out),**h},indent=2))


def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True)
    d=sp.add_parser("decode");d.add_argument("input",type=Path);d.add_argument("output",type=Path);d.add_argument("--payload",type=Path);d.set_defaults(func=cmd_decode)
    e=sp.add_parser("encode");e.add_argument("original",type=Path);e.add_argument("png",type=Path);e.add_argument("output",type=Path);e.add_argument("--payload",type=Path);e.set_defaults(func=cmd_encode)
    a=ap.parse_args();a.func(a)


if __name__=="__main__":main()
