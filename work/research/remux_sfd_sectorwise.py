#!/usr/bin/env python3
"""Build a Sofdec SFD from localized video and byte-exact original ADX sectors.

Both the source SFD and FFmpeg's MPEG-PS video template are 2048-byte sector
streams.  The source's four metadata sectors and every original C0 audio PES
packet are retained.  Template audio sectors are discarded; localized video
sectors and reconstructed audio-only sectors are merged by pack SCR.  This
keeps ADX packetization, timestamps and bytes intact while replacing only the
video elementary stream.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SECTOR = 2048
PACK = b"\x00\x00\x01\xBA"
AUDIO = b"\x00\x00\x01\xC0"
VIDEO = b"\x00\x00\x01\xE0"
PRIVATE2 = b"\x00\x00\x01\xBF"
PROGRAM_END = b"\x00\x00\x01\xB9"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sectors(data: bytes) -> list[bytes]:
    if len(data) % SECTOR:
        raise ValueError(f"stream size is not sector aligned: {len(data)}")
    return [data[pos:pos + SECTOR] for pos in range(0, len(data), SECTOR)]


def scr90k(sector: bytes) -> int:
    if not sector.startswith(PACK) or len(sector) < 12:
        raise ValueError("sector does not start with an MPEG-1 pack header")
    b4, b5, b6, b7, b8 = sector[4:9]
    if b4 & 0xF0 != 0x20:
        raise ValueError("only MPEG-1 pack headers are supported")
    return (
        ((b4 >> 1) & 0x07) << 30
        | b5 << 22
        | ((b6 >> 1) & 0x7F) << 15
        | b7 << 7
        | ((b8 >> 1) & 0x7F)
    )


def pes_packet(sector: bytes, marker: bytes) -> bytes:
    pos = sector.find(marker)
    if pos < 0 or pos + 6 > len(sector):
        raise ValueError("requested PES packet is absent or truncated")
    end = pos + 6 + int.from_bytes(sector[pos + 4:pos + 6], "big")
    if end > len(sector):
        raise ValueError("PES packet crosses sector boundary")
    return sector[pos:end]


def audio_only_sector(source_sector: bytes) -> bytes:
    """Preserve pack and C0 PES bytes, replacing any video tail with padding."""
    if not source_sector.startswith(PACK):
        raise ValueError("audio source sector has no pack header")
    packet = pes_packet(source_sector, AUDIO)
    # Source audio sectors use a 12-byte MPEG-1 pack header.  A rare shared
    # audio/video sector is normalized to pack + exact C0 packet + padding.
    prefix = source_sector[:12]
    remaining = SECTOR - len(prefix) - len(packet)
    if remaining < 6:
        raise ValueError(f"not enough room for padding packet: {remaining}")
    padding = b"\x00\x00\x01\xBE" + (remaining - 6).to_bytes(2, "big") + b"\xFF" * (remaining - 6)
    result = prefix + packet + padding
    if len(result) != SECTOR:
        raise AssertionError(len(result))
    return result


def extract_audio_es(items: list[bytes]) -> bytes:
    return b"".join(pes_packet(item, AUDIO)[6 + _pes_header_length(pes_packet(item, AUDIO)):] for item in items)


def _pes_header_length(packet: bytes) -> int:
    """Length after the six-byte PES prefix before elementary payload."""
    i = 6
    while i < len(packet) and packet[i] == 0xFF:
        i += 1
    if i < len(packet) and packet[i] & 0xC0 == 0x40:
        i += 2
    if i >= len(packet):
        raise ValueError("truncated MPEG-1 PES header")
    marker = packet[i] & 0xF0
    if marker == 0x20:
        i += 5
    elif marker == 0x30:
        i += 10
    elif packet[i] == 0x0F:
        i += 1
    else:
        raise ValueError(f"unknown MPEG-1 PES marker 0x{packet[i]:02X}")
    return i - 6


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source_sfd", type=Path)
    ap.add_argument("video_template", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("report", type=Path)
    args = ap.parse_args()

    source_data = args.source_sfd.read_bytes()
    template_data = args.video_template.read_bytes()
    source = sectors(source_data)
    template = sectors(template_data)

    first_media = next(index for index, item in enumerate(source) if AUDIO in item or VIDEO in item)
    metadata = source[:first_media]
    if first_media != 4 or not any(PRIVATE2 in item for item in metadata):
        raise ValueError(f"unexpected Sofdec metadata prefix: {first_media} sectors")

    original_audio_sectors = [item for item in source[first_media:] if AUDIO in item]
    rebuilt_audio_sectors = [audio_only_sector(item) for item in original_audio_sectors]
    localized_video_sectors = [item for item in template if AUDIO not in item and item.startswith(PACK)]
    if not localized_video_sectors or any(AUDIO in item for item in localized_video_sectors):
        raise ValueError("localized video sector selection failed")

    multiplexed = [(scr90k(item), 0, index, item) for index, item in enumerate(rebuilt_audio_sectors)]
    multiplexed += [(scr90k(item), 1, index, item) for index, item in enumerate(localized_video_sectors)]
    multiplexed.sort(key=lambda row: (row[0], row[1], row[2]))

    end_sector = source[-1]
    if not end_sector.startswith(PROGRAM_END):
        raise ValueError("source SFD has no final program-end sector")
    output_data = b"".join(metadata + [row[3] for row in multiplexed] + [end_sector])

    # Prove that every original audio PES packet is retained byte-for-byte and
    # in order.  Only two shared sectors are structurally normalized.
    output_items = sectors(output_data)
    output_audio_sectors = [item for item in output_items if AUDIO in item]
    source_audio_packets = [pes_packet(item, AUDIO) for item in original_audio_sectors]
    output_audio_packets = [pes_packet(item, AUDIO) for item in output_audio_sectors]
    if source_audio_packets != output_audio_packets:
        raise ValueError("output audio PES sequence differs from original")
    source_audio_es = extract_audio_es(original_audio_sectors)
    output_audio_es = extract_audio_es(output_audio_sectors)
    if source_audio_es != output_audio_es:
        raise ValueError("output ADX elementary bytes differ from original")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_data)
    report = {
        "schema": "arf-ko-sfd-sector-remux-v1",
        "valid": True,
        "source_sfd": str(args.source_sfd),
        "source_sfd_sha256": sha256(source_data),
        "video_template": str(args.video_template),
        "video_template_sha256": sha256(template_data),
        "metadata_sectors_preserved": len(metadata),
        "localized_video_sectors": len(localized_video_sectors),
        "original_audio_sectors": len(original_audio_sectors),
        "audio_pes_packets_byte_exact": True,
        "audio_elementary_bytes": len(source_audio_es),
        "audio_elementary_sha256": sha256(source_audio_es),
        "audio_elementary_byte_exact": True,
        "shared_audio_video_sectors_normalized": sum(VIDEO in item for item in original_audio_sectors),
        "program_end_sector_preserved": True,
        "output": str(args.output),
        "output_size": len(output_data),
        "output_sector_count": len(output_data) // SECTOR,
        "output_sha256": sha256(output_data),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
