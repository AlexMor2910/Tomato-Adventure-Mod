"""Approved Kaizo numeric add-on; offline only, never operates an emulator.

Default is read-only preflight. --apply writes a fresh exclusive output directory.
Only the unchanged rate-two + Alessa recruitment SHA-256 is accepted.
The original whole-stack removal and uncredited surplus are deliberately retained.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/analyze"), str(ROOT / "tools/patch")]
from binky_exchange_rate import encode, verify_rates
from pre_oystown_progression import decode_commands
from sofoubi_guarded_initialization import snapshot

SOURCE = ROOT / "tools/patch/output/binky-rate-two-recruitment-test-aaee9ff3918c42aabf6d9bec7cff611f/binky_exchange_rate_two.gba"
SOURCE_SHA256 = "d356a6979c497524d1e94306989e09cf8dfe96334a22c664eb3a9570f3ab3ea3"
PLAN = ROOT / "reverse_engineering/kaizo_binky_100_proposal.json"
SIZE = 0x1000000
OLD = (4, 7, 10, 13, 17, 21, 26, 31, 37, 43, 50, 57, 65, 73, 81, 90, 99, 109, 119, 130, 141, 153, 165, 180)
NEW = (2, 4, 6, 7, 9, 12, 14, 17, 21, 24, 28, 32, 36, 41, 45, 50, 55, 61, 66, 72, 78, 85, 92, 100)
DISPLAY = (0xFC7CA, 0xFC7FE, 0xFC832, 0xFC872, 0xFC8A6, 0xFC8DA, 0xFC90E, 0xFC94E,
	0xFC982, 0xFC9B6, 0xFC9EA, 0xFCA2A, 0xFCA5E, 0xFCA92, 0xFCAC6, 0xFCAFA,
	0xFCB3A, 0xFCB6E, 0xFCBA2, 0xFCBD6, 0xFCC0A, 0xFCC3E, 0xFCC72, 0xFCCA6)
REWARDS = (0x60, 0x2A, 0x96, 0x62, 0x02, 0xA4, 0x54, 0x1C, 0x6C, 0x04, 0x98, 0x28,
	0x48, 0xF2, 0x8C, 0xDA, 0x06, 0xE6, 0x4A, 0xB0, 0x12, 0xCE, 0x6E, 0x1E)
GATES = {2: 0x22B, 6: 0x22C, 10: 0x22D, 15: 0x96}
NAMES = ("UFO-Cast", "Lucky Cat", "Cyclooka", "Rocket Pak", "Kendama", "Bouncer", "Bee Gatling",
	"Pyramet", "Fart Horn", "Origami", "Popocon", "BowlingRice", "Bunny Hop", "Shadowreel",
	"SlotZooka", "Flame Doll", "TwinDragon", "SesameTop", "Judgment", "Mansnow", "Dragonfire",
	"Momotaro", "StarScope", "Choo-Choo")


def sha(data):
	return hashlib.sha256(data).hexdigest()


def require(condition, message):
	if not condition:
		raise ValueError(message)


def approved_operations():
	ops = []
	for address, old, new in zip(DISPLAY, OLD, NEW):
		for offset in (address, address + 7):
			ops.append((offset, struct.pack("<H", old), struct.pack("<H", new)))
	return tuple(ops) + ((0xFC7A9, b"\xB4\x00", b"\x64\x00"),
		(0xFCCD8, b"\xB4", b"\x64"), (0x64FE13, b"\x78", b"\x70"))


def expected_changes(operations):
	occupied, changes = set(), {}
	for offset, old, new in operations:
		require(len(old) == len(new) and len(old) > 0, "Operand width mismatch")
		for i, (a, b) in enumerate(zip(old, new)):
			require(offset + i not in occupied, "Overlapping operations")
			occupied.add(offset + i)
			if a != b:
				changes[offset + i] = (a, b)
	return changes


def validate_plan(plan):
	require(plan["source_sha256"] == SOURCE_SHA256 and plan["source_size"] == SIZE, "Plan source mismatch")
	require(len(plan["thresholds"]) == 24, "Threshold count mismatch")
	for i, row in enumerate(plan["thresholds"]):
		expected = dict(gimmick=NAMES[i], old=OLD[i], new=NEW[i],
			display_file=f"0x{DISPLAY[i]:08X}", display_bus=f"0x{DISPLAY[i] + 0x08000000:08X}",
			compare_file=f"0x{DISPLAY[i] + 7:08X}", compare_bus=f"0x{DISPLAY[i] + 7 + 0x08000000:08X}",
			old_bytes=struct.pack("<H", OLD[i]).hex(" ").upper(),
			new_bytes=struct.pack("<H", NEW[i]).hex(" ").upper(),
			packed_reward=f"0x{REWARDS[i]:02X}", reward_id=f"0x{REWARDS[i] & 63:02X}",
			owner=REWARDS[i] >> 6, claim_flag=f"0x{0x195 + i:03X}",
			prerequisite_flags=[f"0x{GATES[i]:03X}"] if i in GATES else [],
			script_start=f"0x{DISPLAY[i] - 11 + 0x08000000:08X}")
		require(row == expected, "Threshold/reward/flag plan mismatch: " + NAMES[i])
	ops = tuple((int(o["file"], 16), bytes.fromhex(o["old"]), bytes.fromhex(o["new"])) for o in plan["operations"])
	require(ops == approved_operations(), "Operation ledger differs from approved constants")
	for o in plan["operations"]:
		require(int(o["bus"], 16) == int(o["file"], 16) + 0x08000000, "Bus/file mismatch")
	expected = expected_changes(ops)
	listed = {int(o["file"], 16): (int(o["old"], 16), int(o["new"], 16))
		for o in plan["expected_actual_byte_differences"]}
	require(len(plan["expected_actual_byte_differences"]) == 51 and listed == expected, "Byte ledger mismatch")
	require(len(expected) == plan["expected_changed_bytes"] == 51, "Actual change count mismatch")
	return ops


def validate_context(source):
	commands, end = decode_commands(source, 0xFC775, 0xFCE56)
	require(end == "exact scoped end", "Script boundary mismatch")
	by = {int(c["bus"], 16) - 0x08000000: bytes.fromhex(c["bytes"]) for c in commands}
	for i, address in enumerate(DISPLAY):
		start = address - 11
		end = DISPLAY[i + 1] - 11 if i < 23 else 0xFCCD5
		require(by[start][:4] == b"\xFD\x35" + struct.pack("<H", 0x195 + i), "Claim guard mismatch")
		require(by[address - 3] == b"\xFD\x0B\x14" + struct.pack("<H", OLD[i]), "Display context mismatch")
		require(by[address + 5] == b"\xFD\x1F" + struct.pack("<H", OLD[i]), "Compare context mismatch")
		require(by[address + 2] == bytes.fromhex("FD 0D 30"), "Cumulative reader mismatch")
		require(by[address + 9] == bytes.fromhex("FD 46 30 CD 0F 08"), "Threshold branch mismatch")
		block = source[start:end]
		require(b"\xFD\x0B\x1C" + struct.pack("<H", REWARDS[i]) in block, "Reward ID mismatch")
		require(bytes.fromhex("FD 2F 33 4B 12 08") in block, "Gift call mismatch")
		require(b"\xFD\x49" + struct.pack("<H", 0x195 + i) in block, "Claim setter mismatch")
		gates = [struct.unpack_from("<H", v, 2)[0] for a, v in by.items()
			if start <= a < end and v[:2] == b"\xFD\x36"]
		require(gates == ([GATES[i]] if i in GATES else []), "Prerequisite mismatch")
	for address, context in ((0xFC793, "FD 14 14 FD 0D 30 FD 11 14 FD 0E 30 FE 56 37 FF A7 C7 0F 08 FD 1F B4 00 FD 45 D5 CC 0F 08"),
		(0xFCCD5, "FD 4D 30 B4 FD 30 B1 C7 0F 08"),
		(0xFCD0C, "FD 35 AE 01 24 CD 0F 08 FD 49 AE 01")):
		old = bytes.fromhex(context)
		require(source[address:address + len(old)] == old, "Donation/retirement context mismatch")
	text = (ROOT / "tomatotrans-1.1.1/ta_script_eng.txt").read_text(encoding="utf-8-sig")
	match = re.search(r"(?ms)^0FA-E:(.*?)(?=\n\n[0-9A-F]{3}-E:)", text)
	require(match is not None, "Original text source missing")
	message = match.group(1).replace("\n", "").replace("\r", "")
	require(encode(message) == source[0x64FDF3:0x64FE34], "Original text encoding mismatch")
	require(source[0xFCD26:0xFCD2A] == bytes.fromhex("F3 FD 64 08"), "Text pointer mismatch")
	require(len(encode(message.replace("180", "100"))) == 65, "Replacement text length mismatch")
	verify_rates(source)


def preflight(source, plan):
	require(len(source) == SIZE and sha(source) == SOURCE_SHA256, "Source size/SHA-256 mismatch")
	ops = validate_plan(plan)
	for offset, old, new in ops:
		require(source[offset:offset + len(old)] == old, "Original bytes mismatch")
	validate_context(source)
	return ops


def verify_output(source, output, plan):
	ops = preflight(source, plan)
	require(len(output) == len(source), "ROM size changed")
	actual = {i: (a, b) for i, (a, b) in enumerate(zip(source, output)) if a != b}
	require(actual == expected_changes(ops) and len(actual) == 51, "Unexpected full-file differences")
	for offset, old, new in ops:
		require(output[offset:offset + len(new)] == new, "Output operand mismatch")
	require(output[:0xC0] == source[:0xC0], "Header changed")
	require(output[0x800000:] == source[0x800000:], "Alessa wrapper/extension changed")
	require(output[0x10D69D:0x10D6A3] == source[0x10D69D:0x10D6A3], "Recruitment redirect changed")
	require(output[0x107E81:0x1081DA] == source[0x107E81:0x1081DA], "Exchange scripts changed")
	require(output[0x65FC48:0x65FD15] == source[0x65FC48:0x65FD15], "Exchange advice changed")
	require(output[0x252F4:0x2536C] == source[0x252F4:0x2536C]
		and output[0x62B9D8:0x62B9DC] == source[0x62B9D8:0x62B9DC], "FE49 changed")
	verify_rates(output)
	return dict(changed_bytes=51, compared_bytes=len(source), full_file_comparison=True,
		header_unchanged=True, alessa_wrapper_unchanged=True, exchange_unchanged=True,
		story_claim_prerequisite_reward_bytes_unchanged=True, inventory_capacity_unchanged=True,
		differences=[dict(file=f"0x{i:08X}", bus=f"0x{i + 0x08000000:08X}", old=f"{a:02X}", new=f"{b:02X}")
			for i, (a, b) in sorted(actual.items())])


def build(source, plan):
	ops = preflight(source, plan)
	output = bytearray(source)
	for offset, old, new in ops:
		output[offset:offset + len(new)] = new
	verify_output(source, output, plan)
	return bytes(output)


def donation_model(total, stock, completed=False):
	"""Pure arithmetic model of the traced script; not an emulator."""
	if completed:
		return total, stock
	accumulator = total + stock
	stored = accumulator & 255
	if accumulator >= 100:
		stored = 100
	return stored, 0


def arithmetic_checks():
	for total in range(181):
		for stock in range(100):
			require(donation_model(total, stock) == (min(100, total + stock), 0), "Donation arithmetic mismatch")
	require(all(a < b for a, b in zip(NEW, NEW[1:])), "Nonincreasing requirements")
	require(NEW == tuple((v * 100 + 90) // 180 for v in OLD), "Normalization mismatch")
	return dict(donation_cases=18100, thresholds=24, final_requirement=100, runtime_simulated=False)


def fresh_directory(name):
	require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,100}", name) is not None, "Unsafe output name")
	p = Path(__file__).resolve().parent / "output" / name
	p.mkdir(parents=True, exist_ok=False)
	return p


def write_json(path, data):
	with path.open("x", encoding="utf-8", newline="\n") as f:
		f.write(json.dumps(data, indent=2) + "\n")


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--apply", action="store_true")
	parser.add_argument("--output-name")
	args = parser.parse_args()
	before = snapshot()
	source = SOURCE.read_bytes()
	plan_bytes = PLAN.read_bytes()
	plan = json.loads(plan_bytes)
	preflight(source, plan)
	arithmetic = arithmetic_checks()
	if not args.apply:
		require(snapshot() == before, "Protected artifacts changed")
		print(json.dumps(dict(preflight="passed", expected_changed_bytes=51, arithmetic=arithmetic)))
		return
	output = build(source, plan)
	directory = fresh_directory(args.output_name or "kaizo-binky-100-" + uuid.uuid4().hex)
	path = directory / "kaizo_binky_100.gba"
	with path.open("xb") as f:
		require(f.write(output) == SIZE, "Short write")
	readback = path.read_bytes()
	require(readback == output, "Output readback differs")
	verification = verify_output(source, readback, plan)
	after = snapshot()
	require(after.pop(str(path.relative_to(ROOT)), None) == sha(readback), "Output audit mismatch")
	require(after == before, "Preexisting protected artifact changed")
	write_json(directory / "byte_differences.json", verification["differences"])
	with (directory / "byte_differences.tsv").open("x", encoding="utf-8", newline="\n") as f:
		f.write("file_offset\tbus_address\toriginal\treplacement\n")
		for row in verification["differences"]:
			f.write("\t".join(row[k] for k in ("file", "bus", "old", "new")) + "\n")
	manifest = dict(experiment="Kaizo cumulative donation cap 100; original whole-stack surplus retained",
		source=str(SOURCE), source_sha256=sha(source), source_bytes=len(source),
		output=str(path), output_sha256=sha(readback), output_bytes=len(readback),
		script_sha256=sha(Path(__file__).read_bytes()), proposal_sha256=sha(plan_bytes),
		operations=plan["operations"], verification=verification, arithmetic=arithmetic,
		protected_before=before, protected_after=after, protected_unchanged=True,
		runtime_status="untested; separate user authorization required",
		tests_path=str(ROOT / "tests/test_kaizo_binky_100.py"),
		tests_sha256=sha((ROOT / "tests/test_kaizo_binky_100.py").read_bytes()))
	write_json(directory / "manifest.json", manifest)
	require(json.loads((directory / "manifest.json").read_text()) == manifest, "Manifest readback mismatch")
	print(json.dumps(dict(output=str(path), sha256=sha(readback), bytes=len(readback), changed_bytes=51,
		protected_count=len(before), protected_unchanged=True, arithmetic=arithmetic)))


if __name__ == "__main__":
	main()
