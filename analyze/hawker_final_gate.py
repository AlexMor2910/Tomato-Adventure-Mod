"""Read-only final Hawker gate evidence; JSON stdout. Never constructs a ROM."""
import json
from pathlib import Path
import struct
import sys

from hawker_placement_safety import ROOT, SOURCE, EXPECTED, sha, audit
from hawker_dependency_resolution import analyze
from thumb_inspect import decode


def main():
	# Include toolkit ROMs, disposable saves and checkpoints in this scoped audit.
	extensions = {".gba", ".sav", ".ss0", ".ss1", ".ss2", ".ss3", ".ss4",
		".ss5", ".ss6", ".ss7", ".ss8", ".ss9"}
	paths = [p for p in ROOT.rglob("*") if p.is_file() and
		(p.suffix.lower() in extensions or "savestates" in p.relative_to(ROOT).parts)]
	before = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths}
	r = SOURCE.read_bytes()
	assert len(r) == 0x1000000 and sha(r) == EXPECTED
	prior = {}
	for name in ("hawker_placement_investigation", "hawker_placement_safety_evidence",
		"hawker_dependency_resolution_evidence"):
		p = ROOT / "reverse_engineering" / (name + ".json")
		prior[name] = json.loads(p.read_text(encoding="utf-8"))
	safety, dependency = json.loads(json.dumps(audit())), json.loads(json.dumps(analyze()))
	# Reproduce old evidence without rewriting its historical verification envelope.
	for key, value in dependency.items():
		assert value == prior["hawker_dependency_resolution_evidence"][key], key
	for key, value in safety.items():
		assert value == prior["hawker_placement_safety_evidence"][key], key
	m = json.loads((ROOT / "tools/patch/output/detector-hp120-mit25/manifest.json").read_text())
	k = (ROOT / m["source"]).read_bytes()
	assert sha(k) == m["source_sha256"] and sha(r) == m["output_sha256"]
	diffs = [{"file": f"0x{i:08X}", "before": f"{a:02X}", "after": f"{b:02X}"}
		for i, (a, b) in enumerate(zip(k, r)) if a != b]
	assert len(k) == len(r) and diffs == [
		{"file": "0x00638056", "before": "87", "after": "78"},
		{"file": "0x0063805A", "before": "26", "after": "19"}]
	km = json.loads((ROOT / Path(m["source"]).parent / "manifest.json").read_text())
	assert sha(k) == km["output_sha256"]
	assert all(r[int(op["file"], 16)] == int(op["new"], 16)
		for op in km["verification"]["differences"])
	windows = []
	# Explicit instruction ranges exclude literal pools; no inferred whole-function CFG.
	for name, start, end in (
		("FE C8 dialogue entry", 0x29E20, 0x29E30),
		("FE66 dialogue entry", 0x29D98, 0x29DA8),
		("shared dialogue bridge", 0x29DAC, 0x29DBE),
		("movement deltas accepted or cleared", 0x66476, 0x664A8),
		("movement scheduler entry", 0x664A8, 0x66512),
		("command36 continuation decision", 0x23CD2, 0x23D00),
	):
		a, instructions = start, []
		while a < end:
			i = decode(r, a)
			assert a + i.size <= end
			instructions.append({"bus": f"0x{i.address:08X}", "bytes": i.raw.hex(" "), "text": i.text})
			a += i.size
		windows.append({"name": name, "file_range_exclusive": [hex(start), hex(end)],
			"sha256": sha(r[start:end]), "instructions": instructions,
			"confidence": "Confirmed static instructions; transitive effects unproven"})
	after = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths}
	assert before == after and sha(SOURCE.read_bytes()) == EXPECTED
	print(json.dumps({"status": "BLOCKED — NO ROM MODIFIED", "source": SOURCE.relative_to(ROOT).as_posix(),
		"source_sha256": EXPECTED, "source_bytes": len(r), "prior_evidence_reproduced": True,
		"baseline_parent_sha256": sha(k), "baseline_parent_differences": diffs,
		"kaizo_ledger_bytes_validated": len(km["verification"]["differences"]),
		"header_complement_valid": r[0xBD] == (-sum(r[0xA0:0xBD]) - 0x19) & 255,
		"stats": safety["accepted_stats"], "new_native_windows": windows,
		"checks": {"scratch_lifetime": "BLOCKED: transitive dialogue/event writers not closed",
			"scoped_adapter": "BLOCKED: ownership and executable cursor/register contract unverified",
			"movement": "BLOCKED: collision scheduling and all reachable approaches not proven",
			"graphics_lifetime": "BLOCKED: initialization capacity passes; deferred/event writes not closed",
			"actor_identity": "BLOCKED: record absence passes; saved-state/script ownership not proven"},
		"protected_before": before, "protected_after": after, "protected_count": len(before),
		"protected_unchanged": True, "rom_bytes_changed_this_run": 0,
		"runtime_performed": False, "output_rom": None}, indent=2))


if __name__ == "__main__":
	main()
