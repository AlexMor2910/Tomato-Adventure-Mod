"""Fingerprint and inspect supplied ROMs without writing either input.

Python standard library only. Writes a CSV and Markdown report beneath
reverse_engineering/. Source comparison uses a deliberately limited Thumb
encoder for the instructions in asm/gimmick_text.asm, not a translation build.
It never launches an assembler, inserter, emulator, or package installer.
"""

import argparse
import ast
import csv
import hashlib
import importlib.util
import io
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from thumb_inspect import decode, inspect


BUS = 0x08000000
TABLE = 0x0062C250
COUNT = 50
STRIDE = 0x58
LITERALS = {0x655D4: 0x030018BC, 0x655D8: 0x03001AD2,
	0x655DC: 0x0862C1F8, 0x655E0: 0x03003F34}
REGIONS = (("loader prefix", 0x65518, 0x6556C),
	("retained continuation, including four literal slots", 0x6556C, 0x656B8),
	("epilogue patch region", 0x656B8, 0x656C2))


def sha(data):
	return hashlib.sha256(data).hexdigest()


def hx(value, width=8):
	return f"0x{value:0{width}X}"


def u32(data, offset):
	return struct.unpack_from("<I", data, offset)[0]


def discover(workspace, japanese_arg, english_arg):
	candidates = sorted(p.resolve() for p in workspace.rglob("*")
		if p.is_file() and p.suffix.lower() == ".gba")
	def specified(value):
		p = Path(value)
		return (workspace / p).resolve() if not p.is_absolute() else p.resolve()
	def choose(argument, patched):
		if argument:
			return specified(argument)
		matches = [p for p in candidates if ("patched" in p.name.lower()) == patched]
		if len(matches) != 1:
			raise ValueError("Ambiguous ROM discovery; supply --japanese and --english explicitly. "
				+ "Candidates: " + "; ".join(str(p) for p in candidates))
		return matches[0]
	jp, en = choose(japanese_arg, False), choose(english_arg, True)
	if jp == en:
		raise ValueError("Japanese and English inputs must be distinct files")
	return jp, en, candidates


def source_fingerprint(toolkit):
	"""Hash toolkit files without changing them; ROM inputs are separately hashed."""
	digest = hashlib.sha256()
	for p in sorted(toolkit.rglob("*")):
		if p.is_file() and p.suffix.lower() != ".gba":
			digest.update(p.relative_to(toolkit).as_posix().encode())
			digest.update(hashlib.sha256(p.read_bytes()).digest())
	return digest.hexdigest()


def tooling():
	observations = []
	available = {}
	for name in ["arm-none-eabi-objdump", "arm-linux-gnueabi-objdump", "llvm-objdump", "objdump", "r2", "radare2", "ghidra", "mgba"]:
		path = shutil.which(name)
		available[name] = path
		observations.append(f"- `{name}` on PATH: `{path}`" if path else f"- `{name}` on PATH: not found.")
	for module in ["capstone", "lief", "keystone"]:
		found = importlib.util.find_spec(module)
		observations.append(f"- Python `{module}`: `{found.origin}`" if found else f"- Python `{module}`: not installed.")
	if available["objdump"]:
		result = subprocess.run([available["objdump"], "-i"], capture_output=True, text=True, check=False)
		arm = bool(re.search(r"\b(?:arm|aarch64)\b", result.stdout, re.I))
		observations.append(f"- Existing GNU objdump architecture listing exit {result.returncode}; ARM advertised: {arm}. "
			+ (result.stdout.splitlines()[0] if result.stdout else "No listing returned."))
	observations.append("- Search scope: workspace filenames and command PATH (plus Python import paths); this is not an exhaustive inventory of all installed applications.")
	return observations


def expression(text, env):
	text = re.sub(r"org\(([^()]*)\)", r"\1", text).replace("@", "local_")
	def walk(node):
		if isinstance(node, ast.Constant) and isinstance(node.value, int):
			return node.value
		if isinstance(node, ast.Name):
			if node.id in env:
				return env[node.id]
			for name, value in env.items():
				if name.lower() == node.id.lower():
					return value
			raise KeyError(node.id)
		if isinstance(node, ast.BinOp):
			a, b = walk(node.left), walk(node.right)
			if isinstance(node.op, ast.Add):
				return a + b
			if isinstance(node.op, ast.Sub):
				return a - b
			if isinstance(node.op, ast.Mult):
				return a * b
		raise ValueError(f"Unsupported source expression: {text}")
	return walk(ast.parse(text, mode="eval").body)


def register_list(operand):
	result = []
	for group in operand.split(","):
		m = re.fullmatch(r"r(\d+)(?:-r(\d+))?", group)
		if not m:
			raise ValueError(f"Unsupported register list: {operand}")
		result.extend(range(int(m[1]), int(m[2] or m[1]) + 1))
	return result


def encode_instruction(text, address, env):
	"""Expected bytes for a small source subset, independent of ROM contents."""
	compact = re.sub(r"\s+", "", text.lower())
	if compact == "nop":
		return struct.pack("<H", 0x46C0)
	m = re.fullmatch(r"(push|pop)(.+)", compact)
	if m:
		regs = register_list(m[2])
		pop = m[1] == "pop"
		assert all(x < 8 or x == (15 if pop else 14) for x in regs)
		h = (0xBC00 if pop else 0xB400) | sum(1 << x for x in regs if x < 8)
		if any(x >= 8 for x in regs):
			h |= 0x100
		return struct.pack("<H", h)
	m = re.fullmatch(r"bxr(\d+)", compact)
	if m:
		return struct.pack("<H", 0x4700 | (int(m[1]) << 3))
	m = re.fullmatch(r"(bl|b)(0x[0-9a-f]+)", compact)
	if m:
		delta = int(m[2], 16) - address - 4
		assert delta % 2 == 0
		if m[1] == "bl":
			return struct.pack("<HH", 0xF000 | ((delta >> 12) & 0x7FF), 0xF800 | ((delta >> 1) & 0x7FF))
		assert -2048 <= delta < 2048
		return struct.pack("<H", 0xE000 | ((delta >> 1) & 0x7FF))
	m = re.fullmatch(r"ldrr(\d+),\[(0x[0-9a-f]+)\]", compact)
	if m:
		delta = int(m[2], 16) - ((address + 4) & ~3)
		assert 0 <= delta <= 1020 and delta % 4 == 0
		return struct.pack("<H", 0x4800 | (int(m[1]) << 8) | (delta // 4))
	m = re.fullmatch(r"(ldr|str|ldrb|strb)r(\d+),\[r(\d+)(?:,([^]]+))?\]", compact)
	if m:
		op, d, n, amount = m.groups()
		d, n = int(d), int(n)
		amount = expression(amount or "0", env)
		byte = op.endswith("b")
		scale = 1 if byte else 4
		assert d < 8 and n < 8 and amount % scale == 0 and 0 <= amount // scale < 32
		h = 0x6000 | (0x1000 if byte else 0) | (0x0800 if op.startswith("ldr") else 0)
		return struct.pack("<H", h | ((amount // scale) << 6) | (n << 3) | d)
	m = re.fullmatch(r"movr(\d+),r(\d+)", compact)
	if m:
		d, s = map(int, m.groups())
		h = 0x1C00 | (s << 3) | d if d < 8 and s < 8 else 0x4600 | (s << 3) | (d & 7) | ((d & 8) << 4)
		return struct.pack("<H", h)
	m = re.fullmatch(r"movr(\d+),(.+)", compact)
	if m:
		d, value = int(m[1]), expression(m[2], env)
		assert d < 8 and 0 <= value <= 255
		return struct.pack("<H", 0x2000 | (d << 8) | value)
	m = re.fullmatch(r"(lsl|lsr|asr)r(\d+),r(\d+),(.+)", compact)
	if m:
		op, d, s, value = m.groups()
		value = expression(value, env)
		return struct.pack("<H", {"lsl": 0, "lsr": 0x0800, "asr": 0x1000}[op] | ((value & 31) << 6) | (int(s) << 3) | int(d))
	m = re.fullmatch(r"(mul|and)r(\d+),r(\d+)", compact)
	if m:
		return struct.pack("<H", (0x4340 if m[1] == "mul" else 0x4000) | (int(m[3]) << 3) | int(m[2]))
	m = re.fullmatch(r"addr(\d+),r(\d+),(r\d+|.+)", compact)
	if m:
		d, n, operand = m.groups()
		d, n = int(d), int(n)
		if re.fullmatch(r"r\d+", operand):
			h = 0x1800 | (int(operand[1:]) << 6) | (n << 3) | d
		else:
			value = expression(operand, env)
			assert 0 <= value <= 7
			h = 0x1C00 | (value << 6) | (n << 3) | d
		return struct.pack("<H", h)
	m = re.fullmatch(r"addr(\d+),(.+)", compact)
	if m:
		value = expression(m[2], env)
		assert 0 <= value <= 255
		return struct.pack("<H", 0x3000 | (int(m[1]) << 8) | value)
	raise ValueError(f"Unsupported or unresolved instruction: {text}")


def source_checks(english, toolkit):
	env = {}
	for line in (toolkit / "asm/addresses.inc").read_text(encoding="utf-8-sig").splitlines():
		m = re.match(r"\.definelabel\s+(\w+),([^;]+)", line)
		if m:
			env[m[1]] = expression(m[2], env)
	rows, pc = [], None
	for number, raw in enumerate((toolkit / "asm/gimmick_text.asm").read_text(encoding="utf-8-sig").splitlines(), 1):
		line = raw.split(";", 1)[0].strip()
		if not line:
			continue
		m = re.match(r"(@\w+)\s+equ\s+(.+)", line)
		if m:
			env[m[1].replace("@", "local_")] = expression(m[2], env)
			continue
		m = re.match(r"\.org\s+(0x\w+)", line)
		if m:
			pc = int(m[1], 16)
			continue
		if pc is None or line.startswith("."):
			continue
		position = pc - BUS
		expected, actual, status, detail = "", "", "", ""
		m = re.match(r"ldr r(\d+),=(.+)", line)
		if m:
			value = expression(m[2], env)
			instruction = decode(english, position)
			expected = f"PC-relative ldr r{m[1]} resolving to {hx(value)}"
			actual = instruction.raw.hex(" ") + "; " + instruction.text
			reg = (struct.unpack_from("<H", instruction.raw)[0] >> 8) & 7
			status = "MATCH (literal-resolved)" if instruction.literal_value == value and reg == int(m[1]) else "MISMATCH"
			detail = "Literal allocation inferred from actual instruction; value comes independently from source expression."
			pc += 2
		else:
			m = re.match(r"(db|dw)\s+(.+)", line)
			try:
				if m:
					value = expression(m[2], env)
					n = 1 if m[1] == "db" else 4
					encoded = value.to_bytes(n, "little")
				else:
					encoded = encode_instruction(line, pc, env)
					n = len(encoded)
				expected = encoded.hex(" ")
				actual = english[position:position + n].hex(" ")
				status = "MATCH" if english[position:position + n] == encoded else "MISMATCH"
				pc += n
			except (ValueError, KeyError, AssertionError) as error:
				n = 4 if line.startswith("bl ") else 2
				instruction = decode(english, position)
				expected, actual, status = line, instruction.raw.hex(" ") + "; " + instruction.text, "NOT VERIFIED"
				detail = str(error)
				pc += n
		rows.append((number, BUS + position, line, expected, actual, status, detail))
	return rows


def names(toolkit):
	lines = (toolkit / "ta_menus_eng.txt").read_text(encoding="utf-8-sig").splitlines()
	start = next(i for i, line in enumerate(lines) if line.startswith("RESTRUCT 62C250 "))
	result = []
	for i, line in enumerate(lines[start + 1:start + 1 + COUNT]):
		match = re.fullmatch(r"([0-9A-Fa-f]{2})-E:(.*)", line)
		if not match or int(match[1], 16) != i:
			raise ValueError("Non-contiguous Gimmick name manifest")
		result.append(match[2])
	return result


def csv_data(roms, names_by_index):
	buffer = io.StringIO(newline="")
	columns = ["rom_role", "rom_path", "rom_sha256", "record_index_hex", "expected_loader_id_hex", "english_manifest_name", "record_file_offset_hex", "record_bus_address_hex", "record_sha256", "nontext_hex", "diff_offsets_hex", "text_diff_count", "nontext_diff_count"]
	columns += [f"byte_{x:02X}_u8" for x in range(0x22, STRIDE)]
	columns += [f"word_{x:02X}_le_hex" for x in range(0x3C, STRIDE, 4)]
	writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
	writer.writeheader()
	for role, path, blob in roms:
		for i in range(COUNT):
			position = TABLE + i * STRIDE
			record = blob[position:position + STRIDE]
			jp, en = [b[position:position + STRIDE] for _, _, b in roms]
			diffs = [x for x in range(STRIDE) if jp[x] != en[x]]
			row = dict(rom_role=role, rom_path=path.as_posix(), rom_sha256=sha(blob), record_index_hex=hx(i, 2), expected_loader_id_hex=hx(i + 1, 2), english_manifest_name=names_by_index[i], record_file_offset_hex=hx(position), record_bus_address_hex=hx(BUS + position), record_sha256=sha(record), nontext_hex=record[0x22:].hex(" "), diff_offsets_hex=";".join(hx(x, 2) for x in diffs), text_diff_count=sum(x < 0x22 for x in diffs), nontext_diff_count=sum(x >= 0x22 for x in diffs))
			row.update({f"byte_{x:02X}_u8": record[x] for x in range(0x22, STRIDE)})
			row.update({f"word_{x:02X}_le_hex": hx(u32(record, x)) for x in range(0x3C, STRIDE, 4)})
			writer.writerow(row)
	return buffer.getvalue()


def hexdump(blob, start, end):
	return "\n".join(f"{x:08X} / {BUS+x:08X}  {blob[x:min(x+16,end)].hex(' ')}" for x in range(start, end, 16))


def rle_metadata(blob, start):
	"""Walk RLE packets without emitting/decompressing game graphics."""
	if not 0 <= start <= len(blob) - 4 or blob[start] != 0x30:
		return None
	declared = int.from_bytes(blob[start + 1:start + 4], "little")
	position, produced, last = start + 4, 0, None
	while produced < declared:
		if position >= len(blob):
			raise ValueError("RLE stream extends beyond ROM")
		flag_position = position
		flag = blob[position]
		position += 1
		count = (flag & 127) + (3 if flag & 128 else 1)
		payload = 1 if flag & 128 else count
		if position + payload > len(blob):
			raise ValueError("RLE packet extends beyond ROM")
		last = (flag_position, flag, produced, count, blob[position:position + payload])
		position += payload
		produced += count
	return dict(declared=declared, nominal_produced=produced, encoded_bytes=position-start,
		overshoot=produced-declared, last=last)


def cell(text):
	return str(text).replace("|", "\\|").replace("`", "'").replace("\n", " ")


def report(workspace, roms, candidates, toolkit, checks, tool_notes, source_hash):
	jp, en = [b for _, _, b in roms]
	names_by_index = names(toolkit)
	rows = ["# ROM Verification: Gimmick Table and Loader", "", "Read-only binary reconnaissance. Confidence: **Confirmed (binary)** means exact observed bytes or arithmetic; **Confirmed (source comparison)** means the documented limited checks pass; gameplay meanings remain Candidate/Unconfirmed until consumer and runtime evidence establishes them.", "", "## Inputs and reproducibility", "", "ROMs were located recursively rather than assumed from prior paths. Filename hints select default roles; matching title/game code and patch checks support these roles, but this report does not authenticate a canonical clean dump against an external hash database. All file offsets are zero-based; ROM bus address = file offset + 0x08000000. RAM literals have no ROM file offsets.", "", "| Role | Located path | Bytes | SHA-256 | Header title / game code |", "| --- | --- | --- | --- | --- |"]
	for role, path, blob in roms:
		title = blob[0xA0:0xAC].rstrip(b"\0").decode("ascii", "backslashreplace")
		code = blob[0xAC:0xB0].decode("ascii", "backslashreplace")
		rows.append(f"| {role} | `{path.relative_to(workspace).as_posix() if path.is_relative_to(workspace) else path.as_posix()}` | {len(blob):,} (`{hx(len(blob))}`) | `{sha(blob)}` | `{title}` / `{code}` |")
	def ps_path(path):
		value = path.relative_to(workspace).as_posix() if path.is_relative_to(workspace) else path.as_posix()
		return "'" + value.replace("'", "''") + "'"
	command = f"python tools/analyze/verify_gimmick_roms.py --japanese {ps_path(roms[0][1])} --english {ps_path(roms[1][1])}"
	rows += ["", "Discovered .gba candidates: " + "; ".join(f"`{p.relative_to(workspace).as_posix()}`" for p in candidates), "", f"Toolkit source/asset aggregate SHA-256 before/after analysis: `{source_hash}` (relative filenames + each file's SHA-256; .gba excluded).", "", "Re-run from the repository root:", "", "```powershell", command, "```", "", "Without explicit input flags, the script recursively discovers .gba files and refuses ambiguous filename-based selection. Pass discovered paths explicitly if files are renamed or additional candidates appear. The script uses read-only input reads, bounds checks, and post-analysis hash/size/timestamp checks; it writes only this report and the CSV. It never executes the translation build. Script paths: `tools/analyze/verify_gimmick_roms.py` and `tools/analyze/thumb_inspect.py`.", "", "## Table extraction and byte-for-byte comparison", "", f"Inspected 50 records of 0x58 bytes at file `{hx(TABLE)}` / bus `{hx(BUS+TABLE)}`. Half-open table extent: file `{hx(TABLE)}`–`{hx(TABLE+COUNT*STRIDE)}`, bus `{hx(BUS+TABLE)}`–`{hx(BUS+TABLE+COUNT*STRIDE)}`. This verifies those 50 supported records are present; it does not prove a physical table terminator or exclude unused entries."]
	diffs = []
	for i in range(COUNT):
		for x in range(STRIDE):
			position = TABLE + i * STRIDE + x
			if jp[position] != en[position]:
				diffs.append((i, x, position, jp[position], en[position]))
	changed_records = len({i for i, *_ in diffs})
	rows += ["", f"**{COUNT-changed_records}/50 complete records are byte-identical; {changed_records} record(s) differ; {len(diffs)} differing bytes total.** Text bytes +0x00–+0x21 differ at {sum(x < 0x22 for _,x,*_ in diffs)} positions; non-text bytes +0x22–+0x57 differ at {sum(x >= 0x22 for _,x,*_ in diffs)} positions.", "", "| Record index / English source name | Field offset | File offset | ROM bus | Japanese byte | English byte |", "| --- | --- | --- | --- | --- | --- |"]
	for i, x, position, a, b in diffs:
		rows.append(f"| `{hx(i,2)}` / {names_by_index[i]} | `{hx(x,2)}` | `{hx(position)}` | `{hx(BUS+position)}` | `{hx(a,2)}` | `{hx(b,2)}` |")
	if not diffs:
		rows.append("| No differences | — | — | — | — | — |")
	rows += ["", "CSV: [data/gimmick_raw_fields.csv](data/gimmick_raw_fields.csv), 100 rows (50 per ROM). Each row contains all 54 non-text bytes as unsigned decimal columns `byte_22_u8`…`byte_57_u8`, a lossless hex string, record hash/address, difference metadata, and little-endian word views at +0x3C/+0x40/+0x44/+0x48/+0x4C/+0x50/+0x54. Word views are raw numeric interpretations, not assertions that these fields are pointers. English names are manifest annotations; expected loader IDs are source-derived, not emulator observations.", "", "### Choo-Choo graphics pointer", ""]
	slot = TABLE + 0x1D * STRIDE + 0x44
	a, b = u32(jp, slot), u32(en, slot)
	rows += [f"Record index 0x1D (manifest Choo-Choo), expected loader ID 0x1E, starts at file `{hx(TABLE+0x1D*STRIDE)}` / bus `{hx(BUS+TABLE+0x1D*STRIDE)}`. Field +0x44 occupies file `{hx(slot)}`–`{hx(slot+4)}` (half-open).", "", f"- Japanese bytes: `{jp[slot:slot+4].hex(' ')}` → little-endian `{hx(a)}`.", f"- English bytes: `{en[slot:slot+4].hex(' ')}` → little-endian `{hx(b)}`."]
	for role, _, blob in roms:
		pointer = u32(blob, slot)
		position = pointer - BUS
		if 0 <= position <= len(blob) - 4:
			header = blob[position:position+4]
			rows.append(f"- {role} pointed-to file offset `{hx(position)}`, first four bytes `{header.hex(' ')}`; format byte `{hx(header[0],2)}`, 24-bit LE size `{hx(int.from_bytes(header[1:4], 'little'))}`.")
		else:
			rows.append(f"- {role} pointer lies outside inspected ROM window.")
	rows += ["", "RLE packet metadata walk (no graphics decompression/export):", "", "| ROM | Encoded bytes consumed through final packet | Header decoded size | Nominal packet output | Overshoot | Final packet evidence |", "| --- | --- | --- | --- | --- | --- |"]
	for role, _, blob in roms:
		metadata = rle_metadata(blob, u32(blob, slot) - BUS)
		if metadata:
			position, flag, before, count, payload = metadata['last']
			rows.append(f"| {role} | {metadata['encoded_bytes']} | {metadata['declared']} | {metadata['nominal_produced']} | {metadata['overshoot']} | File `{hx(position)}` / bus `{hx(BUS+position)}`; flag `{hx(flag,2)}`, payload preview `{payload[:8].hex(' ')}` ({len(payload)} byte(s)); {before} bytes before packet, nominal count {count} |")
	english_rle = rle_metadata(en, b - BUS)
	if english_rle and english_rle['overshoot']:
		rows += ["", f"**Observed RLE length inconsistency:** the English stream consumes {english_rle['encoded_bytes']} encoded bytes through its final packet, exceeding the source's 5,049-byte original budget. Its packets nominally produce {english_rle['nominal_produced']} bytes against a header size of {english_rle['declared']} ({english_rle['overshoot']} extra). This supports relocation while identifying a data-format anomaly. `inserter/rle.cpp:17-35` initializes a repeat length to 0x82 and can retain it when fewer identical bytes remain; that source defect is consistent with an oversized final repeat, but build provenance and actual decompressor behavior are not established. No graphics were decompressed/exported and no runtime fault is claimed."]
	rows += ["", "`inserter/images.cpp:754-786` loads original tileset file 0x00577A1C and conditionally rewrites slot 0x0062CC8C through `SaveCompressedTileset`/`WriteRelocs` (lines 167-180/92-96). Header method 0x30 is the RLE format implemented in `inserter/rle.cpp`; the source's shared allocation pool spans file 0x0064B4EC-0x007F0000 for comparison with the observed location. A changed pointer is consistent with known translation image relocation. It does not prove the entire patch was produced by the currently checked source/executable, nor decode the graphic or its runtime consumer. No gameplay-field meanings are inferred from numeric values.", "", "## Loader literals", "", "The four slots are compared across ROMs and with `asm/gimmick_text.asm:77-92` comments. Literal slot addresses are ROM; values beginning 0x03 are IWRAM.", "", "| Slot file / bus | Japanese raw bytes / value | English raw bytes / value | Expected value / role | Comparison |", "| --- | --- | --- | --- | --- |"]
	labels = ["utility parameters (IWRAM)", "ID argument (IWRAM)", "original record base minus 0x58 (ROM bus)", "work-record base (IWRAM)"]
	for (position, expected), label in zip(LITERALS.items(), labels):
		status = "MATCH" if u32(jp, position) == u32(en, position) == expected else "MISMATCH"
		rows.append(f"| `{hx(position)}` / `{hx(BUS+position)}` | `{jp[position:position+4].hex(' ')}` / `{hx(u32(jp,position))}` | `{en[position:position+4].hex(' ')}` / `{hx(u32(en,position))}` | `{hx(expected)}`; {label} | {status} |")
	rows += ["", "## Loader regions and exact bytes", "", "Ranges are half-open. The continuation includes its original four-word literal pool; it is not all executable instructions. Inspection ends at 0x000656C2, the source epilogue patch boundary, not a claim about the full native function size.", "", "| Region | File range / bus range | Bytes | Differing bytes | Japanese SHA-256 | English SHA-256 |", "| --- | --- | --- | --- | --- | --- |"]
	for label, start, end in REGIONS:
		changed = sum(a != b for a, b in zip(jp[start:end], en[start:end]))
		rows.append(f"| {label} | `{hx(start)}`–`{hx(end)}` / `{hx(BUS+start)}`–`{hx(BUS+end)}` | {end-start} | {changed} | `{sha(jp[start:end])}` | `{sha(en[start:end])}` |")
	for role, _, blob in roms:
		rows += ["", f"### {role}: loader hex dump", "", "Format: file offset / ROM bus address, followed by exact bytes. Includes literal pools as data.", "", "```text", hexdump(blob, 0x65518, 0x656C2), "```"]
	rows += ["", "## ASM comparison", "", "Checks below derive expected bytes from the currently read `asm/gimmick_text.asm`. They cover its direct db/dw writes, the loader prefix, name consumer patch, description pointer-store patches and epilogue instructions. The small source encoder implements only the relevant Thumb subset. The symbolic `bl CopyString8x8Clear8` remains NOT VERIFIED because its placement is not declared here; its actual decoded call target is still recorded. The prefix's pseudo-ldr is checked by resolved literal value rather than an assumed allocation address. Region padding and the entire translation project are not reassembled."]
	matches = sum(row[5].startswith("MATCH") for row in checks)
	mismatches = sum(row[5] == "MISMATCH" for row in checks)
	unknown = sum(row[5] == "NOT VERIFIED" for row in checks)
	rows += ["", f"Results: **{matches} matching checks, {mismatches} mismatches, {unknown} unverified check(s).** Source file SHA-256: `{sha((toolkit/'asm/gimmick_text.asm').read_bytes())}`.", "", "| Source line | Bus / file | ASM | Expected | English observed | Status |", "| --- | --- | --- | --- | --- | --- |"]
	for number, address, asm, expected, actual, status, _ in checks:
		rows.append(f"| `asm/gimmick_text.asm:{number}` | `{hx(address)}` / `{hx(address-BUS)}` | `{cell(asm)}` | `{cell(expected)}` | `{cell(actual)}` | {status} |")
	rows += ["", "## Linear Thumb instruction inspection", "", "Generated by the local `thumb_inspect.py` helper. This is limited instruction-format inspection, not an independently validated full disassembler, control-flow graph or runtime trace. Register moves may appear as add-immediate-zero encodings; this report uses instruction encoding rather than guessing higher-level semantics. The four literal slots at file [0x655D4,0x655E4) are excluded from both listings; the patched prefix's literal at [0x65568,0x6556C) is also excluded. Padding at [0x656C0,0x656C2) is excluded."]
	for role, _, blob in roms:
		excluded = [(0x655D4, 0x655E4), (0x656C0, 0x656C2)]
		if role == "English-patched":
			excluded.append((0x65568, 0x6556C))
		rows += ["", f"### {role}: instruction listing", "", "```text"]
		for instruction in inspect(blob, 0x65518, 0x656C2, excluded):
			rows.append(f"{instruction.address-BUS:08X} / {instruction.address:08X}  {instruction.raw.hex(' '):11} {instruction.text}")
		rows += ["```"]
	flags_signature = bytes.fromhex("0f 25 2a 1c 0a 40 45 30 02 70 00 20 33 1c 6d 33 18 70 09 06 09 0f 03 20 01 40 30 1c 6e 30 01 70")
	indexed_signature = bytes.fromhex("60 78 01 38 40 00 78 70 38 71 40 46 78 71 30 1c 28 30 b9 88 43 18 fb 60 19 78 58 1c f8 60 30 1c 69 30 01 70")
	shape_matches = jp[0x6556A:0x6556C] == bytes.fromhex("01 78") and en[0x65564:0x65566] == bytes.fromhex("01 68")
	shape_matches &= all(blob[0x6556C:0x6558C] == flags_signature and blob[0x6558C:0x655B0] == indexed_signature
		and blob[0x655FE:0x65600] == bytes.fromhex("d0 6b") and blob[0x65602:0x65604] == bytes.fromhex("03 78")
		and u32(blob, 0x656C4) == 0x030018BC and u32(blob, 0x656C8) == 0x03003F34 for _, _, blob in roms)
	if shape_matches:
		rows += ["", "### Focused continuation observations", "", "These data-flow observations use actual instruction bytes and the small local Thumb decoder; the listed signatures were checked in both inputs; confirm them independently before assigning gameplay meanings:", "", "- Japanese file `0x0006556A` / bus `0x0806556A` has `01 78` (`ldrb r1,[r0]`) after forming work-record +0x27. English file `0x00065564` / bus `0x08065564` has `01 68` (`ldr r1,[r0]`), matching source line 132. This byte-load versus unaligned word-load difference is real, source-consistent, and needs architecture/runtime validation; it is not a discrepancy between the English bytes and ASM.", "- At file `0x0006556C`–`0x0006558C`, both ROMs mask low four bits of incoming r1 and store at work +0x6C; shifts and mask 3 extract low-byte bits 4–5 into work +0x6E. Meaning of these groups remains unidentified.", "- At file `0x0006558C`–`0x000655AE`, ID-argument byte +1 supplies a one-based selector: subtract one, multiply by two, and add to copied record +0x28. A byte is read into work +0x69; the next byte is consumed in a branch selected by the preceding low-bit group. This supports an indexed two-byte lookup, not a confirmed nine-level difficulty model or power formula.", "- At file `0x000655FE` / bus `0x080655FE`, bytes `d0 6b` load a word from work-record +0x3C; at file `0x00065602` / bus `0x08065602`, `03 78` dereferences that value as a byte. PC-relative literals at file `0x000656C4` / bus `0x080656C4` and file `0x000656C8` / bus `0x080656C8` resolve to `0x030018BC` and `0x03003F34`. This strengthens the pointer-access interpretation at +0x3C but does not identify its data meaning."]
	else:
		rows += ["", "### Focused continuation observations", "", "Instruction signatures differ from the documented inputs; no canned field interpretation is applied. Inspect the actual listings and source-check discrepancies."]
	rows += ["", "## Tool availability and limits", ""] + tool_notes
	rows += ["", "No tool was installed. The existing objdump is usable for GBA only if its architecture listing advertises ARM; generic binary input support alone is insufficient. If no ARM-capable tool is found, obtain an ARMv4T/Thumb-capable disassembler (ARM GNU objdump, LLVM with ARM support, or Ghidra) and a GBA debugger such as mGBA for the next investigation. The local Python helper is sufficient for these bounded format/byte checks, not a replacement for full disassembly or emulation.", "", "## Conclusions and next investigation", "", "- The measured 50-record window and literal comparisons provide evidence for assessing the source layout. Numerical gameplay field meanings remain unverified.", "- The exact table difference list above distinguishes actual changes from hypothetical source relocation. Text and raw field bytes are preserved except the explicitly listed differences.", "- Source checks establish only the bounded agreement reported above; unverified symbolic calls, padding, runtime behavior and whole-ROM build provenance are outside that claim.", "- Next: independently disassemble the retained loader continuation and trace accesses to +0x27 and its indexed +0x28 region, then locate callers and damage/difficulty consumers. Use debugger read watchpoints on the verified IWRAM work base and record per-Gimmick calculation paths. Investigate any RLE packet overshoot separately before trusting a future build; do not assign power/RNG/Kaizo semantics solely from byte values.", "", "Both ROMs were re-read after analysis; SHA-256, byte size and modification timestamp matched the initial snapshots. Toolkit fingerprint also matched. Outputs contain analysis only; no translation build, source edit or ROM write occurred."]
	return "\n".join(rows) + "\n"


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[2])
	parser.add_argument("--japanese")
	parser.add_argument("--english")
	parser.add_argument("--output-dir", type=Path, default=Path("reverse_engineering"))
	args = parser.parse_args()
	workspace = args.workspace.resolve()
	toolkit = workspace / "tomatotrans-1.1.1"
	jp_path, en_path, candidates = discover(workspace, args.japanese, args.english)
	output = (workspace / args.output_dir).resolve()
	analysis_root = (workspace / "reverse_engineering").resolve()
	if not analysis_root.is_relative_to(workspace) or not output.is_relative_to(analysis_root):
		raise ValueError("Output directory must remain beneath workspace/reverse_engineering")
	outputs = [output / "rom_verification.md", output / "data/gimmick_raw_fields.csv"]
	if any(not p.resolve().is_relative_to(output) or p.is_symlink() for p in outputs):
		raise ValueError("Analysis output must not follow a file/directory link outside the output directory")
	if any(p.resolve() in candidates or p.resolve() in (jp_path, en_path) for p in outputs):
		raise ValueError("Output must not alias a ROM input")
	if any(p.exists() and p.samefile(q) for p in outputs for q in (jp_path, en_path)):
		raise ValueError("Output must not share an input ROM filesystem identity")
	roms, snapshots = [], {}
	for role, path in [("Japanese", jp_path), ("English-patched", en_path)]:
		blob = path.read_bytes()
		if len(blob) < max(TABLE + COUNT * STRIDE, 0x656C2):
			raise ValueError(f"ROM too short for requested inspection: {path}")
		roms.append((role, path, blob))
		snapshots[path] = (sha(blob), len(blob), path.stat().st_mtime_ns)
	source_hash = source_fingerprint(toolkit)
	checks = source_checks(roms[1][2], toolkit)
	csv_text = csv_data(roms, names(toolkit))
	report_text = report(workspace, roms, candidates, toolkit, checks, tooling(), source_hash)
	for path, before in snapshots.items():
		current = path.read_bytes()
		if (sha(current), len(current), path.stat().st_mtime_ns) != before:
			raise RuntimeError(f"ROM changed during analysis: {path}")
	if source_fingerprint(toolkit) != source_hash:
		raise RuntimeError("Toolkit sources/assets changed during analysis")
	for path, text in zip(outputs, [report_text, csv_text]):
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_text(text, encoding="utf-8", newline="")
	print(f"Created {outputs[0].relative_to(workspace)}")
	print(f"Created {outputs[1].relative_to(workspace)} (100 records; 54 raw byte fields each)")
	print("Source checks:", {status: sum(row[5] == status for row in checks) for status in sorted({row[5] for row in checks})})
	print("ROM hashes/sizes/timestamps and toolkit fingerprint unchanged.")


if __name__ == "__main__":
	main()
