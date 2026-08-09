#!/usr/bin/env python3
"""Replace only video payload bytes in a Sofdec SFD MPEG program stream.

The trusted SFD remains the container/timestamp/audio template.  A CBR MPEG-1
elementary stream is written sequentially into the original E0 PES payload
capacity.  Unused trailing E0 packets become MPEG padding packets.  Every ADX
audio PES packet, Sofdec metadata packet, pack header, timestamp and file byte
outside the explicit video allowlist is preserved exactly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def pes_payload_offset(buf: bytes | bytearray, pos: int, end: int) -> int:
    i = pos + 6
    if i >= end:
        raise ValueError("truncated PES")
    if buf[i] & 0xC0 == 0x80:  # MPEG-2 PES header
        if i + 3 > end:
            raise ValueError("truncated MPEG-2 PES header")
        return i + 3 + buf[i + 2]
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


def packet_ranges(buf: bytes | bytearray):
    pos, size = 0, len(buf)
    while pos + 4 <= size:
        if buf[pos:pos + 3] != b"\x00\x00\x01":
            nxt = buf.find(b"\x00\x00\x01", pos + 1)
            if nxt < 0:
                break
            pos = nxt
            continue
        sid = buf[pos + 3]
        if sid == 0xBA:
            end = pos + (14 + (buf[pos + 13] & 7) if pos + 14 <= size and buf[pos + 4] & 0xC0 == 0x40 else 12)
        elif sid == 0xB9:
            end = pos + 4
        else:
            if pos + 6 > size:
                raise ValueError("truncated packet header")
            end = pos + 6 + int.from_bytes(buf[pos + 4:pos + 6], "big")
        if end <= pos or end > size:
            raise ValueError(f"invalid packet at 0x{pos:X}")
        yield pos, end, sid
        pos = end


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source_sfd", type=Path)
    ap.add_argument("video_es", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("report", type=Path)
    args = ap.parse_args()

    source = args.source_sfd.read_bytes()
    video = args.video_es.read_bytes()
    if not video.startswith(b"\x00\x00\x01\xB3"):
        raise ValueError("video input is not an MPEG-1 elementary stream")
    buf = bytearray(source)
    video_packets: list[tuple[int, int, int]] = []
    audio_packets: list[tuple[int, int]] = []
    private_packets: list[tuple[int, int]] = []
    for pos, end, sid in packet_ranges(buf):
        if sid == 0xE0:
            payload = pes_payload_offset(buf, pos, end)
            video_packets.append((pos, payload, end))
        elif sid == 0xC0:
            audio_packets.append((pos, end))
        elif sid == 0xBF:
            private_packets.append((pos, end))
    capacity = sum(end - payload for _, payload, end in video_packets)
    if len(video) > capacity:
        raise ValueError(f"localized video exceeds original capacity: {len(video)} > {capacity}")

    allowed = bytearray(len(source))
    cursor = 0
    converted_to_padding = 0
    partial_packet_padding = 0
    for pos, payload, end in video_packets:
        room = end - payload
        if cursor >= len(video):
            buf[pos + 3] = 0xBE
            allowed[pos + 3] = 1
            converted_to_padding += 1
            continue
        count = min(room, len(video) - cursor)
        buf[payload:payload + count] = video[cursor:cursor + count]
        allowed[payload:payload + count] = b"\x01" * count
        cursor += count
        if count < room:
            # The elementary stream already terminates with sequence_end_code.
            # Zero tail bytes are confined to this final, partially used PES.
            buf[payload + count:end] = b"\x00" * (room - count)
            allowed[payload + count:end] = b"\x01" * (room - count)
            partial_packet_padding = room - count
    if cursor != len(video):
        raise AssertionError((cursor, len(video)))

    output = bytes(buf)
    unexpected = [index for index, (before, after) in enumerate(zip(source, output))
                  if before != after and not allowed[index]]
    if unexpected:
        raise ValueError(f"changes outside video allowlist: {unexpected[:20]}")
    if any(source[start:end] != output[start:end] for start, end in audio_packets):
        raise ValueError("ADX audio PES bytes changed")
    if any(source[start:end] != output[start:end] for start, end in private_packets):
        raise ValueError("Sofdec private metadata bytes changed")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    report = {
        "schema": "arf-ko-sfd-video-payload-replacement-v1",
        "valid": True,
        "source_sfd": str(args.source_sfd),
        "source_sfd_sha256": sha256(source),
        "source_size": len(source),
        "localized_video_es": str(args.video_es),
        "localized_video_es_sha256": sha256(video),
        "localized_video_es_bytes": len(video),
        "video_pes_packets": len(video_packets),
        "video_pes_capacity": capacity,
        "unused_video_capacity": capacity - len(video),
        "trailing_video_packets_converted_to_padding": converted_to_padding,
        "final_partial_packet_zero_padding": partial_packet_padding,
        "audio_pes_packets": len(audio_packets),
        "audio_pes_packets_byte_exact": True,
        "sofdec_private_packets": len(private_packets),
        "sofdec_private_packets_byte_exact": True,
        "changes_outside_video_allowlist": len(unexpected),
        "file_size_preserved": len(output) == len(source),
        "output": str(args.output),
        "output_size": len(output),
        "output_sha256": sha256(output),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
