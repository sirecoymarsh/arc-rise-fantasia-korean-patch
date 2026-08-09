#!/usr/bin/env python3
"""Parser, validator, and variable-length rebuilder for Arc Rise Fantasia BSCR.

The implementation is deliberately byte-oriented.  It does not translate text
and does not assume that replacement glyph bytes are decodable by a host codec.
The only format-specific pointer rewrites are the two VM opcodes proven by the
full RPJJ99 corpus audit in this directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


HEADER_SIZE = 0x40
DESCRIPTOR_NAME_SIZE = 32
VM_CELL_SIZE = 16
LITERAL_POINTER_OPCODE = bytes.fromhex("1af0f15a")
CALL_TARGET_POINTER_OPCODE = bytes.fromhex("8100f3f2")
POINTER_OPCODES = {
    LITERAL_POINTER_OPCODE: "literal",
    CALL_TARGET_POINTER_OPCODE: "call_target",
}
CHOICE_OPCODE_SEQUENCE = (
    bytes.fromhex("82bcf35a"),
    bytes.fromhex("82bdf35a"),
    bytes.fromhex("82bef3f2"),
)


class BscrError(ValueError):
    """Raised when BSCR structure or a requested rebuild is invalid."""


@dataclass(frozen=True)
class Descriptor:
    index: int
    offset: int
    size: int
    type_code: int
    name: str
    raw: bytes


@dataclass(frozen=True)
class StringRecord:
    index: int
    relative_offset: int
    absolute_offset: int
    raw: bytes
    roles: tuple[str, ...] = ()
    reference_count: int = 0

    def decoded(self) -> str:
        return self.raw.decode("euc_jp", errors="backslashreplace")


@dataclass(frozen=True)
class VmCell:
    index: int
    offset: int
    opcode: bytes
    operand: int
    tail: bytes


@dataclass(frozen=True)
class ChoiceSite:
    instruction_index: int
    prompt_offset: int
    options_offset: int


@dataclass(frozen=True)
class BscrFile:
    data: bytes
    variant_tag: int
    file_name: str
    declared_file_size: int
    descriptor_count: int
    descriptor_start: int
    string_count: int
    pool_start: int
    bytecode_size: int
    bytecode_start: int
    descriptors: tuple[Descriptor, ...]
    strings: tuple[StringRecord, ...]
    pool_padding: bytes
    cells: tuple[VmCell, ...]
    choice_sites: tuple[ChoiceSite, ...]

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()

    @property
    def string_by_offset(self) -> dict[int, StringRecord]:
        return {record.relative_offset: record for record in self.strings}

    def rebuild(
        self,
        replacements: Mapping[int, bytes] | None = None,
        *,
        allow_call_target_replacement: bool = False,
        preserve_structural_controls: bool = True,
    ) -> bytes:
        """Rebuild with arbitrary-length raw string replacements.

        Keys are original pool-relative string offsets.  New strings may change
        byte length but may not contain NUL.  Command/function identifiers are
        protected by default.  Structural control tokens are protected by
        default, while ordinary line feeds may be reflowed by localization.
        """

        replacements = dict(replacements or {})
        known = self.string_by_offset
        unknown = sorted(set(replacements) - set(known))
        if unknown:
            raise BscrError(f"replacement offsets are not string starts: {[hex(value) for value in unknown]}")

        for offset, replacement in replacements.items():
            if not isinstance(replacement, (bytes, bytearray)):
                raise BscrError(f"replacement at {offset:#x} is not bytes")
            replacement = bytes(replacement)
            if b"\0" in replacement:
                raise BscrError(f"replacement at {offset:#x} contains an embedded NUL")
            source = known[offset]
            if "call_target" in source.roles and not allow_call_target_replacement:
                raise BscrError(f"replacement at {offset:#x} is a protected VM call target")
            if preserve_structural_controls:
                old_controls = structural_control_signature(source.raw)
                new_controls = structural_control_signature(replacement)
                if old_controls != new_controls:
                    raise BscrError(
                        f"replacement at {offset:#x} changes structural controls: "
                        f"{old_controls!r} -> {new_controls!r}"
                    )

        new_pool = bytearray()
        offset_map: dict[int, int] = {}
        for record in self.strings:
            offset_map[record.relative_offset] = len(new_pool)
            raw = bytes(replacements.get(record.relative_offset, record.raw))
            new_pool += raw
            new_pool.append(0)
        # The compiler always emits 1..4 zero bytes after the last terminator,
        # even when the content is already four-byte aligned.
        new_pool += b"\0" * (4 - (len(new_pool) % 4))

        bytecode = bytearray(self.data[self.bytecode_start : self.bytecode_start + self.bytecode_size])
        for cell in self.cells:
            role = POINTER_OPCODES.get(cell.opcode)
            if role is None:
                continue
            if cell.operand not in offset_map:
                raise BscrError(
                    f"{role} pointer at instruction {cell.index} targets non-string {cell.operand:#x}"
                )
            struct.pack_into(">I", bytecode, cell.index * VM_CELL_SIZE + 4, offset_map[cell.operand])

        new_bytecode_start = self.pool_start + len(new_pool)
        new_file_size = new_bytecode_start + self.bytecode_size
        prefix = bytearray(self.data[: self.pool_start])
        struct.pack_into(">I", prefix, 0x24, new_file_size)
        struct.pack_into(">I", prefix, 0x30, len(self.strings))
        struct.pack_into(">I", prefix, 0x34, self.pool_start)
        struct.pack_into(">I", prefix, 0x38, self.bytecode_size)
        struct.pack_into(">I", prefix, 0x3C, new_bytecode_start)
        rebuilt = bytes(prefix + new_pool + bytecode)

        parsed = parse_bscr(rebuilt)
        if parsed.bytecode_size != self.bytecode_size or len(parsed.strings) != len(self.strings):
            raise BscrError("post-rebuild structural verification failed")
        for old_record, new_record in zip(self.strings, parsed.strings, strict=True):
            expected = bytes(replacements.get(old_record.relative_offset, old_record.raw))
            if new_record.raw != expected:
                raise BscrError(f"post-rebuild string mismatch at old offset {old_record.relative_offset:#x}")
        return rebuilt

    def to_dict(self, *, include_raw_hex: bool = True) -> dict[str, object]:
        return {
            "schema": "arf-bscr-inspect-v1",
            "sha256": self.sha256,
            "length": len(self.data),
            "header": {
                "magic": "bscr",
                "variant_tag": self.variant_tag,
                "file_name": self.file_name,
                "file_size": self.declared_file_size,
                "descriptor_count": self.descriptor_count,
                "descriptor_start": self.descriptor_start,
                "string_count": self.string_count,
                "pool_start": self.pool_start,
                "bytecode_size": self.bytecode_size,
                "bytecode_start": self.bytecode_start,
            },
            "pool_padding_hex": self.pool_padding.hex(),
            "descriptors": [
                {
                    "index": item.index,
                    "offset": item.offset,
                    "size": item.size,
                    "type_code": item.type_code,
                    "name": item.name,
                    **({"raw_hex": item.raw.hex()} if include_raw_hex else {}),
                }
                for item in self.descriptors
            ],
            "strings": [
                {
                    "index": item.index,
                    "relative_offset": item.relative_offset,
                    "absolute_offset": item.absolute_offset,
                    "byte_length": len(item.raw),
                    "roles": list(item.roles),
                    "reference_count": item.reference_count,
                    "decoded_euc_jp": item.decoded(),
                    "controls": control_tokens(item.raw),
                    **({"raw_hex": item.raw.hex()} if include_raw_hex else {}),
                }
                for item in self.strings
            ],
            "choice_sites": [
                {
                    "instruction_index": site.instruction_index,
                    "prompt_offset": site.prompt_offset,
                    "options_offset": site.options_offset,
                }
                for site in self.choice_sites
            ],
        }


def _read_ascii_name(raw: bytes, label: str) -> str:
    head = raw.split(b"\0", 1)[0]
    try:
        return head.decode("ascii")
    except UnicodeDecodeError as exc:
        raise BscrError(f"{label} is not ASCII") from exc


def parse_bscr(data: bytes) -> BscrFile:
    if len(data) < HEADER_SIZE:
        raise BscrError("file is shorter than the 0x40-byte BSCR header")
    if data[:4] != b"bscr":
        raise BscrError("bad BSCR magic")
    variant_tag = struct.unpack_from(">H", data, 4)[0]
    file_name = _read_ascii_name(data[6:0x24], "header file name")
    (
        file_size,
        descriptor_count,
        descriptor_start,
        string_count,
        pool_start,
        bytecode_size,
        bytecode_start,
    ) = struct.unpack_from(">7I", data, 0x24)

    if file_size != len(data):
        raise BscrError(f"declared file size {file_size:#x} != actual {len(data):#x}")
    if descriptor_start != HEADER_SIZE:
        raise BscrError(f"unexpected descriptor start {descriptor_start:#x}")
    if not (HEADER_SIZE <= pool_start <= bytecode_start <= len(data)):
        raise BscrError("section offsets are out of order or out of range")
    if bytecode_start + bytecode_size != len(data):
        raise BscrError("bytecode start + size does not equal file size")
    if bytecode_size % VM_CELL_SIZE:
        raise BscrError("bytecode size is not divisible by the 16-byte VM cell size")
    if pool_start % 4 or bytecode_start % 4:
        raise BscrError("string pool boundaries are not four-byte aligned")

    descriptors: list[Descriptor] = []
    cursor = descriptor_start
    for index in range(descriptor_count):
        if cursor + 4 > pool_start:
            raise BscrError(f"descriptor {index} header exceeds descriptor section")
        size, type_code = struct.unpack_from(">HH", data, cursor)
        if size < 4 + DESCRIPTOR_NAME_SIZE or cursor + size > pool_start:
            raise BscrError(f"descriptor {index} has invalid size {size:#x}")
        raw = data[cursor : cursor + size]
        name = _read_ascii_name(raw[4 : 4 + DESCRIPTOR_NAME_SIZE], f"descriptor {index} name")
        descriptors.append(Descriptor(index, cursor, size, type_code, name, raw))
        cursor += size
    if cursor != pool_start:
        raise BscrError(f"descriptor walk ends at {cursor:#x}, pool starts at {pool_start:#x}")

    raw_strings: list[tuple[int, int, bytes]] = []
    pool_cursor = pool_start
    for index in range(string_count):
        terminator = data.find(b"\0", pool_cursor, bytecode_start)
        if terminator < 0:
            raise BscrError(f"string {index} has no NUL terminator")
        raw_strings.append((pool_cursor - pool_start, pool_cursor, data[pool_cursor:terminator]))
        pool_cursor = terminator + 1
    pool_padding = data[pool_cursor:bytecode_start]
    expected_padding = 4 - ((pool_cursor - pool_start) % 4)
    if len(pool_padding) != expected_padding or not (1 <= len(pool_padding) <= 4):
        raise BscrError(
            f"pool padding length {len(pool_padding)} does not match compiler convention {expected_padding}"
        )
    if any(pool_padding):
        raise BscrError("pool padding is not all zero")

    cells: list[VmCell] = []
    reference_roles: dict[int, set[str]] = {relative: set() for relative, _, _ in raw_strings}
    reference_counts: dict[int, int] = {relative: 0 for relative, _, _ in raw_strings}
    string_offsets = set(reference_roles)
    for index in range(bytecode_size // VM_CELL_SIZE):
        offset = bytecode_start + index * VM_CELL_SIZE
        opcode = data[offset : offset + 4]
        operand = struct.unpack_from(">I", data, offset + 4)[0]
        tail = data[offset + 8 : offset + VM_CELL_SIZE]
        cells.append(VmCell(index, offset, opcode, operand, tail))
        role = POINTER_OPCODES.get(opcode)
        if role is not None:
            if operand not in string_offsets:
                raise BscrError(
                    f"{role} pointer at instruction {index} targets non-string offset {operand:#x}"
                )
            reference_roles[operand].add(role)
            reference_counts[operand] += 1

    unreferenced = [offset for offset, count in reference_counts.items() if count == 0]
    if unreferenced:
        raise BscrError(
            "pool contains strings not referenced by either proven pointer opcode: "
            + ", ".join(hex(value) for value in unreferenced[:16])
        )

    strings = tuple(
        StringRecord(
            index=index,
            relative_offset=relative,
            absolute_offset=absolute,
            raw=raw,
            roles=tuple(sorted(reference_roles[relative])),
            reference_count=reference_counts[relative],
        )
        for index, (relative, absolute, raw) in enumerate(raw_strings)
    )

    choices: list[ChoiceSite] = []
    opcodes = [cell.opcode for cell in cells]
    for index in range(2, len(cells) - 2):
        if tuple(opcodes[index : index + 3]) != CHOICE_OPCODE_SEQUENCE:
            continue
        prompt_cell, options_cell = cells[index - 2], cells[index - 1]
        if prompt_cell.opcode != LITERAL_POINTER_OPCODE or options_cell.opcode != LITERAL_POINTER_OPCODE:
            continue
        choices.append(ChoiceSite(index, prompt_cell.operand, options_cell.operand))

    return BscrFile(
        data=data,
        variant_tag=variant_tag,
        file_name=file_name,
        declared_file_size=file_size,
        descriptor_count=descriptor_count,
        descriptor_start=descriptor_start,
        string_count=string_count,
        pool_start=pool_start,
        bytecode_size=bytecode_size,
        bytecode_start=bytecode_start,
        descriptors=tuple(descriptors),
        strings=strings,
        pool_padding=pool_padding,
        cells=tuple(cells),
        choice_sites=tuple(choices),
    )


CONTROL_SPECS = {
    0x14: (4, "item_substitution"),
    0x15: (2, "controller_glyph"),
    0x19: (2, "speaker_slot"),
    0x1C: (4, "message_style"),
}


def control_tokens(raw: bytes) -> list[dict[str, object]]:
    tokens: list[dict[str, object]] = []
    index = 0
    while index < len(raw):
        value = raw[index]
        if value == 0x0A:
            tokens.append({"offset": index, "kind": "line_break", "raw_hex": "0a"})
            index += 1
            continue
        if value == 0x0C:
            tokens.append({"offset": index, "kind": "page_break", "raw_hex": "0c"})
            index += 1
            continue
        spec = CONTROL_SPECS.get(value)
        if spec is not None:
            width, kind = spec
            end = min(len(raw), index + 1 + width)
            payload = raw[index + 1 : end]
            valid_hex = len(payload) == width and all(chr(byte) in "0123456789ABCDEFabcdef" for byte in payload)
            tokens.append(
                {
                    "offset": index,
                    "kind": kind,
                    "payload_ascii": payload.decode("ascii", errors="replace"),
                    "raw_hex": raw[index:end].hex(),
                    "well_formed": valid_hex,
                }
            )
            index = end
            continue
        if value < 0x20 or value == 0x7F:
            tokens.append({"offset": index, "kind": f"unknown_control_{value:02x}", "raw_hex": f"{value:02x}"})
        index += 1
    return tokens


def structural_control_signature(raw: bytes) -> tuple[tuple[str, str], ...]:
    # Line feeds are intentionally excluded because localization may reflow
    # lines.  Page breaks and semantic substitutions/icons must remain exact.
    return tuple(
        (str(token["kind"]), str(token["raw_hex"]))
        for token in control_tokens(raw)
        if token["kind"] != "line_break"
    )


def load_replacements(path: Path) -> dict[int, bytes]:
    document = json.loads(path.read_text(encoding="utf-8"))
    items = document["replacements"] if isinstance(document, dict) else document
    replacements: dict[int, bytes] = {}
    for item in items:
        value = item["offset"]
        offset = int(value, 0) if isinstance(value, str) else int(value)
        if "raw_hex" not in item:
            raise BscrError("replacement JSON requires raw_hex; text encoding is intentionally external")
        raw = bytes.fromhex(item["raw_hex"])
        if "source_raw_hex" in item and bytes.fromhex(item["source_raw_hex"]) == raw:
            # This is allowed; it is useful for explicit no-op manifests.
            pass
        replacements[offset] = raw
    return replacements


def command_inspect(args: argparse.Namespace) -> None:
    parsed = parse_bscr(args.input.read_bytes())
    document = parsed.to_dict(include_raw_hex=not args.omit_raw_hex)
    rendered = json.dumps(document, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


def command_verify(args: argparse.Namespace) -> None:
    parsed = parse_bscr(args.input.read_bytes())
    print(
        json.dumps(
            {
                "valid": True,
                "sha256": parsed.sha256,
                "file_name": parsed.file_name,
                "length": len(parsed.data),
                "descriptor_count": len(parsed.descriptors),
                "string_count": len(parsed.strings),
                "instruction_count": len(parsed.cells),
                "choice_site_count": len(parsed.choice_sites),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def command_rebuild(args: argparse.Namespace) -> None:
    parsed = parse_bscr(args.input.read_bytes())
    replacements = load_replacements(args.replacements) if args.replacements else {}
    rebuilt = parsed.rebuild(
        replacements,
        allow_call_target_replacement=args.allow_call_targets,
        preserve_structural_controls=not args.allow_control_changes,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(rebuilt)
    print(
        json.dumps(
            {
                "source_sha256": parsed.sha256,
                "output_sha256": hashlib.sha256(rebuilt).hexdigest(),
                "source_length": len(parsed.data),
                "output_length": len(rebuilt),
                "replacement_count": len(replacements),
                "byte_exact": rebuilt == parsed.data,
            },
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="parse and export a BSCR inventory")
    inspect_parser.add_argument("input", type=Path)
    inspect_parser.add_argument("--output", type=Path)
    inspect_parser.add_argument("--omit-raw-hex", action="store_true")
    inspect_parser.set_defaults(handler=command_inspect)

    verify_parser = subparsers.add_parser("verify", help="strictly validate a BSCR")
    verify_parser.add_argument("input", type=Path)
    verify_parser.set_defaults(handler=command_verify)

    rebuild_parser = subparsers.add_parser("rebuild", help="rebuild with optional raw-byte replacements")
    rebuild_parser.add_argument("input", type=Path)
    rebuild_parser.add_argument("output", type=Path)
    rebuild_parser.add_argument("--replacements", type=Path)
    rebuild_parser.add_argument("--allow-call-targets", action="store_true")
    rebuild_parser.add_argument("--allow-control-changes", action="store_true")
    rebuild_parser.set_defaults(handler=command_rebuild)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.handler(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
