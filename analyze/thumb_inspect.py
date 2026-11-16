"""Small, read-only ARMv4T Thumb instruction inspector.

This is a local analysis helper, not a full ARM/GBA disassembler or emulator.
It decodes 16-bit Thumb formats and paired BL instructions. Callers must
exclude literal pools/data and choose instruction boundaries themselves.
Unknown/reserved instructions remain explicit .hword entries.
"""

from dataclasses import dataclass
import struct


@dataclass(frozen=True)
class Instruction:
	address: int
	size: int
	raw: bytes
	text: str
	target: int | None = None
	literal_address: int | None = None
	literal_value: int | None = None


def signed(value: int, bits: int) -> int:
	return value - (1 << bits) if value & (1 << (bits - 1)) else value


def registers(mask: int, extra: str | None = None) -> str:
	items = [f"r{i}" for i in range(8) if mask & (1 << i)]
	if extra:
		items.append(extra)
	return "{" + ", ".join(items) + "}"


def decode(rom: bytes, offset: int, bus_base: int = 0x08000000) -> Instruction:
	address = bus_base + offset
	h = struct.unpack_from("<H", rom, offset)[0]
	d, s = h & 7, (h >> 3) & 7
	target = literal_address = literal_value = None
	size = 2
	text = f".hword 0x{h:04X} ; unsupported/reserved"
	if h & 0xF800 == 0xF000 and offset + 4 <= len(rom):
		low = struct.unpack_from("<H", rom, offset + 2)[0]
		if low & 0xF800 == 0xF800:
			target = address + 4 + signed(((h & 0x7FF) << 12) | ((low & 0x7FF) << 1), 23)
			text, size = f"bl 0x{target:08X}", 4
	elif h & 0xF800 == 0x1800:
		operand = f"#{(h >> 6) & 7}" if h & 0x0400 else f"r{(h >> 6) & 7}"
		text = f"{'sub' if h & 0x0200 else 'add'} r{d}, r{s}, {operand}"
	elif h & 0xE000 == 0:
		op = (h >> 11) & 3
		if op < 3:
			amount = (h >> 6) & 31
			if not amount and op in (1, 2):
				amount = 32
			text = f"{['lsl', 'lsr', 'asr'][op]} r{d}, r{s}, #{amount}"
	elif h & 0xE000 == 0x2000:
		text = f"{['mov', 'cmp', 'add', 'sub'][(h >> 11) & 3]} r{(h >> 8) & 7}, #{h & 255}"
	elif h & 0xFC00 == 0x4000:
		op = ['and', 'eor', 'lsl', 'lsr', 'asr', 'adc', 'sbc', 'ror', 'tst', 'neg', 'cmp', 'cmn', 'orr', 'mul', 'bic', 'mvn'][(h >> 6) & 15]
		text = f"{op} r{d}, r{s}"
	elif h & 0xFC00 == 0x4400:
		destination, source = (h & 7) | ((h >> 4) & 8), (h >> 3) & 15
		op = (h >> 8) & 3
		if op == 3 and not h & 0x0080:
			text = f"bx r{source}"
		elif op < 3:
			text = f"{['add', 'cmp', 'mov'][op]} r{destination}, r{source}"
	elif h & 0xF800 == 0x4800:
		literal_address = ((address + 4) & ~3) + (h & 255) * 4
		position = literal_address - bus_base
		if 0 <= position <= len(rom) - 4:
			literal_value = struct.unpack_from("<I", rom, position)[0]
		text = f"ldr r{(h >> 8) & 7}, [pc, #{(h & 255) * 4}] ; slot 0x{literal_address:08X}"
		if literal_value is not None:
			text += f" = 0x{literal_value:08X}"
	elif h & 0xF000 == 0x5000:
		op = ['str', 'strh', 'strb', 'ldrsb', 'ldr', 'ldrh', 'ldrb', 'ldrsh'][(h >> 9) & 7]
		text = f"{op} r{d}, [r{s}, r{(h >> 6) & 7}]"
	elif h & 0xE000 == 0x6000:
		byte = bool(h & 0x1000)
		amount = ((h >> 6) & 31) * (1 if byte else 4)
		text = f"{'ldr' if h & 0x0800 else 'str'}{'b' if byte else ''} r{d}, [r{s}, #{amount}]"
	elif h & 0xF000 == 0x8000:
		text = f"{'ldrh' if h & 0x0800 else 'strh'} r{d}, [r{s}, #{((h >> 6) & 31) * 2}]"
	elif h & 0xF000 == 0x9000:
		text = f"{'ldr' if h & 0x0800 else 'str'} r{(h >> 8) & 7}, [sp, #{(h & 255) * 4}]"
	elif h & 0xF000 == 0xA000:
		text = f"add r{(h >> 8) & 7}, {'sp' if h & 0x0800 else 'pc'}, #{(h & 255) * 4}"
	elif h & 0xFF00 == 0xB000:
		text = f"{'sub' if h & 0x0080 else 'add'} sp, #{(h & 127) * 4}"
	elif h & 0xF600 == 0xB400:
		pop = bool(h & 0x0800)
		extra = ('pc' if pop else 'lr') if h & 0x0100 else None
		text = f"{'pop' if pop else 'push'} {registers(h & 255, extra)}"
	elif h & 0xF000 == 0xC000:
		text = f"{'ldmia' if h & 0x0800 else 'stmia'} r{(h >> 8) & 7}!, {registers(h & 255)}"
	elif h & 0xF000 == 0xD000:
		cond = (h >> 8) & 15
		if cond < 14:
			target = address + 4 + signed(h & 255, 8) * 2
			text = f"b{['eq', 'ne', 'cs', 'cc', 'mi', 'pl', 'vs', 'vc', 'hi', 'ls', 'ge', 'lt', 'gt', 'le'][cond]} 0x{target:08X}"
		elif cond == 15:
			text = f"swi #{h & 255}"
	elif h & 0xF800 == 0xE000:
		target = address + 4 + signed(h & 0x7FF, 11) * 2
		text = f"b 0x{target:08X}"
	return Instruction(address, size, rom[offset:offset + size], text, target, literal_address, literal_value)


def inspect(rom: bytes, start: int, end: int, excluded=()):
	"""Yield linear instruction observations, excluding declared data intervals."""
	offset = start
	while offset < end:
		data_end = next((b for a, b in excluded if a <= offset < b), None)
		if data_end is not None:
			offset = data_end
			continue
		instruction = decode(rom, offset)
		if offset + instruction.size > end:
			raise ValueError("Instruction crosses inspection boundary")
		yield instruction
		offset += instruction.size
