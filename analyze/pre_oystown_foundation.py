"""Audit saved party foundations and prepare unchanged disposable input copies.

Never launches an emulator, writes RAM, patches a ROM or transforms a state.
Default: print read-only audit. --prepare: fresh capture package and manifest.
"""
import argparse
import hashlib
import json
import re
import shutil
import struct
import uuid
import zlib
from pathlib import Path

from awe_initialization import EXPECTED, RECRUITMENT, ROOT, protected


def sha(data):
	return hashlib.sha256(data).hexdigest()


def checkpoint(path, identities):
	data = path.read_bytes()
	if data[:8] != b"\x89PNG\r\n\x1a\n":
		raise ValueError("Unsupported state format; no raw/opaque offset guessing")
	p, state, dimensions = 8, None, None
	while p < len(data):
		if len(data) - p < 12:
			raise ValueError("Truncated PNG chunk")
		n = struct.unpack_from(">I", data, p)[0]
		if p + n + 12 > len(data):
			raise ValueError("Truncated PNG payload")
		tag, value = data[p + 4:p + 8], data[p + 8:p + 8 + n]
		if zlib.crc32(tag + value) & 0xFFFFFFFF != struct.unpack_from(">I", data, p + 8 + n)[0]:
			raise ValueError("PNG CRC mismatch")
		if tag == b"IHDR":
			dimensions = struct.unpack_from(">II", value)
		if tag == b"gbAs":
			if state is not None:
				raise ValueError("Duplicate state chunk")
			decoder = zlib.decompressobj()
			state = decoder.decompress(value, 0x61001)
			if len(state) != 0x61000 or not decoder.eof or decoder.unused_data:
				raise ValueError("Unexpected GBA serialized state size/stream")
		p += n + 12
		if tag == b"IEND":
			break
	if p != len(data) or state is None or dimensions != (240, 160):
		raise ValueError("Incomplete GBA PNG state")
	magic, bios, crc = struct.unpack_from("<III", state)
	if magic != 0x01000007 or (crc, state[0x10:0x20]) not in identities:
		raise ValueError("Unsupported state version or unrecognized ROM identity")
	iw = state[0x19000:0x21000]
	characters = []
	for index in (0, 1):
		base = 0x1EDC + index * 0x60
		count = iw[base + 7]
		characters.append(dict(index=index, record_address=hex(0x03000000 + base),
			record_hex=iw[base:base + 0x60].hex(" "), inventory_count=count,
			inventory=[list(iw[base + 8 + slot * 3:base + 11 + slot * 3])
				for slot in range(min(count, 20))], inventory_count_in_bounds=count <= 20))
	return dict(sha256=sha(data), bytes=len(data), rom_crc32=f"{crc:08X}",
		state_magic=hex(magic), bios_checksum=f"{bios:08X}",
		membership=iw[0x1AB4], derived_party_count=iw[0x35F0],
		map_id=struct.unpack_from("<H", iw, 0x1936)[0], characters=characters,
		alessa_charge=iw[0x1F94], alessa_ready=iw[0x1F95],
		oystown_intro_flag_1F4=bool(iw[0x3325] & 0x10),
		classification="confirmed static saved bytes; stable field context not certified")


def audit():
	before = protected()
	for path, expected in EXPECTED.items():
		if before.get(str(path.relative_to(ROOT))) != expected:
			raise ValueError("Protected fingerprint mismatch: " + str(path))
	evidence = (ROOT / "reverse_engineering/pre_oystown_progression_evidence.json").read_bytes()
	prior = json.loads(evidence.decode("utf-16" if evidence[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"))
	for name, expected in prior["protected_before"].items():
		if before.get(name) != expected:
			raise ValueError("Prior protected artifact missing or changed: " + name)
	identities = set()
	for path in EXPECTED:
		if path.suffix == ".gba":
			rom = path.read_bytes()
			identities.add((zlib.crc32(rom) & 0xFFFFFFFF, rom[0xA0:0xB0]))
	groups, errors, saves = {}, [], []
	for name, digest in before.items():
		path = ROOT / name
		if re.fullmatch(r"\.ss\d.*", path.suffix.lower()):
			if digest in groups:
				groups[digest]["paths"].append(name)
				continue
			try:
				groups[digest] = dict(paths=[name], **checkpoint(path, identities))
			except (ValueError, struct.error, zlib.error) as error:
				errors.append(dict(path=name, error=str(error)))
		elif path.suffix.lower() == ".sav":
			data = path.read_bytes()
			saves.append(dict(path=name, sha256=digest, bytes=len(data),
				erased=bool(data) and all(b == 0xFF for b in data),
				classification="erased/non-erased only; EEPROM record decoding not certified"))
	if protected() != before:
		raise RuntimeError("Protected artifacts changed during audit")
	return dict(protected_before=before, protected_count=len(before),
		checkpoints=list(groups.values()), inspection_errors=errors, battery_saves=saves,
		party_candidates=[g["paths"] for g in groups.values() if g["membership"] == 0x31],
		protected_unchanged=True)


def prepare(report, output_name=None):
	name = output_name or "pre-oystown-foundation-" + uuid.uuid4().hex
	if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name):
		raise ValueError("Output name must be a simple directory name")
	if report["inspection_errors"]:
		raise ValueError("Resolve checkpoint inspection errors before selecting a source")
	if report["party_candidates"]:
		raise ValueError("Post-recruitment candidates found; inspect their context before preparation")
	base = ROOT / "reverse_engineering/experiments/testing"
	base.mkdir(parents=True, exist_ok=True)
	output = base / name
	output.mkdir(exist_ok=False)
	for sub in ("rom", "inputs", "captures", "saves", "patches", "cheats", "screenshots", "logs"):
		(output / sub).mkdir()
	copies = []
	for source, target in ((RECRUITMENT, output / "rom/alessa_recruitment_wrapper.gba"),
		(ROOT / "entry-stop.ss0", output / "inputs/entry-stop.ss0")):
		shutil.copyfile(source, target)
		if source.read_bytes() != target.read_bytes():
			raise RuntimeError("Full-file copy comparison failed")
		copies.append(dict(source=str(source), destination=str(target),
			before_sha256=sha(source.read_bytes()), after_sha256=sha(target.read_bytes()),
			full_file_identical=True, modified_bytes=0))
	after = protected()
	if any(after.get(name) != digest for name, digest in report["protected_before"].items()):
		raise RuntimeError("Protected artifact changed during preparation")
	manifest = dict(status="capture preparation only; post-recruitment source absent; stages A-F not applied",
		output=str(output), audit=report, copies=copies, state_changes=[],
		protected_after=after, preexisting_protected_unchanged=True,
		new_protected_paths=sorted(set(after) - set(report["protected_before"])),
		script_sha256=sha(Path(__file__).read_bytes()),
		next_capture=str(output / "captures/post-recruitment.ss0"))
	with (output / "manifest.json").open("x", encoding="utf-8") as stream:
		stream.write(json.dumps(manifest, indent=2) + "\n")
	if json.loads((output / "manifest.json").read_text()) != manifest:
		raise RuntimeError("Manifest readback failed")
	with (output / "CAPTURE.md").open("x", encoding="utf-8") as stream:
		stream.write("# Capture preparation, not a pre-Oystown checkpoint\n\n"
			"No emulator has been launched. Keep the prior test environment unchanged.\n"
			"If the validated party is still available, export a NEW state while idle in the field, "
			"outside dialogue/battle, to captures/post-recruitment.ss0 here. Do not overwrite a slot.\n"
			"Otherwise use a fresh portable mGBA 0.10.5 environment, this ROM copy and the "
			"inputs/entry-stop.ss0 copy; complete only the already validated first Hanzo reward "
			"interaction, then export that new state. No Mayonen visit is required.\n\n"
			"Use isolated saves/states/patches/cheats paths, loadStateExtdata=9, saveStateExtdata=9, "
			"rewindEnable=0, useBios=0 and skipBios=1. Verify GUI paths before loading. "
			"A CRC-only different-ROM-version warning can occur for the entry checkpoint; "
			"stop on title/ID, BIOS or load errors. Never replay recruitment on a recruited state.\n\n"
			"Stop on an abnormal event, party, inventory or movement result. Do not enter Oystown. "
			"No RAM writes or extra debugger reads are requested for this capture. "
			"The new state will be audited offline before any transformation.\n")
	return output


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--prepare", action="store_true")
	parser.add_argument("--output-name")
	args = parser.parse_args()
	if args.output_name and not args.prepare:
		parser.error("--output-name requires --prepare")
	report = audit()
	if args.prepare:
		print(prepare(report, args.output_name))
	else:
		print(json.dumps(report, indent=2))
