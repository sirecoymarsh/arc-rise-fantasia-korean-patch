#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, mmap, struct
from pathlib import Path


ACTION_NAME_PREFIXES = {
    bytes.fromhex(value)
    for value in (
        "00010000",
        "00020000",
        "00020001",
        "00030000",
        "00040000",
        "02020000",
        "02040000",
    )
}
ALTERNATE_DISPLAY_NAME_OFFSETS = (0x404, 0x4D0, 0x59C)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def contains_japanese(text: str) -> bool:
    return any(0x3000 <= ord(c) <= 0x30FF or 0x3400 <= ord(c) <= 0x9FFF or 0xF900 <= ord(c) <= 0xFAFF or 0xFF01 <= ord(c) <= 0xFFEF for c in text)


def lz10_decompress(packed: bytes) -> bytes:
    if len(packed) < 4 or packed[0] != 0x10:
        raise ValueError('not Nintendo LZ10')
    wanted = int.from_bytes(packed[1:4], 'little')
    out = bytearray()
    pos = 4
    while len(out) < wanted:
        if pos >= len(packed):
            raise ValueError('truncated LZ10 flags')
        flags = packed[pos]
        pos += 1
        for bit in range(7, -1, -1):
            if len(out) >= wanted:
                break
            if flags & (1 << bit):
                if pos + 2 > len(packed):
                    raise ValueError('truncated LZ10 backreference')
                a, b = packed[pos], packed[pos + 1]
                pos += 2
                length = (a >> 4) + 3
                distance = ((a & 0x0F) << 8 | b) + 1
                if distance > len(out):
                    raise ValueError('invalid LZ10 distance')
                for _ in range(length):
                    out.append(out[-distance])
                    if len(out) >= wanted:
                        break
            else:
                if pos >= len(packed):
                    raise ValueError('truncated LZ10 literal')
                out.append(packed[pos])
                pos += 1
    return bytes(out)


def parse_header(header: bytes, vld_size: int):
    if header[:4] != b'RVLX':
        raise ValueError('bad RVLX magic')
    header_size, count, declared = struct.unpack_from('>III', header, 4)
    if header_size != len(header) or declared != vld_size + header_size:
        raise ValueError(f'RVLX geometry mismatch {header_size}/{len(header)} {declared}/{vld_size}')
    if 0x20 + count * 8 > header_size:
        raise ValueError('RVLX table overflow')
    entries = []
    for index in range(count):
        size, offset = struct.unpack_from('>II', header, 0x20 + index * 8)
        next_offset = struct.unpack_from('>I', header, 0x20 + (index + 1) * 8 + 4)[0] if index + 1 < count else vld_size
        if offset + size > vld_size or next_offset < offset + size:
            raise ValueError(f'RVLX entry {index} range')
        entries.append({'index': index, 'packed_size': size, 'offset': offset, 'slot_size': next_offset - offset})
    return entries


def decode_field(data: bytes, offset: int, capacity: int):
    slot = data[offset:offset + capacity]
    end = slot.find(b'\0')
    if end < 0:
        return None
    raw = slot[:end]
    if not raw:
        return None
    try:
        text = raw.decode('euc_jp')
    except UnicodeDecodeError:
        return None
    if not contains_japanese(text):
        return None
    return {'offset': offset, 'capacity': capacity, 'raw_hex': raw.hex().upper(), 'source_text': text}


def overlaps(field: dict[str, object], units: list[dict[str, object]]) -> bool:
    start = int(field['offset'])
    end = start + int(field['capacity'])
    return any(start < int(unit['offset']) + int(unit['capacity']) and int(unit['offset']) < end for unit in units)


def scan_payload(data: bytes, index: int):
    if data[:4] != b'BTEM':
        raise ValueError(f'entry {index}: bad BTEM magic')
    name_offset = struct.unpack_from('>I', data, 8)[0]
    name = decode_field(data, name_offset, 35)
    if name is None:
        raise ValueError(f'entry {index}: missing display name at 0x{name_offset:X}')
    name.update({'id': f'btl_enemy:{index}:display_name', 'field': 'display_name'})

    part_names = []
    if index == 204:
        for part_index, part_offset in enumerate((0x348, 0x368, 0x388)):
            part = decode_field(data, part_offset, 32)
            if part is None:
                raise ValueError(f'entry {index}: missing part name {part_index} at 0x{part_offset:X}')
            part.update({'id': f'btl_enemy:{index}:part:{part_index}', 'field': 'part_name'})
            part_names.append(part)

    alternate_names = []
    for alternate_index, alternate_offset in enumerate(ALTERNATE_DISPLAY_NAME_OFFSETS):
        alternate = decode_field(data, alternate_offset, 36)
        if alternate is None:
            continue
        if alternate['source_text'] != name['source_text']:
            raise ValueError(
                f'entry {index}: alternate name at 0x{alternate_offset:X} differs: '
                f"{alternate['source_text']!r} != {name['source_text']!r}"
            )
        alternate.update({
            'id': f'btl_enemy:{index}:alternate_display_name:{alternate_index}',
            'field': 'alternate_display_name',
            'slot_kind': 'alternate_target_or_action_name',
        })
        alternate_names.append(alternate)

    skills = []
    default_skill = decode_field(data, 0x460, 32)
    if default_skill is not None:
        default_skill.update({
            'id': f'btl_enemy:{index}:skill:{len(skills)}',
            'field': 'skill_name',
            'marker_offset': 0x45C,
            'slot_kind': 'default_action',
        })
        skills.append(default_skill)

    cursor = 0
    marker = b'\x00\x00\x00\x3C'
    first_rtdp = data.find(b'RTDP', name_offset + 36)
    scan_end = first_rtdp if first_rtdp >= 0 else len(data)
    while True:
        marker_at = data.find(marker, cursor, scan_end)
        if marker_at < 0:
            break
        field = decode_field(data, marker_at + 4, 32)
        if field is not None:
            field.update({
                'id': f'btl_enemy:{index}:skill:{len(skills)}',
                'field': 'skill_name',
                'marker_offset': marker_at,
                'slot_kind': 'action_record_marker_0x3c',
            })
            skills.append(field)
        cursor = marker_at + 4

    known_units = [name, *part_names, *alternate_names, *skills]
    for offset in range(4, max(4, scan_end - 31)):
        if data[offset - 4:offset] not in ACTION_NAME_PREFIXES:
            continue
        field = decode_field(data, offset, 32)
        if field is None or overlaps(field, known_units):
            continue
        field.update({
            'id': f'btl_enemy:{index}:skill:{len(skills)}',
            'field': 'skill_name',
            'marker_offset': offset - 4,
            'slot_kind': 'action_record_nonstandard_prefix',
            'action_prefix_hex': data[offset - 4:offset].hex().upper(),
        })
        skills.append(field)
        known_units.append(field)

    return name, part_names, alternate_names, skills, first_rtdp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--header', type=Path, required=True)
    ap.add_argument('--vld', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ns = ap.parse_args()
    header = ns.header.read_bytes()
    entries = parse_header(header, ns.vld.stat().st_size)
    units = []
    payloads = []
    with ns.vld.open('rb') as handle:
        mm = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            for entry in entries:
                packed = mm[entry['offset']:entry['offset'] + entry['packed_size']]
                unpacked = lz10_decompress(packed)
                name, part_names, alternate_names, skills, first_rtdp = scan_payload(unpacked, entry['index'])
                units.append(name)
                units.extend(part_names)
                units.extend(alternate_names)
                units.extend(skills)
                payloads.append({
                    **entry,
                    'packed_sha256': sha256_bytes(packed),
                    'unpacked_size': len(unpacked),
                    'unpacked_sha256': sha256_bytes(unpacked),
                    'first_rtdp_offset': first_rtdp,
                    'display_name': name['source_text'],
                    'part_name_count': len(part_names),
                    'alternate_display_name_count': len(alternate_names),
                    'skill_count': len(skills),
                })
                if entry['index'] % 25 == 0:
                    print(f"{entry['index']}/{len(entries)} {name['source_text']} skills={len(skills)} alt_names={len(alternate_names)}")
        finally:
            mm.close()
    duplicate_ids = len(units) - len({u['id'] for u in units})
    report = {
        'schema': 'arf-btl-enemy-text-catalog-v3',
        'header': str(ns.header.resolve()),
        'vld': str(ns.vld.resolve()),
        'header_sha256': sha256_bytes(header),
        'vld_size': ns.vld.stat().st_size,
        'entry_count': len(entries),
        'unit_count': len(units),
        'display_name_count': len(entries),
        'part_name_count': sum(p['part_name_count'] for p in payloads),
        'alternate_display_name_count': sum(p['alternate_display_name_count'] for p in payloads),
        'skill_name_count': sum(p['skill_count'] for p in payloads),
        'duplicate_id_count': duplicate_ids,
        'payloads': payloads,
        'units': units,
    }
    ns.output.parent.mkdir(parents=True, exist_ok=True)
    ns.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('entry_count', 'unit_count', 'display_name_count', 'part_name_count', 'alternate_display_name_count', 'skill_name_count', 'duplicate_id_count')}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
