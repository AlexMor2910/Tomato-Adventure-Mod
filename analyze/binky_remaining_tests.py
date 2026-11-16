"""Read-only verification and bounded remaining-character test evidence."""
import importlib.util
import json
import struct
import zlib

from awe_initialization import ROOT, RECRUITMENT, protected
from pre_oystown_foundation import checkpoint
from oystown_completion import state_bytes
from thumb_inspect import inspect

OUTPUTS = (
	("baseline", "binky-rate-two-baseline-c4ec3611142c49cf93d891cbfc10f056", "b9967b15193b5aec701032742d322a1040373e76b176b1aeb1e65ce2c06078b6"),
	("recruitment-test", "binky-rate-two-recruitment-test-aaee9ff3918c42aabf6d9bec7cff611f", "d356a6979c497524d1e94306989e09cf8dfe96334a22c664eb3a9570f3ab3ea3"),
)
WINDOWS = (
	("FE49 first-absent companion initializer", 0x252F4, 0x25374, ((0x25320, 0x2532C), (0x2536C, 0x25374))),
	("FE4A membership-only enable", 0x25374, 0x253A4, ((0x25398, 0x253A4),)),
	("FE4B membership-only disable", 0x253A4, 0x253D4, ((0x253C8, 0x253D4),)),
	("initializer bridge", 0x32BF0, 0x32C10, ((0x32C08, 0x32C10),)),
	("generic character initializer", 0x32CB8, 0x32E50, ((0x32DD8, 0x32DF4), (0x32E44, 0x32E50))),
)


def main():
	before = protected()
	prior = json.loads((ROOT / "reverse_engineering/experiments/binky_exchange_rate_two_evidence.json").read_text())
	for name, fingerprint in prior["protected_before"].items():
		if before.get(name) != fingerprint:
			raise ValueError("Prior protected artifact changed: " + name)
	spec = importlib.util.spec_from_file_location("rate_patch", ROOT / "tools/patch/binky_exchange_rate_two.py")
	patch = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(patch)
	verified, identities = [], set()
	for profile, folder, fingerprint in OUTPUTS:
		directory = ROOT / "tools/patch/output" / folder
		manifest = json.loads((directory / "manifest.json").read_text())
		output = (directory / "binky_exchange_rate_two.gba").read_bytes()
		source = patch.PROFILES[profile][0].read_bytes()
		if patch.sha(output) != fingerprint or manifest["output_sha256"] != fingerprint:
			raise ValueError("Output hash mismatch")
		checks = patch.verify_output(source, output, profile)  # No build/main invocation.
		if checks != manifest["verification"] or checks["changed_bytes"] != 118:
			raise ValueError("Verification differs from retained manifest")
		if manifest["script_sha256"] != patch.sha((ROOT / "tools/patch/binky_exchange_rate_two.py").read_bytes()):
			raise ValueError("Patch script differs from construction")
		verified.append(dict(profile=profile, path=str(directory.relative_to(ROOT)), sha256=fingerprint, verification=checks))
		identities.add((zlib.crc32(output) & 0xFFFFFFFF, output[0xA0:0xB0]))
	original = RECRUITMENT.read_bytes()
	identities.add((zlib.crc32(original) & 0xFFFFFFFF, original[0xA0:0xB0]))
	states = []
	for name in ("before_oystown.ss0", "after_exchange_oystown.ss0", "after_exchange_oystown_alessa_test.ss0"):
		path = ROOT / name
		if not path.exists():
			states.append(dict(path=name, missing=True))
			continue
		item = dict(path=name, **checkpoint(path, identities))
		iw = state_bytes(path)[0x19000:0x21000]
		item["cached_node"] = iw[0x35F4]
		item["scheduler_bitmap"] = iw[0x39C1:0x39C5].hex(" ")
		item["tier_bytes"] = {hex(0x03000000 + a): hex(iw[a]) for a in (0x32FE, 0x331F, 0x3326)}
		item["all_character_records"] = [dict(index=i, base=hex(0x03001EDC + i * 0x60),
			membership_mask=hex(0x10 << i), present=bool(iw[0x1AB4] & (0x10 << i)),
			inventory_count=iw[0x1EDC + i * 0x60 + 7],
			charge=iw[0x1EDC + i * 0x60 + 0x58], ready=iw[0x1EDC + i * 0x60 + 0x59],
			raw=iw[0x1EDC + i * 0x60:0x1EDC + (i + 1) * 0x60].hex(" ")) for i in range(4)]
		item["binky_entries"] = [dict(id_address=hex(0x030019D5 + i * 2), count_address=hex(0x030019D6 + i * 2), count=iw[0x19D6 + i * 2])
			for i in range(min(iw[0x19D4], 77)) if iw[0x19D5 + i * 2] == 0x37]
		states.append(item)
	windows = []
	for role, start, end, pools in WINDOWS:
		if original[start:end] != (ROOT / "tools/patch/output" / OUTPUTS[1][1] / "binky_exchange_rate_two.gba").read_bytes()[start:end]:
			raise ValueError("Rate patch changes initialization scope")
		windows.append(dict(role=role, range=[hex(start), hex(end)],
			instructions=[dict(bus=hex(i.address), bytes=i.raw.hex(" "), text=i.text) for i in inspect(original, start, end, pools)]))
	after = protected()
	if before != after:
		raise RuntimeError("Protected files changed")
	print(json.dumps(dict(mode="read-only remaining-test planning; no ROM/state construction", verified_outputs=verified,
		checkpoints=states, initialization_windows=windows,
		default_descriptors=[dict(character=i, bus=hex(0x08630BDC + i * 28), raw=original[0x630BDC + i * 28:0x630BDC + (i + 1) * 28].hex(" ")) for i in (1, 2, 3)],
		protected_count=len(before), protected_before=before, protected_after=after, protected_unchanged=True,
		limitations=["New companion initialization runtime untested", "No one-shot carrier certified for current Oystown state", "Narrative meanings of BA/1C4 not mapped", "Tier simulations are disposable conversation-only candidates"]), indent=2))


if __name__ == "__main__":
	main()
