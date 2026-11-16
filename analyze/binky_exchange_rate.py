"""Bounded exchange-rate preflight. Prints JSON; never patches runtime artifacts."""
import hashlib
import json
import re
import struct
import zlib

from awe_initialization import ROOT, RECRUITMENT, EXPECTED, protected
from pre_oystown_progression import decode_commands
from pre_oystown_foundation import checkpoint
from oystown_completion import state_bytes
from thumb_inspect import inspect

BLOCKS = ((0x107F52, 1, 1), (0x107F89, 1, 2), (0x1080F7, 3, 1),
	(0x10812E, 2, 1), (0x108165, 2, 3))
ADVICE_START, ADVICE_END = 0x65FC48, 0x65FD15
NEW_ADVICE = ("You nyo...[WAIT]I won't [COLOR_ON]trade[COLOR_OFF] you any[BREAK]"
	"binkies unless you bring[CONTINUE]me a [COLOR_ON]full AWE! gauge[COLOR_OFF].[WAIT]"
	"Every full AWE! gauge[BREAK]is worth two binkies,[CONTINUE]"
	"from any character.[WAIT]Nyo-ho-ho...[SIMPLEWAIT][END]")
CONTROLS = {"END": 0x00, "WAIT": 0x01, "CONTINUE": 0x02, "BREAK": 0x05,
	"COLOR_OFF": 0x30, "COLOR_ON": 0x32, "SIMPLEWAIT": 0x40}
WINDOWS = (
	("FD00 display accumulator", 0x28C7C, 0x28C90, ((0x28C8C, 0x28C90),)),
	("FE55 item/quantity", 0x25634, 0x2565C, ((0x25654, 0x2565C),)),
	("FE5C count", 0x257C4, 0x257E4, ((0x257DC, 0x257E4),)),
	("item search/count", 0x28748, 0x28830, ((0x28784, 0x28790), (0x287BC, 0x287C8), (0x287F0, 0x287F8))),
	("item add/failure continuation", 0x291D4, 0x29260, ((0x29200, 0x29210), (0x29248, 0x29254))),
	("actual item count update", 0x80424, 0x8054E, ((0x80444, 0x80450), (0x80458, 0x8045C),
		(0x804A4, 0x804A8), (0x804E0, 0x804E4), (0x8052C, 0x80534))),
	("FD1F count comparison", 0x29AAC, 0x29AFC, ((0x29AD0, 0x29ADC), (0x29AF4, 0x29AFC))),
	("FD45 capacity branch", 0x2984C, 0x29880, ((0x2986C, 0x29878),)),
	("FD3B exact full-charge comparison", 0x2A43C, 0x2A4E8, ((0x2A468, 0x2A474), (0x2A4AC, 0x2A4B8), (0x2A4DC, 0x2A4E0))),
	("FEC0 charge read", 0x29BB8, 0x29BEC, ((0x29BE0, 0x29BEC),)),
	("FEC1 charge and ready reset", 0x29BEC, 0x29C24, ((0x29C1C, 0x29C24),)),
)


def sha(data):
	return hashlib.sha256(data).hexdigest()


def encode(text):
	table = {}
	for line in (ROOT / "tomatotrans-1.1.1/ta_table_eng.txt").read_text(encoding="utf-8-sig").splitlines():
		parts = line.split(maxsplit=1)
		if len(parts) == 2 and len(parts[1]) == 1:
			table.setdefault(parts[1], int(parts[0], 16))
	table[" "] = 0  # ConvComplexString in inserter/text.cpp explicitly emits zero.
	result = bytearray()
	for token in re.findall(r"\[[^]]+\]|.", text):
		if token.startswith("["):
			result.extend((0xFF, CONTROLS[token[1:-1]]))
		else:
			result.append(table[token])
	return bytes(result)


def original_advice():
	text = (ROOT / "tomatotrans-1.1.1/ta_script_eng.txt").read_text(encoding="utf-8-sig")
	match = re.search(r"(?ms)^4B8-E:(.*?)(?=\n\n[0-9A-F]{3}-E:)", text)
	if not match:
		raise ValueError("Missing original advice source")
	return match.group(1).replace("\n", "").replace("\r", "")


def block_bytes(quantity, character):
	return (bytes.fromhex("FD 00") + struct.pack("<H", quantity)
		+ bytes.fromhex("FE 31 03 01 FE C8 C2 FB 65 08 FE 7A B4 81 10 08 FE 5C 37 FD 1F")
		+ struct.pack("<H", 100 - quantity)
		+ bytes.fromhex("FD 45 C0 81 10 08 FE 55 37") + bytes([quantity])
		+ bytes.fromhex("D8 81 10 08 FE B0 3A FE 66 A1 A9 65 08 FE C1")
		+ bytes([character]) + bytes.fromhex("FD 7D"))


def operations(rom):
	commands, end = decode_commands(rom, 0x107E81, 0x1081DA)
	if end != "exact scoped end":
		raise ValueError("Exchange command scope not exact")
	grants = [int(c["bus"], 16) - 0x08000000 for c in commands if c["bytes"].startswith("fe 55 ")]
	if grants != [start + 0x21 for start, q, ch in BLOCKS]:
		raise ValueError("Unexpected exchange grant paths")
	ops = []
	for start, quantity, character in BLOCKS:
		old, new = block_bytes(quantity, character), block_bytes(2, character)
		if len(old) != 0x37 or rom[start:start + len(old)] != old:
			raise ValueError("Unexpected transaction block: " + hex(start))
		if quantity != 2:
			for offset, label in ((2, "display"), (0x19, "capacity cutoff"), (0x24, "actual grant")):
				ops.append(dict(offset=start + offset, old=bytes([old[offset]]), new=bytes([new[offset]]), role=label))
	old = encode(original_advice())
	if len(old) != ADVICE_END - ADVICE_START or rom[ADVICE_START:ADVICE_END] != old:
		raise ValueError("Translated advice bytes/ownership mismatch")
	pointers = (ROOT / "tomatotrans-1.1.1/pointers1.dat").read_text().splitlines()
	owners = []
	for mid, line in enumerate(pointers):
		for token in line.split():
			if token == "FFFFFFFF":
				continue
			pos = int(token, 16)
			pointer = struct.unpack_from("<I", rom, pos)[0] - 0x08000000
			if ADVICE_START <= pointer < ADVICE_END:
				owners.append((mid, pos, pointer))
	if owners != [(0x4B8, 0x1081A2, ADVICE_START)]:
		raise ValueError("Unexpected reference inside advice allocation")
	new = encode(NEW_ADVICE)
	if len(new) > len(old) or not new.endswith(bytes.fromhex("FF 40 FF 00")):
		raise ValueError("Advice replacement exceeds original allocation")
	ops.append(dict(offset=ADVICE_START, old=old, new=new + b"\xff" * (len(old) - len(new)), role="correct obsolete progression advice"))
	return ops


def verify_rates(rom):
	for start, quantity, character in BLOCKS:
		if rom[start:start + 0x37] != block_bytes(2, character):
			raise ValueError("A transaction is not uniformly two Binkies")
	return True


def main():
	before = protected()
	for path, expected in EXPECTED.items():
		if before.get(str(path.relative_to(ROOT))) != expected:
			raise ValueError("Protected fingerprint mismatch")
	prior = json.loads((ROOT / "reverse_engineering/experiments/oystown_completion_evidence.json").read_text())
	if any(before.get(p) != h for p, h in prior["protected_before"].items()):
		raise ValueError("Prior protected artifacts changed")
	rom = (ROOT / "Tomato Adventure (Japan) (patched).gba").read_bytes()
	derivative = RECRUITMENT.read_bytes()
	ops = operations(rom)
	if operations(derivative) != ops:
		raise ValueError("Derivative patch sites differ")
	windows = []
	for role, start, end, pools in WINDOWS:
		if rom[start:end] != derivative[start:end]:
			raise ValueError("Derivative changed scoped native handlers")
		windows.append(dict(role=role, file_range=[hex(start), hex(end)], sha256=sha(rom[start:end]),
			instructions=[dict(bus=hex(i.address), bytes=i.raw.hex(" "), text=i.text) for i in inspect(rom, start, end, pools)]))
	states = []
	identity = {(zlib.crc32(derivative) & 0xFFFFFFFF, derivative[0xA0:0xB0])}
	for name in ("before_oystown.ss0", "after_exchange_oystown.ss0"):
		path = ROOT / name
		snapshot = checkpoint(path, identity)
		state = state_bytes(path)
		iw = state[0x19000:0x21000]
		count = iw[0x19D4]
		items = [(iw[0x19D5 + 2 * i], iw[0x19D6 + 2 * i], hex(0x030019D6 + 2 * i)) for i in range(min(count, 77))]
		states.append(dict(path=name, sha256=snapshot["sha256"], map=snapshot["map_id"],
			pc=hex(struct.unpack_from("<I", state, 0x5C)[0]), scheduler=iw[0x39C1:0x39C5].hex(" "),
			binky_entries=[v for v in items if v[0] == 0x37], charge=snapshot["alessa_charge"]))
	if protected() != before:
		raise ValueError("Protected artifacts changed during preflight")
	commands, boundary = decode_commands(rom, 0x107E81, 0x1081DA)
	print(json.dumps(dict(status="static preflight passed; runtime patch untested", commands=commands, boundary=boundary,
		blocks=[dict(file_start=hex(s), original_quantity=q, reset_character=c) for s, q, c in BLOCKS],
		operations=[dict(offset=hex(o["offset"]), old=o["old"].hex(" "), new=o["new"].hex(" "), role=o["role"]) for o in ops],
		original_advice=original_advice(), replacement_advice=NEW_ADVICE,
		native_windows=windows, checkpoints=states,
		protected_count=len(before), protected_before=before, protected_after=before, protected_unchanged=True), indent=2))


if __name__ == "__main__":
	main()
