#!/usr/bin/env python3
"""Replace MPEG-PS audio PES payload bytes with a complete ADX elementary stream.

FFmpeg can demux CRI ADX from Sofdec/SFD but its stock MPEG-PS muxer refuses
ADX.  This tool uses a deterministic MP2-bearing MPEG-PS as a packet/timestamp
template, preserving all video and pack data while substituting the audio
elementary bytes inside stream 0xC0 PES packets.  Extra template audio capacity
is zero-filled after the ADX stream's declared end.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def pes_payload_offset(buf: bytearray, pos: int, end: int) -> int:
    i = pos + 6
    if i >= end:
        raise ValueError("truncated PES")
    # MPEG-2 PES optional header.
    if buf[i] & 0xC0 == 0x80:
        if i + 3 > end:
            raise ValueError("truncated MPEG-2 PES header")
        return i + 3 + buf[i + 2]
    # MPEG-1 PES header.
    while i < end and buf[i] == 0xFF:
        i += 1
    if i < end and buf[i] & 0xC0 == 0x40:
        i += 2
    if i >= end:
        raise ValueError("truncated MPEG-1 PES header")
    marker = buf[i] & 0xF0
    if marker == 0x20:
        i += 5
    elif marker == 0x30:
        i += 10
    elif buf[i] == 0x0F:
        i += 1
    else:
        raise ValueError(f"unknown MPEG-1 PES marker 0x{buf[i]:02X} at 0x{i:X}")
    return i


def packet_ranges(buf: bytearray):
    pos, n = 0, len(buf)
    while pos + 4 <= n:
        if buf[pos:pos + 3] != b"\x00\x00\x01":
            nxt = buf.find(b"\x00\x00\x01", pos + 1)
            if nxt < 0:
                break
            pos = nxt
            continue
        sid = buf[pos + 3]
        if sid == 0xBA:  # pack header
            if pos + 14 <= n and (buf[pos + 4] & 0xC0) == 0x40:
                end = pos + 14 + (buf[pos + 13] & 7)
            else:
                end = pos + 12
        elif sid == 0xB9:  # program end
            end = pos + 4
        elif sid in (0xB3, 0xB8):
            # These are video elementary start codes and should only occur when
            # resynchronizing malformed input, never at the PS top level.
            nxt = buf.find(b"\x00\x00\x01", pos + 4)
            end = n if nxt < 0 else nxt
        else:
            if pos + 6 > n:
                raise ValueError("truncated PS packet header")
            end = pos + 6 + int.from_bytes(buf[pos + 4:pos + 6], "big")
        if end <= pos or end > n:
            raise ValueError(f"invalid PS packet size at 0x{pos:X}: end=0x{end:X}")
        yield pos, end, sid
        pos = end


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("template", type=Path)
    ap.add_argument("adx", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("report", type=Path)
    args = ap.parse_args()
    original_template = args.template.read_bytes()
    adx = args.adx.read_bytes()
    if len(adx) < 16 or adx[:2] != b"\x80\x00":
        raise SystemExit("input does not look like a CRI ADX elementary stream")
    buf = bytearray(original_template)
    ranges = []
    for pos, end, sid in packet_ranges(buf):
        if sid != 0xC0:
            continue
        payload = pes_payload_offset(buf, pos, end)
        if payload > end:
            raise ValueError("PES header exceeds packet")
        ranges.append((payload, end))
    capacity = sum(end - start for start, end in ranges)
    if len(adx) > capacity:
        raise SystemExit(f"ADX exceeds template capacity: {len(adx)} > {capacity}")
    cursor = 0
    for start, end in ranges:
        count = min(end - start, len(adx) - cursor)
        if count:
            buf[start:start + count] = adx[cursor:cursor + count]
            cursor += count
        if start + count < end:
            buf[start + count:end] = b"\0" * (end - start - count)
    if cursor != len(adx):
        raise AssertionError((cursor, len(adx)))
    out = bytes(buf)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    # Only audio PES payload bytes may differ from the template.
    allowed = bytearray(len(buf))
    for start, end in ranges:
        allowed[start:end] = b"\1" * (end - start)
    unexpected = sum(1 for i, (a, b) in enumerate(zip(original_template, out))
                     if a != b and not allowed[i])
    report = {
        "schema": "arf-ko-sfd-adx-remux-v1",
        "valid": unexpected == 0,
        "template": str(args.template),
        "template_sha256": sha256(original_template),
        "adx": str(args.adx),
        "adx_sha256": sha256(adx),
        "adx_bytes": len(adx),
        "audio_pes_packet_count": len(ranges),
        "audio_pes_capacity": capacity,
        "audio_padding_bytes": capacity - len(adx),
        "unexpected_diff_bytes": unexpected,
        "output": str(args.output),
        "output_size": len(out),
        "output_sha256": sha256(out),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
